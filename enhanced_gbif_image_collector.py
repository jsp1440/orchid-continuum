#!/usr/bin/env python3
"""
Enhanced GBIF Image Collector
============================
Comprehensive collection of orchid images from GBIF's massive database
Access to 15,431+ orchid images with proper attribution and metadata
"""

import requests
import time
import logging
from datetime import datetime
import json
from urllib.parse import urlparse
from app import app, db
from models import OrchidRecord

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedGBIFImageCollector:
    """Enhanced GBIF image collection system"""
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society - Educational Collection/2.0',
            'Accept': 'application/json'
        })
        
        self.collected_count = 0
        self.error_count = 0
        self.skipped_count = 0
        
        # Get Orchidaceae family key
        self.orchidaceae_key = self._get_orchidaceae_key()
        
        # High-priority genera with known image availability
        self.priority_genera = [
            'Orchis', 'Ophrys', 'Dactylorhiza', 'Platanthera', 'Spiranthes',
            'Goodyera', 'Liparis', 'Malaxis', 'Corallorhiza', 'Cypripedium',
            'Calopogon', 'Pogonia', 'Arethusa', 'Cleistes', 'Hexalectris',
            'Aplectrum', 'Tipularia', 'Listera', 'Neottia', 'Epipactis'
        ]

    def _get_orchidaceae_key(self):
        """Get the GBIF family key for Orchidaceae"""
        try:
            params = {
                'q': 'Orchidaceae',
                'rank': 'FAMILY',
                'limit': 5
            }
            
            response = self.session.get(f"{self.base_url}/species/search", params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                families = data.get('results', [])
                
                for family in families:
                    if (family.get('scientificName') == 'Orchidaceae' and 
                        family.get('taxonomicStatus') == 'ACCEPTED'):
                        logger.info(f"🌺 Found Orchidaceae family key: {family.get('key')}")
                        return family.get('key')
            
            # Fallback to known good key
            logger.warning("⚠️ Using fallback Orchidaceae key")
            return 3925978
            
        except Exception as e:
            logger.error(f"❌ Error finding family key: {e}")
            return 3925978

    def collect_all_gbif_orchid_images(self, max_images=5000):
        """Collect comprehensive orchid images from GBIF"""
        logger.info("🌍 STARTING COMPREHENSIVE GBIF ORCHID IMAGE COLLECTION")
        logger.info("=" * 80)
        
        with app.app_context():
            # Phase 1: Priority genera with known good image availability
            logger.info(f"🎯 Phase 1: Priority genera ({len(self.priority_genera)} genera)")
            for i, genus in enumerate(self.priority_genera):
                if self.collected_count >= max_images:
                    break
                logger.info(f"📸 [{i+1}/{len(self.priority_genera)}] Collecting {genus} images")
                self.collect_genus_images(genus, max_per_genus=50)
                time.sleep(2)
            
            # Phase 2: General orchid family search
            logger.info("🌍 Phase 2: General orchid family image collection")
            self.collect_family_images(max_images - self.collected_count)
            
            # Phase 3: Occurrence-based image collection
            logger.info("📍 Phase 3: Geographic occurrence image collection")
            self.collect_occurrence_images(max_images - self.collected_count)
            
            logger.info(f"✅ GBIF IMAGE COLLECTION COMPLETE")
            logger.info(f"   Collected: {self.collected_count} images")
            logger.info(f"   Errors: {self.error_count}")
            logger.info(f"   Skipped: {self.skipped_count}")
            
            return {
                'collected': self.collected_count,
                'errors': self.error_count,
                'skipped': self.skipped_count
            }

    def collect_genus_images(self, genus_name, max_per_genus=50):
        """Collect images for a specific genus"""
        try:
            # Search for species in this genus
            params = {
                'q': genus_name,
                'family': 'Orchidaceae',
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': max_per_genus,
                'offset': 0
            }
            
            response = self.session.get(f"{self.base_url}/occurrence/search", 
                                      params=params, timeout=20)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                
                logger.info(f"   Found {len(results)} {genus_name} records with images")
                
                for record in results:
                    if self.collected_count >= max_per_genus:
                        break
                    self.process_gbif_record(record)
                    
            else:
                logger.warning(f"⚠️ GBIF search failed for {genus_name}: {response.status_code}")
                self.error_count += 1
                
        except Exception as e:
            logger.error(f"❌ Error collecting {genus_name} images: {e}")
            self.error_count += 1

    def collect_family_images(self, max_images):
        """Collect images using family-level search"""
        try:
            batch_size = 300
            offset = 0
            collected_this_phase = 0
            
            while collected_this_phase < max_images:
                params = {
                    'familyKey': self.orchidaceae_key,
                    'mediaType': 'StillImage',
                    'hasCoordinate': 'true',
                    'limit': min(batch_size, max_images - collected_this_phase),
                    'offset': offset
                }
                
                response = self.session.get(f"{self.base_url}/occurrence/search", 
                                          params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        logger.info("   No more family records available")
                        break
                    
                    logger.info(f"   Processing batch: {len(results)} family records")
                    
                    batch_collected = 0
                    for record in results:
                        if collected_this_phase >= max_images:
                            break
                        if self.process_gbif_record(record):
                            batch_collected += 1
                            collected_this_phase += 1
                    
                    if batch_collected == 0:
                        logger.info("   No new records in this batch")
                        break
                        
                    offset += batch_size
                    time.sleep(1)  # Rate limiting
                    
                else:
                    logger.warning(f"⚠️ Family search failed: {response.status_code}")
                    break
                    
        except Exception as e:
            logger.error(f"❌ Error in family image collection: {e}")
            self.error_count += 1

    def collect_occurrence_images(self, max_images):
        """Collect images from geographic occurrence data"""
        try:
            # Search by known orchid-rich regions
            regions = [
                {'country': 'US', 'name': 'United States'},
                {'country': 'CA', 'name': 'Canada'},
                {'country': 'MX', 'name': 'Mexico'},
                {'country': 'CR', 'name': 'Costa Rica'},
                {'country': 'EC', 'name': 'Ecuador'},
                {'country': 'BR', 'name': 'Brazil'},
                {'country': 'AU', 'name': 'Australia'},
                {'country': 'NZ', 'name': 'New Zealand'},
                {'country': 'ZA', 'name': 'South Africa'},
                {'country': 'MG', 'name': 'Madagascar'}
            ]
            
            collected_this_phase = 0
            per_region = max_images // len(regions)
            
            for region in regions:
                if collected_this_phase >= max_images:
                    break
                    
                logger.info(f"   Collecting from {region['name']}")
                
                params = {
                    'family': 'Orchidaceae',
                    'country': region['country'],
                    'mediaType': 'StillImage',
                    'hasCoordinate': 'true',
                    'limit': min(per_region, max_images - collected_this_phase)
                }
                
                response = self.session.get(f"{self.base_url}/occurrence/search", 
                                          params=params, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    for record in results:
                        if collected_this_phase >= max_images:
                            break
                        if self.process_gbif_record(record):
                            collected_this_phase += 1
                
                time.sleep(1)  # Rate limiting
                
        except Exception as e:
            logger.error(f"❌ Error in occurrence image collection: {e}")
            self.error_count += 1

    def process_gbif_record(self, record):
        """Process a single GBIF record with image"""
        try:
            # Extract basic information
            scientific_name = record.get('scientificName', '')
            species = record.get('species', '')
            genus = record.get('genus', '')
            
            if not scientific_name or not genus:
                return False
            
            # Check if already exists
            existing = OrchidRecord.query.filter_by(
                scientific_name=scientific_name,
                ingestion_source='gbif_images'
            ).first()
            
            if existing:
                self.skipped_count += 1
                return False
            
            # Extract media information
            media = record.get('media', [])
            image_url = None
            
            for medium in media:
                if medium.get('type') == 'StillImage' and medium.get('identifier'):
                    image_url = medium.get('identifier')
                    break
            
            if not image_url:
                return False
            
            # Extract geographic information
            country = record.get('country', '')
            state_province = record.get('stateProvince', '')
            locality = record.get('locality', '')
            decimal_latitude = record.get('decimalLatitude')
            decimal_longitude = record.get('decimalLongitude')
            
            # Extract collector information
            collector = record.get('recordedBy', '')
            event_date = record.get('eventDate', '')
            
            # Create orchid record
            orchid_record = OrchidRecord(
                display_name=scientific_name,
                scientific_name=scientific_name,
                genus=genus,
                species=species,
                
                # Geographic data
                country=country,
                state_province=state_province,
                locality=locality,
                decimal_latitude=decimal_latitude,
                decimal_longitude=decimal_longitude,
                
                # Collection data
                collector=collector,
                event_date=event_date,
                
                # Image data
                image_url=image_url,
                image_source='GBIF',
                
                # Source tracking
                ingestion_source='gbif_images',
                data_source=f"GBIF Occurrence {record.get('key', '')}",
                
                # Metadata
                ai_description=f"GBIF occurrence record from {country} with geographic coordinates",
                
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save to database
            db.session.add(orchid_record)
            db.session.commit()
            
            logger.info(f"✅ Collected GBIF: {scientific_name} from {country}")
            self.collected_count += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing GBIF record: {e}")
            self.error_count += 1
            return False

    def enhance_existing_records_with_gbif(self):
        """Enhance existing records with GBIF occurrence data"""
        logger.info("🔄 ENHANCING EXISTING RECORDS WITH GBIF DATA")
        
        with app.app_context():
            # Get records that need enhancement
            records = OrchidRecord.query.filter(
                (OrchidRecord.decimal_latitude.is_(None)) |
                (OrchidRecord.country.is_(None)) |
                (OrchidRecord.native_habitat.is_(None))
            ).filter(
                OrchidRecord.scientific_name.isnot(None)
            ).limit(500).all()
            
            enhanced_count = 0
            
            for i, record in enumerate(records):
                try:
                    logger.info(f"🔍 [{i+1}/{len(records)}] Enhancing {record.scientific_name}")
                    
                    # Search GBIF for this species
                    params = {
                        'scientificName': record.scientific_name,
                        'hasCoordinate': 'true',
                        'limit': 5
                    }
                    
                    response = self.session.get(f"{self.base_url}/occurrence/search", 
                                              params=params, timeout=15)
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        if results:
                            gbif_record = results[0]  # Use first result
                            
                            # Fill missing geographic data
                            if not record.decimal_latitude and gbif_record.get('decimalLatitude'):
                                record.decimal_latitude = gbif_record.get('decimalLatitude')
                                record.decimal_longitude = gbif_record.get('decimalLongitude')
                            
                            if not record.country and gbif_record.get('country'):
                                record.country = gbif_record.get('country')
                            
                            if not record.state_province and gbif_record.get('stateProvince'):
                                record.state_province = gbif_record.get('stateProvince')
                            
                            # Update timestamp
                            record.updated_at = datetime.utcnow()
                            
                            enhanced_count += 1
                            logger.info(f"✅ Enhanced: {record.scientific_name}")
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except Exception as e:
                    logger.error(f"❌ Error enhancing {record.scientific_name}: {e}")
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"✅ Enhanced {enhanced_count} existing records with GBIF data")
            return enhanced_count

    def generate_gbif_collection_report(self):
        """Generate comprehensive GBIF collection report"""
        with app.app_context():
            gbif_orchids = OrchidRecord.query.filter_by(ingestion_source='gbif_images').all()
            
            countries = set(orchid.country for orchid in gbif_orchids if orchid.country)
            genera = set(orchid.genus for orchid in gbif_orchids if orchid.genus)
            
            logger.info("📊 GBIF COLLECTION REPORT")
            logger.info(f"   Total GBIF orchids: {len(gbif_orchids)}")
            logger.info(f"   Countries represented: {len(countries)}")
            logger.info(f"   Genera collected: {len(genera)}")
            logger.info(f"   Records with coordinates: {sum(1 for o in gbif_orchids if o.decimal_latitude)}")
            
            return {
                'total_orchids': len(gbif_orchids),
                'countries': len(countries),
                'genera': len(genera),
                'with_coordinates': sum(1 for o in gbif_orchids if o.decimal_latitude)
            }

if __name__ == "__main__":
    collector = EnhancedGBIFImageCollector()
    
    # Run comprehensive GBIF image collection
    results = collector.collect_all_gbif_orchid_images(max_images=2000)
    
    # Enhance existing records
    collector.enhance_existing_records_with_gbif()
    
    # Generate report
    collector.generate_gbif_collection_report()