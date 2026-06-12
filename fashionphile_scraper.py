"""
Fashionphile scraper.

Fashionphile runs on Shopify, which exposes a predictive-search JSON endpoint:
    /search/suggest.json?q=<query>&resources[type]=product&resources[limit]=<n>

This returns structured product data (title, vendor, price, image, url) without
needing a headless browser. This replaces the original placeholder that scraped
guessed HTML classes from a JavaScript-rendered page (and always returned zero
results).
"""
from base_scraper import BaseScraper
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class FashionphileScraper(BaseScraper):
    """Scraper for Fashionphile.com (Shopify storefront)."""

    def __init__(self):
        super().__init__("Fashionphile")
        self.base_url = "https://www.fashionphile.com"
        self.rate_limit_delay = 3

    def build_query(self, brand: str = "", model: str = "", item_type: str = "") -> str:
        parts = [p for p in [brand, model] if p]
        if not parts and item_type:
            parts = [item_type]
        return " ".join(parts).strip()

    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        """
        Args:
            search_params: {
                'brand': 'Chanel',
                'model': 'Classic Flap',   # optional
                'item_type': 'handbag',     # optional
                'limit': 10                 # optional, max ~10 for suggest API
            }
        """
        brand = search_params.get("brand", "") or ""
        model = search_params.get("model") or search_params.get("model_name") or ""
        item_type = search_params.get("item_type", "") or ""
        limit = min(int(search_params.get("limit", 10) or 10), 10)

        query = self.build_query(brand, model, item_type)
        if not query:
            logger.warning("[Fashionphile] empty query, skipping")
            return []

        url = f"{self.base_url}/search/suggest.json"
        params = {
            "q": query,
            "resources[type]": "product",
            "resources[limit]": limit,
        }
        data = self.fetch_json(url, params=params)
        if not data:
            return []

        products = (
            data.get("resources", {})
            .get("results", {})
            .get("products", [])
        )
        listings = []
        for p in products:
            try:
                listing = self._parse_product(p)
                if listing:
                    listings.append(listing)
            except Exception as e:  # noqa: BLE001 - never let one bad item kill the run
                logger.error(f"[Fashionphile] error parsing product: {e}")
        logger.info(f"[Fashionphile] parsed {len(listings)} listings for '{query}'")
        return listings

    def _parse_product(self, p: Dict) -> Optional[Dict]:
        title = p.get("title")
        if not title:
            return None

        # url may be a path ('/products/...') or absolute
        url = p.get("url") or ""
        if url and not url.startswith("http"):
            url = self.base_url + url

        # featured_image may be a string or an object with a 'url'
        img = p.get("featured_image") or p.get("image")
        if isinstance(img, dict):
            image_url = img.get("url") or img.get("src")
        else:
            image_url = img

        price = self.parse_price(p.get("price"))
        original_price = self.parse_price(
            p.get("compare_at_price_min") or p.get("compare_at_price")
        )
        if original_price and price and original_price <= price:
            original_price = None  # not a genuine markdown

        brand = p.get("vendor") or self._brand_from_title(title)

        return self.build_listing_dict(
            listing_id=str(p.get("id") or p.get("handle") or url.split("/")[-1]),
            url=url,
            brand=brand,
            title=title,
            item_type=(p.get("type") or "handbag"),
            condition="good",  # Fashionphile sells pre-owned; suggest API omits grade
            price=price,
            original_price=original_price,
            currency="USD",
            image_url=image_url,
            authenticated=True,  # Fashionphile authenticates all items
        )

    @staticmethod
    def _brand_from_title(title: str) -> str:
        brands = [
            "Chanel", "Louis Vuitton", "Hermes", "Hermès", "Gucci", "Prada",
            "Dior", "Fendi", "Bottega Veneta", "Celine", "Céline", "Valentino",
            "Saint Laurent", "Balenciaga", "Givenchy", "Burberry", "Goyard",
        ]
        tl = title.lower()
        for b in brands:
            if b.lower() in tl:
                return b
        return title.split()[0] if title else "Unknown"


if __name__ == "__main__":
    scraper = FashionphileScraper()
    results = scraper.scrape_search_results(
        {"brand": "Chanel", "model": "Classic Flap", "limit": 10}
    )
    print(f"Found {len(results)} items")
    if results:
        for k, v in results[0].items():
            print(f"  {k}: {v}")
