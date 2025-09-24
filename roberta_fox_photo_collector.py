#!/usr/bin/env python3
"""
Dedicated Roberta Fox Photo Collector
=====================================
Collects all photos from Roberta Fox's 19 orchid galleries at orchidcentral.org
Updates existing records in database with actual photo URLs
"""

import requests
from bs4 import BeautifulSoup
import time
import logging
import os
import psycopg2
from urllib.parse import urljoin
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RobertaFoxPhotoCollector:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        
        # Database connection
        self.db_url = os.environ.get('DATABASE_URL')
        self.conn = psycopg2.connect(self.db_url)
        
        # Initialize validation system
        self.validator = ScraperValidationSystem()
        self.collected_count = 0
        self.rejected_count = 0
        
        logger.info("🌺 ROBERTA FOX PHOTO COLLECTOR INITIALIZED WITH VALIDATION")
        
    def collect_all_photos(self):
        """Collect all photos from Roberta Fox's 19 galleries"""
        
        # All 19 photo galleries from orchidcentral.org
        galleries = [
            ("Angraecoid", "http://orchidcentral.org/WebPages/GroupAngrecoid.html"),
            ("Bulbophyllum", "http://orchidcentral.org/WebPages/GroupBulbophyllum.html"),
            ("Calanthe", "http://orchidcentral.org/WebPages/GroupCalanthe.html"),
            ("Catasetinae", "http://orchidcentral.org/WebPages/GroupCatasetum.html"),
            ("Cattleya Species", "http://orchidcentral.org/WebPages/GroupCattleya%20-%20Species.html"),
            ("Cattleya Hybrid", "http://orchidcentral.org/WebPages/GroupCattleya%20-%20Hybrid.html"),
            ("Coelogyne", "http://orchidcentral.org/WebPages/GroupCoelogyne.html"),
            ("Cymbidium", "http://orchidcentral.org/WebPages/GroupCymbidium.html"),
            ("Dendrobium", "http://orchidcentral.org/WebPages/GroupDendrobium.html"),
            ("Disa", "http://orchidcentral.org/WebPages/GroupDisa.html"),
            ("Ludisia", "http://orchidcentral.org/WebPages/GroupLudisia.html"),
            ("Oncidium Alliance", "http://orchidcentral.org/WebPages/GroupOncidium.html"),
            ("Paphiopedilum", "http://orchidcentral.org/WebPages/GroupPaphPhrag.html"),
            ("Phalaenopsis", "http://orchidcentral.org/WebPages/GroupPhalaenopsis.html"),
            ("Pleurothallids", "http://orchidcentral.org/WebPages/GroupPleurothallids.html"),
            ("Sobralia", "http://orchidcentral.org/WebPages/GroupSobralia.html"),
            ("Vandaceous", "http://orchidcentral.org/WebPages/GroupVandaceous.html"),
            ("Zygopetalum", "http://orchidcentral.org/WebPages/GroupZygopetalum.html"),
            ("Miscellaneous", "http://orchidcentral.org/WebPages/GroupMiscellaneous.html")
        ]
        
        total_updated = 0
        logger.info(f"🚀 STARTING COLLECTION FROM {len(galleries)} GALLERIES")
        
        for gallery_name, gallery_url in galleries:
            logger.info(f"📸 Processing {gallery_name} gallery...")
            
            try:
                updated_count = self.process_gallery(gallery_url, gallery_name)
                total_updated += updated_count
                logger.info(f"✅ {gallery_name}: Updated {updated_count} records with photos")
                time.sleep(2)  # Be respectful
                
            except Exception as e:
                logger.error(f"❌ Error processing {gallery_name}: {e}")
        
        logger.info(f"🎉 COLLECTION COMPLETE! Updated {total_updated} records with photos")
        self.conn.close()
        return total_updated
    
    def process_gallery(self, gallery_url, gallery_name):
        """Process a single gallery and create validated orchid records"""
        
        try:
            response = self.session.get(gallery_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            gallery_collected = 0
            gallery_rejected = 0
            
            with app.app_context():
                # Find all image links in the gallery
                image_links = soup.find_all('a')
                
                for link in image_links:
                    if not link or not hasattr(link, 'get'):
                        continue
                    
                    try:
                        href = link.get('href', '')
                    except AttributeError:
                        continue
                    
                    # Look for image files
                    if href and isinstance(href, str) and any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                        # Get the full image URL
                        image_url = urljoin(gallery_url, str(href))
                        
                        # Extract orchid name from the link text or nearby text
                        orchid_name = self.extract_orchid_name(link)
                        
                        if orchid_name and len(orchid_name) > 3:
                            # Create validated orchid record
                            created = self.create_validated_orchid_record(orchid_name, image_url, gallery_name, gallery_url)
                            if created:
                                gallery_collected += 1
                                self.collected_count += 1
                                logger.info(f"   ✅ Created validated orchid: {orchid_name[:50]}...")
                            else:
                                gallery_rejected += 1
                                self.rejected_count += 1
            
            logger.info(f"📊 {gallery_name}: {gallery_collected} collected, {gallery_rejected} rejected")
            return gallery_collected
            
        except Exception as e:
            logger.error(f"Error processing gallery {gallery_url}: {e}")
            return 0
    
    def extract_orchid_name(self, link):
        """Extract orchid name from link"""
        # Try link text first
        text = link.get_text(strip=True)
        if text and len(text) > 3:
            return text
        
        # Try alt text of any images in the link
        img = link.find('img')
        if img:
            alt_text = img.get('alt', '').strip()
            if alt_text and len(alt_text) > 3:
                return alt_text
        
        return None
    
    def create_validated_orchid_record(self, orchid_name, image_url, gallery_name, gallery_url):
        """Create a new validated orchid record from Roberta Fox gallery data"""
        try:
            # Parse genus from orchid name
            parts = orchid_name.split()
            genus = parts[0] if parts else ''
            species = parts[1] if len(parts) > 1 else ''
            
            # Prepare record data for validation
            record_data = {
                'display_name': orchid_name,
                'scientific_name': orchid_name,
                'genus': genus,
                'species': species,
                'image_url': image_url,
                'ai_description': f"Orchid from Roberta Fox {gallery_name} gallery: {orchid_name}",
                'ingestion_source': 'roberta_fox_validated',
                'image_source': f'Roberta Fox - {gallery_name}',
                'data_source': gallery_url
            }
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "roberta_fox_scraper")
            
            if validated_data:
                # Create validated record
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
                    orchid_record.created_at = datetime.utcnow()
                    orchid_record.updated_at = datetime.utcnow()
                    
                    db.session.add(orchid_record)
                    db.session.commit()
                    
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Database error for {orchid_name}: {e}")
                    db.session.rollback()
                    return False
            else:
                logger.debug(f"❌ Validation failed for {orchid_name} (genus: {genus})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating validated record for {orchid_name}: {e}")
            return False
    
    def update_orchid_photo(self, orchid_name, image_url, gallery_name):
        """Update orchid record in database with photo URL"""
        
        try:
            cursor = self.conn.cursor()
            
            # Find matching orchid record
            cursor.execute("""
                UPDATE orchid_record 
                SET image_url = %s, image_source = %s 
                WHERE ingestion_source = 'roberta_fox_comprehensive' 
                AND (display_name ILIKE %s OR scientific_name ILIKE %s)
                AND (image_url IS NULL OR image_url = '')
                RETURNING id
            """, (image_url, f"Roberta Fox - {gallery_name}", f"%{orchid_name}%", f"%{orchid_name}%"))
            
            result = cursor.fetchone()
            if result:
                self.conn.commit()
                return True
            
            cursor.close()
            return False
            
        except Exception as e:
            logger.error(f"Database error updating {orchid_name}: {e}")
            self.conn.rollback()
            return False

if __name__ == "__main__":
    collector = RobertaFoxPhotoCollector()
    total_photos = collector.collect_all_photos()
    print(f"🎉 FINAL RESULT: {total_photos} Roberta Fox photos collected!")