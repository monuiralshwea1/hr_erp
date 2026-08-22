# -*- coding: utf-8 -*-
import frappe


# ------------------------------------------------------------------
# Workspace: fix card merge bug caused by stale link_count
# ------------------------------------------------------------------
def fix_workspace(doc, method=None):
	"""Repair stale ``link_count`` and duplicate block ids on Workspace.

	Frappe's ``Workspace.build_links_table_from_card`` deletes a card's old
	rows with ``del self.links[idx : idx + link.link_count + 1]`` using the
	value persisted in the child table. That value goes stale when shortcuts
	are added/removed, so the slice crosses the next ``Card Break`` and the
	shortcuts of several cards get merged into one card. Recomputing the count
	from the actual links on every save keeps the slice exact.
	"""
	fix_link_count(doc)
	dedupe_block_ids(doc)


def fix_link_count(doc):
	links = doc.get("links")
	if not links:
		return

	rows = list(links)
	break_indexes = [i for i, link in enumerate(rows) if link.type == "Card Break"]
	for pos, idx in enumerate(break_indexes):
		next_idx = break_indexes[pos + 1] if pos + 1 < len(break_indexes) else len(rows)
		rows[idx].link_count = next_idx - idx - 1


def dedupe_block_ids(doc):
	content = doc.get("content")
	if not content:
		return

	blocks = frappe.parse_json(content)
	if not isinstance(blocks, list):
		return

	seen = set()
	changed = False
	for block in blocks:
		if not isinstance(block, dict):
			continue
		block_id = block.get("id")
		if not block_id or block_id in seen:
			block["id"] = frappe.generate_hash(length=10)
			changed = True
		seen.add(block["id"])

	if changed:
		doc.content = frappe.as_json(blocks)
