#!/usr/bin/env python3
"""
Comprehensive Photo Analysis System
Analyzes orchid photos for names, metadata, and enhanced identification

Features:
- Filename analysis for automatic orchid name detection
- AI-powered image analysis for species identification
- EXIF metadata extraction
- Enhanced orchid record updating
"""

import os
import logging
from PIL import Image
from PIL.ExifTags import TAGS
import requests
from models import OrchidRecord, db
from filename_parser import parse_orchid_filename, extract_metadata_from_image
from orchid_ai import analyze_orchid_image
import time
from sqlalchemy import or_

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PhotoAnalysisSystem:
    """Comprehensive photo analysis for orchid identification"""
    
    def __init__(self):
        self.stats = {
            'analyzed': 0,
            'improved_names': 0,
            'extracted_metadata': 0,
            'ai_analyzed': 0,
            'errors': 0
        }
    
    def analyze_all_photos(self, max_photos=100):
        """Analyze all orchid photos for names and metadata"""
        logger.info("🔍 STARTING COMPREHENSIVE PHOTO ANALYSIS")
        logger.info("=" * 60)
        
        # Get orchids that need analysis
        orchids_to_analyze = OrchidRecord.query.filter(
            or_(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.google_drive_id.isnot(None)
            ),
            or_(
                OrchidRecord.ai_description.is_(None),
                OrchidRecord.ai_confidence.is_(None),
                OrchidRecord.scientific_name.is_(None)
            )
        ).limit(max_photos).all()
        
        logger.info(f"📊 Found {len(orchids_to_analyze)} orchids needing analysis")
        
        for orchid in orchids_to_analyze:
            try:
                self.analyze_single_orchid(orchid)
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error analyzing orchid {orchid.id}: {e}")
                self.stats['errors'] += 1
                
        db.session.commit()
        
        logger.info("=" * 60)
        logger.info("🎯 PHOTO ANALYSIS COMPLETE")
        logger.info(f"📊 Analyzed: {self.stats['analyzed']}")
        logger.info(f"📝 Improved Names: {self.stats['improved_names']}")
        logger.info(f"🔍 Extracted Metadata: {self.stats['extracted_metadata']}")
        logger.info(f"🤖 AI Analyzed: {self.stats['ai_analyzed']}")
        logger.info(f"❌ Errors: {self.stats['errors']}")
        
        return self.stats
    
    def analyze_single_orchid(self, orchid):
        """Analyze a single orchid photo comprehensively"""
        logger.info(f"🔍 Analyzing: {orchid.display_name} (ID: {orchid.id})")
        
        # 1. Filename Analysis
        filename_results = self.analyze_filename(orchid)
        
        # 2. Image Analysis (if image accessible)
        image_results = self.analyze_image_content(orchid)
        
        # 3. Metadata Extraction
        metadata_results = self.extract_photo_metadata(orchid)
        
        # 4. Update orchid record with findings
        self.update_orchid_with_analysis(orchid, filename_results, image_results, metadata_results)
        
        self.stats['analyzed'] += 1
    
    def analyze_filename(self, orchid):
        """Analyze filename for orchid name detection"""
        results = {'genus': None, 'species': None, 'confidence': 0.0}
        
        # Get filename from image_url or display_name
        filename = ""
        if orchid.image_url:
            filename = os.path.basename(orchid.image_url)
        elif orchid.display_name:
            filename = orchid.display_name
            
        if filename:
            parsed = parse_orchid_filename(filename)
            results = {
                'genus': parsed.get('genus'),
                'species': parsed.get('species'),
                'confidence': parsed.get('confidence', 0.0),
                'method': 'filename_parsing'
            }
            
            if parsed.get('genus'):
                logger.info(f"   📝 Filename analysis found: {parsed.get('genus')} {parsed.get('species', '')}")
        
        return results
    
    def analyze_image_content(self, orchid):
        """Use AI to analyze the actual image content"""
        results = {'description': None, 'species': None, 'confidence': 0.0}
        
        # Skip if already has AI analysis
        if orchid.ai_description and orchid.ai_confidence:
            return results
            
        try:
            # Get image URL
            image_url = None
            if orchid.google_drive_id:
                image_url = f"/api/drive-photo/{orchid.google_drive_id}"
            elif orchid.image_url:
                image_url = orchid.image_url
            
            if image_url:
                # Use existing AI analysis function
                ai_result = analyze_orchid_image(image_url)
                
                if ai_result:
                    results = {
                        'description': ai_result.get('description'),
                        'species': ai_result.get('suggested_name'),
                        'genus': ai_result.get('genus'),
                        'confidence': ai_result.get('confidence', 0.0),
                        'method': 'ai_vision'
                    }
                    
                    logger.info(f"   🤖 AI analysis found: {ai_result.get('suggested_name', 'Unknown')}")
                    self.stats['ai_analyzed'] += 1
                    
        except Exception as e:
            logger.error(f"   ❌ AI analysis failed: {e}")
            
        return results
    
    def extract_photo_metadata(self, orchid):
        """Extract EXIF and other metadata from photo"""
        results = {'location': None, 'date': None, 'camera': None}
        
        try:
            # Use existing metadata extraction
            image_path = orchid.image_url or f"drive:{orchid.google_drive_id}"
            metadata = extract_metadata_from_image(image_path)
            
            if metadata:
                results = {
                    'location': metadata.get('gps_data'),
                    'date': metadata.get('exif_datetime') or metadata.get('exif_datetimeoriginal'),
                    'camera': metadata.get('exif_model'),
                    'analysis': metadata.get('filename_analysis')
                }
                
                if any(results.values()):
                    logger.info(f"   📊 Extracted metadata: {len([v for v in results.values() if v])} fields")
                    self.stats['extracted_metadata'] += 1
                    
        except Exception as e:
            logger.error(f"   ❌ Metadata extraction failed: {e}")
            
        return results
    
    def update_orchid_with_analysis(self, orchid, filename_results, image_results, metadata_results):
        """Update orchid record with analysis results"""
        updated = False
        
        # Update genus/species if we found better information
        best_genus = None
        best_species = None
        best_confidence = 0.0
        
        # Compare filename vs AI results
        if filename_results.get('confidence', 0) > best_confidence:
            best_genus = filename_results.get('genus')
            best_species = filename_results.get('species')
            best_confidence = filename_results.get('confidence', 0)
            
        if image_results.get('confidence', 0) > best_confidence:
            best_genus = image_results.get('genus')
            best_species = image_results.get('species')
            best_confidence = image_results.get('confidence', 0)
        
        # Update genus if we found a better one
        if best_genus and (not orchid.genus or best_confidence > 0.7):
            if orchid.genus != best_genus:
                logger.info(f"   ✅ Updated genus: {orchid.genus} → {best_genus}")
                orchid.genus = best_genus
                updated = True
                self.stats['improved_names'] += 1
        
        # Update species if we found one
        if best_species and (not orchid.species or best_confidence > 0.7):
            if orchid.species != best_species:
                logger.info(f"   ✅ Updated species: {orchid.species} → {best_species}")
                orchid.species = best_species
                updated = True
                self.stats['improved_names'] += 1
        
        # Update scientific name
        if best_genus and best_species:
            new_scientific = f"{best_genus} {best_species}"
            if not orchid.scientific_name or orchid.scientific_name != new_scientific:
                orchid.scientific_name = new_scientific
                updated = True
        
        # Update AI description and confidence
        if image_results.get('description') and not orchid.ai_description:
            orchid.ai_description = image_results['description']
            updated = True
            
        if image_results.get('confidence') and not orchid.ai_confidence:
            orchid.ai_confidence = image_results['confidence']
            updated = True
        
        # Update display name if we have better information
        if best_genus and best_species:
            new_display = f"{best_genus} {best_species}"
            if orchid.display_name != new_display and best_confidence > 0.7:
                orchid.display_name = new_display
                updated = True
        
        if updated:
            logger.info(f"   💾 Updated orchid record with new analysis")
            
    def analyze_photos_by_source(self, source_filter=None, max_photos=50):
        """Analyze photos from specific sources"""
        logger.info(f"🔍 Analyzing photos from source: {source_filter or 'all'}")
        
        query = OrchidRecord.query.filter(
            or_(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.google_drive_id.isnot(None)
            )
        )
        
        if source_filter:
            query = query.filter(OrchidRecord.native_habitat.contains(source_filter))
            
        orchids = query.limit(max_photos).all()
        
        for orchid in orchids:
            self.analyze_single_orchid(orchid)
            time.sleep(1)
            
        db.session.commit()
        return self.stats
    
    def run_comprehensive_analysis(self):
        """Run comprehensive analysis on all photos"""
        logger.info("🚀 STARTING COMPREHENSIVE PHOTO ANALYSIS SYSTEM")
        
        # Phase 1: Analyze photos needing AI analysis
        logger.info("📋 Phase 1: AI Analysis of unprocessed photos")
        self.analyze_all_photos(max_photos=200)
        
        # Phase 2: Enhance existing records with better metadata
        logger.info("📋 Phase 2: Metadata enhancement")
        self.enhance_existing_records()
        
        # Phase 3: Filename analysis for all records
        logger.info("📋 Phase 3: Comprehensive filename analysis")
        self.analyze_all_filenames()
        
        return self.stats
    
    def enhance_existing_records(self):
        """Enhance existing records with better analysis"""
        orchids = OrchidRecord.query.filter(
            or_(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.google_drive_id.isnot(None)
            )
        ).limit(100).all()
        
        for orchid in orchids:
            # Re-analyze for better metadata
            metadata = self.extract_photo_metadata(orchid)
            if metadata.get('date') and not hasattr(orchid, 'photo_date'):
                # Could add new fields for photo metadata
                pass
        
        db.session.commit()
    
    def analyze_all_filenames(self):
        """Run filename analysis on all orchid records"""
        orchids = OrchidRecord.query.limit(500).all()
        
        for orchid in orchids:
            filename_results = self.analyze_filename(orchid)
            if filename_results.get('genus') and filename_results.get('confidence', 0) > 0.8:
                # Update with high-confidence filename results
                if not orchid.genus or filename_results['confidence'] > 0.8:
                    if orchid.genus != filename_results['genus']:
                        orchid.genus = filename_results['genus']
                        self.stats['improved_names'] += 1
        
        db.session.commit()

if __name__ == "__main__":
    system = PhotoAnalysisSystem()
    results = system.run_comprehensive_analysis()
    print(f"Photo analysis completed: {results}")