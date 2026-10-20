# -*- coding: utf-8 -*-
import frappe
from frappe.utils import flt, getdate, get_datetime, cint
from datetime import datetime, timedelta

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"


def get_settings():
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return {}
    try:
        doc = frappe.get_cached_doc(SETTINGS_DOCTYPE)
        return {
            "enabled": cint(doc.get("enable_overtime_generation")),
            "ot15_activity": doc.get("overtime_15_activity"),
            "ot20_activity": doc.get("overtime_20_activity"),
            "threshold": flt(doc.get("overtime_threshold") or 30),
            "max_monthly_hours": flt(doc.get("maximum_monthly_hours") or 0),
            "include_early_entry": cint(doc.get("include_early_entry")),
        }
    except Exception:
        return {}


def apply_overtime_earning(doc, method=None):
    """Validate hook — adds Overtime 1.5 / 2.0 earning rows to Salary Slip
    based on Attendance records in the slip period.

    Gates: enable_overtime_generation must be checked in HR ERP Payroll Settings.
    """
    if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
        return

    settings = get_settings()
    if not settings.get("enabled"):
        return
    if not settings.get("ot15_activity"):
        return

    employee = doc.get("employee")
    start_date = getdate(doc.get("start_date"))
    end_date = getdate(doc.get("end_date"))
    if not employee or not start_date or not end_date:
        return

    # Remove any previously-added overtime rows (idempotent re-run)
    _remove_overtime_rows(doc)

    # Gather attendance
    records = _get_attendance(employee, start_date, end_date)
    if not records:
        return

    # Check holiday list for Overtime 2.0 detection
    holiday_dates = _get_holiday_dates(employee, start_date, end_date)

    # Calculate overtime hours
    ot15_hours = 0.0
    ot20_hours = 0.0
    max_monthly = settings.get("max_monthly_hours") or 0
    threshold_min = settings.get("threshold") or 30

    for att in records:
        if att.status == "Absent":
            continue

        att_date = att.attendance_date

        # Holiday attendance → Overtime 2.0
        if att_date in holiday_dates:
            hours = _calc_holiday_ot_hours(att)
            if hours > 0:
                ot20_hours += hours
            continue

        # Working day: check out_time past shift end
        hours = _calc_working_day_ot_hours(att, threshold_min)
        if hours > 0:
            ot15_hours += hours

    # Cap by maximum monthly hours if set
    if max_monthly > 0:
        total = ot15_hours + ot20_hours
        if total > max_monthly:
            scale = max_monthly / total if total else 0
            ot15_hours *= scale
            ot20_hours *= scale

    # Hourly rate: base / working_days / shift_hours
    hourly_rate = _get_hourly_rate(doc)
    if hourly_rate <= 0:
        return

    # Add earning rows
    if ot15_hours > 0 and settings.get("ot15_activity"):
        amount = round(hourly_rate * 1.5 * ot15_hours, 2)
        if amount > 0:
            _add_earning_row(doc, "Overtime 1.5", amount)

    if ot20_hours > 0 and settings.get("ot20_activity"):
        amount = round(hourly_rate * 2.0 * ot20_hours, 2)
        if amount > 0:
            _add_earning_row(doc, "Overtime 2.0", amount)


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _remove_overtime_rows(doc):
    """Remove Overtime 1.5 and Overtime 2.0 rows from earnings (idempotent)."""
    to_remove = []
    for i, row in enumerate(doc.get("earnings") or []):
        if row.salary_component in ("Overtime 1.5", "Overtime 2.0"):
            to_remove.append(i)
    for i in reversed(to_remove):
        doc.earnings.pop(i)


def _get_attendance(employee, start_date, end_date):
    """Get submitted attendance records for the period."""
    return frappe.get_all(
        "Attendance",
        filters={
            "employee": employee,
            "attendance_date": ["between", [start_date, end_date]],
            "docstatus": 1,
        },
        fields=[
            "name", "attendance_date", "status",
            "in_time", "out_time", "working_hours",
            "shift", "late_entry", "total_overtime_hours",
        ],
    )


def _get_holiday_dates(employee, start_date, end_date):
    """Return set of holiday dates for the employee's holiday list."""
    hl = frappe.db.get_value("Employee", employee, "holiday_list")
    if not hl:
        return set()
    holidays = frappe.get_all(
        "Holiday",
        filters={"parent": hl, "holiday_date": ["between", [start_date, end_date]]},
        pluck="holiday_date",
    )
    return set(holidays)


def _calc_holiday_ot_hours(att):
    """Overtime on a holiday = working_hours (all hours count as OT 2.0)."""
    wh = flt(att.get("working_hours") or 0)
    # Also try computing from in/out if working_hours is 0
    if wh <= 0 and att.in_time and att.out_time:
        in_dt = get_datetime(att.in_time)
        out_dt = get_datetime(att.out_time)
        wh = (out_dt - in_dt).total_seconds() / 3600.0
    return max(0, wh)


def _calc_working_day_ot_hours(att, threshold_min):
    """Overtime on a working day = hours past shift_end_time beyond threshold."""
    if not att.out_time or not att.shift:
        return 0.0

    try:
        shift = frappe.get_cached_doc("Shift Type", att.shift)
    except Exception:
        return 0.0

    shift_end = shift.get("end_time")
    if not shift_end:
        return 0.0

    out_dt = get_datetime(att.out_time)

    # Convert shift_end_time (timedelta or time) to datetime on the same date
    shift_end_dt = _shift_end_as_datetime(out_dt.date(), shift_end)

    if out_dt <= shift_end_dt:
        return 0.0

    overtime_minutes = (out_dt - shift_end_dt).total_seconds() / 60.0
    if overtime_minutes <= threshold_min:
        return 0.0

    # Subtract threshold — only minutes beyond threshold count
    ot_hours = (overtime_minutes - threshold_min) / 60.0
    return max(0, ot_hours)


def _shift_end_as_datetime(d, shift_end):
    """Convert shift end_time to a datetime on date d."""
    if hasattr(shift_end, "total_seconds"):
        sec = int(shift_end.total_seconds())
        h, rem = divmod(sec, 3600)
        m, s = divmod(rem, 60)
        return datetime(d.year, d.month, d.day, h, m, s)
    elif isinstance(shift_end, str):
        parts = shift_end.split(":")
        return datetime(d.year, d.month, d.day, int(parts[0]), int(parts[1]), int(parts[2]) if len(parts) > 2 else 0)
    else:
        return datetime.combine(d, shift_end)


def _get_hourly_rate(doc):
    """Compute hourly rate = base / working_days_per_month / shift_hours."""
    base = flt(doc.get("base") or doc.get("gross_pay") or 0)
    if base <= 0:
        # Try to read from salary structure assignment
        emp = doc.get("employee")
        if emp:
            ssa = frappe.db.get_value(
                "Salary Structure Assignment",
                {"employee": emp, "docstatus": 1},
                ["base", "salary_structure"],
                as_dict=True,
            )
            if ssa and ssa.base:
                base = ssa.base
    if base <= 0:
        return 0.0

    working_days = 30
    settings_doc = frappe.get_cached_doc(SETTINGS_DOCTYPE) if frappe.db.exists("DocType", SETTINGS_DOCTYPE) else None
    if settings_doc:
        working_days = cint(settings_doc.get("working_days_per_month") or 30)

    shift_hours = 8.0
    emp = doc.get("employee")
    if emp:
        shift_name = frappe.db.get_value("Employee", emp, "default_shift")
        if shift_name:
            try:
                st = frappe.get_cached_doc("Shift Type", shift_name)
                if st.start_time and st.end_time:
                    def to_sec(t):
                        return t.total_seconds() if hasattr(t, "total_seconds") else 0
                    diff = to_sec(st.end_time) - to_sec(st.start_time)
                    if diff > 0:
                        shift_hours = diff / 3600.0
            except Exception:
                pass

    daily_rate = base / working_days if working_days else 0
    return daily_rate / shift_hours if shift_hours else 0


def _add_earning_row(doc, component, amount, remark=""):
    """Add or update an earning row."""
    for row in doc.get("earnings") or []:
        if row.salary_component == component:
            row.amount = amount
            return
    doc.append("earnings", {
        "salary_component": component,
        "amount": amount,
    })
