"""
📘 النشر على فيسبوك - كل أنواع المحتوى
"""
import requests
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import FB_PAGE_ID, FB_TOKEN, HEADERS


def upload_photo(image_url, published=False):
    """رفع صورة لفيسبوك"""
    try:
        img_data = requests.get(image_url, headers=HEADERS, timeout=15).content
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {'source': ('img.jpg', io.BytesIO(img_data), 'image/jpeg')}
        data = {'published': str(published).lower(), 'access_token': FB_TOKEN}
        r = requests.post(url, files=files, data=data, timeout=30)
        return r.json().get('id')
    except Exception as e:
        print(f"❌ Upload failed: {e}")
        return None


def post_album(images, caption):
    """نشر ألبوم صور"""
    print(f"\n📸 Uploading {len(images)} images for ALBUM...")
    
    photo_ids_ordered = [None] * len(images)
    with ThreadPoolExecutor(max_workers=10) as ex:
        futures = {ex.submit(upload_photo, img): i for i, img in enumerate(images)}
        for future in as_completed(futures):
            idx = futures[future]
            photo_ids_ordered[idx] = future.result()
    
    photo_ids = [p for p in photo_ids_ordered if p]
    print(f"✅ Uploaded {len(photo_ids)} images")
    
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        'message': caption,
        'attached_media': json.dumps([{"media_fbid": pid} for pid in photo_ids]),
        'access_token': FB_TOKEN
    }
    return requests.post(url, data=payload).json()


def post_single_photo(image_url, caption):
    """نشر صورة واحدة"""
    print("\n🖼️ Posting single photo...")
    try:
        img_data = requests.get(image_url, headers=HEADERS, timeout=15).content
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {'source': ('img.jpg', io.BytesIO(img_data), 'image/jpeg')}
        data = {'caption': caption, 'published': 'true', 'access_token': FB_TOKEN}
        return requests.post(url, files=files, data=data, timeout=30).json()
    except Exception as e:
        return {"error": str(e)}


def post_carousel(images, caption):
    """نشر carousel (نفس الألبوم لكن بترتيب قصصي)"""
    print(f"\n🎠 Posting carousel with {len(images)} images...")
    return post_album(images[:10], caption)


def post_video(video_path, caption):
    """نشر فيديو"""
    print(f"\n🎬 Uploading video...")
    try:
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
        with open(video_path, 'rb') as f:
            files = {'source': f}
            data = {'description': caption, 'access_token': FB_TOKEN}
            r = requests.post(url, files=files, data=data, timeout=300)
        return r.json()
    except Exception as e:
        return {"error": str(e)}


def post_reels(video_path, caption):
    """نشر Reels (Facebook Reels API)"""
    print(f"\n🎥 Uploading Reels...")
    try:
        # 1. Initialize upload
        init_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
        init_data = {'upload_phase': 'start', 'access_token': FB_TOKEN}
        init_r = requests.post(init_url, data=init_data).json()
        video_id = init_r.get('video_id')
        upload_url = init_r.get('upload_url')
        
        if not video_id or not upload_url:
            return {"error": "Failed to initialize Reels upload", "details": init_r}
        
        # 2. Upload video
        import os
        file_size = os.path.getsize(video_path)
        with open(video_path, 'rb') as f:
            upload_headers = {
                'Authorization': f'OAuth {FB_TOKEN}',
                'offset': '0',
                'file_size': str(file_size)
            }
            requests.post(upload_url, headers=upload_headers, data=f, timeout=300)
        
        # 3. Publish
        publish_url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
        publish_data = {
            'video_id': video_id,
            'upload_phase': 'finish',
            'video_state': 'PUBLISHED',
            'description': caption,
            'access_token': FB_TOKEN
        }
        return requests.post(publish_url, data=publish_data).json()
    except Exception as e:
        return {"error": str(e)}


def post_text_only(message):
    """نشر نص بدون صور"""
    print("\n📝 Posting text-only...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    data = {'message': message, 'access_token': FB_TOKEN}
    return requests.post(url, data=data).json()


def post_link(link, message):
    """نشر لينك مع preview"""
    print("\n🔗 Posting link...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    data = {
        'message': message,
        'link': link,
        'access_token': FB_TOKEN
    }
    return requests.post(url, data=data).json()


def post_story_photo(image_url):
    """نشر Story صورة"""
    print("\n📱 Posting Story...")
    try:
        # Upload as unpublished first
        photo_id = upload_photo(image_url, published=False)
        if not photo_id:
            return {"error": "Photo upload failed"}
        
        # Publish as story
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photo_stories"
        data = {'photo_id': photo_id, 'access_token': FB_TOKEN}
        return requests.post(url, data=data).json()
    except Exception as e:
        return {"error": str(e)}
