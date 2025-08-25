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
        
        logger.info("🌺 ROBERTA FOX PHOTO COLLECTOR INITIALIZED")
        
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
        """Process a single gallery and extract photo URLs"""
        
        try:
            response = self.session.get(gallery_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            updated_count = 0
            
            # Find all image links in the gallery
            image_links = soup.find_all('a')
            for link in image_links:
                href = link.get('href', '')
                
                # Look for image files
                if any(ext in href.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                    # Get the full image URL
                    image_url = urljoin(gallery_url, href)
                    
                    # Extract orchid name from the link text or nearby text
                    orchid_name = self.extract_orchid_name(link)
                    
                    if orchid_name:
                        # Update database record with photo URL
                        updated = self.update_orchid_photo(orchid_name, image_url, gallery_name)
                        if updated:
                            updated_count += 1
                            logger.info(f"   📷 Updated {orchid_name[:50]}... with photo")
            
            return updated_count
            
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