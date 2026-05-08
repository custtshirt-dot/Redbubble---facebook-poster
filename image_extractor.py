"""
🖼️ Image Extractor for Redbubble
"""
import re
import requests
from config import HEADERS, PRIORITY_PRODUCTS, PRODUCT_ORDER


def extract_all_images(url):
    """Extract all real product images from Redbubble"""
    print(f"🔍 Fetching: {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        html = r.text
        pattern = re.compile(r'https://ih1\.redbubble\.net/image\.[^"\']+\.jpg')
        all_images = pattern.findall(html)
        unique = list(dict.fromkeys(all_images))
        print(f"✅ Found {len(unique)} unique product images")
        return unique
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def detect_product_type(image_url):
    """Detect product type from image URL"""
    url_lower = image_url.lower()
    for product in PRODUCT_ORDER:
        if product in url_lower:
            return product
    return 'other'


def smart_sort_images(images, max_images=10):
    """
    كل منتج صورة واحدة بس - لا تكرار نهائياً
    """
    if not images:
        return []

    # الخطوة 1: جمّع الصور حسب نوع المنتج
    grouped = {}
    for img in images:
        ptype = detect_product_type(img)
        grouped.setdefault(ptype, []).append(img)

    print(f"📦 Product types found: {list(grouped.keys())}")

    # الخطوة 2: خذ صورة واحدة بس من كل نوع
    one_per_type = {}
    for ptype, imgs in grouped.items():
        one_per_type[ptype] = imgs[0]

    # الخطوة 3: رتّب حسب PRIORITY_PRODUCTS أولاً
    final = []

    for ptype in PRIORITY_PRODUCTS:
        if ptype in one_per_type:
            final.append(one_per_type[ptype])
            del one_per_type[ptype]
        if len(final) >= max_images:
            break

    # باقي المنتجات حسب PRODUCT_ORDER
    if len(final) < max_images:
        for ptype in PRODUCT_ORDER:
            if ptype in one_per_type:
                final.append(one_per_type[ptype])
                del one_per_type[ptype]
            if len(final) >= max_images:
                break

    # أي منتج متبقي
    if len(final) < max_images:
        for img in one_per_type.values():
            final.append(img)
            if len(final) >= max_images:
                break

    print(f"🎯 Final: {len(final)} images - one per product type")
    print(f"📋 Order: {[detect_product_type(img) for img in final]}")

    return final[:max_images]
