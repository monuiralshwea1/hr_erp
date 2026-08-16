# -*- coding: utf-8 -*-
import json

import frappe
import frappe.modules.import_file
from frappe import _


def after_install():
	"""Create the HR portal workspace, dashboard cards/charts, print formats,
	notifications and translations for the hr_erp app."""
	sync_employee_document_doctype()
	create_custom_fields()
	create_number_cards()
	create_dashboard_charts()
	create_workspace()
	create_print_formats()
	create_notifications()
	create_translations()
	frappe.db.commit()


# ------------------------------------------------------------------
# Doctype sync (Employee Document)
# ------------------------------------------------------------------
def sync_employee_document_doctype():
	path = frappe.get_app_path(
		"hr_erp", "hrms_erp", "doctype", "employee_document", "employee_document.json"
	)
	frappe.modules.import_file.import_file_by_path(path)
	print("Employee Document synced:", frappe.db.exists("DocType", "Employee Document"))


# ------------------------------------------------------------------
# Custom Fields (HR Settings / Employee / Employee Checkin)
# ------------------------------------------------------------------
def create_custom_fields():
	"""Idempotent creation of the custom fields used by hr_erp features."""
	_fields = [
		# salary slip auto/manual creation settings
		{
			"dt": "HR Settings",
			"fieldname": "salary_slip_creation_mode",
			"fieldtype": "Select",
			"label": "\u0637\u0631\u064a\u0642\u0629 \u0625\u0646\u0634\u0627\u0621 \u0642\u0633\u064a\u0645\u0629 \u0627\u0644\u0631\u0627\u062a\u0628",
			"options": "Manual\nAuto",
			"default": "Manual",
			"insert_after": "unlink_payment_on_cancellation_of_employee_advance",
		},
		{
			"dt": "HR Settings",
			"fieldname": "auto_submit_salary_slips",
			"fieldtype": "Check",
			"label": "\u0627\u0639\u062a\u0645\u0627\u062f \u0642\u0633\u064a\u0645\u0629 \u0627\u0644\u0631\u0627\u062a\u0628 \u062a\u0644\u0642\u0627\u0626\u064a\u0627\u064b",
			"default": 0,
			"insert_after": "salary_slip_creation_mode",
		},
		# biometric identity on the employee record
		{
			"dt": "Employee",
			"fieldname": "biometric_employee_id",
			"fieldtype": "Data",
			"label": "\u0645\u0639\u0631\u0641 \u0627\u0644\u0645\u0648\u0638\u0641 \u0641\u064a \u062c\u0647\u0627\u0632 \u0627\u0644\u0628\u0635\u0645\u0629",
			"description": "\u0627\u0644\u0645\u0639\u0631\u0641 \u0627\u0644\u0645\u0633\u062c\u0644 \u062f\u0627\u062e\u0644 \u062c\u0647\u0627\u0632 \u0627\u0644\u0628\u0635\u0645\u0629 \u0644\u0644\u0645\u0648\u0638\u0641",
			"insert_after": "salary_cb",
		},
		{
			"dt": "Employee",
			"fieldname": "biometric_fingerprint_id",
			"fieldtype": "Data",
			"label": "\u0631\u0642\u0645 \u0628\u0635\u0645\u0629 \u0627\u0644\u0645\u0648\u0638\u0641",
			"insert_after": "biometric_employee_id",
		},
		{
			"dt": "Employee",
			"fieldname": "biometric_devices",
			"fieldtype": "Small Text",
			"label": "\u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0628\u0635\u0645\u0629 \u0627\u0644\u0645\u0633\u062c\u0644 \u0628\u0647\u0627",
			"description": "\u0623\u0643\u0648\u0627\u062f \u0627\u0644\u0623\u062c\u0647\u0632\u0629 \u0645\u0641\u0635\u0648\u0644\u0629 \u0628\u0641\u0627\u0635\u0644\u0629 \u0641\u0648\u0635\u0644\u0629 (\u060c)",
			"insert_after": "biometric_fingerprint_id",
		},
		{
			"dt": "Employee",
			"fieldname": "biometric_enrolled",
			"fieldtype": "Check",
			"label": "\u0645\u0642\u064a\u062f \u0641\u064a \u0623\u062c\u0647\u0632\u0629 \u0627\u0644\u0628\u0635\u0645\u0629",
			"insert_after": "biometric_devices",
		},
		# dedupe key on the checkin log coming from the device
		{
			"dt": "Employee Checkin",
			"fieldname": "biometric_log_id",
			"fieldtype": "Data",
			"label": "\u0645\u0639\u0631\u0641 \u0633\u062c\u0644 \u0627\u0644\u0628\u0635\u0645\u0629",
			"description": "\u0645\u0639\u0631\u0641 \u0641\u0631\u064a\u062f \u0644\u0644\u0633\u062c\u0644 \u0642\u0627\u062f\u0645 \u0645\u0646 \u062c\u0647\u0627\u0632 \u0627\u0644\u0628\u0635\u0645\u0629 (\u062c\u0647\u0627\u0632+log)",
			"insert_after": "shift",
		},
	]

	for f in _fields:
		_ensure_custom_field(f)
	print("Custom fields ready")


def _ensure_custom_field(fields):
	"""Create the custom field only if it does not already exist."""
	if frappe.db.exists("Custom Field", {"dt": fields["dt"], "fieldname": fields["fieldname"]}):
		return
	try:
		doc = frappe.new_doc("Custom Field")
		doc.dt = fields["dt"]
		doc.fieldname = fields["fieldname"]
		doc.fieldtype = fields["fieldtype"]
		doc.label = fields["label"]
		if fields.get("options"):
			doc.options = fields["options"]
		if fields.get("default") is not None:
			doc.default = fields["default"]
		if fields.get("description"):
			doc.description = fields["description"]
		if fields.get("insert_after") and frappe.db.exists(
			"DocField", {"parent": fields["dt"], "fieldname": fields["insert_after"]}
		):
			doc.insert_after = fields["insert_after"]
		doc.flags.ignore_permissions = True
		doc.insert()
		print("CustomField:", fields["dt"], fields["fieldname"])
	except Exception as e:
		print("CF_ERR", fields["dt"], fields["fieldname"], repr(e)[:200])


# ------------------------------------------------------------------
# Number Cards (12)
# ------------------------------------------------------------------
def _card(label, document_type, function, filters_json, color, aggregate_field=None, method=None):
	if frappe.db.exists("Number Card", label):
		return label
	doc = frappe.new_doc("Number Card")
	doc.label = label
	doc.document_type = document_type
	doc.function = function
	doc.filters_json = json.dumps(filters_json, ensure_ascii=False)
	doc.color = color
	doc.is_public = 1
	doc.module = "hrms-erp"
	doc.type = "Custom" if method else "Document Type"
	if method:
		doc.method = method
	if aggregate_field:
		doc.aggregate_function_based_on = aggregate_field
	doc.flags.ignore_permissions = True
	doc.insert()
	return label


def create_number_cards():
	_cards = [
		# active employees
		("الموظفون النشطون", "Employee", "Count",
		 [["Employee", "status", "=", "Active", False]], "#2490ef"),
		# today attendance (present)
		("حضور اليوم", "Attendance", "Count",
		 [["Attendance", "attendance_date", "Timespan", "today", False],
		  ["Attendance", "status", "=", "Present", False]], "#28a745"),
		# today absences
		("غياب اليوم", "Attendance", "Count",
		 [["Attendance", "attendance_date", "Timespan", "today", False],
		  ["Attendance", "status", "=", "Absent", False]], "#dc3545"),
		# pending leave applications
		("طلبات إجازة معلقة", "Leave Application", "Count",
		 [["Leave Application", "status", "=", "Open", False]], "#fd7e14"),
		# employees on leave today -> custom
		("موظفون في إجازة اليوم", "Leave Application", "Count",
		 [], "#ffc107", None,
		 "hr_erp.hrms_erp.api.smart_defaults.count_on_leave_today"),
		# new employees this month
		("موظفون جدد هذا الشهر", "Employee", "Count",
		 [["Employee", "date_of_joining", "Timespan", "this month", False]], "#17a2b8"),
		# total payroll this month
		("إجمالي رواتب الشهر", "Salary Slip", "Sum",
		 [["Salary Slip", "start_date", "Timespan", "this month", False],
		  ["Salary Slip", "docstatus", "=", 1, False]], "#6f42c1",
		 "net_pay"),
		# pending expense claims
		("مصروفات معلقة", "Expense Claim", "Count",
		 [["Expense Claim", "approval_status", "=", "Draft", False],
		  ["Expense Claim", "docstatus", "=", 0, False]], "#e83e8c"),
		# open jobs
		("وظائف مفتوحة", "Job Opening", "Count",
		 [["Job Opening", "status", "=", "Open", False]], "#20c997"),
		# job applicants
		("المتقدمون للوظائف", "Job Applicant", "Count",
		 [], "#6610f2"),
		# upcoming trainings -> custom
		("تدريبات قادمة", "Training Event", "Count",
		 [], "#007bff", None,
		 "hr_erp.hrms_erp.api.smart_defaults.count_upcoming_trainings"),
		# expiring contracts -> custom
		("عقود تنتهي قريباً", "Employee", "Count",
		 [], "#d63384", None,
		 "hr_erp.hrms_erp.api.smart_defaults.count_expiring_contracts"),
	]

	created = []
	for c in _cards:
		label, dt, fn, flt, color = c[0], c[1], c[2], c[3], c[4]
		agg = c[5] if len(c) > 5 else None
		method = c[6] if len(c) > 6 else None
		try:
			created.append(_card(label, dt, fn, flt, color, agg, method))
		except Exception as e:
			print("CARD_ERR", label, repr(e)[:200])
	print("Number cards:", created)


# ------------------------------------------------------------------
# Dashboard Charts
# ------------------------------------------------------------------
def _chart(chart_name, chart_type, document_type, based_on, chart_kind="Bar",
		   group_by_type="Count", aggregate_field=None, timespan="Last Month",
		   time_interval="Daily", timeseries=0, filters_json=None):
	if frappe.db.exists("Dashboard Chart", chart_name):
		return chart_name
	doc = frappe.new_doc("Dashboard Chart")
	doc.chart_name = chart_name
	doc.chart_type = chart_type
	doc.document_type = document_type
	doc.type = chart_kind
	doc.is_public = 1
	doc.module = "hrms-erp"
	doc.timespan = timespan
	doc.time_interval = time_interval
	doc.timeseries = timeseries
	doc.group_by_type = group_by_type
	if chart_type == "Group By":
		# group-by charts key off group_by_based_on, not based_on
		doc.group_by_based_on = based_on
	else:
		doc.based_on = based_on
	if aggregate_field:
		doc.aggregate_function_based_on = aggregate_field
	doc.filters_json = json.dumps(filters_json or {}, ensure_ascii=False)
	doc.flags.ignore_permissions = True
	doc.insert()
	return chart_name


def create_dashboard_charts():
	# tuple: (chart_name, chart_type, document_type, based_on, chart_kind,
	#         group_by_type, aggregate_field, timespan, time_interval, timeseries)
	_charts = [
		("الموظفون حسب القسم", "Group By", "Employee", "department", "Bar"),
		("الموظفون حسب الفرع", "Group By", "Employee", "branch", "Donut"),
		("الموظفون حسب نوع التوظيف", "Group By", "Employee", "employment_type", "Donut"),
		("الموظفون حسب الحالة", "Group By", "Employee", "status", "Donut"),
		("سجل الحضور - آخر 30 يوم", "Count", "Attendance", "attendance_date", "Line",
		 None, None, "Last Month", "Daily", 1),
		("الإجازات حسب النوع", "Group By", "Leave Application", "leave_type", "Donut"),
		("إجمالي الرواتب حسب القسم", "Group By", "Salary Slip", "department", "Bar",
		 "Sum", "net_pay"),
		("التعيينات الجديدة - آخر 12 شهر", "Count", "Employee", "date_of_joining", "Line",
		 None, None, "Last Year", "Monthly", 1),
		("المغادرون - آخر 12 شهر", "Count", "Employee", "relieving_date", "Line",
		 None, None, "Last Year", "Monthly", 1),
	]

	created = []
	for c in _charts:
		kwargs = {
			"chart_type": c[1],
			"document_type": c[2],
			"based_on": c[3],
			"chart_kind": c[4],
		}
		kwargs["group_by_type"] = c[5] if len(c) > 5 and c[5] else "Count"
		if len(c) > 6 and c[6]:
			kwargs["aggregate_field"] = c[6]
		if len(c) > 7 and c[7]:
			kwargs["timespan"] = c[7]
		if len(c) > 8 and c[8]:
			kwargs["time_interval"] = c[8]
		if len(c) > 9 and c[9]:
			kwargs["timeseries"] = c[9]
		try:
			created.append(_chart(c[0], **kwargs))
		except Exception as e:
			print("CHART_ERR", c[0], repr(e)[:200])
	print("Charts:", created)


# ------------------------------------------------------------------
# Workspace (بوابة الموارد البشرية)
# ------------------------------------------------------------------
def create_workspace():
	ws_title = "بوابة الموارد البشرية"
	# remove existing HR portal (under any name) so re-runs do not duplicate it
	existing = frappe.db.get_value("Workspace", {"title": ws_title}, "name")
	if not existing:
		existing = frappe.db.exists("Workspace", "HR Portal")
	if existing:
		frappe.delete_doc("Workspace", existing, force=1)
	ws_name = ws_title

	cards = ["Setup", "Employee", "Leaves", "Attendance", "Payroll", "Expense Claim",
			 "Recruitment", "Key Reports"]

	blocks = [
		{
			"id": "hrp-header-1",
			"type": "header",
			"data": {
				"text": '<span class="h4"><b>اختصارات سريعة</b></span>',
				"col": 12,
			},
		},
		{"id": "hrp-sh-1", "type": "shortcut", "data": {"shortcut_name": "Employee", "col": 3}},
		{"id": "hrp-sh-2", "type": "shortcut", "data": {"shortcut_name": "Leave Application", "col": 3}},
		{"id": "hrp-sh-3", "type": "shortcut", "data": {"shortcut_name": "Attendance", "col": 3}},
		{"id": "hrp-sh-4", "type": "shortcut", "data": {"shortcut_name": "Employee Document", "col": 3}},
		{"id": "hrp-sp-1", "type": "spacer", "data": {"col": 12}},
		{
			"id": "hrp-header-2",
			"type": "header",
			"data": {
				"text": '<span class="h4"><b>إدارة الموارد البشرية</b></span>',
				"col": 12,
			},
		},
	]

	for i, card in enumerate(cards):
		blocks.append(
			{"id": "hrp-card-%d" % i, "type": "card", "data": {"card_name": card, "col": 4}}
		)

	# number cards block (the child rows above are rendered here)
	blocks.append(
		{
			"id": "hrp-nc-header",
			"type": "header",
			"data": {"text": '<span class="h4"><b>المؤشرات</b></span>', "col": 12},
		}
	)
	for i, nc in enumerate([
		"الموظفون النشطون", "حضور اليوم", "غياب اليوم", "طلبات إجازة معلقة",
		"موظفون في إجازة اليوم", "موظفون جدد هذا الشهر", "إجمالي رواتب الشهر",
		"مصروفات معلقة", "وظائف مفتوحة", "المتقدمون للوظائف", "تدريبات قادمة",
		"عقود تنتهي قريباً",
	]):
		blocks.append(
			{"id": "hrp-nc-%d" % i, "type": "number_card", "data": {"number_card_name": nc, "col": 3}}
		)

	# charts blocks
	blocks.append(
		{
			"id": "hrp-ch-header",
			"type": "header",
			"data": {"text": '<span class="h4"><b>الرسوم البيانية</b></span>', "col": 12},
		}
	)
	for i, ch in enumerate([
		"الموظفون حسب القسم", "الموظفون حسب الفرع", "الموظفون حسب نوع التوظيف",
		"الموظفون حسب الحالة", "سجل الحضور - آخر 30 يوم", "الإجازات حسب النوع",
		"إجمالي الرواتب حسب القسم", "التعيينات الجديدة - آخر 12 شهر",
		"المغادرون - آخر 12 شهر",
	]):
		blocks.append(
			{"id": "hrp-ch-%d" % i, "type": "chart", "data": {"chart_name": ch, "col": 12}}
		)

	workspace = frappe.new_doc("Workspace")
	workspace.name = ws_name
	workspace.label = ws_title
	workspace.title = ws_title
	workspace.icon = "group"
	workspace.sequence_id = 8
	workspace.public = 1
	workspace.module = "hrms-erp"
	workspace.hide_custom = 0
	workspace.content = json.dumps(blocks, ensure_ascii=False)

	# number cards
	for card_label in [
		"الموظفون النشطون", "حضور اليوم", "غياب اليوم", "طلبات إجازة معلقة",
		"موظفون في إجازة اليوم", "موظفون جدد هذا الشهر", "إجمالي رواتب الشهر",
		"مصروفات معلقة", "وظائف مفتوحة", "المتقدمون للوظائف", "تدريبات قادمة",
		"عقود تنتهي قريباً",
	]:
		workspace.append("number_cards", {"number_card_name": card_label})

	# charts
	for chart_name in [
		"الموظفون حسب القسم", "الموظفون حسب الفرع", "الموظفون حسب نوع التوظيف",
		"الموظفون حسب الحالة", "سجل الحضور - آخر 30 يوم", "الإجازات حسب النوع",
		"إجمالي الرواتب حسب القسم", "التعيينات الجديدة - آخر 12 شهر",
		"المغادرون - آخر 12 شهر",
	]:
		workspace.append("charts", {"chart_name": chart_name})

	# shortcuts: must have matching rows in the shortcuts child table
	# because content blocks resolve by label via page_data.shortcuts.items
	workspace.append(
		"shortcuts",
		{"type": "DocType", "link_to": "Employee", "doc_view": "List", "label": "Employee", "color": "Green"},
	)
	workspace.append(
		"shortcuts",
		{"type": "DocType", "link_to": "Leave Application", "doc_view": "List", "label": "Leave Application", "color": "Grey"},
	)
	workspace.append(
		"shortcuts",
		{"type": "DocType", "link_to": "Attendance", "doc_view": "List", "label": "Attendance", "color": "Grey"},
	)
	workspace.append(
		"shortcuts",
		{"type": "DocType", "link_to": "Employee Document", "doc_view": "List", "label": "Employee Document", "color": "Blue"},
	)
	workspace.append(
		"shortcuts",
		{"type": "Report", "link_to": "\u0643\u0634\u0641 \u0627\u0644\u0628\u0635\u0645\u0627\u062a", "doc_view": "List", "label": "\u0643\u0634\u0641 \u0627\u0644\u0628\u0635\u0645\u0627\u062a", "color": "Grey"},
	)

	# links: content card blocks resolve against Card Break groups in the
	# links child table (label must match the card_name used in content)
	link_groups = {
		"Setup": [
			("DocType", "HR Settings"),
			("DocType", "Company"),
			("DocType", "Branch"),
			("DocType", "Department"),
			("DocType", "Designation"),
			("DocType", "Employment Type"),
		],
		"Employee": [
			("DocType", "Employee"),
			("DocType", "Employee Group"),
			("DocType", "Employee Grade"),
			("DocType", "Employee Document"),
			("DocType", "Employee Promotion"),
			("DocType", "Employee Separation"),
		],
		"Leaves": [
			("DocType", "Leave Application"),
			("DocType", "Leave Allocation"),
			("DocType", "Leave Policy"),
			("DocType", "Compensatory Leave Request"),
			("DocType", "Leave Block List"),
		],
		"Attendance": [
			("DocType", "Attendance"),
			("DocType", "Attendance Request"),
			("DocType", "Employee Checkin"),
			("DocType", "Shift Assignment"),
			("DocType", "Shift Request"),
			("Report", "\u0643\u0634\u0641 \u0627\u0644\u0628\u0635\u0645\u0627\u062a"),
		],
		"Payroll": [
			("DocType", "Payroll Entry"),
			("DocType", "Salary Slip"),
			("DocType", "Salary Structure"),
			("DocType", "Salary Structure Assignment"),
			("DocType", "Employee Advance"),
			("DocType", "Additional Salary"),
		],
		"Expense Claim": [
			("DocType", "Expense Claim"),
			("DocType", "Expense Claim Type"),
			("DocType", "Employee Advance"),
			("DocType", "Travel Request"),
		],
		"Recruitment": [
			("DocType", "Job Opening"),
			("DocType", "Job Applicant"),
			("DocType", "Staffing Plan"),
			("DocType", "Employee Onboarding"),
		],
		"Key Reports": [
			("Report", "Employee Information"),
			("Report", "Monthly Attendance Sheet"),
			("Report", "Employee Analytics"),
			("Report", "Employee Leave Balance"),
			("Report", "Employee Leave Balance Summary"),
			("Report", "Recruitment Analytics"),
		],
	}

	for group_label, links in link_groups.items():
		workspace.append("links", {"type": "Card Break", "label": group_label})
		for link_type, link_to in links:
			row = {"type": "Link", "link_type": link_type, "link_to": link_to, "label": link_to}
			if link_type == "Report":
				row["is_query_report"] = 1
			workspace.append("links", row)

	workspace.flags.ignore_permissions = True
	workspace.insert()
	print("Workspace created:", ws_name)


# ------------------------------------------------------------------
# Print Formats (10)
# ------------------------------------------------------------------
def create_print_formats():
	formats = [
		("بطاقة بيانات الموظف", "Employee", _EMP_PROFILE),
		("بطاقة هوية الموظف", "Employee", _EMP_ID_CARD),
		("طلب إجازة", "Leave Application", _LEAVE_APPLICATION),
		("كشف الحضور", "Attendance", _ATTENDANCE),
		("قسيمة راتب", "Salary Slip", _SALARY_SLIP),
		("كشف الرواتب", "Payroll Entry", _PAYROLL_REGISTER),
		("خطاب تعيين", "Employee", _APPOINTMENT_LETTER),
		("شهادة خبرة", "Employee", _EXPERIENCE_CERTIFICATE),
		("مخالصة نهاية الخدمة", "Employee Separation", _EXIT_CLEARANCE),
		("مذكرة مصروفات", "Expense Claim", _EXPENSE_CLAIM),
	]

	for name, doc_type, html in formats:
		if frappe.db.exists("Print Format", name):
			continue
		try:
			pf = frappe.new_doc("Print Format")
			pf.name = name
			pf.doc_type = doc_type
			pf.module = "hrms-erp"
			pf.custom_format = 1
			pf.print_format_type = "Jinja"
			pf.html = html
			pf.align_labels_right = 1
			pf.default_print_language = "ar"
			pf.disabled = 0
			pf.flags.ignore_permissions = True
			pf.insert()
			print("PrintFormat:", name)
		except Exception as e:
			print("PF_ERR", name, repr(e)[:200])


# ------------------------------------------------------------------
# Notifications
# ------------------------------------------------------------------
def create_notifications():
	_notifications = [
		{
			"name": "HR Leave Application Submitted",
			"document_type": "Leave Application",
			"event": "Submit",
			"subject": "تقديم طلب إجازة جديد",
			"message": _NOTIFY_LEAVE,
			"condition": "doc.employee_name",
		},
		{
			"name": "HR Expense Claim Submitted",
			"document_type": "Expense Claim",
			"event": "Submit",
			"subject": "تقديم مذكرة مصروفات جديدة",
			"message": _NOTIFY_EXPENSE,
			"condition": "doc.employee_name",
		},
	]

	for n in _notifications:
		if frappe.db.exists("Notification", n["name"]):
			# ensure module is set (keeps exports consistent)
			_existing = frappe.get_doc("Notification", n["name"])
			if not _existing.module:
				_existing.module = "hrms-erp"
				_existing.flags.ignore_permissions = True
				_existing.save()
			continue

		try:
			notif = frappe.new_doc("Notification")
			notif.name = n["name"]
			notif.enabled = 1
			notif.document_type = n["document_type"]
			notif.event = n["event"]
			notif.subject = n["subject"]
			notif.message = n["message"]
			notif.condition = n["condition"]
			notif.send_system_notification = 1
			notif.module = "hrms-erp"
			# recipient: leave approver or expense approver via doc field
			approver_field = "leave_approver" if n["document_type"] == "Leave Application" else "expense_approver"
			notif.append(
				"recipients", {"receiver_by_document_field": approver_field}
			)
			notif.flags.ignore_permissions = True
			notif.insert()
			print("Notification:", n["name"])
		except Exception as e:
			print("NOTIF_ERR", n["name"], repr(e)[:200])


# ------------------------------------------------------------------
# Translations
# ------------------------------------------------------------------
def create_translations():
	_pairs = [
		("بوابة الموارد البشرية", "HR Portal"),
		("اختصارات سريعة", "Quick Shortcuts"),
		("إدارة الموارد البشرية", "HR Management"),
		("الموظفون النشطون", "Active Employees"),
		("حضور اليوم", "Today's Attendance"),
		("غياب اليوم", "Today's Absences"),
		("طلبات إجازة معلقة", "Pending Leave Applications"),
		("موظفون في إجازة اليوم", "Employees On Leave Today"),
		("موظفون جدد هذا الشهر", "New Employees This Month"),
		("إجمالي رواتب الشهر", "Total Monthly Payroll"),
		("مصروفات معلقة", "Pending Expense Claims"),
		("وظائف مفتوحة", "Open Jobs"),
		("المتقدمون للوظائف", "Job Applicants"),
		("تدريبات قادمة", "Upcoming Trainings"),
		("عقود تنتهي قريباً", "Expiring Contracts"),
		("الموظفون حسب القسم", "Employees by Department"),
		("الموظفون حسب الفرع", "Employees by Branch"),
		("الموظفون حسب نوع التوظيف", "Employees by Employment Type"),
		("الموظفون حسب الحالة", "Employees by Status"),
		("سجل الحضور - آخر 30 يوم", "Attendance Log - Last 30 Days"),
		("الإجازات حسب النوع", "Leaves by Type"),
		("إجمالي الرواتب حسب القسم", "Payroll by Department"),
		("التعيينات الجديدة - آخر 12 شهر", "New Hires - Last 12 Months"),
		("المغادرون - آخر 12 شهر", "Attrition - Last 12 Months"),
		("موظف", "Employee"),
		("اسم الموظف", "Employee Name"),
		("نوع الوثيقة", "Document Type"),
		("رقم الوثيقة", "Document Number"),
		("تاريخ الانتهاء", "Expiry Date"),
	]

	for arabic, english in _pairs:
		if frappe.db.exists("Translation", {"source_text": arabic, "translated_text": english}):
			continue
		try:
			t = frappe.new_doc("Translation")
			t.source_text = arabic
			t.translated_text = english
			t.language = "en"
			t.flags.ignore_permissions = True
			t.insert()
		except Exception as e:
			print("TR_ERR", arabic, repr(e)[:150])
	print("Translations done")


# ------------------------------------------------------------------
# Print format HTML templates (RTL Arabic)
# ------------------------------------------------------------------
_EMP_PROFILE = """{% set cmp = frappe.db.get_value('Company', doc.company, ['company_name','country'], as_dict=True) %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="border-bottom:3px solid #1f6feb;padding-bottom:10px;margin-bottom:15px;">
    <h2 style="margin:0;color:#1f6feb;">{{ cmp.company_name or doc.company }}</h2>
    <div style="font-size:12px;">{{ cmp.country or '' }}</div>
  </div>
  <h3 style="text-align:center;color:#333;margin:5px 0 15px;">بطاقة بيانات الموظف</h3>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="padding:6px;border:1px solid #ddd;width:50%;background:#f7f9fc;"><b>اسم الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee_name }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>رقم الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>القسم</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.department or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الفرع</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.branch or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>المسمى الوظيفي</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.designation or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>تاريخ التعيين</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.date_of_joining) }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الحالة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.status or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>نوع التوظيف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employment_type or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الجنس</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.gender or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الهاتف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.cell_number or doc.mobile_number or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الشركة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.company or '' }}</td></tr>
  </table>
  <div style="text-align:center;margin-top:25px;font-size:11px;color:#777;">صادر عن نظام الموارد البشرية - بوابة الموارد البشرية</div>
</div>"""

_EMP_ID_CARD = """{% set cmp = frappe.db.get_value('Company', doc.company, 'company_name') %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;width:340px;margin:auto;border:2px solid #1f6feb;border-radius:10px;padding:15px;text-align:center;">
  <div style="font-size:16px;font-weight:bold;color:#1f6feb;margin-bottom:8px;">{{ cmp or doc.company }}</div>
  <div style="font-size:11px;color:#555;margin-bottom:12px;">بطاقة تعريف الموظف</div>
  {% if doc.image %}<img src="{{ doc.image }}" style="width:100px;height:120px;object-fit:cover;border-radius:6px;border:1px solid #ccc;margin-bottom:10px;">{% else %}<div style="width:100px;height:120px;background:#eef2f7;border:1px solid #ccc;border-radius:6px;margin:0 auto 10px;line-height:120px;color:#aaa;">الصورة</div>{% endif %}
  <div style="font-size:18px;font-weight:bold;">{{ doc.employee_name }}</div>
  <table style="width:100%;font-size:12px;margin-top:8px;text-align:right;">
    <tr><td style="padding:3px;color:#666;">رقم الموظف</td><td style="padding:3px;"><b>{{ doc.employee }}</b></td></tr>
    <tr><td style="padding:3px;color:#666;">القسم</td><td style="padding:3px;"><b>{{ doc.department or '' }}</b></td></tr>
    <tr><td style="padding:3px;color:#666;">المسمى</td><td style="padding:3px;"><b>{{ doc.designation or '' }}</b></td></tr>
    <tr><td style="padding:3px;color:#666;">الفرع</td><td style="padding:3px;"><b>{{ doc.branch or '' }}</b></td></tr>
  </table>
</div>"""

_LEAVE_APPLICATION = """<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:650px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">طلب إجازة</h3>
    <div style="font-size:12px;color:#666;">رقم الطلب: {{ doc.name }}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;width:30%;"><b>الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee_name or doc.employee }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>نوع الإجازة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.leave_type or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>من تاريخ</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.from_date) }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>إلى تاريخ</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.to_date) }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>عدد الأيام</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.total_leave_days or 0 }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>نصف يوم</b></td><td style="padding:6px;border:1px solid #ddd;">{{ 'نعم' if doc.half_day else 'لا' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>السبب</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.description or doc.reason or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الحالة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.status or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>تاريخ التقديم</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.posting_date) }}</td></tr>
  </table>
  <table style="width:100%;margin-top:40px;font-size:12px;">
    <tr>
      <td style="text-align:center;padding-top:30px;">توقيع الموظف<br/></td>
      <td style="text-align:center;padding-top:30px;">توقيع المدير المباشر</td>
      <td style="text-align:center;padding-top:30px;">الموافقة</td>
    </tr>
  </table>
</div>"""

_ATTENDANCE = """<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:650px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">سجل حضور الموظف</h3>
    <div style="font-size:12px;color:#666;">التاريخ: {{ frappe.utils.formatdate(doc.attendance_date) }}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;width:30%;"><b>الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee_name or doc.employee }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>تاريخ الحضور</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.attendance_date) }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الحالة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.status or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>وقت الحضور</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.in_time or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>وقت الانصراف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.out_time or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الوردية</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.shift or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>إجازة مرتبطة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.leave_type or '' }}</td></tr>
  </table>
</div>"""

_SALARY_SLIP = """<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">قسيمة راتب</h3>
    <div style="font-size:12px;color:#666;">الفترة: {{ frappe.utils.formatdate(doc.start_date) }} - {{ frappe.utils.formatdate(doc.end_date) }}</div>
  </div>
  <table style="width:100%;font-size:13px;margin-bottom:12px;">
    <tr><td style="padding:4px;"><b>الموظف:</b> {{ doc.employee_name or doc.employee }}</td><td style="padding:4px;"><b>الشركة:</b> {{ doc.company or '' }}</td></tr>
    <tr><td style="padding:4px;"><b>القسم:</b> {{ doc.department or '' }}</td><td style="padding:4px;"><b>رقم القسيمة:</b> {{ doc.name }}</td></tr>
  </table>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr style="background:#1f6feb;color:#fff;">
      <th style="padding:6px;border:1px solid #1f6feb;text-align:right;">البنود</th>
      <th style="padding:6px;border:1px solid #1f6feb;text-align:center;">المبلغ</th>
    </tr>
    {% for row in doc.earnings %}
    <tr><td style="padding:6px;border:1px solid #ddd;">{{ row.salary_component }}</td><td style="padding:6px;border:1px solid #ddd;text-align:center;">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td></tr>
    {% endfor %}
    <tr style="background:#f7f9fc;"><td style="padding:6px;border:1px solid #ddd;"><b>الاستقطاعات</b></td><td style="padding:6px;border:1px solid #ddd;"></td></tr>
    {% for row in doc.deductions %}
    <tr><td style="padding:6px;border:1px solid #ddd;">{{ row.salary_component }}</td><td style="padding:6px;border:1px solid #ddd;text-align:center;">{{ frappe.utils.fmt_money(row.amount, currency=doc.currency) }}</td></tr>
    {% endfor %}
    <tr style="background:#eaf2ff;"><td style="padding:7px;border:1px solid #1f6feb;"><b>صافي الراتب</b></td><td style="padding:7px;border:1px solid #1f6feb;text-align:center;"><b>{{ frappe.utils.fmt_money(doc.net_pay, currency=doc.currency) }}</b></td></tr>
  </table>
</div>"""

_PAYROLL_REGISTER = """{% set cur = frappe.db.get_value('Company', doc.company, 'default_currency') %}
{% set slips = frappe.db.get_all('Salary Slip', filters={'payroll_entry': doc.name}, fields=['employee_name','department','gross_pay','net_pay']) %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:800px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">كشف الرواتب</h3>
    <div style="font-size:12px;color:#666;">رقم الإدخال: {{ doc.name }} | التاريخ: {{ frappe.utils.formatdate(doc.posting_date) }}</div>
  </div>
  <table style="width:100%;font-size:13px;margin-bottom:12px;">
    <tr><td style="padding:4px;"><b>الفترة:</b> {{ frappe.utils.formatdate(doc.start_date) }} - {{ frappe.utils.formatdate(doc.end_date) }}</td><td style="padding:4px;"><b>عدد الموظفين:</b> {{ doc.number_of_employees or slips|length }}</td></tr>
  </table>
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <tr style="background:#1f6feb;color:#fff;">
      <th style="padding:5px;border:1px solid #1f6feb;text-align:right;">الموظف</th>
      <th style="padding:5px;border:1px solid #1f6feb;">القسم</th>
      <th style="padding:5px;border:1px solid #1f6feb;">الإجمالي</th>
      <th style="padding:5px;border:1px solid #1f6feb;">الصافي</th>
    </tr>
    {% for row in slips %}
    <tr><td style="padding:5px;border:1px solid #ddd;">{{ row.employee_name or '' }}</td><td style="padding:5px;border:1px solid #ddd;text-align:center;">{{ row.department or '' }}</td><td style="padding:5px;border:1px solid #ddd;text-align:center;">{{ frappe.utils.fmt_money(row.gross_pay or 0, currency=cur) }}</td><td style="padding:5px;border:1px solid #ddd;text-align:center;"><b>{{ frappe.utils.fmt_money(row.net_pay or 0, currency=cur) }}</b></td></tr>
    {% endfor %}
  </table>
  <div style="margin-top:10px;font-size:13px;text-align:left;"><b>الإجمالي الصافي:</b> {{ frappe.utils.fmt_money(slips|sum(attribute='net_pay')|default(0), currency=cur) }}</div>
</div>"""

_APPOINTMENT_LETTER = """{% set cmp = frappe.db.get_value('Company', doc.company, ['company_name','country'], as_dict=True) %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="border-bottom:3px solid #1f6feb;padding-bottom:10px;margin-bottom:15px;">
    <h2 style="margin:0;color:#1f6feb;">{{ cmp.company_name or doc.company }}</h2>
    <div style="font-size:12px;">{{ cmp.country or '' }}</div>
  </div>
  <h3 style="text-align:center;">خطاب تعيين</h3>
  <p style="line-height:2;font-size:13px;">السيد/السيدة <b>{{ doc.employee_name }}</b> المحترم/المحترمة،</p>
  <p style="line-height:2;font-size:13px;text-align:justify;">
    تحية طيبة وبعد،<br/>
    نفيدكم بأنه تم تعيينكم لدى <b>{{ cmp.company_name or doc.company }}</b> بوظيفة <b>{{ doc.designation or '' }}</b>
    في قسم <b>{{ doc.department or '' }}</b> اعتباراً من تاريخ <b>{{ frappe.utils.formatdate(doc.date_of_joining) }}</b>.
    نتمنى لكم التوفيق والنجاح في مهامكم الجديدة.
  </p>
  <table style="width:100%;margin-top:40px;font-size:12px;">
    <tr>
      <td style="text-align:center;padding-top:30px;">توقيع الموظف</td>
      <td style="text-align:center;padding-top:30px;">إدارة الموارد البشرية</td>
    </tr>
  </table>
</div>"""

_EXPERIENCE_CERTIFICATE = """{% set cmp = frappe.db.get_value('Company', doc.company, ['company_name','country'], as_dict=True) %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="border-bottom:3px solid #1f6feb;padding-bottom:10px;margin-bottom:15px;">
    <h2 style="margin:0;color:#1f6feb;">{{ cmp.company_name or doc.company }}</h2>
    <div style="font-size:12px;">{{ cmp.country or '' }}</div>
  </div>
  <h3 style="text-align:center;">شهادة خبرة</h3>
  <p style="line-height:2;font-size:13px;text-align:justify;">
    تشهد <b>{{ cmp.company_name or doc.company }}</b> بأن السيد/السيدة <b>{{ doc.employee_name }}</b>
    قد عمل/ت لدينا بوظيفة <b>{{ doc.designation or '' }}</b> في قسم <b>{{ doc.department or '' }}</b>
    خلال الفترة من <b>{{ frappe.utils.formatdate(doc.date_of_joining) }}</b> إلى
    <b>{{ frappe.utils.formatdate(doc.relieving_date) if doc.relieving_date else 'تاريخ لا يزال يعمل' }}</b>.
    وقد أظهر/ت خلال فترة العمل كفاءة عالية وحسن سلوك. نتمنى له/لها التوفيق.
  </p>
  <table style="width:100%;margin-top:40px;font-size:12px;">
    <tr><td style="text-align:center;padding-top:30px;">إدارة الموارد البشرية</td><td style="text-align:center;padding-top:30px;">التاريخ</td></tr>
  </table>
</div>"""

_EXIT_CLEARANCE = """{% set emp = frappe.db.get_value('Employee', doc.employee, ['reason_for_leaving','date_of_retirement'], as_dict=True) %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">مخالصة نهاية الخدمة</h3>
    <div style="font-size:12px;color:#666;">رقم: {{ doc.name }}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;">
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;width:30%;"><b>الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee_name or doc.employee }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>سبب الانتهاء</b></td><td style="padding:6px;border:1px solid #ddd;">{{ emp.reason_for_leaving or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>تاريخ الانتهاء</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.boarding_begins_on) if doc.boarding_begins_on else (frappe.utils.formatdate(emp.date_of_retirement) if emp.date_of_retirement else '') }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>تاريخ الاستقالة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ frappe.utils.formatdate(doc.resignation_letter_date) if doc.resignation_letter_date else '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>حالة المخالصة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.boarding_status or '' }}</td></tr>
  </table>
  <p style="font-size:12px;margin-top:15px;text-align:justify;">أقر أنا الموظف المذكور أعلاه بأنه تمت تسوية جميع حقوقي المالية المستحقة (الراتب، الإجازات، نهاية الخدمة) لدى الشركة، ولا يحق لي المطالبة بأي مبالغ مستقبلاً.</p>
  <table style="width:100%;margin-top:35px;font-size:12px;">
    <tr><td style="text-align:center;padding-top:30px;">توقيع الموظف</td><td style="text-align:center;padding-top:30px;">إدارة الموارد البشرية</td></tr>
  </table>
</div>"""

_EXPENSE_CLAIM = """{% set cur = frappe.db.get_value('Company', doc.company, 'default_currency') %}
<div dir="rtl" style="font-family:'Tahoma',sans-serif;color:#222;max-width:700px;margin:auto;">
  <div style="text-align:center;border-bottom:2px solid #1f6feb;padding-bottom:8px;margin-bottom:12px;">
    <h3 style="margin:0;">مذكرة مصروفات</h3>
    <div style="font-size:12px;color:#666;">رقم: {{ doc.name }} | التاريخ: {{ frappe.utils.formatdate(doc.posting_date) }}</div>
  </div>
  <table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:10px;">
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;width:30%;"><b>الموظف</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.employee_name or doc.employee }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الشركة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.company or '' }}</td></tr>
    <tr><td style="padding:6px;border:1px solid #ddd;background:#f7f9fc;"><b>الحالة</b></td><td style="padding:6px;border:1px solid #ddd;">{{ doc.approval_status or doc.status or '' }}</td></tr>
  </table>
  <table style="width:100%;border-collapse:collapse;font-size:12px;">
    <tr style="background:#1f6feb;color:#fff;">
      <th style="padding:5px;border:1px solid #1f6feb;text-align:right;">نوع المصروف</th>
      <th style="padding:5px;border:1px solid #1f6feb;">التاريخ</th>
      <th style="padding:5px;border:1px solid #1f6feb;">المبلغ</th>
    </tr>
    {% for row in doc.expenses %}
    <tr>
      <td style="padding:5px;border:1px solid #ddd;">{{ row.expense_type }}</td>
      <td style="padding:5px;border:1px solid #ddd;text-align:center;">{{ frappe.utils.formatdate(row.expense_date) }}</td>
      <td style="padding:5px;border:1px solid #ddd;text-align:center;">{{ frappe.utils.fmt_money(row.amount, currency=cur) }}</td>
    </tr>
    {% endfor %}
    <tr style="background:#eaf2ff;"><td colspan="2" style="padding:6px;border:1px solid #1f6feb;text-align:left;"><b>الإجمالي</b></td><td style="padding:6px;border:1px solid #1f6feb;text-align:center;"><b>{{ frappe.utils.fmt_money(doc.total_claimed_amount or doc.total_sanctioned_amount or 0, currency=cur) }}</b></td></tr>
  </table>
</div>"""

_NOTIFY_LEAVE = """<div dir="rtl" style="font-family:Tahoma,sans-serif;">
  تم تقديم طلب إجازة جديد من الموظف <b>{{ doc.employee_name }}</b>
  نوع الإجازة: {{ doc.leave_type }}<br/>
  من {{ frappe.utils.formatdate(doc.from_date) }} إلى {{ frappe.utils.formatdate(doc.to_date) }}<br/>
  اضغط لعرض الطلب: <a href="/app/leave-application/{{ doc.name }}">{{ doc.name }}</a>
</div>"""

_NOTIFY_EXPENSE = """{% set cur = frappe.db.get_value('Company', doc.company, 'default_currency') %}
<div dir="rtl" style="font-family:Tahoma,sans-serif;">
  تم تقديم مذكرة مصروفات جديدة من الموظف <b>{{ doc.employee_name }}</b>
  بقيمة {{ frappe.utils.fmt_money(doc.total_claimed_amount or 0, currency=cur) }}<br/>
  اضغط لعرض المذكرة: <a href="/app/expense-claim/{{ doc.name }}">{{ doc.name }}</a>
</div>"""


# ------------------------------------------------------------------
# Remove default data (opposite of after_install)
# ------------------------------------------------------------------
def remove_default_data():
	"""Delete every record created by this app's after_install.

	Removes Number Cards, Dashboard Charts, Print Formats, Notifications,
	Translations (module = hrms-erp), the HR portal Workspace and the custom
	fields added on core doctypes. Does NOT drop the Employee Document table
	(use ``bench uninstall-app hr_erp`` for that).
	"""
	deleted = []

	for dt in ["Number Card", "Dashboard Chart", "Print Format", "Notification", "Translation"]:
		for name in frappe.get_all(dt, filters={"module": "hrms-erp"}, pluck="name"):
			frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
			deleted.append((dt, name))

	for name in frappe.get_all("Workspace", filters={"title": "بوابة الموارد البشرية"}, pluck="name"):
		frappe.delete_doc("Workspace", name, force=1, ignore_permissions=True)
		deleted.append(("Workspace", name))
	if frappe.db.exists("Workspace", "HR Portal"):
		frappe.delete_doc("Workspace", "HR Portal", force=1, ignore_permissions=True)
		deleted.append(("Workspace", "HR Portal"))

	cf_fields = [
		"salary_slip_creation_mode",
		"auto_submit_salary_slips",
		"biometric_employee_id",
		"biometric_fingerprint_id",
		"biometric_devices",
		"biometric_enrolled",
		"biometric_log_id",
	]
	for cf in frappe.get_all("Custom Field", filters={"fieldname": ["in", cf_fields]}, pluck="name"):
		frappe.delete_doc("Custom Field", cf, force=1, ignore_permissions=True)
		deleted.append(("Custom Field", cf))

	frappe.db.commit()
	print("Removed %d records created by hr_erp:" % len(deleted))
	for dt, name in deleted:
		print("  - %s: %s" % (dt, name))
	return len(deleted)
