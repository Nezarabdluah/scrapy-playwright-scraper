# Scrapy-Playwright Universal Scraper

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Scrapy](https://img.shields.io/badge/Scrapy-2.11-60A839?style=flat)
![Playwright](https://img.shields.io/badge/Playwright-1.44-2EAD33?style=flat&logo=playwright)
![License](https://img.shields.io/badge/License-MIT-yellow?style=flat)
![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=flat)
![CI](https://github.com/Nezarabdluah/scrapy-playwright-scraper/actions/workflows/ci.yml/badge.svg)

Professional universal web scraper powered by Scrapy + Playwright. Works on any website via `config.yaml` — no code changes needed.

## Features
- Universal: works on any website via config.yaml
- Full JavaScript rendering (Playwright Chromium)
- Login + session persistence
- Pagination: button, URL param, infinite scroll
- Anti-detection: UA rotation (20+), playwright-stealth, random delays
- Proxy rotation via proxies.txt
- Export: CSV + JSON + SQLite simultaneously
- Arabic text support (UTF-8 / NFC normalization)
- Debug screenshots on error

## Installation

```bash
git clone https://github.com/Nezarabdluah/scrapy-playwright-scraper.git
cd scrapy-playwright-scraper
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
copy .env.example .env
```

## Usage

```bash
python main.py
```

## Output
| File | Description |
|------|-------------|
| data/output.csv | CSV (UTF-8 BOM, opens in Excel) |
| data/output.json | JSON with Arabic support |
| data/scraping.db | SQLite database |
| logs/scraper.log | Detailed log |

## Configuration (config.yaml)

```yaml
target_url: "https://example.com/products"
selectors:
  items_list: ".product-card"
  title: "h2.title"
  price: "span.price"
  link: "a.item-link"
pagination:
  type: "button"          # button | url_param | infinite_scroll
  next_selector: "a.next"
  max_pages: 50
delays:
  min: 2.0
  max: 5.0
```

## Project Structure
```
scraper_project/
├── config.yaml              <- All settings
├── .env                     <- Credentials (gitignored)
├── main.py                  <- Entry point
├── scraper/
│   ├── spiders/main_spider.py
│   ├── middlewares/
│   │   ├── playwright_middleware.py
│   │   └── stealth_middleware.py
│   ├── pipelines/data_pipeline.py
│   └── settings.py
├── data/                    <- Output (gitignored)
└── logs/                    <- Logs (gitignored)
```

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)

## License
MIT © [Nezarabdluah](https://github.com/Nezarabdluah)
