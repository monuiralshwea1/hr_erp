# -*- coding: utf-8 -*-
import frappe


def run():
    src = open("/tmp/script.py", encoding="utf-8").read()
    exec(compile(src, "/tmp/script.py", "exec"), {"frappe": frappe})
