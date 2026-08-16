// hr_erp: Expense Claim client enhancements
frappe.ui.form.on("Expense Claim", {
	onload(frm) {
		if (!frm.doc.posting_date) {
			frm.set_value("posting_date", frappe.datetime.get_today());
		}
	},
	refresh(frm) {
		if (frm.doc.employee && frm.doc.employee_name && !frm.doc.expense_approver) {
			// set default expense approver from employee
			frappe.call({
				method: "frappe.client.get_value",
				args: {
					doctype: "Employee",
					filters: { name: frm.doc.employee },
					fieldname: ["expense_approver"],
				},
				callback(r) {
					if (r.message && r.message.expense_approver) {
						frm.set_value("expense_approver", r.message.expense_approver);
					}
				},
			});
		}
	},
});
