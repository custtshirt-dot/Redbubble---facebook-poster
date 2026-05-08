"""
📌 Pinterest Poster v2
Posts pins using board name directly
"""
import requests
import time
import os

PINTEREST_TOKEN = os.getenv('PINTEREST_TOKEN', '')
PINTEREST_BOARD_ID = os.getenv('PINTEREST_BOARD_ID', 'tripod-cat-gifts')
PINTEREST_USERNAME = os.getenv('PINTEREST_USERNAME', 'cust_tshirts')

PINTEREST_HEADERS = {
    'Authorization': f'Bearer {PINTEREST_TOKEN}',
    'Content-Type': 'application/json',
}


def get_numeric_board_id():
    """Get numeric board ID from Pinterest API"""
    try:
        # Try direct board fetch using username/board_name format
        board_slug = f"{PINTEREST_USERNAME}/{PINTEREST_BOARD_ID}"
        r = requests.get(
            f'https://api.pinterest.com/v5/boards/{board_slug}',
            headers=PINTEREST_HEADERS,
            timeout=15
        )
        data = r.json()
        if 'id' in data:
            print(f"✅ Board found: {data['name']} (ID: {data['id']})")
            return data['id']

        # Try listing all boards
        r2 = requests.get(
            'https://api.pinterest.com/v5/boards',
            headers=PINTEREST_HEADERS,
            timeout=15
        )
        data2 = r2.json()
        boards = data2.get('items', [])

        for board in boards:
            board_name = board.get('name', '').lower().replace(' ', '-')
            if PINTEREST_BOARD_ID.lower() in board_name:
                print(f"✅ Board matched: {board['name']} (ID: {board['id']})")
                return board['id']

        # Use first board if available
        if boards:
            print(f"⚠️ Using first board: {boards[0]['name']}")
            return boards[0]['id']

    except Exception as e:
        print(f"❌ Board lookup error: {e}")

    return None


def create_pin(image_url, title, description, link, board_id):
    """Create a Pinterest pin"""
    try:
        payload = {
            'board_id': board_id,
            'title': title[:100],
            'description': description[:500],
            'link': link,
            'media_source': {
                'source_type': 'image_url',
                'url': image_url
            }
        }
        r = requests.post(
            'https://api.pinterest.com/v5/pins',
            headers=PINTEREST_HEADERS,
            json=payload,
            timeout=30
        )
        result = r.json()
        if 'id' in result:
            return result['id']
        else:
            err = result.get('message', str(result))
            print(f"❌ Pin error: {err}")
            return None
    except Exception as e:
        print(f"❌ Pin exception: {e}")
        return None


def post_to_pinterest(image_urls, caption, redbubble_url, design_hint=''):
    """Post to Pinterest"""
    if not PINTEREST_TOKEN:
        print("⚠️ PINTEREST_TOKEN not set - skipping Pinterest")
        return []

    print(f"\n📌 Posting to Pinterest...")
    print(f"   🔍 Looking for board: {PINTEREST_BOARD_ID}")

    board_id = get_numeric_board_id()

    if not board_id:
        print("❌ Could not find Pinterest board")
        print(f"   Board name tried: {PINTEREST_USERNAME}/{PINTEREST_BOARD_ID}")
        return []

    title = design_hint[:100] if design_hint else 'Unique Cat Design'
    description = caption[:500] if caption else 'Amazing design for cat lovers!'

    pin_ids = []
    max_pins = min(5, len(image_urls))

    for i, img_url in enumerate(image_urls[:max_pins]):
        print(f"   📌 Pin {i+1}/{max_pins}...")
        pin_id = create_pin(
            image_url=img_url,
            title=title,
            description=description,
            link=redbubble_url,
            board_id=board_id
        )
        if pin_id:
            print(f"   ✅ Pin created: {pin_id}")
            pin_ids.append(pin_id)
        else:
            print(f"   ❌ Pin {i+1} failed")

        if i < max_pins - 1:
            time.sleep(2)

    print(f"📌 Pinterest: {len(pin_ids)}/{max_pins} pins created")
    return pin_ids
