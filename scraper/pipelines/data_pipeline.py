"""
scraper/pipelines/data_pipeline.py
Three-stage pipeline: deduplication -> cleaning -> export (CSV + JSON + SQLite)
"""
import csv
import json
import logging
import re
import sqlite3
import unicodedata
from pathlib import Path
from typing import Set

from itemadapter import ItemAdapter
from scrapy import Spider
from scrapy.exceptions import DropItem
from w3lib.html import remove_tags

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage 1 - Deduplication
# ---------------------------------------------------------------------------

class DeduplicationPipeline:
    """Drop items whose link or title has already been seen in this run."""

    def __init__(self):
        self.seen: Set[str] = set()

    def process_item(self, item, spider: Spider):
        adapter = ItemAdapter(item)
        key = adapter.get("link") or adapter.get("title") or ""
        if key and key in self.seen:
            raise DropItem(f"Duplicate item: {key}")
        if key:
            self.seen.add(key)
        return item


# ---------------------------------------------------------------------------
# Stage 2 - Cleaning
# ---------------------------------------------------------------------------

class CleaningPipeline:
    """
    Clean all string fields:
      - Strip leading/trailing whitespace
      - Remove HTML tags
      - Normalize Unicode (NFC) for correct Arabic rendering
      - Collapse multiple spaces/newlines
    """

    @staticmethod
    def _clean(value: str) -> str:
        if not isinstance(value, str):
            return value
        # Remove HTML tags
        value = remove_tags(value)
        # Normalize Unicode (handles Arabic, etc.)
        value = unicodedata.normalize("NFC", value)
        # Collapse whitespace
        value = re.sub(r"\s+", " ", value).strip()
        return value

    def process_item(self, item, spider: Spider):
        adapter = ItemAdapter(item)
        for field in list(adapter.keys()):
            val = adapter[field]
            if isinstance(val, str):
                adapter[field] = self._clean(val)
        return item


# ---------------------------------------------------------------------------
# Stage 3 - Export
# ---------------------------------------------------------------------------

class ExportPipeline:
    """Write items to CSV, JSON, and SQLite based on config.yaml output settings."""

    def __init__(self):
        self.config: dict = {}
        self.csv_writer = None
        self.csv_file = None
        self.json_items: list = []
        self.db_conn: sqlite3.Connection = None
        self.db_cursor: sqlite3.Cursor = None
        self._csv_headers_written = False
        self._fieldnames: list = []

    def open_spider(self, spider: Spider):
        self.config = spider.settings.get("CONFIG", {})
        out_cfg = self.config.get("output", {})
        Path("data").mkdir(parents=True, exist_ok=True)

        if out_cfg.get("sqlite", True):
            db_path = Path("data") / out_cfg.get("db_name", "scraping.db")
            self.db_conn = sqlite3.connect(str(db_path))
            self.db_cursor = self.db_conn.cursor()
            logger.info("SQLite database opened: %s", db_path)

        if out_cfg.get("csv", True):
            self.csv_file = open("data/output.csv", "w", newline="", encoding="utf-8-sig")

        logger.info("ExportPipeline ready.")

    def close_spider(self, spider: Spider):
        out_cfg = self.config.get("output", {})

        if self.csv_file:
            self.csv_file.close()
            logger.info("CSV saved: data/output.csv (%d items)", len(self.json_items))

        if out_cfg.get("json", True) and self.json_items:
            with open("data/output.json", "w", encoding="utf-8") as f:
                json.dump(self.json_items, f, ensure_ascii=False, indent=2)
            logger.info("JSON saved: data/output.json (%d items)", len(self.json_items))

        if self.db_conn:
            self.db_conn.commit()
            self.db_conn.close()
            logger.info("SQLite committed and closed.")

    def process_item(self, item, spider: Spider):
        adapter = ItemAdapter(item)
        row = dict(adapter)
        out_cfg = self.config.get("output", {})

        # --- CSV ---
        if out_cfg.get("csv", True) and self.csv_file:
            if not self._csv_headers_written:
                self._fieldnames = list(row.keys())
                self.csv_writer = csv.DictWriter(
                    self.csv_file, fieldnames=self._fieldnames, extrasaction="ignore"
                )
                self.csv_writer.writeheader()
                self._csv_headers_written = True
            self.csv_writer.writerow({k: row.get(k, "") for k in self._fieldnames})

        # --- JSON (in-memory, flushed on close) ---
        if out_cfg.get("json", True):
            self.json_items.append(row)

        # --- SQLite ---
        if out_cfg.get("sqlite", True) and self.db_cursor:
            self._ensure_table(row)
            cols = ", ".join(row.keys())
            placeholders = ", ".join(["?"] * len(row))
            values = tuple(str(v) if v is not None else "" for v in row.values())
            try:
                self.db_cursor.execute(
                    f"INSERT OR IGNORE INTO items ({cols}) VALUES ({placeholders})",
                    values,
                )
            except sqlite3.OperationalError as exc:
                logger.error("SQLite insert error: %s", exc)

        return item

    def _ensure_table(self, row: dict):
        """Create the items table if it does not exist yet."""
        cols_def = ", ".join(
            f'"{col}" TEXT' for col in row.keys()
        )
        self.db_cursor.execute(
            f"CREATE TABLE IF NOT EXISTS items ({cols_def})"
        )
        self.db_conn.commit()
