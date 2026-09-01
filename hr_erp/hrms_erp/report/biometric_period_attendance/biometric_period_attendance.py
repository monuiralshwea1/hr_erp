# Copyright (c) 2026, moneer and contributors
# For license information, please see license.txt

import frappe
from frappe import _


STATUS_TRANSLATIONS = {
    "Present": "حاضر",
    "Absent": "غائب",
    "Late": "متأخر",
    "Half Day": "نصف يوم",
    "On Leave": "في إجازة",
    "Holiday": "عطلة رسمية",
    "Work From Home": "عمل من المنزل",
    "Break": "استراحة",
}


def execute(filters=None):
    filters = frappe._dict(filters or {})
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"fieldname": "employee", "label": _("Employee No."), "fieldtype": "Link", "options": "Employee", "width": 120},
        {"fieldname": "employee_name", "label": _("Employee Name"), "fieldtype": "Data", "width": 180},
        {"fieldname": "branch", "label": _("Branch"), "fieldtype": "Data", "width": 130},
        {"fieldname": "department", "label": _("Department"), "fieldtype": "Link", "options": "Department", "width": 140},
        {"fieldname": "company", "label": _("Company"), "fieldtype": "Link", "options": "Company", "width": 150},
        {"fieldname": "attendance_date", "label": _("Date"), "fieldtype": "Date", "width": 100},
        {"fieldname": "period_name", "label": _("Period"), "fieldtype": "Data", "width": 120},
        {"fieldname": "period_number", "label": _("Period No."), "fieldtype": "Int", "width": 70},
        {"fieldname": "actual_check_in", "label": _("Period In Time"), "fieldtype": "Data", "width": 100},
        {"fieldname": "actual_check_out", "label": _("Period Out Time"), "fieldtype": "Data", "width": 100},
        {"fieldname": "working_hours", "label": _("Working Hours"), "fieldtype": "Float", "width": 90},
        {"fieldname": "period_status", "label": _("Period Status"), "fieldtype": "Data", "width": 100},
        {"fieldname": "status", "label": _("Status"), "fieldtype": "Data", "width": 100},
        {"fieldname": "late_minutes", "label": _("Late (min)"), "fieldtype": "Float", "width": 80},
        {"fieldname": "early_exit_minutes", "label": _("Early Exit (min)"), "fieldtype": "Float", "width": 100},
        {"fieldname": "device_name_in", "label": _("Device (In)"), "fieldtype": "Data", "width": 120},
        {"fieldname": "device_name_out", "label": _("Device (Out)"), "fieldtype": "Data", "width": 120},
    ]


def _fmt_time(value):
    if value in (None, ""):
        return ""
    if hasattr(value, "strftime"):
        try:
            return value.strftime("%H:%M:%S")
        except Exception:
            return str(value)
    text = str(value)
    if len(text) >= 8 and text[2] == ":" and text[5] == ":":
        return text[:8]
    return text


def _translate_status(value):
    if value in (None, ""):
        return ""
    return STATUS_TRANSLATIONS.get(str(value), str(value))


def get_data(filters):
    from frappe.utils import getdate, today

    from_date = getdate(filters.get("from_date") or today())
    to_date = getdate(filters.get("to_date") or today())

    values = {"from_date": from_date, "to_date": to_date}
    conds1 = [
        "a.attendance_date BETWEEN %(from_date)s AND %(to_date)s",
        "a.docstatus = 1",
    ]
    conds2 = list(conds1)

    if filters.get("employee"):
        values["employee"] = filters.get("employee")
        conds1.append("a.employee = %(employee)s")
        conds2.append("a.employee = %(employee)s")
    if filters.get("period_name"):
        values["period_name"] = filters.get("period_name")
        conds1.append("apd.period_name = %(period_name)s")
        conds2.append("1 = 0")
    if filters.get("branch"):
        values["branch"] = filters.get("branch")
        conds1.append("emp.branch = %(branch)s")
        conds2.append("emp.branch = %(branch)s")
    if filters.get("department"):
        values["department"] = filters.get("department")
        conds1.append("a.department = %(department)s")
        conds2.append("a.department = %(department)s")
    if filters.get("company"):
        values["company"] = filters.get("company")
        conds1.append("a.company = %(company)s")
        conds2.append("a.company = %(company)s")
    if filters.get("status"):
        values["status"] = filters.get("status")
        conds1.append("a.status = %(status)s")
        conds2.append("a.status = %(status)s")

    query = """
        {part1}
        UNION ALL
        {part2}
        ORDER BY attendance_date, employee, period_number
    """.format(
        part1="""
            SELECT
                apd.employee AS employee,
                COALESCE(a.employee_name, emp.employee_name) AS employee_name,
                emp.branch AS branch,
                a.department AS department,
                a.company AS company,
                a.attendance_date AS attendance_date,
                apd.period_name AS period_name,
                apd.period_number AS period_number,
                apd.actual_check_in AS check_in,
                apd.actual_check_out AS check_out,
                apd.working_hours AS working_hours,
                apd.period_status AS period_status,
                a.status AS status,
                apd.late_minutes AS late_minutes,
                apd.early_exit_minutes AS early_exit_minutes,
                apd.device_name_in AS device_name_in,
                apd.device_name_out AS device_name_out
            FROM `tabAttendance Period Detail` apd
            INNER JOIN `tabAttendance` a ON a.name = apd.parent
            LEFT JOIN `tabEmployee` emp ON emp.name = apd.employee
            WHERE {conds1}
        """,
        part2="""
            SELECT
                a.employee AS employee,
                a.employee_name AS employee_name,
                emp.branch AS branch,
                a.department AS department,
                a.company AS company,
                a.attendance_date AS attendance_date,
                "" AS period_name,
                0 AS period_number,
                a.in_time AS check_in,
                a.out_time AS check_out,
                a.working_hours AS working_hours,
                "" AS period_status,
                a.status AS status,
                0 AS late_minutes,
                0 AS early_exit_minutes,
                "" AS device_name_in,
                "" AS device_name_out
            FROM `tabAttendance` a
            LEFT JOIN `tabEmployee` emp ON emp.name = a.employee
            WHERE {conds2}
              AND NOT EXISTS (SELECT 1 FROM `tabAttendance Period Detail` x WHERE x.parent = a.name)
        """,
    ).format(conds1=" AND ".join(conds1), conds2=" AND ".join(conds2))

    rows = frappe.db.sql(query, values, as_dict=True)
    for row in rows:
        row["check_in"] = _fmt_time(row.get("check_in"))
        row["check_out"] = _fmt_time(row.get("check_out"))
        row["period_status"] = _translate_status(row.get("period_status"))
        row["status"] = _translate_status(row.get("status"))
        row["actual_check_in"] = row.pop("check_in")
        row["actual_check_out"] = row.pop("check_out")
    return rows