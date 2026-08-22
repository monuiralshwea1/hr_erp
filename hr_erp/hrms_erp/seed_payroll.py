"""
seed_payroll.py v2
=================
1. Delete old PE (wrong company)
2. Create Payroll Entries Jan-Aug 2026 for الشاحذي
3. Create + submit Salary Slips
"""
import frappe
from datetime import date
from calendar import monthrange

COMPANY = "الشاحذي"
SS_NAME = "SH-هيكل رواتب الشاحذي"
PAYABLE_ACCT = "2120 - رواتب واجبة الدفع - sh"
CASH_ACCT = "1110 - نقد - sh"


def _c():
    frappe.db.commit()


def execute():
    print("=" * 60)
    print("PAYROLL SEED v2 - YER - Jan to Aug 2026")
    print("=" * 60)

    _cleanup_old()
    _c()

    _create_all()
    _c()

    _summary()
    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


def _cleanup_old():
    """Cancel/delete all existing Payroll Entries."""
    print("\nCleaning old Payroll Entries...")
    pes = frappe.get_all("Payroll Entry", fields=["name", "docstatus"])
    for pe in pes:
        try:
            d = frappe.get_doc("Payroll Entry", pe.name)
            if pe.docstatus == 1:
                # First cancel salary slips
                slips = frappe.get_all("Salary Slip",
                    filters={"payroll_entry": pe.name, "docstatus": 1},
                    fields=["name"])
                for s in slips:
                    try:
                        frappe.get_doc("Salary Slip", s.name).cancel()
                    except Exception:
                        frappe.clear_messages()
                d.cancel()
            elif pe.docstatus == 0:
                d.delete(ignore_permissions=True)
        except Exception:
            frappe.clear_messages()
    frappe.db.commit()
    print(f"  Cleaned")

    # Also delete orphan salary slips (use frappe.delete_doc for safety)
    orphans = frappe.get_all("Salary Slip", filters={"company": COMPANY}, fields=["name"])
    for o in orphans:
        try:
            frappe.delete_doc("Salary Slip", o.name, force=True)
        except Exception:
            pass
    frappe.db.commit()
    print(f"  Deleted orphan salary slips")


def _create_all():
    """Create Payroll Entries for each month."""
    print("\nCreating Payroll Entries...")

    all_emps = frappe.get_all("Employee",
        filters={"company": COMPANY, "status": "Active"},
        fields=["name", "employee_name", "date_of_joining"],
    )

    months = []
    for m in range(1, 9):  # Jan to Aug 2026
        last_day = monthrange(2026, m)[1]
        months.append((date(2026, m, 1), date(2026, m, last_day)))

    total_pe = 0
    total_slips_created = 0
    total_slips_submitted = 0

    for start, end in months:
        month_label = start.strftime("%m/%Y")
        print(f"\n  --- {month_label} ---")

        # Filter active employees for this month
        active = [e for e in all_emps if (e.date_of_joining or date(2026, 1, 1)) <= end]
        if not active:
            print(f"  No active employees")
            continue

        try:
            pe = frappe.get_doc({
                "doctype": "Payroll Entry",
                "company": COMPANY,
                "posting_date": end,
                "start_date": start.strftime("%Y-%m-%d"),
                "end_date": end.strftime("%Y-%m-%d"),
                "currency": "YER",
                "exchange_rate": 1.0,
                "payroll_frequency": "Monthly",
                "payroll_payable_account": PAYABLE_ACCT,
                "payment_account": CASH_ACCT,
                "salary_structure": SS_NAME,
            })
            for emp in active:
                pe.append("employees", {
                    "employee": emp.name,
                    "employee_name": emp.employee_name,
                })
            pe.insert(ignore_permissions=True)
            print(f"  PE: {pe.name} ({len(active)} employees)")

            # Create salary slips
            pe.create_salary_slips()
            _c()

            # Submit salary slips
            slips = frappe.get_all("Salary Slip",
                filters={"payroll_entry": pe.name, "docstatus": 0},
                fields=["name"])
            submitted = 0
            for s in slips:
                try:
                    frappe.get_doc("Salary Slip", s.name).submit()
                    submitted += 1
                except Exception:
                    frappe.clear_messages()

            total_slips_created += len(slips)
            total_slips_submitted += submitted
            print(f"  Slips: {submitted}/{len(slips)} submitted")

            # Submit PE
            try:
                pe.submit()
                total_pe += 1
                print(f"  PE submitted")
            except Exception:
                frappe.clear_messages()

            _c()

        except Exception as e:
            frappe.clear_messages()
            print(f"  ERROR: {e}")

    print(f"\n  Total PEs submitted: {total_pe}")
    print(f"  Total slips created: {total_slips_created}")
    print(f"  Total slips submitted: {total_slips_submitted}")


def _summary():
    """Print summary of what was created."""
    print("\n--- Summary ---")

    pe_count = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabPayroll Entry`
        WHERE company=%s AND docstatus=1
    """, COMPANY, as_dict=True)
    print(f"  Payroll Entries: {pe_count[0].cnt}")

    ss_count = frappe.db.sql("""
        SELECT COUNT(*) as cnt FROM `tabSalary Slip`
        WHERE company=%s AND docstatus=1
    """, COMPANY, as_dict=True)
    print(f"  Submitted Salary Slips: {ss_count[0].cnt}")

    # Total gross/net
    totals = frappe.db.sql("""
        SELECT SUM(gross_pay) as gross, SUM(net_pay) as net,
               COUNT(DISTINCT employee) as emps
        FROM `tabSalary Slip`
        WHERE company=%s AND docstatus=1
    """, COMPANY, as_dict=True)
    if totals and totals[0].gross:
        print(f"  Total Gross Pay: {totals[0].gross:,.0f} YER")
        print(f"  Total Net Pay: {totals[0].net:,.0f} YER")
        print(f"  Unique Employees: {totals[0].emps}")

    # Per month breakdown
    monthly = frappe.db.sql("""
        SELECT start_date, COUNT(*) as cnt, SUM(gross_pay) as gross
        FROM `tabSalary Slip`
        WHERE company=%s AND docstatus=1
        GROUP BY start_date
        ORDER BY start_date
    """, COMPANY, as_dict=True)
    print(f"\n  Monthly breakdown:")
    for m in monthly:
        print(f"    {m.start_date}: {m.cnt} slips, {m.gross:,.0f} YER")
