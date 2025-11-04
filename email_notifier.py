"""
Email notification system using SendGrid
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import List, Dict, Optional
import logging
from models import User, Match, Notification, get_session
from datetime import datetime

logger = logging.getLogger(__name__)

class EmailNotifier:
    """Send email notifications for matches"""
    
    def __init__(self):
        """Initialize SendGrid client"""
        self.api_key = os.getenv('SENDGRID_API_KEY')
        self.from_email = os.getenv('FROM_EMAIL', 'alerts@luxuryscraper.com')
        
        if not self.api_key:
            logger.warning("SENDGRID_API_KEY not set - emails will not be sent")
            self.client = None
        else:
            self.client = SendGridAPIClient(self.api_key)
    
    def create_match_email_html(self, user: User, matches: List[Dict]) -> str:
        """
        Create HTML email content for match notifications
        
        Args:
            user: User object
            matches: List of match dictionaries with wishlist_item and listing
            
        Returns:
            HTML string
        """
        match_count = len(matches)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: #000; color: #fff; padding: 20px; text-align: center; }}
                .match {{ 
                    border: 1px solid #ddd; 
                    margin: 20px 0; 
                    padding: 15px; 
                    border-radius: 5px;
                    background: #f9f9f9;
                }}
                .match-image {{ max-width: 200px; height: auto; }}
                .price {{ font-size: 24px; font-weight: bold; color: #d4af37; }}
                .button {{ 
                    display: inline-block;
                    padding: 12px 24px;
                    background: #000;
                    color: #fff !important;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 10px 0;
                }}
                .footer {{ text-align: center; color: #666; font-size: 12px; margin-top: 40px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎉 New Luxury Items Match Your Wishlist!</h1>
                </div>
                
                <p>Hi there!</p>
                <p>We found <strong>{match_count}</strong> item{'s' if match_count > 1 else ''} matching your wishlist preferences:</p>
        """
        
        for match_data in matches:
            listing = match_data['listing']
            wishlist_item = match_data['wishlist_item']
            score = match_data['score']
            
            # Calculate total cost (simplified - add shipping/tax in production)
            total_cost = listing.price if listing.price else 0
            
            html += f"""
                <div class="match">
                    <h2>{listing.brand} - {listing.title}</h2>
                    
                    {f'<img src="{listing.image_url}" class="match-image" alt="{listing.title}">' if listing.image_url else ''}
                    
                    <p><strong>Platform:</strong> {listing.platform}</p>
                    <p><strong>Condition:</strong> {listing.condition.title() if listing.condition else 'N/A'}</p>
                    {f'<p><strong>Size:</strong> {listing.size}</p>' if listing.size else ''}
                    {f'<p><strong>Color:</strong> {listing.color}</p>' if listing.color else ''}
                    
                    <p class="price">${listing.price:,.2f} {listing.currency}</p>
                    <p style="font-size: 12px; color: #666;">
                        Estimated total: ${total_cost:,.2f} 
                        <br><small>(+ shipping & tax)</small>
                    </p>
                    
                    <p><strong>Match Score:</strong> {score:.0f}%</p>
                    
                    <a href="{listing.url}" class="button" target="_blank">
                        View on {listing.platform} →
                    </a>
                    
                    <p style="font-size: 12px; color: #666; margin-top: 15px;">
                        This matches your wishlist: <em>{wishlist_item.brand} {wishlist_item.model_name or wishlist_item.item_type}</em>
                    </p>
                </div>
            """
        
        html += f"""
                <div class="footer">
                    <p>You're receiving this because you have active wishlist items.</p>
                    <p>To manage your preferences or unsubscribe, visit your account settings.</p>
                    <p style="margin-top: 20px;">
                        <small>© 2025 Luxury Scraper. All rights reserved.</small>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def create_match_email_text(self, user: User, matches: List[Dict]) -> str:
        """
        Create plain text email content for match notifications
        
        Args:
            user: User object
            matches: List of match dictionaries
            
        Returns:
            Plain text string
        """
        match_count = len(matches)
        
        text = f"""
New Luxury Items Match Your Wishlist!

Hi there!

We found {match_count} item{'s' if match_count > 1 else ''} matching your wishlist preferences:

"""
        
        for i, match_data in enumerate(matches, 1):
            listing = match_data['listing']
            wishlist_item = match_data['wishlist_item']
            score = match_data['score']
            
            text += f"""
{'='*60}
ITEM {i}: {listing.brand} - {listing.title}
{'='*60}

Platform: {listing.platform}
Condition: {listing.condition.title() if listing.condition else 'N/A'}
Price: ${listing.price:,.2f} {listing.currency}
"""
            
            if listing.size:
                text += f"Size: {listing.size}\n"
            if listing.color:
                text += f"Color: {listing.color}\n"
            
            text += f"""
Match Score: {score:.0f}%
View Item: {listing.url}

This matches your wishlist: {wishlist_item.brand} {wishlist_item.model_name or wishlist_item.item_type}

"""
        
        text += """
---
You're receiving this because you have active wishlist items.
To manage your preferences, visit your account settings.

© 2025 Luxury Scraper. All rights reserved.
"""
        
        return text
    
    def send_match_notification(self, user: User, matches: List[Dict]) -> bool:
        """
        Send email notification for matches
        
        Args:
            user: User object
            matches: List of match dictionaries
            
        Returns:
            True if sent successfully
        """
        if not self.client:
            logger.warning(f"Cannot send email to {user.email} - SendGrid not configured")
            return False
        
        try:
            match_count = len(matches)
            subject = f"🎉 {match_count} New Item{'s' if match_count > 1 else ''} Match Your Wishlist!"
            
            # Create email content
            html_content = self.create_match_email_html(user, matches)
            text_content = self.create_match_email_text(user, matches)
            
            # Build message
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(user.email),
                subject=subject,
                plain_text_content=Content("text/plain", text_content),
                html_content=Content("text/html", html_content)
            )
            
            # Send email
            response = self.client.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {user.email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending email to {user.email}: {e}")
            return False
    
    def send_notifications_for_matches(self, match_ids: List[int] = None) -> int:
        """
        Send notifications for unnotified matches
        
        Args:
            match_ids: Optional list of specific match IDs to notify
            
        Returns:
            Number of notifications sent
        """
        session = get_session()
        sent_count = 0
        
        try:
            # Get unnotified matches
            query = session.query(Match).filter_by(notified=False)
            if match_ids:
                query = query.filter(Match.id.in_(match_ids))
            
            matches = query.all()
            
            # Group matches by user
            user_matches = {}
            for match in matches:
                user_id = match.wishlist_item.user_id
                if user_id not in user_matches:
                    user_matches[user_id] = []
                
                user_matches[user_id].append({
                    'match': match,
                    'wishlist_item': match.wishlist_item,
                    'listing': match.listing,
                    'score': match.match_score
                })
            
            # Send notification for each user
            for user_id, matches_data in user_matches.items():
                user = session.query(User).get(user_id)
                
                if not user or not user.active:
                    continue
                
                # Send email
                success = self.send_match_notification(user, matches_data)
                
                if success:
                    # Mark matches as notified
                    for match_data in matches_data:
                        match = match_data['match']
                        match.notified = True
                        match.notified_at = datetime.utcnow()
                        
                        # Create notification record
                        notification = Notification(
                            user_id=user_id,
                            match_id=match.id,
                            notification_type='new_match',
                            subject=f"New match: {match.listing.brand} {match.listing.title}",
                            message=f"Match score: {match.match_score:.0f}%",
                            sent=True,
                            sent_at=datetime.utcnow()
                        )
                        session.add(notification)
                    
                    sent_count += len(matches_data)
            
            session.commit()
            logger.info(f"Sent {sent_count} notifications")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error sending notifications: {e}")
        finally:
            session.close()
        
        return sent_count

# Test email notifier
if __name__ == "__main__":
    from models import init_db, User, WishlistItem, ScrapedListing
    
    # Initialize database
    init_db()
    
    # Test with mock data
    session = get_session()
    
    # Get or create test user
    user = session.query(User).filter_by(email="test@example.com").first()
    if not user:
        user = User(
            email="test@example.com",
            location_country="US",
            location_state="CA"
        )
        session.add(user)
        session.commit()
    
    # Create mock matches
    mock_matches = [{
        'wishlist_item': WishlistItem(
            brand="Chanel",
            model_name="Classic Flap",
            max_price=5000
        ),
        'listing': ScrapedListing(
            platform="Fashionphile",
            url="https://example.com/item",
            brand="Chanel",
            title="Chanel Classic Medium Flap Bag",
            condition="excellent",
            price=4500,
            currency="USD"
        ),
        'score': 95.5
    }]
    
    # Test email creation
    notifier = EmailNotifier()
    
    print("Creating test email HTML...")
    html = notifier.create_match_email_html(user, mock_matches)
    print(f"HTML length: {len(html)} characters")
    
    print("\nCreating test email text...")
    text = notifier.create_match_email_text(user, mock_matches)
    print(text)
    
    print("\n" + "="*60)
    print("To actually send emails:")
    print("1. Set SENDGRID_API_KEY in .env file")
    print("2. Run: notifier.send_match_notification(user, mock_matches)")
    
    session.close()
