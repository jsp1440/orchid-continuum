#!/usr/bin/env python3
"""
FULL PRODUCTION ORCHID SCRAPING
Unleash Ron Parsons and Gary Young Gee scrapers to collect ALL photos
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
from ron_parsons_scraper import RonParsonsOrchidScraper
import time
from datetime import datetime

def run_full_collection():
    """Run full production scraping for both major photographers"""
    with app.app_context():
        print("🚀 STARTING FULL PRODUCTION ORCHID SCRAPING")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Initialize scrapers
        comprehensive_scraper = ComprehensiveOrchidScraper()
        ron_parsons_scraper = RonParsonsOrchidScraper()
        
        total_results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        print("📊 PRE-SCRAPING DATABASE STATUS:")
        current_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        gary_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%gary%'")).scalar()  
        ron_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%ron%'")).scalar()
        
        print(f"   Current total orchids: {current_count:,}")
        print(f"   Gary Young Gee orchids: {gary_count:,}")
        print(f"   Ron Parsons orchids: {ron_count:,}")
        print()
        
        # Phase 1: Gary Young Gee (10,000+ photos expected)
        print("🎯 PHASE 1: GARY YOUNG GEE FULL COLLECTION")
        print("   Target: ~10,000 photos from 440+ genera")
        print("   Source: orchids.yonggee.name")
        print()
        
        try:
            gary_results = comprehensive_scraper.scrape_gary_yong_gee_comprehensive()
            total_results['processed'] += gary_results['processed']
            total_results['errors'] += gary_results['errors']
            total_results['skipped'] += gary_results['skipped']
            
            print(f"✅ Gary Young Gee Complete:")
            print(f"   Processed: {gary_results['processed']:,} orchids")
            print(f"   Errors: {gary_results['errors']:,}")
            print(f"   Skipped: {gary_results['skipped']:,}")
            
        except Exception as e:
            print(f"❌ Gary Young Gee scraping failed: {e}")
            total_results['errors'] += 1
        
        print()
        
        # Small break between phases
        print("⏳ Brief pause before Ron Parsons collection...")
        time.sleep(5)
        
        # Phase 2: Ron Parsons (117,000+ photos expected)  
        print("🎯 PHASE 2: RON PARSONS FULL COLLECTION")
        print("   Target: 118,952+ photos from Flickr + website")
        print("   Source: flickr.com/photos/rpflowershots + flowershots.net")
        print()
        
        try:
            ron_results = ron_parsons_scraper.scrape_ron_parsons_comprehensive()
            total_results['processed'] += ron_results['processed']
            total_results['errors'] += ron_results['errors']
            total_results['skipped'] += ron_results['skipped']
            
            print(f"✅ Ron Parsons Complete:")
            print(f"   Processed: {ron_results['processed']:,} orchids")
            print(f"   Errors: {ron_results['errors']:,}")
            print(f"   Skipped: {ron_results['skipped']:,}")
            
        except Exception as e:
            print(f"❌ Ron Parsons scraping failed: {e}")
            total_results['errors'] += 1
        
        # Final database status
        print()
        print("📊 POST-SCRAPING DATABASE STATUS:")
        final_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        final_gary = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%gary%'")).scalar()  
        final_ron = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%ron%'")).scalar()
        
        print(f"   Total orchids: {final_count:,} (+{final_count - current_count:,})")
        print(f"   Gary Young Gee: {final_gary:,} (+{final_gary - gary_count:,})")
        print(f"   Ron Parsons: {final_ron:,} (+{final_ron - ron_count:,})")
        print()
        
        # Summary
        print("🎉 FULL PRODUCTION SCRAPING COMPLETE!")
        print("=" * 60)
        print(f"📈 TOTAL RESULTS:")
        print(f"   New orchids added: {total_results['processed']:,}")
        print(f"   Total errors: {total_results['errors']:,}")
        print(f"   Total skipped: {total_results['skipped']:,}")
        print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        expected_total = 10000 + 117000  # Gary + Ron expected
        print()
        print(f"🎯 EXPECTED vs ACTUAL:")
        print(f"   Expected: ~{expected_total:,} photos")
        print(f"   Collected: {total_results['processed']:,} photos")
        
        if total_results['processed'] > 1000:
            print(f"   🎉 SUCCESS: Major photo collection achieved!")
        else:
            print(f"   ⚠️  Low collection - may need scraper adjustments")

if __name__ == "__main__":
    run_full_collection()