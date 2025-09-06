#!/usr/bin/env python3
"""
🌅 SUNSET VALLEY ORCHIDS SCRAPER
Specialized scraper for Sarcochilus hybrids from sunsetvalleyorchids.com
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import app, db
from models import OrchidRecord

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SunsetValleyOrchidsScraper:
    """Scraper for Sunset Valley Orchids - focusing on Sarcochilus hybrids"""
    
    def __init__(self):
        self.base_url = "https://sunsetvalleyorchids.com"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        
        # Track processed hybrids and intergeneric crosses
        self.processed_hybrids = set()
        self.processed_intergenerics = set()
        self.sarcochilus_hybrids = []
        self.intergeneric_crosses = []
        
        logger.info("🌅 Sunset Valley Orchids Enhanced Scraper initialized")
        
    def scrape_sarcochilus_hybrids(self):
        """Main method to scrape Sarcochilus hybrid data"""
        logger.info("🌺 Starting Sarcochilus hybrid collection from Sunset Valley Orchids")
        logger.info("=" * 70)
        
        try:
            # Test connection first
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code != 200:
                logger.error(f"❌ Failed to connect to {self.base_url}")
                return []
                
            logger.info(f"✅ Connected to {self.base_url}")
            
            # Search for Sarcochilus content
            sarcochilus_pages = self.find_sarcochilus_pages()
            
            for page_url in sarcochilus_pages:
                try:
                    hybrids = self.extract_hybrids_from_page(page_url)
                    self.sarcochilus_hybrids.extend(hybrids)
                    time.sleep(2)  # Be respectful to the server
                except Exception as e:
                    logger.error(f"❌ Error processing page {page_url}: {e}")
                    
            # Store collected hybrids
            self.store_hybrids_in_database()
            
            logger.info(f"✅ Successfully collected {len(self.sarcochilus_hybrids)} Sarcochilus hybrids")
            return self.sarcochilus_hybrids
            
        except Exception as e:
            logger.error(f"❌ Scraping failed: {e}")
            return []
            
    def find_sarcochilus_pages(self):
        """Find pages containing Sarcochilus hybrid information"""
        logger.info("🔍 Searching for Sarcochilus hybrid pages...")
        
        sarcochilus_pages = []
        
        # Common page patterns for orchid nurseries
        search_paths = [
            "/",
            "/plants",
            "/orchids", 
            "/hybrids",
            "/sarcochilus",
            "/australian-orchids",
            "/species",
            "/plants/sarcochilus",
            "/catalog",
            "/inventory"
        ]
        
        for path in search_paths:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for Sarcochilus mentions
                    if self.contains_sarcochilus_content(soup):
                        sarcochilus_pages.append(url)
                        logger.info(f"✅ Found Sarcochilus content: {url}")
                        
                    # Look for additional links to Sarcochilus pages
                    additional_links = self.find_sarcochilus_links(soup)
                    for link in additional_links:
                        full_url = urljoin(self.base_url, link)
                        if full_url not in sarcochilus_pages:
                            sarcochilus_pages.append(full_url)
                            
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not access {path}: {e}")
                
        logger.info(f"🔍 Found {len(sarcochilus_pages)} pages with Sarcochilus content")
        return sarcochilus_pages
        
    def contains_sarcochilus_content(self, soup):
        """Check if page contains Sarcochilus content"""
        text_content = soup.get_text().lower()
        
        sarcochilus_indicators = [
            'sarcochilus',
            'sarc.',
            'australian native orchid',
            'orange blossom orchid',
            'hybrid sarcochilus',
            'sarc hybrid'
        ]
        
        return any(indicator in text_content for indicator in sarcochilus_indicators)
        
    def find_sarcochilus_links(self, soup):
        """Find links that might lead to Sarcochilus content"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            link_text = link.get_text().lower()
            
            if any(term in href or term in link_text for term in ['sarcochilus', 'sarc', 'australian']):
                links.append(link['href'])
                
        return links
        
    def extract_hybrids_from_page(self, page_url):
        """Extract Sarcochilus hybrid data from a specific page"""
        logger.info(f"🌺 Extracting hybrids from: {page_url}")
        
        hybrids = []
        
        try:
            response = self.session.get(page_url, timeout=15)
            if response.status_code != 200:
                return hybrids
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for plant listings, product cards, or catalog entries
            hybrid_elements = self.find_hybrid_elements(soup)
            
            for element in hybrid_elements:
                hybrid_data = self.parse_hybrid_element(element, page_url)
                if hybrid_data and hybrid_data['name'] not in self.processed_hybrids:
                    hybrids.append(hybrid_data)
                    self.processed_hybrids.add(hybrid_data['name'])
                    
            logger.info(f"✅ Extracted {len(hybrids)} Sarcochilus hybrids from page")
            
        except Exception as e:
            logger.error(f"❌ Error extracting from {page_url}: {e}")
            
        return hybrids
        
    def find_hybrid_elements(self, soup):
        """Find HTML elements containing hybrid information"""
        elements = []
        
        # Common selectors for plant catalogs
        selectors = [
            '.product',
            '.plant',
            '.orchid',
            '.item',
            '.listing',
            '[class*="product"]',
            '[class*="plant"]',
            '[class*="orchid"]',
            'tr',  # Table rows
            'li',  # List items
            'div[class*="card"]',
            'div[class*="entry"]'
        ]
        
        for selector in selectors:
            found_elements = soup.select(selector)
            for element in found_elements:
                if self.element_contains_sarcochilus(element):
                    elements.append(element)
                    
        # Also look for text patterns
        text_elements = soup.find_all(text=re.compile(r'sarcochilus|sarc\.', re.IGNORECASE))
        for text_element in text_elements:
            parent = text_element.parent
            if parent and parent not in elements:
                elements.append(parent)
                
        return elements
        
    def element_contains_sarcochilus(self, element):
        """Check if an element contains Sarcochilus information"""
        text = element.get_text().lower()
        return 'sarcochilus' in text or 'sarc.' in text
        
    def parse_hybrid_element(self, element, source_url):
        """Parse individual hybrid data from an element"""
        try:
            text = element.get_text()
            
            # Extract hybrid name
            name = self.extract_hybrid_name(text)
            if not name:
                return None
                
            # Extract other information
            parentage = self.extract_parentage(text)
            description = self.extract_description(text, element)
            price = self.extract_price(text)
            availability = self.extract_availability(text)
            
            # Look for images
            image_url = self.extract_image_url(element)
            
            hybrid_data = {
                'name': name,
                'genus': 'Sarcochilus',
                'parentage': parentage,
                'description': description,
                'price': price,
                'availability': availability,
                'image_url': image_url,
                'source_url': source_url,
                'nursery': 'Sunset Valley Orchids',
                'extracted_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 Found Sarcochilus hybrid: {name}")
            return hybrid_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing hybrid element: {e}")
            return None
            
    def extract_hybrid_name(self, text):
        """Extract hybrid name from text"""
        # Look for Sarcochilus hybrid patterns
        patterns = [
            r"Sarcochilus\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"Sarc\.?\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+\s+[A-Z][a-z]+).*(?:sarcochilus|sarc\.?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                name = match.group(1).strip()
                # Clean up common issues
                name = re.sub(r'\s+', ' ', name)
                if len(name) > 3 and not name.lower() in ['hybrid', 'orchid', 'plant']:
                    return f"Sarcochilus {name}"
                    
        return None
        
    def extract_parentage(self, text):
        """Extract parentage information"""
        patterns = [
            r"\((.*?)\s*[×x]\s*(.*?)\)",
            r"([A-Z][a-z]+\s+[a-z]+)\s*[×x]\s*([A-Z][a-z]+\s+[a-z]+)",
            r"cross.*?between\s+(.*?)\s+and\s+(.*?)[\.\,\n]",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"{match.group(1)} × {match.group(2)}"
                
        return None
        
    def extract_description(self, text, element):
        """Extract description"""
        # Get surrounding text context
        sentences = re.split(r'[.!?]\s+', text)
        
        description_parts = []
        for sentence in sentences:
            if any(word in sentence.lower() for word in ['flower', 'bloom', 'fragrant', 'color', 'size', 'grow']):
                description_parts.append(sentence.strip())
                
        return '. '.join(description_parts[:3]) if description_parts else None
        
    def extract_price(self, text):
        """Extract price information"""
        price_patterns = [
            r'\$(\d+(?:\.\d{2})?)',
            r'(\d+(?:\.\d{2})?)\s*dollars?',
            r'price:?\s*\$?(\d+(?:\.\d{2})?)'
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return f"${match.group(1)}"
                
        return None
        
    def extract_availability(self, text):
        """Extract availability status"""
        if re.search(r'in\s+stock|available|ready', text, re.IGNORECASE):
            return "In Stock"
        elif re.search(r'out\s+of\s+stock|sold\s+out|unavailable', text, re.IGNORECASE):
            return "Out of Stock"
        elif re.search(r'pre.?order|coming\s+soon', text, re.IGNORECASE):
            return "Pre-order"
            
        return "Unknown"
        
    def extract_image_url(self, element):
        """Extract image URL if available"""
        img_tag = element.find('img')
        if img_tag and img_tag.get('src'):
            return urljoin(self.base_url, img_tag['src'])
            
        return None
        
    def store_hybrids_in_database(self):
        """Store collected hybrids in the database"""
        logger.info("💾 Storing Sarcochilus hybrids in database...")
        
        stored_count = 0
        
        try:
            with app.app_context():
                for hybrid in self.sarcochilus_hybrids:
                    try:
                        # Check if already exists
                        existing = OrchidRecord.query.filter_by(
                            display_name=hybrid['name'],
                            data_source='Sunset Valley Orchids'
                        ).first()
                        
                        if existing:
                            logger.info(f"⚠️ Hybrid already exists: {hybrid['name']}")
                            continue
                            
                        # Create new record
                        new_record = OrchidRecord(
                            genus='Sarcochilus',
                            species='hybrid',
                            display_name=hybrid['name'],
                            parentage_formula=hybrid.get('parentage'),
                            ai_description=hybrid.get('description'),
                            cultural_notes=f"Price: {hybrid.get('price', 'Unknown')} | Availability: {hybrid.get('availability', 'Unknown')}",
                            image_url=hybrid.get('image_url'),
                            data_source='Sunset Valley Orchids',
                            ingestion_source='sunset_valley_scraper',
                            validation_status='pending',
                            created_at=datetime.now()
                        )
                        
                        db.session.add(new_record)
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error storing hybrid {hybrid.get('name', 'Unknown')}: {e}")
                        
                db.session.commit()
                logger.info(f"✅ Successfully stored {stored_count} Sarcochilus hybrids")
                
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            
    def scrape_intergeneric_crosses(self):
        """Comprehensive scraper for intergeneric crosses with parent images"""
        logger.info("🌈 Starting intergeneric cross collection from Sunset Valley Orchids")
        logger.info("=" * 80)
        
        try:
            # Search for intergeneric cross pages
            intergeneric_pages = self.find_intergeneric_pages()
            
            for page_url in intergeneric_pages:
                try:
                    crosses = self.extract_intergeneric_data(page_url)
                    self.intergeneric_crosses.extend(crosses)
                    time.sleep(2)  # Be respectful
                except Exception as e:
                    logger.error(f"❌ Error processing page {page_url}: {e}")
                    
            # Store in database
            self.store_intergenerics_in_database()
            
            logger.info(f"✅ Successfully collected {len(self.intergeneric_crosses)} intergeneric crosses")
            return self.intergeneric_crosses
            
        except Exception as e:
            logger.error(f"❌ Intergeneric scraping failed: {e}")
            return []
            
    def find_intergeneric_pages(self):
        """Find pages containing intergeneric cross information"""
        logger.info("🔍 Searching for intergeneric cross pages...")
        
        pages = []
        
        # Search paths for intergeneric content
        search_paths = [
            "/htm/offerings_intergeneric.html",
            "/htm/offerings_intergenerics.html", 
            "/htm/hybrid_offerings.html",
            "/htm/breeding_archive.html",
            "/htm/crosses.html",
            "/htm/advanced_hybrids.html",
            "/",
            "/offerings",
            "/hybrids"
        ]
        
        for path in search_paths:
            try:
                url = urljoin(self.base_url, path)
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    if self.contains_intergeneric_content(soup):
                        pages.append(url)
                        logger.info(f"✅ Found intergeneric content: {url}")
                        
                    # Look for links to intergeneric pages
                    additional_links = self.find_intergeneric_links(soup)
                    for link in additional_links:
                        full_url = urljoin(self.base_url, link)
                        if full_url not in pages:
                            pages.append(full_url)
                            
                time.sleep(1)
                
            except Exception as e:
                logger.warning(f"⚠️ Could not access {path}: {e}")
                
        logger.info(f"🔍 Found {len(pages)} pages with intergeneric content")
        return pages
        
    def contains_intergeneric_content(self, soup):
        """Check if page contains intergeneric cross content"""
        text_content = soup.get_text().lower()
        
        intergeneric_indicators = [
            'intergeneric',
            'inter-generic',
            'brassavola',
            'cattleya',
            'laelia',
            'brassolaelia',
            'brassocattleya',
            'laeliocattleya',
            'brassolaeliocattleya',
            'blc',
            'rlc',
            'slc',
            'potinara',
            'sophronitis',
            'parent photos',
            'breeding archive',
            'cross between',
            'genera cross'
        ]
        
        return any(indicator in text_content for indicator in intergeneric_indicators)
        
    def find_intergeneric_links(self, soup):
        """Find links that might lead to intergeneric content"""
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            link_text = link.get_text().lower()
            
            if any(term in href or term in link_text for term in [
                'intergeneric', 'inter-generic', 'hybrid', 'cross', 'breeding',
                'blc', 'rlc', 'slc', 'potinara', 'brassavola', 'laelia'
            ]):
                links.append(link['href'])
                
        return links
        
    def extract_intergeneric_data(self, page_url):
        """Extract intergeneric cross data with parent images"""
        logger.info(f"🌈 Extracting intergeneric crosses from: {page_url}")
        
        crosses = []
        
        try:
            response = self.session.get(page_url, timeout=15)
            if response.status_code != 200:
                return crosses
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for cross listings
            cross_elements = self.find_intergeneric_elements(soup)
            
            for element in cross_elements:
                cross_data = self.parse_intergeneric_element(element, page_url)
                if cross_data and cross_data['cross_name'] not in self.processed_intergenerics:
                    crosses.append(cross_data)
                    self.processed_intergenerics.add(cross_data['cross_name'])
                    
            logger.info(f"✅ Extracted {len(crosses)} intergeneric crosses from page")
            
        except Exception as e:
            logger.error(f"❌ Error extracting from {page_url}: {e}")
            
        return crosses
        
    def find_intergeneric_elements(self, soup):
        """Find HTML elements containing intergeneric cross information"""
        elements = []
        
        # Look for various container types
        selectors = [
            'table tr',  # Table rows
            '.cross', '.hybrid', '.breeding',
            '[class*="cross"]', '[class*="hybrid"]', '[class*="breeding"]',
            'div.product', 'div.offering', 'div.plant',
            'p', 'div'  # Paragraphs and divs as fallback
        ]
        
        for selector in selectors:
            found_elements = soup.select(selector)
            for element in found_elements:
                if self.element_contains_intergeneric(element):
                    elements.append(element)
                    
        return elements
        
    def element_contains_intergeneric(self, element):
        """Check if element contains intergeneric cross information"""
        text = element.get_text().lower()
        return any(term in text for term in [
            'intergeneric', 'blc', 'rlc', 'slc', 'potinara',
            'brassavola', 'cattleya', 'laelia', 'sophronitis',
            'brassolaelia', 'brassocattleya', 'laeliocattleya'
        ])
        
    def parse_intergeneric_element(self, element, source_url):
        """Parse individual intergeneric cross data"""
        try:
            text = element.get_text()
            
            # Extract cross name and genera
            cross_name = self.extract_intergeneric_name(text)
            if not cross_name:
                return None
                
            # Extract parent information
            parents = self.extract_parent_data(text, element)
            parentage = self.extract_parentage(text)
            
            # Extract description and characteristics
            description = self.extract_description(text, element)
            
            # Extract pricing and availability
            price = self.extract_price(text)
            availability = self.extract_availability(text)
            
            # Look for parent images
            parent_images = self.extract_parent_images(element)
            
            # Determine genera involved
            genera_involved = self.identify_genera(cross_name, text)
            
            cross_data = {
                'cross_name': cross_name,
                'genera_involved': genera_involved,
                'parents': parents,
                'parentage': parentage,
                'description': description,
                'parent_images': parent_images,
                'price': price,
                'availability': availability,
                'source_url': source_url,
                'nursery': 'Sunset Valley Orchids',
                'extracted_at': datetime.now().isoformat()
            }
            
            logger.info(f"📋 Found intergeneric cross: {cross_name}")
            return cross_data
            
        except Exception as e:
            logger.error(f"❌ Error parsing intergeneric element: {e}")
            return None
            
    def extract_intergeneric_name(self, text):
        """Extract intergeneric cross name"""
        # Look for intergeneric name patterns
        patterns = [
            r"(Potinara\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(Brassolaeliocattleya\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(Brassocattleya\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(Laeliocattleya\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(Brassolaelia\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(BLC\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(RLC\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"(SLC\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
                
        return None
        
    def extract_parent_data(self, text, element):
        """Extract detailed parent orchid data"""
        parents = {}
        
        # Look for parent mentions
        parent_patterns = [
            r"pod parent:?\s*([A-Z][a-z]+\s+[a-z]+(?:\s+'[^']+')?))",
            r"pollen parent:?\s*([A-Z][a-z]+\s+[a-z]+(?:\s+'[^']+')?))",
            r"([A-Z][a-z]+\s+[a-z]+(?:\s+'[^']+')?)?\s*[×x]\s*([A-Z][a-z]+\s+[a-z]+(?:\s+'[^']+')?)"
        ]
        
        for pattern in parent_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                if 'pod parent' in pattern:
                    parents['pod_parent'] = match.group(1)
                elif 'pollen parent' in pattern:
                    parents['pollen_parent'] = match.group(1)
                else:
                    parents['parent1'] = match.group(1)
                    if match.group(2):
                        parents['parent2'] = match.group(2)
                        
        return parents
        
    def extract_parent_images(self, element):
        """Extract parent orchid images if available"""
        parent_images = []
        
        # Look for images in the element or nearby elements
        img_tags = element.find_all('img')
        
        for img in img_tags:
            if img.get('src'):
                img_url = urljoin(self.base_url, img['src'])
                alt_text = img.get('alt', '').lower()
                
                # Check if image might be a parent photo
                if any(term in alt_text for term in ['parent', 'pod', 'pollen', 'original']):
                    parent_images.append({
                        'url': img_url,
                        'alt_text': img.get('alt', ''),
                        'title': img.get('title', ''),
                        'type': 'parent_photo'
                    })
                    
        return parent_images
        
    def identify_genera(self, cross_name, text):
        """Identify genera involved in the cross"""
        genera = []
        
        # Check cross name for genus indicators
        if cross_name:
            name_lower = cross_name.lower()
            if 'potinara' in name_lower:
                genera = ['Brassavola', 'Cattleya', 'Laelia', 'Sophronitis']
            elif 'brassolaeliocattleya' in name_lower or 'blc' in name_lower:
                genera = ['Brassavola', 'Laelia', 'Cattleya']
            elif 'brassocattleya' in name_lower:
                genera = ['Brassavola', 'Cattleya']
            elif 'laeliocattleya' in name_lower:
                genera = ['Laelia', 'Cattleya']
            elif 'brassolaelia' in name_lower:
                genera = ['Brassavola', 'Laelia']
                
        # Also scan text for genus mentions
        text_genera = []
        for genus in ['Brassavola', 'Cattleya', 'Laelia', 'Sophronitis', 'Rhyncholaelia']:
            if genus.lower() in text.lower():
                text_genera.append(genus)
                
        return list(set(genera + text_genera))
        
    def store_intergenerics_in_database(self):
        """Store intergeneric crosses in database"""
        logger.info("💾 Storing intergeneric crosses in database...")
        
        stored_count = 0
        
        try:
            with app.app_context():
                for cross in self.intergeneric_crosses:
                    try:
                        # Check if already exists
                        existing = OrchidRecord.query.filter_by(
                            display_name=cross['cross_name'],
                            data_source='Sunset Valley Orchids'
                        ).first()
                        
                        if existing:
                            logger.info(f"⚠️ Cross already exists: {cross['cross_name']}")
                            continue
                            
                        # Create new record
                        new_record = OrchidRecord(
                            genus='Intergeneric',
                            species='hybrid',
                            display_name=cross['cross_name'],
                            parentage_formula=cross.get('parentage'),
                            ai_description=cross.get('description'),
                            cultural_notes=f"Genera: {', '.join(cross.get('genera_involved', []))} | Price: {cross.get('price', 'Unknown')} | Availability: {cross.get('availability', 'Unknown')}",
                            image_url=cross['parent_images'][0]['url'] if cross.get('parent_images') else None,
                            data_source='Sunset Valley Orchids',
                            ingestion_source='sunset_valley_intergeneric_scraper',
                            validation_status='pending',
                            created_at=datetime.now()
                        )
                        
                        db.session.add(new_record)
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error storing cross {cross.get('cross_name', 'Unknown')}: {e}")
                        
                db.session.commit()
                logger.info(f"✅ Successfully stored {stored_count} intergeneric crosses")
                
        except Exception as e:
            logger.error(f"❌ Database error: {e}")

    def get_summary(self):
        """Get summary of scraping results"""
        return {
            'total_hybrids': len(self.sarcochilus_hybrids),
            'total_intergenerics': len(self.intergeneric_crosses),
            'nursery': 'Sunset Valley Orchids',
            'url': self.base_url,
            'genus': 'Sarcochilus',
            'collection_date': datetime.now().isoformat(),
            'hybrids': self.sarcochilus_hybrids,
            'intergeneric_crosses': self.intergeneric_crosses
        }

def run_sunset_valley_scraper():
    """Run the Sunset Valley Orchids scraper"""
    scraper = SunsetValleyOrchidsScraper()
    hybrids = scraper.scrape_sarcochilus_hybrids()
    summary = scraper.get_summary()
    
    logger.info("🌅 SUNSET VALLEY ORCHIDS SCRAPING COMPLETE")
    logger.info(f"📊 Summary: {summary['total_hybrids']} Sarcochilus hybrids collected")
    
    return summary

def run_svo_intergeneric_scraper():
    """Run comprehensive Sunset Valley Orchids intergeneric cross scraper"""
    scraper = SunsetValleyOrchidsScraper()
    
    # Collect intergeneric crosses
    intergeneric_data = scraper.scrape_intergeneric_crosses()
    
    summary = {
        'total_intergenerics': len(intergeneric_data),
        'nursery': 'Sunset Valley Orchids',
        'url': scraper.base_url,
        'focus': 'Intergeneric crosses with parent data',
        'collection_date': datetime.now().isoformat(),
        'crosses': intergeneric_data
    }
    
    logger.info("🌅 SVO INTERGENERIC COLLECTION COMPLETE")
    logger.info(f"📊 Summary: {summary['total_intergenerics']} intergeneric crosses collected")
    
    return summary

if __name__ == "__main__":
    run_sunset_valley_scraper()