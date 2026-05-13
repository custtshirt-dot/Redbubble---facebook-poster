"""
🏪 Store Manager - اختيار ذكي للمنتجات
- يسكان الستور تلقائي ويجيب كل التصاميم
- يعرف التصاميم الجديدة ويبدأ بيها
- مش هيكرر تصميم ورا بعضه
- يدعم الإضافة اليدوية من manual_products.json
"""
import os
import re
import json
import hashlib
import requests
from datetime import datetime

DESIGNS_HISTORY_FILE = 'designs_history.json'
MANUAL_PRODUCTS_FILE = 'manual_products.json'

# ✅ كول داون لكل تصميم — مش هيتنشر نفس التصميم قبل 24 ساعة
DESIGN_COOLDOWN_HOURS = 24

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.redbubble.com/',
}


# ══════════════════════════════════════════════════════════════
# 🔑 KEY HELPERS
# ══════════════════════════════════════════════════════════════

def url_key(url: str) -> str:
    """Hash قصير للـ URL بيستخدم كـ key في الهيستوري"""
    return hashlib.md5(url.strip().lower().encode()).hexdigest()[:14]


def clean_work_url(url: str) -> str:
    """إزالة parameters من URL وترجيع الـ base URL بس"""
    url = url.split('?')[0].split('#')[0].strip()
    if not url.startswith('http'):
        url = 'https://www.redbubble.com' + url
    return url


# ══════════════════════════════════════════════════════════════
# 📚 DESIGNS HISTORY (منفصل عن post_history)
# ══════════════════════════════════════════════════════════════

def load_designs_history() -> dict:
    """تحميل هيستوري التصاميم"""
    if os.path.exists(DESIGNS_HISTORY_FILE):
        try:
            with open(DESIGNS_HISTORY_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Ensure all required keys exist
                data.setdefault('last_posted_url', None)
                data.setdefault('last_check', None)
                data.setdefault('total_posts', 0)
                data.setdefault('designs', {})
                return data
        except Exception as e:
            print(f"⚠️ History load error: {e} — starting fresh")

    return {
        'last_posted_url': None,
        'last_check': None,
        'total_posts': 0,
        'designs': {}
    }


def save_designs_history(history: dict) -> bool:
    """حفظ هيستوري التصاميم"""
    try:
        with open(DESIGNS_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Failed to save designs history: {e}")
        return False


def record_design_posted(url: str, title: str = '') -> None:
    """تسجيل إن التصميم ده اتنشر بنجاح"""
    history = load_designs_history()
    key = url_key(url)

    if key not in history['designs']:
        history['designs'][key] = {
            'url': url,
            'title': title,
            'first_seen': datetime.now().isoformat(),
            'post_count': 0,
            'last_posted': None,
            'is_manual': False,
        }

    entry = history['designs'][key]
    entry['post_count'] = entry.get('post_count', 0) + 1
    entry['last_posted'] = datetime.now().isoformat()
    if title:
        entry['title'] = title

    history['last_posted_url'] = url
    history['total_posts'] = history.get('total_posts', 0) + 1

    save_designs_history(history)
    print(f"📝 Recorded post: {title or url[:60]}")


# ══════════════════════════════════════════════════════════════
# 📋 MANUAL PRODUCTS (إضافة يدوية)
# ══════════════════════════════════════════════════════════════

def load_manual_products() -> list:
    """
    تحميل المنتجات اللي أضافها المستخدم يدوياً من manual_products.json
    الـ format:
    {
      "products": [
        {"url": "https://...", "title": "اسم التصميم", "enabled": true}
      ]
    }
    """
    if not os.path.exists(MANUAL_PRODUCTS_FILE):
        return []

    try:
        with open(MANUAL_PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)

        products = data.get('products', [])
        enabled = [
            {
                'url': clean_work_url(p['url']),
                'title': p.get('title', ''),
                'is_manual': True,
            }
            for p in products
            if p.get('enabled', True) and p.get('url', '').strip()
        ]

        if enabled:
            print(f"📋 Manual products loaded: {len(enabled)}")
        return enabled

    except Exception as e:
        print(f"⚠️ Failed to load manual_products.json: {e}")
        return []


# ══════════════════════════════════════════════════════════════
# 🔍 STORE SCRAPING
# ══════════════════════════════════════════════════════════════

def _extract_username(store_url: str) -> str | None:
    """استخراج اليوزرنيم من رابط الستور"""
    m = re.search(r'redbubble\.com/people/([^/?#]+)', store_url)
    return m.group(1) if m else None


def scrape_store_designs(store_url: str, max_pages: int = 5) -> list:
    """
    سكان الستور واستخراج كل روابط التصاميم (works)
    بيرجع list of {'url': ..., 'title': ..., 'work_id': ...}
    """
    username = _extract_username(store_url)
    if not username:
        print(f"⚠️ Cannot parse username from store URL: {store_url}")
        return []

    print(f"\n🏪 Scanning Redbubble store: @{username}")
    designs = []
    seen_ids = set()

    for page in range(1, max_pages + 1):
        page_url = (
            f"https://www.redbubble.com/people/{username}/shop"
            f"?page={page}&sortOrder=recent"
        )
        print(f"   📄 Page {page}/{max_pages} ...", end=' ', flush=True)

        try:
            resp = requests.get(page_url, headers=HEADERS, timeout=20)

            if resp.status_code == 429:
                print(f"⚠️ Rate limited — stopping")
                break
            if resp.status_code == 404:
                print(f"❌ Store not found")
                break
            if resp.status_code != 200:
                print(f"⚠️ HTTP {resp.status_code}")
                break

            html = resp.text

            # استخراج روابط الـ works من الـ HTML
            found_on_page = 0
            # Pattern 1: /works/ID-slug
            pattern = re.compile(
                r'href=["\'](/people/' + re.escape(username) +
                r'/works/(\d+)-([^"\'?#\s]+))["\']',
                re.IGNORECASE
            )
            for m in pattern.finditer(html):
                work_path, work_id, slug = m.group(1), m.group(2), m.group(3)
                if work_id not in seen_ids:
                    seen_ids.add(work_id)
                    full_url = f"https://www.redbubble.com{work_path}"
                    title = slug.replace('-', ' ').title()
                    designs.append({
                        'url': full_url,
                        'title': title,
                        'work_id': work_id,
                        'is_manual': False,
                    })
                    found_on_page += 1

            print(f"✅ {found_on_page} designs found")

            # لو الصفحة فارغة معناها وصلنا للآخر
            if found_on_page == 0:
                print(f"   ℹ️ No more designs — stopping at page {page}")
                break

        except requests.exceptions.Timeout:
            print(f"⏱️ Timeout on page {page}")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            break

    print(f"🎨 Store scan complete: {len(designs)} total designs found\n")
    return designs


# ══════════════════════════════════════════════════════════════
# 🧠 SMART SELECTION
# ══════════════════════════════════════════════════════════════

def _register_designs(all_designs: list) -> int:
    """
    تسجيل التصاميم الجديدة في الهيستوري بدون علامة 'posted'
    بيرجع عدد التصاميم الجديدة
    """
    history = load_designs_history()
    new_count = 0

    for d in all_designs:
        key = url_key(d['url'])
        if key not in history['designs']:
            history['designs'][key] = {
                'url': d['url'],
                'title': d.get('title', ''),
                'first_seen': datetime.now().isoformat(),
                'post_count': 0,
                'last_posted': None,
                'is_manual': d.get('is_manual', False),
            }
            new_count += 1

    if new_count > 0:
        history['last_check'] = datetime.now().isoformat()
        save_designs_history(history)

    return new_count


def get_next_product_to_post(store_url: str = None) -> dict | None:
    """
    🧠 الدالة الرئيسية - بتختار التصميم الجاي بذكاء

    الأولوية:
    1. المنتجات اليدوية (manual) اللي ما اتنشرتش لسه
    2. التصاميم الجديدة من الستور (اكتُشفت بعد آخر فحص)
    3. أقدم تصميم اتنشر (بدون تكرار اللي اتنشر قبله مباشرة)

    بيرجع: {'url': str, 'title': str, 'is_new': bool} أو None
    """
    history = load_designs_history()
    last_posted_url = history.get('last_posted_url')

    all_designs = []

    # ── 1. المنتجات اليدوية أول ──────────────────────────────
    manual = load_manual_products()
    manual_urls = {url_key(m['url']) for m in manual}
    all_designs.extend(manual)

    # ── 2. سكان الستور ──────────────────────────────────────
    if store_url and store_url.strip():
        store_designs = scrape_store_designs(store_url.strip())
        for d in store_designs:
            if url_key(d['url']) not in manual_urls:
                all_designs.append(d)

    # ── 3. لو السكان فاشل → ارجع للهيستوري المحفوظ ────────────
    store_scan_failed = not all_designs
    if store_scan_failed:
        history = load_designs_history()
        cached = list(history.get('designs', {}).values())

        if cached:
            print(f"⚠️ Store scan returned 0 results — using {len(cached)} cached designs from history")
            all_designs = [
                {
                    'url': d['url'],
                    'title': d.get('title', ''),
                    'is_manual': d.get('is_manual', False),
                    'post_count': d.get('post_count', 0),
                    'last_posted': d.get('last_posted'),
                }
                for d in cached
                if d.get('url', '').strip()
            ]
        else:
            print("❌ No designs found and history is empty.")
            print("   → Add REDBUBBLE_STORE_URL to Secrets, or add URLs in manual_products.json")
            return None

    # ── 4. تسجيل التصاميم الجديدة (لو السكان نجح) ────────────
    if not store_scan_failed:
        new_count = _register_designs(all_designs)
        if new_count:
            print(f"✨ {new_count} new designs discovered!")

    # إعادة تحميل الهيستوري
    history = load_designs_history()

    # ── 5. تصنيف التصاميم ────────────────────────────────────
    never_posted = []
    posted_before = []

    for d in all_designs:
        key = url_key(d['url'])
        record = history['designs'].get(key, {})
        # لو الـ record موجود في الهيستوري → استخدم بياناته
        post_count  = record.get('post_count',  d.get('post_count', 0))
        last_posted = record.get('last_posted', d.get('last_posted'))
        enriched = {
            **d,
            'url':         record.get('url',   d['url']),
            'title':       record.get('title', d.get('title', '')),
            'post_count':  post_count,
            'last_posted': last_posted,
        }
        if post_count == 0:
            never_posted.append(enriched)
        else:
            posted_before.append(enriched)

    print(f"\n📊 Design Pool:")
    print(f"   🆕 Never posted : {len(never_posted)}")
    print(f"   🔄 Posted before: {len(posted_before)}")
    if last_posted_url:
        print(f"   ⏮️  Last posted  : {last_posted_url[:70]}...")

    # ── 5. اختيار التصميم ────────────────────────────────────

    # أولوية 1: التصاميم الجديدة (اليدوية أول ثم الستور)
    if never_posted:
        # اليدوية أول
        manual_new = [d for d in never_posted if d.get('is_manual')]
        store_new = [d for d in never_posted if not d.get('is_manual')]
        chosen = (manual_new + store_new)[0]
        chosen['is_new'] = True
        print(f"\n✨ Chose NEW: {chosen['title'] or chosen['url'][:70]}")
        return chosen

    # أولوية 2: أقدم تصميم اتنشر مع تجنب التكرار والكول داون
    if posted_before:
        posted_before.sort(key=lambda d: d.get('last_posted') or '0000')
        now = datetime.now()
        from datetime import timedelta

        skipped_cooldown = []

        for candidate in posted_before:
            # تجنب التصميم اللي اتنشر قبله مباشرة
            if candidate['url'] == last_posted_url:
                continue

            # ✅ تحقق من كول داون 24 ساعة
            last_p = candidate.get('last_posted')
            if last_p:
                try:
                    last_dt = datetime.fromisoformat(last_p)
                    hours_since = (now - last_dt).total_seconds() / 3600
                    if hours_since < DESIGN_COOLDOWN_HOURS:
                        hrs_left = DESIGN_COOLDOWN_HOURS - hours_since
                        print(f"   ⏭️ Cooldown ({hrs_left:.1f}h left): {candidate.get('title','')[:40]}")
                        skipped_cooldown.append(candidate)
                        continue
                except Exception:
                    pass

            candidate['is_new'] = False
            print(f"\n🔄 Chose OLD: {candidate['title'] or candidate['url'][:70]}")
            print(f"   ⏳ Last posted: {candidate['last_posted'][:10] if candidate['last_posted'] else 'never'}")
            return candidate

        # ✅ لو كل التصاميم في كول داون — لا تنشر
        if skipped_cooldown:
            print(f"\n⏸️  All {len(skipped_cooldown)} design(s) are in cooldown — skipping this run")
            print(f"   ⏰ Next available in: check designs_history.json")
            return None

        # آخر حل: لو مفيش غير التصميم اللي اتنشر قبله (تصميم واحد بس في الستور)
        chosen = posted_before[0]
        last_p = chosen.get('last_posted')
        if last_p:
            try:
                last_dt = datetime.fromisoformat(last_p)
                hours_since = (now - last_dt).total_seconds() / 3600
                if hours_since < DESIGN_COOLDOWN_HOURS:
                    hrs_left = DESIGN_COOLDOWN_HOURS - hours_since
                    print(f"\n⏸️  Only 1 design and it's in cooldown ({hrs_left:.1f}h left) — skipping")
                    return None
            except Exception:
                pass
        chosen['is_new'] = False
        print(f"\n🔄 Only one design available: {chosen['title']}")
        return chosen

    return None


# ══════════════════════════════════════════════════════════════
# 📊 STATISTICS
# ══════════════════════════════════════════════════════════════

def get_store_stats() -> str:
    """إحصائيات الستور والنشر"""
    history = load_designs_history()
    designs = history.get('designs', {})

    if not designs:
        return "\n📊 No designs tracked yet — run once to start!\n"

    total = len(designs)
    posted = sum(1 for d in designs.values() if d.get('post_count', 0) > 0)
    never = total - posted
    total_posts = history.get('total_posts', 0)
    last_check = (history.get('last_check') or 'Never')[:19]
    last_url = (history.get('last_posted_url') or 'None')[:55]

    # Top 3 أكتر تصاميم اتنشرت
    top = sorted(
        designs.values(),
        key=lambda d: d.get('post_count', 0),
        reverse=True
    )[:3]

    lines = [
        "",
        "╔══════════════════════════════════════════════════╗",
        "║  🏪 STORE MANAGER STATS                         ║",
        "╠══════════════════════════════════════════════════╣",
        f"║  🎨 Total Designs    : {total:<25}║",
        f"║  ✅ Posted           : {posted:<25}║",
        f"║  🆕 Never Posted     : {never:<25}║",
        f"║  📤 Total Posts Made : {total_posts:<25}║",
        f"║  🕐 Last Check       : {last_check:<25}║",
        f"║  📌 Last Posted      : {last_url:<25}║",
        "╠══════════════════════════════════════════════════╣",
        "║  🏆 Top Posted Designs:                         ║",
    ]
    for d in top:
        title = (d.get('title') or 'Unknown')[:30]
        count = d.get('post_count', 0)
        lines.append(f"║    • {title:<30} x{count:<5}     ║")
    lines.append("╚══════════════════════════════════════════════════╝")

    return '\n'.join(lines) + '\n'


def list_upcoming_designs(count: int = 5) -> list:
    """
    عرض التصاميم اللي هتتنشر الجاية
    مفيد للمراجعة اليدوية
    """
    history = load_designs_history()
    designs = list(history.get('designs', {}).values())

    never = [d for d in designs if d.get('post_count', 0) == 0]
    old = sorted(
        [d for d in designs if d.get('post_count', 0) > 0],
        key=lambda d: d.get('last_posted') or '0000'
    )

    upcoming = never[:count] + old[:max(0, count - len(never))]
    return upcoming[:count]
