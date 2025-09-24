#!/usr/bin/env python3
"""
SVO Hybrid Orchid Collector with Breeding Descriptions
======================================================
Specialized scraper for Sunset Valley Orchids hybrid images with breeding descriptions
Focuses on capturing parentage, breeding notes, and detailed hybrid information for AI analysis
"""

import requests
from bs4 import BeautifulSoup
import os
import json
import time
import logging
import re
from urllib.parse import urljoin, urlparse
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SVOHybridCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Hybrid-Research)'
        })
        
        # SVO hybrid URLs - specific sections with breeding info
        self.hybrid_urls = [
            "https://www.svo.org/index.php?dir=hybrids&genus=Cattleya",
            "https://www.svo.org/index.php?dir=hybrids&genus=Dendrobium", 
            "https://www.svo.org/index.php?dir=hybrids&genus=Phalaenopsis",
            "https://www.svo.org/index.php?dir=hybrids&genus=Oncidium",
            "https://www.svo.org/index.php?dir=hybrids&genus=Vanda",
            "https://www.svo.org/index.php?dir=hybrids&genus=Paphiopedilum",
            "https://www.svo.org/index.php?dir=hybrids&genus=Cymbidium",
            "https://www.svo.org/index.php?dir=hybrids&genus=Miltonia",
            "https://www.svo.org/hybrids/",  # Main hybrid directory
            "https://www.svo.org/breeding/",  # Breeding section
            "https://www.svo.org/crosses/"   # Cross information
        ]
        
        # Initialize validation system
        self.validator = ScraperValidationSystem()
        self.collected_count = 0
        self.rejected_count = 0
        
        logger.info("🌺 SVO HYBRID COLLECTOR INITIALIZED WITH VALIDATION")
    
    def collect_all_hybrids(self):
        """Collect all hybrid orchids with breeding descriptions from SVO"""
        
        logger.info(f"🔍 Starting SVO hybrid collection from {len(self.hybrid_urls)} sources...")
        
        with app.app_context():
            for url in self.hybrid_urls:
                logger.info(f"📋 Processing hybrid source: {url}")
                
                try:
                    collected = self.scrape_hybrid_page(url)
                    logger.info(f"✅ Collected {collected} hybrids from {url}")
                    time.sleep(3)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {url}: {e}")
        
        logger.info(f"🎉 SVO HYBRID COLLECTION COMPLETE! Collected {self.collected_count} hybrids with breeding info")
    
    def scrape_hybrid_page(self, url):
        """Scrape hybrid orchids from a specific SVO page"""
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_collected = 0
            
            # Look for hybrid entries with various HTML structures
            hybrid_entries = self.find_hybrid_entries(soup)
            
            logger.info(f"   🔍 Found {len(hybrid_entries)} potential hybrid entries")
            
            for entry in hybrid_entries:
                created = self.process_hybrid_entry(entry, url)
                if created:
                    page_collected += 1
                    self.collected_count += 1
                    
                    # Commit every 5 records
                    if page_collected % 5 == 0:
                        db.session.commit()
                        logger.info(f"   ✅ Committed batch of 5 hybrid records")
            
            # Final commit for this page
            db.session.commit()
            return page_collected
            
        except Exception as e:
            logger.error(f"❌ Error scraping {url}: {e}")
            return 0
    
    def find_hybrid_entries(self, soup):
        """Find hybrid entries with multiple strategies"""
        
        entries = []
        
        # Strategy 1: Look for images with nearby text containing breeding info
        images = soup.find_all('img')
        for img in images:
            if self.is_orchid_image(img):
                entry = self.build_entry_from_image(img)
                if entry:
                    entries.append(entry)
        
        # Strategy 2: Look for table rows with hybrid data
        rows = soup.find_all('tr')
        for row in rows:
            if self.contains_hybrid_info(row):
                entry = self.build_entry_from_row(row)
                if entry:
                    entries.append(entry)
        
        # Strategy 3: Look for div containers with hybrid descriptions
        divs = soup.find_all('div')
        for div in divs:
            if self.contains_breeding_description(div):
                entry = self.build_entry_from_div(div)
                if entry:
                    entries.append(entry)
        
        # Strategy 4: Look for links to individual hybrid pages
        links = soup.find_all('a')
        for link in links:
            if self.is_hybrid_link(link):
                entry = self.build_entry_from_link(link)
                if entry:
                    entries.append(entry)
        
        return entries
    
    def is_orchid_image(self, img):
        """Check if image is likely an orchid photo"""
        src = img.get('src', '')
        alt = img.get('alt', '')
        
        # Skip icons, logos, navigation images
        if any(skip in src.lower() for skip in ['icon', 'logo', 'nav', 'button', 'bullet']):
            return False
        
        # Look for image file extensions
        if any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
            return True
        
        # Check alt text for orchid indicators
        if any(word in alt.lower() for word in ['orchid', 'hybrid', 'cross', 'breeding']):
            return True
        
        return False
    
    def contains_hybrid_info(self, element):
        """Check if element contains hybrid/breeding information"""
        text = element.get_text().lower()
        
        # Look for breeding indicators
        breeding_indicators = [
            'hybrid', 'cross', 'breeding', 'parentage', 'pod parent', 'pollen parent',
            '×', 'x ', 'grex', 'registration', 'rhs', 'awarded', 'clone'
        ]
        
        return any(indicator in text for indicator in breeding_indicators)
    
    def contains_breeding_description(self, element):
        """Check if element contains detailed breeding description"""
        text = element.get_text().lower()
        
        # Look for detailed breeding descriptions
        if len(text) < 50:  # Too short to be a description
            return False
        
        description_indicators = [
            'bred by', 'registered by', 'awarded', 'flower', 'bloom', 'petals',
            'fragrant', 'color', 'size', 'culture', 'growing', 'temperature'
        ]
        
        return any(indicator in text for indicator in description_indicators)
    
    def is_hybrid_link(self, link):
        """Check if link leads to hybrid information"""
        href = link.get('href', '')
        text = link.get_text().lower()
        
        # Check for hybrid-related URLs
        if any(word in href.lower() for word in ['hybrid', 'cross', 'breeding']):
            return True
        
        # Check for hybrid names in link text
        if any(word in text for word in ['hybrid', '×', 'grex']):
            return True
        
        return False
    
    def build_entry_from_image(self, img):
        """Build hybrid entry from image and surrounding content"""
        
        try:
            # Get image details
            img_src = img.get('src', '')
            img_alt = img.get('alt', '')
            
            # Find surrounding content for breeding info
            parent = img.parent
            context_text = ""
            
            # Look in parent and sibling elements for breeding descriptions
            if parent:
                context_text = parent.get_text()
                
                # Also check siblings
                for sibling in parent.find_next_siblings():
                    sibling_text = sibling.get_text()
                    if len(sibling_text) > 20:
                        context_text += " " + sibling_text
                        break
            
            return {
                'type': 'image',
                'image_url': img_src,
                'alt_text': img_alt,
                'breeding_description': context_text,
                'element': img
            }
            
        except Exception as e:
            logger.error(f"❌ Error building entry from image: {e}")
            return None
    
    def build_entry_from_row(self, row):
        """Build hybrid entry from table row"""
        
        try:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 2:
                return None
            
            # Extract data from cells
            name = cells[0].get_text().strip()
            description = ' '.join(cell.get_text().strip() for cell in cells[1:])
            
            # Look for images in the row
            img = row.find('img')
            img_url = img.get('src', '') if img else ''
            
            return {
                'type': 'row',
                'name': name,
                'breeding_description': description,
                'image_url': img_url,
                'element': row
            }
            
        except Exception as e:
            logger.error(f"❌ Error building entry from row: {e}")
            return None
    
    def build_entry_from_div(self, div):
        """Build hybrid entry from div with breeding description"""
        
        try:
            text = div.get_text().strip()
            
            # Look for images in the div
            img = div.find('img')
            img_url = img.get('src', '') if img else ''
            
            # Extract potential name from first line or header
            lines = text.split('\n')
            name = lines[0].strip() if lines else 'Hybrid specimen'
            
            return {
                'type': 'div',
                'name': name,
                'breeding_description': text,
                'image_url': img_url,
                'element': div
            }
            
        except Exception as e:
            logger.error(f"❌ Error building entry from div: {e}")
            return None
    
    def build_entry_from_link(self, link):
        """Build hybrid entry from link to hybrid page"""
        
        try:
            href = link.get('href', '')
            text = link.get_text().strip()
            
            # Follow the link to get more details
            if href.startswith('http'):
                full_url = href
            else:
                full_url = urljoin('https://www.svo.org/', href)
            
            return {
                'type': 'link',
                'name': text,
                'url': full_url,
                'breeding_description': f"Hybrid link: {text}",
                'element': link
            }
            
        except Exception as e:
            logger.error(f"❌ Error building entry from link: {e}")
            return None
    
    def process_hybrid_entry(self, entry, source_url):
        """Process a hybrid entry and create database record"""
        
        try:
            # Extract hybrid information
            name = entry.get('name', 'SVO Hybrid')
            breeding_description = entry.get('breeding_description', '')
            image_url = entry.get('image_url', '')
            
            # Parse genus from name
            genus = self.extract_genus(name)
            if not genus:
                return False
            
            # Clean and enhance breeding description
            enhanced_description = self.enhance_breeding_description(breeding_description, name)
            
            # Build full image URL if relative
            if image_url and not image_url.startswith('http'):
                image_url = urljoin(source_url, image_url)
            
            # Prepare record data for validation
            record_data = {
                'display_name': name,
                'scientific_name': name,
                'genus': genus,
                'species': '',
                'image_url': image_url,
                'ai_description': enhanced_description,
                'ingestion_source': 'svo_hybrid_validated',
                'image_source': 'Sunset Valley Orchids - Hybrid Collection',
                'data_source': source_url,
                'is_hybrid': True
            }
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "svo_hybrid_collector")
            
            if validated_data:
                try:
                    orchid_record = OrchidRecord()
                    orchid_record.display_name = validated_data['display_name']
                    orchid_record.scientific_name = validated_data['scientific_name']
                    orchid_record.genus = validated_data['genus']
                    orchid_record.species = validated_data.get('species', '')
                    orchid_record.image_url = validated_data.get('image_url', '')
                    orchid_record.ai_description = validated_data['ai_description']
                    orchid_record.ingestion_source = validated_data['ingestion_source']
                    orchid_record.image_source = validated_data['image_source']
                    orchid_record.data_source = validated_data['data_source']
                    orchid_record.is_hybrid = True
                    orchid_record.created_at = datetime.utcnow()
                    orchid_record.updated_at = datetime.utcnow()
                    
                    db.session.add(orchid_record)
                    
                    logger.debug(f"   ✅ Created SVO hybrid: {name[:50]}...")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Database error for {name}: {e}")
                    db.session.rollback()
                    return False
            else:
                logger.debug(f"❌ Validation failed for {name} (genus: {genus})")
                self.rejected_count += 1
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing hybrid entry: {e}")
            return False
    
    def extract_genus(self, name):
        """Extract genus from hybrid name"""
        if not name:
            return None
        
        # Split name and take first word as potential genus
        parts = name.split()
        if parts:
            genus = parts[0].strip()
            # Remove any non-alphabetic characters
            genus = re.sub(r'[^a-zA-Z]', '', genus)
            return genus.capitalize() if genus else None
        
        return None
    
    def enhance_breeding_description(self, description, name):
        """Enhance breeding description for AI analysis"""
        
        enhanced = f"SVO Hybrid: {name}. "
        
        if description and len(description.strip()) > 10:
            # Clean up the description
            cleaned = description.strip()
            
            # Add breeding indicators if missing
            if not any(word in cleaned.lower() for word in ['hybrid', 'cross', 'breeding']):
                enhanced += "Hybrid orchid with breeding information: "
            
            enhanced += cleaned
        else:
            enhanced += "Hybrid orchid specimen from Sunset Valley Orchids collection."
        
        # Add AI analysis tags
        enhanced += " [HYBRID] [BREEDING] [SVO]"
        
        return enhanced[:1000]  # Limit length

if __name__ == "__main__":
    collector = SVOHybridCollector()
    collector.collect_all_hybrids()
    
    print(f"\n🌺 SVO HYBRID COLLECTION COMPLETE!")
    print(f"✅ Collected: {collector.collected_count} hybrid orchids with breeding descriptions")
    print(f"❌ Rejected: {collector.rejected_count} invalid records")
    print(f"📈 Success rate: {(collector.collected_count / (collector.collected_count + collector.rejected_count) * 100):.1f}%" if (collector.collected_count + collector.rejected_count) > 0 else "N/A")