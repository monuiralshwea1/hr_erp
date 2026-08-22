# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	employee = filters.get("employee")

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

	get_raw_data_sql = f"""
   
	    WITH RECURSIVE calendar AS (
	    SELECT DATE(%(from_date)s) AS work_date
	    UNION ALL
	    SELECT DATE_ADD(work_date, INTERVAL 1 DAY)
	    FROM calendar
	    WHERE work_date < %(to_date)s
	)

	SELECT
	    e.name AS employee,
	    e.employee_name,
	    c.work_date,
	    e.fingerprint_id,
	    e.department,
	    e.designation,
	    e.branch,
	    CASE 
	        WHEN at.status IS NOT NULL AND at.status <> '' 
	            THEN at.status
	        ELSE (CASE WHEN h.description <> '' THEN h.description WHEN Count(ec.time) > 0 THEN 'Present' ELSE 'Absent' END)
	    END AS status,
	    GROUP_CONCAT(
	        TIME(ec.time)
	        ORDER BY ec.time ASC SEPARATOR ', '
	    ) AS times
	FROM calendar c
	INNER JOIN `tabEmployee` e
	    ON e.name = %(employee)s
	LEFT JOIN `tabAttendance` at
	    ON at.employee = e.name
	    AND at.attendance_date = c.work_date
	LEFT JOIN `tabEmployee Checkin` ec
	    ON ec.employee = e.name
	    AND DATE(ec.time) = c.work_date
	LEFT JOIN `tabHoliday` h
	    ON h.holiday_date = c.work_date
	WHERE
	    e.status = 'Active'
	GROUP BY
	    c.work_date,
	    e.name,
	    e.employee_name,
	    e.fingerprint_id,
	    e.department,
	    e.designation,
	    e.branch,
	    at.status,
	    h.description
	ORDER BY
	    e.fingerprint_id,
	    c.work_date DESC;


	"""

	raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date, "employee":employee}, as_dict=True)
	columns = []
	columns.append({"label": "#", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150})
	columns.append({"label": "أسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الفرع", "fieldname": "branch", "fieldtype": "Data"})
	columns.append({"label": "القسم", "fieldname": "department", "fieldtype": "Data"})
	columns.append({"label": "التخصص", "fieldname": "designation", "fieldtype": "Data"})
	columns.append({"label": "البصمة", "fieldname": "fingerprint_id", "fieldtype": "Int"})
	columns.append({"label": "التاريخ", "fieldname": "date", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الحالة", "fieldname": "status", "fieldtype": "Data", "width": 300})

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
	    employee_map["status"] = f"{r.status}"
    
	    if r.status == "Present":
	        times_list = [t.strip() for t in r.times.split(",")]
	        fixed_times = []
	        f_index = 0
	        for t in times_list:
	            employee_map[f"F{f_index}"] = frappe.utils.format_time(t, "hh:mm a")
	            f_index = f_index + 1
        
	        if f_index > 1:
	            employee_map["status"] = "Present"
	        elif f_index == 1:
	            employee_map["status"] = "FP_FOGET"
        
	    att_status = employee_map["status"]
	    if att_status == "Present":
	        employee_map["status"] = "حاضر"
	    elif att_status == "FP_FOGET":
	        employee_map["status"] = "نسيان بصمة"
	    elif att_status == "Absent":
	        employee_map["status"] = "غائب"
	    elif att_status == "On Leave":
	        employee_map["status"] = "اجازة"
	    elif att_status == "Friday":
	        employee_map["status"] = "جمعة"
        
	    emps.append(employee_map)
	return columns, emps
