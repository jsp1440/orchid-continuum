#!/usr/bin/env python3
"""
Orchid Duplicate Cleanup System
Intelligently removes duplicate orchid records while preserving the best data quality.
"""

from app import app, db
from models import OrchidRecord
from collections import defaultdict
from sqlalchemy import func, and_, or_
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def analyze_record_quality(record):
    """Score a record's data quality for duplicate resolution"""
    score = 0
    
    # Scientific name is most valuable (high priority)
    if record.scientific_name and len(record.scientific_name.strip()) > 2:
        score += 100
    
    # AI description adds significant value
    if record.ai_description and len(record.ai_description.strip()) > 10:
        score += 50
    
    # Photo presence is valuable
    if record.google_drive_id:
        score += 25
    
    # Cultural information adds value
    if record.cultural_notes and len(record.cultural_notes.strip()) > 10:
        score += 20
    
    # Growing characteristics
    if record.growth_habit:
        score += 10
    if record.climate_preference:
        score += 10
    if record.bloom_time:
        score += 10
    
    # Geographic info
    if record.region:
        score += 10
    if record.native_habitat:
        score += 10
    
    # OCR data
    if record.ocr_text and len(record.ocr_text.strip()) > 10:
        score += 15
    
    # Photographer/source info
    if record.photographer:
        score += 5
    
    # Recent records get slight boost (newer data might be better)
    if record.created_at:
        import datetime
        days_old = (datetime.datetime.utcnow() - record.created_at).days
        if days_old < 30:  # Recent records
            score += 5
    
    return score

def find_duplicate_groups():
    """Find all groups of duplicate orchid records"""
    logger.info("🔍 Finding duplicate groups...")
    
    all_records = OrchidRecord.query.all()
    name_groups = defaultdict(list)
    
    for record in all_records:
        if record.display_name:
            # Normalize the name for grouping
            key = record.display_name.strip().lower()
            name_groups[key].append(record)
    
    # Find groups with duplicates
    duplicate_groups = {name: records for name, records in name_groups.items() if len(records) > 1}
    
    logger.info(f"Found {len(duplicate_groups)} duplicate groups")
    return duplicate_groups

def select_best_records(duplicate_groups):
    """Select the best record from each duplicate group"""
    logger.info("🎯 Selecting best records from each group...")
    
    records_to_keep = []
    records_to_remove = []
    
    for group_name, records in duplicate_groups.items():
        if len(records) <= 1:
            continue
            
        # Score each record
        scored_records = []
        for record in records:
            quality_score = analyze_record_quality(record)
            scored_records.append((record, quality_score))
        
        # Sort by score (highest first)
        scored_records.sort(key=lambda x: x[1], reverse=True)
        
        # Keep the best one
        best_record, best_score = scored_records[0]
        records_to_keep.append(best_record)
        
        # Remove the rest
        for record, score in scored_records[1:]:
            records_to_remove.append(record)
        
        if len(records) > 5:  # Log details for major duplicate groups
            logger.info(f"Group '{group_name}': Keeping record {best_record.id} (score: {best_score}), removing {len(records)-1} duplicates")
    
    logger.info(f"Will keep {len(records_to_keep)} records, remove {len(records_to_remove)} duplicates")
    return records_to_keep, records_to_remove

def perform_cleanup(records_to_remove, dry_run=True):
    """Remove duplicate records from database"""
    if dry_run:
        logger.info(f"🧪 DRY RUN: Would remove {len(records_to_remove)} duplicate records")
        
        # Show sample of what would be removed
        logger.info("Sample records that would be removed:")
        for i, record in enumerate(records_to_remove[:10], 1):
            logger.info(f"{i:2d}. ID {record.id}: '{record.display_name}' (source: {record.ingestion_source})")
        
        if len(records_to_remove) > 10:
            logger.info(f"    ... and {len(records_to_remove) - 10} more records")
        
        return {"removed": 0, "dry_run": True}
    
    else:
        logger.info(f"🗑️ REMOVING {len(records_to_remove)} duplicate records...")
        
        removed_count = 0
        for record in records_to_remove:
            try:
                db.session.delete(record)
                removed_count += 1
                
                if removed_count % 100 == 0:
                    logger.info(f"Removed {removed_count}/{len(records_to_remove)} records...")
                    
            except Exception as e:
                logger.error(f"Error removing record {record.id}: {e}")
        
        # Commit the changes
        try:
            db.session.commit()
            logger.info(f"✅ Successfully removed {removed_count} duplicate records")
            return {"removed": removed_count, "dry_run": False}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error committing changes: {e}")
            return {"removed": 0, "error": str(e)}

def cleanup_duplicates(dry_run=True):
    """Main function to clean up duplicate orchid records"""
    logger.info("🚀 STARTING DUPLICATE CLEANUP PROCESS")
    logger.info(f"Mode: {'DRY RUN' if dry_run else 'LIVE CLEANUP'}")
    
    with app.app_context():
        # Get initial count
        initial_count = OrchidRecord.query.count()
        logger.info(f"Initial record count: {initial_count:,}")
        
        # Find duplicates
        duplicate_groups = find_duplicate_groups()
        
        if not duplicate_groups:
            logger.info("✅ No duplicates found!")
            return {"status": "no_duplicates", "initial_count": initial_count}
        
        # Select best records
        records_to_keep, records_to_remove = select_best_records(duplicate_groups)
        
        # Show cleanup preview
        logger.info(f"📊 CLEANUP PREVIEW:")
        logger.info(f"Current records: {initial_count:,}")
        logger.info(f"Records to keep: {len(records_to_keep):,}")
        logger.info(f"Records to remove: {len(records_to_remove):,}")
        logger.info(f"Final count: {initial_count - len(records_to_remove):,}")
        logger.info(f"Size reduction: {len(records_to_remove)/initial_count*100:.1f}%")
        
        # Perform cleanup
        result = perform_cleanup(records_to_remove, dry_run=dry_run)
        
        # Final count
        if not dry_run:
            final_count = OrchidRecord.query.count()
            logger.info(f"Final record count: {final_count:,}")
            result["final_count"] = final_count
        
        result.update({
            "initial_count": initial_count,
            "duplicates_found": len(records_to_remove),
            "groups_processed": len(duplicate_groups)
        })
        
        return result

if __name__ == "__main__":
    # Run cleanup in dry-run mode first
    result = cleanup_duplicates(dry_run=True)
    print(f"Cleanup result: {result}")