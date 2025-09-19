#!/usr/bin/env python3
"""
GBIF Orchid Integration System
==============================
Comprehensive orchid data collection from GBIF (Global Biodiversity Information Facility)
Part of The Orchid Continuum - Five Cities Orchid Society

Features:
- GBIF API integration with authentication
- Orchid occurrence and species data retrieval  
- Geographic and taxonomic data processing
- Proper scientific attribution and citations
- Integration with existing OrchidRecord schema
"""

import requests
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from app import app, db
from models import OrchidRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GBIFOrchidIntegrator:
    """
    GBIF API integration for comprehensive orchid data collection
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        # GBIF API is mostly public access - no auth needed for most endpoints
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'The Orchid Continuum - Five Cities Orchid Society/1.0',
            'Accept': 'application/json'
        })
        
        logger.info("🌍 GBIF API configured - using public access (no key required)")
    
    def search_orchid_occurrences(self, limit: int = 100, offset: int = 0, 
                                country: Optional[str] = None) -> Dict[str, Any]:
        """
        Search GBIF for orchid occurrence records
        
        Args:
            limit: Number of records to retrieve (max 300)
            offset: Starting offset for pagination
            country: ISO country code to filter by location
            
        Returns:
            GBIF API response with occurrence data
        """
        try:
            # GBIF search for Orchidaceae family
            params = {
                'familyKey': 7711,  # Orchidaceae family key in GBIF
                'hasCoordinate': True,  # Only records with coordinates
                'hasGeospatialIssue': False,  # Clean geographic data
                'limit': min(limit, 300),  # GBIF max limit
                'offset': offset
            }
            
            if country:
                params['country'] = country
            
            url = f"{self.base_url}/occurrence/search"
            
            logger.info(f"🔍 Searching GBIF orchid occurrences (limit={limit}, offset={offset})")
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Found {data.get('count', 0)} total orchid occurrences")
            return data
            
        except Exception as e:
            logger.error(f"❌ GBIF occurrence search error: {e}")
            return {}
    
    def get_species_details(self, species_key: str) -> Dict[str, Any]:
        """
        Get detailed species information from GBIF
        
        Args:
            species_key: GBIF species key
            
        Returns:
            Species details including taxonomy, vernacular names, etc.
        """
        try:
            url = f"{self.base_url}/species/{species_key}"
            
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Species details error for {species_key}: {e}")
            return {}
    
    def get_vernacular_names(self, species_key: str) -> List[Dict[str, Any]]:
        """
        Get common/vernacular names for a species
        
        Args:
            species_key: GBIF species key
            
        Returns:
            List of vernacular names with languages
        """
        try:
            url = f"{self.base_url}/species/{species_key}/vernacularNames"
            
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            return data.get('results', [])
            
        except Exception as e:
            logger.error(f"❌ Vernacular names error for {species_key}: {e}")
            return []
    
    def process_occurrence_record(self, occurrence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a GBIF occurrence record into OrchidRecord format
        
        Args:
            occurrence: Raw GBIF occurrence record
            
        Returns:
            Processed orchid data for database storage
        """
        try:
            # Extract basic taxonomic information
            scientific_name = occurrence.get('scientificName', '')
            genus = occurrence.get('genus', '')
            specific_epithet = occurrence.get('specificEpithet', '')
            
            # Be more flexible with GBIF data - just need scientific name
            if not scientific_name:
                logger.warning("❌ Skipping occurrence - no scientific name")
                return None
                
            # Extract genus from scientific name if not provided separately
            if not genus and scientific_name:
                genus_parts = scientific_name.split()
                if len(genus_parts) >= 1:
                    genus = genus_parts[0]
            
            # Build species name
            species_name = f"{genus} {specific_epithet}" if specific_epithet else genus
            
            # Extract geographic information
            country = occurrence.get('country', '')
            latitude = occurrence.get('decimalLatitude')
            longitude = occurrence.get('decimalLongitude')
            locality = occurrence.get('locality', '')
            
            # Extract date information
            event_date = occurrence.get('eventDate')
            date_collected = None
            if event_date:
                try:
                    date_collected = datetime.fromisoformat(event_date.replace('Z', '+00:00'))
                except:
                    pass
            
            # Extract collection information
            collector = occurrence.get('recordedBy', '')
            institution = occurrence.get('institutionCode', '')
            catalog_number = occurrence.get('catalogNumber', '')
            
            # Extract identification information
            identified_by = occurrence.get('identifiedBy', '')
            
            # Build processed record
            processed_record = {
                'scientific_name': scientific_name,
                'genus': genus,
                'species': specific_epithet or '',
                'common_name': '',  # Will be filled from vernacular names
                'family': 'Orchidaceae',
                'country': country,
                'location': locality,
                'habitat': occurrence.get('habitat', ''),
                'elevation': occurrence.get('elevation'),
                'date_collected': date_collected,
                'collector': collector,
                'identified_by': identified_by,
                'institution': institution,
                'catalog_number': catalog_number,
                'gbif_id': occurrence.get('gbifID'),
                'gbif_occurrence_id': occurrence.get('key'),
                'gbif_dataset_id': occurrence.get('datasetKey'),
                'data_source': 'GBIF',
                'source_url': f"https://www.gbif.org/occurrence/{occurrence.get('key')}",
                'latitude': latitude,
                'longitude': longitude,
                'coordinate_precision': occurrence.get('coordinateUncertaintyInMeters'),
                'basis_of_record': occurrence.get('basisOfRecord', ''),
                'occurrence_status': occurrence.get('occurrenceStatus', ''),
                'establishment_means': occurrence.get('establishmentMeans', ''),
            }
            
            return processed_record
            
        except Exception as e:
            logger.error(f"❌ Error processing occurrence record: {e}")
            return None
    
    def save_orchid_record(self, orchid_data: Dict[str, Any]) -> bool:
        """
        Save processed orchid data to database
        
        Args:
            orchid_data: Processed orchid record data
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with app.app_context():
                # Check if record already exists (avoid duplicates)
                existing = None
                if orchid_data.get('gbif_occurrence_id'):
                    existing = OrchidRecord.query.filter_by(
                        image_url=orchid_data['source_url']
                    ).first()
                
                if existing:
                    logger.info(f"⚠️ Skipping duplicate record: {orchid_data['scientific_name']}")
                    return False
                
                # Create new OrchidRecord
                orchid = OrchidRecord()
                orchid.display_name = orchid_data['scientific_name'] 
                orchid.scientific_name = orchid_data['scientific_name']
                orchid.genus = orchid_data['genus']
                orchid.species = orchid_data['species']
                orchid.region = orchid_data['country']
                orchid.native_habitat = orchid_data['location']
                orchid.cultural_notes = f"GBIF ID: {orchid_data.get('gbif_id', 'N/A')} | Institution: {orchid_data['institution']} | Basis: {orchid_data.get('basis_of_record', 'N/A')} | Common: {orchid_data['common_name']}"
                orchid.ingestion_source = 'gbif'
                orchid.image_url = orchid_data['source_url']  # GBIF URL for reference
                orchid.created_at = datetime.now()
                
                db.session.add(orchid)
                db.session.commit()
                
                logger.info(f"✅ Saved: {orchid_data['scientific_name']} ({orchid_data['country']})")
                return True
                
        except Exception as e:
            logger.error(f"❌ Database save error: {e}")
            db.session.rollback()
            return False
    
    def collect_orchid_batch(self, batch_size: int = 100, max_records: int = 1000,
                           country: Optional[str] = None) -> Dict[str, int]:
        """
        Collect a batch of orchid records from GBIF
        
        Args:
            batch_size: Records per API call
            max_records: Maximum total records to collect
            country: ISO country code to filter by
            
        Returns:
            Statistics about collection process
        """
        stats = {
            'total_found': 0,
            'processed': 0,
            'saved': 0,
            'errors': 0,
            'duplicates': 0
        }
        
        try:
            logger.info(f"🌍 Starting GBIF orchid collection (max: {max_records} records)")
            
            offset = 0
            collected = 0
            
            while collected < max_records:
                # Calculate remaining records to collect
                remaining = max_records - collected
                current_batch = min(batch_size, remaining)
                
                # Get batch of occurrence records
                response = self.search_orchid_occurrences(
                    limit=current_batch, 
                    offset=offset, 
                    country=country
                )
                
                if not response or 'results' not in response:
                    logger.warning("⚠️ No more results available")
                    break
                
                occurrences = response['results']
                stats['total_found'] = response.get('count', 0)
                
                if not occurrences:
                    logger.info("✅ No more occurrence records")
                    break
                
                logger.info(f"📋 Processing batch: {len(occurrences)} records (offset: {offset})")
                
                # Process each occurrence in the batch
                for occurrence in occurrences:
                    try:
                        # Process the occurrence record
                        orchid_data = self.process_occurrence_record(occurrence)
                        stats['processed'] += 1
                        
                        if orchid_data:
                            # Try to get common names if species key is available
                            species_key = occurrence.get('speciesKey')
                            if species_key:
                                vernacular_names = self.get_vernacular_names(species_key)
                                if vernacular_names:
                                    # Use first English common name if available
                                    english_names = [v['vernacularName'] for v in vernacular_names 
                                                   if v.get('language') == 'en']
                                    if english_names:
                                        orchid_data['common_name'] = english_names[0]
                            
                            # Save to database
                            if self.save_orchid_record(orchid_data):
                                stats['saved'] += 1
                            else:
                                stats['duplicates'] += 1
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing occurrence: {e}")
                        stats['errors'] += 1
                    
                    collected += 1
                    if collected >= max_records:
                        break
                
                # Prepare for next batch
                offset += len(occurrences)
                
                # Rate limiting - be respectful to GBIF
                time.sleep(0.5)
            
            logger.info(f"🎯 GBIF Collection Complete!")
            logger.info(f"   📊 Found: {stats['total_found']:,} total records")
            logger.info(f"   ✅ Processed: {stats['processed']} records")
            logger.info(f"   💾 Saved: {stats['saved']} new records")
            logger.info(f"   ⚠️ Duplicates: {stats['duplicates']} records")
            logger.info(f"   ❌ Errors: {stats['errors']} records")
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ GBIF collection error: {e}")
            return stats

def run_gbif_collection(max_records: int = 1000, country: Optional[str] = None):
    """
    Run GBIF orchid collection process
    
    Args:
        max_records: Maximum records to collect
        country: ISO country code filter (e.g., 'US', 'BR', 'AU')
    """
    integrator = GBIFOrchidIntegrator()
    
    logger.info("🌍 GBIF ORCHID INTEGRATION SYSTEM")
    logger.info("=" * 50)
    
    logger.info("🔓 Using GBIF public API - full access available")
    
    stats = integrator.collect_orchid_batch(
        batch_size=100,
        max_records=max_records,
        country=country
    )
    
    return stats

if __name__ == "__main__":
    # Test run - collect 500 orchid records
    run_gbif_collection(max_records=500)