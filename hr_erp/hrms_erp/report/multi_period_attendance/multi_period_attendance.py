# Copyright (c) 2026, Shumul. All rights reserved.
# Multi-Period Attendance Report
# Shows per-period attendance breakdown: shift name, period names, check-in/check-out per period
# الفترات تُحسب مباشرة من البصمات (Employee Checkin) بنفس منطق
# Biometric Period Attendance، ولا تعتمد على جدول Attendance Period Detail.
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate
from datetime import datetime, timedelta

try:
	from hr_erp.hrms_erp.report.biometric_period_attendance.biometric_period_attendance import (
		Punch,
		get_effective_periods,
		assign_punch_to_period,
		analyze_period,
		get_assignment_map,
		resolve_shift,
	)

	HAVE_PERIOD_LOGIC = True
except Exception:
	HAVE_PERIOD_LOGIC = False


def execute(filters=None):
	if not filters:
		filters = {}

	# عرض تفاصيل الفترات افتراضياً ما لم يُلغِ المستخدم الخيار صراحةً
	filters.setdefault("show_period_details", 1)

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


def _get_union_periods(shifts):
	"""اتحاد فترات عدة شفتات (بالاسم)، مرتبة حسب period_number."""
	seen = {}
	order = []
	for sh in shifts:
		for p in get_effective_periods(sh):
			name = p["period_name"]
			if name not in seen:
				seen[name] = p
				order.append(name)
	if not seen:
		return []
	return sorted([seen[n] for n in order], key=lambda p: (cint(p["period_number"] or 0), str(p["start_time"])))


def _get_shift_names(filters):
	"""الشفتات الموجودة فعلياً ضمن سجلات الحضور المفلترة."""
	conditions = ["a.docstatus = 1"]
	params = {}

	if filters.get("from_date"):
		conditions.append("a.attendance_date >= %(from_date)s")
		params["from_date"] = filters["from_date"]
	if filters.get("to_date"):
		conditions.append("a.attendance_date <= %(to_date)s")
		params["to_date"] = filters["to_date"]
	if filters.get("shift_type"):
		conditions.append("a.shift = %(shift_type)s")
		params["shift_type"] = filters["shift_type"]

	rows = frappe.db.sql(
		f"SELECT DISTINCT a.shift FROM `tabAttendance` a WHERE {' AND '.join(conditions)} AND a.shift IS NOT NULL",
		params,
		as_list=True,
	)
	return [r[0] for r in rows]


def get_period_columns(filters):
	columns = []
	shifts = _get_shift_names(filters)
	periods = _get_union_periods(shifts) if shifts else []

	for period in periods:
		safe_name = period["period_name"].replace(" ", "_")
		columns.append({
			"label": f"{period['period_name']} - دخول",
			"fieldname": f"period_{safe_name}_in",
			"fieldtype": "Data",
			"width": 100,
		})
		columns.append({
			"label": f"{period['period_name']} - خروج",
			"fieldname": f"period_{safe_name}_out",
			"fieldtype": "Data",
			"width": 100,
		})
		columns.append({
			"label": f"{period['period_name']} - تأخير (د)",
			"fieldname": f"period_{safe_name}_late",
			"fieldtype": "Data",
			"width": 90,
			"align": "center",
		})
		columns.append({
			"label": f"{period['period_name']} - حالة",
			"fieldname": f"period_{safe_name}_status",
			"fieldtype": "Data",
			"width": 80,
			"align": "center",
		})

	return columns


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

	if HAVE_PERIOD_LOGIC:
		try:
			return _build_rows_with_periods(filters, attendance_data)
		except Exception:
			frappe.log_error(frappe.get_traceback(), "Multi-Period Attendance: تعذر تطبيق منطق الفترات")

	# المسار الاحتياطي (قبل وجود hr_erp): الاعتماد على Attendance Period Detail
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

		key = f"{att.employee}|{getdate(att.attendance_date)}"
		checkins = employee_checkins.get(key, [])
		row["checkin_count"] = len(checkins)

		if filters.get("show_period_details"):
			period_details = _get_period_details(att.employee, att.attendance_date)
			if period_details:
				_parse_period_details(row, period_details)

		data.append(row)

	return data


def _build_rows_with_periods(filters, attendance_data):
	"""ملء تفاصيل الفترات من البصمات مباشرة (مسار hr_erp)."""
	pairs = sorted({(a.employee, getdate(a.attendance_date)) for a in attendance_data if a.employee})
	if not pairs:
		return []

	from_d = min(d for _, d in pairs)
	to_d = max(d for _, d in pairs)
	checkin_from = datetime.combine(from_d, datetime.min.time())
	checkin_to = datetime.combine(to_d + timedelta(days=1), datetime.max.time())

	checkins = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": ["in", [e for e, _ in pairs]],
			"time": ["between", [checkin_from.strftime("%Y-%m-%d %H:%M:%S"), checkin_to.strftime("%Y-%m-%d %H:%M:%S")]],
		},
		fields=["employee", "time", "log_type", "device_id", "shift"],
		order_by="employee,time",
	)
	punch_map = {}
	checkin_shift_by_date = {}
	for c in checkins:
		punch_map.setdefault(c.employee, []).append(Punch(c.time, c.log_type, c.device_id, source="biometric"))
		d = getdate(c.time)
		checkin_shift_by_date.setdefault(c.employee, {})
		if c.shift and d not in checkin_shift_by_date[c.employee]:
			checkin_shift_by_date[c.employee][d] = c.shift

	emp_names = [e for e, _ in pairs]
	emp_shifts = dict(
		frappe.get_all("Employee", filters={"name": ["in", emp_names]}, fields=["name", "default_shift"], as_list=True)
	)
	assignment_map = get_assignment_map(emp_names, from_d, to_d)

	data = []
	for att in attendance_data:
		emp = att.employee
		d = getdate(att.attendance_date)

		row = {
			"employee": emp,
			"employee_name": att.employee_name,
			"department": att.department,
			"attendance_date": att.attendance_date,
			"shift_type": att.shift,
			"status": att.status,
			"working_hours": att.working_hours or 0,
			"total_late_minutes": 0,
			"total_overtime_hours": att.total_overtime_hours or 0,
		}

		emp_punches = sorted(punch_map.get(emp, []), key=lambda l: l.time)
		row["checkin_count"] = len(emp_punches)

		shift_name = att.shift or resolve_shift(
			emp, d, assignment_map, checkin_shift_by_date, {emp: emp_shifts.get(emp)}
		)
		row["shift_type"] = shift_name or att.shift

		periods = [dict(p) for p in get_effective_periods(shift_name)]
		assignments = {p["period_number"]: [] for p in periods}
		for punch in emp_punches:
			pidx = assign_punch_to_period(punch, periods, d)
			if pidx is not None:
				assignments[pidx].append(punch)

		total_late = 0.0
		total_hours = 0.0
		any_check_in = False
		for p in periods:
			res = analyze_period(assignments[p["period_number"]], p, d)
			safe_name = p["period_name"].replace(" ", "_")
			row[f"period_{safe_name}_in"] = _fmt_time(res["check_in"])
			row[f"period_{safe_name}_out"] = _fmt_time(res["check_out"])
			row[f"period_{safe_name}_late"] = res["late_minutes"] if res["late_minutes"] else ""
			row[f"period_{safe_name}_status"] = res["status"]

			if res["check_in"]:
				any_check_in = True
				if res["check_out"]:
					total_hours += (res["check_out"] - res["check_in"]).total_seconds() / 3600.0
			total_late += flt(res["late_minutes"] or 0)

		row["total_late_minutes"] = round(total_late, 1) if total_late else 0
		if any_check_in and total_hours:
			row["working_hours"] = round(total_hours, 2)

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
		row[f"period_{safe_name}_late"] = detail.get("late_minutes") or ""


def _fmt_time(dt):
	if not dt:
		return ""
	if hasattr(dt, "strftime"):
		return dt.strftime("%H:%M")
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
			"labels": [_("Present"), _("Absent"), _("Leave"), _("Holiday")],
			"datasets": [{"values": [total_present, total_absent, total_leave, total_holiday]}],
		},
		"type": "donut",
		"colors": ["#28a745", "#dc3545", "#ffc107", "#6c757d"],
	}