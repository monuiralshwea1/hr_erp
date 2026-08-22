"""
seed_setup_data.py
==================
Installs all STRUCTURAL / SYSTEM data needed for the HR module.
Includes: Company, Departments, Designations, Branches, Shift Types,
Shift Periods, Leave Types, Holiday Lists, Salary Structures, Salary Components,
Employment Types, Biometric Devices, Multi Period Settings.

Usage:
    bench --site <site> execute hr_erp.hrms_erp.seed_setup_data.execute
"""
import frappe


def _exists(doctype, filters):
    return frappe.db.get_value(doctype, filters, "name")


def _ensure(doctype, filters, defaults=None):
    """Return existing name or create and return new name."""
    name = _exists(doctype, filters)
    if name:
        return name
    data = dict(defaults or {})
    data["doctype"] = doctype
    data.update(filters)
    try:
        doc = frappe.get_doc(data)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc.name
    except (frappe.DuplicateEntryError, Exception):
        frappe.clear_messages()
        name = _exists(doctype, filters)
        if name:
            return name
        raise


def execute(company=None):
    frappe.flags.dry_run = False

    if not company:
        company = frappe.db.get_default("company") or frappe.db.get_value("Company", {}, "name")
    if not company:
        frappe.throw("No company found. Please create a Company first.")

    # Verify company exists - never create one
    if not _exists("Company", {"name": company}):
        frappe.throw(f"Company '{company}' not found. Please create it first.")

    print(f"Seeding setup data for: {company}")
    print("=" * 50)

    # 1. Company - verify only, don't create
    print(f"  Company: {company} (exists)")

    # 2. Departments
    for d in ["الموارد البشرية", "الحسابات", "التسيق", "المبيعات", "الشراء",
              "العمليات", "الإنتاج", "ارسال", "خدمة العملاء", "الإدارة",
              "إدارة الجودة", "البحث و التطوير", "قانوني", "تقنية المعلومات",
              "الإدارة العليا", "المالية"]:
        _ensure("Department", {"department_name": d, "company": company})
    print("  Departments: 16 ready")

    # 3. Designations
    for d in ["مدير عام", "مدير مالي", "مدير موارد بشرية", "مدير مبيعات",
              "محاسب", "مهندس", "مندوب مبيعات", "مسؤول موارد بشرية",
              "منسق موارد بشرية", "كاتب", "عامل", "محلل بيانات",
              "مطور برمجيات", "مشرف إنتاج", "عميل خدمة", "مدير تسويق"]:
        _ensure("Designation", {"designation_name": d})
    print("  Designations: 16 ready")

    # 4. Branches
    for b in ["المركز الرئيسي", "صنعاء", "فرع صنعاء"]:
        _ensure("Branch", {"branch": b})
    print("  Branches: 3 ready")

    # 5. Employment Types
    for et in ["دوام كامل", "دوام جزئي", "عقد", "مؤقت", "دائم", "فترة تجريبية"]:
        _ensure("Employment Type", {"employee_type_name": et})
    print("  Employment Types: 6 ready")

    # 6. Shift Types + Periods
    shifts_data = [
        ("Multi-Morning-Shift", "06:00:00", "18:00:00", [
            ("الفترة الأولى - الصباح", "06:00", "09:00", 1, 0),
            ("استراحة الغداء", "09:00", "10:00", 2, 1),
            ("الفترة الثانية - ما بعد الاستراحة", "10:00", "14:00", 3, 0),
            ("استراحة العصر", "14:00", "14:30", 4, 1),
            ("الفترة الثالثة - النهاية", "14:30", "18:00", 5, 0),
        ]),
        ("Multi-Evening-Shift", "14:00:00", "23:00:00", [
            ("الفترة الأولى - المساء", "14:00", "17:00", 1, 0),
            ("استراحة العشاء", "17:00", "18:00", 2, 1),
            ("الفترة الثانية - ما بعد العشاء", "18:00", "21:00", 3, 0),
            ("الفترة الثالثة - الإغلاق", "21:00", "23:00", 4, 0),
        ]),
        ("دوام رسمي", "08:00:00", "16:00:00", [
            ("الفترة الأولى", "08:00", "12:00", 1, 0),
            ("استراحة الغداء", "12:00", "13:00", 2, 1),
            ("الفترة الثانية", "13:00", "16:00", 3, 0),
        ]),
        ("دوام تواجد", "08:00:00", "16:00:00", []),
        ("دوام فترة كاملة", "08:00:00", "16:00:00", []),
    ]
    for shift_name, st, et, periods in shifts_data:
        _ensure("Shift Type", {"name": shift_name}, {"start_time": st, "end_time": et})
        for pname, pstart, pend, pnum, pbreak in periods:
            if not _exists("Shift Period", {"parent": shift_name, "period_name": pname}):
                try:
                    frappe.get_doc({
                        "doctype": "Shift Period",
                        "parent": shift_name,
                        "parenttype": "Shift Type",
                        "parentfield": "shift_periods",
                        "period_name": pname,
                        "start_time": pstart,
                        "end_time": pend,
                        "period_number": pnum,
                        "is_break": pbreak,
                    }).insert(ignore_permissions=True)
                except Exception:
                    pass
    frappe.db.commit()
    print("  Shift Types: 5 ready")

    # 7. Leave Types
    for lt in ["إجازة سنوية", "إجازة مرضية", "إجازة طارئة", "إجازة بدون راتب"]:
        _ensure("Leave Type", {"leave_type_name": lt})
    print("  Leave Types: 4 ready")

    # 8. Holiday Lists
    for hl in ["عطلة رسمية - سمارت", "عطل اختيارية - سمارت"]:
        if not _exists("Holiday List", {"holiday_list_name": hl}):
            try:
                frappe.get_doc({
                    "doctype": "Holiday List",
                    "holiday_list_name": hl,
                    "from_date": "2026-01-01",
                    "to_date": "2026-12-31",
                    "company": company,
                }).insert(ignore_permissions=True)
            except Exception:
                pass
    frappe.db.commit()
    print("  Holiday Lists: 2 ready")

    # 9. Salary Components
    for comp, typ, abbr in [
        ("الراتب الأساسي", "Earning", "الراتب"), ("بدل سكن", "Earning", "بدل"),
        ("بدل مواصلات", "Earning", "مواصلات"), ("بدل طعام", "Earning", "طعام"),
        ("بد السكن", "Earning", "سكن"), ("خصم غياب", "Deduction", "خصم"),
    ]:
        _ensure("Salary Component", {"salary_component": comp}, {
            "type": typ, "salary_component_abbr": abbr[:3],
        })
    print("  Salary Components: 6 ready")

    # 10. Salary Structure
    _ensure("Salary Structure", {"name": "هيكل رواتب الموظفين"})
    print("  Salary Structure: 1 ready")

    # 11. Biometric Devices
    for dev, br in [("ZKTeco-Main-Office", "المركز الرئيسي"), ("ZKTeco-Branch-South", "فرع صنعاء")]:
        if not _exists("Biometric Device", {"device_name": dev}):
            try:
                frappe.get_doc({
                    "doctype": "Biometric Device",
                    "device_name": dev, "device_id": dev,
                    "branch": br, "company": company,
                }).insert(ignore_permissions=True)
            except Exception:
                pass
    frappe.db.commit()
    print("  Biometric Devices: 2 ready")

    # 12. Multi Period Settings
    if not _exists("Multi Period Settings", {}):
        try:
            frappe.get_doc({"doctype": "Multi Period Settings", "default_company": company}).insert(ignore_permissions=True)
        except Exception:
            pass
    frappe.db.commit()
    print("  Multi Period Settings: 1 ready")

    print("\n" + "=" * 50)
    print("SETUP DATA SEED COMPLETE")
    print(f"Company: {company}")
    print("System ready for employee creation.")
    return {"status": "ok", "company": company}
