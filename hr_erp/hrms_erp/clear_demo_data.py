"""
clear_demo_data.py
==================
Removes ONLY employee-related demo data.
Keeps all structural/system data intact (departments, shift types, periods, etc.)

What gets DELETED:
    - Employees (all or company-filtered)
    - Salary Structure Assignments
    - Shift Assignments
    - Attendance + Attendance Period Details (child table)
    - Employee Checkins
    - Salary Slips
    - Leave Applications

What gets KEPT:
    - Company, Departments, Designations, Branches
    - Shift Types, Shift Periods
    - Leave Types, Holiday Lists
    - Salary Structures, Salary Components
    - Biometric Devices, Multi Period Settings
    - Employment Types

Usage:
    bench --site <site> execute hr_erp.hrms_erp.clear_demo_data.execute
"""
import frappe


def execute(company=None, dry_run=False):
    frappe.flags.dry_run = dry_run

    if not company:
        company = frappe.db.get_default("company") or frappe.db.get_value("Company", {}, "name")
    if not company:
        frappe.throw("No company found.")

    print(f"Clearing demo data for: {company}")
    if dry_run:
        print("*** DRY RUN - no changes ***")
    print("=" * 50)

    employees = frappe.get_all("Employee", {"company": company}, ["name", "employee_name"])
    if not employees:
        print("No employees found. Nothing to clear.")
        return

    emp_names = tuple([e["name"] for e in employees])
    print(f"Found {len(employees)} employees to remove.")

    deleted = {}

    # Use direct SQL for all deletions (handles submitted docs, much faster)
    def _sql_count(query, params=None):
        return frappe.db.sql(query, params or ())[0][0]

    def _sql_del(query, params=None):
        if not dry_run:
            frappe.db.sql(query, params or ())

    # 1. Salary Slips (direct SQL bypasses docstatus check)
    cnt = _sql_count("SELECT COUNT(*) FROM `tabSalary Slip` WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM `tabSalary Slip` WHERE employee IN %s", (emp_names,))
    deleted["salary_slips"] = cnt

    # 2. Leave Applications
    cnt = _sql_count("SELECT COUNT(*) FROM `tabLeave Application` WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM `tabLeave Application` WHERE employee IN %s", (emp_names,))
    deleted["leave_applications"] = cnt

    # 3. Attendance Period Details (child table)
    cnt = _sql_count(
        "SELECT COUNT(*) FROM `tabAttendance Period Detail` apd "
        "INNER JOIN tabAttendance a ON apd.parent = a.name "
        "WHERE a.employee IN %s", (emp_names,)
    )
    _sql_del(
        "DELETE apd FROM `tabAttendance Period Detail` apd "
        "INNER JOIN tabAttendance a ON apd.parent = a.name "
        "WHERE a.employee IN %s", (emp_names,)
    )
    deleted["period_details"] = cnt

    # 4. Attendance
    cnt = _sql_count("SELECT COUNT(*) FROM tabAttendance WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM tabAttendance WHERE employee IN %s", (emp_names,))
    deleted["attendance"] = cnt

    # 5. Employee Checkins
    cnt = _sql_count("SELECT COUNT(*) FROM `tabEmployee Checkin` WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM `tabEmployee Checkin` WHERE employee IN %s", (emp_names,))
    deleted["checkins"] = cnt

    # 6. Shift Assignments
    cnt = _sql_count("SELECT COUNT(*) FROM `tabShift Assignment` WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM `tabShift Assignment` WHERE employee IN %s", (emp_names,))
    deleted["shift_assignments"] = cnt

    # 7. Salary Structure Assignments
    cnt = _sql_count("SELECT COUNT(*) FROM `tabSalary Structure Assignment` WHERE employee IN %s", (emp_names,))
    _sql_del("DELETE FROM `tabSalary Structure Assignment` WHERE employee IN %s", (emp_names,))
    deleted["salary_assignments"] = cnt

    # 8. Employees
    cnt = len(employees)
    _sql_del("DELETE FROM tabEmployee WHERE name IN %s", (emp_names,))
    deleted["employees"] = cnt

    if not dry_run:
        frappe.db.commit()

    total = sum(deleted.values())
    print("\n" + "=" * 50)
    print("DEMO DATA CLEAR COMPLETE")
    print("=" * 50)
    for k, v in deleted.items():
        print(f"  {k}: {v}")
    print(f"\nTotal: {total} records deleted")
    print("\nStructural data KEPT intact:")
    print("  Departments, Designations, Branches")
    print("  Shift Types, Shift Periods")
    print("  Leave Types, Holiday Lists")
    print("  Salary Structures, Salary Components")
    print("  Biometric Devices, Multi Period Settings")

    return deleted
