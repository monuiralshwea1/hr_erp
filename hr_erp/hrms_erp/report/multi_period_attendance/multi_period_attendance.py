# Copyright (c) 2026, Shumul. All rights reserved.
# Multi-Period Attendance Report
# Shows per-period attendance breakdown: shift name, period names, check-in/check-out per period
import frappe
from frappe import _


def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters)
	chart = get_chart(data) if data else None

	return columns, data, None, chart


def get_columns(filters):
	columns = [
		{"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 90},
		{"label": _("Employee Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
		{"label": _("Department"), "fieldname": "department", "fieldtype": "Link", "options": "Department", "width": 100},
		{"label": _("Date"), "fieldname": "attendance_date", "fieldtype": "Date", "width": 90},
		{"label": "الدوام", "fieldname": "shift_type", "fieldtype": "Link", "options": "Shift Type", "width": 120},
		{"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 70},
		{"label": "ساعات العمل", "fieldname": "working_hours", "fieldtype": "Float", "width": 80},
		{"label": "التأخر (دقيقة)", "fieldname": "total_late_minutes", "fieldtype": "Float", "width": 80},
		{"label": "الإضافي (ساعة)", "fieldname": "total_overtime_hours", "fieldtype": "Float", "width": 80},
	]

	if filters.get("show_period_details"):
		period_columns = get_period_columns(filters)
		columns.extend(period_columns)
	else:
		columns.append({"label": _("Checkins"), "fieldname": "checkin_count", "fieldtype": "Int", "width": 70})

	return columns


def get_period_columns(filters):
	columns = []
	shift_type = _get_shift_type(filters)

	if shift_type:
		periods = frappe.get_all(
			"Shift Period",
			filters={"parent": shift_type},
			fields=["period_name", "start_time", "end_time", "is_break"],
			order_by="start_time",
		)

		for period in periods:
			safe_name = period.period_name.replace(" ", "_")
			if period.is_break:
				columns.append({
					"label": f"{period.period_name}",
					"fieldname": f"period_{safe_name}_status",
					"fieldtype": "Data",
					"width": 90,
					"align": "center",
				})
			else:
				columns.append({
					"label": f"{period.period_name} - دخول",
					"fieldname": f"period_{safe_name}_in",
					"fieldtype": "Data",
					"width": 100,
				})
				columns.append({
					"label": f"{period.period_name} - خروج",
					"fieldname": f"period_{safe_name}_out",
					"fieldtype": "Data",
					"width": 100,
				})
				columns.append({
					"label": f"{period.period_name} - حالة",
					"fieldname": f"period_{safe_name}_status",
					"fieldtype": "Data",
					"width": 80,
					"align": "center",
				})

	return columns


def _get_shift_type(filters):
	shift_type = filters.get("shift_type")
	if shift_type:
		return shift_type

	shift_types = frappe.get_all(
		"Shift Period",
		fields=["parent"],
		group_by="parent",
		limit_page_length=1,
	)
	if shift_types:
		return shift_types[0].parent
	return None


def get_data(filters):
	conditions = get_conditions(filters)

	attendance_data = frappe.db.sql(
		"""
		SELECT
			a.employee,
			a.employee_name,
			a.department,
			a.attendance_date,
			a.shift,
			a.status,
			a.working_hours,
			a.total_late_minutes,
			a.total_overtime_hours
		FROM `tabAttendance` a
		WHERE a.docstatus = 1
			AND {conditions}
		ORDER BY a.employee, a.attendance_date
		""".format(conditions=conditions),
		filters,
		as_dict=True,
	)

	if not attendance_data:
		return []

	employee_checkins = _get_checkins_for_date_range(filters)
	data = []

	for att in attendance_data:
		row = {
			"employee": att.employee,
			"employee_name": att.employee_name,
			"department": att.department,
			"attendance_date": att.attendance_date,
			"shift_type": att.shift,
			"status": att.status,
			"working_hours": att.working_hours or 0,
			"total_late_minutes": att.total_late_minutes or 0,
			"total_overtime_hours": att.total_overtime_hours or 0,
		}

		key = f"{att.employee}|{att.attendance_date}"
		checkins = employee_checkins.get(key, [])
		row["checkin_count"] = len(checkins)

		if filters.get("show_period_details"):
			period_details = _get_period_details(att.employee, att.attendance_date)
			if period_details:
				_parse_period_details(row, period_details)

		data.append(row)

	return data


def _get_checkins_for_date_range(filters):
	params = {
		"from_date": filters.get("from_date"),
		"to_date": filters.get("to_date"),
	}

	employee_clause = ""
	if filters.get("employee"):
		employee_clause = "AND employee = %(employee)s"
		params["employee"] = filters["employee"]

	checkins = frappe.db.sql(
		"""
		SELECT
			employee,
			DATE(time) as checkin_date,
			time,
			log_type,
			shift
		FROM `tabEmployee Checkin`
		WHERE DATE(time) BETWEEN %(from_date)s AND %(to_date)s
			{employee_clause}
		ORDER BY employee, time
		""".format(employee_clause=employee_clause),
		params,
		as_dict=True,
	)

	result = {}
	for c in checkins:
		key = f"{c.employee}|{c.checkin_date}"
		if key not in result:
			result[key] = []
		result[key].append(c)

	return result


def _get_period_details(employee, attendance_date):
	att_name = frappe.db.get_value(
		"Attendance",
		{"employee": employee, "attendance_date": attendance_date, "docstatus": 1},
		"name",
	)
	if not att_name:
		return None

	details = frappe.db.sql(
		"""
		SELECT period_name, period_number, period_status as status,
		       late_minutes, early_exit_minutes, absent_hours, overtime_hours,
		       working_hours, actual_check_in, actual_check_out
		FROM `tabAttendance Period Detail`
		WHERE parent = %s
		ORDER BY period_number
		""",
		(att_name,),
		as_dict=True,
	)
	return details if details else None


def _parse_period_details(row, details):
	if not details or not isinstance(details, list):
		return

	for detail in details:
		if not isinstance(detail, dict):
			continue

		period_name = detail.get("period_name", "")
		safe_name = period_name.replace(" ", "_")
		status = detail.get("status", "")
		check_in = detail.get("actual_check_in")
		check_out = detail.get("actual_check_out")

		row[f"period_{safe_name}_status"] = status
		row[f"period_{safe_name}_in"] = _fmt_time(check_in)
		row[f"period_{safe_name}_out"] = _fmt_time(check_out)


def _fmt_time(dt):
	if not dt:
		return ""
	from frappe.utils import format_time
	try:
		return format_time(dt, "HH:mm")
	except Exception:
		return str(dt)[-8:] if len(str(dt)) > 8 else str(dt)


def get_conditions(filters):
	conditions = ["1=1"]

	if filters.get("from_date"):
		conditions.append("a.attendance_date >= %(from_date)s")

	if filters.get("to_date"):
		conditions.append("a.attendance_date <= %(to_date)s")

	if filters.get("employee"):
		conditions.append("a.employee = %(employee)s")

	if filters.get("department"):
		conditions.append("a.department = %(department)s")

	if filters.get("company"):
		conditions.append("a.company = %(company)s")

	if filters.get("shift_type"):
		conditions.append("a.shift = %(shift_type)s")

	if filters.get("status"):
		conditions.append("a.status = %(status)s")

	return " AND ".join(conditions)


def get_chart(data):
	if not data:
		return None

	total_present = sum(1 for d in data if d.get("status") == "Present")
	total_absent = sum(1 for d in data if d.get("status") == "Absent")
	total_leave = sum(1 for d in data if d.get("status") == "On Leave")
	total_holiday = sum(1 for d in data if d.get("status") == "Holiday")

	return {
		"data": {
			"labels": ["Present", "Absent", "Leave", "Holiday"],
			"datasets": [{"values": [total_present, total_absent, total_leave, total_holiday]}],
		},
		"type": "donut",
		"colors": ["#28a745", "#dc3545", "#ffc107", "#6c757d"],
	}
