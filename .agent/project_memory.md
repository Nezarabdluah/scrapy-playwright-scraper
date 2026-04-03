# 🧠 ذاكرة المشروع — Project Memory

## الهدف من المشروع
أداة استخراج بيانات ويب (Web Scraper) مبنية على **Scrapy + Playwright**، قادرة على:
- سحب أي بيانات من أي موقع بمجرد تعديل `config.yaml`
- تجاوز أنظمة الحماية (Cloudflare, SG-Captcha)
- تصدير البيانات بثلاثة تنسيقات تلقائياً (CSV, JSON, SQLite)
- محاكاة سلوك المستخدم البشري (scroll, mouse move, random wait)

## المعمارية العامة

```
main.py          ← نقطة الدخول الرئيسية (Scrapy CrawlerProcess)
config.yaml      ← جميع إعدادات السحب والاستخراج والتصدير

scraper/
├── spiders/
│   ├── main_spider.py           ← العنكبوت الرئيسي العام
│   └── ar_specialties_spider.py ← عنكبوت روابط قائمة menu_links.json
├── pipelines/data_pipeline.py   ← 3 مراحل: إزالة التكرار، تنظيف، تصدير
├── middlewares/                 ← StealthMiddleware + PlaywrightMiddleware
└── settings.py                  ← إعدادات Scrapy والمتصفح

run_specialties.py  ← تشغيل ar_specialties_spider مباشرة
process_courses.py  ← تنظيف الحقول المتداخلة (أسعار، مدد، تواريخ)
```

## ملاحظات تقنية مهمة
- **حالة `headless`:** يمكن تبديلها في `settings.py` → `PLAYWRIGHT_LAUNCH_OPTIONS`
  - `False` = متصفح مرئي (للمراقبة والتطوير)
  - `True`  = متصفح مخفي (للإنتاج والتشغيل السريع)
- **ترميز الـ CSV:** يُصدَّر دائماً بـ `utf-8-sig` لضمان توافق الإكسل العربي
- **تشغيل بيئة:** يجب استخدام `.\venv\Scripts\python.exe` دائماً وليس `python` مباشرة
