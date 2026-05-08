"""
📸 Instagram Poster
Posts to Instagram via Facebook Graph API
"""
import requests
import time
import os
from config import HEADERS

INSTAGRAM_USER_ID = os.getenv('INSTAGRAM_USER_ID', '17841477368001153')
INSTAGRAM_TOKEN = os.getenv('INSTAGRAM_TOKEN', os.getenv('FB_TOKEN', ''))


def create_ig_container(image_url, caption):
    """Step 1: Create media container"""
    try:
        url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media"
        payload = {
            'image_url': image_url,
            'caption': caption[:2200],
            'access_token': INSTAGRAM_TOKEN
        }
        r = requests.post(url, data=payload, timeout=30)
        result = r.json()
        if 'id' in result:
            return result['id']
        else:
            print(f"❌ IG Container Error: {result.get('error', {}).get('message', str(result))}")
            return None
    except Exception as e:
        print(f"❌ IG Container exception: {e}")
        return None


def publish_ig_container(container_id):
    """Step 2: Publish the container"""
    try:
        url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media_publish"
        payload = {
            'creation_id': container_id,
            'access_token': INSTAGRAM_TOKEN
        }
        r = requests.post(url, data=payload, timeout=30)
        result = r.json()
        if 'id' in result:
            return result['id']
        else:
            print(f"❌ IG Publish Error: {result.get('error', {}).get('message', str(result))}")
            return None
    except Exception as e:
        print(f"❌ IG Publish exception: {e}")
        return None


def create_ig_carousel(image_urls, caption):
    """Create carousel post with multiple images"""
    try:
        # Step 1: Create container for each image
        children = []
        for img_url in image_urls[:10]:
            url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media"
            payload = {
                'image_url': img_url,
                'is_carousel_item': 'true',
                'access_token': INSTAGRAM_TOKEN
            }
            r = requests.post(url, data=payload, timeout=30)
            result = r.json()
            if 'id' in result:
                children.append(result['id'])
            time.sleep(1)

        if not children:
            return None

        # Step 2: Create carousel container
        url = f"https://graph.facebook.com/v19.0/{INSTAGRAM_USER_ID}/media"
        payload = {
            'media_type': 'CAROUSEL',
            'caption': caption[:2200],
            'children': ','.join(children),
            'access_token': INSTAGRAM_TOKEN
        }
        r = requests.post(url, data=payload, timeout=30)
        result = r.json()
        return result.get('id')

    except Exception as e:
        print(f"❌ IG Carousel exception: {e}")
        return None


def post_to_instagram(image_urls, caption, post_type='single'):
    """Post to Instagram"""
    if not INSTAGRAM_TOKEN:
        print("⚠️ INSTAGRAM_TOKEN not set - skipping Instagram")
        return None

    if not INSTAGRAM_USER_ID:
        print("⚠️ INSTAGRAM_USER_ID not set - skipping Instagram")
        return None

    print(f"\n📸 Posting to Instagram ({post_type})...")

    try:
        if post_type == 'album' and len(image_urls) > 1:
            # Carousel post
            container_id = create_ig_carousel(image_urls[:10], caption)
        else:
            # Single post
            container_id = create_ig_container(image_urls[0], caption)

        if not container_id:
            print("❌ Instagram: Container creation failed")
            return None

        # Wait before publishing
        print("   ⏳ Waiting 5 seconds before publishing...")
        time.sleep(5)

        # Publish
        post_id = publish_ig_container(container_id)

        if post_id:
            print(f"   ✅ Instagram posted! ID: {post_id}")
            return post_id
        else:
            print("   ❌ Instagram: Publishing failed")
            return None

    except Exception as e:
        print(f"❌ Instagram error: {e}")
        return None
