#!/usr/bin/env python3
"""
URL SCHEME FIXER - Fix relative URLs that are causing blurry/broken images
Specifically fixes Five Cities Orchid Society Google Drive URLs
"""

from app import app, db
from models import OrchidRecord
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class URLSchemeFixer:
    def __init__(self):
        self.fixed_count = 0
        
    def fix_relative_urls(self):
        """Fix relative URLs by adding proper scheme and host"""
        logger.info("🔧 FIXING RELATIVE URL SCHEMES...")
        
        with app.app_context():
            # Find records with relative URLs
            broken_urls = OrchidRecord.query.filter(
                OrchidRecord.image_url.like('/api/drive-photo/%')
            ).all()
            
            logger.info(f"📊 Found {len(broken_urls)} records with broken relative URLs")
            
            # Get the current domain from environment or default
            import os
            base_domain = os.environ.get('REPLIT_DOMAIN', 'localhost:5000')
            base_scheme = 'https' if 'replit.app' in base_domain else 'http'
            base_url = f"{base_scheme}://{base_domain}"
            
            logger.info(f"🌐 Using base URL: {base_url}")
            
            for record in broken_urls:
                if record.image_url and record.image_url.startswith('/api/drive-photo/'):
                    # Fix the URL by prepending the base URL
                    old_url = record.image_url
                    new_url = f"{base_url}{old_url}"
                    
                    record.image_url = new_url
                    self.fixed_count += 1
                    
                    logger.info(f"✅ FIXED: {record.display_name}")
                    logger.info(f"   Old: {old_url}")
                    logger.info(f"   New: {new_url}")
            
            # Commit all changes
            db.session.commit()
            logger.info(f"🎉 FIXED {self.fixed_count} URLs!")
            
    def fix_other_broken_schemes(self):
        """Fix other types of broken URLs"""
        logger.info("🔧 CHECKING OTHER URL ISSUES...")
        
        with app.app_context():
            # Find records with example.com URLs (demo data)
            demo_urls = OrchidRecord.query.filter(
                OrchidRecord.image_url.like('%example.com%')
            ).all()
            
            logger.info(f"📊 Found {len(demo_urls)} demo URLs to remove")
            
            for record in demo_urls:
                # Remove demo URLs - set to None so they can be replaced later
                record.image_url = None
                self.fixed_count += 1
                logger.info(f"🗑️ Removed demo URL: {record.display_name}")
            
            db.session.commit()
            logger.info(f"🧹 Cleaned up {len(demo_urls)} demo URLs")
    
    def run_comprehensive_url_fix(self):
        """Run comprehensive URL fixing"""
        logger.info("🚀 COMPREHENSIVE URL SCHEME REPAIR")
        logger.info("=" * 50)
        
        # Phase 1: Fix relative URLs  
        self.fix_relative_urls()
        
        # Phase 2: Remove demo URLs
        self.fix_other_broken_schemes()
        
        logger.info("=" * 50)
        logger.info("🎉 URL SCHEME REPAIR COMPLETE!")
        logger.info(f"🔧 Total URLs fixed: {self.fixed_count}")
        
        return self.fixed_count

if __name__ == "__main__":
    fixer = URLSchemeFixer()
    fixed_count = fixer.run_comprehensive_url_fix()
    
    print(f"\n🎯 URL SCHEME FIX RESULTS:")
    print(f"🔧 URLs fixed: {fixed_count}")
    print("✅ Orchid of the Day should now display clearly!")