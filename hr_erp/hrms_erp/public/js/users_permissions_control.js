frappe.ui.form.on('Users Permissions Control', {
	refresh(frm) {
		frm.add_custom_button(__('Fetch Data'), function() {
                // Your button action here
                fetch_data(frm);
            });
	}
})

async function fetch_data(frm){
    emps = await frappe.db.get_list("Employee", 
        {
            fields:["name","employee_name","company","show_other_employees_i_approve","department","user_id", "user_id.is_inspector","designation", "is_manager", "leave_approver", "inspector"],
            filters:[
                ["user_id","!=","],
                ["status","=","Active"]
            ],
            limit:0
        }
    );

    frm.doc.perm_list = [];
    
    for(let e of emps){

       frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.user_id,
                module: "Employee",
                value_for: e.name,
            }); 
        frm.add_child("perm_list", {
            doctype: "Project Permission Table",
            user: e.user_id,
            module: "Company",
            value_for: e.company,
        });
        frm.add_child("perm_list", {
            doctype: "Project Permission Table",
            user: e.user_id,
            module: "Department",
            value_for: e.department,
        }); 

        frm.add_child("perm_list", {
            doctype: "Project Permission Table",
            user: e.user_id,
            module: "User",
            value_for: e.user_id,
            applicable_for: "Inbox Messages"
        }); 
        
        if(e.is_inspector)
        {
            frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.user_id,
                module: "Department",
                value_for: "All Departments",
            }); 
        }
    
        if(e.inspector)
        {
            frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.inspector,
                module: "Employee",
                value_for: e.name,
                hide_descendants: true
            }); 
        }
        
        if(e.designation && !e.is_manager)
        {
            frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.user_id,
                module: "Designation",
                value_for: e.designation,
            }); 
        }
        
        if(e.show_other_employees_i_approve){
            
            const approval_emps = emps.filter(x => x.leave_approver == e.user_id)
            for(let app_emp of approval_emps){
                frm.add_child("perm_list", {
                    doctype: "Project Permission Table",
                    user: e.user_id,
                    module: "Employee",
                    value_for: app_emp.name,
                    hide_descendants: true
                }); 
            }
            frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.user_id,
                module: "Department",
                value_for: "All Departments"
            }); 
        }
        
        if(e.is_manager){
            frm.add_child("perm_list", {
                doctype: "Project Permission Table",
                user: e.user_id,
                module: "User",
                value_for: e.user_id,
                applicable_for: "Internal Message"
            }); 
            
            if(!e.show_other_employees_i_approve)
            {
                const dep_emps = emps.filter(x => x.department == e.department && x.leave_approver == e.user_id)
                for(let de of dep_emps){
                    frm.add_child("perm_list", {
                        doctype: "Project Permission Table",
                        user: e.user_id,
                        module: "Employee",
                        value_for: de.name,
                    }); 
                }
            }
        }
    }
    
    frm.refresh_field("perm_list");
}