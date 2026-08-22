import frappe

def execute():
    # Check Payroll Entry fields
    meta = frappe.get_meta("Payroll Entry")
    print("Payroll Entry fields:")
    for f in meta.fields:
        if f.fieldtype not in ("Section Break", "Column Break", "Tab Break"):
            print(f"  {f.fieldname} ({f.fieldtype}) label={f.label}")

    # Check Salary Slip fields
    print("\nSalary Slip key fields:")
    meta2 = frappe.get_meta("Salary Slip")
    for f in meta2.fields:
        if f.fieldname in ("employee", "employee_name", "posting_date", "start_date",
            "end_date", "salary_structure", "currency", "net_pay", "gross_pay",
            "total_deductions", "payment_days", "payroll_entry", "mode_of_payment",
            "company", "status"):
            print(f"  {f.fieldname} ({f.fieldtype}) label={f.label}")

    # Check if YER exists
    cur = frappe.db.exists("Currency", "YER")
    print(f"\nCurrency YER exists: {cur}")

    # Check Mode of Payment
    mops = frappe.get_all("Mode of Payment", fields=["name", "type"])
    print(f"\nMode of Payment:")
    for m in mops:
        print(f"  {m.name} ({m.type})")
