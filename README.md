# Web Data Scraper

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Scrapy](https://img.shields.io/badge/Scrapy-2.11-60A839?style=flat-square&logo=scrapy&logoColor=white)](https://scrapy.org)
[![Playwright](https://img.shields.io/badge/Playwright-enabled-2EAD33?style=flat-square&logo=playwright&logoColor=white)](https://playwright.dev)
[![License](https://img.shields.io/badge/License-MIT-lightgrey?style=flat-square)](LICENSE)

> A professional, browser-powered web scraper built on Scrapy and Playwright. Capable of bypassing modern bot-protection systems and exporting clean, structured data in three formats simultaneously.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🖥️ **Live Browser View** | Watch the browser navigate pages in real-time as the scraper runs |
| 🧠 **Human-like Simulation** | Random mouse movement, smooth scrolling, and natural wait times to evade detection |
| 🛡️ **Anti-Bot Bypass** | Automatically bypasses Cloudflare, SiteGround Captcha, and similar protection systems |
| 📦 **Triple Export** | Outputs CSV + JSON + SQLite on every single run |
| 🧹 **Smart Data Cleaning** | Splits compound fields (prices, durations, dates) into separate, structured columns |
| ⚙️ **Fully Configurable** | Control the target URL, selectors, and extraction mode entirely via `config.yaml` |

---

## 🚀 Quick Start

### Requirements
- Python 3.10+
- Dependencies listed in `requirements.txt`
- Chromium browser (installed automatically by Playwright)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Nezarabdluah/scrapy-playwright-scraper.git
cd scrapy-playwright-scraper

# 2. Create a virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install the browser
playwright install chromium
```

---

## 📖 Usage

### 1️⃣ General Web Scraping
Edit `config.yaml` with your target URL and run:
```powershell
.\venv\Scripts\python.exe main.py
```

### 2️⃣ Scrape a Custom List of Links
To scrape detailed content for pages listed in `menu_links.json`:
```powershell
.\venv\Scripts\python.exe run_specialties.py
```

### 3️⃣ Clean & Structure Raw Data
To split compound fields (e.g. `14000 MYR • 3 Years • Feb Intake`) into separate columns:
```powershell
.\venv\Scripts\python.exe process_courses.py
```

---

## ⚙️ Configuration — `config.yaml`

```yaml
target_url: "https://example.com/listing/"   # The page to scrape
base_url: "https://example.com"

output:
  project: "my_project"    # Output folder name
  folder: "results"        # Sub-folder name
  filename: "output"       # Output file base name
  csv: true
  json: true
  sqlite: true

extraction_mode: "list"    # "list" for tables/cards, "sections" for heading-based pages
```

---

## 📂 Output Structure

```
data/
└── my_project/
    └── results/
        ├── output.csv      ← Excel-ready (UTF-8 BOM, Arabic-safe)
        ├── output.json     ← API-ready
        └── output.db       ← SQLite database
```

---

## 🧰 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **Scrapy** | 2.11 | Spider framework, pipelines, and export |
| **Playwright** | Latest | Real browser rendering & JavaScript execution |
| **scrapy-playwright** | Latest | Playwright integration for Scrapy |
| **StealthMiddleware** | — | Human behavior simulation & bot detection evasion |
| **SQLite** | Built-in | Structured database output |
| **Python csv** | Built-in | Large-scale data processing and cleaning |

---

## 📄 License
This project is licensed under the [MIT License](LICENSE).
