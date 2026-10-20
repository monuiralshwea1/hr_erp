// Copyright (c) 2026, Shumul. All rights reserved.
// Salary Deductions Report — filters
// التسميات عربية مباشرة (لغة النظام ar) لضمان ظهورها ثابتة

frappe.query_reports["Salary Deductions Report"] = {
	filters: [
		{
			fieldname: "from_date",
			fieldtype: "Date",
			label: "من تاريخ",
			reqd: 1,
			default: frappe.datetime.month_start()
		},
		{
			fieldname: "to_date",
			fieldtype: "Date",
			label: "إلى تاريخ",
			reqd: 1,
			default: frappe.datetime.month_end()
		},
		{
			fieldname: "employee",
			fieldtype: "Link",
			label: "الموظف",
			options: "Employee"
		},
		{
			fieldname: "department",
			fieldtype: "Link",
			label: "القسم",
			options: "Department"
		},
		{
			fieldname: "company",
			fieldtype: "Link",
			label: "الشركة",
			options: "Company"
		},
		{
			fieldname: "status",
			fieldtype: "Select",
			label: "الحالة",
			options: "\nAll\nDraft\nSubmitted",
			default: "Submitted"
		}
	]
};
