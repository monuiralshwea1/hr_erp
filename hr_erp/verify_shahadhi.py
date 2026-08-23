"""Verify Shahadhi data completeness."""
import frappe

def execute():
    print("=" * 60)
    print("SHAHADHI DATA REPORT")
    print("=" * 60)

    emps = frappe.get_all("Employee",
        filters={"company": "الشاحذي"},
        fields=["name", "employee_name", "branch", "department", "designation"],
        order_by="name",
    )
    print(f"\nEmployees: {len(emps)}")
    for e in emps:
        print(f"  {e.name} | {e.employee_name} | {e.branch} | {e.department} | {e.designation}")

    print(f"\n--- Attendance ---")
    atts = frappe.db.sql("""
        SELECT a.name, a.employee, a.attendance_date, a.status, a.working_hours,
               a.shift, a.late_entry, a.early_exit,
               (SELECT COUNT(*) FROM `tabAttendance Period Detail` WHERE parent=a.name) as pd_count
        FROM `tabAttendance` a
        WHERE a.employee LIKE 'SH-HR-EMP-%%'
        ORDER BY a.attendance_date DESC, a.employee
        LIMIT 30
    """, as_dict=True)
    print(f"  (showing last 30)")
    for a in atts:
        print(f"  {a.name} | {a.employee} | {a.attendance_date} | {a.status} | {a.working_hours}h | periods={a.pd_count}")

    # Period detail stats
    pd_stats = frappe.db.sql("""
        SELECT period_status, COUNT(*) as cnt
        FROM `tabAttendance Period Detail` pd
        JOIN `tabAttendance` a ON pd.parent = a.name
        WHERE a.employee LIKE 'SH-HR-EMP-%%'
        GROUP BY period_status
    """, as_dict=True)
    print(f"\n--- Period Details ---")
    for s in pd_stats:
        print(f"  {s.period_status}: {s.cnt}")

    total_pd = sum(s.cnt for s in pd_stats)
    total_att = frappe.db.count("Attendance", {"employee": ["like", "SH-HR-EMP-%"]})
    print(f"\nTotal Attendance: {total_att}")
    print(f"Total Period Details: {total_pd}")

    # Attendance per day
    daily = frappe.db.sql("""
        SELECT attendance_date, COUNT(*) as cnt
        FROM tabAttendance
        WHERE employee LIKE 'SH-HR-EMP-%%' AND docstatus = 1
        GROUP BY attendance_date
        ORDER BY attendance_date
    """, as_dict=True)
    print(f"\n--- Attendance by Date ---")
    for d in daily:
        print(f"  {d.attendance_date}: {d.cnt}")
