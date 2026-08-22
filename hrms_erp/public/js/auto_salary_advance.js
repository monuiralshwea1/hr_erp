frappe.ui.form.on('Auto Salary Advance', {
	 refresh: function(frm) {

        if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Calculate Advance'), function() {
                // Your button action here
                calculateAdvance(frm);
            });
        }
        
        // filter_deduction_advance(frm);
    },
    
    use_deduction: function(frm){
        get_deductions(frm);
    },
    from_date: function(frm){
        get_deductions(frm);
    }
})

async function get_deductions(frm){
    frm.doc.deduction_list = [];
    if(frm.doc.use_deduction)
    {
        const deductions_advance = await frappe.db.get_list('Auto Salary Advance', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["docstatus", "=", 1],
                ["from_date", "=", frm.doc.from_date],
            ],
            limit:0,
        });
        console.log(deductions_advance);
        for(let ded of deductions_advance){
            
            let newRow = frm.add_child("deduction_list", {
                doctype: "Deduction Advance Table",
                advance: ded.name,
                title: ded.title
            });
            
        }
    }
    
    frm.refresh_field("deduction_list");
}


async function calculateAdvance(frm){
    
    if (!frm.doc.from_date || !frm.doc.title) {
        frappe.msgprint(__('Please fill required fields.'));
        return;
    }
    frm.doc.advance_list = [];
    frm.refresh_field("advance_list");
    const from_date = frm.doc.from_date;
    
    // const salary_strucs_assign = await frappe.db.get_list('Salary Structure Assignment', {
    //     fields: ['*'],  // Get all fields (use with caution)
    //     filters:[
    //         ["docstatus", "=", 1],
    //         ["from_date", "=", from_date],
    //     ],
    //     limit:0,
    // });
    
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
    // }
    let all_deductions = [];
    for(let ded of frm.doc.deduction_list){
        const x = await frappe.db.get_doc('Auto Salary Advance', ded.advance);
        all_deductions.push(...x.advance_list);
    }
    
    const employees = await frappe.db.get_list('Employee', {
        fields: ['*'],  // Get all fields (use with caution)
        filters:[
            ["status", "=", "Active"],
        ],
        limit:0,
    });
    
    //  const salary_strucs = await frappe.db.get_list('Salary Structure', {
    //     fields: ['*'],  // Get all fields (use with caution)
    //     filters:[
    //         ["docstatus", "=", 1],
    //     ],
    //     limit:0,
    // });
    
    // for(let sal of salary_strucs_assign){
    for(let emp of employees){
        let advance = 0;
        if(frm.doc.calc_method === "Percentage"){
            //const salary_doc = await frappe.db.get_doc("Salary Structure", sal.salary_structure)
            // const salary_doc = salary_strucs.filter(x => x.name == sal.salary_structure)[0];
            // if(!salary_doc)
            //     continue;
            
            // const earnings = salary_doc.total_earning;
            
            // const deductions = salary_doc.total_deduction;
            
            // const total_salary = earnings - deductions;
            const total_salary = emp.ctc;
            
            if(frm.doc.value > 0)
                advance = total_salary * (frm.doc.value/100);
        }
        else if(frm.doc.calc_method === "Amount"){
            advance = frm.doc.value;
        }
        
        // const advance_deductions = all_deductions.filter(x => x.employee == sal.employee);
        const advance_deductions = all_deductions.filter(x => x.employee == emp.employee);
        console.log(advance_deductions);
        let total_deductions = 0;
        if(advance_deductions)
        {
            for(let d of advance_deductions){
                total_deductions += d.amount;
            }
            console.log(emp, total_deductions, advance_deductions);
        }
        
        
        
        let newRow = frm.add_child("advance_list", {
            doctype: "Auto Salary Advance Table",
            employee: emp.employee,
            employee_name: emp.employee_name,
            // salary_structure: sal.name,
            sal_advance: advance,
            deductions: total_deductions,
            amount: advance - total_deductions,
            base_salary: emp.ctc,
        });
        
        
        
    }
    frm.refresh_field("advance_list");
}