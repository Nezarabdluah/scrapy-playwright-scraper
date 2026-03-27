"""
scraper/middlewares/playwright_middleware.py
Extra Playwright middleware: User-Agent rotation + proxy injection
"""
import logging
import random
from typing import Optional

from fake_useragent import UserAgent
from scrapy import Spider
from scrapy.http import Request, Response

logger = logging.getLogger(__name__)

# 20+ real browser User-Agent strings
FALLBACK_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 OPR/106.0.0.0",
    "Mozilla/5.0 (Linux; Android 13; SM-S918B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Mobile Safari/537.36",
]


class PlaywrightExtraMiddleware:
    """Injects random User-Agent and optional proxy into every Playwright request."""

    def __init__(self, proxy_enabled: bool = False, proxy_list: list = None):
        self.proxy_enabled = proxy_enabled
        self.proxy_list = proxy_list or []
        try:
            self._ua = UserAgent()
        except Exception:
            self._ua = None

    @classmethod
    def from_crawler(cls, crawler):
        config = crawler.settings.get("CONFIG", {})
        proxy_cfg = config.get("proxy", {})
        proxy_enabled = proxy_cfg.get("enabled", False)
        proxy_list = []
        if proxy_enabled:
            try:
                with open("proxies.txt", "r", encoding="utf-8") as f:
                    proxy_list = [line.strip() for line in f if line.strip()]
                logger.info("Loaded %d proxies from proxies.txt", len(proxy_list))
            except FileNotFoundError:
                logger.warning("proxy.enabled=true but proxies.txt not found")
        return cls(proxy_enabled=proxy_enabled, proxy_list=proxy_list)

    def _random_ua(self) -> str:
        if self._ua:
            try:
                return self._ua.random
            except Exception:
                pass
        return random.choice(FALLBACK_USER_AGENTS)

    def process_request(self, request: Request, spider: Spider):
        # Rotate User-Agent
        ua = self._random_ua()
        request.headers["User-Agent"] = ua

        # Inject proxy
        if self.proxy_enabled and self.proxy_list:
            proxy = random.choice(self.proxy_list)
            request.meta["playwright_context_kwargs"] = {
                "proxy": {"server": proxy}
            }
            logger.debug("Using proxy: %s", proxy)
