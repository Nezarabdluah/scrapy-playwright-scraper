# 🧠 Project Memory

## Project Goal
A professional web data scraper built on **Scrapy + Playwright**, capable of:
- Extracting structured data from any website by simply editing `config.yaml`
- Bypassing modern bot-protection systems (Cloudflare, SG-Captcha, etc.)
- Automatically exporting data in three formats: CSV, JSON, and SQLite
- Simulating real human browser behavior (scrolling, mouse movement, random delays)

## Architecture Overview

```
main.py                  ← Main entry point (Scrapy CrawlerProcess)
config.yaml              ← All scraping, extraction, and export settings

scraper/
├── spiders/
│   ├── main_spider.py           ← General-purpose spider (list & sections modes)
│   └── ar_specialties_spider.py ← Spider for scraping a list of URLs from menu_links.json
├── pipelines/data_pipeline.py   ← 3-stage pipeline: dedup → clean → export
├── middlewares/                 ← StealthMiddleware + PlaywrightMiddleware
└── settings.py                  ← Scrapy settings and browser configuration

run_specialties.py   ← Entrypoint to run ar_specialties_spider through the full pipeline
process_courses.py   ← Post-processing script to split compound fields into clean columns
```

## Key Technical Notes
- **`headless` mode:** Toggle in `settings.py` → `PLAYWRIGHT_LAUNCH_OPTIONS`
  - `False` = visible browser (recommended for development and monitoring)
  - `True`  = headless mode (recommended for production and speed)
- **CSV encoding:** Always exported as `utf-8-sig` for full Excel compatibility
- **Python environment:** Always run scripts via `.\venv\Scripts\python.exe`, not the global `python`
- **Human simulation:** Each page visit performs random mouse moves, smooth scroll stages, and random wait intervals before the DOM is read by Scrapy
