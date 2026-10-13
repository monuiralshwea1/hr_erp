# -*- coding: utf-8 -*-
"""Adds HR portal workspace shortcuts (user guide + key attendance reports).

Frappe v15 workspaces render from the `content` JSON field, so every shortcut
must be registered in BOTH the `shortcuts` child table AND a matching
`shortcut` block inside `content`. Idempotent.
"""

import json

import frappe

WORKSPACE_NAME = "بوابة الموارد البشرية"

# كل الاختصارات المطلوبة: (label, type, link_to/url, icon, color)
SHORTCUTS = [
	{
		"label": "دليل استخدام النظام",
		"type": "URL",
		"url": "/hr_guide",
		"icon": "book",
		"color": "#1e40af",
	},
	{
		"label": "الحضور البيومتري للفترة",
		"type": "Report",
		"link_to": "Biometric Period Attendance",
		"icon": "fingerprint",
		"color": "#0e7490",
	},
	{
		"label": "تقرير الحضور والدوام",
		"type": "Report",
		"link_to": "تقرير الحضور والدوام",
		"icon": "calendar",
		"color": "#166534",
	},
	{
		"label": "الحضور متعدد الفترات",
		"type": "Report",
		"link_to": "Multi-Period Attendance",
		"icon": "list",
		"color": "#7c2d12",
	},
	{
		"label": "ملخص الحضور والدوام",
		"type": "Report",
		"link_to": "Attendance Summary V2",
		"icon": "sum",
		"color": "#4c1d95",
	},
	{
		"label": "كشف البصمات",
		"type": "Report",
		"link_to": "كشف البصمات",
		"icon": "file",
		"color": "#155e75",
	},
]


def install():
	"""Append the HR shortcuts to the HR portal workspace if missing."""
	if not frappe.db.exists("Workspace", WORKSPACE_NAME):
		return

	ws = frappe.get_doc("Workspace", WORKSPACE_NAME)
	changed = False

	# 1) shortcuts child table
	existing = []
	for s in ws.get("shortcuts") or []:
		existing.append(
			(s.get("url") or "", s.get("link_to") or "", s.get("label") or "")
		)

	for sc in SHORTCUTS:
		url_or_link = sc.get("url") or sc.get("link_to")
		matched = any(
			(ex_url == url_or_link and ex_url)
			or (ex_link == url_or_link and ex_link)
			or ex_label == sc["label"]
			for ex_url, ex_link, ex_label in existing
		)
		if not matched:
			ws.append("shortcuts", {
				"type": sc["type"],
				"label": sc["label"],
				"icon": sc["icon"],
				"color": sc["color"],
				**({"url": sc["url"]} if sc.get("url") else {}),
				**({"link_to": sc["link_to"]} if sc.get("link_to") else {}),
			})
			existing.append((sc.get("url", ""), sc.get("link_to", ""), sc["label"]))
			changed = True

	# 2) content JSON blocks (this is what the workspace page renders)
	blocks = []
	if ws.get("content"):
		try:
			blocks = json.loads(ws.content)
		except Exception:
			blocks = []
	labels_in_blocks = {
		(b.get("data") or {}).get("shortcut_name")
		for b in blocks
		if b.get("type") == "shortcut"
	}

	for sc in SHORTCUTS:
		if sc["label"] in labels_in_blocks:
			continue
		block = {
			"id": frappe.generate_hash(length=10),
			"type": "shortcut",
			"data": {"shortcut_name": sc["label"], "col": 3},
		}
		insert_at = None
		for i, b in enumerate(blocks):
			if b.get("type") == "shortcut":
				insert_at = i + 1
		if insert_at is None:
			blocks.append(block)
		else:
			blocks.insert(insert_at, block)
		labels_in_blocks.add(sc["label"])
		changed = True

	if changed:
		ws.content = json.dumps(blocks, ensure_ascii=False)
		ws.flags.ignore_permissions = True
		ws.save()
		frappe.db.commit()