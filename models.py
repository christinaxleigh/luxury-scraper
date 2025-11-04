"""
Database models for the luxury consignment scraper
"""
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    location_country = Column(String(100))
    location_state = Column(String(100))
    location_zip = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
    
    wishlists = relationship("WishlistItem", back_populates="user")
    notifications = relationship("Notification", back_populates="user")

class WishlistItem(Base):
    __tablename__ = 'wishlist_items'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Item specifications
    brand = Column(String(255), nullable=False)
    item_type = Column(String(100))  # handbag, shoes, jewelry, etc.
    model_name = Column(String(255))
    size = Column(String(50))
    color = Column(String(100))
    preferred_colors = Column(Text)  # JSON array of acceptable colors
    
    # Price parameters
    min_price = Column(Float)
    max_price = Column(Float, nullable=False)
    currency = Column(String(10), default='USD')
    
    # Condition preferences
    condition_new = Column(Boolean, default=True)
    condition_excellent = Column(Boolean, default=True)
    condition_good = Column(Boolean, default=True)
    condition_fair = Column(Boolean, default=False)
    
    # Preferences
    priority = Column(String(20), default='medium')  # high, medium, low
    notes = Column(Text)
    max_shipping_cost = Column(Float)
    
    # Status
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime)
    
    user = relationship("User", back_populates="wishlists")
    matches = relationship("Match", back_populates="wishlist_item")

class ScrapedListing(Base):
    __tablename__ = 'scraped_listings'
    
    id = Column(Integer, primary_key=True)
    
    # Source information
    platform = Column(String(100), nullable=False)
    listing_id = Column(String(255))  # Platform's internal ID
    url = Column(String(500), nullable=False)
    
    # Item details
    brand = Column(String(255))
    title = Column(String(500))
    description = Column(Text)
    item_type = Column(String(100))
    model_name = Column(String(255))
    size = Column(String(50))
    color = Column(String(100))
    condition = Column(String(50))
    
    # Pricing
    price = Column(Float)
    currency = Column(String(10))
    original_price = Column(Float)  # MSRP if available
    
    # Metadata
    image_url = Column(String(500))
    seller_name = Column(String(255))
    authenticated = Column(Boolean)
    
    # Timestamps
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_seen = Column(DateTime, default=datetime.utcnow)
    sold = Column(Boolean, default=False)
    
    matches = relationship("Match", back_populates="listing")

class Match(Base):
    __tablename__ = 'matches'
    
    id = Column(Integer, primary_key=True)
    wishlist_item_id = Column(Integer, ForeignKey('wishlist_items.id'), nullable=False)
    listing_id = Column(Integer, ForeignKey('scraped_listings.id'), nullable=False)
    
    match_score = Column(Float)  # 0-100 similarity score
    price_within_range = Column(Boolean)
    
    # Notification status
    notified = Column(Boolean, default=False)
    notified_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    wishlist_item = relationship("WishlistItem", back_populates="matches")
    listing = relationship("ScrapedListing", back_populates="matches")

class Notification(Base):
    __tablename__ = 'notifications'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    match_id = Column(Integer, ForeignKey('matches.id'))
    
    notification_type = Column(String(50))  # new_match, price_drop, etc.
    subject = Column(String(255))
    message = Column(Text)
    
    sent = Column(Boolean, default=False)
    sent_at = Column(DateTime)
    opened = Column(Boolean, default=False)
    clicked = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="notifications")

# Database setup functions
def get_engine():
    """Get database engine"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///luxury_scraper.db')
    return create_engine(database_url, echo=False)

def init_db():
    """Initialize database with all tables"""
    engine = get_engine()
    Base.metadata.create_all(engine)
    print("Database initialized successfully!")
    return engine

def get_session():
    """Get database session"""
    engine = get_engine()
    Session = sessionmaker(bind=engine)
    return Session()

if __name__ == "__main__":
    # Initialize database when run directly
    init_db()
