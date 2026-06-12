"""
TheRealReal scraper.

TheRealReal is a Next.js app. Its shop/search pages server-render the full
product result set into a <script id="__NEXT_DATA__"> JSON blob at:
    props.pageProps.serverResult.data.products.edges[].node

Each node carries name, brand (brandUnion.name), attributes (condition, color,
style), price (final/original with usdCents), availability, url, sku and images.
We fetch the search HTML and parse that JSON. This replaces the original
placeholder that scraped guessed HTML classes and always returned zero results.
"""
from base_scraper import BaseScraper
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class TheRealRealScraper(BaseScraper):
    """Scraper for TheRealReal.com (Next.js storefront)."""

    def __init__(self):
        super().__init__("TheRealReal")
        self.base_url = "https://www.therealreal.com"
        self.rate_limit_delay = 3

    # Map generic wishlist item types to TheRealReal shop categories.
    CATEGORY_MAP = {
        "handbag": "women/handbags",
        "bag": "women/handbags",
        "purse": "women/handbags",
        "wallet": "women/handbags",
        "shoes": "women/shoes",
        "jewelry": "women/jewelry",
        "watch": "women/jewelry/watches",
        "clothing": "women/clothing",
    }

    def build_search_url(self, item_type: str = "") -> str:
        category = self.CATEGORY_MAP.get((item_type or "").lower(), "women/handbags")
        return f"{self.base_url}/shop/{category}"

    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        """
        Args:
            search_params: {
                'brand': 'Chanel',
                'model': 'Classic Flap',  # optional, folded into keywords
                'item_type': 'handbag',
            }
        """
        brand = search_params.get("brand", "") or ""
        model = search_params.get("model") or search_params.get("model_name") or ""
        item_type = search_params.get("item_type", "") or ""

        keywords = " ".join([p for p in [brand, model] if p]).strip()
        if not keywords:
            logger.warning("[TheRealReal] empty keywords, skipping")
            return []

        url = self.build_search_url(item_type)
        html = self.fetch_html(url, params={"keywords": keywords})
        if not html:
            return []

        data = self.extract_next_data(html)
        if not data:
            logger.error("[TheRealReal] could not find __NEXT_DATA__ in page")
            return []

        try:
            edges = (
                data["props"]["pageProps"]["serverResult"]["data"]["products"]["edges"]
            )
        except (KeyError, TypeError):
            logger.error("[TheRealReal] unexpected __NEXT_DATA__ shape")
            return []

        listings = []
        for edge in edges:
            node = edge.get("node") if isinstance(edge, dict) else None
            if not node:
                continue
            try:
                listing = self._parse_node(node)
                if listing:
                    listings.append(listing)
            except Exception as e:  # noqa: BLE001
                logger.error(f"[TheRealReal] error parsing node: {e}")
        logger.info(f"[TheRealReal] parsed {len(listings)} listings for '{keywords}'")
        return listings

    def _parse_node(self, node: Dict) -> Optional[Dict]:
        name = node.get("name")
        if not name:
            return None

        brand = None
        bu = node.get("brandUnion")
        if isinstance(bu, dict):
            brand = bu.get("name")

        # attributes -> condition, color
        condition_raw, color = None, None
        for attr in node.get("attributes", []) or []:
            atype = (attr.get("type") or "").upper()
            values = attr.get("values") or []
            if atype == "CONDITION" and values:
                condition_raw = values[0]
            elif atype == "COLOR" and values:
                color = values[0]

        # price
        price, original_price = None, None
        pr = node.get("price") or {}
        final = pr.get("final") or {}
        original = pr.get("original") or {}
        if "usdCents" in final and final["usdCents"] is not None:
            price = round(final["usdCents"] / 100.0, 2)
        else:
            price = self.parse_price(final.get("formatted"))
        if "usdCents" in original and original["usdCents"] is not None:
            original_price = round(original["usdCents"] / 100.0, 2)
        else:
            original_price = self.parse_price(original.get("formatted"))
        if original_price and price and original_price <= price:
            original_price = None

        # url
        url = node.get("url") or ""
        if url and not url.startswith("http"):
            url = self.base_url + url

        # image
        image_url = None
        images = node.get("images") or []
        if images:
            first = images[0]
            image_url = first.get("url") if isinstance(first, dict) else first

        available = (node.get("availability") or "").upper() == "AVAILABLE"

        title = f"{brand} {name}".strip() if brand else name

        return self.build_listing_dict(
            listing_id=str(node.get("sku") or node.get("id") or url.split("/")[-1]),
            url=url,
            brand=brand or "Unknown",
            title=title,
            model_name=name,
            item_type=(item_type_from_url(url) or "handbag"),
            condition=self.normalize_condition(condition_raw),
            color=color,
            price=price,
            original_price=original_price,
            currency="USD",
            image_url=image_url,
            seller_name=None,
            authenticated=True,  # TheRealReal authenticates all items
        )


def item_type_from_url(url: str) -> Optional[str]:
    if not url:
        return None
    u = url.lower()
    if "handbag" in u or "/bags/" in u:
        return "handbag"
    if "shoe" in u:
        return "shoes"
    if "jewelry" in u or "watch" in u:
        return "jewelry"
    if "clothing" in u:
        return "clothing"
    return None


if __name__ == "__main__":
    scraper = TheRealRealScraper()
    results = scraper.scrape_search_results(
        {"brand": "Chanel", "item_type": "handbag"}
    )
    print(f"Found {len(results)} items")
    if results:
        for k, v in results[0].items():
            print(f"  {k}: {v}")
