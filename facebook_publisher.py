"""
📘 Facebook Publisher - All post types
"""
import requests
import io
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import FB_PAGE_ID, FB_TOKEN, HEADERS


def upload_photo(image_url, published=False):
    """Upload single photo to Facebook (unpublished by default)"""
    try:
        img_data = requests.get(image_url, headers=HEADERS, timeout=15).content
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {'source': ('img.jpg', io.BytesIO(img_data), 'image/jpeg')}
        data = {
            'published': 'true' if published else 'false',
            'access_token': FB_TOKEN
        }
        r = requests.post(url, files=files, data=data, timeout=30)
        return r.json().get('id')
    except Exception as e:
        print(f"⚠️ Upload failed: {e}")
        return None


def upload_photos_parallel(image_urls, max_workers=10):
    """Upload multiple photos in parallel, preserving order"""
    print(f"⚡ Uploading {len(image_urls)} images in parallel...")
    
    photo_ids = [None] * len(image_urls)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_idx = {
            executor.submit(upload_photo, url, False): i 
            for i, url in enumerate(image_urls)
        }
        for future in as_completed(future_to_idx):
            idx = future_to_idx[future]
            pid = future.result()
            if pid:
                photo_ids[idx] = pid
    
    valid_ids = [p for p in photo_ids if p]
    print(f"✅ Uploaded {len(valid_ids)}/{len(image_urls)} successfully")
    return valid_ids


# ============================================================
# POST TYPE 1: ALBUM POST (multiple images)
# ============================================================
def post_album(image_urls, caption):
    """Create album post with multiple images"""
    print("\n📸 Creating ALBUM post...")
    
    photo_ids = upload_photos_parallel(image_urls)
    if not photo_ids:
        return {'error': 'No photos uploaded'}
    
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        'message': caption,
        'attached_media': json.dumps([{"media_fbid": pid} for pid in photo_ids]),
        'access_token': FB_TOKEN
    }
    return requests.post(url, data=payload).json()


# ============================================================
# POST TYPE 2: SINGLE PHOTO
# ============================================================
def post_single_photo(image_url, caption):
    """Post single photo with caption"""
    print("\n🖼️ Creating SINGLE PHOTO post...")
    try:
        img_data = requests.get(image_url, headers=HEADERS, timeout=15).content
        url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
        files = {'source': ('img.jpg', io.BytesIO(img_data), 'image/jpeg')}
        data = {
            'message': caption,
            'published': 'true',
            'access_token': FB_TOKEN
        }
        r = requests.post(url, files=files, data=data, timeout=30)
        return r.json()
    except Exception as e:
        return {'error': str(e)}


# ============================================================
# POST TYPE 3: TEXT ONLY POST
# ============================================================
def post_text_only(message):
    """Text-only engagement post"""
    print("\n💬 Creating TEXT-ONLY post...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        'message': message,
        'access_token': FB_TOKEN
    }
    return requests.post(url, data=payload).json()


# ============================================================
# POST TYPE 4: LINK POST
# ============================================================
def post_link(message, link):
    """Link post with preview"""
    print("\n🔗 Creating LINK post...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed"
    payload = {
        'message': message,
        'link': link,
        'access_token': FB_TOKEN
    }
    return requests.post(url, data=payload).json()


# ============================================================
# POST TYPE 5: VIDEO POST
# ============================================================
def post_video(video_path, caption):
    """Upload video to Facebook"""
    print("\n🎬 Creating VIDEO post...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/videos"
    try:
        with open(video_path, 'rb') as f:
            files = {'source': f}
            data = {
                'description': caption,
                'access_token': FB_TOKEN
            }
            r = requests.post(url, files=files, data=data, timeout=300)
            return r.json()
    except Exception as e:
        return {'error': str(e)}


# ============================================================
# POST TYPE 6: REELS
# ============================================================
def post_reels(video_path, caption):
    """Post as Facebook Reels"""
    print("\n🎥 Creating REELS post...")
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels"
    try:
        # Step 1: Initialize upload
        init = requests.post(url, data={
            'upload_phase': 'start',
            'access_token': FB_TOKEN
        }).json()
        
        video_id = init.get('video_id')
        upload_url = init.get('upload_url')
        
        if not video_id:
            return {'error': 'Reels init failed', 'details': init}
        
        # Step 2: Upload video
        with open(video_path, 'rb') as f:
            requests.post(upload_url, headers={
                'Authorization': f'OAuth {FB_TOKEN}',
                'offset': '0',
                'file_size': str(len(f.read()))
            }, data=open(video_path, 'rb').read())
        
        # Step 3: Publish
        publish = requests.post(
            f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/video_reels",
            data={
                'video_id': video_id,
                'upload_phase': 'finish',
                'video_state': 'PUBLISHED',
                'description': caption,
                'access_token': FB_TOKEN
            }
        ).json()
        
        return publish
    except Exception as e:
        return {'error': str(e)}
