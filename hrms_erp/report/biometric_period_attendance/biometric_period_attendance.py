# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
# تقرير الحضور والانصراف حسب الفترات (Biometric Period Attendance)
# يعرض لكل موظف ولكل يوم البصمات مقسمة على الفترات (صباحية/مسائية/غيرها)
# الفترات تُقرأ تلقائياً من جدول فترات الشفت (Shift Type -> Shift Period)
# ويأخذ أسماء الفترات وأوقات الدخول/الخروج/التأخير من الجدول مباشرة.
# البصمات الواردة بدون log_type (من تطبيق الوسيط biometric_integration)
# تُعامَل زمنياً: أول بصمة داخل الفترة = دخول، آخر بصمة = خروج.
# أعمدة مختصرة لكل فترة: دخول | خروج | تأخير (د) | الحالة

import frappe
from frappe import _
from frappe.utils import getdate, get_time, get_datetime, add_days, cint, flt, nowdate
from datetime import datetime, timedelta

# الفترات الافتراضية عند عدم وجود أي فترات معرفة على الشفتات (مرتبة زمنياً وغير متداخلة)
DEFAULT_PERIOD_TIMES = {
	"الفترة الصباحية": ("07:30:00", "13:30:00"),
	"الفترة المسائية": ("14:50:00", "23:00:00"),
}
DEFAULT_PERIOD_ORDER = ["الفترة الصباحية", "الفترة المسائية"]


class Punch(object):
	def __init__(self, time, log_type=None, device_id=None, source="biometric"):
		self.time = get_datetime(time)
		self.log_type = log_type
		self.device_id = device_id
		self.source = source


def get_fallback_periods():
	"""الفترات الافتراضية (هدف العرض عند غياب فترات معرفة)."""
	return [
		{
			"period_name": name,
			"period_number": i + 1,
			"start_time": get_time(st),
			"end_time": get_time(et),
			"late_grace_period": 0,
			"early_exit_grace_period": 0,
			"minimum_working_hours": 0,
			"is_break": 0,
		}
		for i, name in enumerate(DEFAULT_PERIOD_ORDER)
		for st, et in [DEFAULT_PERIOD_TIMES[name]]
	]


def get_shift_periods(shift_name):
	"""فترات الشفت المتعدد المعرفة (Shift Period rows). بلا فترات تعيد قائمة فارغة."""
	if not shift_name:
		return []
	try:
		shift_doc = frappe.get_cached_doc("Shift Type", shift_name)
	except Exception:
		return []

	rows = [p for p in (getattr(shift_doc, "shift_periods", None) or []) if not cint(p.is_break)]
	work_rows = [
		{
			"period_name": p.period_name,
			"period_number": cint(p.period_number or 0),
			"start_time": get_time(p.start_time),
			"end_time": get_time(p.end_time),
			"late_grace_period": cint(p.late_grace_period or 0),
			"early_exit_grace_period": cint(p.early_exit_grace_period or 0),
			"minimum_working_hours": flt(p.minimum_working_hours or 0),
			"is_break": cint(p.is_break or 0),
		}
		for p in rows if p.period_name
	]
	return sorted(work_rows, key=lambda p: p["period_number"])


def get_effective_periods(shift_name):
	"""فترات الشفت إن وجدت، وإلا الفترات الافتراضية."""
	periods = get_shift_periods(shift_name)
	if periods:
		return periods
	return get_fallback_periods()


def get_period_range(period, ref_date):
	"""نطاق الفترة (يدعم المرور عبر منتصف الليل)."""
	start_t = period["start_time"]
	end_t = period["end_time"]
	ref = getdate(ref_date)
	start = datetime.combine(ref, start_t)
	if start_t <= end_t:
		end = datetime.combine(ref, end_t)
	else:
		end = datetime.combine(ref + timedelta(days=1), end_t)
	return start, end


def assign_punch_to_period(punch, periods, ref_date):
	"""إسناد البصمة لأقرب فترة زمنية."""
	best = None
	best_dist = timedelta(days=365)
	for p in periods:
		if p["is_break"]:
			continue
		p_start, p_end = get_period_range(p, ref_date)
		if p_start <= punch.time <= p_end:
			return p["period_number"]
		d = abs(punch.time - p_start)
		if d < best_dist:
			best_dist = d
			best = p["period_number"]
	if best is not None and best_dist <= timedelta(minutes=30):
		return best
	return None


def analyze_period(logs, period, ref_date):
	"""حساب نتيجة الفترة الواحدة.

	البصمات بدون log_type (من تطبيق الوسيط) تُعامَل زمنياً:
	أول بصمة في الفترة = دخول، آخر بصمة = خروج.
	البصمات بالـ log_type: IN أولاً ثم OUT.
	"""
	result = {
		"status": "غ",
		"check_in": None,
		"check_out": None,
		"late_minutes": 0,
		"early_exit_minutes": 0,
		"device_in": None,
		"device_out": None,
		"source": None,
	}
	p_start, p_end = get_period_range(period, ref_date)
	logs = sorted(logs, key=lambda l: l.time)

	in_log = None
	out_log = None

	typed = [l for l in logs if l.log_type in ("IN", "OUT")]
	untyped = [l for l in logs if l.log_type not in ("IN", "OUT")]

	if typed:
		# مسار HRMS القياسي: IN ثم OUT
		for l in typed:
			if in_log is None and l.log_type == "IN":
				in_log = l
				continue
			if in_log is not None and l.log_type == "OUT":
				out_log = l
				break
		# بصمات بدون نوع داخل الفترة تكمّل الدخول/الخروج زمنياً
		if untyped:
			if in_log is None:
				in_log = untyped[0]
			if out_log is None and len(untyped) >= 1 and in_log is not None:
				# آخر بصمة غير مصنفة بعد الدخول تعتبر خروجاً
				if untyped[-1].time > in_log.time:
					out_log = untyped[-1]
	else:
		# كل البصمات بدون نوع (من الوسيط): أولها دخول وآخرها خروج
		if logs:
			in_log = logs[0]
			if len(logs) >= 2:
				out_log = logs[-1]

	if in_log:
		result["check_in"] = in_log.time
		result["device_in"] = in_log.device_id
		result["source"] = in_log.source
	if out_log:
		result["check_out"] = out_log.time
		result["device_out"] = out_log.device_id

	if not in_log:
		result["status"] = "غ"
		return result

	# التأخير (من بداية الفترة + مهلة السماح)
	late_grace = timedelta(minutes=cint(period["late_grace_period"]))
	if in_log.time > p_start + late_grace:
		result["late_minutes"] = round((in_log.time - p_start).total_seconds() / 60.0, 1)

	if out_log:
		early_grace = timedelta(minutes=cint(period["early_exit_grace_period"]))
		if p_end - early_grace and out_log.time < p_end - early_grace:
			result["early_exit_minutes"] = round((p_end - out_log.time).total_seconds() / 60.0, 1)

	# حالة الفترة
	if result["late_minutes"] > 0 and result["early_exit_minutes"] > 0:
		result["status"] = "متأخر + خروج مبكر"
	elif result["late_minutes"] > 0:
		result["status"] = "متأخر"
	elif result["early_exit_minutes"] > 0:
		result["status"] = "خروج مبكر"
	elif not out_log:
		result["status"] = "دخول فقط"
	else:
		result["status"] = "ح"
	return result


def get_assignment_map(emp_names, from_date, to_date):
	"""خريطة الشفتات المعينة لكل موظف لكل يوم ضمن النطاق."""
	assignments = frappe.get_all(
		"Shift Assignment",
		filters={
			"employee": ["in", emp_names],
			"docstatus": 1,
		},
		fields=["employee", "shift_type", "start_date", "end_date"],
		order_by="employee,start_date",
	)
	mapping = {}  # emp -> list of (start, end, shift)
	for a in assignments:
		mapping.setdefault(a.employee, []).append(
			(getdate(a.start_date), getdate(a.end_date) if a.end_date else None, a.shift_type)
		)
	return mapping


def resolve_shift(emp, date, assignment_map, checkin_shift_by_date, default_shift_by_emp):
	"""الشفت الفعلي للموظف في تاريخ محدد."""
	best = None
	best_start = None
	for start, end, shift in assignment_map.get(emp, []):
		if start <= date and (end is None or date <= end):
			if best_start is None or start > best_start:
				best_start = start
				best = shift
	if best:
		return best
	if date in checkin_shift_by_date.get(emp, {}):
		return checkin_shift_by_date[emp][date]
	return default_shift_by_emp.get(emp)


def execute(filters=None):
	filters = filters or {}
	from_date = getdate(filters.get("from_date") or nowdate())
	to_date = getdate(filters.get("to_date") or nowdate())
	employee = filters.get("employee")
	branch = filters.get("branch")
	department = filters.get("department")
	company = filters.get("company")
	shift_filter = filters.get("shift_type")

	emp_filter = {"status": ["in", ["Active", ""]]}
	if employee:
		emp_filter["name"] = employee
	if branch:
		emp_filter["branch"] = branch
	if department:
		emp_filter["department"] = department
	if company:
		emp_filter["company"] = company

	employees = frappe.get_all(
		"Employee",
		filters=emp_filter,
		fields=[
			"name", "employee_name", "employee_number", "branch", "department",
			"company", "attendance_device_id", "biometric_employee_id",
			"biometric_fingerprint_id", "default_shift",
		],
		order_by="name",
	)
	emp_names = [e.name for e in employees]

	if not emp_names:
		return [], []

	# البصمات من جهاز البصمة (Employee Checkin) — بالزيادة يوم واحد لتغطية الفترات العابرة لمنتصف الليل
	checkin_from = datetime.combine(from_date, datetime.min.time())
	checkin_to = datetime.combine(to_date + timedelta(days=1), datetime.max.time())
	checkins = frappe.get_all(
		"Employee Checkin",
		filters={
			"employee": ["in", emp_names],
			"time": ["between", [checkin_from.strftime("%Y-%m-%d %H:%M:%S"), checkin_to.strftime("%Y-%m-%d %H:%M:%S")]],
		},
		fields=["employee", "time", "log_type", "device_id", "shift"],
		order_by="employee,time",
	)
	punch_map = {}
	checkin_shift_by_date = {}
	for c in checkins:
		punch_map.setdefault(c.employee, []).append(
			Punch(c.time, c.log_type, c.device_id, source="biometric")
		)
		d = getdate(c.time)
		checkin_shift_by_date.setdefault(c.employee, {})
		if c.shift and d not in checkin_shift_by_date[c.employee]:
			checkin_shift_by_date[c.employee][d] = c.shift

	# الحضور اليدوي (Manual Attendance) — يُدخل كبصمات IN/OUT لهذا اليوم
	manual_docs = frappe.get_all(
		"Manual Attendance",
		filters={"employee": ["in", emp_names], "issue_date": ["between", [from_date, to_date]], "docstatus": 1},
		fields=["name", "employee", "issue_date"],
		order_by="employee,issue_date",
	)
	if manual_docs:
		manual_checks = frappe.get_all(
			"Manual Attendance Checks Table",
			filters={"parent": ["in", [d.name for d in manual_docs]]},
			fields=["parent", "time", "status"],
			order_by="parent,time",
		)
		doc_map = {d.name: d for d in manual_docs}
		for mc in manual_checks:
			d = doc_map.get(mc.parent)
			if not d:
				continue
			punch_dt = datetime.combine(d.issue_date, get_time(mc.time))
			punch_map.setdefault(d.employee, []).append(
				Punch(punch_dt, mc.status, device_id="manual", source="manual")
			)

	# تعيينات الشفت + الشفت الافتراضي
	assignment_map = get_assignment_map(emp_names, from_date, to_date)
	default_shift_by_emp = {e.name: e.default_shift for e in employees}

	# الشفتات المعنية في النطاق لتجميع أسماء الفترات
	distinct_shifts = set()
	for emp in emp_names:
		cur = from_date
		while cur <= to_date:
			sh = resolve_shift(emp, cur, assignment_map, checkin_shift_by_date, default_shift_by_emp)
			if sh and (not shift_filter or sh == shift_filter):
				distinct_shifts.add(sh)
			cur = add_days(cur, 1)

	# فترات التقرير: اتحاد فترات الشفتات المتعددة المعرفة، وإلا الافتراضية
	all_periods = []
	period_names_order = []
	for sh in sorted(distinct_shifts):
		for p in get_effective_periods(sh):
			if p["period_name"] not in period_names_order:
				period_names_order.append(p["period_name"])
			all_periods.append(p)
	if not all_periods:
		all_periods = get_fallback_periods()
		period_names_order = [p["period_name"] for p in all_periods]

	# جدول الحضور (Attendance) لحالة اليوم
	attendances = frappe.get_all(
		"Attendance",
		filters={
			"employee": ["in", emp_names],
			"attendance_date": ["between", [from_date, to_date]],
			"docstatus": 1,
		},
		fields=["employee", "attendance_date", "status", "shift"],
	)
	att_map = {}
	for a in attendances:
		att_map.setdefault((a.employee, getdate(a.attendance_date)), []).append(a)

	def fmt_time(dt):
		return dt.strftime("%H:%M") if dt else ""

	# الأعمدة الثابتة
	columns = [
		{"label": "الرقم الوظيفي", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 120},
		{"label": "اسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 180},
		{"label": "نوع الدوام", "fieldname": "shift", "fieldtype": "Data", "width": 140},
		{"label": "الفرع", "fieldname": "branch", "fieldtype": "Data", "width": 130},
		{"label": "القسم", "fieldname": "department", "fieldtype": "Data", "width": 150},
		{"label": "التاريخ", "fieldname": "attendance_date", "fieldtype": "Date", "width": 100},
		{"label": "رقم البصمة المرتبط", "fieldname": "biometric_number", "fieldtype": "Data", "width": 110},
	]
	period_idx = {}
	for i, pname in enumerate(period_names_order):
		k = i + 1
		period_idx[pname] = k
		columns += [
			{"label": f"{pname} - دخول", "fieldname": f"p{k}_in", "fieldtype": "Data", "width": 90},
			{"label": f"{pname} - خروج", "fieldname": f"p{k}_out", "fieldtype": "Data", "width": 90},
			{"label": f"{pname} - تأخير (د)", "fieldname": f"p{k}_late", "fieldtype": "Data", "width": 85},
			{"label": f"{pname} - الحالة", "fieldname": f"p{k}_status", "fieldtype": "Data", "width": 130},
		]
	columns += [
		{"label": "حالة اليوم", "fieldname": "day_status", "fieldtype": "Data", "width": 110},
		{"label": "إجمالي التأخير (د)", "fieldname": "total_late", "fieldtype": "Data", "width": 90},
	]

	rows = []
	for e in employees:
		emp_punches = sorted(punch_map.get(e.name, []), key=lambda l: l.time)
		biometric_number = e.attendance_device_id or e.biometric_fingerprint_id or e.biometric_employee_id or ""
		cur = from_date
		while cur <= to_date:
			shift_name = resolve_shift(e.name, cur, assignment_map, checkin_shift_by_date, default_shift_by_emp)
			if shift_filter and shift_name != shift_filter:
				cur = add_days(cur, 1)
				continue

			periods = [dict(p) for p in get_effective_periods(shift_name)]
			assignments = {p["period_number"]: [] for p in periods}
			for punch in emp_punches:
				pidx = assign_punch_to_period(punch, periods, cur)
				if pidx is not None:
					assignments[pidx].append(punch)

			period_results = {}
			total_late = 0.0
			for p in periods:
				logs = assignments.get(p["period_number"], [])
				res = analyze_period(logs, p, cur)
				period_results[p["period_name"]] = res
				if res["late_minutes"] > 0:
					total_late += res["late_minutes"]

			# حالة اليوم: من جدول Attendance إن وجد، وإلا حساب من الفترات
			att_list = att_map.get((e.name, cur), [])
			att_status = att_list[0].status if att_list else None
			if att_status in ("On Leave", "Work From Home", "Holiday"):
				day_status = att_status
			else:
				attended_count = sum(1 for r in period_results.values() if r["check_in"])
				absent_count = sum(1 for r in period_results.values() if r["status"] == "غ")
				if not period_results:
					day_status = "غائب"
				elif attended_count == 0 and absent_count == len(period_results):
					day_status = "غائب"
				elif attended_count == len(period_results):
					day_status = "حاضر"
				else:
					# بعض الفترات فقط
					day_status = "نصف فترة" if attended_count * 2 == len(period_results) else "جزئي"

			row = {
				"employee": e.name,
				"employee_name": e.employee_name,
				"shift": shift_name or "",
				"branch": e.branch,
				"department": e.department,
				"attendance_date": cur,
				"biometric_number": biometric_number,
				"day_status": day_status,
				"total_late": round(total_late, 1) if total_late else "",
			}
			for pname, k in period_idx.items():
				r = period_results.get(pname, {
					"status": "غ", "check_in": None, "check_out": None,
					"late_minutes": 0, "early_exit_minutes": 0,
				})
				row[f"p{k}_in"] = fmt_time(r["check_in"])
				row[f"p{k}_out"] = fmt_time(r["check_out"])
				row[f"p{k}_late"] = r["late_minutes"] if r["late_minutes"] else ""
				row[f"p{k}_status"] = r["status"]

			rows.append(row)
			cur = add_days(cur, 1)

	return columns, rows