"""
Google Drive Orchid Importer for Orchid Continuum
Handles batch importing of orchid images from Google Drive folders
"""

import logging
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from google_drive_service import batch_import_from_drive_folder, get_folder_contents
from models import OrchidRecord, db
from orchid_processor import OrchidProcessor
from datetime import datetime
import json

logger = logging.getLogger(__name__)

drive_import_bp = Blueprint('drive_import', __name__, url_prefix='/drive-import')

@drive_import_bp.route('/')
@login_required
def import_dashboard():
    """Dashboard for Google Drive import operations"""
    return render_template('admin/drive_import.html')

@drive_import_bp.route('/preview-folder', methods=['POST'])
@login_required
def preview_folder():
    """Preview contents of a Google Drive folder"""
    try:
        data = request.get_json()
        folder_url = data.get('folder_url', '')
        
        # Extract folder ID from URL
        folder_id = extract_folder_id_from_url(folder_url)
        if not folder_id:
            return jsonify({'error': 'Invalid Google Drive folder URL'}), 400
        
        # Get folder contents
        files = get_folder_contents(folder_id)
        
        return jsonify({
            'success': True,
            'folder_id': folder_id,
            'file_count': len(files),
            'files': files[:20],  # Preview first 20 files
            'total_files': len(files)
        })
        
    except Exception as e:
        logger.error(f"Error previewing folder: {e}")
        return jsonify({'error': str(e)}), 500

@drive_import_bp.route('/import-folder', methods=['POST'])
@login_required
def import_folder():
    """Import orchid images from a Google Drive folder"""
    try:
        data = request.get_json()
        folder_url = data.get('folder_url', '')
        limit = int(data.get('limit', 50))
        auto_process = data.get('auto_process', True)
        
        # Extract folder ID from URL
        folder_id = extract_folder_id_from_url(folder_url)
        if not folder_id:
            return jsonify({'error': 'Invalid Google Drive folder URL'}), 400
        
        # Perform batch import
        import_result = batch_import_from_drive_folder(folder_id, limit)
        
        if not import_result.get('success'):
            return jsonify({'error': import_result.get('error', 'Import failed')}), 500
        
        # Process imported files through the orchid processor if requested
        processed_records = []
        if auto_process and import_result.get('results'):
            processor = OrchidProcessor()
            
            for result in import_result['results']:
                if result.get('success'):
                    try:
                        # Create database record from imported file
                        db_record = create_orchid_record_from_import(result)
                        processed_records.append(db_record.id if db_record else None)
                        
                    except Exception as e:
                        logger.error(f"Error creating database record: {e}")
        
        return jsonify({
            'success': True,
            'imported_count': import_result['imported_count'],
            'total_processed': import_result['total_processed'],
            'processed_records': len([r for r in processed_records if r]),
            'import_results': import_result['results']
        })
        
    except Exception as e:
        logger.error(f"Error importing folder: {e}")
        return jsonify({'error': str(e)}), 500

def extract_folder_id_from_url(url: str) -> str:
    """Extract folder ID from Google Drive URL"""
    if '/folders/' in url:
        # Format: https://drive.google.com/drive/folders/1YqIWmIfaXSy_0_bAbvSG8EMQjAuNq0lj
        return url.split('/folders/')[-1].split('?')[0]
    elif 'id=' in url:
        # Format: https://drive.google.com/drive/u/0/folders/1YqIWmIfaXSy_0_bAbvSG8EMQjAuNq0lj?resourcekey=
        return url.split('id=')[-1].split('&')[0]
    return ''

def create_orchid_record_from_import(import_result: dict) -> OrchidRecord | None:
    """Create an OrchidRecord from import result"""
    try:
        # Extract data from import result
        suggested_name = import_result.get('suggested_name', 'Unknown Orchid')
        filename = import_result.get('processed_filename')
        file_path = import_result.get('processed_path')
        original_file_id = import_result.get('original_file_id')
        
        # Parse potential genus/species from suggested name
        words = suggested_name.split()
        genus = words[0] if len(words) > 0 else 'Unknown'
        species = words[1] if len(words) > 1 else 'sp.'
        
        # Create new orchid record
        orchid = OrchidRecord()
        orchid.display_name = suggested_name
        orchid.genus = genus
        orchid.species = species
        orchid.hybrid_type = 'species'  # Default, can be updated later
        orchid.image_filename = filename
        orchid.image_url = f'/static/uploads/{filename}' if filename else None
        orchid.google_drive_id = original_file_id
        orchid.photographer = 'Imported from Google Drive'
        orchid.image_source = 'google_drive_import'
        orchid.ingestion_source = 'drive_import'
        orchid.validation_status = 'pending'
        orchid.notes = f'Imported from Google Drive folder on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        orchid.created_at = datetime.utcnow()
        orchid.updated_at = datetime.utcnow()
        
        db.session.add(orchid)
        db.session.commit()
        
        logger.info(f"Created orchid record {orchid.id} for {suggested_name}")
        return orchid
        
    except Exception as e:
        logger.error(f"Error creating orchid record: {e}")
        db.session.rollback()
        return None

@drive_import_bp.route('/import-status/<int:import_id>')
@login_required
def import_status(import_id):
    """Get status of an import operation"""
    # This would track long-running imports if needed
    return jsonify({'status': 'completed', 'message': 'Import completed'})