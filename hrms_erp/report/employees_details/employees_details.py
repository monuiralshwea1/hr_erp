# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	filters = filters or {}
	data = frappe.db.sql(f"""
		SELECT DISTINCT
		e.name as 'ID',
		concat(e.first_name,' ', IFNULL(e.middle_name, ''),' ', IFNULL(e.last_name, '')) as 'Full Name',
		e.date_of_joining as 'Date Of Joining',
		e.fingerprint_id as 'Fingerprint ID',
		case when e.gender = 'Male' then 'ذكر' Else 'انثى' end as 'Gender',
		e.department as 'Department',
		e.designation as 'Designation',
		case when e.is_manager = 1 then 'نعم' Else 'لا' end as 'Is Manager ?',
		e.grade as 'Grade',
		e.level as 'Level',
		e.class as 'Class',
		e.ctc as 'Total Earning'
		FROM `tabEmployee` e
		where e.status = 'Active'
		order by e.ctc DESC
	""", filters, as_dict=0)
	return None, data
