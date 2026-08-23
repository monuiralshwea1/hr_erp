"""Parse CSV with correct column mapping."""
import csv
import codecs
import io


def execute():
    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"

    with codecs.open(path, 'r', encoding='cp1256') as f:
        content = f.read()

    lines = content.split('\n')

    # Correct header mapping
    headers = [
        'ملاحظه', 'البريد الالكتروني', 'المدير المسؤول', 'رقم الجوال',
        'العنوان الاهلي', 'صله القربه', 'رقم الجوال الشخصي', 'تاريخ الميلاد',
        'العنوان الدائم', 'العنوان الحالي', 'تاريخ الانتهاء', 'تاريخ البدء',
        'الراتب الاجمالي', 'بدل مواصلات', 'بدل مخاطر', 'بدل طبيعه عمل',
        'الراتب الاساسي', 'الدرجه الوظيفيه', 'نوع الوظيفه', 'المسمي الوظيفي',
        'الاسم', 'الفرع', 'رقم الوظيفي', 'العدد'
    ]

    # Parse employees
    employees = []
    for line_num, line in enumerate(lines[2:], start=2):
        if not line.strip() or '#NAME' in line:
            continue
        
        reader = csv.reader(io.StringIO(line))
        try:
            row = next(reader)
        except Exception:
            continue
        
        if len(row) < 20:
            continue

        name = row[20].strip() if len(row) > 20 else ''
        mobile = row[3].strip() if len(row) > 3 else ''
        
        if not name or not mobile:
            continue

        emp = {
            'name': name,
            'email': row[1].strip() if len(row) > 1 else '',
            'manager_name': row[2].strip() if len(row) > 2 else '',
            'mobile': mobile,
            'family_address': row[4].strip() if len(row) > 4 else '',
            'relation': row[5].strip() if len(row) > 5 else '',
            'personal_mobile': row[6].strip() if len(row) > 6 else '',
            'dob': row[7].strip() if len(row) > 7 else '',
            'permanent_address': row[8].strip() if len(row) > 8 else '',
            'current_address': row[9].strip() if len(row) > 9 else '',
            'contract_end': row[10].strip() if len(row) > 10 else '',
            'contract_start': row[11].strip() if len(row) > 11 else '',
            'total_salary': row[12].strip() if len(row) > 12 else '',
            'transport_allowance': row[13].strip() if len(row) > 13 else '',
            'risk_allowance': row[14].strip() if len(row) > 14 else '',
            'nature_allowance': row[15].strip() if len(row) > 15 else '',
            'basic_salary': row[16].strip() if len(row) > 16 else '',
            'job_grade': row[17].strip() if len(row) > 17 else '',
            'job_type': row[18].strip() if len(row) > 18 else '',
            'job_title': row[19].strip() if len(row) > 19 else '',
            'branch': row[21].strip() if len(row) > 21 else '',
            'emp_num': row[22].strip() if len(row) > 22 else '',
            'notes': row[0].strip() if len(row) > 0 else '',
        }

        employees.append(emp)

    print(f"Total employees: {len(employees)}")

    # Show unique branches
    branches = set(e['branch'] for e in employees if e['branch'])
    print(f"\nBranches: {branches}")

    # Show unique job titles
    titles = set(e['job_title'] for e in employees if e['job_title'])
    print(f"\nJob titles: {titles}")

    # Show unique job grades
    grades = set(e['job_grade'] for e in employees if e['job_grade'])
    print(f"\nJob grades: {grades}")

    # Show unique job types
    types = set(e['job_type'] for e in employees if e['job_type'])
    print(f"\nJob types: {types}")

    # Show all employees with details
    print(f"\n{'='*80}")
    for i, e in enumerate(employees):
        print(f"\n  [{i+1}] {e['name']}")
        print(f"      Mobile: {e['mobile']}")
        print(f"      Job: {e['job_title']} ({e['job_type']})")
        print(f"      Branch: {e['branch']}")
        print(f"      Grade: {e['job_grade']}")
        print(f"      Basic: {e['basic_salary']}, Total: {e['total_salary']}")
        print(f"      Start: {e['contract_start']}, End: {e['contract_end']}")
        print(f"      DOB: {e['dob']}")
        print(f"      Notes: {e['notes'][:60]}")
