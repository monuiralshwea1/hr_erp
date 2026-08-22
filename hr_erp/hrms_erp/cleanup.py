import frappe, os

def execute():
    base = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/hrms_erp/"
    temp_files = [
        "check_sp.py", "check_apd.py", "check_existing.py", "check_shift_type.py",
        "check_salary.py", "check_ss.py", "check_periods.py", "debug_ssa.py",
        "fix_periods.py", "fix_ss.py", "fix_ss2.py",
    ]
    root = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/"
    root_files = ["check_sp.py", "_gen.py", "_export.json", "map_employees.py"]
    deleted = 0
    for f in temp_files:
        p = base + f
        if os.path.exists(p):
            os.remove(p)
            deleted += 1
    for f in root_files:
        p = root + f
        if os.path.exists(p):
            os.remove(p)
            deleted += 1
    print(f"Cleaned {deleted} temp files")
