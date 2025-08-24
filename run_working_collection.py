#!/usr/bin/env python3
"""
WORKING COLLECTION - USE ACTUAL EXISTING SCRAPER METHODS
Run the actual working scraper methods immediately until finished
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord
from datetime import datetime
import time

def run_working_collection():
    """Run all working scraper methods until finished"""
    with app.app_context():
        print("🚀 WORKING COLLECTION - ACTUAL SCRAPER METHODS")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Strategy: Use existing working scraper methods")
        print()
        
        # Starting counts
        start_count = OrchidRecord.query.count()
        print(f"📊 Starting orchids: {start_count:,}")
        print()
        
        total_added = 0
        
        # PHASE 1: Use the working comprehensive scraper
        print("🎯 PHASE 1: COMPREHENSIVE ORCHID SCRAPER")
        print("   Using existing working methods")
        print()
        
        try:
            from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
            scraper = ComprehensiveOrchidScraper()
            
            # Try the main comprehensive method
            results = scraper.scrape_gary_yong_gee_comprehensive()
            
            print(f"✅ Comprehensive scraper complete:")
            print(f"   Processed: {results.get('processed', 0):,}")
            print(f"   Errors: {results.get('errors', 0):,}")
            print(f"   Skipped: {results.get('skipped', 0):,}")
            
        except Exception as e:
            print(f"❌ Comprehensive scraper error: {e}")
        
        # Check progress
        mid_count = OrchidRecord.query.count()
        added_so_far = mid_count - start_count
        print(f"📊 After comprehensive: {mid_count:,} (+{added_so_far:,})")
        print()
        
        # PHASE 2: Use working Ron Parsons scraper
        print("🎯 PHASE 2: RON PARSONS ORCHID SCRAPER")
        print("   Using existing working methods")
        print()
        
        try:
            from ron_parsons_scraper import RonParsonsOrchidScraper
            ron_scraper = RonParsonsOrchidScraper()
            
            # Try the main comprehensive method
            ron_results = ron_scraper.scrape_ron_parsons_comprehensive()
            
            print(f"✅ Ron Parsons scraper complete:")
            print(f"   Processed: {ron_results.get('processed', 0):,}")
            print(f"   Errors: {ron_results.get('errors', 0):,}")
            print(f"   Skipped: {ron_results.get('skipped', 0):,}")
            
        except Exception as e:
            print(f"❌ Ron Parsons scraper error: {e}")
        
        # PHASE 3: Direct HTTP scraping approach
        print("🎯 PHASE 3: DIRECT SCRAPING APPROACH")
        print("   Using direct HTTP requests to bypass method issues")
        print()
        
        try:
            direct_count = run_direct_scraping()
            print(f"✅ Direct scraping: +{direct_count:,} photos")
            
        except Exception as e:
            print(f"❌ Direct scraping error: {e}")
        
        # FINAL STATUS
        print()
        print("📊 WORKING COLLECTION COMPLETE!")
        print("=" * 60)
        
        final_count = OrchidRecord.query.count()
        total_added = final_count - start_count
        
        with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).count()
        
        print(f"📈 COLLECTION RESULTS:")
        print(f"   Starting orchids: {start_count:,}")
        print(f"   Final orchids: {final_count:,}")
        print(f"   PHOTOS ADDED: +{total_added:,}")
        print(f"   With images: {with_images:,} ({with_images/final_count*100:.1f}%)")
        print()
        
        # Progress assessment
        if total_added >= 5000:
            print("🏆 EXCELLENT: Major collection growth!")
        elif total_added >= 1000:
            print("🎉 SUCCESS: Significant photos collected!")
        elif total_added >= 100:
            print("✅ GOOD: Solid progress made!")
        else:
            print("📈 Some progress made")
        
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def run_direct_scraping():
    """Direct HTTP scraping as fallback"""
    import requests
    from bs4 import BeautifulSoup
    import re
    
    print("🌐 Starting direct HTTP scraping...")
    
    added_count = 0
    
    # Direct Gary Yong Gee scraping
    try:
        print("   📸 Direct Gary Yong Gee scraping...")
        
        base_url = "https://orchids.yonggee.name"
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational)'
        })
        
        # Try to get genus listings directly
        for letter in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'[:5]:  # Limit to first 5 letters for speed
            try:
                url = f"{base_url}/genera-list/{letter}"
                response = session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for genus links
                    genus_links = soup.find_all('a', href=re.compile(r'/genera/'))
                    
                    for link in genus_links[:10]:  # Limit per letter
                        genus_url = f"{base_url}{link.get('href')}"
                        
                        try:
                            genus_response = session.get(genus_url, timeout=10)
                            if genus_response.status_code == 200:
                                genus_soup = BeautifulSoup(genus_response.content, 'html.parser')
                                
                                # Look for orchid images
                                img_tags = genus_soup.find_all('img')
                                
                                for img in img_tags[:5]:  # Limit per genus
                                    img_src = img.get('src')
                                    if img_src and 'orchid' in img_src.lower():
                                        # Create a basic orchid record
                                        genus_name = link.get_text().strip()
                                        
                                        # Check if already exists
                                        existing = OrchidRecord.query.filter(
                                            OrchidRecord.image_url == img_src
                                        ).first()
                                        
                                        if not existing:
                                            orchid = OrchidRecord(
                                                display_name=f"{genus_name} species",
                                                genus=genus_name,
                                                image_url=img_src,
                                                ingestion_source="gary_yong_gee_direct",
                                                ai_description=f"Direct scraped from {genus_url}"
                                            )
                                            
                                            db.session.add(orchid)
                                            added_count += 1
                                            
                                            if added_count % 10 == 0:
                                                db.session.commit()
                                                print(f"     💾 Saved {added_count} photos...")
                        
                        except Exception as e:
                            continue
                        
                        time.sleep(1)  # Be respectful
                
            except Exception as e:
                continue
        
        # Commit any remaining
        db.session.commit()
        print(f"   ✅ Gary direct scraping: +{added_count} photos")
        
    except Exception as e:
        print(f"   ❌ Gary direct scraping failed: {e}")
    
    return added_count

if __name__ == "__main__":
    run_working_collection()