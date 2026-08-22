# -*- coding: utf-8 -*-
import frappe
from frappe import _
from frappe.utils import cint, flt, getdate, get_first_day, get_last_day, nowdate


# ------------------------------------------------------------------
# Settings
# ------------------------------------------------------------------
def get_slip_creation_settings():
	"""Return the auto/manual slip creation configuration from HR Settings."""
	return {
		"mode": frappe.db.get_single_value("HR Settings", "salary_slip_creation_mode") or "Manual",
		"auto_submit": cint(frappe.db.get_single_value("HR Settings", "auto_submit_salary_slips")),
	}


# ------------------------------------------------------------------
# Hook: Salary Structure Assignment
# ------------------------------------------------------------------
def on_salary_assignment_submit(doc, method=None):
	"""Auto create the employee salary slip once the salary is assigned (if enabled)."""
	if frappe.flags.in_install or frappe.flags.in_patch or frappe.flags.in_migrate:
		return

	settings = get_slip_creation_settings()
	if settings["mode"] != "Auto":
		return

	if not doc.get("employee"):
		return

	try:
		slip = create_salary_slip_for_employee(
			doc.employee,
			company=doc.get("company"),
			posting_date=nowdate(),
			submit=settings["auto_submit"],
		)
		if slip:
			frappe.msgprint(
				_("تم إنشاء قسيمة الراتب {0} تلقائياً للموظف {1}.").format(
					frappe.bold(slip), doc.employee
				),
				indicator="green",
				title=_("Salary Slip"),
			)
	except Exception:
		# never block the assignment because of a helper
		frappe.log_error(frappe.get_traceback(), "hr_erp: auto salary slip")


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------
def create_salary_slip_for_employee(
	employee, company=None, posting_date=None, submit=False, payroll_frequency="Monthly"
):
	"""Create and return the salary slip of the employee for the current payroll month.

	Uses the standard HRMS Salary Slip validate() flow so earnings, deductions,
	working days and net pay are computed from the assigned salary structure.
	"""
	from frappe.utils import getdate

	posting_date = getdate(posting_date or nowdate())
	start_date = get_first_day(posting_date)
	end_date = get_last_day(posting_date)

	if not company:
		company = frappe.db.get_value("Employee", employee, "company")
	if not company:
		frappe.log_error(
			"hr_erp: no company for employee %s" % employee, "auto salary slip"
		)
		return None

	# skip if a slip already exists for the same period
	exists = frappe.db.exists(
		"Salary Slip",
		{
			"employee": employee,
			"start_date": start_date,
			"end_date": end_date,
			"docstatus": ["!=", 2],
		},
	)
	if exists:
		return exists

	# NOTE: build the doc with the employee inside the constructor dict,
	# because SalarySlip.__init__ computes the naming series from
	# self.employee at construction time (frappe.new_doc() would yield
	# a stale "Sal Slip/None/..." name).
	slip = frappe.get_doc(
		{
			"doctype": "Salary Slip",
			"employee": employee,
			"company": company,
			"posting_date": posting_date,
			"start_date": start_date,
			"end_date": end_date,
			"payroll_frequency": payroll_frequency,
			"currency": frappe.db.get_value("Company", company, "default_currency"),
		}
	)
	slip.flags.ignore_permissions = True

	# validate() computes components, working days and net pay
	slip.insert(ignore_permissions=True)

	if submit and slip.docstatus == 0:
		slip.submit()

	frappe.db.commit()
	return slip.name
