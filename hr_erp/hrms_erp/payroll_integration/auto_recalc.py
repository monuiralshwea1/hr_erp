# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
إعادة الاحتساب التلقائية لخصومات التأخير والغياب — auto_recalc.py
=====================================================================

الفكرة:
  لكل شهر نحسب "بصمة" لبيانات الحضور (Attendance). إذا تغيّرت البصمة بعد آخر
  إعادة احتساب، فاعلم أن الخصومات في كشوف الرواتب أصبحت قديمة ⇒ نعيد احتسابها.

لماذا البصمة (fingerprint)؟
  - تكشف أي تغيير في المصدر: بصمة جديدة، تحضير يدوي، تعديل على سجل حضور،
    حذف سجل، أو تصحيح بيانات.
  - تجعل العملية idempotent: تشغيلها مرتين بلا تغيير ⇒ لا عمل ولا ازدواج.
  - أرخص من مقارنة كل حقل: استعلام واحد لكل نطاق تاريخي.

لماذا لا نلمس قيود المحاسبة؟
  الأداة تكتب amounts داخل كشف الراتب فقط (Salary Detail + الحقول)، ولا تنشئ
  أي قيد في General Ledger — لذلك لا تتأثر دفاتر الأستاذ ولا تُفسَد أرصدة
  المدينين/الدائنین. إعادة الاعتماد (re-submit) تبقى قراراً منفصلاً.

التشغيل:
  - تلقائياً: من مهمة مجدولة كل ساعة (hooks.py → scheduler_events).
  - فوراً بعد استيراد بصمة تاريخية: biostar_sync.get_employee_checkins.
  - فوراً بعد تحضير/تعديل حضور: doc_event على Attendance (mark_month_dirty).
  - يدوياً: من زر "Reconcile Deductions" في كشف الراتب، أو:
      bench --site <SITE> execute \
        hr_erp.hrms_erp.payroll_integration.auto_recalc.execute \
        --kwargs "{'apply':1,'lookback_months':24}"
"""

import frappe
from frappe import _
from frappe.utils import add_days, cstr, get_datetime, getdate, now_datetime

from hr_erp.hrms_erp.payroll_integration.late_absence_deduction import get_settings
from hr_erp.hrms_erp.payroll_integration.slip_deduction_regenerator import (
	month_has_valid_attendance,
	recalculate_slip,
)

LOG_DOCTYPE = "Payroll Deduction Recalc Log"
FINGERPRINT_FIELD = "audit_recalc_fingerprint"
LAST_RECALC_FIELD = "audit_last_recalc_at"
DIRTY_KEY_PREFIX = "payroll_recalc_dirty"

# الحالة (شهر فاسد) تُحفظ في Redis بمفتاح per company + شهر
DIRTY_TTL = 60 * 60 * 24 * 7

# الحدّ الافتراضي لنسبة الغياب المسموحة (يُضبط من الإعدادات)
DEFAULT_ABSENCE_QUALITY_LIMIT = 50

# الحدّ الأدنى لعدد سجلات الحضور حتى تُطبَّق قاعدة الجودة
MIN_RECORDS_FOR_QUALITY_CHECK = 20

# الحركات التي تعني أن بيانات الشهر تغيّرت
ATTENDANCE_STATUSES = ("Present", "Half Day", "Work From Home", "Absent", "On Leave", "Holiday")


# ----------------------------------------------------------------------
# البصمة
# ----------------------------------------------------------------------
def get_attendance_fingerprint(from_date, to_date):
	"""بصمة بيانات الحضور في مدى زمني.

	تتغيّر عند أي إضافة/تعديل/حذف لسجل حضور داخل المدى.
	"""
	rows = frappe.db.sql(
		"""
		select
			count(*) as total,
			sum(case when status = 'Present' then 1 else 0 end) as present,
			sum(case when status = 'Half Day' then 1 else 0 end) as half_day,
			sum(case when status = 'Absent' then 1 else 0 end) as absent,
			sum(case when in_time is not null then 1 else 0 end) as with_in_time,
			sum(ifnull(total_late_minutes, 0)) as late_minutes,
			sum(case when late_entry = 1 then 1 else 0 end) as late_entries,
			date_format(max(modified), '%%Y%%m%%d%%H%%i%%s') as last_modified
		from `tabAttendance`
		where docstatus = 1
		  and attendance_date between %s and %s
		""",
		(from_date, to_date),
		as_dict=True,
	)
	r = rows[0] if rows else None
	if not r or not r.get("total"):
		return "empty"

	return "t{total}|p{present}|h{half_day}|a{absent}|i{with_in_time}|l{late_minutes}|e{late_entries}|m{last_modified}".format(
		total=int(r["total"] or 0),
		present=int(r["present"] or 0),
		half_day=int(r["half_day"] or 0),
		absent=int(r["absent"] or 0),
		with_in_time=int(r["with_in_time"] or 0),
		late_minutes=int(r["late_minutes"] or 0),
		late_entries=int(r["late_entries"] or 0),
		last_modified=r["last_modified"] or "",
	)


def _slip_fingerprint_field():
	"""هل حقل البصمة موجود على كشف الراتب؟"""
	if not frappe.db.exists("Custom Field", {"dt": "Salary Slip", "fieldname": FINGERPRINT_FIELD}):
		return False
	return True


# ----------------------------------------------------------------------
# فحص جودة بيانات الحضور (حماية من الخصم الخاطئ)
# ----------------------------------------------------------------------
def get_absence_quality_limit():
	"""حدّ نسبة الغياب المسموحة (نسبة مئوية) من الإعدادات."""
	limit = DEFAULT_ABSENCE_QUALITY_LIMIT
	try:
		settings = frappe.get_cached_doc("HR ERP Payroll Settings")
		value = settings.get("absence_data_quality_limit")
		if value not in (None, ""):
			limit = frappe.utils.flt(value)
	except Exception:
		pass
	return limit or DEFAULT_ABSENCE_QUALITY_LIMIT


def check_attendance_quality(from_date, to_date):
	"""يفحص بيانات الحضور في المدى: نسبة غياب غير منطقية ⇐ بيانات مولّدة تلقائياً.

	يُرجع (سليم, رسالة).
	"""
	rows = frappe.db.sql(
		"""
		select
			count(*) as total,
			sum(case when status in ('Present', 'Half Day', 'Work From Home') then 1 else 0 end) as good,
			sum(case when status = 'Absent' then 1 else 0 end) as absent
		from `tabAttendance`
		where docstatus = 1 and attendance_date between %s and %s
		""",
		(from_date, to_date),
		as_dict=True,
	)
	r = rows[0] if rows else None
	total = int((r or {}).get("total") or 0)
	absent = int((r or {}).get("absent") or 0)
	good = int((r or {}).get("good") or 0)

	if total < MIN_RECORDS_FOR_QUALITY_CHECK:
		return True, None

	ratio = (absent * 100.0) / total
	limit = get_absence_quality_limit()

	if ratio > limit:
		return False, _(
			"Absence ratio {0}% exceeds the quality limit {1}% - the attendance data looks "
			"auto-generated (no biometric check-ins). Month skipped to avoid wrong deductions."
		).format(round(ratio, 1), limit)

	if good == 0 and absent > 0:
		return False, _(
			"No real attendance in this period (all records are absences) - month skipped."
		)

	return True, None


# ----------------------------------------------------------------------
# تحديد القسائم التي تحتاج تحديثاً
# ----------------------------------------------------------------------
def get_stale_slips(from_date, to_date, fingerprint):
	"""القسائم المُرسَلة التي بصمتها المخزَّنة مختلفة عن البصمة الحالية."""
	slips = frappe.get_all(
		"Salary Slip",
		filters={
			"docstatus": 1,
			"start_date": ["<=", to_date],
			"end_date": [">=", from_date],
		},
		fields=["name", FINGERPRINT_FIELD],
		ignore_permissions=True,
	)
	return [s for s in slips if (s.get(FINGERPRINT_FIELD) or "") != fingerprint]


# ----------------------------------------------------------------------
# تنفيذ إعادة الاحتساب
# ----------------------------------------------------------------------
def recalculate_range(
	from_date,
	to_date,
	apply=1,
	company=None,
	reason="",
	only_stale=True,
	verbose=1,
	force=0,
):
	"""إعادة احتساب خصومات النطاق الزمني.

	apply      : 1 تنفيذ فعلي وكتابة | 0 معاينة فقط
	only_stale : True ⇒ لا يعيد الاحتساب إلا إذا تغيّرت بصمة بيانات الحضور
	force      : 1 تجاوز فحص جودة البيانات (استخدام واعٍ)
	"""
	from_date = getdate(from_date)
	to_date = getdate(to_date)

	if not _slip_fingerprint_field():
		return {
			"ok": False,
			"message": _(
				"Custom field `{0}` is missing on Salary Slip - run `bench --site <site> migrate` first."
			).format(FINGERPRINT_FIELD),
		}

	settings = get_settings()
	if not settings:
		return {"ok": False, "message": _("HR ERP Payroll Settings is not available yet.")}

	if not settings.get("enable_late") and not settings.get("enable_absence"):
		return {"ok": False, "message": _("Late/Absence deductions are disabled in the settings.")}

	fingerprint = get_attendance_fingerprint(from_date, to_date)
	has_attendance = month_has_valid_attendance(from_date, to_date)

	summary = {
		"ok": True,
		"from_date": str(from_date),
		"to_date": str(to_date),
		"fingerprint": fingerprint,
		"slips_scanned": 0,
		"slips_pending": 0,
		"slips_updated": 0,
		"late_minutes": 0.0,
		"absent_days": 0.0,
		"late_deduction": 0.0,
		"absence_deduction": 0.0,
		"skipped": False,
		"reason": reason,
	}

	if not has_attendance:
		summary["skipped"] = True
		summary["message"] = _("No real attendance in this period - skipped.")
		_log(summary, company=company, status="Skipped")
		return summary

	# حماية من الخصم الخاطئ: نسبة غياب غير منطقية ⇐ بيانات مولّدة تلقائياً (لا بصمة)
	if not force:
		quality_ok, quality_message = check_attendance_quality(from_date, to_date)
		if not quality_ok:
			summary["skipped"] = True
			summary["message"] = quality_message
			_log(summary, company=company, status="Skipped")
			return summary

	slips = frappe.get_all(
		"Salary Slip",
		filters={
			"docstatus": 1,
			"start_date": ["<=", to_date],
			"end_date": [">=", from_date],
		},
		fields=["name", FINGERPRINT_FIELD],
		ignore_permissions=True,
	)
	summary["slips_scanned"] = len(slips)

	stale = slips if not only_stale else [
		s for s in slips if (s.get(FINGERPRINT_FIELD) or "") != fingerprint
	]
	if only_stale and not stale:
		summary["message"] = _("Nothing changed - all slips are up to date.")
		_log(summary, company=company, status="No Change")
		return summary

	summary["slips_pending"] = len(stale)

	total = {"late_minutes": 0.0, "absent_days": 0.0, "late_deduction": 0.0, "absence_deduction": 0.0}

	for slip in stale:
		doc = frappe.get_doc("Salary Slip", slip.name)
		result = recalculate_slip(doc, apply=bool(apply))
		if not result:
			continue
		for key in total:
			total[key] += frappe.utils.flt(result.get(key) or 0)

		if apply:
			fields = {FINGERPRINT_FIELD: fingerprint}
			if frappe.db.has_column("Salary Slip", LAST_RECALC_FIELD):
				fields[LAST_RECALC_FIELD] = now_datetime()
			frappe.db.set_value("Salary Slip", slip.name, fields, update_modified=False)
			summary["slips_updated"] += 1

	summary.update(total)

	if apply:
		frappe.db.commit()

	_log(summary, company=company, status="Applied" if apply else "No Change")
	return summary


def _log(summary, company=None, status="Applied"):
	"""كتابة سجل التدقيق (لا يُفشل العملية).

	تُكتب السجلات المهمة فقط (تم تطبيق / تم التخطي / خطأ)،
	ولا تُكتب سجلات "No Change" لتفادي تضخّم السجل بالمهام المتكررة.
	"""
	if status == "No Change":
		return
	try:
		if not frappe.db.exists("DocType", LOG_DOCTYPE):
			return

		# لا نكرّر سجل "Skipped" لنفس الشهر في نفس اليوم (المهمة تعمل كل ساعة)
		if status == "Skipped":
			already = frappe.db.count(
				LOG_DOCTYPE,
				{
					"month": summary.get("from_date"),
					"status": status,
					"creation": [">", add_days(getdate(now_datetime()), -1)],
				},
			)
			if already:
				return

		frappe.get_doc(
			{
				"doctype": LOG_DOCTYPE,
				"company": company,
				"month": summary.get("from_date"),
				"status": status,
				"slips_scanned": summary.get("slips_scanned") or 0,
				"slips_updated": summary.get("slips_updated") or 0,
				"total_late_minutes": summary.get("late_minutes") or 0,
				"total_absent_days": summary.get("absent_days") or 0,
				"late_deduction": summary.get("late_deduction") or 0,
				"absence_deduction": summary.get("absence_deduction") or 0,
				"attendance_fingerprint": cstr(summary.get("fingerprint"))[:255],
				"details": cstr(summary.get("message") or summary.get("reason") or "")[:500],
			}
		).insert(ignore_permissions=True, ignore_links=True)
	except Exception:
		frappe.log_error(
			title="Payroll auto recalc: failed to write audit log",
			message=frappe.get_traceback(),
		)


# ----------------------------------------------------------------------
# واجهة التنفيذ المجدول
# ----------------------------------------------------------------------
def execute(lookback_months=12, apply=1, company=None, verbose=1, force=0):
	"""مهمة مجدولة: تعيد احتساب كل شهر تغيّرت فيه بيانات الحضور.

	lookback_months : كم شهراً للخلف (افتراضي 12)
	apply           : 1 تنفيذ فعلي | 0 معاينة فقط
	force           : 1 تجاوز فحص جودة بيانات الحضور
	"""
	if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
		return

	lookback_months = max(1, min(int(lookback_months or 12), 60))
	today = getdate(now_datetime())
	first = getdate(add_days(today, -lookback_months * 31))

	results = []
	months = _iter_months(first, today)

	# الشهور المعلَّمة كـ "فاسدة" (حضور يدوي/تعديل خارج النافذة)
	for dirty in _get_dirty_months():
		if dirty not in months:
			months.append(dirty)

	for month_from, month_to in sorted(months):
		summary = recalculate_range(
			month_from,
			month_to,
			apply=apply,
			company=company,
			reason="scheduled",
			only_stale=True,
			verbose=verbose,
			force=force,
		)
		results.append(summary)
		if verbose:
			print(
				"[{0}] scanned={1} pending={2} updated={3} late_min={4} absent_days={5} {6}".format(
					summary.get("from_date"),
					summary.get("slips_scanned"),
					summary.get("slips_pending"),
					summary.get("slips_updated"),
					summary.get("late_minutes"),
					summary.get("absent_days"),
					summary.get("message") or "",
				)
			)

	_clear_dirty_months(months)
	return results


def _iter_months(from_date, to_date):
	"""قائمة (أول يوم, آخر يوم) لكل شهر ميلادي في المدى."""
	from frappe.utils import get_first_day, get_last_day

	months = []
	cursor = getdate(get_first_day(getdate(from_date)))
	end = getdate(to_date)
	while cursor <= end:
		months.append((cursor, getdate(get_last_day(cursor))))
		cursor = getdate(add_days(get_last_day(cursor), 1))
	return months


# ----------------------------------------------------------------------
# علامة "الشهر تغيّر" (للحضور اليدوي خارج نافذة الـlookback)
# ----------------------------------------------------------------------
def mark_month_dirty(company=None, date=None):
	"""وضع علامة أن بيانات حضور شهر ما تغيّرت."""
	date = getdate(date or now_datetime())
	key = f"{DIRTY_KEY_PREFIX}:{company or 'all'}:{date.strftime('%Y-%m')}"
	try:
		frappe.cache().set_value(key, 1, expires_in_sec=DIRTY_TTL)
	except Exception:
		pass


def mark_attendance_dirty(doc, method=None):
	"""doc_event على Attendance: تعليم الشهر بأن بيانات الحضور تغيّرت.

	تُستدعى عند إنشاء سجل حضور أو تعديله (بما في ذلك التحضير اليدوي).
	العملية رخيصة (علامة في Redis فقط)؛ إعادة الاحتساب تتم في المهمة المجدولة.
	"""
	if frappe.flags.in_install or frappe.flags.in_migrate or frappe.flags.in_patch:
		return

	date = doc.get("attendance_date")
	if not date:
		return

	company = None
	employee = doc.get("employee")
	if employee:
		company = frappe.db.get_value("Employee", employee, "company")

	mark_month_dirty(company=company, date=date)


def _get_dirty_months():
	"""الأشهر المعلَّمة كـ فاسدة."""
	out = []
	try:
		keys = frappe.cache().get_keys(DIRTY_KEY_PREFIX) or []
	except Exception:
		keys = []

	for key in keys:
		parts = cstr(key).split(":")
		if len(parts) < 3:
			continue
		ym = parts[-1]
		try:
			first = getdate(f"{ym}-01")
		except Exception:
			continue
		from frappe.utils import get_last_day

		out.append((first, getdate(get_last_day(first))))
	return out


def _clear_dirty_months(processed):
	"""إزالة العلامات التي عولجت."""
	processed_keys = set()
	for month_from, _month_to in processed:
		processed_keys.add(month_from.strftime("%Y-%m"))

	try:
		keys = frappe.cache().get_keys(DIRTY_KEY_PREFIX) or []
	except Exception:
		keys = []

	for key in keys:
		parts = cstr(key).split(":")
		if len(parts) < 3:
			continue
		if parts[-1] in processed_keys:
			try:
				frappe.cache().delete_value(key)
			except Exception:
				pass


# ----------------------------------------------------------------------
# إعادة احتساب فورية لقسيمة واحدة (زر Reconcile)
# ----------------------------------------------------------------------
@frappe.whitelist()
def reconcile_salary_slip(slip_name, apply=1):
	"""إعادة احتساب خصومات كشف راتب واحد فوراً."""
	if not frappe.has_permission("Salary Slip", "read", throw=True):
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("Salary Slip", slip_name)
	summary = recalculate_range(
		doc.start_date,
		doc.end_date,
		apply=apply,
		company=doc.get("company"),
		reason="manual reconcile",
		only_stale=False,
	)
	return summary
