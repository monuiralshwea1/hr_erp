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
	"AML Circulars": "public/js/aml_circulars_permission.js",
	"Attendance Overrider": "public/js/attendance_overrider.js",
	"Auto Attendance": "public/js/auto_attendance_employees.js",
	"Auto Salary Advance": "public/js/auto_salary_advance.js",
	"Auto Salary Entry": "public/js/auto_salary_entry_holiday_select.js",
	"Clients Sanctions Lists": "public/js/clients_sanctions_lists.js",
	"Inbox Messages": "public/js/inbox_messages.js",
	"Internal Message": "public/js/internal_message_validations.js",
	"Issue": "public/js/issue_perm.js",
	"Leave Application": "public/js/leave_application_with_short_leaves.js",
	"Long Term Advance": "public/js/long_term_advance_calculations.js",
	"Periodic Salary Structure": "public/js/periodic_salary_structure_get_employees.js",
	"Permission Change Request": "public/js/permission_change_request.js",
	"Short Leave": "public/js/short_leave.js",
	"Special Shift Assignment": "public/js/special_shift_assignment.js",
	"Task": ["public/js/task_operations.js", "public/js/task_lost.js"],
	"User Group Permissions": "public/js/emp_group_perm_script.js",
	"Users Permissions Control": "public/js/users_permissions_control.js",
	"Shift Type": "public/js/shift_type_multi_period.js",
		"Leave Application": "public/js/leave_application.js",
		"Attendance": "public/js/attendance.js",
		"Expense Claim": "public/js/expense_claim.js",
		"Job Applicant": "public/js/job_applicant.js",
		"Employee Document": "public/js/employee_document.js",
}

# Override DocType Classes
# -------------------------
override_doctype_class = {
	"Shift Type": "hr_erp.hrms_erp.multi_period_shift.shift_type_override.CustomShiftType",
	"Employee Checkin": "hr_erp.hrms_erp.multi_period_shift.employee_checkin_override.CustomEmployeeCheckin",
}

# Installation
# ------------
after_install = "hr_erp.hrms_erp.install.after_install"
after_migrate = [
	"hr_erp.hrms_erp.multi_period_shift.custom_fields.create_custom_fields",
]
# To auto-seed setup data + demo employees on install, uncomment below:
# after_install = "hr_erp.hrms_erp.install.after_install_with_seed"

# Document Events
# ---------------
doc_events = {
	"Attendance Overrider": {
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.attendance_overrider_submit",
	},
	"Auto Attendance": {
		"before_save": "hr_erp.hrms_erp.api.server_scripts.auto_attendance_calculate_v2",
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.auto_attendance_script",
	},
	"Auto Leave Allocation": {
		"after_save": "hr_erp.hrms_erp.api.server_scripts.auto_leave_allocation_save",
		"on_cancel": "hr_erp.hrms_erp.api.server_scripts.auto_leave_allocation_cancel",
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.auto_leave_allocation_submit",
	},
	"Auto Salary Entry": {
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.auto_salary_entry_submit",
	},
	"Auto Shift Assign": {
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.auto_shift_assign_calculate_v3",
	},
	"Clients Sanctions Lists": {
		"before_save": "hr_erp.hrms_erp.api.server_scripts.clients_sanctions_lists",
	},
	"Inbox Messages": {
		"before_insert": "hr_erp.hrms_erp.api.server_scripts.inbox_messages_naming_series",
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.inbox_messages_confirmation",
	},
	"Internal Message": {
		"after_save": "hr_erp.hrms_erp.api.server_scripts.internal_message_submit",
		"before_insert": "hr_erp.hrms_erp.api.server_scripts.internal_message_naming_series",
		"before_save": "hr_erp.hrms_erp.api.server_scripts.get_employees_internal_message",
	},
	"Leave Application": {
		"before_submit": ["hr_erp.hrms_erp.api.server_scripts.leave_application_validation", "hr_erp.hrms_erp.api.server_scripts.leave_application_with_short_leaves"],
	},
	"Long Term Advance": {
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.long_term_advance_submit",
	},
	"Manual Attendance": {
		"on_cancel": "hr_erp.hrms_erp.api.server_scripts.manual_attendance_cancel",
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.manual_attendance_submit",
	},
	"Periodic Salary Structure": {
		"on_submit": "hr_erp.hrms_erp.api.server_scripts.periodic_salary_structure_submit",
	},
	"Project": {
		"before_save": "hr_erp.hrms_erp.api.server_scripts.project_naming",
	},
	"Short Leave": {
		"before_submit": "hr_erp.hrms_erp.api.server_scripts.short_leave_validation",
	},
	"Task": {
		"after_save": "hr_erp.hrms_erp.api.server_scripts.task_close_issue",
		"validate": "hr_erp.hrms_erp.api.server_scripts.issue_linked_tasks",
	},
	"Users Permissions Control": {
		"after_save": "hr_erp.hrms_erp.api.server_scripts.users_permissions_control",
	},
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
}

# Permission Query Conditions
permission_query_conditions = {
	"Permission Change Request": "hr_erp.hrms_erp.api.server_scripts.permission_change_request",
}

# Fixtures - Export from production site alshumul.newsmart.local
fixtures = [
	# --- DocTypes (48 custom) ---
	{
		"dt": "DocType",
		"filters": [
			["name", "in", [
				"AML Circulars",
				"App Version Control",
				"Attachments List",
				"Attendance Overrider",
				"Attendance Overrider Table",
				"Auto Attendance",
				"Auto Attendance Table",
				"Auto Attendance Temp Table",
				"Auto Leave Allocation",
				"Auto Leave Allocation Table",
				"Auto Salary Advance",
				"Auto Salary Advance Table",
				"Auto Salary Entry",
				"Auto Salary Entry Table",
				"Auto Salary Slip",
				"Auto Shift Assign",
				"Auto Shift Assign Table",
				"Branch Management Circulars",
				"CBS Roles",
				"Clients Sanctions Lists",
				"Customer Details",
				"Customer Not Matched Data",
				"Days of Week Table",
				"Day of the Week",
				"Deduction Advance Table",
				"Departments List",
				"Employees List",
				"Employee Alternating Shift Config",
				"Employee Document",
				"Fadhel Screen",
				"Inbox Messages",
				"Internal Message",
				"Long Term Advance",
				"Long Term Advance Table",
				"Manual Attendance",
				"Manual Attendance Checks Table",
				"PCR Accounts",
				"PCR IT Details",
				"Periodic Salary Structure",
				"Periodic Salary Structure Table",
				"Permission Change Request",
				"Project Permission Table",
				"Short Leave",
				"Special Shift Assignment",
				"Special Shift Assignment Employee Table",
				"Standard Operating Procedure",
				"Test",
				"Users Permissions Control",
			# Multi-Period Shift Management
			"Shift Period",
			"Biometric Device",
			"Attendance Period Detail",
			"Multi Period Settings",
			]]
		]
	},
	# --- Client Scripts (21 from production) ---
	{
		"dt": "Client Script",
		"filters": [
			["name", "in", [
				"Auto Salary Entry Holiday Select",
				"Inbox Messages",
				"Clients Sanctions Lists",
				"Permission Change Request",
				"Internal Message Validations",
				"Leave Application WIth Short Leaves",
				"Auto Salary Advance",
				"Auto Attendance Employees",
				"Users Permissions Control",
				"Short Leave",
				"Special Shift Assignment",
				"AML Circulars Permission",
				"Task Operations",
				"Periodic Salary Structure Get Employees",
				"Issue List",
				"Issue Perm",
				"Auto Leave Allocation Calcuation",
				"Task Lost",
				"Long Term Advance Calculations",
				"Attendance Overrider",
				"Emp Group Perm Script",
			]]
		]
	},
	# --- Server Scripts (42 from production) ---
	{
		"dt": "Server Script",
		"filters": [
			["name", "in", [
				"Auto Shift Assign Calculate V3",
				"Auto Shift Assign Calculate V2",
				"Auto Attendance Calculate V2",
				"Clients Sanctions Lists",
				"Permission Change Request",
				"Save Auto Attendance",
				"Auto Shift Assign Calculate",
				"Auto Attendance Calculate",
				"Internal Message Naming Series",
				"Internal Message Resubmit",
				"Disable Users",
				"Internal Message Cancel Linked Inbox",
				"Internal Messages Validation",
				"Internal Message Get Employees API",
				"Task Close Issue",
				"Inbox Messages Confirmation",
				"Internal Message Signature",
				"Internal Message Submit",
				"Users Permissions Control",
				"Auto Leave Allocation Save",
				"Short Leave Validation",
				"Leave Application Validation",
				"Auto Attendance Script",
				"Send Notification",
				"Internal Messages Delete",
				"Auto Leave Allocation Cancel",
				"Auto Leave Allocation Submit",
				"Manual Attendance Cancel",
				"Inbox Messages Naming Series",
				"Update Doc Field",
				"Manual Attendance Submit",
				"Leave Application WIth Short Leaves",
				"Auto Salary Entry Submit",
				"Auto Shift Assign Submit",
				"Periodic Salary Structure Submit",
				"Long Term Advance Submit",
				"Issue Linked Tasks",
				"Project Naming",
				"Auto Shift Assign Test",
				"Attendance Overrider Submit",
				"Auto Salary Entry Save",
				"Auto Attendance Cancel",
			]]
		]
	},
	# --- Custom Fields (76 from production) ---
	{
		"dt": "Custom Field",
		"filters": [
			["name", "in", [
				"Leave Encashment-cost_center",
				"Advance Taxes and Charges-cost_center",
				"Communication-company",
				"Email Account-company",
			    "Employee-job_applicant",
				"Terms and Conditions-hr",
				"Timesheet-salary_slip",
				"Task-total_expense_claim",
				"Project-total_expense_claim",
				"Employee-payroll_cost_center",
				"Employee-salary_cb",
				"Employee-shift_request_approver",
				"Employee-column_break_45",
				"Employee-leave_approver",
				"Employee-expense_approver",
				"Employee-approvers_section",
				"Employee-health_insurance_no",
				"Employee-health_insurance_provider",
				"Employee-health_insurance_section",
				"Employee-default_shift",
				"Employee-grade",
				"Employee-employment_type",
				"Designation-skills",
				"Designation-required_skills_section",
				"Designation-appraisal_template",
				"Department-expense_approvers",
				"Department-leave_approvers",
				"Department-shift_request_approver",
				"Department-approvers",
				"Department-leave_block_list",
				"Department-column_break_9",
				"Department-payroll_cost_center",
				"Department-section_break_4",
				"Company-default_payroll_payable_account",
				"Company-column_break_10",
				"Company-default_employee_advance_account",
				"Company-default_expense_claim_payable_account",
				"Company-hr_settings_section",
				"Company-hr_and_payroll_tab",
				"Address-is_your_company_address",
				"Contact-is_billing_contact",
				"Address-tax_category",
			# Multi-Period Custom Fields
			"Shift Type-enable_multi_period",
			"Shift Type-shift_periods",
			"Shift Type-attendance_day_start_time",
			"Shift Type-multi_period_section",
			"Shift Type-multi_period_summary_section",
			"Shift Type-total_working_period_hours",
			"Shift Type-total_break_period_hours",
			"Attendance-attendance_period_details",
			"Attendance-total_late_minutes",
			"Attendance-total_overtime_hours",
			"Attendance-approved_overtime_hours",
			"Attendance-multi_period_section",
			"Employee Checkin-biometric_device",
			"Employee Checkin-original_timestamp",
			"Employee Checkin-biometric_device_section",
				# [DISABLED - to re-enable, remove # below]
				# "Clients Sanctions Lists-workflow_state",
				# "Permission Change Request-workflow_state",
				# "AML Circulars-workflow_state",
				# "Short Leave-workflow_state",
				# "Internal Message-workflow_state",
			]]
		]
	},
	# --- Reports (21 from app files) ---
	{
		"dt": "Report",
		"filters": [
			["name", "in", [
				"Addresses And Contacts",
				"Attendance Summary V2",
				"Audit System Hooks",
				"Auto Salary Advance Report",
				"Auto Salary Slip Report",
				"Conversation Replies Report",
				"Custom Employee Leave Balance Summary",
				"Custom Employee Leave Balance Summary V2",
				"Employees Details",
				"Figureprint Summary",
				"Fingerprint Device Events",
				"Fingerprint Device Events Advanced",
				"Fingerprint Device Events V2",
				"Issues activity",
				"Issue Test Report",
				"nnn",
				"Review",
				"Shift Summary",
				"Shift Summary V2",
				"Taken Leaves",
				"Users Role",
			]]
		]
	},
	# --- Workflows (3 from production) ---
	{
		"dt": "Workflow",
		"filters": [
			["name", "in", [
				"Clients Sanctions Lists",
				"Permission Change Request Flow",
				"Short Leave Flow",
			]]
		]
	},
	# --- Workflow States (12 from production) ---
	{
		"dt": "Workflow State",
		"filters": [
			["name", "in", [
				"Pending",
				"First Request",
				"Completed",
				"HR Pending",
				"Financial Pending",
				"IT Pending",
				"Cancel",
				"Retrieved",
				"Under Review",
				"Waiting",
				"Rejected",
				"Approved",
			]]
		]
	},
	# --- Workspaces (10 hr-erpc) ---
	{
		"dt": "Workspace",
		"filters": [
			["name", "in", [
				"Shumul - HR",
				"Shumul Employee",
				"Audit and compliance",
				"Internal Requests",
				"Internal Messages",
				"Fadhel",
			]]
		]
	},
	# --- Dashboard Charts (73 from install.py) ---
	{
		"dt": "Dashboard Chart",
		"filters": [
			["name", "in", [
				"رصيد الصناديق",
				"تقرير بحساب الصناديق",
				"Profit and Loss",
				"Warehouse wise Stock Value",
				"Oldest Items",
				"Completed Operation",
				"Grievance Type",
				"Top Customers",
				"Budget Variance",
				"Sales Order Trends",
				"Top Suppliers",
				"Purchase Order Trends",
				"Employee Advance Status",
				"Department wise Expense Claims",
				"Claims by Type",
				"Expense Claims",
				"Employees by Age",
				"Department Wise Employee Count",
				"Employees by Type",
				"Designation Wise Employee Count",
				"Employees by Branch",
				"Employees by Grade",
				"Job Applicants by Country",
				"Interview Status",
				"Job Offer Status",
				"Job Application Status",
				"Hiring vs Attrition Count",
				"Shift Assignment Breakup",
				"Timesheet Activity Breakup",
				"Department wise Timesheet Hours",
				"Attendance Count",
				"Y-O-Y Transfers",
				"Y-O-Y Promotions",
				"Training Type",
				"Job Applicant Pipeline",
				"Job Applicant Source",
				"Department Wise Openings",
				"Designation Wise Openings",
				"Job Application Frequency",
				"Category-wise Asset Value",
				"Location-wise Asset Value",
				"Asset Value Analytics",
				"Material Request Analysis",
				"Project Summary",
				"Sales Order Analysis",
				"Lead Source",
				"Territory Wise Sales",
				"Opportunities via Campaigns",
				"Territory Wise Opportunity Count",
				"Won Opportunities",
				"Opportunity Trends",
				"Incoming Leads",
				"Item-wise Annual Sales",
				"Gender Diversity Ratio",
				"Item Shortage Summary",
				"Purchase Receipt Trends",
				"Delivery Trends",
				"Department Wise Salary(Last Month)",
				"Purchase Order Analysis",
				"Designation Wise Salary(Last Month)",
				"Accounts Payable Ageing",
				"Accounts Receivable Ageing",
				"Bank Balance",
				"Outgoing Salary",
				"Last Month Downtime Analysis",
				"Produced Quantity",
				"Outgoing Bills (Sales Invoice)",
				"Incoming Bills (Purchase Invoice)",
				"Work Order Analysis",
				"Job Card Analysis",
				"Work Order Qty Analysis",
				"Pending Work Order",
				"Quality Inspection Analysis",
			]]
		]
	},
	# --- Number Cards (1) ---
	{
		"dt": "Number Card",
		"filters": [
			["name", "in", [
				"Sum of Amount",
			]]
		]
	},
	# --- Notifications (9 from install.py) ---
	{
		"dt": "Notification",
		"filters": [
			["name", "in", [
				"Inbox Notification",
				"Test",
				"Inbox Notif",
				"Exit Interview Scheduled",
				"Training Scheduled",
				"Material Request Receipt Notification",
				"Retention Bonus",
				"Notification for new fiscal year",
				"Training Feedback",
			]]
		]
	},
	# --- Print Formats (3 from install.py) ---
	{
		"dt": "Print Format",
		"filters": [
			["name", "in", [
				"Drop Shipping Format",
				"Payment Receipt Voucher",
				"Cheque Printing Format",
			]]
		]
	},
]
