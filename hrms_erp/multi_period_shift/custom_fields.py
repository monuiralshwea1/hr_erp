# Copyright (c) 2026, Shumul. All rights reserved.
"""
Custom Fields for Multi-Period Shift Management system.
Applied via hooks.py custom_fields or install.py.
"""

import frappe

CUSTOM_FIELDS = {
	"Shift Type": [
		{
			"fieldname": "multi_period_section",
			"fieldtype": "Section Break",
			"label": "Multi-Period Shift Settings",
			"insert_after": "auto_update_last_sync",
		},
		{
			"fieldname": "enable_multi_period",
			"fieldtype": "Check",
			"label": "Enable Multi Period Shift",
			"default": "0",
			"insert_after": "multi_period_section",
		},
		{
			"fieldname": "shift_periods",
			"fieldtype": "Table",
			"label": "Shift Periods",
			"options": "Shift Period",
			"depends_on": "enable_multi_period",
			"insert_after": "enable_multi_period",
		},
		{
			"fieldname": "attendance_day_start_time",
			"fieldtype": "Time",
			"label": "Attendance Day Start Time",
			"description": "Time when operational day starts (for cross-midnight shifts)",
			"depends_on": "enable_multi_period",
			"insert_after": "shift_periods",
		},
		{
			"fieldname": "multi_period_summary_section",
			"fieldtype": "Section Break",
			"label": "Period Summary",
			"depends_on": "enable_multi_period",
			"insert_after": "attendance_day_start_time",
		},
		{
			"fieldname": "total_working_period_hours",
			"fieldtype": "Float",
			"label": "Total Working Period Hours",
			"read_only": 1,
			"depends_on": "enable_multi_period",
			"insert_after": "multi_period_summary_section",
		},
		{
			"fieldname": "total_break_period_hours",
			"fieldtype": "Float",
			"label": "Total Break Period Hours",
			"read_only": 1,
			"depends_on": "enable_multi_period",
			"insert_after": "total_working_period_hours",
		},
	],
	"Attendance": [
		{
			"fieldname": "late_enter_time",
			"fieldtype": "Time",
			"label": "Late Enter Time",
			"read_only": 1,
			"insert_after": "early_exit",
		},
		{
			"fieldname": "early_exit_time",
			"fieldtype": "Time",
			"label": "Early Exit Time",
			"read_only": 1,
			"insert_after": "late_enter_time",
		},
		{
			"fieldname": "extra_time",
			"fieldtype": "Time",
			"label": "Extra Time",
			"read_only": 1,
			"insert_after": "early_exit_time",
		},
		{
			"fieldname": "total_time",
			"fieldtype": "Float",
			"label": "Total Time",
			"read_only": 1,
			"insert_after": "extra_time",
		},
		{
			"fieldname": "half_shifts",
			"fieldtype": "Check",
			"label": "Half Shifts",
			"insert_after": "total_time",
		},
		{
			"fieldname": "auto_atten_id",
			"fieldtype": "Data",
			"label": "Auto Attendance ID",
			"read_only": 1,
			"insert_after": "half_shifts",
		},
		{
			"fieldname": "multi_period_section",
			"fieldtype": "Section Break",
			"label": "Multi-Period Attendance Details",
			"insert_after": "auto_atten_id",
		},
		{
			"fieldname": "attendance_period_details",
			"fieldtype": "Table",
			"label": "Period Details",
			"options": "Attendance Period Detail",
			"insert_after": "multi_period_section",
		},
		{
			"fieldname": "total_late_minutes",
			"fieldtype": "Float",
			"label": "Total Late Minutes",
			"read_only": 1,
			"insert_after": "attendance_period_details",
		},
		{
			"fieldname": "total_overtime_hours",
			"fieldtype": "Float",
			"label": "Total Overtime Hours",
			"read_only": 1,
			"insert_after": "total_late_minutes",
		},
		{
			"fieldname": "approved_overtime_hours",
			"fieldtype": "Float",
			"label": "Approved Overtime Hours",
			"insert_after": "total_overtime_hours",
		},
	],
	"Employee Checkin": [
		{
			"fieldname": "biometric_device_section",
			"fieldtype": "Section Break",
			"label": "Biometric Device",
			"insert_after": "device_id",
		},
		{
			"fieldname": "biometric_device",
			"fieldtype": "Link",
			"label": "Biometric Device",
			"options": "Biometric Device",
			"insert_after": "biometric_device_section",
		},
		{
			"fieldname": "original_timestamp",
			"fieldtype": "Datetime",
			"label": "Original Device Timestamp",
			"read_only": 1,
			"description": "Raw timestamp from the biometric device before timezone conversion",
			"insert_after": "biometric_device",
		},
	],
}


def create_custom_fields():
	"""Create all custom fields for multi-period shift management."""
	for doctype, fields in CUSTOM_FIELDS.items():
		for field in fields:
			if frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
				continue
			try:
				custom_field = frappe.get_doc({
					"doctype": "Custom Field",
					"dt": doctype,
					"fieldname": field["fieldname"],
					"fieldtype": field.get("fieldtype", "Data"),
					"label": field.get("label"),
					"options": field.get("options"),
					"default": field.get("default"),
					"depends_on": field.get("depends_on"),
					"description": field.get("description"),
					"read_only": field.get("read_only", 0),
					"insert_after": field.get("insert_after"),
					"module": "hrms-erp",
				})
				custom_field.insert(ignore_permissions=True)
			except Exception as e:
				frappe.log_error(f"Failed to create custom field {fieldname} on {doctype}: {e}")
