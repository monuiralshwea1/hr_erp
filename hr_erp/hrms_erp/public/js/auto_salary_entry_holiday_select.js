frappe.ui.form.on('Auto Salary Entry', {
// Run the logic when the form first loads or refreshes
    // Run the logic when the form first loads or refreshes
    
    
    refresh: function(frm) {

        updateFieldStatus(frm);

        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Calculate Salary'), function() {
                // Your button action here
                calculateSalary(frm)
            });
        }
      
    },
	holiday_from: function(frm) {
        // --- Configuration: Replace these values ---
        updateFieldStatus(frm);
        
    },
    from_date: function(frm) {
       updateDaysField(frm);
    },
    to_date: function(frm) {
       updateDaysField(frm);
    }
})
frappe.ui.form.on('Auto Salary Entry Table', {
	 refresh: function(frm) {
	},
	employee_name: function(frm, cdt, cdn) {

        calculate_salary_change(frm, cdt, cdn);
	},
	late_deductions: function(frm, cdt, cdn) {
        calculate_salary_change(frm, cdt, cdn);
	},

	absent: function(frm, cdt, cdn) {
        calculate_present_change(frm, cdt, cdn);
        calculate_salary_change(frm, cdt, cdn);
	},
	total_advance: function(frm, cdt, cdn) {
        calculate_present_change(frm, cdt, cdn);
        calculate_salary_change(frm, cdt, cdn);
	},
    base_salary: function(frm, cdt, cdn) {
        calculate_present_change(frm, cdt, cdn);
        calculate_salary_change(frm, cdt, cdn);
	}
})

function calculate_salary_change(frm, cdt, cdn){
    let changed_row = frappe.get_doc(cdt, cdn); 

    changed_row.total_deductions = changed_row.late_deductions + changed_row.absent_deductions + changed_row.total_advance;
    changed_row.net_salary = changed_row.base_salary - changed_row.total_deductions;
        
    frm.refresh_field("salary_list");
}

function calculate_present_change(frm, cdt, cdn){
    let changed_row = frappe.get_doc(cdt, cdn); 
    changed_row.present = changed_row.base_present - changed_row.absent;
    changed_row.absent_deductions = (changed_row.base_salary / frm.doc.days) * changed_row.absent;
    frm.refresh_field("salary_list");
}

function updateDaysField(frm){
    if (!frm.doc.from_date ||  !frm.doc.to_date)
        return;
        
    const days = getDiffDays(frm.doc.from_date, frm.doc.to_date);
    frm.set_value("days", days);
}

function getHolidays(frm, holiday_List, from_date, to_date){
    const from_fromatted_date = moment(from_date).format('YYYY-MM-DD');
    const to_fromatted_date = moment(to_date).format('YYYY-MM-DD');
    return holiday_List.filter(x => x.parent == frm.doc.holiday_list && x.holiday_date >= from_fromatted_date && x.holiday_date <= to_fromatted_date);
}

async function calculateSalary(frm){
    
    frm.doc.salary_list = [];
    frm.refresh_field("salary_list");
    
    if (!frm.doc.from_date || !frm.doc.to_date || !frm.doc.company || !frm.doc.holiday_from) {
        frappe.msgprint(__('Please set From Date, To Date, Company, and Holiday Source first.'));
        return;
    }
    
    if(frm.doc.working_hours_calculate == undefined){
        frappe.throw("Please select Working Hours Calculate.");
    }
    
    frappe.show_alert({message: __('Fetching data...'), indicator: 'green'});

    const from_date = frm.doc.from_date;
    const to_date = frm.doc.to_date;
    // Convert to days
    let total_days = getDiffDays(from_date, to_date);
    
    if(total_days <= 0){
          frappe.msgprint({
                title: __('Validation Warning'),
                indicator: 'orange',
                message: __('Please select correct date range.')
            });
        return;
    }
    
    const employees_details = await frappe.db.get_list('Employee', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["status", "=", "Active"],
            ],
            limit:0,
        });
        
    const salary_strucs_assign = await frappe.db.get_list('Salary Structure Assignment', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["docstatus", "=", 1],
                ["from_date", "=", from_date],
            ],
            limit:0,
        });
  
    const salary_strucs_base = await frappe.db.get_list('Salary Structure', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["docstatus", "=", 1],
            ],
            limit:0,
        });
        
    const salary_advance = await frappe.db.get_list('Auto Salary Advance', {
        fields: ['*'],  // Get all fields (use with caution)
        filters:[
            ["docstatus", "=", 1],
            ["from_date", "=", from_date],
        ],
        limit:0,
    });
                        
    let salary_advance_list = [];
    
    if (salary_advance && salary_advance.length > 0) {
        
        //const advance_table = await frappe.db.get_doc("Auto Salary Advance Table", salary_advance[0].name);
        for(let sal of salary_advance){
            const advance_table = await frappe.db.get_doc("Auto Salary Advance", sal.name);
            
            
            salary_advance_list.push(...advance_table.advance_list);
        }
       
    }   

    // if(!salary_strucs_assign || salary_strucs_assign.length == 0){
    //     frappe.msgprint({
    //         title: __('Add Data'),
    //         indicator: 'orange',
    //         message: __('Please add Salary Structure Assignment for at least one employee from ' + from_date),
    //         primary_action: {
    //             label: __('Open Form'),
    //             action: function() {
    //                 frappe.set_route('Form', 'Salary Structure Assignment');
    //             }
    //         }
    //     });
    //     return;
    // }
    
    const attendances = await frappe.db.get_list("Attendance",{
        fields:["*"],
        filters:[
                ["attendance_date",">=", from_date],
                ["attendance_date","<=", to_date],
                ["docstatus", "=", 1]
            ],
            limit:0,
        },
        
    );
    
    if (!attendances || attendances.length === 0) {
        frappe.msgprint({
            title: __('Attendance Records'),
            indicator: 'orange',
            message: __('No attendance found'),
        });
        return;
    }
    
    
    let holiday_List = [];
    
    if(frm.doc.holiday_from == "Holiday List"){
        const holidayList = await frappe.db.get_doc("Holiday List", frm.doc.holiday_list);
        holiday_List = holidayList.holidays;
    }
    else if(frm.doc.holiday_from == "Company"){
        const holiday_comp = await frappe.db.get_list(
                    "Company",{
                        fields:["default_holiday_list"],
                        filters:[
                            ["name", "=", frm.doc.company]
                        ],
                        limit:0,
                    }
                );
                
        if(holiday_comp.length === 0)
        {
            frappe.msgprint(__('Please set holiday company.'));
            return;
        }
        const holidayList = await frappe.db.get_doc("Holiday List", holiday_comp[0].default_holiday_list);
        holiday_List = holidayList.holidays;
    }

    const shift_type_all = await frappe.db.get_list(
        "Shift Type",{
            fields:["end_time", "start_time", "name", "allow_check_in"],
            limit:0,
        }
    );
    
    const employees_list = await frappe.db.get_list(
                    "Employee",{
                            fields:["holiday_list", "name", "ignore_attendance", "one_check_present"],
                            limit:0,
                        }
                    );
                    
    const leave_type_list = await frappe.db.get_list(
                    "Leave Type",{
                            fields:["name","is_lwp", "is_compensatory"],
                            limit:0,
                        }
                    );
                    
    const salary_slips = await frappe.db.get_list('Auto Salary Slip', {
        fields: ['*'],  // Get all fields (use with caution)
        filters:[
            ["docstatus", "=", 1],
            ["from_date", "=", from_date],
        ],
        limit:0,
    });
     const short_leaves = await frappe.db.get_list('Short Leave', {
        fields: ['*'],  // Get all fields (use with caution)
        filters:[
            ["docstatus", "=", 1],
            ["short_leave_date", ">=", from_date],
            ["short_leave_date", "<=", to_date],
        ],
        limit:0,
    });
    frappe.show_alert({message: __('Calculating salaries...'), indicator: 'blue'});
    
    const found_holidays = getHolidays(frm, holiday_List, from_date, to_date)
    let slip_found_count = 0;
    
    // for(let sal of salary_strucs_assign){
    for(let e of employees_details){
    
        var employee = e.employee;
        var employee_name = e.employee_name;
        const one_check = e.one_check_present;
        
        // const slip_found = salary_slips.filter(x => x.employee == sal.employee)
        const slip_found = salary_slips.filter(x => x.employee == employee)
        // if(slip_found.length > 0)
        // {
        //     slip_found_count ++;
        //     continue;
        // }
        
        const filterd_att = attendances.filter(x => x.employee === employee);
        
        const advance_found = salary_advance_list.filter(x => x.employee === employee);
        let total_salary_advances = 0;
        if(advance_found)
        {
            for(let af of advance_found){
                total_salary_advances += af.amount;
            }
        }
        const emps = employees_list.filter(x => x.name === employee);
        if(filterd_att.length === 0 || (emps.length > 0 && emps[0].ignore_attendance) || (emps.length > 0 && emps[0].one_check_present))
        {
            // const salary_doc_excp = salary_strucs_base.filter(y => {
            //     return y.name.toString() === sal.salary_structure.toString();
            // });
            
            // if(salary_doc_excp.length == 0)
            //     continue;
            let present_days = 0
            if (emps.length > 0 && emps[0].ignore_attendance)
            {
                present_days = frm.doc.days;
            }
            else if (emps.length > 0 && emps[0].one_check_present){
                present_days = filterd_att.length + found_holidays.length;
            }
            
            const absents = frm.doc.days - present_days;
            
            // if(emps.length > 0)
            //     absents = emps[0].ignore_attendance ? 0 : frm.doc.days - found_holidays.length;
            
            // const total_salary = (salary_doc_excp[0].total_earning - salary_doc_excp[0].total_deduction);
            const exchange_rate = frm.doc.exchange_rate;
            const total_salary = e.ctc;
            const salary_per_day = total_salary / frm.doc.days;
            const total_advance = parseFloat(total_salary_advances);    
            const absent_deduction = salary_per_day * absents;
            
            console.log('ONLY', employee_name, absent_deduction, filterd_att);
            
            frm.add_child("salary_list", {
                doctype: "Auto Salary Entry Table",
                employee: employee,
                employee_name: employee_name,
                total_leaves: 0,
                holidays: found_holidays.length,
                net_salary: (total_salary - total_advance - absent_deduction) * exchange_rate,
                absent_deductions: absent_deduction * exchange_rate,
                late_deductions: 0,
                total_deductions: (total_advance + absent_deduction) * exchange_rate,
                total_advance: total_advance * exchange_rate,
                present: present_days,
                absent: absents,
                base_present: frm.doc.days,
                // base_salary: salary_doc_excp[0].total_earning - salary_doc_excp[0].total_deduction,
                base_salary: total_salary * exchange_rate,
                parenttype: frm.doctype,
                parentfield: "salary_list"
            });

            continue;
        }
            
        let total_late_enter = 0;
        let total_present_days = 0;
        let total_working_days = 0;
        let total_present_seconds = 0;
        let total_absent_days = 0;
        let total_holidays = 0;
        let total_leaves = 0;
        let total_half_days = 0;
        let working_hours_per_day = 0;
        let total_working_hours_per_day = 0;
        let total_additional_seconds = 0;
        
        let current_date = new Date(from_date);
        let to_date_js = new Date(to_date);
        let emp_holidays_fetched = false;
        
        while (current_date <= to_date_js) {
            
            let current_fromatted_date = moment(current_date).format('YYYY-MM-DD');
            
            const current_att = filterd_att.filter(y => {
                return y.attendance_date.toString() == current_fromatted_date.toString();
            });
            // const current_att = filterd_att.filter(x => x.attendance_date == current_fromatted_date);
            
            let is_holiday = false;
            const holidies = holiday_List.filter(x => x.parent == frm.doc.holiday_list && x.holiday_date == current_fromatted_date);
            is_holiday = holidies.length > 0;
            
            if(is_holiday)
            {
                total_holidays ++;
            }
            else if(current_att.length > 0){
                
                const att = current_att[0]
                
                if(att.status === "Work From Home"){
                     total_present_days ++;
                }
                else if(att.status === "On Leave")
                {
                    // total_present_days ++;
                    total_leaves ++;
                    
                    const lwps = leave_type_list.filter(x => x.name == att.leave_type)
                    
                    if(lwps.length > 0 && lwps[0].is_lwp && !lwps[0].is_compensatory){
                        total_absent_days ++;
                    }
                }
                else if(att.status === "Half Day")
                {
                    const half_in_holidies = holiday_List.filter(x => x.parent == frm.doc.holiday_list && x.holiday_date == current_fromatted_date);
                    if(half_in_holidies.length > 0)
                        total_present_days ++;
                    else{
                        
                        total_present_days += 1;
                        // total_half_days += 0.5;
                        
                        const emp_short_leaves = short_leaves.filter(x => x.employee === employee && x.short_leave_date === current_fromatted_date);
                        let total_short_leaves = 0;
                        
                        if(emp_short_leaves.length > 0)
                        {
                            for(let sl of emp_short_leaves)
                            {
                                total_short_leaves += sl.short_leave_amount_in_minuts * 60;
                            }
                        }
                        
                        total_late_enter += Math.max(0,14400 - total_short_leaves);
                        console.log(current_date,employee_name,'total_late_enter:', current_late_time, 'total_short_leaves:', total_short_leaves);
                    }
                }
                else if(att.status === "Present"){
                    total_present_seconds = total_present_seconds + timeStringToSeconds(att.total_time);
                    total_present_days ++;
                    
                    const current_late_time = timeStringToSeconds(att.late_enter_time) + timeStringToSeconds(att.early_exit_time);
                    
                    const shift_type_filtered = shift_type_all.filter(x => x.name == att.shift);
                    extra_time_seconds = timeStringToSeconds(att.extra_time);
                    total_attendance_time = timeStringToSeconds(att.total_time);
                    total_with_extra_time_hours = (extra_time_seconds + total_attendance_time)/60/60;
                    if(total_with_extra_time_hours > 8)
                    {
                        total_additional_seconds += Math.max(total_with_extra_time_hours - 8, 0) * 60*60;
                    }

                    if(!shift_type_filtered || shift_type_filtered.length <= 0)
                    {
                        total_working_hours_per_day = total_working_hours_per_day + (7 / 60/60);
                        total_working_days ++;
                    }else
                    {
                        const shift_type = shift_type_filtered[0];
                                                      
                        if(current_late_time > shift_type.allow_check_in * 60)
                        {
                            
                            const emp_short_leaves = short_leaves.filter(x => x.employee === employee && x.short_leave_date === current_fromatted_date);
                            let total_short_leaves = 0;
                    
                            if(emp_short_leaves.length > 0)
                            {
                                for(let sl of emp_short_leaves)
                                {
                                    total_short_leaves += sl.short_leave_amount_in_minuts * 60;
                                }
                            }
                            
                            total_late_enter += Math.max(0,current_late_time - total_short_leaves);
                        }
                        if(frm.doc.working_hours_calculate == "Working Time"){
                            const hours = (timeStringToSeconds(att.total_time) + timeStringToSeconds(att.late_enter_time) + timeStringToSeconds(att.early_exit_time))/60/60;
                            total_working_hours_per_day = total_working_hours_per_day + hours;
                        }
                        
                        
                        total_working_days ++;
                    }
                   
                }
                else if(att.status === "Absent"){
                    total_absent_days ++;
                }
                
            }else
            {
                let holiday_emp = [];

                // =============================================
                if (frm.doc.holiday_from === "Holiday List"){
                    const holidies = holiday_List.filter(x => x.parent == frm.doc.holiday_list && x.holiday_date == current_fromatted_date);
                    is_holiday = holidies.length > 0;
                }
                //==============================================
                else if(frm.doc.holiday_from === "Company")
                {
                    const holidies = holiday_List.filter(x => x.holiday_date == current_fromatted_date);
                    is_holiday = holidies.length > 0;
                }
                //==============================================
                else if (frm.doc.holiday_from == "Employee"){
                    if(!emp_holidays_fetched)
                    {
                        // holiday_emp = await frappe.db.get_list(
                        // "Employee",{
                        //         fields:["holiday_list"],
                        //         filters:[
                        //             ["name", "=", sal.employee]
                        //         ],
                        //         limit:0,
                        //     }
                        // )
                        
                        holiday_emp = employees_list.filter(x => x.employee == employee);
                    }
                 
                    if(holiday_emp.length > 0){
                        const holidies = holiday_List.filter(x => x.parent == holiday_emp[0].holiday_list && x.holiday_date == current_fromatted_date);
                        is_holiday = holidies.length > 0;
                    }
                    else{
                        if(frm.doc.req_for_all)
                        {
                            frappe.throw("Please assign default holiday list to ({employee} - {employee_name}) company")
                        }
                            
                    }
                }
                
                if(is_holiday)
                {
                    // total_present_days ++;
                    total_holidays ++;
                }
                else
                {
                    total_absent_days ++;
                }
            }
            
            current_date.setDate(current_date.getDate() + 1);
        }
        if(total_working_days == 0)
            total_working_days = 1
        
        working_hours_per_day = total_working_hours_per_day / total_working_days;
        
        if(frm.doc.working_hours_calculate == "8 Hours"){
            working_hours_per_day = 8;
        }
        
        total_working_seconds = working_hours_per_day * 3600;
        // const salary_doc = salary_strucs_base.filter(y => {
        //     return y.name.toString() === sal.salary_structure.toString();
        // });
        
        // const total_salary = salary_doc[0].total_earning - salary_doc[0].total_deduction;
        total_salary = e.ctc;
        
        if(total_working_seconds <= 0)
            total_working_seconds = 8*60*60;
        
        const salary_per_second = total_salary / total_days / total_working_seconds;
        const absent_deductions = salary_per_second * (total_absent_days*total_working_seconds);
        
        // const emp_short_leaves = short_leaves.filter(x => x.employee === employee);
        // let total_short_leaves = 0;

        // if(emp_short_leaves.length > 0)
        // {
        //     for(let sl of emp_short_leaves)
        //     {
        //         total_short_leaves += sl.short_leave_amount_in_minuts * 60;
        //     }
        // }
        
        let total_lates_seconds = total_late_enter;
        
        // if(total_late_enter - total_short_leaves > 0)
        //     total_lates_seconds = total_late_enter - total_short_leaves;
        
        // console.log("Name", employee_name, "Late: ", total_lates_seconds, "Wh:", total_working_seconds);
        // console.log("Name", employee_name, "Late Dud: ", (salary_per_second * total_lates_seconds));

        
        const late_deductions =  (salary_per_second * total_lates_seconds) + (salary_per_second * total_half_days * total_working_seconds);
        const additional_allownace = total_additional_seconds * salary_per_second;
        const final_salary =  total_salary - (late_deductions + absent_deductions) - total_salary_advances;
        
        console.log(
            "EMP ID:",employee, 
            "Name:",employee_name, 
            "Present:", total_present_days, 
            'total_late_enter', total_late_enter,
            // 'total_short_leaves', total_short_leaves,
            "Salary:", salary_per_second,
            "Absent:",total_absent_days, 
            "Holidays:",total_holidays, 
            "Half Days",total_half_days,
            "total_deductions", parseFloat(late_deductions + absent_deductions),
            "Leaves:",total_leaves
            );
        const exchange_rate = frm.doc.exchange_rate;
        let row = {
            doctype: "Auto Salary Entry Table",
            employee: employee,
            employee_name: employee_name,
            leaves: total_leaves,
            holidays: total_holidays,
            net_salary: parseFloat(final_salary) * exchange_rate,
            absent_deductions: parseFloat(absent_deductions) * exchange_rate,
            late_deductions: parseFloat(late_deductions) * exchange_rate,
            total_deductions: parseFloat(late_deductions + absent_deductions + total_salary_advances) * exchange_rate,
            total_advance: parseFloat(total_salary_advances) * exchange_rate,
            additional_allowance: parseFloat(additional_allownace) * exchange_rate,
            present: frm.doc.days - total_absent_days,
            absent: total_absent_days,
            base_present: frm.doc.days,
            base_salary: total_salary * exchange_rate, // Keep original for reference
            parenttype: frm.doctype,
            parentfield: "salary_list",
        };
        frm.add_child("salary_list", row);
    }
    frm.refresh_field("salary_list");
    
    // if(slip_found_count == salary_slips.length & salary_slips.length > 0)
    // {
    //     frappe.msgprint({
    //         title: __('Salary Calculations'),
    //         indicator: 'orange',
    //         message: __('تم صرف رواتب لجميع الموظفين في هذا الشهر'),
    //     });
    // }
}

function timeStringToSeconds(timeStr) {
    const parts = timeStr.split(':');
    return (+parts[0]) * 3600 + (+parts[1]) * 60 + (+parts[2]);
}

function getDiffDays(from_date, to_date){
     
    let d1 = new Date(from_date);
    let d2 = new Date(to_date);
    
    let diffInMs = d2 - d1;
            
    // Convert to days
    return (diffInMs / (1000 * 60 * 60 * 24)) + 1;
}

function updateFieldStatus(frm){
    var select_fieldname = 'holiday_from';   
    var selected_value = frm.doc[select_fieldname];

    frm.toggle_display('company', selected_value === 'Company');
    frm.set_df_property('company', 'reqd', selected_value === 'Company');
    
    frm.toggle_display('holiday_list', selected_value === 'Holiday List');
    frm.set_df_property('holiday_list', 'reqd', selected_value === 'Holiday List');
    
    frm.toggle_display('req_for_all', selected_value === 'Employee');
    frm.set_df_property('req_for_all', 'reqd', selected_value === 'Employee');
}