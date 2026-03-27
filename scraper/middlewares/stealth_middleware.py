"""
scraper/middlewares/stealth_middleware.py
Applies playwright-stealth to every Playwright page to avoid bot detection
"""
import logging

from scrapy import Spider
from scrapy.http import Request

logger = logging.getLogger(__name__)


class StealthMiddleware:
    """Middleware that applies playwright-stealth to hide automation fingerprints."""

    async def process_request(self, request: Request, spider: Spider):
        page = request.meta.get("playwright_page")
        if page is None:
            return

        try:
            from playwright_stealth import stealth_async
            await stealth_async(page)
            logger.debug("Stealth applied to page: %s", request.url)
        except ImportError:
            logger.warning("playwright-stealth not installed; skipping stealth mode")
        except Exception as exc:
            logger.warning("Could not apply stealth: %s", exc)
