# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
إعدادات تكامل الرواتب — HR ERP Payroll Settings
================================================
DocType من نوع Single يجمع إعدادات:
  - خصم التأخير من الراتب (Late Deduction)
  - خصم الغياب من الراتب (Absence Deduction)
  - توليد الإضافي من الحضور (Overtime Generation)
  - مزامنة أجهزة BioStar (Biostar Sync)

كل ميزة لها مفتاح تفعيل (Check) — عطّل المفتاح لإيقاف الميزة دون حذف الكود.
انظر HR_ERP_ADDITIONS_AR.md للتفاصيل.
"""

import frappe
from frappe.model.document import Document


class HRERPPayrollSettings(Document):
	def validate(self):
		# تنبيه إذا فُعّل خصم التأخير دون اختيار مكوّن الراتب
		if self.enable_late_deduction and not self.late_deduction_component:
			frappe.throw(
				"فعّلتَ خصم التأخير لكن لم تختر مكوّن الراتب (Late Deduction Component)."
			)
		if self.enable_absence_deduction and not self.absence_deduction_component:
			frappe.throw(
				"فعّلتَ خصم الغياب لكن لم تختر مكوّن الراتب (Absence Deduction Component)."
			)
