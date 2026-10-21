# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
تقرير خصومات الرواتب وصافي الراتب — Salary Deductions Report
==============================================================

يعرض لكل قسيمة راتب:
  - دقائق التأخير وخصم التأخير
  - أيام الغياب (مع احتساب نصف اليوم) وخصم الغياب
  - جميع بنود المستحقات (أعمدة ديناميكية حسب المكوّنات الموجودة)
  - جميع بنود الخصومات الأخرى (أعمدة ديناميكية)
  - إجمالي المستحقات، إجمالي الخصومات، صافي الراتب

ملاحظة: القيم تُجمع من سطور القسيمة (Salary Detail) مباشرة، حتى تظهر
الخصومات المضافة من payroll_integration/late_absence_deduction.py.
التسميات مكتوبة بالعربية مباشرة (لغة النظام ar) لضمان ظهورها ثابتة.
"""

import frappe
from frappe.utils import flt

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"


def execute(filters=None):
	filters = frappe._dict(filters or {})
	slips = get_salary_slips(filters)

	late_component, absence_component = get_deduction_components()
	earning_components, deduction_components = get_component_names(
		slips, late_component, absence_component
	)

	earning_fields = {
		component: "earning_{0}".format(index)
		for index, component in enumerate(earning_components)
	}
	deduction_fields = {
		component: "deduction_{0}".format(index)
		for index, component in enumerate(deduction_components)
	}

	late_factor, absence_factor = get_factors()
	columns = get_columns(earning_components, deduction_components, earning_fields, deduction_fields)
	data = get_data(
		slips,
		late_component,
		absence_component,
		earning_fields,
		deduction_fields,
		late_factor,
		absence_factor,
	)

	return columns, data


def get_factors():
	"""عوامل خصم التأخير والغياب من الإعدادات.

	تُطبَّق على الكمية المعروضة (الدقائق/الأيام) بنفس الطريقة التي تُطبَّق بها
	على المبلغ، حتى يعكس التقرير الأثر الفعلي للإعدادات الحالية.
	"""
	late_factor = 1.0
	absence_factor = 1.0

	if frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		late_factor = flt(settings.get("late_deduction_factor") or 1.0)
		absence_factor = flt(settings.get("absence_deduction_factor") or 1.0)

	return late_factor, absence_factor


def get_deduction_components():
	"""أسماء مكوّنات خصم التأخير والغياب من الإعدادات."""
	late_component = "Late Deduction"
	absence_component = "Absence Deduction"

	if frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		settings = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		late_component = settings.get("late_deduction_component") or late_component
		absence_component = settings.get("absence_deduction_component") or absence_component

	return late_component, absence_component


def get_salary_slips(filters):
	"""جلب القسائم ضمن الفترة مع الفلاتر."""
	conditions = []
	values = {}

	if filters.get("from_date"):
		conditions.append("ss.start_date <= %(to_date)s")
		values["to_date"] = filters.to_date

	if filters.get("to_date"):
		conditions.append("ss.end_date >= %(from_date)s")
		values["from_date"] = filters.from_date

	if filters.get("employee"):
		conditions.append("ss.employee = %(employee)s")
		values["employee"] = filters.employee

	if filters.get("department"):
		conditions.append("ss.department = %(department)s")
		values["department"] = filters.department

	if filters.get("company"):
		conditions.append("ss.company = %(company)s")
		values["company"] = filters.company

	status = filters.get("status") or "Submitted"
	if status == "Draft":
		conditions.append("ss.docstatus = 0")
	elif status == "Submitted":
		conditions.append("ss.docstatus = 1")
	else:
		conditions.append("ss.docstatus in (0, 1)")

	where_clause = " and ".join(conditions) if conditions else "1=1"

	return frappe.db.sql(
		"""
		select
			ss.name, ss.employee, ss.employee_name, ss.department, ss.company,
			ss.start_date, ss.end_date, ss.docstatus, ss.status,
			ss.gross_pay, ss.total_deduction, ss.net_pay,
			ss.total_late_minutes, ss.total_absent_days,
			ss.total_loan_repayment,
			ss.audit_last_recalc_at
		from `tabSalary Slip` ss
		where {where_clause}
		order by ss.start_date desc, ss.employee asc
		""".format(where_clause=where_clause),
		values,
		as_dict=True,
	)


def get_component_names(slips, late_component, absence_component):
	"""أسماء بنود المستحقات والخصومات الظاهرة في القسائم المفلترة."""
	if not slips:
		return [], []

	slip_names = [slip.name for slip in slips]
	details = frappe.get_all(
		"Salary Detail",
		filters={
			"parent": ["in", slip_names],
			"parenttype": "Salary Slip",
			"parentfield": ["in", ["earnings", "deductions"]],
		},
		fields=["parentfield", "salary_component"],
		order_by="idx asc",
	)

	earning_components = []
	deduction_components = []

	for row in details:
		component = row.get("salary_component")
		if not component:
			continue

		if row.get("parentfield") == "earnings":
			if component not in earning_components:
				earning_components.append(component)
		else:
			# خصم التأخير والغياب لهما أعمدة ثابتة، لا نكررهما
			if component in (late_component, absence_component):
				continue
			if component not in deduction_components:
				deduction_components.append(component)

	return earning_components, deduction_components


def get_columns(
	earning_components,
	deduction_components,
	earning_fields,
	deduction_fields,
):
	columns = [
		{
			"label": "الموظف",
			"fieldname": "employee",
			"fieldtype": "Link",
			"options": "Employee",
			"width": 110,
		},
		{
			"label": "اسم الموظف",
			"fieldname": "employee_name",
			"fieldtype": "Data",
			"width": 170,
		},
		{
			"label": "القسم",
			"fieldname": "department",
			"fieldtype": "Link",
			"options": "Department",
			"width": 120,
		},
		{
			"label": "قسيمة الراتب",
			"fieldname": "salary_slip",
			"fieldtype": "Link",
			"options": "Salary Slip",
			"width": 155,
		},
		{
			"label": "من تاريخ",
			"fieldname": "start_date",
			"fieldtype": "Date",
			"width": 95,
		},
		{
			"label": "إلى تاريخ",
			"fieldname": "end_date",
			"fieldtype": "Date",
			"width": 95,
		},
		{
			"label": "الحالة",
			"fieldname": "status",
			"fieldtype": "Data",
			"width": 90,
		},
		{
			"label": "دقائق التأخير",
			"fieldname": "total_late_minutes",
			"fieldtype": "Float",
			"width": 110,
		},
		{
			"label": "دقائق التأخير الفعّالة",
			"fieldname": "total_late_minutes_effective",
			"fieldtype": "Float",
			"width": 130,
		},
		{
			"label": "خصم التأخير",
			"fieldname": "late_deduction",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": "أيام الغياب",
			"fieldname": "total_absent_days",
			"fieldtype": "Float",
			"width": 100,
		},
		{
			"label": "أيام الغياب الفعّالة",
			"fieldname": "total_absent_days_effective",
			"fieldtype": "Float",
			"width": 120,
		},
		{
			"label": "خصم الغياب",
			"fieldname": "absence_deduction",
			"fieldtype": "Currency",
			"width": 110,
		},
		{
			"label": "آخر إعادة احتساب",
			"fieldname": "audit_last_recalc_at",
			"fieldtype": "Datetime",
			"width": 140,
		},
	]

	# أعمدة المستحقات الديناميكية
	for component in earning_components:
		columns.append(
			{
				"label": "مستحق: {0}".format(component),
				"fieldname": earning_fields[component],
				"fieldtype": "Currency",
				"width": 130,
			}
		)

	columns.append(
		{
			"label": "إجمالي المستحقات",
			"fieldname": "gross_pay",
			"fieldtype": "Currency",
			"width": 130,
		}
	)

	# أعمدة الخصومات الأخرى الديناميكية
	for component in deduction_components:
		columns.append(
			{
				"label": "خصم: {0}".format(component),
				"fieldname": deduction_fields[component],
				"fieldtype": "Currency",
				"width": 130,
			}
		)

	columns.extend(
		[
			{
				"label": "إجمالي الخصومات",
				"fieldname": "total_deduction",
				"fieldtype": "Currency",
				"width": 130,
			},
			{
				"label": "صافي الراتب",
				"fieldname": "net_pay",
				"fieldtype": "Currency",
				"width": 130,
			},
		]
	)

	return columns


def get_data(
	slips,
	late_component,
	absence_component,
	earning_fields,
	deduction_fields,
	late_factor=1.0,
	absence_factor=1.0,
):
	"""تجميع بيانات القسائم من سطور Salary Detail."""
	if not slips:
		return []

	slip_names = [slip.name for slip in slips]
	details = frappe.get_all(
		"Salary Detail",
		filters={
			"parent": ["in", slip_names],
			"parenttype": "Salary Slip",
			"parentfield": ["in", ["earnings", "deductions"]],
		},
		fields=["parent", "parentfield", "salary_component", "amount"],
	)

	details_by_slip = {}
	for row in details:
		slip_data = details_by_slip.setdefault(
			row.parent, {"earnings": {}, "deductions": {}}
		)
		section = "earnings" if row.parentfield == "earnings" else "deductions"
		component = row.salary_component
		slip_data[section][component] = flt(slip_data[section].get(component, 0)) + flt(
			row.amount
		)

	data = []
	for slip in slips:
		slip_data = details_by_slip.get(slip.name, {"earnings": {}, "deductions": {}})
		earnings = slip_data["earnings"]
		deductions = slip_data["deductions"]

		gross_pay = sum(flt(value) for value in earnings.values())
		late_deduction = flt(deductions.get(late_component))
		absence_deduction = flt(deductions.get(absence_component))
		total_deduction = sum(flt(value) for value in deductions.values())
		net_pay = gross_pay - total_deduction - flt(slip.total_loan_repayment)

		raw_late_minutes = flt(slip.total_late_minutes)
		raw_absent_days = flt(slip.total_absent_days)

		row = {
			"employee": slip.employee,
			"employee_name": slip.employee_name,
			"department": slip.department,
			"salary_slip": slip.name,
			"start_date": slip.start_date,
			"end_date": slip.end_date,
			"status": slip.status,
			"total_late_minutes": raw_late_minutes,
			"total_late_minutes_effective": flt(raw_late_minutes * flt(late_factor)),
			"late_deduction": late_deduction,
			"total_absent_days": raw_absent_days,
			"total_absent_days_effective": flt(raw_absent_days * flt(absence_factor)),
			"absence_deduction": absence_deduction,
			"audit_last_recalc_at": getattr(slip, "audit_last_recalc_at", None),
			"gross_pay": gross_pay,
			"total_deduction": total_deduction,
			"net_pay": net_pay,
		}

		for component, fieldname in earning_fields.items():
			row[fieldname] = flt(earnings.get(component))

		for component, fieldname in deduction_fields.items():
			row[fieldname] = flt(deductions.get(component))

		data.append(row)

	return add_total_row(data, earning_fields, deduction_fields)


def add_total_row(data, earning_fields, deduction_fields):
	"""إضافة صف إجمالي في نهاية التقرير."""
	if not data:
		return data

	numeric_fields = [
		"total_late_minutes",
		"total_late_minutes_effective",
		"late_deduction",
		"total_absent_days",
		"total_absent_days_effective",
		"absence_deduction",
		"gross_pay",
		"total_deduction",
		"net_pay",
	]
	numeric_fields.extend(earning_fields.values())
	numeric_fields.extend(deduction_fields.values())

	total_row = {"employee": "الإجمالي", "is_total_row": 1}
	for fieldname in numeric_fields:
		total_row[fieldname] = sum(flt(row.get(fieldname)) for row in data)

	data.append(total_row)
	return data
