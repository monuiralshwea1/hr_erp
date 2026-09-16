// Copyright (c) 2026, Shumul. All rights reserved.
// HR ERP Payroll Settings — واجهة إعدادات الرواتب المخصصة
// زر لتوليد الإضافي من الحضور مباشرة من صفحة الإعدادات

frappe.ui.form.on("HR ERP Payroll Settings", {
	refresh: function (frm) {
		if (frm.doc.enable_overtime_generation) {
			frm.add_custom_button(__("Generate Overtime Timesheets"), function () {
				let d = new frappe.ui.Dialog({
					title: __("Generate Overtime Timesheets"),
					fields: [
						{
							fieldname: "start_date",
							fieldtype: "Date",
							label: __("Start Date"),
							reqd: 1,
							default: frappe.datetime.month_start(),
						},
						{
							fieldname: "end_date",
							fieldtype: "Date",
							label: __("End Date"),
							reqd: 1,
							default: frappe.datetime.month_end(),
						},
					],
					primary_action_label: __("Generate"),
					primary_action: function (values) {
						frappe.call({
							method: "hr_erp.hrms_erp.payroll_integration.overtime_timesheet.generate_overtime_timesheets",
							args: {
								start_date: values.start_date,
								end_date: values.end_date,
							},
							freeze: true,
							freeze_message: __("Generating..."),
							callback: function (r) {
								if (r.message) {
									frappe.show_alert({
										message: r.message.message,
										indicator: "green",
									});
								}
							},
						});
						d.hide();
					},
				});
				d.show();
			});
		}
	},
});
