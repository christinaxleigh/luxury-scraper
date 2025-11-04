"""
Fashionphile scraper - scrapes luxury handbags and accessories
Note: This is for educational purposes. Always check website's robots.txt and terms of service.
"""
from base_scraper import BaseScraper
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)

class FashionphileScraper(BaseScraper):
    """Scraper for Fashionphile.com"""
    
    def __init__(self):
        super().__init__("Fashionphile")
        self.base_url = "https://www.fashionphile.com"
        self.rate_limit_delay = 3  # Be respectful with rate limiting
    
    def build_search_url(self, brand: str = "", item_type: str = "", page: int = 1) -> str:
        """
        Build search URL for Fashionphile
        
        Args:
            brand: Brand name (e.g., "chanel", "louis-vuitton")
            item_type: Item type (e.g., "handbags", "jewelry")
            page: Page number
            
        Returns:
            Search URL
        """
        # Fashionphile URL structure: /shop/{category}?brand={brand}&page={page}
        brand_slug = brand.lower().replace(' ', '-')
        type_slug = item_type.lower().replace(' ', '-') if item_type else 'all'
        
        url = f"{self.base_url}/shop/{type_slug}"
        
        params = []
        if brand:
            params.append(f"brand={brand_slug}")
        if page > 1:
            params.append(f"page={page}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        """
        Scrape Fashionphile search results
        
        Args:
            search_params: {
                'brand': 'Chanel',
                'item_type': 'handbags',
                'max_pages': 2
            }
            
        Returns:
            List of listing dictionaries
        """
        brand = search_params.get('brand', '')
        item_type = search_params.get('item_type', '')
        max_pages = search_params.get('max_pages', 1)
        
        all_listings = []
        
        for page in range(1, max_pages + 1):
            url = self.build_search_url(brand, item_type, page)
            soup = self.fetch_page(url)
            
            if not soup:
                logger.warning(f"Failed to fetch page {page}")
                continue
            
            # Find product listings
            # Note: This is a simplified example - actual selectors may differ
            product_cards = soup.find_all('div', class_='product-card') or \
                          soup.find_all('div', class_='product-item') or \
                          soup.find_all('article', class_='product')
            
            logger.info(f"Found {len(product_cards)} products on page {page}")
            
            for card in product_cards:
                try:
                    listing = self._parse_product_card(card)
                    if listing:
                        all_listings.append(listing)
                except Exception as e:
                    logger.error(f"Error parsing product card: {e}")
                    continue
        
        logger.info(f"Scraped {len(all_listings)} total listings from Fashionphile")
        return all_listings
    
    def _parse_product_card(self, card) -> Optional[Dict]:
        """
        Parse individual product card from search results
        
        Args:
            card: BeautifulSoup element for product card
            
        Returns:
            Listing dictionary or None
        """
        try:
            # Extract link and title
            link_tag = card.find('a', href=True)
            if not link_tag:
                return None
            
            url = link_tag['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Extract title
            title_tag = card.find(['h2', 'h3', 'h4']) or \
                       card.find(class_=['product-title', 'product-name'])
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # Extract price
            price_tag = card.find(class_=['price', 'product-price']) or \
                       card.find('span', string=lambda x: x and '$' in x)
            price = None
            if price_tag:
                price = self.extract_price(price_tag.get_text())
            
            # Extract image
            img_tag = card.find('img')
            image_url = img_tag.get('src') or img_tag.get('data-src') if img_tag else None
            
            # Extract condition
            condition_tag = card.find(class_=['condition', 'item-condition'])
            condition = self.normalize_condition(
                condition_tag.get_text(strip=True) if condition_tag else 'good'
            )
            
            # Try to extract brand from title if not already known
            brand = self._extract_brand_from_title(title)
            
            return self.build_listing_dict(
                listing_id=url.split('/')[-1],
                url=url,
                brand=brand,
                title=title,
                item_type='handbag',  # Default for Fashionphile
                condition=condition,
                price=price,
                currency='USD',
                image_url=image_url,
                authenticated=True  # Fashionphile authenticates all items
            )
            
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand name from product title"""
        luxury_brands = [
            'Chanel', 'Louis Vuitton', 'Hermes', 'Gucci', 'Prada',
            'Dior', 'Fendi', 'Bottega Veneta', 'Celine', 'Valentino',
            'Saint Laurent', 'Balenciaga', 'Givenchy', 'Burberry'
        ]
        
        title_lower = title.lower()
        for brand in luxury_brands:
            if brand.lower() in title_lower:
                return brand
        
        # Default: take first word
        return title.split()[0] if title else "Unknown"
    
    def scrape_item_details(self, url: str) -> Optional[Dict]:
        """
        Scrape detailed information for a specific item
        
        Args:
            url: URL of the item listing
            
        Returns:
            Dictionary with detailed item information
        """
        soup = self.fetch_page(url)
        if not soup:
            return None
        
        try:
            # Extract title
            title_tag = soup.find(['h1', 'h2'], class_=['product-title', 'item-title'])
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # Extract price
            price_tag = soup.find(class_=['price', 'product-price', 'current-price'])
            price = self.extract_price(price_tag.get_text()) if price_tag else None
            
            # Extract description
            desc_tag = soup.find(class_=['description', 'product-description'])
            description = desc_tag.get_text(strip=True) if desc_tag else ""
            
            # Extract condition
            condition_tag = soup.find(class_='condition') or \
                          soup.find(string=lambda x: x and 'condition' in x.lower())
            condition = self.normalize_condition(
                condition_tag.get_text(strip=True) if condition_tag else 'good'
            )
            
            # Extract specifications
            specs = {}
            spec_section = soup.find(class_=['specifications', 'product-details'])
            if spec_section:
                spec_items = spec_section.find_all(['li', 'div'])
                for item in spec_items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        specs[key.strip().lower()] = value.strip()
            
            # Extract images
            image_tags = soup.find_all('img', class_=['product-image', 'gallery-image'])
            images = [img.get('src') or img.get('data-src') for img in image_tags if img.get('src') or img.get('data-src')]
            
            return self.build_listing_dict(
                listing_id=url.split('/')[-1],
                url=url,
                brand=self._extract_brand_from_title(title),
                title=title,
                description=description,
                condition=condition,
                price=price,
                currency='USD',
                image_url=images[0] if images else None,
                size=specs.get('size'),
                color=specs.get('color'),
                authenticated=True
            )
            
        except Exception as e:
            logger.error(f"Error scraping item details from {url}: {e}")
            return None

# Test the scraper
if __name__ == "__main__":
    scraper = FashionphileScraper()
    
    # Test search
    print("Testing Fashionphile scraper...")
    results = scraper.scrape_search_results({
        'brand': 'Chanel',
        'item_type': 'handbags',
        'max_pages': 1
    })
    
    print(f"\nFound {len(results)} items")
    if results:
        print("\nFirst item:")
        for key, value in results[0].items():
            print(f"  {key}: {value}")
