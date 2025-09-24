import requests
from bs4 import BeautifulSoup
import os
import json
import time
import logging
from urllib.parse import urljoin, urlparse
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "https://www.svo.org/index.php?dir=hybrids&genus={}"
GENERAE = ["Sarcochilus", "Zygopetalum", "Cattleya"]
PHOTOS_DIR = "photos/"
OUTPUT_DIR = "output/"
os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def safe_get_text(element):
    """Safely extract text from BeautifulSoup element"""
    return element.get_text().strip() if element else ""

def safe_get_attr(element, attr):
    """Safely extract attribute from BeautifulSoup element"""
    return element.get(attr) if element else ""

def download_image(img_url, filename, base_url):
    """Download image with error handling"""
    try:
        # Handle relative URLs
        if not img_url.startswith('http'):
            img_url = urljoin(base_url, img_url)
        
        response = requests.get(img_url, timeout=10)
        response.raise_for_status()
        
        with open(os.path.join(PHOTOS_DIR, filename), "wb") as f:
            f.write(response.content)
        return True
    except Exception as e:
        print(f"Error downloading {img_url}: {e}")
        return False

def scrape_genus_with_validation(genus):
    """Scrape orchid data for a specific genus with validation"""
    url = BASE_URL.format(genus)
    logger.info(f"🌺 Scraping {genus} from {url}")
    
    validator = ScraperValidationSystem()
    collected_count = 0
    rejected_count = 0
    
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        
        with app.app_context():
            # Strategy: Look for any structure with images and text
            images = soup.find_all('img')
            logger.info(f"🔍 Found {len(images)} images for {genus}")
            
            for i, img in enumerate(images[:10]):  # Limit to 10 per genus
                img_src = safe_get_attr(img, 'src')
                img_alt = safe_get_attr(img, 'alt')
                
                if not img_src or 'icon' in img_src.lower() or 'logo' in img_src.lower():
                    continue
                    
                # Try to find associated text content
                parent = img.parent
                text_content = ""
                name = f"{genus} specimen {i+1}"
                
                if parent:
                    text_content = safe_get_text(parent)
                    # Extract potential orchid name from nearby text
                    text_parts = text_content.split()
                    if len(text_parts) > 1:
                        potential_name = ' '.join(text_parts[:3])  # Take first few words
                        if any(char.isupper() for char in potential_name):
                            name = potential_name
                
                # Prepare record data for validation
                record_data = {
                    'display_name': name,
                    'scientific_name': name,
                    'genus': genus,
                    'species': '',
                    'image_url': urljoin(url, img_src) if not img_src.startswith('http') else img_src,
                    'ai_description': text_content[:200] if text_content else f"SVO hybrid specimen: {name}",
                    'ingestion_source': 'svo_validated_hybrid',
                    'image_source': 'Society for Variation Orchids (SVO)',
                    'data_source': url
                }
                
                # Validate before creating database record
                validated_data = create_validated_orchid_record(record_data, "svo_scraper")
                
                if validated_data:
                    # Create validated record
                    try:
                        orchid_record = OrchidRecord(
                            display_name=validated_data['display_name'],
                            scientific_name=validated_data['scientific_name'],
                            genus=validated_data['genus'],
                            species=validated_data.get('species', ''),
                            image_url=validated_data.get('image_url', ''),
                            ai_description=validated_data['ai_description'],
                            ingestion_source=validated_data['ingestion_source'],
                            image_source=validated_data['image_source'],
                            data_source=validated_data['data_source'],
                            created_at=datetime.utcnow(),
                            updated_at=datetime.utcnow()
                        )
                        
                        db.session.add(orchid_record)
                        db.session.commit()
                        
                        logger.info(f"✅ Added validated SVO orchid: {name}")
                        collected_count += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Database error for {name}: {e}")
                        db.session.rollback()
                        rejected_count += 1
                else:
                    logger.warning(f"❌ Rejected invalid SVO orchid: {name} (genus: {genus})")
                    rejected_count += 1
                
                # Be respectful - small delay between requests
                time.sleep(0.5)
        
        logger.info(f"📊 SVO {genus} Results: {collected_count} collected, {rejected_count} rejected")
        return {'collected': collected_count, 'rejected': rejected_count}
        
    except Exception as e:
        logger.error(f"❌ Error scraping {genus}: {e}")
        return {'collected': 0, 'rejected': 0, 'error': str(e)}

def main():
    """Main scraping function with validation integration"""
    logger.info("🌺 Starting SVO Orchid Scraper with Validation")
    logger.info("=" * 50)
    
    total_collected = 0
    total_rejected = 0
    results = {}
    
    for genus in GENERAE:
        logger.info(f"🔍 Processing genus: {genus}")
        result = scrape_genus_with_validation(genus)
        
        total_collected += result.get('collected', 0)
        total_rejected += result.get('rejected', 0)
        results[genus] = result
        
        # Respectful delay between genera
        time.sleep(2)
    
    # Generate comprehensive report
    logger.info("📊 SVO SCRAPING REPORT WITH VALIDATION")
    logger.info(f"   Total collected: {total_collected}")
    logger.info(f"   Total rejected: {total_rejected}")
    validation_rate = (total_collected / (total_collected + total_rejected) * 100) if (total_collected + total_rejected) > 0 else 0
    logger.info(f"   Validation rate: {validation_rate:.1f}%")
    
    for genus, result in results.items():
        logger.info(f"   {genus}: {result.get('collected', 0)} collected, {result.get('rejected', 0)} rejected")
        if 'error' in result:
            logger.error(f"     Error: {result['error']}")
    
    return {
        'total_collected': total_collected,
        'total_rejected': total_rejected,
        'results_by_genus': results,
        'validation_enabled': True
    }

if __name__ == "__main__":
    main()