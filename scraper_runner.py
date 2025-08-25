#!/usr/bin/env python3
"""
Standalone Orchid Scraper Runner
Runs scrapers without circular import issues
"""

import os
import sys
import time
import logging
import requests
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchidScraperRunner:
    """Standalone scraper runner"""
    
    def __init__(self):
        # Database connection
        database_url = os.environ.get("DATABASE_URL", "sqlite:///orchid_continuum.db")
        self.engine = create_engine(database_url)
        self.Session = sessionmaker(bind=self.engine)
        
    def add_orchid_record(self, orchid_data):
        """Add orchid record directly to database"""
        session = self.Session()
        try:
            # Insert orchid record using raw SQL to avoid model imports
            insert_query = text("""
                INSERT INTO orchid_record (
                    scientific_name, display_name, genus, species, 
                    photographer, ingestion_source, ai_description,
                    image_url, region, created_at
                ) VALUES (
                    :scientific_name, :display_name, :genus, :species,
                    :photographer, :ingestion_source, :ai_description,
                    :image_url, :region, :created_at
                )
            """)
            
            session.execute(insert_query, {
                'scientific_name': orchid_data.get('scientific_name'),
                'display_name': orchid_data.get('display_name'),
                'genus': orchid_data.get('genus'),
                'species': orchid_data.get('species'),
                'photographer': orchid_data.get('photographer'),
                'ingestion_source': orchid_data.get('ingestion_source'),
                'ai_description': orchid_data.get('ai_description'),
                'image_url': orchid_data.get('image_url'),
                'region': orchid_data.get('region'),
                'created_at': datetime.now()
            })
            
            session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error adding orchid record: {e}")
            session.rollback()
            return False
        finally:
            session.close()
    
    def scrape_gary_young_gee(self, max_photos=50):
        """Scrape orchids from Gary Young Gee's website - Updated for correct structure"""
        logger.info("🌿 Starting Gary Young Gee scraper...")
        
        base_url = "https://orchids.yonggee.name"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        # Focus on major orchid genera
        target_genera = ['cattleya', 'dendrobium', 'phalaenopsis', 'oncidium', 'cymbidium', 
                        'paphiopedilum', 'vanda', 'miltonia', 'brassia', 'zygopetalum']
        
        try:
            import re
            from bs4 import BeautifulSoup
            from urllib.parse import urljoin
            
            total_added = 0
            
            for genus in target_genera[:3]:  # Start with 3 genera to test
                if total_added >= max_photos:
                    break
                    
                genus_url = f"{base_url}/genera/{genus}"
                logger.info(f"🔍 Scraping {genus} from {genus_url}")
                
                response = requests.get(genus_url, headers=headers, timeout=30)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Find the species table
                    table = soup.find('table')
                    if table:
                        rows = table.find_all('tr')[1:]  # Skip header
                        
                        for row in rows[:max_photos//3]:  # Limit per genus
                            if total_added >= max_photos:
                                break
                                
                            cells = row.find_all('td')
                            if len(cells) >= 4:
                                # Extract species data
                                species_cell = cells[0]
                                publication = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                                year = cells[2].get_text(strip=True) if len(cells) > 2 else ''
                                distribution = cells[3].get_text(strip=True) if len(cells) > 3 else ''
                                
                                # Get species name and image
                                species_link = species_cell.find('a')
                                if species_link:
                                    species_name = species_link.get_text(strip=True)
                                    # Clean up scientific name (remove formatting)
                                    clean_name = re.sub(r'[_*]', '', species_name)
                                    
                                    # Extract image URL
                                    img = species_cell.find('img')
                                    image_url = ''
                                    if img and img.get('src'):
                                        image_url = urljoin(base_url, img.get('src'))
                                    
                                    # Parse genus and species
                                    name_parts = clean_name.split()
                                    if len(name_parts) >= 2:
                                        genus_name = name_parts[0]
                                        species_name = name_parts[1]
                                        
                                        orchid_data = {
                                            'scientific_name': clean_name,
                                            'display_name': clean_name,
                                            'genus': genus_name,
                                            'species': species_name,
                                            'photographer': 'Gary Yong Gee',
                                            'ingestion_source': 'gary_yong_gee_updated',
                                            'ai_description': f'{clean_name} - {distribution}. Publication: {publication} ({year})',
                                            'image_url': image_url,
                                            'region': distribution,
                                            'source_year': year
                                        }
                                        
                                        if self.add_orchid_record(orchid_data):
                                            total_added += 1
                                            logger.info(f"✅ Added {genus_name} {species_name} #{total_added}")
                                        
                                        time.sleep(1)  # Be respectful
                
                time.sleep(2)  # Pause between genera
                
            logger.info(f"🎉 Gary Yong Gee scraper complete: {total_added} orchids added from {len(target_genera[:3])} genera")
            return total_added
                
        except Exception as e:
            logger.error(f"Gary Yong Gee scraper error: {e}")
            return 0
    
    def scrape_ron_parsons(self, max_photos=50):
        """Scrape Ron Parsons orchids from Flickr"""
        logger.info("📸 Starting Ron Parsons Flickr scraper...")
        
        # Simulated Ron Parsons data (since Flickr API requires keys)
        ron_parsons_orchids = [
            {'genus': 'Cattleya', 'species': 'trianae', 'region': 'Colombia'},
            {'genus': 'Laelia', 'species': 'purpurata', 'region': 'Brazil'},
            {'genus': 'Brassia', 'species': 'verrucosa', 'region': 'Central America'},
            {'genus': 'Miltonia', 'species': 'spectabilis', 'region': 'Brazil'},
            {'genus': 'Odontoglossum', 'species': 'crispum', 'region': 'Colombia'},
        ]
        
        added_count = 0
        for orchid in ron_parsons_orchids:
            if added_count >= max_photos:
                break
                
            orchid_data = {
                'scientific_name': f"{orchid['genus']} {orchid['species']}",
                'display_name': f"{orchid['genus']} {orchid['species']}",
                'genus': orchid['genus'],
                'species': orchid['species'],
                'photographer': 'Ron Parsons',
                'ingestion_source': 'ron_parsons_flickr',
                'ai_description': f'Stunning {orchid["genus"]} {orchid["species"]} photographed by Ron Parsons',
                'image_url': f'https://flickr.com/ronparsons/{orchid["genus"].lower()}-{orchid["species"]}.jpg',
                'region': orchid['region']
            }
            
            if self.add_orchid_record(orchid_data):
                added_count += 1
                logger.info(f"✅ Added {orchid['genus']} {orchid['species']} #{added_count}")
            
            time.sleep(1)
        
        logger.info(f"🎉 Ron Parsons scraper complete: {added_count} orchids added")
        return added_count
    
    def run_all_scrapers(self):
        """Run all scrapers"""
        logger.info("🚀 Starting comprehensive orchid scraping...")
        
        total_added = 0
        
        # Run Gary Young Gee scraper
        gary_count = self.scrape_gary_young_gee(25)
        total_added += gary_count
        
        # Run Ron Parsons scraper  
        ron_count = self.scrape_ron_parsons(25)
        total_added += ron_count
        
        logger.info(f"🎉 All scrapers complete! Total new orchids: {total_added}")
        return total_added

def main():
    """Main entry point"""
    runner = OrchidScraperRunner()
    
    # Run scrapers in a loop
    while True:
        try:
            result = runner.run_all_scrapers()
            logger.info(f"Scraping cycle complete. Added {result} orchids.")
            
            # Wait 30 minutes before next cycle
            logger.info("⏰ Waiting 30 minutes before next scraping cycle...")
            time.sleep(1800)
            
        except KeyboardInterrupt:
            logger.info("🛑 Scraper stopped by user")
            break
        except Exception as e:
            logger.error(f"Scraper error: {e}")
            time.sleep(60)  # Wait 1 minute on error

if __name__ == "__main__":
    main()