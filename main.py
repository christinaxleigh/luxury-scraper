"""
Main scraper orchestrator - runs the complete pipeline
"""
import schedule
import time
import logging
from datetime import datetime
from typing import List, Dict
import argparse

from models import init_db, get_session, WishlistItem, ScrapedListing
from fashionphile_scraper import FashionphileScraper
from therealreal_scraper import TheRealRealScraper
from matching_engine import MatchingEngine
from email_notifier import EmailNotifier

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LuxuryScraperOrchestrator:
    """Main orchestrator for the luxury scraper system"""
    
    def __init__(self):
        """Initialize orchestrator with all components"""
        self.scrapers = {
            'Fashionphile': FashionphileScraper(),
            'TheRealReal': TheRealRealScraper()
        }
        self.matcher = MatchingEngine(min_match_score=70.0)
        self.notifier = EmailNotifier()
        
        logger.info("Luxury Scraper Orchestrator initialized")
    
    def get_active_wishlist_items(self) -> List[Dict]:
        """
        Get all active wishlist items from database
        
        Returns:
            List of wishlist item dictionaries
        """
        client = get_session()
        try:
            result = client.table('wishlist_items').select('*').eq('active', True).execute()
            items = result.data
            logger.info(f"Found {len(items)} active wishlist items")
            return items
        finally:
            pass
    
    def build_search_params_from_wishlist(self, wishlist_items: List[Dict]) -> Dict[str, List[Dict]]:
        """
        Build search parameters for each platform from wishlist items
        
        Args:
            wishlist_items: List of wishlist item dictionaries
            
        Returns:
            Dictionary mapping platform names to search parameter lists
        """
        search_groups = {}
        
        for item in wishlist_items:
            key = (item.get('brand'), item.get('item_type') or 'all')
            if key not in search_groups:
                search_groups[key] = []
            search_groups[key].append(item)
        
        platform_searches = {
            'Fashionphile': [],
            'TheRealReal': []
        }
        
        for (brand, item_type), items in search_groups.items():
            search_param = {
                'brand': brand,
                'item_type': item_type,
                'wishlist_items': items
            }
            platform_searches['Fashionphile'].append(search_param)
            platform_searches['TheRealReal'].append(search_param)
        
        return platform_searches
    
    def get_item_type_mapping(self, item_type: str) -> str:
        """Map generic item types to platform-specific categories"""
        mapping = {
            'handbag': 'handbags',
            'bag': 'handbags',
            'purse': 'handbags',
            'wallet': 'accessories',
            'shoes': 'shoes',
            'jewelry': 'jewelry',
            'watch': 'watches',
            'clothing': 'clothing'
        }
        return mapping.get(item_type.lower(), 'women-bags')
    
    def scrape_all_platforms(self, search_params: Dict[str, List[Dict]]) -> List[Dict]:
        """
        Scrape all platforms with given search parameters
        
        Args:
            search_params: Dictionary of platform searches
            
        Returns:
            List of scraped listing dictionaries
        """
        all_listings = []
        client = get_session()
        
        try:
            for platform_name, searches in search_params.items():
                scraper = self.scrapers.get(platform_name)
                if not scraper:
                    logger.warning(f"No scraper found for {platform_name}")
                    continue
                
                logger.info(f"Scraping {platform_name} with {len(searches)} search queries...")
                
                for search in searches:
                    try:
                        results = scraper.scrape_search_results(search)
                        logger.info(f"  Found {len(results)} items for {search}")
                        
                        for result in results:
                            existing_check = client.table('scraped_listings').select('id, url').eq('url', result['url']).execute()
                            
                            if existing_check.data:
                                client.table('scraped_listings').update({
                                    'last_seen': datetime.utcnow().isoformat()
                                }).eq('url', result['url']).execute()
                                listing = existing_check.data[0]
                            else:
                                new_listing = client.table('scraped_listings').insert(result).execute()
                                listing = new_listing.data[0] if new_listing.data else result
                            
                            all_listings.append(listing)
                    
                    except Exception as e:
                        logger.error(f"Error scraping {platform_name} with {search}: {e}")
                        continue
            
            logger.info(f"Total listings scraped: {len(all_listings)}")
        
        finally:
            pass
        
        return all_listings
    
    def run_matching(self, wishlist_items: List[Dict], listings: List[Dict]) -> List[Dict]:
        """
        Run matching engine on wishlist items and listings
        
        Args:
            wishlist_items: List of wishlist item dictionaries
            listings: List of scraped listing dictionaries
            
        Returns:
            List of match dictionaries
        """
        logger.info("Running matching engine...")
        matches = self.matcher.find_matches(wishlist_items, listings)
        logger.info(f"Found {len(matches)} matches")
        return matches
    
    def send_notifications(self, matches: List[Dict]):
        """
        Send email notifications for new matches
        
        Args:
            matches: List of match dictionaries
        """
        if not matches:
            logger.info("No matches to notify")
            return
        
        logger.info(f"Sending notifications for {len(matches)} matches...")
        
        grouped_by_user = {}
        for match in matches:
            user_id = match.get('user_id')
            if user_id not in grouped_by_user:
                grouped_by_user[user_id] = []
            grouped_by_user[user_id].append(match)
        
        for user_id, user_matches in grouped_by_user.items():
            try:
                self.notifier.send_match_notification(user_id, user_matches)
                logger.info(f"Sent notification to user {user_id} for {len(user_matches)} matches")
            except Exception as e:
                logger.error(f"Error sending notification to user {user_id}: {e}")
    
    def run_full_pipeline(self):
        """Run the complete scraping and matching pipeline"""
        try:
            logger.info("=" * 50)
            logger.info("Starting luxury scraper pipeline")
            logger.info("=" * 50)
            
            wishlist_items = self.get_active_wishlist_items()
            
            if not wishlist_items:
                logger.info("No active wishlist items found. Exiting.")
                return
            
            search_params = self.build_search_params_from_wishlist(wishlist_items)
            
            listings = self.scrape_all_platforms(search_params)
            
            if not listings:
                logger.info("No listings found. Exiting.")
                return
            
            matches = self.run_matching(wishlist_items, listings)
            
            self.send_notifications(matches)
            
            logger.info("=" * 50)
            logger.info("Pipeline completed successfully")
            logger.info("=" * 50)
            
        except Exception as e:
            logger.error(f"Error in pipeline: {e}", exc_info=True)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Luxury Consignment Scraper')
    parser.add_argument('--schedule', action='store_true', help='Run on schedule')
    parser.add_argument('--interval', type=int, default=60, help='Interval in minutes')
    args = parser.parse_args()
    
    init_db()
    
    orchestrator = LuxuryScraperOrchestrator()
    
    if args.schedule:
        logger.info(f"Running on schedule: every {args.interval} minutes")
        schedule.every(args.interval).minutes.do(orchestrator.run_full_pipeline)
        
        while True:
            schedule.run_pending()
            time.sleep(60)
    else:
        logger.info("Running once")
        orchestrator.run_full_pipeline()

if __name__ == "__main__":
    main()
