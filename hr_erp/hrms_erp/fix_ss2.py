import frappe
import codecs, csv, io

def execute():
    """Fix failed SSAs by using employee's actual date_of_joining."""
    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"
    with codecs.open(path, 'r', encoding='cp1256') as f:
        content = f.read()

    def _num(s):
        try:
            return int(str(s).strip().replace(',', ''))
        except:
            return 0

    salary_data = {}
    lines = content.split('\n')
    for line in lines[2:]:
        if not line.strip() or '#NAME' in line:
            continue
        reader = csv.reader(io.StringIO(line))
        try:
            row = next(reader)
        except:
            continue
        if len(row) < 20:
            continue
        mobile = row[3].strip().replace(' ', '') if len(row) > 3 else ''
        if not mobile:
            continue
        salary_data[mobile] = _num(row[16]) if len(row) > 16 else 0

    new_name = "SH-هيكل رواتب الشاحذي"

    all_emps = frappe.get_all("Employee",
        filters={"company": "الشاحذي"},
        fields=["name", "cell_number", "date_of_joining"],
    )

    # Find employees without SSA
    existing_ssas = frappe.get_all("Salary Structure Assignment",
        filters={"salary_structure": new_name, "docstatus": 1},
        fields=["employee"],
    )
    has_ssa = {s.employee for s in existing_ssas}

    created = 0
    for emp in all_emps:
        if emp.name in has_ssa:
            continue
        mobile = (emp.cell_number or "").replace(" ", "").strip()
        basic = salary_data.get(mobile, 0)
        if basic <= 0:
            continue

        join_date = emp.date_of_joining or "2025-01-01"
        try:
            ssa = frappe.get_doc({
                "doctype": "Salary Structure Assignment",
                "employee": emp.name,
                "salary_structure": new_name,
                "from_date": join_date,
                "base": basic,
            })
            ssa.insert(ignore_permissions=True)
            ssa.submit()
            created += 1
            print(f"  Created: {emp.name} base={basic} from={join_date}")
        except Exception as e:
            frappe.clear_messages()
            print(f"  ERROR: {emp.name}: {e}")

    frappe.db.commit()
    print(f"\nCreated {created} additional SSAs")

    # Final count
    total = frappe.db.count("Salary Structure Assignment",
        filters={"salary_structure": new_name, "docstatus": 1})
    print(f"Total active SSAs for {new_name}: {total}")
