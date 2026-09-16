# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
توليد سجلات الإضافي من الحضور — overtime_timesheet.py
=========================================================

منقول ومُكيَّف من تطبيق nl-attendance-timesheet ليعمل داخل hr_erp
(مرجع: https://github.com/navariltd/nl-attendance-timesheet).

آلية العمل:
  1. دالة whitelisted: generate_overtime_timesheets(start_date, end_date)
  2. تقرأ سجلات Attendance (Present) في النطاق.
  3. يوم العطلة الرسمية → Timesheet بنشاط Overtime 2.0
     غير ذلك إذا تجاوز الانصراف نهاية الدوام + Overtime Threshold → Overtime 1.5
  4. تنشئ مستند Timesheet مع سطر time_logs.

الإيقاف: من "HR ERP Payroll Settings" عطّل enable_overtime_generation.
  الدالة تتحقق من المفتاح قبل العمل.

الإعدادات من "HR ERP Payroll Settings":
  overtime_15_activity, overtime_20_activity, overtime_threshold,
  maximum_monthly_hours, include_early_entry
"""

import frappe
from frappe import _
from frappe.utils.data import get_datetime, nowdate
from datetime import datetime

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"


def _get_settings():
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return {}
	try:
		doc = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		return {
			"enabled": frappe.utils.cint(doc.get("enable_overtime_generation")),
			"overtime_15": doc.get("overtime_15_activity"),
			"overtime_20": doc.get("overtime_20_activity"),
			"threshold": frappe.utils.flt(doc.get("overtime_threshold") or 30),
			"max_monthly_hours": frappe.utils.flt(doc.get("maximum_monthly_hours") or 0),
			"include_early_entry": frappe.utils.cint(doc.get("include_early_entry")),
		}
	except Exception:
		return {}


@frappe.whitelist()
def generate_overtime_timesheets(start_date=None, end_date=None):
	"""توليد Timesheets للإضافي — زر/استدعاء يدوي."""
	start_date = start_date or nowdate()
	end_date = end_date or nowdate()

	settings = _get_settings()
	if not settings.get("enabled"):
		frappe.throw(_("Overtime generation is disabled in HR ERP Payroll Settings"))

	overtime_15 = settings.get("overtime_15")
	overtime_20 = settings.get("overtime_20")
	if not overtime_15 or not overtime_20:
		frappe.throw(
			_("Please set up both Overtime 1.5 and Overtime 2.0 activities in HR ERP Payroll Settings")
		)

	attendance = frappe.qb.DocType("Attendance")
	employee = frappe.qb.DocType("Employee")
	shift_type = frappe.qb.DocType("Shift Type")

	conditions = [
		attendance.docstatus == 1,
		attendance.status == "Present",
		attendance.attendance_date[start_date:end_date],
	]

	from pypika import Criterion

	query = (
		frappe.qb.from_(attendance)
		.inner_join(employee)
		.on(employee.name == attendance.employee)
		.left_join(shift_type)
		.on(attendance.shift == shift_type.name)
		.select(
			attendance.employee.as_("employee"),
			attendance.employee_name.as_("employee_name"),
			attendance.name.as_("name"),
			attendance.shift.as_("shift"),
			attendance.attendance_date.as_("attendance_date"),
			attendance.in_time.as_("in_time"),
			attendance.out_time.as_("out_time"),
			attendance.working_hours.as_("working_hours"),
			employee.holiday_list.as_("holiday_list"),
			employee.company.as_("company"),
			employee.department.as_("department"),
			shift_type.start_time.as_("shift_start_time"),
			shift_type.end_time.as_("shift_end_time"),
			shift_type.unpaid_breaks_minutes.as_("unpaid_breaks_minutes"),
		)
		.where(Criterion.all(conditions))
	)

	attendance_records = query.run(as_dict=True)
	created = 0

	for entry in attendance_records:
		if entry.get("holiday_list"):
			holiday_dates = frappe.db.get_all(
				"Holiday", filters={"parent": entry.holiday_list}, pluck="holiday_date"
			)
			if entry.attendance_date in holiday_dates:
				hours = _calc_holiday_hours(entry)
				if hours:
					_create_timesheet(entry, overtime_20, entry.in_time, hours)
					created += 1
				continue

		from_time, hours = _get_from_time_and_hours(entry, settings)
		if from_time and hours:
			_create_timesheet(entry, overtime_15, from_time, hours)
			created += 1

	frappe.db.commit()
	return {"message": _("Generated {} overtime timesheets").format(created), "count": created}


def _calc_holiday_hours(entry):
	"""ساعات العمل في يوم عطلة رسمية = working_hours - خصومات."""
	if entry.out_time and entry.shift_start_time:
		in_time_dt = datetime.strptime(str(entry.in_time).split(".")[0], "%Y-%m-%d %H:%M:%S")
		shift_start_time_dt = datetime.combine(
			in_time_dt.date(),
			datetime.strptime(str(entry.shift_start_time), "%H:%M:%S").time(),
		)
		if in_time_dt < shift_start_time_dt:
			extra = (
				shift_start_time_dt.hour - in_time_dt.hour
				+ (shift_start_time_dt.minute - in_time_dt.minute) / 60
				+ (shift_start_time_dt.second - in_time_dt.second) / 3600
			)
			entry.working_hours -= extra

		entry.working_hours -= (entry.unpaid_breaks_minutes or 0) / 60
		return max(0, entry.working_hours)
	return 0


def _get_from_time_and_hours(entry, settings):
	"""حساب وقت بداية الإضافي وعدد الساعات (Overtime 1.5)."""
	if entry.out_time and entry.shift_end_time:
		check_out_time = datetime.strptime(str(entry.out_time).split(".")[0], "%Y-%m-%d %H:%M:%S").time()
		shift_end_time = datetime.strptime(str(entry.shift_end_time), "%H:%M:%S").time()

		if check_out_time > shift_end_time:
			overtime_minutes = ((check_out_time.hour - shift_end_time.hour) * 60) + (
				check_out_time.minute - shift_end_time.minute
			)
			if overtime_minutes > settings.get("threshold", 30):
				sec = entry.shift_end_time.total_seconds()
				h, rem = divmod(int(sec), 3600)
				m, s = divmod(rem, 60)
				shift_end = get_datetime(f"{h}:{m}:{s}").time()
				from_time = datetime.combine(entry.attendance_date, shift_end)
				return from_time, overtime_minutes / 60
	return None, None


def _create_timesheet(entry, overtime_type, from_time, hours):
	"""إنشاء مستند Timesheet للإضافي."""
	ts = frappe.new_doc("Timesheet")
	ts.employee = entry.employee
	ts.company = entry.company
	ts.department = entry.department
	ts.employee_name = entry.employee_name
	# ربط بالحضور إذا وُجد الحقل المخصص
	if frappe.get_meta("Timesheet").has_field("attendance"):
		ts.attendance = entry.name

	ts.append(
		"time_logs",
		{
			"activity_type": overtime_type,
			"description": overtime_type,
			"from_time": from_time,
			"hours": hours,
			"completed": 1,
		},
	)
	ts.insert(
		ignore_permissions=True,
		ignore_links=True,
		ignore_if_duplicate=True,
		ignore_mandatory=True,
	)
