# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
payroll_integration — حزمة تكامل الرواتب مع الحضور
====================================================

هذه الحزمة أُضيفت إلى تطبيق hr_erp لدمج ميزات التطبيقين التاليين داخل hr_erp:
  1. navari-frappehr-biostar   → مزامنة أجهزة Suprema BioStar (biostar_sync.py)
  2. nl-attendance-timesheet   → توليد الإضافي من الحضور (overtime_timesheet.py)

إضافة إلى ميزة جديدة خاصة بـ hr_erp:
  3. خصم التأخير والغياب من الراتب (late_absence_deduction.py)
     نفس فكرة حساب الإضافي لكن بالاتجاه المعاكس (خصم بدل إضافة).

كل الميزات تُقرأ إعداداتها من DocType واحد: "HR ERP Payroll Settings"
ويمكن إيقاف أي ميزة منه دون حذف الكود.

للتفاصيل الكاملة وكيفية الإيقاف انظر الملف: HR_ERP_ADDITIONS_AR.md
"""
