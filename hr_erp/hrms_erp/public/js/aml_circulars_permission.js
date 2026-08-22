frappe.ui.form.on('AML Circulars', {
	refresh(frm) {
	    refresh_fields(frm, frm.doc.is_private);
		// your code here
	},
	is_private: function(frm){
	    refresh_fields(frm, frm.doc.is_private);
	},
	validate: function(frm) {
	    console.log("Validate");
	    console.log(frm.doc.attachments);
        (frm.doc.attachments || []).forEach(file => {
            frappe.db.set_value("File", file.name, "is_private", 0);
            console.log(file.name);
        });
    }

})

function refresh_fields(frm, is_private){
    frm.set_df_property('only_to_department', 'reqd', is_private);
    frm.toggle_display('only_to_department', is_private);
    
    if(is_private)
        frm.doc.only_to_department = "الامتثال - SH";
    else 
        frm.doc.only_to_department = "
        
    frm.refresh_field("only_to_department");
}