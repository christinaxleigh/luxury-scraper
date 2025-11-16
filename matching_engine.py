"""
Matching engine to compare wishlist items with scraped listings
"""
from fuzzywuzzy import fuzz
from typing import List, Dict, Optional
import logging
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
    
    def calculate_match_score(self, wishlist_item: dict, listing: dict) -> float:
        """
        Calculate similarity score between wishlist item and listing

        Args:
            wishlist_item: Wishlist item dictionary from database
            listing: Scraped listing dictionary from database

        Returns:
            Match score from 0-100
        """
        scores = []
        weights = []

        # Brand match (highest weight)
        w_brand = wishlist_item.get('brand')
        l_brand = listing.get('brand')
        if w_brand and l_brand:
            brand_score = fuzz.ratio(
                w_brand.lower(),
                l_brand.lower()
            )
            scores.append(brand_score)
            weights.append(3.0)  # 3x weight for brand

        # Model name match (high weight)
        w_model = wishlist_item.get('model_name')
        l_model = listing.get('model_name')
        l_title = listing.get('title')

        if w_model and l_model:
            model_score = fuzz.partial_ratio(
                w_model.lower(),
                l_model.lower()
            )
            scores.append(model_score)
            weights.append(2.5)
        elif w_model and l_title:
            # Try matching model name against title
            model_score = fuzz.partial_ratio(
                w_model.lower(),
                l_title.lower()
            )
            scores.append(model_score)
            weights.append(2.0)

        # Item type match
        w_type = wishlist_item.get('item_type')
        l_type = listing.get('item_type')
        if w_type and l_type:
            type_score = fuzz.ratio(
                w_type.lower(),
                l_type.lower()
            )
            scores.append(type_score)
            weights.append(1.5)

        # Size match (exact or close)
        w_size = wishlist_item.get('size')
        l_size = listing.get('size')
        if w_size and l_size:
            size_score = 100 if w_size.lower() == l_size.lower() else 0
            scores.append(size_score)
            weights.append(1.0)

        # Color match
        w_color = wishlist_item.get('color')
        l_color = listing.get('color')
        if w_color and l_color:
            color_score = fuzz.ratio(
                w_color.lower(),
                l_color.lower()
            )
            scores.append(color_score)
            weights.append(1.0)

        # Calculate weighted average
        if not scores:
            return 0.0

        weighted_sum = sum(s * w for s, w in zip(scores, weights))
        total_weight = sum(weights)

        return weighted_sum / total_weight
    
    def is_price_match(self, wishlist_item: dict, listing: dict) -> bool:
        """
        Check if listing price is within wishlist range

        Args:
            wishlist_item: Wishlist item dictionary from database
            listing: Scraped listing dictionary from database

        Returns:
            True if price matches criteria
        """
        listing_price = listing.get('price')
        if not listing_price:
            return False

        # Convert currencies if needed (simplified - in production use proper conversion)
        listing_currency = listing.get('currency', 'USD')
        wishlist_currency = wishlist_item.get('currency', 'USD')
        if listing_currency != wishlist_currency:
            # Simplified: assume USD for now
            # In production, use a currency conversion API
            pass

        # Check price range
        min_price = wishlist_item.get('min_price')
        max_price = wishlist_item.get('max_price')

        if min_price and listing_price < min_price:
            return False

        if max_price and listing_price > max_price:
            return False

        return True
    
    def is_condition_match(self, wishlist_item: dict, listing: dict) -> bool:
        """
        Check if listing condition matches preferences

        Args:
            wishlist_item: Wishlist item dictionary from database
            listing: Scraped listing dictionary from database

        Returns:
            True if condition is acceptable
        """
        condition = listing.get('condition')
        if not condition:
            return True  # Assume acceptable if not specified

        condition_lower = condition.lower()

        # Default to True for all conditions if not specified
        if 'new' in condition_lower and not wishlist_item.get('condition_new', True):
            return False
        if 'excellent' in condition_lower and not wishlist_item.get('condition_excellent', True):
            return False
        if 'good' in condition_lower and not wishlist_item.get('condition_good', True):
            return False
        if 'fair' in condition_lower and not wishlist_item.get('condition_fair', False):
            return False

        return True
    
    def find_matches(self, wishlist_items: List[dict], listings: List[dict]) -> List[Dict]:
        """
        Find matches between wishlist items and listings

        Args:
            wishlist_items: List of wishlist item dictionaries
            listings: List of scraped listing dictionaries

        Returns:
            List of match dictionaries with scores
        """
        matches = []

        for wishlist_item in wishlist_items:
            if not wishlist_item.get('active', True):
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
                    'wishlist_item_id': wishlist_item.get('id'),
                    'user_id': wishlist_item.get('user_id'),
                    'listing': listing,
                    'match_score': score,
                    'price_match': price_match
                })

                brand = listing.get('brand', 'Unknown')
                title = listing.get('title', 'Unknown')
                price = listing.get('price', 0)
                logger.info(f"Match found! Score: {score:.1f} - {brand} {title} for ${price}")

        # Sort by score (highest first)
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        return matches
    
    # Note: save_matches is not implemented for Supabase yet
    # Matches are currently stored in memory and passed to the email notifier
    # Future: Add save_matches implementation using Supabase client

# Test matching engine
if __name__ == "__main__":
    print("Matching engine test")

    # Create test data
    wishlist_item = {
        'id': 1,
        'user_id': 1,
        'brand': 'Chanel',
        'item_type': 'handbag',
        'model_name': 'Classic Flap',
        'max_price': 5000,
        'condition_excellent': True,
        'condition_good': True,
        'active': True
    }

    listing = {
        'platform': 'Fashionphile',
        'url': 'https://example.com/item',
        'brand': 'Chanel',
        'title': 'Chanel Classic Medium Flap Bag',
        'item_type': 'handbag',
        'model_name': 'Classic Flap',
        'condition': 'excellent',
        'price': 4500,
        'currency': 'USD'
    }

    # Test matching
    engine = MatchingEngine(min_match_score=70)
    matches = engine.find_matches([wishlist_item], [listing])

    print(f"\nFound {len(matches)} matches:")
    for match in matches:
        print(f"  Score: {match['match_score']:.1f}")
        print(f"  Item: {match['listing']['brand']} {match['listing']['title']}")
        print(f"  Price: ${match['listing']['price']}")
