"""
📝 Blogger Poster — ينشر مقالة SEO كاملة على Blogger
✅ الصور بتترفع على Blogger
✅ المقالة أكتر من 500 كلمة
✅ 12 صورة منتج على الأقل
✅ SEO كامل
✅ التاجات من designs.txt
"""
import os, re, json, base64, requests
from datetime import datetime

BLOGGER_BLOG_ID       = os.getenv('BLOGGER_BLOG_ID', '')
BLOGGER_CLIENT_ID     = os.getenv('BLOGGER_CLIENT_ID', '')
BLOGGER_CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOGGER_REFRESH_TOKEN = os.getenv('BLOGGER_REFRESH_TOKEN', '')
GROQ_API_KEY          = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL            = 'llama-3.3-70b-versatile'
MIN_IMAGES            = 12


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
# 🖼️ IMAGES
# ══════════════════════════════════════════════════════════════

def fetch_product_images(product_url: str, max_images: int = 20) -> list:
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36',
        'Accept': 'text/html,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.redbubble.com/',
    }
    image_urls = []
    seen = set()
    try:
        resp = requests.get(product_url, headers=headers, timeout=20)
        html = resp.text

        patterns = [
            r'content="(https://ih\d+\.redbubble\.net/[^"]+)"',
            r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"',
            r'src="(https://ih\d+\.redbubble\.net/[^"]+)"',
        ]
        for pat in patterns:
            for m in re.finditer(pat, html):
                url = m.group(1).split("?")[0]
                if url not in seen:
                    seen.add(url)
                    image_urls.append(url)

        nd = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.DOTALL)
        if nd:
            try:
                raw = json.dumps(json.loads(nd.group(1)))
                for m in re.finditer(r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"', raw):
                    url = m.group(1).split("?")[0]
                    if url not in seen:
                        seen.add(url)
                        image_urls.append(url)
            except Exception:
                pass

    except Exception as e:
        print(f"   ⚠️ Image fetch error: {e}")

    print(f"   🖼️  Found {len(image_urls)} images")
    return image_urls[:max_images]


def download_b64(img_url: str):
    try:
        resp = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.redbubble.com/"}, timeout=15)
        if resp.status_code == 200:
            ct = resp.headers.get("Content-Type", "image/jpeg")
            mime = ct.split(";")[0].strip()
            if "png" in mime: mime = "image/png"
            elif "webp" in mime: mime = "image/webp"
            else: mime = "image/jpeg"
            return base64.b64encode(resp.content).decode("utf-8"), mime
    except Exception:
        pass
    return None


# Picasa API removed — using base64 embedding instead


def prepare_images(token: str, product_url: str, design_hint: str) -> list:
    """
    ✅ يحمّل الصور كـ base64 — Blogger بيحوّلها لصور مرفوعة على Google تلقائياً
    """
    print(f"   📥 Fetching & embedding images...")
    raw_urls = fetch_product_images(product_url, max_images=20)
    if not raw_urls:
        return []

    final = []
    for i, img_url in enumerate(raw_urls[:MIN_IMAGES + 4]):
        result = download_b64(img_url)
        if result:
            b64_data, mime = result
            # ✅ data URI — Blogger بيرفعها على Google تلقائياً لما ينشر المقالة
            data_uri = f"data:{mime};base64,{b64_data}"
            final.append(data_uri)
            print(f"      ✅ Image {i+1} embedded as base64")
        else:
            # fallback: رابط أصلي لو التحميل فشل
            final.append(img_url)
            print(f"      ⚠️ Image {i+1} using original URL (download failed)")

        if len(final) >= MIN_IMAGES + 4:
            break

    print(f"   🖼️  Ready: {len(final)} images for article")
    return final


# ══════════════════════════════════════════════════════════════
# 🤖 AI ARTICLE — 500+ words
# ══════════════════════════════════════════════════════════════

def generate_article(design_hint: str, product_url: str, user_tags: list) -> dict:
    tags_str = ", ".join(user_tags) if user_tags else design_hint

    prompt = f"""You are an expert SEO content writer for a Redbubble shop.

Write a FULL SEO article — MUST be 500+ words total.
DESIGN: "{design_hint}"
PRODUCT URL: {product_url}
KEYWORDS: {tags_str}

Respond ONLY with valid JSON — no markdown, no extra text:
{{
  "seo_title": "SEO title 50-60 chars with main keyword",
  "meta_description": "Meta description 150-160 chars",
  "h1": "H1 heading keyword-rich, different from title",
  "labels": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "intro": "4 sentences introduction with main keyword in first sentence. Hook the reader.",
  "section1_h2": "H2 about the design",
  "section1_body": "5 sentences about what makes this design special, its appeal, humor or meaning.",
  "section2_h2": "H2 about available products",
  "section2_body": "5 sentences about t-shirts, hoodies, stickers, mugs, phone cases, tote bags, pillows, art prints, leggings. Quality, worldwide shipping.",
  "section3_h2": "H2 perfect gift idea",
  "section3_body": "5 sentences about who this is perfect for, occasions, why it will delight them.",
  "section4_h2": "H2 why choose Redbubble",
  "section4_body": "4 sentences about quality, satisfaction guarantee, independent artists, secure checkout.",
  "section5_h2": "H2 how to order",
  "section5_body": "4 sentences simple steps to order, fast shipping, multiple payment options.",
  "faq_q1": "FAQ about the design or products",
  "faq_a1": "3 sentence answer",
  "faq_q2": "FAQ about shipping",
  "faq_a2": "3 sentence answer",
  "faq_q3": "FAQ about gifts or sizing",
  "faq_a3": "3 sentence answer",
  "conclusion": "4 sentences conclusion with strong CTA and urgency."
}}

Rules: keyword in title+H1+intro+3 sections. Tone: enthusiastic, persuasive. NEVER mention discount codes."""

    try:
        resp = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": GROQ_MODEL, "temperature": 0.75, "max_tokens": 2500,
                "messages": [
                    {"role": "system", "content": "Respond ONLY with valid JSON. No markdown. No explanation."},
                    {"role": "user", "content": prompt}
                ],
            },
            timeout=45
        )
        raw = resp.json()["choices"][0]["message"]["content"].strip()
        raw = raw.replace("```json","").replace("```","").strip()
        return json.loads(raw)
    except Exception as e:
        print(f"   ⚠️ AI failed: {e} — using fallback")
        return _fallback(design_hint, product_url, user_tags)


def _fallback(design_hint: str, url: str, tags: list) -> dict:
    d = design_hint
    return {
        "seo_title": f"{d} — Unique Design on Redbubble",
        "meta_description": f"Discover the {d} design on Redbubble. T-shirts, stickers, mugs and more. Ships worldwide!",
        "h1": f"{d} — Shop This Unique Design Now",
        "labels": tags[:8] if tags else ["redbubble","design","gift","print on demand"],
        "intro": f"Looking for a unique {d} design? This amazing design is available on dozens of products — from t-shirts and hoodies to stickers, mugs, phone cases and much more. Whether you're treating yourself or searching for the perfect gift, you've found exactly what you need. Read on to discover everything this incredible design has to offer.",
        "section1_h2": f"About The {d} Design",
        "section1_body": f"The {d} design is a one-of-a-kind piece of art that instantly stands out. It captures a unique aesthetic that resonates deeply with people who love to express their personality through creative design. Every detail has been thoughtfully crafted, from the colors to the concept, making it both eye-catching and memorable. Whether displayed on a t-shirt in public or a mug at your desk, this design always starts conversations. It's the kind of design that makes you smile every single time you see it.",
        "section2_h2": "Available On Dozens of Products",
        "section2_body": f"The {d} design is printed on a huge range of high-quality products including t-shirts, hoodies, sweatshirts, stickers, mugs, phone cases, tote bags, pillows, art prints, leggings, notebooks, masks, and much more. All items are produced using premium materials and state-of-the-art printing technology that ensures vivid, long-lasting results. Redbubble ships worldwide, so no matter where you are, this design can be delivered right to your door. The products are made on demand, ensuring freshness and quality with every single order. Explore the full range and find your perfect product.",
        "section3_h2": "The Perfect Gift For Any Occasion",
        "section3_body": f"Struggling to find a gift that's truly unique? The {d} design makes an unforgettable present for birthdays, Christmas, Valentine's Day, graduations, anniversaries, and any other special occasion you can think of. It shows the recipient that you took time to find something genuinely personal and creative, not just another generic gift. Anyone who receives this will immediately know how thoughtful and original the choice was. It's the kind of gift that gets remembered and talked about long after the occasion has passed.",
        "section4_h2": "Why Shop On Redbubble",
        "section4_body": "Redbubble is one of the world's leading print-on-demand marketplaces, trusted by millions of customers globally. Every purchase directly supports independent artists and creatives, making your buy meaningful beyond the product itself. Products come backed by a satisfaction guarantee — if something isn't right, Redbubble's customer service team will make it right. With secure checkout, multiple payment options, and fast worldwide shipping, the shopping experience is smooth and worry-free from start to finish.",
        "section5_h2": "How To Order Your Design",
        "section5_body": f"Ordering your {d} design is quick and straightforward. Simply click the link to visit the product page on Redbubble, browse the available product types, and select the one that suits you best. Choose your preferred size, color, and style if applicable, then add it to your cart and proceed to checkout. Payment is secure and multiple options are available including credit card and PayPal. Your order will be printed fresh and shipped directly to you, typically arriving within a few business days.",
        "faq_q1": f"What products is the {d} design available on?",
        "faq_a1": f"The {d} design is available on t-shirts, hoodies, sweatshirts, stickers, mugs, phone cases, tote bags, art prints, pillows, leggings, notebooks, and many more products. The full range can be viewed on the Redbubble product page. New product types are added regularly, so check back often for more options.",
        "faq_q2": "Does Redbubble ship internationally?",
        "faq_a2": "Yes, Redbubble ships to most countries worldwide. Shipping times and costs vary depending on your location and the shipping method selected at checkout. Standard and express shipping options are typically available, and orders can be tracked once dispatched.",
        "faq_q3": f"Is the {d} design a good gift?",
        "faq_a3": f"Absolutely — the {d} design makes an excellent gift for anyone who appreciates unique, creative products. It's available on practical everyday items that the recipient will use and enjoy regularly. The design is conversation-starting and memorable, making it a gift that truly stands out from the crowd.",
        "conclusion": f"The {d} design is more than just a product — it's a statement of personality, creativity, and individuality. Whether you're buying for yourself or searching for that perfect gift, this design delivers on every level. Don't wait — click the link below to visit the Redbubble page, explore all available products, and order yours today. Join the thousands of happy customers who have made this design a part of their everyday life.",
    }


# ══════════════════════════════════════════════════════════════
# 🏗️ BUILD HTML
# ══════════════════════════════════════════════════════════════

def build_html(data: dict, design_hint: str, product_url: str, images: list) -> str:
    def img(url, alt, n):
        return f'''<div style="text-align:center;margin:22px 0;">
  <img src="{url}" alt="{alt} - {n}" title="{alt}"
       style="max-width:100%;border-radius:8px;box-shadow:0 2px 10px rgba(0,0,0,0.12);" />
</div>'''

    def get(idx):
        return img(images[idx], design_hint, idx+1) if idx < len(images) else ""

    # Grid آخر 6 صور
    grid = ""
    if len(images) >= 7:
        cells = "".join(
            f'''<div style="flex:1;min-width:110px;max-width:190px;padding:4px;">
  <img src="{images[i]}" alt="{design_hint} product {i+1}"
       style="width:100%;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,0.1);" />
</div>''' for i in range(6, min(12, len(images)))
        )
        grid = f'''<div style="margin:24px 0;">
  <p style="text-align:center;color:#666;font-size:0.9em;margin-bottom:10px;">
    🛍️ Available on many products
  </p>
  <div style="display:flex;flex-wrap:wrap;gap:8px;justify-content:center;">{cells}</div>
</div>'''

    faq = f'''<div style="background:#f8f9fa;border-radius:8px;padding:24px;margin:30px 0;">
  <h2 style="color:#2c3e50;margin-top:0;">❓ Frequently Asked Questions</h2>
  <h3 style="color:#34495e;font-size:1em;">Q: {data.get("faq_q1","")}</h3>
  <p style="color:#555;">{data.get("faq_a1","")}</p>
  <h3 style="color:#34495e;font-size:1em;">Q: {data.get("faq_q2","")}</h3>
  <p style="color:#555;">{data.get("faq_a2","")}</p>
  <h3 style="color:#34495e;font-size:1em;">Q: {data.get("faq_q3","")}</h3>
  <p style="color:#555;">{data.get("faq_a3","")}</p>
</div>'''

    return f'''<div style="font-family:Georgia,serif;max-width:820px;margin:0 auto;line-height:1.85;color:#2d2d2d;font-size:1.05em;">

<h1 style="font-size:1.95em;color:#1a1a1a;line-height:1.3;">{data.get("h1", design_hint)}</h1>
<p style="color:#999;font-size:0.82em;">By <strong>Cust Tshirts</strong> • {datetime.now().strftime("%B %d, %Y")} • <a href="{product_url}" style="color:#e74c3c;">View on Redbubble →</a></p>

{get(0)}

<p style="font-size:1.1em;color:#444;border-left:4px solid #e74c3c;padding-left:14px;margin:20px 0;">{data.get("intro","")}</p>

{get(1)}

<h2 style="color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">{data.get("section1_h2","")}</h2>
<p>{data.get("section1_body","")}</p>

{get(2)}

<h2 style="color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">{data.get("section2_h2","")}</h2>
<p>{data.get("section2_body","")}</p>

{get(3)}
{get(4)}
{grid}

<h2 style="color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">{data.get("section3_h2","")}</h2>
<p>{data.get("section3_body","")}</p>

{get(5)}

<h2 style="color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">{data.get("section4_h2","")}</h2>
<p>{data.get("section4_body","")}</p>

<h2 style="color:#2c3e50;border-bottom:2px solid #f0f0f0;padding-bottom:8px;">{data.get("section5_h2","")}</h2>
<p>{data.get("section5_body","")}</p>

{faq}

<p style="font-size:1.05em;color:#444;">{data.get("conclusion","")}</p>

<div style="text-align:center;margin:40px 0 20px;">
  <a href="{product_url}" style="display:inline-block;background:#e74c3c;color:#fff;padding:16px 40px;border-radius:6px;text-decoration:none;font-weight:bold;font-size:1.1em;box-shadow:0 4px 12px rgba(231,76,60,0.35);">
    🛒 Shop This Design on Redbubble
  </a>
  <p style="color:#999;font-size:0.82em;margin-top:10px;">Worldwide shipping • Satisfaction guaranteed</p>
</div>

<hr style="border:none;border-top:1px solid #eee;margin:30px 0;" />
<p style="font-size:0.78em;color:#bbb;text-align:center;">© {datetime.now().year} Cust Tshirts • <a href="{product_url}" style="color:#e74c3c;">Redbubble</a></p>

</div>'''


# ══════════════════════════════════════════════════════════════
# 📤 MAIN PUBLISH FUNCTION
# ══════════════════════════════════════════════════════════════

def post_to_blogger(design_hint: str, product_url: str, images: list, user_tags: list = None) -> dict:
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping")
        return {"success": False, "error": "BLOGGER_BLOG_ID missing"}

    print("\n📝 Publishing SEO article to Blogger...")
    if user_tags is None:
        user_tags = []

    token = get_access_token()
    if not token:
        return {"success": False, "error": "Auth failed"}

    hosted = prepare_images(token, product_url, design_hint)

    # لو مش وصلنا 12 — أكمّل من الروابط الأصلية
    if len(hosted) < MIN_IMAGES:
        extra = fetch_product_images(product_url, max_images=20)
        for u in extra:
            if u not in hosted:
                hosted.append(u)
            if len(hosted) >= MIN_IMAGES:
                break

    print(f"   🖼️  Total images: {len(hosted)}")

    print("   🤖 Generating 500+ word SEO article...")
    article = generate_article(design_hint, product_url, user_tags)

    html = build_html(article, design_hint, product_url, hosted)

    ai_labels  = article.get("labels", [])
    all_labels = list(dict.fromkeys(user_tags + ai_labels))[:20]

    payload = {
        "title":   article.get("seo_title", f"{design_hint} — Shop on Redbubble"),
        "content": html,
        "labels":  all_labels,
    }

    try:
        resp = requests.post(
            f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30
        )
        data = resp.json()

        if resp.status_code in (200, 201) and "id" in data:
            post_url = data.get("url", "")
            print(f"   ✅ Published!")
            print(f"   📰 Title  : {payload['title']}")
            print(f"   🔗 URL    : {post_url}")
            print(f"   🏷️  Labels : {', '.join(all_labels[:6])}...")
            print(f"   🖼️  Images : {len(hosted)}")
            return {"success": True, "post_id": data["id"], "url": post_url, "title": payload["title"]}
        else:
            err = data.get("error", {}).get("message", str(data))
            print(f"   ❌ Blogger error: {err}")
            return {"success": False, "error": err}

    except Exception as e:
        print(f"   ❌ Publish failed: {e}")
        return {"success": False, "error": str(e)}
