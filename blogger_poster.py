"""
📝 Blogger Poster — ينشر مقالة SEO احترافية على Blogger
✅ أسلوب المقال مطابق لقالب الموقع (ألوان، تنسيق، HTML)
✅ التاجات والوصف من designs.txt
✅ أسماء كل المنتجات المتاحة في المقال
✅ صور Redbubble
✅ 500+ كلمة مع SEO كامل
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
STORE_URL             = 'https://www.redbubble.com/people/cust-tshirts/shop'

MIN_IMAGES = 12

# كل المنتجات المتاحة على Redbubble
ALL_PRODUCTS = [
    'Classic T-Shirt', 'Fitted T-Shirt', 'Relaxed T-Shirt',
    'Pullover Hoodie', 'Zip Hoodie', 'Pullover Sweatshirt',
    'Sticker', 'Transparent Sticker', 'Glossy Sticker',
    'Mug', 'Travel Mug', 'Water Bottle',
    'Phone Case', 'Tough Phone Case',
    'Tote Bag', 'Drawstring Bag',
    'Throw Pillow', 'Duvet Cover',
    'Art Print', 'Poster', 'Canvas Print',
    'Photographic Print', 'Art Board Print',
    'Leggings', 'Dress', 'Scarf',
    'Laptop Skin', 'Laptop Sleeve',
    'Greeting Card', 'Spiral Notebook',
    'Pin', 'Magnet',
    'Face Mask', 'Bucket Hat',
]


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
            print(f"❌ Auth failed: {resp.json().get('error_description', '')}")
        return token
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 🔍 SCRAPE DESIGN DATA FROM REDBUBBLE
# ══════════════════════════════════════════════════════════════

def scrape_design_data(product_url: str) -> dict:
    """
    يسحب من صفحة Redbubble:
    - عنوان التصميم الحقيقي
    - الوصف
    - التاجات
    - أسماء المنتجات المتاحة فعلاً
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.redbubble.com/',
    }
    result = {
        'title': '',
        'description': '',
        'tags': [],
        'products': [],
    }
    try:
        # لو /shop/ap/ URL — حوله لـ /i/ أولاً عشان نجيب البيانات الصح
        scrape_url = product_url
        if '/shop/ap/' in product_url:
            import re as _re2
            work_id_m = _re2.search(r'/shop/ap/(\d+)', product_url)
            if work_id_m:
                try:
                    r0 = requests.get(product_url, headers=headers, timeout=20, allow_redirects=True)
                    m0 = _re2.search(r'(https://www\.redbubble\.com/i/[^"\' ?#]+)', r0.text)
                    if m0:
                        scrape_url = m0.group(1)
                        print(f"   🔄 Scraping from: {scrape_url[:70]}")
                except Exception:
                    pass

        resp = requests.get(scrape_url, headers=headers, timeout=25, allow_redirects=True)
        html = resp.text

        # ── 1. العنوان ─────────────────────────────────────────
        # og:title أو <title>
        m = re.search(r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            result['title'] = m.group(1).strip()
        else:
            m2 = re.search(r'<title>([^<]+)</title>', html)
            if m2:
                result['title'] = m2.group(1).split('|')[0].strip()

        # ── 2. الوصف ───────────────────────────────────────────
        m = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            result['description'] = m.group(1).strip()
        if not result['description']:
            m2 = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html)
            if m2:
                result['description'] = m2.group(1).strip()

        # ── 3. التاجات من __NEXT_DATA__ ────────────────────────
        nd = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.DOTALL)
        if nd:
            try:
                data = json.loads(nd.group(1))
                raw_json = json.dumps(data)

                # Tags — جرب كل الأنماط الممكنة
                tag_matches = []
                for pat in [
                    r'"tag"\s*:\s*"([^"]+)"',
                    r'"tagName"\s*:\s*"([^"]+)"',
                    r'"keyword"\s*:\s*"([^"]+)"',
                    r'"keywords"\s*:\s*"([^"]+)"',
                    r'"label"\s*:\s*"([a-z][a-z\s\-]{2,30})"',
                ]:
                    found = re.findall(pat, raw_json, re.IGNORECASE)
                    tag_matches.extend(found)
                # فلترة: بعيد عن الكلمات الغلط
                skip = {'true','false','null','undefined','redbubble','cust','tshirts','shop','store'}
                tag_matches = [t for t in tag_matches if len(t) > 2 and t.lower() not in skip]
                result['tags'] = list(dict.fromkeys(tag_matches))[:20]

                # Products from JSON
                prod_matches = re.findall(r'"productName"\s*:\s*"([^"]+)"', raw_json)
                if not prod_matches:
                    prod_matches = re.findall(r'"name"\s*:\s*"([A-Z][a-zA-Z\s\-]+(?:T-Shirt|Hoodie|Sticker|Mug|Poster|Case|Bag|Print|Pillow|Notebook|Leggings|Dress|Scarf|Skin|Sleeve|Card|Hat|Mask|Magnet|Bottle)[^"]*)"', raw_json)
                result['products'] = list(dict.fromkeys(prod_matches))[:30]
            except Exception:
                pass

        # ── 4. المنتجات من HTML مباشرة (backup) ───────────────
        if not result['products']:
            prod_html = re.findall(
                r'(?:T-Shirt|Hoodie|Sticker|Mug|Poster|Phone Case|Tote Bag|'
                r'Art Print|Canvas|Leggings|Notebook|Pillow|Sweatshirt|'
                r'Water Bottle|Travel Mug|Laptop Skin|Greeting Card|Dress|Scarf)',
                html
            )
            result['products'] = list(dict.fromkeys(prod_html))[:30]

        # ── 5. التاجات من HTML (backup) ────────────────────────
        if not result['tags']:
            tag_html = re.findall(r'["\']tag["\']:\s*["\']([^"\']+)["\']', html)
            result['tags'] = list(dict.fromkeys(tag_html))[:20]

        # ── تنظيف العنوان — لو جاب عنوان عام مش عنوان التصميم ──
        bad_titles = ['redbubble', 'logo', 'home', 'shop', 'store', '404', 'error']
        if any(b in result['title'].lower() for b in bad_titles):
            print(f"   ⚠️ Bad title detected ('{result['title']}') — will use design_hint")
            result['title'] = ''

        print(f"   📌 Title   : {result['title'][:60] or '(none — will use design_hint)'}")
        print(f"   📝 Desc    : {result['description'][:80]}")
        print(f"   🏷️  Tags   : {result['tags'][:6]}")
        print(f"   📦 Products: {result['products'][:6]}")

    except Exception as e:
        print(f"   ⚠️ Scrape failed: {e}")

    return result


# ══════════════════════════════════════════════════════════════
# 🖼️ IMAGES
# ══════════════════════════════════════════════════════════════

def fetch_product_images(product_url: str, max_images: int = 20) -> list:
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/124.0.0.0 Safari/537.36'
        ),
        'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.redbubble.com/',
    }
    image_urls = []
    seen = set()
    try:
        resp = requests.get(product_url, headers=headers, timeout=20)
        html = resp.text
        for pat in [
            r'content="(https://ih\d+\.redbubble\.net/[^"]+)"',
            r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"',
            r'src="(https://ih\d+\.redbubble\.net/[^"]+)"',
        ]:
            for m in re.finditer(pat, html):
                url = m.group(1).split('?')[0]
                if url not in seen:
                    seen.add(url)
                    image_urls.append(url)
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


def prepare_images(token: str, product_url: str, design_hint: str) -> list:
    """يجيب الصور ويحاول يرفعها على Blogger — fallback للروابط الأصلية"""
    print(f"   📥 Fetching product images...")
    raw_urls = fetch_product_images(product_url, max_images=20)
    if not raw_urls:
        return []

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.redbubble.com/',
    }
    uploaded = []
    fallback = []
    album_id = os.getenv('BLOGGER_ALBUM_ID', 'default')
    api_url = f'https://picasaweb.google.com/data/feed/api/user/default/albumid/{album_id}'

    print(f"   ⬆️  Uploading {min(len(raw_urls), MIN_IMAGES)} images to Blogger...")

    for i, img_url in enumerate(raw_urls[:MIN_IMAGES + 4]):
        try:
            r = requests.get(img_url, headers=headers, timeout=15)
            if r.status_code != 200:
                fallback.append(img_url)
                continue
            img_bytes = r.content
            mime = r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
            filename = f"{design_hint[:30].replace(' ', '_')}_{i+1}.jpg"

            upload_resp = requests.post(
                api_url,
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type':  mime,
                    'Slug':          filename[:50],
                    'GData-Version': '2',
                },
                data=img_bytes,
                timeout=30
            )

            hosted = None
            if upload_resp.status_code in (200, 201):
                for pattern in ['lh3.', 'lh4.', 'lh5.', 'lh6.']:
                    idx = upload_resp.text.find(pattern)
                    if idx >= 0:
                        sq = upload_resp.text.rfind('"', 0, idx)
                        eq = upload_resp.text.find('"', idx)
                        if sq >= 0 and eq > idx:
                            hosted = upload_resp.text[sq+1:eq]
                            break

            if hosted:
                uploaded.append(hosted)
                print(f"      ✅ Image {i+1} uploaded to Blogger")
            else:
                fallback.append(img_url)
                print(f"      ⚠️ Image {i+1} — using original URL")

        except Exception as e:
            fallback.append(img_url)
            print(f"      ⚠️ Image {i+1} error: {e}")

        if len(uploaded) + len(fallback) >= MIN_IMAGES:
            break

    all_imgs = uploaded + fallback
    print(f"   🖼️  Ready: {len(uploaded)} on Blogger + {len(fallback)} CDN = {len(all_imgs)} total")
    return all_imgs


# ══════════════════════════════════════════════════════════════
# 🤖 AI — Generate SEO Article (Blogger HTML Style)
# ══════════════════════════════════════════════════════════════

def generate_article(design_hint: str, product_url: str,
                     user_tags: list, user_description: str) -> dict:
    """
    يولّد مقالة SEO — يسحب بيانات التصميم الحقيقية من Redbubble أولاً
    """
    # ── سحب بيانات التصميم من Redbubble ──────────────────────
    print("   🔍 Scraping design data from Redbubble...")
    scraped = scrape_design_data(product_url)

    real_title       = scraped['title'] or design_hint
    real_description = scraped['description'] or user_description
    scraped_tags     = scraped['tags'] or []
    available_prods  = scraped['products'] or ALL_PRODUCTS[:20]

    all_tags     = list(dict.fromkeys(scraped_tags + (user_tags or [])))
    tags_str     = ', '.join(all_tags[:15]) if all_tags else design_hint
    products_str = ', '.join(available_prods[:25]) if available_prods else ', '.join(ALL_PRODUCTS[:20])
    desc_section = f'''\nDESIGN DESCRIPTION:\n"""\n{real_description}\n"""'''  if real_description else ''

    prompt = f"""You are a professional SEO content writer for a Redbubble print-on-demand store called "Cust Tshirts".

YOUR JOB: Write a detailed, engaging HOOK → BODY → CTA article about this specific design that drives real traffic and purchases.

DESIGN DATA (scraped directly from the product page):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Real Title     : "{real_title}"
- Design Keyword : "{design_hint}"
- Product URL    : {product_url}
- Store URL      : {STORE_URL}
- Tags/Keywords  : {tags_str}
- Available Products: {products_str}
{desc_section}

ARTICLE STRUCTURE (Hook → Body → CTA):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔥 HOOK: Start with a bold, irresistible opening about THIS specific design.
   Make the reader feel "this was made for me." Reference the real title and theme.

💎 BODY: Deep dive — the design story, who it speaks to, ALL available products by name,
   gift ideas, quality, worldwide shipping. 700+ words total. Specific to this design.

⚡ CTA: Every section must end with a reason to click. The conclusion must create
   urgency and excitement: "Don't let this one slip away — grab yours now."

REQUIREMENTS:
- Mention specific product names from: {products_str}
- NO keyword stuffing, NO fake prices, NO discount codes
- Write like recommending to a friend who would LOVE this design
- Each section must feel specific to "{real_title}" — NOT generic

OUTPUT: Respond ONLY with valid JSON — no markdown, no extra text:
{{
  "seo_title": "SEO title 55-65 chars with \"{design_hint}\" keyword",
  "meta_description": "Meta 150-160 chars — mention design + strong CTA",
  "h1": "H1 — exciting, keyword-rich, different from title",
  "labels": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "intro": "3-4 sentences. 🔥 HOOK: Bold opening line referencing exactly what \"{real_title}\" is. Why it stops you in your tracks. Main keyword in first sentence. Make them want to read more.",
  "about_h2": "H2 — About the {real_title} Design",
  "about_body": "5-6 sentences. What makes THIS design special — its theme, humor/emotion/aesthetic, the story behind it, who it speaks to. Use details from tags and description. Vivid and specific.",
  "who_for_h2": "H2 — Who Will Love This Design?",
  "who_for_intro": "1-2 sentences — connect the design theme to its perfect audience.",
  "who_for_list": ["Specific fan type 1 based on the design theme", "Fan type 2", "Fan type 3", "Fan type 4", "Fan type 5"],
  "products_h2": "H2 — Available on Multiple Products",
  "products_body": "3-4 sentences. Mention actual product names: {products_str[:100]}. Explain why this design looks great on each. Premium quality Redbubble printing on everything.",
  "products_table_caption": "Short exciting caption for the product table",
  "gift_h2": "H2 — The Perfect Gift for [Audience of This Design]",
  "gift_body": "4-5 sentences. Why THIS design makes an unforgettable gift. Who to gift it to. Occasions matching the design theme. Unique, thoughtful, and ships worldwide.",
  "gift_list": ["Gift occasion tied to design theme 1", "Occasion 2", "Occasion 3", "Occasion 4"],
  "quality_h2": "H2 — Premium Quality, Worldwide Shipping",
  "quality_body": "3-4 sentences about Redbubble print quality, satisfaction guarantee, fast worldwide shipping, supporting independent artists.",
  "quality_highlights": ["Premium print on every product", "Ships worldwide in days", "100% satisfaction guarantee", "Supports independent artists"],
  "how_order_h2": "H2 — How To Order",
  "how_order_steps": ["Click the product link above", "Choose your product, color and size", "Add to cart and checkout securely", "Receive worldwide shipping to your door"],
  "faq_q1": "Question specifically about \"{real_title}\"",
  "faq_a1": "2-3 sentence answer referencing the design theme",
  "faq_q2": "Question about shipping or product range",
  "faq_a2": "2-3 sentence answer",
  "faq_q3": "Question about gifting this design",
  "faq_a3": "2-3 sentence answer connecting design to gift giving",
  "conclusion": "3-4 sentences. ⚡ CTA: Summarize what makes \"{real_title}\" worth having. Create real urgency — \"This design won\'t stay under the radar for long.\" Direct call to action to visit the link and buy now. End with excitement and energy."
}}"""

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
                'max_tokens':  3500,
                'messages': [
                    {
                        'role':    'system',
                        'content': 'You are an expert SEO content writer for a Redbubble print-on-demand store. Write specific, vivid, engaging articles using the REAL design data provided. Every article must feel unique to that specific design. Structure: Hook → Body → CTA. Respond ONLY with valid JSON. No markdown. No explanation.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
            },
            timeout=55
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        return json.loads(raw)
    except Exception as e:
        print(f"   ⚠️ AI failed: {e} — using fallback")
        return _fallback(design_hint, product_url, user_tags)

def _fallback(design_hint: str, url: str, tags: list) -> dict:
    d = design_hint
    return {
        'seo_title': f'{d} — Unique Redbubble Design',
        'meta_description': f'Discover the {d} design on Redbubble. Available on t-shirts, stickers, mugs and more. Ships worldwide!',
        'h1': f'{d} — Shop This Unique Design Now',
        'labels': tags[:8] if tags else ['redbubble', 'design', 'gift', 'print on demand'],
        'intro': f'Looking for a unique {d} design? This amazing design is available on dozens of products — from t-shirts and hoodies to stickers, mugs, phone cases and more. Whether you\'re treating yourself or searching for the perfect gift, you\'ve found exactly what you need.',
        'about_h2': f'About The {d} Design',
        'about_body': f'The {d} design is a one-of-a-kind piece of art that instantly stands out. It captures a unique aesthetic that resonates deeply with people who love to express their personality through creative design. Every detail has been thoughtfully crafted, from the colors to the concept, making it both eye-catching and memorable.',
        'who_for_h2': 'Who Is This Perfect For?',
        'who_for_intro': 'This design speaks to a very specific group of people — those who appreciate unique, creative expression.',
        'who_for_list': ['Anyone who loves unique graphic designs', 'People who want to express their personality', 'Gift buyers looking for something truly original', 'Cat lovers and animal enthusiasts', 'Anyone who appreciates humor and creativity'],
        'products_h2': 'Available On Many Products',
        'products_body': f'The {d} design is printed on a huge range of high-quality products. Choose from classic and fitted t-shirts, pullover hoodies, stickers, mugs, phone cases, tote bags, art prints, posters, throw pillows, leggings, and much more. All products are made on demand with premium printing.',
        'products_table_caption': 'Available products for this design',
        'gift_h2': 'Makes a Perfect Gift',
        'gift_body': f'Struggling to find a gift that\'s truly unique? The {d} design makes an unforgettable present for any occasion. Anyone who receives this will immediately know how thoughtful and original the choice was.',
        'gift_list': ['Birthday gifts', 'Christmas presents', 'Graduation gifts', 'Anniversary surprises'],
        'quality_h2': 'Quality You Can Trust',
        'quality_body': 'Redbubble is one of the world\'s leading print-on-demand marketplaces, trusted by millions of customers globally. Every purchase comes backed by a satisfaction guarantee.',
        'quality_highlights': ['Premium print quality on every product', 'Ships worldwide with tracking', 'Satisfaction guarantee from Redbubble', 'Supporting independent artists'],
        'how_order_h2': 'How To Order',
        'how_order_steps': ['Click the Shop button below to visit Redbubble', 'Choose your preferred product type and size', 'Add to cart and checkout securely', 'Your order ships fresh and direct to your door'],
        'faq_q1': f'What products is the {d} design available on?',
        'faq_a1': f'The {d} design is available on t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints, pillows, leggings, and many more products. Visit the Redbubble page to see all available options.',
        'faq_q2': 'Does Redbubble ship internationally?',
        'faq_a2': 'Yes, Redbubble ships worldwide. Shipping times and costs vary by location and shipping method. Most orders arrive within 1-2 weeks.',
        'faq_q3': f'Is the {d} design a good gift?',
        'faq_a3': f'Absolutely! The {d} design makes an excellent gift for anyone who appreciates unique, creative products. It\'s available on practical everyday items they\'ll use and enjoy.',
        'conclusion': f'The {d} design is more than just a product — it\'s a statement of personality and creativity. Whether you\'re buying for yourself or as a gift, this design delivers on every level. Don\'t wait — click the button below and grab yours today!',
    }


# ══════════════════════════════════════════════════════════════
# 🏗️ BUILD HTML (Blogger template style — red #cc0000)
# ══════════════════════════════════════════════════════════════

def build_html(data: dict, design_hint: str, product_url: str,
               images: list, user_tags: list, user_description: str) -> str:
    """
    يبني HTML المقالة بنفس أسلوب القالب:
    - ألوان #cc0000 و #073763
    - highlighted spans
    - note boxes
    - comparison table
    - ordered/unordered lists
    - CTA buttons
    """

    def img(url: str, alt: str) -> str:
        return (
            f'<div style="text-align:center;margin:18px 0;">'
            f'<img src="{url}" alt="{alt}" title="{alt}" '
            f'referrerpolicy="no-referrer" crossorigin="anonymous" '
            f'style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,0.12);" />'
            f'</div>'
        )

    def get(idx: int) -> str:
        return img(images[idx], f"{design_hint} - Product {idx+1}") if idx < len(images) else ''

    def cta_button(text: str = '🛒 Shop This Design on Redbubble') -> str:
        return (
            f'<div style="text-align:center;margin:24px 0;">'
            f'<a href="{product_url}" target="_blank" rel="noopener" '
            f'style="display:inline-block;background:#cc0000;color:#fff;'
            f'padding:13px 32px;border-radius:6px;font-weight:bold;font-size:1em;'
            f'text-decoration:none;box-shadow:0 3px 10px rgba(204,0,0,0.35);">'
            f'{text}</a></div>'
        )

    def note_box(text: str, emoji: str = '📌') -> str:
        return (
            f'<div style="background-color:#fff2cc;border-left:4px solid #cc0000;'
            f'padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">'
            f'<strong style="color:#073763;">{emoji} Note:</strong> {text}</div>'
        )

    def highlight(text: str, bg: str = '#f3f3f3', color: str = '#741b47') -> str:
        return f'<span style="background-color:{bg};color:{color};padding:2px 6px;">{text}</span>'

    def quote_box(text: str) -> str:
        return (
            f'<div style="background-color:#cfe2f3;border-left:4px solid #1565c0;'
            f'padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;'
            f'font-style:italic;color:#073763;">'
            f'"{text}"</div>'
        )

    # Products table (first 6 columns × 2 rows from ALL_PRODUCTS)
    table_rows = ''
    row1 = ALL_PRODUCTS[:6]
    row2 = ALL_PRODUCTS[6:12]
    row3 = ALL_PRODUCTS[12:18]
    for row in [row1, row2, row3]:
        cells = ''.join(f'<td style="padding:8px;border:1px solid #ddd;">{p}</td>' for p in row)
        table_rows += f'<tr>{cells}</tr>'

    products_table = f'''<table border="1" cellpadding="0" cellspacing="0"
  style="width:100%;border-collapse:collapse;margin:16px 0;font-size:.9em;">
  <thead>
    <tr style="background:#cc0000;color:#fff;">
      <td colspan="6" style="padding:10px;text-align:center;font-weight:bold;">
        🛍️ {data.get("products_table_caption", "Products Available for This Design")}
      </td>
    </tr>
  </thead>
  <tbody>{table_rows}</tbody>
</table>'''

    # Who is it for — unordered list with highlights
    who_list_items = ''
    colors = ['#d9ead3', '#cfe2f3', '#fff2cc', '#f4cccc', '#ead1dc']
    for i, item in enumerate(data.get('who_for_list', [])):
        bg = colors[i % len(colors)]
        who_list_items += f'<li style="margin-bottom:8px;">{highlight(item, bg, "#073763")}</li>'

    # Gift occasions — ordered list
    gift_list_items = ''
    for item in data.get('gift_list', []):
        gift_list_items += (
            f'<li style="margin-bottom:6px;">'
            f'{highlight("📅", "#f3f3f3", "#741b47")} {item}'
            f'</li>'
        )

    # Quality highlights
    quality_items = ''
    for item in data.get('quality_highlights', []):
        quality_items += f'<li style="margin-bottom:6px;">✅ {item}</li>'

    # How to order — numbered
    order_steps = ''
    for i, step in enumerate(data.get('how_order_steps', []), 1):
        order_steps += (
            f'<li style="margin-bottom:10px;">'
            f'{highlight(f"Step {i}", "#f3f3f3", "#741b47")} 📌 {step}'
            f'</li>'
        )

    # Description section from designs.txt
    desc_section = ''
    if user_description:
        desc_section = (
            f'<div style="background:#f8f9fa;border-left:4px solid #cc0000;'
            f'padding:16px;margin:20px 0;border-radius:0 6px 6px 0;">'
            f'<strong style="color:#073763;display:block;margin-bottom:8px;">📋 About This Design</strong>'
            f'<p style="color:#555;margin:0;line-height:1.7;">{user_description}</p>'
            f'</div>'
        )

    # Tags section from designs.txt
    tags_section = ''
    if user_tags:
        tag_spans = ' '.join(
            f'<span style="display:inline-block;background:#f3f3f3;'
            f'border:1px solid #ddd;color:#333;padding:3px 10px;'
            f'border-radius:4px;font-size:.82em;margin:3px;">{t}</span>'
            for t in user_tags
        )
        tags_section = (
            f'<div style="margin:16px 0;">'
            f'<strong style="color:#073763;font-size:.85em;">🏷️ Tags:</strong><br/>'
            f'<div style="margin-top:6px;">{tag_spans}</div>'
            f'</div>'
        )

    # Image grid (images 7-12)
    grid_cells = ''
    for i in range(6, min(12, len(images))):
        grid_cells += (
            f'<div style="flex:1;min-width:100px;max-width:180px;padding:4px;">'
            f'<img src="{images[i]}" alt="{design_hint} product {i+1}" '
            f'referrerpolicy="no-referrer" '
            f'style="width:100%;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,.1);" />'
            f'</div>'
        )
    grid_html = ''
    if grid_cells:
        grid_html = (
            f'<div style="margin:20px 0;">'
            f'<p style="text-align:center;color:#666;font-size:.85em;margin-bottom:10px;">'
            f'🛍️ Available on many products — tap to explore all options</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">'
            f'{grid_cells}</div></div>'
        )

    # FAQ
    faq = (
        f'<div style="background:#f8f9fa;border-radius:8px;padding:20px;margin:28px 0;">'
        f'<h2 style="color:#cc0000;font-size:1.3em;margin-top:0;">❓ Frequently Asked Questions</h2>'
        f'<h3 style="color:#073763;font-size:1em;margin-bottom:5px;">Q: {data.get("faq_q1","")}</h3>'
        f'<p style="color:#555;margin:0 0 16px;">{data.get("faq_a1","")}</p>'
        f'<h3 style="color:#073763;font-size:1em;margin-bottom:5px;">Q: {data.get("faq_q2","")}</h3>'
        f'<p style="color:#555;margin:0 0 16px;">{data.get("faq_a2","")}</p>'
        f'<h3 style="color:#073763;font-size:1em;margin-bottom:5px;">Q: {data.get("faq_q3","")}</h3>'
        f'<p style="color:#555;margin:0;">{data.get("faq_a3","")}</p>'
        f'</div>'
    )

    return f'''<div style="font-family:Georgia,'Times New Roman',serif;max-width:820px;margin:0 auto;line-height:1.82;color:#2d2d2d;font-size:1.02em;">

<!-- ── META ── -->
<p style="color:#999;font-size:.82em;margin-bottom:20px;">
  By <strong>Cust Tshirts</strong> &bull;
  {datetime.now().strftime("%B %d, %Y")} &bull;
  <a href="{product_url}" style="color:#cc0000;" target="_blank" rel="noopener">View on Redbubble &rarr;</a>
</p>

<!-- ── HERO IMAGE ── -->
{get(0)}

<!-- ── INTRO ── -->
<div style="border-left:4px solid #cc0000;padding-left:16px;margin:20px 0;font-size:1.05em;color:#444;">
{data.get("intro","")}
</div>

{get(1)}

{desc_section}

<!-- ── ABOUT ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("about_h2","About This Design")}</h2>
<div>{data.get("about_body","")}</div>

{get(2)}

{note_box("This design is available on over 30 different product types — from everyday wear to home decor gifts.", "🎨")}

<!-- ── WHO IS IT FOR ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("who_for_h2","Who Is This Perfect For?")}</h2>
<div>{data.get("who_for_intro","")}</div>
<ul style="margin-top:12px;">
{who_list_items}
</ul>

{get(3)}

<!-- ── PRODUCTS ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("products_h2","Available On Many Products")}</h2>
<div>{data.get("products_body","")}</div>

{products_table}

{get(4)}
{get(5)}
{grid_html}

{cta_button()}

<!-- ── GIFT ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("gift_h2","Makes a Perfect Gift")}</h2>
<div>{data.get("gift_body","")}</div>
<ol style="margin-top:12px;">
{gift_list_items}
</ol>

{quote_box(f"The perfect gift isn't expensive — it's thoughtful. The {design_hint} design is exactly that.")}

{get(6) if len(images) > 6 else ''}

<!-- ── QUALITY ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("quality_h2","Quality You Can Trust")}</h2>
<div>{data.get("quality_body","")}</div>
<ul style="margin-top:10px;">
{quality_items}
</ul>

<!-- ── HOW TO ORDER ── -->
<h2 style="color:#cc0000;font-size:x-large;">{data.get("how_order_h2","How To Order")}</h2>
<ol style="margin-top:12px;">
{order_steps}
</ol>

{tags_section}

<!-- ── FAQ ── -->
{faq}

<!-- ── CONCLUSION ── -->
<div style="background:#fff2cc;padding:16px;border-radius:6px;margin-top:24px;">
<span style="color:#073763;font-weight:bold;">Final Thoughts:</span>
{data.get("conclusion","")}
</div>

{cta_button("🛒 Shop Now on Redbubble")}

<hr style="border:none;border-top:1px solid #eee;margin:28px 0;" />
<p style="font-size:.78em;color:#bbb;text-align:center;">
  &copy; {datetime.now().year} Cust Tshirts &bull;
  <a href="{STORE_URL}" style="color:#cc0000;" target="_blank" rel="noopener">Browse All Designs</a>
</p>

</div>'''


# ══════════════════════════════════════════════════════════════
# 📤 MAIN PUBLISH FUNCTION
# ══════════════════════════════════════════════════════════════

def post_to_blogger(design_hint: str, product_url: str, images: list,
                    user_tags: list = None,
                    user_description: str = '',
                    collection: str = '') -> dict:
    """
    ينشر مقالة SEO احترافية على Blogger
    - user_tags: التاجات من designs.txt
    - user_description: الوصف من designs.txt (بعد | الثاني)
    """
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping")
        return {'success': False, 'error': 'BLOGGER_BLOG_ID missing'}

    print("\n📝 Publishing SEO article to Blogger...")

    if user_tags is None:
        user_tags = []

    # Auto-generate tags if none provided
    if not user_tags:
        print("   🏷️  No tags in designs.txt — auto-generating...")
        user_tags = _auto_tags(design_hint, product_url)

    # 1. Auth
    token = get_access_token()
    if not token:
        return {'success': False, 'error': 'Auth failed'}

    # 2. Images — استخدم الصور اللي اتبعتت من main.py مباشرة
    if images and len(images) >= 3:
        hosted = list(images)
        print(f"   🖼️  Using {len(hosted)} images passed from main")
    else:
        hosted = prepare_images(token, product_url, design_hint)
        if len(hosted) < MIN_IMAGES:
            extra = fetch_product_images(product_url, max_images=20)
            for u in extra:
                if u not in hosted:
                    hosted.append(u)
                if len(hosted) >= MIN_IMAGES:
                    break
    print(f"   🖼️  Total images: {len(hosted)}")

    # 3. Generate article
    print("   🤖 Generating SEO article...")
    article = generate_article(design_hint, product_url, user_tags, user_description)

    # 4. Build HTML
    html = build_html(article, design_hint, product_url, hosted, user_tags, user_description)

    # 5. Merge labels
    ai_labels  = article.get('labels', [])
    all_labels = list(dict.fromkeys(user_tags + ai_labels))[:20]

    # 6. Publish
    payload = {
        'title':   article.get('seo_title', f'{design_hint} — Shop on Redbubble'),
        'content': html,
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
            post_url = data.get('url', '')
            print(f"   ✅ Published!")
            print(f"   📰 Title  : {payload['title']}")
            print(f"   🔗 URL    : {post_url}")
            print(f"   🏷️  Labels : {', '.join(all_labels[:6])}...")
            print(f"   🖼️  Images : {len(hosted)}")
            return {'success': True, 'post_id': data['id'], 'url': post_url, 'title': payload['title']}
        else:
            err = data.get('error', {}).get('message', str(data))
            print(f"   ❌ Blogger error: {err}")
            return {'success': False, 'error': err}

    except Exception as e:
        print(f"   ❌ Publish failed: {e}")
        return {'success': False, 'error': str(e)}


def _auto_tags(design_hint: str, product_url: str) -> list:
    """يولّد تاجات تلقائية من اسم التصميم لو مفيش في designs.txt"""
    if not GROQ_API_KEY:
        words = re.sub(r'[^a-zA-Z0-9 ]', ' ', design_hint).lower().split()
        stop = {'by', 'for', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'of', 'to', 'with'}
        return [w for w in words if w not in stop and len(w) > 2][:8]
    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': GROQ_MODEL, 'temperature': 0.5, 'max_tokens': 150,
                'messages': [
                    {'role': 'system', 'content': 'Respond ONLY with a valid JSON array of strings.'},
                    {'role': 'user', 'content': f'Generate 8 SEO tags for this Redbubble design: "{design_hint}". Short phrases only. JSON array.'}
                ],
            },
            timeout=20
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        tags = json.loads(raw)
        if isinstance(tags, list):
            print(f"   🏷️  Auto-generated {len(tags)} tags")
            return [str(t).strip() for t in tags][:10]
    except Exception:
        pass
    words = re.sub(r'[^a-zA-Z0-9 ]', ' ', design_hint).lower().split()
    stop = {'by', 'for', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'of', 'to', 'with'}
    return [w for w in words if w not in stop and len(w) > 2][:8]
