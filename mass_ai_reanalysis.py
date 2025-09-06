#!/usr/bin/env python3
"""
Mass AI Re-Analysis Script
Complete AI re-analysis for all records missing descriptions
"""

import os
import sys
import time
import logging
sys.path.append('.')

from app import app, db
from models import OrchidRecord
from ai_orchid_identification import identify_orchid_photo

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mass_ai_reanalysis():
    """Complete AI re-analysis for all records missing descriptions"""
    with app.app_context():
        try:
            # Find ALL records that need AI analysis
            records_to_analyze = db.session.execute(
                db.text("""
                    SELECT id, display_name, google_drive_id 
                    FROM orchid_record 
                    WHERE google_drive_id IS NOT NULL 
                    AND ai_description IS NULL
                    ORDER BY id
                """)
            ).fetchall()
            
            total_records = len(records_to_analyze)
            logger.info(f"🚀 Starting mass AI re-analysis for {total_records} records")
            
            success_count = 0
            error_count = 0
            
            for i, record_data in enumerate(records_to_analyze, 1):
                try:
                    record_id = record_data[0]
                    display_name = record_data[1] 
                    google_drive_id = record_data[2]
                    
                    logger.info(f"[{i}/{total_records}] Analyzing {display_name} (ID: {record_id})")
                    
                    # Construct Google Drive image URL
                    image_path = f"https://drive.google.com/uc?export=view&id={google_drive_id}"
                    
                    # Call AI analysis
                    result = identify_orchid_photo(image_path)
                    
                    if result and not result.get('error'):
                        # Parse AI identification data
                        ai_data = result.get('ai_identification', {})
                        primary_id = ai_data.get('primary_identification', {})
                        
                        # Create comprehensive description
                        genus = primary_id.get('genus', '')
                        species = primary_id.get('species', '')
                        confidence = primary_id.get('confidence', 0)
                        
                        description_parts = []
                        if genus and species:
                            description_parts.append(f"AI identified as {genus} {species} with {confidence}% confidence.")
                        elif genus:
                            description_parts.append(f"AI identified as {genus} species with {confidence}% confidence.")
                        
                        # Add botanical characteristics
                        botanical = ai_data.get('botanical_characteristics', {})
                        if botanical.get('growth_habit'):
                            description_parts.append(f"Growth habit: {botanical['growth_habit']}.")
                        if botanical.get('key_features'):
                            features = botanical['key_features'][:3]  # Top 3 features
                            description_parts.append(f"Key features: {', '.join(features)}.")
                        
                        final_description = ' '.join(description_parts) if description_parts else "AI analysis completed - detailed botanical identification available."
                        
                        # Update using direct SQL to avoid SQLAlchemy issues
                        db.session.execute(
                            db.text("""
                                UPDATE orchid_record 
                                SET ai_description = :description,
                                    ai_confidence = :confidence,
                                    ai_extracted_metadata = :metadata
                                WHERE id = :record_id
                            """),
                            {
                                'description': final_description,
                                'confidence': result.get('confidence_score', confidence),
                                'metadata': str(result),
                                'record_id': record_id
                            }
                        )
                        
                        # Update genus/species if identified with high confidence
                        if confidence > 70:
                            update_fields = {}
                            if genus:
                                update_fields['genus'] = genus
                            if species:
                                update_fields['species'] = species
                            
                            if update_fields:
                                sql_parts = []
                                params = {'record_id': record_id}
                                for field, value in update_fields.items():
                                    sql_parts.append(f"{field} = :{field}")
                                    params[field] = value
                                
                                db.session.execute(
                                    db.text(f"UPDATE orchid_record SET {', '.join(sql_parts)} WHERE id = :record_id"),
                                    params
                                )
                        
                        db.session.commit()
                        success_count += 1
                        logger.info(f"✅ Successfully updated {display_name}")
                    else:
                        error_count += 1
                        logger.warning(f"⚠️ No AI analysis results for {display_name}")
                        
                    # Progress update every 50 records
                    if i % 50 == 0:
                        logger.info(f"📊 Progress: {i}/{total_records} ({(i/total_records)*100:.1f}%) - Success: {success_count}, Errors: {error_count}")
                    
                    # Small delay to prevent API rate limiting
                    time.sleep(1)
                        
                except Exception as e:
                    error_count += 1
                    logger.error(f"❌ Error analyzing {display_name}: {e}")
                    db.session.rollback()
                    continue
            
            logger.info(f"🎉 Mass AI re-analysis completed!")
            logger.info(f"📊 Final results: {success_count} successful, {error_count} errors out of {total_records} total records")
            
        except Exception as e:
            logger.error(f"Fatal error in mass_ai_reanalysis: {e}")
            raise

if __name__ == "__main__":
    mass_ai_reanalysis()