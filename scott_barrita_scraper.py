"""
Scott Barrita Orchids Scraper
Specialized scraper for comprehensive Sarcochilus breeding data collection
"""

import requests
from bs4 import BeautifulSoup
import json
import logging
import re
from datetime import datetime
from urllib.parse import urljoin, urlparse
import time
from app import app, db
from models import OrchidRecord
from orchid_ai import analyze_orchid_image, extract_metadata_from_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ScottBarritaScraper:
    def __init__(self):
        self.base_url = "https://barritaorchids.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.collected_orchids = []
        
    def scrape_collection_page(self, url="https://barritaorchids.com/collections/selected-plants"):
        """Scrape the selected plants collection page"""
        try:
            logger.info(f"🔍 Scraping Barrita Orchids collection: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for product grids and product items
            products = soup.find_all('div', class_=['product-item', 'product-card', 'grid-item'])
            
            if not products:
                # Try alternative selectors
                products = soup.find_all('a', href=re.compile(r'/products/'))
                
            if not products:
                # Look for any links containing product information
                products = soup.find_all('div', class_=re.compile(r'product|item|card'))
            
            logger.info(f"📦 Found {len(products)} potential products")
            
            for product in products:
                try:
                    self.process_product_item(product, soup)
                    time.sleep(1)  # Respectful delay
                except Exception as e:
                    logger.error(f"❌ Error processing product: {e}")
                    continue
                    
            return self.collected_orchids
            
        except requests.RequestException as e:
            logger.error(f"❌ Failed to scrape collection page: {e}")
            return []
    
    def process_product_item(self, product_element, full_soup):
        """Process individual product item"""
        try:
            # Extract product name and link
            product_link = None
            product_name = None
            
            # Try multiple methods to find product link
            link_element = product_element.find('a', href=re.compile(r'/products/'))
            if not link_element:
                link_element = product_element.find_parent('a', href=re.compile(r'/products/'))
            if not link_element:
                link_element = product_element.find('a')
                
            if link_element and link_element.get('href'):
                product_link = urljoin(self.base_url, link_element['href'])
                
                # Extract product name
                product_name = link_element.get('title') or link_element.get_text(strip=True)
                
                # Look for name in child elements
                if not product_name:
                    name_elem = product_element.find(['h2', 'h3', 'h4', 'span'], class_=re.compile(r'title|name|product'))
                    if name_elem:
                        product_name = name_elem.get_text(strip=True)
            
            # Extract image URL
            image_url = None
            img_elem = product_element.find('img')
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                if image_url and not image_url.startswith('http'):
                    image_url = urljoin(self.base_url, image_url)
            
            # Check if this is a Sarcochilus or contains Sarcochilus breeding
            if product_name and ('sarcochilus' in product_name.lower() or 'sarc' in product_name.lower()):
                logger.info(f"🌺 Found Sarcochilus: {product_name}")
                
                # Get detailed product information
                detailed_info = self.scrape_product_details(product_link) if product_link else {}
                
                orchid_data = {
                    'name': product_name,
                    'product_url': product_link,
                    'image_url': image_url,
                    'source': 'Scott Barrita Orchids',
                    'extracted_at': datetime.now().isoformat(),
                    **detailed_info
                }
                
                self.collected_orchids.append(orchid_data)
                
        except Exception as e:
            logger.error(f"❌ Error processing product item: {e}")
    
    def scrape_product_details(self, product_url):
        """Scrape detailed information from individual product page"""
        try:
            logger.info(f"📋 Getting details for: {product_url}")
            response = self.session.get(product_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            details = {}
            
            # Extract price
            price_elem = soup.find(['span', 'div'], class_=re.compile(r'price|cost|amount'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                details['price'] = price_text
            
            # Extract description
            desc_elem = soup.find(['div', 'p'], class_=re.compile(r'description|product-description|details'))
            if desc_elem:
                details['description'] = desc_elem.get_text(strip=True)
            
            # Extract availability/stock
            stock_elem = soup.find(['span', 'div'], class_=re.compile(r'stock|availability|inventory'))
            if stock_elem:
                details['availability'] = stock_elem.get_text(strip=True)
            
            # Look for breeding/parentage information
            parentage_patterns = [
                r'(\w+)\s*[×x]\s*(\w+)',  # Species × Species
                r'Parentage:?\s*(.+)',     # Parentage: info
                r'Parents?:?\s*(.+)',      # Parent: info
                r'Cross:?\s*(.+)'          # Cross: info
            ]
            
            full_text = soup.get_text()
            for pattern in parentage_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    details['parentage'] = match.group(1) if len(match.groups()) == 1 else f"{match.group(1)} × {match.group(2)}"
                    break
            
            # Extract size information
            size_patterns = [
                r'(\d+\.?\d*)\s*(?:inch|in|cm|mm)',
                r'size:?\s*(\w+)',
                r'(\d+\.?\d*)"'
            ]
            
            for pattern in size_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    details['size_info'] = match.group()
                    break
            
            return details
            
        except Exception as e:
            logger.error(f"❌ Error getting product details: {e}")
            return {}
    
    def search_sarcochilus_specifically(self):
        """Search specifically for Sarcochilus on the website"""
        search_urls = [
            "https://barritaorchids.com/search?q=sarcochilus",
            "https://barritaorchids.com/search?q=Sarcochilus",
            "https://barritaorchids.com/collections/sarcochilus",
            "https://barritaorchids.com/collections/australian-orchids"
        ]
        
        for search_url in search_urls:
            try:
                logger.info(f"🔍 Searching: {search_url}")
                response = self.session.get(search_url, timeout=30)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for product results
                    products = soup.find_all('div', class_=re.compile(r'product|result|item'))
                    
                    for product in products:
                        self.process_product_item(product, soup)
                        
                    time.sleep(2)  # Respectful delay between searches
                    
            except Exception as e:
                logger.error(f"❌ Search failed for {search_url}: {e}")
                continue
    
    def store_orchids_to_database(self):
        """Store collected orchid data to database"""
        stored_count = 0
        
        with app.app_context():
            for orchid_data in self.collected_orchids:
                try:
                    # Check if already exists
                    existing = OrchidRecord.query.filter_by(
                        display_name=orchid_data['name'],
                        data_source='Scott Barrita Orchids'
                    ).first()
                    
                    if existing:
                        logger.info(f"⏭️ Skipping existing: {orchid_data['name']}")
                        continue
                    
                    # Analyze the name to extract genus/species
                    genus, species = self.parse_orchid_name(orchid_data['name'])
                    
                    # Create new orchid record
                    new_orchid = OrchidRecord(
                        genus=genus,
                        species=species,
                        display_name=orchid_data['name'],
                        data_source='Scott Barrita Orchids',
                        image_url=orchid_data.get('image_url'),
                        cultural_notes=orchid_data.get('description', ''),
                        ai_description=f"Sarcochilus from Scott Barrita Orchids collection. {orchid_data.get('description', '')}",
                        parentage_formula=orchid_data.get('parentage'),
                        ai_extracted_metadata=json.dumps({
                            'price': orchid_data.get('price'),
                            'availability': orchid_data.get('availability'),
                            'size_info': orchid_data.get('size_info'),
                            'product_url': orchid_data.get('product_url'),
                            'extracted_at': orchid_data.get('extracted_at')
                        }),
                        validation_status='pending',
                        ingestion_source='automated_scraping',
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(new_orchid)
                    stored_count += 1
                    logger.info(f"✅ Stored: {orchid_data['name']}")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to store {orchid_data['name']}: {e}")
                    continue
            
            try:
                db.session.commit()
                logger.info(f"💾 Successfully stored {stored_count} Sarcochilus orchids")
            except Exception as e:
                db.session.rollback()
                logger.error(f"❌ Database commit failed: {e}")
                
        return stored_count
    
    def parse_orchid_name(self, name):
        """Parse orchid name to extract genus and species"""
        # Clean the name
        name = re.sub(r'[^\w\s×x\-\.]', '', name)
        
        # Look for Sarcochilus patterns
        if 'sarcochilus' in name.lower():
            # Try to extract species
            patterns = [
                r'Sarcochilus\s+(\w+)',
                r'Sarc\.?\s+(\w+)',
                r'sarcochilus\s+(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, name, re.IGNORECASE)
                if match:
                    return 'Sarcochilus', match.group(1)
            
            return 'Sarcochilus', 'hybrid'
        
        # Default fallback
        return 'Sarcochilus', 'unknown'

def run_scott_barrita_collection():
    """Main function to run Scott Barrita Orchids collection"""
    logger.info("🚀 Starting Scott Barrita Orchids Sarcochilus collection")
    
    scraper = ScottBarritaScraper()
    
    # First, scrape the main collection page
    orchids = scraper.scrape_collection_page()
    
    # Then search specifically for Sarcochilus
    scraper.search_sarcochilus_specifically()
    
    logger.info(f"📊 Total Sarcochilus found: {len(scraper.collected_orchids)}")
    
    # Store to database
    stored_count = scraper.store_orchids_to_database()
    
    # Return summary
    return {
        'source': 'Scott Barrita Orchids',
        'total_found': len(scraper.collected_orchids),
        'stored_count': stored_count,
        'orchids': scraper.collected_orchids
    }

if __name__ == "__main__":
    result = run_scott_barrita_collection()
    print(json.dumps(result, indent=2))