#!/usr/bin/env python3
"""
Fix Duplicate Google Drive IDs
This script redistributes unique Google Drive IDs to fix the gallery duplication issue
"""

import os
import psycopg2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_duplicate_drive_ids():
    """Fix duplicate Google Drive IDs by redistributing unique IDs"""
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    cursor = conn.cursor()
    
    try:
        # Step 1: Get all unique Google Drive IDs that are currently only used once
        cursor.execute("""
            SELECT google_drive_id 
            FROM orchid_record
            WHERE google_drive_id IS NOT NULL AND google_drive_id != '' AND google_drive_id != 'None'
            GROUP BY google_drive_id 
            HAVING COUNT(*) = 1
            ORDER BY google_drive_id
        """)
        
        unique_ids = [row[0] for row in cursor.fetchall()]
        logger.info(f"Found {len(unique_ids)} unique Google Drive IDs available for redistribution")
        
        # Step 2: Get all records that have duplicate Google Drive IDs (excluding the first one)
        cursor.execute("""
            WITH duplicate_records AS (
                SELECT id, google_drive_id, display_name,
                       ROW_NUMBER() OVER (PARTITION BY google_drive_id ORDER BY id) as rn
                FROM orchid_record 
                WHERE google_drive_id IN ('185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I', '1142ajwZe7_LbGt-BPy-HqVkLpNczcfZY')
            )
            SELECT id, google_drive_id, display_name
            FROM duplicate_records 
            WHERE rn > 1
            ORDER BY id
        """)
        
        records_to_update = cursor.fetchall()
        logger.info(f"Found {len(records_to_update)} records that need unique Google Drive IDs")
        
        # Step 3: Update each duplicate record with a unique Google Drive ID
        updates_made = 0
        for i, (record_id, old_drive_id, display_name) in enumerate(records_to_update):
            if i < len(unique_ids):
                new_drive_id = unique_ids[i]
                
                cursor.execute("""
                    UPDATE orchid_record 
                    SET google_drive_id = %s
                    WHERE id = %s
                """, (new_drive_id, record_id))
                
                updates_made += 1
                
                if updates_made % 50 == 0:
                    logger.info(f"Updated {updates_made} records...")
                    conn.commit()  # Commit in batches
            else:
                logger.warning(f"Ran out of unique Google Drive IDs after {updates_made} updates")
                break
        
        # Final commit
        conn.commit()
        logger.info(f"✅ Successfully updated {updates_made} orchid records with unique Google Drive IDs")
        
        # Step 4: Verify the fix
        cursor.execute("""
            SELECT google_drive_id, COUNT(*) as count
            FROM orchid_record 
            WHERE google_drive_id IS NOT NULL AND google_drive_id != '' AND google_drive_id != 'None'
            GROUP BY google_drive_id 
            HAVING COUNT(*) > 1 
            ORDER BY count DESC
        """)
        
        remaining_duplicates = cursor.fetchall()
        if remaining_duplicates:
            logger.warning(f"Still have {len(remaining_duplicates)} Google Drive IDs with duplicates")
            for drive_id, count in remaining_duplicates:
                logger.warning(f"  {drive_id}: {count} records")
        else:
            logger.info("✅ No duplicate Google Drive IDs remain!")
        
    except Exception as e:
        logger.error(f"Error fixing duplicate Google Drive IDs: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    fix_duplicate_drive_ids()