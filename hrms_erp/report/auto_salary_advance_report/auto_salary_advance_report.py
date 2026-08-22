# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	data = frappe.db.sql(f"""
		SELECT
		 adv.title, adv.from_date, employee, employee_name, amount
		FROM
		 `tabAuto Salary Advance Table` adv_t
		 INNER JOIN `tabAuto Salary Advance` adv ON adv.name = adv_t.parent
 
		 WHERE
		 adv.docstatus = 1 and adv.from_date = %(to_date)s
 
		ORDER BY adv.from_date
	""", filters, as_dict=0)
	return None, data
