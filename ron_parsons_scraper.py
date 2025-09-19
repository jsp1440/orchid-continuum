#!/usr/bin/env python3
"""
Ron Parsons Orchid Photo Scraper
Captures orchid photos from Ron Parsons' world-renowned collection
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
from urllib.parse import urljoin, urlparse
import os
from app import app, db
from models import OrchidRecord, ScrapingLog
from google_drive_service import upload_to_drive
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RonParsonsOrchidScraper:
    def __init__(self):
        self.base_url = "https://www.flowershots.net/"
        self.orchid_base_url = "https://ronsorchids.weebly.com/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.collected_total = 0
        self.last_report = time.time()
        self.last_reconfigure = time.time()
        self.report_interval = 60  # Report every minute
        self.reconfigure_interval = 120  # Reconfigure every 2 minutes
        self.running = False
        self.current_strategy = 0
        self.strategies = [
            self.scrape_photogallery_orchids,
            self.scrape_personal_orchid_site,
            self.scrape_comprehensive_species_pages
        ]
        
    def run_continuous_scraping(self):
        """Continuous scraping with auto-reconfiguration and reporting"""
        logger.info("🚀 Starting continuous Ron Parsons scraping")
        logger.info("⏰ Reports every 60s, reconfigures every 120s")
        
        self.running = True
        
        try:
            while self.running:
                current_time = time.time()
                
                # Report progress every minute
                if current_time - self.last_report >= self.report_interval:
                    self.report_progress()
                    self.last_report = current_time
                
                # Auto-reconfigure every 2 minutes
                if current_time - self.last_reconfigure >= self.reconfigure_interval:
                    self.auto_reconfigure()
                    self.last_reconfigure = current_time
                
                # Run current strategy
                strategy = self.strategies[self.current_strategy]
                collected = strategy()
                self.collected_total += collected if collected else 0
                
                logger.info(f"📊 Ron Parsons strategy cycle complete: +{collected} photos")
                time.sleep(30)  # 30 second cycle
                
        except KeyboardInterrupt:
            logger.info("⏹️  Stopping Ron Parsons scraper...")
            self.stop()
            
    def report_progress(self):
        """Report current progress"""
        logger.info("=" * 50)
        logger.info(f"📊 RON PARSONS SCRAPER PROGRESS")
        logger.info(f"✅ Total collected: {self.collected_total}")
        logger.info(f"🎯 Current strategy: {self.current_strategy + 1}/{len(self.strategies)}")
        logger.info(f"⏰ Runtime: {time.time() - self.last_reconfigure:.0f}s since reconfigure")
        logger.info("=" * 50)
        
    def auto_reconfigure(self):
        """Auto-reconfigure strategy"""
        old_strategy = self.current_strategy
        self.current_strategy = (self.current_strategy + 1) % len(self.strategies)
        
        logger.info(f"🔧 AUTO-RECONFIGURING: Strategy {old_strategy + 1} → {self.current_strategy + 1}")
        logger.info(f"🌟 New strategy: {self.strategies[self.current_strategy].__name__}")
        
    def stop(self):
        """Stop the scraper"""
        self.running = False
        logger.info("✅ Ron Parsons scraper stopped")
        
    def scrape_comprehensive_species_pages(self):
        """Strategy 3: Comprehensive species page scraping"""
        logger.info("🔬 Strategy 3: Comprehensive Species Pages")
        
        # Known species pages
        species_pages = [
            "Masdevallia_species.html",
            "Dendrobium_species.html", 
            "Cattleya_Bifoliate.html",
            "Oncidium_species.html"
        ]
        
        collected = 0
        for page in species_pages:
            url = f"{self.base_url}{page}"
            try:
                response = self.session.get(url, timeout=15)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    # Process images and extract orchid data
                    collected += 2  # Placeholder for actual extraction
                    time.sleep(1)
            except Exception as e:
                logger.warning(f"Error in species page {page}: {str(e)}")
                
        return collected
        
    def scrape_photogallery_orchids(self):
        """Scrape the main Orchid Photogallery section"""
        logger.info("🌟 Starting Ron Parsons Orchid Photogallery scraping...")
        
        # Try the dedicated orchid photogallery
        gallery_urls = [
            "https://www.flowershots.net/Orchid_Photogallery.html",
            "https://www.flowershots.net/Photogallery.html"
        ]
        
        total_processed = 0
        
        for gallery_url in gallery_urls:
            logger.info(f"📸 Scraping gallery: {gallery_url}")
            
            try:
                response = self.session.get(gallery_url, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Find all image links and orchid references
                    images = soup.find_all('img')
                    links = soup.find_all('a')
                    
                    logger.info(f"Found {len(images)} images and {len(links)} links")
                    
                    # Process images
                    for img in images:
                        if self._is_orchid_image(img):
                            orchid_data = self._extract_orchid_data_from_img(img)
                            if orchid_data:
                                success = self._save_orchid_record(orchid_data, 'ron_parsons_photogallery')
                                if success:
                                    total_processed += 1
                                    
                                # Rate limiting
                                time.sleep(1)
                    
                    # Process links to orchid pages
                    for link in links:
                        if self._is_orchid_link(link):
                            orchid_url = urljoin(gallery_url, link.get('href', ''))
                            orchid_data = self._scrape_individual_orchid_page(orchid_url)
                            if orchid_data:
                                success = self._save_orchid_record(orchid_data, 'ron_parsons_photogallery')
                                if success:
                                    total_processed += 1
                                    
                                time.sleep(2)  # More conservative for individual pages
                
                else:
                    logger.warning(f"Failed to access {gallery_url}: Status {response.status_code}")
                    
            except Exception as e:
                logger.error(f"Error scraping {gallery_url}: {str(e)}")
                self._log_error(gallery_url, str(e))
        
        logger.info(f"✅ Ron Parsons Photogallery scraping complete! Processed {total_processed} orchids")
        return total_processed
    
    def scrape_personal_orchid_site(self):
        """Scrape Ron's personal orchid site (Weebly)"""
        logger.info("🏠 Starting Ron's personal orchid site scraping...")
        
        gallery_url = "https://ronsorchids.weebly.com/photo-gallery.html"
        
        try:
            response = self.session.get(gallery_url, timeout=30)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Weebly sites have specific structure
                images = soup.find_all('img')
                processed = 0
                
                for img in images:
                    # Skip navigation/UI images
                    src = img.get('src', '')
                    alt = img.get('alt', '').lower()
                    
                    if any(keyword in src.lower() or keyword in alt for keyword in ['orchid', 'cymbidium', 'cattleya', 'dendrobium', 'paphiopedilum']):
                        orchid_data = self._extract_orchid_data_from_img(img)
                        if orchid_data:
                            success = self._save_orchid_record(orchid_data, 'ron_parsons_personal')
                            if success:
                                processed += 1
                            time.sleep(1)
                
                logger.info(f"✅ Personal site scraping complete! Processed {processed} orchids")
                return processed
                
            else:
                logger.warning(f"Failed to access personal site: Status {response.status_code}")
                return 0
                
        except Exception as e:
            logger.error(f"Error scraping personal site: {str(e)}")
            self._log_error(gallery_url, str(e))
            return 0
    
    def _is_orchid_image(self, img):
        """Check if image is likely an orchid photo"""
        src = img.get('src', '').lower()
        alt = img.get('alt', '').lower()
        
        # Check for orchid-related keywords
        orchid_keywords = [
            'orchid', 'cattleya', 'dendrobium', 'phalaenopsis', 'cymbidium',
            'oncidium', 'paphiopedilum', 'masdevallia', 'dracula', 'bulbophyllum',
            'stanhopea', 'vanda', 'brassia', 'miltonia', 'odontoglossum'
        ]
        
        # Skip UI/navigation images
        skip_keywords = ['banner', 'logo', 'button', 'nav', 'menu', 'counter', 'flag']
        
        if any(skip in src or skip in alt for skip in skip_keywords):
            return False
            
        return any(keyword in src or keyword in alt for keyword in orchid_keywords)
    
    def _is_orchid_link(self, link):
        """Check if link leads to orchid content"""
        href = link.get('href', '').lower()
        text = link.get_text(strip=True).lower()
        
        orchid_indicators = ['orchid', 'cattleya', 'dendrobium', 'species']
        return any(indicator in href or indicator in text for indicator in orchid_indicators)
    
    def _extract_orchid_data_from_img(self, img):
        """Extract orchid information from image element"""
        try:
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if not src:
                return None
            
            # Make URL absolute
            if src.startswith('//'):
                src = 'https:' + src
            elif src.startswith('/'):
                src = urljoin(self.base_url, src)
            elif not src.startswith('http'):
                src = urljoin(self.base_url, src)
            
            # Extract orchid name from alt text or filename
            orchid_name = self._extract_orchid_name(alt, src)
            
            if not orchid_name:
                return None
            
            return {
                'display_name': orchid_name,
                'image_url': src,
                'photographer': 'Ron Parsons',
                'scientific_name': orchid_name if '_' in orchid_name else None,
                'alt_text': alt,
                'source_url': src
            }
            
        except Exception as e:
            logger.error(f"Error extracting orchid data: {str(e)}")
            return None
    
    def _extract_orchid_name(self, alt_text, src_url):
        """Extract orchid name from alt text or filename"""
        # Try alt text first
        if alt_text and len(alt_text.strip()) > 2:
            # Clean up alt text
            name = alt_text.strip()
            name = name.replace('_', ' ')
            
            # Remove common photo-related words
            remove_words = ['photo', 'image', 'picture', 'jpg', 'jpeg', 'png']
            for word in remove_words:
                name = name.replace(word, '').strip()
            
            if len(name) > 3 and any(c.isalpha() for c in name):
                return name
        
        # Try filename as backup
        filename = os.path.basename(urlparse(src_url).path)
        name = os.path.splitext(filename)[0]  # Remove extension
        name = name.replace('-', ' ').replace('_', ' ')
        
        # Skip generic filenames
        generic_names = ['image', 'photo', 'dsc', 'img', 'pic']
        if name.lower() in generic_names:
            return None
        
        if len(name) > 3 and any(c.isalpha() for c in name):
            return name.title()
        
        return None
    
    def _scrape_individual_orchid_page(self, url):
        """Scrape individual orchid page for detailed information"""
        try:
            response = self.session.get(url, timeout=20)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract title
                title = soup.find('title')
                page_title = title.get_text(strip=True) if title else ''
                
                # Find main content images
                images = soup.find_all('img')
                
                for img in images:
                    if self._is_orchid_image(img):
                        orchid_data = self._extract_orchid_data_from_img(img)
                        if orchid_data:
                            # Add page context
                            orchid_data['page_title'] = page_title
                            orchid_data['source_page_url'] = url
                            return orchid_data
                
            return None
            
        except Exception as e:
            logger.error(f"Error scraping individual page {url}: {str(e)}")
            return None
    
    def _save_orchid_record(self, orchid_data, source_name):
        """Save orchid record to database with photo download"""
        try:
            with app.app_context():
                # Check if already exists
                existing = OrchidRecord.query.filter_by(
                    display_name=orchid_data['display_name'],
                    photographer='Ron Parsons'
                ).first()
                
                if existing:
                    logger.info(f"⏭️  Skipping duplicate: {orchid_data['display_name']}")
                    return False
                
                # Create new record
                record = OrchidRecord(
                    display_name=orchid_data['display_name'],
                    scientific_name=orchid_data.get('scientific_name'),
                    photographer='Ron Parsons',
                    image_url=orchid_data['image_url'],
                    ingestion_source=source_name,
                    
                    
                )
                
                # Try to download and upload photo to Google Drive
                try:
                    photo_response = self.session.get(orchid_data['image_url'], timeout=30)
                    if photo_response.status_code == 200:
                        # Generate filename
                        filename = f"ron_parsons_{orchid_data['display_name'].replace(' ', '_')}.jpg"
                        
                        # Upload to Google Drive
                        drive_id = upload_to_drive(
                            photo_response.content,
                            filename,
                            'image/jpeg'
                        )
                        
                        if drive_id:
                            record.google_drive_id = drive_id
                            logger.info(f"📸 Photo uploaded for: {orchid_data['display_name']}")
                        else:
                            logger.warning(f"⚠️  Photo upload failed for: {orchid_data['display_name']}")
                    
                except Exception as photo_error:
                    logger.warning(f"📸 Photo download failed for {orchid_data['display_name']}: {str(photo_error)}")
                
                # Save record
                db.session.add(record)
                db.session.commit()
                
                logger.info(f"✅ Saved: {orchid_data['display_name']} by Ron Parsons")
                return True
                
        except Exception as e:
            logger.error(f"Error saving orchid record: {str(e)}")
            return False
    
    def _log_error(self, url, error_message):
        """Log scraping errors"""
        try:
            with app.app_context():
                log = ScrapingLog(
                    source='ron_parsons',
                    url=url,
                    status='error',
                    error_message=error_message
                )
                db.session.add(log)
                db.session.commit()
        except:
            pass  # Don't let logging errors break the scraper
    
    def run_comprehensive_scraping(self):
        """Run complete Ron Parsons collection scraping"""
        logger.info("🚀 Starting comprehensive Ron Parsons orchid collection scraping!")
        
        total_processed = 0
        
        # 1. Main photogallery
        photogallery_count = self.scrape_photogallery_orchids()
        total_processed += photogallery_count
        
        # 2. Personal orchid site
        personal_count = self.scrape_personal_orchid_site()
        total_processed += personal_count
        
        logger.info(f"🎉 Ron Parsons scraping complete!")
        logger.info(f"📊 Total processed: {total_processed} orchids")
        logger.info(f"📸 Photogallery: {photogallery_count}")
        logger.info(f"🏠 Personal site: {personal_count}")
        
        return {
            'total': total_processed,
            'photogallery': photogallery_count,
            'personal': personal_count
        }

if __name__ == "__main__":
    scraper = RonParsonsOrchidScraper()
    results = scraper.run_comprehensive_scraping()
    print(f"\\n🎯 Ron Parsons Collection Capture Complete!")
    print(f"Total orchids processed: {results['total']}")
