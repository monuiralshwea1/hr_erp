# Copyright (c) 2026, Shumul. All rights reserved.
"""
Override for Shift Type to support multi-period shifts.
"""

from datetime import datetime, timedelta
from itertools import groupby

import frappe
from frappe import _
from frappe.utils import (
	get_datetime,
	get_time,
	getdate,
	time_diff,
	cint,
	flt,
	create_batch,
)

from hrms.hr.doctype.shift_type.shift_type import ShiftType
from hrms.hr.doctype.employee_checkin.employee_checkin import (
	calculate_working_hours,
)
from hrms.hr.doctype.shift_assignment.shift_assignment import get_employee_shift, get_shift_details
from hrms.hr.doctype.attendance.attendance import mark_attendance

from hr_erp.hrms_erp.multi_period_shift.multi_period_attendance_engine import (
	is_multi_period_shift,
	get_sorted_periods,
	process_multi_period_attendance,
	mark_multi_period_attendance,
)

EMPLOYEE_CHUNK_SIZE = 50


class CustomShiftType(ShiftType):

	def process_auto_attendance(self, is_manually_triggered=False):
		if self.has_incorrect_shift_config():
			return

		if is_multi_period_shift(self):
			self._process_multi_period(is_manually_triggered)
			return

		# Fall back to standard HRMS behavior for single-period shifts
		logs = self.get_employee_checkins()
		if is_manually_triggered:
			if len(logs) > 1000 or frappe.flags.test_bg_job:
				job_id = "process_auto_attendance_" + self.name
				job = frappe.enqueue(self._process, logs=logs, timeout=1200, job_id=job_id, deduplicate=True)
				return f"Attendance marking has been queued. You can monitor the job status {frappe.utils.get_link_to_form('RQ Job', job.id, label='here')}"
			else:
				try:
					self._process(logs)
					return "Attendance has been marked as per employee check-ins."
				except Exception as e:
					error_log = frappe.log_error(e)
					return f"An error occurred. Refer the error log {frappe.utils.get_link_to_form('Error Log', error_log.name, label='here')}"
		else:
			self._process(logs)

	def _process_multi_period(self, is_manually_triggered=False):
		"""Process attendance for multi-period shifts."""
		logs = self.get_employee_checkins()

		group_key = lambda x: (x["employee"], x["shift_start"].date() if hasattr(x["shift_start"], "date") else x["shift_start"])
		for key, group in groupby(sorted(logs, key=group_key), key=group_key):
			single_group = list(group)
			employee = key[0]
			attendance_date = key[1] if isinstance(key[1], (str,)) else key[1]

			if not self.should_mark_attendance(employee, attendance_date):
				continue

			# Build frappe objects from dicts
			checkin_docs = []
			for log_dict in single_group:
				doc = frappe._dict(log_dict)
				checkin_docs.append(doc)

			attendance_data = process_multi_period_attendance(
				self, employee, checkin_docs, attendance_date
			)

			if attendance_data:
				attendance_data["_checkins"] = checkin_docs
				mark_multi_period_attendance(attendance_data)

		frappe.db.commit()

		# Mark absents for employees with no checkins
		assigned_employees = self.get_assigned_employees(self.process_attendance_after, True)
		for batch in create_batch(assigned_employees, EMPLOYEE_CHUNK_SIZE):
			for employee in batch:
				self.mark_absent_for_dates_with_no_attendance(employee)
			frappe.db.commit()

	def get_attendance(self, logs):
		"""Override to handle multi-period for single-period fallback."""
		if is_multi_period_shift(self):
			return self._get_multi_period_attendance(logs)
		return super().get_attendance(logs)

	def _get_multi_period_attendance(self, logs):
		"""Get attendance result for a single employee+date using multi-period engine."""
		if not logs:
			return "Absent", 0, False, False, None, None

		employee = logs[0].get("employee") if isinstance(logs[0], dict) else logs[0].employee
		shift_start = logs[0].get("shift_start") if isinstance(logs[0], dict) else logs[0].shift_start
		attendance_date = get_datetime(shift_start).date() if shift_start else getdate()

		checkin_docs = []
		for log in logs:
			doc = frappe._dict(log) if isinstance(log, dict) else log
			checkin_docs.append(doc)

		result = process_multi_period_attendance(self, employee, checkin_docs, attendance_date)
		if result:
			return (
				result["status"],
				result["working_hours"],
				result["late_entry"],
				result["early_exit"],
				result["in_time"],
				result["out_time"],
			)
		return "Absent", 0, False, False, None, None

	def validate(self):
		super().validate()
		if is_multi_period_shift(self):
			self.validate_multi_period()

	def validate_multi_period(self):
		"""Validate multi-period shift configuration."""
		periods = get_sorted_periods(self)
		if not periods:
			frappe.throw(_("Please add at least one shift period when Multi-Period is enabled."))

		start = get_time(self.start_time)
		end = get_time(self.end_time)
		if start == end:
			frappe.throw(_("Start time and end time cannot be same for multi-period shifts."))

		# Validate no overlapping periods (excluding breaks)
		work_periods = [p for p in periods if not p.is_break]
		for i in range(len(work_periods)):
			for j in range(i + 1, len(work_periods)):
				p1_start, p1_end = self._get_period_times(work_periods[i])
				p2_start, p2_end = self._get_period_times(work_periods[j])
				if p1_start < p2_end and p2_start < p1_end:
					frappe.throw(
						_("Periods '{0}' and '{1}' overlap.").format(
							work_periods[i].period_name, work_periods[j].period_name
						)
					)

	def _get_period_times(self, period):
		start = get_time(period.start_time)
		end = get_time(period.end_time)
		return start, end
