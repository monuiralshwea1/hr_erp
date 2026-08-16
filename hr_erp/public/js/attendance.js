// hr_erp: Attendance client enhancements
frappe.ui.form.on("Attendance", {
	onload(frm) {
		// default date to today
		if (!frm.doc.attendance_date) {
			frm.set_value("attendance_date", frappe.datetime.get_today());
		}
	},
	refresh(frm) {
		// mark present/absent quick buttons
		if (frm.is_new()) {
			frm.add_custom_button(
				__("حاضر"),
				() => {
					frm.set_value("status", "Present");
					frm.set_value("in_time", null);
				},
				__("إجراء")
			);
			frm.add_custom_button(
				__("غائب"),
				() => {
					frm.set_value("status", "Absent");
				},
				__("إجراء")
			);
		}
	},
});
