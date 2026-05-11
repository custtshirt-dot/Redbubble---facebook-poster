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
FB_PAGE_ID        = os.getenv('FB_PAGE_ID', '').strip()
FB_TOKEN          = os.getenv('FB_TOKEN', '').strip()
GROQ_API_KEY      = os.getenv('GROQ_API_KEY', '').strip()

# Instagram
INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID', '').strip()
INSTAGRAM_TOKEN   = os.getenv('INSTAGRAM_TOKEN', '').strip()

# Pinterest
PINTEREST_TOKEN    = os.getenv('PINTEREST_TOKEN', '').strip()
PINTEREST_BOARD_ID = os.getenv('PINTEREST_BOARD_ID', '').strip()
PINTEREST_USERNAME = os.getenv('PINTEREST_USERNAME', '').strip()

# ============================================================
# 🏪 REDBUBBLE SETTINGS
# ============================================================

# رابط الستور الكامل (للسكان الأوتوماتيك)
# مثال: https://www.redbubble.com/people/USERNAME/shop
REDBUBBLE_STORE_URL = os.getenv('REDBUBBLE_STORE_URL', '').strip()

# رابط منتج يدوي مباشر (اختياري — يـ override الأوتوماتيك)
# لو موجود بيتجاهل الستور ويستخدم الرابط ده مباشرة
REDBUBBLE_URL = os.getenv('REDBUBBLE_URL', '').strip()

# ============================================================
# 📝 POST SETTINGS
# ============================================================
# القيم: album | single | carousel | link | text | video | reels | all | auto
POST_TYPE  = os.getenv('POST_TYPE', 'auto').lower()
MAX_IMAGES = int(os.getenv('MAX_IMAGES', '30'))
LANGUAGE   = os.getenv('LANGUAGE', 'english').lower()
STYLE      = os.getenv('STYLE', 'mixed').lower()

# index للدوّرة (بيتحدث الـ workflow أوتوماتيك)
POST_ROTATION_INDEX = int(os.getenv('POST_ROTATION_INDEX', '0'))

# ============================================================
# 🌐 HTTP HEADERS
# ============================================================
HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Referer': 'https://www.redbubble.com/',
}

# ============================================================
# 🎯 PRODUCT PRIORITY
# ============================================================
PRIORITY_PRODUCTS = [
    't-shirt',
    'mug',
    'hoodie',
    'sticker',
    'holographic',
    'tote',
    'phone-case',
    'art-board',
    'magnet',
    'postcard',
]

# ============================================================
# 🚫 EXCLUDED PRODUCTS
# ============================================================
EXCLUDED_PRODUCTS = [
    'pin',
    'kids',
    'baby',
    'mask',
    'mat',
]

# ============================================================
# 🖼️ IMAGE SETTINGS
# ============================================================
ONE_IMAGE_PER_PRODUCT = True
MAX_SAME_PRODUCT = 1

# ============================================================
# 📦 PRODUCT ORDER
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
    if not REDBUBBLE_STORE_URL and not REDBUBBLE_URL:
        missing.append('REDBUBBLE_STORE_URL (or REDBUBBLE_URL)')

    if missing:
        print(f"❌ Missing required variables: {', '.join(missing)}")
        print("\nRequired GitHub Secrets:")
        print("  - FB_PAGE_ID            : Facebook Page ID")
        print("  - FB_TOKEN              : Facebook Page Token")
        print("  - REDBUBBLE_STORE_URL   : https://www.redbubble.com/people/USERNAME/shop")
        print("  - GROQ_API_KEY          : (optional) for AI captions")
        sys.exit(1)

    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY not set — will use template captions (still works!)")

    mode = "Manual URL" if REDBUBBLE_URL else "Auto (Store Scan)"
    store_display = (REDBUBBLE_STORE_URL or REDBUBBLE_URL)[:45] + '...'

    print(f"""
╔══════════════════════════════════════════════════╗
║  🚀 REDBUBBLE AUTO POSTER v2.0                  ║
╠══════════════════════════════════════════════════╣
║  🏪 Store:       {store_display:<29}║
║  🤖 Mode:        {mode:<29}║
║  📝 Post Type:   {POST_TYPE:<29}║
║  📸 Max Images:  {str(MAX_IMAGES):<29}║
║  🌍 Language:    {LANGUAGE:<29}║
║  🎨 Style:       {STYLE:<29}║
║  🤖 AI:          {'Enabled (Groq)' if GROQ_API_KEY else 'Disabled (Templates)':<29}║
║  🔄 Rotation #:  {str(POST_ROTATION_INDEX):<29}║
╚══════════════════════════════════════════════════╝
""")
    return True
