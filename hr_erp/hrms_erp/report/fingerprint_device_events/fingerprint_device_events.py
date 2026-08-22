# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	# user_id = frappe.session.user
	# current_emps = frappe.get_list(
	#     "Employee",
	#     fields= ['*'],
	#     filters=[
	#         ["user_id", "=", user_id],
	#     ],
	#     limit=1
	# );
	# current_emp = None
	# if len(current_emps) > 0:
	#     current_emp = current_emps[0]


	get_raw_data_sql = f"""
	        SELECT
	    ec.employee,
	    ec.employee_name,
	    DATE(ec.time) AS work_date,
	    e.fingerprint_id,
	    e.department,
	    e.designation,
	    e.branch,
	    GROUP_CONCAT(
	        time(ec.time)
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
	    e.fingerprint_id,
	    ec.employee_name
	ORDER BY
	    e.fingerprint_id,
	    DATE(ec.time) DESC
    

	"""

	# get_raw_data_sql2 = f"""
	#         SELECT
	#     ec.employee,
	#     ec.employee_name,
	#     DATE(ec.time) AS work_date,
	#     e.fingerprint_id,
	#     e.department,
	#     e.designation,
	#     e.branch,
	#     e.reports_to,
	#     GROUP_CONCAT(
	#         time(ec.time)
	#         ORDER BY ec.time ASC SEPARATOR ', '
	#     ) AS times
	# FROM
	#     `tabEmployee Checkin` ec
	# INNER JOIN `tabEmployee` e ON e.name = ec.employee
	# WHERE
	#     DATE(ec.time) BETWEEN %(from_date)s AND %(to_date)s AND
	#     case when {current_emp != None} then
	#     e.employee = 'HR-EMP-00025' or reports_to = 'HR-EMP-00025' 
	#     ELSE 1=1
	#     END
	# GROUP BY
	#     ec.employee,
	#     DATE(ec.time),
	#     e.fingerprint_id,
	#     ec.employee_name
	# ORDER BY
	#     e.fingerprint_id,
	#     DATE(ec.time) DESC
    

	# """

	raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)

	columns = []
	columns.append({"label": "#", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150})
	columns.append({"label": "أسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الفرع", "fieldname": "branch", "fieldtype": "Data"})
	columns.append({"label": "القسم", "fieldname": "department", "fieldtype": "Data"})
	columns.append({"label": "التخصص", "fieldname": "designation", "fieldtype": "Data"})
	columns.append({"label": "البصمة", "fieldname": "fingerprint_id", "fieldtype": "Int"})
	columns.append({"label": "التاريخ", "fieldname": "date", "fieldtype": "Data", "width": 300})

	for i in range(20):
	    columns.append({
	        "label": f"F{i+1}",
	        "fieldname": f"F{i}",
	        "fieldtype": "Data",
	        "width": 100
	    })
	emps = []
	for r in raw_data:
	    employee_map = {}
	    employee_map["employee"] = r.employee
	    employee_map["employee_name"] = f"{r.employee_name}"
	    employee_map["date"] = f"{r.work_date}"
	    employee_map["fingerprint_id"] = f"{r.fingerprint_id}"
	    employee_map["department"] = f"{r.department}"
	    employee_map["designation"] = f"{r.designation}"
	    employee_map["branch"] = f"{r.branch}"
    
	    times_list = [t.strip() for t in r.times.split(",")]
	    fixed_times = []
	    f_index = 0
	    for t in times_list:
	        employee_map[f"F{f_index}"] = frappe.utils.format_time(t, "hh:mm a")
	        f_index = f_index + 1
        
	    emps.append(employee_map)
	return columns, emps
