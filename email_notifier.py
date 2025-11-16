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
        """
        Create HTML email content for match notifications
        
        Args:
            user_email: User email address
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
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .match {{ background: #f8f9fa; margin: 20px 0; padding: 20px; border-radius: 8px; border-left: 4px solid #667eea; }}
                .match-title {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                .match-details {{ color: #666; }}
                .price {{ font-size: 24px; color: #28a745; font-weight: bold; }}
                .button {{ background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 15px; }}
                .footer {{ text-align: center; color: #999; margin-top: 30px; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="container">
