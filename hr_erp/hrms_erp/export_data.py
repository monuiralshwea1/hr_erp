import frappe, json

def execute():
    data = {}

    emps = frappe.get_all("Employee",
        filters={"company": "الشاحذي"},
        fields=["name", "employee_name", "cell_number", "department", "branch",
                "designation", "date_of_joining", "status", "reports_to"],
        order_by="name",
    )
    data["employees"] = emps

    ssas = frappe.db.sql("""
        SELECT ssa.employee, e.employee_name, e.cell_number, e.department, e.branch,
               ssa.salary_structure, ssa.base, ssa.from_date, ssa.name as ssa_name
        FROM `tabSalary Structure Assignment` ssa
        JOIN `tabEmployee` e ON e.name = ssa.employee
        WHERE e.company = 'الشاحذي' AND ssa.docstatus = 1
        ORDER BY ssa.employee
    """, as_dict=True)
    data["ssas"] = ssas

    att_summary = frappe.db.sql("""
        SELECT a.employee, e.employee_name, e.branch, e.department,
               a.shift, a.status, COUNT(*) as cnt,
               SUM(a.working_hours) as total_hours,
               SUM(CASE WHEN a.late_entry = 1 THEN 1 ELSE 0 END) as late_days
        FROM `tabAttendance` a
        JOIN `tabEmployee` e ON e.name = a.employee
        WHERE e.company = 'الشاحذي' AND a.docstatus = 1
        GROUP BY a.employee, a.shift, a.status
        ORDER BY a.employee
    """, as_dict=True)
    data["att_summary"] = att_summary

    shift_data = frappe.db.sql("""
        SELECT st.name as shift_name, st.enable_multi_period,
               st.start_time, st.end_time,
               sp.period_number, sp.period_name,
               sp.start_time as p_start, sp.end_time as p_end, sp.is_break
        FROM `tabShift Type` st
        LEFT JOIN `tabShift Period` sp ON sp.parent = st.name
        WHERE st.name LIKE 'SH-%%'
        ORDER BY st.name, sp.period_number
    """, as_dict=True)
    data["shifts"] = shift_data

    pd_summary = frappe.db.sql("""
        SELECT apd.period_status, COUNT(*) as cnt,
               SUM(apd.working_hours) as total_hours,
               SUM(apd.late_minutes) as total_late
        FROM `tabAttendance Period Detail` apd
        JOIN `tabEmployee` e ON e.name = apd.employee
        WHERE e.company = 'الشاحذي'
        GROUP BY apd.period_status
    """, as_dict=True)
    data["pd_summary"] = pd_summary

    pd_emp = frappe.db.sql("""
        SELECT apd.employee, e.employee_name, apd.shift_type,
               apd.period_name, apd.period_status, COUNT(*) as cnt,
               SUM(apd.working_hours) as hours, SUM(apd.late_minutes) as late_min,
               SUM(apd.absent_hours) as absent_hrs
        FROM `tabAttendance Period Detail` apd
        JOIN `tabEmployee` e ON e.name = apd.employee
        WHERE e.company = 'الشاحذي'
        GROUP BY apd.employee, apd.shift_type, apd.period_name, apd.period_status
        ORDER BY apd.employee, apd.shift_type, apd.period_name
    """, as_dict=True)
    data["pd_emp"] = pd_emp

    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/_export.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, default=str, ensure_ascii=False)
    print(f"Exported to {path}")
    print(f"employees={len(emps)} ssas={len(ssas)} shifts={len(shift_data)}")
