# -*- coding: utf-8 -*-
"""
إضافات hr_erp — دليل الميزات الجديدة وكيفية إيقافها
=====================================================
التاريخ: 2026-09-13
التطبيق: hr_erp (site1.local @ 192.168.0.248)

هذا الملف يشرح كل إضافة جديدة وكيفية إيقافها عند عدم الاحتياج.
كل الإضافات داخل مجلد: hr_erp/hrms_erp/payroll_integration/
والإعدادات في DocType واحد: "HR ERP Payroll Settings" (إعدادات رواتب hr_erp)

نسخة احتياطية قبل التعديل: ~/hr_erp_backup_20260913.tar.gz (على السيرفر)


═══════════════════════════════════════════════════════════════════════════════
الميزة 1: خصم التأخير والغياب من الراتب (Late & Absence Deduction)
═══════════════════════════════════════════════════════════════════════════════
الملف: hrms_erp/payroll_integration/late_absence_deduction.py

ماذا تفعل:
  - عند حفظ/اعتماد قسيمة راتب (Salary Slip)، تُجمع دقائق التأخير وأيام الغياب
    من سجلات Attendance ضمن فترة القسيمة.
  - تُحسب مبالغ الخصم وتُضاف تلقائياً كسطور في جدول Deductions.
  - خصم التأخير = سعر الساعة × معامل التأخير × (دقائق التأخير / 60)
  - خصم الغياب  = سعر اليوم × معامل الغياب × عدد أيام الغياب

التفعيل:
  من "HR ERP Payroll Settings":
    ✅ Enable Late Deduction    + اختر Late Deduction Component
    ✅ Enable Absence Deduction + اختر Absence Deduction Component

الإيقاف (بدون حذف كود):
  - أوقف الخيارين Enable Late Deduction / Enable Absence Deduction من الإعدادات.
  - أو لإيقاف كامل: احذف هذا السطر من hooks.py ضمن doc_events:
        "Salary Slip": {
            "validate": "hr_erp.hrms_erp.payroll_integration.late_absence_deduction.apply_late_absence_deduction",
        },
    ثم: bench --site site1.local clear-cache && أعد تشغيل السيرفر.

المصدر: فكرة مُكيَّفة من nl-attendance-timesheet (لكن بالاتجاه المعاكس: خصم).


═══════════════════════════════════════════════════════════════════════════════
الميزة 2: توليد الإضافي من الحضور (Overtime Generation)
═══════════════════════════════════════════════════════════════════════════════
الملف: hrms_erp/payroll_integration/overtime_timesheet.py

ماذا تفعل:
  - تقرأ سجلات Attendance (Present) في نطاق تاريخ.
  - إذا تجاوز الانصراف نهاية الدوام + Overtime Threshold → Timesheet بنشاط Overtime 1.5
  - إذا كان اليوم عطلة رسمية → Timesheet بنشاط Overtime 2.0

التفعيل:
  من "HR ERP Payroll Settings": ✅ Enable Overtime Generation
  + اختر Overtime 1.5 Activity و Overtime 2.0 Activity.
  ثم زر "Generate Overtime Timesheets" في صفحة الإعدادات.

الإيقاف:
  - أوقف Enable Overtime Generation من الإعدادات.
  - أو احذف استدعاء الدالة من الواجهة.

المصدر: منقول من nl-attendance-timesheet.


═══════════════════════════════════════════════════════════════════════════════
الميزة 3: مزامنة أجهزة BioStar (Biostar Sync)
═══════════════════════════════════════════════════════════════════════════════
الملفات: hrms_erp/payroll_integration/biostar_sync.py
         hrms_erp/payroll_integration/biostar_connector.py

ماذا تفعل:
  - تتصل بخادم Suprema BioStar TA API وتجلب سجلات الحضور.
  - تنشئ Employee Checkin (IN/OUT) لكل موظف حسب Attendance Device ID.
  - جدولة تلقائية: 23:10 يومياً (اليوم) و 03:00 (إعادة محاولة الأمس).

التفعيل:
  من "HR ERP Payroll Settings": ✅ Enable Biostar Sync
  + أدخل Biostar Username / Password / TA URL.

الإيقاف:
  - أوقف Enable Biostar Sync من الإعدادات (الجدولة تتوقف تلقائياً لأنها تتحقق من المفتاح).
  - أو لإيقاف الجدولة نهائياً: احذف قسم scheduler_events من hooks.py.

المصدر: منقول من navari-frappehr-biostar.


═══════════════════════════════════════════════════════════════════════════════
الميزة 4: الحقول المخصصة والبيانات الافتراضية
═══════════════════════════════════════════════════════════════════════════════
الملفات: payroll_integration/custom_fields.py  → تنشئ حقولاً مخصصة
         payroll_integration/default_data.py   → تنشئ بيانات افتراضية

تعمل تلقائياً عند bench migrate (ضمن after_migrate في hooks.py).

الحقول المُنشأة:
  - Employee.custom_last_attendance_sync_date  (تاريخ آخر مزامنة بصمة)
  - Salary Slip: تبويب "Attendance Details" + total_late_minutes + total_absent_days
  - Timesheet.attendance  (ربط بالحضور)

البيانات الافتراضية:
  - Salary Components: Late Deduction, Absence Deduction, Overtime 1.5, Overtime 2.0
  - Activity Types: Overtime 1.5, Overtime 2.0
  - ربط تلقائي في "HR ERP Payroll Settings"

الإيقاف:
  - احذف السطرين من after_migrate في hooks.py:
        "hr_erp.hrms_erp.payroll_integration.custom_fields.create_custom_fields",
        "hr_erp.hrms_erp.payroll_integration.default_data.create_default_data",
  - البيانات/الحقول المُنشأة تبقى (احذفها يدوياً من الواجهة إذا رغبت).


═══════════════════════════════════════════════════════════════════════════════
الميزة 5: الترجمة العربية
═══════════════════════════════════════════════════════════════════════════════
الملف: hr_erp/translations/ar.csv

أُضيفت 41 ترجمة جديدة للواجهات (إعدادات الرواتب، الإضافي، BioStar، الخصومات).
لتعديل ترجمة: عدّل السطر في ar.csv ثم bench --site site1.local clear-cache.


═══════════════════════════════════════════════════════════════════════════════
ملخص التفعيل السريع
═══════════════════════════════════════════════════════════════════════════════
1. افتح "HR ERP Payroll Settings" من قائمة الإعدادات.
2. فعّل الميزات المطلوبة واختر المكوّنات.
3. احفظ. الخصومات تُطبق تلقائياً على قسائم الرواتب الجديدة.

ملخص الإيقاف السريع:
- كل ميزة لها مفتاح Enable في نفس صفحة الإعدادات.
- لإيقاف شامل: احذف السطور المشار إليها أعلاه من hooks.py ثم أعد التشغيل.
"""
