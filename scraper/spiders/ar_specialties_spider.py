import json
import logging
from pathlib import Path

import scrapy
from scrapy import Spider
from scrapy.http import Response
from scrapy_playwright.page import PageMethod

logger = logging.getLogger(__name__)

class ArSpecialtiesSpider(Spider):
    name = "ar_specialties_spider"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = {}

    def start_requests(self):
        self.config = self.settings.get("CONFIG", {})
        links_file = Path("menu_links.json")
        if not links_file.exists():
            logger.error("menu_links.json not found!")
            return

        with open(links_file, "r", encoding="utf-8") as f:
            all_links = json.load(f)

        for item in all_links:
            name, url = item.split(": ", 1)
            name = name.strip()
            url = url.strip()
            
            # Filter
            if 'جامع' not in name and 'معهد' not in name and 'اكاديمي' not in name and 'الرئيسية' not in name:
                yield scrapy.Request(
                    url=url,
                    callback=self.parse_page,
                    meta={
                        "playwright": True,
                        "playwright_include_page": False,
                        "playwright_page_methods": [
                            # Wait for Cloudflare to vanish and H1 to appear
                            PageMethod("wait_for_timeout", 4000),
                        ],
                        "specialty_name": name,
                    },
                    dont_filter=True,
                )

    def parse_page(self, response: Response):
        name = response.meta.get("specialty_name")
        
        # Check if Cloudflare blocked it
        page_title = response.css("title::text").get("")
        if "403" in page_title or "Forbidden" in page_title or "Just a moment" in page_title:
            logger.error(f"Blocked by Cloudflare: {response.url}")
            return  # The Scrapy retry middleware will usually catch 403s before this anyway
            
        title = response.css("h1::text").get("").strip()
        if not title:
            title = name
            
        paragraphs = response.css(".entry-content p *::text, .elementor-text-editor p *::text").getall()
        # Fallback if there are no nested tags
        if not paragraphs:
            paragraphs = response.css(".entry-content p::text, .elementor-text-editor p::text").getall()

        content_parts = []
        for p in paragraphs:
            p_clean = p.strip()
            if p_clean and len(p_clean) > 20:
                content_parts.append(p_clean)
                
        description = " ".join(content_parts)
        if len(description) > 1000:
            description = description[:997] + "..."

        yield {
            "title": title if title else name,
            "url": response.url,
            "description": description
        }
