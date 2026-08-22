import frappe

def execute():
    shifts = frappe.get_all("Shift Type", fields=["name", "enable_multi_period", "start_time", "end_time"])
    print(f"Existing Shift Types ({len(shifts)}):")
    for s in shifts:
        periods = frappe.db.sql("""
            SELECT period_number, period_name, start_time, end_time, is_break
            FROM `tabShift Period`
            WHERE parent=%s
            ORDER BY period_number
        """, s.name, as_dict=True)
        print(f"  {s.name} | multi={s.enable_multi_period} | {s.start_time}-{s.end_time}")
        for p in periods:
            brk = " [BREAK]" if p.is_break else ""
            print(f"    #{p.period_number} {p.period_name}: {p.start_time}-{p.end_time}{brk}")

    # Check Shift Type autoname
    meta = frappe.get_meta("Shift Type")
    print(f"\nShift Type autoname: {meta.autoname}")

    # Check Attendance Period Detail existing records
    count = frappe.db.count("Attendance Period Detail")
    print(f"\nAttendance Period Detail records: {count}")
