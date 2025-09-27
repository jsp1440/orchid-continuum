#!/usr/bin/env python3
"""
Simple Google Drive SVO Hybrid Importer
======================================
Direct import of SVO hybrid orchids bypassing strict validation
"""

import os
import logging
import re
from datetime import datetime
from app import app, db
from models import OrchidRecord
from google_drive_service import get_drive_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def simple_import_svo_hybrids():
    """Simple import of SVO hybrids from Google Drive folder"""
    
    folder_id = "1HbkrewzvoYcRlG_CPHYiNd-pJp1BIjM7"
    drive_service = get_drive_service()
    
    logger.info("🌺 STARTING SIMPLE SVO HYBRID IMPORT")
    
    with app.app_context():
        try:
            # Get folder contents
            results = drive_service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                pageSize=100,
                fields="files(id, name, mimeType)"
            ).execute()
            
            items = results.get('files', [])
            logger.info(f"📁 Found {len(items)} items in folder")
            
            collected = 0
            skipped = 0
            
            for item in items:
                if item.get('mimeType', '').startswith('image/'):
                    created = create_hybrid_record(item, folder_id)
                    if created:
                        collected += 1
                    else:
                        skipped += 1
                    
                    # Commit every 10 records
                    if collected % 10 == 0:
                        db.session.commit()
                        logger.info(f"   ✅ Committed batch: {collected} collected")
            
            # Final commit
            db.session.commit()
            
            logger.info(f"🎉 IMPORT COMPLETE!")
            logger.info(f"✅ Collected: {collected} SVO hybrid orchids")
            logger.info(f"⏭️ Skipped: {skipped} files")
            
        except Exception as e:
            logger.error(f"❌ Import error: {e}")
            db.session.rollback()

def create_hybrid_record(file_item, folder_id):
    """Create orchid record with minimal validation"""
    
    try:
        file_id = file_item['id']
        filename = file_item['name']
        
        # Clean filename for display
        clean_name = filename.replace('_', ' ').replace('-', ' ')
        clean_name = re.sub(r'\.(jpg|jpeg|png|gif)$', '', clean_name, flags=re.IGNORECASE)
        clean_name = re.sub(r'^\d+[A-Z]?\s+', '', clean_name)  # Remove numeric prefixes
        
        # Map common abbreviations
        if clean_name.startswith('Pot '):
            genus = 'Potinara'
            display_name = clean_name.replace('Pot ', 'Potinara ')
        elif clean_name.startswith('Blc '):
            genus = 'Brassolaeliocattleya'
            display_name = clean_name.replace('Blc ', 'Brassolaeliocattleya ')
        elif clean_name.startswith('Lc '):
            genus = 'Laeliocattleya'
            display_name = clean_name.replace('Lc ', 'Laeliocattleya ')
        else:
            # Extract first word as genus
            words = clean_name.split()
            genus = words[0] if words else 'Cattleya'
            display_name = clean_name
        
        # Check if already exists
        existing = OrchidRecord.query.filter_by(
            display_name=display_name
        ).first()
        
        if existing:
            logger.debug(f"   ⏭️ Already exists: {display_name}")
            return False
        
        # Create breeding description
        description = f"SVO Hybrid Collection: {display_name}. "
        description += f"Collected from Sunset Valley Orchids Google Drive archive. "
        if 'x' in clean_name.lower():
            description += "Cross breeding hybrid with documented parentage for AI analysis. "
        description += f"Source file: {filename}. [HYBRID] [SVO] [BREEDING] [GOOGLE_DRIVE]"
        
        # Create record
        orchid_record = OrchidRecord()
        orchid_record.display_name = display_name
        orchid_record.scientific_name = display_name
        orchid_record.genus = genus
        orchid_record.species = 'hybrid'
        orchid_record.image_url = f"https://drive.google.com/uc?export=view&id={file_id}"
        orchid_record.ai_description = description[:1000]
        orchid_record.ingestion_source = 'google_drive_svo_direct'
        orchid_record.image_source = f'SVO Google Drive Collection: {filename}'
        orchid_record.data_source = f"https://drive.google.com/drive/folders/{folder_id}"
        orchid_record.is_hybrid = True
        orchid_record.created_at = datetime.utcnow()
        orchid_record.updated_at = datetime.utcnow()
        
        db.session.add(orchid_record)
        
        logger.info(f"   ✅ Added: {display_name}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error processing {file_item.get('name', 'unknown')}: {e}")
        return False

if __name__ == "__main__":
    simple_import_svo_hybrids()