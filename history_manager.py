"""
📚 History Manager - Prevent duplicate posts
Tracks what was posted to Facebook/Instagram/Pinterest
منفصل عن designs_history.json اللي بيتابع التصاميم
"""
import os
import json
import hashlib
from datetime import datetime, timedelta

HISTORY_FILE = 'post_history.json'
COOLDOWN_HOURS = 24   # ✅ تم التعديل: نفس التصميم مش هيتنشر تاني قبل 24 ساعة


def load_history() -> dict:
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_history(history: dict) -> bool:
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Failed to save post history: {e}")
        return False


def url_hash(url: str) -> str:
    return hashlib.md5(url.strip().encode()).hexdigest()[:12]


def is_duplicate(url: str, post_type: str = 'any',
                 cooldown_hours: int = COOLDOWN_HOURS) -> bool:
    """
    ✅ هل التصميم ده اتنشر مؤخراً بأي نوع بوست؟
    بيتحقق بفترة COOLDOWN_HOURS (24 ساعة افتراضياً)
    """
    if os.getenv('IGNORE_DUPLICATES', 'false').lower() == 'true':
        print("⚠️ Duplicate check IGNORED (force_post active)")
        return False

    history = load_history()
    url_h = url_hash(url)
    now = datetime.now()
    cooldown = timedelta(hours=cooldown_hours)

    # ✅ بيتحقق من كل الأنواع مش نوع واحد بس
    for key, entry in history.items():
        if not key.startswith(url_h):
            continue
        try:
            last_post = datetime.fromisoformat(entry['date'])
            if now - last_post < cooldown:
                hours_passed = int((now - last_post).total_seconds() // 3600)
                hours_left = cooldown_hours - hours_passed
                print(f"⏸️  Design posted {hours_passed}h ago — {hours_left}h cooldown remaining (type: {entry.get('type','?')})")
                return True
        except Exception as e:
            print(f"⚠️ Date parse error: {e}")
            continue

    return False


def record_post(url: str, post_type: str, post_id, design_hint: str = '') -> None:
    """تسجيل بوست ناجح"""
    history = load_history()
    key = f"{url_hash(url)}_{post_type}"

    history[key] = {
        'url': url,
        'type': post_type,
        'post_id': str(post_id),
        'design': design_hint,
        'date': datetime.now().isoformat(),
    }

    if save_history(history):
        print(f"📝 Post recorded in history")


def get_stats() -> str:
    """إحصائيات البوستات"""
    history = load_history()
    if not history:
        return "\n📊 No posts recorded yet\n"

    total = len(history)
    by_type = {}
    for item in history.values():
        t = item.get('type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1

    stats = f"\n📊 Total posts in post_history: {total}\n"
    for t, count in sorted(by_type.items()):
        stats += f"   • {t}: {count}\n"

    return stats


def clear_old_history(days: int = 30) -> int:
    """حذف السجلات الأقدم من X أيام"""
    history = load_history()
    cutoff = datetime.now() - timedelta(days=days)

    new_history = {}
    for k, v in history.items():
        try:
            if datetime.fromisoformat(v['date']) > cutoff:
                new_history[k] = v
        except Exception:
            new_history[k] = v  # keep if date invalid

    removed = len(history) - len(new_history)
    if removed > 0:
        save_history(new_history)
        print(f"🧹 Cleaned {removed} old entries from post_history")

    return removed


def list_recent_posts(limit: int = 10) -> list:
    """آخر X بوستات"""
    history = load_history()
    if not history:
        return []

    sorted_posts = sorted(
        history.values(),
        key=lambda x: x.get('date', ''),
        reverse=True
    )
    return sorted_posts[:limit]
