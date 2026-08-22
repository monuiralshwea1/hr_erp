frappe.ui.form.on('Special Shift Assignment', {
	refresh(frm) {
        
        if(frm.doc.days_of_week.length == 0)
		    fill_daysOfWeek_table(frm);
		
		frm.set_df_property('days_of_week', 'reqd', 1);
		
		
		 update_employees_table_status(frm);
	},
	onload: function(frm) {
	    let currentYear = frappe.datetime.nowdate().substr(0,4);

	    if(frm.doc.from_date == undefined)
	    {
	        let from_date = currentYear + "-01-01";
            frm.set_value('from_date', from_date);
	    }
	        
        if(frm.doc.to_date == undefined)
        {
            let to_date = currentYear + "-12-31";
            frm.set_value('to_date', to_date);
        }
    },
    all_employees: function(frm){
        frm.set_df_property('employees', 'reqd', !frm.doc.all_employees);
    },
    btn_fetch_managers: function(frm){
        if(frm.doc.include_employees == "Include All")
            return;
            
        fetch_managers(frm)
    },
    include_employees: function(frm)
    {
        update_employees_table_status(frm);
    }
})

async function update_employees_table_status(frm)
{
    if(frm.doc.include_employees == "Include All")
            frm.doc.employees = [];
            
    frm.refresh_field("employees");
    frm.set_df_property('employees', 'reqd', frm.doc.include_employees != "Include All");
}

async function fetch_managers(frm){
    frm.doc.employees = [];
     const managers = await frappe.db.get_list('Employee', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["is_manager","=",1]
                ],
            limit:0,
        });
        
    for(var m of managers)
    {
        let row = {
            doctype: "Special Shift Assignment Employee Table",
            employee: m.name,
            employee_name: m.employee_name,
        };
        
        frm.add_child("employees", row);
        frm.refresh_field("employees");
    }
    console.log(frm.doc.days_of_week);
}

async function fill_daysOfWeek_table(frm){
    frm.doc.days_of_week = [];
     const days = await frappe.db.get_list('Day of the Week', {
            fields: ['*'],  // Get all fields (use with caution)
            limit:0,
        });
        
    for(var d of days)
    {
        let row = {
            doctype: "Days of Week Table",
            day_name: d.name
        };
        
        frm.add_child("days_of_week", row);
        frm.refresh_field("days_of_week");
    }
    console.log(frm.doc.days_of_week);
}