"""
🎬 Professional Video Creator V2 - Improved Design
"""
import os
import io
import requests
import random
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from config import HEADERS

# Fix for Pillow compatibility
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

OUTPUT_DIR = 'generated_videos'
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Reels dimensions (vertical 9:16)
REELS_WIDTH = 1080
REELS_HEIGHT = 1920

# Safe zones for Facebook UI
TOP_SAFE_ZONE = 250      # Reserved for top banner + status bar
BOTTOM_SAFE_ZONE = 400   # Reserved for bottom CTA + FB controls
IMAGE_AREA_HEIGHT = REELS_HEIGHT - TOP_SAFE_ZONE - BOTTOM_SAFE_ZONE

# CTA texts (NO emojis - using text only for compatibility)
CTA_TEXTS = [
    "SHOP NOW",
    "BUY NOW", 
    "GET YOURS",
    "ORDER TODAY",
    "SHOP THE COLLECTION",
    "GRAB YOURS",
    "TAP THE LINK",
    "DON'T MISS OUT",
]

BRAND_NAME = "Custom T-shirts"


def get_font(size=60, bold=False):
    """Load font with fallbacks"""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
        '/System/Library/Fonts/Helvetica.ttc',
        'C:/Windows/Fonts/arial.ttf',
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()


def download_and_prepare_image(url):
    """Download image and prepare for Reels - properly centered in safe area"""
    try:
        data = requests.get(url, headers=HEADERS, timeout=15).content
        img = Image.open(io.BytesIO(data)).convert('RGB')
        
        # Create gradient background (purple to dark)
        background = create_gradient_background()
        
        img_w, img_h = img.size
        
        # Calculate target size for image (fits in safe zone)
        max_width = int(REELS_WIDTH * 0.85)
        max_height = int(IMAGE_AREA_HEIGHT * 0.95)
        
        # Maintain aspect ratio
        scale = min(max_width / img_w, max_height / img_h)
        new_w = int(img_w * scale)
        new_h = int(img_h * scale)
        
        img = img.resize((new_w, new_h), Image.LANCZOS)
        
        # Center horizontally, place in middle of safe zone
        x = (REELS_WIDTH - new_w) // 2
        y = TOP_SAFE_ZONE + (IMAGE_AREA_HEIGHT - new_h) // 2
        
        # Add white rounded background for the image
        padding = 30
        bg_box = Image.new('RGB', (new_w + padding * 2, new_h + padding * 2), (255, 255, 255))
        background.paste(bg_box, (x - padding, y - padding))
        
        # Paste main image
        background.paste(img, (x, y))
        
        return background
    except Exception as e:
        print(f"⚠️ Image prep failed: {e}")
        return None


def create_gradient_background():
    """Create a beautiful gradient background"""
    bg = Image.new('RGB', (REELS_WIDTH, REELS_HEIGHT), (20, 20, 35))
    
    # Random gradient color combinations
    gradients = [
        ((75, 0, 130), (20, 20, 50)),      # Purple to dark
        ((128, 0, 128), (25, 25, 60)),     # Magenta to dark
        ((25, 25, 60), (75, 0, 130)),      # Dark to purple
        ((0, 50, 100), (20, 20, 40)),      # Blue to dark
        ((40, 0, 60), (15, 15, 30)),       # Deep purple
    ]
    
    color_top, color_bottom = random.choice(gradients)
    
    # Create vertical gradient
    draw = ImageDraw.Draw(bg)
    for y in range(REELS_HEIGHT):
        ratio = y / REELS_HEIGHT
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        draw.line([(0, y), (REELS_WIDTH, y)], fill=(r, g, b))
    
    return bg


def add_top_banner(img, text=BRAND_NAME):
    """Add professional top banner"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # Banner with gradient effect
    banner_height = 160
    
    # Main banner (solid color)
    draw.rectangle(
        [(0, 0), (REELS_WIDTH, banner_height)],
        fill=(255, 60, 100, 245)
    )
    
    # Bottom accent line
    draw.rectangle(
        [(0, banner_height - 6), (REELS_WIDTH, banner_height)],
        fill=(255, 215, 0, 255)  # Gold accent
    )
    
    # Brand name text
    font = get_font(70, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (REELS_WIDTH - text_w) // 2
    y = (banner_height - text_h) // 2 - 5
    
    # Shadow effect
    for offset in [(4, 4), (3, 3)]:
        draw.text((x + offset[0], y + offset[1]), text, font=font, fill=(0, 0, 0, 200))
    
    # Main text (white)
    draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))
    
    # Tagline below brand
    tagline_font = get_font(32)
    tagline = "Premium Custom Designs"
    bbox = draw.textbbox((0, 0), tagline, font=tagline_font)
    tag_w = bbox[2] - bbox[0]
    draw.text(
        ((REELS_WIDTH - tag_w) // 2, banner_height - 50),
        tagline,
        font=tagline_font,
        fill=(255, 255, 255, 220)
    )
    
    return img


def add_bottom_cta(img, cta_text):
    """Add professional bottom CTA banner"""
    draw = ImageDraw.Draw(img, 'RGBA')
    
    # CTA banner positioned ABOVE Facebook UI controls
    banner_height = 280
    banner_top = REELS_HEIGHT - banner_height - 100  # Leave space for FB controls
    
    # Background with gradient feel
    draw.rectangle(
        [(0, banner_top), (REELS_WIDTH, banner_top + banner_height)],
        fill=(0, 200, 100, 250)
    )
    
    # Top accent line
    draw.rectangle(
        [(0, banner_top), (REELS_WIDTH, banner_top + 8)],
        fill=(255, 215, 0, 255)
    )
    
    # Arrow indicator (pointing down)
    arrow_y = banner_top + 30
    draw.polygon([
        (REELS_WIDTH // 2 - 30, arrow_y),
        (REELS_WIDTH // 2 + 30, arrow_y),
        (REELS_WIDTH // 2, arrow_y + 30)
    ], fill=(255, 255, 255, 255))
    
    # Main CTA text
    font = get_font(95, bold=True)
    bbox = draw.textbbox((0, 0), cta_text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (REELS_WIDTH - text_w) // 2
    y = banner_top + 90
    
    # Strong shadow
    for offset in [(5, 5), (4, 4), (3, 3)]:
        draw.text((x + offset[0], y + offset[1]), cta_text, font=font, fill=(0, 0, 0, 220))
    
    # Main text
    draw.text((x, y), cta_text, font=font, fill=(255, 255, 255, 255))
    
    # Sub text
    sub_font = get_font(42, bold=True)
    sub_text = "LINK IN CAPTION"
    bbox = draw.textbbox((0, 0), sub_text, font=sub_font)
    sub_w = bbox[2] - bbox[0]
    sub_x = (REELS_WIDTH - sub_w) // 2
    sub_y = banner_top + banner_height - 60
    
    draw.text((sub_x + 2, sub_y + 2), sub_text, font=sub_font, fill=(0, 0, 0, 180))
    draw.text((sub_x, sub_y), sub_text, font=sub_font, fill=(255, 255, 255, 255))
    
    return img


def create_reels_video(image_urls, voice_audio_path=None, output_name='reels.mp4', script_text=''):
    """Create professional Reels video"""
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
                img.save(path, 'JPEG', quality=95)
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
                total_duration = len(prepared_images) * 3.0
        else:
            total_duration = len(prepared_images) * 3.0
        
        # Per-image duration
        per_image = total_duration / len(prepared_images)
        per_image = max(2.5, min(per_image, 4.0))
        
        # Create clips
        clips = []
        for path in prepared_images:
            clip = ImageClip(path).set_duration(per_image)
            clips.append(clip)
        
        # Concatenate
        video = concatenate_videoclips(clips, method='compose')
        
        # Add audio
        if audio:
            if video.duration < audio.duration:
                loops_needed = int(audio.duration / video.duration) + 1
                video = concatenate_videoclips([video] * loops_needed)
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
    """Create square slideshow video for feed"""
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
                size = 1080
                bg = Image.new('RGB', (size, size), (20, 20, 35))
                
                # Resize image
                img.thumbnail((900, 900), Image.LANCZOS)
                x = (size - img.width) // 2
                y = (size - img.height) // 2
                
                # White background for image
                white_bg = Image.new('RGB', (img.width + 40, img.height + 40), (255, 255, 255))
                bg.paste(white_bg, (x - 20, y - 20))
                bg.paste(img, (x, y))
                
                # Top banner
                draw = ImageDraw.Draw(bg, 'RGBA')
                draw.rectangle([(0, 0), (size, 110)], fill=(255, 60, 100, 245))
                draw.rectangle([(0, 104), (size, 110)], fill=(255, 215, 0, 255))
                
                font = get_font(55, bold=True)
                bbox = draw.textbbox((0, 0), BRAND_NAME, font=font)
                text_w = bbox[2] - bbox[0]
                draw.text(((size - text_w) // 2 + 2, 27), BRAND_NAME, font=font, fill=(0, 0, 0, 200))
                draw.text(((size - text_w) // 2, 25), BRAND_NAME, font=font, fill=(255, 255, 255))
                
                # Bottom CTA
                cta = CTA_TEXTS[i % len(CTA_TEXTS)]
                draw.rectangle([(0, 970), (size, 1080)], fill=(0, 200, 100, 245))
                draw.rectangle([(0, 970), (size, 976)], fill=(255, 215, 0, 255))
                
                cta_font = get_font(60, bold=True)
                bbox = draw.textbbox((0, 0), cta, font=cta_font)
                cta_w = bbox[2] - bbox[0]
                draw.text(((size - cta_w) // 2 + 2, 1002), cta, font=cta_font, fill=(0, 0, 0, 200))
                draw.text(((size - cta_w) // 2, 1000), cta, font=cta_font, fill=(255, 255, 255))
                
                path = os.path.join(OUTPUT_DIR, f'slide_{i}.jpg')
                bg.save(path, 'JPEG', quality=92)
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
                per_image = max(2.5, min(per_image, 4.0))
            except Exception as e:
                print(f"⚠️ Audio load failed: {e}")
                audio = None
                per_image = 3.0
        else:
            per_image = 3.0
        
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
