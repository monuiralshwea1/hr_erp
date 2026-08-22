import frappe

def execute():
    meta = frappe.get_meta("Employee")
    salary_fields = [f.fieldname for f in meta.fields if 'salary' in f.fieldname.lower() or 'basic' in f.fieldname.lower()]
    print("Employee salary-related fields:", salary_fields)

    # Check if basic_salary exists as custom field
    all_fields = [f.fieldname for f in meta.fields]
    print("All Employee fields:", all_fields[:50])
    print("...", all_fields[50:])

    # Also check if Salary Structure exists
    ss = frappe.get_all("Salary Structure", fields=["name"])
    print(f"\nSalary Structures: {len(ss)}")
    for s in ss:
        print(f"  {s.name}")

    # Check Salary Component
    sc = frappe.get_all("Salary Component", fields=["name", "salary_component_abbr"])
    print(f"\nSalary Components: {len(sc)}")
    for s in sc:
        print(f"  {s.name} ({s.salary_component_abbr})")

    # Check Salary Structure Assignment
    ssa = frappe.get_all("Salary Structure Assignment", fields=["name", "employee", "salary_structure"])
    print(f"\nSalary Structure Assignments: {len(ssa)}")
