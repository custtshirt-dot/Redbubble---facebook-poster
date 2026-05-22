"""
📝 Blogger Poster — ينشر مقالة SEO احترافية على Blogger
✅ أسلوب بشري طبيعي — بعيد عن الأسلوب الآلي
✅ التاجات والوصف من designs.txt
✅ صور Redbubble
✅ 600+ كلمة مع SEO كامل
"""
import os
import re
import json
import random
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

# عبارات بشرية متنوعة للـ intro — تتغير كل مرة
HUMAN_OPENERS = [
    "Okay, I'll be honest —",
    "So I was scrolling through Redbubble the other day and",
    "Not gonna lie,",
    "Here's the thing —",
    "I wasn't expecting much, but then",
    "Some designs just stop you mid-scroll, and",
    "Let me tell you about",
    "Real talk:",
    "You know that feeling when you find something and immediately think 'I need this'?",
    "I've seen a lot of Redbubble designs, but",
]

HUMAN_TRANSITIONS = [
    "Anyway,", "But here's the thing —", "What I love most is",
    "And honestly,", "The cool part?", "Here's what gets me —",
    "What really stands out is", "I keep coming back to the fact that",
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
    result = {'title': '', 'description': '', 'tags': [], 'products': []}
    try:
        scrape_url = product_url
        if '/shop/ap/' in product_url:
            import re as _re2
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

        # عنوان — نجرب أكتر من pattern
        title_patterns = [
            r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:title["\']',
            r'"productTitle"\s*:\s*"([^"]+)"',
            r'"title"\s*:\s*"([^"]{10,120})"',
        ]
        for pat in title_patterns:
            m = re.search(pat, html)
            if m and m.group(1).lower() not in ('og:title', 'og:description', ''):
                result['title'] = m.group(1).strip()
                break
        if not result['title']:
            m2 = re.search(r'<title>([^<]+)</title>', html)
            if m2:
                result['title'] = m2.group(1).split('|')[0].strip()

        # وصف
        m = re.search(r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\']([^"\']+)["\']', html)
        if m:
            result['description'] = m.group(1).strip()
        if not result['description']:
            m2 = re.search(r'<meta[^>]+name=["\']description["\'][^>]+content=["\']([^"\']+)["\']', html)
            if m2:
                result['description'] = m2.group(1).strip()

        # تاجات ومنتجات من NEXT_DATA
        nd = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.DOTALL)
        if nd:
            try:
                raw_json = json.dumps(json.loads(nd.group(1)))
                tag_names = re.findall(r'"tags"\s*:\s*\[([^\]]+)\]', raw_json)
                tag_matches = []
                for block in tag_names:
                    tag_matches.extend(re.findall(r'"name"\s*:\s*"([^"]+)"', block))
                if not tag_matches:
                    tag_matches = re.findall(r'"name"\s*:\s*"([a-z][a-z\s\-]{2,40})"', raw_json, re.IGNORECASE)
                skip_words = {
                    'primary','supplementary','supplementary2','supplementary3',
                    'supplementary4','supplementary5','true','false','null',
                    'undefined','redbubble','cust','tshirts','shop','store',
                    'default','standard','main','other','none','all','new',
                    'bodycolor','defaulttext','hexcolor','displayorder',
                    'configuration','printlocation','colorname','colorvalue',
                    'imagetype','imagestyle','producttype','productline',
                }
                # فلتر camelCase (كلمات تقنية) وكلمات قصيرة جداً
                def is_human_tag(t):
                    t = t.strip()
                    if len(t) < 3 or len(t) > 50:
                        return False
                    if t.lower() in skip_words:
                        return False
                    # رفض camelCase مثل bodyColor, hexColor
                    if re.search(r'[a-z][A-Z]', t):
                        return False
                    # لازم يحتوي على حروف فقط ومسافات وشرطات
                    if not re.match(r'^[a-zA-Z0-9\s\-]+$', t):
                        return False
                    return True
                tag_matches = [t.strip() for t in tag_matches if is_human_tag(t)]
                result['tags'] = list(dict.fromkeys(tag_matches))[:20]

                prod_matches = re.findall(r'"productName"\s*:\s*"([^"]+)"', raw_json)
                if not prod_matches:
                    prod_matches = re.findall(
                        r'"name"\s*:\s*"([A-Z][a-zA-Z\s\-]+'
                        r'(?:T-Shirt|Hoodie|Sticker|Mug|Poster|Case|Bag|Print|'
                        r'Pillow|Notebook|Leggings|Dress|Scarf|Skin|Sleeve|'
                        r'Card|Hat|Mask|Magnet|Bottle)[^"]*)"', raw_json)
                result['products'] = list(dict.fromkeys(prod_matches))[:30]
            except Exception:
                pass

        if not result['products']:
            prod_html = re.findall(
                r'(?:Classic T-Shirt|Fitted T-Shirt|Pullover Hoodie|Zip Hoodie|'
                r'Sticker|Transparent Sticker|Mug|Travel Mug|Water Bottle|'
                r'Phone Case|Tote Bag|Drawstring Bag|Throw Pillow|Art Print|'
                r'Poster|Canvas Print|Photographic Print|Leggings|Dress|Scarf|'
                r'Laptop Skin|Spiral Notebook|Greeting Card|Pullover Sweatshirt|'
                r'Bucket Hat|Magnet|Face Mask)',
                html
            )
            result['products'] = list(dict.fromkeys(prod_html))[:30]

        if not result['tags']:
            m_kw = re.search(
                r'<meta[^>]+name=["\']keywords["\'][^>]+content=["\']([^"\']+)["\']', html)
            if m_kw:
                result['tags'] = [t.strip() for t in m_kw.group(1).split(',') if t.strip()][:20]

        import html as _html
        result['title'] = _html.unescape(result['title']).strip('"').strip()
        result['description'] = _html.unescape(result['description'])

        bad_titles = ['redbubble', 'logo', 'home', 'shop', 'store', '404', 'error']
        if any(b in result['title'].lower() for b in bad_titles):
            result['title'] = ''

        print(f"   📌 Title   : {result['title'][:60] or '(none)'}")
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
# 🤖 AI — Generate Human-Sounding SEO Article
# ══════════════════════════════════════════════════════════════

def generate_article(design_hint: str, product_url: str,
                     user_tags: list, user_description: str) -> dict:
    print("   🔍 Scraping design data from Redbubble...")
    scraped = scrape_design_data(product_url)

    real_title       = scraped['title'] or design_hint
    real_description = scraped['description'] or user_description
    scraped_tags     = scraped['tags'] or []
    available_prods  = scraped['products'] or ALL_PRODUCTS[:20]

    all_tags     = list(dict.fromkeys(scraped_tags + (user_tags or [])))
    tags_str     = ', '.join(all_tags[:15]) if all_tags else design_hint
    products_str = ', '.join(available_prods[:25]) if available_prods else ', '.join(ALL_PRODUCTS[:20])
    desc_section = f'\nDESIGN DESCRIPTION:\n"""\n{real_description}\n"""' if real_description else ''

    # عشوائية في الأسلوب — كل مقالة تفرق
    opener      = random.choice(HUMAN_OPENERS)
    transition  = random.choice(HUMAN_TRANSITIONS)
    writing_angle = random.choice([
        "You're a fan of this specific niche who genuinely loves it and found this design.",
        "You're a gift-buyer who's always looking for something thoughtful and unique.",
        "You're someone who appreciates good design and hates boring generic merch.",
        "You're a collector who buys Redbubble stuff regularly and knows what's worth it.",
        "You're excited to share a hidden gem you just discovered.",
    ])

    prompt = f"""You're writing a blog post for a Redbubble print-on-demand store called "Cust Tshirts".

DESIGN DATA:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Real Title     : "{real_title}"
- Design Keyword : "{design_hint}"
- Product URL    : {product_url}
- Store URL      : {STORE_URL}
- Tags/Keywords  : {tags_str}
- Available Products: {products_str}
{desc_section}

YOUR PERSONA: {writing_angle}
OPENING LINE TO USE: Start the intro with "{opener}" — then continue naturally from there.
USE THIS TRANSITION SOMEWHERE: "{transition}"

TONE & STYLE RULES (CRITICAL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Write like a real person talking to a friend, NOT like a marketing robot
- Use contractions freely: "you'll", "it's", "don't", "that's", "I've"
- Vary sentence length — mix short punchy sentences with longer detailed ones
- Include occasional casual phrases: "honestly", "to be fair", "look", "here's the thing"
- It's okay to start sentences with "And", "But", "So" — that's natural writing
- Avoid AI giveaways: never use "delve", "showcase", "testament", "elevate", "realm", "tapestry", "vibrant", "dive into", "in conclusion", "in summary", "furthermore", "moreover", "it's worth noting"
- No bullet points that sound like a feature list — write in flowing paragraphs
- The conclusion must feel like a real recommendation, not a sales pitch closing
- Include ONE small imperfection or honest admission (e.g. "it might not be for everyone, but...")
- SEO keywords must feel woven in naturally, not forced

STRUCTURE:
━━━━━━━━━━
1. intro: Start with "{opener}" — hook them in 3-4 sentences. Personal, conversational, specific to "{real_title}".
2. about_body: 5-6 sentences explaining what the design IS and why it's cool. Use the description data. Feel real.
3. who_for_list: 5 specific types of people who'd genuinely love this — be specific to the design theme, not generic.
4. products_body: 3-4 sentences mentioning actual product names naturally — like you're telling someone what to buy.
5. gift_body: 4-5 sentences on gifting — specific occasions that match THIS design's theme.
6. quality_body: 3 sentences — honest, not corporate. Redbubble quality, ships worldwide, satisfaction guarantee.
7. conclusion: 3-4 sentences. Real recommendation. One line of gentle urgency. End with warmth not hype.

OUTPUT: Respond ONLY with valid JSON. No markdown, no backticks, no explanation:
{{
  "seo_title": "SEO title 55-65 chars — keyword '{design_hint}' included naturally",
  "meta_description": "150-160 chars — sounds like a human wrote it, includes main keyword + CTA",
  "h1": "Engaging H1 — different from title, feels like a real article headline",
  "labels": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "intro": "3-4 sentences starting with '{opener}' — casual, specific, makes you want to read more",
  "about_h2": "H2 for the about section — specific to '{real_title}'",
  "about_body": "5-6 sentences about what makes THIS design special. Vivid and specific, not generic.",
  "who_for_h2": "H2 — Who's gonna love this?",
  "who_for_intro": "1-2 casual sentences connecting design theme to its audience.",
  "who_for_list": ["Specific person type 1 based on design", "Type 2", "Type 3", "Type 4", "Type 5"],
  "products_h2": "H2 — What can you get it on?",
  "products_body": "3-4 sentences. Mention actual products naturally. No robotic listing.",
  "products_table_caption": "Short fun caption for the product table",
  "gift_h2": "H2 — gifting section title specific to design audience",
  "gift_body": "4-5 sentences. Real gift advice, specific occasions, why THIS design works as a gift.",
  "gift_list": ["Specific gift occasion for this design", "Occasion 2", "Occasion 3", "Occasion 4"],
  "quality_h2": "H2 — quality/shipping section",
  "quality_body": "3 sentences — honest and conversational about Redbubble quality + worldwide shipping.",
  "quality_highlights": ["Premium print quality", "Worldwide shipping", "Satisfaction guarantee", "Supports independent artists"],
  "how_order_h2": "H2 — how to order",
  "how_order_steps": ["Step 1 — natural language", "Step 2", "Step 3", "Step 4"],
  "faq_q1": "Natural question someone would actually ask about '{real_title}'",
  "faq_a1": "Conversational 2-3 sentence answer",
  "faq_q2": "Question about products or shipping",
  "faq_a2": "Conversational 2-3 sentence answer",
  "faq_q3": "Question about gifting this design",
  "faq_a3": "Conversational 2-3 sentence answer",
  "conclusion": "3-4 sentences. Genuine recommendation. One line of soft urgency. Warm and human ending."
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
                'temperature': 0.92,   # أعلى = أكثر إبداعاً وتنوعاً
                'max_tokens':  3500,
                'messages': [
                    {
                        'role':    'system',
                        'content': (
                            'You are a real human blogger who genuinely loves creative merch. '
                            'You write naturally, conversationally, and specifically. '
                            'You never sound like a marketing email or an AI assistant. '
                            'You use contractions, vary your sentence length, and write like '
                            'you\'re texting a friend who asked for a recommendation. '
                            'NEVER use words like: delve, showcase, testament, elevate, realm, '
                            'tapestry, vibrant, navigate, foster, leverage, paramount, '
                            'in conclusion, in summary, furthermore, moreover, it\'s worth noting. '
                            'Respond ONLY with valid JSON. No markdown. No backticks. No preamble.'
                        )
                    },
                    {'role': 'user', 'content': prompt}
                ],
            },
            timeout=55
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        # إزالة أي نص قبل أو بعد الـ JSON
        start = raw.find('{')
        end   = raw.rfind('}') + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        return json.loads(raw)
    except Exception as e:
        print(f"   ⚠️ AI failed: {e} — using fallback")
        return _fallback(design_hint, product_url, user_tags)


def _fallback(design_hint: str, url: str, tags: list) -> dict:
    d = design_hint
    opener = random.choice(HUMAN_OPENERS)
    return {
        'seo_title': f'{d} — Unique Redbubble Design Worth Checking Out',
        'meta_description': f'Spotted this {d} design on Redbubble and honestly had to share it. Available on t-shirts, mugs, stickers and way more. Ships worldwide!',
        'h1': f'{d} — This One\'s Worth a Look',
        'labels': tags[:8] if tags else ['redbubble', 'design', 'gift', 'print on demand'],
        'intro': f'{opener} this {d} design kind of stopped me mid-scroll. It\'s one of those things where you immediately think "someone put real thought into this." Whether you\'re grabbing it for yourself or looking for a gift that actually means something, you\'re in the right place.',
        'about_h2': f'So What\'s the {d} Design About?',
        'about_body': f'The {d} design is one of those pieces that just works. It\'s got a clear concept, good execution, and the kind of aesthetic that feels specific rather than generic. You can tell it wasn\'t just thrown together — there\'s a real idea behind it, and it shows in every detail from the colors to the composition.',
        'who_for_h2': 'Who\'s Gonna Love This?',
        'who_for_intro': 'This isn\'t a design for everyone — and that\'s kind of the point. It speaks to a specific crowd.',
        'who_for_list': [
            'Anyone tired of boring, mass-produced merch',
            'People who love expressing their personality through what they wear',
            'Gift buyers looking for something that actually feels thoughtful',
            'Fans of unique graphic design and independent artists',
            'Anyone who\'d appreciate humor or creativity in everyday items'
        ],
        'products_h2': 'What Can You Actually Get It On?',
        'products_body': f'The {d} design is available on a solid range of products — classic t-shirts, fitted tees, pullover hoodies, stickers, mugs, phone cases, tote bags, art prints, posters, throw pillows, and more. Basically if you want it on something, Redbubble probably has it. The printing quality holds up well across all of them.',
        'products_table_caption': 'Products this design is available on',
        'gift_h2': 'Looking for a Gift That Actually Lands?',
        'gift_body': f'The {d} design makes a surprisingly good gift — mainly because it doesn\'t feel like something you grabbed last minute. It\'s specific, it\'s creative, and it ships worldwide so distance isn\'t an issue. Redbubble wraps everything nicely too, which helps if you\'re sending it directly.',
        'gift_list': ['Birthdays', 'Christmas or holiday gifts', 'Graduation presents', '"Just because" surprises'],
        'quality_h2': 'Is the Quality Actually Good?',
        'quality_body': 'Redbubble\'s print quality is genuinely solid — colors stay vivid after washing, and the products themselves feel well-made. Everything ships worldwide with tracking, and there\'s a satisfaction guarantee if something goes wrong. To be fair, shipping times can vary by location, but it\'s never been a dealbreaker.',
        'quality_highlights': ['Premium print quality on every product', 'Ships worldwide with tracking', '100% satisfaction guarantee', 'Supports independent artists'],
        'how_order_h2': 'How to Grab One',
        'how_order_steps': [
            'Click the link below to head to the Redbubble product page',
            'Pick your product type, color, and size',
            'Add it to your cart and check out securely',
            'It ships straight to your door — worldwide'
        ],
        'faq_q1': f'What products is the {d} design available on?',
        'faq_a1': f'Quite a few, actually. You\'ll find the {d} design on t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints, pillows, leggings, and more. Check the Redbubble page for the full list.',
        'faq_q2': 'Does Redbubble ship internationally?',
        'faq_a2': 'Yes — Redbubble ships worldwide. Delivery times vary depending on where you are and which shipping option you choose, but most orders arrive within 1–2 weeks.',
        'faq_q3': f'Is this a good gift?',
        'faq_a3': f'Honestly, yes. The {d} design works well as a gift because it feels personal and specific — not like something you grabbed off a shelf. It\'s available on practical everyday items too, so it\'ll actually get used.',
        'conclusion': f'If the {d} design caught your eye, trust that instinct. It\'s the kind of thing that\'s harder to find than it should be — specific, well-made, and genuinely different from what you\'d find in a regular store. It might not be for everyone, but if it resonates with you, that\'s usually a sign. Go take a look.',
    }


# ══════════════════════════════════════════════════════════════
# 🏗️ BUILD HTML
# ══════════════════════════════════════════════════════════════

def build_html(data: dict, design_hint: str, product_url: str,
               images: list, user_tags: list, user_description: str) -> str:

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

    # Products table
    table_rows = ''
    for row in [ALL_PRODUCTS[:6], ALL_PRODUCTS[6:12], ALL_PRODUCTS[12:18]]:
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

    # Who is it for
    who_list_items = ''
    colors = ['#d9ead3', '#cfe2f3', '#fff2cc', '#f4cccc', '#ead1dc']
    for i, item in enumerate(data.get('who_for_list', [])):
        bg = colors[i % len(colors)]
        who_list_items += f'<li style="margin-bottom:8px;">{highlight(item, bg, "#073763")}</li>'

    # Gift list
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

    # How to order
    order_steps = ''
    for i, step in enumerate(data.get('how_order_steps', []), 1):
        order_steps += (
            f'<li style="margin-bottom:10px;">'
            f'{highlight(f"Step {i}", "#f3f3f3", "#741b47")} 📌 {step}'
            f'</li>'
        )

    # Description from designs.txt
    desc_section = ''
    if user_description:
        desc_section = (
            f'<div style="background:#f8f9fa;border-left:4px solid #cc0000;'
            f'padding:16px;margin:20px 0;border-radius:0 6px 6px 0;">'
            f'<strong style="color:#073763;display:block;margin-bottom:8px;">📋 About This Design</strong>'
            f'<p style="color:#555;margin:0;line-height:1.7;">{user_description}</p>'
            f'</div>'
        )

    # Tags
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

    # Image grid (7–12)
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
            f'🛍️ Available on many products — tap to explore</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">'
            f'{grid_cells}</div></div>'
        )

    # FAQ
    faq = (
        f'<div style="background:#f8f9fa;border-radius:8px;padding:20px;margin:28px 0;">'
        f'<h2 style="color:#cc0000;font-size:1.3em;margin-top:0;">❓ Quick Questions</h2>'
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

{note_box("This design is available on over 30 different product types — from everyday wear to home decor.", "🎨")}

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

{quote_box(f"The best gifts aren't the most expensive — they're the ones that feel like they were picked specifically for you. The {design_hint} design is exactly that kind of gift.")}

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
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping")
        return {'success': False, 'error': 'BLOGGER_BLOG_ID missing'}

    print("\n📝 Publishing SEO article to Blogger...")

    if user_tags is None:
        user_tags = []

    if not user_tags:
        print("   🏷️  No tags in designs.txt — auto-generating...")
        user_tags = _auto_tags(design_hint, product_url)

    # Auth
    token = get_access_token()
    if not token:
        return {'success': False, 'error': 'Auth failed'}

    # Images
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

    # Generate article
    print("   🤖 Generating human-style article...")
    article = generate_article(design_hint, product_url, user_tags, user_description)

    # Build HTML
    html = build_html(article, design_hint, product_url, hosted, user_tags, user_description)

    # Labels — فلتر قبل الإرسال لـ Blogger
    ai_labels = article.get('labels', [])
    raw_labels = list(dict.fromkeys(user_tags + ai_labels))

    def clean_label(t):
        t = str(t).strip()
        if not t or len(t) < 2 or len(t) > 200:
            return None
        if re.search(r'[a-z][A-Z]', t):
            return None
        tech = {'bodycolor','hexcolor','defaulttext','displayorder',
                'configuration','printlocation','colorname','imagetype'}
        if t.lower() in tech:
            return None
        return t

    all_labels = [l for l in (clean_label(x) for x in raw_labels) if l][:20]
    if not all_labels:
        all_labels = [design_hint[:50]]

    seo_title = article.get('seo_title', '').strip()
    if not seo_title or len(seo_title) < 5:
        seo_title = f'{design_hint} — Shop on Redbubble'

    # Publish
    payload = {
        'title':   seo_title,
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
    if not GROQ_API_KEY:
        words = re.sub(r'[^a-zA-Z0-9 ]', ' ', design_hint).lower().split()
        stop = {'by', 'for', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'of', 'to', 'with'}
        return [w for w in words if w not in stop and len(w) > 2][:8]
    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': GROQ_MODEL, 'temperature': 0.6, 'max_tokens': 150,
                'messages': [
                    {'role': 'system', 'content': 'Respond ONLY with a valid JSON array of strings. No markdown.'},
                    {'role': 'user', 'content': f'Generate 8 SEO tags for this Redbubble design: "{design_hint}". Short natural phrases only. JSON array.'}
                ],
            },
            timeout=20
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        start = raw.find('[')
        end   = raw.rfind(']') + 1
        if start >= 0 and end > start:
            raw = raw[start:end]
        tags = json.loads(raw)
        if isinstance(tags, list):
            print(f"   🏷️  Auto-generated {len(tags)} tags")
            return [str(t).strip() for t in tags][:10]
    except Exception:
        pass
    words = re.sub(r'[^a-zA-Z0-9 ]', ' ', design_hint).lower().split()
    stop = {'by', 'for', 'the', 'and', 'or', 'a', 'an', 'in', 'on', 'of', 'to', 'with'}
    return [w for w in words if w not in stop and len(w) > 2][:8]
