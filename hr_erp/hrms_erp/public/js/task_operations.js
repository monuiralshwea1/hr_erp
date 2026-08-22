frappe.ui.form.on('Task', {
	refresh(frm) {
		// your code here
	},
	show_issue_btn: function(frm){
	   // frappe.set_route('Form', 'Issue', frm.doc.issue);
        if(!frm.doc.issue)
            return;
        const url = frappe.urllib.get_full_url(
        `/app/issue/${frm.doc.issue}`
        );
        window.open(url, "_blank");
	},
	show_reference_issue: function(frm){
	    
        if(!frm.doc.ref_id)
            return;

        window.open(`https://taskbridge.craftsilicon.com/project/5676f202-da2f-4b48-a7b3-c5a59e32bc40?query=${frm.doc.ref_id}`, "_blank");
	}
})