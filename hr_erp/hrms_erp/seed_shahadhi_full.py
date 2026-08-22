"""
seed_shahadhi_full.py - v2
==========================
1. Create Shift Types with correct periods from XLSX
2. Update employee branches and create shift assignments
3. Recreate attendance with period details
4. Create Salary Structure Assignments per employee from CSV
"""
import frappe
import random
from datetime import datetime, timedelta, date, time

COMPANY = "الشاحذي"
SALARY_STRUCTURE = "هيكل رواتب الموظفين"


def _c():
    frappe.db.commit()


def execute():
    print("=" * 60)
    print("SHAHADHI FULL SEED v2")
    print("=" * 60)

    shifts = _create_shift_types()
    _c()

    assignments = _assign_shifts(shifts)
    _c()

    _recreate_attendance(assignments)
    _c()

    _update_salaries()
    _c()

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


# ── Employee-to-Shift Mapping ───────────────────────────────────────────

EMPLOYEE_MAP = {
    # باجل
    "770998764": ("shift_male_standard", "باجل"),
    "716677947": ("shift_male_standard", "باجل"),
    "711966283": ("shift_male_standard", "باجل"),
    "714525002": ("shift_male_standard", "باجل"),
    "772777509": ("shift_male_standard", "باجل"),
    "777661795": ("shift_male_standard", "باجل"),
    # بيت الفقيه
    "73916633":  ("shift_bit_confirm", "بيت الفقيه"),
    "716845306": ("shift_bit_1", "بيت الفقيه"),
    "773566813": ("shift_bit_1", "بيت الفقيه"),
    "737737566": ("shift_bit_confirm", "بيت الفقيه"),
    "739706744": ("shift_bit_2", "بيت الفقيه"),
    # المطراق
    "777428067": ("shift_iron", "المطراق"),
    "777175075": ("shift_iron", "المطراق"),
    "777003044": ("shift_iron", "المطراق"),
    "772629043": ("shift_iron", "المطراق"),
    "771988228": ("shift_evening_full", "المطراق"),
    "777157600": ("shift_iron", "المطراق"),
    "777160485": ("shift_iron", "المطراق"),
    "779011081": ("shift_evening_full", "المطراق"),
    "776834337": ("shift_iron", "المطراق"),
    "771807276": ("shift_evening_full2", "المطراق"),
    # النخيل
    "715711543": ("shift_iron", "النخيل"),
    "772939330": ("shift_iron", "النخيل"),
    "770584450": ("shift_iron", "النخيل"),
    "735421272": ("shift_iron", "النخيل"),
    "737808171": ("shift_iron", "النخيل"),
    "3246409":   ("shift_iron", "النخيل"),
    "733906125": ("shift_iron", "النخيل"),
    "771932099": ("shift_iron", "النخيل"),
    "779509980": ("shift_nakheel_females", "النخيل"),
    # الزبيري
    "735003547": ("shift_hethimi", "الزبيري"),
    "771848733": ("shift_female_zubayri", "الزبيري"),
    "735999959": ("shift_female_zubayri", "الزبيري"),
    "737322747": ("shift_female_zubayri", "الزبيري"),
    "781649711": ("shift_female_zubayri", "الزبيري"),
    "770620009": ("shift_male_standard", "الزبيري"),
    "771707720": ("shift_male_standard", "الزبيري"),
    "781111773": ("shift_male_standard", "الزبيري"),
    "777728315": ("shift_male_standard", "الزبيري"),
    "777717199": ("shift_male_standard", "الزبيري"),
    "775966954": ("shift_male_standard", "الزبيري"),
    "772221989": ("shift_male_standard", "الزبيري"),
    "773339004": ("shift_male_standard", "الزبيري"),
    # هايل
    "772551812": ("shift_male_standard", "هايل"),
    "770840895": ("shift_male_standard", "هايل"),
}


# ── Shift Definitions from XLSX ─────────────────────────────────────────

SHIFT_DEFS = {
    "shift_male_standard": {
        "name": "SH-دوام العيال",
        "start": "07:30:00", "end": "21:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "21:00:00", 0),
        ],
    },
    "shift_bit_1": {
        "name": "SH-بيت الفقيه 1",
        "start": "07:30:00", "end": "23:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "23:00:00", 0),
        ],
    },
    "shift_bit_2": {
        "name": "SH-بيت الفقيه 2",
        "start": "07:30:00", "end": "23:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "23:00:00", 0),
        ],
    },
    "shift_bit_confirm": {
        "name": "SH-تأكيد حضور بيت الفقيه",
        "start": "07:30:00", "end": "23:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "23:00:00", 0),
        ],
    },
    "shift_iron": {
        "name": "SH-داوم فروع الحديد",
        "start": "07:30:00", "end": "21:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "21:00:00", 0),
        ],
    },
    "shift_evening_full": {
        "name": "SH-دوام متكامل مطراق",
        "start": "14:00:00", "end": "01:00:00",
        "periods": [
            (1, "الفترة المسائية الأولى", "14:00:00", "18:00:00", 0),
            (2, "استراحة العشاء", "18:00:00", "19:00:00", 1),
            (3, "الفترة المسائية الثانية", "19:00:00", "01:00:00", 0),
        ],
    },
    "shift_evening_full2": {
        "name": "SH-دوام متكامل مطراق 2",
        "start": "19:00:00", "end": "03:00:00",
        "periods": [
            (1, "الفترة المسائية الأولى", "19:00:00", "23:00:00", 0),
            (2, "استراحة", "23:00:00", "00:00:00", 1),
            (3, "الفترة المسائية الثانية", "00:00:00", "03:00:00", 0),
        ],
    },
    "shift_nakheel_females": {
        "name": "SH-دوام النخيل (البنات)",
        "start": "07:30:00", "end": "20:30:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "20:30:00", 0),
        ],
    },
    "shift_hethimi": {
        "name": "SH-الزبيري الهيثمي",
        "start": "07:30:00", "end": "21:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "11:30:00", 0),
            (2, "استراحة", "11:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "21:00:00", 0),
        ],
    },
    "shift_female_zubayri": {
        "name": "SH-البنات الزبيري",
        "start": "07:30:00", "end": "20:00:00",
        "periods": [
            (1, "الفترة الصباحية", "07:30:00", "13:30:00", 0),
            (2, "استراحة الغداء", "13:30:00", "14:50:00", 1),
            (3, "الفترة المسائية", "14:50:00", "20:00:00", 0),
        ],
    },
}


def _create_shift_types():
    """Create Shift Types using SQL (autoname=prompt) and add periods."""
    created = {}
    for key, defn in SHIFT_DEFS.items():
        name = defn["name"]
        if frappe.db.exists("Shift Type", name):
            created[key] = name
            print(f"  EXISTS: {name}")
            continue

        try:
            frappe.db.sql("""
                INSERT INTO `tabShift Type`
                (name, enable_multi_period, start_time, end_time, docstatus, owner, creation)
                VALUES (%s, 1, %s, %s, 0, 'Administrator', NOW())
            """, (name, defn["start"], defn["end"]))

            for pnum, pname, start, end, is_break in defn["periods"]:
                frappe.db.sql("""
                    INSERT INTO `tabShift Period`
                    (parent, parenttype, parentfield, period_number, period_name,
                     start_time, end_time, is_break, owner, creation)
                    VALUES (%s, 'Shift Type', 'shift_periods', %s, %s, %s, %s, %s, 'Administrator', NOW())
                """, (name, pnum, pname, start, end, is_break))

            frappe.db.commit()
            created[key] = name
            print(f"  CREATED: {name} ({len(defn['periods'])} periods)")
        except Exception as e:
            frappe.clear_messages()
            created[key] = name
            print(f"  SKIP: {name}: {e}")

    return created


def _assign_shifts(shifts):
    """Update employee branches and create shift assignments."""
    print("\nAssigning shifts...")
    all_emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name", "employee_name", "cell_number", "branch"],
    )

    assignments = {}
    unmapped = []

    for emp in all_emps:
        mobile = (emp.cell_number or "").replace(" ", "").strip()
        mapping = EMPLOYEE_MAP.get(mobile)
        if not mapping:
            unmapped.append(f"{emp.name} ({emp.employee_name}) mobile={mobile}")
            continue

        shift_key, branch = mapping
        shift_name = shifts.get(shift_key)
        if not shift_name:
            continue

        if branch and emp.branch != branch:
            frappe.db.set_value("Employee", emp.name, "branch", branch)

        assignments[emp.name] = shift_name

    # Cancel/delete existing shift assignments
    all_emp_names = [e.name for e in all_emps]
    if all_emp_names:
        old_sa = frappe.get_all("Shift Assignment",
            filters={"employee": ["in", all_emp_names], "docstatus": ["in", [0, 1]]},
            fields=["name", "docstatus"],
        )
        print(f"  Cancelling {len(old_sa)} old shift assignments...")
        for sa in old_sa:
            try:
                doc = frappe.get_doc("Shift Assignment", sa.name)
                if sa.docstatus == 1:
                    doc.cancel()
                else:
                    doc.delete(ignore_permissions=True)
            except Exception:
                frappe.clear_messages()

    # Create new shift assignments
    created_sa = 0
    for emp_name, shift_name in assignments.items():
        try:
            sa = frappe.get_doc({
                "doctype": "Shift Assignment",
                "employee": emp_name,
                "shift_type": shift_name,
                "start_date": "2025-01-01",
            })
            sa.insert(ignore_permissions=True)
            sa.submit()
            created_sa += 1
        except Exception:
            frappe.clear_messages()

    frappe.db.commit()
    print(f"  Mapped: {len(assignments)}, Unmapped: {len(unmapped)}, Assignments: {created_sa}")
    if unmapped:
        for u in unmapped[:5]:
            print(f"    UNMAPPED: {u}")
    return assignments


def _recreate_attendance(assignments):
    """Cancel, delete, then recreate attendance with correct period details."""
    print("\nRecreating attendance...")

    all_emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name"],
    )
    emp_names = [e.name for e in all_emps]

    # Cancel submitted
    old_atts = frappe.get_all("Attendance",
        filters={"employee": ["in", emp_names], "docstatus": 1},
        fields=["name"],
    )
    print(f"  Cancelling {len(old_atts)} submitted...")
    for att in old_atts:
        try:
            frappe.get_doc("Attendance", att.name).cancel()
        except Exception:
            frappe.clear_messages()

    frappe.db.commit()

    # Delete drafts
    draft_atts = frappe.get_all("Attendance",
        filters={"employee": ["in", emp_names], "docstatus": 0},
        fields=["name"],
    )
    for att in draft_atts:
        try:
            frappe.get_doc("Attendance", att.name).delete(ignore_permissions=True)
        except Exception:
            frappe.clear_messages()

    # SQL cleanup
    if emp_names:
        ph = ",".join(["%s"] * len(emp_names))
        frappe.db.sql(f"DELETE FROM `tabAttendance Period Detail` WHERE employee IN ({ph})", emp_names)
        frappe.db.sql(f"DELETE FROM `tabAttendance` WHERE employee IN ({ph})", emp_names)
    frappe.db.commit()
    print(f"  Cleaned")

    # 10 work days ending today
    today = date.today()
    work_dates = []
    d = today
    while len(work_dates) < 10:
        if d.weekday() < 5:
            work_dates.append(d)
        d -= timedelta(days=1)
    work_dates.reverse()
    print(f"  Dates: {work_dates[0]} to {work_dates[-1]}")

    att_count = 0
    pd_count = 0

    for emp in all_emps:
        shift_name = assignments.get(emp.name)
        if not shift_name:
            continue

        periods = frappe.db.sql("""
            SELECT period_number, period_name, start_time, end_time, is_break
            FROM `tabShift Period`
            WHERE parent=%s
            ORDER BY period_number
        """, shift_name, as_dict=True)

        if not periods:
            continue

        # Convert timedelta to time objects
        def _to_time(t):
            if isinstance(t, timedelta):
                total_secs = int(t.total_seconds())
                hours = total_secs // 3600
                minutes = (total_secs % 3600) // 60
                seconds = total_secs % 60
                return time(hours, minutes, seconds)
            return t

        for p in periods:
            p.start_time = _to_time(p.start_time)
            p.end_time = _to_time(p.end_time)

        work_periods = [p for p in periods if not p.is_break]

        for att_date in work_dates:
            scenario = random.choice([
                "on_time", "on_time", "on_time", "on_time", "on_time",
                "late_15", "early_exit", "absent_one_period",
            ])

            total_hours = 0.0
            late_minutes = 0.0
            status = "Present"
            period_details = []

            for p in periods:
                p_start_t = p.start_time
                p_end_t = p.end_time

                ci_dt = datetime.combine(att_date, p_start_t)
                co_dt = datetime.combine(att_date, p_end_t)

                if p_end_t < p_start_t:
                    co_dt += timedelta(days=1)

                if p.is_break:
                    period_details.append({
                        "period_name": p.period_name,
                        "period_number": p.period_number,
                        "period_start": ci_dt,
                        "period_end": co_dt,
                        "actual_check_in": None,
                        "actual_check_out": None,
                        "working_hours": 0.0,
                        "late_minutes": 0.0,
                        "early_exit_minutes": 0.0,
                        "absent_hours": 0.0,
                        "overtime_hours": 0.0,
                        "period_status": "Break",
                    })
                    continue

                actual_ci = ci_dt
                actual_co = co_dt

                if scenario == "late_15" and p == work_periods[0]:
                    actual_ci += timedelta(minutes=random.choice([10, 15, 20, 25]))
                elif scenario == "early_exit" and p == work_periods[-1]:
                    actual_co -= timedelta(minutes=random.choice([10, 15, 20]))
                elif scenario == "absent_one_period" and p == work_periods[-1]:
                    absent_hrs = round((co_dt - ci_dt).total_seconds() / 3600, 2)
                    period_details.append({
                        "period_name": p.period_name,
                        "period_number": p.period_number,
                        "period_start": ci_dt,
                        "period_end": co_dt,
                        "actual_check_in": None,
                        "actual_check_out": None,
                        "working_hours": 0.0,
                        "late_minutes": 0.0,
                        "early_exit_minutes": 0.0,
                        "absent_hours": absent_hrs,
                        "overtime_hours": 0.0,
                        "period_status": "Absent",
                    })
                    continue

                p_late = 0.0
                if scenario == "late_15" and p == work_periods[0]:
                    p_late = float(random.choice([10, 15, 20, 25]))
                    actual_ci = ci_dt + timedelta(minutes=p_late)

                p_hours = max(0, round((actual_co - actual_ci).total_seconds() / 3600, 2))

                total_hours += p_hours
                late_minutes += p_late

                p_status = "Late" if p_late > 0 else "Present"

                period_details.append({
                    "period_name": p.period_name,
                    "period_number": p.period_number,
                    "period_start": ci_dt,
                    "period_end": co_dt,
                    "actual_check_in": actual_ci,
                    "actual_check_out": actual_co,
                    "working_hours": p_hours,
                    "late_minutes": p_late,
                    "early_exit_minutes": 0.0,
                    "absent_hours": 0.0,
                    "overtime_hours": 0.0,
                    "period_status": p_status,
                })

            if total_hours == 0:
                status = "Absent"
            elif total_hours < 5:
                status = "Half Day"

            try:
                att = frappe.get_doc({
                    "doctype": "Attendance",
                    "employee": emp.name,
                    "attendance_date": att_date.strftime("%Y-%m-%d"),
                    "status": status,
                    "working_hours": round(total_hours, 2),
                    "late_entry": 1 if late_minutes > 0 else 0,
                    "shift": shift_name,
                })
                att.insert(ignore_permissions=True)
                att.submit()
                att_count += 1

                for pd in period_details:
                    frappe.get_doc({
                        "doctype": "Attendance Period Detail",
                        "parent": att.name,
                        "parenttype": "Attendance",
                        "parentfield": "attendance_period_details",
                        "employee": emp.name,
                        "attendance": att.name,
                        "shift_type": shift_name,
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

            except Exception:
                frappe.clear_messages()

            if att_count % 50 == 0 and att_count > 0:
                frappe.db.commit()

    frappe.db.commit()
    print(f"  Attendance: {att_count}")
    print(f"  Period Details: {pd_count}")


# ── CSV salary columns ──────────────────────────────────────────────────
# [12] اجمالي الراتب, [13] بدل مواصلات, [14] بدل مخاطر,
# [15] بدل طبيعه عمل, [16] الراتب الاساسي

def _parse_csv():
    """Parse employee CSV and return salary data keyed by mobile."""
    import csv, codecs, io

    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"
    try:
        with codecs.open(path, 'r', encoding='cp1256') as f:
            content = f.read()
    except Exception:
        print("  CSV not found")
        return {}

    def _num(s):
        try:
            return int(str(s).strip().replace(',', ''))
        except (ValueError, AttributeError):
            return 0

    salary_data = {}
    lines = content.split('\n')
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
        mobile = row[3].strip().replace(' ', '') if len(row) > 3 else ''
        if not mobile:
            continue
        salary_data[mobile] = {
            'basic': _num(row[16]) if len(row) > 16 else 0,
            'total': _num(row[12]) if len(row) > 12 else 0,
            'transport': _num(row[13]) if len(row) > 13 else 0,
            'risk': _num(row[14]) if len(row) > 14 else 0,
            'nature': _num(row[15]) if len(row) > 15 else 0,
        }
    return salary_data


def _ensure_salary_components():
    """Create missing salary components: بدل مخاطر, بدل طبيعه عمل."""
    components = {
        "بدل مخاطر": {"abbr": "RISK", "type": "Earning"},
        "بدل طبيعه عمل": {"abbr": "NATURE", "type": "Earning"},
    }
    for name, info in components.items():
        if not frappe.db.exists("Salary Component", name):
            try:
                frappe.get_doc({
                    "doctype": "Salary Component",
                    "salary_component_name": name,
                    "salary_component_abbr": info["abbr"],
                    "type": info["type"],
                    "amount_based_on_formula": 0,
                    "amount": 0,
                }).insert(ignore_permissions=True)
                frappe.db.commit()
                print(f"  Created component: {name}")
            except Exception:
                frappe.clear_messages()


def _update_salary_structure():
    """Update the Salary Structure to include all 5 components with formula."""
    _ensure_salary_components()

    ss_name = SALARY_STRUCTURE
    if not frappe.db.exists("Salary Structure", ss_name):
        print(f"  Salary Structure '{ss_name}' not found!")
        return

    doc = frappe.get_doc("Salary Structure", ss_name)

    existing_earnings = {e.salary_component: e for e in doc.earnings}

    required = [
        ("الراتب الأساسي", "BAS"),
        ("بدل مواصلات", "TRN"),
        ("بدل مخاطر", "RISK"),
        ("بدل طبيعه عمل", "NATURE"),
        ("بدل سكن", "HOU"),
    ]

    for comp_name, abbr in required:
        if comp_name not in existing_earnings:
            doc.append("earnings", {
                "salary_component": comp_name,
                "abbr": abbr,
                "amount_based_on_formula": 0,
                "amount": 0,
            })

    # Remove duplicate basic if there are two
    basics = [e for e in doc.earnings if e.salary_component == "الراتب الأساسي"]
    if len(basics) > 1:
        for b in basics[1:]:
            doc.earnings.remove(b)

    try:
        doc.save(ignore_permissions=True)
        frappe.db.commit()
        print(f"  Updated Salary Structure: {doc.name}")
    except Exception:
        frappe.clear_messages()


def _update_salaries():
    """Create Salary Structure Assignments per employee."""
    print("\nUpdating salaries...")
    _update_salary_structure()

    salary_data = _parse_csv()
    if not salary_data:
        print("  No CSV data")
        return

    all_emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name", "cell_number"],
    )

    # Cancel existing SSAs
    emp_names = [e.name for e in all_emps]
    if emp_names:
        old_ssas = frappe.get_all("Salary Structure Assignment",
            filters={"employee": ["in", emp_names], "docstatus": ["in", [0, 1]]},
            fields=["name", "docstatus"],
        )
        for ssa in old_ssas:
            try:
                doc = frappe.get_doc("Salary Structure Assignment", ssa.name)
                if ssa.docstatus == 1:
                    doc.cancel()
                else:
                    doc.delete(ignore_permissions=True)
            except Exception:
                frappe.clear_messages()
        frappe.db.commit()

    created = 0
    for emp in all_emps:
        mobile = (emp.cell_number or "").replace(" ", "").strip()
        sal = salary_data.get(mobile)
        if not sal:
            continue

        # Build earnings with amounts
        earnings = []
        if sal['basic'] > 0:
            earnings.append({"salary_component": "الراتب الأساسي", "amount": sal['basic']})
        if sal['transport'] > 0:
            earnings.append({"salary_component": "بدل مواصلات", "amount": sal['transport']})
        if sal['risk'] > 0:
            earnings.append({"salary_component": "بدل مخاطر", "amount": sal['risk']})
        if sal['nature'] > 0:
            earnings.append({"salary_component": "بدل طبيعه عمل", "amount": sal['nature']})
        if sal['basic'] > 0:
            earnings.append({"salary_component": "بدل سكن", "amount": int(sal['basic'] * 0.15)})

        if not earnings:
            continue

        try:
            ssa = frappe.get_doc({
                "doctype": "Salary Structure Assignment",
                "employee": emp.name,
                "salary_structure": SALARY_STRUCTURE,
                "base": sal['basic'] if sal['basic'] > 0 else 0,
            })
            for e in earnings:
                ssa.append("earnings", e)
            ssa.insert(ignore_permissions=True)
            ssa.submit()
            created += 1
        except Exception:
            frappe.clear_messages()

    frappe.db.commit()
    print(f"  Created {created} Salary Structure Assignments")
