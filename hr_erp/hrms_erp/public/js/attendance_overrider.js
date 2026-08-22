frappe.ui.form.on('Attendance Overrider', {

	 refresh: function(frm) {
	     	refreshFields(frm);
	 },
	all_employees: function(frm){
	  refreshFields(frm);
        frm.refresh_field("section_general");
        frm.refresh_field("section_table");
	}
})

function refreshFields(frm){
    
      
	    frm.toggle_display('section_general', frm.doc.all_employees);
	    frm.toggle_display('section_table', !frm.doc.all_employees);
	    
        frm.set_df_property('from_date', 'reqd', frm.doc.all_employees);
        frm.set_df_property('to_date', 'reqd', frm.doc.all_employees);
        frm.set_df_property('default_shift', 'reqd', frm.doc.all_employees);
        frm.set_df_property('from_status', 'reqd', frm.doc.all_employees);
        frm.set_df_property('to_status', 'reqd', frm.doc.all_employees);
        
        frm.set_df_property('employees', 'reqd', !frm.doc.all_employees);

}