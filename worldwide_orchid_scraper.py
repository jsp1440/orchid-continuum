"""
Worldwide Major Orchid Database Scraper
Collects orchid data from major botanical gardens and research institutions worldwide
"""

import requests
import time
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from datetime import datetime
import logging
from typing import Dict, List, Optional

from models import OrchidRecord, db
from filename_parser import extract_metadata_from_image, parse_orchid_filename

class WorldwideOrchidScraper:
    """Scraper for major worldwide orchid databases and botanical gardens"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Orchid Database Research) Botanical Education'
        })
        
        # Major worldwide sources discovered
        self.sources = {
            'kew_gardens': {
                'name': 'Royal Botanic Gardens Kew',
                'base_url': 'https://www.kew.org',
                'powo_url': 'http://www.plantsoftheworldonline.org',
                'collection_size': '8,500,000+ items',
                'orchid_focus': '600+ IUCN Red List species'
            },
            'singapore_botanical': {
                'name': 'Singapore Botanic Gardens',
                'base_url': 'https://www.nparks.gov.sg/sbg',
                'collection_size': '1,000+ species, 2,000+ hybrids',
                'status': 'UNESCO World Heritage Site'
            },
            'atlanta_botanical': {
                'name': 'Atlanta Botanical Garden',
                'base_url': 'https://atlantabg.org',
                'ranking': '2nd globally for ex situ orchid taxa',
                'specialty': 'Rare and endangered orchids under glass'
            },
            'missouri_botanical': {
                'name': 'Missouri Botanical Garden',
                'base_url': 'https://www.missouribotanicalgarden.org',
                'collection_size': '5,000+ plants, 700+ unique kinds',
                'conservation_focus': 'Threatened and endangered species'
            },
            'chicago_botanic': {
                'name': 'Chicago Botanic Garden',
                'base_url': 'https://www.chicagobotanic.org',
                'specialty': 'Annual orchid exhibitions'
            },
            'us_botanic': {
                'name': 'U.S. Botanic Garden & Smithsonian',
                'base_url': 'https://www.usbg.gov',
                'specialty': 'Smithsonian collaboration, extensive exhibitions'
            }
        }
        
        print("🌍 Worldwide Orchid Database Scraper Initialized")
        print(f"🏛️ Target: {len(self.sources)} major botanical institutions")
        for key, source in self.sources.items():
            print(f"   • {source['name']}: {source.get('collection_size', 'Major collection')}")
    
    def scrape_all_worldwide_sources(self):
        """Comprehensive scraping of all worldwide orchid sources"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        print("\n🔍 COMPREHENSIVE WORLDWIDE ORCHID SCRAPING")
        print("=" * 60)
        
        # Kew Gardens - POWO Database
        print("\n🇬🇧 Royal Botanic Gardens Kew")
        kew_results = self.scrape_kew_powo()
        results['processed'] += kew_results['processed']
        results['errors'] += kew_results['errors']
        results['skipped'] += kew_results['skipped']
        
        # Singapore Botanic Gardens
        print("\n🇸🇬 Singapore Botanic Gardens")
        singapore_results = self.scrape_singapore_botanical()
        results['processed'] += singapore_results['processed']
        results['errors'] += singapore_results['errors']
        results['skipped'] += singapore_results['skipped']
        
        # Atlanta Botanical Garden
        print("\n🇺🇸 Atlanta Botanical Garden")
        atlanta_results = self.scrape_atlanta_botanical()
        results['processed'] += atlanta_results['processed']
        results['errors'] += atlanta_results['errors']
        results['skipped'] += atlanta_results['skipped']
        
        # Missouri Botanical Garden
        print("\n🇺🇸 Missouri Botanical Garden")
        missouri_results = self.scrape_missouri_botanical()
        results['processed'] += missouri_results['processed']
        results['errors'] += missouri_results['errors']
        results['skipped'] += missouri_results['skipped']
        
        return results
    
    def scrape_kew_powo(self):
        """Scrape Kew Gardens Plants of the World Online (POWO) for orchid data"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # POWO has an API and search interface for monocotyledons including orchids
            powo_search_url = "http://www.plantsoftheworldonline.org/search"
            
            # Search for major orchid genera
            orchid_genera = [
                'Orchis', 'Ophrys', 'Cypripedium', 'Paphiopedilum', 'Phragmipedium',
                'Cattleya', 'Laelia', 'Epidendrum', 'Dendrobium', 'Bulbophyllum',
                'Oncidium', 'Cymbidium', 'Vanda', 'Phalaenopsis', 'Masdevallia'
            ]
            
            for genus in orchid_genera[:5]:  # Start with first 5 genera
                try:
                    print(f"   🔍 Searching POWO for {genus}...")
                    search_params = {
                        'q': genus,
                        'f': 'monocots'  # Filter for monocotyledons
                    }
                    
                    response = self.session.get(powo_search_url, params=search_params, timeout=15)
                    if response.status_code == 200:
                        genus_results = self.parse_powo_results(response.content, genus)
                        results['processed'] += genus_results['processed']
                        results['errors'] += genus_results['errors']
                        results['skipped'] += genus_results['skipped']
                    
                    time.sleep(2)  # Respectful delay
                    
                except Exception as e:
                    print(f"     ❌ Error searching {genus}: {e}")
                    results['errors'] += 1
        
        except Exception as e:
            print(f"   ❌ Error accessing Kew POWO: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_singapore_botanical(self):
        """Scrape Singapore Botanic Gardens orchid data"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Singapore Botanic Gardens National Orchid Garden
            orchid_garden_url = "https://www.nparks.gov.sg/sbg/our-gardens/tyersall-entrance/national-orchid-garden"
            
            response = self.session.get(orchid_garden_url, timeout=15)
            if response.status_code == 200:
                singapore_results = self.parse_singapore_orchids(response.content)
                results['processed'] += singapore_results['processed']
                results['errors'] += singapore_results['errors']
                results['skipped'] += singapore_results['skipped']
        
        except Exception as e:
            print(f"   ❌ Error accessing Singapore Botanic Gardens: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_atlanta_botanical(self):
        """Scrape Atlanta Botanical Garden orchid collection"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Atlanta Botanical Garden orchid collection
            atlanta_url = "https://atlantabg.org/plan-your-visit/atlanta-garden-calendar/orchid-daze/"
            
            response = self.session.get(atlanta_url, timeout=15)
            if response.status_code == 200:
                atlanta_results = self.parse_atlanta_orchids(response.content)
                results['processed'] += atlanta_results['processed']
                results['errors'] += atlanta_results['errors']
                results['skipped'] += atlanta_results['skipped']
        
        except Exception as e:
            print(f"   ❌ Error accessing Atlanta Botanical Garden: {e}")
            results['errors'] += 1
        
        return results
    
    def scrape_missouri_botanical(self):
        """Scrape Missouri Botanical Garden orchid collection"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            # Missouri Botanical Garden orchid show and collection info
            missouri_url = "https://www.missouribotanicalgarden.org/orchid-show-1560"
            
            response = self.session.get(missouri_url, timeout=15)
            if response.status_code == 200:
                missouri_results = self.parse_missouri_orchids(response.content)
                results['processed'] += missouri_results['processed']
                results['errors'] += missouri_results['errors']
                results['skipped'] += missouri_results['skipped']
        
        except Exception as e:
            print(f"   ❌ Error accessing Missouri Botanical Garden: {e}")
            results['errors'] += 1
        
        return results
    
    def parse_powo_results(self, content, genus):
        """Parse Kew POWO search results for orchid species"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for species entries in POWO format
            species_links = soup.find_all('a', href=True)
            for link in species_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for scientific names
                if genus.lower() in text.lower() and len(text.split()) >= 2:
                    species_data = {
                        'name': text,
                        'genus': genus,
                        'source': 'Royal Botanic Gardens Kew',
                        'ingestion_source': 'kew_powo',
                        'source_url': f"http://www.plantsoftheworldonline.org{href}" if href.startswith('/') else href,
                        'database_notes': 'From Kew Gardens POWO - 250 years of botanical knowledge'
                    }
                    
                    if self.save_worldwide_orchid(species_data):
                        results['processed'] += 1
                    else:
                        results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error parsing POWO results: {e}")
            results['errors'] += 1
        
        return results
    
    def parse_singapore_orchids(self, content):
        """Parse Singapore Botanic Gardens orchid data"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract orchid information from the page
            text_content = soup.get_text()
            
            # Look for scientific names mentioned
            scientific_pattern = r'\b([A-Z][a-z]+)\s+([a-z]+(?:\s+[a-z]+)*)\b'
            matches = re.findall(scientific_pattern, text_content)
            
            for genus, species in matches:
                if genus in ['Dendrobium', 'Vanda', 'Oncidium', 'Phalaenopsis', 'Cattleya']:
                    species_data = {
                        'name': f"{genus} {species}",
                        'genus': genus,
                        'species': species,
                        'source': 'Singapore Botanic Gardens',
                        'ingestion_source': 'singapore_botanical',
                        'source_url': 'https://www.nparks.gov.sg/sbg/our-gardens/tyersall-entrance/national-orchid-garden',
                        'database_notes': 'UNESCO World Heritage Site - National Orchid Garden',
                        'region': 'Southeast Asia'
                    }
                    
                    if self.save_worldwide_orchid(species_data):
                        results['processed'] += 1
                    else:
                        results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error parsing Singapore data: {e}")
            results['errors'] += 1
        
        return results
    
    def parse_atlanta_orchids(self, content):
        """Parse Atlanta Botanical Garden orchid collection"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract orchid information from Atlanta's collection
            text_content = soup.get_text()
            
            # Common orchid genera mentioned in their collection
            atlanta_genera = ['Phalaenopsis', 'Cattleya', 'Dendrobium', 'Paphiopedilum', 'Oncidium']
            
            for genus in atlanta_genera:
                if genus.lower() in text_content.lower():
                    # Create entry for this genus representation
                    species_data = {
                        'name': f"{genus} species collection",
                        'genus': genus,
                        'source': 'Atlanta Botanical Garden',
                        'ingestion_source': 'atlanta_botanical',
                        'source_url': 'https://atlantabg.org/plan-your-visit/atlanta-garden-calendar/orchid-daze/',
                        'database_notes': 'Ranks 2nd globally for ex situ orchid taxa - rare and endangered species under glass',
                        'region': 'North America (Conservation Collection)'
                    }
                    
                    if self.save_worldwide_orchid(species_data):
                        results['processed'] += 1
                    else:
                        results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error parsing Atlanta data: {e}")
            results['errors'] += 1
        
        return results
    
    def parse_missouri_orchids(self, content):
        """Parse Missouri Botanical Garden orchid collection"""
        results = {'processed': 0, 'errors': 0, 'skipped': 0}
        
        try:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract information about their 5,000+ plant collection
            text_content = soup.get_text()
            
            # Common genera in Missouri's collection
            missouri_genera = ['Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium', 'Cymbidium']
            
            for genus in missouri_genera:
                if genus.lower() in text_content.lower():
                    species_data = {
                        'name': f"{genus} collection specimens",
                        'genus': genus,
                        'source': 'Missouri Botanical Garden',
                        'ingestion_source': 'missouri_botanical',
                        'source_url': 'https://www.missouribotanicalgarden.org/orchid-show-1560',
                        'database_notes': '5,000+ individual plants, 700+ unique kinds - conservation focus on threatened species',
                        'region': 'North America (Research Collection)'
                    }
                    
                    if self.save_worldwide_orchid(species_data):
                        results['processed'] += 1
                    else:
                        results['skipped'] += 1
        
        except Exception as e:
            print(f"     ❌ Error parsing Missouri data: {e}")
            results['errors'] += 1
        
        return results
    
    def save_worldwide_orchid(self, orchid_data):
        """Save orchid data from worldwide sources to database"""
        try:
            # Check if this orchid already exists
            existing = OrchidRecord.query.filter_by(
                scientific_name=orchid_data['name'],
                ingestion_source=orchid_data['ingestion_source']
            ).first()
            
            if existing:
                return False  # Skip duplicates
            
            # Create new orchid record (fixed schema compatibility)
            orchid = OrchidRecord(
                scientific_name=orchid_data['name'],
                display_name=orchid_data['name'],
                genus=orchid_data.get('genus'),
                species=orchid_data.get('species'),
                photographer=orchid_data.get('source', 'Unknown'),
                ingestion_source=orchid_data['ingestion_source'],
                ai_description=orchid_data.get('database_notes'),
                region=orchid_data.get('region'),
                created_at=datetime.now()
            )
            
            db.session.add(orchid)
            db.session.commit()
            return True
            
        except Exception as e:
            print(f"Error saving worldwide orchid {orchid_data['name']}: {e}")
            db.session.rollback()
            return False