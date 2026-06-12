"""
Base scraper class with common functionality for all platform scrapers.

Rewritten to use each platform's real data source instead of guessed HTML
selectors. Uses a realistic browser User-Agent and a shared requests session.
No Selenium and no network-dependent user-agent library (both were sources of
failure in the original proof-of-concept).
"""
import re
import time
import logging
import requests
from typing import List, Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# A current, realistic desktop Chrome UA. Static on purpose: the old code used
# fake-useragent, which fetched a UA list over the network at startup and could
# crash the worker on boot.
DEFAULT_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)


class BaseScraper:
    """Base class for all platform scrapers."""

    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.session = requests.Session()
        self.rate_limit_delay = 2  # seconds between requests
        self.timeout = 30

    def base_headers(self) -> Dict[str, str]:
        return {
            "User-Agent": DEFAULT_UA,
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    def fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[dict]:
        """GET a URL and return parsed JSON, or None on failure."""
        headers = self.base_headers()
        headers["Accept"] = "application/json, text/plain, */*"
        try:
            logger.info(f"[{self.platform_name}] GET(json) {url}")
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return resp.json()
        except (requests.exceptions.RequestException, ValueError) as e:
            logger.error(f"[{self.platform_name}] JSON fetch failed for {url}: {e}")
            return None

    def fetch_html(self, url: str, params: Optional[Dict] = None) -> Optional[str]:
        """GET a URL and return the raw HTML text, or None on failure."""
        headers = self.base_headers()
        headers["Accept"] = (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
            "image/webp,*/*;q=0.8"
        )
        try:
            logger.info(f"[{self.platform_name}] GET(html) {url}")
            resp = self.session.get(url, params=params, headers=headers, timeout=self.timeout)
            resp.raise_for_status()
            time.sleep(self.rate_limit_delay)
            return resp.text
        except requests.exceptions.RequestException as e:
            logger.error(f"[{self.platform_name}] HTML fetch failed for {url}: {e}")
            return None

    @staticmethod
    def extract_next_data(html: str) -> Optional[dict]:
        """Extract and parse the Next.js __NEXT_DATA__ JSON blob from page HTML."""
        import json
        m = re.search(
            r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.S
        )
        if not m:
            return None
        try:
            return json.loads(m.group(1))
        except ValueError:
            return None

    @staticmethod
    def parse_price(value) -> Optional[float]:
        """Parse a price from a string like '$3,745.00' or '4585.00' or a number."""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[^0-9.]", "", str(value))
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None

    @staticmethod
    def normalize_condition(condition_text: Optional[str]) -> str:
        """Normalize condition text to: 'new', 'excellent', 'good', or 'fair'."""
        if not condition_text:
            return "good"
        c = condition_text.lower()
        if "new" in c or "pristine" in c or "never" in c:
            return "new"
        if "excellent" in c or "like new" in c:
            return "excellent"
        if "very good" in c or "good" in c:
            return "good"
        if "fair" in c or "worn" in c:
            return "fair"
        return "good"

    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        raise NotImplementedError("Subclass must implement scrape_search_results()")

    def build_listing_dict(self, **kwargs) -> Dict:
        """Build a standardized listing dictionary matching the Supabase schema."""
        return {
            "platform": self.platform_name,
            "listing_id": kwargs.get("listing_id"),
            "url": kwargs.get("url"),
            "brand": kwargs.get("brand"),
            "title": kwargs.get("title"),
            "description": kwargs.get("description"),
            "item_type": kwargs.get("item_type"),
            "model_name": kwargs.get("model_name"),
            "size": kwargs.get("size"),
            "color": kwargs.get("color"),
            "condition": kwargs.get("condition"),
            "price": kwargs.get("price"),
            "currency": kwargs.get("currency", "USD"),
            "original_price": kwargs.get("original_price"),
            "image_url": kwargs.get("image_url"),
            "seller_name": kwargs.get("seller_name"),
            "authenticated": kwargs.get("authenticated", True),
        }
