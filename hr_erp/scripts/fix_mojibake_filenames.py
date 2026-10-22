#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
إصلاح أسماء الملفات والمجلدات العربية التالفة (Mojibake) داخل التطبيق
====================================================================
المشكلة
-------
مستودع git يخزّن أسماء الملفات كبايتات خام. عند نقل/سحب المستودع إلى نظام
لغته ليست UTF-8 (أو عبر أداة تقرأ UTF-8 على أنها CP1256) تتحوّل الأسماء العربية
إلى نص مشوّه مثل:

    بوابة_الموارد_البشرية                  ←  (الصحيح)
    ط¨ظˆط§ط¨ط©_ط§ظ„ظ…طˆط§ط±ط¯_ط§ظ„ط¨ط´ط±طٹط©   ←  (تالف)

كما قد توجد في المستودع أسماء قديمة مخزَّنة بترميز CP1256 القديم (ليست UTF-8 أصلاً).

كيف يعمل هذا السكربت
---------------------
* يقرأ الأسماء المتوقعة من git:  git ls-files -z
* لكل مسار متوقع، يبحث على القرص عن المدخل المقابل بثلاث صيغ:
    1) نفس البايتات كما هي
    2) CP1256 قديم  → يُصلَح إلى UTF-8
    3) ترميز مزدوج  (UTF-8 مقروء كـ CP1256)  → يُعاد إلى الأصل
* يعيد التسمية داخل git عبر git mv ليبقى الفهرس متسقاً.

الاستخدام
---------
    cd /path/to/frappe-bench
    ./env/bin/python apps/hr_erp/scripts/fix_mojibake_filenames.py --check   # فحص فقط
    ./env/bin/python apps/hr_erp/scripts/fix_mojibake_filenames.py           # إصلاح

ملاحظة مهمة
-----------
الأفضل منع تلف الأسماء من الأساس بضبط اللغة قبل عمليات git:
    export LANG=C.UTF-8
    export LC_ALL=C.UTF-8
    git config --global core.quotepath false
"""

import argparse
import os
import subprocess
import sys


def git_output(repo, args):
    try:
        proc = subprocess.run(
            ["git", "-C", repo] + args, capture_output=True, check=False
        )
        return proc.stdout
    except FileNotFoundError:
        return b""


def candidate_forms(raw):
    """كل الصيغ المحتملة التي قد يمثّل بها مدخلٌ على القرص بايتَه المتوقعة."""
    forms = {raw}
    # CP1256 قديم -> UTF-8
    try:
        forms.add(raw.decode("cp1256").encode("utf-8"))
    except (UnicodeDecodeError, UnicodeEncodeError, LookupError):
        pass
    # ترميز مزدوج -> الأصل
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = None
    if text is not None:
        for cp in ("cp1256", "cp1252", "latin-1"):
            try:
                forms.add(text.encode(cp))
            except (UnicodeEncodeError, LookupError):
                pass
    return forms


def read_dir_bytes(path):
    try:
        names = os.listdir(path)
    except OSError:
        return []
    out = []
    for name in names:
        try:
            raw = os.fsencode(name)
        except UnicodeEncodeError:
            raw = name.encode("utf-8", "surrogateescape")
        out.append((name, raw))
    return out


def find_match(dir_path, expected_raw):
    """يبحث عن مدخل في المجلد يمثّل expected_raw (بأي صيغة تالفة)."""
    for name, raw in read_dir_bytes(dir_path):
        if raw == expected_raw:
            return name, raw, False
        if expected_raw in candidate_forms(raw):
            return name, raw, True
    return None, None, False


def fix_repo(repo, check_only=False):
    tracked_raw = [p for p in git_output(repo, ["ls-files", "-z"]).split(b"\x00") if p]
    if not tracked_raw:
        print("تعذّر قراءة قائمة الملفات من git — تأكد أنك داخل مستودع git.")
        return 1

    targets = [p for p in tracked_raw if any(b > 127 for b in p)]
    if not targets:
        print("لا توجد أسماء غير ASCII في المستودع — لا حاجة لإصلاح.")
        return 0

    repaired = []
    unresolved = []
    skipped_legacy = 0

    for raw_path in targets:
        parts = raw_path.split(b"/")
        current = repo
        broken = False

        # أسماء قديمة مخزَّنة بترميز CP1256 (ليست UTF-8): لا يمكن تمثيلها كنص
        try:
            raw_path.decode("utf-8")
        except UnicodeDecodeError:
            skipped_legacy += 1
            continue

        for raw_part in parts[:-1]:
            found, raw_found, was_mangled = find_match(current, raw_part)
            if found is None:
                broken = True
                break
            if was_mangled:
                target = os.path.join(current, os.fsdecode(raw_part))
                repaired.append((os.path.join(current, found), target))
                if not check_only:
                    if not move(repo, os.path.join(current, found), target):
                        broken = True
                        break
                    # بعد النقل صار المسار الجديد هو الصحيح
                    current = target
                    continue
            # المتابعة داخل المجلد الموجود فعلياً على القرص
            current = os.path.join(current, found)

        if broken:
            unresolved.append(raw_path.decode("utf-8", "replace"))
            continue

        raw_last = parts[-1]
        found, raw_found, was_mangled = find_match(current, raw_last)
        if found is None:
            unresolved.append(raw_path.decode("utf-8", "replace"))
            continue
        if was_mangled:
            target = os.path.join(current, os.fsdecode(raw_last))
            repaired.append((os.path.join(current, found), target))
            if not check_only:
                move(repo, os.path.join(current, found), target)

    if check_only:
        print("\n=== نتيجة الفحص ===")
        if repaired:
            print("أسماء تالفة تحتاج إصلاحاً (%d):" % len(repaired))
            for src, dst in repaired:
                print("   ", os.path.basename(src), "->", os.path.basename(dst))
        else:
            print("لا توجد أسماء تالفة — كل الأسماء سليمة ✓")
        if skipped_legacy:
            print("مسارات بأسماء قديمة غير UTF-8 (تُتجاهل — أعد تسميتها يدوياً): %d" % skipped_legacy)
        if unresolved:
            print("\nمسارات متوقعة غير موجودة على القرص (%d):" % len(unresolved))
            for u in unresolved:
                print("   ", u)
        return 0

    if repaired:
        print("\n=== تم الإصلاح: %d اسم ===" % len(repaired))
        for src, dst in repaired:
            print("   ", os.path.basename(src), "->", os.path.basename(dst))
        git_output(repo, ["add", "-A"])
        print("تمت مزامنة فهرس git (git add -A).")
    else:
        print("لا توجد أسماء تالفة.")

    if skipped_legacy:
        print("\nمسارات بأسماء قديمة غير UTF-8 (تُتجاهل): %d" % skipped_legacy)

    if unresolved:
        print("\nمسارات متوقعة غير موجودة على القرص (%d):" % len(unresolved))
        for u in unresolved:
            print("   ", u)

    return 0


def move(repo, src, dst):
    """إعادة تسمية مع الحفاظ على فهرس git."""
    tracked = git_output(repo, ["ls-files", "-z", "--", os.path.relpath(src, repo)])
    if tracked:
        r = subprocess.run(
            ["git", "-C", repo, "mv", "--", os.path.relpath(src, repo), os.path.relpath(dst, repo)],
            capture_output=True,
        )
        if r.returncode == 0:
            return True
        print("   تعذّر git mv، جرّب إعادة تسمية مباشرة:", r.stderr.decode(errors="replace")[:120])
    try:
        os.rename(src, dst)
        return True
    except OSError as e:
        print("   تعذّرت إعادة التسمية:", e)
        return False


def main():
    parser = argparse.ArgumentParser(
        description="إصلاح أسماء الملفات العربية التالفة (Mojibake)"
    )
    parser.add_argument("--repo", help="مسار جذر المستودع (افتراضي: يُبحث عنه تلقائياً)")
    parser.add_argument("--check", action="store_true", help="فحص فقط دون تعديل")
    args = parser.parse_args()

    here = os.path.dirname(os.path.abspath(__file__))
    repo = args.repo or os.path.abspath(os.path.join(here, "..", ".."))

    probe = repo
    while probe and not os.path.isdir(os.path.join(probe, ".git")):
        parent = os.path.dirname(probe)
        if parent == probe:
            break
        probe = parent
    if os.path.isdir(os.path.join(probe, ".git")):
        repo = probe

    print("مستودع git:", repo)
    print("الوضع:", "فحص فقط" if args.check else "إصلاح فعلي")
    return fix_repo(repo, check_only=args.check)


if __name__ == "__main__":
    sys.exit(main())
