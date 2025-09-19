"""
Member Photo Submission Monitor
Automatically monitors Google Form submissions and notifies when new member photos arrive
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from dataclasses import dataclass
from app import db, app
from models import OrchidRecord, UserUpload
from google_sheets_service import GoogleSheetsService

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class PhotoSubmission:
    """Member photo submission data"""
    timestamp: str
    member_name: str
    member_email: str
    orchid_name: str
    photo_url: str
    description: str
    row_number: int
    processed: bool = False

class MemberPhotoMonitor:
    """Monitor Google Form submissions for member orchid photos"""
    
    def __init__(self):
        self.spreadsheet_id = "1103vQ_D00Qio5W7PllFeRaFoFAzr7jd8ivOo79sdfgs"
        self.sheets_service = GoogleSheetsService()
        self.last_check_time = datetime.now()
        self.notification_email = "jeff@fivecitiesorchidsociety.org"  # Your email
        
    def check_for_new_submissions(self) -> List[PhotoSubmission]:
        """Check Google Sheets for new photo submissions"""
        logger.info("🔍 Checking for new member photo submissions...")
        
        try:
            # Get all form submissions
            submissions = self.sheets_service.get_form_submissions(self.spreadsheet_id)
            
            if not submissions:
                logger.info("No submissions found")
                return []
            
            # Filter for new submissions since last check
            new_submissions = []
            for i, submission in enumerate(submissions, start=2):  # Start at row 2 (row 1 is headers)
                submission_time = self._parse_timestamp(submission.get('Timestamp', ''))
                
                # Check if this is a new submission
                if submission_time and submission_time > self.last_check_time:
                    photo_submission = PhotoSubmission(
                        timestamp=submission.get('Timestamp', ''),
                        member_name=submission.get('Name', 'Unknown Member'),
                        member_email=submission.get('Email Address', ''),
                        orchid_name=submission.get('Orchid Name/Species', 'Unknown Orchid'),
                        photo_url=submission.get('Photo Upload', ''),
                        description=submission.get('Description', ''),
                        row_number=i,
                        processed=submission.get('Processed', '').lower() == 'yes'
                    )
                    
                    if not photo_submission.processed:
                        new_submissions.append(photo_submission)
            
            if new_submissions:
                logger.info(f"🎉 Found {len(new_submissions)} new photo submissions!")
                self._send_notification(new_submissions)
            else:
                logger.info("No new submissions since last check")
            
            # Update last check time
            self.last_check_time = datetime.now()
            return new_submissions
            
        except Exception as e:
            logger.error(f"Error checking for submissions: {e}")
            return []
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse Google Forms timestamp"""
        if not timestamp_str:
            return None
            
        try:
            # Google Forms typically uses MM/DD/YYYY HH:MM:SS format
            return datetime.strptime(timestamp_str, '%m/%d/%Y %H:%M:%S')
        except ValueError:
            try:
                # Try alternative format
                return datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                logger.warning(f"Could not parse timestamp: {timestamp_str}")
                return None
    
    def _send_notification(self, submissions: List[PhotoSubmission]):
        """Send notification about new photo submissions"""
        logger.info(f"📧 Sending notification about {len(submissions)} new submissions")
        
        # Create notification message
        message_parts = [
            "🌺 NEW ORCHID PHOTO SUBMISSIONS FOR NEWSLETTER! 🌺",
            "",
            f"You have {len(submissions)} new member photo submissions:",
            ""
        ]
        
        for i, submission in enumerate(submissions, 1):
            message_parts.extend([
                f"{i}. {submission.member_name}",
                f"   Orchid: {submission.orchid_name}",
                f"   Email: {submission.member_email}",
                f"   Description: {submission.description[:100]}..." if len(submission.description) > 100 else f"   Description: {submission.description}",
                f"   Submitted: {submission.timestamp}",
                ""
            ])
        
        message_parts.extend([
            "These photos are ready to be imported into your newsletter!",
            "",
            f"View all submissions: https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}/edit",
            "",
            "- FCOS Photo Submission Monitor"
        ])
        
        notification_message = "\n".join(message_parts)
        
        # Log the notification (in production, this would send an email)
        logger.info("NOTIFICATION MESSAGE:")
        logger.info("=" * 60)
        logger.info(notification_message)
        logger.info("=" * 60)
        
        # Store notification for admin dashboard
        self._store_notification(notification_message, submissions)
    
    def _store_notification(self, message: str, submissions: List[PhotoSubmission]):
        """Store notification in database for admin dashboard"""
        try:
            with app.app_context():
                # Create notification record (you could create a Notification model)
                notification_data = {
                    'type': 'member_photo_submission',
                    'message': message,
                    'submission_count': len(submissions),
                    'created_at': datetime.now().isoformat(),
                    'submissions': [
                        {
                            'member_name': sub.member_name,
                            'orchid_name': sub.orchid_name,
                            'email': sub.member_email,
                            'timestamp': sub.timestamp
                        } for sub in submissions
                    ]
                }
                
                # Save to a simple file for now (could be database in production)
                notifications_file = 'member_photo_notifications.json'
                notifications = []
                
                if os.path.exists(notifications_file):
                    with open(notifications_file, 'r') as f:
                        notifications = json.load(f)
                
                notifications.append(notification_data)
                
                # Keep only last 50 notifications
                notifications = notifications[-50:]
                
                with open(notifications_file, 'w') as f:
                    json.dump(notifications, f, indent=2)
                
                logger.info(f"Notification stored for admin dashboard")
                
        except Exception as e:
            logger.error(f"Error storing notification: {e}")
    
    def import_submissions_to_orchid_continuum(self, submissions: List[PhotoSubmission]) -> int:
        """Import new photo submissions into the Orchid Continuum platform"""
        logger.info(f"🌺 Importing {len(submissions)} photo submissions to Orchid Continuum...")
        
        imported_count = 0
        
        with app.app_context():
            for submission in submissions:
                try:
                    # Check if already imported
                    existing = OrchidRecord.query.filter_by(
                        photographer=submission.member_name,
                        display_name=submission.orchid_name
                    ).first()
                    
                    if existing:
                        logger.info(f"Submission from {submission.member_name} already imported")
                        continue
                    
                    # Create new orchid record
                    orchid_record = OrchidRecord(
                        display_name=submission.orchid_name,
                        scientific_name=submission.orchid_name,  # Could be enhanced with AI identification
                        photographer=submission.member_name,
                        image_url=submission.photo_url,
                        ingestion_source='member_submission',
                        cultural_notes=submission.description,
                        validation_status='pending',
                        created_at=datetime.now()
                    )
                    
                    db.session.add(orchid_record)
                    db.session.commit()
                    
                    # Mark as processed in Google Sheets
                    self.sheets_service.mark_submission_processed(
                        self.spreadsheet_id, 
                        submission.row_number
                    )
                    
                    imported_count += 1
                    logger.info(f"✅ Imported: {submission.orchid_name} by {submission.member_name}")
                    
                except Exception as e:
                    logger.error(f"Error importing submission from {submission.member_name}: {e}")
                    db.session.rollback()
        
        logger.info(f"🎉 Successfully imported {imported_count} member photo submissions!")
        return imported_count
    
    def get_recent_notifications(self) -> List[Dict]:
        """Get recent notifications for admin dashboard"""
        try:
            notifications_file = 'member_photo_notifications.json'
            if os.path.exists(notifications_file):
                with open(notifications_file, 'r') as f:
                    notifications = json.load(f)
                return notifications[-10:]  # Return last 10 notifications
            return []
        except Exception as e:
            logger.error(f"Error reading notifications: {e}")
            return []

# Global monitor instance
photo_monitor = MemberPhotoMonitor()

def check_member_photo_submissions():
    """Function to be called by scheduler or cron job"""
    new_submissions = photo_monitor.check_for_new_submissions()
    
    if new_submissions:
        # Automatically import to Orchid Continuum
        imported_count = photo_monitor.import_submissions_to_orchid_continuum(new_submissions)
        logger.info(f"📊 SUMMARY: {len(new_submissions)} new submissions, {imported_count} imported")
        return {
            'new_submissions': len(new_submissions),
            'imported_count': imported_count,
            'submissions': new_submissions
        }
    
    return {'new_submissions': 0, 'imported_count': 0, 'submissions': []}

if __name__ == "__main__":
    # Test the monitor
    logging.basicConfig(level=logging.INFO)
    result = check_member_photo_submissions()
    print(f"Monitor result: {result}")