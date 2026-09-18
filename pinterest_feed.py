"""
📌 PINTEREST FEED — RSS مخصص بروابط Redbubble
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
بدل ما نستخدم Pinterest API (معقد وغير مستقر)، بنبني ملف RSS بسيط
إحنا اللي متحكمين فيه بالكامل، وبنخلي Pinterest "Automatic pin
creation from RSS" تقرأ منه.

الفايدة الأساسية: كل <link> في الفييد ده بيكون رابط المنتج على
Redbubble نفسه (بالظبط زي اللي بينزل في بوست فيسبوك/انستجرام)،
مش رابط مقال بلوجر.

الملفات:
  pinterest_feed_items.json  → قائمة آخر التصاميم (بيانات خام)
  pinterest_feed.xml         → ملف الـ RSS النهائي اللي Pinterest بيقرأه
                                (لازم يتنشر عن طريق GitHub Pages)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import json
from datetime import datetime
from xml.sax.saxutils import escape

FEED_ITEMS_FILE = 'pinterest_feed_items.json'
FEED_XML_FILE   = 'pinterest_feed.xml'
MAX_FEED_ITEMS  = 60   # آخر 60 تصميم بس، عشان الملف يفضل خفيف

SITE_TITLE = 'Cust Tshirts — Latest Designs'
SITE_LINK  = 'https://cust-tshirts.blogspot.com/'
SITE_DESC  = 'Latest print-on-demand designs from Cust Tshirts on Redbubble.'


def load_feed_items() -> list:
    """تحميل قائمة عناصر الفييد الحالية"""
    if os.path.exists(FEED_ITEMS_FILE):
        try:
            with open(FEED_ITEMS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Pinterest feed items load error: {e} — starting fresh")
    return []


def save_feed_items(items: list) -> bool:
    """حفظ قائمة عناصر الفييد"""
    try:
        with open(FEED_ITEMS_FILE, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Failed to save {FEED_ITEMS_FILE}: {e}")
        return False


def build_feed_xml(items: list) -> str:
    """بناء RSS 2.0 صالح تقدر Pinterest تقرأه"""
    now = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

    items_xml = []
    for item in items:
        pub_date = item.get('added_at', now)
        try:
            # لو مخزنة ISO format، حوّلها لصيغة RFC-822 اللي RSS بيتوقعها
            dt = datetime.fromisoformat(item['added_at'])
            pub_date = dt.strftime('%a, %d %b %Y %H:%M:%S GMT')
        except Exception:
            pass

        items_xml.append(f"""    <item>
      <title>{escape(item.get('title', ''))}</title>
      <link>{escape(item.get('url', ''))}</link>
      <guid isPermaLink="false">{escape(item.get('id', item.get('url', '')))}</guid>
      <pubDate>{pub_date}</pubDate>
      <description>{escape(item.get('description', ''))}</description>
      <enclosure url="{escape(item.get('image', ''))}" type="image/jpeg"/>
    </item>""")

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">
  <channel>
    <title>{escape(SITE_TITLE)}</title>
    <link>{escape(SITE_LINK)}</link>
    <description>{escape(SITE_DESC)}</description>
    <language>en-us</language>
    <lastBuildDate>{now}</lastBuildDate>
{chr(10).join(items_xml)}
  </channel>
</rss>
"""


def add_feed_item(url: str, image: str, title: str, description: str = '') -> None:
    """
    ➕ يضيف تصميم جديد لأول الفييد، ويعيد بناء pinterest_feed.xml
    url         → رابط المنتج على Redbubble (مش رابط بلوجر)
    image       → رابط صورة المنتج
    title       → عنوان التصميم
    description → وصف قصير (اختياري)
    """
    items = load_feed_items()

    new_item = {
        'id':          f"{url}#{datetime.now().timestamp()}",
        'url':         url,
        'image':       image,
        'title':       title[:100] if title else 'New Design',
        'description': (description or title or '')[:300],
        'added_at':    datetime.now().isoformat(),
    }

    items.insert(0, new_item)
    items = items[:MAX_FEED_ITEMS]

    save_feed_items(items)

    xml = build_feed_xml(items)
    try:
        with open(FEED_XML_FILE, 'w', encoding='utf-8') as f:
            f.write(xml)
        print(f"   📌 Pinterest feed updated ({len(items)} items) → {FEED_XML_FILE}")
    except Exception as e:
        print(f"⚠️ Failed to write {FEED_XML_FILE}: {e}")
