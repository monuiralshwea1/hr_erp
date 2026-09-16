# -*- coding: utf-8 -*-
"""
seed_salary_slips.py  (hr_erp app) - created on request
Creates:
  1) Salary Structure "هيكل رواتب شهر 1الى12" (if missing) - fixed amounts, no auto formulas
  2) Salary Structure Assignment per employee (from max(2026-01-01, joining date))
  3) Salary Slips for every listed employee for months 2026-01 .. 2026-09
     with the exact fixed values from the supplied table, plus
     Late Deduction (خصم التأخير) and Absence Deduction (خصم الغياب) rows (0).
Any existing slips of these employees in the window are hard-deleted first (safe to re-run).

How to run on THIS server / ANY other server:
  cd <BENCH>/sites
  <BENCH>/env/bin/python <BENCH>/apps/hr_erp/hr_erp/hrms_erp/seed_salary_slips.py [SITE]
  (SITE defaults to site1.local - pass the site name of the new server if different.)
"""
import calendar
import sys
from datetime import date

import frappe
from frappe.utils import flt

SITE = sys.argv[1] if len(sys.argv) > 1 else "site1.local"
COMPANY = "الشاحذي"
STRUCTURE_NAME = "هيكل رواتب شهر 1الى12"
CURRENCY = "YER"
FROM_YEAR, TO_YEAR = 2026, 2026
MONTHS = list(range(1, 10))  # months 1..9

EARN_C = ["الراتب الأساسي", "بدل طبيعه عمل", "بدل مخاطر", "بدل مواصلات"]
DED_C = ["Late Deduction", "Absence Deduction"]


def normalize_ar(s):
    """Normalize common Arabic spelling variations so matching is tolerant."""
    s = (s or "").strip()
    s = s.replace("أ", "ا").replace("إ", "ا").replace("آ", "ا").replace("ٱ", "ا")
    s = s.replace("ى", "ي").replace("ئ", "ي")
    s = s.replace("ة", "ه")
    s = s.replace("\u0640", "")  # tatweel
    s = " ".join(s.split())  # collapse whitespace
    return s

# (رقم، اسم الموظف، الفرع، الراتب الأساسي، بدل طبيعة عمل، بدل مخاطر، بدل مواصلات)
EMPLOYEES = [
    (1,  "محمد يحيى صالح هازع",            "باجل",      70000, 40000, 30000, 10000),
    (2,  "حمد محمد حسن القديمي",           "باجل",      50000, 15000, 15000, 10000),
    (3,  "غندري أحمد احمد الغندري",        "باجل",      50000, 15000, 15000, 10000),
    (4,  "سعيد حسن عايض حسن الاهدل العنوان","باجل",     50000, 15000, 15000, 10000),
    (5,  "عاني سعيد عبده عبدالله الاغبري", "باجل",      50000, 10000, 10000, 10000),
    (6,  "احمد حسن محمد عبده مضاريه",      "باجل",      55000, 10000, 10000, 0),
    (7,  "نايف ردمان محمد مهدي",           "بيت الفقيه", 70000, 40000, 30000, 10000),
    (8,  "عبدالرحمن عبدالله هبه نايف العمري", "بيت الفقيه", 50000, 15000, 15000, 10000),
    (9,  "وليد عبده يحيى حسن العواضي",     "بيت الفقيه", 50000, 15000, 15000, 10000),
    (10, "محرم يحيى على حميده",            "بيت الفقيه", 50000, 15000, 15000, 10000),
    (11, "عاليه احمد صغير احمد الابي",     "بيت الفقيه", 50000, 10000, 5000, 5000),
    (12, "نجيب احمد ابراهيم",              "بيت الفقيه", 55000, 10000, 10000, 0),
    (13, "محمد عارف محمد عبدالرحمن الشيباني", "المطراق", 50000, 15000, 15000, 10000),
    (14, "مازن ابراهيم احمد فقير",         "المطراق",  50000, 15000, 15000, 10000),
    (15, "نشوان عبدالرحمن محمد الزبيدي",   "المطراق",  50000, 15000, 15000, 10000),
    (16, "غدير عمر عبدالله الشحاري",       "المطراق",  50000, 15000, 15000, 10000),
    (17, "حمدي عبد الحكيم احمد الشرجبي",   "المطراق",  50000, 15000, 15000, 10000),
    (18, "هديل قاسم محمد الثمار",          "المطراق",  50000, 15000, 15000, 10000),
    (19, "فهمي احمد محمد عبدالله",         "المطراق",  30000, 10000, 20000, 10000),
    (20, "اسامه نبيل على الجمالي",         "المطراق",  30000, 5000, 5000, 5000),
    (21, "سليمان محمد إبراهيم الدري",      "المطراق",  55000, 10000, 10000, 0),
    (22, "ايمن يحيى محمد الشاحذي",         "المطراق",  50000, 15000, 15000, 10000),
    (23, "نوره عزالدين شعبين حسن",         "النخيل",   50000, 15000, 15000, 10000),
    (24, "خالد علي حسن قشر",               "النخيل",   70000, 40000, 30000, 10000),
    (25, "اكرم محسن عبدالله الرباعي",      "النخيل",   50000, 15000, 15000, 10000),
    (26, "علا إبراهيم عبدالله مرشد",       "النخيل",   50000, 15000, 15000, 10000),
    (27, "محمد يحيى جابر مساوي رويدي",     "النخيل",   50000, 15000, 15000, 10000),
    (28, "محمد عبدالله محمد حسن جفه",      "النخيل",   30000, 10000, 10000, 10000),
    (29, "محمد سعد احمد سعد مشهف",         "النخيل",   30000, 5000, 10000, 5000),
    (30, "نبيل علي الجمالي",               "النخيل",   30000, 5000, 5000, 5000),
    (31, "علي يحيى محمد الشاحذي",          "النخيل",   50000, 15000, 15000, 10000),
    (32, "علي محمد صالح محمد الهيثمي",     "الزبيري",  70000, 60000, 60000, 10000),
    (33, "ارزاق جميل مهيوب محمد العبسي",   "الزبيري",  70000, 50000, 40000, 10000),
    (34, "رندا على عبده عبدويس",           "الزبيري",  50000, 15000, 15000, 10000),
    (35, "ولاء احمد محمد صويلح",           "الزبيري",  50000, 10000, 5000, 5000),
    (36, "طيبه محمد غانم الوصابي",         "الزبيري",  50000, 10000, 5000, 5000),
    (37, "محمد عبدالله محمد عبد الكريم",   "الزبيري",  50000, 15000, 15000, 10000),
    (38, "عبدالله محمد علي كريش",          "الزبيري",  50000, 15000, 15000, 10000),
    (39, "امجد هاني ناصر محمد الورقي",     "الزبيري",  50000, 15000, 15000, 10000),
    (40, "صالح اكرم صالح قبائل",           "الزبيري",  30000, 10000, 10000, 10000),
    (41, "يحيى صالح صالح هازع",            "الزبيري",  50000, 40000, 40000, 20000),
    (42, "وسام إسماعيل علي الارياني",      "الزبيري",  55000, 10000, 10000, 0),
    (43, "طلال غوبريحيى غوبر",             "الزبيري",  55000, 10000, 10000, 0),
    (44, "علي يحيى رزق الصرمي",            "الزبيري",  60000, 10000, 10000, 10000),
    (45, "ايمن صالح حسين الشيعاني",        "هايل",     70000, 40000, 30000, 10000),
    (46, "محمد حميد يحيى بادر",            "هايل",     50000, 15000, 15000, 10000),
    (47, "توفيق سعيد قاسم الشراعي",        "هايل",     55000, 10000, 1000, 0),
]


def main():
    frappe.init(site=SITE)
    frappe.connect()
    frappe.set_user("Administrator")
    frappe.local.lang = "ar"

    created, skipped, errors = [], [], []

    # 1) match employees - tolerant Arabic matching (exact spelling preferred,
    #    otherwise normalized spelling). Also prints clear guidance for missing ones.
    emp_map = {}
    all_emp = frappe.db.sql(
        "SELECT name, company, branch, department, date_of_joining, employee_name "
        "FROM `tabEmployee` ORDER BY name", as_dict=True)
    buckets = {}
    for e in all_emp:
        key = normalize_ar(e.employee_name or e.name)
        buckets.setdefault(key, []).append(e)
    for row in EMPLOYEES:
        no, name, branch, base, nat, risk, trans = row
        cand = buckets.get(normalize_ar(name), [])
        emp = None
        if len(cand) == 1:
            emp = cand[0]
        elif len(cand) > 1:
            exact = [c for c in cand if (c.employee_name or c.name or "").strip() == name]
            emp = exact[0] if len(exact) == 1 else None
        if emp is None:
            print(f"!! {no}. {name}: NOT FOUND or ambiguous ({len(cand)} match(es))", flush=True)
            skipped.append(name)
            continue
        emp_map[name] = (emp, base, nat, risk, trans)

    print(f"matched employees: {len(emp_map)} / {len(EMPLOYEES)}", flush=True)
    missing = [f"{r[0]}. {r[1]}" for r in EMPLOYEES if r[1] not in emp_map]
    if missing:
        print("MISSING:", " | ".join(missing), flush=True)
        print("  -> they exist on the target server? check exact spelling in `tabEmployee.employee_name`.", flush=True)

    # 1b) ensure salary components exist (portability: works on fresh servers too)
    for c, t in [(c, "Earning") for c in EARN_C] + [(c, "Deduction") for c in DED_C]:
        if not frappe.db.exists("Salary Component", c):
            frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": c,
                "type": t,
                "remove_if_zero_valued": 1,
                "disabled": 0,
            }).insert(ignore_permissions=True)
            print(f"created salary component: {c}", flush=True)
    frappe.db.commit()

    # 2) ensure salary structure (must be submitted: docstatus=1)
    structure = None
    if frappe.db.exists("Salary Structure", STRUCTURE_NAME):
        structure = frappe.get_doc("Salary Structure", STRUCTURE_NAME)
        print("structure exists - reusing", flush=True)
        if structure.docstatus == 0:
            structure.submit()
            print("structure submitted", flush=True)
    else:
        structure = frappe.get_doc({
            "doctype": "Salary Structure",
            "name": STRUCTURE_NAME,
            "structure_name": STRUCTURE_NAME,
            "company": COMPANY,
            "payroll_frequency": "Monthly",
            "salary_slip_based_on_timesheet": 0,
            "is_active": "Yes",
            "earnings": [{"salary_component": c, "amount": 0} for c in EARN_C],
            "deductions": [{"salary_component": c, "amount": 0} for c in DED_C],
        }).insert()
        structure.submit()
        print("structure created + submitted", flush=True)

    # 3) hard-delete ALL existing slips (any structure, ANY docstatus incl. cancelled)
#    for these employees in the window - direct SQL (no cancel(), bypasses validate)
    emp_ids = [v[0].name for v in emp_map.values()]
    before = frappe.db.sql("""SELECT COUNT(*) FROM `tabSalary Slip`
        WHERE employee IN %s AND start_date>='2026-01-01' AND end_date<='2026-09-30'""", (emp_ids,))[0][0]
    rows = frappe.db.sql("""DELETE FROM `tabSalary Slip`
        WHERE employee IN %s
          AND start_date>='2026-01-01' AND end_date<='2026-09-30'""", (emp_ids,))
    frappe.db.commit()
    print(f"hard-deleted slips: {before}", flush=True)

    # 4) salary structure assignments (replace all existing -> new structure, submitted)
    for name, (emp, base, *_rest) in emp_map.items():
        eff_from = date(2026, 1, 1)
        if emp.date_of_joining and emp.date_of_joining > eff_from:
            eff_from = emp.date_of_joining
        frappe.db.sql("DELETE FROM `tabSalary Structure Assignment` WHERE employee=%s", (emp.name,))
        asg = frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": emp.name,
            "salary_structure": STRUCTURE_NAME,
            "company": emp.company or COMPANY,
            "from_date": eff_from,
            "base": base,
            "variable": 0,
        }).insert()
        asg.submit()
    frappe.db.commit()
    print("structure assignments done (submitted, replaced)", flush=True)

    # 3b) re-delete slips created by assignment on_submit hooks
    after_hook = frappe.db.sql("""DELETE FROM `tabSalary Slip`
        WHERE employee IN %s
          AND start_date>='2026-01-01' AND end_date<='2026-09-30'""", (emp_ids,))
    frappe.db.commit()
    print(f"post-hook slips deleted: {after_hook}", flush=True)

    # 5) salary slips
    total = 0
    for (m, d) in [(m, calendar.monthrange(TO_YEAR, m)[1]) for m in MONTHS]:
        start = date(TO_YEAR, m, 1)
        end = date(TO_YEAR, m, d)
        for name, (emp, base, nat, risk, trans) in emp_map.items():
            if emp.date_of_joining and end < emp.date_of_joining:
                continue
            gross = base + nat + risk + trans
            exists = frappe.db.sql("""SELECT name FROM `tabSalary Slip`
                WHERE employee=%s AND start_date=%s AND end_date=%s AND docstatus!=2""",
                (emp.name, start, end))
            if exists:
                skipped.append(f"{name} {m}")
                continue
            try:
                ss = frappe.new_doc("Salary Slip")
                ss.employee = emp.name
                ss.company = emp.company or COMPANY
                ss.posting_date = end
                ss.start_date = start
                ss.end_date = end
                ss.salary_structure = STRUCTURE_NAME
                ss.payroll_frequency = "Monthly"
                ss.currency = CURRENCY
                ss.payment_days = 30
                ss.total_working_days = 30
                ss.leave_without_pay = 0
                ss.absent_days = 0
                ss.flags.ignore_permissions = True
                ss.flags.ignore_validate = True
                for (c, amt) in [(EARN_C[0], base), (EARN_C[1], nat), (EARN_C[2], risk), (EARN_C[3], trans)]:
                    ss.append("earnings", {
                        "salary_component": c, "amount": amt,
                        "depends_on_payment_days": 0, "default_amount": 0,
                    })
                for c in DED_C:
                    ss.append("deductions", {
                        "salary_component": c, "amount": 0,
                        "depends_on_payment_days": 0, "default_amount": 0,
                    })
                ss.insert()
                ss.gross_pay = gross
                ss.base_gross_pay = gross
                ss.total_deduction = 0.0
                ss.base_total_deduction = 0.0
                ss.net_pay = gross
                ss.rounded_total = gross
                ss.base_net_pay = gross
                ss.base_rounded_total = gross
                ss.total_loan_repayment = 0.0
                ss.flags.ignore_validate = True
                ss.submit()
                created.append((name, m, gross))
                total += 1
            except Exception as e:
                errors.append(f"{name} {m}: {type(e).__name__}: {str(e)[:200]}")
                frappe.db.rollback()
            if total % 50 == 0:
                frappe.db.commit()
    frappe.db.commit()

    print("\n=== RESULT ===", flush=True)
    print("created slips:", len(created), flush=True)
    print("skipped:", len(skipped), flush=True)
    print("errors:", len(errors), flush=True)
    for e in errors[:30]:
        print("  ERR", e, flush=True)

    # verify totals per employee (exact count + exact gross)
    from collections import Counter
    cnt = Counter(name for (name, m, g) in created)
    off = []
    for name, (emp, base, nat, risk, trans) in emp_map.items():
        want = base + nat + risk + trans
        expected = 0
        for (m, md) in [(m, calendar.monthrange(TO_YEAR, m)[1]) for m in MONTHS]:
            if not (emp.date_of_joining and date(TO_YEAR, m, md) < emp.date_of_joining):
                expected += 1
        got = frappe.db.sql("""SELECT gross_pay, COUNT(*) FROM `tabSalary Slip`
            WHERE employee=%s AND docstatus=1 AND start_date>='2026-01-01' AND end_date<='2026-09-30'
            GROUP BY gross_pay""", (emp.name,))
        total_got = sum(g[1] for g in got)
        bad = total_got != expected or any(flt(g[0]) != want for g in got)
        if bad:
            off.append((name, want, expected, got, cnt.get(name, 0), total_got))
    print("\ngross/count mismatches:", len(off), flush=True)
    for o in off:
        print("  ", o, flush=True)
    if not off:
        print("ALL MATCH: every employee has exact expected slips with exact gross", flush=True)

    frappe.destroy()


if __name__ == "__main__":
    main()