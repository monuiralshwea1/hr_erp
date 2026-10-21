# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
تعديلات على الحقول المخصصة للرواتب — custom_fields.py
=====================================================
يُنشأ تلقائياً عبر after_migrate (انظر hooks.py).
كل حقل يُنشأ مرة واحدة فقط (idempotent).

الحقول:
  - Employee: custom_last_attendance_sync_date (آخر مزامنة بصمة — BioStar)
  - Salary Slip: attendance_details (تفاصيل الحضور — تبويب)
  - Timesheet: attendance (ربط بالحضور)

الحقول الجديدة (2026-10-21) — نظام إعادة الاحتساب التلقائية:
  - Salary Slip: audit_recalc_fingerprint  (بصمة بيانات الحضور آخر مرة احتُسبت)
  - Salary Slip: audit_last_recalc_at      (آخر إعادة احتساب)
"""

import frappe
from frappe.custom.doctype.custom_field.custom_field import (
	create_custom_fields as _frappe_create_custom_fields,
)


CUSTOM_FIELDS = {
	"Employee": [
		{
			"fieldname": "custom_last_attendance_sync_date",
			"fieldtype": "Date",
			"label": "Last Attendance Sync Date",
			"insert_after": "attendance_device_id",
			"read_only": 1,
		},
	],
	"Salary Slip": [
		{
			"fieldname": "attendance_details_tab",
			"fieldtype": "Tab Break",
			"label": "Attendance Details",
			"insert_after": "deductions",
		},
		{
			"fieldname": "attendance_section",
			"fieldtype": "Section Break",
			"label": "Attendance",
			"insert_after": "attendance_details_tab",
		},
		{
			"fieldname": "total_late_minutes",
			"fieldtype": "Float",
			"label": "Total Late Minutes",
			"read_only": 1,
			"insert_after": "attendance_section",
		},
		{
			# MODIFIED: Int -> Float لدعم نصف يوم الغياب (0.5)
			# ORIGINAL: "fieldtype": "Int",
			"fieldname": "total_absent_days",
			"fieldtype": "Float",
			"label": "Total Absent Days",
			"read_only": 1,
			"insert_after": "total_late_minutes",
		},
		{
			# MODIFIED (2026-10-21): حقول نظام إعادة الاحتساب التلقائية
			# البصمة تُخزَّن على القسيمة لمقارنة بيانات الحضور الحالية بما احتُسب سابقاً
			"fieldname": "audit_last_recalc_at",
			"fieldtype": "Datetime",
			"label": "Last Deduction Reconciliation",
			"read_only": 1,
			"insert_after": "total_absent_days",
		},
		{
			"fieldname": "audit_recalc_fingerprint",
			"fieldtype": "Data",
			"label": "Attendance Fingerprint",
			"read_only": 1,
			"hidden": 1,
			"insert_after": "audit_last_recalc_at",
		},
	],
	"Timesheet": [
		{
			"fieldname": "attendance",
			"fieldtype": "Link",
			"label": "Attendance",
			"options": "Attendance",
			"insert_after": "employee",
			"read_only": 1,
		},
	],
}


def create_custom_fields():
	"""إنشاء الحقول المخصصة — idempotent (لا تكرر الموجود)."""
	_frappe_create_custom_fields(CUSTOM_FIELDS, ignore_validate=True, update=True)
