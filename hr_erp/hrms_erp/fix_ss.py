import frappe

def execute():
    """Create a new Salary Structure for Shahadhi employees with formula-based earnings."""
    new_name = "SH-هيكل رواتب الشاحذي"

    if frappe.db.exists("Salary Structure", new_name):
        print(f"Already exists: {new_name}")
        doc = frappe.get_doc("Salary Structure", new_name)
        doc.earnings = []
    else:
        doc = frappe.get_doc({
            "doctype": "Salary Structure",
            "name": new_name,
            "company": "الشاحذي",
            "payroll_frequency": "Monthly",
            "currency": "SAR",
        })

    components = [
        ("الراتب الأساسي", "BAS", "base"),
        ("بدل مواصلات", "TRN", "base * 0.20"),
        ("بدل مخاطر", "RISK", "base * 0.50"),
        ("بدل طبيعه عمل", "NAT", "base * 0.60"),
        ("بدل سكن", "HOU", "base * 0.15"),
    ]

    for comp_name, abbr, formula in components:
        doc.append("earnings", {
            "salary_component": comp_name,
            "abbr": abbr,
            "amount_based_on_formula": 1,
            "formula": formula,
            "amount": 0,
            "default_amount": 0,
        })

    try:
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created: {doc.name}")
        for e in doc.earnings:
            print(f"  {e.salary_component} ({e.abbr}): {e.formula}")
    except Exception as e:
        frappe.clear_messages()
        print(f"ERROR: {e}")

    # Now create Salary Structure Assignments
    print("\nCreating SSAs...")
    import codecs, csv, io

    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"
    try:
        with codecs.open(path, 'r', encoding='cp1256') as f:
            content = f.read()
    except:
        print("CSV not found")
        return

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
        salary_data[mobile] = {
            'basic': _num(row[16]) if len(row) > 16 else 0,
            'total': _num(row[12]) if len(row) > 12 else 0,
            'transport': _num(row[13]) if len(row) > 13 else 0,
            'risk': _num(row[14]) if len(row) > 14 else 0,
            'nature': _num(row[15]) if len(row) > 15 else 0,
        }

    all_emps = frappe.get_all("Employee",
        filters={"company": "الشاحذي"},
        fields=["name", "cell_number"],
    )

    # Cancel existing SSAs
    emp_names = [e.name for e in all_emps]
    if emp_names:
        old_ssas = frappe.get_all("Salary Structure Assignment",
            filters={"employee": ["in", emp_names]},
            fields=["name", "docstatus"],
        )
        for ssa in old_ssas:
            try:
                doc = frappe.get_doc("Salary Structure Assignment", ssa.name)
                if ssa.docstatus == 1:
                    doc.cancel()
                elif ssa.docstatus == 0:
                    doc.delete(ignore_permissions=True)
            except:
                frappe.clear_messages()
        frappe.db.commit()

    created = 0
    errors = []
    for emp in all_emps:
        mobile = (emp.cell_number or "").replace(" ", "").strip()
        sal = salary_data.get(mobile)
        if not sal or sal['basic'] <= 0:
            continue

        try:
            ssa = frappe.get_doc({
                "doctype": "Salary Structure Assignment",
                "employee": emp.name,
                "salary_structure": new_name,
                "from_date": "2025-01-01",
                "base": sal['basic'],
            })
            ssa.insert(ignore_permissions=True)
            ssa.submit()
            created += 1
        except Exception as e:
            frappe.clear_messages()
            errors.append(f"{emp.name}: {e}")

    frappe.db.commit()
    print(f"Created {created} SSAs")
    if errors:
        for err in errors[:5]:
            print(f"  ERROR: {err}")
