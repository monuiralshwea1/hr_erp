"""
create_slips.py - Create salary slips directly for each Payroll Entry
"""
import frappe
from datetime import date
from calendar import monthrange

COMPANY = "الشاحذي"
SS_NAME = "SH-هيكل رواتب الشاحذي"


def execute():
    print("Creating Salary Slips for all Payroll Entries...")

    pes = frappe.get_all("Payroll Entry",
        filters={"company": COMPANY, "docstatus": 1},
        fields=["name", "start_date", "end_date"],
        order_by="start_date",
    )

    total_created = 0
    total_submitted = 0

    for pe_doc in pes:
        pe = frappe.get_doc("Payroll Entry", pe_doc.name)
        month_label = pe.start_date.strftime("%m/%Y")
        print(f"\n  --- {month_label} ({pe.name}) ---")

        created = 0
        submitted = 0
        for emp_row in pe.employees:
            emp_name = emp_row.employee
            if not emp_name:
                continue

            # Check if slip already exists
            existing = frappe.db.exists("Salary Slip", {
                "employee": emp_name,
                "start_date": pe.start_date,
                "end_date": pe.end_date,
            })
            if existing:
                print(f"    EXISTS: {emp_name}")
                continue

            try:
                slip = frappe.get_doc({
                    "doctype": "Salary Slip",
                    "employee": emp_name,
                    "company": COMPANY,
                    "start_date": pe.start_date.strftime("%Y-%m-%d"),
                    "end_date": pe.end_date.strftime("%Y-%m-%d"),
                    "posting_date": pe.end_date.strftime("%Y-%m-%d"),
                    "salary_structure": SS_NAME,
                    "currency": "YER",
                    "payroll_entry": pe.name,
                    "mode_of_payment": "نقد",
                })
                slip.insert(ignore_permissions=True)
                created += 1

                # Submit
                try:
                    slip.submit()
                    submitted += 1
                except Exception as e:
                    frappe.clear_messages()
                    print(f"    SUBMIT ERR {emp_name}: {e}")

            except Exception as e:
                frappe.clear_messages()
                print(f"    INSERT ERR {emp_name}: {e}")

            if created % 20 == 0 and created > 0:
                frappe.db.commit()

        frappe.db.commit()
        total_created += created
        total_submitted += submitted
        print(f"  Created: {created}, Submitted: {submitted}")

    print(f"\n  Total Created: {total_created}")
    print(f"  Total Submitted: {total_submitted}")

    # Summary
    summary = frappe.db.sql("""
        SELECT start_date, COUNT(*) as cnt, SUM(gross_pay) as gross, SUM(net_pay) as net
        FROM `tabSalary Slip`
        WHERE company=%s AND docstatus=1
        GROUP BY start_date
        ORDER BY start_date
    """, COMPANY, as_dict=True)
    print(f"\n  Monthly Summary:")
    total_gross = 0
    total_net = 0
    for s in summary:
        total_gross += s.gross or 0
        total_net += s.net or 0
        print(f"    {s.start_date}: {s.cnt} slips | Gross: {(s.gross or 0):,.0f} YER | Net: {(s.net or 0):,.0f} YER")
    print(f"  TOTAL: Gross={total_gross:,.0f} YER | Net={total_net:,.0f} YER")
