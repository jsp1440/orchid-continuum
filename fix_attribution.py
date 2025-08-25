#!/usr/bin/env python3
"""
Attribution Fix Script for Orchid Continuum
Adds photographer credits and source information for Google Drive orchids
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AttributionFixer:
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
    
    def add_default_attribution(self):
        """Add default attribution for Five Cities Orchid Society collection"""
        logger.info("🔧 Adding photographer attribution for Google Drive orchids...")
        
        # Update Google Sheets imports with default attribution
        update_query = text("""
            UPDATE orchid_record 
            SET photographer = 'Five Cities Orchid Society Collection',
                image_source = CONCAT('https://drive.google.com/file/d/', google_drive_id, '/view'),
                updated_at = CURRENT_TIMESTAMP
            WHERE ingestion_source = 'google_sheets_import'
              AND google_drive_id IS NOT NULL
              AND (photographer IS NULL OR photographer = '')
        """)
        
        result = self.session.execute(update_query)
        count = result.rowcount
        self.session.commit()
        
        logger.info(f"✅ Updated {count} orchids with photographer attribution")
        return count
    
    def add_validation_flags(self):
        """Add validation flags for records needing expert review"""
        logger.info("🏷️ Adding validation flags for quality review...")
        
        # Add validation notes for low confidence records
        update_query = text("""
            UPDATE orchid_record 
            SET cultural_notes = CASE 
                WHEN cultural_notes IS NULL OR cultural_notes = '' THEN 
                    'NOTE: This identification has low AI confidence and needs expert review.'
                ELSE 
                    cultural_notes || ' NOTE: This identification has low AI confidence and needs expert review.'
                END,
                updated_at = CURRENT_TIMESTAMP
            WHERE validation_status = 'needs_review'
              AND ai_confidence <= 0.7
              AND (cultural_notes IS NULL OR cultural_notes NOT LIKE '%low AI confidence%')
        """)
        
        result = self.session.execute(update_query)
        count = result.rowcount
        self.session.commit()
        
        logger.info(f"✅ Added validation flags to {count} orchids")
        return count
    
    def create_attribution_report(self):
        """Generate report on attribution completeness"""
        logger.info("📊 Generating attribution report...")
        
        report_query = text("""
            SELECT 
                ingestion_source,
                COUNT(*) as total,
                COUNT(CASE WHEN photographer IS NOT NULL AND photographer != '' THEN 1 END) as with_photographer,
                COUNT(CASE WHEN image_source IS NOT NULL AND image_source != '' THEN 1 END) as with_source
            FROM orchid_record 
            GROUP BY ingestion_source
            ORDER BY total DESC
        """)
        
        result = self.session.execute(report_query)
        
        print("\n📊 ATTRIBUTION COMPLETENESS BY SOURCE")
        print("=" * 50)
        for row in result:
            photographer_pct = (row.with_photographer / row.total * 100) if row.total > 0 else 0
            source_pct = (row.with_source / row.total * 100) if row.total > 0 else 0
            print(f"{row.ingestion_source:25} {row.total:4d} total | {row.with_photographer:3d} photos ({photographer_pct:5.1f}%) | {row.with_source:3d} sources ({source_pct:5.1f}%)")
        
        self.session.close()

if __name__ == "__main__":
    fixer = AttributionFixer()
    
    print("🔧 FIXING ATTRIBUTION ISSUES")
    print("=" * 40)
    
    # Fix attribution
    count = fixer.add_default_attribution()
    print(f"✅ Added photographer credits to {count} orchids")
    
    # Add validation flags
    flag_count = fixer.add_validation_flags()
    print(f"✅ Added validation flags to {flag_count} orchids")
    
    # Generate report
    fixer.create_attribution_report()
    
    print("\n💡 NEXT STEPS:")
    print("  1. Expert review of orchids marked 'needs_review'")
    print("  2. Verify photographer attributions are correct")
    print("  3. Update any specific photographer names if known")
    print("  4. Re-run AI analysis on failed identifications")