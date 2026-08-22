import frappe
import codecs, csv, io

def execute():
    # Check CSV parsing
    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"
    try:
        with codecs.open(path, 'r', encoding='cp1256') as f:
            content = f.read()
    except Exception as e:
        print(f"CSV error: {e}")
        return

    def _num(s):
        try:
            return int(str(s).strip().replace(',', ''))
        except:
            return 0

    lines = content.split('\n')
    parsed = 0
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
        basic = _num(row[16]) if len(row) > 16 else 0
        transport = _num(row[13]) if len(row) > 13 else 0
        risk = _num(row[14]) if len(row) > 14 else 0
        nature = _num(row[15]) if len(row) > 15 else 0
        if parsed < 5:
            print(f"  mobile={mobile} basic={basic} transport={transport} risk={risk} nature={nature} cols={len(row)}")
        parsed += 1
    print(f"Total parsed: {parsed}")

    # Check SSA meta
    meta = frappe.get_meta("Salary Structure Assignment")
    print(f"\nSSA fields:")
    for f in meta.fields:
        print(f"  {f.fieldname} ({f.fieldtype}) label={f.label}")

    # Check Salary Structure Assignment Detail child
    meta2 = frappe.get_meta("Salary Detail")
    print(f"\nSalary Detail fields:")
    for f in meta2.fields:
        print(f"  {f.fieldname} ({f.fieldtype}) label={f.label}")
