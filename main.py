"""
Main scraper orchestrator - runs the complete pipeline
"""
import schedule
import time
import logging
from datetime import datetime
from typing import List, Dict
import argparse

from models import init_db, get_session, User, WishlistItem, ScrapedListing
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
    
    def get_active_wishlist_items(self) -> List[WishlistItem]:
        """
        Get all active wishlist items from database
        
        Returns:
            List of WishlistItem objects
        """
        session = get_session()
        try:
            items = session.query(WishlistItem).filter_by(active=True).all()
            logger.info(f"Found {len(items)} active wishlist items")
            return items
        finally:
            session.close()
    
    def build_search_params_from_wishlist(self, wishlist_items: List[WishlistItem]) -> Dict[str, List[Dict]]:
        """
        Build search parameters for each platform from wishlist items
        
        Args:
            wishlist_items: List of WishlistItem objects
            
        Returns:
            Dictionary mapping platform names to search parameter lists
        """
        # Group by brand and item type to minimize searches
        search_groups = {}
        
        for item in wishlist_items:
            key = (item.brand, item.item_type or 'all')
            if key not in search_groups:
                search_groups[key] = []
            search_groups[key].append(item)
        
        # Build search params for each platform
        platform_searches = {
            'Fashionphile': [],
            'TheRealReal': []
        }
        
        for (brand, item_type), items in search_groups.items():
            # Fashionphile search params
            platform_searches['Fashionphile'].append({
                'brand': brand,
                'item_type': item_type if item_type != 'all' else 'handbags',
                'max_pages': 2  # Limit pages to be respectful
            })
            
            # TheRealReal search params
            trr_category = self._map_item_type_to_trr_category(item_type)
            platform_searches['TheRealReal'].append({
                'brand': brand,
                'category': trr_category,
                'max_pages': 2
            })
        
        return platform_searches
    
    def _map_item_type_to_trr_category(self, item_type: str) -> str:
        """Map generic item type to TheRealReal category"""
        mapping = {
            'handbag': 'women-bags',
            'handbags': 'women-bags',
            'shoes': 'women-shoes',
            'jewelry': 'women-jewelry',
            'watch': 'jewelry-watches',
            'watches': 'jewelry-watches',
            'all': 'women-bags'
        }
        return mapping.get(item_type.lower(), 'women-bags')
    
    def scrape_all_platforms(self, search_params: Dict[str, List[Dict]]) -> List[ScrapedListing]:
        """
        Scrape all platforms with given search parameters
        
        Args:
            search_params: Dictionary of platform searches
            
        Returns:
            List of ScrapedListing objects
        """
        all_listings = []
        session = get_session()
        
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
                        
                        # Convert to ScrapedListing objects and save to DB
                        for result in results:
                            # Check if listing already exists
                            existing = session.query(ScrapedListing).filter_by(
                                platform=result['platform'],
                                url=result['url']
                            ).first()
                            
                            if existing:
                                # Update last_seen timestamp
                                existing.last_seen = datetime.utcnow()
                                listing = existing
                            else:
                                # Create new listing
                                listing = ScrapedListing(**result)
                                session.add(listing)
                            
                            all_listings.append(listing)
                        
                        session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error scraping {platform_name} with {search}: {e}")
                        continue
            
            logger.info(f"Total listings scraped: {len(all_listings)}")
            
        finally:
            session.close()
        
        return all_listings
    
    def run_matching(self, wishlist_items: List[WishlistItem], listings: List[ScrapedListing]) -> List[Dict]:
        """
        Run matching engine on wishlist items and listings
        
        Args:
            wishlist_items: List of WishlistItem objects
            listings: List of ScrapedListing objects
            
        Returns:
            List of match dictionaries
        """
        logger.info("Running matching engine...")
        matches = self.matcher.find_matches(wishlist_items, listings)
        logger.info(f"Found {len(matches)} matches")
        
        # Save matches to database
        saved = self.matcher.save_matches(matches)
        logger.info(f"Saved {saved} new matches to database")
        
        return matches
    
    def send_notifications(self) -> int:
        """
        Send notifications for all unnotified matches
        
        Returns:
            Number of notifications sent
        """
        logger.info("Sending notifications...")
        sent = self.notifier.send_notifications_for_matches()
        logger.info(f"Sent {sent} notifications")
        return sent
    
    def run_full_cycle(self):
        """Run a complete scraping cycle"""
        logger.info("="*60)
        logger.info("Starting new scraping cycle")
        logger.info("="*60)
        
        start_time = datetime.utcnow()
        
        try:
            # 1. Get active wishlist items
            wishlist_items = self.get_active_wishlist_items()
            
            if not wishlist_items:
                logger.info("No active wishlist items found. Skipping cycle.")
                return
            
            # 2. Build search parameters
            search_params = self.build_search_params_from_wishlist(wishlist_items)
            
            # 3. Scrape all platforms
            listings = self.scrape_all_platforms(search_params)
            
            # 4. Run matching
            matches = self.run_matching(wishlist_items, listings)
            
            # 5. Send notifications
            self.send_notifications()
            
            # Log summary
            duration = (datetime.utcnow() - start_time).total_seconds()
            logger.info("="*60)
            logger.info("Cycle complete!")
            logger.info(f"Duration: {duration:.1f} seconds")
            logger.info(f"Wishlist items checked: {len(wishlist_items)}")
            logger.info(f"Listings found: {len(listings)}")
            logger.info(f"Matches found: {len(matches)}")
            logger.info("="*60)
            
        except Exception as e:
            logger.error(f"Error in scraping cycle: {e}", exc_info=True)
    
    def start_scheduler(self, interval_minutes: int = 15):
        """
        Start the scheduler to run cycles periodically
        
        Args:
            interval_minutes: Minutes between cycles
        """
        logger.info(f"Starting scheduler with {interval_minutes} minute interval")
        
        # Run immediately on start
        self.run_full_cycle()
        
        # Schedule periodic runs
        schedule.every(interval_minutes).minutes.do(self.run_full_cycle)
        
        logger.info("Scheduler started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Luxury Consignment Scraper')
    parser.add_argument(
        '--mode',
        choices=['once', 'schedule'],
        default='once',
        help='Run once or start scheduler'
    )
    parser.add_argument(
        '--interval',
        type=int,
        default=15,
        help='Interval in minutes for scheduled mode'
    )
    parser.add_argument(
        '--init-db',
        action='store_true',
        help='Initialize database'
    )
    
    args = parser.parse_args()
    
    # Initialize database if requested
    if args.init_db:
        logger.info("Initializing database...")
        init_db()
        logger.info("Database initialized!")
        return
    
    # Create orchestrator
    orchestrator = LuxuryScraperOrchestrator()
    
    # Run based on mode
    if args.mode == 'once':
        logger.info("Running single scraping cycle...")
        orchestrator.run_full_cycle()
    else:
        logger.info("Starting scheduler...")
        orchestrator.start_scheduler(args.interval)

if __name__ == "__main__":
    main()
