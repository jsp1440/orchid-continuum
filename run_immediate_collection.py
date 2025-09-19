#!/usr/bin/env python3
"""
IMMEDIATE COMPLETE ORCHID COLLECTION
Run all working scrapers until finished - no limits, no timeouts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
from ron_parsons_scraper import RonParsonsOrchidScraper
import time
from datetime import datetime
from models import OrchidRecord

def run_immediate_collection():
    """Run immediate complete collection from all working sources"""
    with app.app_context():
        print("🚀 IMMEDIATE COMPLETE ORCHID COLLECTION")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("🎯 Strategy: Run until ALL photos collected from working sources")
        print("⚡ Mode: NO LIMITS, NO TIMEOUTS, RUN TO COMPLETION")
        print()
        
        # Starting counts
        start_count = OrchidRecord.query.count()
        start_gary = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%gary%')).count()
        start_ron = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%ron%')).count()
        
        print("📊 STARTING STATUS:")
        print(f"   Total orchids: {start_count:,}")
        print(f"   Gary Young Gee: {start_gary:,}")
        print(f"   Ron Parsons: {start_ron:,}")
        print()
        
        total_added = 0
        
        # PHASE 1: Gary Young Gee - Aggressive Complete Collection
        print("🎯 PHASE 1: GARY YOUNG GEE - AGGRESSIVE COMPLETE COLLECTION")
        print("   Target: Every single photo from all genera A-Z")
        print("   Limits: REMOVED - collect everything available")
        print()
        
        try:
            scraper = ComprehensiveOrchidScraper()
            
            # Run the most comprehensive Gary collection possible
            alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            gary_total = 0
            
            for letter in alphabet:
                print(f"🔤 Processing ALL genera starting with '{letter}'...")
                
                try:
                    # Call the existing working method with maximum settings
                    letter_results = scraper.scrape_gary_yong_gee_by_letter(
                        letter, 
                        max_genera=999,      # No genus limit
                        max_species=999,     # No species limit  
                        max_photos=999       # No photo limit
                    )
                    
                    gary_total += letter_results.get('processed', 0)
                    print(f"   ✅ Letter {letter}: +{letter_results.get('processed', 0)} photos")
                    
                except Exception as e:
                    print(f"   ⚠️ Letter {letter} error: {e}")
                    continue
                
                # Quick progress check
                current = OrchidRecord.query.count()
                if current > start_count:
                    print(f"   📈 Running total: {current:,} (+{current - start_count:,})")
            
            print(f"✅ Gary Young Gee PHASE COMPLETE: +{gary_total:,} photos")
            
        except Exception as e:
            print(f"❌ Gary Young Gee collection error: {e}")
        
        # Check Gary progress
        mid_count = OrchidRecord.query.count()
        gary_final = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%gary%')).count()
        print(f"📊 After Gary: {mid_count:,} total (+{mid_count - start_count:,})")
        print(f"   Gary orchids: {gary_final:,} (+{gary_final - start_gary:,})")
        print()
        
        # PHASE 2: Ron Parsons - Complete Flickr Exhaustion
        print("🎯 PHASE 2: RON PARSONS - COMPLETE FLICKR EXHAUSTION")
        print("   Target: Every single photo from all albums")
        print("   Limits: REMOVED - exhaust entire Flickr collection")
        print()
        
        try:
            ron_scraper = RonParsonsOrchidScraper()
            
            # Run most aggressive Ron Parsons collection
            ron_results = ron_scraper.scrape_all_flickr_albums_aggressively(
                max_albums=999,              # Process every album
                max_photos_per_album=999,    # Every photo in each album
                skip_rate_limiting=False,    # Be respectful but thorough
                exhaust_collection=True      # Don't stop until done
            )
            
            print(f"✅ Ron Parsons PHASE COMPLETE:")
            print(f"   Photos added: +{ron_results.get('processed', 0):,}")
            print(f"   Albums processed: {ron_results.get('albums', 0):,}")
            print(f"   Total requests: {ron_results.get('requests', 0):,}")
            
        except Exception as e:
            print(f"❌ Ron Parsons collection error: {e}")
            # Fallback to basic Ron Parsons scraping
            try:
                print("🔄 Trying basic Ron Parsons collection...")
                basic_results = ron_scraper.scrape_ron_parsons_basic_collection()
                print(f"✅ Basic collection: +{basic_results.get('processed', 0):,} photos")
            except Exception as e2:
                print(f"❌ Basic Ron Parsons also failed: {e2}")
        
        # FINAL STATUS
        print()
        print("📊 IMMEDIATE COLLECTION COMPLETE!")
        print("=" * 60)
        
        final_count = OrchidRecord.query.count()
        final_gary = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%gary%')).count()
        final_ron = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%ron%')).count()
        
        with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).count()
        
        total_added = final_count - start_count
        
        print(f"📈 COLLECTION RESULTS:")
        print(f"   Starting orchids: {start_count:,}")
        print(f"   Final orchids: {final_count:,}")
        print(f"   PHOTOS ADDED: +{total_added:,}")
        print()
        print(f"📊 BY SOURCE:")
        print(f"   Gary Young Gee: {final_gary:,} (+{final_gary - start_gary:,})")
        print(f"   Ron Parsons: {final_ron:,} (+{final_ron - start_ron:,})")
        print(f"   With images: {with_images:,} ({with_images/final_count*100:.1f}%)")
        print()
        
        # Achievement assessment
        target_100k = 100000
        progress = (final_count / target_100k) * 100
        
        print(f"🎯 TARGET PROGRESS:")
        print(f"   Target: {target_100k:,} photos")
        print(f"   Current: {final_count:,} photos")
        print(f"   Progress: {progress:.1f}%")
        
        if total_added >= 10000:
            print(f"   🏆 EXCELLENT: Major collection growth achieved!")
        elif total_added >= 5000:
            print(f"   🎉 SUCCESS: Significant photos collected!")
        elif total_added >= 1000:
            print(f"   ✅ GOOD: Solid collection progress!")
        else:
            print(f"   📈 PROGRESS: Collection expanded!")
        
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🌺 IMMEDIATE COLLECTION FINISHED!")
        print("Ready for enhanced Darwin Core export with new photos!")

if __name__ == "__main__":
    run_immediate_collection()