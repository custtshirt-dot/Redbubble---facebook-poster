"""
📝 Caption Templates
Used as fallback when AI is not available
"""
import random

# ══════════════════════════════════════════════════════════════
# 🔥 HOOKS
# ══════════════════════════════════════════════════════════════
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

# ══════════════════════════════════════════════════════════════
# 💪 BODIES
# ══════════════════════════════════════════════════════════════
BODIES_EN = [
    "✨ Premium quality printed on demand\n🎨 Unique design - not found anywhere else\n📦 Ships worldwide in days\n💯 100% satisfaction guaranteed\n\nAvailable on stickers, t-shirts, mugs, phone cases, and 70+ products!",
    "Why customers LOVE this:\n✅ Eye-catching original artwork\n✅ Made to last - premium materials\n✅ Perfect gift for any occasion\n✅ Multiple products to choose from\n\nGrab yours before this trends even more 🚀",
    "🐾 Designed with love\n🎁 The perfect unique gift\n⭐ Top-rated by Redbubble customers\n🌍 Worldwide shipping available\n\nFrom $1.57 stickers to premium apparel - pick what fits YOU 👇",
    "What makes this special:\n🔥 Design that turns heads\n💪 Vibrant prints that last\n🎉 70+ products to choose from\n🚚 Fast worldwide shipping\n\nDon't just like it - OWN it 💯",
]

# ══════════════════════════════════════════════════════════════
# 🎯 CTAs
# ══════════════════════════════════════════════════════════════
CTAS_EN = [
    "👇 Tap the link below to grab yours NOW\n💬 Comment which product you want!\n🔄 Share with someone who'd love this!",
    "🛒 SHOP NOW - link below ⬇️\n❤️ Like if you'd wear this\n💬 Tell me your favorite in the comments!",
    "⏰ Don't wait - order today:\n🔗 Direct link below\n📲 Save this post!\n👥 Tag a friend who NEEDS this!",
    "🎯 3 easy steps:\n1️⃣ Click the link\n2️⃣ Pick your product\n3️⃣ Enjoy worldwide shipping! 📦\n\n💬 Which one are you getting?",
]

# ══════════════════════════════════════════════════════════════
# 🏷️ HASHTAGS - مقسمة حسب الكولكشن
# ══════════════════════════════════════════════════════════════

HASHTAGS_BY_COLLECTION = {

    'three_legged': (
        "#TripodCat #ThreeLeggedCat #TripaWd #CatMomGift #CatLovers "
        "#FunnyCat #CatDad #CatRescue #ThreeLeggedLegend #CatParent "
        "#GiftForMom #MothersDayGift #CatHumor #AmputeeCat #CatMerch "
        "#UniqueGifts #CustTshirts #Redbubble"
    ),

    'islamic': (
        "#IslamicArt #IslamicWallArt #MuslimGift #ArabicCalligraphy "
        "#RamadanGift #EidGift #MuslimHomeDecor #IslamicCalligraphy "
        "#IslamicDecor #ProphetMuhammad #IslamicDesign #MuslimArt "
        "#IslamicQuotes #HalalGift #CustTshirts #Redbubble"
    ),

    'motivational': (
        "#MotivationalQuotes #MotivationalQuotesForWork #GymMotivation "
        "#FitnessMotivation #InspirationalQuotes #WorkMotivation "
        "#BossGift #EntrepreneurGift #PositiveVibes #DailyMotivation "
        "#StayTrue #BestMotivationalQuotes #HustleQuotes "
        "#MotivationalGift #CustTshirts #Redbubble"
    ),

    'spooky': (
        "#SpookySeason #HalloweenVibes #HalloweenGift #FunnyHalloween "
        "#SpookyVibes #HalloweenCat #GhostCat #HalloweenShirt "
        "#SpookyDesign #HalloweenDecor #CatHalloween #DarkAesthetic "
        "#HalloweenCollection #SpookyArt #CustTshirts #Redbubble"
    ),

    'whimsical': (
        "#WhimsicalArt #FunnyAnimalShirt #CuteIllustration #QuirkyArt "
        "#BookLoverGift #ReaderGift #WhimsicalDesign #AnimalArt "
        "#FunnyDuck #AlligatorArt #CottageCore #NatureArt "
        "#ArtLovers #UniqueGifts #CustTshirts #Redbubble"
    ),

    'say_it': (
        "#CustomDesign #PersonalizedGift #TypographyArt #BoldDesign "
        "#CustomShirt #SayItYourWay #UniqueGifts #PersonalizedShirt "
        "#CustomMerch #GraphicTee #BoldTypography #CustomGifts "
        "#ExpressYourself #NeonDesign #CustTshirts #Redbubble"
    ),

    'general': (
        "#Redbubble #UniqueGifts #CustomGifts #PrintOnDemand "
        "#ArtMerch #GraphicTee #StickerShop #GiftIdeas "
        "#CatLovers #FunnyShirts #CustTshirts #ShopNow "
        "#WorldwideShipping #ArtistOnRedbubble #POD"
    ),
}


def detect_collection(url='', design_hint=''):
    """تحديد الكولكشن من الـ URL أو اسم التصميم"""
    text = (url + ' ' + design_hint).lower()

    if any(w in text for w in ['tripod', 'tripawd', 'three legged', 'three-legged', '3 leg']):
        return 'three_legged'
    elif any(w in text for w in ['islamic', 'muslim', 'prophet', 'muhammad', 'quran', 'allah', 'ramadan', 'eid']):
        return 'islamic'
    elif any(w in text for w in ['motivat', 'inspir', 'hustle', 'graffiti', 'donut give', 'stay true', 'drag me']):
        return 'motivational'
    elif any(w in text for w in ['spooky', 'halloween', 'ghost', 'skull', 'horror', 'creepy', 'scary']):
        return 'spooky'
    elif any(w in text for w in ['whimsical', 'duck', 'alligator', 'reader', 'book', 'vacation']):
        return 'whimsical'
    elif any(w in text for w in ['say it', 'neon heart', 'customiz']):
        return 'say_it'
    else:
        return 'general'


def get_hashtags(url='', design_hint=''):
    """جيب الهاشتاقات المناسبة للتصميم"""
    collection = detect_collection(url, design_hint)
    return HASHTAGS_BY_COLLECTION.get(collection, HASHTAGS_BY_COLLECTION['general'])


def get_template_caption(style='mixed', url='', post_type='album', design_hint=''):
    """Generate a caption from templates"""

    if style == 'mixed':
        style = random.choice(['funny', 'emotional', 'hard_sell'])

    hook = random.choice(HOOKS_EN.get(style, HOOKS_EN['funny']))
    body = random.choice(BODIES_EN)
    cta  = random.choice(CTAS_EN)

    # الهاشتاقات الذكية حسب الكولكشن
    hashtags = get_hashtags(url, design_hint)

    caption = (
        f"{hook}\n\n"
        f"{body}\n\n"
        f"━━━━━━━━━━━━━━━━━━━\n"
        f"{cta}\n"
        f"━━━━━━━━━━━━━━━━━━━\n\n"
        f"🛒 SHOP HERE 👇\n{url}\n\n"
        f"{hashtags}"
    )
    return caption


def get_text_only_post(url='', design_hint=''):
    """Text-only engagement post"""
    questions = [
        "🐱 Cat lovers! What's your cat's funniest habit? Tell me below! 👇",
        "Quick poll: Stickers or T-shirts? Which do you collect? 💬",
        "Drop a 🔥 if you love unique cat designs!",
        "Tell me your cat's name and I'll suggest the perfect design! 🎨",
        "If your cat had their own merch line, what would it say? 😂👇",
    ]
    hashtags = get_hashtags(url, design_hint)
    return random.choice(questions) + f"\n\n{hashtags}"


def get_link_post(url, design_hint=''):
    """Link post with strong CTA"""
    hashtags = get_hashtags(url, design_hint)
    return (
        f"🔥 NEW DROP ALERT! 🔥\n\n"
        f"Check out our latest collection - 70+ products available!\n\n"
        f"🛒 {url}\n\n"
        f"{hashtags}"
    )
