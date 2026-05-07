"""
📋 قوالب احتياطية (لو الـ AI فشل)
"""
import random

HOOKS = [
    "Stop scrolling 🛑 You NEED to see this design before it sells out...",
    "I just got 4 sales in 24 hours from THIS design 🤯",
    "POV: You finally found the perfect gift for cat lovers 🐱✨",
    "This design is breaking the internet right now 🔥",
    "Warning ⚠️ Once you see this, you'll want it on EVERYTHING",
    "Trending NOW on Redbubble 📈 Don't miss out",
    "The funniest cat design of 2026 just dropped 🎉",
]

BODIES = [
    "✨ Premium quality on demand\n🎨 Unique design\n📦 Worldwide shipping\n💯 Hundreds of happy customers",
    "Why customers LOVE this:\n✅ Eye-catching artwork\n✅ Premium materials\n✅ Perfect gift\n✅ Ships worldwide",
    "🐾 Designed for cat lovers\n🎁 Standout gift\n⭐ Top-rated\n🌍 Ships globally",
]

CTAS = [
    "👇 Tap the link to grab yours NOW\n💬 Comment 'WANT' for direct link!",
    "🛒 SHOP NOW before it's gone:\n👉 Click the link below",
    "⏰ Limited stock - order today:\n🔗 Direct link below ⬇️",
]

HASHTAGS = "#Redbubble #CatLovers #FunnyCatGifts #Stickers #TripodCat #CatMom #CatDad #CustomGifts #UniqueGifts #CatMerch #StickerShop #GiftIdeas #CatHumor #Pawsome"


def get_fallback_content(post_type, url):
    """قوالب احتياطية حسب نوع البوست"""
    
    hook = random.choice(HOOKS)
    body = random.choice(BODIES)
    cta = random.choice(CTAS)
    
    templates_dict = {
        "album": f"{hook}\n\n{body}\n\n━━━━━━━━━━━━━━━━━━━\n{cta}\n━━━━━━━━━━━━━━━━━━━\n\n🛒 SHOP HERE 👇\n{url}\n\n{HASHTAGS}",
        
        "single": f"{hook}\n\n🛒 Get yours: {url}\n\n{HASHTAGS}",
        
        "carousel": f"{hook}\n\nLet me show you why this is a MUST-HAVE 👇\n\n{body}\n\n{cta}\n\n🔗 {url}\n\n{HASHTAGS}",
        
        "reels": f"{hook} 🔥\n\n👀 Watch till the end!\n\n🛒 {url}\n\n{HASHTAGS}",
        
        "video": f"🎬 {hook}\n\n{body}\n\nWatch the full collection above ⬆️\n\n🛒 Shop: {url}\n\n{HASHTAGS}",
        
        "text": f"Quick question for cat lovers 🐱\n\n{hook}\n\nWhich design speaks to YOU?\n\nCheck the full collection: {url}\n\n{HASHTAGS}",
        
        "link": f"{hook}\n\n{cta}\n\n{HASHTAGS}",
        
        "story": f"🔥 NEW DROP! Tap to shop ⬆️"
    }
    
    return templates_dict.get(post_type, templates_dict["album"])
