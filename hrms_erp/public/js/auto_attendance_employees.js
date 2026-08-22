frappe.ui.form.on('Auto Attendance', {
	refresh(frm) {
		updateListState(frm);
		if(frm.doc.docstatus == 0)
		{
		    
    		frm.add_custom_button("Process Attendance Range", async function() {
    		    if(frm.doc.attendance_results.length == 0){
    		        frappe.msgprint("لا توجد بيانات لحفظها");
    		        frm.save("Submit");
    		        return;
    		    }
	            
               const start = 0;
               const end = Math.min(frm.doc.attendance_results.length, frm.doc.saved_records);
               
               
            //   frm.set_value("saved_records", end);
                await frappe.call({
                    method: "save_auto_attendance", // your Server Script API
                    args: {
                        doctype: frm.doctype,
                        docname: frm.docname,
                        start: start,
                        end: end
                    },
                    freeze: true,
                    freeze_message: "Processing attendance records...",
                    callback: function(r) {
                        frappe.msgprint(r.message);
                        
                    }
                });
                
                frm.set_value("calculated", false);
                frappe.msgprint("جاري التحقق من وجود بصمات متبقية");
                frm.save();
                
            });
		}

	},
	all_employees: function(frm) {
	   updateListState(frm);
    },
})

function updateListState(frm){
    frm.toggle_display('employees',  !frm.doc.all_employees);
    frm.set_df_property('employees', 'reqd', !frm.doc.all_employees);
}