// Copyright (c) 2026, Shumul and contributors
// For license information, please see license.txt

frappe.query_reports["Biometric Period Attendance"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": __("من تاريخ"),
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": __("إلى تاريخ"),
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": __("الموظف"),
			"options": "Employee"
		},
		{
			"fieldname": "branch",
			"fieldtype": "Link",
			"label": __("الفرع"),
			"options": "Branch"
		},
		{
			"fieldname": "department",
			"fieldtype": "Link",
			"label": __("القسم"),
			"options": "Department"
		},
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": __("الشركة"),
			"options": "Company"
		},
		{
			"fieldname": "shift_type",
			"fieldtype": "Link",
			"label": __("الدوام"),
			"options": "Shift Type"
		}
	],
	"onload": function(report) {
		const company = frappe.boot.user && frappe.boot.user.defaults
			? frappe.boot.user.defaults.company
			: null;
		if (company) {
			frappe.query_reports["Biometric Period Attendance"].filters
				.filter(f => f.fieldname === "company")
				.forEach(f => f.default = company);
		}
	}
};