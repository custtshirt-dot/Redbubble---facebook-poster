"""
🚀 MAIN - Redbubble Auto Poster
"""
import sys
import time
from config import (
    validate_config, REDBUBBLE_URL, POST_TYPE, MAX_IMAGES
)
from image_extractor import extract_all_images, smart_sort_images
from ai_generator import generate_ai_caption, generate_design_hint
from facebook_publisher import (
    post_album, post_single_photo, post_text_only,
    post_link, post_video, post_reels
)
from video_creator import create_slideshow_video, create_reels_video
from templates import get_text_only_post, get_link_post


def run_album_post(images, url, design_hint):
    """Album post with all images"""
    caption = generate_ai_caption('album', url, design_hint)
    result = post_album(images, caption)
    return result


def run_single_post(images, url, design_hint):
    """Single photo post"""
    caption = generate_ai_caption('single', url, design_hint)
    result = post_single_photo(images[0], caption)
    return result


def run_text_post(url):
    """Text-only engagement post"""
    message = get_text_only_post()
    result = post_text_only(message)
    return result


def run_link_post(url):
    """Link post"""
    message = get_link_post(url)
    result = post_link(message, url)
    return result


def run_video_post(images, url, design_hint):
    """Video post"""
    video_path = create_slideshow_video(images[:10])
    if not video_path:
        return {'error': 'Video creation failed'}
    
    caption = generate_ai_caption('video', url, design_hint)
    result = post_video(video_path, caption)
    return result


def run_reels_post(images, url, design_hint):
    """Reels post"""
    video_path = create_reels_video(images[:8])
    if not video_path:
        return {'error': 'Reels creation failed'}
    
    caption = generate_ai_caption('reels', url, design_hint)
    result = post_reels(video_path, caption)
    return result


def run_all_types(images, url, design_hint):
    """Run all post types one by one"""
    print("\n" + "=" * 60)
    print("🚀 RUNNING ALL POST TYPES")
    print("=" * 60)
    
    results = {}
    
    print("\n[1/6] 📸 Album post...")
    results['album'] = run_album_post(images, url, design_hint)
    time.sleep(5)
    
    print("\n[2/6] 🖼️ Single photo...")
    results['single'] = run_single_post(images, url, design_hint)
    time.sleep(5)
    
    print("\n[3/6] 💬 Text post...")
    results['text'] = run_text_post(url)
    time.sleep(5)
    
    print("\n[4/6] 🔗 Link post...")
    results['link'] = run_link_post(url)
    time.sleep(5)
    
    print("\n[5/6] 🎬 Video post...")
    results['video'] = run_video_post(images, url, design_hint)
    time.sleep(5)
    
    print("\n[6/6] 🎥 Reels post...")
    results['reels'] = run_reels_post(images, url, design_hint)
    
    return results


def main():
    # Validate configuration
    validate_config()
    
    # Extract images
    images = extract_all_images(REDBUBBLE_URL)
    if len(images) < 3:
        print("❌ Not enough images found")
        sys.exit(1)
    
    # Smart sort (priority products first)
    sorted_images = smart_sort_images(images, MAX_IMAGES)
    
    # Detect design type from images
    design_hint = generate_design_hint(' '.join(images[:3]))
    print(f"🎨 Design detected: {design_hint}")
    
    # Run based on POST_TYPE
    print(f"\n🎯 Running: {POST_TYPE.upper()}")
    
    if POST_TYPE == 'album':
        result = run_album_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'single':
        result = run_single_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'text':
        result = run_text_post(REDBUBBLE_URL)
    elif POST_TYPE == 'link':
        result = run_link_post(REDBUBBLE_URL)
    elif POST_TYPE == 'video':
        result = run_video_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'reels':
        result = run_reels_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'carousel':
        result = run_album_post(sorted_images, REDBUBBLE_URL, design_hint)
    elif POST_TYPE == 'all':
        result = run_all_types(sorted_images, REDBUBBLE_URL, design_hint)
    else:
        print(f"❌ Unknown post type: {POST_TYPE}")
        sys.exit(1)
    
    # Print result
    print("\n" + "=" * 60)
    if isinstance(result, dict) and 'id' in result:
        print(f"🎉 SUCCESS! Post ID: {result['id']}")
    elif isinstance(result, dict) and 'error' in result:
        print(f"❌ Error: {result['error']}")
    else:
        print(f"📊 Result: {result}")
    print("=" * 60)


if __name__ == "__main__":
    main()
