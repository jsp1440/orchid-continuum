"""
Enhanced Orchid Analysis System
===============================

Comprehensive AI analysis with flowering detection, EXIF extraction,
and detailed habitat/morphology metadata capture.
"""

from orchid_ai import analyze_orchid_image
from models import OrchidRecord, db
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)

def analyze_and_update_orchid(orchid_id, image_path=None):
    """
    Analyze orchid with enhanced AI system and update database with comprehensive metadata
    
    Args:
        orchid_id: ID of the orchid record to update
        image_path: Path to image file for analysis (optional if orchid already has image)
    
    Returns:
        dict: Analysis results and update status
    """
    try:
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            raise Exception(f"Orchid {orchid_id} not found")
        
        # Use provided image path or construct from existing data
        if not image_path and orchid.google_drive_id:
            # If no image path provided, skip AI analysis but return current data
            logger.info(f"No local image available for orchid {orchid_id}, skipping AI analysis")
            return {
                'success': True,
                'message': 'Orchid exists but no image analysis performed',
                'orchid_data': get_orchid_metadata_summary(orchid)
            }
        
        if not image_path:
            raise Exception("No image path provided and orchid has no Google Drive image")
        
        logger.info(f"🔍 Analyzing orchid {orchid_id} with enhanced AI system...")
        
        # Run enhanced AI analysis
        ai_results = analyze_orchid_image(image_path)
        
        # Update orchid record with comprehensive metadata
        update_success = update_orchid_with_analysis(orchid, ai_results)
        
        if update_success:
            logger.info(f"✅ Successfully updated orchid {orchid_id} with enhanced metadata")
            return {
                'success': True,
                'message': f'Enhanced analysis completed for {orchid.display_name}',
                'ai_results': ai_results,
                'orchid_data': get_orchid_metadata_summary(orchid)
            }
        else:
            raise Exception("Failed to update orchid record")
            
    except Exception as e:
        logger.error(f"❌ Error analyzing orchid {orchid_id}: {e}")
        return {
            'success': False,
            'error': str(e),
            'orchid_id': orchid_id
        }

def update_orchid_with_analysis(orchid, ai_results):
    """
    Update OrchidRecord with comprehensive AI analysis results
    
    Args:
        orchid: OrchidRecord instance
        ai_results: Dictionary of AI analysis results
    
    Returns:
        bool: True if update successful
    """
    try:
        # Botanical identification updates
        if ai_results.get('scientific_name'):
            orchid.scientific_name = ai_results['scientific_name']
        if ai_results.get('genus'):
            orchid.genus = ai_results['genus']
        if ai_results.get('species'):
            orchid.species = ai_results['species']
        
        # AI analysis updates
        orchid.ai_description = ai_results.get('description')
        orchid.ai_confidence = ai_results.get('confidence', 0.0)
        orchid.ai_extracted_metadata = json.dumps(ai_results)
        
        # Enhanced flowering metadata
        orchid.is_flowering = ai_results.get('is_flowering', False)
        orchid.flowering_stage = ai_results.get('flowering_stage')
        orchid.flower_count = ai_results.get('flower_count', 0)
        orchid.inflorescence_count = ai_results.get('inflorescence_count', 0)
        orchid.flower_size_mm = ai_results.get('flower_size_mm')
        orchid.flower_measurements = ai_results.get('flower_measurements')
        orchid.bloom_season_indicator = ai_results.get('bloom_season_indicator')
        
        # Photo metadata from EXIF
        if ai_results.get('flowering_photo_date'):
            orchid.flowering_photo_date = datetime.fromisoformat(ai_results['flowering_photo_date'])
        if ai_results.get('flowering_photo_datetime'):
            orchid.flowering_photo_datetime = datetime.fromisoformat(ai_results['flowering_photo_datetime'])
        
        orchid.photo_gps_coordinates = ai_results.get('photo_gps_coordinates')
        orchid.camera_info = ai_results.get('camera_info')
        orchid.exif_data = ai_results.get('exif_data')
        
        # Enhanced habitat and environment analysis
        orchid.growing_environment = ai_results.get('growing_environment')
        orchid.substrate_type = ai_results.get('substrate_type')
        orchid.mounting_evidence = ai_results.get('mounting_evidence')
        orchid.natural_vs_cultivated = ai_results.get('natural_vs_cultivated')
        
        # Environmental conditions observed
        orchid.light_conditions = ai_results.get('light_conditions')
        orchid.humidity_indicators = ai_results.get('humidity_indicators')
        orchid.temperature_indicators = ai_results.get('temperature_indicators')
        
        # Update growth habit with AI analysis if more specific
        if ai_results.get('growth_habit') and ai_results['growth_habit'] != 'unknown':
            orchid.growth_habit = ai_results['growth_habit']
        
        # Plant morphology details
        orchid.root_visibility = ai_results.get('root_visibility')
        orchid.plant_maturity = ai_results.get('plant_maturity')
        
        # Location and context
        orchid.setting_type = ai_results.get('setting_type')
        orchid.companion_plants = ai_results.get('companion_plants')
        orchid.elevation_indicators = ai_results.get('elevation_indicators')
        orchid.conservation_status_clues = ai_results.get('conservation_status_clues')
        
        # Update cultural notes with AI recommendations
        if ai_results.get('cultural_tips'):
            existing_notes = orchid.cultural_notes or ""
            orchid.cultural_notes = f"{existing_notes}\n\nAI Analysis: {ai_results['cultural_tips']}" if existing_notes else ai_results['cultural_tips']
        
        # Update timestamps
        orchid.updated_at = datetime.utcnow()
        
        # Commit changes
        db.session.commit()
        
        logger.info(f"✅ Updated orchid {orchid.id} with enhanced metadata")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error updating orchid: {e}")
        db.session.rollback()
        return False

def get_orchid_metadata_summary(orchid):
    """
    Get summary of orchid metadata for reporting
    
    Args:
        orchid: OrchidRecord instance
    
    Returns:
        dict: Summary of metadata fields
    """
    return {
        'basic_info': {
            'display_name': orchid.display_name,
            'scientific_name': orchid.scientific_name,
            'genus': orchid.genus,
            'species': orchid.species
        },
        'flowering_analysis': {
            'is_flowering': orchid.is_flowering,
            'flowering_stage': orchid.flowering_stage,
            'flower_count': orchid.flower_count,
            'inflorescence_count': orchid.inflorescence_count,
            'flower_size_mm': orchid.flower_size_mm,
            'flowering_photo_date': orchid.flowering_photo_date.isoformat() if orchid.flowering_photo_date else None
        },
        'habitat_environment': {
            'growing_environment': orchid.growing_environment,
            'substrate_type': orchid.substrate_type,
            'natural_vs_cultivated': orchid.natural_vs_cultivated,
            'growth_habit': orchid.growth_habit,
            'setting_type': orchid.setting_type
        },
        'location_data': {
            'gps_coordinates': orchid.photo_gps_coordinates,
            'region': orchid.region,
            'country': orchid.country,
            'decimal_latitude': orchid.decimal_latitude,
            'decimal_longitude': orchid.decimal_longitude
        },
        'analysis_metadata': {
            'ai_confidence': orchid.ai_confidence,
            'plant_maturity': orchid.plant_maturity,
            'conservation_clues': orchid.conservation_status_clues,
            'last_updated': orchid.updated_at.isoformat() if orchid.updated_at else None
        }
    }

def bulk_analyze_orchids(orchid_ids, progress_callback=None):
    """
    Analyze multiple orchids in batch
    
    Args:
        orchid_ids: List of orchid IDs to analyze
        progress_callback: Optional callback function for progress updates
    
    Returns:
        dict: Batch analysis results
    """
    results = {
        'total_orchids': len(orchid_ids),
        'successful_analyses': 0,
        'failed_analyses': 0,
        'results': [],
        'errors': []
    }
    
    for i, orchid_id in enumerate(orchid_ids):
        try:
            if progress_callback:
                progress_callback(i + 1, len(orchid_ids), orchid_id)
            
            analysis_result = analyze_and_update_orchid(orchid_id)
            results['results'].append(analysis_result)
            
            if analysis_result['success']:
                results['successful_analyses'] += 1
            else:
                results['failed_analyses'] += 1
                results['errors'].append(analysis_result)
                
        except Exception as e:
            error_result = {
                'success': False,
                'error': str(e),
                'orchid_id': orchid_id
            }
            results['results'].append(error_result)
            results['failed_analyses'] += 1
            results['errors'].append(error_result)
            
            logger.error(f"❌ Batch analysis error for orchid {orchid_id}: {e}")
    
    logger.info(f"📊 Batch analysis complete: {results['successful_analyses']}/{results['total_orchids']} successful")
    return results

def get_flowering_statistics():
    """
    Get statistics about flowering orchids in the database
    
    Returns:
        dict: Flowering statistics
    """
    try:
        total_orchids = OrchidRecord.query.count()
        flowering_orchids = OrchidRecord.query.filter_by(is_flowering=True).count()
        with_flower_counts = OrchidRecord.query.filter(OrchidRecord.flower_count > 0).count()
        with_gps_data = OrchidRecord.query.filter(OrchidRecord.photo_gps_coordinates.isnot(None)).count()
        with_photo_dates = OrchidRecord.query.filter(OrchidRecord.flowering_photo_date.isnot(None)).count()
        
        # Get flowering stages distribution
        flowering_stages = db.session.query(
            OrchidRecord.flowering_stage,
            db.func.count(OrchidRecord.id)
        ).filter(
            OrchidRecord.flowering_stage.isnot(None)
        ).group_by(OrchidRecord.flowering_stage).all()
        
        # Get habitat distribution
        habitat_distribution = db.session.query(
            OrchidRecord.natural_vs_cultivated,
            db.func.count(OrchidRecord.id)
        ).filter(
            OrchidRecord.natural_vs_cultivated.isnot(None)
        ).group_by(OrchidRecord.natural_vs_cultivated).all()
        
        return {
            'total_orchids': total_orchids,
            'flowering_orchids': flowering_orchids,
            'flowering_percentage': (flowering_orchids / total_orchids * 100) if total_orchids > 0 else 0,
            'with_flower_counts': with_flower_counts,
            'with_gps_data': with_gps_data,
            'with_photo_dates': with_photo_dates,
            'flowering_stages': dict(flowering_stages),
            'habitat_distribution': dict(habitat_distribution)
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting flowering statistics: {e}")
        return {'error': str(e)}