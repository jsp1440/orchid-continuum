"""
Ron Parsons Orchid Photography Scraper
Accesses Ron Parsons' 118,952+ orchid photos from Flickr and other sources
One of the world's largest individual orchid photography collections
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from typing import Dict, List, Optional

from models import OrchidRecord, db
from filename_parser import extract_metadata_from_image, parse_orchid_filename

class RonParsonsOrchidScraper:
    """Scraper for Ron Parsons' extensive orchid photography collection"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Orchid Database Research) Botanical Education'
        })
        
        # Ron Parsons' main sources
        self.flickr_base = "https://www.flickr.com/photos/rpflowershots"
        self.website_base = "https://flowershots.net"
        
        print("🌸 Ron Parsons Orchid Scraper Initialized")
        print(f"📸 Target: 118,952+ photos from world's leading orchid photographer")
        print(f"🔗 Flickr: {self.flickr_base}")
        print(f"🌐 Website: {self.website_base}")
    
    def scrape_ron_parsons_comprehensive(self):
        """Comprehensive scraping of Ron Parsons' orchid photography"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        print("\n🔍 COMPREHENSIVE RON PARSONS SCRAPING")
        print("=" * 50)
        
        # Phase 1: Flickr Albums (Organized Collections)
        print("\n📚 Phase 1: Flickr Albums")
        flickr_results = self.scrape_flickr_albums()
        results['processed'] += flickr_results['processed']
        results['errors'] += flickr_results['errors']
        results['skipped'] += flickr_results['skipped']
        
        # Phase 2: Flickr Photostream (Recent Photos)
        print("\n📷 Phase 2: Flickr Photostream")
        photostream_results = self.scrape_flickr_photostream()
        results['processed'] += photostream_results['processed']
        results['errors'] += photostream_results['errors']
        results['skipped'] += photostream_results['skipped']
        
        # Phase 3: Website Gallery (if accessible)
        print("\n🌐 Phase 3: Website Gallery")
        website_results = self.scrape_website_gallery()
        results['processed'] += website_results['processed']
        results['errors'] += website_results['errors']
        results['skipped'] += website_results['skipped']
        
        return results
    
    def scrape_flickr_albums(self):
        """Scrape Ron Parsons' Flickr albums for organized orchid collections"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Get albums list
            albums_url = f"{self.flickr_base}/albums"
            response = self.session.get(albums_url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ Failed to access albums: {response.status_code}")
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find album links
            album_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/albums/' in href and href not in album_links:
                    if href.startswith('/'):
                        full_url = f"https://www.flickr.com{href}"
                    else:
                        full_url = href
                    album_links.append(full_url)
            
            print(f"   Found {len(album_links)} albums")
            
            # Process ALL albums - FULL PRODUCTION MODE
            for i, album_url in enumerate(album_links):  # Process ALL albums - no limits!
                print(f"   📖 Processing album {i+1}/{len(album_links)}...")
                
                album_results = self.scrape_flickr_album(album_url)
                results['processed'] += album_results['processed']
                results['errors'] += album_results['errors']
                results['skipped'] += album_results['skipped']
                
                time.sleep(2)  # Respectful delay
        
        except Exception as e:
            print(f"   ❌ Error scraping albums: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_flickr_album(self, album_url):
        """Scrape individual Flickr album for orchid photos"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            response = self.session.get(album_url, timeout=15)
            if response.status_code != 200:
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract album title for context
            album_title = ""
            title_elem = soup.find('h1')
            if title_elem:
                album_title = title_elem.get_text(strip=True)
            
            # Find photo links in album
            photo_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/photos/' in href and '/in/album-' in href:
                    if href.startswith('/'):
                        full_url = f"https://www.flickr.com{href}"
                    else:
                        full_url = href
                    photo_links.append(full_url)
            
            print(f"     Album: {album_title[:50]}... ({len(photo_links)} photos)")
            
            # Process ALL photos from album - FULL PRODUCTION MODE
            for photo_url in photo_links:  # Process ALL photos - no limits!
                photo_data = self.scrape_flickr_photo(photo_url, album_title)
                
                if photo_data and self.save_ron_parsons_orchid(photo_data):
                    results['processed'] += 1
                    time.sleep(1)  # Small delay between photos
                else:
                    results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error processing album: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_flickr_photostream(self):
        """Scrape Ron Parsons' main Flickr photostream"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Access main photostream
            photostream_url = f"{self.flickr_base}/"
            response = self.session.get(photostream_url, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ Failed to access photostream: {response.status_code}")
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find recent photo links
            photo_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if '/photos/rpflowershots/' in href and href not in photo_links:
                    if href.startswith('/'):
                        full_url = f"https://www.flickr.com{href}"
                    else:
                        full_url = href
                    photo_links.append(full_url)
            
            print(f"   Found {len(photo_links)} recent photos")
            
            # Process ALL recent photos - FULL PRODUCTION MODE
            for photo_url in photo_links:  # Process ALL photos - no limits!
                photo_data = self.scrape_flickr_photo(photo_url, "Photostream")
                
                if photo_data and self.save_ron_parsons_orchid(photo_data):
                    results['processed'] += 1
                    time.sleep(1)  # Small delay between photos
                else:
                    results['skipped'] += 1
        
        except Exception as e:
            print(f"   ❌ Error scraping photostream: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_flickr_photo(self, photo_url, context=""):
        """Extract detailed information from individual Flickr photo"""
        try:
            response = self.session.get(photo_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract photo title
            title = ""
            title_elem = soup.find('h1', class_='photo-title')
            if not title_elem:
                title_elem = soup.find('h1')
            if title_elem:
                title = title_elem.get_text(strip=True)
            
            # Extract description
            description = ""
            desc_elem = soup.find('div', class_='photo-description')
            if desc_elem:
                description = desc_elem.get_text(strip=True)
            
            # Extract tags
            tags = []
            for tag_elem in soup.find_all('a', class_='tag'):
                tags.append(tag_elem.get_text(strip=True))
            
            # Find high-resolution image URL
            image_url = ""
            img_elem = soup.find('img', {'src': True})
            if img_elem:
                src = img_elem.get('src', '')
                # Try to get larger version
                if '_m.jpg' in src:
                    image_url = src.replace('_m.jpg', '_b.jpg')  # Large version
                elif '_c.jpg' in src:
                    image_url = src.replace('_c.jpg', '_b.jpg')  # Large version
                else:
                    image_url = src
            
            # Parse orchid name from title using filename parser
            orchid_name_data = parse_orchid_filename(title)
            
            # Also try to extract from description and tags
            combined_text = f"{title} {description} {' '.join(tags)}"
            
            return {
                'title': title,
                'description': description,
                'tags': tags,
                'image_url': image_url,
                'source_url': photo_url,
                'context': context,
                'orchid_analysis': orchid_name_data,
                'combined_text': combined_text,
                'photographer': 'Ron Parsons'
            }
            
        except Exception as e:
            print(f"     ❌ Error scraping photo {photo_url}: {e}")
            return None
    
    def scrape_website_gallery(self):
        """Scrape Ron Parsons' website gallery (if accessible)"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            response = self.session.get(self.website_base, timeout=15)
            
            if response.status_code != 200:
                print(f"   ❌ Website not accessible: {response.status_code}")
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for gallery or photo links
            gallery_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                link_text = link.get_text(strip=True).lower()
                
                if any(keyword in link_text for keyword in ['gallery', 'photos', 'orchids', 'images']):
                    full_url = urljoin(self.website_base, href)
                    gallery_links.append(full_url)
            
            print(f"   Found {len(gallery_links)} potential gallery links")
            
            # Process gallery links (if any found)
            for gallery_url in gallery_links[:3]:  # Limit for testing
                gallery_results = self.scrape_website_gallery_page(gallery_url)
                results['processed'] += gallery_results['processed']
                results['errors'] += gallery_results['errors']
                results['skipped'] += gallery_results['skipped']
        
        except Exception as e:
            print(f"   ❌ Error scraping website: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_website_gallery_page(self, gallery_url):
        """Scrape individual gallery page from website"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            response = self.session.get(gallery_url, timeout=15)
            if response.status_code != 200:
                return results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find images
            for img in soup.find_all('img'):
                src = img.get('src', '')
                alt = img.get('alt', '')
                
                if src and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    full_img_url = urljoin(gallery_url, src)
                    
                    # Parse orchid information from alt text or filename
                    orchid_data = parse_orchid_filename(alt or src)
                    
                    photo_data = {
                        'title': alt,
                        'image_url': full_img_url,
                        'source_url': gallery_url,
                        'context': 'Website Gallery',
                        'orchid_analysis': orchid_data,
                        'photographer': 'Ron Parsons'
                    }
                    
                    if self.save_ron_parsons_orchid(photo_data):
                        results['processed'] += 1
                        time.sleep(1)
                    else:
                        results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error processing gallery page: {e}")
            results['errors'] += 1
        
        return results
    
    def save_ron_parsons_orchid(self, photo_data):
        """Save Ron Parsons orchid photo to database with proper attribution"""
        try:
            # Extract orchid name from analysis
            orchid_analysis = photo_data.get('orchid_analysis', {})
            genus = orchid_analysis.get('genus')
            species = orchid_analysis.get('species')
            
            # Create display name
            if genus and species:
                display_name = f"{genus} {species}"
            elif genus:
                display_name = genus
            else:
                # Try to extract from title
                title = photo_data.get('title', '')
                if title:
                    display_name = title[:50]  # Use first 50 chars of title
                else:
                    return False  # Skip if no identifiable orchid name
            
            # Check if already exists
            existing = OrchidRecord.query.filter_by(
                display_name=display_name,
                ingestion_source='ron_parsons_flickr'
            ).first()
            
            if existing:
                return False  # Skip duplicates
            
            # Create comprehensive cultural information
            cultural_info = f"Photo by Ron Parsons - World's Leading Orchid Photographer\\n"
            cultural_info += f"Collection: 118,952+ photos on Flickr + 100,000+ digital images\\n"
            cultural_info += f"Experience: 49 years growing orchids, worldwide documentation\\n\\n"
            
            if photo_data.get('description'):
                cultural_info += f"Description: {photo_data['description'][:200]}\\n\\n"
            
            if photo_data.get('tags'):
                cultural_info += f"Tags: {', '.join(photo_data['tags'][:5])}\\n\\n"
            
            cultural_info += f"Context: {photo_data.get('context', 'Unknown')}\\n"
            cultural_info += f"Confidence: {orchid_analysis.get('confidence', 0.0):.1f}\\n"
            cultural_info += f"Parsing Method: {orchid_analysis.get('parsing_method', 'unknown')}\\n\\n"
            
            cultural_info += f"© Ron Parsons - flowershots.net\\n"
            cultural_info += f"Source: {photo_data['source_url']}\\n"
            cultural_info += f"Author: One of America's most respected orchid photographers"
            
            orchid = OrchidRecord(
                display_name=display_name,
                scientific_name=orchid_analysis.get('full_name') or display_name,
                genus=genus,
                species=species,
                ingestion_source='ron_parsons_flickr',
                image_source=photo_data.get('image_url'),
                cultural_notes=cultural_info,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            db.session.add(orchid)
            return True
            
        except Exception as e:
            print(f"     ❌ Error saving Ron Parsons orchid: {e}")
            return False

def run_ron_parsons_scraper():
    """Run Ron Parsons scraper independently"""
    scraper = RonParsonsOrchidScraper()
    
    print("\\n🌸 RON PARSONS COMPREHENSIVE SCRAPING")
    print("Target: 118,952+ photos from world's leading orchid photographer")
    print("=" * 60)
    
    results = scraper.scrape_ron_parsons_comprehensive()
    
    try:
        db.session.commit()
        print(f"\\n✅ RON PARSONS RESULTS:")
        print(f"   Processed: {results['processed']}")
        print(f"   Errors: {results['errors']}")
        print(f"   Skipped: {results['skipped']}")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Database commit error: {e}")
    
    return results

if __name__ == "__main__":
    run_ron_parsons_scraper()