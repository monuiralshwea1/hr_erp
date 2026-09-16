# Copyright (c) 2026, Shumul. All rights reserved.
"""
Override for Employee Checkin to add biometric device tracking and enhanced duplicate detection.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime
from datetime import timedelta

from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin


class CustomEmployeeCheckin(EmployeeCheckin):

	def validate_distance_from_shift_location(self):
		"""Skip lat/long validation — handled by biometric device registration."""
		pass

	def validate_duplicate_log(self):
		"""Enhanced duplicate detection with device_id support."""
		# ORIGINAL (active): exact + near-dup matching always filters by log_type.
		existing = frappe.db.exists(
			"Employee Checkin",
			{
				"employee": self.employee,
				"time": self.time,
				"name": ("!=", self.name),
				"log_type": self.log_type,
			},
		)
		if existing:
			doc_link = frappe.get_desk_link("Employee Checkin", existing)
			frappe.throw(
				_("This employee already has a log with the same timestamp.{0}").format("<Br>" + doc_link)
			)

		# Additional: check for near-duplicate with same device within 5 seconds
		if self.device_id:
			checkin_time = get_datetime(self.time)
			window = 5
			near_dup = frappe.db.exists(
				"Employee Checkin",
				[
					["employee", "=", self.employee],
					["time", ">=", checkin_time - timedelta(seconds=window)],
					["time", "<=", checkin_time + timedelta(seconds=window)],
					["device_id", "=", self.device_id],
					["log_type", "=", self.log_type],
					["name", "!=", self.name],
				],
			)
			if near_dup:
				doc_link = frappe.get_desk_link("Employee Checkin", near_dup)
				frappe.throw(
					_("Duplicate fingerprint detected from device {0}.{1}").format(
						self.device_id, "<Br>" + doc_link
					)
				)

		# ============================================================
		# DISABLED (2026-09-10): BiometricBridge — ignore log_type in
		# duplicate matching so empty-type bridge punches are not
		# flagged against typed ones. To re-enable, comment the ORIGINAL
		# filters above and drop the two "log_type" lines you removed
		# (see hr_erp_DISABLED_CHANGES.txt). Restored original keeps them.
		# ============================================================
