#!/usr/bin/env python3
"""
Taxonomy Database Importer
Import the comprehensive 30,000+ species orchid taxonomy database
"""

import os
import csv
import logging
import requests
from io import StringIO
from typing import Dict, List, Any, Optional
from app import app, db
from models import OrchidRecord
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class TaxonomyDatabaseImporter:
    """Import system for the comprehensive orchid taxonomy database"""
    
    def __init__(self):
        self.processed_count = 0
        self.error_count = 0
        self.taxonomy_records = []
        self.orchid_records = []
    
    def download_taxonomy_csv(self, file_id: str = "1-tabVTYi22Fq_jY_rtK8wEYXxbcu1KWW") -> Optional[str]:
        """Download the taxonomy CSV from Google Drive"""
        try:
            # Google Drive direct download URL
            download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
            
            logger.info(f"Downloading taxonomy database from {file_id}")
            response = requests.get(download_url, timeout=30)
            
            if response.status_code == 200:
                logger.info(f"Successfully downloaded taxonomy database ({len(response.text)} characters)")
                return response.text
            else:
                logger.error(f"Failed to download: HTTP {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading taxonomy database: {e}")
            return None
    
    def parse_taxonomy_record(self, row: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """Parse a single taxonomy record from CSV"""
        try:
            # Extract basic taxonomy information
            taxon_type = row.get('Taxon', '').strip()
            number = row.get('Number', '').strip()
            name = row.get('Name', '').strip()
            literature = row.get('Literature', '').strip()
            trivial_name = row.get('TrivialName', '').strip()
            distribution = row.get('Distribution', '').strip()
            synonyms = row.get('Synonyms', '').strip()
            status = row.get('Status', '').strip()
            remarks = row.get('Remarks', '').strip()
            conservation_status = row.get('ConservationStatus', '').strip()
            photo = row.get('Photo', '').strip()
            author = row.get('Author', '').strip()
            gbif_link = row.get('GBIF_Link', '').strip()
            iospe_match = row.get('IOSPE_Match', '').strip()
            inaturalist_match = row.get('iNaturalist_Match', '').strip()
            
            # Parse genus and species from name
            genus, species = self.parse_genus_species(name, taxon_type)
            
            # Clean and normalize data
            parsed = {
                'taxon_type': taxon_type,
                'taxon_number': number,
                'full_name': name,
                'genus': genus,
                'species': species,
                'common_name': trivial_name,
                'literature_reference': literature,
                'native_habitat': distribution,
                'synonyms': synonyms,
                'taxonomic_status': status,
                'remarks': remarks,
                'conservation_status': conservation_status,
                'author': author,
                'gbif_link': gbif_link,
                'iospe_match': iospe_match,
                'inaturalist_match': inaturalist_match,
                'photo_reference': photo,
                'data_source': 'Master Taxonomy Database',
                'ingestion_source': 'Comprehensive Species Database'
            }
            
            return parsed
            
        except Exception as e:
            logger.error(f"Error parsing taxonomy record: {e}")
            return None
    
    def parse_genus_species(self, name: str, taxon_type: str) -> tuple:
        """Extract genus and species from taxonomic name"""
        try:
            if not name or taxon_type not in ['G', 'S', 'V']:  # Genus, Species, Variety
                return None, None
            
            # Remove author citations and extra info
            clean_name = re.sub(r'\s+\([^)]+\)', '', name)  # Remove parenthetical authors
            clean_name = re.sub(r'\s+[A-Z][a-z]+\.\s*$', '', clean_name)  # Remove trailing authors
            clean_name = clean_name.strip()
            
            parts = clean_name.split()
            
            if taxon_type == 'G':  # Genus
                return parts[0] if parts else None, None
            elif taxon_type == 'S' or taxon_type == 'V':  # Species or Variety
                if len(parts) >= 2:
                    return parts[0], parts[1]
                elif len(parts) == 1:
                    return parts[0], None
            
            return None, None
            
        except Exception as e:
            logger.error(f"Error parsing genus/species from '{name}': {e}")
            return None, None
    
    def create_orchid_record_from_taxonomy(self, parsed_data: Dict[str, Any]) -> Optional[OrchidRecord]:
        """Create an OrchidRecord from taxonomy data"""
        try:
            # Only create OrchidRecord for species (not genera or families)
            if (parsed_data.get('taxon_type') not in ['S', 'V'] or 
                not parsed_data.get('genus') or 
                not parsed_data.get('species')):
                return None
            
            orchid = OrchidRecord()
            orchid.display_name = parsed_data.get('common_name') or f"{parsed_data.get('genus')} {parsed_data.get('species')}"
            orchid.genus = parsed_data.get('genus')
            orchid.species = parsed_data.get('species')
            orchid.author = parsed_data.get('author')
            orchid.native_habitat = parsed_data.get('native_habitat')
            orchid.conservation_status = parsed_data.get('conservation_status')
            orchid.data_source = parsed_data.get('data_source')
            orchid.ingestion_source = parsed_data.get('ingestion_source')
            orchid.validation_status = 'taxonomy_verified'
            orchid.taxonomic_notes = parsed_data.get('remarks')
            orchid.created_at = datetime.utcnow()
            orchid.updated_at = datetime.utcnow()
            
            return orchid
            
        except Exception as e:
            logger.error(f"Error creating orchid record from taxonomy: {e}")
            return None
    
    
    def import_taxonomy_database(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Import the complete taxonomy database"""
        try:
            logger.info("Starting comprehensive taxonomy database import")
            
            # Download the CSV data
            csv_data = self.download_taxonomy_csv()
            if not csv_data:
                return {'success': False, 'error': 'Could not download taxonomy database'}
            
            # Parse CSV
            csv_reader = csv.DictReader(StringIO(csv_data))
            
            orchid_records = []
            
            for i, row in enumerate(csv_reader):
                if limit and i >= limit:
                    break
                
                # Parse the record
                parsed = self.parse_taxonomy_record(row)
                if not parsed:
                    self.error_count += 1
                    continue
                
                # Create orchid record for species-level entries
                orchid = self.create_orchid_record_from_taxonomy(parsed)
                if orchid:
                    orchid_records.append(orchid)
                
                self.processed_count += 1
                
                # Log progress
                if i % 1000 == 0:
                    logger.info(f"Processed {i} taxonomy records...")
            
            # Batch insert orchid records to database
            logger.info(f"Inserting {len(orchid_records)} orchid species records...")
            if orchid_records:
                db.session.bulk_save_objects(orchid_records)
                db.session.commit()
            
            return {
                'success': True,
                'total_processed': self.processed_count,
                'orchid_records': len(orchid_records),
                'errors': self.error_count
            }
            
        except Exception as e:
            logger.error(f"Error importing taxonomy database: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}

def import_taxonomy_database(limit: Optional[int] = None):
    """Convenience function to import taxonomy database"""
    
    with app.app_context():
        importer = TaxonomyDatabaseImporter()
        result = importer.import_taxonomy_database(limit)
        
        if result.get('success'):
            print(f"\n🌿 TAXONOMY DATABASE IMPORT COMPLETE")
            print(f"📊 Total Processed: {result.get('total_processed', 0)}")
            print(f"🌺 Orchid Species Records: {result.get('orchid_records', 0)}")
            print(f"❌ Errors: {result.get('errors', 0)}")
            print(f"\n✅ Authoritative taxonomy foundation established!")
        else:
            print(f"❌ Import failed: {result.get('error')}")
        
        return result

if __name__ == "__main__":
    # Test import with small batch first
    print("🧪 Testing taxonomy database import...")
    result = import_taxonomy_database(limit=100)