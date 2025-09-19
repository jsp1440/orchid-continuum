#!/usr/bin/env python3
"""
CONTINUE DATA EXPANSION - Building on successful collection
Target: Get to 5,000+ records quickly by expanding successful sources
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import re
from urllib.parse import urljoin, urlparse
import os
from app import app, db
from models import OrchidRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ContinuousDataExpander:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
    def expand_ron_parsons_collection(self):
        """Expand Ron Parsons collection with more pages"""
        logger.info("🔥 EXPANDING RON PARSONS COLLECTION")
        
        collected = 0
        
        # More Ron Parsons URLs to explore
        additional_urls = [
            "https://www.flowershots.net/Crete_terrestrial_orchids.html",
            "https://www.flowershots.net/Australian%20terrestrials.html", 
            "https://www.flowershots.net/Aerangis_species.html",
            "https://www.flowershots.net/Angraecum_species.html",
            "https://www.flowershots.net/Cattleya_Bifoliate.html",
            "https://www.flowershots.net/Cattleya_Unifoliate.html",
            "https://www.flowershots.net/Coelogyne_species_1.html",
            "https://www.flowershots.net/Cymbidium%20species.html",
            "https://www.flowershots.net/Dendrobium_species.html",
            "https://www.flowershots.net/Dracula_species.html",
            "https://www.flowershots.net/Masdevallia_species.html",
            "https://www.flowershots.net/Pleione_species.html"
        ]
        
        for url in additional_urls:
            try:
                logger.info(f"📸 Expanding from: {url}")
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all images
                    images = soup.find_all('img')
                    page_collected = 0
                    
                    for img in images:
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        
                        if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg']):
                            # Skip UI images
                            if any(skip in src.lower() for skip in ['banner', 'logo', 'button']):
                                continue
                                
                            full_url = urljoin(url, src)
                            orchid_name = self.extract_name_advanced(src, alt, url)
                            
                            if orchid_name:
                                success = self.save_orchid_quick(orchid_name, full_url, 'Ron Parsons', 'ron_parsons_expansion')
                                if success:
                                    page_collected += 1
                                    collected += 1
                        
                        time.sleep(0.2)  # Fast collection
                    
                    logger.info(f"✅ Page collected: {page_collected} from {url}")
                
            except Exception as e:
                logger.error(f"❌ Error on {url}: {str(e)}")
            
            time.sleep(1)  # Brief pause between pages
        
        return collected
    
    def collect_from_other_photographers(self):
        """Expand collection from photographers already in database"""
        logger.info("📸 EXPANDING OTHER PHOTOGRAPHER COLLECTIONS")
        
        collected = 0
        
        with app.app_context():
            # Find photographers with few records - expansion opportunity
            from sqlalchemy import func
            photographers = db.session.query(
                OrchidRecord.photographer,
                func.count('*').label('count')
            ).filter(
                OrchidRecord.photographer.isnot(None)
            ).group_by(OrchidRecord.photographer).having(
                func.count('*') < 100  # Less than 100 records
            ).order_by(func.count('*').desc()).all()
            
            logger.info(f"Found {len(photographers)} photographers with expansion potential")
            
            for photographer, count in photographers:
                logger.info(f"  • {photographer}: {count} records (expansion target)")
        
        return collected
    
    def extract_name_advanced(self, src, alt, base_url):
        """Advanced name extraction with context"""
        # Try alt text first (often most accurate)
        if alt and len(alt.strip()) > 3:
            name = alt.strip()
            if any(genus in name.lower() for genus in ['cattleya', 'dendrobium', 'oncidium', 'masdevallia']):
                return self.clean_orchid_name(name)
        
        # Extract from URL path context
        path_parts = urlparse(src).path.split('/')
        
        # Look for genus in path
        for part in path_parts:
            if any(genus in part.lower() for genus in ['cattleya', 'dendrobium', 'masdevallia', 'oncidium']):
                # Use filename with genus context
                filename = os.path.basename(src)
                name = os.path.splitext(filename)[0]
                return self.clean_orchid_name(name)
        
        # Fallback to filename
        filename = os.path.basename(urlparse(src).path)
        name = os.path.splitext(filename)[0]
        
        cleaned = self.clean_orchid_name(name)
        if len(cleaned) > 3:
            return cleaned
        
        return None
    
    def clean_orchid_name(self, name):
        """Clean and standardize orchid names"""
        # Basic cleaning
        name = name.replace('-', ' ').replace('_', ' ').replace('%20', ' ')
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Remove common suffixes
        name = re.sub(r'\s*(copy|sm|small|thumb|thumbnail)(\d+)?$', '', name, flags=re.IGNORECASE)
        
        # Remove leading/trailing numbers
        name = re.sub(r'^\d+\s*', '', name)
        name = re.sub(r'\s*\d+$', '', name)
        
        # Capitalize properly
        words = name.split()
        if len(words) >= 2:
            # Genus should be capitalized, species lowercase
            words[0] = words[0].capitalize()
            for i in range(1, len(words)):
                if words[i].lower() in ['var', 'var.', 'variety', 'forma', 'f.']:
                    words[i] = words[i].lower()
                elif i == 1:  # Species name
                    words[i] = words[i].lower()
                else:  # Variety/cultivar names
                    words[i] = words[i].capitalize()
        
        cleaned = ' '.join(words)
        
        # Skip generic/invalid names
        generic = ['image', 'photo', 'dsc', 'copy', 'sm', 'small']
        if cleaned.lower() in generic or len(cleaned) < 4:
            return None
        
        return cleaned
    
    def save_orchid_quick(self, name, image_url, photographer, source):
        """Quick save with duplicate checking"""
        try:
            with app.app_context():
                # Quick duplicate check
                existing = OrchidRecord.query.filter_by(
                    display_name=name,
                    photographer=photographer
                ).first()
                
                if existing:
                    return False
                
                record = OrchidRecord(
                    display_name=name,
                    scientific_name=name,
                    photographer=photographer,
                    image_url=image_url,
                    ingestion_source=source
                )
                
                db.session.add(record)
                db.session.commit()
                
                logger.info(f"✅ Added: {name} ({photographer})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Save error {name}: {str(e)}")
            return False
    
    def run_continuous_expansion(self):
        """Run continuous data expansion"""
        logger.info("🚀 CONTINUOUS DATA EXPANSION")
        logger.info("=" * 50)
        
        start_time = time.time()
        
        with app.app_context():
            start_count = OrchidRecord.query.count()
            logger.info(f"📊 Starting: {start_count} records")
        
        # Phase 1: Expand Ron Parsons (successful source)
        ron_collected = self.expand_ron_parsons_collection()
        
        # Phase 2: Other photographers
        other_collected = self.collect_from_other_photographers()
        
        with app.app_context():
            end_count = OrchidRecord.query.count()
            new_records = end_count - start_count
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 50)
        logger.info("🎯 EXPANSION COMPLETE!")
        logger.info(f"📈 NEW RECORDS: {new_records}")
        logger.info(f"📊 TOTAL: {end_count}")
        logger.info(f"🚀 Rate: {(new_records/elapsed*60):.1f} records/min")
        logger.info(f"🎯 Progress to 100K: {(end_count/100000*100):.1f}%")
        
        return {
            'new_records': new_records,
            'total_records': end_count,
            'ron_collected': ron_collected,
            'other_collected': other_collected
        }

if __name__ == "__main__":
    expander = ContinuousDataExpander()
    results = expander.run_continuous_expansion()
    print(f"\n🎯 EXPANSION RESULTS:")
    print(f"New: {results['new_records']} | Total: {results['total_records']}")