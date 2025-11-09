"""
Matching engine to compare wishlist items with scraped listings
"""
from fuzzywuzzy import fuzz
from typing import List, Dict, Optional
import logging
from models import WishlistItem, ScrapedListing, get_session
from datetime import datetime

logger = logging.getLogger(__name__)

class MatchingEngine:
    """Match wishlist items with scraped listings"""
    
    def __init__(self, min_match_score: float = 70.0):
        """
        Initialize matching engine
        
        Args:
            min_match_score: Minimum similarity score (0-100) to consider a match
        """
        self.min_match_score = min_match_score
    
    def calculate_match_score(self, wishlist_item: WishlistItem, listing: ScrapedListing) -> float:
        """
        Calculate similarity score between wishlist item and listing
        
        Args:
            wishlist_item: WishlistItem from database
            listing: ScrapedListing from database
            
        Returns:
            Match score from 0-100
        """
        scores = []
        weights = []
        
        # Brand match (highest weight)
        if wishlist_item.brand and listing.brand:
            brand_score = fuzz.ratio(
                wishlist_item.brand.lower(),
                listing.brand.lower()
            )
            scores.append(brand_score)
            weights.append(3.0)  # 3x weight for brand
        
        # Model name match (high weight)
        if wishlist_item.model_name and listing.model_name:
            model_score = fuzz.partial_ratio(
                wishlist_item.model_name.lower(),
                listing.model_name.lower()
            )
            scores.append(model_score)
            weights.append(2.5)
        elif wishlist_item.model_name and listing.title:
            # Try matching model name against title
            model_score = fuzz.partial_ratio(
                wishlist_item.model_name.lower(),
                listing.title.lower()
            )
            scores.append(model_score)
            weights.append(2.0)
        
        # Item type match
        if wishlist_item.item_type and listing.item_type:
            type_score = fuzz.ratio(
                wishlist_item.item_type.lower(),
                listing.item_type.lower()
            )
            scores.append(type_score)
            weights.append(1.5)
        
        # Size match (exact or close)
        if wishlist_item.size and listing.size:
            size_score = 100 if wishlist_item.size.lower() == listing.size.lower() else 0
            scores.append(size_score)
            weights.append(1.0)
        
        # Color match
        if wishlist_item.color and listing.color:
            color_score = fuzz.ratio(
                wishlist_item.color.lower(),
                listing.color.lower()
            )
            scores.append(color_score)
            weights.append(1.0)
        
        # Calculate weighted average
        if not scores:
            return 0.0
        
        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)
        
        return weighted_sum / total_weight
    
    def is_price_match(self, wishlist_item: WishlistItem, listing: ScrapedListing) -> bool:
        """
        Check if listing price is within wishlist range
        
        Args:
            wishlist_item: WishlistItem from database
            listing: ScrapedListing from database
            
        Returns:
            True if price matches criteria
        """
        if not listing.price:
            return False
        
        # Convert currencies if needed (simplified - in production use proper conversion)
        listing_price = listing.price
        if listing.currency != wishlist_item.currency:
            # Simplified: assume USD for now
            # In production, use a currency conversion API
            pass
        
        # Check price range
        if wishlist_item.min_price and listing_price < wishlist_item.min_price:
            return False
        
        if wishlist_item.max_price and listing_price > wishlist_item.max_price:
            return False
        
        return True
    
    def is_condition_match(self, wishlist_item: WishlistItem, listing: ScrapedListing) -> bool:
        """
        Check if listing condition matches preferences
        
        Args:
            wishlist_item: WishlistItem from database
            listing: ScrapedListing from database
            
        Returns:
            True if condition is acceptable
        """
        if not listing.condition:
            return True  # Assume acceptable if not specified
        
        condition_lower = listing.condition.lower()
        
        if 'new' in condition_lower and not wishlist_item.condition_new:
            return False
        if 'excellent' in condition_lower and not wishlist_item.condition_excellent:
            return False
        if 'good' in condition_lower and not wishlist_item.condition_good:
            return False
        if 'fair' in condition_lower and not wishlist_item.condition_fair:
            return False
        
        return True
    
    def find_matches(self, wishlist_items: List[WishlistItem], listings: List[ScrapedListing]) -> List[Dict]:
        """
        Find matches between wishlist items and listings
        
        Args:
            wishlist_items: List of WishlistItem objects
            listings: List of ScrapedListing objects
            
        Returns:
            List of match dictionaries with scores
        """
        matches = []
        
        for wishlist_item in wishlist_items:
            if not wishlist_item.active:
                continue
            
            for listing in listings:
                # Calculate match score
                score = self.calculate_match_score(wishlist_item, listing)
                
                if score < self.min_match_score:
                    continue
                
                # Check price range
                price_match = self.is_price_match(wishlist_item, listing)
                if not price_match:
                    continue
                
                # Check condition preferences
                condition_match = self.is_condition_match(wishlist_item, listing)
                if not condition_match:
                    continue
                
                matches.append({
                    'wishlist_item': wishlist_item,
                    'listing': listing,
                    'score': score,
                    'price_match': price_match
                })
                
                logger.info(f"Match found! Score: {score:.1f} - {listing.brand} {listing.title} for ${listing.price}")
        
        # Sort by score (highest first)
        matches.sort(key=lambda x: x['score'], reverse=True)
        
        return matches
    
    def save_matches(self, matches: List[Dict]) -> int:
        """
        Save matches to database
        
        Args:
            matches: List of match dictionaries
            
        Returns:
            Number of matches saved
        """
        session = get_session()
        saved_count = 0
        
        try:
            for match_data in matches:
                wishlist_item = match_data['wishlist_item']
                listing = match_data['listing']
                
                # Check if match already exists
                existing = session.query(Match).filter_by(
                    wishlist_item_id=wishlist_item.id,
                    listing_id=listing.id
                ).first()
                
                if existing:
                    continue
                
                # Create new match
                match = Match(
                    wishlist_item_id=wishlist_item.id,
                    listing_id=listing.id,
                    match_score=match_data['score'],
                    price_within_range=match_data['price_match'],
                    notified=False
                )
                
                session.add(match)
                saved_count += 1
            
            session.commit()
            logger.info(f"Saved {saved_count} new matches to database")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving matches: {e}")
        finally:
            session.close()
        
        return saved_count

# Test matching engine
if __name__ == "__main__":
    from models import init_db
    
    # Initialize database
    init_db()
    
    # Create test data
    session = get_session()
    
    # Create test user
    from models import User
    user = User(
        email="test@example.com",
        location_country="US",
        location_state="CA"
    )
    session.add(user)
    session.commit()
    
    # Create test wishlist item
    wishlist = WishlistItem(
        user_id=user.id,
        brand="Chanel",
        item_type="handbag",
        model_name="Classic Flap",
        max_price=5000,
        condition_excellent=True,
        condition_good=True
    )
    session.add(wishlist)
    session.commit()
    
    # Create test listing
    listing = ScrapedListing(
        platform="Fashionphile",
        url="https://example.com/item",
        brand="Chanel",
        title="Chanel Classic Medium Flap Bag",
        item_type="handbag",
        model_name="Classic Flap",
        condition="excellent",
        price=4500,
        currency="USD"
    )
    session.add(listing)
    session.commit()
    
    # Test matching
    engine = MatchingEngine(min_match_score=70)
    matches = engine.find_matches([wishlist], [listing])
    
    print(f"\nFound {len(matches)} matches:")
    for match in matches:
        print(f"  Score: {match['score']:.1f}")
        print(f"  Item: {match['listing'].brand} {match['listing'].title}")
        print(f"  Price: ${match['listing'].price}")
    
    # Save matches
    saved = engine.save_matches(matches)
    print(f"\nSaved {saved} matches to database")
    
    session.close()
