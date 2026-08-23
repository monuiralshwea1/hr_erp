"""Quick count of Shahadhi data."""
import frappe

def execute():
    emps = frappe.db.count("Employee", {"company": "الشاحذي"})
    atts = frappe.db.count("Attendance", {"employee": ["like", "SH-HR-EMP-%"]})
    chkins = frappe.db.count("Employee Checkin", {"employee": ["like", "SH-HR-EMP-%"]})
    print(f"Employees: {emps}")
    print(f"Attendance: {atts}")
    print(f"Checkins: {chkins}")
