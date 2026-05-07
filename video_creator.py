"""
🎬 Professional Video Creator with Voice & Animations
"""
import os
import io
import requests
import random
from PIL import Image, ImageDraw, ImageFont
from config import HEADERS

OUTPUT_DIR = 'generated_videos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Reels dimensions
REELS_WIDTH = 1080
REELS_HEIGHT = 1920

# CTA texts that rotate
CTA_TEXTS = [
    "🛒 SHOP NOW",
    "👆 BUY NOW",
    "🔥 GET YOURS",
    "✨ ORDER TODAY",
    "💯 SHOP THE COLLECTION",
    "🎁 LIMITED STOCK",
    "⚡ TAP THE LINK",
    "🌟 SHOP NOW",
]

BRAND_NAME = "Custom T-shirts"


def get_font(size=60, bold=False):
    """Try to load a good font, fallback to default"""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/arial.ttf',
        'arial.ttf',
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def download_and_prepare_image(url, target_size=(REELS_WIDTH, REELS_HEIGHT)):
    """Download image and prepare for Reels"""
    try:
        data = requests.get(url, headers=HEADERS, timeout=15).content
        img = Image.open(io.BytesIO(data)).convert('RGB')
        
        # Create background
        background = Image.new('RGB', target_size, (15, 15, 25))  # Dark background
        
        # Resize image to fit nicely (centered, with padding)
        img_w, img_h = img.size
        target_w, target_h = target_size
        
        # Scale to fit 80% of width, keep aspect ratio
        scale = (target_w * 0.85) / img_w
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        # If too tall, scale by height instead
        if new_h > target_h * 0.65:
            scale = (target_h * 0.65) / img_h
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
        
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Center it (slightly above center)
        x = (target_w - new_w) // 2
        y = (target_h - new_h) // 2 - 100
        background.paste(img, (x, y))
        
        return background
    except Exception as e:
        print(f"⚠️ Image prep failed: {e}")
        return None


def add_top_banner(img, text=BRAND_NAME):
    """Add top banner with brand name"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Banner background (gradient feel)
    banner_height = 120
    draw.rectangle(
        [(0, 0), (REELS_WIDTH, banner_height)],
        fill=(255, 60, 100, 230)  # Pink/Red
    )
    
    # Brand text
    font = get_font(55, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (REELS_WIDTH - text_w) // 2
    y = (banner_height - text_h) // 2 - 10
    
    # Shadow
    draw.text((x + 3, y + 3), text, font=font, fill=(0, 0, 0, 180))
    # Main text
    draw.text((x, y), text, font=font, fill=(255, 255, 255))
    
    return img


def add_bottom_cta(img, cta_text):
    """Add bottom CTA banner"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # CTA banner
    banner_top = REELS_HEIGHT - 200
    draw.rectangle(
        [(0, banner_top), (REELS_WIDTH, REELS_HEIGHT)],
        fill=(0, 200, 100, 240)  # Green
    )
    
    # CTA text
    font = get_font(75, bold=True)
    bbox = draw.textbbox((0, 0), cta_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (REELS_WIDTH - text_w) // 2
    y = banner_top + (200 - text_h) // 2 - 15
    
    # Shadow
    draw.text((x + 4, y + 4), cta_text, font=font, fill=(0, 0, 0, 200))
    # Main
    draw.text((x, y), cta_text, font=font, fill=(255, 255, 255))
    
    # Sub text
    sub_font = get_font(35)
    sub_text = "Link in caption ⬇️"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    sub_w = bbox[2] - bbox[0]
    sub_x = (REELS_WIDTH - sub_w) // 2
    draw.text((sub_x, banner_top + 130), sub_text, font=sub_font, fill=(255, 255, 255))
    
    return img


def create_reels_video(image_urls, voice_audio_path=None, output_name='reels.mp4', script_text=''):
    """
    Create professional Reels video with:
    - Top banner (brand name)
    - Bottom CTA (rotating)
    - Voice narration
    - Smooth transitions
    """
    try:
        from moviepy.editor import (
            ImageClip, concatenate_videoclips, AudioFileClip,
            CompositeVideoClip
        )
        
        print(f"🎥 Creating PRO Reels video...")
        
        # Download and prepare images
        prepared_images = []
        for i, url in enumerate(image_urls[:8]):
            img = download_and_prepare_image(url)
            if img:
                # Add banners
                img = add_top_banner(img)
                cta = CTA_TEXTS[i % len(CTA_TEXTS)]
                img = add_bottom_cta(img, cta)
                
                # Save
                path = os.path.join(OUTPUT_DIR, f'reel_frame_{i}.jpg')
                img.save(path, 'JPEG', quality=92)
                prepared_images.append(path)
        
        if not prepared_images:
            print("❌ No images prepared")
            return None
        
        # Determine duration
        if voice_audio_path and os.path.exists(voice_audio_path):
            audio = AudioFileClip(voice_audio_path)
            total_duration = audio.duration
            print(f"🎙️ Voice duration: {total_duration:.1f}s")
        else:
            audio = None
            total_duration = len(prepared_images) * 2.5
        
        # Calculate per-image duration
        per_image = total_duration / len(prepared_images)
        per_image = max(2.0, min(per_image, 4.0))  # Between 2-4 seconds
        
        # Create clips with zoom effect
        clips = []
        for i, path in enumerate(prepared_images):
            clip = ImageClip(path).set_duration(per_image)
            
            # Add subtle zoom
            clip = clip.resize(lambda t, c=clip: 1 + 0.03 * t)
            
            clips.append(clip)
        
        # Concatenate
        video = concatenate_videoclips(clips, method='compose')
        
        # Add audio
        if audio:
            # Loop or trim video to match audio
            if video.duration < audio.duration:
                # Slow down video to match
                video = video.set_duration(audio.duration)
            else:
                # Trim video to audio
                video = video.subclip(0, audio.duration)
            
            video = video.set_audio(audio)
        
        # Export
        output_path = os.path.join(OUTPUT_DIR, output_name)
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac' if audio else None,
            preset='fast',
            verbose=False,
            logger=None,
            threads=4,
        )
        
        print(f"✅ Reels created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Reels creation failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_slideshow_video(image_urls, output_name='slideshow.mp4', voice_audio_path=None):
    """Create regular slideshow video (square, for feed)"""
    try:
        from moviepy.editor import (
            ImageClip, concatenate_videoclips, AudioFileClip
        )
        
        print(f"🎬 Creating slideshow from {len(image_urls)} images...")
        
        paths = []
        for i, url in enumerate(image_urls[:10]):
            try:
                data = requests.get(url, headers=HEADERS, timeout=15).content
                img = Image.open(io.BytesIO(data)).convert('RGB')
                
                # Square format
                bg = Image.new('RGB', (1080, 1080), (15, 15, 25))
                img.thumbnail((950, 950), Image.LANCZOS)
                x = (1080 - img.width) // 2
                y = (1080 - img.height) // 2
                bg.paste(img, (x, y))
                
                # Add brand banner
                bg = add_top_banner(bg)
                
                path = os.path.join(OUTPUT_DIR, f'slide_{i}.jpg')
                bg.save(path, 'JPEG', quality=90)
                paths.append(path)
            except:
                continue
        
        if not paths:
            return None
        
        if voice_audio_path and os.path.exists(voice_audio_path):
            audio = AudioFileClip(voice_audio_path)
            per_image = audio.duration / len(paths)
        else:
            audio = None
            per_image = 2.5
        
        clips = [ImageClip(p).set_duration(per_image) for p in paths]
        video = concatenate_videoclips(clips, method='compose')
        
        if audio:
            video = video.set_audio(audio)
        
        output_path = os.path.join(OUTPUT_DIR, output_name)
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio_codec='aac' if audio else None,
            preset='fast',
            verbose=False,
            logger=None,
        )
        
        print(f"✅ Video created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        return None
