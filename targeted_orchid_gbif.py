#!/usr/bin/env python3
"""
Targeted Orchid GBIF Importer
==============================
Ultra-focused orchid import system that ensures we only get actual orchids
Uses multiple validation layers to guarantee orchid species only
"""

import requests
import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from app import app, db
from models import OrchidRecord
from sqlalchemy import func

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetedOrchidGBIF:
    """
    Laser-focused GBIF integration that ONLY imports verified orchid species
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society - Targeted Import/1.0',
            'Accept': 'application/json'
        })
        
        # Verified orchid genera with high GBIF representation
        self.verified_orchid_genera = [
            'Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium', 'Cymbidium',
            'Orchis', 'Ophrys', 'Epidendrum', 'Bulbophyllum', 'Masdevallia',
            'Paphiopedilum', 'Vanda', 'Aerangis', 'Angraecum', 'Brassia',
            'Laelia', 'Miltonia', 'Odontoglossum', 'Vanilla', 'Pleurothallis'
        ]
        
        logger.info("🎯 Targeted Orchid GBIF Importer initialized")
    
    def get_verified_orchid_records(self, genus: str, limit: int = 50) -> List[Dict]:
        """
        Get verified orchid records for a specific genus
        Uses multiple validation steps to ensure orchid authenticity
        """
        try:
            # Search specifically for the genus with orchid validation
            params = {
                'genus': genus,
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': limit,
                'family': 'Orchidaceae'  # Double-check family
            }
            
            response = self.session.get(
                f"{self.base_url}/occurrence/search",
                params=params,
                timeout=30
            )
            
            if response.status_code != 200:
                logger.warning(f"❌ Search failed for {genus}: {response.status_code}")
                return []
            
            data = response.json()
            results = data.get('results', [])
            
            # Filter to ensure we only get actual orchids
            verified_orchids = []
            for record in results:
                if self._is_verified_orchid(record, genus):
                    verified_orchids.append(record)
            
            logger.info(f"✅ {genus}: Found {len(verified_orchids)} verified orchid records")
            return verified_orchids
            
        except Exception as e:
            logger.error(f"❌ Error getting {genus} records: {e}")
            return []
    
    def _is_verified_orchid(self, record: Dict, expected_genus: str) -> bool:
        """
        Multi-layer validation to ensure this is actually an orchid
        """
        # Check 1: Scientific name must contain expected genus
        scientific_name = record.get('scientificName', '').lower()
        if expected_genus.lower() not in scientific_name:
            return False
        
        # Check 2: Family must be Orchidaceae (if provided)
        family = record.get('family', '').lower()
        if family and 'orchidaceae' not in family:
            return False
        
        # Check 3: Genus field must match
        genus = record.get('genus', '').lower()
        if genus and genus != expected_genus.lower():
            return False
        
        # Check 4: Must have images
        media = record.get('media', [])
        if not media:
            return False
        
        # Check 5: Scientific name should have species (genus + species)
        name_parts = scientific_name.split()
        if len(name_parts) < 2:
            return False
        
        return True
    
    def import_targeted_orchids(self, max_per_genus: int = 20, max_total: int = 500) -> Dict:
        """
        Import a targeted batch of verified orchids
        """
        results = {
            'imported': 0,
            'skipped': 0,
            'errors': 0,
            'genera_processed': 0
        }
        
        logger.info(f"🚀 Starting targeted orchid import (max {max_total} total)")
        
        with app.app_context():
            for genus in self.verified_orchid_genera:
                if results['imported'] >= max_total:
                    break
                
                logger.info(f"🔍 Processing genus: {genus}")
                
                # Get verified records for this genus
                records = self.get_verified_orchid_records(genus, max_per_genus)
                
                for record in records:
                    if results['imported'] >= max_total:
                        break
                    
                    try:
                        # Check if we already have this GBIF record
                        gbif_id = record.get('gbifID')
                        if gbif_id:
                            existing = OrchidRecord.query.filter_by(gbif_id=gbif_id).first()
                            if existing:
                                results['skipped'] += 1
                                continue
                        
                        # Create new orchid record
                        orchid = self._create_orchid_from_gbif(record)
                        if orchid:
                            db.session.add(orchid)
                            results['imported'] += 1
                            logger.info(f"  ✅ Imported: {orchid.genus} {orchid.species}")
                        else:
                            results['errors'] += 1
                    
                    except Exception as e:
                        logger.error(f"  ❌ Error importing record: {e}")
                        results['errors'] += 1
                
                results['genera_processed'] += 1
                
                # Commit every genus to avoid losing progress
                try:
                    db.session.commit()
                except Exception as e:
                    logger.error(f"❌ Commit error for {genus}: {e}")
                    db.session.rollback()
        
        logger.info(f"🎉 Import complete: {results['imported']} imported, {results['skipped']} skipped, {results['errors']} errors")
        return results
    
    def _create_orchid_from_gbif(self, record: Dict) -> Optional[OrchidRecord]:
        """
        Create an OrchidRecord from a GBIF record
        """
        try:
            orchid = OrchidRecord()
            
            # Basic taxonomy
            scientific_name = record.get('scientificName', '')
            orchid.scientific_name = scientific_name
            orchid.genus = record.get('genus', '')
            orchid.species = record.get('species', '')
            
            # Display name
            if orchid.genus and orchid.species:
                orchid.display_name = f"{orchid.genus} {orchid.species}"
            else:
                orchid.display_name = scientific_name
            
            # Geographic data
            orchid.region = record.get('country', '')
            orchid.native_habitat = record.get('locality', '')
            if record.get('decimalLatitude') and record.get('decimalLongitude'):
                lat = record.get('decimalLatitude')
                lon = record.get('decimalLongitude')
                if orchid.native_habitat:
                    orchid.native_habitat += f" (Lat: {lat}, Lon: {lon})"
                else:
                    orchid.native_habitat = f"Coordinates: {lat}, {lon}"
            
            # Image data
            media = record.get('media', [])
            if media and len(media) > 0:
                # Use the first image
                image_info = media[0]
                image_url = image_info.get('identifier')
                if image_url:
                    orchid.image_url = image_url
            
            # Metadata and source info
            institution = record.get('institutionCode', '') or record.get('publishingOrganization', '')
            collector = record.get('recordedBy', '')
            date = record.get('eventDate', '')
            
            orchid.ai_description = f"GBIF specimen from {institution}. "
            if collector:
                orchid.ai_description += f"Collected by {collector}. "
            if date:
                orchid.ai_description += f"Collection date: {date}. "
            if orchid.native_habitat:
                orchid.ai_description += f"Location: {orchid.native_habitat}."
            
            # Source tracking
            orchid.data_source = 'GBIF Targeted Import'
            orchid.gbif_id = record.get('gbifID')
            orchid.validation_status = 'validated'
            
            # Collection details
            orchid.collector = collector
            orchid.collection_date = date
            
            return orchid
            
        except Exception as e:
            logger.error(f"❌ Error creating orchid record: {e}")
            return None

# Quick test function
def run_targeted_import_test():
    """Test the targeted import system"""
    importer = TargetedOrchidGBIF()
    results = importer.import_targeted_orchids(max_per_genus=5, max_total=25)
    return results

if __name__ == "__main__":
    with app.app_context():
        results = run_targeted_import_test()
        print(f"Test import results: {results}")
