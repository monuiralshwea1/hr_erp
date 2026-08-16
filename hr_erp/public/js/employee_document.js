// hr_erp: Employee Document client enhancements
frappe.ui.form.on("Employee Document", {
	refresh(frm) {
		if (frm.doc.expiry_date) {
			const today = frappe.datetime.get_today();
			const expiry = frappe.datetime.str_to_obj(frm.doc.expiry_date);
			const today_obj = frappe.datetime.str_to_obj(today);
			const days = Math.ceil((expiry - today_obj) / (1000 * 60 * 60 * 24));
			if (days < 0) {
				frm.set_value("status", "منتهي");
			} else if (days <= 30) {
				frm.set_value("status", "قريب الانتهاء");
			} else {
				frm.set_value("status", "ساري");
			}
			if (days >= 0 && days <= 30) {
				frm.dashboard.set_headline(
					__("⚠️ تنتهي هذه الوثيقة خلال {0} يوم", [days]),
					"yellow"
				);
			}
		}
	},
});
