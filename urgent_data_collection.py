#!/usr/bin/env python3
"""
URGENT DATA COLLECTION - IMPERATIVE PHOTO CAPTURE
Direct HTTP scraping approach that works reliably
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
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UrgentDataCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.collected_today = 0
        
    def collect_gary_yong_gee_direct(self):
        """Direct collection from Gary Yong Gee - bypass broken methods"""
        logger.info("🌟 URGENT: Gary Yong Gee Direct Collection")
        
        collected = 0
        
        # Start with high-value genera
        priority_genera = [
            'cattleya', 'dendrobium', 'phalaenopsis', 'oncidium', 'cymbidium',
            'masdevallia', 'bulbophyllum', 'paphiopedilum', 'vanda', 'brassia',
            'miltonia', 'laelia', 'epidendrum', 'maxillaria', 'coelogyne'
        ]
        
        for genus in priority_genera:
            try:
                genus_url = f"https://orchids.yonggee.name/genera/{genus}"
                logger.info(f"📸 Collecting {genus}...")
                
                response = self.session.get(genus_url, timeout=20)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for species links
                    species_links = soup.find_all('a', href=re.compile(r'/species/'))
                    logger.info(f"Found {len(species_links)} species in {genus}")
                    
                    # Process first 20 species per genus for speed
                    for i, link in enumerate(species_links[:20]):
                        if i >= 20:  # Limit for speed
                            break
                            
                        species_url = urljoin(genus_url, link.get('href'))
                        species_data = self.scrape_species_page(species_url)
                        
                        if species_data:
                            success = self.save_orchid_record(species_data, f'gary_yong_gee_{genus}')
                            if success:
                                collected += 1
                                self.collected_today += 1
                        
                        time.sleep(0.5)  # Rate limiting
                
                logger.info(f"✅ {genus}: {collected} species collected")
                time.sleep(2)  # Genus-level rate limiting
                
            except Exception as e:
                logger.error(f"❌ Error collecting {genus}: {str(e)}")
        
        return collected
    
    def scrape_species_page(self, url):
        """Scrape individual species page for data and images"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract species name from title or heading
                title = soup.find('title')
                h1 = soup.find('h1')
                
                species_name = None
                if title:
                    species_name = title.get_text(strip=True)
                elif h1:
                    species_name = h1.get_text(strip=True)
                
                if not species_name:
                    return None
                
                # Clean up species name
                species_name = re.sub(r'^[^-]+-\s*', '', species_name)  # Remove site prefix
                species_name = species_name.replace(' - Gary Yong Gee', '').strip()
                
                # Look for images
                images = soup.find_all('img')
                image_url = None
                
                for img in images:
                    src = img.get('src', '')
                    if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.webp']):
                        if 'logo' not in src.lower() and 'banner' not in src.lower():
                            image_url = urljoin(url, src)
                            break
                
                return {
                    'display_name': species_name,
                    'scientific_name': species_name,
                    'image_url': image_url,
                    'source_url': url,
                    'photographer': 'Gary Yong Gee'
                }
                
        except Exception as e:
            logger.error(f"Error scraping species page {url}: {str(e)}")
            return None
    
    def collect_ron_parsons_direct(self):
        """Direct collection from Ron Parsons - bypass broken methods"""
        logger.info("🌟 URGENT: Ron Parsons Direct Collection")
        
        collected = 0
        
        # Direct URLs from his site
        target_urls = [
            "https://www.flowershots.net/Orchid_Photogallery.html",
            "https://www.flowershots.net/web-content/Photogallery/Masdevallias/index.html",
            "https://www.flowershots.net/web-content/Photogallery/Oncidium/index.html",
            "https://www.flowershots.net/web-content/stanhopea%20webpages/index.html"
        ]
        
        for url in target_urls:
            try:
                logger.info(f"📸 Processing {url}...")
                response = self.session.get(url, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all images
                    images = soup.find_all('img')
                    
                    for img in images:
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        
                        if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg']):
                            full_url = urljoin(url, src)
                            
                            # Extract orchid name
                            orchid_name = self.extract_orchid_name_from_path(src, alt)
                            
                            if orchid_name:
                                orchid_data = {
                                    'display_name': orchid_name,
                                    'scientific_name': orchid_name,
                                    'image_url': full_url,
                                    'photographer': 'Ron Parsons',
                                    'source_url': url
                                }
                                
                                success = self.save_orchid_record(orchid_data, 'ron_parsons_direct')
                                if success:
                                    collected += 1
                                    self.collected_today += 1
                        
                        time.sleep(0.3)
                
            except Exception as e:
                logger.error(f"❌ Error processing {url}: {str(e)}")
        
        return collected
    
    def extract_orchid_name_from_path(self, path, alt_text):
        """Extract orchid name from file path or alt text"""
        # Try alt text first
        if alt_text and len(alt_text.strip()) > 3:
            name = alt_text.strip()
            if any(char.isalpha() for char in name):
                return name
        
        # Extract from filename
        filename = os.path.basename(urlparse(path).path)
        name = os.path.splitext(filename)[0]
        
        # Clean up filename
        name = name.replace('-', ' ').replace('_', ' ').replace('%20', ' ')
        name = re.sub(r'\d+$', '', name).strip()  # Remove trailing numbers
        
        # Skip generic names
        generic_names = ['image', 'photo', 'dsc', 'img', 'copy']
        if name.lower() in generic_names:
            return None
        
        if len(name) > 3 and any(char.isalpha() for char in name):
            return name.title()
        
        return None
    
    def save_orchid_record(self, orchid_data, source):
        """Save orchid record to database"""
        try:
            with app.app_context():
                # Check if already exists
                existing = OrchidRecord.query.filter_by(
                    display_name=orchid_data['display_name'],
                    photographer=orchid_data['photographer']
                ).first()
                
                if existing:
                    return False  # Skip duplicate
                
                # Create new record
                record = OrchidRecord(
                    display_name=orchid_data['display_name'],
                    scientific_name=orchid_data.get('scientific_name'),
                    photographer=orchid_data['photographer'],
                    image_url=orchid_data.get('image_url'),
                    ingestion_source=source
                )
                
                db.session.add(record)
                db.session.commit()
                
                logger.info(f"✅ Saved: {orchid_data['display_name']} ({orchid_data['photographer']})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error saving {orchid_data['display_name']}: {str(e)}")
            return False
    
    def run_urgent_collection(self):
        """Run complete urgent data collection"""
        logger.info("🚀 URGENT DATA COLLECTION - NO LIMITS!")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Get starting count
        with app.app_context():
            start_count = OrchidRecord.query.count()
            logger.info(f"📊 Starting records: {start_count}")
        
        # Phase 1: Gary Yong Gee
        gary_collected = self.collect_gary_yong_gee_direct()
        logger.info(f"🌺 Gary Yong Gee collected: {gary_collected}")
        
        # Phase 2: Ron Parsons  
        ron_collected = self.collect_ron_parsons_direct()
        logger.info(f"📸 Ron Parsons collected: {ron_collected}")
        
        # Final stats
        with app.app_context():
            end_count = OrchidRecord.query.count()
            new_records = end_count - start_count
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("🎉 URGENT COLLECTION COMPLETE!")
        logger.info(f"📈 NEW RECORDS: {new_records}")
        logger.info(f"📊 TOTAL RECORDS: {end_count}")
        logger.info(f"⏱️ Time elapsed: {elapsed:.1f} seconds")
        logger.info(f"🚀 Collection rate: {(new_records/elapsed*60):.1f} records/minute")
        
        return {
            'new_records': new_records,
            'total_records': end_count,
            'gary_collected': gary_collected,
            'ron_collected': ron_collected,
            'elapsed_time': elapsed
        }

if __name__ == "__main__":
    collector = UrgentDataCollector()
    results = collector.run_urgent_collection()
    print(f"\n🎯 URGENT COLLECTION RESULTS:")
    print(f"New records added: {results['new_records']}")
    print(f"Total database: {results['total_records']}")
    print(f"Time: {results['elapsed_time']:.1f}s")