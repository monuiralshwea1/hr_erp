import frappe

def execute():
    # Check Shift Type meta for autoname
    meta = frappe.get_meta("Shift Type")
    print(f"Shift Type autoname: {meta.autoname}")
    print(f"Shift Type fields:")
    for f in meta.fields:
        if f.fieldname in ("shift_type_name", "name", "shift_name"):
            print(f"  {f.fieldname} (fieldtype={f.fieldtype}, label={f.label})")

    # Try creating a test shift type using the name field
    test_name = "TEST-SHIFT-DELETE-ME"
    try:
        doc = frappe.get_doc({
            "doctype": "Shift Type",
            "name": test_name,
            "enable_multi_period": 1,
            "start_time": "07:30:00",
            "end_time": "21:00:00",
        })
        doc.insert(ignore_permissions=True)
        print(f"\nCreated test: {doc.name}")
        frappe.delete_doc("Shift Type", doc.name)
        print("Deleted test")
    except Exception as e:
        print(f"\nError with name: {e}")
        frappe.clear_messages()

    # Try with shift_type_name field
    test_name2 = "TEST-SHIFT-2-DELETE"
    try:
        doc2 = frappe.get_doc({
            "doctype": "Shift Type",
            "shift_type_name": test_name2,
            "enable_multi_period": 1,
            "start_time": "07:30:00",
            "end_time": "21:00:00",
        })
        doc2.insert(ignore_permissions=True)
        print(f"\nCreated test2: {doc2.name}")
        frappe.delete_doc("Shift Type", doc2.name)
        print("Deleted test2")
    except Exception as e:
        print(f"\nError with shift_type_name: {e}")
        frappe.clear_messages()
