// Copyright (c) 2026, moneer and contributors
// For license information, please see license.txt

frappe.query_reports["Multi-Period Attendance"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"fieldtype": "Date",
			"label": "From Date",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"fieldtype": "Date",
			"label": "To Date",
			"reqd": 1
		},
		{
			"fieldname": "employee",
			"fieldtype": "Link",
			"label": "Employee",
			"options": "Employee"
		},
		{
			"fieldname": "department",
			"fieldtype": "Link",
			"label": "Department",
			"options": "Department"
		},
		{
			"fieldname": "company",
			"fieldtype": "Link",
			"label": "Company",
			"options": "Company"
		},
		{
			"fieldname": "shift_type",
			"fieldtype": "Link",
			"label": "Shift Type",
			"options": "Shift Type"
		},
		{
			"fieldname": "status",
			"fieldtype": "Select",
			"label": "Status",
			"options": "\nPresent\nAbsent\nOn Leave\nHalf Day\nWork From Home"
		},
		{
			"fieldname": "show_period_details",
			"fieldtype": "Check",
			"label": "Show Period Details",
			"default": 0
		}
	]
};
