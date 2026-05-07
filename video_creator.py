"""
🎬 إنشاء فيديوهات وReels من الصور
"""
import os
import requests
import io
from PIL import Image
from moviepy.editor import ImageClip, concatenate_videoclips, AudioFileClip
from config import HEADERS, VIDEO_DIR, TEMP_DIR


def download_image(url, save_path):
    """تحميل صورة من الإنترنت"""
    try:
        r = requests.get(url, headers=HEADERS, timeout=15)
        with open(save_path, 'wb') as f:
            f.write(r.content)
        return save_path
    except:
        return None


def prepare_image_for_video(image_path, size=(1080, 1920)):
    """تجهيز الصورة للفيديو (Reels = 9:16)"""
    try:
        img = Image.open(image_path).convert("RGB")
        # خلفية بيضاء
        bg = Image.new("RGB", size, (255, 255, 255))
        # تحجيم مع الحفاظ على النسبة
        img.thumbnail((size[0] - 100, size[1] - 200))
        # وضع في المنتصف
        x = (size[0] - img.width) // 2
        y = (size[1] - img.height) // 2
        bg.paste(img, (x, y))
        bg.save(image_path)
        return image_path
    except Exception as e:
        print(f"⚠️ Image prep failed: {e}")
        return image_path


def create_reels(image_urls, output_name="reel.mp4", duration_per_image=1.5):
    """
    إنشاء Reels (9:16) من الصور
    """
    print(f"\n🎥 Creating Reels from {len(image_urls)} images...")
    
    # تحميل الصور
    image_paths = []
    for i, url in enumerate(image_urls[:15]):  # أقصى 15 صورة
        path = os.path.join(TEMP_DIR, f"reel_img_{i}.jpg")
        if download_image(url, path):
            prepare_image_for_video(path, size=(1080, 1920))
            image_paths.append(path)
    
    if not image_paths:
        return None
    
    # إنشاء clips
    clips = [ImageClip(p).set_duration(duration_per_image) for p in image_paths]
    final = concatenate_videoclips(clips, method="compose")
    
    # حفظ الفيديو
    output_path = os.path.join(VIDEO_DIR, output_name)
    final.write_videofile(
        output_path,
        fps=30,
        codec='libx264',
        audio=False,
        preset='medium',
        verbose=False,
        logger=None
    )
    
    # تنظيف الصور المؤقتة
    for p in image_paths:
        try:
            os.remove(p)
        except:
            pass
    
    print(f"✅ Reels saved: {output_path}")
    return output_path


def create_video_slideshow(image_urls, output_name="video.mp4", duration_per_image=2.5):
    """
    إنشاء فيديو عادي (16:9) من الصور
    """
    print(f"\n🎬 Creating video slideshow from {len(image_urls)} images...")
    
    image_paths = []
    for i, url in enumerate(image_urls[:20]):
        path = os.path.join(TEMP_DIR, f"vid_img_{i}.jpg")
        if download_image(url, path):
            prepare_image_for_video(path, size=(1920, 1080))
            image_paths.append(path)
    
    if not image_paths:
        return None
    
    clips = [ImageClip(p).set_duration(duration_per_image) for p in image_paths]
    final = concatenate_videoclips(clips, method="compose")
    
    output_path = os.path.join(VIDEO_DIR, output_name)
    final.write_videofile(
        output_path,
        fps=24,
        codec='libx264',
        audio=False,
        preset='medium',
        verbose=False,
        logger=None
    )
    
    for p in image_paths:
        try:
            os.remove(p)
        except:
            pass
    
    print(f"✅ Video saved: {output_path}")
    return output_path
