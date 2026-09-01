"""
🚀 MAIN - Redbubble Auto Poster
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
الصبح  (06:00–16:00 مصر) → Album جديد + يحفظ التصميم
المساء (20:00 مصر)       → Reels لنفس تصميم الصبح
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import os
import sys
import json
import time
from datetime import datetime

from config import (
    validate_config,
    REDBUBBLE_URL,
    REDBUBBLE_STORE_URL,
    POST_TYPE,
    MAX_IMAGES,
    LANGUAGE,
    STYLE,
)
from store_manager import (
    get_next_product_to_post,
    record_design_posted,
    get_store_stats,
    list_upcoming_designs,
)
from image_extractor import extract_all_images, smart_sort_images
from ai_generator import (
    generate_ai_caption, generate_design_hint, generate_video_script
)
from facebook_publisher import (
    post_album, post_reels
)
from instagram_poster import post_to_instagram
from pinterest_poster import post_to_pinterest
from blogger_poster import post_to_blogger
from video_creator import create_reels_video
from voice_generator import generate_voice, get_random_voice_style
from history_manager import record_post, get_stats, is_duplicate

# ──────────────────────────────────────────────────────────────
# 📁 ملف يحفظ تصميم الصبح عشان الريلز يلاقيه المساء
# ──────────────────────────────────────────────────────────────
TODAY_DESIGN_FILE = 'today_design.json'


def save_today_design(url: str, design_hint: str, images: list,
                      tags: list, description: str, collection: str):
    data = {
        'url':         url,
        'design_hint': design_hint,
        'images':      images[:10],
        'tags':        tags,
        'description': description,
        'collection':  collection,
        'saved_at':    datetime.now().isoformat(),
    }
    try:
        with open(TODAY_DESIGN_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"   💾 Today's design saved → {TODAY_DESIGN_FILE}")
    except Exception as e:
        print(f"   ⚠️ Could not save today design: {e}")


def load_today_design() -> dict | None:
    if not os.path.exists(TODAY_DESIGN_FILE):
        print(f"   ⚠️ {TODAY_DESIGN_FILE} not found — no morning album to reuse")
        return None
    try:
        with open(TODAY_DESIGN_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # تأكد إنه من نفس اليوم
        saved_at = datetime.fromisoformat(data.get('saved_at', '2000-01-01'))
        if saved_at.date() != datetime.now().date():
            print(f"   ⚠️ Today's design file is from {saved_at.date()} — too old")
            return None
        print(f"   ✅ Loaded today's design: {data.get('design_hint','?')[:50]}")
        return data
    except Exception as e:
        print(f"   ⚠️ Could not load today design: {e}")
        return None


# ──────────────────────────────────────────────────────────────
# ⏰ منطق الوقت — صبح أم مساء؟
# ──────────────────────────────────────────────────────────────

def get_egypt_hour() -> int:
    """الساعة الحالية بتوقيت مصر (UTC+2 شتاء / UTC+3 صيف)"""
    # GitHub Actions بتشتغل بـ UTC
    utc_hour = datetime.utcnow().hour
    # مصر UTC+2 (نستخدم +2 كـ safe default)
    egypt_hour = (utc_hour + 2) % 24
    return egypt_hour


def decide_post_mode() -> str:
    """
    يقرر نوع البوست بناءً على الوقت:
    - لو POST_TYPE محدد يدوياً → استخدمه
    - لو auto:
        06:00–17:59 مصر → album (صبح ونص النهار)
        18:00–23:59 مصر → reels (مساء)
        00:00–05:59 مصر → album (فجر — نادر)
    """
    # override يدوي
    if POST_TYPE and POST_TYPE.lower() not in ('auto', ''):
        print(f"   📌 Manual post type: {POST_TYPE.upper()}")
        return POST_TYPE.lower()

    egypt_hour = get_egypt_hour()
    print(f"   🕐 Egypt time: {egypt_hour:02d}:xx")

    if 6 <= egypt_hour <= 17:
        mode = 'album'
    elif 18 <= egypt_hour <= 23:
        mode = 'reels'
    else:
        mode = 'album'  # فجر → album

    print(f"   🎯 Auto mode: {mode.upper()} (Egypt hour={egypt_hour})")
    return mode


# ──────────────────────────────────────────────────────────────
# 📤 ALBUM POST (الصبح — تصميم جديد)
# ──────────────────────────────────────────────────────────────

def run_album_post(images, url, design_hint,
                   tags=None, collection='', description=''):
    caption = generate_ai_caption('album', url, design_hint)

    fb_images = images[:10]
    print(f"\n📸 Facebook Album: {len(fb_images)} photos")
    result = post_album(fb_images, caption)

    # Instagram
    try:
        post_to_instagram(image_urls=images[:10], caption=caption, post_type='album')
    except Exception as e:
        print(f"⚠️ Instagram album failed: {e}")

    # Pinterest
    try:
        post_to_pinterest(images, caption, url, design_hint)
    except Exception as e:
        print(f"⚠️ Pinterest failed: {e}")

    # Blogger
    try:
        post_to_blogger(design_hint, url, fb_images, tags or [], description, collection)
    except Exception as e:
        print(f"⚠️ Blogger failed: {e}")

    # ✅ احفظ التصميم عشان الريلز المساء
    save_today_design(url, design_hint, images, tags or [], description, collection)

    return result


# ──────────────────────────────────────────────────────────────
# 🎬 REELS POST (المساء — نفس تصميم الصبح)
# ──────────────────────────────────────────────────────────────

def run_reels_post(images, url, design_hint,
                   tags=None, collection='', description=''):
    print("\n🎬 Creating 15-second Reels...")

    # سكريبت قصير 15 ثانية
    script = generate_video_script(design_hint, url)
    print(f"📜 Script: {script[:100]}...")

    voice_style = get_random_voice_style()
    voice_path  = generate_voice(script, 'reels_voice.mp3', voice_style)
    if not voice_path:
        print("⚠️ Voice failed — video will be silent")

    # فيديو 15 ثانية
    video_path = create_reels_video(
        images[:8],
        voice_audio_path=voice_path,
        output_name='reels.mp4',
        duration=15,          # 15 ثانية بالظبط
    )

    if not video_path:
        print("⚠️ Reels creation failed — falling back to album")
        return run_album_post(images, url, design_hint, tags, collection, description)

    caption = generate_ai_caption('reels', url, design_hint)

    # Facebook Reels
    result = post_reels(video_path, caption)

    # Instagram Reels
    try:
        post_to_instagram(caption=caption, post_type='reels', video_path=video_path)
    except Exception as e:
        print(f"⚠️ Instagram reels failed: {e}")

    return result


# ──────────────────────────────────────────────────────────────
# 🔍 GET TARGET URL
# ──────────────────────────────────────────────────────────────

def get_target_url() -> dict:
    if REDBUBBLE_URL and REDBUBBLE_URL.strip():
        print(f"\n📌 Manual URL: {REDBUBBLE_URL[:70]}")
        return {'url': REDBUBBLE_URL.strip(), 'title': 'Manual', 'is_new': False}

    if not REDBUBBLE_STORE_URL:
        print("❌ REDBUBBLE_STORE_URL not set!")
        sys.exit(1)

    print("\n🤖 Auto-selecting next design...")
    product = get_next_product_to_post(REDBUBBLE_STORE_URL)
    if not product:
        print("❌ No product found")
        sys.exit(1)

    return product


# ──────────────────────────────────────────────────────────────
# 🖼️ EXTRACT IMAGES WITH FALLBACK
# ──────────────────────────────────────────────────────────────

def get_images_with_fallback(target: dict) -> tuple:
    from store_manager import url_key, record_failed_design

    url   = target['url']
    title = target.get('title', '')
    is_new = target.get('is_new', False)

    print(f"\n🔍 Extracting images from:\n   {url[:80]}")
    images = extract_all_images(url)

    # ✅ لو فشل الاستخراج، سجّله في failed_designs.json وجرّب تصاميم تانية
    #    (لغاية 4 محاولات) بدل ما ترجع لنفس التصميم اللي فشل
    tried_urls = {url_key(url)}
    attempts = 0
    max_attempts = 4

    if len(images) < 2 and not REDBUBBLE_URL:
        record_failed_design(url, title, reason=f'{len(images)} images found')

    while len(images) < 2 and not REDBUBBLE_URL and attempts < max_attempts:
        attempts += 1
        print(f"⚠️ Only {len(images)} images — trying another design ({attempts}/{max_attempts})...")
        next_product = get_next_product_to_post(REDBUBBLE_STORE_URL, exclude_urls=tried_urls)
        if not next_product:
            print("   ⚠️ No more designs available to try")
            break

        next_key = url_key(next_product['url'])
        if next_key in tried_urls:
            # احتياطي: لو رجّع نفس حاجة اتجربت قبل كده لأي سبب
            break

        tried_urls.add(next_key)
        url    = next_product['url']
        title  = next_product.get('title', '')
        is_new = next_product.get('is_new', False)
        print(f"\n🔍 Extracting images from:\n   {url[:80]}")
        images = extract_all_images(url)

        if len(images) < 2:
            record_failed_design(url, title, reason=f'{len(images)} images found')

    if len(images) < 2:
        print(f"❌ Not enough images ({len(images)}) after {attempts} attempt(s)")
        sys.exit(1)

    return images, url, title, is_new


# ──────────────────────────────────────────────────────────────
# 🚀 MAIN
# ──────────────────────────────────────────────────────────────

def main():
    validate_config()
    print(get_stats())
    print(get_store_stats())

    # ── تحديد الوضع: album أم reels ──────────────────────────
    mode = decide_post_mode()

    # ══════════════════════════════════════════════════════════
    # 🌅 ALBUM MODE — صبح: تصميم جديد
    # ══════════════════════════════════════════════════════════
    if mode == 'album':
        target = get_target_url()
        pre_url = target.get('url', '')

        # duplicate check — 12 ساعة (مش 24 عشان الريلز المساء مش يتأثر)
        if pre_url and is_duplicate(pre_url, 'album', cooldown_hours=12):
            print(f"\n⏸️  Already posted as album in last 12h — skipping")
            sys.exit(0)

        images, target_url, design_title, is_new = get_images_with_fallback(target)
        sorted_images = smart_sort_images(images, MAX_IMAGES)
        resolved_url  = getattr(extract_all_images, 'resolved_url', target_url)
        design_hint   = generate_design_hint(resolved_url, ' '.join(images[:5]))

        print(f"\n{'='*60}")
        print(f"🌅 MODE       : ALBUM (Morning)")
        print(f"🎨 Design     : {design_hint}")
        print(f"🔗 URL        : {target_url[:70]}")
        print(f"🆕 New Design : {'YES ✨' if is_new else 'No (repost)'}")
        print(f"📸 Images     : {len(sorted_images)}")
        print(f"🌍 Language   : {LANGUAGE}")
        print('='*60)

        result = run_album_post(
            sorted_images, target_url, design_hint,
            target.get('tags', []),
            target.get('collection', ''),
            target.get('description', ''),
        )

    # ══════════════════════════════════════════════════════════
    # 🌙 REELS MODE — مساء: نفس تصميم الصبح
    # ══════════════════════════════════════════════════════════
    elif mode == 'reels':
        today = load_today_design()

        if today:
            # ✅ استخدم تصميم الصبح
            target_url  = today['url']
            design_hint = today['design_hint']
            images      = today['images']
            tags        = today.get('tags', [])
            description = today.get('description', '')
            collection  = today.get('collection', '')
        else:
            # fallback: لو مفيش تصميم صبح → اختار جديد
            print("   ℹ️  No morning design found — selecting new design for reels")
            target = get_target_url()
            images, target_url, _, _ = get_images_with_fallback(target)
            images      = smart_sort_images(images, MAX_IMAGES)
            resolved_url = getattr(extract_all_images, 'resolved_url', target_url)
            design_hint = generate_design_hint(resolved_url, ' '.join(images[:5]))
            tags        = target.get('tags', [])
            description = target.get('description', '')
            collection  = target.get('collection', '')

        # duplicate check للريلز — 20 ساعة
        if is_duplicate(target_url, 'reels', cooldown_hours=20):
            print(f"\n⏸️  Already posted as reels today — skipping")
            sys.exit(0)

        print(f"\n{'='*60}")
        print(f"🌙 MODE       : REELS (Evening)")
        print(f"🎨 Design     : {design_hint}")
        print(f"🔗 URL        : {target_url[:70]}")
        print(f"📸 Images     : {len(images)}")
        print(f"🌍 Language   : {LANGUAGE}")
        print('='*60)

        result = run_reels_post(
            images, target_url, design_hint,
            tags, collection, description,
        )

    else:
        print(f"❌ Unknown mode: {mode}")
        sys.exit(1)

    # ── تسجيل النتيجة ────────────────────────────────────────
    print(f"\n{'='*60}")

    if isinstance(result, dict):
        if 'id' in result:
            post_id = result['id']
            print(f"🎉 SUCCESS! Post ID: {post_id}")
            record_post(target_url, mode, post_id, design_hint)
            if mode == 'album':
                record_design_posted(target_url, design_hint)
        elif 'error' in result:
            print(f"❌ Error: {result['error']}")

    # ── التصاميم الجاية ──────────────────────────────────────
    upcoming = list_upcoming_designs(3)
    if upcoming:
        print(f"\n🔮 Next designs in queue:")
        for i, d in enumerate(upcoming, 1):
            title  = d.get('title', 'Unknown')[:50]
            count  = d.get('post_count', 0)
            status = '🆕' if count == 0 else f'🔄 x{count}'
            print(f"   {i}. {status} {title}")

    print('='*60)


if __name__ == "__main__":
    main()
