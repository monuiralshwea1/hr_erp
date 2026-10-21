# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
إعادة احتساب خصومات التأخير والغياب على قسائم الرواتب — Monthly Regenerator
=========================================================================

يعالج القسائم المُقدَّمة (Submitted) التي أُنشئت قبل تفعيل ميزة خصم التأخير
والغياب، فيعيد احتساب سطور الخصم والإجماليات ويحدّثها في قاعدة البيانات
دون لمس حالة القسيمة (تبقى Submitted ولا تُنتج قيوداً محاسبية جديدة).

الخصائص:
  - يعمل شهرياً: يقبل نطاق تواريخ ويقسّمه إلى أشهر ميلادية.
  - يتخطى تلقائياً الأشهر التي لا تحتوي بيانات حضور صالحة (Present/Half Day)،
    لتجنّب خصم أشهر بياناتها تجريبية أو فارغة.
  - يدعم dry-run (apply=0) لعرض الأثر قبل التنفيذ.

التشغيل عبر bench:
  # تجربة (بدون تنفيذ) لشهر سابق:
  bench --site site1.local execute hr_erp.hrms_erp.payroll_integration.slip_deduction_regenerator.execute --kwargs "{'from_date':'2026-08-01','to_date':'2026-08-31','apply':0}"

  # تنفيذ فعلي لشهر أغسطس 2026:
  bench --site site1.local execute hr_erp.hrms_erp.payroll_integration.slip_deduction_regenerator.execute --kwargs "{'from_date':'2026-08-01','to_date':'2026-08-31','apply':1}"

  # تنفيذ نطاق كامل (يتخطى الأشهر بلا حضور):
  bench --site site1.local execute hr_erp.hrms_erp.payroll_integration.slip_deduction_regenerator.execute --kwargs "{'from_date':'2026-01-01','to_date':'2026-12-31','apply':1}"

  # بلا وسائط: يعالج الشهر السابق فقط تلقائياً:
  bench --site site1.local execute hr_erp.hrms_erp.payroll_integration.slip_deduction_regenerator.execute
"""

import frappe
from frappe.utils import (
	flt,
	getdate,
	get_first_day,
	get_last_day,
	add_months,
	nowdate,
)

from hr_erp.hrms_erp.payroll_integration.late_absence_deduction import (
	apply_late_absence_deduction,
	get_settings,
)

PARENT_FIELDS = [
	"total_late_minutes",
	"total_absent_days",
	"gross_pay",
	"base_gross_pay",
	"total_deduction",
	"base_total_deduction",
	"net_pay",
	"rounded_total",
	"base_net_pay",
	"base_rounded_total",
	"total_in_words",
	"base_total_in_words",
]

PRESENT_STATUSES = ("Present", "Work From Home", "Half Day")


def _parent_fields():
	meta = frappe.get_meta("Salary Slip")
	return [field for field in PARENT_FIELDS if meta.has_field(field)]


def month_has_valid_attendance(from_date, to_date):
	"""هل يوجد حضور فعلي (Present/Half Day) في المدى؟ يُستخدم لتخطي الأشهر الفارغة."""
	count = frappe.db.sql(
		"""
		select count(*)
		from `tabAttendance`
		where attendance_date between %s and %s
		  and docstatus = 1
		  and status in %s
		""",
		(from_date, to_date, PRESENT_STATUSES),
	)[0][0]
	return bool(count)


def get_slips_in_range(from_date, to_date):
	"""القسائم المُقدَّمة التي تتقاطع مع المدى المحدد."""
	return frappe.get_all(
		"Salary Slip",
		filters={
			"start_date": ["<=", to_date],
			"end_date": [">=", from_date],
			"docstatus": 1,
		},
		fields=["name", "employee", "start_date", "end_date", "gross_pay"],
		order_by="employee asc, start_date asc",
	)


def recalculate_slip(
	doc,
	apply=False,
	late_component=None,
	absence_component=None,
	parent_fields=None,
):
	"""إعادة احتساب خصومات قسيمة واحدة.

	تستخدم نفس منطق الـhook المستخدم عند إنشاء كشف الراتب، فتكون النتيجة
	مطابقة تماماً لما سيُحسب مستقبلاً (عملية idempotent: سطر الخصم يُحدَّث
	ولا يُضاف سطر جديد).

	المعاملات:
		doc              : مستند كشف الراتب
		apply            : True = كتابة القيم في قاعدة البيانات
		parent_fields    : الحقول التي تُكتب على كشف الراتب (تُحسب تلقائياً إن لم تُمرَّر)

	يُعيد قاموساً فيه: late_minutes, absent_days, late_deduction, absence_deduction.
	"""
	settings = get_settings()
	late_component = late_component or settings.get("late_component")
	absence_component = absence_component or settings.get("absence_component")
	parent_fields = parent_fields if parent_fields is not None else _parent_fields()

	apply_late_absence_deduction(doc)

	row_amounts = {}
	for row in doc.deductions or []:
		if row.salary_component in (late_component, absence_component):
			row_amounts[row.salary_component] = flt(row.amount)
			if apply:
				frappe.db.set_value(
					"Salary Detail", row.name, "amount", flt(row.amount), update_modified=False
				)

	if apply:
		fields = {field: doc.get(field) for field in parent_fields}
		frappe.db.set_value("Salary Slip", doc.name, fields, update_modified=False)

	return {
		"late_minutes": flt(doc.get("total_late_minutes")),
		"absent_days": flt(doc.get("total_absent_days")),
		"late_deduction": row_amounts.get(late_component, 0.0),
		"absence_deduction": row_amounts.get(absence_component, 0.0),
	}


def recalculate_slips(from_date, to_date, apply=False):
	"""إعادة احتساب الخصومات لقسائم المدى.

	apply=False → معاينة فقط (dry-run) دون كتابة.
	يُعيد قاموس ملخّص مجمّع.
	"""
	settings = get_settings()
	late_component = settings.get("late_component")
	absence_component = settings.get("absence_component")
	parent_fields = _parent_fields()

	slips = get_slips_in_range(from_date, to_date)

	summary = {
		"from_date": str(from_date),
		"to_date": str(to_date),
		"slips": len(slips),
		"updated": 0,
		"late_minutes": 0.0,
		"absent_days": 0.0,
		"late_deduction": 0.0,
		"absence_deduction": 0.0,
		"samples": [],
	}

	for slip in slips:
		doc = frappe.get_doc("Salary Slip", slip.name)
		result = recalculate_slip(
			doc,
			apply=apply,
			late_component=late_component,
			absence_component=absence_component,
			parent_fields=parent_fields,
		)

		late_amount = result.get("late_deduction", 0.0)
		absence_amount = result.get("absence_deduction", 0.0)

		summary["updated"] += 1
		summary["late_minutes"] += flt(doc.get("total_late_minutes"))
		summary["absent_days"] += flt(doc.get("total_absent_days"))
		summary["late_deduction"] += late_amount
		summary["absence_deduction"] += absence_amount

		if late_amount or absence_amount:
			summary["samples"].append(
				{
					"slip": doc.name,
					"employee": doc.employee,
					"late_minutes": flt(doc.get("total_late_minutes")),
					"absent_days": flt(doc.get("total_absent_days")),
					"late_deduction": late_amount,
					"absence_deduction": absence_amount,
					"gross_pay": flt(doc.get("gross_pay")),
					"total_deduction": flt(doc.get("total_deduction")),
					"net_pay": flt(doc.get("net_pay")),
				}
			)

	if apply:
		frappe.db.commit()

	return summary


def _iter_months(from_date, to_date):
	"""تقسيم المدى إلى أشهر ميلادية (أول يوم, آخر يوم)."""
	start = getdate(from_date)
	end = getdate(to_date)
	cursor = getdate(get_first_day(start))

	while cursor <= end:
		month_start = cursor
		month_end = getdate(get_last_day(cursor))
		yield max(month_start, start), min(month_end, end)
		cursor = getdate(add_months(cursor, 1))


def execute(from_date=None, to_date=None, apply=1, skip_invalid_months=1, verbose=1):
	"""نقطة الدخول لتشغيل bench execute.

	from_date / to_date : نطاق التاريخ (بلا وسائط → الشهر السابق).
	apply               : 1 تنفيذ فعلي، 0 معاينة فقط.
	skip_invalid_months : 1 تخطي الأشهر بلا حضور فعلي.
	"""
	apply = int(apply) if str(apply).strip() else 1
	skip_invalid_months = int(skip_invalid_months) if str(skip_invalid_months).strip() else 1

	if not from_date or not to_date:
		today = getdate(nowdate())
		prev_month = getdate(add_months(get_first_day(today), -1))
		from_date = get_first_day(prev_month)
		to_date = get_last_day(prev_month)

	results = {"apply": bool(apply), "months": [], "processed": 0, "skipped": 0}

	for month_from, month_to in _iter_months(from_date, to_date):
		label = month_from.strftime("%Y-%m")

		if skip_invalid_months and not month_has_valid_attendance(month_from, month_to):
			results["skipped"] += 1
			if verbose:
				print("[{0}] SKIPPED — لا يوجد حضور فعلي في هذا الشهر.".format(label))
			continue

		summary = recalculate_slips(month_from, month_to, apply=bool(apply))
		results["processed"] += 1
		results["months"].append(summary)

		if verbose:
			print(
				"[{0}] slips={1} updated={2} late_min={3} absent_days={4} "
				"late_amt={5} absence_amt={6}{7}".format(
					label,
					summary["slips"],
					summary["updated"],
					round(summary["late_minutes"], 1),
					round(summary["absent_days"], 1),
					round(summary["late_deduction"], 2),
					round(summary["absence_deduction"], 2),
					"" if apply else "  (معاينة)",
				)
			)

	if verbose:
		print("---")
		print(
			"الأشهر المُعالجة: {0} | المُتخطّاة: {1} | الوضع: {2}".format(
				results["processed"], results["skipped"], "تنفيذ" if apply else "معاينة"
			)
		)

	return results
