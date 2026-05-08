"""
📌 Pinterest Poster
Posts pins to Pinterest boards automatically
"""
import requests
import time
from config import HEADERS

PINTEREST_TOKEN = __import__('os').getenv('PINTEREST_TOKEN', '')
PINTEREST_BOARD_ID = __import__('os').getenv('PINTEREST_BOARD_ID', 'tripod-cat-gifts')
PINTEREST_USERNAME = __import__('os').getenv('PINTEREST_USERNAME', 'cust_tshirts')

PINTEREST_HEADERS = {
    'Authorization': f'Bearer {PINTEREST_TOKEN}',
    'Content-Type': 'application/json',
}


def get_board_id():
    """Get numeric board ID from board name"""
    try:
        r = requests.get(
            'https://api.pinterest.com/v5/boards',
            headers=PINTEREST_HEADERS,
            timeout=15
        )
        data = r.json()
        boards = data.get('items', [])
        for board in boards:
            if PINTEREST_BOARD_ID in board.get('name', '').lower().replace(' ', '-'):
                return board['id']
            if board.get('id') == PINTEREST_BOARD_ID:
                return board['id']
        if boards:
            print(f"⚠️ Board not found, using first board: {boards[0]['name']}")
            return boards[0]['id']
    except Exception as e:
        print(f"❌ Error getting boards: {e}")
    return None


def create_pin(image_url, title, description, link, board_id):
    """Create a single Pinterest pin"""
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
            print(f"❌ Pinterest Error: {result}")
            return None
    except Exception as e:
        print(f"❌ Pin creation error: {e}")
        return None


def post_to_pinterest(image_urls, caption, redbubble_url, design_hint=''):
    """Post multiple pins to Pinterest"""
    if not PINTEREST_TOKEN:
        print("⚠️ PINTEREST_TOKEN not set - skipping Pinterest")
        return []

    print(f"\n📌 Posting to Pinterest...")

    board_id = get_board_id()
    if not board_id:
        print("❌ Could not find Pinterest board")
        return []

    print(f"✅ Board ID: {board_id}")

    # Extract title from design hint or URL
    title = design_hint[:100] if design_hint else 'Unique Cat Design'
    short_desc = caption[:500] if caption else 'Check out this amazing design!'

    pin_ids = []
    max_pins = min(5, len(image_urls))

    for i, img_url in enumerate(image_urls[:max_pins]):
        print(f"   📌 Creating pin {i+1}/{max_pins}...")
        pin_id = create_pin(
            image_url=img_url,
            title=title,
            description=short_desc,
            link=redbubble_url,
            board_id=board_id
        )
        if pin_id:
            print(f"   ✅ Pin created: {pin_id}")
            pin_ids.append(pin_id)
        else:
            print(f"   ❌ Pin {i+1} failed")

        if i < max_pins - 1:
            time.sleep(3)

    print(f"📌 Pinterest: {len(pin_ids)}/{max_pins} pins created")
    return pin_ids
