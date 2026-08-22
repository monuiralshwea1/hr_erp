"""
seed_demo_employees.py
======================
Installs DEMO employees, shift assignments, checkins, and processes
multi-period attendance using the engine.

Usage:
    bench --site <site> execute hr_erp.hrms_erp.seed_demo_employees.execute
"""
import frappe
from datetime import datetime, timedelta, time as dt_time
import random


def _c():
    if not frappe.flags.get("dry_run"):
        frappe.db.commit()


def execute(company=None, employee_count=20):
    frappe.flags.dry_run = False

    if not company:
        company = frappe.db.get_default("company") or frappe.db.get_value("Company", {}, "name")
    if not company:
        frappe.throw("No company found. Run seed_setup_data first.")

    print(f"Seeding demo employees for company: {company}")
    print("=" * 50)

    dept = frappe.db.get_value("Department", {"company": company, "department_name": "الموارد البشرية"}, "name")
    if not dept:
        dept = frappe.db.get_value("Department", {"company": company}, "name")

    designation = frappe.db.get_value("Designation", {"designation_name": "محاسب"}, "name") or frappe.db.get_value("Designation", {}, "name")
    employment_type = frappe.db.get_value("Employment Type", {"employee_type_name": "دوام كامل"}, "name") or frappe.db.get_value("Employment Type", {}, "name")
    branch = frappe.db.get_value("Branch", {"branch": "المركز الرئيسي"}, "name") or frappe.db.get_value("Branch", {}, "name")
    salary_structure = frappe.db.get_value("Salary Structure", {"name": "هيكل رواتب الموظفين"}, "name")

    morning_shift = "Multi-Morning-Shift"
    evening_shift = "Multi-Evening-Shift"

    employees_data = _get_employee_list()[:employee_count]
    created = []
    today = datetime.now().date()

    for idx, ed in enumerate(employees_data, 1):
        emp_name = ed["first_name"] + " " + ed["last_name"]
        existing = frappe.db.get_value("Employee", {"employee_name": emp_name, "company": company}, "name")
        if existing:
            created.append(existing)
            print(f"  [{idx}] EXISTS: {existing} | {emp_name}")
            continue

        emp_desig = frappe.db.get_value("Designation", {"designation_name": ed["designation"]}, "name") or designation
        emp_dept = frappe.db.get_value("Department", {"department_name": ed["department"], "company": company}, "name") or dept

        try:
            emp_doc = frappe.get_doc({
                "doctype": "Employee",
                "employee_name": emp_name,
                "first_name": ed["first_name"],
                "last_name": ed["last_name"],
                "gender": ed["gender"],
                "company": company,
                "department": emp_dept,
                "designation": emp_desig,
                "employment_type": employment_type,
                "branch": branch,
                "date_of_birth": "1990-01-15",
                "date_of_joining": "2024-01-01",
                "status": "Active",
                "cell_number": "+96777" + str(random.randint(100000, 999999)),
            })
            emp_doc.insert(ignore_permissions=True)
            _c()
            created.append(emp_doc.name)
            print(f"  [{idx}] Created: {emp_doc.name} | {emp_name}")

            _create_salary_assignment(emp_doc.name, ed["basic_salary"], salary_structure, company)

            emp_shift = morning_shift if ed["shift"] == "morning" else evening_shift
            _create_shift_assignment(emp_doc.name, emp_shift)

        except Exception as e:
            frappe.clear_messages()
            print(f"  [{idx}] ERROR: {emp_name} - {str(e)[:60]}")

    print(f"\nEmployees created: {len(created)}")

    if created:
        _create_multiperiod_attendance(created, company, today)

    print("\n" + "=" * 50)
    print("DEMO DATA SEED COMPLETE")
    print("=" * 50)
    return created


def _get_employee_list():
    return [
        {"first_name": "أحمد", "last_name": "الشرعبي", "gender": "Male", "designation": "مدير عام", "department": "الإدارة", "basic_salary": 850000, "shift": "morning"},
        {"first_name": "فاطمة", "last_name": "العبسي", "gender": "Female", "designation": "مدير مالي", "department": "الحسابات", "basic_salary": 750000, "shift": "morning"},
        {"first_name": "خالد", "last_name": "الحمادي", "gender": "Male", "designation": "مدير موارد بشرية", "department": "الموارد البشرية", "basic_salary": 700000, "shift": "morning"},
        {"first_name": "سمير", "last_name": "المقطري", "gender": "Male", "designation": "مدير مبيعات", "department": "المبيعات", "basic_salary": 680000, "shift": "evening"},
        {"first_name": "نور", "last_name": "المخلافي", "gender": "Female", "designation": "محاسب", "department": "الحسابات", "basic_salary": 450000, "shift": "morning"},
        {"first_name": "محمد", "last_name": "الدبعي", "gender": "Male", "designation": "مهندس", "department": "العمليات", "basic_salary": 550000, "shift": "evening"},
        {"first_name": "عبدالرزاق", "last_name": "الأسودي", "gender": "Male", "designation": "مندوب مبيعات", "department": "المبيعات", "basic_salary": 350000, "shift": "evening"},
        {"first_name": "أمل", "last_name": "الجابري", "gender": "Female", "designation": "كاتب", "department": "الإدارة", "basic_salary": 320000, "shift": "morning"},
        {"first_name": "يوسف", "last_name": "الشامي", "gender": "Male", "designation": "مهندس", "department": "تقنية المعلومات", "basic_salary": 600000, "shift": "morning"},
        {"first_name": "عادل", "last_name": "العريقي", "gender": "Male", "designation": "مسؤول موارد بشرية", "department": "الموارد البشرية", "basic_salary": 400000, "shift": "evening"},
        {"first_name": "سامي", "last_name": "المطري", "gender": "Male", "designation": "محلل بيانات", "department": "الإدارة", "basic_salary": 420000, "shift": "morning"},
        {"first_name": "هدى", "last_name": "الحوثي", "gender": "Female", "designation": "مسؤول موارد بشرية", "department": "الموارد البشرية", "basic_salary": 380000, "shift": "evening"},
        {"first_name": "بلال", "last_name": "ثابت", "gender": "Male", "designation": "مهندس", "department": "العمليات", "basic_salary": 520000, "shift": "morning"},
        {"first_name": "عبير", "last_name": "الذبحاني", "gender": "Female", "designation": "كاتب", "department": "خدمة العملاء", "basic_salary": 300000, "shift": "evening"},
        {"first_name": "ماجد", "last_name": "العواضي", "gender": "Male", "designation": "مشرف إنتاج", "department": "الإنتاج", "basic_salary": 480000, "shift": "morning"},
        {"first_name": "سلوى", "last_name": "الرميمة", "gender": "Female", "designation": "كاتب", "department": "خدمة العملاء", "basic_salary": 310000, "shift": "evening"},
        {"first_name": "جمال", "last_name": "بازرعة", "gender": "Male", "designation": "مسؤول مشتريات", "department": "الشراء", "basic_salary": 430000, "shift": "morning"},
        {"first_name": "وضاح", "last_name": "النهاري", "gender": "Male", "designation": "مسؤول مشتريات", "department": "الشراء", "basic_salary": 410000, "shift": "evening"},
        {"first_name": "ريم", "last_name": "السياني", "gender": "Female", "designation": "منسق موارد بشرية", "department": "الموارد البشرية", "basic_salary": 370000, "shift": "morning"},
        {"first_name": "منير", "last_name": "الشويع", "gender": "Male", "designation": "مدير عام", "department": "الإدارة", "basic_salary": 900000, "shift": "evening"},
    ]


def _create_salary_assignment(employee_name, basic_salary, salary_structure, company):
    if not salary_structure:
        return
    existing = frappe.db.get_value("Salary Structure Assignment", {
        "employee": employee_name, "salary_structure": salary_structure
    }, "name")
    if existing:
        return
    try:
        frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": employee_name,
            "salary_structure": salary_structure,
            "from_date": "2024-01-01",
            "company": company,
        }).insert(ignore_permissions=True)
        _c()
    except Exception:
        frappe.clear_messages()


def _create_shift_assignment(employee_name, shift_type):
    if not shift_type:
        return
    existing = frappe.db.get_value("Shift Assignment", {
        "employee": employee_name, "shift_type": shift_type
    }, "name")
    if existing:
        return
    try:
        frappe.get_doc({
            "doctype": "Shift Assignment",
            "employee": employee_name,
            "shift_type": shift_type,
            "start_date": "2024-01-01",
            "docstatus": 1,
        }).insert(ignore_permissions=True)
        _c()
    except Exception:
        frappe.clear_messages()


def _create_multiperiod_attendance(employee_names, company, today):
    """Create multi-period attendance using the engine."""
    print("\nCreating multi-period attendance via engine...")

    from hr_erp.hrms_erp.multi_period_shift.multi_period_attendance_engine import (
        process_multi_period_attendance,
        mark_multi_period_attendance,
    )

    morning_shift_doc = frappe.get_doc("Shift Type", "Multi-Morning-Shift")
    evening_shift_doc = frappe.get_doc("Shift Type", "Multi-Evening-Shift")

    work_dates = []
    d = today
    while len(work_dates) < 10:
        if d.weekday() < 5:
            work_dates.append(d)
        d -= timedelta(days=1)
    work_dates.reverse()

    attendance_count = 0
    checkin_count = 0

    for emp_name in employee_names:
        emp_shift_name = frappe.db.get_value("Shift Assignment", {
            "employee": emp_name, "docstatus": 1
        }, "shift_type")
        shift_doc = evening_shift_doc if emp_shift_name == "Multi-Evening-Shift" else morning_shift_doc

        periods = sorted(shift_doc.shift_periods, key=lambda p: p.period_number or 0)
        work_periods = [p for p in periods if not p.is_break]

        for att_date in work_dates:
            existing_att = frappe.db.exists("Attendance", {
                "employee": emp_name, "attendance_date": att_date.strftime("%Y-%m-%d"),
                "docstatus": ["!=", 2],
            })
            if existing_att:
                continue

            scenario = random.choice(["on_time", "on_time", "on_time", "late_15", "late_30", "early_exit", "absent_one_period", "overtime"])

            checkins = []
            for p in work_periods:
                p_start_t = datetime.strptime(str(p.start_time), "%H:%M:%S").time()
                p_end_t = datetime.strptime(str(p.end_time), "%H:%M:%S").time()

                ci_dt = datetime.combine(att_date, p_start_t)
                co_dt = datetime.combine(att_date, p_end_t)

                if scenario == "late_15":
                    ci_dt += timedelta(minutes=random.choice([10, 15, 20]))
                elif scenario == "late_30":
                    ci_dt += timedelta(minutes=random.choice([25, 30, 35]))
                elif scenario == "early_exit":
                    co_dt -= timedelta(minutes=random.choice([10, 15, 20]))

                if scenario == "absent_one_period" and p == work_periods[-1]:
                    continue

                if scenario == "overtime" and p == work_periods[-1]:
                    co_dt += timedelta(minutes=random.choice([30, 45, 60]))

                try:
                    ci = frappe.get_doc({
                        "doctype": "Employee Checkin",
                        "employee": emp_name,
                        "time": ci_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "log_type": "IN",
                        "shift": shift_doc.name,
                    })
                    ci.insert(ignore_permissions=True)
                    checkins.append(ci)
                    checkin_count += 1
                except Exception:
                    frappe.clear_messages()

                try:
                    co = frappe.get_doc({
                        "doctype": "Employee Checkin",
                        "employee": emp_name,
                        "time": co_dt.strftime("%Y-%m-%d %H:%M:%S"),
                        "log_type": "OUT",
                        "shift": shift_doc.name,
                    })
                    co.insert(ignore_permissions=True)
                    checkins.append(co)
                    checkin_count += 1
                except Exception:
                    frappe.clear_messages()

            if checkins:
                try:
                    result = process_multi_period_attendance(
                        shift_doc, emp_name, checkins, att_date
                    )
                    if result:
                        result["_checkins"] = checkins
                        att_name = mark_multi_period_attendance(result)
                        attendance_count += 1
                except Exception:
                    frappe.clear_messages()

            if attendance_count % 10 == 0 and attendance_count > 0:
                _c()

    _c()
    print(f"  Attendance: {attendance_count} records with period details")
    print(f"  Checkins: {checkin_count} records created")
