"""
🎙️ Voice Generator - Multiple FREE TTS providers with fallbacks
1. Edge TTS (Microsoft) - best quality
2. gTTS (Google) - reliable fallback
"""
import os
import asyncio
import random

OUTPUT_DIR = 'generated_videos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Edge TTS voices
EDGE_VOICES = {
    'female_energetic': 'en-US-AriaNeural',
    'female_warm': 'en-US-JennyNeural',
    'male_confident': 'en-US-GuyNeural',
    'male_casual': 'en-US-DavisNeural',
    'female_youthful': 'en-US-AnaNeural',
    'female_professional': 'en-US-MichelleNeural',
    'male_young': 'en-US-TonyNeural',
    'female_uk': 'en-GB-SoniaNeural',
    'male_uk': 'en-GB-RyanNeural',
}

# gTTS accents (fallback)
GTTS_ACCENTS = {
    'us': 'com',
    'uk': 'co.uk',
    'au': 'com.au',
    'ca': 'ca',
    'in': 'co.in',
}


async def _edge_tts_async(text, output_path, voice='en-US-AriaNeural', rate='+5%'):
    """Try Edge TTS first"""
    try:
        import edge_tts
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,
        )
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"⚠️ Edge TTS failed: {str(e)[:100]}")
        return False


def _try_edge_tts(text, output_path, voice_style='female_energetic'):
    """Attempt Edge TTS generation"""
    voice = EDGE_VOICES.get(voice_style, EDGE_VOICES['female_energetic'])
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            _edge_tts_async(text, output_path, voice)
        )
        loop.close()
        return success and os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"⚠️ Edge TTS error: {str(e)[:100]}")
        return False


def _try_gtts(text, output_path, accent='us', slow=False):
    """Fallback to Google TTS"""
    try:
        from gtts import gTTS
        tld = GTTS_ACCENTS.get(accent, 'com')
        
        tts = gTTS(text=text, lang='en', tld=tld, slow=slow)
        tts.save(output_path)
        
        return os.path.exists(output_path) and os.path.getsize(output_path) > 1000
    except Exception as e:
        print(f"⚠️ gTTS failed: {str(e)[:100]}")
        return False


def generate_voice(text, output_name='voice.mp3', voice_style='female_energetic'):
    """
    Generate human-like voice with automatic fallback
    Tries Edge TTS first, then falls back to gTTS
    """
    output_path = os.path.join(OUTPUT_DIR, output_name)
    
    # Try Edge TTS first (better quality)
    print(f"🎙️ Trying Edge TTS ({voice_style})...")
    if _try_edge_tts(text, output_path, voice_style):
        print(f"✅ Edge TTS success: {output_path}")
        return output_path
    
    # Fallback to gTTS
    print(f"🎙️ Falling back to Google TTS...")
    accent = random.choice(list(GTTS_ACCENTS.keys()))
    if _try_gtts(text, output_path, accent):
        print(f"✅ Google TTS success ({accent}): {output_path}")
        return output_path
    
    print("❌ All TTS providers failed")
    return None


def get_random_voice_style():
    """Get random voice style for variety"""
    return random.choice(list(EDGE_VOICES.keys()))
