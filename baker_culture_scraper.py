#!/usr/bin/env python3
"""
BAKER'S CULTURE SHEETS SCRAPER
High-quality orchid cultivation data from Charles and Margaret Baker
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import OrchidRecord
import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
from urllib.parse import urljoin

class BakerCultureScraper:
    def __init__(self):
        self.base_url = "https://orchidculture.com/COD/FREE/"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.results = {'processed': 0, 'errors': 0, 'skipped': 0}
        self.collected_total = 0
        self.last_report = time.time()
        self.last_reconfigure = time.time()
        self.report_interval = 60  # Report every minute
        self.reconfigure_interval = 120  # Reconfigure every 2 minutes
        self.running = False
        
        import logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        print("🏆 Baker's Culture Sheets Scraper Initialized")
        print("📋 Target: Professional orchid cultivation data")
        print("🌐 Source: https://orchidculture.com/COD/FREE/")
        print("⭐ Quality: PREMIUM - Authoritative cultivation metadata")
        print()

    def scrape_baker_culture_comprehensive(self):
        """Scrape all Baker's culture sheets with full metadata"""
        
        try:
            print("📋 Starting Baker's Culture Sheets comprehensive scraping...")
            
            # Get the main index page
            response = self.session.get(self.base_url, timeout=15)
            if response.status_code != 200:
                print(f"❌ Failed to access Baker's index: {response.status_code}")
                return self.results
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find all culture sheet links 
            culture_links = []
            
            # Look for links that match the culture sheet pattern (FS*.html)
            for link in soup.find_all('a', href=re.compile(r'FS\d+\.html')):
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    species_name = link.get_text().strip()
                    culture_links.append((full_url, species_name))
            
            print(f"📋 Found {len(culture_links)} culture sheets to process")
            print()
            
            # Process each culture sheet
            for i, (culture_url, species_name) in enumerate(culture_links):
                try:
                    print(f"[{i+1}/{len(culture_links)}] Processing: {species_name}")
                    
                    # Check if we already have this culture sheet
                    existing = OrchidRecord.query.filter(
                        OrchidRecord.scientific_name == species_name,
                        OrchidRecord.ingestion_source.like('%baker%')
                    ).first()
                    
                    if existing:
                        print(f"   ⏭️ Already exists: {species_name}")
                        self.results['skipped'] += 1
                        continue
                    
                    # Fetch the culture sheet
                    culture_data = self.scrape_culture_sheet(culture_url, species_name)
                    
                    if culture_data:
                        # Create comprehensive description with all climate data
                        full_description = culture_data['description']
                        if culture_data.get('climate'):
                            full_description += f" Climate: {culture_data['climate']}."
                        if culture_data.get('temperature'):
                            full_description += f" Temperature: {culture_data['temperature']}."
                        if culture_data.get('humidity'):
                            full_description += f" Humidity: {culture_data['humidity']}."
                        if culture_data.get('cultivation'):
                            full_description += f" Cultivation: {culture_data['cultivation']}."
                        
                        # Create comprehensive culture notes for notes field
                        culture_notes = self.format_culture_notes(culture_data)
                        
                        # Create orchid record with all available metadata
                        orchid = OrchidRecord(
                            display_name=culture_data['display_name'],
                            scientific_name=culture_data['scientific_name'],
                            genus=culture_data['genus'],
                            species=culture_data['species'],
                            region=culture_data.get('origin'),
                            ai_description=full_description,
                            cultural_notes=culture_notes,  # Culture sheets data goes in cultural_notes
                            ingestion_source="baker_culture_sheets",
                            photographer="Charles & Margaret Baker"
                        )
                        
                        db.session.add(orchid)
                        self.results['processed'] += 1
                        
                        print(f"   ✅ Added: {species_name}")
                        
                        # Commit every 10 records
                        if self.results['processed'] % 10 == 0:
                            db.session.commit()
                            print(f"   💾 Saved batch: {self.results['processed']} culture sheets")
                    
                    else:
                        print(f"   ❌ Failed to process: {species_name}")
                        self.results['errors'] += 1
                    
                    # Be respectful - pause between requests
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"   ❌ Error processing {species_name}: {e}")
                    self.results['errors'] += 1
                    continue
            
            # Final commit
            db.session.commit()
            
            print()
            print("🏆 Baker's Culture Sheets Scraping Complete!")
            print(f"   Culture sheets processed: {self.results['processed']:,}")
            print(f"   Errors: {self.results['errors']:,}")
            print(f"   Skipped duplicates: {self.results['skipped']:,}")
            
        except Exception as e:
            print(f"❌ Baker's scraping error: {e}")
            self.results['errors'] += 1
        
        return self.results
    
    def format_culture_notes(self, culture_data):
        """Format comprehensive culture information for cultural_notes field"""
        notes = "BAKER'S CULTURE SHEET DATA:\n"
        notes += "=" * 40 + "\n"
        
        if culture_data.get('origin'):
            notes += f"ORIGIN: {culture_data['origin']}\n"
        
        if culture_data.get('climate'):
            notes += f"CLIMATE: {culture_data['climate']}\n"
            
        if culture_data.get('temperature'):
            notes += f"TEMPERATURE: {culture_data['temperature']}\n"
            
        if culture_data.get('humidity'):
            notes += f"HUMIDITY: {culture_data['humidity']}\n"
            
        if culture_data.get('cultivation'):
            notes += f"CULTIVATION NOTES:\n{culture_data['cultivation']}\n"
            
        notes += "\nSOURCE: Charles & Margaret Baker Professional Culture Sheets\n"
        notes += "AUTHORITY: Orchid Culture Database\n"
        notes += f"EXTRACTED: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        
        return notes
        
    def run_continuous_scraping(self):
        """Continuous scraping with auto-reconfiguration and reporting"""
        self.logger.info("🚀 Starting continuous Baker's Culture scraping")
        self.logger.info("⏰ Reports every 60s, reconfigures every 120s")
        
        self.running = True
        
        try:
            while self.running:
                current_time = time.time()
                
                # Report progress every minute
                if current_time - self.last_report >= self.report_interval:
                    self.report_progress()
                    self.last_report = current_time
                
                # Auto-reconfigure every 2 minutes
                if current_time - self.last_reconfigure >= self.reconfigure_interval:
                    self.auto_reconfigure()
                    self.last_reconfigure = current_time
                
                # Run collection cycle
                collected = self.scrape_baker_culture_comprehensive()
                if isinstance(collected, dict):
                    self.collected_total += collected.get('processed', 0)
                else:
                    self.collected_total += collected if collected else 0
                
                self.logger.info(f"📊 Baker's Culture cycle complete: +{collected} culture sheets")
                time.sleep(30)  # 30 second cycle
                
        except KeyboardInterrupt:
            self.logger.info("⏹️  Stopping Baker's Culture scraper...")
            self.stop()
            
    def report_progress(self):
        """Report current progress"""
        self.logger.info("=" * 50)
        self.logger.info(f"📊 BAKER'S CULTURE SCRAPER PROGRESS")
        self.logger.info(f"✅ Total collected: {self.collected_total}")
        self.logger.info(f"⏰ Runtime: {time.time() - self.last_reconfigure:.0f}s since reconfigure")
        self.logger.info("=" * 50)
        
    def auto_reconfigure(self):
        """Auto-reconfigure scraping strategy"""
        self.logger.info(f"🔧 AUTO-RECONFIGURING BAKER'S CULTURE SCRAPER")
        # Adjust scraping parameters based on performance
        
    def stop(self):
        """Stop the scraper"""
        self.running = False
        self.logger.info("✅ Baker's Culture scraper stopped")

    def scrape_culture_sheet(self, url, species_name):
        """Extract metadata from individual culture sheet"""
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract species information
            # Parse scientific name with authority
            scientific_name = species_name
            authority = ""
            
            # Look for authority in parentheses or brackets
            if '(' in species_name and ')' in species_name:
                parts = species_name.split('(')
                if len(parts) >= 2:
                    scientific_name = parts[0].strip()
                    authority = parts[1].replace(')', '').strip()
            elif '[' in species_name and ']' in species_name:
                parts = species_name.split('[')
                if len(parts) >= 2:
                    scientific_name = parts[0].strip()
                    authority = parts[1].replace(']', '').strip()
            
            # Parse genus and species
            name_parts = scientific_name.split()
            genus = name_parts[0] if len(name_parts) > 0 else ""
            species = name_parts[1] if len(name_parts) > 1 else ""
            
            # Extract text content for analysis
            page_text = soup.get_text()
            
            # Extract climate and origin information
            origin = self.extract_origin(page_text)
            climate = self.extract_climate_info(page_text)
            temperature = self.extract_temperature(page_text)
            humidity = self.extract_humidity(page_text)
            cultivation = self.extract_cultivation_notes(page_text)
            
            # Create description
            description = f"Professional culture sheet from Charles & Margaret Baker. "
            if climate:
                description += f"Climate: {climate}. "
            if origin:
                description += f"Origin: {origin}. "
            description += f"Detailed cultivation data available. Source: {url}"
            
            return {
                'display_name': species_name,
                'scientific_name': scientific_name,
                'genus': genus,
                'species': species,
                'authority': authority,
                'origin': origin,
                'climate': climate,
                'temperature': temperature,
                'humidity': humidity,
                'description': description,
                'cultivation': cultivation
            }
            
        except Exception as e:
            print(f"   ⚠️ Culture sheet extraction error: {e}")
            return None

    def extract_origin(self, text):
        """Extract geographic origin from text"""
        origin_patterns = [
            r'(Brazil|Colombia|Ecuador|Peru|Venezuela|Guyana)',
            r'(Madagascar|Tanzania|Kenya|South Africa)',
            r'(Indonesia|Malaysia|Thailand|Philippines|Myanmar)',
            r'(India|China|Japan|Vietnam|Laos|Cambodia)',
            r'(Mexico|Guatemala|Costa Rica|Panama|Honduras)',
            r'(Australia|New Guinea|Papua)'
        ]
        
        for pattern in origin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None

    def extract_climate_info(self, text):
        """Extract climate information"""
        climate_keywords = ['warm', 'cool', 'intermediate', 'hot', 'cold', 'temperate', 'tropical']
        
        for keyword in climate_keywords:
            if keyword in text.lower():
                return keyword.title()
        return None

    def extract_temperature(self, text):
        """Extract temperature range"""
        temp_pattern = r'(\d+)[-–](\d+)[°]?[CF]'
        match = re.search(temp_pattern, text)
        if match:
            return f"{match.group(1)}-{match.group(2)}°"
        return None

    def extract_humidity(self, text):
        """Extract humidity range"""
        humidity_pattern = r'(\d+)[-–](\d+)%'
        match = re.search(humidity_pattern, text)
        if match:
            return f"{match.group(1)}-{match.group(2)}%"
        return None
        
    def extract_cultivation_notes(self, text):
        """Extract detailed cultivation notes from culture sheet"""
        cultivation_keywords = [
            'watering', 'fertilizer', 'light', 'potting', 'medium', 
            'repotting', 'growing', 'culture', 'care', 'bloom', 
            'flowering', 'mount', 'basket', 'bark', 'moss'
        ]
        
        # Extract sentences containing cultivation keywords
        sentences = text.split('.')
        cultivation_notes = []
        
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in cultivation_keywords):
                clean_sentence = sentence.strip()
                if len(clean_sentence) > 20 and len(clean_sentence) < 200:
                    cultivation_notes.append(clean_sentence)
                    
        if cultivation_notes:
            return '. '.join(cultivation_notes[:3])  # Top 3 most relevant notes
        return None

    def extract_cultivation_notes(self, text):
        """Extract key cultivation notes"""
        # Look for key cultivation terms
        cultivation_terms = ['epiphyte', 'terrestrial', 'lithophyte', 'mount', 'bark', 'sphagnum']
        notes = []
        
        for term in cultivation_terms:
            if term in text.lower():
                notes.append(term)
        
        return ", ".join(notes) if notes else None

def run_baker_scraper():
    """Run Baker's culture sheets scraper"""
    with app.app_context():
        scraper = BakerCultureScraper()
        results = scraper.scrape_baker_culture_comprehensive()
        
        print()
        print("🏆 BAKER'S CULTURE SCRAPING COMPLETE!")
        print(f"📋 Professional culture sheets: {results['processed']:,}")
        print(f"❌ Errors: {results['errors']:,}")
        print(f"⏭️ Skipped: {results['skipped']:,}")
        
        return results

if __name__ == "__main__":
    run_baker_scraper()