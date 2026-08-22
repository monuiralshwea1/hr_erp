# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	from_date = filters.get("from_date")
	to_date = filters.get("to_date")
	employee = filters.get("employee")


	get_raw_data_sql = """
	      SELECT
	    at.employee,
	    at.employee_name,
	    at.attendance_date,
	    at.status,

	    sl.short_leave_in_minutes,
	    sl.short_leave_out_minutes,

	    at.late_enter_time AS OLD,

	    (
	        SELECT COUNT(*)
	        FROM `tabEmployee Checkin` ec
	        WHERE DATE(ec.time) = at.attendance_date
	          AND ec.employee = at.employee
	    ) AS fb_count,

	    SEC_TO_TIME(
	        GREATEST(
	            0,
	            CASE
	                WHEN (TIME_TO_SEC(at.late_enter_time) - IFNULL(sl.short_leave_in_minutes, 0) * 60) > 960
	                THEN (TIME_TO_SEC(at.late_enter_time) - IFNULL(sl.short_leave_in_minutes, 0) * 60)
	                ELSE 0
	            END
	        )
	    ) AS late_enter_time,

	    SEC_TO_TIME(
	        GREATEST(
	            0,
	            TIME_TO_SEC(at.early_exit_time) - IFNULL(sl.short_leave_out_minutes, 0) * 60
	        )
	    ) AS early_exit_time

	FROM `tabAttendance` at

	LEFT JOIN (
	    SELECT
	        short_leave_date,
	        employee,
	        SUM(CASE
	                WHEN log_type = 'IN'
	                THEN short_leave_amount_in_minuts
	                ELSE 0
	            END) AS short_leave_in_minutes,
	        SUM(CASE
	                WHEN log_type = 'OUT'
	                THEN short_leave_amount_in_minuts
	                ELSE 0
	            END) AS short_leave_out_minutes
	    FROM `tabShort Leave`
	    WHERE docstatus = 1
	    GROUP BY
	        short_leave_date,
	        employee
	) sl
	    ON sl.short_leave_date = at.attendance_date
	   AND sl.employee = at.employee

	WHERE
	    at.attendance_date BETWEEN %(from_date)s AND %(to_date)s
	    AND at.docstatus = 1
	    AND (
	        %(employee)s IS NULL
	        OR %(employee)s = ''
	        OR at.employee = %(employee)s
	    )

	ORDER BY
	    at.employee,
	    at.attendance_date;

	"""

	raw_data = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date, "employee":employee}, as_dict=True)
	#frappe.throw(f"{raw_data}")


	get_raw_data_sql = """
	    SELECT
	        sl.employee,sl.employee_name, SUM(sl.short_leave_amount_in_minuts) minutes, sl.log_type
	    FROM
	        `tabShort Leave` sl
	    WHERE
	        sl.short_leave_date BETWEEN %(from_date)s AND %(to_date)s
	        AND sl.docstatus = 1
    
	    GROUP BY sl.employee,sl.employee_name, sl.log_type
	    ORDER BY
	        sl.employee, sl.short_leave_date
	"""

	short_leaves = frappe.db.sql(get_raw_data_sql, values={"from_date":from_date, "to_date":to_date}, as_dict=True)

	get_raw_data_sql = """
	    SELECT DISTINCT *, concat(first_name,' ', IFNULL(middle_name, ''),' ', IFNULL(last_name, '')) as full_name
	    FROM
	        `tabEmployee`
	    Where status = 'Active'
	        AND employee = CASE 
	            WHEN %(employee)s IS NULL OR %(employee)s = '' THEN employee
	            ELSE %(employee)s
	        END
        
	    ORDER BY CAST(fingerprint_id AS INT)
	"""

	employees = frappe.db.sql(get_raw_data_sql, values={"employee":employee} , as_dict=True)

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


	columns = []
	columns.append({"label": "#", "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 150})
	columns.append({"label": "أسم الموظف", "fieldname": "employee_name", "fieldtype": "Data", "width": 300})
	columns.append({"label": "الفرع", "fieldname": "branch", "fieldtype": "Data", "width": 300})
	columns.append({"label": "القسم", "fieldname": "department", "fieldtype": "Data", "width": 300})
	columns.append({"label": "التخصص", "fieldname": "designation", "fieldtype": "Data", "width": 300})
	columns.append({"label": "االبصمة", "fieldname": "fingerprint_id", "fieldtype": "Data"})
	columns.append({"label": "مدير؟", "fieldname": "is_manager", "fieldtype": "Data"})
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
	columns.append({
	    "label": f"اذونات الدخول (بالدقيقة)",
	    "fieldname": f"in_short_leaves",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"اذونات الخروج (بالدقيقة)",
	    "fieldname": f"out_short_leaves",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"التأخير (بالدقيقة) بعد الاذن",
	    "fieldname": f"lates",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"ايام التأخير",
	    "fieldname": f"lates_day",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"ايام نسيان البصمة",
	    "fieldname": f"half_day",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"الخروج المبكر (بالدقيقة)",
	    "fieldname": f"early_exit",
	    "fieldtype": "Data"
	})
	columns.append({
	    "label": f"ايام الخروج المبكر",
	    "fieldname": f"early_exit_day",
	    "fieldtype": "Data"
	})
	emps = []
	for e in employees:
	    presents = 0
	    absents = 0
	    lates = 0
	    lates_day = 0
	    half_day = 0
	    early_exit_day = 0
	    early_exit = 0
	    leaves = 0
	    holidays = 0
    
	    employee_map = {}
	    employee_map["employee"] = e.name
	    employee_map["employee_name"] = f"{e.full_name}"
	    employee_map["branch"] = f"{e.branch}"
	    employee_map["department"] = f"{e.department}"
	    employee_map["designation"] = f"{e.designation}"
	    employee_map["fingerprint_id"] = f"{e.fingerprint_id}"
	    employee_map["is_manager"] = f"{e.is_manager}"
    
	    emp_in_short_leaves = 0
	    emp_out_short_leaves = 0
    
	    for sl in short_leaves:
	        if sl["employee"] == e.name:
	            if sl["log_type"] == "IN":
	                emp_in_short_leaves = sl["minutes"]
	            if sl["log_type"] == "OUT":
	                emp_out_short_leaves = sl["minutes"]
                
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
                
	            if att.status == "Present" and att.fb_count > 1:
	                presents = presents + 1
                
	                current_late = frappe.utils.get_time(att.late_enter_time)
	                current_late_minutes = (current_late.hour * 60) + current_late.minute
                    
	                current_early_exit = frappe.utils.get_time(att.early_exit_time)
	                current_early_ext_minutes = (current_early_exit.hour * 60) + current_early_exit.minute
                
                
	                in_late_text = ""
	                out_late_text = ""
                
	                if current_late_minutes > 3:
	                    lates = lates +  current_late_minutes
	                    lates_day = lates_day + 1
	                    in_late_text = f" in({current_late_minutes}m)"
                
	                if current_early_ext_minutes > 2:
	                    early_exit = early_exit + current_early_ext_minutes
	                    early_exit_day = early_exit_day + 1
	                    out_late_text = f" out({current_early_ext_minutes}m)"
                    
	                statu = f"P" + in_late_text + out_late_text
                
	            if att.status == "Absent":
	                statu = "A"
	                absents = absents + 1
                
	            if att.status == "Half Day" or att.fb_count == 1:
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
	    employee_map[f"lates"] = lates
	    employee_map[f"in_short_leaves"] = emp_in_short_leaves
	    employee_map[f"lates_day"] = lates_day
	    employee_map[f"half_day"] = half_day
	    employee_map[f"early_exit_day"] = early_exit_day
	    employee_map[f"early_exit"] = early_exit
	    employee_map[f"out_short_leaves"] = emp_out_short_leaves
	    employee_map["leaves"] = leaves
	    employee_map["holidays"] = holidays
	    emps.append(employee_map)
	return columns, emps
