import frappe
from datetime import date, timedelta

def execute():
    hl_name = "SH-عطلات 2026"
    if not frappe.db.exists("Holiday List", hl_name):
        doc = frappe.get_doc({
            "doctype": "Holiday List",
            "holiday_list_name": hl_name,
            "from_date": "2026-01-01",
            "to_date": "2026-12-31",
            "weekly_off": "Friday",
        })
        # Add some holidays
        holidays = [
            ("2026-01-01", "رأس السنة"),
            ("2026-05-01", "عيد العمال"),
            ("2026-06-15", "عيد الفطر"),
            ("2026-08-22", "عيد الأضحى"),
            ("2026-09-23", "اليوم الوطني"),
            ("2026-09-16", "ليلة المولد"),
        ]
        for hdate, desc in holidays:
            doc.append("holidays", {
                "holiday_date": hdate,
                "description": desc,
                "weekly_off": 0,
            })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"Created Holiday List: {doc.name}")
    else:
        print(f"Holiday List exists: {hl_name}")

    # Set on all employees
    frappe.db.sql("""
        UPDATE `tabEmployee` SET holiday_list=%s WHERE company='الشاحذي'
    """, hl_name)
    frappe.db.commit()
    print(f"Set holiday_list on all employees")

    # Also set default on company
    frappe.db.set_value("Company", "الشاحذي", "default_holiday_list", hl_name)
    frappe.db.commit()
    print(f"Set default holiday list on company")
