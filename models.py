"""
Database helpers for the luxury consignment scraper using Supabase
"""
from supabase import create_client
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

def get_supabase_client():
    """Get Supabase client"""
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_ANON_KEY')

    # Debug: Print what we got from environment (first 20 chars only for security)
    print(f"DEBUG: SUPABASE_URL = {supabase_url[:20] + '...' if supabase_url else 'NOT SET'}")
    print(f"DEBUG: SUPABASE_ANON_KEY = {supabase_key[:20] + '...' if supabase_key else 'NOT SET'}")

    if not supabase_url or not supabase_key:
        raise ValueError("SUPABASE_URL and SUPABASE_ANON_KEY must be set")

    return create_client(supabase_url, supabase_key)

def init_db():
    """Initialize database - tables already exist in Supabase"""
    client = get_supabase_client()
    print("✅ Connected to Supabase successfully!")
    return client

def get_session():
    """Get Supabase client (replaces SQLAlchemy session)"""
    return get_supabase_client()

class User:
    """User operations"""
    
    @staticmethod
    def create(client, email, location_country=None, location_state=None):
        data = {
            'email': email,
            'location_country': location_country,
            'location_state': location_state,
            'created_at': datetime.utcnow().isoformat(),
            'active': True
        }
        return client.table('users').insert(data).execute()
    
    @staticmethod
    def get_by_email(client, email):
        return client.table('users').select('*').eq('email', email).execute()

class WishlistItem:
    """Wishlist operations"""
    
    @staticmethod
    def create(client, user_id, brand, max_price, **kwargs):
        data = {
            'user_id': user_id,
            'brand': brand,
            'max_price': max_price,
            'active': True,
            'created_at': datetime.utcnow().isoformat(),
            **kwargs
        }
        return client.table('wishlist_items').insert(data).execute()
    
    @staticmethod
    def get_active(client):
        return client.table('wishlist_items').select('*').eq('active', True).execute()

class ScrapedListing:
    """Scraped listing operations"""
    
    @staticmethod
    def create(client, platform, url, brand, title, price, **kwargs):
        data = {
            'platform': platform,
            'url': url,
            'brand': brand,
            'title': title,
            'price': price,
            'first_seen': datetime.utcnow().isoformat(),
            'last_seen': datetime.utcnow().isoformat(),
            'sold': False,
            **kwargs
        }
        return client.table('scraped_listings').insert(data).execute()
    
    @staticmethod
    def check_exists(client, url):
        result = client.table('scraped_listings').select('id').eq('url', url).execute()
        return len(result.data) > 0
    
    @staticmethod
    def update_last_seen(client, url):
        return client.table('scraped_listings').update({
            'last_seen': datetime.utcnow().isoformat()
        }).eq('url', url).execute()

if __name__ == "__main__":
    init_db()
