#!/usr/bin/env python3
"""
Baker OrchidCulture.com Scraper - Import Charles and Margaret Baker culture sheets
Imports detailed orchid culture information from orchidculture.com
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

class BakerOrchidCultureScraper:
    """Scraper for Charles and Margaret Baker culture sheets from orchidculture.com"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.base_url = "https://www.orchidculture.com"
        self.collected_count = 0
        
        # Baker culture articles and sheets
        self.culture_articles = [
            {
                'url': 'https://www.orchidculture.com/COD/FREE/Paph_arm_Art.html',
                'species': 'Paphiopedilum armeniacum',
                'genus': 'Paphiopedilum',
                'type': 'detailed_habitat'
            },
            {
                'url': 'https://www.orchidculture.com/COD/FREE/Miltoniopsis_Art.html',
                'species': 'Miltoniopsis',
                'genus': 'Miltoniopsis',
                'type': 'genus_comprehensive'
            },
            {
                'url': 'https://www.orchidculture.com/COD/FREE/Miltonia_Art.html',
                'species': 'Miltonia',
                'genus': 'Miltonia',
                'type': 'genus_comprehensive'
            },
            {
                'url': 'https://www.orchidculture.com/COD/FREE/Coel_Art.html',
                'species': 'Coelogyne',
                'genus': 'Coelogyne',
                'type': 'genus_comprehensive'
            },
            {
                'url': 'https://www.orchidculture.com/COD/FREE/Den_Art.html',
                'species': 'Dendrobium',
                'genus': 'Dendrobium',
                'type': 'genus_comprehensive'
            },
            {
                'url': 'https://www.orchidculture.com/COD/fragrance.html',
                'species': 'Orchid Fragrance Database',
                'genus': 'Multiple',
                'type': 'fragrance_database'
            },
            {
                'url': 'https://www.orchidculture.com/COD/daylength.html',
                'species': 'Orchid Daylength Database',
                'genus': 'Multiple',
                'type': 'daylength_database'
            },
            {
                'url': 'https://www.orchidculture.com/COD/humidity.html',
                'species': 'Orchid Humidity Guide',
                'genus': 'Multiple',
                'type': 'technical_guide'
            },
            {
                'url': 'https://www.orchidculture.com/COD/lightlevel.html',
                'species': 'Orchid Light Levels Guide',
                'genus': 'Multiple',  
                'type': 'technical_guide'
            },
            {
                'url': 'https://www.orchidculture.com/COD/favorites.html',
                'species': 'Orchid Research Links Database',
                'genus': 'Multiple',
                'type': 'research_database'
            },
            {
                'url': 'https://www.orchidculture.com/COD/intro_climate.html',
                'species': 'Orchid Climate Tables Guide',
                'genus': 'Multiple',
                'type': 'scientific_methodology'
            }
        ]
    
    def scrape_all_baker_culture_sheets(self):
        """Scrape all Baker culture sheets"""
        logger.info("🌺 Starting Baker Culture Sheet import from orchidculture.com...")
        logger.info(f"📚 Found {len(self.culture_articles)} culture articles to import")
        
        with app.app_context():
            results = []
            
            for article in self.culture_articles:
                try:
                    logger.info(f"📖 Processing {article['species']} culture article...")
                    
                    culture_data = self.scrape_culture_article(article)
                    
                    if culture_data:
                        # Save to database
                        saved = self.save_baker_culture_data(culture_data)
                        if saved:
                            results.append(culture_data)
                            self.collected_count += 1
                            logger.info(f"✅ {article['species']} culture sheet imported successfully")
                        else:
                            logger.warning(f"⚠️ Failed to save {article['species']} culture sheet")
                    else:
                        logger.warning(f"⚠️ No data extracted for {article['species']}")
                    
                    # Be respectful to orchidculture.com servers
                    time.sleep(3)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {article['species']}: {str(e)}")
                    continue
            
            logger.info(f"🎉 Baker OrchidCulture import complete: {self.collected_count} culture sheets imported")
            return results

    def import_individual_culture_sheets(self, url_list):
        """Import individual Baker culture sheets from URLs"""
        logger.info(f"📖 Starting import of {len(url_list)} individual Baker culture sheets...")
        
        with app.app_context():
            results = []
            
            for url in url_list:
                try:
                    # Extract FS number for tracking
                    fs_number = url.split('/')[-1].replace('.html', '').replace('FS', '')
                    logger.info(f"📖 Processing FS{fs_number}...")
                    
                    # Fetch and parse the page
                    response = self.session.get(url, timeout=15)
                    response.raise_for_status()
                    
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract species name from the page content
                    species_name = None
                    
                    # Try to find species name in italic text (most common location)
                    em_tag = soup.find('em')
                    if em_tag:
                        species_name = em_tag.get_text().strip()
                    
                    # If not found, look for pattern in text
                    if not species_name:
                        text = soup.get_text()
                        import re
                        # Look for pattern like "Genus species Author"
                        pattern = r'([A-Z][a-z]+\s+[a-z]+(?:\s+[a-z]+)*)\s+[A-Z]'
                        match = re.search(pattern, text)
                        if match:
                            species_name = match.group(1)
                    
                    # If still not found, use FS number
                    if not species_name or len(species_name) < 5:
                        species_name = f"Baker Culture Sheet FS{fs_number}"
                    
                    # Get the full content
                    content = soup.get_text()
                    
                    # Create culture data record
                    culture_data = {
                        'species': species_name,
                        'genus': species_name.split()[0] if ' ' in species_name else 'Baker',
                        'source_url': url,
                        'article_type': f'individual_culture_sheet_FS{fs_number}',
                        'authors': 'Charles and Margaret Baker',
                        'full_text': content,
                        'habitat_data': self.extract_habitat_data(content),
                        'climate_data': self.extract_climate_data(content), 
                        'culture_recommendations': self.extract_culture_recommendations(content),
                        'extracted_at': datetime.now()
                    }
                    
                    # Save to database
                    saved = self.save_baker_culture_data(culture_data)
                    if saved:
                        logger.info(f"✅ Successfully imported {species_name} (FS{fs_number})")
                        results.append(culture_data)
                        self.collected_count += 1
                    else:
                        logger.warning(f"❌ Failed to save {species_name} (FS{fs_number})")
                    
                    # Be respectful to servers
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing {url}: {str(e)}")
                    continue
            
            logger.info(f"🎉 Individual culture sheet import complete: {len(results)} sheets imported")
            return results
    
    def scrape_culture_article(self, article):
        """Scrape individual culture article"""
        try:
            response = self.session.get(article['url'], timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract the full text content
            full_text = soup.get_text()
            
            # Parse the specific sections
            culture_data = {
                'species': article['species'],
                'genus': article['genus'],
                'source_url': article['url'],
                'article_type': article['type'],
                'authors': 'Charles and Margaret Baker',
                'full_text': full_text,
                'habitat_data': self.extract_habitat_data(full_text),
                'climate_data': self.extract_climate_data(full_text),
                'culture_recommendations': self.extract_culture_recommendations(full_text),
                'extracted_at': datetime.now()
            }
            
            return culture_data
            
        except Exception as e:
            logger.error(f"Error scraping {article['species']} culture article: {str(e)}")
            return None
    
    def extract_habitat_data(self, text):
        """Extract habitat information from the text"""
        habitat_info = {}
        
        # Extract elevation
        elevation_match = re.search(r'(\d+,?\d*)\s*ft\.?\s*\((\d+,?\d*)\s*m\)', text)
        if elevation_match:
            habitat_info['elevation_ft'] = elevation_match.group(1).replace(',', '')
            habitat_info['elevation_m'] = elevation_match.group(2).replace(',', '')
        
        # Extract location - specific patterns
        if 'Yunnan Province' in text:
            habitat_info['location'] = 'Yunnan Province, China'
            habitat_info['country'] = 'China'
        elif 'Colombia, Ecuador, and Panama' in text:
            habitat_info['location'] = 'Colombia, Ecuador, Panama'
            habitat_info['country'] = 'South America'
        elif 'Andean' in text:
            habitat_info['location'] = 'Andean regions'
            habitat_info['country'] = 'South America'
        elif 'Brazilian' in text and 'Brazil' in text:
            habitat_info['location'] = 'Brazil (multiple states)'
            habitat_info['country'] = 'Brazil'
        elif 'Himalayan' in text and 'India' in text:
            habitat_info['location'] = 'Himalayan region (India, Nepal, Sikkim)'
            habitat_info['country'] = 'India/Nepal'
        elif 'Vietnam' in text and 'Annam' in text:
            habitat_info['location'] = 'Vietnam (formerly Annam)'
            habitat_info['country'] = 'Vietnam'
        elif 'Philippines' in text and 'Luzon' in text:
            habitat_info['location'] = 'Philippines (Luzon)'
            habitat_info['country'] = 'Philippines'
        elif 'southeast Asia' in text and 'Indonesia' in text:
            habitat_info['location'] = 'Southeast Asia (Indonesia)'
            habitat_info['country'] = 'Indonesia'
        
        # Extract latitude if mentioned
        lat_match = re.search(r'(\d+\.?\d*)°N\s*Latitude', text)
        if lat_match:
            habitat_info['latitude'] = lat_match.group(1)
        
        # Extract specific habitat description
        if 'limestone hills and cliffs' in text:
            habitat_info['substrate'] = 'limestone cliffs'
            habitat_info['habitat_type'] = 'semishady mountain forests'
        elif 'cloudforests' in text:
            habitat_info['habitat_type'] = 'humid cloudforests'
        elif 'humid forests' in text:
            habitat_info['habitat_type'] = 'humid forests'
        
        return habitat_info
    
    def extract_climate_data(self, text):
        """Extract detailed climate data from the text"""
        climate_data = {}
        
        # Look for the climate table
        if 'F AVG MAX' in text:
            # Extract temperature ranges
            temp_pattern = r'F AVG MAX\s+([\d\s]+)\nF AVG MIN\s+([\d\s]+)'
            temp_match = re.search(temp_pattern, text)
            if temp_match:
                max_temps = temp_match.group(1).split()
                min_temps = temp_match.group(2).split()
                
                climate_data['temp_max_f'] = max_temps
                climate_data['temp_min_f'] = min_temps
        
        # Extract humidity data
        humidity_match = re.search(r'HUMIDITY/%\s+([\d\s]+)', text)
        if humidity_match:
            climate_data['humidity_percent'] = humidity_match.group(1).split()
        
        # Extract rainfall data
        rainfall_match = re.search(r'RAIN/INCHES\s+([\d\.\s]+)', text)
        if rainfall_match:
            climate_data['rainfall_inches'] = rainfall_match.group(1).split()
        
        return climate_data
    
    def extract_culture_recommendations(self, text):
        """Extract specific culture recommendations"""
        recommendations = {}
        
        # Extract light requirements
        light_match = re.search(r'LIGHT:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if light_match:
            recommendations['light'] = light_match.group(1).strip()
        
        # Extract temperature requirements
        temp_match = re.search(r'TEMPERATURES:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if temp_match:
            recommendations['temperature'] = temp_match.group(1).strip()
        
        # Extract humidity requirements
        humidity_match = re.search(r'HUMIDITY:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if humidity_match:
            recommendations['humidity'] = humidity_match.group(1).strip()
        
        # Extract watering requirements
        water_match = re.search(r'WATER:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if water_match:
            recommendations['water'] = water_match.group(1).strip()
        
        # Extract fertilizer requirements
        fert_match = re.search(r'FERTILIZER:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if fert_match:
            recommendations['fertilizer'] = fert_match.group(1).strip()
        
        # Extract rest period info
        rest_match = re.search(r'REST PERIOD:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if rest_match:
            recommendations['rest_period'] = rest_match.group(1).strip()
        
        # Extract growing media info
        media_match = re.search(r'GROWING MEDIA:\s*([^\n]+(?:\n[^A-Z\n][^\n]*)*)', text)
        if media_match:
            recommendations['growing_media'] = media_match.group(1).strip()
        
        return recommendations
    
    def save_baker_culture_data(self, culture_data):
        """Save Baker culture data to database"""
        try:
            # Create comprehensive cultural notes
            cultural_notes = self.format_baker_cultural_notes(culture_data)
            
            # Check if we already have a record for this species/genus
            # Handle both species-specific and genus-wide articles
            if culture_data['article_type'] == 'genus_comprehensive':
                search_name = culture_data['genus']
                display_name = f"{culture_data['genus']} Comprehensive Culture Guide"
                species_part = 'Comprehensive Guide'
            else:
                search_name = culture_data['species']
                display_name = f"{culture_data['species']} - Baker Culture Guide"
                species_part = culture_data['species'].split()[1] if len(culture_data['species'].split()) > 1 else 'sp.'
            
            existing_record = OrchidRecord.query.filter_by(
                scientific_name=search_name,
                photographer='Charles and Margaret Baker'
            ).first()
            
            if existing_record:
                # Update existing record
                existing_record.cultural_notes = cultural_notes
                existing_record.ingestion_source = 'Baker OrchidCulture.com'
                existing_record.updated_at = datetime.now()
                logger.info(f"📝 Updated existing {search_name} culture record")
            else:
                # Create new record
                habitat_info = culture_data.get('habitat_data', {})
                elevation_info = f"Elevation: {habitat_info.get('elevation_ft', 'Various')} ft" if habitat_info.get('elevation_ft') else ""
                habitat_type = habitat_info.get('habitat_type', '')
                native_habitat = f"{elevation_info}, {habitat_type}".strip(', ') if elevation_info or habitat_type else "Various habitats"
                
                new_record = OrchidRecord(
                    scientific_name=search_name,
                    display_name=display_name,
                    genus=culture_data['genus'],
                    species=species_part,
                    photographer='Charles and Margaret Baker',
                    ingestion_source='Baker OrchidCulture.com',
                    cultural_notes=cultural_notes,
                    ai_description=f"Comprehensive culture guide for {search_name} by Charles and Margaret Baker",
                    region=habitat_info.get('location', 'South America'),
                    native_habitat=native_habitat,
                    created_at=datetime.now()
                )
                
                db.session.add(new_record)
                logger.info(f"🆕 Created new {search_name} culture record")
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error saving culture data for {culture_data['species']}: {str(e)}")
            db.session.rollback()
            return False
    
    def format_baker_cultural_notes(self, data):
        """Format Baker culture data into comprehensive notes"""
        notes = f"BAKER CULTURE GUIDE - {data['species']}\n"
        notes += "=" * 60 + "\n\n"
        notes += "By Charles and Margaret Baker\n\n"
        
        # Habitat information
        if data['habitat_data']:
            notes += "🏔️ HABITAT DATA:\n"
            habitat = data['habitat_data']
            if habitat.get('location'):
                notes += f"Location: {habitat['location']}\n"
            if habitat.get('elevation_ft'):
                notes += f"Elevation: {habitat['elevation_ft']} ft ({habitat.get('elevation_m', 'Unknown')} m)\n"
            if habitat.get('latitude'):
                notes += f"Latitude: {habitat['latitude']}°N\n"
            if habitat.get('substrate'):
                notes += f"Substrate: {habitat['substrate']}\n"
            if habitat.get('habitat_type'):
                notes += f"Habitat: {habitat['habitat_type']}\n"
            notes += "\n"
        
        # Culture recommendations
        if data['culture_recommendations']:
            recs = data['culture_recommendations']
            
            if recs.get('light'):
                notes += "💡 LIGHT:\n"
                notes += recs['light'] + "\n\n"
            
            if recs.get('temperature'):
                notes += "🌡️ TEMPERATURE:\n"
                notes += recs['temperature'] + "\n\n"
            
            if recs.get('humidity'):
                notes += "💨 HUMIDITY:\n"
                notes += recs['humidity'] + "\n\n"
            
            if recs.get('water'):
                notes += "💧 WATERING:\n"
                notes += recs['water'] + "\n\n"
            
            if recs.get('fertilizer'):
                notes += "🌱 FERTILIZER:\n"
                notes += recs['fertilizer'] + "\n\n"
            
            if recs.get('rest_period'):
                notes += "😴 REST PERIOD:\n"
                notes += recs['rest_period'] + "\n\n"
            
            if recs.get('growing_media'):
                notes += "🪴 GROWING MEDIA:\n"
                notes += recs['growing_media'] + "\n\n"
        
        # Climate data summary
        if data['climate_data']:
            notes += "📊 CLIMATE SUMMARY:\n"
            climate = data['climate_data']
            if climate.get('temp_max_f'):
                notes += "Temperature range throughout the year with precise monthly data\n"
            if climate.get('humidity_percent'):
                notes += "Humidity varies seasonally from 60-85%\n"
            if climate.get('rainfall_inches'):
                notes += "Distinct wet and dry seasons\n"
            notes += "\n"
        
        notes += f"Source: {data['source_url']}\n"
        notes += f"Authors: {data['authors']}\n"
        notes += f"Imported: {data['extracted_at'].strftime('%Y-%m-%d %H:%M:%S')}\n"
        notes += "© Charles and Margaret Baker - Used for educational purposes"
        
        return notes

def run_baker_import():
    """Run the Baker OrchidCulture.com import"""
    scraper = BakerOrchidCultureScraper()
    results = scraper.scrape_all_baker_culture_sheets()
    
    print("🎉 BAKER ORCHIDCULTURE.COM IMPORT COMPLETE!")
    print(f"📊 Total imported: {scraper.collected_count} culture sheets")
    print(f"🌺 Species covered: {', '.join([r['species'] for r in results])}")
    
    return results

if __name__ == "__main__":
    run_baker_import()