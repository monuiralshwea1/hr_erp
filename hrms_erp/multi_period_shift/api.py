# Copyright (c) 2026, Shumul. All rights reserved.
"""
Multi-Period Shift Management API
Provides whitelisted endpoints for biometric device integration and attendance processing.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime

from hr_erp.hrms_erp.multi_period_shift.duplicate_detector import safe_create_checkin
from hr_erp.hrms_erp.multi_period_shift.biometric_handler import get_device_by_id, update_device_sync


@frappe.whitelist()
def receive_biometric_checkin(employee_field_value, timestamp, device_id=None, log_type=None,
                               skip_auto_attendance=0, employee_fieldname="attendance_device_id"):
	"""
	Receive a checkin from a biometric device with duplicate prevention.
	Safe to call multiple times with same data (idempotent).
	"""
	if not employee_field_value or not timestamp:
		frappe.throw(_("'employee_field_value' and 'timestamp' are required."))

	employee = frappe.db.get_values(
		"Employee",
		{employee_fieldname: employee_field_value},
		["name", "employee_name", employee_fieldname],
		as_dict=True,
	)
	if not employee:
		frappe.throw(_("No Employee found for value '{}': {}").format(employee_fieldname, employee_field_value))

	employee = employee[0]

	# Resolve biometric device
	resolved_device_id = device_id
	if device_id:
		device = get_device_by_id(device_id)
		if device:
			resolved_device_id = device.name

	checkin = safe_create_checkin(
		employee=employee.name,
		timestamp=timestamp,
		log_type=log_type,
		device_id=device_id,
		skip_auto=skip_auto_attendance,
	)

	if checkin:
		if resolved_device_id and frappe.db.exists("Biometric Device", resolved_device_id):
			update_device_sync(resolved_device_id)
		return {"status": "created", "checkin": checkin.name}
	else:
		return {"status": "duplicate", "checkin": None}


@frappe.whitelist()
def process_attendance_for_shift(shift_type_name, date=None):
	"""
	Manually trigger multi-period attendance processing for a shift type.
	"""
	shift_doc = frappe.get_doc("Shift Type", shift_type_name)
	if not shift_doc.enable_auto_attendance:
		frappe.throw(_("Auto attendance is not enabled for this shift type."))

	result = shift_doc.process_auto_attendance(is_manually_triggered=True)
	return result


@frappe.whitelist()
def get_employee_period_attendance(employee, attendance_date):
	"""
	Get period-wise attendance details for an employee on a specific date.
	"""
	if not frappe.db.exists("Attendance", {"employee": employee, "attendance_date": attendance_date}):
		frappe.throw(_("No attendance found for {} on {}").format(employee, attendance_date))

	att = frappe.get_doc("Attendance", frappe.db.exists(
		"Attendance", {"employee": employee, "attendance_date": attendance_date}
	))

	return {
		"attendance": att.name,
		"employee": att.employee,
		"date": str(att.attendance_date),
		"status": att.status,
		"working_hours": att.working_hours,
		"late_entry": att.late_entry,
		"early_exit": att.early_exit,
		"in_time": str(att.in_time) if att.in_time else None,
		"out_time": str(att.out_time) if att.out_time else None,
		"total_late_minutes": att.total_late_minutes if hasattr(att, 'total_late_minutes') else 0,
		"total_overtime_hours": att.total_overtime_hours if hasattr(att, 'total_overtime_hours') else 0,
		"period_details": [
			{
				"period_name": pd.period_name,
				"period_number": pd.period_number,
				"period_start": str(pd.period_start) if pd.period_start else None,
				"period_end": str(pd.period_end) if pd.period_end else None,
				"actual_check_in": str(pd.actual_check_in) if pd.actual_check_in else None,
				"actual_check_out": str(pd.actual_check_out) if pd.actual_check_out else None,
				"working_hours": pd.working_hours,
				"late_minutes": pd.late_minutes,
				"early_exit_minutes": pd.early_exit_minutes,
				"absent_hours": pd.absent_hours,
				"overtime_hours": pd.overtime_hours,
				"period_status": pd.period_status,
			}
			for pd in att.period_details
		] if hasattr(att, 'period_details') and att.period_details else [],
	}


@frappe.whitelist()
def bulk_import_checkins(checkins_json):
	"""
	Bulk import checkins from a JSON array.
	checkins_json: JSON string or list of dicts with keys: employee_field_value, timestamp, device_id, log_type
	Returns: {created: int, duplicates: int, errors: list}
	"""
	import json

	if isinstance(checkins_json, str):
		try:
			checkins = json.loads(checkins_json)
		except json.JSONDecodeError:
			frappe.throw(_("Invalid JSON format"))
			return
	elif isinstance(checkins_json, list):
		checkins = checkins_json
	else:
		frappe.throw(_("checkins_json must be a JSON array"))
		return

	if not checkins:
		frappe.throw(_("No checkins provided"))

	if len(checkins) > 1000:
		frappe.throw(_("Maximum 1000 checkins per batch. Received {}").format(len(checkins)))

	result = {"created": 0, "duplicates": 0, "errors": []}

	for idx, item in enumerate(checkins):
		try:
			employee_field_value = item.get("employee_field_value") or item.get("employee") or item.get("employee_id")
			timestamp = item.get("timestamp") or item.get("time")
			device_id = item.get("device_id")
			log_type = item.get("log_type")

			if not employee_field_value or not timestamp:
				result["errors"].append({"index": idx, "error": "Missing employee_field_value or timestamp"})
				continue

			employee_fieldname = item.get("employee_fieldname", "attendance_device_id")

			# Resolve employee name from field value
			emp = frappe.db.get_values(
				"Employee",
				{employee_fieldname: employee_field_value},
				["name"],
				as_dict=True,
			)
			if not emp:
				result["errors"].append({"index": idx, "error": f"Employee not found for {employee_fieldname}={employee_field_value}"})
				continue
			employee_name = emp[0].name

			resolved_device_id = device_id
			if device_id:
				device = get_device_by_id(device_id)
				if device:
					resolved_device_id = device.name

			checkin = safe_create_checkin(
				employee=employee_name,
				timestamp=timestamp,
				log_type=log_type,
				device_id=device_id,
				skip_auto=0,
			)

			if checkin:
				result["created"] += 1
				if resolved_device_id and frappe.db.exists("Biometric Device", resolved_device_id):
					update_device_sync(resolved_device_id)
			else:
				result["duplicates"] += 1

		except Exception as e:
			result["errors"].append({"index": idx, "error": str(e)})

	frappe.db.commit()
	return result


@frappe.whitelist(allow_guest=False)
def approve_overtime(attendance_name, approved_overtime_hours=None):
	"""
	Approve overtime for an attendance record.
	Updates total_overtime_hours or approved_overtime_hours.
	"""
	if not attendance_name:
		frappe.throw(_("Attendance name is required"))

	if not frappe.has_permission("Attendance", "write"):
		frappe.throw(_("Insufficient permissions"))

	att = frappe.get_doc("Attendance", attendance_name)

	if att.docstatus != 1:
		frappe.throw(_("Can only approve overtime for submitted attendance"))

	current_overtime = getattr(att, 'total_overtime_hours', 0) or 0
	if current_overtime <= 0:
		frappe.throw(_("No overtime to approve for this attendance"))

	if approved_overtime_hours is not None:
		approved = float(approved_overtime_hours)
		if approved > current_overtime:
			frappe.throw(
				_("Approved overtime ({}) cannot exceed calculated overtime ({})").format(
					approved, current_overtime
				)
			)
	else:
		approved = current_overtime

	att.approved_overtime_hours = approved
	att.save(ignore_permissions=True)
	frappe.db.commit()

	return {
		"status": "approved",
		"attendance": att.name,
		"approved_overtime_hours": approved,
		"total_overtime_hours": current_overtime,
	}


@frappe.whitelist(allow_guest=False)
def bulk_approve_overtime(attendance_names, approved_hours_map=None):
	"""
	Bulk approve overtime for multiple attendance records.
	attendance_names: JSON list of attendance names
	approved_hours_map: optional JSON dict {attendance_name: hours}
	"""
	import json

	if isinstance(attendance_names, str):
		attendance_names = json.loads(attendance_names)
	if isinstance(approved_hours_map, str) and approved_hours_map:
		approved_hours_map = json.loads(approved_hours_map)

	if not attendance_names:
		frappe.throw(_("No attendance records provided"))

	results = []
	for name in attendance_names:
		try:
			hours = approved_hours_map.get(name) if approved_hours_map else None
			result = approve_overtime(name, hours)
			results.append(result)
		except Exception as e:
			results.append({"status": "error", "attendance": name, "error": str(e)})

	return {"results": results, "total": len(results)}


@frappe.whitelist(allow_guest=False)
def get_period_attendance_summary(employee, from_date, to_date):
	"""
	Get period-wise attendance summary for an employee over a date range.
	Used for payroll integration and reports.
	"""
	attendances = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [from_date, to_date]],
			"docstatus": 1,
		},
		fields=["name", "attendance_date", "shift_type", "status",
				"total_late_minutes", "total_overtime_hours", "approved_overtime_hours",
				"attendance_period_details"],
		order_by="attendance_date",
	)

	summary = {
		"employee": employee,
		"from_date": from_date,
		"to_date": to_date,
		"total_days": len(attendances),
		"present_days": 0,
		"absent_days": 0,
		"leave_days": 0,
		"half_days": 0,
		"total_late_minutes": 0,
		"total_overtime_hours": 0,
		"total_approved_overtime_hours": 0,
		"period_summary": {},
	}

	for att in attendances:
		if att.status == "Present":
			summary["present_days"] += 1
		elif att.status == "Absent":
			summary["absent_days"] += 1
		elif att.status == "On Leave":
			summary["leave_days"] += 1
		elif att.status == "Half Day":
			summary["half_days"] += 1

		summary["total_late_minutes"] += att.total_late_minutes or 0
		summary["total_overtime_hours"] += att.total_overtime_hours or 0
		summary["total_approved_overtime_hours"] += att.approved_overtime_hours or 0

		if att.attendance_period_details:
			try:
				import json
				details = json.loads(att.attendance_period_details) if isinstance(att.attendance_period_details, str) else att.attendance_period_details
				if isinstance(details, list):
					for d in details:
						if not isinstance(d, dict):
							continue
						pname = d.get("period_name", "Unknown")
						if pname not in summary["period_summary"]:
							summary["period_summary"][pname] = {
								"present": 0, "absent": 0, "late_minutes": 0, "overtime_minutes": 0
							}
						ps = summary["period_summary"][pname]
						pstatus = d.get("status", "")
						if pstatus == "Present":
							ps["present"] += 1
						elif pstatus == "Absent":
							ps["absent"] += 1
						ps["late_minutes"] += d.get("late_minutes", 0) or 0
						ps["overtime_minutes"] += d.get("overtime_minutes", 0) or 0
			except (ValueError, TypeError):
				pass

	return summary
