# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import cint, get_datetime


# ------------------------------------------------------------------
# Simple auth: the device app authenticates with api_key / api_secret
# of a user that holds the "HR Manager" role. Every whitelisted method
# is additionally guarded by this check.
# ------------------------------------------------------------------
def _require_hr_permission():
	if frappe.session.user == "Administrator":
		return
	roles = frappe.get_roles(frappe.session.user)
	if not ({"HR Manager", "HR User", "System Manager"} & set(roles)):
		frappe.throw(
			_("Not permitted: HR Manager role required for biometric API."),
			frappe.PermissionError,
		)


# ------------------------------------------------------------------
# Device-facing endpoints
# ------------------------------------------------------------------
@frappe.whitelist()
def ping():
	"""Health check used by the device bridge to validate credentials/URL."""
	_require_hr_permission()
	return {
		"ok": True,
		"site": frappe.local.site,
		"server_time": frappe.utils.now_datetime().isoformat(),
		"frappe_version": frappe.__version__,
	}


@frappe.whitelist()
def get_branches():
	"""Active branches (device locations)."""
	_require_hr_permission()
	return [
		{"name": b.name}
		for b in frappe.get_all("Branch", fields=["name"], order_by="name asc")
	]


@frappe.whitelist()
def get_employees():
	"""Active employees with their biometric identity, for enrollment sync."""
	_require_hr_permission()
	rows = frappe.get_all(
		"Employee",
		filters={"status": "Active"},
		fields=[
			"name",
			"employee_name",
			"department",
			"biometric_employee_id",
			"biometric_fingerprint_id",
			"biometric_devices",
			"biometric_enrolled",
		],
		order_by="employee_name asc",
	)
	return [
		{
			"employee": e.name,
			"employee_name": e.employee_name,
			"department": e.department,
			"biometric_employee_id": e.biometric_employee_id,
			"biometric_fingerprint_id": e.biometric_fingerprint_id,
			"biometric_devices": e.biometric_devices,
			"biometric_enrolled": cint(e.biometric_enrolled),
		}
		for e in rows
	]


@frappe.whitelist()
def register_fingerprint(employee, fingerprint_id=None, device_id=None):
	"""Record that an employee is enrolled on a device (called by the bridge
	after it successfully pushes the template to the device)."""
	_require_hr_permission()
	if not employee or not frappe.db.exists("Employee", employee):
		frappe.throw(_("Employee not found: {0}").format(employee))

	doc = frappe.get_doc("Employee", employee)
	doc.flags.ignore_permissions = True
	doc.flags.ignore_mandatory = True

	if fingerprint_id:
		doc.biometric_fingerprint_id = str(fingerprint_id)
	if not doc.biometric_employee_id:
		doc.biometric_employee_id = str(fingerprint_id or employee)

	if device_id:
		devices = [d.strip() for d in (doc.biometric_devices or "").split(",") if d.strip()]
		if device_id not in devices:
			devices.append(device_id)
			doc.biometric_devices = ", ".join(devices)

	doc.biometric_enrolled = 1
	doc.save()
	return {"ok": True, "employee": employee}


# ------------------------------------------------------------------
# Checkin sync
# ------------------------------------------------------------------
@frappe.whitelist()
def sync_checkins(branch=None, device_id=None, checkins=None):
	"""Bulk create Employee Checkin records coming from a device.

	Each item in `checkins`:
	    {
	        "employee": "EMP-00001",       # server employee name
	        "time": "2026-08-09 08:01:12", # ISO / MySQL datetime
	        "log_type": "IN" | "OUT",
	        "biometric_log_id": "<device>:<uid>:<ts>",  # dedupe key (required)
	        "device_id": "branch-1",
	    }

	Records whose biometric_log_id already exists are skipped (idempotent).
	"""
	_require_hr_permission()
	if not checkins:
		return {"ok": True, "created": 0, "skipped": 0, "failed": 0, "errors": []}

	if isinstance(checkins, str):
		import json

		checkins = json.loads(checkins)

	created = 0
	skipped = 0
	failed = 0
	errors = []

	existing = _existing_log_ids([c.get("biometric_log_id") for c in checkins])

	for c in checkins:
		log_id = (c.get("biometric_log_id") or "").strip()
		if not log_id:
			errors.append({"employee": c.get("employee"), "error": "missing biometric_log_id"})
			failed += 1
			continue
		if log_id in existing:
			skipped += 1
			continue

		try:
			emp = c.get("employee")
			if not emp or not frappe.db.exists("Employee", emp):
				# try resolving by biometric identity
				emp = _resolve_employee(c)
			if not emp:
				errors.append({"biometric_log_id": log_id, "error": "unknown employee"})
				failed += 1
				continue

			log_type = c.get("log_type") or "IN"
			if log_type not in ("IN", "OUT"):
				errors.append({"biometric_log_id": log_id, "error": "bad log_type"})
				failed += 1
				continue

			checkin = frappe.new_doc("Employee Checkin")
			checkin.employee = emp
			checkin.time = get_datetime(c["time"])
			checkin.log_type = log_type
			checkin.device_id = c.get("device_id") or device_id
			checkin.biometric_log_id = log_id
			checkin.flags.ignore_permissions = True
			checkin.insert()
			existing.add(log_id)
			created += 1
		except Exception as e:
			failed += 1
			errors.append({"biometric_log_id": log_id, "error": str(e)})

	frappe.db.commit()
	return {"ok": True, "created": created, "skipped": skipped, "failed": failed, "errors": errors}


def _existing_log_ids(log_ids):
	"""Return the set of biometric_log_id values already present."""
	log_ids = [l for l in (log_ids or []) if l]
	if not log_ids:
		return set()
	rows = frappe.get_all(
		"Employee Checkin",
		filters={"biometric_log_id": ["in", log_ids]},
		fields=["biometric_log_id"],
	)
	return {r.biometric_log_id for r in rows}


def _resolve_employee(c):
	"""Resolve the employee from biometric identity fields sent by the bridge."""
	bid = (c.get("biometric_employee_id") or "").strip()
	if bid:
		emp = frappe.db.get_value("Employee", {"biometric_employee_id": bid}, "name")
		if emp:
			return emp
	fid = (c.get("fingerprint_id") or "").strip()
	if fid:
		emp = frappe.db.get_value("Employee", {"biometric_fingerprint_id": fid}, "name")
		if emp:
			return emp
	return None
