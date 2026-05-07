"""
🎙️ Voice Generator using Microsoft Edge TTS (FREE)
Natural human-like voices in many languages
"""
import os
import asyncio
import edge_tts
import random

OUTPUT_DIR = 'generated_videos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Best English voices for marketing/ads
VOICES = {
    'female_energetic': 'en-US-AriaNeural',       # Energetic, friendly
    'female_warm': 'en-US-JennyNeural',           # Warm, professional
    'male_confident': 'en-US-GuyNeural',          # Confident, clear
    'male_casual': 'en-US-DavisNeural',           # Casual, modern
    'female_youthful': 'en-US-AnaNeural',         # Young, energetic
    'female_professional': 'en-US-MichelleNeural', # Professional
    'male_young': 'en-US-TonyNeural',             # Young male
    'female_uk': 'en-GB-SoniaNeural',             # British female
    'male_uk': 'en-GB-RyanNeural',                # British male
}


async def _generate_voice_async(text, output_path, voice='en-US-AriaNeural', rate='+5%'):
    """Generate voice using Edge TTS"""
    try:
        communicate = edge_tts.Communicate(
            text=text,
            voice=voice,
            rate=rate,  # Slightly faster for energy
        )
        await communicate.save(output_path)
        return True
    except Exception as e:
        print(f"❌ Voice generation failed: {e}")
        return False


def generate_voice(text, output_name='voice.mp3', voice_style='female_energetic'):
    """
    Generate human-like voice from text
    
    Args:
        text: The text to speak
        output_name: Output filename
        voice_style: One of: female_energetic, female_warm, male_confident, etc.
    """
    voice = VOICES.get(voice_style, VOICES['female_energetic'])
    output_path = os.path.join(OUTPUT_DIR, output_name)
    
    print(f"🎙️ Generating voice ({voice_style})...")
    
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success = loop.run_until_complete(
            _generate_voice_async(text, output_path, voice)
        )
        loop.close()
        
        if success and os.path.exists(output_path):
            print(f"✅ Voice saved: {output_path}")
            return output_path
        return None
    except Exception as e:
        print(f"❌ Voice error: {e}")
        return None


def get_random_voice_style():
    """Get random voice style for variety"""
    return random.choice(list(VOICES.keys()))
