# -*- coding: utf-8 -*-
"""PDF download endpoint for the HR user guide."""

import os
import subprocess
import tempfile

import frappe
from frappe import _


@frappe.whitelist()
def download_pdf():
	"""Render the HR guide as a downloadable PDF via wkhtmltopdf."""
	if frappe.session.user == "Guest":
		frappe.throw(_("يجب تسجيل الدخول أولاً"), frappe.PermissionError)

	template_path = frappe.get_app_path("hr_erp", "www", "hr_guide.html")
	with open(template_path, encoding="utf-8") as f:
		template = f.read()

	html = frappe.render_template(template, {"pdf_mode": True})
	pdf = _html_to_pdf(html)

	frappe.local.response.filename = "دليل استخدام نظام الموارد البشرية - شركة نيو سمارت تك.pdf"
	frappe.local.response.filecontent = pdf
	frappe.local.response.type = "download"


def _html_to_pdf(html):
	"""Convert HTML to PDF bytes using wkhtmltopdf directly (self-contained)."""
	src = None
	out = None
	try:
		with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
			f.write(html)
			src = f.name
		out = src[:-5] + ".pdf"
		subprocess.run(
			[
				"wkhtmltopdf",
				"--encoding", "utf-8",
				"--page-size", "A4",
				"--enable-local-file-access",
				"--quiet",
				src,
				out,
			],
			check=True,
			timeout=120,
		)
		with open(out, "rb") as f:
			return f.read()
	finally:
		for p in (src, out):
			if p and os.path.exists(p):
				try:
					os.remove(p)
				except OSError:
					pass
