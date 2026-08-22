# Copyright (c) 2026, Shumul. All rights reserved.
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class ShiftPeriod(Document):
	def validate(self):
		self.validate_times()
		self.validate_grace_periods()

	def validate_times(self):
		if self.start_time == self.end_time:
			frappe.throw("Start time and end time cannot be the same for period: {0}".format(self.period_name))

	def validate_grace_periods(self):
		if self.late_grace_period and self.late_grace_period < 0:
			frappe.throw("Late grace period cannot be negative for: {0}".format(self.period_name))
		if self.early_exit_grace_period and self.early_exit_grace_period < 0:
			frappe.throw("Early exit grace period cannot be negative for: {0}".format(self.period_name))
