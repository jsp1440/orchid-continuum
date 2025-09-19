#!/usr/bin/env python3
"""
Mobile Field Research System for Orchid Continuum
Progressive Web App with offline capabilities for field researchers
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
import logging
import json
import os
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from werkzeug.utils import secure_filename
from PIL import Image
import io
import base64

from models import db, FieldObservation
from google_drive_service import upload_to_drive
from orchid_ai import analyze_orchid_image

logger = logging.getLogger(__name__)

# Create blueprint for field research mobile app
field_research_bp = Blueprint('field_research', __name__, url_prefix='/field')

# FieldObservation model is now imported from models.py

@field_research_bp.route('/')
def mobile_app():
    """Main mobile field research app"""
    try:
        # Check if user is accessing from mobile
        user_agent = request.headers.get('User-Agent', '').lower()
        is_mobile = any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone'])
        
        return render_template('field_research/mobile_app.html', 
                             is_mobile=is_mobile,
                             app_version="1.0.0")
    
    except Exception as e:
        logger.error(f"Error loading mobile app: {e}")
        return render_template('error.html', error="Error loading mobile field research app")

@field_research_bp.route('/capture')
def capture_interface():
    """Camera capture interface"""
    return render_template('field_research/capture.html')

@field_research_bp.route('/observation', methods=['POST'])
def create_observation():
    """Create new field observation"""
    try:
        data = request.get_json()
        
        # Create observation record
        observation = FieldObservation()
        
        # Basic info
        observation.researcher_name = data.get('researcher_name')
        observation.researcher_email = data.get('researcher_email')
        observation.session_id = data.get('session_id', str(uuid.uuid4())[:8])
        
        # Location data
        observation.latitude = data.get('latitude')
        observation.longitude = data.get('longitude')
        observation.altitude = data.get('altitude')
        observation.location_accuracy = data.get('location_accuracy')
        observation.location_description = data.get('location_description')
        
        # Environmental conditions
        observation.habitat_notes = data.get('habitat_notes')
        observation.weather_conditions = data.get('weather_conditions')
        observation.light_conditions = data.get('light_conditions')
        observation.substrate_type = data.get('substrate_type')
        observation.companion_species = data.get('companion_species')
        
        # Orchid data
        observation.tentative_genus = data.get('tentative_genus')
        observation.tentative_species = data.get('tentative_species')
        observation.growth_stage = data.get('growth_stage')
        observation.flower_color = data.get('flower_color')
        observation.estimated_size = data.get('estimated_size')
        observation.population_count = data.get('population_count')
        
        # Field notes
        observation.field_notes = data.get('field_notes')
        observation.research_questions = data.get('research_questions')
        observation.conservation_concerns = data.get('conservation_concerns')
        
        # Privacy settings
        observation.sensitivity_flag = data.get('sensitivity_flag', False)
        observation.location_privacy = data.get('location_privacy', 'precise')
        observation.research_consent = data.get('research_consent', True)
        
        # Save to database
        db.session.add(observation)
        db.session.commit()
        
        logger.info(f"📱 Created field observation: {observation.observation_id}")
        
        return jsonify({
            'success': True,
            'observation_id': observation.observation_id,
            'message': 'Observation recorded successfully'
        })
        
    except Exception as e:
        logger.error(f"Error creating observation: {e}")
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)})

@field_research_bp.route('/upload', methods=['POST'])
def upload_photo():
    """Upload photo for field observation"""
    try:
        observation_id = request.form.get('observation_id')
        
        if not observation_id:
            return jsonify({'success': False, 'error': 'Observation ID required'})
        
        # Get observation record
        observation = FieldObservation.query.filter_by(observation_id=observation_id).first()
        if not observation:
            return jsonify({'success': False, 'error': 'Observation not found'})
        
        # Handle file upload
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo uploaded'})
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No photo selected'})
        
        if file and file.filename and allowed_file(file.filename):
            # Secure filename
            filename = f"field_{observation_id}_{secure_filename(file.filename)}"
            
            # Upload to Google Drive
            drive_id = upload_to_drive(file, filename, folder_name='Field_Observations')
            
            if drive_id:
                # Update observation with photo info
                observation.photo_drive_id = drive_id
                observation.photo_filename = filename
                observation.photo_url = f"/api/drive-photo/{drive_id}"
                observation.sync_status = 'synced'
                
                db.session.commit()
                
                # Queue for AI analysis
                queue_ai_analysis(observation_id)
                
                logger.info(f"📸 Uploaded photo for observation {observation_id}: {drive_id}")
                
                return jsonify({
                    'success': True,
                    'photo_url': observation.photo_url,
                    'drive_id': drive_id
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to upload photo'})
        
        return jsonify({'success': False, 'error': 'Invalid file type'})
        
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        return jsonify({'success': False, 'error': str(e)})

@field_research_bp.route('/upload/chunk', methods=['POST'])
def upload_chunk():
    """Upload photo in chunks for low bandwidth connections"""
    try:
        observation_id = request.form.get('observation_id')
        chunk_number = int(request.form.get('chunk_number', 0))
        total_chunks = int(request.form.get('total_chunks', 1))
        chunk_data = request.form.get('chunk_data')  # Base64 encoded
        
        if not all([observation_id, chunk_data]):
            return jsonify({'success': False, 'error': 'Missing required data'})
        
        # Store chunk temporarily (in production, use Redis or similar)
        chunk_key = f"chunk_{observation_id}_{chunk_number}"
        # For now, store in temporary file system
        os.makedirs('/tmp/chunks', exist_ok=True)
        
        with open(f'/tmp/chunks/{chunk_key}', 'wb') as f:
            f.write(base64.b64decode(chunk_data))
        
        # If this is the last chunk, assemble the file
        if chunk_number == total_chunks - 1:
            return assemble_chunks(observation_id, total_chunks)
        else:
            return jsonify({
                'success': True,
                'chunk_received': chunk_number,
                'remaining': total_chunks - chunk_number - 1
            })
        
    except Exception as e:
        logger.error(f"Error uploading chunk: {e}")
        return jsonify({'success': False, 'error': str(e)})

@field_research_bp.route('/queue/status')
def get_queue_status():
    """Get sync queue status for offline observations"""
    try:
        session_id = request.args.get('session_id')
        
        if session_id:
            observations = FieldObservation.query.filter_by(
                session_id=session_id
            ).order_by(FieldObservation.created_at.desc()).limit(20).all()
        else:
            # Return recent pending observations
            observations = FieldObservation.query.filter_by(
                sync_status='pending'
            ).order_by(FieldObservation.created_at.desc()).limit(10).all()
        
        queue_data = []
        for obs in observations:
            queue_data.append({
                'observation_id': obs.observation_id,
                'sync_status': obs.sync_status,
                'processing_status': obs.processing_status,
                'created_at': obs.created_at.isoformat() if obs.created_at else None,
                'has_photo': bool(obs.photo_drive_id),
                'ai_identification': obs.ai_identification
            })
        
        return jsonify({
            'success': True,
            'queue': queue_data,
            'pending_count': len([q for q in queue_data if q['sync_status'] == 'pending'])
        })
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@field_research_bp.route('/observations/<observation_id>')
def get_observation(observation_id):
    """Get specific observation details"""
    try:
        observation = FieldObservation.query.filter_by(observation_id=observation_id).first()
        
        if not observation:
            return jsonify({'success': False, 'error': 'Observation not found'})
        
        return jsonify({
            'success': True,
            'observation': observation.to_dict()
        })
        
    except Exception as e:
        logger.error(f"Error getting observation: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Helper functions
def allowed_file(filename):
    """Check if uploaded file type is allowed"""
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def queue_ai_analysis(observation_id: str):
    """Queue observation for AI analysis"""
    try:
        observation = FieldObservation.query.filter_by(observation_id=observation_id).first()
        if not observation or not observation.photo_drive_id:
            return False
        
        # Update processing status
        observation.processing_status = 'processing'
        db.session.commit()
        
        # Run AI analysis (simplified version)
        if observation.photo_url:
            ai_result = analyze_orchid_image(observation.photo_url)
            
            if ai_result:
                observation.ai_identification = ai_result
                observation.ai_confidence = ai_result.get('confidence', 0)
                observation.processing_status = 'completed'
                
                # Extract genus/species if identified
                if ai_result.get('genus'):
                    observation.tentative_genus = ai_result.get('genus')
                if ai_result.get('species'):
                    observation.tentative_species = ai_result.get('species')
                
                db.session.commit()
                logger.info(f"🤖 AI analysis completed for {observation_id}")
                return True
            else:
                observation.processing_status = 'failed'
                db.session.commit()
        
        return False
        
    except Exception as e:
        logger.error(f"Error in AI analysis for {observation_id}: {e}")
        return False

def assemble_chunks(observation_id: str, total_chunks: int):
    """Assemble uploaded chunks into complete file"""
    try:
        # Read all chunks
        assembled_data = b''
        for i in range(total_chunks):
            chunk_path = f'/tmp/chunks/chunk_{observation_id}_{i}'
            if os.path.exists(chunk_path):
                with open(chunk_path, 'rb') as f:
                    assembled_data += f.read()
                os.remove(chunk_path)  # Clean up
        
        # Create file object from assembled data
        file_obj = io.BytesIO(assembled_data)
        filename = f"field_{observation_id}_chunked.jpg"
        
        # Upload to Google Drive
        drive_id = upload_to_drive(file_obj, filename, folder_name='Field_Observations')
        
        if drive_id:
            # Update observation
            observation = FieldObservation.query.filter_by(observation_id=observation_id).first()
            if observation:
                observation.photo_drive_id = drive_id
                observation.photo_filename = filename
                observation.photo_url = f"/api/drive-photo/{drive_id}"
                observation.sync_status = 'synced'
                db.session.commit()
                
                # Queue for AI analysis
                queue_ai_analysis(observation_id)
                
                return jsonify({
                    'success': True,
                    'message': 'File assembled and uploaded successfully',
                    'photo_url': observation.photo_url
                })
        
        return jsonify({'success': False, 'error': 'Failed to upload assembled file'})
        
    except Exception as e:
        logger.error(f"Error assembling chunks: {e}")
        return jsonify({'success': False, 'error': str(e)})

# Service worker and PWA manifest routes
@field_research_bp.route('/manifest.json')
def pwa_manifest():
    """PWA manifest for mobile app installation"""
    manifest = {
        "name": "Orchid Field Research",
        "short_name": "OrchidField",
        "description": "Field research tool for orchid observations",
        "start_url": "/field/",
        "display": "standalone",
        "background_color": "#1a202c",
        "theme_color": "#805ad5",
        "orientation": "portrait",
        "icons": [
            {
                "src": "/static/icons/orchid-icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/orchid-icon-512.png", 
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
    
    response = jsonify(manifest)
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

@field_research_bp.route('/sw.js')
def service_worker():
    """Service worker for offline functionality"""
    return render_template('field_research/service_worker.js'), 200, {'Content-Type': 'application/javascript'}