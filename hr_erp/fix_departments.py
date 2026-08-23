"""Fix department assignments for Shahadhi employees based on their designation."""
import frappe

COMPANY = "الشاحذي"

# Department mapping based on designation/role
DESIG_DEPT_MAP = {
    'مدير فرع': 'الاداره العامه',
    'مديره الموارد البشريه': 'الموارد البشريه',
    'خدمه عملاء وصندوق': 'المبيعات',
    'خدمه عملاء': 'المبيعات',
    'خدمه عملاء داخليه': 'المبيعات',
    'خدمه عملاء وشبكات': 'المبيعات',
    'عداد وخدمهعملاء': 'المبيعات',
    'عداد': 'المبيعات',
    'حارس': 'الحراسه',
    'رئيــس قســـم الحارسه': 'الحراسه',
    'رئيــس قســـم الحسابات': 'الماليه',
    'رئيــس قســـم الامتثال والعمليات': 'الاداره العامه',
    'حسابات': 'الماليه',
    'مورد بشريه': 'الموارد البشريه',
    'موظف اداري': 'الاداره العامه',
    'مندوب': 'المبيعات',
    'مدير اداره': 'الاداره العامه',
    'خدمه عملاء،': 'المبيعات',
    'خدمه عملاء،وصندوق': 'المبيعات',
    'خدمه عملاء،وصندوق +عداد': 'المبيعات',
    'خدمه عملاء،وعداد': 'المبيعات',
    'خدمه عملاءوشبكات': 'المبيعات',
    'خدمه عملاءو شبكات': 'المبيعات',
    'عداد+ خدمه عملاء وصنوق مؤقت': 'المبيعات',
    'صندوق وخدمه عملاء': 'المبيعات',
}

def execute():
    emps = frappe.get_all("Employee",
        filters={"company": COMPANY},
        fields=["name", "employee_name", "designation", "department"],
    )

    fixed = 0
    for emp in emps:
        desig = emp.designation or ''
        new_dept = DESIG_DEPT_MAP.get(desig)

        if not new_dept:
            if 'حارس' in desig:
                new_dept = 'الحراسه'
            elif 'خدم' in desig or 'عداد' in desig or 'مندوب' in desig or 'صندوق' in desig:
                new_dept = 'المبيعات'
            elif 'حساب' in desig or 'مالي' in desig:
                new_dept = 'الماليه'
            elif 'موارد' in desig or 'بشري' in desig:
                new_dept = 'الموارد البشريه'
            else:
                new_dept = 'الاداره العامه'

        # Get full department name with company suffix
        dept_doc = frappe.db.get_value("Department",
            {"department_name": new_dept, "company": COMPANY}, "name")

        if dept_doc and dept_doc != emp.department:
            frappe.db.set_value("Employee", emp.name, "department", dept_doc)
            fixed += 1
            print(f"  FIXED: {emp.name} | {emp.employee_name} -> {new_dept}")
        elif not dept_doc:
            print(f"  MISSING DEPT: {new_dept} for {emp.name}")

    frappe.db.commit()
    print(f"\nFixed {fixed} employees")

    # Show final stats
    depts = frappe.db.sql("""
        SELECT department, COUNT(*) as cnt
        FROM tabEmployee WHERE company='الشاحذي'
        GROUP BY department
    """, as_dict=True)
    print("\n--- Department Distribution ---")
    for d in depts:
        print(f"  {d.department}: {d.cnt}")
