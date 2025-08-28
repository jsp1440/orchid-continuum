"""
Neon One CRM Integration for FCOS Member Management
Automates member workflows, email campaigns, and payment processing
"""

import os
import json
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from app import db
from models import WorkshopRegistration, User
from philosophy_quiz_system import PHILOSOPHY_PROFILES

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class NeonMember:
    """Neon One member data structure"""
    account_id: str
    email: str
    first_name: str
    last_name: str
    membership_status: str
    membership_level: str
    expiration_date: Optional[str] = None
    phone: Optional[str] = None
    organization: Optional[str] = None

class NeonOneAPI:
    """Neon One CRM API Integration"""
    
    def __init__(self):
        self.api_key = os.environ.get('NEON_ONE_API_KEY')
        self.base_url = "https://api.neoncrm.com/v2"
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        
        if not self.api_key:
            logger.warning("Neon One API key not found. Integration will run in simulation mode.")
    
    def _make_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request to Neon One"""
        if not self.api_key:
            logger.info(f"SIMULATION: {method} {endpoint} - {data}")
            return {"simulation": True, "success": True}
        
        try:
            url = f"{self.base_url}{endpoint}"
            
            if method.upper() == 'GET':
                response = requests.get(url, headers=self.headers, params=data)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=self.headers, json=data)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=self.headers, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Neon One API error: {e}")
            return None
    
    def get_member_by_email(self, email: str) -> Optional[NeonMember]:
        """Find member by email address"""
        endpoint = "/accounts"
        params = {"search.email": email}
        
        response = self._make_request('GET', endpoint, params)
        if not response or not response.get('accounts'):
            return None
        
        # Get first matching account
        account = response['accounts'][0]
        return self._parse_member_data(account)
    
    def get_member_memberships(self, account_id: str) -> List[Dict]:
        """Get member's membership history"""
        endpoint = f"/accounts/{account_id}/memberships"
        response = self._make_request('GET', endpoint)
        return response.get('memberships', []) if response else []
    
    def create_activity_record(self, account_id: str, activity_data: Dict) -> bool:
        """Create activity record for member (workshop registration, etc.)"""
        endpoint = f"/accounts/{account_id}/activities"
        response = self._make_request('POST', endpoint, activity_data)
        return response is not None
    
    def update_member_notes(self, account_id: str, notes: str) -> bool:
        """Add notes to member record"""
        endpoint = f"/accounts/{account_id}"
        data = {"notes": notes}
        response = self._make_request('PUT', endpoint, data)
        return response is not None
    
    def trigger_email_campaign(self, campaign_id: str, member_emails: List[str]) -> bool:
        """Trigger automated email campaign for specific members"""
        # This would use Neon One's email automation features
        endpoint = f"/email/campaigns/{campaign_id}/send"
        data = {"recipients": member_emails}
        response = self._make_request('POST', endpoint, data)
        return response is not None
    
    def _parse_member_data(self, account_data: Dict) -> NeonMember:
        """Parse Neon One account data into our member structure"""
        return NeonMember(
            account_id=account_data.get('accountId', ''),
            email=account_data.get('primaryContact', {}).get('email', ''),
            first_name=account_data.get('primaryContact', {}).get('firstName', ''),
            last_name=account_data.get('primaryContact', {}).get('lastName', ''),
            membership_status=account_data.get('membershipStatus', 'Unknown'),
            membership_level=account_data.get('membershipLevel', 'Unknown'),
            phone=account_data.get('primaryContact', {}).get('phone', ''),
            organization=account_data.get('organization', {}).get('name', '')
        )

class FCOSMemberAutomation:
    """FCOS-specific member automation workflows"""
    
    def __init__(self):
        self.neon = NeonOneAPI()
        self.email_campaigns = {
            'workshop_welcome': 'FCOS_WORKSHOP_WELCOME',
            'workshop_reminder': 'FCOS_WORKSHOP_REMINDER', 
            'member_renewal': 'FCOS_MEMBER_RENEWAL',
            'new_member_welcome': 'FCOS_NEW_MEMBER_WELCOME',
            'philosophy_quiz_results': 'FCOS_PHILOSOPHY_QUIZ_RESULTS'
        }
    
    def process_workshop_registration(self, registration: WorkshopRegistration) -> Dict[str, Any]:
        """Process workshop registration with Neon One integration"""
        logger.info(f"Processing workshop registration for {registration.email}")
        
        results = {
            'member_found': False,
            'member_data': None,
            'activity_created': False,
            'email_sent': False,
            'member_benefits_applied': False
        }
        
        # Find member in Neon One
        member = self.neon.get_member_by_email(registration.email)
        if member:
            results['member_found'] = True
            results['member_data'] = member
            logger.info(f"Found FCOS member: {member.first_name} {member.last_name}")
            
            # Apply member benefits
            if member.membership_status == 'Active':
                # Apply member discount if applicable
                if registration.amount_paid > 10.00:
                    member_discount = 2.00  # $2 member discount
                    registration.amount_paid = max(8.00, registration.amount_paid - member_discount)
                    registration.notes = f"Member discount applied: -${member_discount}. " + (registration.notes or "")
                    results['member_benefits_applied'] = True
                    logger.info(f"Applied member discount: ${member_discount}")
            
            # Create activity record in Neon One
            activity_data = {
                'activityType': 'Workshop Registration',
                'activityDate': registration.created_at.isoformat(),
                'subject': f'Orchid Workshop Registration - {registration.workshop_date}',
                'description': f"""
                Workshop: Traditional vs. Semi-Hydroponic Repotting
                Date: {registration.workshop_date}
                Payment: ${registration.amount_paid} ({registration.payment_method})
                Experience Level: {registration.experience_level}
                Bringing Orchid: {'Yes' if registration.bringing_orchid else 'No'}
                Primary Interest: {registration.primary_interest}
                """.strip(),
                'amount': registration.amount_paid
            }
            
            if self.neon.create_activity_record(member.account_id, activity_data):
                results['activity_created'] = True
                logger.info("Created activity record in Neon One")
            
            # Send welcome email
            if self.neon.trigger_email_campaign(
                self.email_campaigns['workshop_welcome'], 
                [registration.email]
            ):
                results['email_sent'] = True
                logger.info("Triggered workshop welcome email")
        
        else:
            logger.info(f"Email {registration.email} not found in FCOS membership database")
            # Could trigger new member prospect workflow here
        
        return results
    
    def send_workshop_reminders(self, workshop_date: str) -> Dict[str, int]:
        """Send automated workshop reminders to registered participants"""
        logger.info(f"Sending workshop reminders for {workshop_date}")
        
        # Get all registrations for the workshop date
        registrations = WorkshopRegistration.query.filter_by(
            workshop_date=datetime.strptime(workshop_date, '%Y-%m-%d').date(),
            registration_status='confirmed'
        ).all()
        
        member_emails = []
        non_member_emails = []
        
        for reg in registrations:
            member = self.neon.get_member_by_email(reg.email)
            if member and member.membership_status == 'Active':
                member_emails.append(reg.email)
            else:
                non_member_emails.append(reg.email)
        
        results = {
            'members_notified': 0,
            'non_members_notified': 0,
            'total_registrations': len(registrations)
        }
        
        # Send member reminders (may have different template)
        if member_emails and self.neon.trigger_email_campaign(
            self.email_campaigns['workshop_reminder'], 
            member_emails
        ):
            results['members_notified'] = len(member_emails)
        
        # Send non-member reminders
        if non_member_emails and self.neon.trigger_email_campaign(
            self.email_campaigns['workshop_reminder'], 
            non_member_emails
        ):
            results['non_members_notified'] = len(non_member_emails)
        
        logger.info(f"Workshop reminders sent: {results}")
        return results
    
    def sync_member_renewals(self) -> Dict[str, int]:
        """Check for members needing renewal and trigger campaigns"""
        logger.info("Checking for members needing renewal...")
        
        # This would typically query Neon One for members expiring soon
        # For now, simulate the process
        
        results = {
            'members_expiring_soon': 0,
            'renewal_emails_sent': 0,
            'grace_period_members': 0
        }
        
        # In real implementation, would query Neon One API for expiring memberships
        # then trigger appropriate email campaigns
        
        logger.info(f"Member renewal check completed: {results}")
        return results
    
    def generate_member_engagement_report(self) -> Dict[str, Any]:
        """Generate report on member engagement with workshops and activities"""
        
        # Get workshop registrations by member status
        total_registrations = WorkshopRegistration.query.count()
        paid_registrations = WorkshopRegistration.query.filter_by(payment_status='paid').count()
        
        # This would be enhanced with actual Neon One member data
        report = {
            'total_workshop_registrations': total_registrations,
            'paid_registrations': paid_registrations,
            'payment_rate': round((paid_registrations / total_registrations * 100), 2) if total_registrations > 0 else 0,
            'member_vs_non_member_breakdown': {
                'members': 0,  # Would get from Neon One
                'non_members': total_registrations,  # Would calculate difference
                'member_conversion_opportunities': total_registrations
            },
            'generated_at': datetime.now().isoformat()
        }
        
        return report
    
    def calculate_philosophy_quiz_score(self, answers: List[str]) -> Dict[str, Any]:
        """
        Calculate philosophy quiz results from form answers
        Returns scored philosophy type and badge data for Neon One workflow
        """
        # Philosophy scoring weights for each answer
        weights = {
            'A': {'zen': 3, 'stoic': 2, 'epicurean': 1, 'skeptic': 1, 'empiricist': 2, 'rationalist': 1, 'existentialist': 2, 'pragmatist': 3, 'hedonist': 1, 'minimalist': 3},
            'B': {'zen': 1, 'stoic': 3, 'epicurean': 2, 'skeptic': 2, 'empiricist': 3, 'rationalist': 2, 'existentialist': 1, 'pragmatist': 2, 'hedonist': 2, 'minimalist': 1},
            'C': {'zen': 2, 'stoic': 1, 'epicurean': 3, 'skeptic': 3, 'empiricist': 1, 'rationalist': 3, 'existentialist': 3, 'pragmatist': 1, 'hedonist': 3, 'minimalist': 2},
            'D': {'zen': 1, 'stoic': 2, 'epicurean': 2, 'skeptic': 3, 'empiricist': 3, 'rationalist': 3, 'existentialist': 2, 'pragmatist': 2, 'hedonist': 3, 'minimalist': 1}
        }
        
        # Calculate scores for each philosophy
        scores = {phil: 0 for phil in weights['A'].keys()}
        
        for answer in answers:
            if answer in weights:
                for phil, weight in weights[answer].items():
                    scores[phil] += weight
        
        # Find winning philosophy
        winning_philosophy = max(scores, key=scores.get)
        winning_score = scores[winning_philosophy]
        
        # Get badge data
        badge_data = PHILOSOPHY_PROFILES[winning_philosophy]
        
        return {
            'philosophy_type': winning_philosophy,
            'score': winning_score,
            'total_possible': 30,  # 10 questions × 3 max points
            'percentage': round((winning_score / 30) * 100),
            'badge_data': badge_data,
            'all_scores': scores
        }
    
    def generate_philosophy_email_data(self, quiz_results: Dict, user_data: Dict) -> Dict[str, str]:
        """
        Generate email content data for Neon One workflow system
        Returns subject, HTML content, and custom field data
        """
        badge = quiz_results['badge_data']
        
        # Email subject
        subject = f"🌺 Your Orchid Philosophy: {badge['badge_name']} - Five Cities Orchid Society"
        
        # Generate custom field data for Neon One
        custom_fields = {
            'philosophy_type': quiz_results['philosophy_type'],
            'philosophy_badge_name': badge['badge_name'],
            'philosophy_score': quiz_results['score'],
            'philosophy_percentage': quiz_results['percentage'],
            'badge_emoji': badge['badge_emoji'],
            'badge_philosophy_quote': badge['philosophy'],
            'badge_growing_style': badge['growing_style'],
            'badge_description': badge['description'],
            'quiz_completion_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            # Flatten recommendations for Neon One fields
            'growing_rec_1': badge['growing_recommendations'][0] if len(badge['growing_recommendations']) > 0 else '',
            'growing_rec_2': badge['growing_recommendations'][1] if len(badge['growing_recommendations']) > 1 else '',
            'growing_rec_3': badge['growing_recommendations'][2] if len(badge['growing_recommendations']) > 2 else '',
            'book_rec_1': badge['recommended_reading'][0] if len(badge['recommended_reading']) > 0 else '',
            'book_rec_2': badge['recommended_reading'][1] if len(badge['recommended_reading']) > 1 else '',
            'book_rec_3': badge['recommended_reading'][2] if len(badge['recommended_reading']) > 2 else ''
        }
        
        return {
            'subject': subject,
            'custom_fields': custom_fields,
            'email_template_id': 'philosophy_quiz_results'
        }
    
    def process_philosophy_quiz_submission(self, form_data: Dict) -> Dict[str, Any]:
        """
        Process philosophy quiz submission and prepare for Neon One workflow
        """
        logger.info(f"Processing philosophy quiz for {form_data.get('email', 'anonymous')}")
        
        # Extract quiz answers (question_1 through question_10)
        answers = []
        for i in range(1, 11):
            answer = form_data.get(f'question_{i}', 'A')
            answers.append(answer)
        
        # Calculate quiz results
        quiz_results = self.calculate_philosophy_quiz_score(answers)
        
        # User data for personalization
        user_data = {
            'first_name': form_data.get('first_name', ''),
            'last_name': form_data.get('last_name', ''),
            'email': form_data.get('email', ''),
            'phone': form_data.get('phone', ''),
            'website_url': os.environ.get('REPLIT_DEV_DOMAIN', 'your-website.com')
        }
        
        # Generate email data for Neon One
        email_data = self.generate_philosophy_email_data(quiz_results, user_data)
        
        # Check if this person is already a member
        member = self.neon.get_member_by_email(user_data['email']) if user_data['email'] else None
        
        # Prepare complete data package for Neon One
        neon_submission = {
            # Standard contact fields
            **user_data,
            
            # Quiz-specific custom fields  
            **email_data['custom_fields'],
            
            # Workflow triggers
            'trigger_philosophy_email': True,
            'email_template': email_data['email_template_id'],
            'is_existing_member': member is not None,
            'member_account_id': member.account_id if member else '',
            
            # Activity tracking
            'activity_type': 'Philosophy Quiz Completion',
            'activity_points': 50,  # Points awarded for completing quiz
            'activity_date': datetime.now().isoformat()
        }
        
        results = {
            'quiz_results': quiz_results,
            'email_data': email_data,
            'neon_submission': neon_submission,
            'member_found': member is not None,
            'member_data': member.__dict__ if member else None
        }
        
        logger.info(f"Philosophy quiz processed: {quiz_results['philosophy_type']} ({quiz_results['percentage']}%)")
        return results

# API endpoint functions for Flask routes
def setup_neon_one_routes(app):
    """Setup Flask routes for Neon One integration"""
    
    automation = FCOSMemberAutomation()
    
    @app.route('/api/neon-member-lookup/<email>')
    def neon_member_lookup(email):
        """API endpoint to lookup member in Neon One"""
        member = automation.neon.get_member_by_email(email)
        if member:
            return {
                'found': True,
                'member': {
                    'account_id': member.account_id,
                    'name': f"{member.first_name} {member.last_name}",
                    'membership_status': member.membership_status,
                    'membership_level': member.membership_level
                }
            }
        return {'found': False}
    
    @app.route('/admin/neon-sync-workshop/<registration_id>')
    def admin_sync_workshop_registration(registration_id):
        """Admin endpoint to manually sync workshop registration"""
        registration = WorkshopRegistration.query.get_or_404(registration_id)
        results = automation.process_workshop_registration(registration)
        
        return {
            'success': True,
            'registration_id': registration_id,
            'sync_results': results
        }
    
    @app.route('/admin/neon-workshop-reminders/<workshop_date>')
    def admin_send_workshop_reminders(workshop_date):
        """Admin endpoint to send workshop reminders"""
        results = automation.send_workshop_reminders(workshop_date)
        return {
            'success': True,
            'reminder_results': results
        }
    
    @app.route('/admin/neon-engagement-report')
    def admin_engagement_report():
        """Admin endpoint for member engagement report"""
        report = automation.generate_member_engagement_report()
        return report
    
    @app.route('/api/philosophy-quiz/submit', methods=['POST'])
    def philosophy_quiz_submit():
        """API endpoint for philosophy quiz submission with Neon One integration"""
        try:
            from flask import request, jsonify
            form_data = request.form.to_dict()
            
            # Process quiz through automation system
            results = automation.process_philosophy_quiz_submission(form_data)
            
            # If we have an email, create/update the contact in Neon One
            if results['neon_submission'].get('email'):
                # This would send to Neon One CRM via API or webhook
                # For now, log the submission data
                logger.info(f"Philosophy quiz submission ready for Neon One: {results['neon_submission']['email']}")
                logger.info(f"Philosophy type: {results['quiz_results']['philosophy_type']}")
                logger.info(f"Badge: {results['quiz_results']['badge_data']['badge_name']}")
            
            return jsonify({
                'success': True,
                'philosophy_type': results['quiz_results']['philosophy_type'],
                'badge_name': results['quiz_results']['badge_data']['badge_name'],
                'score_percentage': results['quiz_results']['percentage'],
                'redirect_url': '/philosophy-quiz/result',
                'neon_data': results['neon_submission']  # This would be sent to Neon One
            })
            
        except Exception as e:
            logger.error(f"Philosophy quiz submission error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/api/philosophy-quiz/neon-webhook', methods=['POST'])
    def philosophy_quiz_neon_webhook():
        """Webhook endpoint for Neon One to get email content"""
        try:
            from flask import request, jsonify
            neon_data = request.json
            
            # Generate email content from Neon One data
            email_content = automation.generate_philosophy_email_html(neon_data)
            
            return jsonify({
                'success': True,
                'email_subject': email_content['subject'],
                'email_html': email_content['html_content'],
                'custom_fields': email_content.get('custom_fields', {})
            })
            
        except Exception as e:
            logger.error(f"Neon One webhook error: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

# Initialize the integration
fcos_automation = FCOSMemberAutomation()

# Export for use in other modules
__all__ = ['FCOSMemberAutomation', 'NeonOneAPI', 'setup_neon_one_routes', 'fcos_automation']