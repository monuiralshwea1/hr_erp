# hr_erp — HRMS Arabic Customization App

تطبيق تخصيص عربي لنظام ERPNext/HRMS على الموقع `site1.local` (فرابي v15، إدارة جديدة smart @ 192.168.0.248).

## المحتويات المثبّتة

| المكوّن | الوصف |
|---|---|
| **Employee Document** | DocType جديد — مستندات الموظف مع حالة تلقائية (ساري / قريب الانتهاء / منتهي) ونظام ترقيم `HRD-YYYY-####` |
| **بوابة الموارد البشرية (Workspace)** | صفحة HR Portal: 8 بطاقات، 4 اختصارات، 12 عدداً، 9 رسوم بيانية |
| **Number Cards (12)** | بطاقات عدّ/جمع، منها 3 بطاقات مخصّصة (Custom) تستدعي دوال السيرفر |
| **Dashboard Charts (9)** | رسوم بيانية عن الموظفين والحضور والإجازات والرواتب والتعيينات |
| **Print Formats (10)** | قوالب طباعة عربية RTL (بطاقة موظف، طلب إجازة، كشف حضور، قسيمة راتب، ...) |
| **Notifications (2)** | إشعار عند تقديم إجازة/مصروفات إلى الموفّق |
| **doc_events** | تحقّقات وقيم افتراضية ذكية للموظف والإجازات والحضور والمصروفات والتوظيف |
| **Translations** | ترجمات عربية↔إنجليزية لمركّبات الواجهة |
| **CSS/JS** | `hr_style.css` و `hr_common.js` مرفقان على مستوى التطبيق |

## البنية (المسارات الصحيحة)

التطبيق اسم حزمة بايثون `hr_erp` ويحتوي موديول `hrms_erp` داخله.
**أي مسار استيراد يجب أن يكون بالشكل التالي** (الخطأ الشائع حذف `hr_erp.`):

```
hr_erp.hrms_erp.api.smart_defaults.count_on_leave_today        # دالة number card
hr_erp.hrms_erp.api.smart_defaults.validate_leave              # doc_event
hr_erp.hrms_erp.install.after_install                          # after_install
```

المسار `hrms_erp.api...` **غير صالح** ويُنتج الخطأ:
`Failed to get method ... لم يتم تثبيت التطبيق hrms_erp`

ملفات البنية:
```
apps/hr_erp/
├── hr_erp/                  # حزمة بايثون (app_name = hr_erp)
│   ├── hooks.py             # doc_events / after_install / assets
│   ├── hrms_erp/            # الموديول
│   │   ├── install.py       # after_install (ينشئ كل شيء)
│   │   ├── api/smart_defaults.py
│   │   └── doctype/employee_document/
│   └── public/ (css/js)
```

## تثبيت جديد (من الصفر)

```bash
cd /home/newsmart/frappe-bench2
bench --site site1.local install-app hr_erp
bench --site site1.local migrate
bench --site site1.local clear-cache
bench build
```

`after_install` ينشئ: الـ DocType، الـ 12 Number Card، الـ 9 Charts، الـ Workspace، الـ 10 Print Formats، الـ Notification، الترجمات. كل الدوال **idempotent** (تتخطى الموجود).

## ملاحظات تصحيح مهمة

1. **رقم صفحة HR Portal:** يجب أن يتطابق `name == label == title` وإلا تُفشل واجهة الفرابي
   التوجيه (`/app/بوابة-الموارد-البشرية`) برسالة "غير موجود".
2. **Number Cards المخصّصة:** تُخزّن مسار الميثود في حقل `method` ويجب أن يكون
   بالصيغة الكاملة `hr_erp.hrms_erp.api.smart_defaults.count_*`.
3. **Charts من نوع Group By:** تستخدم `group_by_based_on` وليس `based_on`.
4. **Print Formats:** لا تُستخدم حقول غير موجودة في الـ DocType المعني (مثل أعمدة
   Payroll child على Salary Slip، أو حقول Separation). تأكّد دائماً عبر `frappe.get_meta`.
5. **Notifications:** المستلم عبر `receiver_by_document_field` (leave_approver / expense_approver).

## التراجع (Rollback)

إزالة كل ما أنشأه التطبيق يدوياً (لا يوجد أمر تلقائي):

```bash
cd /home/newsmart/frappe-bench2
# حذف السجلات التي أنشأها hr_erp (تحقّق من أسماء الأدلة أولاً)
bench --site site1.local console <<'EOF'
import frappe
for dt in ["Number Card", "Dashboard Chart", "Print Format", "Notification", "Translation"]:
    for name in frappe.get_all(dt, filters={"module": "hrms-erp"}):
        frappe.delete_doc(dt, name, force=1, ignore_permissions=True)
frappe.delete_doc("Workspace", "بوابة الموارد البشرية", force=1, ignore_permissions=True)
frappe.db.commit()
EOF

# ثم أزل التطبيق من الموقع
bench --site site1.local uninstall-app hr_erp
```

ملاحظة: `uninstall-app` يمسح جداول DocType المخصّصة (Employee Document). النسخ الاحتياطي قبل أي إجراء:
```bash
bench --site site1.local backup
```

## الفحص/التحقق

```bash
# مسارات الـ hooks تحلّ بشكل صحيح
printf 'exec(open("/tmp/_v.py").read(), globals())\n' | bench --site site1.local console
# /tmp/_v.py:
# import frappe
# print(frappe.get_attr("hr_erp.hrms_erp.api.smart_defaults.count_expiring_contracts")())
```
