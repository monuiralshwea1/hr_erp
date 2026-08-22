frappe.ui.form.on('Short Leave', {
    
	refresh: async function(frm) {

	    if(frm.doc.docstatus == 1)
	        return;
        
        if(frm.doc.employee)
        {
            const { message  } = await frappe.db.get_value(
                "Employee",
                { user_id: frappe.session.user },
                "name"
            );
            
            if(message.name != frm.doc.employee)
            {
                get_last_allocated_leave(frm);
            }
        }else
        {
            get_last_allocated_leave(frm);
        }
	},
	validate: function(frm){
	    
	    if(frm.doc.leave_balance_minutes <= 0 || frm.doc.short_leave_amount_in_minuts > frm.doc.leave_balance_minutes){
	        frappe.throw(__("Insufficient leave balance. You do not have enough minutes available for this short leave request."));
	    }
	},
	employee: function(frm){
	     get_last_allocated_leave(frm);
	},
    shift_type: function(frm) {
        // calculate_total_hours(frm);
        get_last_allocated_leave(frm);
    },
    leave_type: function(frm) {
        get_last_allocated_leave(frm);
    },
    short_leave_date: function(frm){
        get_last_allocated_leave(frm);
    },
    short_leave_amount_in_minuts: function(frm) {
        let value = frm.doc.short_leave_amount_in_minuts;
        if(frm.doc.short_leave_amount_in_minuts <= 0)
        {
            value = 0;
        }
        else if(frm.doc.short_leave_amount_in_minuts >= frm.doc.leave_balance_minutes)
        {
            value = frm.doc.leave_balance_minutes;
        }
        frm.set_value('short_leave_amount_in_minuts', value);
        frm.refresh_field('short_leave_amount_in_minuts');

    },
})

async function calculate_leave_balance_minutes(frm){
    
     const prev_short_leaves = await frappe.db.get_list('Short Leave', {
        fields: ['*'],  // Get all fields (use with caution)
        filters:[
            ["docstatus", "=", 1],
            ["leave_type", "=", frm.doc.leave_type],
            ["employee", "=", frm.doc.employee],
        ],
        limit:0,
    });
    
    let total_amount = 0;
    
    for(let lev of prev_short_leaves){
        total_amount += lev.short_leave_amount_in_minuts;
    }
    
    const balance_minutes = (frm.doc.leave_balance * frm.doc.shift_duration_minutes * 60) - total_amount;
    // console.log(total_amount);
    frm.set_value('leave_balance_minutes', balance_minutes);
    frm.refresh_field('leave_balance_minutes');
}

async function get_last_allocated_leave(frm){
    
    if(!frm.doc.employee || !frm.doc.short_leave_date || !frm.doc.leave_type)
        return;
 
    const response = await frappe.call({
        method: "frappe.desk.query_report.run",
        args: {
            report_name: "Custom Employee Leave Balance Summary V2",
            filters: {
                "company": "بنك الشمول عدن",
                "date": frm.doc.short_leave_date,
                "employee": frm.doc.employee
            }
        }
    });
    const reportData = response.message;
    
    const leave_column = reportData.columns.find(col => col.label === frm.doc.leave_type || col.fieldname === frm.doc.leave_type);
    const leave_balance = reportData.result[0][leave_column.fieldname];
    const prev_short_leaves = reportData.result[0]["SL"];
    
    // console.log("Leave: ", leave_column);
    // console.log("Leave Balance: ", reportData.result[0]);
    
    frm.set_value('leave_balance', leave_balance);
    frm.refresh_field('leave_balance');
    
    const balance_minutes = (frm.doc.leave_balance * frm.doc.shift_duration_minutes * 60);
    frm.set_value('leave_balance_minutes', balance_minutes);
    frm.refresh_field('leave_balance_minutes');
    
    frm.set_intro(null);
    
    if (!leave_balance) {
        frm.set_intro(__('لا يوجد رصيد اجازات لهذا الموظف'), 'red');
    }else{
        frm.set_intro(__('Current Leave Balance: {0}', [frm.doc.leave_balance]), 'green');
        frm.set_intro(__('Total consumed permissions previously: {0}', [prev_short_leaves]), 'green');
    }
    
    // const last_allocated_leave = await frappe.db.get_list('Leave Allocation', {
    //     fields: ['*'],  // Get all fields (use with caution)
    //     filters:[
    //         ["docstatus", "=", 1],
    //         ["leave_type", "=", frm.doc.leave_type],
    //         ["employee", "=", frm.doc.employee],
    //         ["from_date", "<=", frm.doc.short_leave_date],
    //         ["to_date", ">=", frm.doc.short_leave_date],
    //     ],
    //     limit:1,
    // });
    // console.log(last_allocated_leave)
    // if(!last_allocated_leave || last_allocated_leave.length == 0)
    // {
    //     frm.set_value('leave_allocation', ");
    // }else
    // {
    //     frm.set_value('leave_allocation', last_allocated_leave[0].name);
    //     await calculate_total_leaves(frm);
    //     await calculate_leave_balance_minutes(frm);
    // }
    // frm.set_df_property('short_leave_amount_in_minuts', 'read_only', frm.doc.leave_balance <= 0);
    // frm.refresh_field('leave_allocation');

    // if (!last_allocated_leave || last_allocated_leave.length === 0) {
    //     frm.set_intro(__('لا يوجد رصيد اجازات لهذا الموظف'), 'red');
    // }else{
        
    //     frm.set_intro(__('رصيد الاجازات الحالي: ' +frm.doc.leave_balance), 'green');
    // }
}

async function calculate_total_hours(frm){
    const shift = await frappe.db.get_doc('Shift Type', frm.doc.shift_type);
    const time_to_minutes = (t) => {
        const [h, m, s] = t.split(':').map(Number);
        return h * 60 + m + s/60;
    }

    const start_minutes = time_to_minutes(shift.start_time);
    const end_minutes = time_to_minutes(shift.end_time);

    // Calculate duration in minutes
    let duration_hours = (end_minutes - start_minutes) / 60;
    
    // console.log('Duration in minutes:', duration_hours);
    // frm.set_value('shift_duration_minutes', duration_hours);
    // frm.refresh_field('shift_duration_minutes');
    
    await calculate_leave_balance_minutes(frm);
}

// async function calculate_total_leaves(frm){
//     const leave_allocation = await frappe.db.get_doc('Leave Allocation', frm.doc.leave_allocation);
//     console.log(leave_allocation);
//     frm.set_value('leave_balance', leave_allocation.total_leaves_allocated);
//     frm.refresh_field('leave_balance');
// }