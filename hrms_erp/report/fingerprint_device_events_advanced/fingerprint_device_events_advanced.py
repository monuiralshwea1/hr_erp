# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	log_type = filters.get("log_type")
	from_time = filters.get("from_time")
	to_time = filters.get("to_time")
	only_managers = filters.get("only_managers")

	get_raw_data_sql = f"""
	SELECT
	    ec.employee,
	    ec.employee_name,
	    DATE(ec.time) AS work_date,
	    CASE DAYOFWEEK(ec.time)
	        WHEN 1 THEN 'الأحد'
	        WHEN 2 THEN 'الاثنين'
	        WHEN 3 THEN 'الثلاثاء'
	        WHEN 4 THEN 'الأربعاء'
	        WHEN 5 THEN 'الخميس'
	        WHEN 6 THEN 'الجمعة'
	        WHEN 7 THEN 'السبت'
	    END AS day_name,
	    e.is_manager,
	    e.fingerprint_id,
	    e.department,
	    e.designation,
	    e.branch,
	    GROUP_CONCAT(
	        TIME(ec.time)
	        ORDER BY ec.time ASC SEPARATOR ', '
	    ) AS times
	FROM
	    `tabEmployee Checkin` ec
	INNER JOIN `tabEmployee` e ON e.name = ec.employee
	WHERE
	    DATE(ec.time) BETWEEN %(from_date)s AND %(to_date)s
	GROUP BY
	    ec.employee,
	    DATE(ec.time),
	    e.is_manager,
	    e.fingerprint_id,
	    ec.employee_name
	ORDER BY
	    e.fingerprint_id,
	    DATE(ec.time) DESC
    

	"""

	raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)

	columns = []
	columns.append({"label": "#", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150})
	columns.append({"label": "أسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الفرع", "fieldname": "branch", "fieldtype": "Data"})
	columns.append({"label": "القسم", "fieldname": "department", "fieldtype": "Data"})
	columns.append({"label": "التخصص", "fieldname": "designation", "fieldtype": "Data"})
	columns.append({"label": "مدير؟", "fieldname": "is_manager", "fieldtype": "Int"})
	columns.append({"label": "البصمة", "fieldname": "fingerprint_id", "fieldtype": "Int"})
	columns.append({"label": "التاريخ", "fieldname": "date", "fieldtype": "Data", "width": 300})
	columns.append({"label": "اليوم", "fieldname": "day", "fieldtype": "Data", "width": 300})


	for i in range(20):
	    columns.append({
	        "label": f"F{i+1}",
	        "fieldname": f"F{i}",
	        "fieldtype": "Data",
	        "width": 100
	    })
	emps = []
	for r in raw_data:
    
	    if only_managers and r.is_manager == 0:
	        continue
    
	    employee_map = {}
	    employee_map["employee"] = r.employee
	    employee_map["employee_name"] = f"{r.employee_name}"
	    employee_map["date"] = f"{r.work_date}"
	    employee_map["fingerprint_id"] = f"{r.fingerprint_id}"
	    employee_map["department"] = f"{r.department}"
	    employee_map["designation"] = f"{r.designation}"
	    employee_map["branch"] = f"{r.branch}"
	    employee_map["is_manager"] = f"{r.is_manager}"
	    employee_map["day"] = f"{r.day_name}"
    
	    times_list = [t.strip() for t in r.times.split(",")]
	    fixed_times = []
	    f_index = 0
	    is_found = False;
	    if log_type == "IN":
	        first_time = times_list[0]
	        if frappe.utils.get_time(first_time) >= frappe.utils.get_time(from_time) and frappe.utils.get_time(first_time) <= frappe.utils.get_time(to_time):
	            is_found = True
    
	    if log_type == "OUT":
	        first_time = times_list[-1]
	        if frappe.utils.get_time(first_time) >= frappe.utils.get_time(from_time) and frappe.utils.get_time(first_time) <= frappe.utils.get_time(to_time):
	            is_found = True
            
	    for t in times_list:
	        employee_map[f"F{f_index}"] = frappe.utils.format_time(t, "hh:mm a")
	        f_index = f_index + 1
    
	    if is_found:  
	        emps.append(employee_map)
	return columns, emps
