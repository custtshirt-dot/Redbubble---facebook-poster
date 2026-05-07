"""
⚙️ إعدادات المشروع
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============ Facebook ============
FB_PAGE_ID = os.getenv("FB_PAGE_ID", "772609922609531")
FB_TOKEN = os.getenv("FB_TOKEN", "ضع_التوكن_هنا")

# ============ Groq AI ============
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "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")
GROQ_MODEL = "llama-3.3-70b-versatile"  # أقوى موديل مجاني

# ============ Headers ============
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.redbubble.com/',
}

# ============ منتجات الأولوية (المبيعات الأخيرة) ============
PRIORITY_PRODUCTS = [
    'sticker', 'postcard', 'holographic', 'magnet', 'pin'
]

PRODUCT_ORDER = [
    'sticker', 'postcard', 'magnet', 'pin', 'mug', 'tshirt', 't-shirt',
    'hoodie', 'tank', 'pullover', 'sweatshirt', 'long-sleeve', 'baseball',
    'poster', 'print', 'canvas', 'metal-print', 'photographic-print',
    'tote', 'bag', 'backpack', 'pouch', 'phone-case', 'iphone', 'samsung',
    'laptop', 'notebook', 'journal', 'spiral', 'hardcover',
    'pillow', 'throw', 'blanket', 'duvet', 'mounted', 'tapestry',
    'apron', 'socks', 'leggings', 'scarf', 'mask', 'cap', 'hat',
    'water-bottle', 'travel-mug', 'coaster', 'clock'
]

# ============ Output Folders ============
OUTPUT_DIR = "output"
VIDEO_DIR = os.path.join(OUTPUT_DIR, "videos")
TEMP_DIR = os.path.join(OUTPUT_DIR, "temp")

os.makedirs(VIDEO_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
