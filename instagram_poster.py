"""
📸 Instagram Poster v2
Posts photos, videos, carousels & reels to Instagram
via Facebook Graph API
"""
import requests
import time
import os

INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID', '17841477368001153')
INSTAGRAM_TOKEN   = os.getenv('INSTAGRAM_TOKEN', os.getenv('FB_TOKEN', ''))

IG_API = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}"


# ══════════════════════════════════════════════════════════════
# 🔧 HELPERS
# ══════════════════════════════════════════════════════════════

def _publish(container_id):
    """نشر أي container بعد إنشاؤه"""
    try:
        r = requests.post(
            f"{IG_API}/media_publish",
            data={'creation_id': container_id, 'access_token': INSTAGRAM_TOKEN},
            timeout=30
        )
        result = r.json()
        if 'id' in result:
            return result['id']
        print(f"❌ IG Publish Error: {result.get('error', {}).get('message', str(result))}")
        return None
    except Exception as e:
        print(f"❌ IG Publish exception: {e}")
        return None


def upload_video_to_public_url(video_path):
    """
    رفع الفيديو على سيرفر مؤقت عشان Instagram يقدر يوصله
    بيستخدم transfer.sh (مجاني)
    """
    try:
        filename = os.path.basename(video_path)
        print(f"   📤 Uploading video to temp server...")
        with open(video_path, 'rb') as f:
            r = requests.put(
                f"https://transfer.sh/{filename}",
                data=f,
                timeout=120
            )
        if r.status_code == 200:
            url = r.text.strip()
            print(f"   ✅ Video uploaded: {url}")
            return url
        else:
            print(f"   ❌ Upload failed: {r.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ Upload exception: {e}")
        return None


def check_container_status(container_id, max_wait=120):
    """انتظار اكتمال معالجة الفيديو"""
    print(f"   ⏳ Waiting for video processing...")
    for i in range(max_wait // 10):
        time.sleep(10)
        try:
            r = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={'fields': 'status_code', 'access_token': INSTAGRAM_TOKEN},
                timeout=15
            )
            status = r.json().get('status_code', '')
            print(f"   Status: {status}")
            if status == 'FINISHED':
                return True
            elif status == 'ERROR':
                return False
        except:
            pass
    return False


# ══════════════════════════════════════════════════════════════
# 📸 IMAGE POSTS
# ══════════════════════════════════════════════════════════════

def post_single_image(image_url, caption):
    """نشر صورة واحدة"""
    try:
        r = requests.post(
            f"{IG_API}/media",
            data={
                'image_url': image_url,
                'caption': caption[:2200],
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=30
        )
        result = r.json()
        container_id = result.get('id')
        if not container_id:
            print(f"❌ IG Single Error: {result.get('error', {}).get('message', str(result))}")
            return None

        time.sleep(5)
        return _publish(container_id)

    except Exception as e:
        print(f"❌ IG Single exception: {e}")
        return None


def post_carousel(image_urls, caption):
    """نشر carousel بـ 10 صور"""
    try:
        children = []
        for img_url in image_urls[:10]:
            r = requests.post(
                f"{IG_API}/media",
                data={
                    'image_url': img_url,
                    'is_carousel_item': 'true',
                    'access_token': INSTAGRAM_TOKEN
                },
                timeout=30
            )
            result = r.json()
            if 'id' in result:
                children.append(result['id'])
            time.sleep(1)

        if not children:
            return None

        r = requests.post(
            f"{IG_API}/media",
            data={
                'media_type': 'CAROUSEL',
                'caption': caption[:2200],
                'children': ','.join(children),
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=30
        )
        container_id = r.json().get('id')
        if not container_id:
            return None

        time.sleep(5)
        return _publish(container_id)

    except Exception as e:
        print(f"❌ IG Carousel exception: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 🎬 VIDEO POSTS
# ══════════════════════════════════════════════════════════════

def post_video_to_ig(video_path, caption):
    """نشر فيديو عادي على Instagram"""
    try:
        # رفع الفيديو على سيرفر مؤقت
        video_url = upload_video_to_public_url(video_path)
        if not video_url:
            return None

        # إنشاء container
        r = requests.post(
            f"{IG_API}/media",
            data={
                'media_type': 'VIDEO',
                'video_url': video_url,
                'caption': caption[:2200],
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=30
        )
        result = r.json()
        container_id = result.get('id')
        if not container_id:
            print(f"❌ IG Video Error: {result.get('error', {}).get('message', str(result))}")
            return None

        # انتظار المعالجة
        if not check_container_status(container_id):
            print("❌ IG Video: Processing failed")
            return None

        return _publish(container_id)

    except Exception as e:
        print(f"❌ IG Video exception: {e}")
        return None


def post_reels_to_ig(video_path, caption):
    """نشر Reels على Instagram"""
    try:
        # رفع الفيديو على سيرفر مؤقت
        video_url = upload_video_to_public_url(video_path)
        if not video_url:
            return None

        # إنشاء Reels container
        r = requests.post(
            f"{IG_API}/media",
            data={
                'media_type': 'REELS',
                'video_url': video_url,
                'caption': caption[:2200],
                'share_to_feed': 'true',
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=30
        )
        result = r.json()
        container_id = result.get('id')
        if not container_id:
            print(f"❌ IG Reels Error: {result.get('error', {}).get('message', str(result))}")
            return None

        # انتظار المعالجة
        if not check_container_status(container_id, max_wait=180):
            print("❌ IG Reels: Processing failed")
            return None

        return _publish(container_id)

    except Exception as e:
        print(f"❌ IG Reels exception: {e}")
        return None


# ══════════════════════════════════════════════════════════════
# 🚀 MAIN FUNCTION
# ══════════════════════════════════════════════════════════════

def post_to_instagram(image_urls=None, caption='', post_type='single',
                      video_path=None):
    """
    النشر على Instagram - كل الأنواع
    post_type: single | album | video | reels
    """
    if not INSTAGRAM_TOKEN:
        print("⚠️ INSTAGRAM_TOKEN not set - skipping Instagram")
        return None

    if not INSTAGRAM_USER_ID:
        print("⚠️ INSTAGRAM_USER_ID not set - skipping Instagram")
        return None

    print(f"\n📸 Posting to Instagram ({post_type})...")

    # ── Video / Reels ─────────────────────────────────────────
    if post_type == 'reels' and video_path:
        post_id = post_reels_to_ig(video_path, caption)

    elif post_type == 'video' and video_path:
        post_id = post_video_to_ig(video_path, caption)

    # ── Album / Carousel ──────────────────────────────────────
    elif post_type == 'album' and image_urls and len(image_urls) > 1:
        post_id = post_carousel(image_urls[:10], caption)

    # ── Single Image ──────────────────────────────────────────
    elif image_urls:
        post_id = post_single_image(image_urls[0], caption)

    else:
        print("❌ No content provided for Instagram")
        return None

    if post_id:
        print(f"   ✅ Instagram posted! ID: {post_id}")
    else:
        print("   ❌ Instagram: Failed")

    return post_id
