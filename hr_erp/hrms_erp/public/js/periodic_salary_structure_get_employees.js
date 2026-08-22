frappe.ui.form.on('Periodic Salary Structure', {
	refresh(frm) {
		// your code here
		if (frm.doc.docstatus === 0) {
            frm.add_custom_button(__('Get Employees'), function() {
                // Your button action here
                getEmployees(frm);
            });
        }
	},
})

frappe.ui.form.on('Periodic Salary Structure Table', {
   employee: function(frm, cdt, cdn) {
        console.log("Employee field changed in row:", cdn);
        let currentRowData = locals[cdt][cdn]; // This gets the entire row object
        if (currentRowData) {
            console.log("--- Full Row Data when 'employee' changed ---");
            console.log(JSON.parse(JSON.stringify(currentRowData)));
            // Access all other columns:
            // console.log("Current Amount:", currentRowData.amount);
            // console.log("Current Formula:", currentRowData.formula);
        }
    },
})

async function getEmployees(frm){
    frm.doc.employees = [];
    frm.refresh_field("employees");
    const salary_structures = await frappe.db.get_list('Salary Structure', {
        fields: ['name', 'total_earning', 'currency', 'level', 'grade', 'class','is_active'],  // Get all fields (use with caution)
        filters: [
            ["docstatus", "=", 1],    
            ["is_active", "=", "Yes"],   
        ],
        limit:0,
    });
    
    if(!salary_structures || salary_structures.length === 0){
        frappe.msgprint({
                title: __('Validation Warning'),
                indicator: 'orange',
                message: __('No salary structure found.')
            });
    }
    const employees = await frappe.db.get_list('Employee', {
        fields: ['*'],  // Get all fields (use with caution)
        filters: [
            ["status", "=", "Active"],   
        ],
        limit:0,
    });
    if(!employees || employees.length === 0){
         frappe.msgprint({
                title: __('Validation Warning'),
                indicator: 'orange',
                message: __('No employees found.')
            });
    }
    
    for(let e of employees){
        if(e.grade == null || e.level == null || e.class == null){
            continue;
        }
        
        let s = salary_structures.filter(x => x.grade == e.grade && x.class == e.class && x.level == e.level);
        console.log(s);
        if(!s || s.length === 0)
        {
            continue;
        }
        let newRow = frm.add_child("employees", {
            doctype: "Periodic Salary Structure Table",
            employee: e.name,
            employee_name: e.employee_name,
            salary_structure: s[0].name,
            amount: s[0].total_earning,
            currency: s[0].currency
        });
        frm.refresh_field("employees");
    }
    
    
}