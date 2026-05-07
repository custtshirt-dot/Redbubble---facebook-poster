"""
🎬 Video Creator from Images
"""
import os
import requests
import io
from PIL import Image
from config import HEADERS

OUTPUT_DIR = 'generated_videos'
os.makedirs(OUTPUT_DIR, exist_ok=True)


def download_images(image_urls, max_imgs=10):
    """Download images locally"""
    paths = []
    for i, url in enumerate(image_urls[:max_imgs]):
        try:
            data = requests.get(url, headers=HEADERS, timeout=15).content
            img = Image.open(io.BytesIO(data)).convert('RGB')
            # Resize to 1080x1080 (square - works for both feed and reels)
            img = img.resize((1080, 1080), Image.LANCZOS)
            path = os.path.join(OUTPUT_DIR, f'img_{i}.jpg')
            img.save(path, 'JPEG', quality=90)
            paths.append(path)
        except Exception as e:
            print(f"⚠️ Failed to download {url}: {e}")
    return paths


def create_slideshow_video(image_urls, output_name='slideshow.mp4', duration_per_image=2):
    """Create slideshow video from images"""
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips
        
        print(f"🎬 Creating video from {len(image_urls)} images...")
        
        paths = download_images(image_urls, max_imgs=15)
        if not paths:
            return None
        
        clips = [ImageClip(p).set_duration(duration_per_image) for p in paths]
        video = concatenate_videoclips(clips, method='compose')
        
        output_path = os.path.join(OUTPUT_DIR, output_name)
        video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio=False,
            preset='ultrafast',
            verbose=False,
            logger=None
        )
        
        print(f"✅ Video created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Video creation failed: {e}")
        return None


def create_reels_video(image_urls, output_name='reels.mp4'):
    """Create vertical reels video (1080x1920)"""
    try:
        from moviepy.editor import ImageClip, concatenate_videoclips
        
        print(f"🎥 Creating Reels video...")
        
        paths = []
        for i, url in enumerate(image_urls[:8]):
            try:
                data = requests.get(url, headers=HEADERS, timeout=15).content
                img = Image.open(io.BytesIO(data)).convert('RGB')
                # Resize for Reels (vertical 9:16)
                img = img.resize((1080, 1920), Image.LANCZOS)
                path = os.path.join(OUTPUT_DIR, f'reel_{i}.jpg')
                img.save(path, 'JPEG', quality=90)
                paths.append(path)
            except:
                continue
        
        if not paths:
            return None
        
        clips = [ImageClip(p).set_duration(2) for p in paths]
        video = concatenate_videoclips(clips, method='compose')
        
        output_path = os.path.join(OUTPUT_DIR, output_name)
        video.write_videofile(
            output_path,
            fps=30,
            codec='libx264',
            audio=False,
            preset='ultrafast',
            verbose=False,
            logger=None
        )
        
        print(f"✅ Reels created: {output_path}")
        return output_path
        
    except Exception as e:
        print(f"❌ Reels creation failed: {e}")
        return None
