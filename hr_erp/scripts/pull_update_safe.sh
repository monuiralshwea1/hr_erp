#!/bin/bash
# =============================================================================
#  سحب تحديثات hr_erp على السيرفر الثاني بشكل آمن
#  يمنع تشوّه الأسماء العربية (Mojibake) ويصلح أي تلف سابق
#
#  الاستخدام:
#      cd ~/frappe2
#      ./apps/hr_erp/hr_erp/scripts/pull_update_safe.sh <اسم_الموقع>
#
#  مثال:
#      ./apps/hr_erp/hr_erp/scripts/pull_update_safe.sh albashaer.newsmart.local
#
#  ما يفعله هذا السكربت بالترتيب:
#      1) ضبط اللغة على UTF-8 (السبب الجذري لتشوّه الأسماء)
#      2) سحب التحديثات من git
#      3) إصلاح أي أسماء ملفات تالفة (مقارنةً بأسماء git)
#      4) تحديث قاعدة البيانات (bench migrate)  ← ضروري لظهور الحقول والتقارير
#      5) مسح الذاكرة المؤقتة وإعادة تشغيل الخدمة
# =============================================================================
set -u

APP_DIR="$(cd "$(dirname "$0")/../.." && pwd)"     # apps/hr_erp
BENCH_DIR="$(cd "$APP_DIR/../.." && pwd)"          # جذر البنش (apps/..)
SITE="${1:-site1.local}"
RUN_MIGRATE=1

for arg in "$@"; do
    if [ "$arg" = "--no-migrate" ]; then
        RUN_MIGRATE=0
    fi
done

echo "=============================================================="
echo "  hr_erp — سحب آمن للتحديثات"
echo "=============================================================="
echo "  التطبيق : $APP_DIR"
echo "  البنش   : $BENCH_DIR"
echo "  الموقع  : $SITE"
echo

# ---------------------------------------------------------------- 1) اللغة
echo "==> [1/5] ضبط اللغة على UTF-8 ..."
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONIOENCODING=utf-8
echo "    LANG=$LANG  LC_ALL=$LC_ALL"
git -C "$APP_DIR" config core.quotepath false 2>/dev/null || true
echo

# ------------------------------------------------------------ 2) فحص قبل
echo "==> [2/5] فحص الأسماء قبل السحب ..."
if [ -f "$APP_DIR/hr_erp/scripts/fix_mojibake_filenames.py" ]; then
    "$BENCH_DIR/env/bin/python" "$APP_DIR/hr_erp/scripts/fix_mojibake_filenames.py" --check || true
else
    echo "    (أداة الإصلاح غير موجودة بعد — سيصل مع التحديث)"
fi
echo

# --------------------------------------------------------------- 3) السحب
echo "==> [3/5] سحب التحديثات من git ..."
( cd "$APP_DIR" && git pull --ff-only )
echo

# ------------------------------------------------------------ 4) الإصلاح
echo "==> [4/5] إصلاح أي أسماء عربية متشوّهة ..."
if [ -f "$APP_DIR/hr_erp/scripts/fix_mojibake_filenames.py" ]; then
    "$BENCH_DIR/env/bin/python" "$APP_DIR/hr_erp/scripts/fix_mojibake_filenames.py"
else
    echo "    تخطّي (الأداة غير موجودة)"
fi
echo

# ------------------------------------------------------------ 5) التفعيل
echo "==> [5/5] تحديث قاعدة البيانات وتشغيل الخدمة ..."
cd "$BENCH_DIR"
if [ "$RUN_MIGRATE" = "1" ]; then
    echo "    -- bench --site $SITE migrate"
    bench --site "$SITE" migrate
    echo "    -- bench --site $SITE clear-cache"
    bench --site "$SITE" clear-cache
else
    echo "    تخطّي migrate (خيار --no-migrate)"
fi
bench restart

echo
echo "=============================================================="
echo "  تمّ. تحقّق من الأسماء:"
echo "    ls $APP_DIR/hr_erp | head -20"
echo "    ls $APP_DIR/hr_erp/hrms_erp/workspace/"
echo "=============================================================="
