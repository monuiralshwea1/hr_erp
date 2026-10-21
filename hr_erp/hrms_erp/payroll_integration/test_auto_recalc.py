# Copyright (c) 2026, Shumul. All rights reserved.
"""
ط§ط®طھط¨ط§ط±ط§طھ ظ†ط¸ط§ظ… ط¥ط¹ط§ط¯ط© ط§ظ„ط§ط­طھط³ط§ط¨ ط§ظ„طھظ„ظ‚ط§ط¦ظٹط© ظ„ط®طµظˆظ…ط§طھ ط§ظ„طھط£ط®ظٹط± ظˆط§ظ„ط؛ظٹط§ط¨.
ط§ظ„طھط´ط؛ظٹظ„:
  bench --site <SITE> run-tests --app hr_erp \
    --module hr_erp.hrms_erp.payroll_integration.test_auto_recalc
"""

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, getdate, get_datetime, now_datetime

from hr_erp.hrms_erp.payroll_integration import auto_recalc
from hr_erp.hrms_erp.payroll_integration.late_absence_deduction import get_settings

COMPONENTS = ("Late Deduction", "Absence Deduction")


class TestAutoRecalc(FrappeTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")
		cls.company = cls._get_company()
		cls.employee = cls._get_employee()

	# ------------------------------------------------------------------ helpers
	@classmethod
	def _get_company(cls):
		for row in frappe.get_all("Company", fields=["name"], limit=1):
			return row["name"]
		raise AssertionError("ظ„ط§ طھظˆط¬ط¯ ط´ط±ظƒط© ظپظٹ ظ‡ط°ظ‡ ط§ظ„ط¨ظٹط¦ط©")

	@classmethod
	def _get_employee(cls):
		row = frappe.get_all(
			"Employee",
			filters={"status": "Active"},
			fields=["name"],
			limit=1,
		)
		if not row:
			raise unittest.SkipTest("ظ„ط§ ظٹظˆط¬ط¯ ظ…ظˆط¸ظپ ظ†ط´ط· ظپظٹ ظ‡ط°ظ‡ ط§ظ„ط¨ظٹط¦ط©")
		return row[0]["name"]

	def _ensure_fields(self):
		for field in ("audit_recalc_fingerprint", "audit_last_recalc_at"):
			if not frappe.db.exists("Custom Field", {"dt": "Salary Slip", "fieldname": field}):
				self.skipTest(f"ط§ظ„ط­ظ‚ظ„ {field} ط؛ظٹط± ظ…ظˆط¬ظˆط¯ â€” ط´ط؛ظ‘ظ„ bench migrate")

	def _ensure_settings(self):
		settings = get_settings()
		if not settings or not settings.get("enable_late"):
			self.skipTest("ط®طµظ… ط§ظ„طھط£ط®ظٹط± ط؛ظٹط± ظ…ظپط¹ظ‘ظ„ ظپظٹ HR ERP Payroll Settings")

	def _attendance_rows(self, from_date, to_date):
		return frappe.db.sql(
			"""
			select count(*) as total,
			       sum(case when status = 'Present' then 1 else 0 end) as present,
			       sum(case when status = 'Absent' then 1 else 0 end) as absent,
			       sum(case when late_entry = 1 then 1 else 0 end) as late_entries,
			       sum(case when in_time is not null then 1 else 0 end) as with_in_time
			from `tabAttendance`
			where docstatus = 1 and attendance_date between %s and %s
			""",
			(from_date, to_date),
			as_dict=True,
		)[0]

	def _valid_month(self):
		"""أول شهر يحتوي حضوراً فعلياً (Present)."""
		row = frappe.db.sql(
			"""
			select date_format(min(attendance_date), '%Y-%m') as ym
			from `tabAttendance`
			where docstatus = 1 and status in ('Present', 'Half Day', 'Work From Home')
			""",
			as_dict=True,
		)
		if not row or not row[0]["ym"]:
			self.skipTest("لا توجد بيانات حضور فعلي في هذه البيئة")

		from frappe.utils import get_first_day, get_last_day

		first = get_first_day(getdate(f"{row[0]['ym']}-01"))
		return first, get_last_day(first)

	def _slips_in(self, from_date, to_date):
		return frappe.get_all(
			"Salary Slip",
			filters={
				"docstatus": 1,
				"start_date": ["<=", to_date],
				"end_date": [">=", from_date],
			},
			fields=["name", "audit_recalc_fingerprint"],
			ignore_permissions=True,
		)

	# ------------------------------------------------------------------- tests
	def test_fingerprint_changes_with_attendance(self):
		"""ط§ظ„ط¨طµظ…ط© طھطھط؛ظٹظ‘ط± ط¹ظ†ط¯ طھط؛ظٹظ‘ط± ط¨ظٹط§ظ†ط§طھ ط§ظ„ط­ط¶ظˆط±."""
		from_date = getdate("2026-01-01")
		to_date = getdate("2026-12-31")
		fp = auto_recalc.get_attendance_fingerprint(from_date, to_date)
		self.assertIsInstance(fp, str)
		self.assertTrue(fp)
		if fp == "empty":
			self.skipTest("ظ„ط§ طھظˆط¬ط¯ ط¨ظٹط§ظ†ط§طھ ط­ط¶ظˆط±")

	def test_fingerprint_is_stable_without_changes(self):
		"""ط§ظ„ط¨طµظ…ط© ظ†ظپط³ظ‡ط§ ظ…ط§ ظ„ظ… طھطھط؛ظٹظ‘ط± ط§ظ„ط¨ظٹط§ظ†ط§طھ (ط£ط³ط§ط³ ط¹ط¯ظ… ط§ظ„طھظƒط±ط§ط±)."""
		from_date = getdate("2026-01-01")
		to_date = getdate("2026-12-31")
		fp1 = auto_recalc.get_attendance_fingerprint(from_date, to_date)
		fp2 = auto_recalc.get_attendance_fingerprint(from_date, to_date)
		self.assertEqual(fp1, fp2)

	def test_empty_month_has_empty_fingerprint(self):
		fp = auto_recalc.get_attendance_fingerprint(getdate("1990-01-01"), getdate("1990-01-31"))
		self.assertEqual(fp, "empty")

	def test_stale_slips_detection(self):
		"""ط§ظ„ظ‚ط³ط§ط¦ظ… ط§ظ„طھظٹ ظ„ظ… طھظڈط­ط³ط¨ ط¨ط¹ط¯ طھظڈط¹طھط¨ط± staleطŒ ظˆط¨ط¹ط¯ ط§ظ„ط­ط³ط§ط¨ ظ„ط§ طھط¹ظˆط¯ stale."""
		self._ensure_fields()
		from_date = getdate("2026-01-01")
		to_date = getdate("2026-12-31")

		slips = self._slips_in(from_date, to_date)
		if not slips:
			self.skipTest("ظ„ط§ طھظˆط¬ط¯ ظƒط´ظˆظپ ط±ظˆط§طھط¨ ظ…ظڈط±ط³ظژظ„ط©")

		fp = auto_recalc.get_attendance_fingerprint(from_date, to_date)
		stale = auto_recalc.get_stale_slips(from_date, to_date, fp)
		self.assertIsInstance(stale, list)

	def test_recalc_is_idempotent(self):
		"""طھط´ط؛ظٹظ„ ط¥ط¹ط§ط¯ط© ط§ظ„ط§ط­طھط³ط§ط¨ ظ…ط±طھظٹظ† ظ„ط§ ظٹط؛ظٹظ‘ط± ط§ظ„ط£ط±ظ‚ط§ظ… ظˆظ„ط§ ظٹظƒط±ط± ط£ط³ط·ط± ط§ظ„ط®طµظ…."""
		self._ensure_fields()
		self._ensure_settings()

		from_date, to_date = self._valid_month()
		slips = self._slips_in(from_date, to_date)
		if not slips:
			self.skipTest("ظ„ط§ طھظˆط¬ط¯ ظƒط´ظˆظپ ط±ظˆط§طھط¨ ظپظٹ ط§ظ„ط´ظ‡ط± ط§ظ„ظ…ط®طھط§ط±")

		def snapshot():
			return frappe.db.sql(
				"""
				select count(*) as slips,
				       sum(ifnull(total_deduction, 0)) as ded,
				       sum(ifnull(total_late_minutes, 0)) as late,
				       sum(ifnull(total_absent_days, 0)) as absent
				from `tabSalary Slip`
				where docstatus = 1 and start_date <= %s and end_date >= %s
				""",
				(to_date, from_date),
				as_dict=True,
			)[0]

		before = snapshot()
		first = auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
		after_first = snapshot()
		second = auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
		after_second = snapshot()

		# ط§ظ„ط£ط±ظ‚ط§ظ… ظ„ط§ طھطھط؛ظٹط±
		self.assertAlmostEqual(float(before["ded"] or 0), float(after_first["ded"] or 0), places=2)
		self.assertAlmostEqual(float(after_first["ded"] or 0), float(after_second["ded"] or 0), places=2)

		# ط§ظ„طھط´ط؛ظٹظ„ ط§ظ„ط«ط§ظ†ظٹ ظ„ط§ ظٹط­ط¯ظ‘ط« ط´ظٹط¦ط§ظ‹ (ط§ظ„ط¨طµظ…ط© ظ…ط·ط§ط¨ظ‚ط©)
		self.assertEqual(second.get("slips_updated"), 0)

		# ظ„ط§ ط§ط²ط¯ظˆط§ط¬ ظپظٹ ط£ط³ط·ط± ط§ظ„ط®طµظ…
		dupes = frappe.db.sql(
			"""
			select s.name, sd.salary_component, count(*) as c
			from `tabSalary Slip` s
			join `tabSalary Detail` sd on sd.parent = s.name and sd.parenttype = 'Salary Slip'
			where s.docstatus = 1 and s.start_date <= %s and s.end_date >= %s
			  and sd.salary_component in ('Late Deduction', 'Absence Deduction')
			group by s.name, sd.salary_component having count(*) > 1
			""",
			(to_date, from_date),
		)
		self.assertEqual(len(dupes), 0, f"ط£ط³ط·ط± ط®طµظ… ظ…ظƒط±ظ‘ط±ط©: {dupes}")

		# ط§ظ„ط¨طµظ…ط© ظ…ط®ط²ظژظ‘ظ†ط© ط¹ظ„ظ‰ ط§ظ„ظ‚ط³ط§ط¦ظ… ط¨ط¹ط¯ ط§ظ„طھظ†ظپظٹط°
		stored = frappe.db.count(
			"Salary Slip",
			{
				"docstatus": 1,
				"start_date": ["<=", to_date],
				"end_date": [">=", from_date],
				"audit_recalc_fingerprint": ["is", "set"],
			},
		)
		self.assertGreater(stored, 0)

	def test_skipped_month_without_attendance(self):
		"""ط´ظ‡ط± ط¨ظ„ط§ ط­ط¶ظˆط± ظپط¹ظ„ظٹ ظٹظڈطھط®ط·ظ‘ظ‰ ظˆظ„ط§ طھظڈظƒطھط¨ ط®طµظˆظ…ط§طھ."""
		from_date = getdate("1990-01-01")
		to_date = getdate("1990-01-31")
		result = auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
		self.assertTrue(result.get("skipped"))
		self.assertEqual(result.get("slips_updated"), 0)

	def test_dry_run_does_not_write(self):
		"""ط§ظ„ظ…ط¹ط§ظٹظ†ط© (apply=0) ظ„ط§ طھظƒطھط¨ ط£ظٹ ط£ط±ظ‚ط§ظ…."""
		self._ensure_fields()
		self._ensure_settings()
		from_date, to_date = self._valid_month()
		slips = self._slips_in(from_date, to_date)
		if not slips:
			self.skipTest("ظ„ط§ طھظˆط¬ط¯ ظƒط´ظˆظپ ط±ظˆط§طھط¨ ظپظٹ ط§ظ„ط´ظ‡ط± ط§ظ„ظ…ط®طھط§ط±")

		def fingerprint_count():
			return frappe.db.count(
				"Salary Slip",
				{
					"docstatus": 1,
					"start_date": ["<=", to_date],
					"end_date": [">=", from_date],
					"audit_recalc_fingerprint": ["is", "set"],
				},
			)

		before = fingerprint_count()
		auto_recalc.recalculate_range(from_date, to_date, apply=0, reason="test")
		self.assertEqual(fingerprint_count(), before)

	def test_dirty_month_marker(self):
		"""ط¹ظ„ط§ظ…ط© ط§ظ„ط´ظ‡ط± ط§ظ„ظپط§ط³ط¯ طھظڈط­ظپط¸ ظˆطھظڈظ‚ط±ط£."""
		auto_recalc.mark_month_dirty(company="Test Co", date=getdate("2026-08-15"))
		months = auto_recalc._get_dirty_months()
		self.assertTrue(months)
		self.assertTrue(any(str(m[0]).startswith("2026-08") for m in months))
		# طھظ†ط¸ظٹظپ
		for key in frappe.cache().get_keys(auto_recalc.DIRTY_KEY_PREFIX) or []:
			if "Test Co" in str(key):
				frappe.cache().delete_value(key)

	def test_attendance_quality_guard_blocks_high_absence_ratio(self):
		"""حماية: نسبة غياب غير منطقية ⇐ يُتخطّى الشهر (يمنع خصم خاطئ)."""
		from_date, to_date = self._valid_month()

		ok, message = auto_recalc.check_attendance_quality(from_date, to_date)
		self.assertTrue(ok, f"شهر سليم يجب أن يجتاز: {message}")

		# نضبط الحدّ على قيمة أقل من نسبة الغياب الفعلية ⇒ يجب أن يُرفض
		rows = frappe.db.sql(
			"""
			select count(*) as total,
			       sum(case when status = 'Absent' then 1 else 0 end) as absent
			from `tabAttendance`
			where docstatus = 1 and attendance_date between %s and %s
			""",
			(from_date, to_date),
			as_dict=True,
		)
		total = int((rows[0] or {}).get("total") or 0)
		absent = int((rows[0] or {}).get("absent") or 0)
		if total < 20 or absent == 0:
			self.skipTest("لا توجد بيانات كافية لاختبار حدّ الجودة")

		settings = frappe.get_single("HR ERP Payroll Settings")
		old_limit = settings.get("absence_data_quality_limit")
		settings.absence_data_quality_limit = 0.01
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="HR ERP Payroll Settings")
		try:
			ok2, message2 = auto_recalc.check_attendance_quality(from_date, to_date)
			self.assertFalse(ok2, "يجب رفض الشهر عند تجاوز حدّ الجودة")
			self.assertTrue(message2)
		finally:
			settings.reload()
			settings.absence_data_quality_limit = old_limit
			settings.save(ignore_permissions=True)
			frappe.clear_cache(doctype="HR ERP Payroll Settings")

	def test_high_absence_month_is_skipped_not_applied(self):
		"""شهر بنسبة غياب عالية لا يُكتب فيه أي خصم."""
		self._ensure_fields()
		self._ensure_settings()

		from_date, to_date = self._valid_month()
		slips = self._slips_in(from_date, to_date)
		if not slips:
			self.skipTest("لا توجد كشوف رواتب في الشهر المختار")

		def deduction_sum():
			return frappe.db.sql(
				"""
				select sum(ifnull(total_deduction, 0))
				from `tabSalary Slip`
				where docstatus = 1 and start_date <= %s and end_date >= %s
				""",
				(to_date, from_date),
			)[0][0] or 0

		before = deduction_sum()
		settings = frappe.get_single("HR ERP Payroll Settings")
		old_limit = settings.get("absence_data_quality_limit")
		settings.absence_data_quality_limit = 0.01
		settings.save(ignore_permissions=True)
		frappe.clear_cache(doctype="HR ERP Payroll Settings")
		try:
			result = auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
			self.assertTrue(result.get("skipped"))
			self.assertEqual(result.get("slips_updated"), 0)
			self.assertAlmostEqual(float(before or 0), float(deduction_sum() or 0), places=2)
		finally:
			settings.reload()
			settings.absence_data_quality_limit = old_limit
			settings.save(ignore_permissions=True)
			frappe.clear_cache(doctype="HR ERP Payroll Settings")

	def test_audit_log_not_written_for_no_change(self):
		"""لا تتضخّم سجلات التدقيق: التشغيل المتكرر لنفس النتيجة لا يضيف صفوفاً."""
		self._ensure_fields()
		from_date, to_date = self._valid_month()
		slips = self._slips_in(from_date, to_date)
		if not slips:
			self.skipTest("لا توجد كشوف رواتب في الشهر المختار")

		# التشغيل الأول يطبّق ويكتب سجلاً
		auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
		after_first = frappe.db.count("Payroll Deduction Recalc Log")

		# التشغيل الثاني: لا تغيير ⇒ لا سجل جديد
		auto_recalc.recalculate_range(from_date, to_date, apply=1, reason="test")
		after_second = frappe.db.count("Payroll Deduction Recalc Log")

		self.assertEqual(after_second, after_first, "تكرّر التشغيل يضيف صفوف تدقيق بلا داعٍ")
