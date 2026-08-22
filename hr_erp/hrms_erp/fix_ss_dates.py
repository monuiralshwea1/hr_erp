import frappe

def execute():
    # Update all submitted SSAs to have from_date = 2025-01-01
    count = frappe.db.sql("""
        UPDATE `tabSalary Structure Assignment`
        SET from_date='2025-01-01'
        WHERE salary_structure='SH-هيكل رواتب الشاحذي'
        AND docstatus=1
    """)
    frappe.db.commit()
    print(f"Updated {count} SSAs from_date to 2025-01-01")

    # Verify
    ssas = frappe.db.sql("""
        SELECT name, employee, from_date, salary_structure, docstatus
        FROM `tabSalary Structure Assignment`
        WHERE salary_structure='SH-هيكل رواتب الشاحذي' AND docstatus=1
        LIMIT 5
    """, as_dict=True)
    for s in ssas:
        print(f"  {s.name} | {s.employee} | from={s.from_date} | ds={s.docstatus}")
