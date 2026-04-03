import os
import sys
import logging
from pathlib import Path

import yaml
from dotenv import load_dotenv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

load_dotenv()

def load_config(config_path: str = "config.yaml") -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

def setup_directories():
    for d in ["data", "logs"]:
        Path(d).mkdir(parents=True, exist_ok=True)

def setup_logging(log_level: str = "INFO"):
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
    
    # Overwrite config output explicitly for specialties
    config["output"]["project"] = "your_uni"
    config["output"]["folder"] = "specialties_ar"
    config["output"]["filename"] = "specialties"

    settings = get_project_settings()
    settings.setmodule("scraper.settings")
    settings.set("CONFIG", config)

    process = CrawlerProcess(settings)
    process.crawl("ar_specialties_spider")
    process.start()

if __name__ == "__main__":
    main()
