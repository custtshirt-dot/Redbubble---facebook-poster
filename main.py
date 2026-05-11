"""
🚀 MAIN - Redbubble Auto Poster
Supports: Facebook + Instagram (Photo/Video/Reels) + Pinterest
"""
import sys
import time
from config import (
    validate_config, REDBUBBLE_URL, POST_TYPE, MAX_IMAGES
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
from video_creator import create_slideshow_video, create_reels_video
from voice_generator import generate_voice, get_random_voice_style
from templates import get_text_only_post, get_link_post
from history_manager import is_duplicate, record_post, get_stats


# ══════════════════════════════════════════════════════════════
# POST FUNCTIONS
# ══════════════════════════════════════════════════════════════

def run_album_post(images, url, design_hint):
    caption = generate_ai_caption('album', url, design_hint)

    # Facebook album
    result = post_album(images, caption)

    # Instagram carousel (10 صور بس)
    post_to_instagram(
        image_urls=images[:10],
        caption=caption,
        post_type='album'
    )

    # Pinterest
    post_to_pinterest(images, caption, url, design_hint)

    return result


def run_single_post(images, url, design_hint):
    caption = generate_ai_caption('single', url, design_hint)

    # Facebook
    result = post_single_photo(images[0], caption)

    # Instagram single
    post_to_instagram(
        image_urls=images,
        caption=caption,
        post_type='single'
    )

    # Pinterest
    post_to_pinterest(images[:1], caption, url, design_hint)

    return result


def run_text_post(url):
    message = get_text_only_post()
    return post_text_only(message)


def run_link_post(url):
    message = get_link_post(url)
    return post_link(message, url)


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
        return {'error': 'Video creation failed'}

    caption = generate_ai_caption('video', url, design_hint)

    # Facebook video
    result = post_video(video_path, caption)

    # Instagram video ✅ جديد
    print("\n📸 Posting video to Instagram...")
    post_to_instagram(
        caption=caption,
        post_type='video',
        video_path=video_path
    )

    return result


def run_reels_post(images, url, design_hint):
    print("\n🎬 Generating Reels with voice...")
    script = generate_video_script(design_hint, url)
    print(f"📜 Script: {script[:120]}...")

    voice_style = get_random_voice_style()
    voice_path = generate_voice(script, 'reels_voice.mp3', voice_style)
    if not voice_path:
        print("⚠️ Voice failed, reels will be silent")

    video_path = create_reels_video(
        images[:8],
        voice_audio_path=voice_path,
        output_name='reels.mp4'
    )
    if not video_path:
        return {'error': 'Reels creation failed'}

    caption = generate_ai_caption('reels', url, design_hint)

    # Facebook reels
    result = post_reels(video_path, caption)

    # Instagram reels ✅ جديد
    print("\n📸 Posting reels to Instagram...")
    post_to_instagram(
        caption=caption,
        post_type='reels',
        video_path=video_path
    )

    return result


def run_all_types(images, url, design_hint):
    print("\n" + "=" * 60)
    print("🚀 RUNNING ALL POST TYPES")
    print("=" * 60)
    results = {}

    print("\n[1/4] 📸 Album (FB + IG + Pinterest)...")
    results['album'] = run_album_post(images, url, design_hint)
    time.sleep(15)

    print("\n[2/4] 🖼️ Single (FB + IG)...")
    results['single'] = run_single_post(images, url, design_hint)
    time.sleep(15)

    print("\n[3/4] 💬 Text (FB)...")
    results['text'] = run_text_post(url)
    time.sleep(15)

    print("\n[4/4] 🔗 Link (FB)...")
    results['link'] = run_link_post(url)

    return results


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    validate_config()
    print(get_stats())

    if is_duplicate(REDBUBBLE_URL, POST_TYPE):
        print(f"\n🛑 STOPPED: Already posted recently")
        sys.exit(0)

    images = extract_all_images(REDBUBBLE_URL)
    if len(images) < 3:
        print("❌ Not enough images found")
        sys.exit(1)

    sorted_images = smart_sort_images(images, MAX_IMAGES)
    design_hint = generate_design_hint(REDBUBBLE_URL, ' '.join(images[:5]))

    print(f"🎨 Design: {design_hint}")
    print(f"🎯 Type: {POST_TYPE.upper()}")
    print(f"📱 Platforms: Facebook ✅ | Instagram ✅ | Pinterest ✅")

    # ── Router ────────────────────────────────────────────────
    if POST_TYPE == 'album':
        result = run_album_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'single':
        result = run_single_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'carousel':
        result = run_album_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'text':
        result = run_text_post(REDBUBBLE_URL)
    elif POST_TYPE == 'link':
        result = run_link_post(REDBUBBLE_URL)
    elif POST_TYPE == 'video':
        result = run_video_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'reels':
        result = run_reels_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'all':
        result = run_all_types(sorted_images, REDBUBBLE_URL, design_hint)
    else:
        print(f"❌ Unknown post type: {POST_TYPE}")
        sys.exit(1)

    # ── Results ───────────────────────────────────────────────
    print("\n" + "=" * 60)
    if isinstance(result, dict):
        if 'id' in result:
            print(f"🎉 SUCCESS! Post ID: {result['id']}")
            record_post(REDBUBBLE_URL, POST_TYPE, result['id'], design_hint)
        elif POST_TYPE == 'all':
            success = sum(1 for r in result.values()
                         if isinstance(r, dict) and 'id' in r)
            print(f"🎉 ALL DONE! {success}/{len(result)} succeeded")
            for ptype, res in result.items():
                if isinstance(res, dict) and 'id' in res:
                    print(f"   ✅ {ptype}: {res['id']}")
                    record_post(REDBUBBLE_URL, ptype, res['id'], design_hint)
                else:
                    err = res.get('error', '?') if isinstance(res, dict) else '?'
                    print(f"   ❌ {ptype}: {err}")
        elif 'error' in result:
            print(f"❌ Error: {result['error']}")
    print("=" * 60)


if __name__ == "__main__":
    main()
