# Copyright (c) 2026, Shumul. All rights reserved.
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BiometricDevice(Document):
	def validate(self):
		self.validate_ip_port()

	def validate_ip_port(self):
		if self.ip_address and self.port and self.port <= 0:
			frappe.throw("Port number must be positive")

	def before_insert(self):
		self.active = 1
		self.sync_enabled = 1
