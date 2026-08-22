import frappe

def execute():
    shifts = frappe.get_all("Shift Type", fields=["name", "enable_multi_period"])
    for s in shifts:
        periods = frappe.db.sql(
            "SELECT COUNT(*) as cnt FROM `tabShift Period` WHERE parent=%s", s.name, as_dict=True
        )
        cnt = periods[0].cnt if periods else 0
        print(f"{s.name} | multi={s.enable_multi_period} | periods={cnt}")

    # Check what shift names are in Shift Period
    all_parents = frappe.db.sql("SELECT DISTINCT parent FROM `tabShift Period`", as_list=True)
    print(f"\nShift Period parents: {[p[0] for p in all_parents]}")
