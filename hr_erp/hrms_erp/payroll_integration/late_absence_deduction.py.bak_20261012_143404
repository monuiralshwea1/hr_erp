# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
محرك خصم التأخير والغياب من الراتب — late_absence_deduction.py
================================================================

الميزة: خصم أوقات التأخير وأيام الغياب من قسيمة الراتب تلقائياً،
بنفس فكرة حساب الإضافي في تطبيق nl-attendance-timesheet لكن بالاتجاه المعاكس.

آلية العمل:
  1. يعمل كـ hook على حدث validate في Salary Slip (انظر hooks.py).
  2. يجمع دقائق التأخير من سجلات Attendance ضمن فترة القسيمة:
       - late_entry في Attendance (Check) → حضور متأخر
       - دقائق التأخير = in_time - (بداية الشفت + فترة السماح)
  3. يجمع أيام الغياب من Attendance (status = "Absent").
  4. يحسب المبلغ:
       خصم التأخير = hourly_rate × late_deduction_factor × (late_minutes / 60)
       خصم الغياب  = daily_rate  × absence_deduction_factor × absent_days
  5. يضيف سطر خصم في جدول Deductions داخل القسيمة.

الإيقاف: من DocType "HR ERP Payroll Settings" عطّل:
    enable_late_deduction  → يوقف خصم التأخير
    enable_absence_deduction → يوقف خصم الغياب
  أو احذف السطر من doc_events في hooks.py لإيقاف الميزة كلياً.

الإعدادات تُقرأ من "HR ERP Payroll Settings" (انظر HR_ERP_ADDITIONS_AR.md).
"""

import frappe
from frappe.utils import flt, getdate, get_datetime, cint

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"


def get_settings():
	"""قراءة الإعدادات من DocType الإعدادات الموحد."""
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return {}
	try:
		doc = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		return {
			"enable_late": cint(doc.get("enable_late_deduction")),
			"late_component": doc.get("late_deduction_component"),
			"late_factor": flt(doc.get("late_deduction_factor") or 1.0),
			"late_grace_override": cint(doc.get("late_grace_period_override") or 0),
			"enable_absence": cint(doc.get("enable_absence_deduction")),
			"absence_component": doc.get("absence_deduction_component"),
			"absence_factor": flt(doc.get("absence_deduction_factor") or 1.0),
			"working_days": cint(doc.get("working_days_per_month") or 30),
		}
	except Exception:
		return {}


# ----------------------------------------------------------------------
# Hook: Salary Slip validate
# ----------------------------------------------------------------------
def apply_late_absence_deduction(doc, method=None):
	"""Hook على Salary Slip.validate — يضيف خصومات التأخير والغياب."""
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	settings = get_settings()
	if not settings:
		return
	if not settings.get("enable_late") and not settings.get("enable_absence"):
		return

	employee = doc.get("employee")
	start_date = getdate(doc.get("start_date"))
	end_date = getdate(doc.get("end_date"))
	if not employee or not start_date or not end_date:
		return

	# --- حساب دقائق التأخير ---
	late_minutes = 0.0
	if settings.get("enable_late") and settings.get("late_component"):
		late_minutes = _calc_late_minutes(employee, start_date, end_date, settings)

	# --- حساب أيام الغياب ---
	absent_days = 0
	if settings.get("enable_absence") and settings.get("absence_component"):
		absent_days = _count_absent_days(employee, start_date, end_date)

	if late_minutes <= 0 and absent_days <= 0:
		return

	# --- حساب السعر ---
	base = flt(doc.get("base") or doc.get("gross_pay") or 0)
	working_days = settings.get("working_days") or 30
	daily_rate = base / working_days if working_days else 0
	# سعر الساعة = اليومي / ساعات الدوام (نقدّر 8 ساعات افتراضياً إن لم توجد)
	shift_hours = _get_shift_hours(doc) or 8.0
	hourly_rate = daily_rate / shift_hours if shift_hours else 0

	# --- إضافة سطور الخصم ---
	if late_minutes > 0 and settings.get("late_component"):
		late_amount = round(hourly_rate * settings["late_factor"] * (late_minutes / 60.0), 2)
		if late_amount > 0:
			_add_deduction_row(
				doc,
				settings["late_component"],
				late_amount,
				remark="خصم تأخير: {:.1f} دقيقة".format(late_minutes),
			)

	if absent_days > 0 and settings.get("absence_component"):
		absence_amount = round(daily_rate * settings["absence_factor"] * absent_days, 2)
		if absence_amount > 0:
			_add_deduction_row(
				doc,
				settings["absence_component"],
				absence_amount,
				remark="خصم غياب: {} يوم".format(absent_days),
			)


# ----------------------------------------------------------------------
# حساب دقائق التأخير
# ----------------------------------------------------------------------
def _calc_late_minutes(employee, start_date, end_date, settings):
	"""إجمالي دقائق التأخير = مجموع (in_time - بداية الشفت - فترة السماح)."""
	attendances = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [start_date, end_date]],
			"docstatus": 1,
			"status": ["in", ["Present", "Half Day", "Work From Home"]],
			"late_entry": 1,
		},
		fields=["name", "attendance_date", "in_time", "shift"],
	)

	total_late = 0.0
	for att in attendances:
		if not att.get("in_time"):
			continue
		in_dt = get_datetime(att["in_time"])

		# بداية الشفت وفترة السماح
		shift_start, grace = _get_shift_start_and_grace(att.get("shift"), in_dt, settings)
		if not shift_start:
			continue

		# حد التأخير المسموح = بداية الشفت + فترة السماح
		from datetime import timedelta
		allowed = shift_start + timedelta(minutes=grace)
		if in_dt > allowed:
			late_seconds = (in_dt - allowed).total_seconds()
			total_late += late_seconds / 60.0

	return round(total_late, 2)


def _get_shift_start_and_grace(shift_name, in_dt, settings):
	"""إرجاع (بداية الشفت كـ datetime, فترة السماح بالدقائق)."""
	if not shift_name:
		return None, 0

	try:
		shift = frappe.get_cached_doc("Shift Type", shift_name)
	except Exception:
		return None, 0

	start_time = shift.get("start_time")
	if not start_time:
		return None, 0

	from datetime import datetime, timedelta
	# فترة السماح: الإعداد العام يتجاوز إعداد الشفت إذا > 0
	grace = settings.get("late_grace_override") or cint(shift.get("late_entry_grace_period") or 0)

	# دمج تاريخ الحضور مع وقت بداية الشفت
	if hasattr(start_time, "total_seconds"):
		# timedelta
		sec = start_time.total_seconds()
		h, rem = divmod(int(sec), 3600)
		m, s = divmod(rem, 60)
		shift_start = datetime.combine(in_dt.date(), datetime.min.time()) + timedelta(
			hours=h, minutes=m, seconds=s
		)
	else:
		shift_start = datetime.combine(in_dt.date(), start_time)

	return shift_start, grace


def _get_shift_hours(doc):
	"""ساعات الشفت اليومية لتقدير سعر الساعة."""
	# نحاول من Salary Structure Assignment → Shift Type
	try:
		shift = frappe.db.get_value("Employee", doc.get("employee"), "default_shift")
		if shift:
			st = frappe.get_cached_doc("Shift Type", shift)
			start, end = st.get("start_time"), st.get("end_time")
			if start and end:
				from datetime import timedelta
				def to_sec(t):
					return t.total_seconds() if hasattr(t, "total_seconds") else 0
				diff = to_sec(end) - to_sec(start)
				if diff > 0:
					return diff / 3600.0
	except Exception:
		pass
	return 0


# ----------------------------------------------------------------------
# حساب أيام الغياب
# ----------------------------------------------------------------------
def _count_absent_days(employee, start_date, end_date):
	"""عدد أيام الغياب (status = Absent) ضمن الفترة."""
	rows = frappe.get_all(
		"Attendance",
		filters={
			"employee": employee,
			"attendance_date": ["between", [start_date, end_date]],
			"docstatus": 1,
			"status": "Absent",
		},
		fields=["name"],
	)
	return len(rows)


# ----------------------------------------------------------------------
# إضافة سطر خصم إلى القسيمة
# ----------------------------------------------------------------------
def _add_deduction_row(doc, component, amount, remark=""):
	"""إضافة أو تحديث سطر خصم في جدول Deductions."""
	# إذا كان المكوّن موجوداً مسبقاً، حدّث المبلغ بدل التكرار
	for row in doc.get("deductions") or []:
		if row.salary_component == component:
			row.amount = amount
			return

	doc.append(
		"deductions",
		{
			"salary_component": component,
			"amount": amount,
		},
	)
