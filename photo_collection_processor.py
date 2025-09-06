#!/usr/bin/env python3
"""
Photo Collection Processor for Five Cities Orchid Society
Processes large photo collections and matches them with taxonomy database
"""

import logging
import re
import os
from typing import Dict, List, Optional, Tuple
from app import app, db
from models import OrchidRecord
from datetime import datetime
import requests

logger = logging.getLogger(__name__)

class PhotoCollectionProcessor:
    """Process photo collections and match with existing taxonomy"""
    
    def __init__(self):
        self.processed_count = 0
        self.matched_count = 0
        self.new_records_count = 0
        self.error_count = 0
    
    def extract_orchid_info_from_filename(self, filename: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """Extract genus, species, and additional info from filename patterns"""
        if not filename:
            return None, None, None
        
        try:
            # Remove file extension
            name = filename.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').replace('.JPG', '')
            
            # Common patterns in Chris Howard collections
            patterns = [
                # "Aer. crassifolia_413.jpg" -> Aeranthes crassifolia
                r'^([A-Z][a-z]{2,3})\.\s*([a-z]+)',
                # "Aca. mantinianum_20.jpg" -> Acampe mantinianum  
                r'^([A-Z][a-z]{2,3})\.\s*([a-z]+)',
                # "Phalaenopsis amabilis var. alba"
                r'^([A-Z][a-z]+)\s+([a-z]+)',
                # "Dendrobium nobile"
                r'^([A-Z][a-z]+)\s+([a-z]+)',
                # Handle abbreviated genus names
                r'^([A-Z][a-z]{1,4})\.\s*([a-z]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, name)
                if match:
                    genus_abbrev = match.group(1)
                    species = match.group(2)
                    
                    # Expand common genus abbreviations
                    genus_expansions = {
                        'Aer': 'Aeranthes',
                        'Aca': 'Acampe', 
                        'Phal': 'Phalaenopsis',
                        'Den': 'Dendrobium',
                        'Cat': 'Cattleya',
                        'Cyc': 'Cycnoches',
                        'Cyp': 'Cypripedium',
                        'Enc': 'Encyclia',
                        'Epi': 'Epidendrum',
                        'Max': 'Maxillaria',
                        'Onc': 'Oncidium',
                        'Paph': 'Paphiopedilum',
                        'Van': 'Vanda'
                    }
                    
                    genus = genus_expansions.get(genus_abbrev, genus_abbrev)
                    
                    # Extract additional info (clone numbers, variety info)
                    additional_info = name.replace(match.group(0), '').strip('_').strip()
                    
                    return genus, species, additional_info
            
            logger.warning(f"Could not parse orchid info from filename: {filename}")
            return None, None, None
            
        except Exception as e:
            logger.error(f"Error parsing filename '{filename}': {e}")
            return None, None, None
    
    def find_matching_taxonomy_record(self, genus: str, species: str) -> Optional[OrchidRecord]:
        """Find existing taxonomy record that matches this photo"""
        try:
            # Look for exact match first
            exact_match = db.session.query(OrchidRecord).filter(
                OrchidRecord.genus == genus,
                OrchidRecord.species == species,
                OrchidRecord.data_source == 'Master Taxonomy Database'
            ).first()
            
            if exact_match:
                return exact_match
            
            # Look for genus match with similar species
            genus_matches = db.session.query(OrchidRecord).filter(
                OrchidRecord.genus == genus,
                OrchidRecord.data_source == 'Master Taxonomy Database'
            ).all()
            
            for record in genus_matches:
                if record.species and species in record.species:
                    return record
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding taxonomy match for {genus} {species}: {e}")
            return None
    
    def create_or_update_orchid_record(self, genus: str, species: str, photo_id: str, 
                                     photographer: str = None, additional_info: str = None) -> Optional[OrchidRecord]:
        """Create new orchid record or update existing with photo"""
        try:
            # Check if record with this photo already exists
            existing = db.session.query(OrchidRecord).filter(
                OrchidRecord.google_drive_id == photo_id
            ).first()
            
            if existing:
                logger.info(f"Photo {photo_id} already exists in database")
                return existing
            
            # Try to find matching taxonomy record
            taxonomy_match = self.find_matching_taxonomy_record(genus, species)
            
            if taxonomy_match and not taxonomy_match.google_drive_id:
                # Update existing taxonomy record with photo
                taxonomy_match.google_drive_id = photo_id
                taxonomy_match.photographer = photographer or 'Collection'
                taxonomy_match.image_source = 'Photo Collection'
                taxonomy_match.validation_status = 'photo_matched'
                if additional_info:
                    taxonomy_match.ai_description = f"Collection specimen: {additional_info}"
                taxonomy_match.updated_at = datetime.utcnow()
                
                self.matched_count += 1
                logger.info(f"✅ Matched photo to taxonomy: {genus} {species}")
                return taxonomy_match
            
            else:
                # Create new record
                orchid = OrchidRecord()
                orchid.display_name = f"{genus} {species}" + (f" {additional_info}" if additional_info else "")
                orchid.genus = genus
                orchid.species = species
                orchid.google_drive_id = photo_id
                orchid.photographer = photographer or 'Collection'
                orchid.image_source = 'Photo Collection'
                orchid.data_source = 'Photo Collection'
                orchid.ingestion_source = 'Five Cities Orchid Society Photo Archive'
                orchid.validation_status = 'photo_added'
                if additional_info:
                    orchid.ai_description = f"Collection specimen: {additional_info}"
                orchid.created_at = datetime.utcnow()
                orchid.updated_at = datetime.utcnow()
                
                db.session.add(orchid)
                self.new_records_count += 1
                logger.info(f"🆕 Created new record: {genus} {species}")
                return orchid
                
        except Exception as e:
            logger.error(f"Error creating/updating record for {genus} {species}: {e}")
            return None
    
    def process_photo_collection(self, photo_list: List[Dict[str, str]], collection_name: str = "Photo Collection") -> Dict[str, int]:
        """Process a list of photos with metadata"""
        try:
            logger.info(f"Processing {collection_name} with {len(photo_list)} photos")
            
            for photo_info in photo_list:
                try:
                    filename = photo_info.get('filename', '')
                    photo_id = photo_info.get('id', '')
                    photographer = photo_info.get('photographer', '')
                    
                    if not filename or not photo_id:
                        self.error_count += 1
                        continue
                    
                    # Extract orchid information from filename
                    genus, species, additional_info = self.extract_orchid_info_from_filename(filename)
                    
                    if not genus or not species:
                        logger.warning(f"Could not extract orchid info from: {filename}")
                        self.error_count += 1
                        continue
                    
                    # Create or update record
                    record = self.create_or_update_orchid_record(
                        genus, species, photo_id, photographer, additional_info
                    )
                    
                    if record:
                        self.processed_count += 1
                    else:
                        self.error_count += 1
                    
                    # Log progress
                    if self.processed_count % 50 == 0:
                        logger.info(f"Processed {self.processed_count} photos...")
                        
                except Exception as e:
                    logger.error(f"Error processing photo {filename}: {e}")
                    self.error_count += 1
                    continue
            
            # Commit all changes
            db.session.commit()
            
            return {
                'total_processed': self.processed_count,
                'matched_to_taxonomy': self.matched_count,
                'new_records_created': self.new_records_count,
                'errors': self.error_count
            }
            
        except Exception as e:
            logger.error(f"Error processing photo collection: {e}")
            db.session.rollback()
            return {'error': str(e)}

def test_filename_parsing():
    """Test the filename parsing with examples"""
    processor = PhotoCollectionProcessor()
    
    test_filenames = [
        "Aer. crassifolia_413.jpg",
        "Aca. mantinianum_20.jpg", 
        "Phalaenopsis amabilis var. alba.jpg",
        "Dendrobium nobile.JPG",
        "Cat. warscewiczii.png"
    ]
    
    print("🧪 Testing filename parsing:")
    for filename in test_filenames:
        genus, species, info = processor.extract_orchid_info_from_filename(filename)
        print(f"📁 {filename}")
        print(f"   → Genus: {genus}, Species: {species}, Info: {info}")
        print()

if __name__ == "__main__":
    test_filename_parsing()