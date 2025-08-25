#!/usr/bin/env python3
"""
AOS Culture Sheet Scraper - Import American Orchid Society culture sheets
Imports comprehensive orchid care information from AOS.org
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import logging
from app import app, db
from models import OrchidRecord, OrchidTaxonomy
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AOSCultureSheetScraper:
    """Scraper for AOS culture sheets from aos.org"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.base_url = "https://www.aos.org"
        self.collected_count = 0
        
        # All available AOS culture sheets
        self.culture_sheets = [
            ('Angraecum', '/orchid-care/care-sheets/angraecum-culture-sheet'),
            ('Bulbophyllum', '/orchid-care/care-sheets/bulbophyllum-culture-sheet'),
            ('Catasetum', '/orchid-care/care-sheets/catasetum-culture-sheet'),
            ('Cattleya', '/orchid-care/care-sheets/cattleya-culture-sheet'),
            ('Coelogyne', '/orchid-care/care-sheets/coelogyne-culture-sheet'),
            ('Cymbidium', '/orchid-care/care-sheets/cymbidium-culture-sheet'),
            ('Gongora', '/orchid-care/care-sheets/gongora-culture-sheet'),
            ('Habenaria', '/orchid-care/care-sheets/habenaria-culture-sheet'),
            ('Lycaste', '/orchid-care/care-sheets/lycaste-culture-sheet'),
            ('Masdevallia', '/orchid-care/care-sheets/masdevallia-culture-sheet'),
            ('Miltonia', '/orchid-care/care-sheets/miltonia-culture-sheet'),
            ('Miltoniopsis', '/orchid-care/care-sheets/miltoniopsis-culture-sheet'),
            ('Oncidium', '/orchid-care/care-sheets/oncidium-culture-sheet'),
            ('Paphiopedilum', '/orchid-care/care-sheets/paphiopedilum-culture-sheet'),
            ('Phalaenopsis', '/orchid-care/care-sheets/phalaenopsis-culture-sheet'),
            ('Stanhopea', '/orchid-care/care-sheets/stanhopea-culture-sheet'),
            ('Tolumnia', '/orchid-care/care-sheets/tolumnia-culture-sheet'),
            ('Vanda', '/orchid-care/care-sheets/vanda-culture-sheet')
        ]
    
    def scrape_all_culture_sheets(self):
        """Scrape all AOS culture sheets"""
        logger.info("🌺 Starting AOS Culture Sheet import...")
        logger.info(f"📚 Found {len(self.culture_sheets)} culture sheets to import")
        
        results = []
        
        for genus, url_path in self.culture_sheets:
            try:
                logger.info(f"📖 Processing {genus} culture sheet...")
                
                culture_data = self.scrape_culture_sheet(genus, url_path)
                
                if culture_data:
                    # Save to database
                    saved = self.save_culture_data(culture_data)
                    if saved:
                        results.append(culture_data)
                        self.collected_count += 1
                        logger.info(f"✅ {genus} culture sheet imported successfully")
                    else:
                        logger.warning(f"⚠️ Failed to save {genus} culture sheet")
                else:
                    logger.warning(f"⚠️ No data extracted for {genus}")
                
                # Be respectful to AOS servers
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Error processing {genus}: {str(e)}")
                continue
        
        logger.info(f"🎉 AOS import complete: {self.collected_count} culture sheets imported")
        return results
    
    def scrape_culture_sheet(self, genus, url_path):
        """Scrape individual culture sheet"""
        full_url = self.base_url + url_path
        
        try:
            response = self.session.get(full_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract culture information
            culture_data = {
                'genus': genus,
                'source_url': full_url,
                'light_requirements': self.extract_section_content(soup, 'light'),
                'temperature_requirements': self.extract_section_content(soup, 'temperature'),
                'water_requirements': self.extract_section_content(soup, 'water'),
                'humidity_requirements': self.extract_section_content(soup, 'humidity'),
                'fertilizer_requirements': self.extract_section_content(soup, 'fertilize'),
                'potting_requirements': self.extract_section_content(soup, 'potting'),
                'special_notes': self.extract_section_content(soup, 'other'),
                'extracted_at': datetime.now()
            }
            
            # Clean and format the data
            culture_data = self.clean_culture_data(culture_data)
            
            return culture_data
            
        except Exception as e:
            logger.error(f"Error scraping {genus} culture sheet: {str(e)}")
            return None
    
    def extract_section_content(self, soup, section_name):
        """Extract content from specific culture section"""
        try:
            # Look for section headers with icons
            section_content = ""
            
            # Find the section by looking for headers containing the section name
            headers = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
            
            for header in headers:
                if section_name.lower() in header.get_text().lower():
                    # Found the section, now extract following content
                    current = header.find_next_sibling()
                    while current and current.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        if current.name == 'p' or current.name == 'div':
                            text = current.get_text().strip()
                            if text and not text.startswith('###'):
                                section_content += text + " "
                        elif current.name == 'ul':
                            # Handle bullet points
                            for li in current.find_all('li'):
                                section_content += "• " + li.get_text().strip() + " "
                        current = current.find_next_sibling()
                    break
            
            return section_content.strip() if section_content else None
            
        except Exception as e:
            logger.error(f"Error extracting {section_name} section: {str(e)}")
            return None
    
    def clean_culture_data(self, data):
        """Clean and format extracted culture data"""
        for key, value in data.items():
            if isinstance(value, str):
                # Remove extra whitespace and clean up text
                value = re.sub(r'\s+', ' ', value)
                value = value.replace('o ', '• ')  # Fix bullet points
                value = value.strip()
                data[key] = value if value else None
        
        return data
    
    def save_culture_data(self, culture_data):
        """Save culture data to database"""
        try:
            # Create comprehensive cultural notes
            cultural_notes = self.format_cultural_notes(culture_data)
            
            # Check if we already have a record for this genus
                existing_record = OrchidRecord.query.filter_by(
                    genus=culture_data['genus'],
                    photographer='American Orchid Society'
                ).first()
                
                if existing_record:
                    # Update existing record
                    existing_record.cultural_notes = cultural_notes
                    existing_record.ingestion_source = 'AOS Culture Sheet'
                    existing_record.updated_at = datetime.now()
                    logger.info(f"📝 Updated existing {culture_data['genus']} culture record")
                else:
                    # Create new record
                    new_record = OrchidRecord(
                        scientific_name=f"{culture_data['genus']} sp.",
                        display_name=f"{culture_data['genus']} Culture Guide",
                        genus=culture_data['genus'],
                        species='Culture Guide',
                        photographer='American Orchid Society',
                        ingestion_source='AOS Culture Sheet',
                        cultural_notes=cultural_notes,
                        ai_description=f"Official AOS culture guide for {culture_data['genus']} orchids",
                        region='Comprehensive Guide',
                        created_at=datetime.now()
                    )
                    
                    db.session.add(new_record)
                    logger.info(f"🆕 Created new {culture_data['genus']} culture record")
                
                # Also update taxonomy table if exists
                taxonomy_record = OrchidTaxonomy.query.filter_by(
                    genus=culture_data['genus']
                ).first()
                
                if taxonomy_record:
                    taxonomy_record.cultural_notes = cultural_notes
                    logger.info(f"📚 Updated taxonomy for {culture_data['genus']}")
                
                db.session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving culture data for {culture_data['genus']}: {str(e)}")
            db.session.rollback()
            return False
    
    def format_cultural_notes(self, data):
        """Format culture data into comprehensive notes"""
        notes = f"AOS CULTURE GUIDE - {data['genus']}\n"
        notes += "=" * 50 + "\n\n"
        
        if data.get('light_requirements'):
            notes += "💡 LIGHT REQUIREMENTS:\n"
            notes += data['light_requirements'] + "\n\n"
        
        if data.get('temperature_requirements'):
            notes += "🌡️ TEMPERATURE:\n"
            notes += data['temperature_requirements'] + "\n\n"
        
        if data.get('water_requirements'):
            notes += "💧 WATERING:\n"
            notes += data['water_requirements'] + "\n\n"
        
        if data.get('humidity_requirements'):
            notes += "💨 HUMIDITY:\n"
            notes += data['humidity_requirements'] + "\n\n"
        
        if data.get('fertilizer_requirements'):
            notes += "🌱 FERTILIZER:\n"
            notes += data['fertilizer_requirements'] + "\n\n"
        
        if data.get('potting_requirements'):
            notes += "🪴 POTTING:\n"
            notes += data['potting_requirements'] + "\n\n"
        
        if data.get('special_notes'):
            notes += "ℹ️ SPECIAL NOTES:\n"
            notes += data['special_notes'] + "\n\n"
        
        notes += f"Source: {data['source_url']}\n"
        notes += f"Imported: {data['extracted_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        notes += "© American Orchid Society - Used for educational purposes"
        
        return notes

def run_aos_import():
    """Run the AOS culture sheet import"""
    with app.app_context():
        scraper = AOSCultureSheetScraper()
        results = scraper.scrape_all_culture_sheets()
    
    print("🎉 AOS CULTURE SHEET IMPORT COMPLETE!")
    print(f"📊 Total imported: {scraper.collected_count} culture sheets")
    print(f"📚 Genera covered: {', '.join([r['genus'] for r in results])}")
    
    return results

if __name__ == "__main__":
    run_aos_import()