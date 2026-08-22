# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")

	get_raw_data_sql = """
   
	SELECT
	    at.employee,
	    at.employee_name,
	    at.attendance_date AS attendance_date,
	    time(0) as late_enter_time,
	    time(0) as early_exit_time,
	    CASE WHEN  COUNT(ec.time) > 1 THEN 'Present' 
	        WHEN COUNT(ec.time) = 0 THEN  at.status
	        WHEN COUNT(ec.time) = 1 THEN  'Half Day'
	        ELSE 'Absent' END as status,
        
	    COUNT(ec.time) AS checks_count
	FROM `tabAttendance` at
	LEFT JOIN `tabEmployee Checkin` ec
	       ON ec.employee = at.employee
	      AND DATE(ec.time) = at.attendance_date
	WHERE 
	    at.attendance_date BETWEEN %(from_date)s AND %(to_date)s
	GROUP BY 
	    at.employee,
	    at.employee_name,
	    at.attendance_date

	UNION

	-- Part 2: Checkins without attendance
	SELECT
	    ec.employee,
	    ec.employee_name,
	    DATE(ec.time) AS attendance_date,
	    time(0) as late_enter_time,
	    time(0) as early_exit_time,
    
	    CASE WHEN  COUNT(ec.time) > 1 THEN 'Present' 
	        WHEN COUNT(ec.time) = 0 THEN  at.status
	        WHEN COUNT(ec.time) = 1 THEN  'Half Day'
	        ELSE 'Absent' END as status,
        
	    COUNT(ec.time) AS checks_count
	FROM `tabEmployee Checkin` ec
	LEFT JOIN `tabAttendance` at
	       ON at.employee = ec.employee
	      AND at.attendance_date = DATE(ec.time)
	WHERE 
	    DATE(ec.time) BETWEEN %(from_date)s AND %(to_date)s
	    AND at.attendance_date IS NULL
	GROUP BY 
	    ec.employee,
	    ec.employee_name,
	    DATE(ec.time)

	"""

	raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)

	get_raw_data_sql = """
	SELECT DISTINCT e.*, concat(e.first_name,' ', IFNULL(e.middle_name, ''),' ', IFNULL(e.last_name, '')) as full_name,
	    d.department_name
	FROM
	        `tabEmployee` e
	INNER JOIN `tabDepartment` d on d.name = e.department
	WHERE status = 'Active'

	ORDER BY CAST(fingerprint_id AS INT)
	"""

	employees = frappe.db.sql(get_raw_data_sql, as_dict=True)

	get_raw_data_sql = """
	    SELECT
	        *
	    FROM
	        `tabHoliday`
        
	    WHERE
	        holiday_date between %(from_date)s and %(to_date)s
	    ORDER BY holiday_date
    
	"""

	holidays_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)

	log(raw_data)

	columns = []
	columns.append({"label": "#", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150})
	columns.append({"label": "أسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الفرع", "fieldname": "branch", "fieldtype": "Data", "width": 300})
	columns.append({"label": "القسم", "fieldname": "department", "fieldtype": "Data", "width": 300})
	columns.append({"label": "التخصص", "fieldname": "designation", "fieldtype": "Data", "width": 300})
	columns.append({"label": "االبصمة", "fieldname": "fingerprint_id", "fieldtype": "Data"})

	current_date = from_date
	while current_date <= to_date:

	    m = frappe.utils.formatdate(current_date, "MM") 
	    d = frappe.utils.formatdate(current_date, "dd") 
	    weekday = frappe.utils.get_weekday(frappe.utils.getdate(current_date)) 
    
	    columns.append({
	        "label": f"{d}/{m} {weekday[:2]}",
	        "fieldname": f"{d}/{m}",
	        "fieldtype": "Data"
	    })
	    current_date = frappe.utils.add_days(current_date, 1)
    
	columns.append({
	    "label": f"الحضور",
	    "fieldname": f"presents",
	    "fieldtype": "Data"
	})

	columns.append({
	    "label": f"الغياب",
	    "fieldname": f"absents",
	    "fieldtype": "Data"
	})

	columns.append({
	    "label": f"الاجازات",
	    "fieldname": f"leaves",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"العطل",
	    "fieldname": f"holidays",
	    "fieldtype": "Data"
	})

	emps = []

	for e in employees:
	    presents = 0
	    absents = 0
	    half_day = 0
	    leaves = 0
	    holidays = 0
    
	    employee_map = {}
	    employee_map["employee"] = e.name
	    employee_map["employee_name"] = f"{e.full_name}"
	    employee_map["branch"] = f"{e.branch}"
	    employee_map["department"] = f"{e.department}"
	    employee_map["designation"] = f"{e.designation}"
	    employee_map["fingerprint_id"] = f"{e.fingerprint_id}"
    

	    current_att = from_date
	    while current_att <= to_date:
    
	        current_date = frappe.utils.getdate(current_att)
	        is_holiday = False
        
	        m = frappe.utils.formatdate(current_date, "MM") 
	        d = frappe.utils.formatdate(current_date, "dd")
        
	        statu = None
	        for hd in holidays_data:
	            if hd.holiday_date == current_date:
	                is_holiday = True
	                holidays = holidays + 1
	                break;
    
	        if is_holiday:
	            employee_map[f"{d}/{m}"] = "H"
	            current_att = frappe.utils.add_days(current_att, 1)
	            continue
        
	        att = None
	        for at in raw_data:
	            if at.attendance_date == current_date and at.employee == e.name:
	                att = at
	                break;
        
	        if att:
	            statu = None
	            if att.status == "On Leave":
	                statu = "L"
	                leaves = leaves + 1
                
	            if att.status == "Present":
	                presents = presents + 1
	                statu = "P"
                
	            if att.status == "Absent":
	                statu = "A"
	                absents = absents + 1
                
	            if att.status == "Half Day":
	                statu = "HD"
	                half_day = half_day + 1
	                presents = presents + 0.5
	                absents = absents + 0.5
                
	            if att.status == "Work From Home":
	                statu = "W"
	                presents = presents + 1
                
	            employee_map[f"{d}/{m}"] = statu
	        else:
	            statu = "A"
	            for hd in holidays_data:
	                if hd.holiday_date == current_date:
	                    statu = "H"
	                    break;
            
	            if statu == "A":
	                absents = absents + 1
                
	            if statu == "H":
	                presents = presents + 1
                
	            employee_map[f"{d}/{m}"] = statu
	        current_att = frappe.utils.add_days(current_att, 1)

	    employee_map[f"presents"] = presents
	    employee_map[f"absents"] = absents
	    employee_map[f"half_day"] = half_day
	    employee_map["leaves"] = leaves
	    employee_map["holidays"] = holidays
	    emps.append(employee_map)
	return columns, emps
