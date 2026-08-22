# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	summary = filters.get("summary")

	columns = []
	get_raw_data_sql = ""
	raw_data = None

	if summary:
	    columns = []
	    get_raw_data_sql = ""

	    columns.append({"label": _('Employee Name'), "fieldname": "employee_name", "fieldtype": "Data", "width": 150})
	    columns.append({"label": _('Leave Type'), "fieldname": "leave_type", "fieldtype": "Data", "width": 150})
	    columns.append({"label": _('Leaves'), "fieldname": "leaves", "fieldtype": "Data", "width": 150})
    
	    get_raw_data_sql = f"""
    
	        SELECT employee_name,
	        leave_type,
	        COUNT(employee_name) as leaves from `tabAttendance` e
	        WHERE attendance_date between %(from_date)s and %(to_date)s and status = 'On Leave'
	        GROUP BY employee_name, leave_type
	        order by employee_name desc
	    """
    
	    raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)
	else:
	    columns = []
	    get_raw_data_sql = ""

	    columns.append({"label": _('Employee Name'), "fieldname": "employee_name", "fieldtype": "Data", "width": 150})
	    columns.append({"label": _('Leave Type'), "fieldname": "leave_type", "fieldtype": "Data", "width": 150})
	    columns.append({"label": _('Date'), "fieldname": "attendance_date", "fieldtype": "Data", "width": 150})
    
	    get_raw_data_sql = f"""
    
	        SELECT 
	            employee_name,
	            leave_type,
	            attendance_date
	        from `tabAttendance` e
	        WHERE attendance_date between %(from_date)s and %(to_date)s and status = 'On Leave'
	        order by employee_name, attendance_date desc 
	    """
	    raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)
	return columns, raw_data
