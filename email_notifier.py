"""
Email notification system using SendGrid
"""
import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content
from typing import List, Dict, Optional
import logging
from models import get_session
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
    
    def create_match_email_html(self, user_email: str, matches: List[Dict]) -> str:
        """Create HTML email content for match notifications"""
        match_count = len(matches)
        plural = "s" if match_count != 1 else ""
        
        html_parts = [
            '<!DOCTYPE html>',
            '<html>',
            '<head>',
            '<style>',
            'body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }',
            '.container { max-width: 600px; margin: 0 auto; padding: 20px; }',
            '.header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }',
            '.match { background: #f8f9fa; margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }',
            '.match-title { font-size: 18px; font-weight: bold; margin-bottom: 10px; }',
            '.match-details { color: #666; }',
            '.price { font-size: 24px; color: #28a745; font-weight: bold; }',
            '.button { background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }',
            '.footer { text-align: center; color: #999; margin-top: 30px; padding: 20px; }',
            '</style>',
            '</head>',
            '<body>',
            '<div class="container">',
            '<div class="header">',
            '<h1>🎯 New Luxury Finds!</h1>',
            '<p>We found ' + str(match_count) + ' item' + plural + ' matching your wishlist</p>',
            '</div>'
        ]
        
        for match in matches:
            listing = match.get('listing', {})
            
            brand = str(listing.get('brand', 'Unknown Brand'))
            title = str(listing.get('title', 'Untitled Item'))
            price = float(listing.get('price', 0))
            currency = str(listing.get('currency', 'USD'))
            platform = str(listing.get('platform', 'Unknown'))
            url = str(listing.get('url', '#'))
            condition = str(listing.get('condition', 'N/A'))
            match_score = int(match.get('match_score', 0))
            
            match_html = [
                '<div class="match">',
                '<div class="match-title">' + brand + ' - ' + title + '</div>',
                '<div class="match-details">',
                '<p><strong>Platform:</strong> ' + platform + '</p>',
                '<p><strong>Condition:</strong> ' + condition + '</p>',
                '<p><strong>Match Score:</strong> ' + str(match_score) + '%</p>',
                '</div>',
                '<div class="price">' + currency + ' $' + '{:,.2f}'.format(price) + '</div>',
                '<a href="' + url + '" class="button">View Item →</a>',
                '</div>'
            ]
            html_parts.extend(match_html)
        
        html_parts.extend([
            '<div class="footer">',
            '<p>You\'re receiving this because you have active wishlists</p>',
            '<p>Luxury Scraper © 2024</p>',
            '</div>',
            '</div>',
            '</body>',
            '</html>'
        ])
        
        return '\n'.join(html_parts)
    
    def send_match_notification(self, user_id: int, matches: List[Dict]) -> bool:
        """Send email notification for new matches"""
        if not self.client:
            logger.warning("SendGrid client not initialized - cannot send email")
            return False

        try:
            # Fetch user email from Supabase
            supabase_client = get_session()
            user_result = supabase_client.table('users').select('email').eq('id', user_id).execute()

            if not user_result.data:
                logger.error(f"User {user_id} not found in database")
                return False

            user_email = user_result.data[0]['email']

            match_count = len(matches)
            plural = "s" if match_count != 1 else ""
            subject = "🎯 " + str(match_count) + " New Luxury Item" + plural + " Found!"

            html_content = self.create_match_email_html(user_email, matches)

            message = Mail(
                from_email=self.from_email,
                to_emails=user_email,
                subject=subject,
                html_content=html_content
            )

            response = self.client.send(message)
            logger.info("Email sent to " + user_email + " - Status: " + str(response.status_code))

            return response.status_code == 202

        except Exception as e:
            logger.error("Error sending email notification: " + str(e))
            return False
