#!/usr/bin/env python3
"""
🌅 SUNSET VALLEY ORCHIDS ENHANCED SCRAPER
Specialized scraper for Sarcochilus hybrids from sunsetvalleyorchids.com
Integrated with Google Sheets, AI Breeder Pro, and comprehensive data storage
"""

import requests
import time
import logging
import json
import urllib.parse
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app import app, db
from models import OrchidRecord, BreedingProject, BreedingCross
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GOOGLE_SHEETS_AVAILABLE = True
except ImportError:
    GOOGLE_SHEETS_AVAILABLE = False
    logging.warning("Google Sheets libraries not available - sheets integration disabled")

# Import the new Google Cloud integration
try:
    from google_cloud_integration import get_google_integration, save_svo_data_to_sheets
    GOOGLE_CLOUD_INTEGRATION_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_INTEGRATION_AVAILABLE = False
    logging.warning("Google Cloud integration not available - using fallback functionality")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SunsetValleyOrchidsEnhancedScraper:
    """Enhanced scraper for Sunset Valley Orchids with Google Sheets integration"""
    
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
        
        # Google Cloud integration (preferred)
        self.google_integration = None
        if GOOGLE_CLOUD_INTEGRATION_AVAILABLE:
            self.google_integration = get_google_integration()
            logger.info("🌤️ Using enhanced Google Cloud integration")
        
        # Legacy Google Sheets integration (fallback)
        self.google_sheets_client = None
        self.worksheet = None
        self.initialize_google_sheets()
        
        # Image download folder
        self.image_folder = "static/uploads/svo_images"
        os.makedirs(self.image_folder, exist_ok=True)
        
        # Rate limiting
        self.request_delay = 1  # seconds between requests
        
        logger.info("🌅 Sunset Valley Orchids Enhanced Scraper initialized")
    
    def initialize_google_sheets(self):
        """Initialize Google Sheets connection for data export"""
        if not GOOGLE_SHEETS_AVAILABLE:
            logger.warning("⚠️ Google Sheets libraries not available")
            return
            
        try:
            # Check for service account credentials
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                credentials_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                credentials = Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/spreadsheets',
                           'https://www.googleapis.com/auth/drive']
                )
                self.google_sheets_client = gspread.authorize(credentials)
                
                # Create or open SVO Hybrid Data sheet
                try:
                    spreadsheet = self.google_sheets_client.open("SVO_Hybrid_Data")
                except gspread.SpreadsheetNotFound:
                    spreadsheet = self.google_sheets_client.create("SVO_Hybrid_Data")
                    
                self.worksheet = spreadsheet.sheet1
                
                # Initialize headers if sheet is empty
                if not self.worksheet.get_all_values():
                    self.worksheet.append_row([
                        "Genus", "Hybrid Name", "Parent1", "Parent2", "Year", 
                        "Breeder Notes", "Image URLs", "Price", "Availability", 
                        "Source URL", "Scraped At"
                    ])
                    
                logger.info("✅ Google Sheets integration initialized")
            else:
                logger.warning("⚠️ No Google service account found - sheets integration disabled")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Sheets: {e}")
            self.google_sheets_client = None
    
    def download_image(self, url: str, save_folder: str = None) -> Optional[str]:
        """Download image from URL and return local path"""
        if not save_folder:
            save_folder = self.image_folder
            
        try:
            # Create filename from URL
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            if not filename:
                filename = f"image_{int(time.time())}.jpg"
            
            filepath = os.path.join(save_folder, filename)
            
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            with open(filepath, "wb") as f:
                f.write(response.content)
                
            logger.info(f"📸 Downloaded image: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"❌ Error downloading image {url}: {e}")
            return None
    
    def download_and_upload_to_drive(self, url: str, filename: str = None) -> Tuple[Optional[str], Optional[str]]:
        """Download image and upload to Google Drive, return (local_path, drive_url)"""
        try:
            # Download image first
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Create filename if not provided
            if not filename:
                parsed_url = urlparse(url)
                filename = os.path.basename(parsed_url.path)
                if not filename:
                    filename = f"svo_image_{int(time.time())}.jpg"
            
            # Save locally first
            local_path = os.path.join(self.image_folder, filename)
            with open(local_path, "wb") as f:
                f.write(response.content)
            
            # Upload to Google Drive if available
            drive_url = None
            if self.google_integration and self.google_integration.is_available():
                drive_url = self.google_integration.upload_image_to_drive(
                    response.content, 
                    f"svo_{filename}"
                )
                if drive_url:
                    logger.info(f"☁️ Uploaded to Drive: {filename} -> {drive_url}")
            
            return local_path, drive_url
            
        except Exception as e:
            logger.error(f"❌ Error downloading/uploading image {url}: {e}")
            return None, None
    
    def parse_hybrid_dynamic(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Dynamic parsing of hybrid information from various HTML structures"""
        hybrids = []
        
        # Method 1: Look for table-based data
        for table in soup.find_all("table"):
            rows = table.find_all("tr")
            for row in rows:
                hybrid_data = {"images": []}
                cells = row.find_all(["td", "th"])
                
                if len(cells) < 2:
                    continue
                    
                for cell in cells:
                    text = cell.get_text(strip=True)
                    
                    # Detect hybrid names
                    if any(term in text for term in ["Hybrid", "Sarc.", "Cross", "Sarcochilus"]):
                        hybrid_data['name'] = text
                    
                    # Detect parentage (looking for 'x' or '×')
                    if "x" in text or "×" in text:
                        parts = re.split(r'[x×]', text)
                        if len(parts) >= 2:
                            hybrid_data['parent1'] = parts[0].strip()
                            hybrid_data['parent2'] = parts[1].strip()
                    
                    # Detect breeder notes (longer text)
                    if len(text) > 50 and not hybrid_data.get('notes'):
                        hybrid_data['notes'] = text
                    
                    # Detect price
                    price_match = re.search(r'\$([0-9]+(?:\.[0-9]{2})?)', text)
                    if price_match:
                        hybrid_data['price'] = f"${price_match.group(1)}"
                
                # Look for images in the row
                imgs = row.find_all("img")
                hybrid_data['images'] = [urljoin(self.base_url, img.get('src')) 
                                       for img in imgs if img.get('src')]
                
                if hybrid_data.get('name') or hybrid_data.get('images'):
                    hybrids.append(hybrid_data)
        
        # Method 2: Look for div-based product cards
        product_selectors = [
            '.product', '.plant', '.orchid', '.hybrid',
            '[class*="product"]', '[class*="plant"]', '[class*="orchid"]'
        ]
        
        for selector in product_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text()
                if any(term in text.lower() for term in ['sarcochilus', 'sarc.', 'hybrid']):
                    hybrid_data = self.parse_product_element(element)
                    if hybrid_data:
                        hybrids.append(hybrid_data)
        
        return hybrids
    
    def parse_product_element(self, element) -> Optional[Dict[str, Any]]:
        """Parse a product element for hybrid information"""
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
            images = []
            img_tags = element.find_all('img')
            for img in img_tags:
                if img.get('src'):
                    images.append(urljoin(self.base_url, img['src']))
            
            return {
                'name': name,
                'parentage': parentage,
                'description': description,
                'price': price,
                'availability': availability,
                'images': images,
                'notes': description
            }
            
        except Exception as e:
            logger.error(f"❌ Error parsing product element: {e}")
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
    
    def scrape_svo_complete(self, genera: List[str], years: List[int], max_pages: int = 5):
        """Complete scraping of SVO data with Google Sheets export"""
        logger.info("🌅 Starting comprehensive SVO scraping...")
        
        all_hybrids = []
        
        for genus in genera:
            for year in years:
                for page in range(1, max_pages + 1):
                    url = f"{self.base_url}/htm/offerings_{genus.lower()}.html"
                    if year:
                        url += f"?year={year}&page={page}"
                    
                    logger.info(f"🔍 Scraping: {url}")
                    
                    try:
                        response = self.session.get(url, timeout=15)
                        if response.status_code != 200:
                            logger.warning(f"⚠️ Failed to fetch {url} (status: {response.status_code})")
                            continue
                            
                        soup = BeautifulSoup(response.text, 'html.parser')
                        hybrids = self.parse_hybrid_dynamic(soup)
                        
                        if not hybrids:
                            logger.info(f"📭 No hybrids found on page {page} for {genus} {year}")
                            break  # No more hybrids on this page
                        
                        for hybrid in hybrids:
                            # Download images and upload to Google Drive
                            local_files = []
                            drive_urls = []
                            
                            for img_url in hybrid.get('images', []):
                                # Use enhanced download with Google Drive integration
                                local_path, drive_url = self.download_and_upload_to_drive(img_url)
                                if local_path:
                                    local_files.append(local_path)
                                if drive_url:
                                    drive_urls.append(drive_url)
                            
                            # Prepare hybrid data with enhanced Google integration
                            hybrid_data = {
                                'genus': genus,
                                'name': hybrid.get('name', ''),
                                'parent1': hybrid.get('parent1', ''),
                                'parent2': hybrid.get('parent2', ''),
                                'year': str(year),
                                'notes': hybrid.get('notes', ''),
                                'image_paths': ", ".join(local_files),
                                'image_urls': ", ".join(drive_urls),  # Google Drive URLs
                                'price': hybrid.get('price', ''),
                                'availability': hybrid.get('availability', ''),
                                'source_url': url,
                                'scraped_at': datetime.now().isoformat()
                            }
                            
                            all_hybrids.append(hybrid_data)
                            
                            # Save to Google Sheets using enhanced integration
                            if self.google_integration and self.google_integration.is_available():
                                # Use the new standardized Google integration
                                svo_data = {
                                    'genus': hybrid_data['genus'],
                                    'name': hybrid_data['name'],
                                    'parent1': hybrid_data['parent1'],
                                    'parent2': hybrid_data['parent2'],
                                    'year': hybrid_data['year'],
                                    'notes': hybrid_data['notes'],
                                    'image_urls': hybrid_data['image_urls'],
                                    'price': hybrid_data['price'],
                                    'availability': hybrid_data['availability'],
                                    'source_url': hybrid_data['source_url']
                                }
                                success = self.google_integration.save_svo_data(svo_data)
                                if success:
                                    logger.info(f"📊 Saved {hybrid_data['name']} to Google Sheets")
                            
                            # Fallback to legacy Google Sheets if available
                            elif self.worksheet:
                                try:
                                    self.worksheet.append_row([
                                        hybrid_data['genus'],
                                        hybrid_data['name'],
                                        hybrid_data['parent1'],
                                        hybrid_data['parent2'],
                                        hybrid_data['year'],
                                        hybrid_data['notes'],
                                        hybrid_data.get('image_urls', hybrid_data['image_paths']),
                                        hybrid_data['price'],
                                        hybrid_data['availability'],
                                        hybrid_data['source_url'],
                                        hybrid_data['scraped_at']
                                    ])
                                    logger.info(f"📊 Added {hybrid_data['name']} to legacy Google Sheets")
                                except Exception as e:
                                    logger.error(f"❌ Failed to add to legacy Google Sheets: {e}")
                        
                        time.sleep(self.request_delay)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"❌ Error scraping page {url}: {e}")
        
        # Store in database
        self.store_hybrids_in_database(all_hybrids)
        
        logger.info(f"✅ Scraping complete. Collected {len(all_hybrids)} hybrids")
        return all_hybrids
    
    def store_hybrids_in_database(self, hybrids: List[Dict[str, Any]]):
        """Store collected hybrids in the database"""
        logger.info("💾 Storing SVO hybrids in database...")
        
        stored_count = 0
        
        try:
            with app.app_context():
                for hybrid in hybrids:
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
                            genus=hybrid['genus'],
                            species='hybrid',
                            display_name=hybrid['name'],
                            parentage_formula=f"{hybrid.get('parent1', '')} × {hybrid.get('parent2', '')}",
                            ai_description=hybrid.get('notes'),
                            cultural_notes=f"Price: {hybrid.get('price', 'Unknown')} | Availability: {hybrid.get('availability', 'Unknown')}",
                            image_path=hybrid.get('image_paths', '').split(', ')[0] if hybrid.get('image_paths') else None,
                            data_source='Sunset Valley Orchids',
                            ingestion_source='svo_enhanced_scraper',
                            validation_status='pending',
                            created_at=datetime.now()
                        )
                        
                        db.session.add(new_record)
                        stored_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error storing hybrid {hybrid.get('name', 'Unknown')}: {e}")
                
                db.session.commit()
                logger.info(f"✅ Successfully stored {stored_count} SVO hybrids")
                
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
    
    def get_svo_breeding_data_for_ai(self) -> List[Dict[str, Any]]:
        """Get SVO breeding data formatted for AI Breeder Pro analysis"""
        try:
            with app.app_context():
                svo_records = OrchidRecord.query.filter_by(
                    data_source='Sunset Valley Orchids'
                ).all()
                
                breeding_data = []
                for record in svo_records:
                    if record.parentage_formula and '×' in record.parentage_formula:
                        parents = record.parentage_formula.split('×')
                        breeding_data.append({
                            'cross_name': record.display_name,
                            'pod_parent': parents[0].strip() if len(parents) > 0 else 'Unknown',
                            'pollen_parent': parents[1].strip() if len(parents) > 1 else 'Unknown',
                            'genus': record.genus,
                            'description': record.ai_description or '',
                            'cultural_notes': record.cultural_notes or '',
                            'image_path': getattr(record, 'image_path', getattr(record, 'image_url', None)),
                            'source': 'Sunset Valley Orchids',
                            'validated': record.validation_status == 'validated'
                        })
                
                logger.info(f"🧬 Retrieved {len(breeding_data)} SVO breeding records for AI analysis")
                return breeding_data
                
        except Exception as e:
            logger.error(f"❌ Error retrieving SVO breeding data: {e}")
            return []

# Function to run the scraper
def run_svo_scraper():
    """Run the SVO scraper with default parameters"""
    scraper = SunsetValleyOrchidsEnhancedScraper()
    
    # Define genera and years to scrape
    genera = ["Sarcochilus", "Cattleya", "Paphiopedilum", "Dendrobium", "Zygopetalum"]
    years = list(range(2013, 2025))  # Adjust based on available years
    
    return scraper.scrape_svo_complete(genera, years, max_pages=10)

if __name__ == "__main__":
    # Run the scraper when executed directly
    run_svo_scraper()