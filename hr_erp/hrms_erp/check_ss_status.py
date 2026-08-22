import frappe

def execute():
    # Check SSA status
    ssas = frappe.db.sql("""
        SELECT name, employee, from_date, salary_structure, docstatus
        FROM `tabSalary Structure Assignment`
        WHERE salary_structure='SH-هيكل رواتب الشاحذي'
        ORDER BY employee, from_date
    """, as_dict=True)
    print(f"Total SSAs: {len(ssas)}")
    for s in ssas[:5]:
        print(f"  {s.name} | emp={s.employee} | from={s.from_date} | ds={s.docstatus}")

    # Check for duplicates per employee
    emp_counts = {}
    for s in ssas:
        emp_counts.setdefault(s.employee, []).append(s)
    dupes = {k: v for k, v in emp_counts.items() if len(v) > 1}
    print(f"\nEmployees with duplicate SSAs: {len(dupes)}")
    for emp, records in list(dupes.items())[:5]:
        for r in records:
            print(f"  {emp} | {r.name} | from={r.from_date} | ds={r.docstatus}")

    # Check status distribution
    statuses = {}
    for s in ssas:
        statuses[s.docstatus] = statuses.get(s.docstatus, 0) + 1
    print(f"\nBy docstatus: {statuses}")
