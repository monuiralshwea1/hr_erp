frappe.ui.form.on('Leave Application', {
	refresh(frm) {
	    if(frm.doc.docstatus == 1)
	        return;
	        
        hide_leave_balance_header(frm);
        get_employees_has_fingerprint(frm);
        
	},
	employee: function(frm){
	    hide_leave_balance_header(frm);
	    get_employees_has_fingerprint(frm);
	    populate_leaves_table(frm);
	},
	before_save: function(frm) {
        populate_leaves_table(frm);
    },
    after_save: function(frm) {
        // populate_leaves_table(frm);
    },
    from_date: function(frm) {
	    get_employees_has_fingerprint(frm);
	    populate_leaves_table(frm);
	    frm.set_value('replacement_employee', undefined);
	},
	to_date: function(frm) {
	    populate_leaves_table(frm);
	    frm.set_value('replacement_employee', undefined);
	},
	
	leave_type: function(frm) {
	    populate_leaves_table(frm);
	    hide_leave_balance_header(frm);
	    get_employees_has_fingerprint(frm);
	    validate_replacement_employee(frm);
	}
})

async function get_emp_leave_balance(frm, emp_id, date)
{
    var report_data = null;
    await frappe.call({
            method: "frappe.desk.query_report.run",
            args: {
                report_name: "Custom Employee Leave Balance Summary V2",
                filters: {
                    "date": date,
                    "company": frm.doc.company,
                    "employee": frm.doc.employee
                }
            },
            callback: function(r) {
                if (r.message && r.message.result) {
                    report_data = r.message.result;
                    // console.log("Report Data", report_data[0]);
                }
            }
        });
    console.log(data);
    var data = report_data.filter(x => x.employee == emp_id)
    
    return data[0];
}

async function validate_replacement_employee(frm){
      
    const leave_type_doc = await frappe.db.get_value('Leave Type', { name: frm.doc.leave_type },'replacement_required');
    
    // Extract the value safely
    const replacement_required = leave_type_doc ? leave_type_doc.message.replacement_required : null;
    
    frm.set_df_property('replacement_employee', 'reqd', replacement_required);
    frm.set_df_property('replacement_employee', 'read_only', !replacement_required);
}

function get_leave_name(frm)
{
    if(frm.doc.leave_type == "اجازة سنوية")
        return "اجازة_سنوية";
        
    
    return ";
}

// async function update_js_table(frm, data, value)
// {
//     let target_data = data;
//     let result = null;
    
//     // Target the table inside the form wrapper
//     $(frm.wrapper).find('.table-bordered tbody tr').each(function() {
//         // Get the first cell (td)
//         let first_td = $(this).find('td').first();
        
//         // Clean the text (remove extra whitespace)
//         let cell_text = first_td.text().trim();
    
//         if (cell_text === target_data) {
//             result = $(this).find('td')[5]; // Returns the jQuery object of the matching row
//             return false;    // This breaks the jQuery .each() loop early
//         }
//     });
    
//     if (result) {
//         console.log("Found row:", result);
//     }
    
//     result.text(value);
// }


function hide_leave_balance_header(frm)
{
    $('.form-dashboard').hide();
}

async function get_employees_has_fingerprint(frm)
{
    // frm.set_df_property('replacement_employee', 'read_only', 1);
    frappe.set
    if(frm.doc.employee == undefined || frm.doc.from_date == undefined)
        return;
    
    var employees_list = []
    await frappe.call({
        method: 'get_employees_has_fingerprint',
        args:{
            department: frm.doc.department,
            att_date: frm.doc.from_date,
            employee: frm.doc.employee,
        },
        callback: function(r) {
            employees_list = r.results;
        }
    });
    
    const employeeNames = employees_list.map(e => e.name);
    
    frm.set_query('replacement_employee', function() {
        return {
            filters: [
                ["name", "in", employeeNames]
            ]
        };
    });
    
    // frm.set_df_property('replacement_employee', 'read_only', 0);
    
    // console.log(employees_list)
}

// async function calculate_used_short_leaves(frm)
// {
//     frm.set_df_property('leave_balance', 'hidden', 1);
    
//     if(frm.doc.to_date == undefined)
//         return;
    
//     const prev_short_leaves = await frappe.db.get_list('Short Leave', {
//         fields: ['*'],  // Get all fields (use with caution)
//         filters:[
//             ["docstatus", "=", 1],
//             ["leave_type", "=", frm.doc.leave_type],
//             ["employee", "=", frm.doc.employee],
//         ],
//         limit:0,
//     });
//     let total_amount = 0;
    
//     for(let lev of prev_short_leaves){
//         total_amount += lev.short_leave_amount_in_minuts / lev.shift_duration_minutes / 60;
//     }
//     var leave_balance_data = await get_emp_leave_balance(frm, frm.doc.employee, frm.doc.from_date);
//     var last_leave_balance = leave_balance_data[get_leave_name(frm)]
    
//     if(last_leave_balance != undefined)
//     {
//         frm.set_value('leave_balance', last_leave_balance);
//         frm.set_value('short_leaves_used', total_amount);
//         frm.refresh_field('short_leaves_used');
//         frm.refresh_field('leave_balance');
        
//         // update_js_table(frm, frm.doc.leave_type, last_leave_balance);
//     }

//     frm.set_df_property('leave_balance', 'hidden', 0);
// }

async function populate_leaves_table(frm) {
    // 1. Safety check for required fields
    if (!frm.doc.employee || !frm.doc.from_date) {
        return;
    }
        
    // 2. Fetch the custom report data
    const response = await frappe.call({
        method: "frappe.desk.query_report.run",
        args: {
            report_name: "Custom Employee Leave Balance Summary V2",
            filters: {
                "company": "بنك الشمول عدن",
                "date": frm.doc.from_date, // Note: ensure frm.doc.from_date exists on your form
                "employee": frm.doc.employee
            }
        }
    });
    
    const reportData = response.message;
    if (!reportData) return;
    
    let raw_columns =  [
        {"fieldname": "اجازة_سنوية", "label" : "إجازة سنوية"},
        {"fieldname": "اجازة_مرضية", "label" : "إجازة مرضية"},
        {"fieldname": "اجازة_تعويضية", "label" : "إجازة تعويضية"},
        {"fieldname": "SL", "label" : "الاذونات/يوم"},
    ];
    
    let user_lang = frappe.boot.lang; 
    if(user_lang == "en")
        raw_columns.unshift({"fieldname": "employee_name", "label" : "Employee Name"});
    else
        raw_columns.unshift({"fieldname": "اسم_الموظف", "label" : "اسم الموظف"});
    
    const rows = reportData.result || [];
    console.log(raw_columns, rows)
    let html_content = ``;
        
    if (rows && rows.length > 0) {
        // Normalize columns (Frappe columns can be strings "Label:Type:Width" or objects)
        const columns = raw_columns.map(col => {
            if (typeof col === 'string') {
                const parts = col.split(':');
                return { label: parts[0], fieldname: parts[1] || parts[0] };
            }
            return { label: col.label || col.title, fieldname: col.fieldname };
        });

        html_content = `
            <div class="table-responsive">
                <table class="table table-bordered table-striped table-hover" style="margin-top: 10px;">
                    <thead>
                        <tr style="background-color: #f8f9fa;">
        `;

        // Render headers dynamically based on the report's actual columns
        columns.forEach(col => {
            html_content += `<th>${col.label}</th>`;
        });

        html_content += `
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        // Loop through the report rows
        rows.forEach(row => {
            html_content += `<tr>`;
            
            columns.forEach((col, index) => {
                let val = ";
                
                // Handle both array-of-objects and array-of-arrays formats
                if (Array.isArray(row)) {
                    val = row[index];
                } else if (typeof row === 'object') {
                    val = row[col.fieldname];
                }
                
                // Fallback for null/undefined values
                if (val === null || val === undefined) {
                    val = ";
                }

                // Optional: Make "Leave Type" or ID values look nice if they appear in your report
                if (col.fieldname === 'name' || col.label === 'ID') {
                    val = `<a href="/app/leave-application/${val}"><strong>${val}</strong></a>`;
                }

                html_content += `<td>${val}</td>`;
            });

            html_content += `</tr>`;
        });
        
        html_content += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        // Fallback message if the report is empty
        html_content = `
            <div class="text-muted text-center" style="padding: 20px; border: 1px dashed #d1d8dd; border-radius: 4px;">
                No leave records found.
            </div>
        `;
    }

    // 3. Render the HTML content inside the target HTML field
    frm.set_df_property('leaves_table_html', 'options', html_content);
    frm.refresh_field('leaves_table_html');
        
    if(frm.doc.leave_type)
    {
        total_short_leaves = reportData.result[0]["SL"];
        frm.set_value('short_leaves_used', total_short_leaves);
        
        let result = frm.doc.leave_type.replace(" ", "_");
        leave_balance = reportData.result[0][result];
        
        console.log(leave_balance);
        
        frm.set_value('leave_balance', leave_balance);
        
        frm.refresh_field('short_leaves_used');
        frm.refresh_field('leave_balance');
    }

}