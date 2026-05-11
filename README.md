# 🚀 Redbubble Smart Auto Poster

نظام ذكي للنشر الأوتوماتيك على **Facebook + Instagram + Pinterest** من ستور Redbubble — **كل 3 ساعات** بدون تدخل منك.

---

## ✨ المميزات الجديدة (v2.0)

| الميزة | التفاصيل |
|--------|----------|
| ⏰ نشر كل 3 ساعات | أوتوماتيك بـ GitHub Actions Scheduler |
| 🤖 اختيار ذكي | يسكان الستور ويختار التصميم الجاي تلقائياً |
| 🆕 تصاميم جديدة أول | لو في تصاميم جديدة ينشرها قبل القديمة |
| 🔄 بدون تكرار | مش هيكرر نفس التصميم ورا بعضه |
| 📋 إضافة يدوية | أضف روابط معينة في `manual_products.json` |
| 🎲 تنوع في المحتوى | يدور بين album/single/link/video تلقائياً |
| 💾 حفظ الهيستوري | بيحفظ في الريبو نفسه عشان يتذكر |

---

## ⚡ Setup — 3 خطوات بس

### 1. Fork الريبو

اضغط **Fork** في الأعلى ليمين.

### 2. أضف Secrets

اروح **Settings → Secrets and Variables → Actions → New repository secret**

| Secret | القيمة | مطلوب؟ |
|--------|--------|---------|
| `FB_PAGE_ID` | ID صفحتك على فيسبوك | ✅ |
| `FB_TOKEN` | Long-lived Page Token | ✅ |
| `REDBUBBLE_STORE_URL` | `https://www.redbubble.com/people/USERNAME/shop` | ✅ |
| `GROQ_API_KEY` | مفتاح Groq AI (مجاني) | ⭐ موصى |
| `INSTAGRAM_USER_ID` | Instagram Business ID | ⬜ اختياري |
| `INSTAGRAM_TOKEN` | Instagram Token | ⬜ اختياري |
| `PINTEREST_TOKEN` | Pinterest Token | ⬜ اختياري |
| `PINTEREST_BOARD_ID` | Pinterest Board ID | ⬜ اختياري |

### 3. شغّل لأول مرة

اروح **Actions → Auto Post Every 3 Hours → Run workflow** ← اضغط **Run workflow**

بعدها هيشتغل كل 3 ساعات **تلقائياً** 🎉

---

## 📋 إضافة منتجات يدوياً

افتح ملف `manual_products.json` وأضف روابطك:

```json
{
  "products": [
    {
      "url": "https://www.redbubble.com/people/USERNAME/works/12345-my-design",
      "title": "اسم التصميم",
      "enabled": true
    },
    {
      "url": "https://www.redbubble.com/people/USERNAME/works/67890-another-design",
      "title": "تصميم تاني",
      "enabled": true
    }
  ]
}
```

> **المنتجات اليدوية بتتنشر قبل الستور أوتوماتيك ✅**

---

## 🧠 كيف الاختيار الذكي بيشتغل؟

```
كل 3 ساعات:
  ├── سكان الستور ← بيلاقي كل التصاميم
  ├── لو في تصاميم جديدة؟
  │     └── YES → انشر الجديد أول ✨
  └── مفيش جديد؟
        └── ارجع للقديم اللي اتنشر منذ أطول وقت 🔄
              └── بدون تكرار اللي اتنشر في آخر مرة
```

---

## 📁 ملفات الهيستوري

| الملف | المحتوى |
|-------|---------|
| `designs_history.json` | كل التصاميم + عدد مرات النشر + آخر تاريخ |
| `post_history.json` | تفاصيل كل بوست (ID + تاريخ + نوع) |

> ملفات الهيستوري بتتحفظ في الريبو أوتوماتيك بعد كل run.

---

## 🔧 التشغيل اليدوي

اروح **Actions → Run workflow** وعندك خيارات:

| الخيار | الوصف |
|--------|-------|
| `redbubble_url` | رابط منتج معين (override) |
| `post_type` | auto / album / single / link / video |
| `language` | english / arabic / both |
| `style` | mixed / funny / emotional / hard_sell |
| `force_post` | نشر حتى لو اتنشر مؤخراً |

---

## 🛠️ التشغيل المحلي (للتجربة)

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO
cd YOUR_REPO
pip install -r requirements.txt
cp .env.example .env
# عدّل .env وحط مفاتيحك
python main.py
```

---

## ❓ مشاكل شائعة

| المشكلة | الحل |
|---------|------|
| `FB_TOKEN expired` | جدّد الـ token من Facebook Developer |
| `Not enough images` | تأكد رابط الستور صح وعام |
| `No designs found` | تأكد USERNAME صح في الرابط |
| `Rate limited` | عادي — GitHub Actions هيحاول تاني |

---

## 📊 متابعة الأداء

شوف **Actions** في الريبو لكل run — وفيه summary بعدد التصاميم والبوستات.

---

Made with ❤️ — يشتغل على GitHub Actions مجاناً
