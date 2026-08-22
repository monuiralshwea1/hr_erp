frappe.ui.form.on('Permission Change Request', {
	async refresh(frm) {
	    const all_emps = await frappe.db.get_list('Employee', {
            fields: ['*'],  // Get all fields (use with caution)
            filters:[
                ["user_id", "=", frappe.session.user],
            ],
            limit:0,
        });
        
        // const role_profile = await frappe.db.get_list('User', {
        //     fields: ['*'],  // Get all fields (use with caution)
        //     filters:[
        //         ["name", "=", frappe.session.user],
        //     ],
        //     limit:0
        // });
        
        if(all_emps == undefined || all_emps.length == 0)
        {
            frappe.throw("المستخدم غير مربوط بموظف");
        }
        
        var emp = all_emps[0];
        
 		read_only_fields(frm,'employee_details_section', frm.doc.workflow_state != 'First Request');
 		
 		const is_hr = !(frm.doc.workflow_state == 'HR Pending' && emp.department == 'ادارة الموارد البشرية - SH');
 		read_only_fields(frm,'hr_approval_section', is_hr);
 		
        read_only_fields(frm,'financing_details_section', !(frm.doc.workflow_state == 'Financial Pending' && emp.department == 'الادارة المالية - SH'));
        read_only_fields(frm,'it_details_section', !(frm.doc.workflow_state == 'IT Pending' && emp.department == 'IT - SH'));
	    
	    not_required_fields(frm);
	    always_read_only(frm);
	    request_type_fields(frm);
	    await auto_assign_fields(frm, emp);
	    

	},
	request_type: function (frm)
	{
	    request_type_fields(frm);
	},
	before_save: async function(frm)
	{
	    if(frm.doc.workflow_state == 'First Request')
	    {
	        const roles = await frappe.db.get_list('CBS Roles', {
    fields: ['finance_approval'],
    filters: {
        name: frm.doc.new_role
    },
    limit: 1
});

const financeApproval = roles.length ? roles[0].finance_approval : 0;

console.log(financeApproval);
     		//if(frm.doc.new_role == "صندوق")
     		if(financeApproval)
     		{
     		    frm.set_value("direct_to", "المالية");
     		}else{
      		    frm.set_value("direct_to", "الايتي");
     		}
	    }

	}
})


function request_type_fields(frm)
{
    const is_required = frm.doc.request_type != "فتح حساب";
	    
    // frm.set_df_property('client_id', 'reqd', is_required);
    // frm.set_df_property('client_id', 'read_only', !is_required);
    
    if(!is_required)
    {
        frm.set_value('client_id', '');
        frm.set_value('old_role', 'لا يوجد');
    }
}



async function auto_assign_fields(frm, emp)
{
    if(frm.doc.workflow_state == 'First Request')
    {
        // console.log(frm.doc.owner, frappe.session.user);
        
        // const all_managers = await frappe.db.get_list('Employee', {
        //     fields: ['name'],  // Get all fields (use with caution)
        //     ignore_permissions: true
        //     // filters:[
        //     //     ["user_id", "=", frappe.session.user],
        //     // ],
        //     // limit:0,
        // });
        
        // await frappe.call({
        //     method: 'get_employee_managers',
        //     args:{
        //         user_id: frm.doc.owner,
        //     },
        //     callback: function(r) {
        //         managers_list = r.results;
        //     }
        // });
        
        // console.log(all_managers);
        // if(all_managers.length > 0)
        // {
            
        // }
        frm.set_value('manager_user', frappe.session.user);
    }
    if(frm.doc.workflow_state == 'HR Pending' && emp.department == 'ادارة الموارد البشرية - SH')
        frm.set_value('hr_user', frappe.session.user);
    if(frm.doc.workflow_state == 'Financial Pending' && emp.department == 'الادارة المالية - SH')
        frm.set_value('finance_user', frappe.session.user);
    if(frm.doc.workflow_state == 'IT Pending' && emp.department == 'IT - SH')
        frm.set_value('it_user', frappe.session.user);

    frm.set_value()
}


function not_required_fields(frm)
{
    frm.set_df_property('manager_user', 'reqd', false);
    frm.set_df_property('description', 'reqd', false);
    // frm.set_df_property('cbs_currencies', 'reqd', false);
    
    frm.set_df_property('department', 'reqd', false);
    frm.set_df_property('employee_user', 'reqd', false);
    frm.set_df_property('designation', 'reqd', false);
    frm.set_df_property('employee_name', 'reqd', false);
    frm.set_df_property('client_id', 'reqd', false);
}

function always_read_only(frm)
{
    frm.set_df_property('manager_user', 'read_only', true);
    
    frm.set_df_property('department', 'read_only', true);
    frm.set_df_property('employee_user', 'read_only', true);
    frm.set_df_property('designation', 'read_only', true);
    frm.set_df_property('employee_name', 'read_only', true);

}

function read_only_fields(frm,section_name, read_only)
{
    const target_section = section_name; 
    let is_inside_section = false;

    frm.meta.fields.forEach(df => {

        // 1. Start locking when we hit our target section break
        if (df.fieldname === target_section) {
            is_inside_section = true;
            return; 
        }

        // 2. Stop locking when we hit the NEXT section break
        if (is_inside_section && df.fieldtype === 'Section Break') {
            is_inside_section = false;
        }

        // 3. Apply the read_only property to everything in between
        if (is_inside_section) {

            if(df.fieldtype != "Section Break" && df.fieldtype != "Column Break")
            {
                frm.set_df_property(df.fieldname, 'read_only', read_only);
                frm.set_df_property(df.fieldname, 'reqd', !read_only);
            }
        }
    });
}