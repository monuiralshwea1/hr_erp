# -*- coding: utf-8 -*-
# Copyright (c) 2026, Shumul. All rights reserved.
"""
تحويل المبالغ إلى كلمات عربية — Arabic amount in words
=====================================================

السبب: Frappe تستخدم money_in_words() التي تُنتج النص بالإنجليزية دائماً
(English) لأنها لا تدعم العربية. لذلك نضيف هذه الوحدة لتوليد النص العربي
لصافي الراتب (net_pay) وحقوله الأساسية، وتُستدعى بعد set_net_pay().

الاستخدام:
    from hr_erp.hrms_erp.payroll_integration.arabic_amount_words import (
        number_to_arabic_words,
    )
    number_to_arabic_words(138333.33, currency="ريال يمني", subunit="فلس")
"""

import frappe
from frappe.utils import flt


# ----------------------------------------------------------------------
# المفردات الأساسية
# ----------------------------------------------------------------------
_ONES = [
    "", "واحد", "اثنان", "ثلاثة", "أربعة", "خمسة",
    "ستة", "سبعة", "ثمانية", "تسعة",
]

_TEENS = {
    10: "عشرة",
    11: "أحد عشر",
    12: "اثنا عشر",
    13: "ثلاثة عشر",
    14: "أربعة عشر",
    15: "خمسة عشر",
    16: "ستة عشر",
    17: "سبعة عشر",
    18: "ثمانية عشر",
    19: "تسعة عشر",
}

_TENS = {
    20: "عشرون", 30: "ثلاثون", 40: "أربعون", 50: "خمسون",
    60: "ستون", 70: "سبعون", 80: "ثمانون", 90: "تسعون",
}

_HUNDREDS = {
    100: "مئة", 200: "مئتان", 300: "ثلاثمئة", 400: "أربعمئة",
    500: "خمسمئة", 600: "ستمئة", 700: "سبعمئة", 800: "ثمانمئة", 900: "تسعمئة",
}

# (القيمة, المفرد, المثنى, الجمع)
_SCALES = [
    (1_000_000_000, "مليار", "ملياران", "مليارات"),
    (1_000_000, "مليون", "مليونان", "ملايين"),
    (1_000, "ألف", "ألفان", "آلاف"),
]


def _join(parts):
    """ربط الأجزاء بحرف الواو العربي."""
    parts = [p for p in parts if p]
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return " و".join(parts)


def _three_digits(number):
    """تحويل عدد من 0 إلى 999 إلى كلمات عربية."""
    words = []
    hundreds = number // 100
    remainder = number % 100

    if hundreds:
        words.append(_HUNDREDS[hundreds * 100])

    if remainder:
        if remainder < 10:
            words.append(_ONES[remainder])
        elif remainder < 20:
            words.append(_TEENS[remainder])
        else:
            tens = remainder // 10 * 10
            ones = remainder % 10
            if ones:
                words.append("%s و%s" % (_ONES[ones], _TENS[tens]))
            else:
                words.append(_TENS[tens])

    return _join(words)


def _scaled_group(count, singular, dual, plural):
    """صياغة مجموعة مع مقياسها (ألف/مليون/مليار)."""
    if count == 1:
        return singular
    if count == 2:
        return dual
    if 3 <= count <= 10:
        return "%s %s" % (_three_digits(count), plural)
    return "%s %s" % (_three_digits(count), singular)


def _integer_to_words(number):
    """تحويل عدد صحيح (بلا كسور) إلى كلمات عربية."""
    if number == 0:
        return "صفر"

    parts = []
    remaining = number

    for value, singular, dual, plural in _SCALES:
        if remaining >= value:
            group = remaining // value
            remaining = remaining % value
            parts.append(_scaled_group(group, singular, dual, plural))

    if remaining:
        parts.append(_three_digits(remaining))

    return _join(parts)


def number_to_arabic_words(number, currency=None, subunit=None, with_only=True):
    """تحويل مبلغ إلى نص عربي.

    number   : المبلغ (قد يحتوي كسور عشرية).
    currency : اسم العملة (مثال: "ريال يمني"). إن كان None تُترك بلا لاحقة.
    subunit  : اسم جزء العملة (مثال: "فلس") لعرض الكسور.
    with_only: إضافة كلمة "فقط" في نهاية النص.
    """
    number = flt(number or 0)

    negative = number < 0
    number = abs(number)

    integer_part = int(number)
    # جزءان عشريان (الفلس/الهللة عادةً كسر من 100)
    fraction = int(round((number - integer_part) * 100))
    if fraction == 100:
        integer_part += 1
        fraction = 0

    segments = [_integer_to_words(integer_part)]
    if currency:
        segments[-1] = "%s %s" % (segments[-1], currency)

    if fraction:
        frac_words = " ".join(filter(None, [_integer_to_words(fraction), subunit]))
        segments.append(frac_words)

    text = _join(segments)

    if negative:
        text = "سالب " + text

    if with_only:
        text = text + " فقط"

    return text


# ----------------------------------------------------------------------
# تكامل مع Salary Slip
# ----------------------------------------------------------------------
def get_currency_labels(company=None):
    """إرجاع (اسم العملة, اسم جزء العملة) حسب عملة الشركة."""
    currency = None
    if company:
        currency = frappe.db.get_value("Company", company, "default_currency")

    labels = {
        "YER": ("ريال يمني", "فلس"),
        "SAR": ("ريال سعودي", "هللة"),
        "AED": ("درهم إماراتي", "فلس"),
        "USD": ("دولار أمريكي", "سنت"),
        "EUR": ("يورو", "سنت"),
    }
    return labels.get(currency, (currency or "", ""))


def set_salary_slip_total_in_words_ar(doc):
    """كتابة صافي الراتب بالكلمات العربية على القسيمة.

    تُستدعى بعد set_net_pay() لتستبدل النص الإنجليزي بالعربي.
    تُعيد نصّين: (total_in_words, base_total_in_words) كـ (bool) نجاح.
    """
    currency, subunit = get_currency_labels(doc.get("company"))

    try:
        if doc.meta.has_field("total_in_words"):
            doc.total_in_words = number_to_arabic_words(
                doc.get("net_pay"), currency=currency, subunit=subunit
            )
        if doc.meta.has_field("base_total_in_words"):
            doc.base_total_in_words = number_to_arabic_words(
                doc.get("base_net_pay"), currency=currency, subunit=subunit
            )
        return True
    except Exception:
        frappe.log_error(frappe.get_traceback(), "hr_erp: arabic amount in words")
        return False
