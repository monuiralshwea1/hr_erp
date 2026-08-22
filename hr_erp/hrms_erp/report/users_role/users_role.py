# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	data = frappe.db.sql(f"""
		SELECT 
		u.full_name,
		    u.name AS user,
		    e.branch,
		    e.department,e.designation,
		    GROUP_CONCAT(r.role ORDER BY r.role SEPARATOR ', ') AS roles,
		    u.creation,
		    CASE WHEN u.enabled = 1 THEN 'Active' ELSE 'Closed' END Status
		FROM `tabUser` u
		left join `tabEmployee` e on e.user_id = u.name
		LEFT JOIN `tabHas Role` r ON r.parent = u.name
		GROUP BY u.name
		ORDER BY u.name;
	""", filters, as_dict=0)
	return None, data
