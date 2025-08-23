"""
Simple email service for password reset functionality
In production, this would use a real email service like SendGrid, Mailgun, or AWS SES
"""

import logging
from datetime import datetime
from flask import render_template, url_for

logger = logging.getLogger(__name__)

class EmailService:
    """Email service for sending password reset emails"""
    
    def __init__(self, app=None):
        self.app = app
        self.mock_mode = True  # In development, use mock mode
        
    def init_app(self, app):
        self.app = app
        
    def send_password_reset_email(self, user, reset_token):
        """Send password reset email to user"""
        try:
            subject = "Orchid Continuum - Password Reset Request"
            
            # Generate reset URL
            reset_url = url_for('auth.reset_password', token=reset_token.token, _external=True)
            
            # Email content
            email_data = {
                'user': user,
                'reset_url': reset_url,
                'token_expires_in': '24 hours',
                'app_name': 'Orchid Continuum'
            }
            
            # In mock mode, just log the email content
            if self.mock_mode:
                logger.info(f"MOCK EMAIL SENT TO: {user.email}")
                logger.info(f"Subject: {subject}")
                logger.info(f"Reset URL: {reset_url}")
                logger.info(f"Token expires: {reset_token.expires_at}")
                
                # Store mock email for testing
                if not hasattr(self, '_mock_emails'):
                    self._mock_emails = []
                
                self._mock_emails.append({
                    'to': user.email,
                    'subject': subject,
                    'reset_url': reset_url,
                    'sent_at': datetime.utcnow(),
                    'token': reset_token.token
                })
                
                return True
            else:
                # In production, implement actual email sending here
                # Example using Flask-Mail or similar:
                # msg = Message(subject, recipients=[user.email])
                # msg.html = render_template('email/password_reset.html', **email_data)
                # mail.send(msg)
                pass
                
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
            return False
    
    def get_mock_emails(self):
        """Get mock emails sent (for testing only)"""
        return getattr(self, '_mock_emails', [])
    
    def clear_mock_emails(self):
        """Clear mock email history (for testing only)"""
        self._mock_emails = []

# Initialize email service
email_service = EmailService()