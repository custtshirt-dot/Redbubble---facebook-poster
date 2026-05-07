"""
🖼️ استخراج وترتيب صور المنتجات
"""
import requests
import re
from config import HEADERS, PRIORITY_PRODUCTS, PRODUCT_ORDER


def extract_all_images(url):
    """استخراج كل الصور الحقيقية من صفحة Redbubble"""
    print("🔍 Extracting product images...")
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        html = r.text
        pattern = re.compile(r'https://ih1\.redbubble\.net/image\.[^"\']+\.jpg')
        all_images = pattern.findall(html)
        unique_images = list(dict.fromkeys(all_images))
        print(f"✅ Found {len(unique_images)} unique images")
        return unique_images
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def detect_product_type(image_url):
    """تحديد نوع المنتج من الرابط"""
    url_lower = image_url.lower()
    for product in PRODUCT_ORDER:
        if product in url_lower:
            return product
    return 'other'


def smart_sort_images(images):
    """ترتيب ذكي: الأولوية في الأول + منع التكرار المتتالي"""
    grouped = {}
    for img in images:
        ptype = detect_product_type(img)
        grouped.setdefault(ptype, []).append(img)
    
    priority_imgs = []
    other_imgs = []
    
    for ptype in PRIORITY_PRODUCTS:
        if ptype in grouped:
            priority_imgs.extend(grouped[ptype])
            del grouped[ptype]
    
    for ptype, imgs in grouped.items():
        other_imgs.extend(imgs)
    
    def interleave(imgs):
        """خلط ذكي لمنع التكرار"""
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
    return final
