app_name = "hr_erp"
app_title = "hrms-erp"
app_publisher = "moneer"
app_description = "HRMS Arabic customization app"
app_email = "moneer@gmail.com"
app_license = "mit"

# Includes in <head>
# ------------------
app_include_css = "/assets/hr_erp/css/hr_style.css"
app_include_js = "/assets/hr_erp/js/hr_common.js"

# include js in doctype views
doctype_js = {
	"Leave Application": "public/js/leave_application.js",
	"Attendance": "public/js/attendance.js",
	"Expense Claim": "public/js/expense_claim.js",
	"Job Applicant": "public/js/job_applicant.js",
	"Employee Document": "public/js/employee_document.js",
}

# Override DocType controllers for multi-period shift support
# -----------------------------------------------------------
override_doctype_class = {
	"Shift Type": "hr_erp.hrms_erp.multi_period_shift.shift_type_override.CustomShiftType",
	"Employee Checkin": "hr_erp.hrms_erp.multi_period_shift.employee_checkin_override.CustomEmployeeCheckin",
}

# Installation
# ------------
after_install = "hr_erp.hrms_erp.install.after_install"

# after_migrate
# -------------
after_migrate = [
	"hr_erp.hrms_erp.multi_period_shift.custom_fields.create_custom_fields",
	"hr_erp.hrms_erp.payroll_integration.custom_fields.create_custom_fields",
	"hr_erp.hrms_erp.payroll_integration.default_data.create_default_data",
]

# Document Events
# ---------------
doc_events = {
	"Employee": {
		"before_save": "hr_erp.hrms_erp.api.smart_defaults.before_employee_save",
		"on_update": "hr_erp.hrms_erp.api.smart_defaults.on_employee_update",
	},
	"Leave Application": {
		"validate": "hr_erp.hrms_erp.api.smart_defaults.validate_leave",
		"on_submit": "hr_erp.hrms_erp.api.smart_defaults.on_leave_submit",
	},
	"Attendance": {
		"validate": "hr_erp.hrms_erp.api.smart_defaults.validate_attendance",
	},
	"Expense Claim": {
		"validate": "hr_erp.hrms_erp.api.smart_defaults.validate_expense_claim",
	},
	"Job Applicant": {
		"validate": "hr_erp.hrms_erp.api.smart_defaults.validate_job_applicant",
	},
	"Salary Structure Assignment": {
		"validate": "hr_erp.hrms_erp.api.smart_defaults.validate_salary_assignment",
		"on_submit": "hr_erp.hrms_erp.api.payroll.on_salary_assignment_submit",
	},
	"Workspace": {
		"validate": "hr_erp.hrms_erp.api.workspace_utils.fix_workspace",
	},
	"Salary Slip": {
		"validate": [
			"hr_erp.hrms_erp.payroll_integration.late_absence_deduction.apply_late_absence_deduction",
			"hr_erp.hrms_erp.payroll_integration.overtime_earning.apply_overtime_earning",
		],
	},
}

# Scheduled Tasks
# ---------------
scheduler_events = {
	"cron": {
		"10 23 * * *": [
			"hr_erp.hrms_erp.payroll_integration.biostar_sync.add_checkin_logs_for_current_day"
		],
		"0 3 * * *": [
			"hr_erp.hrms_erp.payroll_integration.biostar_sync.check_for_yesterday_logs"
		],
	},
}
