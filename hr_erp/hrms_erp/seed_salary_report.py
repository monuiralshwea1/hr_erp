# -*- coding: utf-8 -*-
"""
seed_salary_report.py — توليد بيانات كشف الراتب الافتراضية لأغسطس 2026
========================================================================

يُنشئ حضور لجميع موظفي الشاحذي لأغسطس 2026 ب أنماط متنوعة:
  - حضور في الوقت (70%)
  - حضور متأخر (15%)
  - غياب (5%)
  - نصف دوام (5%)
  - إضافي (5% — ساعات عمل تتجاوز نهاية الشفت)

ثم يُنشئ قسائم رواتب لأغسطس 2026 مع الخصومات التالية (تلقائياً عبر hooks):
  - خصم التأخير (Late Deduction)
  - خصم الغياب (Absence Deduction)
  - إضافي 1.5 (Overtime 1.5 — earns)

التشغيل:
  cd ~/frappe-bench2/sites
  bench --site site1.local execute hr_erp.hrms_erp.seed_salary_report.execute

التشغيل الآمن: خوارزمية تكرارية — يحذف ويُنشئ بيانات أغسطس من جديد.
"""

import frappe
from frappe import _
from frappe.utils import flt, cint, getdate, nowdate
from datetime import datetime, timedelta, date
from calendar import monthrange
import hashlib

# ------------------------------------------------------------------
# Configuration
# ------------------------------------------------------------------
COMPANY = "الشاحذي"
SS_NAME = "SH-هيكل رواتب الشاحذي"
PAYROLL_MONTH = date(2026, 8, 1)
OFFICIAL_SHIFT = "دوام رسمي"
START_DATE = date(2026, 8, 1)
END_DATE = date(2026, 8, 31)

# Probability thresholds for attendance patterns (deterministic via hash)
THRESHOLDS = {
    "present": 0.70,       # 70% on time
    "late": 0.85,          # 15% late (70-85%)
    "absent": 0.90,        # 5% absent (85-90%)
    "half_day": 0.95,      # 5% half day (90-95%)
    "overtime": 1.00,      # 5% overtime (95-100%)
}


def execute():
    """Main entry point — run via bench execute."""
    print("=" * 60)
    print("SEED SALARY REPORT — أغسطس 2026 — الشاحذي")
    print("=" * 60)

    # 1. Cancel existing Aug slips
    _cancel_aug_slips()
    frappe.db.commit()

    # 2. Delete existing Aug attendance for الشاحذي (if any)
    _delete_aug_attendance()
    frappe.db.commit()

    # 3. Create Aug attendance for all الشاحذي employees
    _create_aug_attendance()
    frappe.db.commit()

    # 4. Create and submit salary slips
    _create_aug_slips()
    frappe.db.commit()

    # 5. Summary
    _print_summary()

    print("\n" + "=" * 60)
    print("DONE — كشف الراتب لأغسطس 2026 جاهز")
    print("=" * 60)


# ------------------------------------------------------------------
# 1. Cancel existing August salary slips
# ------------------------------------------------------------------
def _cancel_aug_slips():
    print("\n[1/5] Cancellation existing Aug salary slips...")

    # Find Aug 2026 PEs for الشاحذي
    pes = frappe.get_all(
        "Payroll Entry",
        filters={
            "company": COMPANY,
            "start_date": ["between", ["2026-08-01", "2026-08-31"]],
            "docstatus": 1,
        },
        fields=["name", "docstatus"],
    )

    for pe in pes:
        print(f"  Cancelling PE: {pe.name}")
        # Cancel slips linked to this PE
        slips = frappe.get_all(
            "Salary Slip",
            filters={"payroll_entry": pe.name, "docstatus": 1},
            fields=["name"],
        )
        for s in slips:
            try:
                frappe.get_doc("Salary Slip", s.name).cancel()
            except Exception as e:
                frappe.clear_messages()
                print(f"    Cannot cancel slip {s.name}: {e}")

        # Cancel the PE
        try:
            pe_doc = frappe.get_doc("Payroll Entry", pe.name)
            pe_doc.cancel()
            print(f"    PE {pe.name} cancelled")
        except Exception as e:
            frappe.clear_messages()
            print(f"    Cannot cancel PE {pe.name}: {e}")

    # Also cancel orphan slips for Aug
    orphans = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": ["like", "SH-HR-EMP-%"],
            "start_date": "2026-08-01",
            "docstatus": 1,
        },
        fields=["name"],
    )
    for o in orphans:
        try:
            frappe.get_doc("Salary Slip", o.name).cancel()
        except Exception:
            frappe.clear_messages()

    # Delete draft slips
    drafts = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": ["like", "SH-HR-EMP-%"],
            "start_date": "2026-08-01",
            "docstatus": 0,
        },
        fields=["name"],
    )
    for d in drafts:
        try:
            frappe.delete_doc("Salary Slip", d.name, force=True)
        except Exception:
            pass

    frappe.db.commit()
    print(f"  Cancelled {len(orphans)} slips + {len(pes)} PEs")


# ------------------------------------------------------------------
# 2. Delete existing August attendance for الشاحذي
# ------------------------------------------------------------------
def _delete_aug_attendance():
    print("\n[2/5] Deleting existing Aug attendance for الشاحذي...")
    atts = frappe.get_all(
        "Attendance",
        filters={
            "employee": ["like", "SH-HR-EMP-%"],
            "attendance_date": ["between", ["2026-08-01", "2026-08-31"]],
        },
        fields=["name", "docstatus"],
    )
    deleted = 0
    for att in atts:
        try:
            if att.docstatus == 1:
                frappe.get_doc("Attendance", att.name).cancel()
            frappe.delete_doc("Attendance", att.name, force=True)
            deleted += 1
        except Exception:
            frappe.clear_messages()
    frappe.db.commit()
    print(f"  Deleted {deleted} attendance records")


# ------------------------------------------------------------------
# 3. Create August attendance for الشاحذي employees
# ------------------------------------------------------------------
def _create_aug_attendance():
    print("\n[3/5] Creating Aug 2026 attendance for الشاحذي...")

    employees = frappe.get_all(
        "Employee",
        filters={"company": COMPANY, "status": "Active"},
        fields=["name", "employee_name", "default_shift"],
    )

    # Determine working days in Aug 2026 (Mon-Fri pattern matching existing data)
    # Also exclude Aug 22 (Eid Al-Adha holiday)
    holiday_dates = set()
    hl = frappe.db.get_value("Employee", employees[0].name, "holiday_list") if employees else None
    if hl:
        for h in frappe.get_all(
            "Holiday",
            filters={"parent": hl, "holiday_date": ["between", ["2026-08-01", "2026-08-31"]]},
            fields=["holiday_date"],
        ):
            holiday_dates.add(h["holiday_date"])

    # Also check standard weekly holidays (Fri+Sat? or just Fri?)
    # Based on existing data: Mon-Fri are working days, Sat-Sun off
    working_days = []
    for day in range(1, 32):
        d = date(2026, 8, day)
        if d.weekday() in (5, 6):  # Sat=5, Sun=6 — off
            continue
        if d in holiday_dates:
            continue
        working_days.append(d)

    print(f"  Working days: {len(working_days)} (Fri-Sat off, Eid excluded)")

    created = 0
    shift_name = OFFICIAL_SHIFT

    for emp in employees:
        for d in working_days:
            # Deterministic pattern based on employee + date hash
            pattern = _get_pattern(emp.name, d)

            # Determine status and times
            in_time, out_time, status, late, ot_hours = _determine_attendance(
                emp.name, d, pattern, shift_name
            )

            # Working hours
            working_hours = 0.0
            if in_time and out_time:
                delta = (out_time - in_time).total_seconds() / 3600.0
                working_hours = max(0, delta - 1.0)  # subtract 1hr break

            # Create attendance
            try:
                att = frappe.get_doc({
                    "doctype": "Attendance",
                    "employee": emp.name,
                    "employee_name": emp.employee_name,
                    "company": COMPANY,
                    "attendance_date": d.strftime("%Y-%m-%d"),
                    "status": status,
                    "in_time": in_time.strftime("%Y-%m-%d %H:%M:%S") if in_time else None,
                    "out_time": out_time.strftime("%Y-%m-%d %H:%M:%S") if out_time else None,
                    "working_hours": round(working_hours, 2),
                    "late_entry": late,
                    "shift": shift_name,
                })
                att.insert(ignore_permissions=True)
                att.submit()
                created += 1
            except Exception as e:
                frappe.clear_messages()

            if created % 50 == 0 and created > 0:
                frappe.db.commit()

    frappe.db.commit()
    print(f"  Created {created} attendance records for {len(employees)} employees")


def _get_pattern(emp_name, d):
    """Deterministic pattern hash for (employee, date)."""
    h = hashlib.md5(f"{emp_name}{d.isoformat()}".encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _determine_attendance(emp_name, d, pattern, shift_name):
    """Return (in_time, out_time, status, late_entry, ot_hours)."""
    if pattern < THRESHOLDS["present"]:
        # On time (70%)
        in_dt = datetime(d.year, d.month, d.day, 8, 0)
        out_dt = datetime(d.year, d.month, d.day, 17, 0)
        return in_dt, out_dt, "Present", 0, 0.0

    elif pattern < THRESHOLDS["late"]:
        # Late (15%) — arrive 25-60 min late
        h = hashlib.md5(f"{emp_name}{d.isoformat()}late".encode()).hexdigest()
        late_min = 25 + (int(h[:4], 16) % 36)  # 25-60 min
        in_dt = datetime(d.year, d.month, d.day, 8, 0) + timedelta(minutes=late_min)
        out_dt = datetime(d.year, d.month, d.day, 17, 0)
        return in_dt, out_dt, "Present", 1, 0.0

    elif pattern < THRESHOLDS["absent"]:
        # Absent (5%)
        return None, None, "Absent", 0, 0.0

    elif pattern < THRESHOLDS["half_day"]:
        # Half day (5%)
        in_dt = datetime(d.year, d.month, d.day, 8, 0)
        out_dt = datetime(d.year, d.month, d.day, 12, 0)
        return in_dt, out_dt, "Half Day", 0, 0.0

    else:
        # Overtime (5%) — work past 17:00
        h = hashlib.md5(f"{emp_name}{d.isoformat()}ot".encode()).hexdigest()
        ot_extra_min = 60 + (int(h[:4], 16) % 180)  # 1-4 hours extra
        in_dt = datetime(d.year, d.month, d.day, 8, 0)
        out_dt = datetime(d.year, d.month, d.day, 17, 0) + timedelta(minutes=ot_extra_min)
        ot_hours = ot_extra_min / 60.0
        return in_dt, out_dt, "Present", 0, round(ot_hours, 2)


# ------------------------------------------------------------------
# 4. Create and submit August salary slips
# ------------------------------------------------------------------
def _create_aug_slips():
    print("\n[4/5] Creating Aug 2026 salary slips...")

    employees = frappe.get_all(
        "Employee",
        filters={"company": COMPANY, "status": "Active"},
        fields=["name", "employee_name"],
    )

    created = 0
    submitted = 0
    errors = 0

    for emp in employees:
        # Skip if slip already exists
        existing = frappe.db.exists("Salary Slip", {
            "employee": emp.name,
            "start_date": "2026-08-01",
            "end_date": "2026-08-31",
            "docstatus": 1,
        })
        if existing:
            print(f"  EXISTS: {emp.name} — skipping")
            continue

        try:
            slip = frappe.get_doc({
                "doctype": "Salary Slip",
                "employee": emp.name,
                "company": COMPANY,
                "start_date": "2026-08-01",
                "end_date": "2026-08-31",
                "posting_date": "2026-08-31",
                "salary_structure": SS_NAME,
                "currency": "YER",
                "mode_of_payment": "نقد",
            })
            slip.insert(ignore_permissions=True)
            created += 1

            try:
                slip.submit()
                submitted += 1
            except Exception as e:
                frappe.clear_messages()
                errors += 1
                print(f"  SUBMIT ERR {emp.name}: {e}")

        except Exception as e:
            frappe.clear_messages()
            errors += 1
            print(f"  INSERT ERR {emp.name}: {e}")

        if created % 20 == 0 and created > 0:
            frappe.db.commit()

    frappe.db.commit()
    print(f"  Created: {created}, Submitted: {submitted}, Errors: {errors}")


# ------------------------------------------------------------------
# 5. Summary
# ------------------------------------------------------------------
def _print_summary():
    print("\n[5/5] Summary...")

    # Count deductions
    slips = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": ["like", "SH-HR-EMP-%"],
            "start_date": "2026-08-01",
            "docstatus": 1,
        },
        fields=["name", "employee", "employee_name", "gross_pay", "net_pay",
                "total_deduction", "total_late_minutes", "total_absent_days",
                "overtime_hours"],
    )

    total_late = 0
    total_absent = 0
    total_gross = 0
    total_net = 0
    has_late = 0
    has_absent = 0
    has_ot = 0

    for s in slips:
        total_gross += flt(s.gross_pay or 0)
        total_net += flt(s.net_pay or 0)
        if flt(s.total_late_minutes or 0) > 0:
            has_late += 1
            total_late += flt(s.total_late_minutes)
        if cint(s.total_absent_days or 0) > 0:
            has_absent += 1
            total_absent += cint(s.total_absent_days)

    print(f"\n  Total slips: {len(slips)}")
    print(f"  Slips with late: {has_late}")
    print(f"  Slips with absent: {has_absent}")
    print(f"  Total gross: {total_gross:,.0f} YER")
    print(f"  Total net: {total_net:,.0f} YER")

    # Sample a slip with deductions
    for s in slips:
        if flt(s.total_late_minutes or 0) > 50 or cint(s.total_absent_days or 0) >= 1:
            print(f"\n  Sample: {s.employee} {s.employee_name}")
            print(f"    Gross: {s.gross_pay:,.0f} | Net: {s.net_pay:,.0f}")
            print(f"    Late minutes: {s.total_late_minutes} | Absent days: {s.total_absent_days}")

            # Get deduction/earning rows
            doc = frappe.get_doc("Salary Slip", s.name)
            print(f"    Earnings:")
            for e in doc.earnings:
                print(f"      {e.salary_component}: {e.amount:,.0f}")
            print(f"    Deductions:")
            for d in doc.deductions:
                print(f"      {d.salary_component}: {d.amount:,.0f}")
            break
