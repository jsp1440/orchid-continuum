#!/usr/bin/env python3
"""
Data Quality Dashboard for Orchid Continuum
Identifies and reports data quality issues for expert review
"""

import logging
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityDashboard:
    def __init__(self):
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            raise ValueError("DATABASE_URL environment variable not set")
        
        self.engine = create_engine(database_url)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
    def analyze_quality_issues(self):
        """Comprehensive data quality analysis"""
        print("🔍 ORCHID CONTINUUM DATA QUALITY REPORT")
        print("=" * 60)
        print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}")
        print()
        
        # Issue 1: Misidentification Analysis
        print("📊 IDENTIFICATION CONFIDENCE ANALYSIS")
        print("-" * 40)
        
        confidence_query = text("""
            SELECT 
                CASE 
                    WHEN ai_confidence >= 0.9 THEN 'High (≥90%)'
                    WHEN ai_confidence >= 0.8 THEN 'Good (80-89%)'
                    WHEN ai_confidence >= 0.7 THEN 'Moderate (70-79%)'
                    WHEN ai_confidence >= 0.5 THEN 'Low (50-69%)'
                    WHEN ai_confidence > 0 THEN 'Very Low (<50%)'
                    ELSE 'No Confidence/Error'
                END as confidence_level,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
            FROM orchid_record 
            WHERE ingestion_source = 'google_sheets_import'
            GROUP BY 
                CASE 
                    WHEN ai_confidence >= 0.9 THEN 'High (≥90%)'
                    WHEN ai_confidence >= 0.8 THEN 'Good (80-89%)'
                    WHEN ai_confidence >= 0.7 THEN 'Moderate (70-79%)'
                    WHEN ai_confidence >= 0.5 THEN 'Low (50-69%)'
                    WHEN ai_confidence > 0 THEN 'Very Low (<50%)'
                    ELSE 'No Confidence/Error'
                END
            ORDER BY COUNT(*) DESC
        """)
        
        result = self.session.execute(confidence_query)
        for row in result:
            print(f"  {row.confidence_level:20} {row.count:4d} orchids ({row.percentage:5.1f}%)")
        print()
        
        # Issue 2: Attribution Analysis
        print("📸 ATTRIBUTION COMPLETENESS ANALYSIS")
        print("-" * 40)
        
        attribution_query = text("""
            SELECT 
                COUNT(*) as total_orchids,
                COUNT(CASE WHEN photographer IS NOT NULL AND photographer != '' THEN 1 END) as with_photographer,
                COUNT(CASE WHEN image_source IS NOT NULL AND image_source != '' THEN 1 END) as with_source,
                COUNT(google_drive_id) as with_google_photos
            FROM orchid_record 
            WHERE ingestion_source = 'google_sheets_import'
        """)
        
        result = self.session.execute(attribution_query).fetchone()
        print(f"  Total Google Sheets orchids: {result.total_orchids}")
        print(f"  With photographer credit:     {result.with_photographer} ({result.with_photographer/result.total_orchids*100:.1f}%)")
        print(f"  With image source:            {result.with_source} ({result.with_source/result.total_orchids*100:.1f}%)")
        print(f"  With Google Drive photos:     {result.with_google_photos} ({result.with_google_photos/result.total_orchids*100:.1f}%)")
        print()
        
        # Issue 3: Generic Description Analysis
        print("🤖 AI DESCRIPTION QUALITY ANALYSIS")
        print("-" * 40)
        
        generic_query = text("""
            SELECT 
                COUNT(CASE WHEN ai_description LIKE '%beautiful orchid with unique characteristics%' THEN 1 END) as generic_descriptions,
                COUNT(CASE WHEN ai_description LIKE '%Error during AI analysis%' THEN 1 END) as failed_analysis,
                COUNT(CASE WHEN ai_description IS NULL OR ai_description = '' THEN 1 END) as no_description,
                COUNT(*) as total
            FROM orchid_record 
            WHERE ingestion_source = 'google_sheets_import'
        """)
        
        result = self.session.execute(generic_query).fetchone()
        print(f"  Generic descriptions:         {result.generic_descriptions} ({result.generic_descriptions/result.total*100:.1f}%)")
        print(f"  Failed AI analysis:           {result.failed_analysis} ({result.failed_analysis/result.total*100:.1f}%)")
        print(f"  No description:               {result.no_description} ({result.no_description/result.total*100:.1f}%)")
        print()
        
        # Issue 4: Suspected Misidentifications
        print("⚠️  SUSPECTED MISIDENTIFICATIONS")
        print("-" * 40)
        
        suspicious_query = text("""
            SELECT id, genus, species, display_name, ai_confidence, ai_description
            FROM orchid_record 
            WHERE ingestion_source = 'google_sheets_import'
              AND (ai_confidence <= 0.7 OR ai_description LIKE '%beautiful orchid with unique characteristics%')
              AND validation_status = 'needs_review'
            ORDER BY ai_confidence ASC, id ASC
            LIMIT 10
        """)
        
        result = self.session.execute(suspicious_query)
        print("  Top 10 most suspicious records:")
        for row in result:
            print(f"    ID {row.id:4d}: {row.display_name} (confidence: {row.ai_confidence:.1f})")
        print()
        
        # Recommendations
        print("💡 RECOMMENDED ACTIONS")
        print("-" * 40)
        print("  1. Expert review of 595 orchids marked 'needs_review'")
        print("  2. Implement photographer attribution from original data source")
        print("  3. Re-run AI analysis on failed/low-confidence identifications")
        print("  4. Add image source URLs to Google Drive photos")
        print("  5. Create bulk editing tools for expert reviewers")
        print()
        
        self.session.close()
    
    def get_review_candidates(self, limit=20):
        """Get orchids that most urgently need expert review"""
        query = text("""
            SELECT id, genus, species, display_name, ai_confidence, ai_description, google_drive_id
            FROM orchid_record 
            WHERE validation_status = 'needs_review'
              AND ingestion_source = 'google_sheets_import'
            ORDER BY 
                CASE WHEN ai_confidence IS NULL THEN 0 ELSE ai_confidence END ASC,
                CASE WHEN ai_description LIKE '%Error%' THEN 1 ELSE 0 END DESC,
                id ASC
            LIMIT :limit
        """)
        
        result = self.session.execute(query, {"limit": limit})
        return result.fetchall()

if __name__ == "__main__":
    dashboard = DataQualityDashboard()
    dashboard.analyze_quality_issues()