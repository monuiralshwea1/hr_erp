import frappe

def execute():
    cols = frappe.db.sql("SHOW COLUMNS FROM `tabSalary Slip`", as_dict=True)
    for c in cols:
        cn = c.get("Field", "").lower()
        if any(k in cn for k in ["earn", "deduc", "gross", "total", "net"]):
            print(f"  {c['Field']} ({c.get('Type', '')})")
