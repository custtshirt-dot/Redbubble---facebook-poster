"""
📋 Update Catalog — يحدث قائمة كل التصاميم الموجودة في الستور
يتشغل أوتوماتيك كل يوم الساعة 7 صباحاً (UTC) عبر GitHub Actions
الناتج: all_designs.json — بيتحفظ في الـ repo
"""
import os
import json
import sys
from datetime import datetime

# ── Import من نفس المشروع ────────────────────────────────────
from store_manager import scrape_store_designs, load_designs_history, url_key
from config import REDBUBBLE_STORE_URL

ALL_DESIGNS_FILE = 'all_designs.json'


def update_all_designs_catalog() -> bool:
    """
    سكان الستور الكامل وتحديث all_designs.json
    """
    store_url = (REDBUBBLE_STORE_URL or '').strip()

    if not store_url:
        print("❌ REDBUBBLE_STORE_URL not set — cannot update catalog")
        return False

    print("=" * 60)
    print("📋 DAILY CATALOG UPDATE")
    print(f"   🕐 Time : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   🏪 Store: {store_url[:65]}")
    print("=" * 60)

    # ── سكان كامل (حتى 10 صفحات) ────────────────────────────
    designs = scrape_store_designs(store_url, max_pages=10)

    if not designs:
        print("⚠️ No designs found during scan")
        # حفظ ملف فاضي مع timestamp بس
        catalog = {
            'last_updated': datetime.now().isoformat(),
            'store_url': store_url,
            'total': 0,
            'note': 'Store scan returned 0 results — might be a scraping issue',
            'designs': []
        }
        with open(ALL_DESIGNS_FILE, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, indent=2, ensure_ascii=False)
        return False

    # ── تحميل الهيستوري عشان نضيف بيانات النشر لكل تصميم ────
    history = load_designs_history()
    history_designs = history.get('designs', {})

    # ── بناء الكتالوج ────────────────────────────────────────
    catalog_designs = []
    posted_count = 0
    never_posted_count = 0

    for d in designs:
        key = url_key(d['url'])
        record = history_designs.get(key, {})

        post_count = record.get('post_count', 0)
        last_posted = record.get('last_posted')
        first_seen = record.get('first_seen')

        if post_count > 0:
            posted_count += 1
        else:
            never_posted_count += 1

        catalog_designs.append({
            'title'      : d.get('title', 'Unknown'),
            'url'        : d['url'],
            'work_id'    : d.get('work_id', ''),
            'post_count' : post_count,
            'last_posted': last_posted,
            'first_seen' : first_seen,
            'status'     : '✅ Posted' if post_count > 0 else '🆕 Never Posted',
        })

    # ترتيب: الأكتر نشراً في الأعلى
    catalog_designs.sort(key=lambda x: x['post_count'], reverse=True)

    catalog = {
        'last_updated'     : datetime.now().isoformat(),
        'store_url'        : store_url,
        'total'            : len(catalog_designs),
        'posted_count'     : posted_count,
        'never_posted_count': never_posted_count,
        'total_posts_made' : history.get('total_posts', 0),
        'designs'          : catalog_designs,
    }

    # ── حفظ الملف ────────────────────────────────────────────
    with open(ALL_DESIGNS_FILE, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Catalog saved to {ALL_DESIGNS_FILE}")
    print(f"   🎨 Total designs  : {len(catalog_designs)}")
    print(f"   ✅ Posted before  : {posted_count}")
    print(f"   🆕 Never posted   : {never_posted_count}")
    print(f"   📤 Total posts    : {history.get('total_posts', 0)}")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = update_all_designs_catalog()
    sys.exit(0 if success else 1)
