"""
main.py - Entry point for the scraper
Run: python main.py
"""
import os
import sys
import logging
import subprocess
from pathlib import Path

import yaml
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Load environment variables from .env
load_dotenv()

def load_config(config_path: str = "config.yaml") -> dict:
    """Load YAML configuration file."""
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def setup_directories():
    """Ensure required output directories exist."""
    for d in ["data", "logs"]:
        Path(d).mkdir(parents=True, exist_ok=True)

def setup_logging(log_level: str = "INFO"):
    """Configure root logger to file + console."""
    log_file = Path("logs/scraper.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

def main():
    config = load_config()
    setup_directories()
    setup_logging(config.get("log_level", "INFO"))
    logger = logging.getLogger("main")
    logger.info("Starting scraper...")

    # Inject credentials from .env into config
    if config.get("auth", {}).get("enabled"):
        config["auth"]["username"] = os.getenv("SCRAPER_USERNAME", "")
        config["auth"]["password"] = os.getenv("SCRAPER_PASSWORD", "")

    # Build Scrapy settings
    settings = get_project_settings()
    settings.setmodule("scraper.settings")
    settings.set("CONFIG", config)

    # Override robots.txt based on config
    settings.set(
        "ROBOTSTXT_OBEY",
        config.get("respect_robots_txt", False),
        priority="cmdline",
    )

    process = CrawlerProcess(settings)
    process.crawl("main_spider")
    process.start()
    logger.info("Scraping finished. Check data/ and logs/ directories.")

if __name__ == "__main__":
    main()
