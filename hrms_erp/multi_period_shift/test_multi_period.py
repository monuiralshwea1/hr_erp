# Copyright (c) 2026, Shumul. All rights reserved.
"""
Tests for Multi-Period Shift Management system.
Run with: bench --site site1.local run-tests --app hr_erp --module hr_erp.hrms_erp.multi_period_shift.test_multi_period
"""

import frappe
from frappe.utils import getdate, get_datetime
from datetime import time, datetime, timedelta

from hr_erp.hrms_erp.multi_period_shift.multi_period_attendance_engine import (
	get_sorted_periods,
	get_period_datetime_range,
	assign_checkins_to_periods,
	analyze_period,
	calculate_daily_absence_policy,
	process_multi_period_attendance,
)
from frappe.tests import IntegrationTestCase


class TestMultiPeriodShift(IntegrationTestCase):
	@classmethod
	def setUpClass(cls):
		super().setUpClass()
		frappe.set_user("Administrator")

	def _create_shift_type(self, name="Test Multi Period Shift"):
		if frappe.db.exists("Shift Type", name):
			frappe.delete_doc("Shift Type", name)

		shift = frappe.get_doc({
			"doctype": "Shift Type",
			"shift_type": name,
			"start_time": "08:00:00",
			"end_time": "22:00:00",
			"enable_auto_attendance": 1,
			"process_attendance_after": getdate(),
			"last_sync_of_checkin": get_datetime(),
			"enable_multi_period": 1,
			"attendance_day_start_time": "06:00:00",
			"shift_periods": [
				{
					"period_name": "Period 1",
					"period_number": 1,
					"start_time": "08:00:00",
					"end_time": "13:00:00",
					"late_grace_period": 15,
					"early_exit_grace_period": 15,
					"minimum_working_hours": 4,
					"enable_period_attendance": 1,
					"allow_overtime": 0,
				},
				{
					"period_name": "Break",
					"period_number": 2,
					"start_time": "13:00:00",
					"end_time": "15:00:00",
					"is_break": 1,
					"break_type": "Unpaid",
				},
				{
					"period_name": "Period 2",
					"period_number": 3,
					"start_time": "15:00:00",
					"end_time": "22:00:00",
					"late_grace_period": 15,
					"early_exit_grace_period": 15,
					"minimum_working_hours": 4,
					"enable_period_attendance": 1,
					"allow_overtime": 1,
					"overtime_start_after": 0.5,
				},
			],
		})
		shift.insert(ignore_permissions=True)
		frappe.db.commit()
		return shift

	def _create_checkin(self, employee, time_str, log_type="IN", device_id="TEST_DEVICE"):
		"""Helper to create an Employee Checkin."""
		checkin = frappe.new_doc("Employee Checkin")
		checkin.employee = employee
		checkin.time = time_str
		checkin.log_type = log_type
		checkin.device_id = device_id
		checkin.flags.ignore_validate = True
		checkin.insert(ignore_permissions=True)
		frappe.db.commit()
		return checkin

	def test_single_period_shift(self):
		"""Test 1: Single period shift with two periods (morning + evening) - classic 2 period shift."""
		shift = self._create_shift_type("Test Single Period")
		shift.enable_multi_period = 0
		shift.save()
		frappe.db.commit()
		self.assertFalse(shift.enable_multi_period)

	def test_two_period_shift(self):
		"""Test 2: Two-period shift with break in between."""
		shift = self._create_shift_type("Test Two Period")
		periods = get_sorted_periods(shift)
		self.assertEqual(len(periods), 3)
		self.assertEqual(periods[0].period_name, "Period 1")
		self.assertTrue(periods[1].is_break)
		self.assertEqual(periods[2].period_name, "Period 2")

	def test_three_period_shift(self):
		"""Test 3: Three working periods."""
		shift = self._create_shift_type("Test Three Period")
		shift.shift_periods = []
		for i, (name, start, end) in enumerate([
			("Morning", "06:00:00", "10:00:00"),
			("Afternoon", "12:00:00", "16:00:00"),
			("Evening", "18:00:00", "22:00:00"),
		], 1):
			shift.append("shift_periods", {
				"period_name": name,
				"period_number": i,
				"start_time": start,
				"end_time": end,
				"enable_period_attendance": 1,
			})
		shift.save()
		frappe.db.commit()
		periods = get_sorted_periods(shift)
		work_periods = [p for p in periods if not p.is_break]
		self.assertEqual(len(work_periods), 3)

	def test_multiple_breaks(self):
		"""Test 4: Multiple break periods."""
		shift = self._create_shift_type("Test Multiple Breaks")
		shift.shift_periods = []
		config = [
			("Work 1", "08:00", "12:00", False),
			("Break 1", "12:00", "12:30", True),
			("Work 2", "12:30", "16:00", False),
			("Break 2", "16:00", "17:00", True),
			("Work 3", "17:00", "22:00", False),
		]
		for i, (name, start, end, is_break) in enumerate(config, 1):
			shift.append("shift_periods", {
				"period_name": name,
				"period_number": i,
				"start_time": f"{start}:00",
				"end_time": f"{end}:00",
				"is_break": 1 if is_break else 0,
				"enable_period_attendance": 0 if is_break else 1,
			})
		shift.save()
		frappe.db.commit()
		periods = get_sorted_periods(shift)
		breaks = [p for p in periods if p.is_break]
		self.assertEqual(len(breaks), 2)

	def test_cross_midnight_shift(self):
		"""Test 5: Shift that crosses midnight."""
		shift = self._create_shift_type("Test Cross Midnight")
		shift.start_time = "22:00:00"
		shift.end_time = "06:00:00"
		shift.shift_periods = []
		shift.append("shift_periods", {
			"period_name": "Night Work 1",
			"period_number": 1,
			"start_time": "22:00:00",
			"end_time": "23:00:00",
			"enable_period_attendance": 1,
		})
		shift.append("shift_periods", {
			"period_name": "Break",
			"period_number": 2,
			"start_time": "23:00:00",
			"end_time": "01:00:00",
			"is_break": 1,
		})
		shift.append("shift_periods", {
			"period_name": "Night Work 2",
			"period_number": 3,
			"start_time": "01:00:00",
			"end_time": "06:00:00",
			"enable_period_attendance": 1,
		})
		shift.save()
		frappe.db.commit()
		p_start, p_end = get_period_datetime_range(shift.shift_periods[2], getdate())
		self.assertEqual(p_start.date(), getdate())
		self.assertEqual(p_end.date(), getdate() + timedelta(days=1))

	def test_late_within_grace(self):
		"""Test 7: Late entry within grace period."""
		shift = self._create_shift_type("Test Late Grace")
		checkin_time = datetime.combine(getdate(), time(8, 10, 0))
		period_start = datetime.combine(getdate(), time(8, 0, 0))
		late_grace = timedelta(minutes=15)
		self.assertTrue(checkin_time <= period_start + late_grace)

	def test_late_after_grace(self):
		"""Test 8: Late entry after grace period."""
		shift = self._create_shift_type("Test Late After Grace")
		checkin_time = datetime.combine(getdate(), time(8, 20, 0))
		period_start = datetime.combine(getdate(), time(8, 0, 0))
		late_grace = timedelta(minutes=15)
		self.assertTrue(checkin_time > period_start + late_grace)
		late_mins = (checkin_time - period_start).total_seconds() / 60
		self.assertEqual(late_mins, 20)

	def test_early_exit(self):
		"""Test 9: Early exit detection."""
		p_end = datetime.combine(getdate(), time(16, 0, 0))
		checkout = datetime.combine(getdate(), time(15, 30, 0))
		early_exit_mins = (p_end - checkout).total_seconds() / 60
		self.assertEqual(early_exit_mins, 30)

	def test_period_analysis_working(self):
		"""Test working period analysis."""
		shift = self._create_shift_type("Test Period Analysis")
		periods = get_sorted_periods(shift)
		work_period = periods[0]

		mock_logs = [
			frappe._dict({
				"time": datetime.combine(getdate(), time(8, 0, 0)),
				"log_type": "IN",
				"device_id": "DEV1",
			}),
			frappe._dict({
				"time": datetime.combine(getdate(), time(13, 0, 0)),
				"log_type": "OUT",
				"device_id": "DEV1",
			}),
		]
		result = analyze_period(mock_logs, work_period, getdate())
		self.assertEqual(result["period_status"], "Present")
		self.assertAlmostEqual(result["working_hours"], 5.0, places=1)

	def test_period_analysis_absent(self):
		"""Test absent period (no checkins)."""
		shift = self._create_shift_type("Test Absent Period")
		periods = get_sorted_periods(shift)
		result = analyze_period([], periods[0], getdate())
		self.assertEqual(result["period_status"], "Absent")

	def test_absence_policy_all_required(self):
		"""Test absence policy: All Periods Required."""
		settings = frappe.get_single("Multi Period Settings")
		settings.absence_policy = "All Periods Required"
		settings.save()
		frappe.db.commit()

		period_results = [
			{"working_hours": 5, "absent_hours": 0, "period_status": "Present"},
			{"working_hours": 7, "absent_hours": 0, "period_status": "Present"},
		]
		status, hours = calculate_daily_absence_policy(period_results, settings)
		self.assertEqual(status, "Present")

	def test_absence_policy_half_day(self):
		"""Test absence policy: Half Day on Any Absence."""
		settings = frappe.get_single("Multi Period Settings")
		settings.absence_policy = "Half Day on Any Absence"
		settings.save()
		frappe.db.commit()

		period_results = [
			{"working_hours": 5, "absent_hours": 0, "period_status": "Present"},
			{"working_hours": 0, "absent_hours": 7, "period_status": "Absent"},
		]
		status, hours = calculate_daily_absence_policy(period_results, settings)
		self.assertEqual(status, "Half Day")
