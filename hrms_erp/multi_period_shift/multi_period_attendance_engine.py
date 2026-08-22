# Copyright (c) 2026, Shumul. All rights reserved.
"""
Multi-Period Attendance Engine
Processes employee checkins for multi-period shifts, assigns them to periods,
calculates working hours, late minutes, early exit, overtime, and marks attendance.
"""

from datetime import datetime, timedelta, time as dt_time
from typing import Optional

import frappe
from frappe import _
from frappe.utils import (
	get_datetime,
	get_time,
	getdate,
	time_diff_in_hours,
	cint,
	flt,
)

from hrms.hr.doctype.employee_checkin.employee_checkin import time_diff_in_hours as hrms_time_diff


def get_settings():
	"""Get Multi Period Settings singleton."""
	return frappe.get_single("Multi Period Settings")


def is_multi_period_shift(shift_type_doc):
	"""Check if shift type has multi-period enabled."""
	return cint(getattr(shift_type_doc, "enable_multi_period", 0))


def get_sorted_periods(shift_type_doc):
	"""Get shift periods sorted by period number."""
	periods = shift_type_doc.shift_periods or []
	return sorted(periods, key=lambda p: p.period_number or 0)


def resolve_date_for_cross_midnight(checkin_time, shift_start_time, attendance_day_start=None):
	"""
	Determine the correct attendance date for a checkin.
	Handles cross-midnight shifts using attendance_day_start_time.
	"""
	settings = get_settings()
	if not attendance_day_start:
		attendance_day_start = get_time(settings.attendance_day_start_time or "06:00:00")

	checkin_t = get_datetime(checkin_time).time()
	shift_start_t = get_time(shift_start_time)

	if attendance_day_start <= shift_start_t:
		return get_datetime(checkin_time).date()
	else:
		checkin_dt = get_datetime(checkin_time)
		shift_start_dt = get_datetime(shift_start_time)
		if checkin_t < attendance_day_start and shift_start_t >= attendance_day_start:
			return checkin_dt.date() - timedelta(days=1)
		return checkin_dt.date()


def get_period_datetime_range(period, reference_date):
	"""
	Get the actual datetime range for a shift period on a given date.
	Handles cross-midnight periods.
	Returns (period_start_dt, period_end_dt).
	"""
	start_t = get_time(period.start_time)
	end_t = get_time(period.end_time)
	ref = get_datetime(reference_date).date()

	period_start = datetime.combine(ref, start_t)
	if start_t <= end_t:
		period_end = datetime.combine(ref, end_t)
	else:
		period_end = datetime.combine(ref + timedelta(days=1), end_t)

	return period_start, period_end


def assign_checkins_to_periods(checkins, periods, reference_date, shift_actual_start=None, shift_actual_end=None):
	"""
	Assign checkin logs to shift periods.
	Returns a dict: {period_number: [checkins_in_this_period]}
	"""
	period_assignments = {}
	for p in periods:
		period_assignments[p.period_number] = []

	for checkin in checkins:
		checkin_time = get_datetime(checkin.time)
		assigned = False

		for period in periods:
			if period.is_break:
				continue

			p_start, p_end = get_period_datetime_range(period, reference_date)

			if shift_actual_start and shift_actual_end:
				extended_start = p_start - timedelta(minutes=15)
				extended_end = p_end + timedelta(minutes=15)
				if extended_start <= checkin_time <= extended_end:
					period_assignments[period.period_number].append(checkin)
					assigned = True
					break
			else:
				if p_start <= checkin_time <= p_end:
					period_assignments[period.period_number].append(checkin)
					assigned = True
					break

		if not assigned:
			closest_period = None
			min_distance = timedelta(days=365)
			for period in periods:
				if period.is_break:
					continue
				p_start, p_end = get_period_datetime_range(period, reference_date)
				dist_to_start = abs(checkin_time - p_start)
				if dist_to_start < min_distance:
					min_distance = dist_to_start
					closest_period = period
			if closest_period and min_distance <= timedelta(minutes=30):
				period_assignments[closest_period.period_number].append(checkin)

	return period_assignments


def analyze_period(checkin_logs, period, reference_date):
	"""
	Analyze a single period and return period result dict.
	"""
	p_start, p_end = get_period_datetime_range(period, reference_date)
	period_hours = hrms_time_diff(p_start, p_end) if p_start < p_end else 0

	result = {
		"period_name": period.period_name,
		"period_number": period.period_number,
		"period_start": p_start,
		"period_end": p_end,
		"actual_check_in": None,
		"actual_check_out": None,
		"working_hours": 0,
		"late_minutes": 0,
		"early_exit_minutes": 0,
		"absent_hours": 0,
		"overtime_hours": 0,
		"period_status": "Absent",
		"device_check_in": None,
		"device_check_out": None,
		"device_name_in": None,
		"device_name_out": None,
	}

	if period.is_break:
		result["period_status"] = "Break"
		result["absent_hours"] = 0
		return result

	if not checkin_logs:
		result["period_status"] = "Absent"
		result["absent_hours"] = period_hours
		return result

	# Sort checkins by time
	sorted_logs = sorted(checkin_logs, key=lambda l: get_datetime(l.time))

	# Determine check-in and check-out from logs
	in_log = None
	out_log = None
	for log in sorted_logs:
		if hasattr(log, 'log_type') and log.log_type:
			if log.log_type == "IN" and not in_log:
				in_log = log
			elif log.log_type == "OUT":
				out_log = log
		else:
			if not in_log:
				in_log = log
			else:
				out_log = log

	if not in_log:
		result["period_status"] = "Missing Checkin"
		result["absent_hours"] = period_hours
		return result

	checkin_time = get_datetime(in_log.time)
	result["actual_check_in"] = checkin_time
	result["device_check_in"] = str(checkin_time)
	if hasattr(in_log, 'device_id') and in_log.device_id:
		result["device_name_in"] = in_log.device_id

	if out_log:
		checkout_time = get_datetime(out_log.time)
		result["actual_check_out"] = checkout_time
		result["device_check_out"] = str(checkout_time)
		if hasattr(out_log, 'device_id') and out_log.device_id:
			result["device_name_out"] = out_log.device_id

	# Calculate working hours
	if result["actual_check_out"]:
		actual_hours = hrms_time_diff(checkin_time, checkout_time)
		result["working_hours"] = round(max(0, actual_hours), 2)
	else:
		if checkin_time <= p_end:
			result["working_hours"] = round(hrms_time_diff(checkin_time, p_end), 2)
		else:
			result["working_hours"] = 0

	# Late calculation
	late_grace = cint(period.late_grace_period or 0)
	late_threshold = p_start + timedelta(minutes=late_grace)
	if checkin_time > late_threshold:
		result["late_minutes"] = round((checkin_time - p_start).total_seconds() / 60, 1)

	# Early exit calculation
	early_grace = cint(period.early_exit_grace_period or 0)
	if result["actual_check_out"]:
		early_threshold = p_end - timedelta(minutes=early_grace)
		if checkout_time < early_threshold:
			result["early_exit_minutes"] = round((p_end - checkout_time).total_seconds() / 60, 1)

	# Determine period status
	has_late = result["late_minutes"] > 0
	has_early_exit = result["early_exit_minutes"] > 0

	if result["working_hours"] <= 0:
		result["period_status"] = "Absent"
		result["absent_hours"] = period_hours
	elif result["working_hours"] < (period.minimum_working_hours or 0):
		result["period_status"] = "Partial"
		result["absent_hours"] = round(period_hours - result["working_hours"], 2)
	elif has_late or has_early_exit:
		result["period_status"] = "Late"
	else:
		result["period_status"] = "Present"

	# Overtime calculation
	if period.allow_overtime:
		overtime_threshold = cint(period.overtime_start_after or 0)
		if result["actual_check_out"] and checkout_time > p_end:
			overtime_mins = (checkout_time - p_end).total_seconds() / 60
			if overtime_mins >= overtime_threshold * 60:
				result["overtime_hours"] = round(overtime_mins / 60, 2)

	return result


def calculate_daily_absence_policy(period_results, settings):
	"""
	Apply daily absence policy based on settings.
	"""
	policy = settings.absence_policy if settings else "All Periods Required"
	work_periods = [p for p in period_results if not _is_break_or_holiday(p)]

	if not work_periods:
		return "Present", 0

	total_required = sum(p["working_hours"] + p["absent_hours"] for p in work_periods if p["absent_hours"] > 0 or p["working_hours"] > 0)
	total_working = sum(p["working_hours"] for p in work_periods)
	total_absent = sum(p["absent_hours"] for p in work_periods)

	all_present = all(p["period_status"] in ("Present", "Break", "Holiday", "On Leave") for p in work_periods)
	any_absent = any(p["period_status"] == "Absent" for p in work_periods)
	any_partial = any(p["period_status"] == "Partial" for p in work_periods)

	if policy == "All Periods Required":
		if all_present:
			return "Present", 0
		elif any_absent:
			if total_working <= 0:
				return "Absent", 0
			else:
				threshold = (settings.absent_threshold_percentage or 100) / 100
				if total_required > 0 and total_working / total_required >= threshold:
					return "Present", total_working
				return "Half Day", total_working
		elif any_partial:
			return "Half Day", total_working
		return "Present", total_working

	elif policy == "Half Day on Any Absence":
		if all_present:
			return "Present", total_working
		else:
			if total_working <= 0:
				return "Absent", 0
			return "Half Day", total_working

	elif policy == "Proportional to Hours":
		if total_required > 0:
			percentage = (total_working / total_required) * 100
			threshold = settings.absent_threshold_percentage or 100
			if percentage >= threshold:
				return "Present", total_working
			elif percentage >= threshold / 2:
				return "Half Day", total_working
			else:
				return "Absent", total_working
		return "Absent", 0

	return "Present", total_working


def _is_break_or_holiday(period_result):
	return period_result.get("period_status") in ("Break", "Holiday", "On Leave")


def process_multi_period_attendance(shift_type_doc, employee, checkins, reference_date):
	"""
	Main entry point: process multi-period attendance for an employee on a date.
	Returns a dict with attendance info and period details.
	"""
	periods = get_sorted_periods(shift_type_doc)
	if not periods:
		return None

	shift_actual_start = None
	shift_actual_end = None
	if checkins:
		shift_actual_start = getattr(checkins[0], 'shift_actual_start', None)
		shift_actual_end = getattr(checkins[0], 'shift_actual_end', None)

	period_assignments = assign_checkins_to_periods(
		checkins, periods, reference_date, shift_actual_start, shift_actual_end
	)

	period_results = []
	for period in periods:
		assigned_checkins = period_assignments.get(period.period_number, [])
		result = analyze_period(assigned_checkins, period, reference_date)
		result["employee"] = employee
		period_results.append(result)

	settings = get_settings()
	status, working_hours = calculate_daily_absence_policy(period_results, settings)

	total_late = sum(p["late_minutes"] for p in period_results)
	total_overtime = sum(p["overtime_hours"] for p in period_results)

	in_time = None
	out_time = None
	for p in period_results:
		if p["actual_check_in"] and (in_time is None or p["actual_check_in"] < in_time):
			in_time = p["actual_check_in"]
		if p["actual_check_out"] and (out_time is None or p["actual_check_out"] > out_time):
			out_time = p["actual_check_out"]

	late_entry = total_late > 0
	early_exit = any(p["early_exit_minutes"] > 0 for p in period_results)

	return {
		"employee": employee,
		"attendance_date": reference_date,
		"status": status,
		"working_hours": round(working_hours, 2),
		"late_entry": late_entry,
		"early_exit": early_exit,
		"in_time": in_time,
		"out_time": out_time,
		"shift": shift_type_doc.name,
		"period_details": period_results,
		"total_late_minutes": round(total_late, 1),
		"total_overtime_hours": round(total_overtime, 2),
	}


def mark_multi_period_attendance(attendance_data):
	"""
	Create or update Attendance record with period details.
	"""
	employee = attendance_data["employee"]
	attendance_date = attendance_data["attendance_date"]

	existing = frappe.db.exists(
		"Attendance",
		{"employee": employee, "attendance_date": attendance_date, "docstatus": ["!=", 2]},
	)

	existing = frappe.db.exists(
		"Attendance",
		{"employee": employee, "attendance_date": attendance_date, "docstatus": ["!=", 2]},
	)

	if existing:
		att = frappe.get_doc("Attendance", existing)
		if att.docstatus == 1:
			att.cancel()
			existing = None

	if existing:
		att = frappe.get_doc("Attendance", existing)
		att.working_hours = attendance_data["working_hours"]
		att.status = attendance_data["status"]
		att.late_entry = attendance_data["late_entry"]
		att.early_exit = attendance_data["early_exit"]
		att.in_time = attendance_data["in_time"]
		att.out_time = attendance_data["out_time"]
		att.shift = attendance_data["shift"]
		att.attendance_period_details = []
		for pd in attendance_data.get("period_details", []):
			att.append("attendance_period_details", {
				"employee": employee,
				"attendance": att.name,
				"shift_type": attendance_data["shift"],
				"period_name": pd["period_name"],
				"period_number": pd["period_number"],
				"period_start": pd["period_start"],
				"period_end": pd["period_end"],
				"actual_check_in": pd["actual_check_in"],
				"actual_check_out": pd["actual_check_out"],
				"working_hours": pd["working_hours"],
				"late_minutes": pd["late_minutes"],
				"early_exit_minutes": pd["early_exit_minutes"],
				"absent_hours": pd["absent_hours"],
				"overtime_hours": pd["overtime_hours"],
				"period_status": pd["period_status"],
				"device_check_in": pd.get("device_check_in"),
				"device_check_out": pd.get("device_check_out"),
				"device_name_in": pd.get("device_name_in"),
				"device_name_out": pd.get("device_name_out"),
			})
		att.flags.ignore_validate = True
		att.save(ignore_permissions=True)
	else:
		att = frappe.new_doc("Attendance")
		att.update({
			"employee": employee,
			"attendance_date": attendance_date,
			"status": attendance_data["status"],
			"working_hours": attendance_data["working_hours"],
			"late_entry": attendance_data["late_entry"],
			"early_exit": attendance_data["early_exit"],
			"in_time": attendance_data["in_time"],
			"out_time": attendance_data["out_time"],
			"shift": attendance_data["shift"],
		})
		for pd in attendance_data.get("period_details", []):
			att.append("attendance_period_details", {
				"employee": employee,
				"attendance": None,
				"shift_type": attendance_data["shift"],
				"period_name": pd["period_name"],
				"period_number": pd["period_number"],
				"period_start": pd["period_start"],
				"period_end": pd["period_end"],
				"actual_check_in": pd["actual_check_in"],
				"actual_check_out": pd["actual_check_out"],
				"working_hours": pd["working_hours"],
				"late_minutes": pd["late_minutes"],
				"early_exit_minutes": pd["early_exit_minutes"],
				"absent_hours": pd["absent_hours"],
				"overtime_hours": pd["overtime_hours"],
				"period_status": pd["period_status"],
				"device_check_in": pd.get("device_check_in"),
				"device_check_out": pd.get("device_check_out"),
				"device_name_in": pd.get("device_name_in"),
				"device_name_out": pd.get("device_name_out"),
			})
		att.flags.ignore_validate = True
		att.insert(ignore_permissions=True)
		att.submit()

	# Link checkins to attendance
	if attendance_data.get("_checkins"):
		for checkin in attendance_data["_checkins"]:
			frappe.db.set_value("Employee Checkin", checkin.name, "attendance", att.name)

	frappe.db.commit()
	return att.name


def duplicate_checkin_exists(employee, timestamp, log_type, device_id=None):
	"""
	Enhanced duplicate detection considering device_id and time window.
	"""
	filters = {
		"employee": employee,
		"time": timestamp,
		"log_type": log_type,
		"name": ["!=", ""],
	}
	if device_id:
		filters["device_id"] = device_id

	existing = frappe.db.exists("Employee Checkin", filters)
	if existing:
		return True

	filters.pop("name", None)
	window = 5
	ts = get_datetime(timestamp)
	existing = frappe.db.exists(
		"Employee Checkin",
		{
			"employee": employee,
			"time": (">=", ts - timedelta(seconds=window)),
			"time": ("<=", ts + timedelta(seconds=window)),
			"log_type": log_type,
			"name": ["!=", ""],
		},
	)
	return bool(existing)
