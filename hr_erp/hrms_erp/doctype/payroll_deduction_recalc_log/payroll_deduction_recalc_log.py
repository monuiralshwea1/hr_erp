# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
سجل إعادة احتساب خصومات الرواتب — Payroll Deduction Recalc Log
===============================================================
سجل تدقيق (Append-only) يوثّق كل عملية إعادة احتساب لخصومات التأخير والغياب:
  - أي شهر تمت معالجته
  - عدد القسائم التي فُحصت وال ones التي حُدِّثت
  - الأرقام الناتجة (دقائق التأخير، أيام الغياب، مبالغ الخصم)
  - بصمة بيانات الحضور المستخدمة (لمقارنة التشغيل الحالي بما سبق)
"""

import frappe
from frappe.model.document import Document

LOG_DOCTYPE = "Payroll Deduction Recalc Log"


class PayrollDeductionRecalcLog(Document):
	"""سجل تدقيق غير قابل للتعديل من المستخدمين (يكتبه الخادم فقط)."""

	def validate(self):
		# السجل يكتبه الخادم فقط: لا يُقبل إنشاؤه من الواجهة
		if not frappe.flags.in_install and not frappe.flags.in_patch and not frappe.flags.in_migrate:
			if not frappe.conf.developer_mode and not self.flags.ignore_permissions:
				frappe.throw(
					frappe._("This log is written by the system only."),
					frappe.PermissionError,
				)

	def on_trash(self):
		if frappe.session.user != "Administrator":
			frappe.throw(
				frappe._("Audit records cannot be deleted."),
				frappe.PermissionError,
			)
