#!/usr/bin/env python3
"""
GBIF Orchid Data Importer
=========================
Downloads comprehensive orchid taxonomic data from GBIF (Global Biodiversity Information Facility)
Integrates with our validation system to ensure data quality
"""

import requests
import time
import logging
import json
import os
from datetime import datetime
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GBIFOrchidImporter:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid-Continuum/1.0 (Educational/Research; gbif-integration)'
        })
        
        # GBIF API base URL
        self.base_url = "https://api.gbif.org/v1"
        
        # Initialize validation system
        self.validator = ScraperValidationSystem()
        self.collected_count = 0
        self.rejected_count = 0
        self.total_gbif_records = 0
        
        logger.info("🌍 GBIF ORCHID IMPORTER INITIALIZED WITH VALIDATION")
    
    def download_orchid_families(self):
        """Download all orchid family data from GBIF"""
        
        logger.info("🔍 Starting GBIF orchid family data download...")
        
        # Get Orchidaceae family key from GBIF
        orchidaceae_key = self.get_orchidaceae_family_key()
        if not orchidaceae_key:
            logger.error("❌ Could not find Orchidaceae family in GBIF")
            return
        
        logger.info(f"✅ Found Orchidaceae family key: {orchidaceae_key}")
        
        # Download all species in Orchidaceae
        self.download_family_species(orchidaceae_key)
        
        logger.info(f"🎉 GBIF IMPORT COMPLETE! Collected {self.collected_count} valid orchids from {self.total_gbif_records} GBIF records")
    
    def get_orchidaceae_family_key(self):
        """Get the GBIF key for Orchidaceae family"""
        
        try:
            # Search for Orchidaceae family
            response = self.session.get(
                f"{self.base_url}/species/search",
                params={
                    'q': 'Orchidaceae',
                    'rank': 'FAMILY',
                    'status': 'ACCEPTED'
                },
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            for result in results:
                if (result.get('scientificName', '').lower() == 'orchidaceae' and 
                    result.get('rank') == 'FAMILY' and
                    result.get('taxonomicStatus') == 'ACCEPTED'):
                    return result.get('key')
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching for Orchidaceae: {e}")
            return None
    
    def download_family_species(self, family_key, limit=1000, max_records=10000):
        """Download all species in the Orchidaceae family"""
        
        offset = 0
        batch_count = 0
        
        logger.info(f"📥 Downloading orchid species data (max {max_records} records)...")
        
        with app.app_context():
            while offset < max_records:
                try:
                    # Get species data from GBIF
                    response = self.session.get(
                        f"{self.base_url}/species/search",
                        params={
                            'familyKey': family_key,
                            'rank': 'SPECIES',
                            'status': 'ACCEPTED',
                            'limit': limit,
                            'offset': offset
                        },
                        timeout=30
                    )
                    response.raise_for_status()
                    
                    data = response.json()
                    results = data.get('results', [])
                    
                    if not results:
                        logger.info("📭 No more results - download complete")
                        break
                    
                    batch_count += 1
                    self.total_gbif_records += len(results)
                    
                    logger.info(f"📦 Processing batch {batch_count}: {len(results)} species (offset: {offset})")
                    
                    # Process each species
                    batch_collected = 0
                    batch_rejected = 0
                    
                    for species_data in results:
                        created = self.create_orchid_from_gbif(species_data)
                        if created:
                            batch_collected += 1
                            self.collected_count += 1
                        else:
                            batch_rejected += 1
                            self.rejected_count += 1
                    
                    logger.info(f"📊 Batch {batch_count}: {batch_collected} collected, {batch_rejected} rejected")
                    
                    # Commit batch to database
                    try:
                        db.session.commit()
                        logger.info(f"✅ Batch {batch_count} committed to database")
                    except Exception as e:
                        logger.error(f"❌ Database error: {e}")
                        db.session.rollback()
                    
                    offset += limit
                    
                    # Be respectful to GBIF API
                    time.sleep(1)
                    
                    # Check if we've reached the end
                    if len(results) < limit:
                        logger.info("📭 Reached end of results")
                        break
                        
                except Exception as e:
                    logger.error(f"❌ Error downloading batch at offset {offset}: {e}")
                    offset += limit
                    time.sleep(5)
    
    def create_orchid_from_gbif(self, gbif_data):
        """Create validated orchid record from GBIF species data"""
        
        try:
            # Extract basic taxonomic information
            scientific_name = gbif_data.get('scientificName', '')
            genus = gbif_data.get('genus', '')
            species = gbif_data.get('species', '')
            author = gbif_data.get('authorship', '')
            
            if not scientific_name or not genus:
                return False
            
            # Create display name
            display_name = scientific_name
            if author:
                display_name = f"{scientific_name} {author}"
            
            # Prepare record data for validation
            record_data = {
                'display_name': display_name,
                'scientific_name': scientific_name,
                'genus': genus,
                'species': species or '',
                'author': author,
                'ai_description': f"GBIF taxonomic record for {scientific_name}. GBIF Key: {gbif_data.get('key', 'Unknown')}",
                'ingestion_source': 'gbif_validated',
                'data_source': f"GBIF API - Species Key: {gbif_data.get('key', 'Unknown')}"
            }
            
            # Add additional GBIF metadata if available
            if gbif_data.get('taxonomicStatus'):
                record_data['ai_description'] += f" Status: {gbif_data.get('taxonomicStatus')}"
            
            if gbif_data.get('rank'):
                record_data['ai_description'] += f" Rank: {gbif_data.get('rank')}"
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "gbif_importer")
            
            if validated_data:
                try:
                    orchid_record = OrchidRecord()
                    orchid_record.display_name = validated_data['display_name']
                    orchid_record.scientific_name = validated_data['scientific_name']
                    orchid_record.genus = validated_data['genus']
                    orchid_record.species = validated_data.get('species', '')
                    orchid_record.author = validated_data.get('author', '')
                    orchid_record.ai_description = validated_data['ai_description']
                    orchid_record.ingestion_source = validated_data['ingestion_source']
                    orchid_record.data_source = validated_data['data_source']
                    orchid_record.created_at = datetime.utcnow()
                    orchid_record.updated_at = datetime.utcnow()
                    
                    db.session.add(orchid_record)
                    
                    logger.debug(f"   ✅ Created GBIF orchid: {scientific_name}")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Database error for {scientific_name}: {e}")
                    db.session.rollback()
                    return False
            else:
                logger.debug(f"❌ Validation failed for {scientific_name} (genus: {genus})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating GBIF record: {e}")
            return False
    
    def get_statistics(self):
        """Get import statistics"""
        return {
            'total_gbif_records': self.total_gbif_records,
            'collected_count': self.collected_count,
            'rejected_count': self.rejected_count,
            'success_rate': round((self.collected_count / self.total_gbif_records * 100) if self.total_gbif_records > 0 else 0, 2)
        }

if __name__ == "__main__":
    importer = GBIFOrchidImporter()
    importer.download_orchid_families()
    
    stats = importer.get_statistics()
    print(f"\n🎉 GBIF IMPORT COMPLETE!")
    print(f"📊 Total GBIF records processed: {stats['total_gbif_records']}")
    print(f"✅ Valid orchids collected: {stats['collected_count']}")
    print(f"❌ Invalid records rejected: {stats['rejected_count']}")
    print(f"📈 Success rate: {stats['success_rate']}%")