# Copyright (c) 2026, Shumul. All rights reserved.
"""
Biometric Device Handler
Manages biometric device synchronization and data processing.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime, now_datetime


def get_device_by_id(device_id):
	"""Get Biometric Device by device_id."""
	return frappe.db.get_value(
		"Biometric Device",
		{"device_id": device_id, "active": 1},
		["name", "device_name", "company", "branch", "location", "timezone"],
		as_dict=True,
	)


def update_device_sync(device_name):
	"""Update last sync time for a device."""
	frappe.db.set_value("Biometric Device", device_name, "last_sync", now_datetime())
	frappe.db.commit()


def get_active_devices(company=None):
	"""Get all active biometric devices, optionally filtered by company."""
	filters = {"active": 1, "sync_enabled": 1}
	if company:
		filters["company"] = company
	return frappe.get_all(
		"Biometric Device",
		filters=filters,
		fields=["name", "device_name", "device_id", "company", "branch", "location"],
	)


def log_device_event(device_name, event_type, details=None):
	"""Log a biometric device event."""
	frappe.get_doc({
		"doctype": "Comment",
		"comment_type": "Info",
		"reference_doctype": "Biometric Device",
		"reference_name": device_name,
		"content": f"<b>{event_type}</b>: {details or 'No details'}",
	}).insert(ignore_permissions=True)
