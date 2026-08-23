"""Read CSV with proper Arabic encoding and parse employees."""
import csv
import codecs


def execute():
    path = "/home/newsmart/frappe-bench2/apps/hr_erp/hr_erp/shahadhi_employees.csv"

    # Try different encodings
    for enc in ['cp1256', 'utf-8-sig', 'utf-8', 'iso-8859-6', 'windows-1256']:
        try:
            with codecs.open(path, 'r', encoding=enc) as f:
                content = f.read()
            # Check if Arabic text decoded properly
            if 'الاسم' in content or 'الوظيفة' in content or 'راتب' in content or 'رقم' in content:
                print(f"Encoding: {enc} - SUCCESS")
                lines = content.split('\n')
                for i, line in enumerate(lines[:5]):
                    print(f"  Line {i}: {line.strip()[:200]}")
                print(f"  Total lines: {len(lines)}")
                return enc
        except Exception as e:
            print(f"Encoding {enc}: FAILED - {e}")

    # If none worked, try raw binary
    print("\nTrying raw read...")
    with open(path, 'rb') as f:
        raw = f.read()
    print(f"  File size: {len(raw)} bytes")
    print(f"  First 100 bytes hex: {raw[:100].hex()}")
    return None
