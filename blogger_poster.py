"""
📝 Blogger Poster — ينشر مقالة SEO على Blogger
بيستخدم Groq AI لكتابة المقالة وBlogger API v3 للنشر
"""
import os
import json
import requests
from datetime import datetime

# ── Blogger Credentials ───────────────────────────────────────
BLOGGER_BLOG_ID       = os.getenv('BLOGGER_BLOG_ID', '')
BLOGGER_CLIENT_ID     = os.getenv('BLOGGER_CLIENT_ID', '')
BLOGGER_CLIENT_SECRET = os.getenv('BLOGGER_CLIENT_SECRET', '')
BLOGGER_REFRESH_TOKEN = os.getenv('BLOGGER_REFRESH_TOKEN', '')

GROQ_API_KEY = os.getenv('GROQ_API_KEY', '')
GROQ_MODEL   = 'llama-3.3-70b-versatile'


# ══════════════════════════════════════════════════════════════
# 🔑 AUTH — Get Access Token
# ══════════════════════════════════════════════════════════════

def get_access_token() -> str | None:
    """تجديد الـ Access Token باستخدام الـ Refresh Token"""
    if not all([BLOGGER_CLIENT_ID, BLOGGER_CLIENT_SECRET, BLOGGER_REFRESH_TOKEN]):
        print("⚠️ Blogger credentials missing — skipping Blogger post")
        return None

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

    data = resp.json()
    token = data.get('access_token')

    if not token:
        print(f"❌ Blogger auth failed: {data.get('error_description', data)}")
        return None

    return token


# ══════════════════════════════════════════════════════════════
# 🤖 AI — Generate SEO Article
# ══════════════════════════════════════════════════════════════

def generate_seo_article(design_hint: str, product_url: str, images: list) -> dict:
    """
    يولّد مقالة SEO كاملة بالـ AI
    بيرجع: {title, content, labels, meta_description}
    """
    if not GROQ_API_KEY:
        print("⚠️ GROQ_API_KEY missing — using basic article")
        return _basic_article(design_hint, product_url, images)

    # اختار صورة أولى للمقالة
    main_image = images[0] if images else ''
    extra_images = images[1:4] if len(images) > 1 else []

    images_html = ''
    for img in extra_images:
        images_html += f'<img src="{img}" alt="{design_hint}" style="max-width:100%;margin:10px 0;" />\n'

    prompt = f"""You are an expert SEO content writer for a print-on-demand Redbubble shop.

Write a complete SEO-optimized blog article about this product:
DESIGN: "{design_hint}"
PRODUCT URL: {product_url}
MAIN IMAGE: {main_image}

OUTPUT FORMAT — respond ONLY with valid JSON, no markdown, no extra text:
{{
  "title": "SEO title (50-60 chars, include main keyword)",
  "meta_description": "Meta description (150-160 chars, compelling, include keyword)",
  "labels": ["tag1", "tag2", "tag3", "tag4", "tag5"],
  "h1": "H1 heading (different from title, keyword-rich)",
  "intro": "2-3 sentence intro paragraph that hooks the reader and includes the main keyword naturally",
  "section1_h2": "H2 for first section",
  "section1_body": "3-4 sentences about the design's story, meaning, or appeal",
  "section2_h2": "H2 about products available (t-shirts, stickers, mugs, etc.)",
  "section2_body": "3-4 sentences about the variety of products this design is available on",
  "section3_h2": "H2 about who this is perfect for (gift ideas, target audience)",
  "section3_body": "3-4 sentences about ideal buyers, gift occasions, who would love this",
  "cta_heading": "H2 call-to-action heading",
  "cta_body": "2-3 sentences urgent CTA encouraging them to visit the shop and buy"
}}

SEO RULES:
- Main keyword = the design theme from "{design_hint}"
- Use keyword naturally in title, H1, intro, and at least 2 sections
- Write for humans first, Google second
- Tone: enthusiastic, friendly, sales-oriented
- All text in English"""

    try:
        resp = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={
                'Authorization': f'Bearer {GROQ_API_KEY}',
                'Content-Type': 'application/json',
            },
            json={
                'model':       GROQ_MODEL,
                'temperature': 0.7,
                'max_tokens':  1500,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are an SEO expert. Always respond with valid JSON only. No markdown, no explanation, just the JSON object.'
                    },
                    {'role': 'user', 'content': prompt}
                ],
            },
            timeout=30
        )

        raw = resp.json()['choices'][0]['message']['content'].strip()
        raw = raw.replace('```json', '').replace('```', '').strip()
        article_data = json.loads(raw)

        # بناء HTML المقالة
        content = _build_html(article_data, design_hint, product_url, main_image, images_html)

        return {
            'title':            article_data.get('title', f'{design_hint} — Shop Now'),
            'content':          content,
            'labels':           article_data.get('labels', ['redbubble', 'design', 'gift']),
            'meta_description': article_data.get('meta_description', ''),
        }

    except Exception as e:
        print(f"⚠️ AI article generation failed: {e}")
        return _basic_article(design_hint, product_url, images)


def _build_html(data: dict, design_hint: str, url: str, main_image: str, extra_imgs: str) -> str:
    """بناء HTML المقالة من البيانات"""
    main_img_html = f'<img src="{main_image}" alt="{design_hint}" style="max-width:100%;border-radius:8px;margin:15px 0;" />' if main_image else ''

    return f"""
<div style="font-family: Georgia, serif; max-width: 800px; margin: 0 auto; line-height: 1.8; color: #333;">

  <h1 style="font-size:2em; color:#1a1a1a; margin-bottom:10px;">{data.get('h1', data.get('title', design_hint))}</h1>

  {main_img_html}

  <p style="font-size:1.1em; color:#555;">{data.get('intro', '')}</p>

  <h2 style="color:#2c2c2c; margin-top:30px;">{data.get('section1_h2', 'About This Design')}</h2>
  <p>{data.get('section1_body', '')}</p>

  {extra_imgs}

  <h2 style="color:#2c2c2c; margin-top:30px;">{data.get('section2_h2', 'Available Products')}</h2>
  <p>{data.get('section2_body', '')}</p>

  <h2 style="color:#2c2c2c; margin-top:30px;">{data.get('section3_h2', 'Perfect As a Gift')}</h2>
  <p>{data.get('section3_body', '')}</p>

  <div style="background:#f9f9f9; border-left:4px solid #e74c3c; padding:20px; margin:30px 0; border-radius:4px;">
    <h2 style="color:#e74c3c; margin-top:0;">{data.get('cta_heading', 'Shop This Design Now')}</h2>
    <p>{data.get('cta_body', '')}</p>
    <a href="{url}"
       style="display:inline-block; background:#e74c3c; color:white; padding:12px 28px;
              border-radius:5px; text-decoration:none; font-weight:bold; font-size:1.05em;
              margin-top:10px;">
      🛒 Shop on Redbubble
    </a>
  </div>

  <hr style="border:none; border-top:1px solid #eee; margin:30px 0;" />
  <p style="font-size:0.85em; color:#999;">
    Published by <strong>Cust Tshirts</strong> •
    <a href="{url}" style="color:#e74c3c;">View on Redbubble</a>
  </p>

</div>
"""


def _basic_article(design_hint: str, url: str, images: list) -> dict:
    """مقالة بسيطة لو الـ AI فشل"""
    img_html = f'<img src="{images[0]}" alt="{design_hint}" style="max-width:100%;" />' if images else ''
    content = f"""
<div style="font-family:Georgia,serif;max-width:800px;margin:0 auto;line-height:1.8;">
  <h1>{design_hint} — Available on Redbubble</h1>
  {img_html}
  <p>Discover our latest design: <strong>{design_hint}</strong>. Available on t-shirts, stickers, mugs, and more!</p>
  <p>Perfect as a gift or a treat for yourself. High quality print-on-demand products shipped worldwide.</p>
  <p><a href="{url}" style="background:#e74c3c;color:white;padding:10px 20px;border-radius:5px;text-decoration:none;">🛒 Shop Now</a></p>
</div>
"""
    return {
        'title':   f'{design_hint} Design — Shop on Redbubble',
        'content': content,
        'labels':  ['redbubble', 'design', 'gift idea', 'print on demand'],
        'meta_description': f'Check out our {design_hint} design on Redbubble. Available on t-shirts, stickers, mugs and more. Ships worldwide!',
    }


# ══════════════════════════════════════════════════════════════
# 📤 PUBLISH TO BLOGGER
# ══════════════════════════════════════════════════════════════

def post_to_blogger(design_hint: str, product_url: str, images: list) -> dict:
    """
    ينشر مقالة SEO على Blogger
    بيرجع: {'success': True, 'post_id': '...', 'url': '...'} أو {'success': False}
    """
    if not BLOGGER_BLOG_ID:
        print("⚠️ BLOGGER_BLOG_ID not set — skipping Blogger")
        return {'success': False, 'error': 'BLOGGER_BLOG_ID missing'}

    print("\n📝 Publishing to Blogger...")

    # جيب الـ Access Token
    token = get_access_token()
    if not token:
        return {'success': False, 'error': 'Auth failed'}

    # ولّد المقالة
    print("   🤖 Generating SEO article...")
    article = generate_seo_article(design_hint, product_url, images)

    # انشر على Blogger API
    api_url = f"https://www.googleapis.com/blogger/v3/blogs/{BLOGGER_BLOG_ID}/posts/"

    payload = {
        'title':   article['title'],
        'content': article['content'],
        'labels':  article['labels'],
    }

    try:
        resp = requests.post(
            api_url,
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
            print(f"   ✅ Blogger post published!")
            print(f"   📰 Title : {article['title']}")
            print(f"   🔗 URL   : {post_url}")
            return {
                'success': True,
                'post_id': data['id'],
                'url':     post_url,
                'title':   article['title'],
            }
        else:
            err = data.get('error', {}).get('message', str(data))
            print(f"   ❌ Blogger API error: {err}")
            return {'success': False, 'error': err}

    except Exception as e:
        print(f"   ❌ Blogger request failed: {e}")
        return {'success': False, 'error': str(e)}
