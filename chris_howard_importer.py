#!/usr/bin/env python3
"""
Chris Howard Photo Import System
Import ~1,075 orchid photos from Chris Howard's Google Drive collection.
"""

import requests
import re
from app import app, db
from models import OrchidRecord
from datetime import datetime
import logging
import time
from openai import OpenAI
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Chris Howard's Google Drive folder
CHRIS_FOLDER_ID = '1dJ5AbZ_iEdX4-SgHVA3RB-306meBedBu'

def extract_file_ids_from_folder(folder_id):
    """Extract Google Drive file IDs from a folder"""
    logger.info(f"Extracting file IDs from folder: {folder_id}")
    
    try:
        url = f'https://drive.google.com/embeddedfolderview?id={folder_id}'
        response = requests.get(url, timeout=20)
        
        if response.status_code != 200:
            logger.error(f"Unable to access folder: {response.status_code}")
            return []
        
        html = response.text
        
        # Extract file IDs using multiple patterns
        patterns = [
            r'file/d/([a-zA-Z0-9_-]{25,35})',  # Direct file links
            r'id=([a-zA-Z0-9_-]{25,35})',      # ID parameters
            r'"([a-zA-Z0-9_-]{25,35})"',       # Quoted IDs
        ]
        
        file_ids = set()
        for pattern in patterns:
            matches = re.findall(pattern, html)
            for match in matches:
                if len(match) >= 25 and match != folder_id:
                    file_ids.add(match)
        
        logger.info(f"Extracted {len(file_ids)} potential file IDs")
        return list(file_ids)
        
    except Exception as e:
        logger.error(f"Error extracting file IDs: {e}")
        return []

def test_photo_accessibility(file_ids, sample_size=10):
    """Test a sample of file IDs to see which are accessible photos"""
    logger.info(f"Testing photo accessibility for {min(sample_size, len(file_ids))} files...")
    
    working_photos = []
    sample_ids = file_ids[:sample_size]
    
    for i, file_id in enumerate(sample_ids, 1):
        try:
            photo_url = f'https://drive.google.com/uc?export=view&id={file_id}'
            response = requests.head(photo_url, timeout=5)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'image' in content_type:
                working_photos.append(file_id)
                logger.info(f"  {i:2d}. {file_id} ✅ Image")
            else:
                logger.info(f"  {i:2d}. {file_id} ❌ Not image ({content_type})")
                
        except Exception as e:
            logger.info(f"  {i:2d}. {file_id} ❌ Failed: {e}")
    
    success_rate = len(working_photos) / len(sample_ids) if sample_ids else 0
    estimated_total = int(len(file_ids) * success_rate) if success_rate > 0 else 0
    
    logger.info(f"Success rate: {len(working_photos)}/{len(sample_ids)} ({success_rate*100:.0f}%)")
    logger.info(f"Estimated working photos: ~{estimated_total}")
    
    return working_photos, success_rate, estimated_total

def analyze_photo_with_ai(photo_url):
    """Use AI to analyze orchid photo and extract metadata"""
    try:
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Analyze this orchid photo. Identify the species/genus if possible, describe key characteristics, growth habit, and any notable features. Provide scientific name if identifiable."
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": photo_url}
                        }
                    ]
                }
            ],
            max_tokens=300
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        return None

def create_orchid_record(file_id, ai_description=None):
    """Create an OrchidRecord from a Google Drive photo"""
    try:
        # Generate display name from AI analysis or use generic name
        if ai_description and len(ai_description) > 20:
            # Try to extract genus/species from AI description
            lines = ai_description.split('\n')
            first_line = lines[0].strip()
            
            # Look for scientific names in format "Genus species"
            scientific_match = re.search(r'([A-Z][a-z]+\s+[a-z]+)', first_line)
            if scientific_match:
                display_name = scientific_match.group(1)
                scientific_name = scientific_match.group(1)
            else:
                # Extract first meaningful words
                words = first_line.split()[:3]
                display_name = ' '.join(words).replace(',', '').replace('.', '')
                scientific_name = None
        else:
            display_name = f"Chris Howard Collection #{file_id[:8]}"
            scientific_name = None
        
        # Create the orchid record
        orchid = OrchidRecord(
            display_name=display_name,
            scientific_name=scientific_name,
            google_drive_id=file_id,
            image_url=f'https://drive.google.com/uc?export=view&id={file_id}',
            photographer='Chris Howard',
            image_source='Chris Howard Collection',
            ai_description=ai_description,
            ai_confidence=0.8 if ai_description else None,
            ingestion_source='chris_howard_import',
            validation_status='pending',
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        return orchid
        
    except Exception as e:
        logger.error(f"Error creating orchid record: {e}")
        return None

def import_chris_howard_photos(limit=100, use_ai=True):
    """Import Chris Howard's orchid photos"""
    logger.info("🚀 STARTING CHRIS HOWARD PHOTO IMPORT")
    logger.info(f"Limit: {limit} photos")
    logger.info(f"AI Analysis: {'Enabled' if use_ai else 'Disabled'}")
    
    with app.app_context():
        # Step 1: Extract file IDs
        file_ids = extract_file_ids_from_folder(CHRIS_FOLDER_ID)
        
        if not file_ids:
            logger.error("No file IDs found in folder")
            return {"success": False, "error": "No files found"}
        
        # Step 2: Test photo accessibility
        working_photos, success_rate, estimated_total = test_photo_accessibility(file_ids)
        
        if success_rate == 0:
            logger.error("No accessible photos found")
            return {"success": False, "error": "No accessible photos"}
        
        # Step 3: Import photos
        logger.info(f"Starting import of up to {limit} photos...")
        
        imported_count = 0
        error_count = 0
        imported_ids = []
        
        # Select photos to import (prioritize working ones we tested)
        photos_to_import = working_photos + [f for f in file_ids if f not in working_photos]
        photos_to_import = photos_to_import[:limit]
        
        for i, file_id in enumerate(photos_to_import, 1):
            try:
                logger.info(f"Processing photo {i}/{len(photos_to_import)}: {file_id}")
                
                # Check if already exists
                existing = OrchidRecord.query.filter_by(google_drive_id=file_id).first()
                if existing:
                    logger.info(f"  ⚠️ Already exists, skipping")
                    continue
                
                # Get photo URL
                photo_url = f'https://drive.google.com/uc?export=view&id={file_id}'
                
                # AI analysis (optional)
                ai_description = None
                if use_ai and i <= 20:  # Limit AI usage to first 20 photos to save costs
                    logger.info(f"  🤖 Running AI analysis...")
                    ai_description = analyze_photo_with_ai(photo_url)
                    time.sleep(1)  # Rate limiting
                
                # Create orchid record
                orchid = create_orchid_record(file_id, ai_description)
                
                if orchid:
                    db.session.add(orchid)
                    db.session.commit()
                    
                    imported_count += 1
                    imported_ids.append(file_id)
                    logger.info(f"  ✅ Imported: '{orchid.display_name}'")
                else:
                    error_count += 1
                    logger.error(f"  ❌ Failed to create record")
                
                # Progress update
                if i % 10 == 0:
                    logger.info(f"Progress: {i}/{len(photos_to_import)} processed, {imported_count} imported")
                
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {file_id}: {e}")
        
        # Final results
        result = {
            "success": True,
            "imported": imported_count,
            "errors": error_count,
            "total_processed": len(photos_to_import),
            "estimated_remaining": estimated_total - imported_count,
            "imported_ids": imported_ids
        }
        
        logger.info(f"🎉 IMPORT COMPLETE")
        logger.info(f"Imported: {imported_count} orchids")
        logger.info(f"Errors: {error_count}")
        logger.info(f"Estimated remaining: {result['estimated_remaining']}")
        
        return result

if __name__ == "__main__":
    # Test run with a small batch
    result = import_chris_howard_photos(limit=20, use_ai=True)
    print(f"Import result: {result}")