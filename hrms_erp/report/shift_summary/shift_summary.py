# -*- coding: utf-8 -*-
import frappe
from frappe import _


def execute(filters=None):
	columns = [
	    {"label": "ID", "fieldname": "ID", "fieldtype": "Data", "width": 120},
	    {"label": "اسم الموظف", "fieldname": "اسم الموظف", "fieldtype": "Data", "width": 200},
	    {"label": "القسم", "fieldname": "القسم", "fieldtype": "Data", "width": 150},
	    {"label": "التخصص", "fieldname": "التخصص", "fieldtype": "Data", "width": 150},
	    {"label": "الفرع", "fieldname": "الفرع", "fieldtype": "Data", "width": 120},
	    {"label": "الشفت الاول", "fieldname": "الشفت الاول", "fieldtype": "Data", "width": 150},
	    {"label": "الفترة الاولى", "fieldname": "الفترة الاولى", "fieldtype": "Data", "width": 200},
	    {"label": "الشفت الثاني", "fieldname": "الشفت الثاني", "fieldtype": "Data", "width": 150},
	    {"label": "الفترة الثانية", "fieldname": "الفترة الثانية", "fieldtype": "Data", "width": 200},
	    {"label": "ايام الدوام", "fieldname": "ايام الدوام", "fieldtype": "Data", "width": 220},
	]

	data = frappe.db.sql("""
	    SELECT
	        employee_id AS 'ID',
	        employee_name AS 'اسم الموظف',
	        department_name AS 'القسم',
	        designation AS 'التخصص',
	        branch AS 'الفرع',
	        shift_type AS 'الشفت الاول',
	        CONCAT(DATE_FORMAT(start_time, "%h:%i %p"),' -> ', DATE_FORMAT(end_time, "%h:%i %p")) as 'الفترة الاولى',
	        shift_type_2 as 'الشفت الثاني',
	        CONCAT(DATE_FORMAT(start_time2, "%h:%i %p"),' -> ', DATE_FORMAT(end_time2, "%h:%i %p")) as 'الفترة الثانية',

	        days AS 'ايام الدوام'
	    FROM (
	        SELECT 
	            inner_results.*,
	            MAX(inner_results.is_default)
	                OVER (PARTITION BY inner_results.employee_id) AS emp_has_default_flag
	        FROM (
	            SELECT
	                e.name AS employee_id,
	                e.employee_name,
	                dep.department_name,
	                e.designation,
	                e.branch,
	                ssa.title AS shift_title,
	                ssa.shift_type,
	                st.start_time,
	                st.end_time,
	                ssa.shift_type_2,
	                st2.start_time AS start_time2,
	                st2.end_time AS end_time2,
	                ssa.is_default,
	                GROUP_CONCAT(
	                    CASE LOWER(dow.day_name)
	                        WHEN 'saturday'  THEN 'السبت'
	                        WHEN 'sunday'    THEN 'الاحد'
	                        WHEN 'monday'    THEN 'الاثنين'
	                        WHEN 'tuesday'   THEN 'الثلاثاء'
	                        WHEN 'wednesday' THEN 'الاربعاء'
	                        WHEN 'thursday'  THEN 'الخميس'
	                        WHEN 'friday'    THEN 'الجمعة'
	                    END
	                    ORDER BY
	                        CASE LOWER(dow.day_name)
	                            WHEN 'saturday'  THEN 1
	                            WHEN 'sunday'    THEN 2
	                            WHEN 'monday'    THEN 3
	                            WHEN 'tuesday'   THEN 4
	                            WHEN 'wednesday' THEN 5
	                            WHEN 'thursday'  THEN 6
	                            WHEN 'friday'    THEN 7
	                        END DESC
	                    SEPARATOR ' ,'
	                ) AS days
	            FROM `tabEmployee` e
	            INNER JOIN `tabSpecial Shift Assignment` ssa
	                ON (
	                    ssa.include_employees = 'Include All'
	                    OR (
	                        ssa.include_employees = 'Include Only'
	                        AND EXISTS (
	                            SELECT 1
	                            FROM `tabSpecial Shift Assignment Employee Table` emps
	                            WHERE emps.employee = e.employee
	                            AND emps.parent = ssa.name
	                        )
	                    )
	                    OR ssa.include_employees = 'Exclude Only'
	                )
	            INNER JOIN `tabDepartment` dep ON dep.name = e.department
	            INNER JOIN `tabShift Type` st ON st.name = ssa.shift_type
	            LEFT JOIN `tabShift Type` st2 ON st2.name = ssa.shift_type_2
	            LEFT JOIN `tabDays of Week Table` dow
	                ON dow.parent = ssa.name
	                AND dow.parenttype = 'Special Shift Assignment'
	                AND dow.parentfield = 'days_of_week'
	            GROUP BY
	                dep.department_name,
	                e.designation,
	                e.branch,
	                e.employee_name,
	                e.name,
	                ssa.title,
	                ssa.include_employees,
	                ssa.shift_type,
	                ssa.is_default,
	                ssa.shift_type_2
	        ) AS inner_results
	    ) AS final_filter
	    WHERE
	        (emp_has_default_flag = 1 AND is_default = 1)
	        OR
	        (emp_has_default_flag = 0)
	""", as_dict=True)
	return columns, data
