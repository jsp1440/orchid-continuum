#!/usr/bin/env python3
"""
Complete Gary Yong Gee Collection System
=======================================
Comprehensive collection of ALL orchid data from Gary's authorized collection
Based on the IOSPE safe ETL template provided by user
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
from urllib.parse import urljoin, quote
from app import app, db
from models import OrchidRecord

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompleteGaryCollectionSystem:
    """Complete collection system for Gary Yong Gee's orchid database"""
    
    def __init__(self):
        self.base_url = "https://orchids.yonggee.name"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'FCOS-OrchidContinuum-SafeETL/2.0 (contact: webmaster@fcos.org)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        
        self.collected_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        # All known orchid genera - comprehensive list for complete collection
        self.orchid_genera = [
            'Aa', 'Abdominea', 'Acampe', 'Acanthephippium', 'Aceratorchis', 'Acianthus',
            'Acineta', 'Acriopsis', 'Acrorchis', 'Ada', 'Adenoncos', 'Aerangis',
            'Aeranthes', 'Aerides', 'Aganisia', 'Agrostophyllum', 'Alamania', 'Amesiella',
            'Amparoa', 'Anacamptis', 'Ancistrochilus', 'Angraecum', 'Anguloa', 'Ansellia',
            'Arachnanthe', 'Arethusa', 'Armodorum', 'Arundina', 'Ascocentrum', 'Ascocenda',
            'Ascofinetia', 'Ascoglossum', 'Barkeria', 'Bletia', 'Bletilla', 'Brassavola',
            'Brassia', 'Bulbophyllum', 'Calanthe', 'Calypso', 'Catasetum', 'Cattleya',
            'Cephalanthera', 'Ceratostylis', 'Chondrorhyncha', 'Christensonia', 'Chysis',
            'Cirrhaea', 'Cleisostoma', 'Cochlioda', 'Coelogyne', 'Comparettia', 'Coryanthes',
            'Cycnoches', 'Cymbidium', 'Cypripedium', 'Cyrtopodium', 'Cyrtorchis', 'Dactylorhiza',
            'Dendrobium', 'Dendrochilum', 'Diaphananthe', 'Disa', 'Dossinia', 'Dracula',
            'Dracaena', 'Encyclia', 'Epidendrum', 'Epigeneium', 'Eria', 'Esmeralda',
            'Eulophia', 'Galeandra', 'Gongora', 'Goodyera', 'Grammatophyllum', 'Grobya',
            'Guarianthe', 'Habenaria', 'Haraella', 'Houlletia', 'Huntleya', 'Ionopsis',
            'Isochilus', 'Jumellea', 'Kefersteinia', 'Laelia', 'Laeliocattleya', 'Lepanthes',
            'Liparis', 'Ludisia', 'Luisia', 'Lycaste', 'Macodes', 'Masdevallia',
            'Maxillaria', 'Mediocalcar', 'Miltonia', 'Miltoniopsis', 'Mormodes', 'Mystacidium',
            'Neofinetia', 'Nepenthes', 'Oberonia', 'Odontoglossum', 'Oeceoclades', 'Oncidium',
            'Orchis', 'Ornithocephalus', 'Pabstiella', 'Paphiopedilum', 'Paraphalaenopsis',
            'Peristeria', 'Pescatorea', 'Phalaenopsis', 'Pholidota', 'Phragmipedium', 'Platanthera',
            'Plectorrhiza', 'Pleione', 'Pleurothallis', 'Podangis', 'Polystachya', 'Porroglossum',
            'Promenaea', 'Prosthechea', 'Psychopsis', 'Pterostylis', 'Rangaeris', 'Renanthera',
            'Restrepia', 'Restrepiella', 'Rhynchostylis', 'Robiquetia', 'Rodriguezia', 'Rossioglossum',
            'Saccolabium', 'Sarcochilus', 'Scaphosepalum', 'Schoenorchis', 'Sedirea', 'Sobralia',
            'Sophronitis', 'Spathoglottis', 'Spiranthes', 'Stanhopea', 'Stelis', 'Stenorrhynchos',
            'Tolumnia', 'Trichocentrum', 'Trichoglottis', 'Tridactyle', 'Tuberolabium', 'Vanda',
            'Vandopsis', 'Vanilla', 'Warczewiczella', 'Warrea', 'Xylobium', 'Zygopetalum'
        ]
        
        # Priority genera (user has photos for these)
        self.priority_genera = [
            'Bulbophyllum', 'Dendrobium', 'Cattleya', 'Phalaenopsis', 'Oncidium', 'Paphiopedilum',
            'Cymbidium', 'Vanda', 'Masdevallia', 'Epidendrum', 'Lycaste', 'Brassia', 'Miltonia',
            'Zygopetalum', 'Maxillaria', 'Laelia', 'Angraecum', 'Aerangis', 'Catasetum', 'Vanilla'
        ]

    def collect_complete_gary_database(self):
        """Collect the complete Gary Yong Gee orchid database"""
        logger.info("🌺 STARTING COMPLETE GARY YONG GEE COLLECTION")
        logger.info("=" * 80)
        
        with app.app_context():
            # Start with priority genera first
            logger.info(f"🎯 Phase 1: Priority genera ({len(self.priority_genera)} genera)")
            for i, genus in enumerate(self.priority_genera):
                logger.info(f"📂 [{i+1}/{len(self.priority_genera)}] Collecting {genus}")
                self.collect_genus_complete(genus)
                time.sleep(3)  # Respectful delay
            
            # Then collect all remaining genera
            remaining_genera = [g for g in self.orchid_genera if g not in self.priority_genera]
            logger.info(f"🌍 Phase 2: Complete collection ({len(remaining_genera)} additional genera)")
            
            for i, genus in enumerate(remaining_genera):
                logger.info(f"📂 [{i+1}/{len(remaining_genera)}] Collecting {genus}")
                self.collect_genus_complete(genus)
                time.sleep(2)  # Slightly faster for non-priority
            
            logger.info(f"✅ COMPLETE COLLECTION FINISHED")
            logger.info(f"   Collected: {self.collected_count} orchids")
            logger.info(f"   Errors: {self.error_count}")
            logger.info(f"   Skipped: {self.skipped_count}")
            
            return {
                'collected': self.collected_count,
                'errors': self.error_count,
                'skipped': self.skipped_count
            }

    def collect_genus_complete(self, genus_name):
        """Collect all species from a genus with complete metadata"""
        try:
            # Get genus page
            genus_url = f"{self.base_url}/genera/{genus_name.lower()}"
            response = self.session.get(genus_url, timeout=20)
            
            if response.status_code != 200:
                logger.warning(f"⚠️ Cannot access {genus_name} - Status: {response.status_code}")
                self.error_count += 1
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract genus-level information
            genus_data = self.extract_genus_metadata(soup, genus_name)
            
            # Find all species links
            species_links = self.find_all_species_links(soup, genus_name)
            logger.info(f"   Found {len(species_links)} species in {genus_name}")
            
            # Collect each species
            for species_info in species_links:
                try:
                    self.collect_single_species(species_info, genus_data)
                    time.sleep(1)  # Brief delay between species
                except Exception as e:
                    logger.error(f"❌ Error collecting {species_info.get('name', 'unknown')}: {e}")
                    self.error_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error collecting genus {genus_name}: {e}")
            self.error_count += 1

    def extract_genus_metadata(self, soup, genus_name):
        """Extract comprehensive genus-level metadata"""
        genus_data = {
            'genus': genus_name,
            'author': '',
            'etymology': '',
            'distribution': '',
            'characteristics': '',
            'subfamily': '',
            'tribe': '',
            'subtribe': '',
            'type_species': '',
            'abbreviation': '',
            'synonyms': [],
            'references': []
        }
        
        # Extract from various HTML structures
        text_content = soup.get_text()
        
        # Look for author information
        author_match = re.search(rf'{genus_name}\s+([A-Z][a-z]+\.?(?:\s+&?\s+[A-Z][a-z]+\.?)*)', text_content)
        if author_match:
            genus_data['author'] = author_match.group(1)
        
        # Look for etymology
        if 'etymology' in text_content.lower() or 'named' in text_content.lower():
            etymology_match = re.search(r'etymology:?\s*([^.]+\.)', text_content, re.IGNORECASE)
            if etymology_match:
                genus_data['etymology'] = etymology_match.group(1).strip()
        
        # Look for distribution
        if 'distribution' in text_content.lower() or 'found' in text_content.lower():
            dist_match = re.search(r'distribution:?\s*([^.]+\.)', text_content, re.IGNORECASE)
            if dist_match:
                genus_data['distribution'] = dist_match.group(1).strip()
        
        # Look for abbreviation
        abbrev_match = re.search(r'abbreviation:?\s*([A-Z][a-z]*\.?)', text_content, re.IGNORECASE)
        if abbrev_match:
            genus_data['abbreviation'] = abbrev_match.group(1)
        
        return genus_data

    def find_all_species_links(self, soup, genus_name):
        """Find all species links using multiple strategies"""
        species_links = []
        
        # Strategy 1: Look for direct species links
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            text = link.get_text(strip=True)
            
            # Match species patterns
            if (href and text and 
                genus_name.lower() in text.lower() and
                href.endswith('.htm') or href.endswith('.html')):
                
                species_links.append({
                    'name': text,
                    'url': urljoin(self.base_url, href),
                    'href': href
                })
        
        # Strategy 2: Look for species list sections
        species_sections = soup.find_all(['ul', 'ol', 'div'], class_=re.compile(r'species|list', re.I))
        for section in species_sections:
            for link in section.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text(strip=True)
                
                if href and text and genus_name.lower() in text.lower():
                    species_links.append({
                        'name': text,
                        'url': urljoin(self.base_url, href),
                        'href': href
                    })
        
        # Strategy 3: Look for table rows with species
        tables = soup.find_all('table')
        for table in tables:
            for row in table.find_all('tr'):
                cells = row.find_all(['td', 'th'])
                for cell in cells:
                    link = cell.find('a', href=True)
                    if link:
                        href = link.get('href')
                        text = link.get_text(strip=True)
                        
                        if href and text and genus_name.lower() in text.lower():
                            species_links.append({
                                'name': text,
                                'url': urljoin(self.base_url, href),
                                'href': href
                            })
        
        # Remove duplicates
        seen_urls = set()
        unique_links = []
        for link in species_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        return unique_links

    def collect_single_species(self, species_info, genus_data):
        """Collect complete data for a single species"""
        try:
            # Check if already exists
            species_name = species_info['name']
            existing = OrchidRecord.query.filter_by(
                display_name=species_name,
                ingestion_source='gary_complete_collection'
            ).first()
            
            if existing:
                logger.debug(f"⏭️ Skipping existing: {species_name}")
                self.skipped_count += 1
                return
            
            # Get species page
            response = self.session.get(species_info['url'], timeout=15)
            if response.status_code != 200:
                logger.warning(f"⚠️ Cannot access {species_name} - Status: {response.status_code}")
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract complete species metadata using IOSPE-style safe extraction
            species_data = self.extract_species_metadata_safe(soup, species_name, genus_data)
            
            # Create orchid record
            orchid_record = OrchidRecord(
                display_name=species_data['display_name'],
                scientific_name=species_data['scientific_name'],
                genus=species_data['genus'],
                species=species_data['species'],
                author=species_data['author'],
                
                # Geographic data
                region=species_data['region'],
                native_habitat=species_data['habitat'],
                country=species_data['country'],
                
                # Cultural data
                growth_habit=species_data['growth_habit'],
                climate_preference=species_data['temperature'],
                bloom_time=species_data['bloom_season'],
                
                # Source tracking
                ingestion_source='gary_complete_collection',
                image_source='Gary Yong Gee Orchids',
                image_url=species_data['image_url'],
                
                # Metadata
                ai_description=f"Complete botanical data from Gary Yong Gee: {species_data['characteristics'][:200]}",
                cultural_notes=species_data['cultural_notes'],
                
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(orchid_record)
            db.session.commit()
            
            logger.info(f"✅ Collected: {species_data['display_name']}")
            self.collected_count += 1
            
        except Exception as e:
            logger.error(f"❌ Error collecting species {species_info.get('name', 'unknown')}: {e}")
            self.error_count += 1

    def extract_species_metadata_safe(self, soup, species_name, genus_data):
        """Extract species metadata using safe IOSPE-style extraction"""
        # Initialize with safe defaults
        species_data = {
            'display_name': species_name,
            'scientific_name': species_name,
            'genus': genus_data['genus'],
            'species': '',
            'author': genus_data.get('author', ''),
            'abbreviation': genus_data.get('abbreviation', ''),
            'synonyms': '',
            'region': genus_data.get('distribution', ''),
            'altitude_meters': '',
            'habitat': '',
            'bloom_season': '',
            'growth_habit': '',
            'temperature': '',
            'characteristics': '',
            'cultural_notes': '',
            'image_url': '',
            'country': ''
        }
        
        # Parse scientific name
        name_parts = species_name.split()
        if len(name_parts) >= 2:
            species_data['genus'] = name_parts[0]
            species_data['species'] = name_parts[1]
            species_data['scientific_name'] = f"{name_parts[0]} {name_parts[1]}"
        
        # Extract text content for pattern matching
        text_content = soup.get_text()
        
        # Safe extraction patterns (facts only, no copyrighted content)
        patterns = {
            'author': rf'{re.escape(species_name)}\s+([A-Z][a-z]+\.?(?:\s+&?\s+[A-Z][a-z]+\.?)*)',
            'altitude': r'altitude:?\s*(\d+[^\d]*m(?:eters?)?)',
            'habitat': r'habitat:?\s*([^.]+\.)',
            'bloom_season': r'bloom(?:ing)?:?\s*([^.]+\.)',
            'temperature': r'temperature:?\s*([^.]+\.)',
            'distribution': r'distribution:?\s*([^.]+\.)',
            'synonyms': r'synonym(?:s)?:?\s*([^.]+\.)'
        }
        
        for field, pattern in patterns.items():
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match and field in species_data:
                species_data[field] = match.group(1).strip()
        
        # Extract image URL (first image found)
        img_tag = soup.find('img')
        if img_tag and img_tag.get('src'):
            img_src = img_tag.get('src')
            if not img_src.startswith('http'):
                img_src = urljoin(self.base_url, img_src)
            species_data['image_url'] = img_src
        
        # Determine country from region/distribution
        if species_data['region']:
            region_text = species_data['region'].lower()
            countries = {
                'indonesia': 'Indonesia', 'malaysia': 'Malaysia', 'thailand': 'Thailand',
                'philippines': 'Philippines', 'australia': 'Australia', 'ecuador': 'Ecuador',
                'brazil': 'Brazil', 'colombia': 'Colombia', 'peru': 'Peru', 'china': 'China',
                'india': 'India', 'madagascar': 'Madagascar', 'tanzania': 'Tanzania'
            }
            
            for country_key, country_name in countries.items():
                if country_key in region_text:
                    species_data['country'] = country_name
                    break
        
        # Set growth habit based on genus (safe assumption)
        genus_habits = {
            'Phalaenopsis': 'epiphytic', 'Dendrobium': 'epiphytic', 'Cattleya': 'epiphytic',
            'Paphiopedilum': 'terrestrial', 'Cymbidium': 'terrestrial', 'Bulbophyllum': 'epiphytic',
            'Vanda': 'epiphytic', 'Oncidium': 'epiphytic', 'Masdevallia': 'epiphytic'
        }
        
        if species_data['genus'] in genus_habits:
            species_data['growth_habit'] = genus_habits[species_data['genus']]
        
        return species_data

    def generate_collection_report(self):
        """Generate comprehensive collection report"""
        with app.app_context():
            gary_orchids = OrchidRecord.query.filter_by(ingestion_source='gary_complete_collection').all()
            
            genera_count = len(set(orchid.genus for orchid in gary_orchids))
            species_count = len(set(orchid.scientific_name for orchid in gary_orchids))
            
            logger.info("📊 GARY COLLECTION REPORT")
            logger.info(f"   Total orchids: {len(gary_orchids)}")
            logger.info(f"   Unique genera: {genera_count}")
            logger.info(f"   Unique species: {species_count}")
            
            return {
                'total_orchids': len(gary_orchids),
                'unique_genera': genera_count,
                'unique_species': species_count
            }

if __name__ == "__main__":
    collector = CompleteGaryCollectionSystem()
    
    # Run complete collection
    results = collector.collect_complete_gary_database()
    
    # Generate report
    collector.generate_collection_report()