"""
Admin Notification Service for Photo Submissions
Sends email alerts when members upload photos
"""

import os
import sys
import logging
from datetime import datetime
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content

logger = logging.getLogger(__name__)

class AdminNotificationService:
    def __init__(self):
        self.sendgrid_key = os.environ.get('SENDGRID_API_KEY')
        self.admin_email = "jeffery@fivecitiesorchidsociety.org"
        self.from_email = "noreply@fivecitiesorchidsociety.org"
        
    def send_photo_submission_alert(self, upload_record, orchid_record=None):
        """Send email notification when a member submits a photo"""
        if not self.sendgrid_key:
            logger.warning("SendGrid API key not configured - notification not sent")
            return False
            
        try:
            # Create the email content
            subject = f"🌺 New Photo Submission - {upload_record.original_filename}"
            
            # Generate email body
            html_content = self._create_submission_email_html(upload_record, orchid_record)
            text_content = self._create_submission_email_text(upload_record, orchid_record)
            
            # Create SendGrid email
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(self.admin_email),
                subject=subject,
                html_content=Content("text/html", html_content),
                plain_text_content=Content("text/plain", text_content)
            )
            
            # Send the email
            sg = SendGridAPIClient(self.sendgrid_key)
            response = sg.send(message)
            
            logger.info(f"📧 Photo submission notification sent for upload {upload_record.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send photo submission notification: {e}")
            return False
    
    def _create_submission_email_html(self, upload_record, orchid_record):
        """Create HTML email content for photo submission notification"""
        submission_time = upload_record.created_at.strftime("%B %d, %Y at %I:%M %p")
        
        # AI identification results
        ai_info = ""
        if orchid_record:
            ai_info = f"""
            <div style="background: #e8f5e8; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #27ae60; margin: 0 0 10px 0;">🤖 AI Identification Results</h3>
                <p><strong>Suggested Name:</strong> {orchid_record.display_name or 'Unknown'}</p>
                <p><strong>Scientific Name:</strong> {orchid_record.scientific_name or 'Not identified'}</p>
                <p><strong>Genus:</strong> {orchid_record.genus or 'Unknown'}</p>
                <p><strong>Species:</strong> {orchid_record.species or 'Unknown'}</p>
                <p><strong>AI Confidence:</strong> {orchid_record.ai_confidence:.1%}</p>
                {f'<p><strong>Description:</strong> {orchid_record.ai_description}</p>' if orchid_record.ai_description else ''}
            </div>
            """
        
        # Member notes
        notes_section = ""
        if upload_record.user_notes:
            notes_section = f"""
            <div style="background: #fff3cd; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h3 style="color: #856404; margin: 0 0 10px 0;">📝 Member Notes</h3>
                <p style="margin: 0;">{upload_record.user_notes}</p>
            </div>
            """
        
        # Processing status
        status_color = "#27ae60" if upload_record.processing_status == "completed" else "#e74c3c"
        status_text = "✅ Successfully Processed" if upload_record.processing_status == "completed" else "❌ Processing Failed"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>New Photo Submission</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto;">
            <div style="background: linear-gradient(135deg, #8e44ad 0%, #3498db 100%); color: white; padding: 20px; text-align: center;">
                <h1 style="margin: 0;">🌺 Five Cities Orchid Society</h1>
                <h2 style="margin: 10px 0 0 0; font-weight: normal;">New Photo Submission Alert</h2>
            </div>
            
            <div style="padding: 20px;">
                <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                    <h3 style="color: #2c3e50; margin: 0 0 15px 0;">📸 Submission Details</h3>
                    <p><strong>File Name:</strong> {upload_record.original_filename}</p>
                    <p><strong>Submitted:</strong> {submission_time}</p>
                    <p><strong>File Size:</strong> {self._format_file_size(upload_record.file_size)}</p>
                    <p><strong>File Type:</strong> {upload_record.mime_type}</p>
                    <p><strong>Upload ID:</strong> {upload_record.plant_id}</p>
                </div>
                
                <div style="background: {status_color}; color: white; padding: 15px; border-radius: 8px; margin: 15px 0; text-align: center;">
                    <h3 style="margin: 0;">{status_text}</h3>
                </div>
                
                {ai_info}
                {notes_section}
                
                <div style="background: #e3f2fd; padding: 15px; border-radius: 8px; margin: 20px 0;">
                    <h3 style="color: #1976d2; margin: 0 0 15px 0;">🔗 Quick Actions</h3>
                    <p style="margin: 0;">
                        <a href="https://fivecitiesorchidsociety.replit.app/admin" style="color: #1976d2; text-decoration: none; font-weight: bold;">→ View Admin Dashboard</a>
                    </p>
                    {f'<p style="margin: 10px 0 0 0;"><a href="https://fivecitiesorchidsociety.replit.app/orchid/{orchid_record.id}" style="color: #1976d2; text-decoration: none; font-weight: bold;">→ View Orchid Details</a></p>' if orchid_record else ''}
                </div>
                
                <div style="text-align: center; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #666;">
                    <p style="margin: 0; font-size: 14px;">This is an automated notification from your Orchid Continuum system.</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _create_submission_email_text(self, upload_record, orchid_record):
        """Create plain text email content for photo submission notification"""
        submission_time = upload_record.created_at.strftime("%B %d, %Y at %I:%M %p")
        
        text = f"""
Five Cities Orchid Society - New Photo Submission

SUBMISSION DETAILS:
File Name: {upload_record.original_filename}
Submitted: {submission_time}
File Size: {self._format_file_size(upload_record.file_size)}
File Type: {upload_record.mime_type}
Upload ID: {upload_record.plant_id}
Status: {upload_record.processing_status.title()}

"""
        
        if orchid_record:
            text += f"""
AI IDENTIFICATION RESULTS:
Suggested Name: {orchid_record.display_name or 'Unknown'}
Scientific Name: {orchid_record.scientific_name or 'Not identified'}
Genus: {orchid_record.genus or 'Unknown'}
Species: {orchid_record.species or 'Unknown'}
AI Confidence: {orchid_record.ai_confidence:.1%}
{f'Description: {orchid_record.ai_description}' if orchid_record.ai_description else ''}

"""
        
        if upload_record.user_notes:
            text += f"""
MEMBER NOTES:
{upload_record.user_notes}

"""
        
        text += f"""
QUICK ACTIONS:
Admin Dashboard: https://fivecitiesorchidsociety.replit.app/admin
{f'Orchid Details: https://fivecitiesorchidsociety.replit.app/orchid/{orchid_record.id}' if orchid_record else ''}

---
This is an automated notification from your Orchid Continuum system.
        """
        
        return text.strip()
    
    def _format_file_size(self, size_bytes):
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        size_index = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and size_index < len(size_names) - 1:
            size /= 1024.0
            size_index += 1
        
        return f"{size:.1f} {size_names[size_index]}"

# Create global instance
notification_service = AdminNotificationService()