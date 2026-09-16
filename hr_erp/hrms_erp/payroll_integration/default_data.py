# -*- coding: utf-8 -*-
"""
البيانات الافتراضية لتكامل الرواتب — default_data.py
====================================================

تُنشأ تلقائياً عبر after_migrate (انظر hooks.py).
كل عنصر يُنشأ مرة واحدة فقط (idempotent).

الإيقاف: احذف السطر من after_migrate في hooks.py.

1. Salary Components (Late Deduction / Absence Deduction / Overtime 1.5 / 2.0)
2. Activity Types (Overtime 1.5 / Overtime 2.0)
3. ربط المكوّنات في HR ERP Payroll Settings
4. ضبط HR ERP Payroll Settings (تفعيل الخصومات والإضافي)
5. ضبط Multi Period Settings (تفعيل الإضافي)
6. تعيين الدوام الرسمي لجميع الموظفين النشطين
"""

import frappe
from frappe import _
from frappe.utils import cint, flt

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"
OFFICIAL_SHIFT = "دوام رسمي"


def create_default_data():
    """إنشاء البيانات الافتراضية — idempotent."""
    _create_salary_components()
    _create_activity_types()
    _link_settings_components()
    _configure_payroll_settings()
    _configure_multi_period_settings()
    frappe.db.commit()


# ------------------------------------------------------------------
# 1. Salary Components
# ------------------------------------------------------------------
def _create_salary_components():
    components = [
        ("Late Deduction", "خصم تأخير", "Deduction", "خصم دقائق التأخير من الراتب"),
        ("Absence Deduction", "خصم غياب", "Deduction", "خصم أيام الغياب من الراتب"),
        ("Overtime 1.5", "إضافي عادي", "Earning", "أجر ساعات العمل الإضافي بمعامل 1.5"),
        ("Overtime 2.0", "إضافي عطلة", "Earning", "أجر ساعات العمل في العطل الرسمية بمعامل 2.0"),
        ("بدل مخاطر", "بدل مخاطر", "Earning", "بدل مخاطر العمل"),
        ("بدل طبيعه عمل", "بدل طبيعه عمل", "Earning", "بدل طبيعة العمل"),
    ]
    for name, arabic, ctype, desc in components:
        if frappe.db.exists("Salary Component", name):
            continue
        doc = frappe.get_doc({
            "doctype": "Salary Component",
            "salary_component": name,
            "salary_component_abbr": "".join([w[0] for w in name.split()]).upper(),
            "type": ctype,
            "description": desc,
        })
        doc.insert(ignore_permissions=True)
        print(f"Created Salary Component: {name}")


# ------------------------------------------------------------------
# 2. Activity Types
# ------------------------------------------------------------------
def _create_activity_types():
    for activity in ["Overtime 1.5", "Overtime 2.0"]:
        if frappe.db.exists("Activity Type", activity):
            continue
        doc = frappe.get_doc({"doctype": "Activity Type", "activity_type": activity})
        doc.insert(ignore_permissions=True)
        print(f"Created Activity Type: {activity}")


# ------------------------------------------------------------------
# 3. Link components in settings
# ------------------------------------------------------------------
def _link_settings_components():
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return
    try:
        settings = frappe.get_doc(SETTINGS_DOCTYPE)
        updated = False
        if not settings.get("late_deduction_component"):
            settings.late_deduction_component = "Late Deduction"
            updated = True
        if not settings.get("absence_deduction_component"):
            settings.absence_deduction_component = "Absence Deduction"
            updated = True
        if not settings.get("overtime_15_activity"):
            settings.overtime_15_activity = "Overtime 1.5"
            updated = True
        if not settings.get("overtime_20_activity"):
            settings.overtime_20_activity = "Overtime 2.0"
            updated = True
        if updated:
            settings.save(ignore_permissions=True)
            print("Linked default components in HR ERP Payroll Settings")
    except Exception as e:
        frappe.log_error(f"hr_erp default_data link error: {e}")


# ------------------------------------------------------------------
# 4. Configure HR ERP Payroll Settings
# ------------------------------------------------------------------
def _configure_payroll_settings():
    if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
        return
    try:
        settings = frappe.get_doc(SETTINGS_DOCTYPE)
        updated = False

        # Late Deduction
        if not cint(settings.get("enable_late_deduction")):
            settings.enable_late_deduction = 1
            updated = True
        if flt(settings.get("late_deduction_factor") or 0) < 1:
            settings.late_deduction_factor = 1.0
            updated = True

        # Absence Deduction
        if not cint(settings.get("enable_absence_deduction")):
            settings.enable_absence_deduction = 1
            updated = True
        if flt(settings.get("absence_deduction_factor") or 0) < 1:
            settings.absence_deduction_factor = 1.0
            updated = True
        if not cint(settings.get("working_days_per_month")):
            settings.working_days_per_month = 30
            updated = True

        # Overtime Generation
        if not cint(settings.get("enable_overtime_generation")):
            settings.enable_overtime_generation = 1
            updated = True
        if flt(settings.get("overtime_threshold") or 0) < 1:
            settings.overtime_threshold = 30
            updated = True

        if updated:
            settings.save(ignore_permissions=True)
            print("Configured HR ERP Payroll Settings")
    except Exception as e:
        frappe.log_error(f"hr_erp configure_payroll_settings error: {e}")


# ------------------------------------------------------------------
# 5. Configure Multi Period Settings
# ------------------------------------------------------------------
def _configure_multi_period_settings():
    if not frappe.db.exists("DocType", "Multi Period Settings"):
        return
    try:
        mps = frappe.get_doc("Multi Period Settings")
        updated = False
        if not cint(mps.get("enable_overtime")):
            mps.enable_overtime = 1
            updated = True
        if flt(mps.get("overtime_threshold_minutes") or 0) < 1:
            mps.overtime_threshold_minutes = 30
            updated = True
        if updated:
            mps.save(ignore_permissions=True)
            print("Configured Multi Period Settings")
    except Exception as e:
        frappe.log_error(f"hr_erp configure_multi_period_settings error: {e}")


# ------------------------------------------------------------------
# 6. Assign official shift to all active employees
# ------------------------------------------------------------------
def set_default_shift_all(company=None):
    """تعيين الدوام الرسمي لجميع الموظفين النشطين — idempotent."""
    if not frappe.db.exists("Shift Type", OFFICIAL_SHIFT):
        print(f"Shift Type '{OFFICIAL_SHIFT}' does not exist — skipping assignment")
        return

    filters = {"status": "Active"}
    if company:
        filters["company"] = company

    employees = frappe.get_all("Employee", filters=filters, fields=["name", "default_shift"])
    updated = 0
    for emp in employees:
        if emp.default_shift == OFFICIAL_SHIFT:
            continue
        frappe.db.set_value("Employee", emp.name, "default_shift", OFFICIAL_SHIFT)
        updated += 1

    if updated:
        frappe.db.commit()
        print(f"Assigned {OFFICIAL_SHIFT} to {updated} employees")
    else:
        print("All active employees already on official shift")
