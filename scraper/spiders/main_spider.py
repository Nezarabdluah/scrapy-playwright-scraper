"""
scraper/spiders/main_spider.py
Main Scrapy-Playwright spider - works with any website via config.yaml
Supports two extraction modes:
  - "list": table/card-based layouts (default)
  - "sections": heading-based layouts (h3 + sibling paragraphs)
"""
import logging
import random
from typing import Any, Generator
from urllib.parse import urlparse, urlencode, parse_qs, urlunparse

import scrapy
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

    def start_requests(self):
        """Generate initial requests from config."""
        self.config = self.settings.get("CONFIG", {})
        cfg = self.config

        target_url = cfg.get("target_url", "")
        if not target_url:
            logger.error("target_url is not set in config.yaml")
            return

        yield scrapy.Request(
            url=target_url,
            callback=self.parse_page,
            meta=self._playwright_meta(),
            errback=self.handle_error,
            dont_filter=True,
        )

    # ------------------------------------------------------------------
    # Main parser - dispatches to the correct extraction mode
    # ------------------------------------------------------------------

    def parse_page(self, response: Response):
        """Parse items from Playwright-rendered page using Scrapy selectors."""
        cfg = self.config
        mode = cfg.get("extraction_mode", "list")

        self.page_count += 1
        logger.info("Parsing page %d: %s (mode=%s)", self.page_count, response.url, mode)

        if mode == "sections":
            yield from self._parse_sections(response)
        else:
            yield from self._parse_list(response)

        # ----- Pagination -----
        pag_cfg = cfg.get("pagination", {})
        max_pages = pag_cfg.get("max_pages", 50)

        if self.page_count >= max_pages:
            logger.info("Reached max_pages limit (%d). Stopping.", max_pages)
            return

        pag_type = pag_cfg.get("type", "button")

        if pag_type == "button":
            next_sel = pag_cfg.get("next_selector", "")
            if next_sel:
                next_url = response.css(f"{next_sel}::attr(href)").get()
                if next_url:
                    yield scrapy.Request(
                        url=response.urljoin(next_url),
                        callback=self.parse_page,
                        meta=self._playwright_meta(),
                        errback=self.handle_error,
                    )

        elif pag_type == "url_param":
            param = pag_cfg.get("url_param", "page")
            next_page_num = self.page_count + 1
            parsed = urlparse(response.url)
            params = parse_qs(parsed.query)
            params[param] = [str(next_page_num)]
            new_query = urlencode({k: v[0] for k, v in params.items()})
            new_url = urlunparse(parsed._replace(query=new_query))
            yield scrapy.Request(
                url=new_url,
                callback=self.parse_page,
                meta=self._playwright_meta(),
                errback=self.handle_error,
            )

    # ------------------------------------------------------------------
    # Mode: "list" - table/card-based extraction
    # ------------------------------------------------------------------

    def _parse_list(self, response: Response):
        """Extract items from table rows or card containers."""
        cfg = self.config
        sel_cfg = cfg.get("selectors", {})

        items_sel = sel_cfg.get("items_list", "")
        if not items_sel:
            logger.warning("No items_list selector configured.")
            return

        item_elements = response.css(items_sel)
        if not item_elements:
            logger.warning("No items found with selector: %s", items_sel)
            return

        logger.info("Found %d items on page %d", len(item_elements), self.page_count)

        for el in item_elements:
            item = {"url": response.url, "page_number": self.page_count}

            for field in ["title", "description", "price", "date"]:
                field_sel = sel_cfg.get(field, "")
                if field_sel:
                    # Use string(.) to get all nested text (e.g., spans inside div)
                    matched_el = el.css(field_sel)
                    if matched_el:
                        # Clean up multiple whitespaces/newlines
                        text = matched_el[0].xpath("string(.)").get("").strip()
                        import re
                        item[field] = re.sub(r'\s+', ' ', text)
                    else:
                        item[field] = ""
                else:
                    item[field] = ""

            image_sel = sel_cfg.get("image", "")
            if image_sel:
                item["image"] = el.css(f"{image_sel}::attr(src)").get("")
            else:
                item["image"] = ""

            link_sel = sel_cfg.get("link", "")
            if link_sel:
                href = el.css(f"{link_sel}::attr(href)").get("")
                item["link"] = response.urljoin(href) if href else ""
            else:
                item["link"] = ""

            if not item.get("title") and not item.get("price"):
                continue

            yield item

    # ------------------------------------------------------------------
    # Mode: "sections" - heading-based extraction (h3 + siblings)
    # ------------------------------------------------------------------

    def _parse_sections(self, response: Response):
        """Extract items from heading-based layouts (h3 with following paragraphs)."""
        cfg = self.config
        sel_cfg = cfg.get("selectors", {})
        sec_cfg = cfg.get("section_selectors", {})

        headings_sel = sel_cfg.get("items_list", "h3")
        headings = response.css(headings_sel)

        if not headings:
            logger.warning("No headings found with selector: %s", headings_sel)
            return

        logger.info("Found %d headings on page %d", len(headings), self.page_count)

        count = 0
        for heading in headings:
            # Extract title
            title_sel = sec_cfg.get("title", "a")
            title = heading.css(f"{title_sel}::text").get("").strip()
            if not title:
                title = "".join(heading.css("::text").getall()).strip()

            if not title or len(title) < 3:
                continue

            # Skip noise titles (educational consultant links, etc)
            if any(x in title for x in ["يوريوني", "خطوة بخطوة", "اضغط هنا"]):
                continue

            # Extract link
            link = heading.css(f"{title_sel}::attr(href)").get("")
            if link:
                link = response.urljoin(link)

            # --- Extract Description ---
            description_parts = []
            
            # Find the widget container (Elementor wraps everything in divs)
            # We want the sibling of the div that contains this h3
            current_node = heading
            # Go up until we find a sibling or reach entry-content
            for _ in range(5):
                following_siblings = current_node.xpath("following-sibling::*")
                if following_siblings:
                    break
                current_node = current_node.xpath("parent::*")
                if not current_node or "entry-content" in current_node.attrib.get("class", ""):
                    break

            if following_siblings:
                for sib in following_siblings:
                    tag = sib.xpath("name()").get("")
                    # Check if it's a text block (direct p or Elementor text widget)
                    is_text = tag == "p" or sib.css(".elementor-text-editor") or "elementor-widget-text-editor" in "".join(sib.xpath("@class").getall())
                    
                    if is_text:
                        text_nodes = sib.css("::text").getall()
                        text = " ".join(t.strip() for t in text_nodes if t.strip())
                        if text:
                            description_parts.append(text)
                    elif tag in ("h3", "h2", "h1") or sib.css(".elementor-widget-heading") or "elementor-widget-heading" in "".join(sib.xpath("@class").getall()):
                        # Stop at the next heading
                        break

            description = " ".join(description_parts)

            # Find "read more" link if not already found
            if not link:
                read_more_text = sec_cfg.get("read_more_text", "إقراء المزيد")
                for sib in following_siblings:
                    tag = sib.xpath("name()").get("")
                    if tag in ("h3", "h2", "h1"):
                        break
                    links = sib.css("a")
                    for a in links:
                        a_text = a.css("::text").get("")
                        if read_more_text in a_text:
                            link = response.urljoin(a.attrib.get("href", ""))
                            break

            item = {
                "url": response.url,
                "page_number": self.page_count,
                "title": title,
                "description": description[:500] if description else "",
                "link": link,
                "price": "",
                "date": "",
                "image": "",
            }

            count += 1
            yield item

        logger.info("Extracted %d universities from page %d", count, self.page_count)

    # ------------------------------------------------------------------
    # Error handler
    # ------------------------------------------------------------------

    def handle_error(self, failure):
        logger.error("Request failed: %s", failure.value)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _playwright_meta(self) -> dict:
        """Build Playwright meta dict for Scrapy requests."""
        import random
        cfg = self.config
        wait_sel = cfg.get("wait", {}).get("selector", "body")
        wait_timeout = cfg.get("wait", {}).get("timeout", 30000)
        width = cfg.get("browser", {}).get("viewport_width", 1920)
        height = cfg.get("browser", {}).get("viewport_height", 1080)

        goto_kwargs = {
            "wait_until": cfg.get("playwright_options", {}).get("wait_until", "domcontentloaded"),
            "timeout": cfg.get("playwright_options", {}).get("timeout", 60000)
        }

        return {
            "playwright": True,
            "playwright_include_page": False,
            "playwright_page_methods": [
                PageMethod("set_viewport_size", {"width": width, "height": height}),
                PageMethod("wait_for_selector", wait_sel, timeout=wait_timeout),
                # ---- Human-like behavior ----
                # Move mouse to a random position on the page
                PageMethod("mouse.move", random.randint(300, 900), random.randint(200, 500)),
                # Pause like a human reading the top of the page
                PageMethod("wait_for_timeout", random.randint(800, 1800)),
                # Scroll down slowly (simulate reading / browsing)
                PageMethod("evaluate", "window.scrollTo({top: document.body.scrollHeight * 0.3, behavior: 'smooth'})"),
                PageMethod("wait_for_timeout", random.randint(700, 1400)),
                PageMethod("evaluate", "window.scrollTo({top: document.body.scrollHeight * 0.65, behavior: 'smooth'})"),
                PageMethod("wait_for_timeout", random.randint(700, 1400)),
                PageMethod("evaluate", "window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'})"),
                PageMethod("wait_for_timeout", random.randint(500, 1000)),
                # Scroll back to top before Scrapy reads the DOM
                PageMethod("evaluate", "window.scrollTo({top: 0, behavior: 'smooth'})"),
                PageMethod("wait_for_timeout", random.randint(400, 800)),
            ],
            "playwright_page_goto_kwargs": goto_kwargs,
        }
