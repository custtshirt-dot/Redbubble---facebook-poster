"""
🤖 توليد المحتوى بـ Groq AI
"""
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL
import templates
import random

client = Groq(api_key=GROQ_API_KEY)


def generate_content(post_type, product_url, product_info=""):
    """توليد محتوى احترافي حسب نوع البوست"""
    
    prompts = {
        "album": f"""You are an expert Facebook ad copywriter for Redbubble print-on-demand store.
Write a HIGH-CONVERTING Facebook album post for this product collection: {product_url}
Product info: {product_info}

Requirements:
- Strong scroll-stopping HOOK (first line must grab attention)
- Compelling BODY (build desire, mention quality, variety, worldwide shipping)
- Powerful CTA (drive clicks to buy)
- Use emojis strategically
- 12-15 viral hashtags at the end
- Include the link: {product_url}
- Total length: 150-200 words
- Tone: Exciting, urgent, friendly

Write ONLY the post text, ready to publish.""",

        "single": f"""Write a SHORT punchy Facebook caption for a SINGLE product image from Redbubble.
Product: {product_url}

Requirements:
- One killer hook line
- 2-3 benefit lines
- Strong CTA with link
- 8-10 hashtags
- Max 80 words
- Use emojis

Write ONLY the caption.""",

        "carousel": f"""Write a STORYTELLING Facebook carousel post for Redbubble.
Product: {product_url}

Requirements:
- Hook that promises a story
- Tell a mini story (problem → solution = our product)
- Build emotional connection
- End with strong CTA
- 10 hashtags
- 120-150 words

Write ONLY the post.""",

        "reels": f"""Write a VIRAL Facebook Reels caption for Redbubble product.
Product: {product_url}

Requirements:
- Trendy hook (POV, "Wait for it", "Tell me you...", etc)
- Very short (40-60 words max)
- Include trending hashtags
- Strong CTA
- Use line breaks for readability

Write ONLY the caption.""",

        "video": f"""Write a Facebook Video post caption for Redbubble showcase.
Product: {product_url}

Requirements:
- Cinematic hook
- Mention "watch till the end"
- Showcase variety of products
- CTA to shop
- 100-130 words
- 10 hashtags

Write ONLY the caption.""",

        "text": f"""Write an ENGAGING text-only Facebook post about Redbubble cat designs.
Product link: {product_url}

Requirements:
- Ask an engaging question
- Share a relatable opinion/story
- Encourage comments
- Mention link naturally
- 80-120 words
- Use emojis
- 5-8 hashtags

Write ONLY the post.""",

        "link": f"""Write a Facebook link-share caption that drives clicks.
Link: {product_url}

Requirements:
- Curiosity-driven hook
- Tease what they'll find
- Strong urgency
- Direct CTA
- 60-80 words
- 8 hashtags

Write ONLY the caption.""",

        "story": f"""Write a Facebook Story text overlay (very short).
Product: {product_url}

Requirements:
- Max 15 words
- Urgent tone
- One emoji
- "Swipe up" or "Link in bio" style CTA

Write ONLY the text."""
    }
    
    prompt = prompts.get(post_type, prompts["album"])
    
    try:
        print(f"🤖 Generating {post_type} content with Groq AI...")
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a viral Facebook marketing expert specialized in print-on-demand sales."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.9,
            max_tokens=600,
        )
        content = response.choices[0].message.content.strip()
        print(f"✅ AI generated {len(content)} characters")
        return content
    except Exception as e:
        print(f"⚠️ Groq AI failed: {e}")
        print("📋 Falling back to templates...")
        return templates.get_fallback_content(post_type, product_url)


def generate_hashtags(product_info=""):
    """توليد hashtags ذكية"""
    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{
                "role": "user",
                "content": f"Generate 15 viral Facebook hashtags for Redbubble cat product. Product info: {product_info}. Return only hashtags separated by spaces, no explanation."
            }],
            temperature=0.8,
            max_tokens=200,
        )
        return response.choices[0].message.content.strip()
    except:
        return "#Redbubble #CatLovers #FunnyCats #Stickers #CustomGifts #CatMerch #UniqueGifts #CatMom #CatDad #GiftIdeas #CatHumor #StickerShop #Pawsome #CatsOfFacebook #TripodCat"
