// hr_erp: Job Applicant client enhancements
frappe.ui.form.on("Job Applicant", {
	refresh(frm) {
		if (frm.doc.email_id && !frm.doc.applicant_name) {
			frm.set_value("applicant_name", frm.doc.email_id.split("@")[0]);
		}
		if (frm.is_new() && !frm.doc.status) {
			frm.set_value("status", "Open");
		}
	},
});
