"""
🔧 Configuration Module
Loads all environment variables and settings
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

# ============================================================
# 🔒 SECRETS
# ============================================================
FB_PAGE_ID = os.getenv('FB_PAGE_ID')
FB_TOKEN = os.getenv('FB_TOKEN')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# ============================================================
# 📝 USER INPUTS
# ============================================================
REDBUBBLE_URL = os.getenv('REDBUBBLE_URL', '').strip()
POST_TYPE = os.getenv('POST_TYPE', 'album').lower()
MAX_IMAGES = int(os.getenv('MAX_IMAGES', '30'))
LANGUAGE = os.getenv('LANGUAGE', 'english').lower()
STYLE = os.getenv('STYLE', 'mixed').lower()

# ============================================================
# 🌐 HTTP HEADERS
# ============================================================
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Referer': 'https://www.redbubble.com/',
}

# ============================================================
# 🎯 PRODUCT PRIORITY
# كل منتج هيظهر مرة واحدة بس - بالترتيب ده
# ============================================================
PRIORITY_PRODUCTS = [
    't-shirt',      # 1. تيشيرت - الأوضح والأكتر مبيعاً
    'mug',          # 2. ماج - هدية مثالية
    'hoodie',       # 3. هودي
    'sticker',      # 4. ستيكر
    'holographic',  # 5. هولوجرافيك ستيكر
    'tote',         # 6. توت باج
    'phone-case',   # 7. كفر موبايل
    'art-board',    # 8. آرت برينت
    'magnet',       # 9. ماجنيت
    'postcard',     # 10. بوستكارد
]

# ============================================================
# 🚫 منتجات ممنوعة - مش هتظهر نهائياً
# ============================================================
EXCLUDED_PRODUCTS = [
    'pin',
    'kids',
    'baby',
    'mask',
    'mat',
]

# ============================================================
# 🖼️ منع التكرار
# ============================================================
ONE_IMAGE_PER_PRODUCT = True
MAX_SAME_PRODUCT = 1

# ============================================================
# 📦 ترتيب باقي المنتجات
# ============================================================
PRODUCT_ORDER = [
    't-shirt', 'mug', 'hoodie', 'sticker', 'holographic',
    'tote', 'phone-case', 'art-board', 'magnet', 'postcard',
    'pullover', 'sweatshirt', 'long-sleeve', 'baseball',
    'poster', 'print', 'canvas', 'metal-print', 'photographic-print',
    'bag', 'backpack', 'pouch', 'iphone', 'samsung',
    'laptop', 'notebook', 'journal', 'spiral', 'hardcover',
    'pillow', 'throw', 'blanket', 'duvet', 'mounted', 'tapestry',
    'apron', 'socks', 'leggings', 'scarf', 'cap', 'hat',
    'water-bottle', 'travel-mug', 'coaster', 'clock', 'tank',
]

# ============================================================
# ✅ VALIDATION
# ============================================================
def validate_config():
    missing = []
    if not FB_PAGE_ID:
        missing.append('FB_PAGE_ID')
    if not FB_TOKEN:
        missing.append('FB_TOKEN')
    if not REDBUBBLE_URL:
        missing.append('REDBUBBLE_URL')

    if missing:
        print(f"❌ Missing required variables: {', '.join(missing)}")
        sys.exit(1)

    if not GROQ_API_KEY:
        print("⚠️ Warning: GROQ_API_KEY not set. Will use template captions.")

    print(f"""
╔══════════════════════════════════════════════════╗
║  🚀 REDBUBBLE AUTO POSTER - Configuration       ║
╠══════════════════════════════════════════════════╣
║  🔗 URL:        {REDBUBBLE_URL[:33]}...
║  📝 Type:       {POST_TYPE}
║  📸 Max Images: {MAX_IMAGES}
║  🌍 Language:   {LANGUAGE}
║  🎨 Style:      {STYLE}
║  🤖 AI:         {'Enabled (Groq)' if GROQ_API_KEY else 'Disabled (Templates)'}
║  🚫 No duplicates: {ONE_IMAGE_PER_PRODUCT}
╚══════════════════════════════════════════════════╝
""")
    return True
