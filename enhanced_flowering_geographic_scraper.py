"""
Enhanced Orchid Flowering Date & Geographic Origin Scraper
Specifically designed to increase database entries with flowering dates and precise coordinates.
Focus: Endemic species and cross-latitude blooming patterns.
"""

import requests
from bs4 import BeautifulSoup
from models import OrchidRecord, db
from datetime import datetime
import time
import logging
import re
from urllib.parse import urljoin
import json
from app import app

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FloweringGeographicScraper:
    """Enhanced scraper focusing on flowering dates and geographic origins"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        
        # Target sources known for flowering and geographic data
        self.priority_sources = [
            {
                'name': 'Internet Orchid Species Photo Encyclopedia',
                'base_url': 'https://orchidspecies.com/',
                'flowering_patterns': True,
                'geographic_precision': 'high'
            },
            {
                'name': 'Gary Yong Gee Enhanced',
                'base_url': 'https://orchids.yonggee.name/',
                'flowering_patterns': True,
                'geographic_precision': 'medium'
            },
            {
                'name': 'OrchidWire Global',
                'base_url': 'https://www.orchidwire.com/',
                'flowering_patterns': True,
                'geographic_precision': 'high'
            },
            {
                'name': 'Australian Orchid Database',
                'base_url': 'https://www.orchids.org.au/',
                'flowering_patterns': True,
                'geographic_precision': 'very_high'
            }
        ]
        
        # Flowering pattern extractors
        self.flowering_patterns = [
            r'flowering?\s*(?:time|season|period)?:?\s*([^.!?]+)',
            r'bloom[s]?\s*(?:in|during)?:?\s*([^.!?]+)',
            r'flowers?\s*(?:in|during)?:?\s*([^.!?]+)',
            r'(?:spring|summer|autumn|fall|winter|year.round)',
            r'(?:january|february|march|april|may|june|july|august|september|october|november|december)',
            r'(?:wet|dry)\s*season',
            r'(?:early|mid|late)\s*(?:spring|summer|autumn|fall|winter)'
        ]
        
        # Geographic coordinate patterns
        self.coordinate_patterns = [
            r'(\d+\.?\d*)[°\s]*([NS])\s*[,\s]*(\d+\.?\d*)[°\s]*([EW])',
            r'lat(?:itude)?:?\s*(-?\d+\.?\d*)',
            r'lon(?:gitude)?:?\s*(-?\d+\.?\d*)',
            r'elevation:?\s*(\d+)\s*m',
            r'altitude:?\s*(\d+)\s*(?:m|ft)'
        ]
        
        # Endemic species indicators
        self.endemic_indicators = [
            'endemic to',
            'native to',
            'restricted to',
            'found only in',
            'confined to',
            'limited to'
        ]
        
        self.stats = {
            'total_processed': 0,
            'with_flowering_dates': 0,
            'with_coordinates': 0,
            'with_both': 0,
            'endemic_species': 0,
            'cross_latitude_candidates': 0
        }

    def run_enhanced_collection(self):
        """Main collection routine focusing on flowering dates and coordinates"""
        logger.info("🌸📍 ENHANCED FLOWERING & GEOGRAPHIC COLLECTION STARTED")
        logger.info("Target: Increase orchid records with flowering dates AND coordinates")
        
        with app.app_context():
            # Phase 1: Enhance existing records with missing data
            self.enhance_existing_records()
            
            # Phase 2: Collect new records prioritizing flowering/geographic data
            self.collect_flowering_geographic_priority()
            
            # Phase 3: Identify and analyze endemic species
            self.analyze_endemic_species()
            
            # Phase 4: Report results
            self.report_collection_results()
            
            return self.stats

    def enhance_existing_records(self):
        """Enhance existing records with missing flowering dates or coordinates"""
        logger.info("🔄 Phase 1: Enhancing existing records with missing data")
        
        # Find records with genus/species but missing flowering/coordinate data
        records_needing_enhancement = OrchidRecord.query.filter(
            OrchidRecord.genus.isnot(None),
            OrchidRecord.species.isnot(None),
            db.or_(
                OrchidRecord.bloom_time.is_(None),
                OrchidRecord.decimal_latitude.is_(None)
            )
        ).limit(100).all()
        
        logger.info(f"Found {len(records_needing_enhancement)} records needing enhancement")
        
        for record in records_needing_enhancement:
            enhanced = self.enhance_single_record(record)
            if enhanced:
                self.stats['total_processed'] += 1
                
        db.session.commit()
        logger.info(f"✅ Enhanced {self.stats['total_processed']} existing records")

    def enhance_single_record(self, record):
        """Enhance a single record with flowering and geographic data"""
        try:
            scientific_name = f"{record.genus} {record.species}".strip()
            
            # Try to find flowering and geographic data from multiple sources
            enhancement_data = self.search_species_metadata(scientific_name)
            
            updated = False
            
            # Add flowering date if missing
            if not record.bloom_time and enhancement_data.get('flowering_time'):
                record.bloom_time = enhancement_data['flowering_time']
                self.stats['with_flowering_dates'] += 1
                updated = True
                logger.info(f"   📅 Added flowering data: {scientific_name} -> {enhancement_data['flowering_time']}")
            
            # Add coordinates if missing
            if not record.decimal_latitude and enhancement_data.get('latitude'):
                record.decimal_latitude = enhancement_data['latitude']
                record.decimal_longitude = enhancement_data['longitude']
                record.country = enhancement_data.get('country', record.country)
                self.stats['with_coordinates'] += 1
                updated = True
                logger.info(f"   🌍 Added coordinates: {scientific_name} -> ({enhancement_data['latitude']}, {enhancement_data['longitude']})")
            
            # Check if this is an endemic species
            if enhancement_data.get('endemic_info'):
                record.native_habitat = f"{record.native_habitat or ''} ENDEMIC: {enhancement_data['endemic_info']}".strip()
                self.stats['endemic_species'] += 1
                updated = True
                logger.info(f"   🏝️  Endemic species: {scientific_name} -> {enhancement_data['endemic_info']}")
            
            # Count records with both flowering and coordinates
            if record.bloom_time and record.decimal_latitude:
                self.stats['with_both'] += 1
            
            return updated
            
        except Exception as e:
            logger.error(f"Error enhancing {record.scientific_name}: {e}")
            return False

    def search_species_metadata(self, scientific_name):
        """Search multiple sources for species flowering and geographic metadata"""
        metadata = {
            'flowering_time': None,
            'latitude': None,
            'longitude': None,
            'country': None,
            'endemic_info': None
        }
        
        # Search Gary Yong Gee (enhanced extraction)
        gary_data = self.search_gary_enhanced(scientific_name)
        if gary_data:
            metadata.update(gary_data)
        
        # Search Internet Orchid Species if still missing data
        if not metadata['flowering_time'] or not metadata['latitude']:
            iospe_data = self.search_iospe_species(scientific_name)
            if iospe_data:
                for key, value in iospe_data.items():
                    if not metadata[key]:
                        metadata[key] = value
        
        return metadata

    def search_gary_enhanced(self, scientific_name):
        """Enhanced Gary Yong Gee search with flowering/geographic focus"""
        try:
            genus = scientific_name.split()[0]
            genus_url = f"https://orchids.yonggee.name/genera/{genus.lower()}"
            
            response = self.session.get(genus_url, timeout=15)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for species-specific information
            species_data = {}
            
            # Extract flowering information
            flowering_time = self.extract_flowering_patterns(soup.get_text())
            if flowering_time:
                species_data['flowering_time'] = flowering_time
            
            # Extract geographic information
            coordinates = self.extract_coordinates(soup.get_text())
            if coordinates:
                species_data.update(coordinates)
            
            # Extract endemic information
            endemic_info = self.extract_endemic_info(soup.get_text())
            if endemic_info:
                species_data['endemic_info'] = endemic_info
            
            return species_data if species_data else None
            
        except Exception as e:
            logger.debug(f"Gary search error for {scientific_name}: {e}")
            return None

    def search_iospe_species(self, scientific_name):
        """Search Internet Orchid Species Photo Encyclopedia"""
        try:
            genus = scientific_name.split()[0]
            species = scientific_name.split()[1] if len(scientific_name.split()) > 1 else ''
            
            # Try common IOSPE URL patterns
            possible_urls = [
                f"https://orchidspecies.com/{genus.lower()}/{genus.lower()}{species.lower()}.htm",
                f"https://orchidspecies.com/species/{genus.lower()}{species.lower()}.htm"
            ]
            
            for url in possible_urls:
                try:
                    response = self.session.get(url, timeout=15)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'html.parser')
                        
                        species_data = {}
                        text = soup.get_text()
                        
                        # IOSPE often has detailed flowering and habitat information
                        flowering_time = self.extract_flowering_patterns(text)
                        if flowering_time:
                            species_data['flowering_time'] = flowering_time
                        
                        coordinates = self.extract_coordinates(text)
                        if coordinates:
                            species_data.update(coordinates)
                        
                        endemic_info = self.extract_endemic_info(text)
                        if endemic_info:
                            species_data['endemic_info'] = endemic_info
                        
                        if species_data:
                            return species_data
                            
                except:
                    continue
                    
            return None
            
        except Exception as e:
            logger.debug(f"IOSPE search error for {scientific_name}: {e}")
            return None

    def extract_flowering_patterns(self, text):
        """Extract flowering time patterns from text"""
        text_lower = text.lower()
        
        for pattern in self.flowering_patterns:
            match = re.search(pattern, text_lower)
            if match:
                if match.groups():
                    flowering_info = match.group(1).strip()
                else:
                    flowering_info = match.group(0)
                
                # Clean up the flowering information
                flowering_info = re.sub(r'\s+', ' ', flowering_info)
                if len(flowering_info) < 50:  # Reasonable length
                    return flowering_info
        
        return None

    def extract_coordinates(self, text):
        """Extract coordinate information from text"""
        coordinates = {}
        
        for pattern in self.coordinate_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                groups = match.groups()
                
                if len(groups) >= 4 and groups[1] in ['N', 'S'] and groups[3] in ['E', 'W']:
                    # Format: lat N/S, lon E/W
                    lat = float(groups[0])
                    if groups[1] == 'S':
                        lat = -lat
                    lon = float(groups[2])
                    if groups[3] == 'W':
                        lon = -lon
                    
                    coordinates['latitude'] = lat
                    coordinates['longitude'] = lon
                    return coordinates
                    
                elif len(groups) >= 2:
                    # Try to extract individual lat/lon values
                    if 'lat' in pattern.lower():
                        coordinates['latitude'] = float(groups[0])
                    elif 'lon' in pattern.lower():
                        coordinates['longitude'] = float(groups[0])
        
        return coordinates if len(coordinates) >= 2 else None

    def extract_endemic_info(self, text):
        """Extract endemic species information"""
        text_lower = text.lower()
        
        for indicator in self.endemic_indicators:
            if indicator in text_lower:
                # Find the sentence containing the endemic information
                sentences = text.split('.')
                for sentence in sentences:
                    if indicator.lower() in sentence.lower():
                        # Clean and return endemic information
                        endemic_sentence = sentence.strip()
                        if len(endemic_sentence) < 200:  # Reasonable length
                            return endemic_sentence
        
        return None

    def collect_flowering_geographic_priority(self):
        """Collect new records prioritizing those with flowering/geographic data"""
        logger.info("🌸 Phase 2: Collecting new records with flowering/geographic priority")
        
        # Focus on genera known for good flowering/geographic documentation
        priority_genera = [
            'Cypripedium',  # Well-documented terrestrials
            'Ophrys',       # European terrestrials with precise locations
            'Orchis',       # Well-studied European species
            'Platanthera',  # North American terrestrials
            'Spiranthes',   # Widely distributed, well-documented
            'Caladenia',    # Australian terrestrials
            'Diuris',       # Australian terrestrials
            'Pterostylis'   # Australian terrestrials
        ]
        
        for genus in priority_genera:
            logger.info(f"🔍 Collecting {genus} species with priority metadata")
            self.collect_genus_flowering_geographic(genus)
            time.sleep(2)

    def collect_genus_flowering_geographic(self, genus_name):
        """Collect species from a genus with focus on flowering/geographic data"""
        try:
            # Search multiple sources for this genus
            sources_data = []
            
            # Gary Yong Gee
            gary_species = self.search_gary_genus_comprehensive(genus_name)
            sources_data.extend(gary_species)
            
            # Australian sources for relevant genera
            if genus_name in ['Caladenia', 'Diuris', 'Pterostylis']:
                aussie_species = self.search_australian_genus(genus_name)
                sources_data.extend(aussie_species)
            
            # European sources for relevant genera
            if genus_name in ['Ophrys', 'Orchis', 'Cypripedium']:
                euro_species = self.search_european_genus(genus_name)
                sources_data.extend(euro_species)
            
            # Process and save collected species
            for species_data in sources_data:
                if self.has_priority_metadata(species_data):
                    self.save_priority_species(species_data)
            
        except Exception as e:
            logger.error(f"Error collecting {genus_name}: {e}")

    def search_gary_genus_comprehensive(self, genus_name):
        """Comprehensive Gary genus search"""
        # Implementation for comprehensive Gary searching
        return []

    def search_australian_genus(self, genus_name):
        """Search Australian orchid databases for genus"""
        # Implementation for Australian sources
        return []

    def search_european_genus(self, genus_name):
        """Search European orchid databases for genus"""
        # Implementation for European sources
        return []

    def has_priority_metadata(self, species_data):
        """Check if species data has priority metadata (flowering + coordinates)"""
        return (
            species_data.get('flowering_time') and 
            species_data.get('latitude') and 
            species_data.get('longitude')
        )

    def save_priority_species(self, species_data):
        """Save species with priority metadata to database"""
        try:
            with app.app_context():
                # Check if species already exists
                existing = OrchidRecord.query.filter_by(
                    scientific_name=species_data['scientific_name']
                ).first()
                
                if existing:
                    return
                
                # Create new record
                record = OrchidRecord(
                    display_name=species_data['scientific_name'],
                    scientific_name=species_data['scientific_name'],
                    genus=species_data.get('genus'),
                    species=species_data.get('species'),
                    bloom_time=species_data.get('flowering_time'),
                    decimal_latitude=species_data.get('latitude'),
                    decimal_longitude=species_data.get('longitude'),
                    country=species_data.get('country'),
                    native_habitat=species_data.get('endemic_info', ''),
                    ingestion_source='enhanced_flowering_geographic',
                    data_source=species_data.get('source_url'),
                    created_at=datetime.utcnow()
                )
                
                db.session.add(record)
                db.session.commit()
                
                self.stats['total_processed'] += 1
                self.stats['with_flowering_dates'] += 1
                self.stats['with_coordinates'] += 1
                self.stats['with_both'] += 1
                
                if 'endemic' in (species_data.get('endemic_info', '') or '').lower():
                    self.stats['endemic_species'] += 1
                
                logger.info(f"✅ Saved priority species: {species_data['scientific_name']}")
                
        except Exception as e:
            logger.error(f"Error saving {species_data.get('scientific_name')}: {e}")
            db.session.rollback()

    def analyze_endemic_species(self):
        """Phase 3: Identify and analyze endemic species for cross-latitude patterns"""
        logger.info("🏝️  Phase 3: Analyzing endemic species and cross-latitude patterns")
        
        with app.app_context():
            # Find potential endemic species
            endemic_candidates = OrchidRecord.query.filter(
                OrchidRecord.native_habitat.contains('endemic'),
                OrchidRecord.decimal_latitude.isnot(None),
                OrchidRecord.bloom_time.isnot(None)
            ).all()
            
            logger.info(f"Found {len(endemic_candidates)} potential endemic species with coordinates and flowering data")
            
            # Analyze cross-latitude flowering patterns
            latitude_groups = {}
            for record in endemic_candidates:
                lat_band = round(record.decimal_latitude / 5) * 5  # Group by 5° bands
                if lat_band not in latitude_groups:
                    latitude_groups[lat_band] = []
                latitude_groups[lat_band].append(record)
            
            # Look for same species in different latitude bands
            cross_latitude_species = self.find_cross_latitude_species()
            self.stats['cross_latitude_candidates'] = len(cross_latitude_species)
            
            logger.info(f"🌐 Found {len(cross_latitude_species)} species with cross-latitude occurrence patterns")

    def find_cross_latitude_species(self):
        """Find species that occur at different latitudes with flowering data"""
        with app.app_context():
            # Query for species with multiple latitude records
            species_locations = {}
            
            records_with_coords = OrchidRecord.query.filter(
                OrchidRecord.decimal_latitude.isnot(None),
                OrchidRecord.bloom_time.isnot(None),
                OrchidRecord.scientific_name.isnot(None)
            ).all()
            
            for record in records_with_coords:
                name = record.scientific_name
                if name not in species_locations:
                    species_locations[name] = []
                
                species_locations[name].append({
                    'latitude': record.decimal_latitude,
                    'longitude': record.decimal_longitude,
                    'flowering_time': record.bloom_time,
                    'record_id': record.id
                })
            
            # Find species with significant latitude variation
            cross_latitude_species = []
            for species_name, locations in species_locations.items():
                if len(locations) >= 2:
                    lats = [loc['latitude'] for loc in locations]
                    lat_range = max(lats) - min(lats)
                    
                    if lat_range >= 10:  # At least 10° latitude difference
                        cross_latitude_species.append({
                            'species': species_name,
                            'locations': locations,
                            'latitude_range': lat_range
                        })
            
            return cross_latitude_species

    def report_collection_results(self):
        """Generate comprehensive collection report"""
        logger.info("=" * 70)
        logger.info("📊 ENHANCED FLOWERING & GEOGRAPHIC COLLECTION REPORT")
        logger.info("=" * 70)
        logger.info(f"Total records processed: {self.stats['total_processed']}")
        logger.info(f"Records with flowering dates: {self.stats['with_flowering_dates']}")
        logger.info(f"Records with coordinates: {self.stats['with_coordinates']}")
        logger.info(f"Records with BOTH flowering & coordinates: {self.stats['with_both']}")
        logger.info(f"Endemic species identified: {self.stats['endemic_species']}")
        logger.info(f"Cross-latitude species candidates: {self.stats['cross_latitude_candidates']}")
        logger.info("=" * 70)
        
        # Get updated database stats
        with app.app_context():
            total_records = db.session.query(OrchidRecord).count()
            with_bloom = db.session.query(OrchidRecord).filter(OrchidRecord.bloom_time.isnot(None)).count()
            with_coords = db.session.query(OrchidRecord).filter(OrchidRecord.decimal_latitude.isnot(None)).count()
            with_both = db.session.query(OrchidRecord).filter(
                OrchidRecord.bloom_time.isnot(None),
                OrchidRecord.decimal_latitude.isnot(None)
            ).count()
            
            logger.info(f"📊 UPDATED DATABASE TOTALS:")
            logger.info(f"   Total orchid records: {total_records}")
            logger.info(f"   With flowering dates: {with_bloom}")
            logger.info(f"   With coordinates: {with_coords}")
            logger.info(f"   With BOTH (target data): {with_both}")
            logger.info(f"   Completion rate: {(with_both/total_records)*100:.1f}%")
        
        logger.info("=" * 70)

if __name__ == "__main__":
    scraper = FloweringGeographicScraper()
    results = scraper.run_enhanced_collection()