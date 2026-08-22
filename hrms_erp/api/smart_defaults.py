# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import flt, getdate, nowdate


# ------------------------------------------------------------------
# Employee
# ------------------------------------------------------------------
def before_employee_save(doc, method=None):
	"""Smart defaults + validations for Employee."""
	meta = frappe.get_meta("Employee")

	# full name fallback from first/last name
	if not doc.get("employee_name"):
		first = (doc.get("first_name") or "").strip()
		last = (doc.get("last_name") or "").strip()
		if first:
			doc.employee_name = ("%s %s" % (first, last)).strip()

	# default status
	if not doc.get("status"):
		doc.status = "Active"

	# company default
	if not doc.get("company"):
		doc.company = frappe.defaults.get_user_default("Company")

	# employment type default
	if not doc.get("employment_type") and meta.has_field("employment_type"):
		et = frappe.db.get_value("Employment Type", "Full-time", "name") or frappe.db.get_value(
			"Employment Type", {"is_default": 1}, "name"
		)
		if et:
			doc.employment_type = et

	# validate date fields
	if doc.get("date_of_joining") and doc.get("contract_end_date"):
		if getdate(doc.contract_end_date) < getdate(doc.date_of_joining):
			frappe.throw(
				_("تاريخ نهاية العقد لا يمكن أن يسبق تاريخ بداية التوظيف.")
			)


def on_employee_update(doc, method=None):
	"""Auto-create default leave allocation when a new employee is created."""
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	# on_update always has the row; a new record has no doc_before_save
	previous = doc.get_doc_before_save()
	if previous:
		return

	if doc.get("date_of_joining") and doc.get("user_id"):
		_submit_leave_allocations(doc)


def _submit_leave_allocations(employee_doc):
	"""Auto-create a default leave allocation (annual) on joining if none exists."""
	if not employee_doc.get("date_of_joining"):
		return

	leave_type = frappe.db.get_value("Leave Type", {"is_annual": 1}, "name")
	if not leave_type:
		return

	if frappe.db.exists(
		"Leave Allocation",
		{
			"employee": employee_doc.name,
			"leave_type": leave_type,
			"from_date": ["<=", nowdate()],
			"to_date": [">=", nowdate()],
		},
	):
		return

	from frappe.utils import add_days, getdate

	try:
		allocation = frappe.new_doc("Leave Allocation")
		allocation.employee = employee_doc.name
		allocation.employee_name = employee_doc.employee_name
		allocation.leave_type = leave_type
		allocation.from_date = getdate(employee_doc.date_of_joining)
		allocation.to_date = add_days(
			getdate(employee_doc.date_of_joining), 365
		)
		allocation.new_leaves_allocated = 0
		allocation.flags.ignore_permissions = True
		allocation.insert()
		frappe.db.commit()
	except Exception:
		# never block employee creation because of a helper
		frappe.db.rollback()
		frappe.log_error(frappe.get_traceback(), "hr_erp: auto leave allocation")


# ------------------------------------------------------------------
# Leave Application
# ------------------------------------------------------------------
def validate_leave(doc, method=None):
	"""Validations + smart defaults for Leave Application."""
	if doc.get("from_date") and doc.get("to_date"):
		if getdate(doc.to_date) < getdate(doc.from_date):
			frappe.throw(_("تاريخ نهاية الإجازة لا يمكن أن يسبق تاريخ بدايتها."))

		# auto compute days when empty
		if not doc.get("total_leave_days") and not doc.get("half_day"):
			days = (getdate(doc.to_date) - getdate(doc.from_date)).days + 1
			if days > 0:
				doc.total_leave_days = days

	# default leave type
	if not doc.get("leave_type"):
		leave_type = frappe.db.get_value("Leave Type", {"is_annual": 1}, "name")
		if leave_type:
			doc.leave_type = leave_type

	# default employee from current user
	if not doc.get("employee"):
		emp = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user}, ["name", "employee_name"]
		)
		if emp:
			doc.employee = emp[0]
			if not doc.get("employee_name"):
				doc.employee_name = emp[1]

	# default posting date
	if not doc.get("posting_date"):
		doc.posting_date = nowdate()


def on_leave_submit(doc, method=None):
	"""Notify approvers when a leave application is submitted."""
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	approver = doc.get("leave_approver")
	if not approver:
		approver = frappe.db.get_value(
			"Employee", doc.get("employee"), "leave_approver"
		)
	if not approver:
		# fallback: any user with Leave Approver role
		rows = frappe.get_all("Has Role", filters={"role": "Leave Approver"},
							  fields=["parent"], limit=1)
		approver = rows[0]["parent"] if rows else None

	if approver:
		_add_notification_log(
			user=approver,
			doctype="Leave Application",
			docname=doc.name,
			subject=_("طلب إجازة جديد من {0}").format(doc.get("employee_name") or doc.get("employee")),
		)


# ------------------------------------------------------------------
# Attendance
# ------------------------------------------------------------------
def validate_attendance(doc, method=None):
	"""Validations for Attendance."""
	if doc.get("attendance_date"):
		if getdate(doc.attendance_date) > getdate(nowdate()):
			frappe.throw(_("لا يمكن تسجيل الحضور لتاريخ في المستقبل."))

	if not doc.get("status"):
		doc.status = "Present"

	if not doc.get("company"):
		doc.company = frappe.defaults.get_user_default("Company")


# ------------------------------------------------------------------
# Expense Claim
# ------------------------------------------------------------------
def validate_expense_claim(doc, method=None):
	"""Smart defaults for Expense Claim."""
	if not doc.get("posting_date"):
		doc.posting_date = nowdate()

	if not doc.get("approval_status"):
		doc.approval_status = "Draft"

	# default expense approver
	if not doc.get("expense_approver"):
		emp = frappe.db.get_value(
			"Employee", {"user_id": frappe.session.user}, "name"
		)
		if emp:
			doc.expense_approver = frappe.db.get_value("Employee", emp, "expense_approver")

	# validate amounts
	if doc.get("expenses"):
		for row in doc.expenses:
			if not row.get("amount") or flt(row.get("amount")) <= 0:
				frappe.throw(
					_("الصف رقم {0}: يجب إدخال مبلغ أكبر من صفر لكل بند مصروف.").format(row.idx)
				)


# ------------------------------------------------------------------
# Job Applicant
# ------------------------------------------------------------------
def validate_job_applicant(doc, method=None):
	"""Smart defaults for Job Applicant."""
	if not doc.get("status"):
		doc.status = "Open"

	if not doc.get("applicant_name"):
		email = (doc.get("email_id") or "").strip()
		if email:
			doc.applicant_name = email.split("@")[0]


# ------------------------------------------------------------------
# Salary Structure Assignment
# ------------------------------------------------------------------
def validate_salary_assignment(doc, method=None):
	"""Prevent assignments in the past that override active structure."""
	if doc.get("effective_from") and getdate(doc.effective_from) < getdate(nowdate()):
		frappe.msgprint(
			_("تنبيه: تاريخ سريان بداية الهيكل ({0}) في الماضي. تأكد أن هذا مقصود.").format(
				doc.effective_from
			),
			alert=True,
		)


# ------------------------------------------------------------------
# Number Card custom methods
# ------------------------------------------------------------------
@frappe.whitelist()
def count_on_leave_today():
	"""Employees on approved leave today (custom number card)."""
	today = nowdate()
	return frappe.db.count(
		"Leave Application",
		{
			"from_date": ["<=", today],
			"to_date": [">=", today],
			"status": "Approved",
			"docstatus": 1,
		},
	)


@frappe.whitelist()
def count_upcoming_trainings():
	"""Training events scheduled in the future (custom number card)."""
	from frappe.utils import now_datetime

	return frappe.db.count(
		"Training Event",
		{
			"start_time": [">", now_datetime()],
			"docstatus": 1,
		},
	)


@frappe.whitelist()
def count_expiring_contracts():
	"""Active employees whose contracts expire within the next 30 days."""
	from frappe.utils import add_days

	today = nowdate()
	limit = add_days(today, 30)
	return frappe.db.count(
		"Employee",
		{
			"status": "Active",
			"contract_end_date": ["between", [today, limit]],
		},
	)


@frappe.whitelist()
def hr_dashboard_kpis():
	"""Aggregated KPIs for the HR dashboard indicator block."""
	from frappe.utils import add_days, get_first_day, now_datetime, nowdate

	today = nowdate()
	present = frappe.db.count(
		"Attendance", {"attendance_date": today, "status": "Present", "docstatus": 1}
	)
	absent = frappe.db.count(
		"Attendance", {"attendance_date": today, "status": "Absent", "docstatus": 1}
	)
	half_day = frappe.db.count(
		"Attendance", {"attendance_date": today, "status": "Half Day", "docstatus": 1}
	)
	on_leave = frappe.db.count(
		"Leave Application",
		{"from_date": ["<=", today], "to_date": [">=", today], "status": "Approved", "docstatus": 1},
	)
	total_payroll = frappe.db.sql(
		"""select ifnull(sum(net_pay), 0) from `tabSalary Slip`
		where docstatus = 1 and start_date >= %s""",
		get_first_day(today),
	)[0][0]

	return {
		"active_employees": frappe.db.count("Employee", {"status": "Active"}),
		"today_present": present,
		"today_absent": absent,
		"today_half_day": half_day,
		"today_on_leave": on_leave,
		"pending_leaves": frappe.db.count("Leave Application", {"status": "Open"}),
		"new_hires_month": frappe.db.count(
			"Employee", {"date_of_joining": ["between", [get_first_day(today), today]]}
		),
		"monthly_payroll": int(total_payroll),
		"pending_claims": frappe.db.count("Expense Claim", {"approval_status": "Draft", "docstatus": 0}),
		"open_jobs": frappe.db.count("Job Opening", {"status": "Open"}),
		"applicants": frappe.db.count("Job Applicant", {}),
		"upcoming_trainings": frappe.db.count(
			"Training Event", {"start_time": [">", now_datetime()], "docstatus": 1}
		),
		"expiring_contracts": frappe.db.count(
			"Employee",
			{"status": "Active", "contract_end_date": ["between", [today, add_days(today, 30)]]},
		),
	}


@frappe.whitelist()
def active_employees():
	"""Active employees for print/selector widgets."""
	return [
		{"name": e.name, "employee_name": e.employee_name}
		for e in frappe.get_all(
			"Employee",
			filters={"status": "Active"},
			fields=["name", "employee_name"],
			order_by="employee_name asc",
		)
	]


@frappe.whitelist()
def salary_slips_current_month():
	"""Submitted salary slips of the current month for printing."""
	from frappe.utils import get_first_day, nowdate

	rows = frappe.get_all(
		"Salary Slip",
		filters={"docstatus": 1, "start_date": [">=", get_first_day(nowdate())]},
		fields=["name", "employee", "employee_name", "net_pay"],
		order_by="employee_name asc",
	)
	return [
		{
			"name": s.name,
			"employee": s.employee,
			"employee_name": s.employee_name,
			"net_pay": s.net_pay,
		}
		for s in rows
	]


@frappe.whitelist()
def latest_attendance(employee):
	"""Latest submitted attendance record of an employee (for printing)."""
	rows = frappe.get_all(
		"Attendance",
		filters={"employee": employee, "docstatus": 1},
		fields=["name"],
		order_by="attendance_date desc",
		limit=1,
	)
	return rows[0].name if rows else None


# ------------------------------------------------------------------
# helpers
# ------------------------------------------------------------------
def _add_notification_log(user, doctype, docname, subject, type="Alert"):
	try:
		log = frappe.new_doc("Notification Log")
		log.for_user = user
		log.document_type = doctype
		log.document_name = docname
		log.subject = subject
		log.type = type
		log.flags.ignore_permissions = True
		log.insert()
	except Exception:
		frappe.log_error(frappe.get_traceback(), "hr_erp: notification log")
