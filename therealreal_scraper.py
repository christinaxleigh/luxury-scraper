"""
The RealReal scraper - scrapes authenticated luxury items
Note: This is for educational purposes. Always check website's robots.txt and terms of service.
"""
from base_scraper import BaseScraper
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)

class TheRealRealScraper(BaseScraper):
    """Scraper for TheRealReal.com"""
    
    def __init__(self):
        super().__init__("TheRealReal")
        self.base_url = "https://www.therealreal.com"
        self.rate_limit_delay = 3  # Be respectful
    
    def build_search_url(self, brand: str = "", category: str = "", page: int = 1) -> str:
        """
        Build search URL for The RealReal
        
        Args:
            brand: Brand name
            category: Category (women-bags, jewelry, shoes, etc.)
            page: Page number
            
        Returns:
            Search URL
        """
        # The RealReal uses structure like: /shop?keywords=brand&category=women-bags
        url = f"{self.base_url}/shop"
        
        params = []
        if brand:
            params.append(f"keywords={brand.replace(' ', '+')}")
        if category:
            params.append(f"category={category}")
        if page > 1:
            params.append(f"page={page}")
        
        if params:
            url += "?" + "&".join(params)
        
        return url
    
    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        """
        Scrape The RealReal search results
        
        Args:
            search_params: {
                'brand': 'Hermes',
                'category': 'women-bags',
                'max_pages': 2
            }
            
        Returns:
            List of listing dictionaries
        """
        brand = search_params.get('brand', '')
        category = search_params.get('category', 'women-bags')
        max_pages = search_params.get('max_pages', 1)
        
        all_listings = []
        
        for page in range(1, max_pages + 1):
            url = self.build_search_url(brand, category, page)
            soup = self.fetch_page(url)
            
            if not soup:
                logger.warning(f"Failed to fetch page {page}")
                continue
            
            # The RealReal often uses JSON-LD structured data
            json_ld_scripts = soup.find_all('script', type='application/ld+json')
            
            # Also look for product cards in HTML
            product_cards = soup.find_all(['div', 'article'], class_=lambda x: x and ('product' in x.lower() or 'item' in x.lower()))
            
            logger.info(f"Found {len(product_cards)} products on page {page}")
            
            # Try to parse JSON-LD first (more reliable)
            for script in json_ld_scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and data.get('@type') == 'Product':
                        listing = self._parse_json_ld(data)
                        if listing:
                            all_listings.append(listing)
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                listing = self._parse_json_ld(item)
                                if listing:
                                    all_listings.append(listing)
                except json.JSONDecodeError:
                    continue
            
            # Parse HTML product cards as fallback
            for card in product_cards:
                try:
                    listing = self._parse_product_card(card)
                    if listing and listing['url'] not in [l['url'] for l in all_listings]:
                        all_listings.append(listing)
                except Exception as e:
                    logger.error(f"Error parsing product card: {e}")
                    continue
        
        logger.info(f"Scraped {len(all_listings)} total listings from The RealReal")
        return all_listings
    
    def _parse_json_ld(self, data: Dict) -> Optional[Dict]:
        """
        Parse JSON-LD structured data
        
        Args:
            data: JSON-LD dictionary
            
        Returns:
            Listing dictionary or None
        """
        try:
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            
            price_str = offers.get('price', '')
            price = float(price_str) if price_str else None
            
            # Extract brand
            brand_obj = data.get('brand', {})
            brand = brand_obj.get('name', 'Unknown') if isinstance(brand_obj, dict) else str(brand_obj)
            
            # Extract images
            image = data.get('image', '')
            if isinstance(image, list):
                image = image[0] if image else ''
            if isinstance(image, dict):
                image = image.get('url', '')
            
            return self.build_listing_dict(
                listing_id=data.get('sku', data.get('url', '').split('/')[-1]),
                url=data.get('url', ''),
                brand=brand,
                title=data.get('name', 'Unknown'),
                description=data.get('description', ''),
                condition=self.normalize_condition(data.get('itemCondition', 'good')),
                price=price,
                currency=offers.get('priceCurrency', 'USD'),
                image_url=image,
                authenticated=True  # TheRealReal authenticates all items
            )
            
        except Exception as e:
            logger.error(f"Error parsing JSON-LD: {e}")
            return None
    
    def _parse_product_card(self, card) -> Optional[Dict]:
        """
        Parse individual product card from search results
        
        Args:
            card: BeautifulSoup element for product card
            
        Returns:
            Listing dictionary or None
        """
        try:
            # Extract link
            link_tag = card.find('a', href=True)
            if not link_tag:
                return None
            
            url = link_tag['href']
            if not url.startswith('http'):
                url = self.base_url + url
            
            # Extract title
            title_tag = card.find(['h2', 'h3', 'h4', 'p'], class_=lambda x: x and 'title' in x.lower()) or \
                       card.find(['h2', 'h3', 'h4'])
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            # Extract brand - often in a separate element
            brand_tag = card.find(class_=lambda x: x and 'brand' in x.lower())
            brand = brand_tag.get_text(strip=True) if brand_tag else self._extract_brand_from_title(title)
            
            # Extract price
            price_tag = card.find(class_=lambda x: x and 'price' in x.lower()) or \
                       card.find('span', string=lambda x: x and '$' in str(x))
            price = None
            if price_tag:
                price = self.extract_price(price_tag.get_text())
            
            # Extract original price (if on sale)
            original_price_tag = card.find(class_=lambda x: x and 'original' in str(x).lower())
            original_price = None
            if original_price_tag:
                original_price = self.extract_price(original_price_tag.get_text())
            
            # Extract image
            img_tag = card.find('img')
            image_url = None
            if img_tag:
                image_url = img_tag.get('src') or img_tag.get('data-src') or img_tag.get('data-lazy')
            
            # Extract size (if available)
            size_tag = card.find(class_=lambda x: x and 'size' in str(x).lower())
            size = size_tag.get_text(strip=True) if size_tag else None
            
            return self.build_listing_dict(
                listing_id=url.split('/')[-1].split('?')[0],
                url=url,
                brand=brand,
                title=title,
                size=size,
                price=price,
                original_price=original_price,
                currency='USD',
                image_url=image_url,
                authenticated=True
            )
            
        except Exception as e:
            logger.error(f"Error parsing product card: {e}")
            return None
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand name from product title"""
        luxury_brands = [
            'Hermes', 'Chanel', 'Louis Vuitton', 'Gucci', 'Prada',
            'Dior', 'Fendi', 'Bottega Veneta', 'Celine', 'Valentino',
            'Saint Laurent', 'YSL', 'Balenciaga', 'Givenchy', 'Burberry',
            'Cartier', 'Rolex', 'Tiffany', 'Van Cleef', 'Bulgari'
        ]
        
        title_lower = title.lower()
        for brand in luxury_brands:
            if brand.lower() in title_lower:
                return brand
        
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
            # Try JSON-LD first
            json_ld_script = soup.find('script', type='application/ld+json')
            if json_ld_script:
                try:
                    data = json.loads(json_ld_script.string)
                    if isinstance(data, dict):
                        return self._parse_json_ld(data)
                    elif isinstance(data, list):
                        for item in data:
                            if item.get('@type') == 'Product':
                                return self._parse_json_ld(item)
                except json.JSONDecodeError:
                    pass
            
            # Fallback to HTML parsing
            title_tag = soup.find(['h1', 'h2'], class_=lambda x: x and 'product' in str(x).lower())
            title = title_tag.get_text(strip=True) if title_tag else "Unknown"
            
            brand_tag = soup.find(class_=lambda x: x and 'brand' in str(x).lower())
            brand = brand_tag.get_text(strip=True) if brand_tag else self._extract_brand_from_title(title)
            
            price_tag = soup.find(class_=lambda x: x and 'price' in str(x).lower())
            price = self.extract_price(price_tag.get_text()) if price_tag else None
            
            desc_tag = soup.find(class_=lambda x: x and 'description' in str(x).lower())
            description = desc_tag.get_text(strip=True) if desc_tag else ""
            
            condition_tag = soup.find(class_=lambda x: x and 'condition' in str(x).lower())
            condition = self.normalize_condition(
                condition_tag.get_text(strip=True) if condition_tag else 'good'
            )
            
            # Extract images
            image_tags = soup.find_all('img', class_=lambda x: x and ('product' in str(x).lower() or 'gallery' in str(x).lower()))
            images = [img.get('src') or img.get('data-src') for img in image_tags if img.get('src') or img.get('data-src')]
            
            return self.build_listing_dict(
                listing_id=url.split('/')[-1].split('?')[0],
                url=url,
                brand=brand,
                title=title,
                description=description,
                condition=condition,
                price=price,
                currency='USD',
                image_url=images[0] if images else None,
                authenticated=True
            )
            
        except Exception as e:
            logger.error(f"Error scraping item details from {url}: {e}")
            return None

# Test the scraper
if __name__ == "__main__":
    scraper = TheRealRealScraper()
    
    print("Testing The RealReal scraper...")
    results = scraper.scrape_search_results({
        'brand': 'Hermes',
        'category': 'women-bags',
        'max_pages': 1
    })
    
    print(f"\nFound {len(results)} items")
    if results:
        print("\nFirst item:")
        for key, value in results[0].items():
            print(f"  {key}: {value}")
