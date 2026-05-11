"""
📸 Instagram Poster v3
- صور + فيديو + ريلز
- رفع فيديو مباشر بدون سيرفر خارجي
"""
import requests
import time
import os
import json

INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID', '17841477368001153')
INSTAGRAM_TOKEN   = os.getenv('INSTAGRAM_TOKEN', os.getenv('FB_TOKEN', ''))
IG_API = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}"


def _publish(container_id):
    """نشر container"""
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


def upload_video_transfer(video_path):
    """رفع فيديو على transfer.sh"""
    try:
        filename = os.path.basename(video_path)
        print(f"   📤 Uploading to transfer.sh...")
        with open(video_path, 'rb') as f:
            r = requests.put(
                f"https://transfer.sh/{filename}",
                data=f,
                headers={'Max-Days': '1'},
                timeout=120
            )
        if r.status_code == 200:
            url = r.text.strip()
            print(f"   ✅ Uploaded: {url}")
            return url
    except Exception as e:
        print(f"   ❌ transfer.sh failed: {e}")

    # Fallback: 0x0.st
    try:
        print(f"   📤 Trying 0x0.st...")
        with open(video_path, 'rb') as f:
            r = requests.post(
                'https://0x0.st',
                files={'file': f},
                timeout=120
            )
        if r.status_code == 200:
            url = r.text.strip()
            print(f"   ✅ Uploaded: {url}")
            return url
    except Exception as e:
        print(f"   ❌ 0x0.st failed: {e}")

    return None


def wait_for_processing(container_id, max_wait=300):
    """انتظار معالجة الفيديو"""
    print(f"   ⏳ Processing video...")
    for i in range(max_wait // 15):
        time.sleep(15)
        try:
            r = requests.get(
                f"https://graph.facebook.com/v19.0/{container_id}",
                params={
                    'fields': 'status_code,status',
                    'access_token': INSTAGRAM_TOKEN
                },
                timeout=15
            )
            data = r.json()
            status = data.get('status_code', '')
            print(f"   [{(i+1)*15}s] Status: {status}")

            if status == 'FINISHED':
                return True
            elif status in ['ERROR', 'EXPIRED']:
                print(f"   ❌ Processing failed: {data.get('status', '')}")
                return False
        except Exception as e:
            print(f"   ⚠️ Status check error: {e}")

    print("   ❌ Timeout waiting for processing")
    return False


def post_single_image(image_url, caption):
    """صورة واحدة"""
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
        cid = r.json().get('id')
        if not cid:
            print(f"❌ IG Single Error: {r.json()}")
            return None
        time.sleep(5)
        return _publish(cid)
    except Exception as e:
        print(f"❌ IG Single exception: {e}")
        return None


def post_carousel(image_urls, caption):
    """Carousel - 10 صور"""
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
            cid = r.json().get('id')
            if cid:
                children.append(cid)
            time.sleep(2)

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
        cid = r.json().get('id')
        if not cid:
            return None
        time.sleep(5)
        return _publish(cid)
    except Exception as e:
        print(f"❌ IG Carousel exception: {e}")
        return None


def post_reels_to_ig(video_path, caption):
    """Reels على Instagram"""
    try:
        # رفع الفيديو
        video_url = upload_video_transfer(video_path)
        if not video_url:
            print("❌ IG Reels: Video upload failed")
            return None

        # إنشاء Reels container
        print("   📦 Creating Reels container...")
        r = requests.post(
            f"{IG_API}/media",
            data={
                'media_type': 'REELS',
                'video_url': video_url,
                'caption': caption[:2200],
                'share_to_feed': 'true',
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=60
        )
        result = r.json()
        cid = result.get('id')

        if not cid:
            err = result.get('error', {}).get('message', str(result))
            print(f"❌ IG Reels Container Error: {err}")
            return None

        print(f"   ✅ Container created: {cid}")

        # انتظار المعالجة
        if not wait_for_processing(cid, max_wait=300):
            print("❌ IG Reels: Processing failed")
            return None

        # نشر
        post_id = _publish(cid)
        return post_id

    except Exception as e:
        print(f"❌ IG Reels exception: {e}")
        return None


def post_video_to_ig(video_path, caption):
    """فيديو عادي على Instagram"""
    try:
        video_url = upload_video_transfer(video_path)
        if not video_url:
            return None

        print("   📦 Creating Video container...")
        r = requests.post(
            f"{IG_API}/media",
            data={
                'media_type': 'VIDEO',
                'video_url': video_url,
                'caption': caption[:2200],
                'access_token': INSTAGRAM_TOKEN
            },
            timeout=60
        )
        cid = r.json().get('id')
        if not cid:
            print(f"❌ IG Video Error: {r.json()}")
            return None

        if not wait_for_processing(cid, max_wait=240):
            return None

        return _publish(cid)

    except Exception as e:
        print(f"❌ IG Video exception: {e}")
        return None


def post_to_instagram(image_urls=None, caption='', post_type='single',
                      video_path=None):
    """النشر على Instagram - كل الأنواع"""
    if not INSTAGRAM_TOKEN:
        print("⚠️ INSTAGRAM_TOKEN not set - skipping Instagram")
        return None

    print(f"\n📸 Posting to Instagram ({post_type})...")

    if post_type == 'reels' and video_path:
        post_id = post_reels_to_ig(video_path, caption)

    elif post_type == 'video' and video_path:
        post_id = post_video_to_ig(video_path, caption)

    elif post_type == 'album' and image_urls and len(image_urls) > 1:
        post_id = post_carousel(image_urls[:10], caption)

    elif image_urls:
        post_id = post_single_image(image_urls[0], caption)

    else:
        print("❌ No content provided")
        return None

    if post_id:
        print(f"   ✅ Instagram posted! ID: {post_id}")
    else:
        print("   ❌ Instagram: Failed")

    return post_id
