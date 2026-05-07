"""
📝 Caption Templates
Used as fallback when AI is not available
"""
import random

# 🔥 STRONG HOOKS (stop the scroll)
HOOKS_EN = {
    'funny': [
        "POV: You just found your new favorite design 👀",
        "Stop everything. This design is too good to scroll past 🛑",
        "Warning ⚠️ Once you see this, you'll want it on EVERYTHING",
        "This design lives rent-free in my customers' heads 🧠✨",
        "Tell me you're a cat lover without telling me 🐱👇",
    ],
    'emotional': [
        "Some designs just hit different 💖 This is one of them.",
        "Made for the ones who truly understand... 🥺",
        "When art meets passion, magic happens ✨",
        "This isn't just merch. It's a whole vibe 💫",
        "For everyone who needs this in their life right now 💝",
    ],
    'hard_sell': [
        "🔥 SELLING FAST! Get yours before stock runs out",
        "⏰ LIMITED TIME: Premium quality at unbeatable prices",
        "💯 100+ happy customers can't be wrong - shop now!",
        "🚨 TRENDING NOW on Redbubble - don't miss out!",
        "⭐ Best-seller alert! Order today, ships worldwide 📦",
    ]
}

# 💪 BODY TEMPLATES
BODIES_EN = [
    "✨ Premium quality printed on demand\n🎨 Unique design - not found anywhere else\n📦 Ships worldwide in days\n💯 100% satisfaction guaranteed\n\nAvailable on stickers, t-shirts, mugs, phone cases, and 70+ products!",
    
    "Why customers LOVE this:\n✅ Eye-catching original artwork\n✅ Made to last - premium materials\n✅ Perfect gift for any occasion\n✅ Multiple products to choose from\n\nGrab yours before this trends even more 🚀",
    
    "🐾 Designed with love\n🎁 The perfect unique gift\n⭐ Top-rated by Redbubble customers\n🌍 Worldwide shipping available\n\nFrom $1.57 stickers to premium apparel - pick what fits YOU 👇",
    
    "What makes this special:\n🔥 Design that turns heads\n💪 Vibrant prints that last\n🎉 70+ products to choose from\n🚚 Fast worldwide shipping\n\nDon't just like it - OWN it 💯",
]

# 🎯 STRONG CTAs
CTAS_EN = [
    "👇 Tap the link below to grab yours NOW\n💬 Comment which product you want!\n🔄 Share with someone who'd love this!",
    
    "🛒 SHOP NOW - link below ⬇️\n❤️ Like if you'd wear this\n💬 Tell me your favorite in the comments!",
    
    "⏰ Don't wait - order today:\n🔗 Direct link below\n📲 Save this post!\n👥 Tag a friend who NEEDS this!",
    
    "🎯 3 easy steps:\n1️⃣ Click the link\n2️⃣ Pick your product\n3️⃣ Enjoy worldwide shipping! 📦\n\n💬 Which one are you getting?",
]

# 🏷️ HASHTAGS
HASHTAGS = "#Redbubble #CatLovers #FunnyCatGifts #Stickers #TripodCat #CatMom #CatDad #CustomGifts #UniqueGifts #CatMerch #StickerShop #GiftIdeas #CatHumor #Pawsome #CustTshirts"


def get_template_caption(style='mixed', url='', post_type='album'):
    """Generate a caption from templates"""
    
    if style == 'mixed':
        style = random.choice(['funny', 'emotional', 'hard_sell'])
    
    hook = random.choice(HOOKS_EN.get(style, HOOKS_EN['funny']))
    body = random.choice(BODIES_EN)
    cta = random.choice(CTAS_EN)
    
    caption = (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{cta}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛒 SHOP HERE 👇\n{url}\n\n"
        f"{HASHTAGS}"
    )
    return caption


def get_text_only_post():
    """Text-only engagement post"""
    questions = [
        "🐱 Cat lovers! What's your cat's funniest habit? Tell me below! 👇",
        "Quick poll: Stickers or T-shirts? Which do you collect? 💬",
        "Drop a 🔥 if you love unique cat designs!",
        "Tell me your cat's name and I'll suggest the perfect design! 🎨",
    ]
    return random.choice(questions) + f"\n\n{HASHTAGS}"


def get_link_post(url):
    """Link post with strong CTA"""
    return (
        f"🔥 NEW DROP ALERT! 🔥\n\n"
        f"Check out our latest collection - 70+ products available!\n\n"
        f"🛒 {url}\n\n"
        f"{HASHTAGS}"
    )
