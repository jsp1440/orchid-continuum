#!/usr/bin/env python3
"""
Re-trigger AI Analysis for Specific Records
This script forces AI re-analysis for orchid records that have mismatched image-description pairs
"""

import os
import sys
sys.path.append('.')

from app import app, db
from models import OrchidRecord
from ai_orchid_identification import identify_orchid_photo
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retrigger_ai_analysis():
    """Re-trigger AI analysis for records with NULL ai_description"""
    with app.app_context():
        try:
            # Find records that need AI re-analysis (those with NULL ai_description and valid images)
            records_to_analyze = OrchidRecord.query.filter(
                OrchidRecord.ai_description.is_(None),
                OrchidRecord.google_drive_id.isnot(None)
            ).limit(50).all()
            
            logger.info(f"Found {len(records_to_analyze)} records that need AI re-analysis")
            
            for i, record in enumerate(records_to_analyze, 1):
                try:
                    logger.info(f"[{i}/{len(records_to_analyze)}] Analyzing {record.display_name} (ID: {record.id})")
                    
                    # Construct Google Drive image URL
                    image_path = f"https://drive.google.com/uc?export=view&id={record.google_drive_id}"
                    
                    # Call AI analysis
                    result = identify_orchid_photo(image_path)
                    
                    if result and not result.get('error'):
                        # Parse AI identification data
                        ai_data = result.get('ai_identification', {})
                        primary_id = ai_data.get('primary_identification', {})
                        
                        # Update the record with new AI analysis
                        record.ai_confidence = result.get('confidence_score', 0)
                        record.ai_extracted_metadata = str(result)
                        
                        # Create a comprehensive description
                        genus = primary_id.get('genus', '')
                        species = primary_id.get('species', '')
                        confidence = primary_id.get('confidence', 0)
                        
                        description_parts = []
                        if genus and species:
                            description_parts.append(f"AI identified as {genus} {species} with {confidence}% confidence.")
                        
                        # Add botanical characteristics
                        botanical = ai_data.get('botanical_characteristics', {})
                        if botanical.get('growth_habit'):
                            description_parts.append(f"Growth habit: {botanical['growth_habit']}.")
                        if botanical.get('key_features'):
                            features = botanical['key_features'][:3]  # Top 3 features
                            description_parts.append(f"Key features: {', '.join(features)}.")
                        
                        record.ai_description = ' '.join(description_parts)
                        
                        # Update genus/species if identified with high confidence
                        if confidence > 70:
                            if genus:
                                record.genus = genus
                            if species:
                                record.species = species
                        
                        db.session.commit()
                        logger.info(f"✅ Successfully updated AI analysis for {record.display_name}")
                    else:
                        logger.warning(f"⚠️ No AI analysis results for {record.display_name}")
                        
                except Exception as e:
                    logger.error(f"❌ Error analyzing {record.display_name}: {e}")
                    db.session.rollback()
                    continue
            
            logger.info(f"🎉 Completed AI re-analysis for {len(records_to_analyze)} records")
            
        except Exception as e:
            logger.error(f"Error in retrigger_ai_analysis: {e}")
            raise

if __name__ == "__main__":
    retrigger_ai_analysis()