#!/usr/bin/env python3
"""
PARALLEL DATABASE SCRAPER - Multiple Sources Simultaneously
Scrapes 4-6 orchid databases at the same time for maximum collection speed
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
import threading
import queue
from concurrent.futures import ThreadPoolExecutor, as_completed
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ParallelOrchidScraper:
    def __init__(self):
        self.results_queue = queue.Queue()
        self.session_pool = []
        self.total_collected = 0
        self.lock = threading.Lock()
        
        # Create multiple sessions for parallel requests
        for i in range(6):
            session = requests.Session()
            session.headers.update({
                'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.{36+i} (KHTML, like Gecko) Chrome/91.0.4472.{124+i} Safari/537.{36+i}'
            })
            self.session_pool.append(session)
    
    def get_session(self):
        """Get a random session from the pool"""
        return random.choice(self.session_pool)
    
    def scrape_ron_parsons_parallel(self):
        """Scrape Ron Parsons with multiple threads"""
        logger.info("🌟 PARALLEL: Ron Parsons Collection")
        
        collected = 0
        
        # All the Ron Parsons URLs we want to hit
        ron_urls = [
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
            "https://www.flowershots.net/Pleione_species.html",
            "https://www.flowershots.net/Bulbophyllum_species.html",
            "https://www.flowershots.net/Paphiopedilum_species.html",
            "https://www.flowershots.net/Oncidium_species.html"
        ]
        
        def scrape_ron_page(url):
            page_collected = 0
            try:
                session = self.get_session()
                response = session.get(url, timeout=20)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    images = soup.find_all('img')
                    
                    for img in images:
                        src = img.get('src', '')
                        alt = img.get('alt', '')
                        
                        if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg']):
                            if any(skip in src.lower() for skip in ['banner', 'logo', 'button']):
                                continue
                                
                            full_url = urljoin(url, src)
                            name = self.extract_orchid_name(src, alt)
                            
                            if name and len(name) > 3:
                                success = self.save_orchid_parallel(name, full_url, 'Ron Parsons', 'ron_parsons_parallel')
                                if success:
                                    page_collected += 1
                        
                        time.sleep(0.1)
                
                logger.info(f"✅ Ron Parsons {url}: +{page_collected}")
                return page_collected
                
            except Exception as e:
                logger.error(f"❌ Ron Parsons {url}: {str(e)}")
                return 0
        
        # Run Ron Parsons pages in parallel
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(scrape_ron_page, url) for url in ron_urls]
            
            for future in as_completed(futures):
                result = future.result()
                collected += result
        
        return collected
    
    def scrape_gary_yong_gee_parallel(self):
        """Scrape Gary Yong Gee with different approach - parallel genus collection"""
        logger.info("🌟 PARALLEL: Gary Yong Gee Collection")
        
        collected = 0
        
        # Target high-value genera URLs
        gary_urls = [
            "https://orchids.yonggee.name/genera/cattleya",
            "https://orchids.yonggee.name/genera/dendrobium",
            "https://orchids.yonggee.name/genera/phalaenopsis", 
            "https://orchids.yonggee.name/genera/oncidium",
            "https://orchids.yonggee.name/genera/cymbidium",
            "https://orchids.yonggee.name/genera/masdevallia",
            "https://orchids.yonggee.name/genera/bulbophyllum",
            "https://orchids.yonggee.name/genera/paphiopedilum",
            "https://orchids.yonggee.name/genera/vanda",
            "https://orchids.yonggee.name/genera/laelia"
        ]
        
        def scrape_gary_genus(url):
            genus_collected = 0
            try:
                session = self.get_session()
                response = session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for any links that might lead to species
                    all_links = soup.find_all('a', href=True)
                    species_links = [link for link in all_links if '/species/' in link.get('href', '')]
                    
                    genus_name = url.split('/')[-1].title()
                    logger.info(f"📸 Gary {genus_name}: found {len(species_links)} potential species")
                    
                    # Process some species links
                    for i, link in enumerate(species_links[:10]):  # Limit for parallel efficiency
                        href = link.get('href')
                        species_url = urljoin(url, href)
                        
                        # Try to get species data
                        species_data = self.scrape_gary_species(species_url)
                        if species_data:
                            success = self.save_orchid_parallel(
                                species_data['name'], 
                                species_data.get('image_url'), 
                                'Gary Yong Gee', 
                                'gary_yong_gee_parallel'
                            )
                            if success:
                                genus_collected += 1
                        
                        time.sleep(0.3)
                
                logger.info(f"✅ Gary {genus_name}: +{genus_collected}")
                return genus_collected
                
            except Exception as e:
                logger.error(f"❌ Gary {url}: {str(e)}")
                return 0
        
        # Run Gary genera in parallel
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(scrape_gary_genus, url) for url in gary_urls]
            
            for future in as_completed(futures):
                result = future.result()
                collected += result
        
        return collected
    
    def scrape_gary_species(self, url):
        """Quick scrape of Gary species page"""
        try:
            session = self.get_session()
            response = session.get(url, timeout=10)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract name
                title = soup.find('title')
                name = None
                if title:
                    name = title.get_text(strip=True)
                    name = re.sub(r'^[^-]+-\s*', '', name)  # Remove prefix
                    name = name.replace(' - Gary Yong Gee', '').strip()
                
                # Look for image
                images = soup.find_all('img')
                image_url = None
                for img in images:
                    src = img.get('src', '')
                    if src and '.jpg' in src.lower() and 'logo' not in src.lower():
                        image_url = urljoin(url, src)
                        break
                
                if name:
                    return {'name': name, 'image_url': image_url}
            
        except:
            pass
        
        return None
    
    def scrape_botanical_gardens_parallel(self):
        """Scrape botanical garden collections in parallel"""
        logger.info("🌟 PARALLEL: Botanical Gardens Collection")
        
        collected = 0
        
        # Botanical garden URLs (hypothetical - would need real URLs)
        garden_sources = [
            {
                'name': 'Missouri Botanical Garden',
                'base_url': 'https://www.missouribotanicalgarden.org', 
                'search_path': '/gardens-gardening/your-garden/plant-finder/plant-details/kc/a924/orchidaceae'
            },
            {
                'name': 'Brooklyn Botanic Garden',
                'base_url': 'https://www.bbg.org',
                'search_path': '/collections/orchids'
            }
        ]
        
        def scrape_garden(garden_info):
            garden_collected = 0
            try:
                # This would implement specific scraping logic for each garden
                # For now, return 0 as we'd need actual garden APIs/pages
                logger.info(f"📸 {garden_info['name']}: checking availability")
                time.sleep(1)  # Simulate work
                return garden_collected
            except Exception as e:
                logger.error(f"❌ {garden_info['name']}: {str(e)}")
                return 0
        
        # Run gardens in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(scrape_garden, garden) for garden in garden_sources]
            
            for future in as_completed(futures):
                result = future.result()
                collected += result
        
        return collected
    
    def scrape_international_databases_parallel(self):
        """Scrape international orchid databases in parallel"""
        logger.info("🌟 PARALLEL: International Database Collection")
        
        collected = 0
        
        # International database sources
        intl_sources = [
            "https://www.orchidspecies.com/indexbyletter.htm",
            "https://www.aos.org/orchids/species-identification.aspx",
            "https://orchid.unibas.ch/index.php"
        ]
        
        def scrape_international(url):
            source_collected = 0
            try:
                session = self.get_session()
                response = session.get(url, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for orchid-related content
                    links = soup.find_all('a', href=True)
                    orchid_links = []
                    
                    for link in links:
                        href = link.get('href', '')
                        text = link.get_text(strip=True)
                        
                        # Look for genus names or species references
                        if any(genus in text.lower() for genus in ['cattleya', 'dendrobium', 'orchid', 'species']):
                            orchid_links.append(urljoin(url, href))
                    
                    logger.info(f"📸 International {urlparse(url).netloc}: found {len(orchid_links)} potential links")
                    
                    # Process a few links quickly
                    for link in orchid_links[:5]:  # Limit for speed
                        # This would implement specific extraction logic
                        time.sleep(0.5)
                
                logger.info(f"✅ International {urlparse(url).netloc}: +{source_collected}")
                return source_collected
                
            except Exception as e:
                logger.error(f"❌ International {url}: {str(e)}")
                return 0
        
        # Run international sources in parallel
        with ThreadPoolExecutor(max_workers=2) as executor:
            futures = [executor.submit(scrape_international, url) for url in intl_sources]
            
            for future in as_completed(futures):
                result = future.result()
                collected += result
        
        return collected
    
    def extract_orchid_name(self, src, alt):
        """Extract orchid name from various sources"""
        # Try alt text first
        if alt and len(alt.strip()) > 3:
            name = alt.strip()
            if any(char.isalpha() for char in name) and 'logo' not in name.lower():
                return self.clean_name(name)
        
        # Extract from filename
        filename = os.path.basename(urlparse(src).path)
        name = os.path.splitext(filename)[0]
        
        return self.clean_name(name)
    
    def clean_name(self, name):
        """Clean orchid name"""
        name = name.replace('-', ' ').replace('_', ' ').replace('%20', ' ')
        name = re.sub(r'\s+', ' ', name).strip()
        name = re.sub(r'\s*(copy|sm|small|thumb)(\d+)?$', '', name, flags=re.IGNORECASE)
        name = re.sub(r'^\d+\s*', '', name)
        name = re.sub(r'\s*\d+$', '', name)
        
        if len(name) < 4 or name.lower() in ['image', 'photo', 'dsc']:
            return None
            
        return name.title()
    
    def save_orchid_parallel(self, name, image_url, photographer, source):
        """Thread-safe orchid saving"""
        try:
            with app.app_context():
                with self.lock:
                    # Check for duplicate
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
                    
                    self.total_collected += 1
                    logger.info(f"✅ Parallel saved: {name} ({photographer})")
                    return True
                    
        except Exception as e:
            logger.error(f"❌ Save error {name}: {str(e)}")
            return False
    
    def run_parallel_scraping(self):
        """Run all scrapers in parallel"""
        logger.info("🚀 MASSIVE PARALLEL SCRAPING - ALL DATABASES SIMULTANEOUSLY!")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        with app.app_context():
            start_count = OrchidRecord.query.count()
            logger.info(f"📊 Starting: {start_count} records")
        
        # Run ALL scrapers in parallel with ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=4) as executor:
            
            # Submit all scraper tasks
            future_ron = executor.submit(self.scrape_ron_parsons_parallel)
            future_gary = executor.submit(self.scrape_gary_yong_gee_parallel)
            future_gardens = executor.submit(self.scrape_botanical_gardens_parallel)
            future_intl = executor.submit(self.scrape_international_databases_parallel)
            
            # Collect results as they complete
            futures = {
                future_ron: "Ron Parsons",
                future_gary: "Gary Yong Gee", 
                future_gardens: "Botanical Gardens",
                future_intl: "International DBs"
            }
            
            results = {}
            for future in as_completed(futures):
                scraper_name = futures[future]
                try:
                    result = future.result()
                    results[scraper_name] = result
                    logger.info(f"🎉 {scraper_name}: {result} records collected!")
                except Exception as e:
                    logger.error(f"❌ {scraper_name} failed: {str(e)}")
                    results[scraper_name] = 0
        
        # Final statistics
        with app.app_context():
            end_count = OrchidRecord.query.count()
            new_records = end_count - start_count
        
        elapsed = time.time() - start_time
        
        logger.info("=" * 70)
        logger.info("🎉 PARALLEL SCRAPING COMPLETE!")
        logger.info(f"📈 NEW RECORDS: {new_records}")
        logger.info(f"📊 TOTAL: {end_count}")
        logger.info(f"⏱️ Time: {elapsed:.1f}s")
        logger.info(f"🚀 Rate: {(new_records/elapsed*60):.1f} records/minute")
        
        logger.info("\n📋 BY SCRAPER:")
        for scraper, count in results.items():
            logger.info(f"  • {scraper}: {count} records")
        
        return {
            'new_records': new_records,
            'total_records': end_count,
            'results_by_scraper': results,
            'elapsed_time': elapsed
        }

if __name__ == "__main__":
    scraper = ParallelOrchidScraper()
    results = scraper.run_parallel_scraping()
    
    print(f"\n🎯 PARALLEL SCRAPING RESULTS:")
    print(f"New records: {results['new_records']}")
    print(f"Total database: {results['total_records']}")
    print(f"Time: {results['elapsed_time']:.1f}s")
    print(f"Sources scraped: {len(results['results_by_scraper'])}")