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


def smart_sort_images(images, max_images=30):
    """
    Smart sorting:
    1. Priority products first (stickers, postcards - your best sellers)
    2. Interleave to prevent same product type appearing consecutively
    """
    if not images:
        return []
    
    # Group by type
    grouped = {}
    for img in images:
        ptype = detect_product_type(img)
        grouped.setdefault(ptype, []).append(img)
    
    # Separate priority from rest
    priority_imgs = []
    other_imgs = []
    
    for ptype in PRIORITY_PRODUCTS:
        if ptype in grouped:
            priority_imgs.extend(grouped[ptype])
            del grouped[ptype]
    
    for ptype, imgs in grouped.items():
        other_imgs.extend(imgs)
    
    # Interleave to avoid duplicates next to each other
    def interleave(imgs):
        by_type = {}
        for img in imgs:
            t = detect_product_type(img)
            by_type.setdefault(t, []).append(img)
        
        result = []
        while any(by_type.values()):
            for t in list(by_type.keys()):
                if by_type[t]:
                    result.append(by_type[t].pop(0))
                else:
                    del by_type[t]
        return result
    
    final = interleave(priority_imgs) + interleave(other_imgs)
    
    print(f"🎯 Sorted: {len(priority_imgs)} priority + {len(other_imgs)} others")
    return final[:max_images]
