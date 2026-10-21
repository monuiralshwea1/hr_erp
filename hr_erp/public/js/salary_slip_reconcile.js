// Copyright (c) 2026, Shumul. All rights reserved.
// زر "إعادة احتساب الخصومات" في كشف الراتب
// ---------------------------------------------------------------
// يعيد حساب خصم التأخير وخصم الغياب لكشف الراتب الحالي من بيانات الحضور
// (نفس منطق الـhook الذي يعمل عند إنشاء القسيمة).
// ملاحظة: لا يُنشئ أي قيد محاسبي — القسيمة تبقى كما هي حالتها.

frappe.ui.form.on("Salary Slip", {
	refresh(frm) {
		if (frm.is_new() || frm.doc.docstatus !== 1) {
			return;
		}

		frm.add_custom_button(__("Reconcile Deductions"), () => {
			frappe.confirm(
				__(
					"Recalculate late and absence deductions for this salary slip from the current attendance data?<br><br>This updates the slip only (no accounting entries are created)."
				),
				() => {
					frm.call({
						method:
							"hr_erp.hrms_erp.payroll_integration.auto_recalc.reconcile_salary_slip",
						args: { slip_name: frm.doc.name, apply: 1 },
						freeze: true,
						freeze_message: __("Reconciling deductions..."),
						callback(r) {
							const result = r.message || {};
							frm.reload_doc();
							frappe.show_alert({
								message:
									__("Deductions reconciled") +
									" — late: " +
									(frappe.utils.flt(result.late_minutes) || 0) +
									" min, absence: " +
									(frappe.utils.flt(result.absent_days) || 0) +
									" day(s), updated slips: " +
									(result.slips_updated || 0),
								indicator: "green",
							});
						},
						error() {
							frappe.msgprint({
								title: __("Reconciliation Failed"),
								message: __("Could not reconcile the deductions. Check the Error Log."),
								indicator: "red",
							});
						},
					});
				}
			);
		});
	},
});
