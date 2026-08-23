"""
gen_standalone_seed.py - Generates a STANDALONE seed file with ALL data embedded
Run on source server: bench --site site1.local execute hr_erp.hrms_erp.gen_standalone_seed.execute
Output: shahadhi_full_seed.py (can run on ANY fresh ERPNext+HRMS install)
"""
import frappe
import json
from datetime import date, time, datetime, timedelta


def execute():
    D = {}

    # ── 1. Company ──
    comp = frappe.get_doc("Company", "الشاحذي")
    D["company"] = {
        "name": comp.name,
        "abbr": comp.abbr,
        "default_currency": comp.default_currency,
        "country": comp.country,
        "company_name": comp.company_name,
        "tax_id": comp.tax_id,
        "default_holiday_list": comp.default_holiday_list,
        "payroll_payable_account": comp.default_payroll_payable_account,
    }

    # Accounts needed
    accounts = frappe.get_all("Account",
        filters={"company": "الشاحذي"},
        fields=["name", "account_name", "account_type", "root_type", "parent_account"],
    )
    D["accounts"] = [
        {k: a.get(k) for k in ["name", "account_name", "account_type", "root_type", "parent_account"]}
        for a in accounts if a.name in (
            "2120 - رواتب واجبة الدفع - sh",
            "1110 - نقد - sh",
            comp.default_cash_account or "",
            comp.default_bank_account or "",
            comp.default_receivable_account or "",
            comp.default_expense_account or "",
        )
    ]
    # Cost centers
    ccs = frappe.get_all("Cost Center", filters={"company": "الشاحذي"}, fields=["name"])
    D["cost_centers"] = [c.name for c in ccs]

    # Modes of payment
    mops = frappe.get_all("Mode of Payment", fields=["name"])
    D["modes_of_payment"] = [m.name for m in mops]

    # Currencies
    curs = frappe.get_all("Currency", filters={"enabled": 1}, fields=["name"])
    D["currencies"] = [c.name for c in curs]

    # ── 2. Departments & Branches & Designations ──
    D["departments"] = frappe.get_all("Department",
        filters={"company": "الشاحذي"}, fields=["name", "department_name"])
    D["branches"] = frappe.get_all("Branch",
        filters={"branch": ["like", "%- sh"]}, fields=["name", "branch"])
    if not D["branches"]:
        D["branches"] = frappe.get_all("Branch",
            fields=["name", "branch"])
    D["designations"] = list(set(
        e["designation"] for e in frappe.get_all("Employee",
            filters={"company": "الشاحذي"}, fields=["designation"]) if e.designation))

    # ── 3. Holiday List ──
    hls = frappe.get_all("Holiday List",
        filters={"name": ["like", "SH-%"]},
        fields=["name", "holiday_list_name", "from_date", "to_date", "weekly_off"])
    for hl in hls:
        hl["holidays"] = frappe.get_all("Holiday",
            filters={"parent": hl.name},
            fields=["holiday_date", "description", "weekly_off"],
            order_by="holiday_date")
    D["holiday_lists"] = hls

    # ── 4. Employees ──
    emps = frappe.get_all("Employee",
        filters={"company": "الشاحذي"},
        fields=["*"],
        order_by="name",
    )
    keep_emp_fields = [
        "name", "employee_name", "first_name", "gender", "date_of_birth",
        "date_of_joining", "status", "cell_number", "personal_email",
        "department", "branch", "designation", "employment_type",
        "holiday_list", "company",
    ]
    D["employees"] = [{k: e.get(k) for k in keep_emp_fields} for e in emps]

    # ── 5. Salary Structures ──
    sss = frappe.get_all("Salary Structure",
        filters={"company": "الشاحذي"},
        fields=["name", "company", "is_active", "currency", "payroll_frequency",
                "docstatus", "mode_of_payment"],
    )
    for ss in sss:
        ss["earnings"] = frappe.get_all("Salary Detail",
            filters={"parent": ss.name, "parenttype": "Salary Structure",
                     "parentfield": "earnings"},
            fields=["salary_component", "abbr", "amount", "formula", "amount_based_on_formula",
                    "depends_on_payment_days", "do_not_include_in_total"],
            order_by="idx")
        ss["deductions"] = frappe.get_all("Salary Detail",
            filters={"parent": ss.name, "parenttype": "Salary Structure",
                     "parentfield": "deductions"},
            fields=["salary_component", "abbr", "amount", "formula", "amount_based_on_formula"],
            order_by="idx")
    D["salary_structures"] = sss

    # Salary Components used
    comps = set()
    for ss in sss:
        for e in ss["earnings"]:
            comps.add(e.salary_component)
    scs = []
    for c in sorted(comps):
        doc = frappe.db.get_value("Salary Component", c,
            ["name", "salary_component_abbr", "type"], as_dict=True)
        if doc:
            scs.append(dict(doc))
    D["salary_components"] = scs

    # ── 6. Salary Structure Assignments ──
    ssas = frappe.get_all("Salary Structure Assignment",
        filters={"docstatus": 1, "employee": ["in", [e["name"] for e in emps]]},
        fields=["employee", "salary_structure", "from_date", "base",
                "variable", "currency", "payroll_payable_account"],
        order_by="employee",
    )
    D["ssas"] = ssas

    # ── 7. Shift Types + Periods + Assignments ──
    sts = frappe.get_all("Shift Type",
        filters={"name": ["like", "SH-%"]},
        fields=["*"],
        order_by="name",
    )
    keep_st = ["name", "start_time", "end_time", "enable_multi_period",
               "late_entry_grace_period", "early_exit_grace_period",
               "enable_auto_attendance", "working_hours_threshold_for_half_day"]
    shift_types = []
    for st in sts:
        d = {k: st.get(k) for k in keep_st}
        periods = frappe.get_all("Shift Period",
            filters={"parent": st.name},
            fields=["period_number", "period_name", "start_time", "end_time",
                    "is_break", "late_grace_period", "early_exit_grace_period",
                    "minimum_working_hours", "enable_period_attendance", "notes"],
            order_by="period_number")
        # convert times
        def t2s(t):
            if t is None: return None
            if isinstance(t, timedelta):
                total = int(t.total_seconds())
                return f"{total//3600:02d}:{(total%3600)//60:02d}:{total%60:02d}"
            return str(t)
        d["shift_periods"] = [{
            "period_number": p.period_number, "period_name": p.period_name,
            "start_time": t2s(p.start_time), "end_time": t2s(p.end_time),
            "is_break": p.is_break, "late_grace_period": p.late_grace_period,
            "early_exit_grace_period": p.early_exit_grace_period,
            "minimum_working_hours": p.minimum_working_hours,
            "enable_period_attendance": p.enable_period_attendance,
            "notes": p.notes,
        } for p in periods]
        d["start_time"] = t2s(d["start_time"])
        d["end_time"] = t2s(d["end_time"])
        shift_types.append(d)
    D["shift_types"] = shift_types

    assignments = frappe.get_all("Shift Type Assignment Tool Log",
        fields=["*"]) if frappe.db.exists("DocType", "Shift Type Assignment Tool Log") else []

    # Shift assignments from Employee Checkin approach — use actual assignment table
    sa_table = "`tabShift Type Assignment`" if frappe.db.exists("DocType", "Shift Type Assignment") else None
    if not sa_table:
        # HRMS v15 uses tabShift Assignment? check
        pass

    shift_assignments = frappe.get_all("Shift Assignment",
        filters={"employee": ["in", [e["name"] for e in emps]]},
        fields=["name", "employee", "shift_type", "start_date", "end_date",
                "status", "company", "docstatus"],
        order_by="employee")
    for sa in shift_assignments:
        sa.pop("name")
    D["shift_assignments"] = shift_assignments

    # ── 8. Attendance + Period Details ──
    atts = frappe.get_all("Attendance",
        filters={"employee": ["in", [e["name"] for e in emps]], "docstatus": ["<", 2]},
        fields=["name", "employee", "attendance_date", "status", "shift",
                "in_time", "out_time", "working_hours", "late_entry", "early_exit",
                "docstatus"],
        order_by="employee, attendance_date")
    att_map = {}
    for a in atts:
        att_map[a.name] = a
        # times to strings
        for tf in ("in_time", "out_time"):
            if a.get(tf):
                a[tf] = str(a[tf])
        a.pop("name")

    pds = frappe.get_all("Attendance Period Detail",
        filters={"employee": ["in", [e["name"] for e in emps]]},
        fields=["parent", "employee", "attendance", "shift_type",
                "period_name", "period_number", "period_start", "period_end",
                "actual_check_in", "actual_check_out", "period_status",
                "working_hours", "late_minutes", "early_exit_minutes",
                "absent_hours", "overtime_hours"],
        order_by="parent, period_number")
    pd_by_parent = {}
    for pd in pds:
        for tf in ("period_start", "period_end", "actual_check_in", "actual_check_out"):
            if pd.get(tf):
                pd[tf] = str(pd[tf])
        pd_by_parent.setdefault(pd.parent, []).append({k: v for k, v in pd.items() if k != "parent"})

    attendance = []
    for name, a in att_map.items():
        a["period_details"] = pd_by_parent.get(name, [])
        attendance.append(a)
    D["attendance"] = attendance

    # ── 9. Payroll Entries ──
    pes = frappe.get_all("Payroll Entry",
        filters={"company": "الشاحذي", "docstatus": 1},
        fields=["name", "start_date", "end_date", "payroll_frequency",
                "currency", "exchange_rate", "number_of_employees",
                "salary_slips_created", "salary_slips_submitted",
                "payroll_payable_account", "payment_account",
                "posting_date"],
        order_by="start_date")
    payroll_entries = []
    emp_child_dt = "Payroll Employee Detail" if frappe.db.exists("DocType", "Payroll Employee Detail") else "Payroll Entry Employee"
    for pe in pes:
        employees = frappe.get_all(emp_child_dt,
            filters={"parent": pe.name},
            fields=["employee", "employee_name"],
            order_by="idx")
        pe_d = {k: v for k, v in pe.items()}
        pe_d["employees"] = employees
        payroll_entries.append(pe_d)
    D["payroll_entries"] = payroll_entries

    # ── 10. Salary Slips ──
    slips = frappe.get_all("Salary Slip",
        filters={"company": "الشاحذي", "docstatus": 1},
        fields=["name", "employee", "employee_name", "start_date", "end_date",
                "posting_date", "salary_structure", "currency",
                "gross_pay", "net_pay", "total_earnings", "total_deduction",
                "rounded_total", "payroll_entry", "mode_of_payment",
                "total_working_days", "payment_days", "leave_without_pay"],
        order_by="start_date, employee")
    slip_names = [s["name"] for s in slips]
    details = frappe.get_all("Salary Detail",
        filters={"parenttype": "Salary Slip", "parent": ["in", slip_names]},
        fields=["parent", "parentfield", "salary_component", "abbr", "amount"],
        order_by="parent, idx")
    by_parent = {}
    for d in details:
        by_parent.setdefault(d["parent"], {}).setdefault(
            d["parentfield"], []).append({
                "salary_component": d["salary_component"],
                "abbr": d["abbr"],
                "amount": float(d["amount"] or 0)})
    slips_out = []
    for s in slips:
        sd = {k: v for k, v in s.items()}
        sd["earnings"] = by_parent.get(s["name"], {}).get("earnings", [])
        sd["deductions"] = by_parent.get(s["name"], {}).get("deductions", [])
        slips_out.append(sd)
    D["salary_slips"] = slips_out

    # ── Write output ──
    out_path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_data.py"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("# -*- coding: utf-8 -*-\n")
        f.write('"""\n')
        f.write("shahadhi_data.py - بيانات شركة طه الشاحذي كاملة (مستقلة)\n")
        f.write("Generated: %s\n" % datetime.now())
        f.write("This file contains ALL data embedded - runs on any fresh ERPNext+HRMS install\n")
        f.write('"""\n\n')
        f.write("DATA = ")
        from pprint import pformat

        def _strify(v):
            if isinstance(v, dict):
                return {k: _strify(x) for k, x in v.items()}
            if isinstance(v, (list, tuple)):
                return [_strify(x) for x in v]
            if isinstance(v, (datetime, date)):
                s = v.isoformat(sep=" ") if isinstance(v, datetime) else v.isoformat()
                return s
            if hasattr(v, "isoformat"):  # time
                return v.isoformat()
            if isinstance(v, timedelta):
                return str(v.total_seconds())
            return v

        f.write(pformat(_strify(D), width=120))
        f.write("\n")

    import os
    size_kb = os.path.getsize(out_path) / 1024
    print(f"Generated: {out_path} ({size_kb:.0f} KB)")
    print(f"  company={1}, departments={len(D['departments'])}, branches={len(D['branches'])}")
    print(f"  employees={len(D['employees'])}")
    print(f"  salary_structures={len(D['salary_structures'])}, components={len(D['salary_components'])}")
    print(f"  ssas={len(D['ssas'])}")
    print(f"  shift_types={len(D['shift_types'])}, shift_assignments={len(D['shift_assignments'])}")
    print(f"  attendance={len(D['attendance'])} (with period details)")
    print(f"  payroll_entries={len(D['payroll_entries'])}")
    print(f"  salary_slips={len(D['salary_slips'])}")
