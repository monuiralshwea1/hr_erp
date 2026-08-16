# Copyright (c) 2026, moneer and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import get_first_day, today


def execute(filters=None):
	filters = frappe._dict(filters or {})
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	return [
		{
			"fieldname": "employee",
			"label": _("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"width": 120,
		},
		{
			"fieldname": "employee_name",
			"label": _("Employee Name"),
			"fieldtype": "Data",
			"width": 180,
		},
		{
			"fieldname": "date",
			"label": _("Date"),
			"fieldtype": "Date",
			"width": 100,
		},
		{
			"fieldname": "time",
			"label": _("Time"),
			"fieldtype": "Datetime",
			"width": 150,
		},
		{
			"fieldname": "log_type",
			"label": _("Type"),
			"fieldtype": "Data",
			"width": 80,
		},
		{
			"fieldname": "device_id",
			"label": _("Device"),
			"fieldtype": "Data",
			"width": 120,
		},
		{
			"fieldname": "shift",
			"label": _("Shift"),
			"fieldtype": "Link",
			"options": "Shift Type",
			"width": 140,
		},
	]


def get_data(filters):
	from frappe.utils import getdate

	from_date = filters.get("from_date") or get_first_day(today())
	to_date = filters.get("to_date") or today()

	conditions = []
	values = {"from_date": from_date, "to_date": to_date}
	if filters.get("employee"):
		conditions.append("e.employee = %(employee)s")
		values["employee"] = filters.get("employee")
	if filters.get("device_id"):
		conditions.append("e.device_id = %(device_id)s")
		values["device_id"] = filters.get("device_id")
	if filters.get("log_type"):
		conditions.append("e.log_type = %(log_type)s")
		values["log_type"] = filters.get("log_type")

	where = " and ".join(conditions) if conditions else "1=1"

	return frappe.db.sql(
		"""
		select
			e.employee,
			emp.employee_name,
			date(e.time) as date,
			e.time,
			e.log_type,
			e.device_id,
			e.shift
		from `tabEmployee Checkin` e
		left join `tabEmployee` emp on emp.name = e.employee
		where date(e.time) between %(from_date)s and %(to_date)s
			and {where}
		order by e.time asc, e.employee asc
		""".format(where=where),
		values,
		as_dict=True,
	)
