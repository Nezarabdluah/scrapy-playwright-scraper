"""
scraper/settings.py - Scrapy project settings
"""
import os

BOT_NAME = "scraper"
SPIDER_MODULES = ["scraper.spiders"]
NEWSPIDER_MODULE = "scraper.spiders"

# Playwright integration
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}
PLAYWRIGHT_BROWSER_TYPE = "chromium"
PLAYWRIGHT_LAUNCH_OPTIONS = {
    "headless": False,
    "args": [
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-blink-features=AutomationControlled",
    ],
}
PLAYWRIGHT_DEFAULT_NAVIGATION_TIMEOUT = 120000

# Twisted async reactor required by playwright
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Middlewares
SPIDER_MIDDLEWARES = {}
DOWNLOADER_MIDDLEWARES = {
    "scraper.middlewares.playwright_middleware.PlaywrightExtraMiddleware": 543,
    "scraper.middlewares.stealth_middleware.StealthMiddleware": 544,
}

# Pipelines
ITEM_PIPELINES = {
    "scraper.pipelines.data_pipeline.DeduplicationPipeline": 200,
    "scraper.pipelines.data_pipeline.CleaningPipeline": 300,
    "scraper.pipelines.data_pipeline.ExportPipeline": 400,
}

# Concurrency
CONCURRENT_REQUESTS = 1
CONCURRENT_REQUESTS_PER_DOMAIN = 1

# Retry
RETRY_ENABLED = True
RETRY_TIMES = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

# Cache (disabled in production for fresh data)
HTTPCACHE_ENABLED = False

# Encoding
FEED_EXPORT_ENCODING = "utf-8"

# Logging
LOG_LEVEL = "INFO"
LOG_FILE = "logs/scrapy.log"
LOG_ENCODING = "utf-8"
