frappe.ui.form.on('Issue', {
	refresh(frm) {
	   console.log(frm.doc.subject == undefined, frm.doc.department == null, frm.doc.issue_type == null);
	   if(frm.doc.subject != undefined && frm.doc.department != null && frm.doc.issue_type != null)
	   {
	       set_fields(frm);
	   }
	   // if(frm.docstatus == 0)
	   // {
	   //     set_fields(frm);
	   // }

	}
})

async function set_fields(frm)
{
    const user = frappe.session.user;
        
        
        // Get the employee record for current user
        const employeeData = await frappe.db.get_list('Employee', {
            filters: { user_id: user },
            fields: ['name', 'department'],
            limit: 1
        });
    
        if (!employeeData.length) {
            frappe.msgprint('No employee record linked to your user.');
            return;
        }
        
        const department = employeeData[0].department;
        set_form_read_only(frm, frm.doc.department != department);
}

// --- Helper function to make the code cleaner ---
function set_form_read_only(frm, should_be_read_only) {
    // Loop through all fields in the form's dictionary
    
    for (const field of frm.fields) {
        // Set the 'read_only' property for each field. 1 = true, 0 = false.
        frm.set_df_property(field.df.fieldname, 'read_only', should_be_read_only ? 1 : 0);
    }
    // Also disable the save button for a better user experience
    // frm.page.set_primary_action_label(__("Save")); // Reset label first
    // frm.page.set_primary_action_icon("fa-save");
    // frm.disable_save();
    // if(!should_be_read_only){
    //     frm.page.clear_primary_action();
    // }
}