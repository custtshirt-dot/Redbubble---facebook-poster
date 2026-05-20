"""
🖼️ Image Extractor for Redbubble
- كل منتج صورة واحدة بس
- المنتجات السوداء أول
- أكبر عدد ممكن من الصور
"""
import re
import requests
from config import HEADERS, PRIORITY_PRODUCTS, PRODUCT_ORDER

# ── المنتجات المستبعدة نهائياً ──────────────────────────────
EXCLUDED_PRODUCTS = ['pin', 'kids', 'baby', 'mask', 'mat']

# ── كلمات تدل على اللون الأسود في URL الصورة ───────────────
BLACK_KEYWORDS = [
    'black', '000000', '1a1a1a', '212121', '2b2b2b',
    'dark', 'noir', 'nero', 'negro'
]

# ── كلمات تدل على اللون الفاتح ──────────────────────────────
LIGHT_KEYWORDS = [
    'white', 'ffffff', 'f8f8f8', 'light', 'cream',
    'heather', 'grey', 'gray', 'silver', 'natural'
]


def _convert_shop_ap_url(url: str) -> str:
    """
    ✅ يحول رابط /shop/ap/WORK_ID لرابط /i/t-shirt/ عشان يجيب كل الصور
    /shop/ap/ بيرجع صورة واحدة بس — نحتاج رابط المنتج الكامل
    """
    import re as _re
    if '/shop/ap/' not in url:
        return url
    work_id_m = _re.search(r'/shop/ap/(\d+)', url)
    if not work_id_m:
        return url
    work_id = work_id_m.group(1)
    print(f"   🔄 /shop/ap/ detected — fetching product slug for work_id {work_id}...")
    try:
        # اجيب الصفحة عشان نجيب الـ slug
        r = requests.get(url, headers=HEADERS, timeout=20)
        html = r.text
        # ابحث عن رابط /i/ في الصفحة
        m = _re.search(r'href=["\'](/i/[^"\'?#]+/' + work_id + r'[^"\'?#]*)["\']>', html)
        if m:
            full_url = 'https://www.redbubble.com' + m.group(1)
            print(f"   ✅ Found product URL: {full_url[:70]}")
            return full_url
        # fallback: ابحث عن canonical link
        m2 = _re.search(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\']([^"\']+)["\']>', html)
        if m2 and work_id in m2.group(1):
            print(f"   ✅ Canonical: {m2.group(1)[:70]}")
            return m2.group(1)
        # fallback 2: ابحث عن أي /i/ link في الصفحة
        import re as _re2
        m3 = _re2.search(r'["\']((https://www\.redbubble\.com)?/i/[^"\' ?#]+)["\']', html)
        if m3:
            found = m3.group(1)
            if not found.startswith('http'):
                found = 'https://www.redbubble.com' + found
            print(f"   ✅ Found /i/ URL from page: {found[:70]}")
            return found
        # fallback 3: رجّع الـ URL الأصلي عشان نستخرج الصور منه مباشرة
        print(f"   ⚠️ Could not find /i/ URL, extracting from original page")
        return url
    except Exception as e:
        print(f"   ⚠️ Conversion failed: {e}")
        return url


def extract_all_images(url):
    """استخراج كل صور المنتجات من Redbubble — يدعم /shop/ap/ و /i/
    بيرجع: list of image URLs (الـ converted URL محفوظ في extract_all_images.resolved_url)
    """
    # ✅ حوّل /shop/ap/ لرابط كامل عشان تجيب كل الصور
    extract_all_images.resolved_url = url  # default
    if '/shop/ap/' in url:
        url = _convert_shop_ap_url(url)
        extract_all_images.resolved_url = url  # الـ /i/ URL الحقيقي

    print(f"🔍 Fetching: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        html = r.text
        pattern = re.compile(
            r'https://ih\d\.redbubble\.net/image\.[^"\']+\.(?:jpg|png|webp)'
        )
        all_images = pattern.findall(html)
        unique = list(dict.fromkeys(all_images))

        # ✅ لو لسه قليل — جرب استخراج من __NEXT_DATA__
        if len(unique) < 5:
            import json as _json
            nd = re.search(
                r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>',
                html, re.DOTALL
            )
            if nd:
                try:
                    raw = nd.group(1)
                    for m in re.finditer(
                        r'(https://ih\d+\.redbubble\.net/image\.[^"\'\\s]+)', raw
                    ):
                        img = m.group(1).split('?')[0]
                        if img not in unique:
                            unique.append(img)
                except Exception:
                    pass

        print(f"✅ Found {len(unique)} unique product images")
        return unique
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def detect_product_type(image_url):
    """تحديد نوع المنتج من URL الصورة"""
    url_lower = image_url.lower()

    # تحقق من المستبعدات
    for excluded in EXCLUDED_PRODUCTS:
        if excluded in url_lower:
            return None

    # ابحث عن نوع المنتج
    for product in PRODUCT_ORDER:
        if product in url_lower:
            return product

    return 'other'


def is_black_product(image_url):
    """هل المنتج بلون أسود أو داكن؟"""
    url_lower = image_url.lower()
    for keyword in BLACK_KEYWORDS:
        if keyword in url_lower:
            return True
    return False


def is_light_product(image_url):
    """هل المنتج بلون فاتح؟"""
    url_lower = image_url.lower()
    for keyword in LIGHT_KEYWORDS:
        if keyword in url_lower:
            return True
    return False


def smart_sort_images(images, max_images=30):
    """
    ترتيب ذكي للصور:
    1. كل منتج صورة واحدة بس
    2. المنتجات السوداء أول
    3. أكبر عدد ممكن
    """
    if not images:
        return []

    # ── الخطوة 1: تجميع الصور حسب نوع المنتج ──────────────
    grouped = {}
    for img in images:
        ptype = detect_product_type(img)
        if ptype is None:  # مستبعد
            continue
        grouped.setdefault(ptype, {'black': [], 'light': [], 'other': []})

        if is_black_product(img):
            grouped[ptype]['black'].append(img)
        elif is_light_product(img):
            grouped[ptype]['light'].append(img)
        else:
            grouped[ptype]['other'].append(img)

    print(f"📦 Product types found: {list(grouped.keys())}")

    # ── الخطوة 2: اختار أفضل صورة لكل منتج ─────────────────
    # الأولوية: أسود ← تاني ← فاتح
    best_per_type = {}
    for ptype, colors in grouped.items():
        if colors['black']:
            best_per_type[ptype] = colors['black'][0]
        elif colors['other']:
            best_per_type[ptype] = colors['other'][0]
        elif colors['light']:
            best_per_type[ptype] = colors['light'][0]

    # ── الخطوة 3: ترتيب حسب PRIORITY_PRODUCTS ───────────────
    black_priority = []    # أسود + أولوية عالية
    black_others = []      # أسود + أولوية عادية
    light_priority = []    # فاتح + أولوية عالية
    light_others = []      # فاتح + أولوية عادية

    # Priority products أول
    for ptype in PRIORITY_PRODUCTS:
        if ptype in best_per_type:
            img = best_per_type[ptype]
            if is_black_product(img):
                black_priority.append(img)
            else:
                light_priority.append(img)
            del best_per_type[ptype]

    # باقي المنتجات حسب PRODUCT_ORDER
    for ptype in PRODUCT_ORDER:
        if ptype in best_per_type:
            img = best_per_type[ptype]
            if is_black_product(img):
                black_others.append(img)
            else:
                light_others.append(img)
            del best_per_type[ptype]

    # أي منتج متبقي
    for img in best_per_type.values():
        if is_black_product(img):
            black_others.append(img)
        else:
            light_others.append(img)

    # ── الخطوة 4: دمج بالترتيب الصح ─────────────────────────
    # الأسود أول دايماً
    final = (
        black_priority +
        black_others +
        light_priority +
        light_others
    )

    print(f"🎯 Total: {len(final)} images (one per product)")
    print(f"⬛ Black first: {len(black_priority + black_others)}")
    print(f"⬜ Light after: {len(light_priority + light_others)}")
    print(f"📋 Order: {[detect_product_type(img) for img in final[:10]]}")

    return final[:max_images]
