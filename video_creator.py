"""
🎬 Professional Video Creator with Voice & Animations
Compatible with Pillow 9.5+ and 10+
"""
import os
import io
import requests
import random
from PIL import Image, ImageDraw, ImageFont
from config import HEADERS

# Fix for Pillow 10+ compatibility (add ANTIALIAS back)
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

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
    "💯 SHOP NOW",
    "🎁 LIMITED STOCK",
    "⚡ TAP THE LINK",
    "🌟 SHOP TODAY",
]

BRAND_NAME = "Custom T-shirts"


def get_font(size=60, bold=False):
    """Try to load a good font, fallback to default"""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
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
        
        # Create dark background
        background = Image.new('RGB', target_size, (15, 15, 25))
        
        img_w, img_h = img.size
        target_w, target_h = target_size
        
        # Scale to fit 85% of width
        scale = (target_w * 0.85) / img_w
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        # If too tall, scale by height
        if new_h > target_h * 0.65:
            scale = (target_h * 0.65) / img_h
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
        
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Center it (slightly above middle)
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
    
    banner_height = 120
    draw.rectangle(
        [(0, 0), (REELS_WIDTH, banner_height)],
        fill=(255, 60, 100, 230)
    )
    
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
    
    banner_top = REELS_HEIGHT - 200
    draw.rectangle(
        [(0, banner_top), (REELS_WIDTH, REELS_HEIGHT)],
        fill=(0, 200, 100, 240)
    )
    
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
    sub_text = "Link in caption"
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
            ImageClip, concatenate_videoclips, AudioFileClip
        )
        
        print(f"🎥 Creating PRO Reels video...")
        
        # Download and prepare images with banners
        prepared_images = []
        for i, url in enumerate(image_urls[:8]):
            img = download_and_prepare_image(url)
            if img:
                img = add_top_banner(img)
                cta = CTA_TEXTS[i % len(CTA_TEXTS)]
                img = add_bottom_cta(img, cta)
                
                path = os.path.join(OUTPUT_DIR, f'reel_frame_{i}.jpg')
                img.save(path, 'JPEG', quality=92)
                prepared_images.append(path)
        
        if not prepared_images:
            print("❌ No images prepared")
            return None
        
        print(f"✅ Prepared {len(prepared_images)} frames")
        
        # Determine duration from audio
        audio = None
        if voice_audio_path and os.path.exists(voice_audio_path):
            try:
                audio = AudioFileClip(voice_audio_path)
                total_duration = audio.duration
                print(f"🎙️ Voice duration: {total_duration:.1f}s")
            except Exception as e:
                print(f"⚠️ Audio load failed: {e}")
                audio = None
                total_duration = len(prepared_images) * 2.5
        else:
            total_duration = len(prepared_images) * 2.5
        
        # Per-image duration (between 2-4 seconds)
        per_image = total_duration / len(prepared_images)
        per_image = max(2.0, min(per_image, 4.0))
        
        # Create clips WITHOUT zoom (to avoid ANTIALIAS issues)
        clips = []
        for path in prepared_images:
            clip = ImageClip(path).set_duration(per_image)
            clips.append(clip)
        
        # Concatenate
        video = concatenate_videoclips(clips, method='compose')
        
        # Add audio
        if audio:
            if video.duration < audio.duration:
                # Loop video to match audio duration
                from moviepy.editor import concatenate_videoclips as concat
                loops_needed = int(audio.duration / video.duration) + 1
                video = concat([video] * loops_needed)
                video = video.subclip(0, audio.duration)
            else:
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
                
                # Add brand banner at top
                draw = ImageDraw.Draw(bg, 'RGBA')
                draw.rectangle([(0, 0), (1080, 100)], fill=(255, 60, 100, 230))
                font = get_font(45, bold=True)
                bbox = draw.textbbox((0, 0), BRAND_NAME, font=font)
                text_w = bbox[2] - bbox[0]
                draw.text(((1080 - text_w) // 2, 25), BRAND_NAME, font=font, fill=(255, 255, 255))
                
                # Add bottom CTA banner
                cta = CTA_TEXTS[i % len(CTA_TEXTS)]
                draw.rectangle([(0, 980), (1080, 1080)], fill=(0, 200, 100, 230))
                cta_font = get_font(50, bold=True)
                bbox = draw.textbbox((0, 0), cta, font=cta_font)
                cta_w = bbox[2] - bbox[0]
                draw.text(((1080 - cta_w) // 2, 1005), cta, font=cta_font, fill=(255, 255, 255))
                
                path = os.path.join(OUTPUT_DIR, f'slide_{i}.jpg')
                bg.save(path, 'JPEG', quality=90)
                paths.append(path)
            except Exception as e:
                print(f"⚠️ Slide {i} failed: {e}")
                continue
        
        if not paths:
            return None
        
        print(f"✅ Prepared {len(paths)} slides")
        
        audio = None
        if voice_audio_path and os.path.exists(voice_audio_path):
            try:
                audio = AudioFileClip(voice_audio_path)
                per_image = audio.duration / len(paths)
                per_image = max(2.0, min(per_image, 4.0))
            except Exception as e:
                print(f"⚠️ Audio load failed: {e}")
                audio = None
                per_image = 2.5
        else:
            per_image = 2.5
        
        clips = [ImageClip(p).set_duration(per_image) for p in paths]
        video = concatenate_videoclips(clips, method='compose')
        
        if audio:
            if video.duration < audio.duration:
                loops_needed = int(audio.duration / video.duration) + 1
                video = concatenate_videoclips([video] * loops_needed)
                video = video.subclip(0, audio.duration)
            else:
                video = video.subclip(0, audio.duration)
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
        import traceback
        traceback.print_exc()
        return None
