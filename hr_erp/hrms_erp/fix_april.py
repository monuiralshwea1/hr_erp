"""
fix_april.py - Create April 2026 Payroll Entry + slips, and fix PE counts
"""
import frappe
from frappe.utils import getdate, add_days

COMPANY = "الشاحذي"
SS_NAME = "SH-هيكل رواتب الشاحذي"

def execute():
    print("=" * 60)
    print("FIX APRIL 2026 + UPDATE PE COUNTS")
    print("=" * 60)

    # Step 1: Create April 2026 Payroll Entry
    apr_start = getdate("2026-04-01")
    apr_end = getdate("2026-04-30")

    existing = frappe.db.exists("Payroll Entry", {
        "company": COMPANY,
        "start_date": apr_start,
        "end_date": apr_end,
        "docstatus": 1,
    })

    if not existing:
        print("\n  Creating April 2026 Payroll Entry...")
        employees = frappe.get_all("Employee",
            filters={"company": COMPANY, "status": "Active",
                     "date_of_joining": ("<=", apr_end)},
            fields=["name", "employee_name", "date_of_joining"],
        )
        pe = frappe.get_doc({
            "doctype": "Payroll Entry",
            "company": COMPANY,
            "start_date": str(apr_start),
            "end_date": str(apr_end),
            "payroll_frequency": "Monthly",
            "currency": "YER",
            "exchange_rate": 1.0,
            "payroll_payable_account": "2120 - رواتب واجبة الدفع - sh",
            "payment_account": "1110 - نقد - sh",
            "mode_of_payment": "نقد",
            "department": None,
        })
        for emp in employees:
            pe.append("employees", {
                "employee": emp.name,
                "employee_name": emp.employee_name,
                "joining_date": str(emp.date_of_joining),
            })
        pe.insert(ignore_permissions=True)
        pe.submit()
        print(f"  PE created: {pe.name} ({len(employees)} employees)")
        pe_name = pe.name
    else:
        print(f"  April PE exists: {existing}")
        pe_name = existing

    # Step 2: Create April salary slips
    print("\n  Creating April salary slips...")
    created = 0
    submitted = 0
    employees = frappe.get_all("Employee",
        filters={"company": COMPANY, "status": "Active",
                 "date_of_joining": ("<=", apr_end)},
        fields=["name"],
    )
    for emp in employees:
        existing_slip = frappe.db.exists("Salary Slip", {
            "employee": emp.name,
            "start_date": apr_start,
            "end_date": apr_end,
        })
        if existing_slip:
            continue
        try:
            slip = frappe.get_doc({
                "doctype": "Salary Slip",
                "employee": emp.name,
                "company": COMPANY,
                "start_date": str(apr_start),
                "end_date": str(apr_end),
                "posting_date": str(apr_end),
                "salary_structure": SS_NAME,
                "currency": "YER",
                "payroll_entry": pe_name,
                "mode_of_payment": "نقد",
            })
            slip.insert(ignore_permissions=True)
            created += 1
            try:
                slip.submit()
                submitted += 1
            except Exception as e:
                frappe.clear_messages()
                print(f"    SUBMIT ERR {emp.name}: {e}")
        except Exception as e:
            frappe.clear_messages()
            print(f"    INSERT ERR {emp.name}: {e}")

        if created % 20 == 0 and created > 0:
            frappe.db.commit()

    frappe.db.commit()
    print(f"  April: Created={created}, Submitted={submitted}")

    # Step 3: Update all Payroll Entry counts
    print("\n  Updating Payroll Entry counts...")
    pes = frappe.get_all("Payroll Entry",
        filters={"company": COMPANY, "docstatus": 1},
        fields=["name", "start_date"],
        order_by="start_date",
    )
    for pe_info in pes:
        pe_doc = frappe.get_doc("Payroll Entry", pe_info.name)
        slips = frappe.get_all("Salary Slip",
            filters={"employee": ["in", [e.employee for e in pe_doc.employees]],
                     "start_date": pe_info.start_date,
                     "docstatus": 1},
            fields=["name"],
        )
        created_count = frappe.db.count("Salary Slip", {
            "employee": ["in", [e.employee for e in pe_doc.employees]],
            "start_date": pe_info.start_date,
        })
        frappe.db.set_value("Payroll Entry", pe_info.name, {
            "salary_slips_created": created_count,
            "salary_slips_submitted": len(slips),
        })
        print(f"    {pe_info.name} ({pe_info.start_date}): created={created_count}, submitted={len(slips)}")
    frappe.db.commit()

    # Step 4: Final summary
    print("\n  " + "=" * 50)
    print("  FINAL SUMMARY")
    print("  " + "=" * 50)
    summary = frappe.db.sql("""
        SELECT start_date, COUNT(*) as cnt, SUM(gross_pay) as gross, SUM(net_pay) as net
        FROM `tabSalary Slip`
        WHERE company=%s AND docstatus=1
        GROUP BY start_date
        ORDER BY start_date
    """, COMPANY, as_dict=True)
    total_gross = 0
    total_net = 0
    total_slips = 0
    for s in summary:
        total_gross += s.gross or 0
        total_net += s.net or 0
        total_slips += s.cnt
        print(f"    {s.start_date}: {s.cnt} slips | Gross: {(s.gross or 0):,.0f} YER | Net: {(s.net or 0):,.0f} YER")
    print(f"  " + "-" * 50)
    print(f"  TOTAL: {total_slips} slips | Gross={total_gross:,.0f} YER | Net={total_net:,.0f} YER")

    pe_count = frappe.db.count("Payroll Entry", {"company": COMPANY, "docstatus": 1})
    print(f"  Payroll Entries: {pe_count}")
    print("=" * 60)
