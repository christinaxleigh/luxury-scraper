"""
Base scraper class with common functionality for all platform scrapers
"""
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BaseScraper:
    """Base class for all platform scrapers"""
    
    def __init__(self, platform_name: str):
        self.platform_name = platform_name
        self.ua = UserAgent()
        self.session = requests.Session()
        self.rate_limit_delay = 2  # seconds between requests
        
    def get_headers(self) -> Dict[str, str]:
        """Generate request headers with random user agent"""
        return {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
    
    def fetch_page(self, url: str) -> Optional[BeautifulSoup]:
        """
        Fetch a page and return BeautifulSoup object
        
        Args:
            url: URL to fetch
            
        Returns:
            BeautifulSoup object or None if fetch fails
        """
        try:
            logger.info(f"Fetching: {url}")
            response = self.session.get(
                url, 
                headers=self.get_headers(),
                timeout=30
            )
            response.raise_for_status()
            
            # Respect rate limits
            time.sleep(self.rate_limit_delay)

            return BeautifulSoup(response.content, 'html.parser')
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {url}: {e}")
            return None
    
    def extract_price(self, price_text: str) -> Optional[float]:
        """
        Extract numeric price from text
        
        Args:
            price_text: Text containing price (e.g., "$1,234.56")
            
        Returns:
            Float price or None
        """
        try:
            # Remove currency symbols and commas
            cleaned = price_text.replace('$', '').replace(',', '').replace('€', '').replace('£', '')
            cleaned = cleaned.strip()
            
            # Extract first number found
            import re
            match = re.search(r'\d+\.?\d*', cleaned)
            if match:
                return float(match.group())
            return None
        except (ValueError, AttributeError):
            return None
    
    def normalize_condition(self, condition_text: str) -> str:
        """
        Normalize condition text to standard values
        
        Args:
            condition_text: Raw condition text from site
            
        Returns:
            Normalized condition: 'new', 'excellent', 'good', or 'fair'
        """
        condition_lower = condition_text.lower()
        
        if 'new' in condition_lower or 'pristine' in condition_lower:
            return 'new'
        elif 'excellent' in condition_lower or 'like new' in condition_lower:
            return 'excellent'
        elif 'very good' in condition_lower or 'good' in condition_lower:
            return 'good'
        elif 'fair' in condition_lower or 'worn' in condition_lower:
            return 'fair'
        else:
            return 'good'  # default
    
    def scrape_search_results(self, search_params: Dict) -> List[Dict]:
        """
        Scrape search results - must be implemented by subclass
        
        Args:
            search_params: Dictionary with search parameters (brand, type, etc.)
            
        Returns:
            List of listing dictionaries
        """
        raise NotImplementedError("Subclass must implement scrape_search_results()")
    
    def scrape_item_details(self, url: str) -> Optional[Dict]:
        """
        Scrape detailed information for a specific item
        Must be implemented by subclass
        
        Args:
            url: URL of the item listing
            
        Returns:
            Dictionary with item details or None
        """
        raise NotImplementedError("Subclass must implement scrape_item_details()")
    
    def build_listing_dict(self, **kwargs) -> Dict:
        """
        Build standardized listing dictionary
        
        Returns:
            Dictionary with listing information
        """
        return {
            'platform': self.platform_name,
            'listing_id': kwargs.get('listing_id'),
            'url': kwargs.get('url'),
            'brand': kwargs.get('brand'),
            'title': kwargs.get('title'),
            'description': kwargs.get('description'),
            'item_type': kwargs.get('item_type'),
            'model_name': kwargs.get('model_name'),
            'size': kwargs.get('size'),
            'color': kwargs.get('color'),
            'condition': kwargs.get('condition'),
            'price': kwargs.get('price'),
            'currency': kwargs.get('currency', 'USD'),
            'original_price': kwargs.get('original_price'),
            'image_url': kwargs.get('image_url'),
            'seller_name': kwargs.get('seller_name'),
            'authenticated': kwargs.get('authenticated', False),
            'scraped_at': datetime.utcnow()
        }
