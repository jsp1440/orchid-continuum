"""
Automated Submission Scheduler
Runs periodic checks for new member photo submissions
"""

import schedule
import time
import logging
from datetime import datetime
from member_photo_submission_monitor import check_member_photo_submissions

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('member_submission_monitor.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def scheduled_check():
    """Scheduled function to check for new submissions"""
    logger.info("🔍 Running scheduled check for member photo submissions...")
    
    try:
        result = check_member_photo_submissions()
        
        if result['new_submissions'] > 0:
            logger.info(f"🎉 ALERT: {result['new_submissions']} new member photo submissions found!")
            logger.info(f"📊 Imported {result['imported_count']} photos to newsletter database")
        else:
            logger.info("ℹ️  No new submissions since last check")
            
    except Exception as e:
        logger.error(f"❌ Error during scheduled check: {e}")

def run_monitoring_service():
    """Run the continuous monitoring service"""
    logger.info("🚀 Starting Member Photo Submission Monitor...")
    logger.info("📋 Monitoring schedule: Every 15 minutes")
    logger.info("📧 Notifications will be logged and stored for admin dashboard")
    
    # Schedule checks every 15 minutes
    schedule.every(15).minutes.do(scheduled_check)
    
    # Also schedule hourly summaries
    schedule.every().hour.do(lambda: logger.info("📊 Hourly monitor status: Active and running"))
    
    # Run initial check
    scheduled_check()
    
    # Keep the service running
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute for scheduled tasks

if __name__ == "__main__":
    run_monitoring_service()