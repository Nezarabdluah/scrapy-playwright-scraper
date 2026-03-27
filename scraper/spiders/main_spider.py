"""
scraper/spiders/main_spider.py
Main Scrapy-Playwright spider - works with any website via config.yaml
"""
import asyncio
import logging
import random
import time
from pathlib import Path
from typing import Any, Generator

import scrapy
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from scrapy import Spider
from scrapy.http import Response
from scrapy_playwright.page import PageMethod

logger = logging.getLogger(__name__)


class MainSpider(Spider):
    """Universal spider powered by Playwright and configurable via config.yaml."""

    name = "main_spider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config: dict = {}
        self.page_count: int = 0
        self.session_cookies: list = []

    def start_requests(self):
        """Generate initial requests from config."""
        self.config = self.settings.get("CONFIG", {})
        cfg = self.config

        target_url = cfg.get("target_url", "")
        if not target_url:
            logger.error("target_url is not set in config.yaml")
            return

        auth_cfg = cfg.get("auth", {})
        if auth_cfg.get("enabled") and cfg.get("login_url"):
            # Start with login page
            yield scrapy.Request(
                url=cfg["login_url"],
                callback=self.do_login,
                meta=self._playwright_meta(wait_selector=auth_cfg.get("username_field")),
                errback=self.handle_error,
                dont_filter=True,
            )
        else:
            # Go directly to target
            yield scrapy.Request(
                url=target_url,
                callback=self.parse_page,
                meta=self._playwright_meta(),
                errback=self.handle_error,
                dont_filter=True,
            )

    # ------------------------------------------------------------------
    # Authentication
    # ------------------------------------------------------------------

    async def do_login(self, response: Response):
        """Handle login form submission via Playwright."""
        auth_cfg = self.config.get("auth", {})
        page: Page = response.meta["playwright_page"]

        try:
            username = auth_cfg.get("username", "")
            password = auth_cfg.get("password", "")
            user_field = auth_cfg.get("username_field", "username")
            pass_field = auth_cfg.get("password_field", "password")
            submit_sel = auth_cfg.get("submit_selector", "button[type=submit]")
            success_sel = auth_cfg.get("success_selector", "body")

            await page.fill(f"[name={user_field}]", username)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.fill(f"[name={pass_field}]", password)
            await asyncio.sleep(random.uniform(0.5, 1.5))
            await page.click(submit_sel)

            # Wait for post-login redirect
            await page.wait_for_selector(success_sel, timeout=15000)
            logger.info("Login successful.")

            # Store session cookies
            self.session_cookies = await page.context.cookies()
        except PlaywrightTimeoutError:
            logger.error("Login timed out - check selectors in config.yaml")
            await self._screenshot(page, "login_error")
        finally:
            await page.close()

        # Proceed to target URL after login
        yield scrapy.Request(
            url=self.config["target_url"],
            callback=self.parse_page,
            meta=self._playwright_meta(),
            cookies={c["name"]: c["value"] for c in self.session_cookies},
            errback=self.handle_error,
            dont_filter=True,
        )

    # ------------------------------------------------------------------
    # Main parser
    # ------------------------------------------------------------------

    async def parse_page(self, response: Response):
        """Parse items from page and handle pagination."""
        page: Page = response.meta["playwright_page"]
        cfg = self.config
        sel_cfg = cfg.get("selectors", {})
        pag_cfg = cfg.get("pagination", {})
        delay_cfg = cfg.get("delays", {})
        max_pages = pag_cfg.get("max_pages", 50)

        self.page_count += 1
        logger.info("Parsing page %d: %s", self.page_count, response.url)

        try:
            # Wait for items to appear
            wait_sel = cfg.get("wait", {}).get("selector", sel_cfg.get("items_list", "body"))
            wait_timeout = cfg.get("wait", {}).get("timeout", 30000)
            await page.wait_for_selector(wait_sel, timeout=wait_timeout)

            # Extract items
            items_sel = sel_cfg.get("items_list", "")
            item_elements = await page.query_selector_all(items_sel) if items_sel else []

            if not item_elements:
                logger.warning("No items found on page %d with selector: %s", self.page_count, items_sel)
                await page.close()
                return

            for el in item_elements:
                item = {}
                item["url"] = response.url
                item["page_number"] = self.page_count

                # Extract each field
                for field in ["title", "description", "price", "date", "image"]:
                    field_sel = sel_cfg.get(field, "")
                    if field_sel:
                        try:
                            child = await el.query_selector(field_sel)
                            if child:
                                if field == "image":
                                    item[field] = await child.get_attribute("src") or ""
                                else:
                                    item[field] = await child.inner_text() or ""
                            else:
                                item[field] = ""
                        except Exception:
                            item[field] = ""
                    else:
                        item[field] = ""

                # Extract link
                link_sel = sel_cfg.get("link", "a")
                try:
                    link_el = await el.query_selector(link_sel)
                    if link_el:
                        href = await link_el.get_attribute("href") or ""
                        item["link"] = response.urljoin(href)
                    else:
                        item["link"] = ""
                except Exception:
                    item["link"] = ""

                yield item

            # ----- Pagination -----
            if self.page_count >= max_pages:
                logger.info("Reached max_pages limit (%d). Stopping.", max_pages)
                await page.close()
                return

            pag_type = pag_cfg.get("type", "button")
            delay_min = delay_cfg.get("min", 2.0)
            delay_max = delay_cfg.get("max", 5.0)
            await asyncio.sleep(random.uniform(delay_min, delay_max))

            if pag_type == "button":
                next_sel = pag_cfg.get("next_selector", "")
                if next_sel:
                    next_btn = await page.query_selector(next_sel)
                    if next_btn:
                        next_url = await next_btn.get_attribute("href")
                        if next_url:
                            await page.close()
                            yield scrapy.Request(
                                url=response.urljoin(next_url),
                                callback=self.parse_page,
                                meta=self._playwright_meta(),
                                errback=self.handle_error,
                            )
                            return
                        else:
                            # Click the button (JS navigation)
                            await next_btn.click()
                            await page.wait_for_load_state("networkidle", timeout=15000)
                            new_url = page.url
                            await page.close()
                            yield scrapy.Request(
                                url=new_url,
                                callback=self.parse_page,
                                meta=self._playwright_meta(),
                                errback=self.handle_error,
                            )
                            return
                    else:
                        logger.info("No next page button found. Pagination complete.")

            elif pag_type == "url_param":
                param = pag_cfg.get("url_param", "page")
                next_page_num = self.page_count + 1
                from urllib.parse import urlparse, urlencode, parse_qs, urlunparse
                parsed = urlparse(response.url)
                params = parse_qs(parsed.query)
                params[param] = [str(next_page_num)]
                new_query = urlencode({k: v[0] for k, v in params.items()})
                new_url = urlunparse(parsed._replace(query=new_query))
                await page.close()
                yield scrapy.Request(
                    url=new_url,
                    callback=self.parse_page,
                    meta=self._playwright_meta(),
                    errback=self.handle_error,
                )
                return

            elif pag_type == "infinite_scroll":
                # Scroll down and check for new content
                prev_height = await page.evaluate("document.body.scrollHeight")
                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(random.uniform(delay_min, delay_max))
                new_height = await page.evaluate("document.body.scrollHeight")
                if new_height > prev_height:
                    # More content loaded - continue on same page
                    await page.close()
                    yield scrapy.Request(
                        url=response.url,
                        callback=self.parse_page,
                        meta=self._playwright_meta(),
                        errback=self.handle_error,
                        dont_filter=True,
                    )
                    return
                else:
                    logger.info("Infinite scroll reached end of content.")

        except PlaywrightTimeoutError:
            logger.error("Timeout waiting for content on page %d", self.page_count)
            await self._screenshot(page, f"timeout_page_{self.page_count}")
        except Exception as exc:
            logger.exception("Unexpected error on page %d: %s", self.page_count, exc)
            await self._screenshot(page, f"error_page_{self.page_count}")
        finally:
            try:
                await page.close()
            except Exception:
                pass

    # ------------------------------------------------------------------
    # Error handler
    # ------------------------------------------------------------------

    def handle_error(self, failure):
        logger.error("Request failed: %s", failure.value)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _playwright_meta(self, wait_selector: str = None) -> dict:
        """Build Playwright meta dict for Scrapy requests."""
        cfg = self.config
        wait_sel = wait_selector or cfg.get("wait", {}).get("selector", "body")
        headless = cfg.get("browser", {}).get("headless", True)
        width = cfg.get("browser", {}).get("viewport_width", 1920)
        height = cfg.get("browser", {}).get("viewport_height", 1080)

        return {
            "playwright": True,
            "playwright_include_page": True,
            "playwright_page_methods": [
                PageMethod("set_viewport_size", {"width": width, "height": height}),
            ],
            "playwright_browser_launch_options": {"headless": headless},
        }

    @staticmethod
    async def _screenshot(page: Page, name: str):
        """Save a debug screenshot."""
        path = Path("logs") / f"{name}.png"
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            await page.screenshot(path=str(path), full_page=True)
            logger.info("Screenshot saved: %s", path)
        except Exception as e:
            logger.warning("Could not save screenshot: %s", e)
