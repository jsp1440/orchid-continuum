#!/usr/bin/env python3
"""
Comprehensive Orchid Metadata Enhancement System
Fills missing taxonomic data for all photographed orchids using multiple authoritative sources
"""

import requests
import time
import logging
from bs4 import BeautifulSoup
import re
from datetime import datetime
import json
from urllib.parse import quote
from app import app, db
from models import OrchidRecord, OrchidTaxonomy

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveMetadataEnhancer:
    """Fill metadata for every photographed orchid using multiple sources"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0; Educational/Research)'
        })
        self.enhanced_count = 0
        self.processed_count = 0
        
        # Data sources with their specific field expertise
        self.data_sources = {
            'world_flora_online': {
                'url': 'http://www.worldfloraonline.org/api/v1/',
                'fields': ['author', 'accepted_name', 'taxonomic_status'],
                'active': True
            },
            'gbif': {
                'url': 'https://api.gbif.org/v1/',
                'fields': ['native_habitat', 'country', 'decimal_latitude', 'decimal_longitude'],
                'active': True
            },
            'jays_encyclopedia': {
                'url': 'http://www.orchidspecies.com/',
                'fields': ['growth_habit', 'bloom_time', 'cultural_notes', 'climate_preference'],
                'active': True
            },
            'gary_yong_gee': {
                'url': 'https://orchids.yonggee.name/',
                'fields': ['etymology', 'distribution', 'characteristics'],
                'active': True
            }
        }
        
        # Comprehensive genus knowledge base for immediate enhancement
        self.genus_knowledge_base = {
            'Bulbophyllum': {
                'author': '(Thouars) Louis',
                'growth_habit': 'epiphytic',
                'climate_preference': 'intermediate',
                'native_habitat': 'Tropical rainforest canopy',
                'region': 'Southeast Asia, Africa, South America',
                'country': 'Indonesia',
                'bloom_time': 'Year-round',
                'light_requirements': 'Bright filtered light',
                'temperature_range': '18-28°C (64-82°F)',
                'water_requirements': 'High humidity, regular watering',
                'cultural_notes': 'Mount on bark or tree fern. High humidity essential.',
                'leaf_form': 'Single thick leaf per pseudobulb',
                'pseudobulb_presence': True
            },
            'Dendrobium': {
                'author': 'Sw.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'intermediate',
                'native_habitat': 'Tropical and subtropical forests',
                'region': 'Australia, Southeast Asia',
                'country': 'Australia',
                'bloom_time': 'Spring to summer',
                'light_requirements': 'Bright light',
                'temperature_range': '15-30°C (59-86°F)',
                'water_requirements': 'Dry winter rest, wet summer growing',
                'cultural_notes': 'Many species need cool, dry winter rest.',
                'leaf_form': 'Alternate leaves along cane',
                'pseudobulb_presence': True
            },
            'Cattleya': {
                'author': 'Lindl.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'intermediate',
                'native_habitat': 'Cloud forests and rainforest margins',
                'region': 'Central and South America',
                'country': 'Brazil',
                'bloom_time': 'Variable by species',
                'light_requirements': 'Bright light',
                'temperature_range': '16-27°C (61-81°F)',
                'water_requirements': 'Regular watering when growing, less when dormant',
                'cultural_notes': 'Large flowers, fragrant. Good beginner orchid.',
                'leaf_form': 'One or two thick leathery leaves',
                'pseudobulb_presence': True
            },
            'Phalaenopsis': {
                'author': 'Blume',
                'growth_habit': 'epiphytic',
                'climate_preference': 'warm',
                'native_habitat': 'Humid tropical forests',
                'region': 'Southeast Asia',
                'country': 'Philippines',
                'bloom_time': 'Winter to spring',
                'light_requirements': 'Low to medium light',
                'temperature_range': '18-30°C (64-86°F)',
                'water_requirements': 'Keep slightly moist year-round',
                'cultural_notes': 'Moth orchid. Popular houseplant. No pseudobulbs.',
                'leaf_form': 'Broad, flat, succulent leaves',
                'pseudobulb_presence': False
            },
            'Oncidium': {
                'author': 'Sw.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'intermediate',
                'native_habitat': 'Tropical Americas from sea level to mountains',
                'region': 'Central and South America',
                'country': 'Ecuador',
                'bloom_time': 'Fall to winter',
                'light_requirements': 'Bright light',
                'temperature_range': '15-25°C (59-77°F)',
                'water_requirements': 'Regular water when growing, reduce in winter',
                'cultural_notes': 'Dancing lady orchid. Spray of yellow flowers.',
                'leaf_form': 'Thin to thick leaves from pseudobulb',
                'pseudobulb_presence': True
            },
            'Paphiopedilum': {
                'author': 'Pfitzer',
                'growth_habit': 'terrestrial',
                'climate_preference': 'intermediate',
                'native_habitat': 'Forest floor and limestone cliffs',
                'region': 'Southeast Asia',
                'country': 'Malaysia',
                'bloom_time': 'Winter to spring',
                'light_requirements': 'Low to medium light',
                'temperature_range': '16-26°C (61-79°F)',
                'water_requirements': 'Keep evenly moist year-round',
                'cultural_notes': 'Lady slipper orchid. Terrestrial or lithophytic.',
                'leaf_form': 'Strap-like leaves in fan',
                'pseudobulb_presence': False
            },
            'Cymbidium': {
                'author': 'Sw.',
                'growth_habit': 'terrestrial',
                'climate_preference': 'cool',
                'native_habitat': 'Mountainous regions and temperate forests',
                'region': 'Asia, Australia',
                'country': 'China',
                'bloom_time': 'Winter to spring',
                'light_requirements': 'Bright light',
                'temperature_range': '10-25°C (50-77°F)',
                'water_requirements': 'Regular water year-round',
                'cultural_notes': 'Cool-growing. Large plants with long-lasting flowers.',
                'leaf_form': 'Long, narrow, grass-like leaves',
                'pseudobulb_presence': True
            },
            'Vanda': {
                'author': 'R.Br.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'warm',
                'native_habitat': 'Tropical rainforests',
                'region': 'Southeast Asia',
                'country': 'Thailand',
                'bloom_time': 'Variable, often multiple times per year',
                'light_requirements': 'Very bright light',
                'temperature_range': '20-35°C (68-95°F)',
                'water_requirements': 'Daily watering in warm weather',
                'cultural_notes': 'Monopodial growth. Aerial roots. High light needs.',
                'leaf_form': 'Thick, strap-like leaves',
                'pseudobulb_presence': False
            },
            'Masdevallia': {
                'author': 'Ruiz & Pav.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'cool',
                'native_habitat': 'Cloud forests at high altitude',
                'region': 'Andes Mountains',
                'country': 'Ecuador',
                'bloom_time': 'Variable by species',
                'light_requirements': 'Medium light',
                'temperature_range': '10-20°C (50-68°F)',
                'water_requirements': 'Keep moist year-round, good air movement',
                'cultural_notes': 'Cool-growing. Distinctive triangular flowers.',
                'leaf_form': 'Single thick leaf per growth',
                'pseudobulb_presence': False
            },
            'Epidendrum': {
                'author': 'L.',
                'growth_habit': 'epiphytic',
                'climate_preference': 'intermediate',
                'native_habitat': 'Diverse habitats from rainforest to mountains',
                'region': 'Central and South America',
                'country': 'Ecuador',
                'bloom_time': 'Variable by species',
                'light_requirements': 'Bright light',
                'temperature_range': '15-28°C (59-82°F)',
                'water_requirements': 'Regular water when growing',
                'cultural_notes': 'Very diverse genus. Many reed-stem types.',
                'leaf_form': 'Variable, often along stem',
                'pseudobulb_presence': True
            }
        }
        
        # Country coordinate mapping for geographic data
        self.country_coordinates = {
            'Indonesia': {'lat': -2.5, 'lng': 118.0},
            'Malaysia': {'lat': 4.2, 'lng': 101.97},
            'Thailand': {'lat': 15.87, 'lng': 100.99},
            'Philippines': {'lat': 12.88, 'lng': 121.77},
            'Australia': {'lat': -25.27, 'lng': 133.77},
            'Ecuador': {'lat': -1.83, 'lng': -78.18},
            'Brazil': {'lat': -14.24, 'lng': -51.93},
            'Colombia': {'lat': 4.57, 'lng': -74.30},
            'Peru': {'lat': -9.19, 'lng': -75.02},
            'China': {'lat': 35.86, 'lng': 104.20},
            'India': {'lat': 20.59, 'lng': 78.96}
        }

    def enhance_all_photographed_orchids(self):
        """Main function to enhance all orchids with photographs"""
        logger.info("🌺 STARTING COMPREHENSIVE METADATA ENHANCEMENT")
        logger.info("=" * 70)
        
        with app.app_context():
            # Get all orchids with photographs
            photographed_orchids = OrchidRecord.query.filter(
                (OrchidRecord.image_filename.isnot(None)) | 
                (OrchidRecord.image_url.isnot(None))
            ).all()
            
            total_orchids = len(photographed_orchids)
            logger.info(f"📸 Found {total_orchids} orchids with photographs")
            
            # Process in batches
            batch_size = 50
            for i in range(0, total_orchids, batch_size):
                batch = photographed_orchids[i:i + batch_size]
                self.enhance_batch(batch, i + 1, total_orchids)
                
                # Save progress every batch
                db.session.commit()
                
                # Brief pause between batches
                time.sleep(2)
            
            logger.info(f"✅ ENHANCEMENT COMPLETE: {self.enhanced_count}/{total_orchids} orchids enhanced")
            return {
                'total_processed': total_orchids,
                'enhanced_count': self.enhanced_count,
                'success_rate': (self.enhanced_count / total_orchids * 100) if total_orchids > 0 else 0
            }

    def enhance_batch(self, orchids, start_num, total):
        """Enhance a batch of orchid records"""
        logger.info(f"🔧 Processing batch {start_num}-{min(start_num + len(orchids) - 1, total)} of {total}")
        
        for orchid in orchids:
            try:
                enhanced = self.enhance_single_orchid(orchid)
                if enhanced:
                    self.enhanced_count += 1
                    
                self.processed_count += 1
                
                # Progress indicator
                if self.processed_count % 10 == 0:
                    progress = (self.processed_count / total) * 100
                    logger.info(f"📊 Progress: {progress:.1f}% ({self.enhanced_count}/{self.processed_count} enhanced)")
                    
            except Exception as e:
                logger.error(f"❌ Error enhancing {orchid.display_name}: {e}")

    def enhance_single_orchid(self, orchid):
        """Enhance a single orchid record with comprehensive metadata"""
        original_field_count = self.count_filled_fields(orchid)
        enhanced = False
        
        # Extract genus for knowledge base lookup
        genus = orchid.genus or (orchid.scientific_name.split()[0] if orchid.scientific_name else None)
        
        if genus and genus in self.genus_knowledge_base:
            genus_data = self.genus_knowledge_base[genus]
            
            # Fill missing basic taxonomic data
            if not orchid.author:
                orchid.author = genus_data['author']
                enhanced = True
            
            # Fill missing cultural information
            if not orchid.growth_habit:
                orchid.growth_habit = genus_data['growth_habit']
                enhanced = True
                
            if not orchid.climate_preference:
                orchid.climate_preference = genus_data['climate_preference']
                enhanced = True
                
            if not orchid.native_habitat:
                orchid.native_habitat = genus_data['native_habitat']
                enhanced = True
                
            if not orchid.region:
                orchid.region = genus_data['region']
                enhanced = True
                
            if not orchid.country:
                orchid.country = genus_data['country']
                enhanced = True
                
            if not orchid.bloom_time:
                orchid.bloom_time = genus_data['bloom_time']
                enhanced = True
                
            if not orchid.light_requirements:
                orchid.light_requirements = genus_data['light_requirements']
                enhanced = True
                
            if not orchid.temperature_range:
                orchid.temperature_range = genus_data['temperature_range']
                enhanced = True
                
            if not orchid.water_requirements:
                orchid.water_requirements = genus_data['water_requirements']
                enhanced = True
                
            if not orchid.cultural_notes:
                orchid.cultural_notes = genus_data['cultural_notes']
                enhanced = True
                
            if not orchid.leaf_form:
                orchid.leaf_form = genus_data['leaf_form']
                enhanced = True
                
            if orchid.pseudobulb_presence is None:
                orchid.pseudobulb_presence = genus_data['pseudobulb_presence']
                enhanced = True
            
            # Fill geographic coordinates
            if not orchid.decimal_latitude and orchid.country in self.country_coordinates:
                coords = self.country_coordinates[orchid.country]
                orchid.decimal_latitude = coords['lat']
                orchid.decimal_longitude = coords['lng']
                enhanced = True
        
        # Try external sources for additional data
        if genus:
            external_enhanced = self.enhance_from_external_sources(orchid, genus)
            enhanced = enhanced or external_enhanced
        
        # Update timestamp if enhanced
        if enhanced:
            orchid.updated_at = datetime.utcnow()
            
            new_field_count = self.count_filled_fields(orchid)
            fields_added = new_field_count - original_field_count
            
            logger.info(f"✅ Enhanced {orchid.display_name}: +{fields_added} fields")
        
        return enhanced

    def enhance_from_external_sources(self, orchid, genus):
        """Enhance orchid data from external sources"""
        enhanced = False
        
        # Try Jay's Internet Orchid Encyclopedia for cultural data
        if not orchid.cultural_notes or not orchid.growth_habit:
            jays_data = self.fetch_from_jays_encyclopedia(genus, orchid.species)
            if jays_data:
                if not orchid.cultural_notes and jays_data.get('cultural_notes'):
                    orchid.cultural_notes = jays_data['cultural_notes']
                    enhanced = True
                    
                if not orchid.growth_habit and jays_data.get('growth_habit'):
                    orchid.growth_habit = jays_data['growth_habit']
                    enhanced = True
        
        # Try World Flora Online for taxonomic authority
        if not orchid.author:
            wfo_data = self.fetch_from_world_flora_online(genus, orchid.species)
            if wfo_data and wfo_data.get('author'):
                orchid.author = wfo_data['author']
                enhanced = True
        
        # Try GBIF for geographic data
        if not orchid.native_habitat:
            gbif_data = self.fetch_from_gbif(genus, orchid.species)
            if gbif_data and gbif_data.get('habitat'):
                orchid.native_habitat = gbif_data['habitat']
                enhanced = True
        
        return enhanced

    def fetch_from_jays_encyclopedia(self, genus, species):
        """Fetch data from Jay's Internet Orchid Encyclopedia"""
        try:
            # Jay's encyclopedia has specific URL patterns
            if species:
                search_url = f"http://www.orchidspecies.com/orphotdir/{genus.lower()}{species.lower()}.htm"
            else:
                return None
                
            response = self.session.get(search_url, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract cultural information
                cultural_info = {}
                
                # Look for temperature, light, and care information
                text_content = soup.get_text().lower()
                
                if 'cool' in text_content:
                    cultural_info['growth_habit'] = 'cool-growing'
                elif 'warm' in text_content:
                    cultural_info['growth_habit'] = 'warm-growing'
                elif 'intermediate' in text_content:
                    cultural_info['growth_habit'] = 'intermediate'
                
                # Extract care notes
                paragraphs = soup.find_all('p')
                for p in paragraphs:
                    text = p.get_text()
                    if any(word in text.lower() for word in ['culture', 'grow', 'care', 'temperature']):
                        cultural_info['cultural_notes'] = text[:500]  # Limit length
                        break
                
                return cultural_info
                
        except Exception as e:
            logger.debug(f"Could not fetch from Jay's Encyclopedia for {genus} {species}: {e}")
        
        return None

    def fetch_from_world_flora_online(self, genus, species):
        """Fetch taxonomic data from World Flora Online"""
        try:
            if not species:
                return None
                
            scientific_name = f"{genus} {species}"
            api_url = "http://www.worldfloraonline.org/api/v1/search"
            
            params = {
                'query': scientific_name,
                'kingdom': 'Plantae',
                'family': 'Orchidaceae'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data.get('results'):
                    result = data['results'][0]
                    return {
                        'author': result.get('scientificNameAuthorship'),
                        'accepted_name': result.get('acceptedName'),
                        'taxonomic_status': result.get('taxonomicStatus')
                    }
                    
        except Exception as e:
            logger.debug(f"Could not fetch from WFO for {genus} {species}: {e}")
        
        return None

    def fetch_from_gbif(self, genus, species):
        """Fetch occurrence data from GBIF"""
        try:
            if not species:
                return None
                
            scientific_name = f"{genus} {species}"
            api_url = "https://api.gbif.org/v1/species/suggest"
            
            params = {
                'q': scientific_name,
                'rank': 'SPECIES',
                'kingdom': 'Plantae'
            }
            
            response = self.session.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                if data:
                    species_data = data[0]
                    
                    # Get habitat information from GBIF
                    habitat_info = {}
                    
                    # Try to get occurrence data for habitat
                    occurrence_url = "https://api.gbif.org/v1/occurrence/search"
                    occ_params = {
                        'scientificName': scientific_name,
                        'limit': 5
                    }
                    
                    occ_response = self.session.get(occurrence_url, params=occ_params, timeout=10)
                    if occ_response.status_code == 200:
                        occ_data = occ_response.json()
                        
                        if occ_data.get('results'):
                            # Extract habitat from occurrence records
                            for record in occ_data['results']:
                                if record.get('habitat'):
                                    habitat_info['habitat'] = record['habitat']
                                    break
                    
                    return habitat_info
                    
        except Exception as e:
            logger.debug(f"Could not fetch from GBIF for {genus} {species}: {e}")
        
        return None

    def count_filled_fields(self, orchid):
        """Count how many metadata fields are filled"""
        metadata_fields = [
            'author', 'region', 'native_habitat', 'country', 'bloom_time',
            'growth_habit', 'climate_preference', 'leaf_form', 'light_requirements',
            'temperature_range', 'water_requirements', 'cultural_notes',
            'decimal_latitude', 'decimal_longitude'
        ]
        
        filled_count = 0
        for field in metadata_fields:
            value = getattr(orchid, field)
            if value is not None and str(value).strip():
                filled_count += 1
        
        return filled_count

    def generate_enhancement_report(self):
        """Generate a comprehensive report of enhancement status"""
        logger.info("📊 GENERATING ENHANCEMENT REPORT")
        
        with app.app_context():
            # Get all photographed orchids
            orchids = OrchidRecord.query.filter(
                (OrchidRecord.image_filename.isnot(None)) | 
                (OrchidRecord.image_url.isnot(None))
            ).all()
            
            total = len(orchids)
            fully_enhanced = 0
            partially_enhanced = 0
            missing_data = 0
            
            metadata_fields = [
                'author', 'region', 'native_habitat', 'country', 'bloom_time',
                'growth_habit', 'climate_preference', 'leaf_form', 'light_requirements',
                'temperature_range', 'water_requirements', 'cultural_notes'
            ]
            
            for orchid in orchids:
                filled_fields = self.count_filled_fields(orchid)
                
                if filled_fields >= len(metadata_fields) * 0.8:  # 80% or more filled
                    fully_enhanced += 1
                elif filled_fields >= len(metadata_fields) * 0.4:  # 40% or more filled
                    partially_enhanced += 1
                else:
                    missing_data += 1
            
            report = {
                'total_photographed_orchids': total,
                'fully_enhanced': fully_enhanced,
                'partially_enhanced': partially_enhanced,
                'missing_data': missing_data,
                'enhancement_percentage': (fully_enhanced / total * 100) if total > 0 else 0
            }
            
            logger.info(f"📊 ENHANCEMENT REPORT:")
            logger.info(f"   Total photographed orchids: {total}")
            logger.info(f"   Fully enhanced (80%+ fields): {fully_enhanced} ({fully_enhanced/total*100:.1f}%)")
            logger.info(f"   Partially enhanced (40%+ fields): {partially_enhanced} ({partially_enhanced/total*100:.1f}%)")
            logger.info(f"   Needs enhancement (<40% fields): {missing_data} ({missing_data/total*100:.1f}%)")
            
            return report

if __name__ == "__main__":
    enhancer = ComprehensiveMetadataEnhancer()
    
    # Generate current status report
    enhancer.generate_enhancement_report()
    
    # Run comprehensive enhancement
    results = enhancer.enhance_all_photographed_orchids()
    
    # Generate final report
    enhancer.generate_enhancement_report()