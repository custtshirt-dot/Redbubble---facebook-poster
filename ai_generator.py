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
        'funny': 'funny, witty, and humorous',
        'emotional': 'emotional, heartfelt, and touching',
        'hard_sell': 'urgent, persuasive, and sales-focused',
        'mixed': random.choice(['funny', 'emotional', 'persuasive'])
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
    
    prompt = f"""You are a professional social media marketer for a Redbubble shop.

The design is: "{design_hint}"

Create {type_instruction} that is {selected_style}. {lang_instruction}

CRITICAL: The caption MUST be ABOUT this specific design ({design_hint}).
Do NOT write generic content. Reference the actual design theme!

Structure:
1. HOOK (1-2 lines): Stop the scroll - mention the design theme
2. BODY (3-5 lines): Describe the design's appeal, build desire
3. CTA (2-3 lines): Strong call-to-action with urgency
4. Include emojis that match the design theme
5. End with: 🛒 SHOP: {url}
6. Add these hashtags: {HASHTAGS}

STRICT RULES - NEVER violate these:
- NEVER mention discount codes, promo codes, coupon codes, or percentage discounts
- NEVER write things like "Use code X", "10% off", "SAVE20", or any promotional codes
- NEVER invent prices or fake offers

Make it authentic and design-specific. Optimize for Facebook engagement.
Keep total under 500 words."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert Facebook marketing copywriter. You ALWAYS write design-specific content. You NEVER include discount codes, promo codes, or coupon codes in any caption."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=800,
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
    
    prompt = f"""You are writing a SPOKEN script for a 20-30 second Facebook Reels video about a Redbubble design.

The design is: "{design_hint}"

Write a script that follows this EXACT structure:

🔥 HOOK (3-5 seconds, ~12-15 words):
- Grab attention immediately
- Use shock, curiosity, or relatable problem
- Examples: "Stop scrolling!", "You won't believe this design...", "POV: You found..."

💪 BODY (15-20 seconds, ~50-70 words):
- Describe the design vibrantly
- Mention products it's available on (stickers, t-shirts, mugs, etc.)
- Build desire with quality, uniqueness
- Speak directly to the viewer ("you", "your")

🎯 CTA (3-5 seconds, ~10-15 words):
- Strong call-to-action
- Create urgency
- Examples: "Tap the link now!", "Get yours before they're gone!"

CRITICAL RULES:
1. Write ONLY what should be SPOKEN (no emojis, no hashtags, no formatting, no markdown)
2. Use natural conversational English
3. Keep total under 90 words (fits 25-30 seconds)
4. Use short punchy sentences
5. Add commas for natural pauses
6. Reference the design theme: {design_hint}
7. Make it ENERGETIC and ENGAGING
8. NO labels like "Hook:" or "Body:" - just flowing speech
9. NEVER mention discount codes, promo codes, coupon codes, or percentage discounts
10. NEVER say things like "Use code X", "10% off", or any promotional codes

Output ONLY the spoken text. Nothing else. No markdown. No labels."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You write punchy, engaging video scripts for social media ads. Output only spoken words with no formatting. Never mention discount codes or promo codes."},
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
