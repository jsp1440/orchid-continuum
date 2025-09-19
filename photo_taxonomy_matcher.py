#!/usr/bin/env python3
"""
PHOTO-TAXONOMY MATCHER SYSTEM
============================
AI-powered system to compare existing photo records against 
Dr. Michael Hassler's authoritative taxonomy database.

Capabilities:
- Match 5,973 photo records against 7,376 taxonomy entries
- Identify naming discrepancies and suggest corrections
- Find missing species in photo collection
- Validate species identifications using AI image analysis
"""

import os
import logging
from sqlalchemy import create_engine, text
from datetime import datetime
import openai
import json
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class PhotoTaxonomyMatcher:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        
        # Initialize OpenAI for image analysis
        openai.api_key = os.environ.get('OPENAI_API_KEY')
        
        self.stats = {
            'photo_records': 0,
            'taxonomy_entries': 0,
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'mismatches': 0,
            'missing_in_photos': 0,
            'validation_suggestions': []
        }
    
    def get_database_counts(self):
        """Get current counts of records in both databases"""
        with self.engine.connect() as conn:
            # Count photo records
            result = conn.execute(text("SELECT COUNT(*) FROM orchid_record")).fetchone()
            self.stats['photo_records'] = result[0] if result else 0
            
            # Count taxonomy entries
            result = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).fetchone()
            self.stats['taxonomy_entries'] = result[0] if result else 0
            
        logger.info(f"📊 Database Status:")
        logger.info(f"   • Photo records: {self.stats['photo_records']:,}")
        logger.info(f"   • Taxonomy entries: {self.stats['taxonomy_entries']:,}")
    
    def find_exact_matches(self):
        """Find exact matches between photo records and taxonomy"""
        logger.info("🔍 Finding exact matches between photos and taxonomy...")
        
        with self.engine.connect() as conn:
            # Find exact genus+species matches
            result = conn.execute(text("""
                SELECT DISTINCT 
                    or_rec.genus, 
                    or_rec.species, 
                    or_rec.display_name,
                    ot.scientific_name,
                    COUNT(*) as photo_count
                FROM orchid_record or_rec
                INNER JOIN orchid_taxonomy ot 
                    ON LOWER(or_rec.genus) = LOWER(ot.genus) 
                    AND LOWER(or_rec.species) = LOWER(ot.species)
                WHERE or_rec.genus IS NOT NULL 
                    AND or_rec.species IS NOT NULL
                    AND ot.genus IS NOT NULL 
                    AND ot.species IS NOT NULL
                GROUP BY or_rec.genus, or_rec.species, or_rec.display_name, ot.scientific_name
                ORDER BY photo_count DESC
            """)).fetchall()
            
            self.stats['exact_matches'] = len(result)
            
            logger.info(f"✅ Found {self.stats['exact_matches']} exact matches!")
            
            if result:
                logger.info("📋 Top exact matches:")
                for row in result[:10]:
                    logger.info(f"  • {row[0]} {row[1]} ({row[4]} photos) ✓ Dr. Hassler: {row[3]}")
            
            return result
    
    def find_potential_mismatches(self):
        """Find potential naming discrepancies that need review"""
        logger.info("⚠️ Identifying potential naming discrepancies...")
        
        with self.engine.connect() as conn:
            # Find photo records where genus exists in taxonomy but species doesn't match
            result = conn.execute(text("""
                SELECT DISTINCT 
                    or_rec.genus,
                    or_rec.species,
                    or_rec.display_name,
                    ot.species as hassler_species,
                    ot.scientific_name,
                    COUNT(*) as photo_count
                FROM orchid_record or_rec
                INNER JOIN orchid_taxonomy ot ON LOWER(or_rec.genus) = LOWER(ot.genus)
                WHERE or_rec.genus IS NOT NULL 
                    AND or_rec.species IS NOT NULL
                    AND ot.genus IS NOT NULL 
                    AND ot.species IS NOT NULL
                    AND LOWER(or_rec.species) != LOWER(ot.species)
                GROUP BY or_rec.genus, or_rec.species, or_rec.display_name, ot.species, ot.scientific_name
                ORDER BY photo_count DESC
                LIMIT 50
            """)).fetchall()
            
            self.stats['mismatches'] = len(result)
            
            logger.info(f"⚠️ Found {self.stats['mismatches']} potential naming discrepancies")
            
            if result:
                logger.info("📋 Top potential mismatches for review:")
                for row in result[:5]:
                    logger.info(f"  • Photo: {row[0]} {row[1]} vs Dr. Hassler: {row[0]} {row[3]}")
            
            return result
    
    def find_missing_species(self):
        """Find species in Dr. Hassler's taxonomy that are missing from photo collection"""
        logger.info("🔍 Finding species missing from photo collection...")
        
        with self.engine.connect() as conn:
            # Find taxonomy entries with no corresponding photo records
            result = conn.execute(text("""
                SELECT 
                    ot.genus,
                    ot.species,
                    ot.scientific_name,
                    ot.author
                FROM orchid_taxonomy ot
                LEFT JOIN orchid_record or_rec 
                    ON LOWER(ot.genus) = LOWER(or_rec.genus) 
                    AND LOWER(ot.species) = LOWER(or_rec.species)
                WHERE or_rec.id IS NULL
                    AND ot.genus IS NOT NULL 
                    AND ot.species IS NOT NULL
                ORDER BY ot.genus, ot.species
                LIMIT 100
            """)).fetchall()
            
            self.stats['missing_in_photos'] = len(result)
            
            logger.info(f"📸 Found {self.stats['missing_in_photos']} species in Dr. Hassler's database missing from photo collection")
            
            if result:
                logger.info("📋 Priority species to photograph:")
                for row in result[:10]:
                    logger.info(f"  • {row[2]} ({row[3] or 'No author'})")
            
            return result
    
    def analyze_photo_with_ai(self, photo_url, current_name):
        """Use AI to analyze photo and suggest taxonomic validation"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Analyze this orchid photo currently identified as '{current_name}'. Based on visible characteristics, does this identification appear correct? Look for distinctive features like flower shape, lip structure, column characteristics, and growth habit. Provide confidence level and reasoning."
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
            logger.error(f"AI analysis error: {e}")
            return None
    
    def generate_validation_report(self):
        """Generate comprehensive validation report"""
        logger.info("📊 PHOTO-TAXONOMY VALIDATION REPORT")
        logger.info("=" * 60)
        logger.info(f"📚 Dr. Michael Hassler's Taxonomy Database")
        logger.info(f"🌺 Citation: Hassler, M. (2025). World Orchids Database.")
        logger.info("=" * 60)
        
        # Get updated counts
        self.get_database_counts()
        
        # Run matching analysis
        exact_matches = self.find_exact_matches()
        mismatches = self.find_potential_mismatches()
        missing_species = self.find_missing_species()
        
        # Calculate coverage
        coverage_percentage = (self.stats['exact_matches'] / self.stats['taxonomy_entries']) * 100 if self.stats['taxonomy_entries'] > 0 else 0
        
        logger.info("=" * 60)
        logger.info("📈 ANALYSIS SUMMARY:")
        logger.info(f"✅ Exact matches: {self.stats['exact_matches']:,}")
        logger.info(f"⚠️ Potential mismatches: {self.stats['mismatches']:,}")
        logger.info(f"📸 Missing from photos: {self.stats['missing_in_photos']:,}")
        logger.info(f"📊 Taxonomy coverage: {coverage_percentage:.1f}%")
        logger.info("=" * 60)
        
        # Recommendations
        logger.info("🎯 RECOMMENDATIONS:")
        logger.info("1. Review potential mismatches for taxonomic accuracy")
        logger.info("2. Prioritize photographing missing species")
        logger.info("3. Use AI validation on questionable identifications")
        logger.info("4. Cross-reference with GBIF occurrence data")
        logger.info("=" * 60)
        
        return {
            'exact_matches': exact_matches,
            'mismatches': mismatches,
            'missing_species': missing_species,
            'stats': self.stats
        }

def main():
    """Run the photo-taxonomy matching analysis"""
    logger.info("🌺 DR. HASSLER PHOTO-TAXONOMY MATCHER")
    logger.info("Comparing photo collection against authoritative taxonomy")
    
    try:
        matcher = PhotoTaxonomyMatcher()
        report = matcher.generate_validation_report()
        
        logger.info("🎉 Photo-taxonomy analysis complete!")
        logger.info("📧 Use results to guide data collection and validation efforts")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Analysis failed: {e}")
        return False

if __name__ == "__main__":
    main()