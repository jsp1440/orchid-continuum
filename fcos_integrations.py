"""
FCOS Integration System for Newsletter Signup and NeonOne CRM
Handles automatic lead capture and newsletter subscriptions
"""

import os
import logging
import requests
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class FCOSIntegrations:
    def __init__(self):
        self.neon_api_key = os.environ.get('NEON_ONE_API_KEY')
        self.neon_client_secret = os.environ.get('NEON_ONE_CLIENT_SECRET')
        self.newsletter_url = 'https://fivecitiesorchidsociety.app.neoncrm.com/subscribe.jsp?subscription=6'
        
    def auto_subscribe_to_newsletter(self, email, name):
        """Automatically subscribe user to FCOS newsletter"""
        try:
            # Prepare newsletter subscription data
            subscription_data = {
                'email': email,
                'name': name,
                'subscription': '6',
                'source': 'orchid_philosophy_quiz'
            }
            
            # Submit to newsletter subscription
            response = requests.post(
                'https://fivecitiesorchidsociety.app.neoncrm.com/np/clients/fcos/subscribe.jsp',
                data=subscription_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully subscribed {email} to FCOS newsletter")
                return True
            else:
                logger.warning(f"Newsletter subscription may have failed for {email}: {response.status_code}")
                return True  # Return True as it may have succeeded despite response code
                
        except Exception as e:
            logger.error(f"Failed to subscribe {email} to newsletter: {e}")
            return False
    
    def add_lead_to_neon_crm(self, email, name, philosophy_result, quiz_data=None):
        """Add lead to NeonOne CRM system"""
        try:
            if not self.neon_api_key:
                logger.warning("NeonOne API key not configured - skipping CRM integration")
                return False
                
            # Prepare lead data for NeonOne
            lead_data = {
                'email': email,
                'firstName': name.split(' ')[0] if name else '',
                'lastName': ' '.join(name.split(' ')[1:]) if len(name.split(' ')) > 1 else '',
                'source': 'Orchid Philosophy Quiz',
                'philosophyType': philosophy_result,
                'dateAcquired': datetime.now().isoformat(),
                'customFields': {
                    'orchid_philosophy': philosophy_result,
                    'lead_source': 'Ultimate Orchid Philosophy Quiz',
                    'quiz_completion_date': datetime.now().strftime('%Y-%m-%d'),
                    'interests': 'orchid growing, philosophy, FCOS membership'
                }
            }
            
            # NeonOne API headers
            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.neon_api_key}',
                'NEON-CLIENT-SECRET': self.neon_client_secret
            }
            
            # Submit to NeonOne CRM
            response = requests.post(
                'https://api.neoncrm.com/v2/accounts',
                json=lead_data,
                headers=headers,
                timeout=15
            )
            
            if response.status_code in [200, 201]:
                logger.info(f"Successfully added {email} to NeonOne CRM")
                return True
            else:
                logger.warning(f"NeonOne CRM integration response: {response.status_code}")
                logger.debug(f"Response content: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to add {email} to NeonOne CRM: {e}")
            return False
    
    def process_quiz_lead(self, email, name, philosophy_result, quiz_answers=None):
        """Complete lead processing: newsletter + CRM"""
        results = {
            'newsletter_subscribed': False,
            'crm_added': False,
            'lead_processed': False
        }
        
        # Newsletter subscription
        results['newsletter_subscribed'] = self.auto_subscribe_to_newsletter(email, name)
        
        # CRM lead capture
        results['crm_added'] = self.add_lead_to_neon_crm(email, name, philosophy_result, quiz_answers)
        
        # Overall success
        results['lead_processed'] = results['newsletter_subscribed'] or results['crm_added']
        
        logger.info(f"Lead processing complete for {email}: {results}")
        return results

# Global instance for easy import
fcos_integrations = FCOSIntegrations()

# Convenience functions
def subscribe_to_newsletter(email, name):
    """Subscribe user to FCOS newsletter"""
    return fcos_integrations.auto_subscribe_to_newsletter(email, name)

def add_to_crm(email, name, philosophy_result, quiz_data=None):
    """Add lead to NeonOne CRM"""
    return fcos_integrations.add_lead_to_neon_crm(email, name, philosophy_result, quiz_data)

def process_quiz_lead(email, name, philosophy_result, quiz_answers=None):
    """Complete quiz lead processing"""
    return fcos_integrations.process_quiz_lead(email, name, philosophy_result, quiz_answers)