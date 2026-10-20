# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
الحقول المخصصة لتكامل الرواتب — custom_fields.py
===================================================

تُنشأ تلقائياً عبر after_migrate (انظر hooks.py).
كل حقل يُنشأ مرة واحدة فقط (idempotent).

الإيقاف: احذف السطر من after_migrate في hooks.py ثم احذف الحقول يدوياً
  من Setup > Custom Field إذا رغبت.

الحقول:
  - Employee: custom_last_attendance_sync_date (آخر مزامنة بصمة — BioStar)
  - Salary Slip: attendance_details (تفاصيل الحضور — تبويب)
  - Timesheet: attendance (ربط بالحضور)
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
			"fieldname": "total_absent_days",
			"fieldtype": "Int",
			"label": "Total Absent Days",
			"read_only": 1,
			"insert_after": "total_late_minutes",
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
