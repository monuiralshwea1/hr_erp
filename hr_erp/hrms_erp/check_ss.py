import frappe

def execute():
    # Check Salary Structure details
    ss = frappe.get_doc("Salary Structure", "هيكل رواتب الموظفين")
    print(f"Salary Structure: {ss.name}")
    for e in ss.earnings:
        print(f"  EARN: {e.salary_component} ({e.abbr}) formula={e.amount_based_on_formula} formula_val={e.formula if hasattr(e, 'formula') else 'N/A'} amount={e.amount}")
    for d in ss.deductions:
        print(f"  DED: {d.salary_component} ({d.abbr}) formula={d.amount_based_on_formula} formula_val={d.formula if hasattr(d, 'formula') else 'N/A'} amount={d.amount}")

    # Check existing SSAs
    ssas = frappe.get_all("Salary Structure Assignment",
        filters={"employee": ["in", frappe.get_all("Employee", filters={"company": "الشاحذي"}, pluck="name")]},
        fields=["name", "employee", "employee_name", "salary_structure", "base", "docstatus"],
    )
    print(f"\nShahadhi SSAs: {len(ssas)}")
    for s in ssas:
        print(f"  {s.name} | {s.employee} | {s.employee_name} | base={s.base} | docstatus={s.docstatus}")

    # Check Salary Component for allowances
    comps = frappe.get_all("Salary Component", fields=["name", "salary_component_abbr", "type"])
    print(f"\nSalary Components:")
    for c in comps:
        print(f"  {c.name} ({c.salary_component_abbr}) type={c.type}")
