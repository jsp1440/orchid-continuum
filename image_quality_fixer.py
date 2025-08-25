#!/usr/bin/env python3
"""
IMAGE QUALITY FIXER - Fix blurry/hazy orchid images
Validates image URLs, checks quality, and updates with better sources
"""

import requests
from PIL import Image
import io
import logging
from app import app, db
from models import OrchidRecord
import time
from urllib.parse import urlparse
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageQualityFixer:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.fixed_count = 0
        
    def check_image_quality(self, image_url):
        """Check if image is accessible and of good quality"""
        if not image_url:
            return False, "No URL"
        
        try:
            response = self.session.get(image_url, timeout=10, stream=True)
            
            if response.status_code != 200:
                return False, f"HTTP {response.status_code}"
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type:
                return False, "Not an image"
            
            # Check if we can open the image
            try:
                image_data = response.content
                image = Image.open(io.BytesIO(image_data))
                
                # Check image dimensions - reject very small images (likely thumbnails)
                width, height = image.size
                if width < 200 or height < 200:
                    return False, f"Too small ({width}x{height})"
                
                # Check file size - reject very small files (likely poor quality)
                file_size = len(image_data)
                if file_size < 10000:  # Less than 10KB
                    return False, f"File too small ({file_size} bytes)"
                
                return True, f"Good quality ({width}x{height}, {file_size} bytes)"
                
            except Exception as e:
                return False, f"Cannot open image: {str(e)}"
                
        except Exception as e:
            return False, f"Request failed: {str(e)}"
    
    def find_better_image_url(self, orchid_record):
        """Try to find a better quality image URL for the orchid"""
        
        # If it's a Ron Parsons photo, try different URL patterns
        if orchid_record.photographer == "Ron Parsons" and orchid_record.image_url:
            original_url = orchid_record.image_url
            
            # Try replacing with higher resolution versions
            better_urls = []
            
            # Try removing size suffixes
            url_without_suffix = re.sub(r'_sm\.|_small\.|_thumb\.', '.', original_url)
            if url_without_suffix != original_url:
                better_urls.append(url_without_suffix)
            
            # Try replacing small with large
            large_url = original_url.replace('_sm.', '_lg.').replace('_small.', '_large.')
            if large_url != original_url:
                better_urls.append(large_url)
            
            # Try direct file names without copy suffixes
            clean_url = re.sub(r'%20copy\.|%20Copy\.|\%20copy\.', '.', original_url)
            if clean_url != original_url:
                better_urls.append(clean_url)
            
            # Test each potential better URL
            for test_url in better_urls:
                is_good, reason = self.check_image_quality(test_url)
                if is_good:
                    logger.info(f"✅ Found better image: {orchid_record.display_name}")
                    return test_url
        
        # For Gary Yong Gee, try to construct better URLs
        elif orchid_record.photographer == "Gary Yong Gee":
            # Try to find the original Gary Yong Gee page and extract high-res image
            if orchid_record.display_name:
                genus = orchid_record.display_name.split()[0].lower() if orchid_record.display_name else ""
                if genus:
                    # Try Gary's site structure
                    test_urls = [
                        f"https://orchids.yonggee.name/images/{genus}_high.jpg",
                        f"https://orchids.yonggee.name/photos/{genus}.jpg"
                    ]
                    
                    for test_url in test_urls:
                        is_good, reason = self.check_image_quality(test_url)
                        if is_good:
                            return test_url
        
        return None
    
    def fix_orchid_images(self, limit=50):
        """Fix blurry/problematic images in the database"""
        logger.info(f"🔧 FIXING IMAGE QUALITY - Checking up to {limit} records...")
        
        with app.app_context():
            # Get orchids that might have image quality issues
            orchids_to_check = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None)
            ).limit(limit).all()
            
            logger.info(f"📊 Checking {len(orchids_to_check)} orchid images...")
            
            for orchid in orchids_to_check:
                try:
                    # Check current image quality
                    is_good, reason = self.check_image_quality(orchid.image_url)
                    
                    if not is_good:
                        logger.info(f"❌ Poor quality: {orchid.display_name} - {reason}")
                        
                        # Try to find better image
                        better_url = self.find_better_image_url(orchid)
                        
                        if better_url:
                            # Verify the better URL is actually better
                            is_better, better_reason = self.check_image_quality(better_url)
                            
                            if is_better:
                                # Update the record
                                orchid.image_url = better_url
                                db.session.commit()
                                
                                self.fixed_count += 1
                                logger.info(f"✅ FIXED: {orchid.display_name} - {better_reason}")
                            else:
                                logger.info(f"⚠️ Better URL also failed: {orchid.display_name}")
                        else:
                            logger.info(f"🔍 No better URL found: {orchid.display_name}")
                    else:
                        logger.info(f"✅ Good quality: {orchid.display_name} - {reason}")
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"❌ Error checking {orchid.display_name}: {str(e)}")
            
            logger.info(f"🎉 IMAGE QUALITY FIX COMPLETE!")
            logger.info(f"📈 Fixed {self.fixed_count} images")
    
    def fix_orchid_of_day_specifically(self):
        """Specifically fix the Orchid of the Day image"""
        logger.info("🌟 FIXING ORCHID OF THE DAY IMAGE...")
        
        with app.app_context():
            # Find recent featured orchids that might be "Orchid of the Day"
            recent_orchids = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None)
            ).order_by(OrchidRecord.created_at.desc()).limit(20).all()
            
            for orchid in recent_orchids:
                logger.info(f"🔍 Checking: {orchid.display_name}")
                
                is_good, reason = self.check_image_quality(orchid.image_url)
                
                if not is_good:
                    logger.info(f"❌ Issue found: {reason}")
                    
                    better_url = self.find_better_image_url(orchid)
                    if better_url:
                        orchid.image_url = better_url
                        db.session.commit()
                        logger.info(f"✅ FIXED Orchid of Day candidate: {orchid.display_name}")
                        self.fixed_count += 1
                else:
                    logger.info(f"✅ Image OK: {orchid.display_name}")
                
                time.sleep(0.2)
    
    def run_comprehensive_image_fix(self):
        """Run comprehensive image quality fixing"""
        logger.info("🚀 COMPREHENSIVE IMAGE QUALITY REPAIR")
        logger.info("=" * 50)
        
        start_time = time.time()
        
        # Phase 1: Fix Orchid of the Day specifically
        self.fix_orchid_of_day_specifically()
        
        # Phase 2: Fix general image quality issues
        self.fix_orchid_images(100)  # Check 100 records
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 50)
        logger.info("🎉 IMAGE REPAIR COMPLETE!")
        logger.info(f"🔧 Total images fixed: {self.fixed_count}")
        logger.info(f"⏱️ Time taken: {elapsed:.1f} seconds")
        
        return {
            'images_fixed': self.fixed_count,
            'elapsed_time': elapsed
        }

if __name__ == "__main__":
    fixer = ImageQualityFixer()
    results = fixer.run_comprehensive_image_fix()
    
    print(f"\n🎯 IMAGE QUALITY FIX RESULTS:")
    print(f"🔧 Images fixed: {results['images_fixed']}")
    print(f"⏱️ Time: {results['elapsed_time']:.1f}s")
    print("🚀 Scraping continues in background!")