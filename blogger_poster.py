"""
📝 Blogger Poster — ينشر مقالة SEO احترافية على Blogger
✅ أسلوب مطابق لقالب الموقع (ألوان، تنسيق، HTML)
✅ التاجات والوصف والكوليكشن من designs.txt
✅ الكوليكشن = label رئيسي في Blogger (section)
✅ أسماء كل المنتجات المتاحة
✅ 600+ كلمة مع SEO كامل
"""
import os, re, json, requests
from datetime import datetime

BLOGGER_BLOG_ID       = os.getenv('BLOGGER_BLOG_ID', '')
BLOGGER_CLIENT_ID     = os.getenv('BLOGGER_CLIENT_ID', '')
BLOGGER_CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOGGER_REFRESH_TOKEN = os.getenv('BLOGGER_REFRESH_TOKEN', '')
GROQ_API_KEY          = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL            = 'llama-3.3-70b-versatile'
STORE_URL             = 'https://www.redbubble.com/people/cust-tshirts/shop'
MIN_IMAGES            = 12

ALL_PRODUCTS = [
    'Classic T-Shirt','Fitted T-Shirt','Relaxed T-Shirt',
    'Pullover Hoodie','Zip Hoodie','Pullover Sweatshirt',
    'Sticker','Transparent Sticker','Glossy Sticker',
    'Mug','Travel Mug','Water Bottle',
    'Phone Case','Tough Phone Case',
    'Tote Bag','Drawstring Bag',
    'Throw Pillow','Duvet Cover',
    'Art Print','Poster','Canvas Print',
    'Photographic Print','Art Board Print',
    'Leggings','Dress','Scarf',
    'Laptop Skin','Laptop Sleeve',
    'Greeting Card','Spiral Notebook',
    'Pin','Magnet','Face Mask','Bucket Hat',
]

COLLECTION_URLS = {
    'Three Legged Legends':         'https://www.redbubble.com/people/cust-tshirts/shop?artistUserName=Cust-tshirts&collections=4463017&iaCode=all-departments&sortOrder=top%20selling',
    'Whimsical Illustrations':      'https://www.redbubble.com/people/cust-tshirts/shop?artistUserName=cust-tshirts&collections=4364050&iaCode=all-departments&sortOrder=top%20selling',
    'Islamic Art':                  'https://www.redbubble.com/people/cust-tshirts/shop?artistUserName=cust-tshirts&collections=4372617&iaCode=all-departments&sortOrder=top%20selling',
    'Motivational & Inspirational': 'https://www.redbubble.com/people/cust-tshirts/shop?artistUserName=cust-tshirts&collections=4425787&iaCode=all-departments&sortOrder=top%20selling',
    'Spooky Season Vibes':          'https://www.redbubble.com/people/cust-tshirts/shop?artistUserName=cust-tshirts&collections=4367457&iaCode=all-departments&sortOrder=top%20selling',
}


# ══════════════════════════════════════════════════════════════
# 🔑 AUTH
# ══════════════════════════════════════════════════════════════

def get_access_token():
    if not all([BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN]):
        print("⚠️ Blogger credentials missing")
        return None
    try:
        r = requests.post(
            'https://oauth2.googleapis.com/token',
            data={
                'client_id':     BLOGGER_CLIENT_ID,
                'client_secret': BLOGGER_CLIENT_SECRET,
                'refresh_token': BLOGGER_REFRESH_TOKEN,
                'grant_type':    'refresh_token',
            }, timeout=15
        )
        token = r.json().get('access_token')
        if not token:
            print(f"❌ Auth failed: {r.json().get('error_description','')}")
        return token
    except Exception as e:
        print(f"❌ Auth error: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 🖼️ IMAGES
# ══════════════════════════════════════════════════════════════

def fetch_product_images(product_url, max_images=20):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36',
        'Accept': 'text/html,*/*;q=0.8',
        'Referer': 'https://www.redbubble.com/',
    }
    urls, seen = [], set()
    try:
        html = requests.get(product_url, headers=headers, timeout=20).text
        for pat in [
            r'content="(https://ih\d+\.redbubble\.net/[^"]+)"',
            r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"',
            r'src="(https://ih\d+\.redbubble\.net/[^"]+)"',
        ]:
            for m in re.finditer(pat, html):
                u = m.group(1).split('?')[0]
                if u not in seen:
                    seen.add(u)
                    urls.append(u)
        nd = re.search(r'<script[^>]+id=["\']__NEXT_DATA__["\'][^>]*>(.+?)</script>', html, re.DOTALL)
        if nd:
            try:
                for m in re.finditer(r'"(https://ih\d+\.redbubble\.net/image\.[^"]+)"', json.dumps(json.loads(nd.group(1)))):
                    u = m.group(1).split('?')[0]
                    if u not in seen:
                        seen.add(u)
                        urls.append(u)
            except Exception:
                pass
    except Exception as e:
        print(f"   ⚠️ Image fetch error: {e}")
    print(f"   🖼️  Found {len(urls)} images")
    return urls[:max_images]


def prepare_images(token, product_url, design_hint):
    print("   📥 Fetching & uploading images...")
    raw = fetch_product_images(product_url, 20)
    if not raw:
        return []

    hdrs = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://www.redbubble.com/'}
    album_id = os.getenv('BLOGGER_ALBUM_ID', 'default')
    api = f'https://picasaweb.google.com/data/feed/api/user/default/albumid/{album_id}'

    uploaded, fallback = [], []
    for i, img_url in enumerate(raw[:MIN_IMAGES + 4]):
        try:
            r = requests.get(img_url, headers=hdrs, timeout=15)
            if r.status_code != 200:
                fallback.append(img_url)
                continue
            mime = r.headers.get('Content-Type', 'image/jpeg').split(';')[0].strip()
            up = requests.post(api, headers={
                'Authorization': f'Bearer {token}',
                'Content-Type': mime,
                'Slug': f"{design_hint[:30].replace(' ','_')}_{i+1}.jpg",
                'GData-Version': '2',
            }, data=r.content, timeout=30)

            hosted = None
            if up.status_code in (200, 201):
                for pfx in ['lh3.', 'lh4.', 'lh5.', 'lh6.']:
                    idx = up.text.find(pfx)
                    if idx >= 0:
                        sq = up.text.rfind('"', 0, idx)
                        eq = up.text.find('"', idx)
                        if sq >= 0 and eq > idx:
                            hosted = up.text[sq+1:eq]
                            break
            if hosted:
                uploaded.append(hosted)
                print(f"      ✅ Image {i+1} uploaded")
            else:
                fallback.append(img_url)
                print(f"      ⚠️ Image {i+1} CDN URL")
        except Exception as e:
            fallback.append(img_url)
        if len(uploaded) + len(fallback) >= MIN_IMAGES:
            break

    all_imgs = uploaded + fallback
    print(f"   🖼️  Ready: {len(uploaded)} Blogger + {len(fallback)} CDN = {len(all_imgs)}")
    return all_imgs


# ══════════════════════════════════════════════════════════════
# 🤖 AI ARTICLE
# ══════════════════════════════════════════════════════════════

def generate_article(design_hint, product_url, user_tags, user_description, collection):
    tags_str  = ', '.join(user_tags) if user_tags else design_hint
    prods     = ', '.join(ALL_PRODUCTS[:20])
    col_url   = COLLECTION_URLS.get(collection, STORE_URL)
    desc_part = f'\nDESIGN DESCRIPTION:\n"""\n{user_description}\n"""' if user_description else ''
    col_part  = f'\nCOLLECTION: "{collection}" — URL: {col_url}' if collection else ''

    prompt = f"""You are a professional English content writer for "Cust Tshirts" — a Redbubble print-on-demand store.

PRODUCT:
- Design: "{design_hint}"
- URL: {product_url}
- Keywords: {tags_str}
- Available on: {prods}
{col_part}
{desc_part}

Write a 600+ word SEO article. Friendly, human, enthusiastic tone. No keyword stuffing. No fake prices.

Respond ONLY with valid JSON (no markdown, no explanation):
{{
  "seo_title": "SEO title 55-65 chars with main keyword",
  "meta_description": "150-160 chars meta description with keyword and CTA",
  "h1": "H1 heading — keyword-rich, different from title",
  "labels": ["tag1","tag2","tag3","tag4","tag5","tag6","tag7","tag8"],
  "intro": "3-4 sentences. Hook the reader. Main keyword in first sentence. Use design description if provided.",
  "about_h2": "H2 about the design",
  "about_body": "5-6 sentences about what makes this design special. Use description details.",
  "who_for_h2": "H2 who is this for",
  "who_for_intro": "1-2 sentences intro",
  "who_for_list": ["Person type 1","Person type 2","Person type 3","Person type 4","Person type 5"],
  "products_h2": "H2 available products",
  "products_body": "3-4 sentences about the variety: t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints, posters and more.",
  "products_table_caption": "Short table caption",
  "gift_h2": "H2 perfect gift",
  "gift_body": "4-5 sentences. Perfect gift for birthdays, Christmas, graduation, anniversaries.",
  "gift_list": ["Occasion 1","Occasion 2","Occasion 3","Occasion 4"],
  "quality_h2": "H2 quality",
  "quality_body": "3-4 sentences about Redbubble quality, satisfaction guarantee, worldwide shipping.",
  "quality_highlights": ["Highlight 1","Highlight 2","Highlight 3","Highlight 4"],
  "how_order_h2": "H2 how to order",
  "how_order_steps": ["Step 1","Step 2","Step 3","Step 4"],
  "faq_q1": "FAQ about this design",
  "faq_a1": "2-3 sentence answer",
  "faq_q2": "FAQ about shipping",
  "faq_a2": "2-3 sentence answer",
  "faq_q3": "FAQ about gifts",
  "faq_a3": "2-3 sentence answer",
  "conclusion": "3-4 sentences strong conclusion with CTA"
}}"""

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {GROQ_API_KEY}', 'Content-Type': 'application/json'},
            json={
                'model': GROQ_MODEL, 'temperature': 0.72, 'max_tokens': 3000,
                'messages': [
                    {'role': 'system', 'content': 'Expert SEO writer. Respond ONLY with valid JSON. No markdown.'},
                    {'role': 'user',   'content': prompt}
                ],
            }, timeout=50
        )
        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json','').replace('```','').strip()
        return json.loads(raw)
    except Exception as e:
        print(f"   ⚠️ AI failed: {e} — using fallback")
        return _fallback(design_hint, user_tags)


def _fallback(d, tags):
    return {
        'seo_title': f'{d} — Unique Redbubble Design',
        'meta_description': f'Discover the {d} design on Redbubble. T-shirts, stickers, mugs and more. Ships worldwide!',
        'h1': f'{d} — Shop This Unique Design Now',
        'labels': tags[:8] if tags else ['redbubble','design','gift','print on demand'],
        'intro': f'Looking for a unique {d} design? This amazing design is available on dozens of products — from t-shirts and hoodies to stickers, mugs, phone cases and more.',
        'about_h2': f'About The {d} Design',
        'about_body': f'The {d} design is a one-of-a-kind piece of art that instantly stands out. It captures a unique aesthetic that resonates with people who love creative expression.',
        'who_for_h2': 'Who Is This Perfect For?',
        'who_for_intro': 'This design speaks to people who appreciate unique, creative expression.',
        'who_for_list': ['Unique graphic design lovers','People who want to express personality','Gift buyers seeking something original','Animal or humor enthusiasts','Anyone who appreciates creativity'],
        'products_h2': 'Available On Many Products',
        'products_body': f'The {d} design is available on t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints, posters and much more.',
        'products_table_caption': 'Available products for this design',
        'gift_h2': 'Makes a Perfect Gift',
        'gift_body': f'The {d} design makes an unforgettable present for any occasion.',
        'gift_list': ['Birthday gifts','Christmas presents','Graduation gifts','Anniversary surprises'],
        'quality_h2': 'Quality You Can Trust',
        'quality_body': 'Redbubble is trusted by millions. Every purchase is backed by a satisfaction guarantee.',
        'quality_highlights': ['Premium print quality','Ships worldwide','Satisfaction guarantee','Supports independent artists'],
        'how_order_h2': 'How To Order',
        'how_order_steps': ['Click Shop below to visit Redbubble','Choose your product and size','Add to cart and checkout securely','Shipped fresh directly to your door'],
        'faq_q1': f'What products is the {d} design on?',
        'faq_a1': f'Available on t-shirts, hoodies, stickers, mugs, phone cases, tote bags, art prints and more.',
        'faq_q2': 'Does Redbubble ship internationally?',
        'faq_a2': 'Yes, Redbubble ships worldwide. Most orders arrive within 1-2 weeks.',
        'faq_q3': f'Is the {d} design a good gift?',
        'faq_a3': 'Absolutely! It makes an excellent gift for anyone who loves unique, creative products.',
        'conclusion': f'The {d} design is more than just a product — it is a statement. Grab yours today!',
    }


# ══════════════════════════════════════════════════════════════
# 🏗️ BUILD HTML
# ══════════════════════════════════════════════════════════════

def build_html(data, design_hint, product_url, images, user_tags, user_description, collection):
    col_url = COLLECTION_URLS.get(collection, STORE_URL)

    def img(url, alt):
        return (f'<div style="text-align:center;margin:18px 0;">'
                f'<img src="{url}" alt="{alt}" referrerpolicy="no-referrer" crossorigin="anonymous" '
                f'style="max-width:100%;border-radius:8px;box-shadow:0 2px 8px rgba(0,0,0,.12);"/>'
                f'</div>')

    def get(i):
        return img(images[i], f"{design_hint} - Product {i+1}") if i < len(images) else ''

    def cta(text='🛒 Shop This Design on Redbubble', url=None):
        href = url or product_url
        return (f'<div style="text-align:center;margin:24px 0;">'
                f'<a href="{href}" target="_blank" rel="noopener" '
                f'style="display:inline-block;background:#cc0000;color:#fff;padding:13px 32px;'
                f'border-radius:6px;font-weight:bold;font-size:1em;text-decoration:none;'
                f'box-shadow:0 3px 10px rgba(204,0,0,.35);">{text}</a></div>')

    def note(text, em='📌'):
        return (f'<div style="background:#fff2cc;border-left:4px solid #cc0000;'
                f'padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;">'
                f'<strong style="color:#073763;">{em} Note:</strong> {text}</div>')

    def hl(text, bg='#f3f3f3', color='#741b47'):
        return f'<span style="background:{bg};color:{color};padding:2px 6px;">{text}</span>'

    def quote(text):
        return (f'<div style="background:#cfe2f3;border-left:4px solid #1565c0;'
                f'padding:14px 16px;margin:20px 0;border-radius:0 6px 6px 0;'
                f'font-style:italic;color:#073763;">"{text}"</div>')

    # Products table
    rows = ''
    for i in range(0, min(18, len(ALL_PRODUCTS)), 6):
        chunk = ALL_PRODUCTS[i:i+6]
        rows += '<tr>' + ''.join(f'<td style="padding:8px;border:1px solid #ddd;">{p}</td>' for p in chunk) + '</tr>'

    prod_table = (f'<table border="1" cellpadding="0" cellspacing="0" '
                  f'style="width:100%;border-collapse:collapse;margin:16px 0;font-size:.9em;">'
                  f'<thead><tr style="background:#cc0000;color:#fff;">'
                  f'<td colspan="6" style="padding:10px;text-align:center;font-weight:bold;">'
                  f'🛍️ {data.get("products_table_caption","Available Products")}</td></tr></thead>'
                  f'<tbody>{rows}</tbody></table>')

    # Who list
    who_items = ''
    bgs = ['#d9ead3','#cfe2f3','#fff2cc','#f4cccc','#ead1dc']
    for i, item in enumerate(data.get('who_for_list', [])):
        who_items += f'<li style="margin-bottom:8px;">{hl(item, bgs[i%len(bgs)], "#073763")}</li>'

    # Gift list
    gift_items = ''
    for item in data.get('gift_list', []):
        gift_items += f'<li style="margin-bottom:6px;">{hl("📅","#f3f3f3","#741b47")} {item}</li>'

    # Quality list
    qual_items = ''.join(f'<li style="margin-bottom:6px;">✅ {i}</li>' for i in data.get('quality_highlights', []))

    # Order steps
    order_steps = ''
    for i, s in enumerate(data.get('how_order_steps', []), 1):
        order_steps += f'<li style="margin-bottom:10px;">{hl(f"Step {i}","#f3f3f3","#741b47")} 📌 {s}</li>'

    # Description box
    desc_box = ''
    if user_description:
        desc_box = (f'<div style="background:#f8f9fa;border-left:4px solid #cc0000;'
                    f'padding:16px;margin:20px 0;border-radius:0 6px 6px 0;">'
                    f'<strong style="color:#073763;display:block;margin-bottom:8px;">📋 About This Design</strong>'
                    f'<p style="color:#555;margin:0;line-height:1.7;">{user_description}</p></div>')

    # Tags box
    tags_box = ''
    if user_tags:
        spans = ' '.join(
            f'<span style="display:inline-block;background:#f3f3f3;border:1px solid #ddd;'
            f'color:#333;padding:3px 10px;border-radius:4px;font-size:.82em;margin:3px;">{t}</span>'
            for t in user_tags)
        tags_box = (f'<div style="margin:16px 0;">'
                    f'<strong style="color:#073763;font-size:.85em;">🏷️ Tags:</strong><br/>'
                    f'<div style="margin-top:6px;">{spans}</div></div>')

    # Collection badge
    col_badge = ''
    if collection:
        col_badge = (f'<div style="margin:16px 0;">'
                     f'<a href="{col_url}" target="_blank" rel="noopener" '
                     f'style="display:inline-block;background:#073763;color:#fff;'
                     f'padding:5px 14px;border-radius:4px;font-size:.82em;font-weight:bold;'
                     f'text-decoration:none;">📂 Collection: {collection}</a></div>')

    # Image grid
    grid_cells = ''.join(
        f'<div style="flex:1;min-width:100px;max-width:180px;padding:4px;">'
        f'<img src="{images[i]}" alt="{design_hint} product {i+1}" referrerpolicy="no-referrer" '
        f'style="width:100%;border-radius:6px;box-shadow:0 2px 6px rgba(0,0,0,.1);"/></div>'
        for i in range(6, min(12, len(images)))
    )
    grid = (f'<div style="margin:20px 0;">'
            f'<p style="text-align:center;color:#666;font-size:.85em;margin-bottom:10px;">'
            f'🛍️ Available on many products</p>'
            f'<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">'
            f'{grid_cells}</div></div>') if grid_cells else ''

    # FAQ
    faq = (f'<div style="background:#f8f9fa;border-radius:8px;padding:20px;margin:28px 0;">'
           f'<h2 style="color:#cc0000;font-size:x-large;margin-top:0;">❓ Frequently Asked Questions</h2>'
           f'<h3 style="color:#073763;font-size:large;margin-bottom:5px;">Q: {data.get("faq_q1","")}</h3>'
           f'<p style="color:#555;margin:0 0 16px;">{data.get("faq_a1","")}</p>'
           f'<h3 style="color:#073763;font-size:large;margin-bottom:5px;">Q: {data.get("faq_q2","")}</h3>'
           f'<p style="color:#555;margin:0 0 16px;">{data.get("faq_a2","")}</p>'
           f'<h3 style="color:#073763;font-size:large;margin-bottom:5px;">Q: {data.get("faq_q3","")}</h3>'
           f'<p style="color:#555;margin:0;">{data.get("faq_a3","")}</p></div>')

    col_cta_html = ''
    if collection:
        col_cta_html = (
            '<div style="text-align:center;margin:16px 0;">'
            '<a href="' + col_url + '" target="_blank" rel="noopener" '
            'style="display:inline-block;background:#073763;color:#fff;'
            'padding:10px 22px;border-radius:6px;font-size:.9em;'
            'font-weight:bold;text-decoration:none;">'
            + '📂 Browse ' + collection + ' Collection'
            + '</a></div>'
        )

    return f'''<div style="font-family:Georgia,'Times New Roman',serif;max-width:820px;margin:0 auto;line-height:1.82;color:#2d2d2d;font-size:1.02em;">

<p style="color:#999;font-size:.82em;margin-bottom:16px;">
By <strong>Cust Tshirts</strong> &bull; {datetime.now().strftime("%B %d, %Y")} &bull;
<a href="{product_url}" style="color:#cc0000;" target="_blank" rel="noopener">View on Redbubble &rarr;</a>
</p>

{col_badge}

{get(0)}

<div style="border-left:4px solid #cc0000;padding-left:16px;margin:20px 0;font-size:1.05em;color:#444;">
{data.get("intro","")}
</div>

{get(1)}
{desc_box}

<h2 style="color:#cc0000;font-size:x-large;">{data.get("about_h2","About This Design")}</h2>
<div>{data.get("about_body","")}</div>
{get(2)}
{note("This design is available on 30+ product types — from everyday wear to home decor and gifts.", "🎨")}

<h2 style="color:#cc0000;font-size:x-large;">{data.get("who_for_h2","Who Is This For?")}</h2>
<div>{data.get("who_for_intro","")}</div>
<ul style="margin-top:12px;">{who_items}</ul>
{get(3)}

<h2 style="color:#cc0000;font-size:x-large;">{data.get("products_h2","Available On Many Products")}</h2>
<div>{data.get("products_body","")}</div>
{prod_table}
{get(4)}{get(5)}{grid}
{cta()}

<h2 style="color:#cc0000;font-size:x-large;">{data.get("gift_h2","Makes a Perfect Gift")}</h2>
<div>{data.get("gift_body","")}</div>
<ol style="margin-top:12px;">{gift_items}</ol>
{quote(f"The perfect gift isn't expensive — it's thoughtful. The {design_hint} design is exactly that.")}
{get(6) if len(images)>6 else ''}

<h2 style="color:#cc0000;font-size:x-large;">{data.get("quality_h2","Quality You Can Trust")}</h2>
<div>{data.get("quality_body","")}</div>
<ul style="margin-top:10px;">{qual_items}</ul>

<h2 style="color:#cc0000;font-size:x-large;">{data.get("how_order_h2","How To Order")}</h2>
<ol style="margin-top:12px;">{order_steps}</ol>

{tags_box}
{faq}

<div style="background:#fff2cc;padding:16px;border-radius:6px;margin-top:24px;">
<span style="color:#073763;font-weight:bold;">Final Thoughts:</span>
{data.get("conclusion","")}
</div>

{cta("🛒 Shop Now on Redbubble")}

{col_cta_html}

<hr style="border:none;border-top:1px solid #eee;margin:24px 0;"/>
<p style="font-size:.78em;color:#bbb;text-align:center;">
&copy; {datetime.now().year} Cust Tshirts &bull;
<a href="{STORE_URL}" style="color:#cc0000;" target="_blank" rel="noopener">Browse All Designs</a>
</p>
</div>'''


# ══════════════════════════════════════════════════════════════
# 🏷️ AUTO TAGS
# ══════════════════════════════════════════════════════════════

def auto_tags(design_hint, product_url):
    if not GROQ_API_KEY:
        words = re.sub(r'[^a-zA-Z0-9 ]',' ',design_hint).lower().split()
        stop  = {'by','for','the','and','or','a','an','in','on','of','to','with'}
        return [w for w in words if w not in stop and len(w)>2][:8]
    try:
        r = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization':f'Bearer {GROQ_API_KEY}','Content-Type':'application/json'},
            json={
                'model':GROQ_MODEL,'temperature':.5,'max_tokens':150,
                'messages':[
                    {'role':'system','content':'Respond ONLY with a valid JSON array of strings.'},
                    {'role':'user','content':f'Generate 8 SEO tags for this Redbubble design: "{design_hint}". Short phrases. JSON array only.'}
                ],
            }, timeout=20
        )
        raw = r.json()['choices'][0]['message']['content'].strip().replace('```json','').replace('```','').strip()
        tags = json.loads(raw)
        if isinstance(tags,list):
            print(f"   🏷️  Auto-generated {len(tags)} tags")
            return [str(t).strip() for t in tags][:10]
    except Exception:
        pass
    words = re.sub(r'[^a-zA-Z0-9 ]',' ',design_hint).lower().split()
    stop  = {'by','for','the','and','or','a','an','in','on','of','to','with'}
    return [w for w in words if w not in stop and len(w)>2][:8]


# ══════════════════════════════════════════════════════════════
# 📤 MAIN
# ══════════════════════════════════════════════════════════════

def post_to_blogger(design_hint, product_url, images,
                    user_tags=None, user_description='', collection=''):
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping")
        return {'success': False, 'error': 'BLOGGER_BLOG_ID missing'}

    print("\n📝 Publishing SEO article to Blogger...")
    if user_tags is None:
        user_tags = []
    if not user_tags:
        print("   🏷️  No tags — auto-generating...")
        user_tags = auto_tags(design_hint, product_url)

    token = get_access_token()
    if not token:
        return {'success': False, 'error': 'Auth failed'}

    # Images
    hosted = prepare_images(token, product_url, design_hint)
    if len(hosted) < MIN_IMAGES:
        for u in fetch_product_images(product_url, 20):
            if u not in hosted:
                hosted.append(u)
            if len(hosted) >= MIN_IMAGES:
                break
    print(f"   🖼️  Total images: {len(hosted)}")

    # Article
    print("   🤖 Generating SEO article...")
    article = generate_article(design_hint, product_url, user_tags, user_description, collection)

    # HTML
    html = build_html(article, design_hint, product_url, hosted, user_tags, user_description, collection)

    # Labels — ✅ Collection is FIRST label (= Blogger section)
    ai_labels = article.get('labels', [])
    all_labels = []
    if collection:
        all_labels.append(collection)          # أول label = اسم الكوليكشن
    all_labels += [t for t in user_tags if t != collection]
    all_labels += [t for t in ai_labels if t not in all_labels]
    all_labels = list(dict.fromkeys(all_labels))[:20]

    payload = {
        'title':   article.get('seo_title', f'{design_hint} — Shop on Redbubble'),
        'content': html,
        'labels':  all_labels,
    }

    try:
        resp = requests.post(
            f'https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/',
            headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'},
            json=payload, timeout=30
        )
        data = resp.json()
        if resp.status_code in (200, 201) and 'id' in data:
            post_url = data.get('url','')
            print(f"   ✅ Published!")
            print(f"   📰 Title      : {payload['title']}")
            print(f"   🔗 URL        : {post_url}")
            print(f"   📂 Collection : {collection or 'General'}")
            print(f"   🏷️  Labels     : {', '.join(all_labels[:6])}...")
            print(f"   🖼️  Images     : {len(hosted)}")
            return {'success':True,'post_id':data['id'],'url':post_url,'title':payload['title']}
        else:
            err = data.get('error',{}).get('message',str(data))
            print(f"   ❌ Blogger error: {err}")
            return {'success':False,'error':err}
    except Exception as e:
        print(f"   ❌ Publish failed: {e}")
        return {'success':False,'error':str(e)}
