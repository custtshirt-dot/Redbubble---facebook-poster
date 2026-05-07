"""
🚀 Redbubble Auto Publisher Pro
Main entry point - publish all content types
"""
import sys
import time
from image_extractor import extract_all_images, smart_sort_images
from ai_generator import generate_content
from facebook_publisher import (
    post_album, post_single_photo, post_carousel,
    post_video, post_reels, post_text_only,
    post_link, post_story_photo
)
from video_creator import create_reels, create_video_slideshow


def print_banner():
    print("\n" + "=" * 80)
    print("    🚀 REDBUBBLE AUTO PUBLISHER PRO - ALL CONTENT TYPES")
    print("    💎 Powered by Groq AI + MoviePy")
    print("=" * 80)


def get_url_from_user():
    """صندوق إدخال الرابط"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + " " * 20 + "📦 PASTE YOUR REDBUBBLE URL HERE" + " " * 26 + "║")
    print("╚" + "═" * 78 + "╝")
    print("\n┌" + "─" * 78 + "┐")
    url = input("│ 🔗 URL: ").strip()
    print("└" + "─" * 78 + "┘\n")
    return url


def show_menu():
    print("\n" + "=" * 80)
    print("📋 CHOOSE CONTENT TYPE TO PUBLISH:")
    print("=" * 80)
    print("  1️⃣  Album Post (multiple images)")
    print("  2️⃣  Single Photo Post")
    print("  3️⃣  Carousel Post (storytelling)")
    print("  4️⃣  Reels (9:16 vertical video)")
    print("  5️⃣  Video Slideshow (16:9)")
    print("  6️⃣  Text-Only Post")
    print("  7️⃣  Link Post (with preview)")
    print("  8️⃣  Story (24h)")
    print("  9️⃣  🔥 PUBLISH ALL TYPES (the bomb!)")
    print("  0️⃣  Exit")
    print("=" * 80)
    return input("\n👉 Your choice: ").strip()


def publish_album(url, images):
    caption = generate_content("album", url)
    result = post_album(images[:30], caption)
    print_result("Album", result)


def publish_single(url, images):
    caption = generate_content("single", url)
    result = post_single_photo(images[0], caption)
    print_result("Single Photo", result)


def publish_carousel(url, images):
    caption = generate_content("carousel", url)
    result = post_carousel(images[:10], caption)
    print_result("Carousel", result)


def publish_reels(url, images):
    video_path = create_reels(images[:15])
    if video_path:
        caption = generate_content("reels", url)
        result = post_reels(video_path, caption)
        print_result("Reels", result)


def publish_video(url, images):
    video_path = create_video_slideshow(images[:20])
    if video_path:
        caption = generate_content("video", url)
        result = post_video(video_path, caption)
        print_result("Video", result)


def publish_text(url):
    message = generate_content("text", url)
    result = post_text_only(message)
    print_result("Text Post", result)


def publish_link(url):
    message = generate_content("link", url)
    result = post_link(url, message)
    print_result("Link Post", result)


def publish_story(images):
    result = post_story_photo(images[0])
    print_result("Story", result)


def publish_all(url, images):
    """🔥 نشر كل أنواع المحتوى"""
    print("\n" + "🔥" * 40)
    print("  PUBLISHING ALL CONTENT TYPES - THE FULL BOMB! 💣")
    print("🔥" * 40)
    
    actions = [
        ("Album", lambda: publish_album(url, images)),
        ("Single Photo", lambda: publish_single(url, images)),
        ("Carousel", lambda: publish_carousel(url, images)),
        ("Text Post", lambda: publish_text(url)),
        ("Link Post", lambda: publish_link(url)),
        ("Story", lambda: publish_story(images)),
        ("Video", lambda: publish_video(url, images)),
        ("Reels", lambda: publish_reels(url, images)),
    ]
    
    for name, action in actions:
        try:
            print(f"\n{'─' * 80}\n▶️  Publishing: {name}\n{'─' * 80}")
            action()
            time.sleep(5)  # تأخير بين البوستات لتجنب الـ rate limit
        except Exception as e:
            print(f"❌ {name} failed: {e}")
    
    print("\n" + "🎉" * 40)
    print("  ALL CONTENT PUBLISHED SUCCESSFULLY! 🎉")
    print("🎉" * 40)


def print_result(post_type, result):
    if result and ('id' in result or 'post_id' in result):
        post_id = result.get('id') or result.get('post_id')
        print(f"\n✅ {post_type} published! ID: {post_id}")
    else:
        print(f"\n⚠️ {post_type} result: {result}")


def main():
    print_banner()
    
    # 📦 إدخال الرابط
    url = get_url_from_user()
    if not url:
        print("❌ No URL provided.")
        return
    
    # 🖼️ استخراج الصور
    images = extract_all_images(url)
    if len(images) < 3:
        print("❌ Not enough images found.")
        return
    
    # 🎯 ترتيب ذكي
    images = smart_sort_images(images)
    
    # 📋 القائمة
    while True:
        choice = show_menu()
        
        if choice == "1":
            publish_album(url, images)
        elif choice == "2":
            publish_single(url, images)
        elif choice == "3":
            publish_carousel(url, images)
        elif choice == "4":
            publish_reels(url, images)
        elif choice == "5":
            publish_video(url, images)
        elif choice == "6":
            publish_text(url)
        elif choice == "7":
            publish_link(url)
        elif choice == "8":
            publish_story(images)
        elif choice == "9":
            publish_all(url, images)
        elif choice == "0":
            print("\n👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice")
        
        again = input("\n🔄 Publish another? (y/n): ").strip().lower()
        if again != 'y':
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Stopped by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
