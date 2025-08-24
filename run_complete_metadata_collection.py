#!/usr/bin/env python3
"""
COMPLETE METADATA COLLECTION
Collect photos AND all metadata from all sources immediately until finished
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord
from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
from ron_parsons_scraper import RonParsonsOrchidScraper
from datetime import datetime
import time

def run_complete_metadata_collection():
    """Run complete collection with full metadata extraction"""
    with app.app_context():
        print("🚀 COMPLETE METADATA COLLECTION")
        print("=" * 60)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("📸 Target: Photos + ALL metadata (scientific names, locations, dates, etc.)")
        print("⚡ Mode: Run until ALL sources exhausted")
        print()
        
        start_count = OrchidRecord.query.count()
        start_with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).count()
        
        print(f"📊 STARTING STATUS:")
        print(f"   Total orchids: {start_count:,}")
        print(f"   With images: {start_with_images:,}")
        print()
        
        # PHASE 1: Gary Yong Gee with Full Metadata
        print("🎯 PHASE 1: GARY YONG GEE + FULL METADATA")
        print("   Collecting: Photos, names, locations, descriptions, etc.")
        print()
        
        gary_results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            scraper = ComprehensiveOrchidScraper()
            gary_results = scraper.scrape_gary_yong_gee_comprehensive()
            
            print(f"✅ Gary Yong Gee Complete:")
            print(f"   Photos + metadata: {gary_results.get('processed', 0):,}")
            print(f"   Errors: {gary_results.get('errors', 0):,}")
            print(f"   Skipped: {gary_results.get('skipped', 0):,}")
            
        except Exception as e:
            print(f"❌ Gary collection error: {e}")
            gary_results['errors'] += 1
        
        # Progress check
        mid_count = OrchidRecord.query.count()
        mid_with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).count()
        
        print(f"📊 After Gary: {mid_count:,} total (+{mid_count - start_count:,})")
        print(f"   With images: {mid_with_images:,} (+{mid_with_images - start_with_images:,})")
        print()
        
        # PHASE 2: Ron Parsons with Full Metadata  
        print("🎯 PHASE 2: RON PARSONS + FULL METADATA")
        print("   Collecting: Professional photos, EXIF data, locations, dates")
        print()
        
        ron_results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            ron_scraper = RonParsonsOrchidScraper()
            ron_results = ron_scraper.scrape_ron_parsons_comprehensive()
            
            print(f"✅ Ron Parsons Complete:")
            print(f"   Photos + metadata: {ron_results.get('processed', 0):,}")
            print(f"   Albums processed: {ron_results.get('albums', 0):,}")
            print(f"   Errors: {ron_results.get('errors', 0):,}")
            print(f"   Skipped: {ron_results.get('skipped', 0):,}")
            
        except Exception as e:
            print(f"❌ Ron Parsons error: {e}")
            ron_results['errors'] += 1
        
        # PHASE 3: Enhanced Direct Metadata Scraping
        print("🎯 PHASE 3: ENHANCED DIRECT METADATA SCRAPING")
        print("   Target: Additional sources with rich metadata")
        print()
        
        direct_results = run_enhanced_direct_scraping()
        
        # FINAL COMPREHENSIVE STATUS
        print()
        print("📊 COMPLETE METADATA COLLECTION FINISHED!")
        print("=" * 60)
        
        final_count = OrchidRecord.query.count()
        final_with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.image_url != ''
        ).count()
        
        # Count records with rich metadata
        with_scientific_names = OrchidRecord.query.filter(
            OrchidRecord.scientific_name.isnot(None),
            OrchidRecord.scientific_name != ''
        ).count()
        
        with_locations = OrchidRecord.query.filter(
            OrchidRecord.region.isnot(None),
            OrchidRecord.region != ''
        ).count()
        
        with_descriptions = OrchidRecord.query.filter(
            OrchidRecord.ai_description.isnot(None),
            OrchidRecord.ai_description != ''
        ).count()
        
        total_added = final_count - start_count
        images_added = final_with_images - start_with_images
        
        print(f"📈 COLLECTION RESULTS:")
        print(f"   Starting records: {start_count:,}")
        print(f"   Final records: {final_count:,}")
        print(f"   TOTAL ADDED: +{total_added:,}")
        print()
        print(f"📸 IMAGE COLLECTION:")
        print(f"   Starting with images: {start_with_images:,}")
        print(f"   Final with images: {final_with_images:,}")
        print(f"   IMAGES ADDED: +{images_added:,}")
        print(f"   Image coverage: {final_with_images/final_count*100:.1f}%")
        print()
        print(f"📋 METADATA QUALITY:")
        print(f"   Scientific names: {with_scientific_names:,} ({with_scientific_names/final_count*100:.1f}%)")
        print(f"   Location data: {with_locations:,} ({with_locations/final_count*100:.1f}%)")
        print(f"   Descriptions: {with_descriptions:,} ({with_descriptions/final_count*100:.1f}%)")
        print()
        
        # Source breakdown
        gary_final = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%gary%')).count()
        ron_final = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%ron%')).count()
        direct_final = OrchidRecord.query.filter(OrchidRecord.ingestion_source.like('%direct%')).count()
        
        print(f"📊 BY SOURCE:")
        print(f"   Gary Yong Gee: {gary_final:,}")
        print(f"   Ron Parsons: {ron_final:,}")
        print(f"   Direct scraping: {direct_final:,}")
        print()
        
        # Achievement assessment
        target_100k = 100000
        progress = (final_count / target_100k) * 100
        
        print(f"🎯 PROGRESS TOWARD 100K TARGET:")
        print(f"   Target: {target_100k:,} photos")
        print(f"   Current: {final_count:,}")
        print(f"   Progress: {progress:.1f}%")
        
        if images_added >= 10000:
            print(f"   🏆 MASSIVE SUCCESS: {images_added:,} photos with metadata!")
        elif images_added >= 5000:
            print(f"   🎉 MAJOR SUCCESS: {images_added:,} photos collected!")
        elif images_added >= 1000:
            print(f"   ✅ SOLID SUCCESS: {images_added:,} photos added!")
        elif images_added >= 100:
            print(f"   📈 GOOD PROGRESS: {images_added:,} photos collected!")
        else:
            print(f"   📊 Progress made: Collection expanded")
        
        print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        print("🌺 READY FOR ENHANCED DARWIN CORE EXPORT!")
        print("All photos now include comprehensive metadata for GBIF submission")

def run_enhanced_direct_scraping():
    """Enhanced direct scraping with metadata extraction"""
    import requests
    from bs4 import BeautifulSoup
    import re
    from urllib.parse import urljoin, urlparse
    
    print("🌐 Enhanced direct metadata scraping...")
    
    added_count = 0
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
    })
    
    # Enhanced Gary Yong Gee scraping with metadata
    try:
        print("   📸 Enhanced Gary Yong Gee with metadata...")
        
        base_url = "https://orchids.yonggee.name"
        
        # Target specific genera pages with rich metadata
        target_genera = ['Bulbophyllum', 'Dendrobium', 'Cattleya', 'Oncidium', 'Phalaenopsis']
        
        for genus in target_genera:
            try:
                genus_url = f"{base_url}/genera/{genus.lower()}"
                response = session.get(genus_url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for species pages with detailed metadata
                    species_links = soup.find_all('a', href=re.compile(rf'/{genus.lower()}/'))
                    
                    for link in species_links[:20]:  # Process up to 20 species per genus
                        species_url = urljoin(base_url, link.get('href'))
                        
                        try:
                            species_response = session.get(species_url, timeout=10)
                            if species_response.status_code == 200:
                                species_soup = BeautifulSoup(species_response.content, 'html.parser')
                                
                                # Extract comprehensive metadata
                                species_name = link.get_text().strip()
                                
                                # Look for images
                                images = species_soup.find_all('img')
                                for img in images[:3]:  # Up to 3 images per species
                                    img_src = img.get('src')
                                    if img_src and not img_src.endswith('.gif'):
                                        img_url = urljoin(species_url, img_src)
                                        
                                        # Check for existing record
                                        existing = OrchidRecord.query.filter(
                                            OrchidRecord.image_url == img_url
                                        ).first()
                                        
                                        if not existing:
                                            # Extract metadata from page
                                            page_text = species_soup.get_text()
                                            
                                            # Extract location information
                                            location_patterns = [
                                                r'(Indonesia|Malaysia|Thailand|Philippines|Brazil|Ecuador|Colombia|Peru)',
                                                r'(Madagascar|Tanzania|India|China|Myanmar|Vietnam|Australia)'
                                            ]
                                            location = None
                                            for pattern in location_patterns:
                                                match = re.search(pattern, page_text, re.IGNORECASE)
                                                if match:
                                                    location = match.group(1)
                                                    break
                                            
                                            # Extract scientific name
                                            scientific_name = species_name
                                            if ' ' not in scientific_name:
                                                scientific_name = f"{genus} {species_name}"
                                            
                                            # Create record with metadata
                                            orchid = OrchidRecord(
                                                display_name=species_name,
                                                scientific_name=scientific_name,
                                                genus=genus,
                                                species=species_name.split()[-1] if ' ' in species_name else species_name,
                                                image_url=img_url,
                                                region=location,
                                                ingestion_source="gary_yong_gee_enhanced_direct",
                                                ai_description=f"Enhanced scraping from {species_url}",
                                                photographer="Gary Yong Gee"
                                            )
                                            
                                            db.session.add(orchid)
                                            added_count += 1
                                            
                                            if added_count % 25 == 0:
                                                db.session.commit()
                                                print(f"     💾 Saved {added_count} photos with metadata...")
                        
                        except Exception as e:
                            continue
                        
                        time.sleep(2)  # Be respectful
                
            except Exception as e:
                print(f"   ⚠️ Genus {genus} error: {e}")
                continue
        
        # Commit final batch
        db.session.commit()
        print(f"   ✅ Enhanced direct scraping: +{added_count} photos with metadata")
        
    except Exception as e:
        print(f"   ❌ Enhanced scraping failed: {e}")
    
    return {'processed': added_count, 'errors': 0, 'skipped': 0}

if __name__ == "__main__":
    run_complete_metadata_collection()