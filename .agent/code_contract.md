# ⚖️ Code Contract & Standards

## 1. Execution & Environment
- Always use the project's virtual environment when running any script:
  ```powershell
  .\venv\Scripts\python.exe main.py
  ```
- Never use the global `python` command — it will not have the required dependencies.

## 2. Anti-Bot Policy
- Never use raw `urllib` or `requests` for direct scraping — these are trivially blocked by modern WAFs.
- All HTTP requests must go through **Scrapy-Playwright** with the `StealthMiddleware` active.
- Human simulation (scroll, mouse movement, random delays) is applied automatically on every page visit via `_playwright_meta()` in the main spider.

## 3. Output & Encoding
- All CSV exports must use `utf-8-sig` encoding to ensure correct column display in Excel (including multi-byte character sets).
- All exports are written to `data/<project>/<folder>/` as defined in `config.yaml`.
- Every scraping run produces three output files: `.csv`, `.json`, and `.db`.

## 4. Spider Modes
- Use `extraction_mode: "list"` in `config.yaml` for table or card-based page layouts.
- Use `extraction_mode: "sections"` for heading-based layouts (e.g., h3 followed by paragraphs).

## 5. Browser Visibility
- `headless: False` in `settings.py` → browser is visible (development/monitoring).
- `headless: True` → browser runs silently in background (production/speed).

## 6. Adding New Spiders
- All new spiders must be placed in `scraper/spiders/`.
- They must inherit from `scrapy.Spider` and use `_playwright_meta()` or equivalent Playwright meta for every request.
- Data must be yielded as plain dicts — the pipeline handles export automatically.
