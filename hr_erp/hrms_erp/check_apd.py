import frappe

def execute():
    meta = frappe.get_meta("Attendance Period Detail")
    for f in meta.fields:
        print(f"{f.fieldname} ({f.fieldtype})")
