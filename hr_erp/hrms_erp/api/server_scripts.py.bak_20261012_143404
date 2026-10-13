# -*- coding: utf-8 -*-
"""Server scripts converted from alshumul production system."""

import frappe
import json

# Event: Auto Shift Assign Calculate V3 -> Auto Shift Assign.After Submit
def auto_shift_assign_calculate_v3(doc, method=None):

	from_date = doc.from_date
	to_date = doc.to_date
	employees = []

	if len(doc.employees) > 0:
	    for e in doc.employees:
	       employees.append({"employee": e.employee}) 
	else:
	    checkin_emps = frappe.get_all(
	        "Employee Checkin",
	        fields=["employee"],  # The Link field to the Employee doctype
	        filters=[
	            ["time", ">=", f"{from_date} 00:00:00"],  # Start of from_date
	            ["time", "<=", f"{to_date} 23:59:59"]     # End of to_date
	         ],
	        distinct=True
	    )
	    for e in checkin_emps:
	        employees.append({"employee": e.employee}) 

	all_employees = frappe.get_all(
	    "Employee",
	    fields=["name", "employee_name", "company", "use_default_shift","default_shift"],
	    filters=[
	        ["status", "=", "Active"],
	    ],
	    limit=0
	)

	from_date_filter = frappe.utils.add_days(from_date, 0)

	to_date_filter = frappe.utils.add_days(to_date, 1)

	query = f"""
	    SELECT distinct *
	    FROM `tabEmployee Checkin`
	    WHERE DATE(time) BETWEEN DATE('{from_date_filter}') AND DATE('{to_date_filter}')
	    ORDER BY
	        time ASC
	"""

	checks = frappe.db.sql(query, as_dict=True)


	query = f"""
	    select 
	    emp_ss.employee,
	    emp_ss.employee_name,
	    ssa.name,
	    ssa.is_default,
	    ssa.shift_type,
	    ssa.shift_type_2,
	    ssa.include_employees,
	    dow.day_name,
	    ssa.from_date,
	    ssa.to_date,
	    ssa.priority
    
	    from `tabSpecial Shift Assignment` ssa
	    left join `tabSpecial Shift Assignment Employee Table` emp_ss on emp_ss.parent = ssa.name
	    left join `tabDays of Week Table` dow on dow.parent = ssa.name
	    where DATE('{to_date_filter}') >= from_date and DATE('{from_date_filter}') <= to_date and ssa.is_active = 1
	    order by ssa.priority
	"""

	ssa = frappe.db.sql(query, as_dict=True)
	query = f"""
	    select distinct st.*
	    from `tabSpecial Shift Assignment` ssa
	    left join `tabShift Type` st on st.name = ssa.shift_type or st.name = ssa.shift_type_2
	    where DATE('{to_date_filter}') >= from_date and DATE('{from_date_filter}') <= to_date and ssa.is_active = 1
	"""

	shifts  = frappe.db.sql(query, as_dict=True)

	#Fetch All shifts for current employee
	def get_emp_shifts(emp, ssa,day,current_date):
	    candidate_shifts = []
	    emd_excluded = False
	    emp_name = emp["employee"]
    
	    shifts_for_day = []
	    for sa in ssa:
	        if sa.day_name == day:
	            shifts_for_day.append(sa)
            
	    excluded_shifts = []
    
	    included_shifts = {sa.name for sa in shifts_for_day
	                       if sa.day_name == day and sa.include_employees == "Include Only" and sa.employee == emp_name}
      
	    # Step 2: mark shifts as excluded if not included or explicitly excluded
	    # for sa in shifts_for_day:
	    #     # If the shift is not in included_shifts, check if it should be excluded
	    #     if sa.name not in included_shifts:
	    #         # Exclude if explicitly excluded
	    #         found = False
	    #         if sa.include_employees == "Exclude Only" and sa.employee == emp_name:
	    #             found = True
	    #         # Exclude if "Include Only" and employee is not listed
	    #         elif sa.include_employees == "Include Only" and sa.employee != emp_name:
	    #             found = True
                
	    #         if found and sa.name not in excluded_shifts:
	    #             excluded_shifts.append(sa.name)
    
	    shifts_for_day_grouped = list(set([shift.name for shift in shifts_for_day]))
	    for sa in shifts_for_day:
	        for sg in shifts_for_day_grouped:
	            if sa.name == sg and sg not in included_shifts and sg not in excluded_shifts:
	                if sa.include_employees == "Exclude Only" and sa.employee == emp_name:
	                    if sa.name not in excluded_shifts:
	                        excluded_shifts.append(sa.name)
	                        break
    
	    for sg_name in shifts_for_day_grouped:
	        # Skip if we already decided to include or exclude this shift name
	        if sg_name in included_shifts or sg_name in excluded_shifts:
	            continue
    
	        is_excluded = False
        
	        # Check all entries for this specific shift name
	        for sa in shifts_for_day:
	            if sa.name == sg_name:
	                # 1. If this employee is explicitly EXCLUDED, stop and mark as excluded
	                if sa.include_employees == "Exclude Only" and sa.employee == emp_name:
	                    is_excluded = True
	                    break
                
	                # 2. If it's an "Include Only" shift and it's NOT for this employee
	                if sa.include_employees == "Include Only" and sa.employee != emp_name:
	                    is_excluded = True
	                    # Don't break yet, because another entry might say "Include Only" for this employee
        
	        # Final check: If we found a reason to exclude it, add to list
	        if is_excluded:
	            excluded_shifts.append(sg_name)
                    
	    # for sa in shifts_for_day:
	    #     include_found = False
	    #     for sg in shifts_for_day_grouped:
	    #         if sa.name == sg and sg not in included_shifts and sg not in excluded_shifts:
	    #             if (sa.include_employees == "Include Only" and sa.employee == emp_name):
	    #                 break
                
	    #     if not include_found:
	    #         if sa.name not in excluded_shifts:
	    #             excluded_shifts.append(sa.name)
                         
    
	    # valid_from_groups = [shifts_for_day_grouped not in excluded_shifts]
    
	    # 2. Combine with included_shifts and use set() to ensure no duplicates
	    # candidate_shifts = list(set([*included_shifts, *valid_from_groups]))    
	    # shift_names = list(set([shift.name for shift in all_available_shifts]))
    
	    for sn in shifts_for_day_grouped:
	        if sn in excluded_shifts:
	            continue
        
	        if sn not in candidate_shifts:
	            candidate_shifts.append(sn)
        
	        # if sa.include_employees == "Include Only" and emp_name == sa.employee:
	        #     candidate_shifts.append(sa.name)
	        # elif sa.include_employees == "Include All":
	        #     candidate_shifts.append(sa.name)
	        #     frappe.throw(f"{sa.name}")
    
    
	    # remaining_shifts = []
	    # for sa in shifts_for_day:
	    #     if sa.name in excluded_shifts or sa.name in candidate_shifts:
	    #         continue
        
	    #     if sa.name not in remaining_shifts:
	    #         remaining_shifts.append(sa.name)

	    # candidate_shifts.extend(remaining_shifts)
    
	    final_shifts = []
	    default_shifts = []
    
	    for cs in candidate_shifts:
	        for sa in shifts_for_day:
	            if sa.name == cs:
	                is_in_range = frappe.utils.getdate(sa.from_date) <= frappe.utils.getdate(current_date) <= frappe.utils.getdate(sa.to_date)

	                if is_in_range:
	                    if sa.is_default:
	                        default_shifts.append(sa)
	                    else:
	                        final_shifts.append(sa)

                        
	                break
    
	    if len(default_shifts) > 0:
	        final_shifts = []
	        final_shifts.extend(default_shifts)
    
	    final_default_shifts = []
                   
	    # frappe.throw(f"XXX {current_date} --- {final_shifts}")
        
        
	    if len(final_shifts) > 0:
	        for p in range(5, 0, -1):
	            found = False
	            priority_shifts = [fs for fs in final_shifts if int(fs.priority) == p]
            
	            if len(priority_shifts) == 0:
	                continue
            
	            final_default_shifts = []   

	            for fs in priority_shifts:
	                if fs.is_default:
	                    found = True
	                    if fs not in final_default_shifts:
	                        final_default_shifts.append(fs)
            
	            if found == False:
	                for fs in priority_shifts:
	                    if fs not in final_default_shifts:
	                        final_default_shifts.append(fs)

	    # if len(default_shifts) > 0:
	    #     final_shifts = default_shifts;
	    # frappe.throw(f"{final_default_shifts}")
    

    
	    return final_default_shifts

	selected_shifts = []
    
	def get_date_checks(checks, date, is_next_date=False):
	    current_date_checks = []
	    dates = []
	    dates.append(frappe.utils.getdate(date))
	    if is_next_date:
	        dates.append(frappe.utils.add_days(frappe.utils.getdate(date), 1))
	    for log in checks:
	        if log.time.date() in dates:
	            current_date_checks.append(log)
    
	    return current_date_checks


	def process_shift(sh, current_date_checks, e, current_date, find_only_end = False):
    
	    start_checkin_seconds = sh.begin_check_in_before_shift_start_time * 60
	    end_checkin_seconds = sh.end_check_in_after_shift_start_time * 60
	    # end_checkin_seconds = ((sh.end_time.total_seconds() - sh.start_time.total_seconds()))-60
	    # frappe.throw(f"{end_checkin_seconds}")
	    begin_checkout_seconds = sh.begin_check_out_before_shift_end * 60
	    last_checkout_seconds = sh.end_check_out_after_shift_end * 60
    
	    start_time_seconds = sh.start_time.total_seconds()
	    end_time_seconds = sh.end_time.total_seconds()

	    start_range_seconds = sh.start_time.total_seconds() - start_checkin_seconds
	    end_range_seconds = sh.end_time.total_seconds() + last_checkout_seconds
    
	    shift_checks = []
	    for log in current_date_checks:
	        if log in shift_checks:
	            continue
        
	        check_time = frappe.utils.get_time(log.time)
	        check_date = frappe.utils.getdate(log.time)
	        check_time_seconds = (check_time.hour * 3600) + (check_time.minute * 60) + check_time.second
        
	        if sh.end_next_day:
	            next_date = frappe.utils.getdate(frappe.utils.add_days(current_date, 1))
	            current_date_date = frappe.utils.getdate(current_date)
	            end_day_seconds = frappe.utils.get_timedelta("23:59:59").total_seconds()
            
	            if check_time_seconds >= start_range_seconds and check_time_seconds <= end_day_seconds and check_date == current_date_date:
	                shift_checks.append(log)
                
	            if check_time_seconds >= 0 and check_date == next_date and check_time_seconds <= end_range_seconds:
	                if log not in shift_checks:
	                    shift_checks.append(log)
	        else:
	            if check_time_seconds >= start_range_seconds and check_time_seconds <= end_range_seconds:
	                shift_checks.append(log)
        
	    if shift_checks is None or len(shift_checks) == 0:
	        return None
    
	    shift_checks.sort(key=lambda x: x.time)
	    current_check = shift_checks[0]
	    current_check_time = frappe.utils.get_time(current_check.time)
	    current_check_time_seconds = (current_check_time.hour * 3600) + (current_check_time.minute * 60) + current_check_time.second
	    if find_only_end:
	        if current_check_time_seconds >= (end_time_seconds - begin_checkout_seconds) and current_check_time_seconds <= (end_time_seconds + last_checkout_seconds):
	            selected_shift = {
	                "shift_type": sh.name,
	                "check_in": current_check,
	                "check_out": None,
	                "is_end" :  False,
	                "checks_count": len(shift_checks)
	            }
	            return selected_shift
	    elif current_check_time_seconds >= start_range_seconds and current_check_time_seconds <= (start_time_seconds + end_checkin_seconds):
	        selected_shift = {
	            "shift_type": sh.name,
	            "check_in": current_check,
	            "check_out": None,
	            "is_end" :  False,
	            "checks_count": len(shift_checks)
	        }
        
	        if len(shift_checks) <= 1:
	            return selected_shift
            
	        current_check_out = shift_checks[-1]
        
	        current_check_time = frappe.utils.get_time(current_check_out.time)
	        current_check_time_seconds = (current_check_time.hour * 3600) + (current_check_time.minute * 60) + current_check_time.second
        
	        if current_check_time_seconds >= (end_time_seconds - begin_checkout_seconds) and current_check_time_seconds <= (end_time_seconds + last_checkout_seconds):
	        # if current_check_time_seconds >= (end_time_seconds - begin_checkout_seconds) and current_check_time_seconds <= (end_time_seconds + last_checkout_seconds):
	            selected_shift = {
	                "shift_type": sh.name,
	                "check_in": current_check,
	                "check_out": current_check_out,
	                "is_end" :  True,
	                "checks_count": len(shift_checks)
	            }
	            return selected_shift
        
	        return selected_shift
    
    
    
	    return None


	def get_nearest_shift(found_shifts, current_date_checks, e, current_date):
	    near_shift = None
	    min_time_difference = None
	    xx = []
	    for fs in found_shifts:
	        sh = fs["sh"]
	        es = fs["es"]
        
	        t = sh["check_in"].time
	        dt_check_in = frappe.utils.get_datetime(t)
	        dt_check_in = (dt_check_in - dt_check_in.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()

	        dt_shift_start = frappe.utils.get_datetime(es.start_time).total_seconds()
	        time_diff = abs(dt_check_in - dt_shift_start)
	        x = {
	            "dt_check_in": dt_check_in,
	            "dt_shift_start": dt_shift_start,
	            "diff": time_diff,
	            "type": es.name
	        }
	        xx.append(x)
	        # if time_diff < 0:
	        #     time_diff = -time_diff  # محاكاة لدالة abs() بدون import لضمان القيمة الموجبة
        
	        # المقارنة لتحديد الشفت الأقرب
	        if min_time_difference is None:
	            min_time_difference = time_diff
	            near_shift = sh
            
	        elif time_diff < min_time_difference:
	            min_time_difference = time_diff
	            near_shift = sh
            
	    # frappe.throw(f"{xx}")        
	    return near_shift
    
	for e in employees:
    
	    last_shift_type = None
	    emp_shifts = None
	    current_date = frappe.utils.add_days(from_date, 0)
	    emp_selected_shifts = []
    
	    emp_checks = []
    
	    for log in checks:
	        if log.employee == e["employee"]:
	            emp_checks.append(log)
    
	    if emp_checks is None or len(emp_checks) == 0:
	        continue
    
	    while current_date <= to_date:

	        shifts_found = []
	        week_day = frappe.utils.get_weekday(frappe.utils.getdate(current_date))
        
	        emp_shifts = get_emp_shifts(e, ssa, week_day, current_date)
        
	        current_date_checks = get_date_checks(emp_checks, current_date)
        
	        selected_shift = None
        
	        emp_exists_shifts = []
	        for es in emp_shifts:
	            found_shift = {}

	            for shift in shifts:
	                if shift.name == es.shift_type:
	                    found_shift["shift1"] = shift
	                    found_shift["shift2"] = None
	                    break

	            for shift in shifts:
	                if shift.name == es.shift_type_2:
	                    found_shift["shift2"] = shift
	                    break
            
	            if found_shift is not None:
	                emp_exists_shifts.append(found_shift)
        

	        max_checks_count = 0
	        max_checks_count_2 = 0         
	        found_shifts1 = []
	        found_shifts2 = []
	        correct_shift_found = False
	        selected_shift = {
	                "shift_type": None,
	                "shift_type_2": None,
	                "is_mulitple_shifts": False,
	                "employee": e["employee"],
	                "date": current_date
	            }
	        for es in emp_exists_shifts:
	            shift1 = es["shift1"]
	            shift2 = es["shift2"]
	            # selected_shift["is_mulitple_shifts"] = shift1 is not None and shift2 is not None
            
	            if shift1 is not None:
	                if shift1.end_next_day:
	                    current_date_checks = get_date_checks(emp_checks, current_date, True)
                    
	                sh = process_shift(shift1, current_date_checks, e, current_date)
                
	                if sh is not None:
	                    checks_count = sh["checks_count"]
                    
	                    max_checks_count = int(checks_count)
	                    correct_shift_found = sh["is_end"]
                    
	                    st = sh["shift_type"]
	                    # selected_shift["shift_type"] = st
	                    found_shifts1.append({
	                        "sh": sh,
	                        "es": shift1,
	                        "count": max_checks_count
	                    })

	            if shift2 is not None:

	                sh = process_shift(shift2, current_date_checks, e, current_date)
                
	                if sh is not None:
                    
	                    st = sh["shift_type"]
	                    # selected_shift["shift_type_2"] = st
	                    correct_shift_found = sh["is_end"]
	                    max_checks_count_2 = int(checks_count)
	                    found_shifts2.append({
	                            "sh": sh,
	                            "es": shift2,
	                            "count": sh["checks_count"]
	                        })
                        
	            # if correct_shift_found:
	            #     break
            
	        # frappe.throw(f"{emp_exists_shifts}")
	        # frappe.throw(f"found_shifts1: {found_shifts1}")
	        if found_shifts1:
	            highest_record = [x for x in found_shifts1 if x.get("sh", {}).get("is_end") is True]
	            if len(highest_record) == 0:
	                max_item = max(found_shifts1, key=lambda x: x.get("count", 0))
	                highest_record = [max_item]
            
	            found_shifts1 = highest_record
            
	        if found_shifts2:
	            highest_record = [x for x in found_shifts2 if x.get("sh", {}).get("is_end") is True]
	            if len(highest_record) == 0:
	                max_item = max(found_shifts2, key=lambda x: x.get("count", 0))
	                highest_record = [max_item]
            
	            found_shifts2 = highest_record
            
         
	        near_shift1_type = None
	        near_shift2_type = None
        
	        if found_shifts1:
	            near_shift1 = get_nearest_shift(found_shifts1, current_date_checks, e, current_date)
	            near_shift1_type = near_shift1["shift_type"]

	        if found_shifts2:
	            near_shift2 = get_nearest_shift(found_shifts2, current_date_checks, e, current_date)
	            # frappe.throw(f"XXXXXX {near_shift2} ---- {found_shifts2}")
	            near_shift2_type = near_shift2["shift_type"]
        
	        selected_shift["shift_type"] = near_shift1_type
	        selected_shift["shift_type_2"] = near_shift2_type
	        selected_shift["is_mulitple_shifts"] = near_shift1_type is not None and near_shift2_type is not None
        
	        if selected_shift["shift_type"] is not None or selected_shift["shift_type_2"] is not None:
	            emp_selected_shifts.append(selected_shift)   
            
	        # frappe.throw(f"emp_selected_shifts: {emp_selected_shifts}") 
        
	        current_date = frappe.utils.add_days(current_date, 1)
        
	    if emp_selected_shifts is None or len(emp_selected_shifts) == 0:
	        continue
    
	    #Simplfy shifts
	    selected_shift = emp_selected_shifts[0]
	    start_date = selected_shift["date"]
	    end_date = start_date
	    current_shift_type = selected_shift["shift_type"]
	    current_shift_type_2 = selected_shift["shift_type_2"]
	    is_mulitple_shifts = selected_shift["is_mulitple_shifts"]
    
	    for emp_shift in emp_selected_shifts:
        
	        emp_shift_type = emp_shift["shift_type"]
	        emp_shift_type_2 = emp_shift["shift_type_2"]
	        emp_is_mulitple_shifts = emp_shift["is_mulitple_shifts"]
        
	        shift_date = emp_shift["date"]
        
	        if emp_shift_type == current_shift_type and emp_shift_type_2 == current_shift_type_2 and emp_is_mulitple_shifts == is_mulitple_shifts:
	            end_date = shift_date
	        else: 
	            selected_shifts.append({"shift_type": current_shift_type,"shift_type_2": current_shift_type_2, "employee": e["employee"], "start_date": start_date, "end_date": end_date, "is_mulitple_shifts": is_mulitple_shifts,})
	            start_date = shift_date
	            end_date = shift_date
	            current_shift_type = emp_shift_type
	            current_shift_type_2 = emp_shift_type_2
	            is_mulitple_shifts = emp_is_mulitple_shifts
            
	    selected_shifts.append({
	        "shift_type": current_shift_type,
	        "shift_type_2": current_shift_type_2,
	        "employee": e["employee"],
	        "is_mulitple_shifts": is_mulitple_shifts,
	        "start_date": start_date,
	        "end_date": end_date
	    })

	# frappe.throw(f"END {selected_shifts}")
	for s in selected_shifts:
    
	    if s["shift_type"] is None and s["shift_type_2"] is not None:
	        s["shift_type"] = s["shift_type_2"]
	        s["shift_type_2"] = None
    
	    new_record = frappe.get_doc({
	                "doctype": "Shift Assignment",
	                "employee": s["employee"],
	                "shift_type": s["shift_type"],
	                "shift_type_2": s["shift_type_2"],
	                "start_date": s["start_date"],
	                "is_mulitple_shifts": s["is_mulitple_shifts"],
	                "end_date": s["end_date"],
	                "auto_shift_assign": doc.name,
	            })
    
	    new_record.insert()  # First insert the document
	    new_record.submit()  # Then submit it


# Event: Auto Attendance Calculate V2 -> Auto Attendance.Before Save
def auto_attendance_calculate_v2(doc, method=None):

	if not doc.calculated:
	    from_date = doc.from_date
	    to_date = doc.to_date
      
	    attendances = frappe.get_all(
	        "Attendance",
	        filters=[
	            ["auto_atten_id", "=", doc.amended_from],
	        ],
	        limit=0
	    )
    
	    for att in attendances:
	        attendance = frappe.get_doc("Attendance", att.name)
	        attendance.delete()
    
	    emps = []
    
	    if doc.all_employees:
	        all_emps = frappe.get_all(
	            "Employee",
	             fields="*",
	             filters=[["status","=","Active"]],
	             limit=0,
	        )
	        for e in all_emps:
	            emps.append({"name": e.employee, "default_shift": e.default_shift, "company": e.company})
	    else:
	        for e in doc.employees:
	            emps.append({"name": e.employee, "default_shift": e.default_shift, "company": e.company})
    
	    from_date_filter = frappe.utils.add_days(from_date, 0)
    
	    to_date_filter = frappe.utils.add_days(to_date, 1)
    
    
	    query = f"""
	        SELECT distinct *
	        FROM `tabEmployee Checkin`
	        WHERE DATE(time) BETWEEN DATE('{from_date_filter}') AND DATE('{to_date_filter}')
	        ORDER BY
	            time ASC
	    """
    
	    checks = frappe.db.sql(query, as_dict=True)
    
	    shift_assignment = frappe.get_all(
	                    "Shift Assignment",
	                    fields="*",
	                    filters=[
	                        ["start_date", ">=", from_date],
	                        ["end_date", "<=", to_date],
	                        ["docstatus", "=", 1],
	                    ],
	                    order_by= "start_date desc",
	                    limit=0
	                )
                
	    shifts_type = frappe.get_all(
	                    "Shift Type",
	                    fields="*",
	                    limit=0
	                )
                
	    manual_attendance = frappe.get_all(
	                "Attendance",
	                fields="*",
	                filters=[
	                    ["docstatus","=",1],
                    
	                    ["attendance_date",">=",from_date],
	                    ["attendance_date","<=",to_date]
	                ],
	                limit=0,
	        )
        
	    def get_shift_type(shifts_type, shift_name):
	        for shift in shifts_type:
	            if shift.name == shift_name:
	                return shift
	        return None
    
	    # def seconds_to_hhmm(seconds):
	    #     hours = seconds // 3600
	    #     remaining_seconds = seconds % 3600
	    #     minutes = remaining_seconds // 60
	    #     seconds_final = remaining_seconds % 60
        
	        # return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds_final):02d}"
	    def seconds_to_hhmm(seconds):
        
	        if seconds == 0:
	            return "00:00:00"
	        hours = int(seconds // 3600)          
        
	        remaining_seconds = seconds % 3600    
	        minutes = int((remaining_seconds + 29) // 60)  
        
	        if minutes >= 60:
	            additional_hours = minutes // 60
	            hours = hours + additional_hours
	            minutes = minutes % 60
        
	        if hours >= 24:
	            hours = hours % 24
        
	        return f"{hours:02d}:{minutes:02d}:00"
        
	    def get_date_checks(checks, date, is_next_day=False):
	        current_date_checks = []
	        dates = []
	        dates.append(frappe.utils.getdate(date))
        
	        if is_next_day:
	            dates.append(frappe.utils.getdate(frappe.utils.add_days(date,1)))
        
	        for log in checks:
	            if log.time.date() in dates:
	                current_date_checks.append(log)
                
	        return current_date_checks
    
	    def get_shift_checks(current_date_checks, shift, current_date):
	        start_range_seconds = shift.start_time.total_seconds() - (shift.begin_check_in_before_shift_start_time * 60)
	        end_range_seconds = shift.end_time.total_seconds() + (shift.end_check_out_after_shift_end * 60)
	        shift_checks = []

	        for log in current_date_checks:
	            if log in shift_checks:
	                continue
            
	            check_time = frappe.utils.get_time(log.time)
	            check_date = frappe.utils.getdate(log.time)
	            check_time_seconds = (check_time.hour * 3600) + (check_time.minute * 60) + check_time.second
            
	            if shift.end_next_day:
	                next_date = frappe.utils.getdate(frappe.utils.add_days(current_date, 1))
	                current_date_date = frappe.utils.getdate(current_date)
	                end_day_seconds = frappe.utils.get_timedelta("24:00:00").total_seconds()
                
	                if check_time_seconds >= start_range_seconds and check_time_seconds <= end_day_seconds and check_date == current_date_date:
	                    shift_checks.append(log)
                    
	                if check_time_seconds >= 0 and check_date == next_date and check_time_seconds <= end_range_seconds:
	                    if log not in shift_checks:
	                        shift_checks.append(log)
	            else:
	                if check_time_seconds >= start_range_seconds and check_time_seconds <= end_range_seconds:
	                    shift_checks.append(log)
            
	        shift_checks.sort(key=lambda x: x.time)
	        return shift_checks
    
	    def get_shift_duration(shift_type):
        
	        start_time_seconds = frappe.utils.get_timedelta(shift_type.start_time).total_seconds()
	        end_time_seconds = frappe.utils.get_timedelta(shift_type.end_time).total_seconds()
        
	        if shift_type.end_next_day:
	            end_day_time = frappe.utils.get_timedelta("24:00:00").total_seconds()
	            total_shift_seconds = (end_day_time - start_time_seconds) + end_time_seconds
	        else:
	            total_shift_seconds = (end_time_seconds - start_time_seconds)
        
	        return total_shift_seconds
        
	    def calculate_shift_status(emp_id, current_date, shift_type, checkin, checkout):
        
        
	        def get_punch_seconds(timestamp, base_date):
	            if not timestamp:
	                return 0
            
	            tm = frappe.utils.get_time(timestamp)
	            seconds = (tm.hour * 3600) + (tm.minute * 60) + tm.second
            
	            days_diff = frappe.utils.date_diff(frappe.utils.getdate(timestamp), frappe.utils.getdate(base_date))
	            return seconds + (days_diff * 86400)
        
        
	        start_time_seconds = frappe.utils.get_timedelta(shift_type.start_time).total_seconds()
	        end_time_seconds = frappe.utils.get_timedelta(shift_type.end_time).total_seconds()
        
        
	        if shift_type.end_next_day:
	            end_time_seconds = end_time_seconds + 86400
            
	        total_shift_seconds = end_time_seconds - start_time_seconds
            
        
	        first_in_seconds = get_punch_seconds(checkin.time, current_date)
	        last_out_seconds = get_punch_seconds(checkout.time, current_date)
        
	        if last_out_seconds <= start_time_seconds:
	            last_out_seconds = 0
    
        
	        allow_check_in_seconds = (shift_type.allow_check_in or 0) * 60
        
	        if first_in_seconds <= start_time_seconds + allow_check_in_seconds:
	            first_in_seconds = start_time_seconds

	        late_enter = 0
	        if first_in_seconds > start_time_seconds:
	            late_enter = first_in_seconds - start_time_seconds
	            # if late_enter <= allow_check_in_seconds:
	            #     late_enter = 0
            
        
	        extra_time = 0
	        early_exit_time = 0
        
	        if last_out_seconds != 0:
	            if last_out_seconds < end_time_seconds:
	                early_exit_time = end_time_seconds - last_out_seconds
	            elif last_out_seconds > end_time_seconds:
	                extra_time = last_out_seconds - end_time_seconds
	        else:
	            extra_time = 0
	            early_exit_time = 0
	            late_enter = total_shift_seconds / 2
    
	        # effective_in = max(first_in_seconds, start_time_seconds)
	        # effective_out = min(last_out_seconds, end_time_seconds) if last_out_seconds > 0 else effective_in
        
	        total_time = last_out_seconds - first_in_seconds
            
	        if total_time <= 0:
	            total_time = 0
    
	        results = {
	            "total_time": total_time,
	            "status": "Present" if total_time > 0 else "Absent",
	            "late_enter": late_enter,
	            "early_exit_time": early_exit_time,
	            "extra_time": extra_time
	        }
        
	        # if current_date == "2026-02-28" and emp_id == "HR-EMP-00089":
	        #     frappe.throw(f"h {last_out_seconds} < {end_time_seconds}")

            
	        return results
        
    
	    calculated_attendaces = []
    
	    for e in emps:
        
	        emp_id = e["name"]
	        emp_checks = []
        
	        for log in checks:
	            if log.employee == emp_id:
	                emp_checks.append(log)
        
	        if emp_checks is None or len(emp_checks) == 0:
	            continue
        
	        emp_calculated_att = []
    
	        current_date = doc.from_date
        
	        while current_date <= doc.to_date:

	            is_manual = False
	            if doc.ignore_exiting_attendance:
	                for manual in manual_attendance:
	                    if manual.employee == emp_id and str(manual.attendance_date) == str(current_date):
	                        is_manual = True
	                        break
    
	            if is_manual:
	                current_date = frappe.utils.add_days(current_date, 1)
	                continue
            
	            current_date_checks = get_date_checks(emp_checks, current_date)

	            if current_date_checks is None or len(current_date_checks) == 0:
	                current_date = frappe.utils.add_days(current_date, 1)
	                continue
            
	            emp_shift_assign = None
	            for sa in shift_assignment:
	                if sa.employee == emp_id and frappe.utils.getdate(current_date) >= sa.start_date and frappe.utils.getdate(current_date) <= sa.end_date:
	                    emp_shift_assign = sa
	                    break
                
	            if emp_shift_assign is None:
	                current_date = frappe.utils.add_days(current_date, 1)
	                continue
            
	            is_mulitple_shifts = emp_shift_assign.is_mulitple_shifts
            
	            emp_shifts = []
	            shift_type_1 = get_shift_type(shifts_type, emp_shift_assign.shift_type)
	            emp_shifts.append(shift_type_1)
                
	            shift_type_2 = get_shift_type(shifts_type, emp_shift_assign.shift_type_2)
	            if shift_type_2 is not None:
	                emp_shifts.append(shift_type_2)
                
	            emp_shifts.reverse()
            
	            emp_calculated_shifts = []
            
	            for current_shift in emp_shifts:
                
	                if current_shift.end_next_day:
	                    current_date_checks = get_date_checks(emp_checks, current_date, True)

	                shift_checks = get_shift_checks(current_date_checks, current_shift, current_date) 
                    
	                shift_duration = get_shift_duration(current_shift)
                
                
                
	                if shift_checks is None or len(shift_checks) == 0:
                    
	                    att_record = {
	                        "employee": e["name"],
	                        "late_enter": shift_duration,
	                        "early_exit_time": 0,
	                        "extra_time": 0,
	                        "total_time": 0,
	                        "attendance_date": current_date,
	                        "status": "Present",
	                        "shift": current_shift.name,
	                        "auto_atten_id": doc.name,
	                        "company": e["company"],
	                    }   
                    
	                    emp_calculated_shifts.append(att_record)
	                    continue

	                att_record = None
	                if len(shift_checks) == 1:
                    
	                    att_record = {
	                        "employee": e["name"],
	                        "late_enter": shift_duration/2,
	                        "early_exit_time": 0,
	                        "extra_time": 0,
	                        "total_time": shift_duration/2,
	                        "attendance_date": current_date,
	                        "status": "Present",
	                        "shift": current_shift.name,
	                        "auto_atten_id": doc.name,
	                        "company": e["company"],
	                    }
                    
                        
	                    emp_calculated_shifts.append(att_record)
                    
	                    continue
    
	                checkin = shift_checks[0]
	                checkout = shift_checks[-1]
                
                        
                
	                shift_data = calculate_shift_status(emp_id, current_date, current_shift, checkin, checkout)
                
	                late_enter = shift_data["late_enter"]
	                early_exit_time = shift_data["early_exit_time"]
	                extra_time = shift_data["extra_time"]
	                total_time = shift_data["total_time"]
	                status = shift_data["status"]
	                att_record = {
	                    "employee": e["name"],
	                    "late_enter": late_enter,
	                    "early_exit_time": early_exit_time,
	                    "extra_time": extra_time,
	                    "total_time": total_time,
	                    "attendance_date": current_date,
	                    "status": status,
	                    "shift": current_shift.name,
	                    "auto_atten_id": doc.name,
	                    "company": e["company"],
	                }   
                
	                if att_record is not None:
	                    emp_calculated_shifts.append(att_record)
            
            
            
	            late_enter = 0
	            early_exit_time = 0
	            extra_time = 0
	            total_time = 0
	            half_shifts = 0
	            status = "Present"
            
	            for emp_att in emp_calculated_shifts:
                
                
	                if  emp_att["status"] == "Half Day":
	                    half_shifts = half_shifts + 2
	                late_enter = late_enter + int(emp_att["late_enter"])
	                extra_time = extra_time + int(emp_att["extra_time"])
	                early_exit_time = early_exit_time + int(emp_att["early_exit_time"])
	                total_time = total_time + int(emp_att["total_time"])
            
	            if is_mulitple_shifts and len(emp_shifts) == 1:
	                default_shift_duration = get_shift_duration(emp_shifts[0])
	                second_shift_duration = (8*60*60) - default_shift_duration
	                late_enter = late_enter + int(second_shift_duration)
                
	            # if current_date == "2026-02-25" and emp_id == e["name"]:
	            #     frappe.throw(f"h {seconds_to_hhmm(extra_time)}")
            
            
	            att_record = {
	                    "employee": e["name"],
	                    "late_enter_time": seconds_to_hhmm(late_enter),
	                    "early_exit_time": seconds_to_hhmm(early_exit_time),
	                    "extra_time": seconds_to_hhmm(extra_time),
	                    "total_time": seconds_to_hhmm(total_time),
	                    "attendance_date": current_date,
	                    "status": status,
	                    "half_shifts": half_shifts,
	                    "shift": current_shift.name,
	                    "auto_atten_id": doc.name,
	                    "company": e["company"],
	                }   

	            emp_calculated_att.append(att_record)
	            # if current_date == "2026-02-28" and emp_id == e["name"]:
	            # frappe.throw(f"h {att_record}")
                
	            # frappe.throw(f"{total_time} - {att_record} ")
            
	            current_date = frappe.utils.add_days(current_date, 1)

	        calculated_attendaces.extend(emp_calculated_att)
        

	    doc.attendance_results = []
	    frappe.msgprint(f"Attendance Count = {len(calculated_attendaces)}")
	    for att in calculated_attendaces:
	        new_row = {
	            "employee": att["employee"],
	            "late_enter_time": att["late_enter_time"],
	            "early_exit_time": att["early_exit_time"],
	            "extra_time": att["extra_time"],
	            "total_time": att["total_time"],
	            "attendance_date": att["attendance_date"],
	            "status": att["status"],
	            "shift": att["shift"],
	            "half_shifts": att["half_shifts"],
	            "auto_atten_id": doc.name,
	            "company": att["company"],
	        }
	        doc.append("attendance_results", new_row)
        
	    doc.calculated = True

    
    
        
    
    
	# frappe.throw(f"END")


# Event: Clients Sanctions Lists -> Clients Sanctions Lists.Before Save
def clients_sanctions_lists(doc, method=None):
	old_doc = doc.get_doc_before_save()


	if old_doc.client_id != doc.client_id:
	    url = "https://kpi.shumulbankapps.com/api/data"

	    payload = json.dumps(
	        {
	            "requestType": "clientid",
	            "clientID": f"{doc.client_id}"
	        }
	    )
	    headers = {
	        "Content-Type": "application/json",
	        "Accept": "application/json",
	        "X-API-KPISYSTEM-LIVE":"KPI_2026_BankSYSTEM_INTERNAL_27F2A9ER12C5BP8E4F6A"
	    }
    
	    try:
	        response = frappe.make_post_request(url, data=payload, headers=headers)
        
	        client_data = response.get("data")        
	        doc.client_name = client_data.get("Name")
	        doc.opened_date = client_data.get("CreatedOn")
	        doc.opened_by = client_data.get("CreatedBy")
        
	        # frappe.throw(f"{client_data}")
	    except:
	        frappe.throw("فشل في جلب بيانات العميل, تأكد من كتابة رقم العميل بشكل صحيح.")


# Permission Query: Permission Change Request -> Permission Change Request
def permission_change_request(user):
	conditions = []
	user = frappe.session.user

	user_info = frappe.db.get_value("Employee", {"user_id": user}, ["department", "name"], as_dict=True)
	role_profile = frappe.db.get_value("User", user, "role_profile_name")

	# 1. Base conditions (always applied)
	# Includes Owner check and Leave Approver check
	conditions = [
	    f"owner = '{user}'",
	    f"EXISTS (SELECT 1 FROM `tabEmployee` WHERE user_id = `tabPermission Change Request`.owner AND leave_approver = '{user}')"
	]

	# 2. Administrator / No Role Profile check
	if not role_profile:
	    conditions.append(f"EXISTS (SELECT 1 FROM `tabUser` WHERE name='{user}' AND role_profile_name IS NULL)")


	# 3. HR Access (Role-based)
	if user_info and user_info.get("department") == 'ادارة الموارد البشرية - SH':
	    conditions.append("workflow_state IN ('HR Pending', 'Financial Pending', 'IT Pending', 'Completed', 'Rejected') and hr_department = 'ادارة الموارد البشرية - SH'")

	# 4. Department-based Access (using user_info)
	if user_info:
	    dept = user_info.get("department")
    
	    if dept == 'الادارة المالية - SH':
	        conditions.append("workflow_state IN ('Financial Pending', 'IT Pending', 'Completed') and direct_to='المالية'")
        
	    elif dept == 'IT - SH':
	        conditions.append("workflow_state IN ('IT Pending', 'Completed')")

	# Join all conditions with OR
	conditions = f"({' OR '.join(conditions)})"
	# frappe.throw(f"{conditions}")
	return conditions


# API: Save Auto Attendance
@frappe.whitelist()
def save_auto_attendance(**kwargs):
	args = frappe.form_dict


	start = int(args.start)
	end = int(args.end)

	doc = frappe.get_doc(args.doctype, args.docname)

	# Safety check: make sure range is valid
	total = len(doc.attendance_results)
	if start < 0:
	    start = 0
	if end > total:
	    end = total

	# Process only the selected slice
	selected_rows = doc.attendance_results[start:end]

	for att in selected_rows:
	    try:
	        new_row = {
	            "doctype": "Attendance",
	            "employee": att.employee,
	            "late_enter_time": att.late_enter_time,
	            "early_exit_time": att.early_exit_time,
	            "extra_time": att.extra_time,
	            "total_time": att.total_time,
	            "attendance_date": att.attendance_date,
	            "status": att.status,
	            "shift": att.shift,
	            "half_shifts": att.half_shifts,
	            "auto_atten_id": doc.name,
	            "company": att.company,
	        }

	        attendance = frappe.get_doc(new_row)
	        attendance.flags.ignore_permissions = True
	        attendance.insert()
	        attendance.submit()

	    except Exception as e:
	        frappe.msgprint(f"Exception {str(e)}")

	# Remove only the processed rows from child table

	# doc.attendance_results = doc.attendance_results[end:]
	# doc.save(ignore_permissions=True)

	frappe.response['message'] = len(selected_rows)


# Event: Internal Message Naming Series -> Internal Message.Before Insert
def internal_message_naming_series(doc, method=None):
	if doc.inbox_reference_id:
	    ref_doc = frappe.get_doc("Inbox Messages", doc.inbox_reference_id)
	    is_submitted = False
	    if ref_doc:
	        is_submitted = ref_doc.docstatus == 1
    
	    if not is_submitted:
	        frappe.throw(
	            msg=_("Message not submitted. Please check the Cost Center settings."),
	            title=_("يجب اعتماد البريد قبل إعادة توجيهه."),
	            exc=frappe.ValidationError
	        )

	date_str = frappe.utils.nowdate().replace("-","")
	# 4. Construct the prefix for the naming series.
	# This will look like "FIN-01032024-"
	prefix = f"OUT-{doc.shortcut}-{date_str}-"
	# 5. Find the last used number for this specific prefix (department and date).
	# We query the database for all existing documents that start with our prefix.
	last_doc = frappe.db.sql(f"""
	    SELECT name
	    FROM `tabInternal Message`
	    WHERE from_department = '{doc.from_department}'
	    ORDER BY creation DESC
	    LIMIT 1
	""", as_dict=True)
	# 6. Calculate the next number in the sequence.
	next_number = 1
	if last_doc:
    
	    # If a previous document was found, extract its number.
	    # e.g., from "FIN-01032024-00005", we get "00005"
	    last_series_str = last_doc[0]["name"].split('-')[-1]
	    # Convert it to an integer (5) and add 1 to get the next number (6).
	    next_number = int(last_series_str) + 1

	# 7. Format the final name with 5-digit zero-padding for the number.
	# e.g., 6 becomes "00006"
	final_name = f"{prefix}{next_number:05d}"

	# 8. Set the document's name. This will be its unique ID.
	doc.naming_series = final_name


# API: Internal Message Resubmit
@frappe.whitelist()
def send_message(**kwargs):
	args = frappe.form_dict

	doc_name = args["name"]
	doc = frappe.get_doc("Internal Message", doc_name)

	if doc.inbox_reference_id:
	    ref_doc = frappe.get_doc("Inbox Messages", doc.inbox_reference_id)
	    is_submitted = False
	    if ref_doc:
	        is_submitted = ref_doc.docstatus == 1
    
	    if not is_submitted:
	        frappe.throw(
	            msg=_("Message not submitted. Please check the Cost Center settings."),
	            title=_("يجب اعتماد البريد قبل إعادة توجيهه."),
	            exc=frappe.ValidationError
	        )

	to_employees = []
	for row in doc.to_employees:
	    to_employees.append({
	        "employee": row.employee,
	        "employee_name": row.employee_name
	    })
    
	attachments = []
	for row in doc.attachments:
	    attachments.append({
	        "attachment": row.attachment,
	        "title": row.title
	    })

	args.to_employees = to_employees
	args.from_department = doc.from_department
	args.from_employee_name = doc.employee_name
	args.from_employee = doc.issued_by_emp
	args.issue_date = doc.issue_date
	args.subject = doc.subject
	args.attachments = attachments
	args.description = doc.description
	args.internal_reference_id = doc.internal_reference_id
	args.conversation_id = doc.conversation_id

	secret_key = frappe.db.get_single_value(
	    "System Settings",
	    "messaging_key"
	)

	data = f"{doc.name}:{doc.issued_by_user}:{doc.from_department}"
	secret = secret_key

	payload = secret + data
	digital_signature  = frappe.utils.generate_hash(payload)
	doc.digital_signature = f"{digital_signature}:{data}"


	if doc.docstatus != 2:
	    doc.submit()
    
	# to_employees = json.loads(args.to_employees)
	# attachments = json.loads(args.attachments)

	to_employees = args.to_employees
	attachments = args.attachments

	submitted = False
	inboxDocs = []

	for emp in to_employees:
	    employee = emp["employee"]
	    employee_name = emp["employee_name"]
    
	    found_records = frappe.get_all("Inbox Messages",
	        filters={"internal_reference_id": args.name, "to_employee": employee},
	        fields=["name", "subject"]
	    )
	    if len(found_records) > 0:
	        continue
	    submitted = True
	    new__inbox_record = frappe.get_doc({
	            "doctype": "Inbox Messages",
	            "from_department": args.from_department,
	            "from_employee_name": args.from_employee_name,
	            "from_employee": args.from_employee,
	            "to_employee": employee,
	            "issue_date": args.issue_date,
	            "subject": args.subject,
	            "attachments": attachments,
	            "description": args.description,
	            "internal_reference_id": args.name,
	        })
        
	    if args.conversation_id:
	        new__inbox_record.conversation_id = args.conversation_id
	    else:
	        new__inbox_record.conversation_id = args.name
	    new__inbox_record.insert(ignore_permissions=True)  # First insert the document
    
	    inboxDocs.append({
	        "employee": employee,
	        "docname": new__inbox_record.name
	    })
    
	if submitted:
	    frappe.msgprint("تم إرسال الرسالة بنجاح.")
	else:
	    frappe.msgprint("الرسالة مُرسلة مسبقًا.")
    
	frappe.response['inboxDocs'] = inboxDocs


# API: Internal Message Cancel Linked Inbox
@frappe.whitelist()
def cancel_linked_inbox(**kwargs):
	args = frappe.form_dict


	all_darft_inbox = frappe.get_all(
	    "Inbox Messages", 
	    fields=["*"],
	    filters=[
	        ["internal_reference_id","=", args.internal_reference_id]
	    ]
	)

	can_retrive = True

	for inbox in all_darft_inbox:
	    if inbox.docstatus == 1:
	        can_retrive = False
	        break

	if not can_retrive:
	    frappe.msgprint("لا يمكن التراجع, تم استلام بعض الرسائل")
	    frappe.response['retrieved'] = "false"
	else:
	    for inbox in all_darft_inbox:
	        if inbox.docstatus == 0:
	            record = frappe.get_doc("Inbox Messages", inbox.name)
	            record.delete(ignore_permissions=True)
	    if len(all_darft_inbox) > 0:
	        frappe.msgprint(f"تم التراجع عن {len(all_darft_inbox)} رسالة")
	        frappe.response['retrieved'] = "true"
	    else:
	        frappe.msgprint("تم استلام جميع الرسائل او لم يتم ارسالها بعد, لا يمكن التراجع عن العملية")
	        frappe.response['retrieved'] = "false"


# API: Internal Messages Validation
@frappe.whitelist()
def validate_message(**kwargs):
	args = frappe.form_dict
	doc_name = args["name"]
	doc = frappe.get_doc("Internal Message", doc_name)
	to_employees = []

	for row in doc.to_employees:
	    to_employees.append({
	        "employee": row.employee,
	        "employee_name": row.employee_name
	    })
    
	can_send = False
	can_retreive = False

	all_darft_inbox = frappe.get_all(
	    "Inbox Messages", 
	    fields=["*"],
	    filters=[
	        ["docstatus","!=", 1],
	        ["internal_reference_id","=", args.name]
	    ]
	)

	can_retreive = len(all_darft_inbox) > 0
	for emp in to_employees:
	    employee = emp["employee"]
	    employee_name = emp["employee_name"]
    
	    found_records = frappe.get_all("Inbox Messages",
	        filters={"internal_reference_id": args.name, "to_employee": employee},
	        fields=["name", "subject"]
	    )
    
	    if len(found_records) == 0:
	        can_send = True
	        break
    
	frappe.response['can_send'] = can_send
	frappe.response['can_retreive'] = can_retreive


# API: Internal Message Get Employees API
@frappe.whitelist()
def get_employees_internal_message(**kwargs):
	args = frappe.form_dict
	query = f"""
	    SELECT name, employee_name, in_inbox_managers_list, department
	    FROM `tabEmployee`
	    WHERE 
	       (status = 'Active' AND department = %(department)s) OR (status = 'Active' AND in_inbox_managers_list = 1)
	    """
    
	results = frappe.db.sql(query, values = {"department": args["department"]} ,as_dict=True)

	frappe.response['results'] = results


# Event: Task Close Issue -> Task.After Save
def task_close_issue(doc, method=None):

	if doc.issue:
	    issue_doc = frappe.get_doc("Issue", doc.issue)
    
	    if issue_doc.status != "closed":
	        if doc.status == "Completed":
	            issue_doc.status = "Resolved"
	        if doc.status == "Working" or doc.status == "Open":
	            issue_doc.status = "Replied"
	        if doc.status == "Pending Review":
	            issue_doc.status = "On Hold"
	        if doc.status == "Cancelled":
	            issue_doc.status = "Cancelled"
            
	        issue_doc.save(ignore_permissions=True)
	        frappe.msgprint(f"Issue {issue_doc.name} has been changed to {issue_doc.status}.")


# Event: Inbox Messages Confirmation -> Inbox Messages.After Submit
def inbox_messages_confirmation(doc, method=None):
	reference_doc = frappe.get_doc("Internal Message", doc.internal_reference_id)
	if reference_doc.message_status == "Waiting":
	    reference_doc.message_status = "Seen"
	# reference_doc.message_status = doc.message_status
	reference_doc.receiver_comment = doc.quick_reply
	reference_doc.save(ignore_permissions=True)


# Event: Internal Message Submit -> Internal Message.After Save
def internal_message_submit(doc, method=None):

	# doc.save()
	if doc.message_saved == False:
	    # frappe.msgprint("تم حفظ الرسالة, قم بالضغط على زر الارسال لكي يتم ارسال الرسالة")
	    doc.message_saved = True
	    doc.save()


# Event: Users Permissions Control -> Users Permissions Control.After Save
def users_permissions_control(doc, method=None):
	id = "Users_Permissions_Control"

	permissions = frappe.get_all("User Permission",
	    filters={
	        "ref_id" : id,
	    },
	)
	user_grps = frappe.get_all("User Group",
	    filters={
	        "ref_id" : id,
	    },
	)

	for perm in permissions:
	    frappe.delete_doc("User Permission", perm.name, ignore_permissions=True)
	for perm in user_grps:
	    frappe.delete_doc("User Group", perm.name, ignore_permissions=True)

	for p in doc.perm_list:
	    row_data = {
	            "doctype": "User Permission",
	            "user": p.user,
	            "allow": p.module,
	            "for_value": p.value_for,
	            "ref_id": id,
	            "apply_to_all_doctypes": p.applicable_for is None,
	            "applicable_for": p.applicable_for,
	            "hide_descendants": p.hide_descendants
	        }
	    try:
	        new_perm = frappe.get_doc(row_data).insert()
	    except Exception as e:
	        frappe.msgprint(f"Error while creating permission for: {row_data}")

	all_roles = [p.value_for for p in doc.perm_list if p.module == "Department" and not p.value_for == "All Departments"]
	all_departments = list(set(all_roles))

	for dep in all_departments:
    
	    user_group = frappe.get_doc({
	                "doctype": "User Group",
	                "name": dep,
	                "user_group_name": dep,
	                "ref_id": id,
	            })
            
	    for p in doc.perm_list:
	        if p.value_for == dep and p.module == "Department":
	            user_group.append("user_group_members", {
	                    "user": p.user
	                })
                
	    user_group.insert(ignore_permissions=True)
    
    
	frappe.msgprint(f"Data saved with id: {id}")


# Event: Auto Leave Allocation Save -> Auto Leave Allocation.After Save
def auto_leave_allocation_save(doc, method=None):
	query = f"""
	    SELECT 
	    la.employee,
	    la.employee_name,
	    la.from_date,
	    la.to_date,
	    la.new_leaves_allocated as prev_leaves_allocated,
	    la.name AS allocation_name
	FROM `tabLeave Allocation` la
	INNER JOIN (
	    SELECT 
	        employee,
	        MAX(from_date) AS last_allocation_date
	    FROM `tabLeave Allocation`
	    WHERE docstatus = 1
	        and leave_type = %(leave_type)s
	    GROUP BY employee
	) latest ON la.employee = latest.employee 
	AND la.from_date = latest.last_allocation_date
	WHERE la.docstatus = 1 and la.leave_type = %(leave_type)s
	ORDER BY la.employee;
	"""

	last_allocated_leaves = frappe.db.sql(query,values={"leave_type": doc.leave_type}, as_dict=True)

	doc.leaves_list = []

	for la in last_allocated_leaves:
	    doc.append("leaves_list", {
	        "employee": la["employee"],
	        "employee_name": la["employee_name"],
	        "last_allocation_date": la["from_date"],
	        "last_allocated_leaves": la["prev_leaves_allocated"],
	        "leave_allocation_id": la["allocation_name"],
	        "new_leaves": doc.new_leaves + la["prev_leaves_allocated"]
	    })


	# for leave in doc.leaves_list:
	#     period = frappe.get_doc("Leave Period", doc.leave_period)
	#     new_alloc = frappe.get_doc({
	#         "doctype": "Leave Allocation",
	#         "employee": leave.employee,
	#         "leave_type": doc.leave_type,
	#         "from_date": period.from_date,
	#         "to_date": period.to_date,
	#         "new_leaves_allocated": leave.new_leaves,
	#         "carry_forward": 0
	#     })
    
	#     new_alloc.insert()  # First insert the document
	#     new_alloc.submit()  # Then submit it


# Event: Short Leave Validation -> Short Leave.Before Submit
def short_leave_validation(doc, method=None):
	employees = frappe.get_list("Employee", fields=["name"], filters={"user_id": frappe.session.user})
	if employees != None and len(employees) > 0:
	    if doc.short_leave_approvar != frappe.session.user:
	        frappe.throw("لا يمكن للموظف الموافقة على طلب الاذن الخاص به. يرجى رفع الطلب إلى المسؤول المباشر لاتخاذ الإجراء المناسب.")


# Event: Leave Application Validation -> Leave Application.Before Submit
def leave_application_validation(doc, method=None):
	employees = frappe.get_list("Employee", fields=["name"], filters={"user_id": frappe.session.user})

	if employees != None and len(employees) > 0:
	    if doc.leave_approver != frappe.session.user:
	        frappe.throw("لا يمكن للموظف الموافقة على طلب الإجازة الخاص به. يرجى رفع الطلب إلى المسؤول المباشر لاتخاذ الإجراء المناسب.")


# Event: Auto Attendance Script -> Auto Attendance.After Submit
def auto_attendance_script(doc, method=None):
	# from_date = doc.from_date
	# to_date = doc.to_date
  
	# attendances = frappe.get_all(
	#     "Attendance",
	#     filters=[
	#         ["auto_atten_id", "=", doc.amended_from],
	#     ],
	#     limit=0
	# )
	# # 2. Cancel each attendance
	# for att in attendances:
	#     attendance = frappe.get_doc("Attendance", att.name)
	#     attendance.delete()

	# emps = []

	# if doc.all_employees:
	#     all_emps = frappe.get_all(
	#         "Employee",
	#          fields="*",
	#          filters=[["status","=","Active"]],
	#          limit=0,
	#     )
	#     for e in all_emps:
	#         emps.append({"name": e.employee, "default_shift": e.default_shift, "company": e.company})
	# else:
	#     for e in doc.employees:
	#         emps.append({"name": e.employee, "default_shift": e.default_shift, "company": e.company})

	# from_date_filter = frappe.utils.add_days(from_date, 0)

	# to_date_filter = frappe.utils.add_days(to_date, 1)


	# query = f"""
	#     SELECT distinct *
	#     FROM `tabEmployee Checkin`
	#     WHERE time BETWEEN DATE('{from_date_filter}') AND DATE('{to_date_filter}')
	#     ORDER BY
	#         time ASC
	# """

	# checks = frappe.db.sql(query, as_dict=True)

	# shift_assignment = frappe.get_all(
	#                 "Shift Assignment",
	#                 fields="*",
	#                 filters=[
	#                     ["start_date", ">=", from_date],
	#                     ["end_date", "<=", to_date],
	#                     ["docstatus", "=", 1],
	#                 ],
	#                 order_by= "start_date desc",
	#                 limit=0
	#             )
            
	# shifts_type = frappe.get_all(
	#                 "Shift Type",
	#                 fields="*",
	#                 limit=0
	#             )
            
	# manual_attendance = frappe.get_all(
	#             "Attendance",
	#             fields="*",
	#             filters=[
	#                 ["docstatus","=",1],
	#                 # ["status","=","On Leave"],
	#                 ["attendance_date",">=",from_date],
	#                 ["attendance_date","<=",to_date]
	#             ],
	#             limit=0,
	#     )
    
	# def get_shift_type(shifts_type, shift_name):
	#     for shift in shifts_type:
	#         if shift.name == shift_name:
	#             return shift
	#     return None
    
	# def seconds_to_hhmm(seconds):
    
	#     if seconds == 0:
	#         return "00:00:00"
	#     hours = int(seconds // 3600)          # 18000 // 3600 = 5
    
	#     remaining_seconds = seconds % 3600    # 18000 % 3600 = 0
	#     minutes = int((remaining_seconds + 29) // 60)  # (0 + 29) // 60 = 0
    
	#     if minutes >= 60:
	#         additional_hours = minutes // 60
	#         hours = hours + additional_hours
	#         minutes = minutes % 60

	#     return f"{hours:02d}:{minutes:02d}:00"
    
	# def get_date_checks(checks, date):
	#     current_date_checks = []
	#     for log in checks:
	#         if log.time.date() == frappe.utils.getdate(date):
	#             current_date_checks.append(log)
    
	#     return current_date_checks

	# def get_shift_checks(current_date_checks, shift):
	#     start_range_seconds = shift.start_time.total_seconds() - (shift.begin_check_in_before_shift_start_time * 60)
	#     end_range_seconds = shift.end_time.total_seconds() + (shift.end_check_out_after_shift_end * 60)
	#     shift_checks = []
	#     for log in current_date_checks:
	#         if log in shift_checks:
	#             continue
        
	#         check_time = frappe.utils.get_time(log.time)
	#         check_time_seconds = (check_time.hour * 3600) + (check_time.minute * 60) + check_time.second
        
	#         if check_time_seconds >= start_range_seconds and check_time_seconds <= end_range_seconds:
	#             shift_checks.append(log)
	#     shift_checks.sort(key=lambda x: x.time)
	#     return shift_checks

	# def get_shift_duration(shift_type):
	#     start_time_seconds = frappe.utils.get_timedelta(shift_type.start_time).total_seconds()
	#     end_time_seconds = frappe.utils.get_timedelta(shift_type.end_time).total_seconds()
	#     total_shift_seconds = (end_time_seconds - start_time_seconds)
	#     return total_shift_seconds
    
	# def calculate_shift_status(emp_id, current_date, shift_type, checkin, checkout):
    
	#     first_in_time = frappe.utils.get_time(checkin.time)
	#     first_in_seconds = (first_in_time.hour * 3600) + (first_in_time.minute * 60) + first_in_time.second
    
	#     last_out_time = frappe.utils.get_time(checkout.time)
	#     last_out_seconds = (last_out_time.hour * 3600) + (last_out_time.minute * 60) + last_out_time.second
	#     # Convert shift times to seconds
	#     start_time_seconds = frappe.utils.get_timedelta(shift_type.start_time).total_seconds()
	#     end_time_seconds = frappe.utils.get_timedelta(shift_type.end_time).total_seconds()
	#     total_shift_seconds = (end_time_seconds - start_time_seconds)
    
	#     if last_out_seconds <= start_time_seconds:
	#         last_out_seconds = 0
    
	#     # Allowed margins
	#     allow_check_in_seconds = shift_type.allow_check_in * 60
	#     allow_before_check_out_seconds = shift_type.begin_check_out_before_shift_end * 60
    
	#     # Late entry calculation
	#     late_enter = first_in_seconds - start_time_seconds
	#     if late_enter <= allow_check_in_seconds:
	#         late_enter = 0
    
    
	#     # Early exit / extra time calculation
	#     extra_time = last_out_seconds - end_time_seconds
	#     early_exit_time = 0
    
	#     if last_out_seconds != 0:
	#         if extra_time < 0:
	#             early_exit_time = abs(extra_time)
	#             extra_time = 0
	#     else:
	#         extra_time = 0
	#         early_exit_time = 0
	#         late_enter = total_shift_seconds / 2

	#     # Adjust first_in and last_out within shift bounds
	#     if first_in_seconds < start_time_seconds:
	#         first_in_seconds = start_time_seconds
	#     if last_out_seconds > end_time_seconds:
	#         last_out_seconds = end_time_seconds

	#     # Calculate total worked time
	#     total_time = total_shift_seconds - late_enter - early_exit_time

	#     if total_time <= 0:
	#         total_time = 0

	#     # Determine status
	#     status = "Present"
	#     #if total_time <= (total_shift_seconds / 2):
	#     #    status = "Half Day"
    
	#     results = {
	#         "total_time" : total_time,
	#         "status": status,
	#         "late_enter": late_enter,
	#         "early_exit_time": early_exit_time,
	#         "extra_time": extra_time
	#     }
	#     # if current_date == '2025-10-01' and emp_id == 'HR-EMP00010':
	#     #     frappe.throw(f"{results} , {shift_type.name}")
	#     return results

    


	# calculated_attendaces = []

	# for e in emps:
    
	#     emp_id = e["name"]
	#     emp_checks = []
    
	#     for log in checks:
	#         if log.employee == emp_id:
	#             emp_checks.append(log)
    
	#     if emp_checks is None or len(emp_checks) == 0:
	#         continue
    
	#     emp_calculated_att = []

	#     current_date = doc.from_date
    
	#     while current_date <= doc.to_date:
        
        
	#         is_manual = False
	#         for manual in manual_attendance:
	#             if manual.employee == emp_id and str(manual.attendance_date) == str(current_date):
	#                 is_manual = True
	#                 break

	#         if is_manual:
	#             current_date = frappe.utils.add_days(current_date, 1)
	#             continue
        
	#         current_date_checks = get_date_checks(emp_checks, current_date)

	#         if current_date_checks is None or len(current_date_checks) == 0:
	#             current_date = frappe.utils.add_days(current_date, 1)
	#             continue
        
	#         emp_shift_assign = None
	#         for sa in shift_assignment:
	#             if sa.employee == emp_id and frappe.utils.getdate(current_date) >= sa.start_date and frappe.utils.getdate(current_date) <= sa.end_date:
	#                 emp_shift_assign = sa
	#                 break
            
	#         if emp_shift_assign is None:
	#             current_date = frappe.utils.add_days(current_date, 1)
	#             continue
        
	#         is_mulitple_shifts = emp_shift_assign.is_mulitple_shifts
        
	#         emp_shifts = []
	#         shift_type_1 = get_shift_type(shifts_type, emp_shift_assign.shift_type)
	#         emp_shifts.append(shift_type_1)
            
	#         shift_type_2 = get_shift_type(shifts_type, emp_shift_assign.shift_type_2)
	#         if shift_type_2 is not None:
	#             emp_shifts.append(shift_type_2)

	#         emp_calculated_shifts = []

	#         for current_shift in emp_shifts:
	#             shift_checks = get_shift_checks(current_date_checks, current_shift) 
	#             shift_duration = get_shift_duration(current_shift)
            
	#             if shift_checks is None or len(shift_checks) == 0:
                
	#                 att_record = {
	#                     "employee": e["name"],
	#                     "late_enter": shift_duration,
	#                     "early_exit_time": 0,
	#                     "extra_time": 0,
	#                     "total_time": 0,
	#                     "attendance_date": current_date,
	#                     "status": "Present",
	#                     "shift": current_shift.name,
	#                     "auto_atten_id": doc.name,
	#                     "company": e["company"],
	#                 }   
	#                 # emp_calculated_att.append(att_record)
	#                 emp_calculated_shifts.append(att_record)
	#                 continue

	#              #تعديل احتساب التأخير او نسيان البصمة
	#             att_record = None
	#             if len(shift_checks) == 1:
	#                 att_record = {
	#                     "employee": e["name"],
	#                     "late_enter": shift_duration/2,
	#                     "early_exit_time": 0,
	#                     "extra_time": 0,
	#                     "total_time": shift_duration/2,
	#                     "attendance_date": current_date,
	#                     "status": "Present",
	#                     "shift": current_shift.name,
	#                     "auto_atten_id": doc.name,
	#                     "company": e["company"],
	#                 }   
	#                 emp_calculated_shifts.append(att_record)
	#                 continue

	#             checkin = shift_checks[0]
	#             checkout = shift_checks[-1]

	#             shift_data = calculate_shift_status(emp_id, current_date, current_shift, checkin, checkout)
	#             # if current_date == '2025-10-01' and emp_id == 'HR-EMP00010':
	#             #     frappe.throw(f"{shift_data}")
            
	#             late_enter = shift_data["late_enter"]
	#             early_exit_time = shift_data["early_exit_time"]
	#             extra_time = shift_data["extra_time"]
	#             total_time = shift_data["total_time"]
	#             status = shift_data["status"]
	#             att_record = {
	#                 "employee": e["name"],
	#                 "late_enter": late_enter,
	#                 "early_exit_time": early_exit_time,
	#                 "extra_time": extra_time,
	#                 "total_time": total_time,
	#                 "attendance_date": current_date,
	#                 "status": status,
	#                 "shift": current_shift.name,
	#                 "auto_atten_id": doc.name,
	#                 "company": e["company"],
	#             }   
            
	#             if att_record is not None:
	#                 emp_calculated_shifts.append(att_record)
        
	#         late_enter = 0
	#         early_exit_time = 0
	#         extra_time = 0
	#         total_time = 0
	#         half_shifts = 0
	#         status = "Present"

	#         for emp_att in emp_calculated_shifts:
	#             # if emp_att["status"] == "Half Day":
	#             #     half_shifts = half_shifts + 1
	#             if  emp_att["status"] == "Half Day":
	#                 half_shifts = half_shifts + 2
	#             late_enter = late_enter + int(emp_att["late_enter"])
	#             extra_time = extra_time + int(emp_att["extra_time"])
	#             early_exit_time = early_exit_time + int(emp_att["early_exit_time"])
	#             total_time = total_time + int(emp_att["total_time"])
        
	#         if is_mulitple_shifts and len(emp_shifts) == 1:
	#             default_shift_duration = get_shift_duration(emp_shifts[0])
	#             late_enter = late_enter + int(default_shift_duration)
            
	#         att_record = {
	#                 "employee": e["name"],
	#                 "late_enter_time": seconds_to_hhmm(late_enter),
	#                 "early_exit_time": seconds_to_hhmm(early_exit_time),
	#                 "extra_time": seconds_to_hhmm(extra_time),
	#                 "total_time": seconds_to_hhmm(total_time),
	#                 "attendance_date": current_date,
	#                 "status": status,
	#                 "half_shifts": half_shifts,
	#                 "shift": current_shift.name,
	#                 "auto_atten_id": doc.name,
	#                 "company": e["company"],
	#             }   
	#         # if current_date == "2025-08-21":
	#         #     frappe.throw(f"{att_record}")         
	#         emp_calculated_att.append(att_record)
        
	#         # if current_date == '2025-09-29':
	#         #     frappe.throw(f"Records {att_record}")
        
	#         current_date = frappe.utils.add_days(current_date, 1)
        
	#     # frappe.msgprint(f"DONE {emp_id} - {current_date}")
	#     calculated_attendaces.extend(emp_calculated_att)
    
	#     # if emp_id == 'HR-EMP-00032':
	#     #     frappe.throw(f"VVV {emp_calculated_att}")    
	# names = [d["employee"] for d in calculated_attendaces]    
	# # frappe.throw(f"VVV {names}")     

	# # doc.attendance_results = calculated_attendaces
	# for att in calculated_attendaces:
	#     new_row = {
	#         "employee": att["employee"],
	#         "late_enter_time": att["late_enter_time"],
	#         "early_exit_time": att["early_exit_time"],
	#         "extra_time": att["extra_time"],
	#         "total_time": att["total_time"],
	#         "attendance_date": att["attendance_date"],
	#         "status": att["status"],
	#         "shift": att["shift"],
	#         "half_shifts": att["half_shifts"],
	#         "auto_atten_id": doc.name,
	#         "company": att["company"],
	#     }
	#     doc.append("attendance_results", new_row)


	if len(doc.attendance_results) > 0:
	    frappe.throw("هناك سجلات متبقية")

	# for att in doc.attendance_results:
	#     new_row = {
	#         "doctype": "Attendance",
	#         "employee": att.employee,
	#         "late_enter_time": att.late_enter_time,
	#         "early_exit_time": att.early_exit_time,
	#         "extra_time": att.extra_time,
	#         "total_time": att.total_time,
	#         "attendance_date": att.attendance_date,
	#         "status": att.status,
	#         "shift": att.shift,
	#         "half_shifts": att.half_shifts,
	#         "auto_atten_id": doc.name,
	#         "company": att.company,
	#     } 

	#     attendance = frappe.get_doc(new_row)
    
	#     attendance.insert()  # First insert the document
	#     attendance.submit()  # Then submit it

    
	# doc.attendance_results = []


# API: Send Notification
@frappe.whitelist()
def send_notification(**kwargs):
	args = frappe.form_dict

	def notify_user(user, subject, message, doctype=None, docname=None):
	    if not user or user == "Guest":
	        return "Invalid user"


	    # 2) Notification Log entry (shows in Notification Bell)
	    notification = frappe.get_doc({
	        "doctype": "Notification Log",
	        "subject": subject,
	        "email_content": message,
	        "for_user": user,
	        "type": "Alert",
	        "document_type": doctype if doctype else "",
	        "document_name": docname if docname else ""
	    })

	    notification.insert(ignore_permissions=True)

	    return f"Notification sent to {user}"

	docs = json.loads(args.docs)
	# frappe.throw(f"{args.docs}")
	for doc in docs:
	    if "user_id" not in doc:
	        continue
    
	    user_id = doc["user_id"]
	    docname = doc["docname"]

	    subject = args.subject
	    notify_user(
	        user=user_id,
	        subject=subject,
	        message= "",
	        doctype=args.doctype,
	        docname=docname
	    )


# API: Internal Messages Delete
@frappe.whitelist()
def delete_internal_message(**kwargs):
	args = frappe.form_dict
	doc_name = args["name"]
	try:
	    doc = frappe.get_doc("Internal Message", doc_name)
	    if doc.docstatus == 1:
	        doc.cancel()
        
	    doc.delete()
	except frappe.LinkExistsError:
	    frappe.throw("لا يمكن حذف الرسالة لارتباطها برسائل اخرى")
	except Exception as e:
	    frappe.throw(f"Unable to delete the document: {str(e)}")


# Event: Auto Leave Allocation Cancel -> Auto Leave Allocation.After Cancel
def auto_leave_allocation_cancel(doc, method=None):

	for new_leave in doc.leaves_list:
	    current_doc = frappe.get_doc("Leave Allocation", new_leave.leave_allocation_id)
	    current_doc.new_leaves_allocated = current_doc.new_leaves_allocated - doc.new_leaves
	    current_doc.save()

	frappe.msgprint("تم الغاء رصيد الاجازات بنجاح");


# Event: Auto Leave Allocation Submit -> Auto Leave Allocation.After Submit
def auto_leave_allocation_submit(doc, method=None):

	for new_leave in doc.leaves_list:
	    current_doc = frappe.get_doc("Leave Allocation", new_leave.leave_allocation_id)
	    current_doc.new_leaves_allocated = new_leave.new_leaves
	    current_doc.save()

	frappe.msgprint("تم اضافة رصيد اجازات جديدة بنجاح");


# Event: Manual Attendance Cancel -> Manual Attendance.After Cancel
def manual_attendance_cancel(doc, method=None):
	all_records = frappe.get_all(
	    "Employee Checkin", 
	    fields=["name"],
	    filters=[
	        ["manual_attendance","=", doc.name]
	    ]
	)

	for c in all_records:
	    new_record = frappe.get_doc("Employee Checkin", c.name)
	    new_record.delete(ignore_permissions=True)  # First insert the document


# Event: Inbox Messages Naming Series -> Inbox Messages.Before Insert
def inbox_messages_naming_series(doc, method=None):

	date_str = frappe.utils.nowdate().replace("-","")
	# 4. Construct the prefix for the naming series.
	# This will look like "FIN-01032024-"
	prefix = f"IN-{doc.shortcut}-{date_str}-"
	# 5. Find the last used number for this specific prefix (department and date).
	# We query the database for all existing documents that start with our prefix.
	last_doc = frappe.db.sql(f"""
	    SELECT name
	    FROM `tabInbox Messages`
	    WHERE to_department = '{doc.to_department}'
	    ORDER BY creation DESC
	    LIMIT 1
	""", as_dict=True)
	# 6. Calculate the next number in the sequence.
	next_number = 1
	if last_doc:
    
	    # If a previous document was found, extract its number.
	    # e.g., from "FIN-01032024-00005", we get "00005"
	    last_series_str = last_doc[0]["name"].split('-')[-1]
	    # Convert it to an integer (5) and add 1 to get the next number (6).
	    next_number = int(last_series_str) + 1

	# 7. Format the final name with 5-digit zero-padding for the number.
	# e.g., 6 becomes "00006"
	final_name = f"{prefix}{next_number:05d}"

	# 8. Set the document's name. This will be its unique ID.
	doc.naming_series = final_name


# Event: Manual Attendance Submit -> Manual Attendance.After Submit
def manual_attendance_submit(doc, method=None):
	for c in doc.checks:
	    checkTime = f"{doc.issue_date} {c.time}"
	    new_record = frappe.get_doc({
	        "doctype": "Employee Checkin",
	        "employee": doc.employee,
	        "time": checkTime,
	        "log_type": c.status,
	        "device_id": doc.title,
	        "manual_attendance": doc.name
	    })
    
	    new_record.insert(ignore_permissions=True)  # First insert the document


# Event: Leave Application WIth Short Leaves -> Leave Application.Before Submit
def leave_application_with_short_leaves(doc, method=None):

	allocated_leaves = frappe.get_all(
	    "Leave Allocation",
	    fields=["*"],
	    filters=[
	        ["leave_type","=",doc.leave_type],
	        ["employee","=",doc.employee],
	        ["from_date", "<=", doc.from_date],
	        ["to_date", ">=", doc.to_date],
	    ],
	    limit=0
	)
	if len(allocated_leaves) > 0:
	    leaves = frappe.get_all(
	        "Leave Type",
	        fields=["*"],
	        filters=[
	            ["name","=",doc.leave_type],
	            ["is_compensatory", "!=", "1"],
	        ],
	        limit=0
	    )
	    prev_short_leaves = frappe.get_list(
	        "Short Leave",
	        fields= ['*'],
	        filters=[
	            ["docstatus", "=", 1],
	            ["leave_type", "=", doc.leave_type],
	            ["employee", "=", doc.employee],
	        ],
	        limit=0
	    );
    
	    total_amount = 0;
    
	    for lev in prev_short_leaves:
	        total_amount = total_amount + lev.short_leave_amount_in_minuts / (8 * 60) / 60;
    
	    remaining_leaves = round(doc.leave_balance - total_amount, 2)
	    total_amount = round(total_amount, 2)
    
	    if doc.total_leave_days >= remaining_leaves:
	        frappe.throw(
	        f"لا يوجد رصيد إجازات كافٍ. الرصيد المتاح: {remaining_leaves} يوم/أيام، عدد الأذون المستخدمة: {total_amount}.",
	        title="رصيد الإجازات غير كافٍ"
	    )
    
	    doc.short_leaves_used = total_amount


# Event: Auto Salary Entry Submit -> Auto Salary Entry.After Submit
def auto_salary_entry_submit(doc, method=None):
	submitted_salaries = frappe.get_all(
	    "Auto Salary Slip",
	    filters=[
	        ["entry_title","=",doc.title]
	    ]
	)
	# 2. Cancel each attendance
	for ssal in submitted_salaries:
	    auto_sal_slip = frappe.get_doc("Auto Salary Slip", ssal.name)
	    auto_sal_slip.delete()


	salaries = frappe.get_all(
	    "Auto Salary Entry Table",
	    fields="*",
	    filters=[
	        ["parent", "=", doc.name]
	    ],
	)

	for sal in salaries:
	    auto_sal_slip = frappe.get_doc({
	        "doctype": "Auto Salary Slip",
	        "employee": sal.employee,
	        "net_salary": sal.net_salary,
	        "total_deductions": sal.absent_deductions + sal.late_deductions,
	        "late_deductions": sal.late_deductions,
	        "late_advance": sal.total_advance,
	        "absent_deductions": sal.absent_deductions,
	        "base_salary" : sal.base_salary,
	        "additional_allowance": sal.additional_allowance,
	        "present": sal.present,
	        "absent" : sal.absent,
	        "from_date": doc.from_date,
	        "to_date": doc.to_date,
	        "auto_salary_entry": doc.name,
	    })
        
	    auto_sal_slip.insert()  # First insert the document
	    auto_sal_slip.submit()  # Then submit it


# Event: Periodic Salary Structure Submit -> Periodic Salary Structure.After Submit
def periodic_salary_structure_submit(doc, method=None):
	submitted = frappe.get_all(
	    "Salary Structure Assignment",
	    filters=[
	        ["periodic_salary_structure","=",doc.amended_from]
	    ]
	)

	# 2. Cancel each attendance
	for s in submitted:
	    found_records = frappe.get_doc("Salary Structure Assignment", s.name)
	    found_records.delete()

	emps = doc.employees
	for e in emps:
	    salary_struct_assignment = frappe.get_doc({
	        "doctype": "Salary Structure Assignment",
	        "employee": e.employee,
	        "salary_structure": e.salary_structure,
	        "from_date": doc.from_date,
	        "periodic_salary_structure": doc.name,
	    })
    
	    salary_struct_assignment.insert()  # First insert the document
	    salary_struct_assignment.submit()  # Then submit it
	    # frappe.msgprint(f"=================================================")


# Event: Long Term Advance Submit -> Long Term Advance.After Submit
def long_term_advance_submit(doc, method=None):
	doc.advance_list[0]

	min_date = None
	max_date = None
	advances = []

	for adv in doc.advance_list:
	    if min_date == None:
	        min_date = adv.from_date
	    else:
	        if adv.from_date < min_date:
	            min_date = adv.from_date
            
	for adv in doc.advance_list:
	    adv_month = 0
	    while adv_month < adv.months:
	        adv_date = frappe.utils.add_months(adv.from_date, adv_month)
	        advances.append({"employee":adv.employee, "date": adv_date,"value_per_month": adv.value_per_month})
	        adv_month = adv_month +1
        
	for adv in advances:
	    if max_date == None:
	        max_date = adv["date"]
	    else:
	        if adv["date"] > max_date:
	            max_date = adv["date"]
            

	current_month = frappe.utils.add_months(min_date, 0)

	while current_month <= max_date:
	    current_advance_list = []

	    for adv in advances:
	        if adv["date"] == current_month:
	            current_advance_list.append({"employee":adv["employee"], "date": current_month, "sal_advance": adv["value_per_month"], "amount": adv["value_per_month"], "salary_structure":"HR-SSA-25-06-00105"})
    
	    if len(current_advance_list) > 0:
	        date = current_advance_list[0]["date"]
	        new_record = frappe.get_doc({
	            "doctype": "Auto Salary Advance",
	            "title": f"{doc.title} - {date}",
	            "from_date": date,
	            "advance_type": "Amount",
	            "issue_date": frappe.utils.nowdate(),
	            "value": 0,
	            "long_term_advance": doc.name,
	            "advance_list": current_advance_list
	        })
	        new_record.insert()  # First insert the document
	        new_record.submit()  # Then submit it
                
	    current_month = frappe.utils.add_months(current_month, 1)


# Event: Issue Linked Tasks -> Task.Before Validate
def issue_linked_tasks(doc, method=None):

	if doc.issue:
	    # Mark the Issue as linked
	    frappe.db.set_value("Issue", doc.issue, "linked", 1)
	else:
	    # If task has no issue, check if the old issue field existed
	    if doc.get_doc_before_save() and doc.get_doc_before_save().issue:
	        old_issue = doc.get_doc_before_save().issue
	        frappe.db.set_value("Issue", old_issue, "linked", 0)


# Event: Project Naming -> Project.Before Save
def project_naming(doc, method=None):

	# 1. Validate that the Department field is set
	if not doc.department or not doc.designation :
	    frappe.throw("Please select a <b>Department</b> and <b>Designation</b> before saving the Project.")
	# 3. Construct the naming series prefix using the department
	# Example: if department is 'Sales', prefix becomes 'PROJ-.Sales.'
	if not doc.is_name_refreshed:
        
	    naming_series_prefix = f"{doc.project_name} - {doc.designation}"
	    # 4. Generate the new name and assign it to the document's 'name' field
	    # The 'make_autoname' function automatically finds the next number (e.g., 0001)
	    doc.is_name_refreshed = True
	    doc.project_name = naming_series_prefix


# Event: Attendance Overrider Submit -> Attendance Overrider.After Submit
def attendance_overrider_submit(doc, method=None):
	employees = []

	if len(doc.employees) > 0 and not doc.all_employees:
	    for e in doc.employees:
	       employees.append({"employee": e.employee,"max_days": e.max_days, "shift_type": e.shift_type, "from_date": e.from_date, "to_date": e.to_date, "from_status": e.from_status, "to_status": e.to_status}) 
	else:
	    checkin_emps = frappe.get_all(
	        "Attendance",
	        fields=["employee"],  # The Link field to the Employee doctype
	        filters=[
	            ["attendance_date", ">=", doc.from_date],  # Start of from_date
	            ["attendance_date", "<=", doc.to_date]     # End of to_date
	         ],
	         limit=0,
	        distinct=True
	    )

	    for e in checkin_emps:
	           employees.append({"employee": e.employee,"max_days": doc.max_days, "shift_type": doc.default_shift, "from_date": doc.from_date, "to_date": doc.to_date, "from_status": doc.from_status, "to_status": doc.to_status}) 


	for emp in employees:
	    attendances = frappe.get_all(
	        "Attendance",
	         fields="*",
	         filters=[
	            ["employee", "=", emp["employee"]], 
	            ["status", "=", emp["from_status"]],
	            ["attendance_date", ">=", emp["from_date"]],  # Start of from_date
	            ["attendance_date", "<=", emp["to_date"]]     # End of to_date
	         ],
	         limit=emp["max_days"],
	    )
    
	    for att in attendances:
	        found_att = frappe.get_doc("Attendance", att.name)
	        att_employee = found_att.employee
	        att_date = found_att.attendance_date
	        att_company = found_att.company
	        att_auto_atten_id = found_att.auto_atten_id
        
	        if found_att.docstatus != 2:
	            found_att.cancel()
	        found_att.delete()
        
	        new_att = frappe.get_doc({
	            "doctype": "Attendance",
	            "employee": att_employee,
	            "late_enter_time": "00:00:00",
	            "early_exit_time": "00:00:00",
	            "extra_time": "00:00:00",
	            "total_time": "00:00:00",
	            "attendance_date": att_date,
	            "shift": emp["shift_type"],
	            "status": emp["to_status"],
	            "auto_atten_id": att_auto_atten_id,
	            "attendance_override_id" : doc.name,
	            "company": att_company,
	        })
        
	        new_att.insert()  # First insert the document
	        new_att.submit()  # Then submit it

