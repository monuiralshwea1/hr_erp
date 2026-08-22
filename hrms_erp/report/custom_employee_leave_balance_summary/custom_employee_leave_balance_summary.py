# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	date = filters.get("date")
	company = filters.get("company")
	report_filters = {
	            "date": date,
	            "company": company,
	            "employee_status": "Active"
	        }

	report_data = frappe.call(
	    "frappe.desk.query_report.run",
	    report_name="Employee Leave Balance Summary",
	    filters=report_filters,
	    _lang="en"
	)

	columns = report_data.get("columns")
	result_rows = report_data.get("result")

	prev_short_leaves = frappe.get_list(
	    "Short Leave",
	    fields= ['*'],
	    filters=[
	        ["docstatus", "=", 1],
	    ],
	    limit=0
	);

	for r in result_rows:
	    emp = r.get("employee") #or r["الموظف"]
	    emp_name = r.get("employee_name") #or r["اسم_الموظف"]
    
	    total_short_leaves = {}
	    for sl in prev_short_leaves:
	        if sl.employee == emp:
	            short_leave_value = (sl.short_leave_amount_in_minuts / sl.shift_duration_minutes / 60)
	            key = f"{sl.leave_type}"
            
	            if key not in total_short_leaves:
	                total_short_leaves[key] = round(short_leave_value,2)
	            else:
	                total_short_leaves[key] = round(total_short_leaves[key] + short_leave_value,2)
    
	    for tsl in total_short_leaves:
	        key = f"{tsl}"
	        v = total_short_leaves[key]
	        rKey = key.replace(" ", "_")
	        oldValue = r[rKey]
	        r[rKey] = round(float(r[rKey]) - v,2)
	        g = r[rKey]
	return columns, result_rows
