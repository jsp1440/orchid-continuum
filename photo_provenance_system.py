"""
Photo Provenance and Source Tracking System
Ensures transparency and accountability for all orchid photos in the database
"""

from flask import Blueprint, render_template, request, jsonify, session, flash
from models import db, OrchidRecord, UserUpload, ScrapingLog
from datetime import datetime
import json
import logging
import re

logger = logging.getLogger(__name__)

provenance_bp = Blueprint('provenance', __name__, url_prefix='/provenance')

class PhotoProvenance:
    """Manages photo source tracking and verification"""
    
    @staticmethod
    def get_photo_source_info(orchid_id):
        """Get comprehensive source information for an orchid photo"""
        try:
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                return None
            
            # Determine the source type and details
            source_info = {
                'orchid_id': orchid_id,
                'photo_type': None,
                'source_name': 'Unknown',
                'contributor': 'Unknown',
                'date_added': None,
                'verification_status': 'Unverified',
                'photo_url': None,
                'metadata': {},
                'confidence_level': 'Low'
            }
            
            # Check if it's a Google Drive photo (FCOS collection)
            if orchid.google_drive_id:
                source_info.update({
                    'photo_type': 'Google Drive (FCOS Collection)',
                    'source_name': 'Five Cities Orchid Society',
                    'contributor': 'FCOS Members',
                    'photo_url': f'/api/drive-photo/{orchid.google_drive_id}',
                    'verification_status': 'Society Verified',
                    'confidence_level': 'High',
                    'metadata': {
                        'drive_id': orchid.google_drive_id,
                        'collection': 'Official FCOS Collection',
                        'quality': 'Professional'
                    }
                })
            
            # Check if it's from web scraping
            elif orchid.photo_url:
                # Determine source from URL patterns
                if 'garyyonggee' in orchid.photo_url or 'orchids.yonggee.name' in orchid.photo_url:
                    source_info.update({
                        'photo_type': 'Scraped from Gary Yong Gee',
                        'source_name': 'Gary Yong Gee Orchid Database',
                        'contributor': 'Gary Yong Gee',
                        'verification_status': 'Expert Verified',
                        'confidence_level': 'High',
                        'metadata': {
                            'source_url': orchid.photo_url,
                            'expert': 'Gary Yong Gee',
                            'database': 'Professional Orchid Database'
                        }
                    })
                elif 'robertafox' in orchid.photo_url or 'aos.org' in orchid.photo_url:
                    source_info.update({
                        'photo_type': 'AOS/Roberta Fox Collection',
                        'source_name': 'American Orchid Society',
                        'contributor': 'Roberta Fox',
                        'verification_status': 'AOS Verified',
                        'confidence_level': 'High',
                        'metadata': {
                            'source_url': orchid.photo_url,
                            'organization': 'American Orchid Society',
                            'expert': 'Roberta Fox'
                        }
                    })
                elif 'gbif.org' in orchid.photo_url:
                    source_info.update({
                        'photo_type': 'GBIF Scientific Database',
                        'source_name': 'Global Biodiversity Information Facility',
                        'contributor': 'Scientific Community',
                        'verification_status': 'Scientifically Verified',
                        'confidence_level': 'Very High',
                        'metadata': {
                            'source_url': orchid.photo_url,
                            'database': 'GBIF',
                            'type': 'Scientific Specimen'
                        }
                    })
                else:
                    # Unknown web source
                    source_info.update({
                        'photo_type': 'Web Source',
                        'source_name': 'External Website',
                        'contributor': 'Unknown Web Source',
                        'verification_status': 'Unverified',
                        'confidence_level': 'Low',
                        'metadata': {
                            'source_url': orchid.photo_url,
                            'needs_verification': True
                        }
                    })
            
            # Check for user uploads
            user_upload = UserUpload.query.filter_by(orchid_id=orchid_id).first()
            if user_upload:
                source_info.update({
                    'photo_type': 'User Upload',
                    'source_name': 'Community Contribution',
                    'contributor': f"User {user_upload.user_id}",
                    'date_added': user_upload.created_at,
                    'verification_status': 'Community Submitted',
                    'confidence_level': 'Medium',
                    'metadata': {
                        'upload_id': user_upload.id,
                        'user_id': user_upload.user_id,
                        'filename': user_upload.filename
                    }
                })
            
            # Check scraping logs for more details
            scraping_log = ScrapingLog.query.filter(
                ScrapingLog.details.like(f'%{orchid_id}%')
            ).first()
            
            if scraping_log:
                source_info['date_added'] = scraping_log.timestamp
                if scraping_log.source:
                    source_info['metadata']['scraping_source'] = scraping_log.source
            
            # Add orchid basic info
            source_info['orchid_info'] = {
                'genus': orchid.genus,
                'species': orchid.species,
                'display_name': orchid.display_name,
                'region': orchid.region
            }
            
            return source_info
            
        except Exception as e:
            logger.error(f"Error getting photo source info: {e}")
            return None
    
    @staticmethod
    def get_all_photo_sources():
        """Get summary of all photo sources in the database"""
        try:
            # Count by source type
            sources = {
                'fcos_collection': 0,
                'gary_yong_gee': 0,
                'aos_roberta_fox': 0,
                'gbif_scientific': 0,
                'user_uploads': 0,
                'unknown_web': 0,
                'no_photo': 0
            }
            
            all_orchids = OrchidRecord.query.all()
            
            for orchid in all_orchids:
                if orchid.google_drive_id:
                    sources['fcos_collection'] += 1
                elif orchid.photo_url:
                    if 'garyyonggee' in orchid.photo_url or 'orchids.yonggee.name' in orchid.photo_url:
                        sources['gary_yong_gee'] += 1
                    elif 'robertafox' in orchid.photo_url or 'aos.org' in orchid.photo_url:
                        sources['aos_roberta_fox'] += 1
                    elif 'gbif.org' in orchid.photo_url:
                        sources['gbif_scientific'] += 1
                    else:
                        sources['unknown_web'] += 1
                else:
                    # Check for user uploads
                    user_upload = UserUpload.query.filter_by(orchid_id=orchid.id).first()
                    if user_upload:
                        sources['user_uploads'] += 1
                    else:
                        sources['no_photo'] += 1
            
            return sources
            
        except Exception as e:
            logger.error(f"Error getting photo sources summary: {e}")
            return {}
    
    @staticmethod
    def flag_photo_for_verification(orchid_id, user_id, reason):
        """Flag a photo as needing source verification"""
        try:
            # Create a verification flag
            from models import UserActivity
            
            flag_activity = UserActivity()
            flag_activity.user_id = user_id
            flag_activity.activity_type = 'photo_verification_flag'
            flag_activity.points_earned = 1
            flag_activity.details = json.dumps({
                'orchid_id': orchid_id,
                'reason': reason,
                'flag_type': 'source_verification',
                'timestamp': datetime.now().isoformat()
            })
            
            db.session.add(flag_activity)
            db.session.commit()
            
            logger.info(f"Photo verification flag created for orchid {orchid_id} by user {user_id}")
            return {'success': True, 'message': 'Photo flagged for source verification'}
            
        except Exception as e:
            logger.error(f"Error flagging photo: {e}")
            db.session.rollback()
            return {'success': False, 'message': 'Failed to flag photo'}

# Routes
@provenance_bp.route('/dashboard')
def provenance_dashboard():
    """Photo provenance dashboard"""
    sources_summary = PhotoProvenance.get_all_photo_sources()
    
    return render_template('provenance/dashboard.html', 
                         sources=sources_summary)

@provenance_bp.route('/api/photo-source/<int:orchid_id>')
def api_photo_source(orchid_id):
    """API endpoint for photo source information"""
    source_info = PhotoProvenance.get_photo_source_info(orchid_id)
    
    if source_info:
        return jsonify(source_info)
    else:
        return jsonify({'error': 'Orchid not found'}), 404

@provenance_bp.route('/api/flag-photo', methods=['POST'])
def api_flag_photo():
    """API endpoint to flag photo for verification"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'error': 'Login required'}), 401
    
    data = request.get_json()
    orchid_id = data.get('orchid_id')
    reason = data.get('reason', '').strip()
    
    if not orchid_id or not reason:
        return jsonify({'error': 'Missing required fields'}), 400
    
    result = PhotoProvenance.flag_photo_for_verification(orchid_id, user_id, reason)
    return jsonify(result)

@provenance_bp.route('/api/sources-summary')
def api_sources_summary():
    """API endpoint for photo sources summary"""
    sources = PhotoProvenance.get_all_photo_sources()
    return jsonify(sources)