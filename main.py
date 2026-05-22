"""
🚀 MAIN - Redbubble Auto Poster (Smart Edition)
- يختار التصميم الجاي تلقائياً من الستور
- يفضّل التصاميم الجديدة
- مش بيكرر نفس التصميم ورا بعضه
- تنوع في نوع البوست في كل مرة
- يدعم الإضافة اليدوية من manual_products.json
"""
import os
import sys
import time
import random

from config import (
    validate_config,
    REDBUBBLE_URL,          # اختياري - override يدوي
    REDBUBBLE_STORE_URL,    # رابط الستور للسكان الأوتوماتيك
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
    post_album, post_single_photo, post_text_only,
    post_link, post_video, post_reels
)
from instagram_poster import post_to_instagram
from pinterest_poster import post_to_pinterest
from blogger_poster import post_to_blogger
from video_creator import create_slideshow_video, create_reels_video
from voice_generator import generate_voice, get_random_voice_style
from templates import get_text_only_post, get_link_post
from history_manager import record_post, get_stats, is_duplicate


# ══════════════════════════════════════════════════════════════
# 🎲 SMART POST TYPE ROTATION (تنوع في المحتوى)
# ══════════════════════════════════════════════════════════════

# دوّرة album/reels فقط — أفضل للإنجيجمنت
POST_TYPE_CYCLE = [
    'album',   # ألبوم صور
    'reels',   # ريلز — إنجيجمنت عالي
    'album',   # ألبوم
    'reels',   # ريلز
    'album',   # ألبوم
    'reels',   # ريلز
    'album',   # ألبوم
    'reels',   # ريلز
]


def get_post_type_for_this_run() -> str:
    """
    اختيار نوع البوست الجاي بذكاء.
    لو POST_TYPE=auto → يدور على الدوّرة
    لو تحديد يدوي → يستخدمه
    """
    if POST_TYPE and POST_TYPE.lower() not in ('auto', ''):
        return POST_TYPE.lower()

    # استخدام index من environment variable
    # يتحدث كل run في الـ workflow
    idx = int(os.getenv('POST_ROTATION_INDEX', '0'))
    chosen = POST_TYPE_CYCLE[idx % len(POST_TYPE_CYCLE)]
    print(f"🎲 Auto post type (index {idx}): {chosen.upper()}")
    return chosen


# ══════════════════════════════════════════════════════════════
# 📤 POST FUNCTIONS
# ══════════════════════════════════════════════════════════════

def run_album_post(images, url, design_hint, tags=None, collection='', description=''):
    caption = generate_ai_caption('album', url, design_hint)

    # Facebook: 30 صورة كاملة
    fb_images = images[:10]
    print(f"\n📸 Facebook Album: {len(fb_images)} photos")
    result = post_album(fb_images, caption)

    # Instagram: حد أقصى 10 صور
    try:
        post_to_instagram(image_urls=images[:10], caption=caption, post_type='album')
    except Exception as e:
        print(f"⚠️ Instagram album failed: {e}")

    # Pinterest
    try:
        post_to_pinterest(images, caption, url, design_hint)
    except Exception as e:
        print(f"⚠️ Pinterest failed: {e}")

    # Blogger SEO Article
    try:
        post_to_blogger(design_hint, url, fb_images, tags or [], description, collection)
    except Exception as e:
        print(f"⚠️ Blogger failed: {e}")

    return result


def run_single_post(images, url, design_hint):
    caption = generate_ai_caption('single', url, design_hint)
    result = post_single_photo(images[0], caption)

    try:
        post_to_instagram(image_urls=images, caption=caption, post_type='single')
    except Exception as e:
        print(f"⚠️ Instagram single failed: {e}")

    try:
        post_to_pinterest(images[:1], caption, url, design_hint)
    except Exception as e:
        print(f"⚠️ Pinterest failed: {e}")

    return result


def run_link_post(url):
    message = get_link_post(url)
    return post_link(message, url)


def run_text_post(url):
    message = get_text_only_post()
    return post_text_only(message)


def run_video_post(images, url, design_hint):
    print("\n🎬 Generating video with voice...")
    script = generate_video_script(design_hint, url)
    print(f"📜 Script: {script[:120]}...")

    voice_style = get_random_voice_style()
    voice_path = generate_voice(script, 'video_voice.mp3', voice_style)
    if not voice_path:
        print("⚠️ Voice failed, video will be silent")

    video_path = create_slideshow_video(
        images[:10],
        voice_audio_path=voice_path,
        output_name='slideshow.mp4'
    )
    if not video_path:
        print("⚠️ Video creation failed, falling back to album post")
        return run_album_post(images, url, design_hint)

    caption = generate_ai_caption('video', url, design_hint)
    result = post_video(video_path, caption)

    try:
        post_to_instagram(caption=caption, post_type='video', video_path=video_path)
    except Exception as e:
        print(f"⚠️ Instagram video failed: {e}")

    return result


def run_reels_post(images, url, design_hint, tags=None, collection='', description=''):
    print("\n🎬 Generating Reels with voice...")
    script = generate_video_script(design_hint, url)

    voice_style = get_random_voice_style()
    voice_path = generate_voice(script, 'reels_voice.mp3', voice_style)

    video_path = create_reels_video(
        images[:8],
        voice_audio_path=voice_path,
        output_name='reels.mp4'
    )
    if not video_path:
        print("⚠️ Reels creation failed, falling back to album post")
        return run_album_post(images, url, design_hint, tags)

    caption = generate_ai_caption('reels', url, design_hint)
    result = post_reels(video_path, caption)

    try:
        post_to_instagram(caption=caption, post_type='reels', video_path=video_path)
    except Exception as e:
        print(f"⚠️ Instagram reels failed: {e}")

    # Blogger SEO Article
    try:
        post_to_blogger(design_hint, url, images, tags or [], description, collection)
    except Exception as e:
        print(f"⚠️ Blogger failed: {e}")

    return result


# ══════════════════════════════════════════════════════════════
# 🔍 GET TARGET URL (الاختيار الذكي للتصميم)
# ══════════════════════════════════════════════════════════════

def get_target_url() -> dict:
    """
    اختيار التصميم اللي هيتنشر:
    1. لو في REDBUBBLE_URL يدوي → استخدمه
    2. لو في REDBUBBLE_STORE_URL → سكان الستور واختر الأذكى
    3. لو ما فيش → خطأ

    بيرجع: {'url': str, 'title': str, 'is_new': bool}
    """
    # ── Manual override ──────────────────────────────────────
    if REDBUBBLE_URL and REDBUBBLE_URL.strip():
        print(f"\n📌 Manual URL override: {REDBUBBLE_URL[:70]}")
        return {
            'url': REDBUBBLE_URL.strip(),
            'title': 'Manual',
            'is_new': False,
        }

    # ── Auto selection ───────────────────────────────────────
    if not REDBUBBLE_STORE_URL:
        print("❌ Neither REDBUBBLE_URL nor REDBUBBLE_STORE_URL is set!")
        print("   Add REDBUBBLE_STORE_URL to your GitHub Secrets")
        sys.exit(1)

    print(f"\n🤖 Auto-selecting next design from store...")
    product = get_next_product_to_post(REDBUBBLE_STORE_URL)

    if not product:
        print("❌ No product found to post")
        sys.exit(1)

    return product


# ══════════════════════════════════════════════════════════════
# 🖼️ EXTRACT IMAGES WITH FALLBACK (مع Fallback لتصميم تاني)
# ══════════════════════════════════════════════════════════════

def get_images_with_fallback(target: dict) -> tuple:
    """
    استخراج الصور من URL، لو ما فيش يجرب التصميم الجاي.
    بيرجع: (images, url, title, is_new)
    """
    url = target['url']
    title = target.get('title', '')
    is_new = target.get('is_new', False)

    print(f"\n🔍 Extracting images from:")
    print(f"   {url[:80]}")

    images = extract_all_images(url)

    # لو ما لقيناش صور كافية → جرب التاني
    if len(images) < 2 and not REDBUBBLE_URL:
        print(f"⚠️ Not enough images ({len(images)}) — trying next design...")
        next_product = get_next_product_to_post(REDBUBBLE_STORE_URL)
        if next_product and next_product['url'] != url:
            url = next_product['url']
            title = next_product.get('title', '')
            is_new = next_product.get('is_new', False)
            images = extract_all_images(url)

    if len(images) < 2:
        print(f"❌ Not enough images ({len(images)}) even after fallback")
        sys.exit(1)

    return images, url, title, is_new


# ══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ══════════════════════════════════════════════════════════════

def main():
    validate_config()

    print(get_stats())
    print(get_store_stats())

    # ── اختيار التصميم ──────────────────────────────────────
    target = get_target_url()

    # ✅ التحقق من التكرار قبل أي حاجة تانية
    active_post_type_check = get_post_type_for_this_run()
    pre_url = target.get('url', '')
    if pre_url and is_duplicate(pre_url, active_post_type_check, cooldown_hours=24):
        print(f"\n⏸️  Design already posted within 24h — skipping this run")
        print(f"   URL: {pre_url[:70]}")
        print("=" * 60)
        sys.exit(0)

    # ── استخراج الصور ───────────────────────────────────────
    images, target_url, design_title, is_new = get_images_with_fallback(target)
    sorted_images = smart_sort_images(images, MAX_IMAGES)

    # ── تحليل التصميم بالـ AI ────────────────────────────────
    # استخدم الـ /i/ URL الحقيقي لاستخراج اسم التصميم بدقة
    resolved_url = getattr(extract_all_images, 'resolved_url', target_url)
    design_hint = generate_design_hint(resolved_url, ' '.join(images[:5]))

    # ── اختيار نوع البوست ───────────────────────────────────
    active_post_type = get_post_type_for_this_run()

    print(f"\n{'=' * 60}")
    print(f"🎨 Design     : {design_hint}")
    print(f"🔗 URL        : {target_url[:70]}")
    print(f"🎯 Post Type  : {active_post_type.upper()}")
    print(f"🆕 New Design : {'YES ✨' if is_new else 'No (repost)'}")
    print(f"📸 Images     : {len(sorted_images)}")
    print(f"🌍 Language   : {LANGUAGE}")
    print(f"🎨 Style      : {STYLE}")
    print('=' * 60)

    # ── التوجيه لنوع البوست ─────────────────────────────────
    result = None

    if active_post_type in ('album', 'carousel'):
        result = run_album_post(sorted_images, target_url, design_hint, target.get('tags', []), target.get('collection', ''), target.get('description', ''))

    elif active_post_type == 'single':
        result = run_single_post(sorted_images, target_url, design_hint)

    elif active_post_type == 'link':
        result = run_link_post(target_url)

    elif active_post_type == 'text':
        result = run_text_post(target_url)

    elif active_post_type == 'video':
        result = run_video_post(sorted_images, target_url, design_hint)

    elif active_post_type == 'reels':
        result = run_reels_post(sorted_images, target_url, design_hint, target.get('tags', []), target.get('collection', ''), target.get('description', ''))

    elif active_post_type == 'all':
        # كل الأنواع
        results = {}
        for ptype, fn in [
            ('album', lambda: run_album_post(sorted_images, target_url, design_hint, target.get('tags', []), target.get('collection', ''), target.get('description', ''))),
            ('single', lambda: run_single_post(sorted_images, target_url, design_hint)),
            ('link', lambda: run_link_post(target_url)),
        ]:
            print(f"\n▶ Running {ptype}...")
            results[ptype] = fn()
            time.sleep(10)
        result = results
    else:
        result = run_album_post(sorted_images, target_url, design_hint, target.get('tags', []))

    # ── تسجيل النتيجة ───────────────────────────────────────
    print(f"\n{'=' * 60}")

    if isinstance(result, dict):
        if 'id' in result:
            post_id = result['id']
            print(f"🎉 SUCCESS! Post ID: {post_id}")
            # تسجيل في الهيستوريين
            record_post(target_url, active_post_type, post_id, design_hint)
            record_design_posted(target_url, design_title or design_hint)

        elif active_post_type == 'all':
            success = sum(1 for r in result.values() if isinstance(r, dict) and 'id' in r)
            print(f"🎉 ALL DONE! {success}/{len(result)} succeeded")
            for ptype, res in result.items():
                if isinstance(res, dict) and 'id' in res:
                    print(f"   ✅ {ptype}: {res['id']}")
                    record_post(target_url, ptype, res['id'], design_hint)
                else:
                    err = res.get('error', '?') if isinstance(res, dict) else '?'
                    print(f"   ❌ {ptype}: {err}")
            record_design_posted(target_url, design_title or design_hint)

        elif 'error' in result:
            print(f"❌ Error: {result['error']}")

    # ── عرض التصاميم الجاية ──────────────────────────────────
    upcoming = list_upcoming_designs(3)
    if upcoming:
        print(f"\n🔮 Next designs in queue:")
        for i, d in enumerate(upcoming, 1):
            title = d.get('title', 'Unknown')[:50]
            count = d.get('post_count', 0)
            status = '🆕' if count == 0 else f'🔄 x{count}'
            print(f"   {i}. {status} {title}")

    print('=' * 60)


if __name__ == "__main__":
    main()
