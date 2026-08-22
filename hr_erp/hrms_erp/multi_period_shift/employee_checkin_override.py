# Copyright (c) 2026, Shumul. All rights reserved.
"""
Override for Employee Checkin to add biometric device tracking and enhanced duplicate detection.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime

from hrms.hr.doctype.employee_checkin.employee_checkin import EmployeeCheckin


class CustomEmployeeCheckin(EmployeeCheckin):

	def validate_distance_from_shift_location(self):
		"""Skip lat/long validation — handled by biometric device registration."""
		pass

	def validate_duplicate_log(self):
		"""Enhanced duplicate detection with device_id support."""
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
				{
					"employee": self.employee,
					"time": (">=", checkin_time - frappe.utils.timedelta(seconds=window)),
					"time": ("<=", checkin_time + frappe.utils.timedelta(seconds=window)),
					"device_id": self.device_id,
					"log_type": self.log_type,
					"name": ("!=", self.name),
				},
			)
			if near_dup:
				doc_link = frappe.get_desk_link("Employee Checkin", near_dup)
				frappe.throw(
					_("Duplicate fingerprint detected from device {0}.{1}").format(
						self.device_id, "<Br>" + doc_link
					)
				)
