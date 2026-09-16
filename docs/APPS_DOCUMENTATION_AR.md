# -*- coding: utf-8 -*-
"""
شرح تطبيقي Navari المثبتين على site1.local
==========================================
تاريخ الإعداد: 2026-09-13
السيرفر: site1.local @ 192.168.0.248 — bench: ~/frappe-bench2


═══════════════════════════════════════════════════════════════════════════════
1) تطبيق navari-frappehr-biostar (navari_frappehr_biostar)
   https://github.com/navariltd/navari-frappehr-biostar
   الغرض: تكامل مع أجهزة بصمة Suprema BioStar 2 (واجهة TA API) لسحب سجلات
          الحضور والانصراف وإنشاء مستندات Employee Checkin تلقائياً.
═══════════════════════════════════════════════════════════════════════════════

المكونات:
---------
- DocType "Biostar Settings" (Single): إعدادات الاتصال بخادم BioStar:
    * Username / Password: بيانات دخول خادم BioStar (كلمة السر مشفرة Password field)
    * TA URL: رابط واجهة Time & Attendance (مثال: http://server:port/api أو ما شابه)
    * Start Date / End Date: نطاق جلب السجلات
    * Active: تفعيل/إيقاف التكامل (افتراضياً 0 — يجب تفعيله)
    * Last Server Status: حالة آخر اتصال (Online/Offline) — تلقائي

- controllers/utils/biostar_connector.py (class BiostarConnector):
    * login(): تسجيل الدخول إلى BioStar والحصول على كوكي الجلسة
    * get_attendance_ids(): جلب attendance_device_id لكل الموظفين النشطين
    * get_attendance_report(): طلب تقرير الحضور اليومي من BioStar (report.json)
    * create_punch_logs(): تحويل inTime/outTime إلى سجلات IN/OUT
    * create_employee_checkins(): إنشاء Employee Checkin في ERPNext (خلفية/Background Job)
    * update_last_sync_employee_date(): تحديث حقل آخر مزامنة في Employee

- controllers/biostar_calls.py:
    * get_employee_checkins(start_date, end_date, employees=None): جلب سجلات لنطاق تاريخ
    * add_checkin_logs_for_current_day(): جلب سجلات اليوم الحالي
    * check_for_yesterday_logs() / check_for_yesterday_logs_again(): جلب سجلات الأمس

- جدولة تلقائية (Cron) في hooks.py:
    * 23:10 يومياً: add_checkin_logs_for_current_day
    * 03:00 و 05:30: check_for_yesterday_logs (إعادة المحاولة لسجلات الأمس)

- زر في واجهة Employee: "Fetch Attendance" (fetch_employee_checkins.js)
  وفي قائمة Employee: إجراء جماعي "Fetch Attendance" (fetch_list.js)

ملاحظة: يتطلب أن يكون لكل موظف Attendance Device ID مطابق لمعرف المستخدم في جهاز BioStar.


═══════════════════════════════════════════════════════════════════════════════
2) تطبيق nl-attendance-timesheet (nl_attendance_timesheet)
   https://github.com/navariltd/nl-attendance-timesheet
   الغرض: أتمتة إنشاء سجلات الدوام (Timesheets) من سجلات الحضور، وحساب
          العمل الإضافي (Overtime) وربطه بقسائم الرواتب (Salary Slip).
═══════════════════════════════════════════════════════════════════════════════

المكونات:
---------
- DocType "Navari Custom Payroll Settings" (Single): إعدادات الرواتب المخصصة:
    * Maximum monthly hours: الحد الأقصى للساعات الشهرية — ما يزيد عنها يُحسب إضافياً
    * Overtime 1.5 Activity: نوع النشاط للإضافي العادي (بعد نهاية الدوام)
    * Overtime 2.0 Activity: نوع النشاط لإضافي أيام العطل الرسمية
    * Include early entry: هل تُحسب ساعات الحضور المبكر قبل بداية الدوام
    * Overtime Threshold: الحد الأدنى بالدقائق بعد نهاية الدوام لاعتبارها إضافياً (افتراضي 30)

- DocType "Timesheet Center": مركز توليد سجلات الإضافي:
    * تختار start_date و end_date ثم زر "Generate Timesheets"
    * ينشئ Timesheet لكل موظف عمل ساعات إضافية

- controllers/generate_overtime_timesheets.py:
    * generate_overtime_timesheets(start_date, end_date):
      - يقرأ سجلات Attendance (Present) في النطاق
      - إذا كان اليوم عطلة رسمية (Holiday List للموظف) → Timesheet بنشاط Overtime 2.0
      - وإلا إذا تجاوز وقت الانصراف نهاية الدوام بأكثر من Threshold → Overtime 1.5
      - ينشئ Timesheet مع time_logs ويربطه بسجل Attendance

- controllers/add_attendance_to_salary_slip.py:
    * add_attendance_data(payroll_entry): يُستدعى من زر في Payroll Entry
      ("Update Timesheet into Salary Slips") — لكل قسيمة راتب مسودة:
      - يجلب سجلات الحضور ويملأ جدول "Attendance" في القسيمة
      - يجلب سجلات الإضافي (Timesheets) ويملأ جداول "Overtime 1.5" و "Overtime 2.0"
      - يحسب: Regular Working Hours / Overtime Hours / Holiday Hours
      - قواعد الترحيل (Carry-over):
          إذا تجاوزت الساعات العادية الحد الأقصى الشهري → الفائض يتحول لإضافي
          إذا قلّت → يُكمل من ساعات الإضافي حتى الحد الأقصى

- controllers/get_employee_attendance.py:
    * get_employee_attendance(): جلب حضور الموظف مع احترام خصم الاستراحات غير مدفوعة
      (unpaid breaks) وساعات الحضور المبكر (حسب إعداد Include early entry)

- حقول مخصصة (Custom Fields) أُنشئت تلقائياً:
    * Salary Slip: تبويب "Attendance Details" (attendance, regular_overtime,
      holiday_overtime, overtime_hours, holiday_hours, hourly_rate,
      regular_working_hours, wage_based_salary_hours)
    * Attendance: payment_hours, overtime
    * Shift Type: include_unpaid_breaks, unpaid_breaks_minutes, min_hours_to_include_a_break
    * Salary Structure: wage_based_salary_hours
    * Timesheet: attendance (Link)

- DocTypes مساعدة (جداول فرعية): Regular Overtime, Holiday Overtime,
  Navari Attendance, Earned Bonus vs Attained Score

طريقة حساب الرواتب بالساعة (Wage based salary):
    Basic = hourly_rate × regular_working_hours
    Overtime 1.5 = hourly_rate × 1.5 × overtime_hours
    Holiday OT = hourly_rate × 2.0 × holiday_hours
    (hourly_rate يُجلب من Salary Structure المعين للموظف)


═══════════════════════════════════════════════════════════════════════════════
3) حالة التثبيت على site1.local
═══════════════════════════════════════════════════════════════════════════════
- navari_frappehr_biostar  (branch: version-15)  ✅ مثبت
- nl_attendance_timesheet  (branch: version-15)  ✅ مثبت
- الحقول المخصصة: 21 حقل (أُنشئت يدوياً بعد تعذر مزامنة fixtures بسبب
  كاش قديم في module_app — تم إصلاحه بإعادة بناء الكاش)
- ملاحظة: التطبيقان يتطلبان frappe >= 15 — السيرفر يعمل بـ frappe 15.92.0 ✅


═══════════════════════════════════════════════════════════════════════════════
4) تحليل: هل يمكن خصم أوقات التأخير من الراتب بنفس فكرة حساب الإضافي؟
═══════════════════════════════════════════════════════════════════════════════

نعم — الفكرة قابلة للتطبيق بالكامل وبنفس الآلية. المقارنة:

  الإضافي (Overtime) في nl-attendance-timesheet:
    - شرط: وقت الانصراف > نهاية الدوام + Overtime Threshold (مثلاً 30 دقيقة)
    - الحساب: ساعات_الإضافي = (وقت الانصراف - نهاية الدوام) بالساعات
    - المبلغ: hourly_rate × 1.5 × ساعات_الإضافي  → يُضاف كأرباح (Earnings)

  خصم التأخير (Late Deduction) — بنفس الفكرة معكوسة:
    - شرط: وقت الحضور > بداية الدوام + فترة السماح (Late Grace Period)
    - الحساب: دقائق_التأخير = (وقت الحضور - بداية الدوام - فترة السماح)
    - المبلغ: hourly_rate × معامل_الخصم × (دقائق_التأخير / 60)  → خصم (Deductions)

  خصم الغياب (Absence Deduction):
    - شرط: سجل Attendance بحالة "Absent"
    - المبلغ: daily_rate × معامل_الخصم × عدد_أيام_الغياب
      حيث daily_rate = الراتب الأساسي / عدد أيام العمل الشهرية

طريقة التنفيذ في ERPNext/FrappeHR:
    1) عند إنشاء/اعتماد Salary Slip، نجمع:
       - إجمالي دقائق التأخير من سجلات Attendance/Employee Checkin مقابل Shift Type
       - عدد أيام الغياب من Attendance (status = Absent)
    2) نحسب مبلغ الخصم = سعر الساعة (أو اليوم) × المعامل
    3) نضيف سطر خصم في جدول Deductions داخل قسيمة الراتب بمكوّن راتب
       (Salary Component) مخصص مثل "Late Deduction" و "Absence Deduction"
    4) يظهر الخصم تلقائياً في صافي الراتب (Net Pay)

    بديل: إنشاء مستند "Additional Salary" بنوع خصم لكل موظف — لكن التعديل
    المباشر في Salary Slip أدق لأنه يُحسب من نفس فترة القسيمة.

الخلاصة: نفس محرك حساب الإضافي يعمل للخصم، فقط نعكس الإشارة ونستخدم
         Salary Component من نوع Deduction بدل Earning.

═══════════════════════════════════════════════════════════════════════════════
5) التعديلات المضافة إلى hr_erp (انظر الملف HR_ERP_ADDITIONS_AR.md للتفاصيل)
═══════════════════════════════════════════════════════════════════════════════
- محرك خصم التأخير والغياب: hrms_erp/payroll_integration/late_absence_deduction.py
- توليد الإضافي من الحضور: hrms_erp/payroll_integration/overtime_timesheet.py
- مزامنة BioStar: hrms_erp/payroll_integration/biostar_sync.py
- إعدادات: DocType "HR ERP Payroll Settings" (Single)
- الترجمة العربية: hr_erp/translations/ar.csv
"""
