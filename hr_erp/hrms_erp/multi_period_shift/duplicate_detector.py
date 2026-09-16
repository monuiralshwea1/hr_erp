# Copyright (c) 2026, Shumul. All rights reserved.
"""
Duplicate Detection Module
Prevents duplicate checkin records from biometric devices.
"""

import frappe
from frappe import _
from frappe.utils import get_datetime
from datetime import timedelta


def is_duplicate_checkin(employee, timestamp, log_type, device_id=None, exclude_name=None):
	"""
	Enhanced duplicate detection for Employee Checkin.
	Checks exact match and near-duplicate within time window.
	"""
	ts = get_datetime(timestamp)

	# ORIGINAL (active). Exact + near/wider window matching always filters by log_type.
	filters = {
		"employee": employee,
		"time": ts,
		"log_type": log_type,
	}
	if exclude_name:
		filters["name"] = ["!=", exclude_name]

	if frappe.db.exists("Employee Checkin", filters):
		return True

	# Near-duplicate within 5 second window (same device)
	if device_id:
		window = timedelta(seconds=5)
		near_dup = frappe.db.exists(
			"Employee Checkin",
			{
				"employee": employee,
				"time": [">=", ts - window],
				"log_type": log_type,
				"device_id": device_id,
				"name": ["!=", exclude_name or ""],
			},
		)
		if near_dup:
			return True

	# Wider window check for any device (10 seconds)
	wider_window = timedelta(seconds=10)
	wider_dup = frappe.db.exists(
		"Employee Checkin",
		{
			"employee": employee,
			"time": [">=", ts - wider_window, "<=", ts + wider_window],
			"log_type": log_type,
			"name": ["!=", exclude_name or ""],
		},
	)
	return bool(wider_dup)

	# ============================================================
	# DISABLED (2026-09-10): BiometricBridge empty-log_type dedupe.
	# To re-enable, comment the ORIGINAL block above and uncomment
	# this ENABLED block. See hr_erp_DISABLED_CHANGES.txt
	# ============================================================
	# ==== ENABLED (BiometricBridge) ====
	# log_type = (log_type or "").strip().upper() or None
	# filters = {"employee": employee, "time": ts}
	# if log_type:
	# 	filters["log_type"] = log_type
	# if exclude_name:
	# 	filters["name"] = ["!=", exclude_name]
	# if frappe.db.exists("Employee Checkin", filters):
	# 	return True
	# if device_id:
	# 	window = timedelta(seconds=5)
	# 	near_filters = {
	# 		"employee": employee,
	# 		"time": [">=", ts - window],
	# 		"device_id": device_id,
	# 		"name": ["!=", exclude_name or ""],
	# 	}
	# 	if log_type:
	# 		near_filters["log_type"] = log_type
	# 	if frappe.db.exists("Employee Checkin", near_filters):
	# 		return True
	# wider_window = timedelta(seconds=10)
	# wider_filters = {
	# 	"employee": employee,
	# 	"time": [">=", ts - wider_window, "<=", ts + wider_window],
	# 	"name": ["!=", exclude_name or ""],
	# }
	# if log_type:
	# 	wider_filters["log_type"] = log_type
	# return bool(frappe.db.exists("Employee Checkin", wider_filters))
	# ============================


def safe_create_checkin(employee, timestamp, log_type, device_id=None, skip_auto=0):
	"""
	Safely create an Employee Checkin with duplicate prevention.
	Returns the checkin doc if created, None if duplicate.
	"""
	if is_duplicate_checkin(employee, timestamp, log_type, device_id):
		return None

	doc = frappe.new_doc("Employee Checkin")
	doc.employee = employee
	doc.time = timestamp
	doc.log_type = log_type
	doc.device_id = device_id
	if skip_auto:
		doc.skip_auto_attendance = 1
	doc.insert(ignore_permissions=True)
	frappe.db.commit()
	return doc
