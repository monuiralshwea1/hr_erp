# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
مزامنة أجهزة Suprema BioStar — biostar_sync.py
================================================

منقول ومُكيَّف من تطبيق navari-frappehr-biostar ليعمل داخل hr_erp
(مرجع: https://github.com/navariltd/navari-frappehr-biostar).

آلية العمل:
  1. الاتصال بخادم BioStar TA API (login → report.json)
  2. جلب تقرير الحضور اليومي لكل الموظفين (أو موظفين محددين)
  3. تحويل inTime/outTime إلى سجلات Employee Checkin (IN/OUT)
  4. تحديث حقل آخر مزامنة في Employee

الإيقاف: من "HR ERP Payroll Settings" عطّل enable_biostar_sync.
  أو احذف أسطر scheduler_events من hooks.py لإيقاف الجدولة التلقائية.

الإعدادات من "HR ERP Payroll Settings":
  biostar_username, biostar_password, biostar_ta_url
"""

import frappe
from frappe import _
from frappe.utils import getdate, add_days
from frappe.utils.password import get_decrypted_password

SETTINGS_DOCTYPE = "HR ERP Payroll Settings"


def _get_settings():
	if not frappe.db.exists("DocType", SETTINGS_DOCTYPE):
		return {}
	try:
		doc = frappe.get_cached_doc(SETTINGS_DOCTYPE)
		return {
			"enabled": frappe.utils.cint(doc.get("enable_biostar_sync")),
			"username": doc.get("biostar_username"),
			"password": get_decrypted_password(SETTINGS_DOCTYPE, SETTINGS_DOCTYPE, "biostar_password"),
			"ta_url": doc.get("biostar_ta_url"),
		}
	except Exception:
		return {}


@frappe.whitelist()
def get_employee_checkins(start_date, end_date, employees=None):
	"""جلب سجلات البصمة من BioStar لنطاق تاريخ محدد."""
	settings = _get_settings()
	if not settings.get("enabled"):
		frappe.throw(_("Biostar sync is disabled in HR ERP Payroll Settings"))

	from .biostar_connector import BiostarConnector

	biostar = BiostarConnector(settings["username"], settings["password"], settings["ta_url"])
	biostar.login()

	if employees:
		if isinstance(employees, str):
			employees = frappe.parse_json(employees)
		employees = [emp.get("name") for emp in employees]
		attendance_ids = biostar.get_attendance_ids(employees)
	else:
		attendance_ids = biostar.get_attendance_ids()

	biostar.get_attendance_report(attendance_ids, start_date, end_date)
	biostar.format_attendance_logs()


@frappe.whitelist()
def add_checkin_logs_for_current_day():
	"""جلب سجلات اليوم الحالي — للجدولة اليومية."""
	settings = _get_settings()
	if not settings.get("enabled"):
		return  # صامت — لا خطأ عند الإيقاف
	start_date = getdate().strftime("%Y-%m-%d")
	return get_employee_checkins(start_date, start_date)


@frappe.whitelist()
def check_for_yesterday_logs():
	"""جلب سجلات الأمس — للجدولة الليلية (إعادة المحاولة)."""
	settings = _get_settings()
	if not settings.get("enabled"):
		return
	yesterday = add_days(getdate(), -1).strftime("%Y-%m-%d")
	return get_employee_checkins(yesterday, yesterday)
