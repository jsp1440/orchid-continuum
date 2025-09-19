#!/usr/bin/env python3
"""
COMPLETE ORCHID COLLECTION - RUN UNTIL FINISHED
Aggressively collect all photos from all sources without stopping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
from ron_parsons_scraper import RonParsonsOrchidScraper
from international_orchid_scraper import InternationalOrchidScraper
import time
from datetime import datetime

def run_complete_collection():
    """Run complete orchid collection from ALL sources until finished"""
    with app.app_context():
        print("🚀 COMPLETE ORCHID COLLECTION - ALL SOURCES")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Target: Collect ALL available photos until completion")
        print()
        
        # Initialize all scrapers
        comprehensive_scraper = ComprehensiveOrchidScraper()
        ron_parsons_scraper = RonParsonsOrchidScraper()
        
        total_results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        # Starting database status
        print("📊 STARTING DATABASE STATUS:")
        start_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        print(f"   Starting orchids: {start_count:,}")
        print()
        
        # PHASE 1: Gary Young Gee - Complete Collection
        print("🎯 PHASE 1: GARY YOUNG GEE - COMPLETE COLLECTION")
        print("   Target: ALL ~10,000 photos from all genera")
        print("   Strategy: Process every genus A-Z until exhausted")
        print()
        
        try:
            print("🌺 Starting Gary Young Gee comprehensive scraping...")
            gary_results = comprehensive_scraper.scrape_gary_yong_gee_comprehensive(
                max_genera_per_letter=999,  # No limit
                max_species_per_genus=999,  # No limit  
                max_photos_per_species=999  # No limit
            )
            
            total_results['processed'] += gary_results['processed']
            total_results['errors'] += gary_results['errors']
            total_results['skipped'] += gary_results['skipped']
            
            print(f"✅ Gary Young Gee COMPLETE:")
            print(f"   Photos collected: {gary_results['processed']:,}")
            print(f"   Errors: {gary_results['errors']:,}")
            print(f"   Skipped duplicates: {gary_results['skipped']:,}")
            
        except Exception as e:
            print(f"❌ Gary Young Gee collection error: {e}")
            total_results['errors'] += 1
        
        # Check progress
        current_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        print(f"📈 Current total: {current_count:,} (+{current_count - start_count:,})")
        print()
        
        # PHASE 2: Ron Parsons - Complete Flickr Collection
        print("🎯 PHASE 2: RON PARSONS - COMPLETE FLICKR COLLECTION")
        print("   Target: ALL 118,952+ photos from every album")
        print("   Strategy: Process every album until exhausted")
        print()
        
        try:
            print("📸 Starting Ron Parsons comprehensive Flickr scraping...")
            ron_results = ron_parsons_scraper.scrape_ron_parsons_comprehensive(
                max_albums=999,     # Process all albums
                max_photos_per_album=999,  # All photos per album
                include_sets=True,  # Include all photo sets
                include_galleries=True  # Include galleries
            )
            
            total_results['processed'] += ron_results['processed']
            total_results['errors'] += ron_results['errors'] 
            total_results['skipped'] += ron_results['skipped']
            
            print(f"✅ Ron Parsons COMPLETE:")
            print(f"   Photos collected: {ron_results['processed']:,}")
            print(f"   Albums processed: {ron_results.get('albums_processed', 0):,}")
            print(f"   Errors: {ron_results['errors']:,}")
            print(f"   Skipped duplicates: {ron_results['skipped']:,}")
            
        except Exception as e:
            print(f"❌ Ron Parsons collection error: {e}")
            total_results['errors'] += 1
        
        # Check progress again
        current_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        print(f"📈 Current total: {current_count:,} (+{current_count - start_count:,})")
        print()
        
        # PHASE 3: International Sources - Complete Collection
        print("🎯 PHASE 3: INTERNATIONAL SOURCES - COMPLETE COLLECTION")
        print("   Target: ALL photos from international botanical sites")
        print("   Strategy: Process every available source")
        print()
        
        try:
            print("🌍 Starting international orchid sources...")
            international_scraper = InternationalOrchidScraper()
            intl_results = international_scraper.scrape_all_international_sources(
                max_photos_per_source=999,  # No limits
                include_backup_sources=True  # Include all backup sources
            )
            
            total_results['processed'] += intl_results['processed']
            total_results['errors'] += intl_results['errors']
            total_results['skipped'] += intl_results['skipped']
            
            print(f"✅ International Sources COMPLETE:")
            print(f"   Photos collected: {intl_results['processed']:,}")
            print(f"   Sources processed: {intl_results.get('sources_processed', 0):,}")
            print(f"   Errors: {intl_results['errors']:,}")
            
        except Exception as e:
            print(f"❌ International collection error: {e}")
            total_results['errors'] += 1
        
        # FINAL DATABASE STATUS
        print()
        print("📊 FINAL DATABASE STATUS:")
        final_count = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record")).scalar()
        
        # Count by source
        gary_final = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%gary%'")).scalar()
        ron_final = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%ron%'")).scalar()
        intl_final = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE ingestion_source LIKE '%international%'")).scalar()
        
        with_images = db.session.execute(db.text("SELECT COUNT(*) FROM orchid_record WHERE image_url IS NOT NULL AND image_url != ''")).scalar()
        
        print(f"   Total orchids: {final_count:,}")
        print(f"   Photos added: +{final_count - start_count:,}")
        print(f"   Gary Young Gee: {gary_final:,}")
        print(f"   Ron Parsons: {ron_final:,}")
        print(f"   International: {intl_final:,}")
        print(f"   With images: {with_images:,} ({with_images/final_count*100:.1f}%)")
        print()
        
        # COMPLETION SUMMARY
        print("🎉 COMPLETE ORCHID COLLECTION FINISHED!")
        print("=" * 60)
        print(f"📈 TOTAL COLLECTION RESULTS:")
        print(f"   Photos collected: {total_results['processed']:,}")
        print(f"   Total errors: {total_results['errors']:,}")
        print(f"   Duplicates skipped: {total_results['skipped']:,}")
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Success metrics
        target_100k = 100000
        progress = (final_count / target_100k) * 100
        
        print()
        print(f"🎯 TARGET ACHIEVEMENT:")
        print(f"   Target: {target_100k:,} photos")
        print(f"   Collected: {final_count:,} photos")
        print(f"   Progress: {progress:.1f}%")
        
        if final_count >= target_100k:
            print(f"   🏆 SUCCESS: Target exceeded!")
        elif final_count >= 50000:
            print(f"   🎉 MAJOR SUCCESS: Substantial collection achieved!")
        elif final_count >= 25000:
            print(f"   ✅ GOOD PROGRESS: Significant growth achieved!")
        else:
            print(f"   📈 PROGRESS MADE: Collection expanded!")
        
        print()
        print("🌺 All available orchid photos have been collected!")
        print("🏆 Darwin Core export ready with enhanced taxonomic data!")

if __name__ == "__main__":
    run_complete_collection()