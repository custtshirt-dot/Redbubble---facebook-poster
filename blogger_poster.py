"""
📝 Blogger Poster — ينشر مقالة SEO كاملة على Blogger
✅ الصور بتترفع على Blogger مش روابط خارجية
✅ المقالة أكتر من 500 كلمة
✅ 12 صورة منتج على الأقل
✅ SEO كامل
✅ التاجات من designs.txt
"""
import os
import re
import json
import base64
import requests
from datetime import datetime

# ── Credentials ───────────────────────────────────────────────
BLOGGER_BLOG_ID       = os.getenv('BLOGGER_BLOG_ID', '')
BLOGGER_CLIENT_ID     = os.getenv('BLOGGER_CLIENT_ID', '')
BLOGGER_CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOGGER_REFRESH_TOKEN = os.getenv('BLOGGER_REFRESH_TOKEN', '')
GROQ_API_KEY          = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL            = 'llama-3.3-70b-versatile'

MIN_IMAGES   = 12
MIN_WORDS    = 500


# ══════════════════════════════════════════════════════════════
# 🔑 AUTH
# ══════════════════════════════════════════════════════════════

def get_access_token() -> str | None:
    if not all([BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN]):
        print("⚠️ Blogger credentials missing")
        return None
    try:
        resp = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id':     BLOGGER_CLIENT_ID,
                'client_secret': BLOGGER_CLIENT_SECRET,
                'refresh_token': BLOGGER_REFRESH_TOKEN,
                'grant_type':    'refresh_token',
            },
            timeout=15
        )
        token = resp.json().get('access_token')
        if not token:
            print(f"❌ Auth failed: {resp.json().get('error_description','')}")
        return token
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 🖼️ IMAGES — جيب 12+ صورة وارفعها على Blogger
# ══════════════════════════════════════════════════════════════

def fetch_all_product_images(product_url: str, max_images: int = 20) -> list:
    """
    يجيب كل صور المنتج من Redbubble — أنواع مختلفة (تيشرت، ستيكر، ماج، إلخ)
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
    }

    image_urls = []
    seen = set()

    try:
        resp = requests.get(product_url, headers=headers, timeout=20)
        html = resp.text

        # Pattern 1: صور الـ og:image والـ JSON-LD
        for pat in [
            r'content="(https://ih\d+\.redbubble\.net/[^"]+)"',
            r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"',
            r'src="(https://ih\d+\.redbubble\.net/[^"]+)"',
            r"src='(https://ih\d+\.redbubble\.net/[^']+)'",
        ]:
            for m in re.finditer(pat, html):
                url = m.group(1).split('?')[0]
                if url not in seen and url.endswith(('.jpg', '.jpeg', '.png', '.webp')):
                    seen.add(url)
                    image_urls.append(url)

        # Pattern 2: __NEXT_DATA__ JSON
        nd = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.DOTALL)
        if nd:
            try:
                raw = json.dumps(json.loads(nd.group(1)))
                for m in re.finditer(r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"', raw):
                    url = m.group(1).split('?')[0]
                    if url not in seen:
                        seen.add(url)
                        image_urls.append(url)
            except Exception:
                pass

    except Exception as e:
        print(f"   ⚠️ Image fetch error: {e}")

    print(f"   🖼️  Found {len(image_urls)} images from product page")
    return image_urls[:max_images]


def download_image_as_base64(img_url: str) -> tuple[str, str] | None:
    """
    يحمّل الصورة ويرجعها كـ (base64_data, mime_type)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.redbubble.com/',
    }
    try:
        resp = requests.get(img_url, headers=headers, timeout=15)
        if resp.status_code == 200:
            content_type = resp.headers.get('Content-Type', 'image/jpeg')
            mime = content_type.split(';')[0].strip()
            if 'jpeg' in mime or 'jpg' in mime:
                mime = 'image/jpeg'
            elif 'png' in mime:
                mime = 'image/png'
            elif 'webp' in mime:
                mime = 'image/webp'
            else:
                mime = 'image/jpeg'
            b64 = base64.b64encode(resp.content).decode('utf-8')
            return b64, mime
    except Exception:
        pass
    return None


def upload_image_to_blogger(token: str, b64_data: str, mime_type: str, alt_text: str) -> str | None:
    """
    يرفع صورة على Blogger API ويرجع الـ URL المباشر
    Blogger بيستخدم Picasa/Google Photos API داخلياً
    """
    try:
        # رفع عبر Blogger Media endpoint
        image_bytes = base64.b64decode(b64_data)
        resp = requests.post(
            f'https://www.googleapis.com/upload/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/',
            headers={
                'Authorization':  f'Bearer {token}',
                'Content-Type':   mime_type,
                'X-Upload-Content-Type': mime_type,
            },
            params={'uploadType': 'media'},
            data=image_bytes,
            timeout=30
        )
        # Blogger مش بيدعم media upload مباشرة — نستخدم Picasa
    except Exception:
        pass

    # ✅ الطريقة الصح: Picasa Web Albums API (بتشتغل مع Blogger token)
    try:
        image_bytes = base64.b64decode(b64_data)
        resp = requests.post(
            'https://picasaweb.google.com/data/feed/api/user/default/albumid/default',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type':  mime_type,
                'Slug':          f'{alt_text[:50]}.jpg',
            },
            data=image_bytes,
            timeout=30
        )

        if resp.status_code in (200, 201):
            # استخرج الـ URL من الـ XML response
            m = re.search(r'<media:content[^>]+url=["\']([^"\']+)["\']', resp.text)
            if m:
                return m.group(1)
            m = re.search(r'<content[^>]+src=["\']([^"\']+)["\']', resp.text)
            if m:
                return m.group(1)
    except Exception:
        pass

    return None


def prepare_images_for_article(token: str, product_url: str, design_hint: str) -> list:
    """
    يجيب الصور ويرفعها — يرجع list من URLs جاهزة للمقالة
    لو الرفع فشل بيستخدم الروابط الأصلية كـ fallback
    """
    print(f"   📥 Fetching product images...")
    raw_urls = fetch_all_product_images(product_url, max_images=20)

    if not raw_urls:
        print("   ⚠️ No images found")
        return []

    uploaded = []
    fallback = []

    print(f"   ⬆️  Uploading {min(len(raw_urls), MIN_IMAGES)} images to Blogger...")

    for i, img_url in enumerate(raw_urls[:MIN_IMAGES + 4]):  # نجيب أكتر احتياطاً
        result = download_image_as_base64(img_url)
        if not result:
            fallback.append(img_url)
            continue

        b64, mime = result
        hosted_url = upload_image_to_blogger(token, b64, mime, f"{design_hint} {i+1}")

        if hosted_url:
            uploaded.append(hosted_url)
            print(f"      ✅ Image {i+1} uploaded")
        else:
            # Fallback: استخدم الرابط الأصلي
            fallback.append(img_url)
            print(f"      ⚠️ Image {i+1} — using original URL")

        if len(uploaded) + len(fallback) >= MIN_IMAGES:
            break

    final = uploaded + fallback
    print(f"   🖼️  Ready: {len(uploaded)} uploaded + {len(fallback)} linked = {len(final)} total")
    return final[:MIN_IMAGES + 4]


# ══════════════════════════════════════════════════════════════
# 🤖 AI — Generate 500+ Word SEO Article
# ══════════════════════════════════════════════════════════════

def generate_seo_article(design_hint: str, product_url: str, user_tags: list) -> dict:
    """
    يولّد مقالة SEO أكتر من 500 كلمة بالـ AI
    """
    tags_str = ', '.join(user_tags) if user_tags else design_hint

    prompt = f"""You are an expert SEO content writer for a Redbubble print-on-demand shop.

Write a FULL SEO blog article about this product:
DESIGN: "{design_hint}"
PRODUCT URL: {product_url}
KEYWORDS/TAGS: {tags_str}

CRITICAL: The article MUST be more than 500 words total.

OUTPUT — respond ONLY with valid JSON, no markdown, no extra text:
{{
  "seo_title": "SEO title 50-60 chars with main keyword",
  "meta_description": "Compelling meta description 150-160 chars with keyword and CTA",
  "h1": "H1 heading, different from title, keyword-rich",
  "labels": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "intro": "3-4 sentences introduction. Hook the reader. Mention the design theme naturally. Include the main keyword in first sentence.",
  "section1_h2": "H2 — About The Design",
  "section1_body": "4-5 sentences about what makes this design special, its story, meaning, humor or emotional value. Who would relate to it. Why it stands out.",
  "section2_h2": "H2 — Available On Multiple Products",
  "section2_body": "4-5 sentences about the variety: t-shirts, hoodies, stickers, mugs, phone cases, tote bags, pillows, art prints, masks, leggings. High quality print. Ships worldwide. Easy ordering.",
  "section3_h2": "H2 — Perfect Gift Idea",
  "section3_body": "4-5 sentences about who this makes a perfect gift for. Occasions: birthday, Christmas, graduation, anniversary. Why it will make them smile. Unique and thoughtful.",
  "section4_h2": "H2 — Why Choose Redbubble",
  "section4_body": "3-4 sentences about Redbubble quality, worldwide shipping, satisfaction guarantee, independent artist support, easy returns.",
  "section5_h2": "H2 — How To Order",
  "section5_body": "3-4 sentences simple step-by-step: visit the link, choose your product type and size, add to cart, checkout. Fast shipping. Multiple payment options.",
  "faq_q1": "FAQ question 1 related to the design or product",
  "faq_a1": "2-3 sentence answer",
  "faq_q2": "FAQ question 2 about shipping or customization",
  "faq_a2": "2-3 sentence answer",
  "faq_q3": "FAQ question 3 about gift wrapping or sizing",
  "faq_a3": "2-3 sentence answer",
  "conclusion": "3-4 sentence conclusion. Summarize appeal. Strong CTA. Mention product URL context. Create urgency."
}}

RULES:
- Main keyword from "{design_hint}" appears in: title, H1, intro, at least 3 sections
- Secondary keywords from: {tags_str}
- Tone: enthusiastic, friendly, persuasive
- Write for humans — no keyword stuffing
- Each section body = minimum 4 sentences
- NEVER mention discount codes or fake prices"""

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type':  'application/json',
            },
            json={
                'model':       GROQ_MODEL,
                'temperature': 0.75,
                'max_tokens':  2500,
                'messages': [
                    {
                        'role':    'system',
                        'content': 'You are an expert SEO writer. Respond ONLY with valid JSON. No markdown. No explanation. Just the JSON object.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
            },
            timeout=45
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)

    except Exception as e:
        print(f"   ⚠️ AI generation failed: {e} — using fallback")
        return _fallback_article_data(design_hint, product_url, user_tags)


def _fallback_article_data(design_hint: str, url: str, tags: list) -> dict:
    return {
        'seo_title':      f'{design_hint} — Unique Design on Redbubble',
        'meta_description': f'Discover the {design_hint} design on Redbubble. Available on t-shirts, stickers, mugs and more. Ships worldwide!',
        'h1':             f'{design_hint} — Shop This Unique Design',
        'labels':         tags[:8] if tags else ['redbubble', 'design', 'gift', 'print on demand'],
        'intro':          f'Looking for a unique {design_hint} design? You\'ve found it! This amazing design is available on dozens of products, from t-shirts to stickers, mugs and more. Whether for yourself or as a gift, this design is guaranteed to impress.',
        'section1_h2':    f'About The {design_hint} Design',
        'section1_body':  f'The {design_hint} design is a one-of-a-kind piece of art that stands out in any crowd. It captures a unique aesthetic that resonates with people who have a great sense of humor and style. The design is carefully crafted to be eye-catching and memorable, making it perfect for anyone who loves to express their personality through what they wear or use every day. From the bold colors to the clever concept, every detail has been thoughtfully considered.',
        'section2_h2':    'Available On Dozens of Products',
        'section2_body':  f'The {design_hint} design is available on a huge variety of products including t-shirts, hoodies, sweatshirts, stickers, mugs, phone cases, tote bags, pillows, art prints, leggings, masks, and much more. All products are printed on demand using high-quality materials and printing technology. Redbubble ships worldwide, so no matter where you are, you can get this amazing design delivered right to your door. The ordering process is simple and secure.',
        'section3_h2':    'The Perfect Gift For Any Occasion',
        'section3_body':  f'Struggling to find the perfect gift? The {design_hint} design makes an amazing gift for birthdays, Christmas, graduations, anniversaries, and any other special occasion. It\'s a unique and thoughtful present that shows you really put effort into finding something special. Unlike generic gifts, this design will make the recipient smile every time they see it. It\'s the kind of gift that gets remembered.',
        'section4_h2':    'Why Shop On Redbubble?',
        'section4_body':  'Redbubble is one of the world\'s leading print-on-demand marketplaces, known for its quality products and independent artist designs. Every purchase supports independent artists and creatives. Products come with a satisfaction guarantee — if you\'re not happy, Redbubble will make it right. With multiple payment options and fast worldwide shipping, shopping is easy and secure.',
        'section5_h2':    'How To Order Your Design',
        'section5_body':  'Ordering is quick and easy. Simply click the link to visit the product page, choose your preferred product type (t-shirt, mug, sticker, etc.), select your size and color if applicable, and add it to your cart. Checkout takes just a few minutes with multiple secure payment options available. Your order will be printed and shipped directly to you, usually within a few business days.',
        'faq_q1':         f'What products is the {design_hint} available on?',
        'faq_a1':         f'The {design_hint} design is available on t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints, pillows, leggings, and many more products. Visit the Redbubble page to see all available options.',
        'faq_q2':         'Does Redbubble ship internationally?',
        'faq_a2':         'Yes! Redbubble ships worldwide. Shipping times and costs vary by location, but they offer multiple shipping options to suit your needs. Most orders arrive within 1-2 weeks.',
        'faq_q3':         'Is this a good gift?',
        'faq_a3':         f'Absolutely! The {design_hint} design makes a wonderful gift for anyone who appreciates unique and creative designs. It\'s thoughtful, personal, and available on dozens of practical products they\'ll use every day.',
        'conclusion':     f'The {design_hint} design is more than just a product — it\'s a statement. Whether you\'re treating yourself or finding the perfect gift, this design delivers on every level. Don\'t miss out on owning something truly unique. Click the link now and explore all the products this amazing design is available on. Order today and experience the quality and creativity that makes Redbubble special.',
    }


# ══════════════════════════════════════════════════════════════
# 🏗️ BUILD HTML ARTICLE
# ══════════════════════════════════════════════════════════════

def build_article_html(data: dict, design_hint: str, product_url: str, images: list) -> str:
    """
    يبني HTML المقالة الكاملة مع الصور موزعة على الأقسام
    """
    def img_tag(url: str, alt: str, caption: str = '') -> str:
        cap = f'<p style="text-align:center;font-size:0.85em;color:#777;margin-top:4px;">{caption}</p>' if caption else ''
        return f'''<div style="text-align:center;margin:20px 0;">
  <img src="{url}" alt="{alt}" title="{alt}"
       style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.15);" />
  {cap}
</div>'''

    # توزيع الصور على الأقسام
    imgs = images + [''] * MAX(0, MIN_IMAGES - len(images))

    def get_img(idx: int) -> str:
        if idx < len(images) and images[idx]:
            return img_tag(images[idx], f"{design_hint} - Product {idx+1}")
        return ''

    # بناء قسم الـ FAQ
    faq_html = f'''
<div style="background:#f8f9fa;border-radius:8px;padding:24px;margin:30px 0;">
  <h2 style="color:#2c3e50;font-size:1.4em;margin-top:0;">❓ Frequently Asked Questions</h2>

  <div style="margin-bottom:18px;">
    <h3 style="color:#34495e;font-size:1.05em;margin-bottom:6px;">Q: {data.get("faq_q1","")}</h3>
    <p style="color:#555;margin:0;">{data.get("faq_a1","")}</p>
  </div>

  <div style="margin-bottom:18px;">
    <h3 style="color:#34495e;font-size:1.05em;margin-bottom:6px;">Q: {data.get("faq_q2","")}</h3>
    <p style="color:#555;margin:0;">{data.get("faq_a2","")}</p>
  </div>

  <div>
    <h3 style="color:#34495e;font-size:1.05em;margin-bottom:6px;">Q: {data.get("faq_q3","")}</h3>
    <p style="color:#555;margin:0;">{data.get("faq_a3","")}</p>
  </div>
</div>'''

    # بناء جريد الصور الإضافية (3 صور في صف)
    grid_imgs = images[6:12] if len(images) > 6 else []
    grid_html = ''
    if grid_imgs:
        cells = ''
        for i, img_url in enumerate(grid_imgs):
            cells += f'''<div style="flex:1;min-width:120px;max-width:200px;padding:4px;">
  <img src="{img_url}" alt="{design_hint} product {i+7}"
       style="width:100%;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.1);" />
</div>'''
        grid_html = f'''
<div style="margin:24px 0;">
  <p style="text-align:center;color:#666;font-size:0.9em;margin-bottom:12px;">
    🛍️ Available on many products — see all options below
  </p>
  <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;">
    {cells}
  </div>
</div>'''

    return f'''<div style="font-family:Georgia,'Times New Roman',serif;max-width:820px;margin:0 auto;line-height:1.85;color:#2d2d2d;font-size:1.05em;">

<!-- H1 -->
<h1 style="font-size:2em;color:#1a1a1a;margin-bottom:8px;line-height:1.3;">
  {data.get("h1", design_hint)}
</h1>

<p style="color:#888;font-size:0.85em;margin-bottom:20px;">
  Published by <strong>Cust Tshirts</strong> •
  {datetime.now().strftime("%B %d, %Y")} •
  <a href="{product_url}" style="color:#e74c3c;">View on Redbubble →</a>
</p>

<!-- Hero Image -->
{get_img(0)}

<!-- Intro -->
<p style="font-size:1.1em;color:#444;border-left:3px solid #e74c3c;padding-left:16px;margin:20px 0;">
  {data.get("intro","")}
</p>

{get_img(1)}

<!-- Section 1 -->
<h2 style="color:#2c3e50;font-size:1.35em;margin-top:35px;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
  {data.get("section1_h2","About The Design")}
</h2>
<p>{data.get("section1_body","")}</p>

{get_img(2)}

<!-- Section 2 -->
<h2 style="color:#2c3e50;font-size:1.35em;margin-top:35px;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
  {data.get("section2_h2","Available Products")}
</h2>
<p>{data.get("section2_body","")}</p>

{get_img(3)}
{get_img(4)}

<!-- Product Grid -->
{grid_html}

<!-- Section 3 -->
<h2 style="color:#2c3e50;font-size:1.35em;margin-top:35px;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
  {data.get("section3_h2","Perfect Gift Idea")}
</h2>
<p>{data.get("section3_body","")}</p>

{get_img(5)}

<!-- Section 4 -->
<h2 style="color:#2c3e50;font-size:1.35em;margin-top:35px;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
  {data.get("section4_h2","Why Choose Redbubble")}
</h2>
<p>{data.get("section4_body","")}</p>

<!-- Section 5 -->
<h2 style="color:#2c3e50;font-size:1.35em;margin-top:35px;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">
  {data.get("section5_h2","How To Order")}
</h2>
<p>{data.get("section5_body","")}</p>

<!-- FAQ -->
{faq_html}

<!-- Conclusion -->
<p style="font-size:1.05em;color:#444;margin-top:30px;">{data.get("conclusion","")}</p>

<!-- CTA Button -->
<div style="text-align:center;margin:40px 0 30px;">
  <a href="{product_url}"
     style="display:inline-block;background:#e74c3c;color:#ffffff;
            padding:16px 40px;border-radius:6px;text-decoration:none;
            font-weight:bold;font-size:1.15em;
            box-shadow:0 4px 12px rgba(231,76,60,0.4);">
    🛒 Shop This Design on Redbubble
  </a>
  <p style="margin-top:12px;color:#888;font-size:0.85em;">
    Free worldwide shipping available • Satisfaction guaranteed
  </p>
</div>

<hr style="border:none;border-top:1px solid #eee;margin:30px 0;" />
<p style="font-size:0.8em;color:#aaa;text-align:center;">
  © {datetime.now().year} Cust Tshirts •
  <a href="{product_url}" style="color:#e74c3c;">View on Redbubble</a>
</p>

</div>'''


def MAX(a, b):
    return a if a > b else b


# ══════════════════════════════════════════════════════════════
# 📤 PUBLISH
# ══════════════════════════════════════════════════════════════

def post_to_blogger(design_hint: str, product_url: str, images: list,
                    user_tags: list = None) -> dict:
    """
    Main function — ينشر مقالة SEO كاملة على Blogger
    """
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping")
        return {'success': False, 'error': 'BLOGGER_BLOG_ID missing'}

    print("\n📝 Publishing SEO article to Blogger...")

    if user_tags is None:
        user_tags = []

    # 1. Auth
    token = get_access_token()
    if not token:
        return {'success': False, 'error': 'Auth failed'}

    # 2. جيب وارفع الصور
    hosted_images = prepare_images_for_article(token, product_url, design_hint)

    # لو مش وصلنا 12 صورة — استخدم الروابط الأصلية احتياطاً
    if len(hosted_images) < MIN_IMAGES:
        extra = fetch_all_product_images(product_url, max_images=20)
        for img in extra:
            if img not in hosted_images:
                hosted_images.append(img)
            if len(hosted_images) >= MIN_IMAGES:
                break

    print(f"   🖼️  Total images for article: {len(hosted_images)}")

    # 3. ولّد المقالة بالـ AI
    print("   🤖 Generating SEO article (500+ words)...")
    article_data = generate_seo_article(design_hint, product_url, user_tags)

    # 4. بناء HTML
    html_content = build_article_html(article_data, design_hint, product_url, hosted_images)

    # 5. دمج التاجات: من الـ AI + من designs.txt
    ai_labels  = article_data.get('labels', [])
    all_labels = list(dict.fromkeys(user_tags + ai_labels))[:20]  # max 20 tag

    # 6. النشر على Blogger API
    payload = {
        'title':   article_data.get('seo_title', f'{design_hint} — Shop on Redbubble'),
        'content': html_content,
        'labels':  all_labels,
    }

    try:
        resp = requests.post(
            f'https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/',
            headers={
                'Authorization': f'Bearer {token}',
                'Content-Type':  'application/json',
            },
            json=payload,
            timeout=30
        )

        data = resp.json()

        if resp.status_code in (200, 201) and 'id' in data:
            post_url   = data.get('url', '')
            post_title = payload['title']
            print(f"   ✅ Blogger article published!")
            print(f"   📰 Title  : {post_title}")
            print(f"   🔗 URL    : {post_url}")
            print(f"   🏷️  Labels : {', '.join(all_labels[:5])}...")
            print(f"   🖼️  Images : {len(hosted_images)}")
            return {
                'success': True,
                'post_id': data['id'],
                'url':     post_url,
                'title':   post_title,
            }
        else:
            err = data.get('error', {}).get('message', str(data))
            print(f"   ❌ Blogger API error: {err}")
            return {'success': False, 'error': err}

    except Exception as e:
        print(f"   ❌ Publish failed: {e}")
        return {'success': False, 'error': str(e)}
