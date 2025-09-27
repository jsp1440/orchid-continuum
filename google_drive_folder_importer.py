#!/usr/bin/env python3
"""
Google Drive Folder Importer for SVO Hybrid Orchids
==================================================
Specialized importer for collecting SVO hybrid orchid images with breeding descriptions
from shared Google Drive folders
"""

import os
import logging
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record
from google_drive_service import get_drive_service

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class GoogleDriveFolderImporter:
    def __init__(self):
        self.drive_service = get_drive_service()
        self.validator = ScraperValidationSystem()
        self.collected_count = 0
        self.rejected_count = 0
        
        logger.info("🌺 GOOGLE DRIVE FOLDER IMPORTER INITIALIZED")
    
    def extract_folder_id(self, folder_url):
        """Extract folder ID from Google Drive folder URL"""
        try:
            # Parse various Google Drive folder URL formats
            if 'folders/' in folder_url:
                folder_id = folder_url.split('folders/')[-1].split('?')[0]
            elif 'folderview' in folder_url:
                parsed = urlparse(folder_url)
                folder_id = parse_qs(parsed.query).get('id', [None])[0]
            else:
                # Try to extract from other formats
                folder_id = folder_url.split('/')[-1].split('?')[0]
            
            logger.info(f"📁 Extracted folder ID: {folder_id}")
            return folder_id
            
        except Exception as e:
            logger.error(f"❌ Error extracting folder ID from {folder_url}: {e}")
            return None
    
    def import_from_folder(self, folder_url):
        """Import SVO hybrid orchids from Google Drive folder"""
        
        folder_id = self.extract_folder_id(folder_url)
        if not folder_id:
            logger.error("❌ Invalid folder URL")
            return
        
        logger.info(f"🔍 Starting import from Google Drive folder: {folder_id}")
        
        with app.app_context():
            try:
                # Get folder contents
                results = self.drive_service.files().list(
                    q=f"'{folder_id}' in parents and trashed=false",
                    pageSize=100,
                    fields="nextPageToken, files(id, name, mimeType, description, createdTime, modifiedTime, webViewLink, thumbnailLink, size)"
                ).execute()
                
                items = results.get('files', [])
                logger.info(f"📁 Found {len(items)} items in folder")
                
                for item in items:
                    # Debug: Show all files found
                    logger.debug(f"   📄 Found file: {item.get('name', 'Unknown')} (type: {item.get('mimeType', 'Unknown')})")
                    
                    if self.is_orchid_image(item):
                        logger.info(f"   🌺 Processing: {item.get('name', 'Unknown')}")
                        processed = self.process_orchid_file(item, folder_url)
                        if processed:
                            self.collected_count += 1
                        else:
                            self.rejected_count += 1
                        
                        # Commit every 5 records
                        if self.collected_count % 5 == 0:
                            db.session.commit()
                            logger.info(f"   ✅ Committed batch of 5 records")
                        
                        time.sleep(1)  # Be respectful to API
                    else:
                        logger.debug(f"   ⏭️ Skipping non-orchid file: {item.get('name', 'Unknown')}")
                
                # Final commit
                db.session.commit()
                
                logger.info(f"🎉 GOOGLE DRIVE IMPORT COMPLETE!")
                logger.info(f"✅ Collected: {self.collected_count} SVO hybrid orchids")
                logger.info(f"❌ Rejected: {self.rejected_count} invalid files")
                
            except Exception as e:
                logger.error(f"❌ Error importing from folder: {e}")
                db.session.rollback()
    
    def is_orchid_image(self, file_item):
        """Check if file is likely an orchid image"""
        
        name = file_item.get('name', '').lower()
        mime_type = file_item.get('mimeType', '')
        
        # Check if it's an image file
        if not mime_type.startswith('image/'):
            return False
        
        # Look for orchid/hybrid indicators in filename (expanded to include abbreviations)
        orchid_indicators = [
            # Full genus names
            'orchid', 'hybrid', 'svo', 'sunset', 'valley', 'breeding',
            'cattleya', 'dendrobium', 'phalaenopsis', 'oncidium', 'vanda',
            'paphiopedilum', 'cymbidium', 'miltonia', 'cross', 'grex',
            'laelia', 'epidendrum', 'brassavola', 'sophronitis', 'encyclia',
            'bulbophyllum', 'masdevallia', 'maxillaria', 'prosthechea',
            # Common abbreviations found in SVO files
            '_c ', '_l ', '_epi ', '_den ', '_phal ', '_onc ', '_van ',
            '_paph ', '_cym ', '_mil ', '_brs ', '_soph ', '_enc ', '_bulb ',
            '_masd ', '_max ', '_pro ', '_nagiela', '_pot ', '_blc ', '_slc ',
            # Also check without underscore for filenames like "3055C_"
            'c_', 'l_', 'epi_', 'den_', 'phal_', 'onc_', 'van_', 'paph_',
            'cym_', 'mil_', 'brs_', 'soph_', 'enc_', 'bulb_', 'masd_',
            'max_', 'pro_', 'nagiela', 'pot_', 'blc_', 'slc_'
        ]
        
        # Also check for pattern like "2994T_C " or "3055_L " (number + optional letter + underscore + genus abbreviation)
        import re
        pattern = r'\d+[A-Z]*_[A-Z]+ '
        if re.search(pattern, name.upper()):
            return True
        
        return any(indicator in name for indicator in orchid_indicators)
    
    def process_orchid_file(self, file_item, source_folder):
        """Process an orchid file and create database record"""
        
        try:
            file_id = file_item['id']
            file_name = file_item['name']
            description = file_item.get('description', '')
            
            logger.info(f"   🌺 Processing: {file_name}")
            
            # Extract orchid information from filename and description
            orchid_info = self.extract_orchid_info(file_name, description)
            
            if not orchid_info:
                logger.debug(f"   ❌ Could not extract orchid info from {file_name}")
                return False
            
            # Build Google Drive image URL
            image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
            
            # Create breeding description
            breeding_description = self.create_breeding_description(
                file_name, description, orchid_info
            )
            
            # Prepare record data for validation
            record_data = {
                'display_name': orchid_info['name'],
                'scientific_name': orchid_info['scientific_name'],
                'genus': orchid_info['genus'],
                'species': orchid_info.get('species', ''),
                'image_url': image_url,
                'ai_description': breeding_description,
                'ingestion_source': 'google_drive_svo_hybrids',
                'image_source': f'Google Drive SVO Collection: {file_name}',
                'data_source': source_folder,
                'is_hybrid': True
            }
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "drive_folder_importer")
            
            if validated_data:
                try:
                    orchid_record = OrchidRecord()
                    orchid_record.display_name = validated_data['display_name']
                    orchid_record.scientific_name = validated_data['scientific_name']
                    orchid_record.genus = validated_data['genus']
                    orchid_record.species = validated_data.get('species', '')
                    orchid_record.image_url = validated_data.get('image_url', '')
                    orchid_record.ai_description = validated_data['ai_description']
                    orchid_record.ingestion_source = validated_data['ingestion_source']
                    orchid_record.image_source = validated_data['image_source']
                    orchid_record.data_source = validated_data['data_source']
                    orchid_record.is_hybrid = True
                    orchid_record.created_at = datetime.utcnow()
                    orchid_record.updated_at = datetime.utcnow()
                    
                    db.session.add(orchid_record)
                    
                    logger.debug(f"   ✅ Created SVO hybrid: {orchid_info['name'][:50]}...")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Database error for {file_name}: {e}")
                    db.session.rollback()
                    return False
            else:
                logger.debug(f"❌ Validation failed for {file_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error processing {file_item.get('name', 'unknown')}: {e}")
            return False
    
    def extract_orchid_info(self, filename, description):
        """Extract orchid name and taxonomy from filename and description"""
        
        try:
            # Clean filename
            clean_name = filename.replace('_', ' ').replace('-', ' ')
            clean_name = re.sub(r'\.(jpg|jpeg|png|gif)$', '', clean_name, flags=re.IGNORECASE)
            
            # Remove numeric prefixes like "2811T" or "2811"
            clean_name = re.sub(r'^\d+[A-Z]?\s+', '', clean_name)
            
            # Common hybrid abbreviations mapping
            hybrid_abbreviations = {
                'Pot': 'Potinara',
                'Blc': 'Brassolaeliocattleya', 
                'Lc': 'Laeliocattleya',
                'Slc': 'Sophrolaeliocattleya',
                'Bc': 'Brassocattleya',
                'Rlc': 'Rhyncholaeliocattleya',
                'C': 'Cattleya',
                'Den': 'Dendrobium',
                'Phal': 'Phalaenopsis',
                'Onc': 'Oncidium',
                'V': 'Vanda',
                'Paph': 'Paphiopedilum',
                'Cym': 'Cymbidium',
                'Milt': 'Miltonia',
                'Zygo': 'Zygopetalum',
                'Sarc': 'Sarcochilus'
            }
            
            # Look for genus patterns - check abbreviations first
            genus = None
            words = clean_name.split()
            if words:
                first_word = words[0]
                # Check if first word is a hybrid abbreviation
                if first_word in hybrid_abbreviations:
                    genus = hybrid_abbreviations[first_word]
                else:
                    # Look for full genus names
                    genus_patterns = [
                        r'\b(Cattleya|Dendrobium|Phalaenopsis|Oncidium|Vanda|Paphiopedilum|Cymbidium|Miltonia|Zygopetalum|Sarcochilus|Potinara|Brassolaeliocattleya|Laeliocattleya|Sophrolaeliocattleya|Brassocattleya|Rhyncholaeliocattleya)\b'
                    ]
                    
                    for pattern in genus_patterns:
                        match = re.search(pattern, clean_name, re.IGNORECASE)
                        if match:
                            genus = match.group(1).capitalize()
                            break
                    
                    # If still no genus, try first capitalized word
                    if not genus and first_word.isalpha():
                        genus = first_word.capitalize()
            
            # Create scientific name - keep the hybrid cross notation
            scientific_name = clean_name.strip()
            if not scientific_name:
                scientific_name = f"{genus} hybrid" if genus else "Orchid hybrid"
            
            # For hybrids, species is usually 'hybrid' or the cross name
            species = "hybrid"
            if 'x' in clean_name.lower():
                species = "hybrid"
            
            return {
                'name': scientific_name,
                'scientific_name': scientific_name,
                'genus': genus or 'Potinara',  # Default to Potinara for SVO hybrids
                'species': species
            }
            
        except Exception as e:
            logger.error(f"❌ Error extracting orchid info: {e}")
            return None
    
    def create_breeding_description(self, filename, description, orchid_info):
        """Create enhanced breeding description for AI analysis"""
        
        enhanced = f"SVO Hybrid Collection: {orchid_info['name']}. "
        
        # Add description if available
        if description and len(description.strip()) > 10:
            enhanced += f"Description: {description.strip()} "
        
        # Add filename context
        if filename and filename != orchid_info['name']:
            enhanced += f"Source file: {filename}. "
        
        # Add breeding context
        enhanced += "Collected from Sunset Valley Orchids hybrid collection via Google Drive. "
        
        # Look for breeding indicators in text
        combined_text = f"{filename} {description}".lower()
        if any(indicator in combined_text for indicator in ['cross', 'breeding', 'parentage', 'hybrid']):
            enhanced += "Contains breeding information suitable for AI analysis. "
        
        # Add AI analysis tags
        enhanced += "[HYBRID] [SVO] [BREEDING] [GOOGLE_DRIVE]"
        
        return enhanced[:1000]  # Limit length

def main():
    """Main function to run the Google Drive folder importer"""
    
    # SVO hybrid folder from user
    folder_url = "https://drive.google.com/drive/folders/1HbkrewzvoYcRlG_CPHYiNd-pJp1BIjM7"
    
    importer = GoogleDriveFolderImporter()
    importer.import_from_folder(folder_url)

if __name__ == "__main__":
    main()