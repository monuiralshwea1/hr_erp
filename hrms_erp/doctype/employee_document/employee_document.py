# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, getdate, nowdate


class EmployeeDocument(Document):
	def validate(self):
		if not self.employee_name and self.employee:
			self.employee_name = frappe.db.get_value("Employee", self.employee, "employee_name")

		if self.document_name and not self.document_type:
			self.document_type = self.document_name

		# auto status based on expiry date
		if self.expiry_date:
			today = getdate(nowdate())
			expiry = getdate(self.expiry_date)
			if expiry < today:
				self.status = "منتهي"
			elif expiry <= add_days(today, 30):
				self.status = "قريب الانتهاء"
			else:
				self.status = "ساري"
