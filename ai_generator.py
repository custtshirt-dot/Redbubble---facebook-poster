"""
🤖 AI Caption Generator using Groq
"""
from groq import Groq
from config import GROQ_API_KEY, LANGUAGE, STYLE
from templates import get_template_caption, HASHTAGS
import random

client = None
if GROQ_API_KEY:
    try:
        client = Groq(api_key=GROQ_API_KEY)
        print("✅ Groq AI initialized")
    except Exception as e:
        print(f"⚠️ Groq init failed: {e}")


def generate_ai_caption(post_type='album', url='', design_hint='cat design'):
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
        'reels': 'a short Facebook Reels video caption (max 100 chars hook)',
        'video': 'a Facebook video post caption',
        'text': 'a text-only engagement post asking a question',
        'link': 'a link post driving clicks to the shop',
        'carousel': 'a carousel post telling a story',
    }.get(post_type, 'a Facebook post')
    
    prompt = f"""You are a professional social media marketer for a Redbubble shop selling {design_hint}.

Create {type_instruction} that is {selected_style}. {lang_instruction}

Structure:
1. HOOK (1-2 lines): Stop the scroll with curiosity, shock, or relatability
2. BODY (3-5 lines): Build desire - features, benefits, social proof
3. CTA (2-3 lines): Strong call-to-action with urgency
4. Include emojis naturally
5. End with: 🛒 SHOP: {url}
6. Add these hashtags at the end: {HASHTAGS}

Make it feel authentic, not salesy. Optimize for Facebook algorithm (engagement, comments, shares).
Keep total under 500 words. Use line breaks for readability."""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are an expert Facebook marketing copywriter that creates viral, high-converting posts."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=800,
        )
        
        caption = response.choices[0].message.content.strip()
        print("✅ AI caption generated successfully")
        return caption
        
    except Exception as e:
        print(f"⚠️ AI failed: {e}. Using template instead.")
        return get_template_caption(STYLE, url, post_type)


def generate_design_hint(image_url):
    """Extract design hint from image URL"""
    url_lower = image_url.lower()
    hints = []
    if 'cat' in url_lower: hints.append('cats')
    if 'tripod' in url_lower: hints.append('tripod cats')
    if 'funny' in url_lower: hints.append('humor')
    if 'horror' in url_lower or 'spooky' in url_lower: hints.append('horror/spooky')
    if 'retro' in url_lower: hints.append('retro')
    return ', '.join(hints) if hints else 'unique designs'
