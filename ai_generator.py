"""
🤖 AI Caption & Script Generator using Groq
"""
import os
import re
import random
from urllib.parse import unquote
from config import GROQ_API_KEY, LANGUAGE, STYLE
from templates import get_template_caption, HASHTAGS

client = None
if GROQ_API_KEY:
    try:
        # Fix for proxies issue in some environments
        os.environ.pop('HTTP_PROXY', None)
        os.environ.pop('HTTPS_PROXY', None)
        os.environ.pop('http_proxy', None)
        os.environ.pop('https_proxy', None)
        
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI initialized")
    except Exception as e:
        print(f"⚠️ Groq init failed: {e}")
        client = None


# ============================================================
# DESIGN DETECTION
# ============================================================
def extract_design_name_from_url(url):
    """Extract design name from Redbubble URL"""
    try:
        url = unquote(url)
        # Pattern: /i/t-shirt/Neon-Gradient-Monster-Teeth-Evil-Grin-by-Cust-tshirts/
        match = re.search(r'/i/[^/]+/([^/]+?)-by-', url)
        if match:
            design_name = match.group(1).replace('-', ' ')
            return design_name
        
        # Fallback patterns
        match = re.search(r'/([A-Z][a-zA-Z\-]+)-by-', url)
        if match:
            return match.group(1).replace('-', ' ')
        
        return None
    except:
        return None


def generate_design_hint(redbubble_url, sample_image_urls=''):
    """Smart design detection from URL + images"""
    
    # Try URL extraction first (most accurate)
    design_name = extract_design_name_from_url(redbubble_url)
    
    if design_name:
        print(f"🎨 Design extracted from URL: {design_name}")
        return design_name
    
    # Fallback: detect from image URLs
    text = (redbubble_url + ' ' + sample_image_urls).lower()
    hints = []
    
    keywords = {
        'cat': 'cats',
        'tripod': 'tripod cats',
        'funny': 'humor',
        'horror': 'horror/spooky',
        'spooky': 'spooky',
        'retro': 'retro vintage',
        'monster': 'monsters',
        'neon': 'neon designs',
        'evil': 'edgy/dark',
        'gradient': 'gradient art',
        'ghost': 'ghosts',
        'skull': 'skulls',
        'dragon': 'dragons',
        'anime': 'anime',
        'gaming': 'gaming',
        'music': 'music',
        'space': 'space/galaxy',
        'flower': 'floral',
        'minimalist': 'minimalist',
        'vintage': 'vintage',
        'pirate': 'pirates',
        'tshirt': 'apparel',
        't-shirt': 'apparel',
    }
    
    for keyword, hint in keywords.items():
        if keyword in text:
            hints.append(hint)
    
    return ', '.join(hints[:5]) if hints else 'unique creative designs'


# ============================================================
# CAPTION GENERATION (for Facebook posts)
# ============================================================
def generate_ai_caption(post_type='album', url='', design_hint='unique design'):
    """Generate caption using Groq AI"""
    
    if not client:
        return get_template_caption(STYLE, url, post_type)
    
    style_map = {
        'funny':       'funny, witty, and humorous — make them laugh then buy',
        'emotional':   'emotional and heartfelt — make them feel this design was made for them',
        'hard_sell':   'urgent, high-pressure, and sales-focused — create FOMO',
        'sales_blast': 'explosive, hype-driven, desire-building — make them feel they NEED this NOW',
        'mixed':       random.choice(['sales_blast', 'emotional', 'hard_sell', 'funny'])
    }
    
    selected_style = style_map.get(STYLE, 'engaging')
    lang_instruction = {
        'english': 'Write ONLY in English.',
        'arabic': 'اكتب باللغة العربية فقط.',
        'both': 'Write in both English and Arabic.'
    }.get(LANGUAGE, 'Write in English.')
    
    type_instruction = {
        'album': 'a Facebook album post showcasing multiple products',
        'single': 'a single Facebook photo post',
        'reels': 'a SHORT Facebook Reels caption (max 200 chars total!)',
        'video': 'a Facebook video post caption',
        'text': 'a text-only engagement post asking a question',
        'link': 'a link post driving clicks to the shop',
        'carousel': 'a carousel post telling a story',
    }.get(post_type, 'a Facebook post')
    
    # اختار hook مختلف كل مرة عشان مش تبان مكررة
    hook_styles = [
        "Start with a bold relatable statement that makes them say 'That's SO me!'",
        "Start with a curiosity-gap question they HAVE to answer",
        "Start with a dramatic 'POV:' scenario putting them IN the design",
        "Start with social proof: 'Everyone who sees this asks where I got it'",
        "Start with a pattern-interrupt: unexpected, weird, or shocking first line",
    ]
    hook_choice = random.choice(hook_styles)

    prompt = f"""You are a TOP-TIER Redbubble sales copywriter. Your captions drive real purchases.

DESIGN: "{design_hint}"
POST TYPE: {type_instruction}
STYLE: {selected_style}
LANGUAGE: {lang_instruction}

YOUR MISSION: Write a caption so good they stop scrolling, feel something, and click BUY.

HOOK STRATEGY: {hook_choice}

PROVEN CAPTION STRUCTURE:
━━━━━━━━━━━━━━━━━━━━━━━━
1. 🔥 HOOK (2 lines MAX)
   - {hook_choice}
   - Make it IMPOSSIBLE to ignore
   - Directly reference: {design_hint}

2. 💎 DESIRE BUILD (3-4 lines)
   - Paint the picture: what does owning this FEEL like?
   - Who is this PERFECT for? (gift idea angle works great)
   - Mention it ships worldwide, high quality
   - Use sensory/emotional language

3. ⚡ URGENCY TRIGGER (1-2 lines)
   - Create FOMO without fake discounts
   - Examples: "This won't stay under the radar long"
   - "Perfect for [occasion] — don't wait"

4. 🛒 CTA (2 lines)
   - Direct: "Grab yours now 👇"
   - Then: 🛒 SHOP: {url}

5. #️⃣ HASHTAGS:
   {HASHTAGS}

POWER RULES — READ CAREFULLY:
✅ Every sentence must earn its place — no filler
✅ Use emojis that MATCH the design theme ({design_hint})
✅ Speak TO the buyer ("you", "your", "you'll love")
✅ Gift angle: "Perfect gift for [audience who loves this design]"
✅ For reels: keep caption under 150 chars — pure punch
✅ Make the design sound EXCLUSIVE and SPECIAL
❌ NEVER: discount codes, promo codes, fake prices, % off
❌ NEVER: generic captions that could apply to ANY product
❌ NEVER: boring, corporate, or robotic language

This caption must feel HUMAN, EXCITING, and make them think "I need this."
Max 400 words."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an elite Redbubble sales copywriter who writes scroll-stopping, purchase-driving captions. Every word is intentional. You write with energy, emotion, and urgency. You ALWAYS match the design theme. You NEVER use discount codes, promo codes, or fake offers. You write captions that make people feel they NEED this product NOW."},
                {"role": "user", "content": prompt}
            ],
            temperature=1.0,
            max_tokens=900,
        )
        
        caption = response.choices[0].message.content.strip()
        print(f"✅ AI caption generated for: {design_hint}")
        return caption
        
    except Exception as e:
        print(f"⚠️ AI failed: {e}. Using template instead.")
        return get_template_caption(STYLE, url, post_type)


# ============================================================
# VIDEO SCRIPT GENERATION (for spoken narration)
# ============================================================
def generate_video_script(design_hint, url, max_seconds=30):
    """
    Generate spoken script for video narration
    Returns text optimized for TTS (15-30 seconds when spoken)
    """
    
    if not client:
        return _get_fallback_script(design_hint)
    
    hook_openers = [
        "Stop. You need to see this.",
        "Wait — is this not the most perfect thing you've seen?",
        "POV: You finally found it.",
        "I wasn't going to post this but...",
        "This design is going viral for a reason.",
        "Okay hear me out —",
    ]
    opener = random.choice(hook_openers)

    prompt = f"""Write a SPOKEN Reels script for a Facebook/Instagram video about this Redbubble design.

DESIGN: "{design_hint}"
OPENER TO USE: "{opener}"

STRUCTURE (spoken words only — no labels, no emojis):

HOOK (2-3 seconds): Use this opener: "{opener}" then connect to {design_hint}
DESIRE (15 seconds): Paint the picture — who wears/uses this, how it makes them feel, available on tees/stickers/mugs/more
SOCIAL PROOF (5 seconds): "People are obsessed with this" / "Perfect gift" / "Everyone asks where I got it"
CTA (3 seconds): Short, punchy, urgent — "Link in bio, grab yours now" or "Tap below before it blows up"

RULES:
- ONLY spoken words. No emojis. No hashtags. No markdown. No labels.
- Short punchy sentences. Commas for pauses.
- Max 85 words — tight, fast, viral
- Energy level: 9/10 — excited but natural
- Reference {design_hint} naturally throughout
- NEVER mention discount codes, promo codes, or % off

Output ONLY the spoken script. Nothing else."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a viral Reels scriptwriter. Your scripts hook in 2 seconds, build desire fast, and end with a punch. Output ONLY spoken words — no labels, no formatting, no markdown. Never mention discount codes."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=400,
        )
        
        script = response.choices[0].message.content.strip()
        
        # Clean any markdown or formatting
        script = re.sub(r'[*_#`]', '', script)
        script = re.sub(r'\[.*?\]', '', script)  # Remove [labels]
        script = re.sub(r'\(.*?\)', '', script)  # Remove (notes)
        script = re.sub(r'^(Hook|Body|CTA|Script)[:.]?\s*', '', script, flags=re.IGNORECASE | re.MULTILINE)
        script = re.sub(r'\n+', ' ', script)
        script = re.sub(r'\s+', ' ', script).strip()
        
        # Remove common AI prefixes
        for prefix in ['Script:', 'Here is', "Here's", 'Spoken text:', 'Voiceover:']:
            if script.lower().startswith(prefix.lower()):
                script = script.split(':', 1)[-1].strip() if ':' in script else script
        
        # Remove emojis (TTS reads them awkwardly)
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001f926-\U0001f937"
            "\U00010000-\U0010ffff"
            "\u2640-\u2642"
            "\u2600-\u2B55"
            "\u200d"
            "\u23cf"
            "\u23e9"
            "\u231a"
            "\ufe0f"
            "\u3030"
            "]+",
            flags=re.UNICODE,
        )
        script = emoji_pattern.sub('', script).strip()
        script = re.sub(r'\s+', ' ', script).strip()
        
        word_count = len(script.split())
        print(f"📝 Script generated ({word_count} words)")
        
        if word_count < 20:
            print("⚠️ Script too short, using fallback")
            return _get_fallback_script(design_hint)
        
        return script
        
    except Exception as e:
        print(f"⚠️ Script generation failed: {e}")
        return _get_fallback_script(design_hint)


def _get_fallback_script(design_hint):
    """Fallback script if AI fails"""
    templates = [
        f"Stop scrolling! You need to see this incredible {design_hint} design. "
        f"It's available on stickers, t-shirts, mugs, phone cases, and so much more. "
        f"Premium quality, ships worldwide, and trust me, you've never seen anything like this. "
        f"Don't wait, tap the link in the caption and grab yours before they're gone!",
        
        f"POV: You just found the perfect {design_hint} design you've been searching for. "
        f"This unique artwork looks amazing on every product, from stickers to apparel and home decor. "
        f"Made with premium materials, designed to last, and shipped worldwide in days. "
        f"Click the link below to make it yours today!",
        
        f"Warning! This {design_hint} design is highly addictive. "
        f"Once you see it, you'll want it on everything you own. "
        f"Available on over seventy products, with worldwide shipping and amazing quality. "
        f"Hundreds of happy customers can't be wrong. Tap the link and start shopping now!",
    ]
    return random.choice(templates)
