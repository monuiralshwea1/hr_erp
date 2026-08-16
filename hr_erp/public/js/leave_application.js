// hr_erp: Leave Application client enhancements
frappe.ui.form.on("Leave Application", {
	refresh(frm) {
		// show employee balance hint in sidebar
		if (frm.doc.employee && frm.doc.leave_type) {
			frappe.call({
				method: "hrms.hr.doctype.leave_application.leave_application.get_leave_balance_on",
				args: {
					employee: frm.doc.employee,
					date: frm.doc.from_date || frappe.datetime.get_today(),
					leave_type: frm.doc.leave_type,
				},
				callback(r) {
					if (r.message != null) {
						frm.dashboard.add_comment(
							__("رصيد الإجازة الحالي: {0} يوم", [r.message]),
							"blue",
							true
						);
					}
				},
			});
		}
	},

	employee(frm) {
		if (!frm.doc.employee) return;
		frappe.call({
			method: "hrms.hr.api.get_leave_approver_and_department",
			args: { employee: frm.doc.employee },
			callback(r) {
				if (r.message) {
					const m = r.message;
					if (!frm.doc.leave_approver) frm.set_value("leave_approver", m.leave_approver);
					if (!frm.doc.department) frm.set_value("department", m.department);
				}
			},
		});
	},
});
