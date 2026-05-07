"""
📚 History Manager - Prevent duplicate posts
"""
import os
import json
import hashlib
from datetime import datetime, timedelta

HISTORY_FILE = 'post_history.json'
COOLDOWN_DAYS = 30  # Don't repost same URL for 30 days


def load_history():
    """Load posting history"""
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_history(history):
    """Save posting history"""
    try:
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"⚠️ Failed to save history: {e}")
        return False


def url_hash(url):
    """Create a unique hash for URL"""
    return hashlib.md5(url.encode()).hexdigest()[:12]


def is_duplicate(url, post_type='album', cooldown_days=COOLDOWN_DAYS):
    """Check if URL was posted recently with same type"""
    
    # Allow override via env var
    if os.getenv('IGNORE_DUPLICATES', 'false').lower() == 'true':
        print("⚠️ Duplicate check IGNORED (override active)")
        return False
    
    history = load_history()
    key = f"{url_hash(url)}_{post_type}"
    
    if key not in history:
        return False
    
    try:
        last_post = datetime.fromisoformat(history[key]['date'])
        cooldown = timedelta(days=cooldown_days)
        
        if datetime.now() - last_post < cooldown:
            days_passed = (datetime.now() - last_post).days
            days_left = cooldown_days - days_passed
            print(f"⚠️ Duplicate detected! Last posted {days_passed} days ago")
            print(f"   Cooldown: {days_left} days remaining")
            return True
    except Exception as e:
        print(f"⚠️ Date parse error: {e}")
        return False
    
    return False


def record_post(url, post_type, post_id, design_hint=''):
    """Record a successful post"""
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


def get_stats():
    """Get posting statistics"""
    history = load_history()
    if not history:
        return "📊 No posts recorded yet\n"
    
    total = len(history)
    by_type = {}
    for item in history.values():
        t = item.get('type', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
    
    stats = f"\n📊 Total posts in history: {total}\n"
    for t, count in sorted(by_type.items()):
        stats += f"   • {t}: {count}\n"
    
    return stats


def clear_old_history(days=90):
    """Remove entries older than X days"""
    history = load_history()
    cutoff = datetime.now() - timedelta(days=days)
    
    new_history = {}
    for k, v in history.items():
        try:
            if datetime.fromisoformat(v['date']) > cutoff:
                new_history[k] = v
        except:
            new_history[k] = v
    
    removed = len(history) - len(new_history)
    if removed > 0:
        save_history(new_history)
        print(f"🧹 Cleaned {removed} old entries")
    
    return removed


def list_recent_posts(limit=10):
    """Show recent posts"""
    history = load_history()
    if not history:
        return []
    
    sorted_posts = sorted(
        history.values(),
        key=lambda x: x.get('date', ''),
        reverse=True
    )
    return sorted_posts[:limit]
