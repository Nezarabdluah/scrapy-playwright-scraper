# 📖 Usage Guide

## Running the Main Scraper
Configure your target in `config.yaml`, then run:
```powershell
.\venv\Scripts\python.exe main.py
```

## Scraping a Custom List of URLs
Add your URLs to `menu_links.json` (one per line, format: `Name: https://url`), then run:
```powershell
.\venv\Scripts\python.exe run_specialties.py
```

## Cleaning & Structuring Raw Data
After scraping, split compound text fields into clean columns:
```powershell
.\venv\Scripts\python.exe process_courses.py
```

## Output Location
All extracted files are saved to `data/<project>/<folder>/` as defined in `config.yaml`:
- `output.csv`  → Excel-compatible (UTF-8 BOM)
- `output.json` → API-ready
- `output.db`   → SQLite database

## Live Browser Monitoring
The browser window is visible by default during scraping.
To run silently (headless), set `"headless": True` in `scraper/settings.py`.
