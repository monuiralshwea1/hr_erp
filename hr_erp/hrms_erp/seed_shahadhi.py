"""Batch create remaining employees + attendance via SQL for speed."""
import frappe
import csv
import codecs
import io
from datetime import datetime, timedelta, date
import random

COMPANY = "الشاحذي"

def execute():
    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"
    with codecs.open(path, 'r', encoding='cp1256') as f:
        content = f.read()
    lines = content.split('\n')

    employees = []
    for line in lines[2:]:
        if not line.strip() or '#NAME' in line:
            continue
        reader = csv.reader(io.StringIO(line))
        try:
            row = next(reader)
        except Exception:
            continue
        if len(row) < 20:
            continue
        name = row[20].strip() if len(row) > 20 else ''
        mobile = row[3].strip().replace(' ', '') if len(row) > 3 else ''
        if not name or not mobile or name == 'الاسم':
            continue
        employees.append({
            'name': name,
            'email': row[1].strip() if len(row) > 1 else '',
            'mobile': mobile,
            'dob': row[7].strip() if len(row) > 7 else '',
            'contract_start': row[11].strip() if len(row) > 11 else '',
            'contract_end': row[10].strip() if len(row) > 10 else '',
            'total_salary': row[12].strip().replace(',', '') if len(row) > 12 else '',
            'basic_salary': row[16].strip().replace(',', '') if len(row) > 16 else '',
            'branch': row[21].strip() if len(row) > 21 else '',
            'job_title': row[19].strip() if len(row) > 19 else '',
            'job_type': row[18].strip() if len(row) > 18 else '',
            'job_grade': row[17].strip() if len(row) > 17 else '',
            'transport': row[13].strip().replace(',', '') if len(row) > 13 else '',
            'risk': row[14].strip().replace(',', '') if len(row) > 14 else '',
            'nature': row[15].strip().replace(',', '') if len(row) > 15 else '',
        })

    existing_emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name", "cell_number"],
    )
    existing_mobiles = set(e.cell_number.replace(' ', '') for e in existing_emps if e.cell_number)
    existing_names = set(e.name for e in existing_emps)

    print(f"Total in CSV: {len(employees)}")
    print(f"Already in ERP: {len(existing_emps)}")

    missing = [e for e in employees if e['mobile'] not in existing_mobiles]
    print(f"Missing: {len(missing)}")

    for emp in missing:
        _create_one_employee(emp)

    frappe.db.commit()

    # Now create attendance for ALL employees using batch SQL
    _batch_create_attendance()

    print("\nDONE")


def _fix_email(email):
    """Clean and validate email."""
    if not email or '@' not in email:
        return ''
    email = email.strip().replace(' ', '').replace('.com', '.com').replace('.cim', '.com')
    if not email.endswith('.com') and not email.endswith('.net') and not email.endswith('.org') and not email.endswith('.sa'):
        email += '.com'
    return email


def _parse_date(s):
    if not s or not s.strip():
        return None
    s = s.strip().replace('\\', '/')
    for fmt in ['%m/%d/%Y', '%d/%m/%Y', '%m/%d/%y', '%d/%m/%y']:
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _create_one_employee(emp):
    name_parts = emp['name'].split()
    first_name = name_parts[0]
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else emp['name']
    dob = _parse_date(emp['dob'])
    join = _parse_date(emp['contract_start'])
    is_female = any(w in emp['name'] for w in ['نوره', 'غدير', 'هديل', 'رندا', 'ولاء', 'طيبه', 'علا', 'عليه', 'عاليه', 'رند'])
    gender = "Female" if is_female else "Male"

    branch = emp['branch'] if emp['branch'] in ['باجل', 'بيت الفقيه', 'المطراق', 'النخيل', 'الزبيري', 'هايل'] else 'الزبيري'

    job_title = emp['job_title']
    if '(' in job_title:
        job_title = job_title[:job_title.index('(')].strip()

    dept = 'الاداره العامه'
    jt = emp['job_type'].lower()
    if 'مال' in jt or 'تنفيذ' in jt:
        dept = 'الماليه'
    elif 'حراس' in jt or 'امن' in jt or 'أمن' in jt:
        dept = 'الحراسه'
    elif 'تقني' in jt or 'شبكات' in jt:
        dept = 'تقنية المعلومات'
    elif 'خدم' in jt:
        dept = 'الخدمات'

    desig = job_title if len(job_title) < 40 else job_title[:40]

    existing_desig = frappe.db.exists("Designation", {"designation_name": desig})
    if not existing_desig:
        try:
            frappe.get_doc({"doctype": "Designation", "designation_name": desig}).insert(ignore_permissions=True)
        except Exception:
            frappe.clear_messages()

    existing_dept = frappe.db.exists("Department", {"department_name": dept, "company": COMPANY})
    if not existing_dept:
        try:
            frappe.get_doc({"doctype": "Department", "department_name": dept, "company": COMPANY}).insert(ignore_permissions=True)
        except Exception:
            frappe.clear_messages()

    try:
        doc = frappe.get_doc({
            "doctype": "Employee",
            "employee_name": emp['name'],
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "company": COMPANY,
            "department": dept,
            "designation": desig,
            "employment_type": "دوام كامل",
            "branch": branch,
            "date_of_birth": dob.strftime("%Y-%m-%d") if dob else "1990-01-01",
            "date_of_joining": join.strftime("%Y-%m-%d") if join else "2020-01-01",
            "cell_number": emp['mobile'],
            "personal_email": _fix_email(emp['email']),
            "status": "Active",
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Created: {doc.name} | {emp['name']}")
    except Exception as e:
        frappe.clear_messages()
        print(f"  ERROR: {emp['name']} - {str(e)[:60]}")


def _batch_create_attendance():
    """Batch create attendance + period details via SQL."""
    print("\nBatch creating attendance...")

    all_emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name"],
    )
    emp_names = [e.name for e in all_emps]

    existing_count = frappe.db.count("Attendance", {"employee": ["in", emp_names]})
    print(f"  Existing attendance: {existing_count}")

    today = date.today()
    work_dates = []
    d = today
    while len(work_dates) < 10:
        if d.weekday() < 5:
            work_dates.append(d)
        d -= timedelta(days=1)
    work_dates.reverse()

    morning_periods = [
        (1, "الفترة الأولى - الصباح", 6, 0, 9, 0),
        (3, "الفترة الثانية - ما بعد الاستراحة", 10, 0, 14, 0),
        (5, "الفترة الثالثة - النهاية", 14, 30, 18, 0),
    ]
    evening_periods = [
        (1, "الفترة الأولى - المساء", 14, 0, 17, 0),
        (3, "الفترة الثانية - ما بعد العشاء", 18, 0, 21, 0),
        (5, "الفترة الثالثة - الإغلاق", 21, 0, 23, 0),
    ]

    att_count = 0
    pd_count = 0

    for emp_name in emp_names:
        existing_atts = frappe.db.sql(
            "SELECT attendance_date FROM tabAttendance WHERE employee=%s AND docstatus != 2",
            (emp_name,), as_dict=True
        )
        existing_dates = set(str(a.attendance_date) for a in existing_atts)

        is_security = frappe.db.get_value("Employee", emp_name, "department") == "الحراسه"
        periods = evening_periods if is_security else morning_periods

        for att_date in work_dates:
            date_str = att_date.strftime("%Y-%m-%d")
            if date_str in existing_dates:
                continue

            scenario = random.choice(["on_time", "on_time", "on_time", "on_time", "late_15", "early_exit", "absent_one_period"])
            late_minutes = 0
            early_exit_min = 0
            total_hours = 0
            status = "Present"

            period_details = []
            for pnum, pname, sh, sm, eh, em in periods:
                ci_time = datetime.combine(att_date, datetime.min.time().replace(hour=sh, minute=sm))
                co_time = datetime.combine(att_date, datetime.min.time().replace(hour=eh, minute=em))

                if scenario == "late_15":
                    ci_time += timedelta(minutes=random.choice([10, 15, 20]))
                elif scenario == "early_exit":
                    co_time -= timedelta(minutes=random.choice([10, 15, 20]))

                if scenario == "absent_one_period" and pnum == periods[-1][0]:
                    period_details.append({
                        "period_name": pname, "period_number": pnum,
                        "period_start": ci_time, "period_end": co_time,
                        "actual_check_in": None, "actual_check_out": None,
                        "working_hours": 0, "late_minutes": 0, "early_exit_minutes": 0,
                        "absent_hours": round((eh * 60 + em - sh * 60 - sm) / 60, 2),
                        "overtime_hours": 0, "period_status": "Absent",
                    })
                    continue

                actual_ci = ci_time
                actual_co = co_time

                p_late = max(0, (ci_time - datetime.combine(att_date, datetime.min.time().replace(hour=sh, minute=sm))).total_seconds() / 60) if scenario == "late_15" else 0
                p_early = max(0, (co_time - actual_co).total_seconds() / 60) if scenario == "early_exit" else 0
                p_hours = round((actual_co - actual_ci).total_seconds() / 3600, 2)
                if p_hours < 0:
                    p_hours = 0

                p_status = "Present"
                if p_late > 0:
                    p_status = "Late"

                total_hours += p_hours
                late_minutes += p_late
                early_exit_min += p_early

                period_details.append({
                    "period_name": pname, "period_number": pnum,
                    "period_start": ci_time, "period_end": co_time,
                    "actual_check_in": actual_ci, "actual_check_out": actual_co,
                    "working_hours": p_hours, "late_minutes": p_late, "early_exit_minutes": p_early,
                    "absent_hours": 0, "overtime_hours": 0, "period_status": p_status,
                })

            if total_hours == 0:
                status = "Absent"
            elif total_hours < 5:
                status = "Half Day"

            try:
                att = frappe.get_doc({
                    "doctype": "Attendance",
                    "employee": emp_name,
                    "attendance_date": date_str,
                    "status": status,
                    "working_hours": round(total_hours, 2),
                    "late_entry": 1 if late_minutes > 0 else 0,
                    "early_exit": 1 if early_exit_min > 0 else 0,
                    "shift": "Multi-Morning-Shift" if not is_security else "Multi-Evening-Shift",
                })
                att.flags.ignore_validate = True
                att.insert(ignore_permissions=True)
                att.submit()
                att_count += 1

                for pd in period_details:
                    frappe.get_doc({
                        "doctype": "Attendance Period Detail",
                        "parent": att.name,
                        "parenttype": "Attendance",
                        "parentfield": "attendance_period_details",
                        "employee": emp_name,
                        "attendance": att.name,
                        "shift_type": att.shift,
                        "period_name": pd["period_name"],
                        "period_number": pd["period_number"],
                        "period_start": pd["period_start"],
                        "period_end": pd["period_end"],
                        "actual_check_in": pd["actual_check_in"],
                        "actual_check_out": pd["actual_check_out"],
                        "working_hours": pd["working_hours"],
                        "late_minutes": pd["late_minutes"],
                        "early_exit_minutes": pd["early_exit_minutes"],
                        "absent_hours": pd["absent_hours"],
                        "overtime_hours": pd["overtime_hours"],
                        "period_status": pd["period_status"],
                    }).insert(ignore_permissions=True)
                    pd_count += 1

            except Exception as e:
                frappe.clear_messages()

            if att_count % 20 == 0 and att_count > 0:
                frappe.db.commit()

    frappe.db.commit()
    print(f"  Attendance: {att_count} records")
    print(f"  Period Details: {pd_count} rows")
