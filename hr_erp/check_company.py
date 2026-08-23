"""Check existing company and structural data."""
import frappe


def execute():
    # Check companies
    companies = frappe.get_all("Company", fields=["name", "company_name", "abbr"])
    print("=== Companies ===")
    for c in companies:
        print(f"  {c.name} ({c.abbr})")

    # Check if الشاحذي exists
    shahadhi = frappe.db.exists("Company", {"company_name": ["like", "%الشاحذي%"]})
    print(f"\nالشاحذي exists: {shahadhi}")

    # Check departments
    depts = frappe.get_all("Department", fields=["name", "department_name", "company"])
    print(f"\n=== Departments ({len(depts)}) ===")
    for d in depts[:20]:
        print(f"  {d.name} - {d.department_name} ({d.company})")

    # Check branches
    branches = frappe.get_all("Branch", fields=["name", "branch"])
    print(f"\n=== Branches ({len(branches)}) ===")
    for b in branches:
        print(f"  {b.name}")

    # Check designations
    desigs = frappe.get_all("Designation", fields=["name", "designation_name"])
    print(f"\n=== Designations ({len(desigs)}) ===")
    for d in desigs:
        print(f"  {d.name}")

    # Check employment types
    emp_types = frappe.get_all("Employment Type", fields=["name", "employee_type_name"])
    print(f"\n=== Employment Types ({len(emp_types)}) ===")
    for e in emp_types:
        print(f"  {e.name}")

    # Check shift types
    shifts = frappe.get_all("Shift Type", fields=["name", "enable_multi_period"])
    print(f"\n=== Shift Types ({len(shifts)}) ===")
    for s in shifts:
        print(f"  {s.name} (multi_period={s.enable_multi_period})")
