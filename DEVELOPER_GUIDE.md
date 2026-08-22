# دليل التطوير وحل الأخطاء - تطبيق hr_erp
## Shumul HR Customization App

---

## الفصل الأول: مقدمة عن التطبيق

تطبيق **hr_erp** هو تطبيق مخصص لـ Frappe/ERPNext يحتوي على تخصيصات عربية
للموارد البشرية. يُشغّل على Frappe 15.92.0 و ERPNext 15.95.2 و HRMS 15.63.2.

**معلومات البيئة:**
- السيرفر: `192.168.0.248` (المستخدم: `newsmart`، كلمة المرور: `123456`)
- مسار Bench: `/home/newsmart/frappe-bench2`
- موقع التطوير: `site1.local` (المنفذ: 8001)
- موقع الإنتاج: `alshumul.newsmart.local`

**التبعيات:**
- `frappe` → `erpnext` → `hrms` → `hr_erp`
- `tageep` → تطبيق منفصل للرواتب

---

## الفصل الثاني: هيكل التطبيق

### 2.1 هيكل المجلدات العام

```
hr_erp/                          # مجلد التطبيق الرئيسي
├── __init__.py                  # ملف فارغ (يُعرّف أن هذا مجلد بايثون)
├── hooks.py                     # ملف الإعدادات الرئيسي - يربط كل شيء
├── modules.txt                  # يحتوي: "hrms-erp" (اسم الوحدة)
├── fixtures/                    # ملفات التصدير (JSON)
│   ├── custom_field.json        # الحقول المخصصة
│   ├── client_script.json       # سكربتات العميل
│   ├── server_script.json       # سكربتات الخادم
│   ├── doctype.json             # DocTypes
│   ├── report.json              # التقارير
│   ├── workspace.json           # صفحات العمل
│   ├── workflow.json            # سير العمل
│   └── ... (12 ملف)
├── translations/
│   └── ar.csv                   # الترجمات العربية
└── hrms_erp/                    # مجلد الوحدة الرئيسي
    ├── __init__.py
    ├── custom_fields.py         # تعريف الحقول المخصصة
    ├── install.py               # ما يحدث بعد التثبيت
    ├── api/                     # طبقات API
    ├── multi_period_shift/      # نظام النوبات المتعددة الفترات
    ├── doctype/                 # جميع DocTypes (52 نوع)
    ├── public/js/               # سكربتات العميل (21 ملف)
    ├── report/                  # التقارير (22 مجلد)
    └── workspace/               # ملفات صفحات العمل (7 ملفات)
```

### 2.2 شرح كل ملف رئيسي

#### `hooks.py` - ملف الإعدادات الرئيسي
هذا أهم ملف في التطبيق. يربط كل شيء بـ Frappe:

```python
# مثال على hooks.py:

app_name = "hr_erp"
app_title = "hrms-erp"
app_publisher = "moneer"

# تحميل ملفات JS/CSS عامة
app_include_js = "/assets/hr_erp/js/hr_common.js"
app_include_css = "/assets/hr_erp/css/hr_style.css"

# تجاوز كلاسات DocTypes معينة
override_doctype_class = {
    "Shift Type": "hr_erp.hrms_erp.multi_period_shift.shift_type_override.CustomShiftType",
    "Employee Checkin": "hr_erp.hrms_erp.multi_period_shift.employee_checkin_override.CustomEmployeeCheckin",
}

# إضافة سكربت JS معين لـ DocType معين
doctype_js = {
    "Shift Type": ["public/js/shift_type_multi_period.js"],
    "Short Leave": ["public/js/short_leave.js"],
}

# أحداث المستندات (Doc Events)
doc_events = {
    "Attendance": {
        "validate": "hr_erp.hrms_erp.api.smart_defaults.validate_attendance",
    },
    "Leave Application": {
        "validate": "hr_erp.hrms_erp.api.server_scripts.validate_leave_application",
        "on_submit": "hr_erp.hrms_erp.api.server_scripts.leave_short_leaves",
    },
}

# ما يحدث بعد التثبيت
after_install = "hr_erp.hrms_erp.install.after_install"

# ما يحدث بعد كل migrate
after_migrate = ["hr_erp.hrms_erp.multi_period_shift.custom_fields.create_custom_fields"]
```

#### `install.py` - ما يحدث بعد التثبيت
يُنفَّذ مرة واحدة فقط بعد تثبيت التطبيق:

```python
def after_install():
    # إنشاء workspace
    # إنشاء custom fields
    # إنشاء server scripts
    # إنشاء client scripts
    # إنشاء سير العمل
    pass
```

#### `custom_fields.py` - الحقول المخصصة
يُنشئ حقولاً مخصصة على DocTypes موجودة:

```python
import frappe

def create_custom_fields():
    custom_fields = {
        "Attendance": [
            {
                "fieldname": "total_late_minutes",
                "fieldtype": "Float",
                "label": "Total Late Minutes",
                "insert_after": "early_exit",
            },
            {
                "fieldname": "attendance_period_details",
                "fieldtype": "Table",
                "label": "Attendance Period Details",
                "options": "Attendance Period Detail",
            },
        ],
    }
    frappe.flags.ignore_validate_connection = True
    frappe.db.commit()
    for doctype, fields in custom_fields.items():
        for field in fields:
            if not frappe.db.exists("Custom Field", {"dt": doctype, "fieldname": field["fieldname"]}):
                frappe.get_doc({
                    "doctype": "Custom Field",
                    "dt": doctype,
                    **field,
                }).insert(ignore_permissions=True)
    frappe.db.commit()
```

### 2.3 أنواع الملفات الرئيسية

| الملف | الوظيفة | مثال |
|-------|---------|------|
| `hooks.py` | ربط التطبيق بـ Frappe | تحميل JS، تجاوز DocTypes |
| `custom_fields.py` | إضافة حقول جديدة لـ DocTypes موجودة | إضافة `total_late_minutes` لـ Attendance |
| `install.py` | التهيئة بعد التثبيت | إنشاء workspace، سكربتات |
| `doctype/xxx/xxx.py` | منطق DocType (Python) | validate, before_save |
| `doctype/xxx/xxx.js` | واجهة DocType (JavaScript) | تحكم في الحقول والconomic |
| `public/js/xxx.js` | سكربتات عميل مشتركة | تُحمّل عبر hooks |
| `report/xxx/xxx.py` | منطق التقارير | get_data, get_columns |
| `api/*.py` | دوال مشتركة | 처리 الأحداث وال确证 |

---

## الفصل الثالث: كيف تنشئ ملفات وترفعها للسيرفر

### 3.1 الأداة المستخدمة للنقل
نستخدم **pscp** و **plink** من PuTTY:

```powershell
# مسار الأدوات
C:\Program Files (x86)\PuTTY\pscp.exe
C:\Program Files (x86)\PuTTY\plink.exe
```

### 3.2 رفع ملف من الكمبيوتر للسيرفر

```powershell
# الأمر:
& "C:\Program Files (x86)\PuTTY\pscp.exe" -batch -pw 123456 "مسار_الملف_محلياً" newsmart@192.168.0.248:مسار_الملف_على_السيرفر

# مثال: رفع ملف hooks.py
& "C:\Program Files (x86)\PuTTY\pscp.exe" -batch -pw 123456 "C:\Users\ebh\Desktop\erp\stage\hr_erp_app\hr_erp\hooks.py" newsmart@192.168.0.248:/home/newsmart/frappe-bench2/apps/hr_erp/hooks.py

# مثال: رفع سكربت بايثون
& "C:\Program Files (x86)\PuTTY\pscp.exe" -batch -pw 123456 "C:\Users\ebh\Desktop\erp\stage\my_script.py" newsmart@192.168.0.248:/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/my_script.py
```

### 3.3 تنفيذ أمر على السيرفر

```powershell
# الأمر:
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "الأمر"

# مثال: حفظ الكاش
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2 && bench --site site1.local clear-cache 2>&1"

# مثال: تنفيذ سكربت بايثون
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2 && bench --site site1.local execute hr_erp.my_module.my_script.execute 2>&1"
```

### 3.4 رفع ملف + تنفيذ (دفعة واحدة)

```powershell
& "C:\Program Files (x86)\PuTTY\pscp.exe" -batch -pw 123456 "C:\path\to\script.py" newsmart@192.168.0.248:/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/script.py; plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2 && bench --site site1.local execute hr_erp.script.execute 2>&1"
```

### 3.5 التعامل مع Git

```powershell
# رفع تعديل + حفظ على السيرفر
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2/apps/hr_erp && git add -A && git commit -m 'description' 2>&1"

# رفع إلى GitHub (يتطلب توكن)
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2/apps/hr_erp && git push origin master 2>&1"
```

---

## الفصل الرابع: أوامر Frappe الكاملة

### 4.1 أوامر Bench الأساسية

```bash
# بدء تشغيل الموقع
bench --site site1.local serve --port 8001

# حفظ الكاش (يجب تنفيذه بعد أي تغيير)
bench --site site1.local clear-cache

# تحديث قاعدة البيانات (بعد تغيير DocTypes)
bench --site site1.local migrate

# تثبيت/تحديث التطبيق
bench --site site1.local install-app hr_erp
bench --site site1.local update

# تشغيل سكربت بايثون
bench --site site1.local execute hr_erp.hrms_erp.my_module.my_function

# فتح كونسول بايثون
bench --site site1.local console

# التحقق من صحة التطبيق
bench --site site1.local doctor

# عرض سجلات الأخطاء
bench --site site1.local mariadb
```

### 4.2 أوامر Frappe من بايثون

```python
import frappe

# ============ البحث والقراءة ============

# التحقق من وجود مستند
frappe.db.exists("Employee", "HR-EMP-00001")
frappe.db.exists("Employee", {"employee_name": "أحمد"})

# جلب قيمة واحدة
frappe.db.get_value("Employee", "HR-EMP-00001", "employee_name")

# جلب عدة حقول
frappe.db.get_value("Employee", "HR-EMP-00001", ["employee_name", "department", "designation"], as_dict=True)

# استعلام SQL مباشر
result = frappe.db.sql("SELECT name, employee_name FROM tabEmployee LIMIT 5", as_dict=True)

# استعلام مع شروط
result = frappe.db.sql("""
    SELECT name, employee_name FROM tabEmployee
    WHERE department = %s AND status = 'Active'
""", ("IT Department",), as_dict=True)

# فرز/بحث متقدم
employees = frappe.get_all("Employee",
    filters={"status": "Active", "company": "Shumul"},
    fields=["name", "employee_name", "department"],
    order_by="employee_name asc",
    limit_page_length=20,
)

# ============ إنشاء وتعديل ============

# إنشاء مستند جديد
doc = frappe.get_doc({
    "doctype": "Employee",
    "employee_name": "محمد أحمد",
    "company": "Shumul",
    "department": "IT",
})
doc.insert()  # يُنشئ المستند
doc.submit()  # يُرسل المستند (إذا كان DocType يدعم الإرسال)

# حفظ تعديل
doc = frappe.get_doc("Employee", "HR-EMP-00001")
doc.employee_name = "محمد أحمد الجديد"
doc.save()

# حفظ سريع بدون تحميل المستند كاملاً
frappe.db.set_value("Employee", "HR-EMP-00001", "employee_name", "محمد")

# حذف مستند
frappe.delete_doc("My DocType", "DOC-NAME-001")

# ============ صلاحيات ============

# تنفيذ بأذونات مخصصة
doc.insert(ignore_permissions=True)

# التحقق من الصلاحيات
frappe.has_permission("Employee", "read")
frappe.has_permission("Employee", "write")

# ============ الكاش ============

# مسح الكاش (مهم بعد التغييرات)
frappe.clear_cache()

# مسح كاش مستند معين
frappe.clear_cache(doctype="Employee")

# ============ أحداث المستندات ============

# إطلاق حدث
frappe.publish_realtime("show_alert", {"message": "تم الحفظ بنجاح!", "alert_type": "green"})

# ============ التحقق من الأخطاء ============

# رمي خطأ
frappe.throw("حدث خطأ! الرجاء التحقق من البيانات")

# طباعة رسالة
frappe.msgprint("تم الحفظ بنجاح")

# ============ 작업 ============

# بدء عملية
task = frappe.enqueue("my_module.my_function", queue="default", timeout=300)

# ============ ملفات_workbench ============

# حفظ workspace
ws = frappe.get_doc("Workspace", "Shumul - HR")
ws.append("shortcuts", {
    "type": "Report",
    "name": "My Report",
    "link_to": "My Report",
    "label": "تقريري",
})
ws.save(ignore_permissions=True)
```

### 4.3 أوامر SQL المفيدة

```sql
-- عرض هيكل جدول
SHOW COLUMNS FROM tabEmployee;

-- البحث عن حقل معين
SHOW COLUMNS FROM tabAttendance LIKE '%shift%';

-- عرض عدد السجلات
SELECT COUNT(*) FROM tabEmployee WHERE status = 'Active';

-- حذف سجلات (小心!)
DELETE FROM tabMyTable WHERE field = 'value';

-- تحديث سجلات
UPDATE tabAttendance SET shift = 'Morning' WHERE shift IS NULL;

-- فحص جداول Child
SELECT parent, COUNT(*) FROM `tabAttendance Period Detail` GROUP BY parent;
```

---

## الفصل الخامس: إنشاء أنواع مختلفة من التخصيصات

### 5.1 إنشاء DocType جديد

**الملفات المطلوبة:**
```
hrms_erp/doctype/my_doctype/
├── __init__.py
├── my_doctype.json          # تعريف DocType
├── my_doctype.py            # منطق بايثون
└── my_doctype.js            # واجهة جافاسكريبت
```

**ملف JSON:**
```json
{
  "name": "My DocType",
  "module": "HRMS-ERP",
  "doctype": "DocType",
  "engine": "InnoDB",
  "istable": 0,
  "autoname": "field:my_field",
  "field_order": ["my_field", "description"],
  "fields": [
    {"fieldname": "my_field", "fieldtype": "Data", "label": "My Field", "reqd": 1},
    {"fieldname": "description", "fieldtype": "Small Text", "label": "Description"}
  ],
  "permissions": [{"role": "HR Manager", "read": 1, "write": 1, "create": 1}]
}
```

**ملف Python:**
```python
import frappe
from frappe.model.document import Document

class MyDocType(Document):
    def validate(self):
        """يُنفَّذ قبل الحفظ"""
        if not self.my_field:
            frappe.throw("My Field مطلوب!")

    def before_save(self):
        """يُنفَّذ قبل الحفظ مباشرة"""
        pass

    def after_insert(self):
        """يُنفَّذ بعد الإنشاء"""
        pass

    def on_submit(self):
        """يُنفَّذ عند الإرسال"""
        pass

    def on_cancel(self):
        """يُنفَّذ عند الإلغاء"""
        pass
```

**ملف JavaScript:**
```javascript
frappe.ui.form.on('My DocType', {
    refresh(frm) {
        // يُنفَّذ عند فتح المستند
    },

    my_field(frm) {
        // يُنفَّذ عند تغيير my_field
        if (frm.doc.my_field) {
            frm.set_value('description', 'تم اختيار: ' + frm.doc.my_field);
        }
    }
});
```

### 5.2 إنشاء Child Table

```json
{
  "name": "My Child Table",
  "module": "HRMS-ERP",
  "istable": 1,
  "fields": [
    {"fieldname": "item", "fieldtype": "Data", "label": "Item", "in_list_view": 1},
    {"fieldname": "amount", "fieldtype": "Float", "label": "Amount", "in_list_view": 1}
  ]
}
```

**ربط Child Table بـ DocType رئيسي:**
```json
{
  "fieldname": "my_items",
  "fieldtype": "Table",
  "label": "My Items",
  "options": "My Child Table"
}
```

### 5.3 إنشاء Custom Field (حقل مخصص)

```python
# في custom_fields.py
custom_fields = {
    "Attendance": [  # DocType المطلوب تعديل他的
        {
            "fieldname": "my_custom_field",
            "fieldtype": "Data",
            "label": "My Custom Field",
            "insert_after": "existing_field_name",  # بعد أي حقل
        },
        {
            "fieldname": "my_link_field",
            "fieldtype": "Link",
            "label": "My Link",
            "options": "Employee",
            "insert_after": "my_custom_field",
        },
        {
            "fieldname": "my_table_field",
            "fieldtype": "Table",
            "label": "My Table",
            "options": "My Child Table",
        },
    ],
}
```

**أنواع الحقول المتاحة:**
| Type | الوصف | options |
|------|-------|---------|
| `Data` | نص عادي | - |
| `Text` | نص طويل | - |
| `Small Text` | نص قصير | - |
| `Int` | عدد صحيح | - |
| `Float` | عدد عشري | - |
| `Check` | مربع اختيار (0/1) | - |
| `Date` | تاريخ | - |
| `Datetime` | تاريخ ووقت | - |
| `Time` | وقت | - |
| `Select` | قائمة منسدلة | `Option1\nOption2\nOption3` |
| `Link` | ربط بـ DocType آخر | `Employee` |
| `Table` | جدول Child | `My Child Table` |
| `Section Break` | فاصل قسم | - |
| `Column Break` | فاصل عمود | - |

### 5.4 إنشاء Report (تقرير)

**الملفات المطلوبة:**
```
hrms_erp/report/my_report/
├── __init__.py
├── my_report.json     # تعريف التقرير
├── my_report.py       # منطق بايثون
└── my_report.js       # واجهة (اختياري)
```

**ملف JSON:**
```json
{
  "doctype": "Report",
  "name": "My Report",
  "module": "HRMS-ERP",
  "title": "تقريري",
  "report_type": "Script Report",
  "ref_doctype": "Attendance",
  "is_standard": "Yes",
  "filters": [
    {"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1},
    {"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1},
    {"fieldname": "employee", "fieldtype": "Link", "label": "Employee", "options": "Employee"}
  ],
  "permissions": [{"role": "HR Manager", "read": 1}]
}
```

**ملف Python:**
```python
import frappe
from frappe import _

def execute(filters=None):
    if not filters:
        filters = {}

    columns = get_columns(filters)
    data = get_data(filters)
    chart = get_chart(data) if data else None

    return columns, data, None, chart

def get_columns(filters):
    return [
        {"label": _("Employee"), "fieldname": "employee", "fieldtype": "Link", "options": "Employee", "width": 90},
        {"label": _("Name"), "fieldname": "employee_name", "fieldtype": "Data", "width": 150},
        {"label": _("Date"), "fieldname": "attendance_date", "fieldtype": "Date", "width": 100},
        {"label": _("Status"), "fieldname": "status", "fieldtype": "Data", "width": 80},
    ]

def get_data(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("from_date"):
        conditions.append("a.attendance_date >= %(from_date)s")
        values["from_date"] = filters["from_date"]

    if filters.get("to_date"):
        conditions.append("a.attendance_date <= %(to_date)s")
        values["to_date"] = filters["to_date"]

    data = frappe.db.sql("""
        SELECT a.employee, a.employee_name, a.attendance_date, a.status
        FROM tabAttendance a
        WHERE a.docstatus = 1 AND {conditions}
        ORDER BY a.employee, a.attendance_date
    """.format(conditions=" AND ".join(conditions)), values, as_dict=True)

    return data

def get_chart(data):
    present = sum(1 for d in data if d.status == "Present")
    absent = sum(1 for d in data if d.status == "Absent")
    return {
        "data": {
            "labels": ["Present", "Absent"],
            "datasets": [{"values": [present, absent]}],
        },
        "type": "donut",
        "colors": ["#28a745", "#dc3545"],
    }
```

**ملاحظة مهمة:** إذا كان `is_standard="Yes"`، يحمّل السكربت من ملف `.py`
إذا كان `is_standard="No"`، يجب حفظ السكربت في حقل `report_script` في قاعدة البيانات.

### 5.5 إضافة اختصار Report إلى Workspace

```python
import frappe

ws = frappe.get_doc("Workspace", "Shumul - HR")
ws.append("shortcuts", {
    "type": "Report",
    "name": "My Report",
    "link_to": "My Report",
    "label": "تقريري",
    "icon": "octicon octicon-graph",
    "color": "#5e64ff",
})
ws.save(ignore_permissions=True)
frappe.db.commit()
```

### 5.6 إنشاء Client Script

```python
import frappe

frappe.get_doc({
    "doctype": "Client Script",
    "name": "My Script",
    "dt": "Employee",           # DocType المطلوب
    "script_type": "Client",    # Client Script
    "script": """
frappe.ui.form.on('Employee', {
    refresh(frm) {
        if (frm.doc.status === 'Active') {
            frm.set_intro('هذا الموظف نشط');
        }
    }
});
""",
    "enabled": 1,
}).insert(ignore_permissions=True)
```

### 5.7 إنشاء Server Script

```python
import frappe

frappe.get_doc({
    "doctype": "Server Script",
    "name": "My Server Script",
    "script_type": "DocType Event",
    "reference_doctype": "Attendance",
    "doctype_event": "validate",
    "script": """
employee_name = frappe.db.get_value("Employee", doc.employee, "employee_name")
if not employee_name:
    frappe.throw("Employee not found!")
""",
    "enabled": 1,
}).insert(ignore_permissions=True)
```

---

## الفصل السادس: حل الأخطاء الشائعة

### 6.1 خطأ: Unknown column in 'SELECT'

**الخطأ:**
```
pymysql.err.OperationalError: (1054, "Unknown column 'e.is_manager' in 'SELECT'")
```

**السبب:** حقل غير موجود في الجدول.

**الحل:**
```python
# 1. افحص الأعمدة الموجودة:
frappe.db.sql("SHOW COLUMNS FROM tabEmployee", as_dict=True)

# 2. ابحث عن الحقل البديل:
frappe.db.sql("SHOW COLUMNS FROM tabEmployee LIKE '%manager%'", as_dict=True)

# 3. استبدل في السكربت:
# ❌ القديم: e.is_manager
# ✅ الجديد: CASE WHEN e.reports_to IS NOT NULL THEN 1 ELSE 0 END AS is_manager

# أو استخدم الحقل الصحيح:
# ❌ القديم: e.fingerprint_id
# ✅ الجديد: e.biometric_fingerprint_id
```

**قاعدة:** دائماً افحص `SHOW COLUMNS FROM tabX` قبل استخدام حقل.

### 6.2 خطأ: Unknown column in 'WHERE'

**الخطأ:**
```
pymysql.err.OperationalError: (1054, "Unknown column 'a.shift_type' in 'SELECT'")
```

**السبب:** `tabAttendance` يستخدم `shift` وليس `shift_type`.

**الحل:**
```python
# ❌ القديم
"a.shift_type"

# ✅ الجديد (استخدم الحقل الصحيح في tabAttendance)
"a.shift"

# في شروط WHERE:
# ❌ القديم
conditions.append("a.shift_type = %(shift_type)s")

# ✅ الجديد
conditions.append("a.shift = %(shift_type)s")
```

### 6.3 خطأ: Not allowed source type: NoneType

**الخطأ:**
```
TypeError: Not allowed source type: "NoneType".
```

**السبب:** تقرير Script Report أُنشئ بدون محتوى سكربت (`report_script=None`).

**الحل:**
```python
# إذا كان is_standard="No"، يجب حفظ السكربت في DB:
frappe.db.set_value("Report", "My Report", "is_standard", "Yes")

# أو اقرأ ملف .py واحفظه:
with open("path/to/my_report.py") as f:
    script = f.read()
frappe.db.set_value("Report", "My Report", "report_script", script)
```

**القاعدة:** التقارير بـ `is_standard="Yes"` تحمل السكربت من ملف `.py` على القرص.

### 6.4 خطأ: 'str' object does not support item assignment

**الخطأ:**
```
TypeError: 'str' object does not support item assignment
```

**السبب:** تمرير نص JSON بدلاً من قائمة dict لحقل Child Table.

**الحل:**
```python
# ❌ القديم: تمرير JSON string
"attendance_period_details": json.dumps(period_details_list)

# ✅ الجديد: تمرير قائمة dict مباشرة
"attendance_period_details": period_details_list
```

### 6.5 خطأ: Overlapping Shifts

**الخطأ:**
```
OverlappingShiftError: Employee already has an active Shift
```

**السبب:** موظف لديه بالفعل نوبة عمل تتداخل مع النوبة الجديدة.

**الحل:**
```python
# 1. ألغِ النوبات القديمة أولاً:
existing = frappe.db.sql("""
    SELECT name FROM `tabShift Assignment`
    WHERE employee = %s AND status = 'Active'
    AND start_date <= %s AND (end_date IS NULL OR end_date >= %s)
""", (employee, end_date, start_date), as_dict=True)

for ea in existing:
    frappe.db.set_value("Shift Assignment", ea.name, "status", "Inactive")
    frappe.db.set_value("Shift Assignment", ea.name, "end_date", yesterday)

# 2. ثم أنشئ النوبة الجديدة
```

### 6.6 خطأ: Validation Error في Select field

**الخطأ:**
```
ValidationError: Row #5: Status cannot be "Early Exit"
```

**السبب:** القيمة غير موجودة في خيارات الحقل Select.

**الحل:**
```python
# 1. افحص الخيارات المتاحة:
field = frappe.get_meta("Attendance Period Detail").get_field("period_status")
print(field.options)
# النتيجة: "Present\nLate\nAbsent\nPartial\nMissing Checkin\nBreak\nOn Leave\nHoliday\nOvertime"

# 2. استخدم قيمة صحيحة:
# ❌ القديم: "Early Exit"
# ✅ الجديد: "Partial"
```

### 6.7 خطأ: Please set the document name

**الخطأ:**
```
ValidationError: Please set the document name
```

**السبب:** DocType يستخدم `autoname = "prompt"` (يتطلب تعيين الاسم يدوياً).

**الحل:**
```python
# ❌ القديم
doc = frappe.get_doc({"doctype": "Shift Type", "shift_type": "My Shift"})

# ✅ الجديد: أضف حقل name
doc = frappe.get_doc({
    "doctype": "Shift Type",
    "name": "My Shift",          # ← مطلوب مع autoname="prompt"
    "shift_type": "My Shift",
})
```

### 6.8 خطأ: Latitude and longitude values required

**الخطأ:**
```
ValidationError: Latitude and longitude values are required for checking in.
```

**السبب:** Employee Checkin يتحقق من الموقع الجغرافي.

**الحل:**
```python
# في Override Class:
class CustomEmployeeCheckin(EmployeeCheckin):
    def validate_distance_from_shift_location(self):
        """تخطي التحقق من الموقع - يتم التعامل معه عبر جهاز البصمة"""
        pass
```

### 6.9 خطأ: Group By مع alias

**الخطأ:**
```
pymysql.err.OperationalError: (1054, "Unknown column 'is_manager' in 'group statement'"
```

**السبب:** MySQL لا يدعم استخدام aliases في GROUP BY.

**الحل:**
```sql
-- ❌ القديم (في SELECT و GROUP BY):
SELECT ... CASE WHEN ... END AS is_manager, ...
GROUP BY ... CASE WHEN ... END AS is_manager, ...

-- ✅ الجديد (حذف alias من GROUP BY فقط):
SELECT ... CASE WHEN ... END AS is_manager, ...
GROUP BY ... CASE WHEN ..., ...
```

### 6.10 خطأ: LinkValidationError

**الخطأ:**
```
LinkValidationError: Could not find Row #3: Link To: Multi-Period Attendance
```

**السبب:** حقل Link يشير لـ DocType غير موجود.

**الحل:**
```python
# 1. افحص وجود المستند:
frappe.db.exists("Report", "Multi-Period Attendance")  # None = غير موجود

# 2. أنشئ المستند أولاً:
frappe.get_doc({
    "doctype": "Report",
    "report_name": "Multi-Period Attendance",
    # ... باقي البيانات
}).insert(ignore_permissions=True)

# 3. ثم أضف الاختصار
```

---

## الفصل السابع: مثال عملي كامل - إنشاء تقرير من الصفر

### الخطوة 1: إنشاء المجلد والملفات

```
hrms_erp/report/my_new_report/
├── __init__.py         (فارغ)
├── my_new_report.json
├── my_new_report.py
└── my_new_report.js    (اختياري)
```

### الخطوة 2: ملف JSON

```json
{
  "name": "My New Report",
  "module": "HRMS-ERP",
  "doctype": "Report",
  "report_type": "Script Report",
  "ref_doctype": "Attendance",
  "is_standard": "Yes",
  "filters": [
    {"fieldname": "from_date", "fieldtype": "Date", "label": "من تاريخ", "reqd": 1},
    {"fieldname": "to_date", "fieldtype": "Date", "label": "إلى تاريخ", "reqd": 1}
  ],
  "permissions": [{"role": "HR Manager", "read": 1}]
}
```

### الخطوة 3: ملف Python

```python
import frappe

def execute(filters=None):
    columns = [
        {"label": "الموظف", "fieldname": "employee", "fieldtype": "Data", "width": 100},
        {"label": "التاريخ", "fieldname": "date", "fieldtype": "Date", "width": 100},
        {"label": "الحالة", "fieldname": "status", "fieldtype": "Data", "width": 80},
    ]

    data = frappe.db.sql("""
        SELECT employee, attendance_date as date, status
        FROM tabAttendance
        WHERE docstatus = 1
        AND attendance_date BETWEEN %(from_date)s AND %(to_date)s
    """, filters, as_dict=True)

    return columns, data, None, None
```

### الخطوة 4: رفع للسيرفر

```powershell
# 1. ارفع المجلد كاملاً
& "C:\Program Files (x86)\PuTTY\pscp.exe" -batch -pw 123456 -r "C:\Users\ebh\Desktop\erp\stage\hr_erp_app\hr_erp\hrms_erp\report\my_new_report" newsmart@192.168.0.248:/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/hrms_erp/report/my_new_report

# 2. حفظ الكاش
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2 && bench --site site1.local clear-cache 2>&1"

# 3. اختبار التقرير
plink.exe -batch -pw 123456 newsmart@192.168.0.248 "cd /home/newsmart/frappe-bench2 && bench --site site1.local execute hr_erp.hrms_erp.report.my_new_report.my_new_report.execute 2>&1"
```

### الخطوة 5: ربط التقرير في قاعدة البيانات

```python
import frappe
frappe.get_doc({
    "doctype": "Report",
    "report_name": "My New Report",
    "module": "hrms-erp",
    "title": "تقريري الجديد",
    "report_type": "Script Report",
    "ref_doctype": "Attendance",
    "is_standard": "Yes",
    "filters": [
        {"fieldname": "from_date", "fieldtype": "Date", "label": "From Date", "reqd": 1},
        {"fieldname": "to_date", "fieldtype": "Date", "label": "To Date", "reqd": 1},
    ],
    "permissions": [{"role": "HR Manager", "read": 1}],
}).insert(ignore_permissions=True)
frappe.db.commit()
```

### الخطوة 6: إضافة اختصار في Workspace

```python
ws = frappe.get_doc("Workspace", "Shumul - HR")
ws.append("shortcuts", {
    "type": "Report",
    "name": "My New Report",
    "link_to": "My New Report",
    "label": "تقريري الجديد",
})
ws.save(ignore_permissions=True)
```

---

## الفصل الثامن: أنماط التكرار الشائعة

### 8.1 حل مشكلة تكرار المفتاح في Dict

```python
# ❌ خطأ: مفتاح مكرر
filters = {
    "time": (">=", start),
    "time": ("<=", end),  # ← يُ他是一个覆盖 previous
}

# ✅ صحيح: استخدام OR
filters = [
    ["time", ">=", start],
    ["time", "<=", end],
]
```

### 8.2 التعامل مع Child Table

```python
# قراءة بيانات child table
doc = frappe.get_doc("Attendance", att_name)
for child in doc.attendance_period_details:
    print(child.period_name, child.period_status)

# إنشاء مستند مع child table
doc = frappe.get_doc({
    "doctype": "Attendance",
    "employee": "HR-EMP-00001",
    "attendance_date": "2026-08-20",
    "attendance_period_details": [
        {"period_name": "Morning", "period_number": 1, "period_status": "Present"},
        {"period_name": "Evening", "period_number": 2, "period_status": "Present"},
    ],
})
doc.insert()
```

### 8.3 بناء استعلام ديناميكي

```python
def get_conditions(filters):
    conditions = ["1=1"]
    values = {}

    if filters.get("employee"):
        conditions.append("a.employee = %(employee)s")
        values["employee"] = filters["employee"]

    if filters.get("department"):
        conditions.append("a.department = %(department)s")
        values["department"] = filters["department"]

    return " AND ".join(conditions), values

conditions, values = get_conditions(filters)
data = frappe.db.sql(f"SELECT ... WHERE {conditions}", values, as_dict=True)
```

---

## الفصل التاسع: ملخص hooks.py - كل hook ومشروحي

```python
# 1. تحميل ملفات عامة
app_include_js = "/assets/hr_erp/js/hr_common.js"
app_include_css = "/assets/hr_erp/css/hr_style.css"

# 2. تجاوز كلاسات DocTypes (الأكثر أهمية)
override_doctype_class = {
    "Shift Type": "hr_erp...shift_type_override.CustomShiftType",
    "Employee Checkin": "hr_erp...employee_checkin_override.CustomEmployeeCheckin",
}

# 3. حقن JS في DocType معين
doctype_js = {
    "Leave Application": ["public/js/leave_application_with_short_leaves.js"],
}

# 4. أحداث المستندات
doc_events = {
    "Leave Application": {
        "validate": "...",        # قبل الحفظ
        "before_submit": "...",   # قبل الإرسال
        "on_submit": "...",       # عند الإرسال
        "before_save": "...",     # قبل الحفظ
        "after_save": "...",      # بعد الحفظ
    }
}

# 5. ما بعد التثبيت
after_install = "hr_erp.hrms_erp.install.after_install"

# 6. ما بعد كل migrate
after_migrate = ["hr_erp...custom_fields.create_custom_fields"]
```

---

## الفصل العاشر: قائمة مرجعية سريعة

### أنواع الحقول
Data, Text, Small Text, Long Text, Int, Float, Check, Date, Datetime, Time, Select, Link, Table, Section Break, Column Break, Code, HTML, Password, Currency, Duration, Geolocation, JSON, Read Only, Text Editor, Signature, Barcode, Attachment, Dynamic Link, Table MultiSelect

### أنواع الـ Report
1. **Report Builder** - واجهة سحب وإفلات
2. **Query Report** - SQL مباشر
3. **Script Report** - سكربت بايثون (الأكثر مرونة)

### أنواع الـ Workspace
- **Links** - روابط لـ DocTypes
- **Shortcuts** - اختصارات في الشريط الجانبي
- **Charts** - رسوم بيانية
- **Number Cards** - بطاقات أرقام

### أنواع أحداث المستندات
`before_insert`, `validate`, `before_save`, `after_insert`, `on_update`,
`on_submit`, `on_cancel`, `on_trash`, `after_delete`, `before_rename`, `after_rename`

### أنواع Override
```python
# 1. Override DocType Class (giới thiệu class mới)
override_doctype_class = {"My DocType": "app.module.MyClass"}

# 2. Override DocType JS (إضافة سكربت)
doctype_js = {"My DocType": ["public/js/my.js"]}

# 3. Override DocType Events (أحداث)
doc_events = {"My DocType": {"validate": "app.module.handler"}}
```

---

> **آخر تحديث:** 2026-08-20
> **المطور:** Shumul Team
