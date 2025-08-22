"""
Photo Editor Integration for Orchid Continuum
Manages separate storage for original submissions vs edited versions
"""

import os
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from PIL import Image
from werkzeug.utils import secure_filename
import uuid

from models import OrchidRecord, db
from google_drive_service import upload_to_drive, get_drive_file_url

logger = logging.getLogger(__name__)

class PhotoEditorManager:
    def __init__(self):
        self.temp_dir = 'temp'
        self.original_folder = 'Orchid_Original_Submissions'
        self.edited_folder = 'Orchid_Edited_Versions'
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def prepare_photo_for_editing(self, orchid_id: int) -> Dict[str, Any]:
        """Prepare an orchid photo for editing by creating a working copy"""
        try:
            orchid = OrchidRecord.query.get_or_404(orchid_id)
            
            if not orchid.image_url:
                return {'error': 'No image available for editing'}
            
            # Create editing session
            editing_session = {
                'session_id': str(uuid.uuid4()),
                'orchid_id': orchid_id,
                'original_url': orchid.image_url,
                'original_filename': orchid.image_filename or f'orchid_{orchid_id}.jpg',
                'created_at': datetime.now().isoformat(),
                'modifications': []
            }
            
            # Store session info in orchid record
            enhancement_data = json.loads(orchid.enhancement_data or '{}')
            if 'editing_sessions' not in enhancement_data:
                enhancement_data['editing_sessions'] = []
            
            enhancement_data['editing_sessions'].append(editing_session)
            orchid.enhancement_data = json.dumps(enhancement_data)
            db.session.commit()
            
            return {
                'success': True,
                'session_id': editing_session['session_id'],
                'orchid_id': orchid_id,
                'orchid_name': orchid.scientific_name or orchid.display_name,
                'image_url': orchid.image_url,
                'editing_url': f'/photo-editor/{editing_session["session_id"]}'
            }
            
        except Exception as e:
            logger.error(f"Error preparing photo for editing: {e}")
            return {'error': str(e)}
    
    def save_edited_version(self, session_id: str, edited_image_data: bytes, 
                           modifications: List[Dict], notes: str = "") -> Dict[str, Any]:
        """Save an edited version while keeping the original intact"""
        try:
            # Find the editing session
            orchid = self._find_orchid_by_session(session_id)
            if not orchid:
                return {'error': 'Invalid editing session'}
            
            # Generate filename for edited version
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = orchid.image_filename or f'orchid_{orchid.id}'
            name_without_ext = os.path.splitext(base_name)[0]
            edited_filename = f'{name_without_ext}_edited_{timestamp}.jpg'
            
            # Save edited image temporarily
            temp_path = os.path.join(self.temp_dir, edited_filename)
            with open(temp_path, 'wb') as f:
                f.write(edited_image_data)
            
            # Upload edited version to Google Drive
            edited_drive_id = upload_to_drive(temp_path, edited_filename, self.edited_folder)
            edited_url = get_drive_file_url(edited_drive_id) if edited_drive_id else None
            
            # Update orchid record with edited version info
            enhancement_data = json.loads(orchid.enhancement_data or '{}')
            
            if 'edited_versions' not in enhancement_data:
                enhancement_data['edited_versions'] = []
            
            edited_version = {
                'version_id': str(uuid.uuid4()),
                'session_id': session_id,
                'filename': edited_filename,
                'drive_id': edited_drive_id,
                'url': edited_url,
                'modifications': modifications,
                'editor_notes': notes,
                'created_at': datetime.now().isoformat()
            }
            
            enhancement_data['edited_versions'].append(edited_version)
            orchid.enhancement_data = json.dumps(enhancement_data)
            
            # Track that this orchid has edited versions
            orchid.has_edited_versions = True
            
            db.session.commit()
            
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
            return {
                'success': True,
                'version_id': edited_version['version_id'],
                'edited_url': edited_url,
                'message': 'Edited version saved successfully'
            }
            
        except Exception as e:
            logger.error(f"Error saving edited version: {e}")
            return {'error': str(e)}
    
    def get_editing_history(self, orchid_id: int) -> Dict[str, Any]:
        """Get the editing history for an orchid"""
        try:
            orchid = OrchidRecord.query.get_or_404(orchid_id)
            enhancement_data = json.loads(orchid.enhancement_data or '{}')
            
            return {
                'orchid_id': orchid_id,
                'orchid_name': orchid.scientific_name or orchid.display_name,
                'original_url': orchid.image_url,
                'editing_sessions': enhancement_data.get('editing_sessions', []),
                'edited_versions': enhancement_data.get('edited_versions', []),
                'has_edited_versions': len(enhancement_data.get('edited_versions', [])) > 0
            }
            
        except Exception as e:
            logger.error(f"Error getting editing history: {e}")
            return {'error': str(e)}
    
    def _find_orchid_by_session(self, session_id: str) -> Optional[OrchidRecord]:
        """Find orchid record by editing session ID"""
        try:
            # Search for orchid with this session ID
            orchids = OrchidRecord.query.all()
            
            for orchid in orchids:
                if orchid.enhancement_data:
                    enhancement_data = json.loads(orchid.enhancement_data)
                    sessions = enhancement_data.get('editing_sessions', [])
                    
                    for session in sessions:
                        if session.get('session_id') == session_id:
                            return orchid
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding orchid by session: {e}")
            return None
    
    def delete_edited_version(self, orchid_id: int, version_id: str) -> Dict[str, Any]:
        """Delete a specific edited version"""
        try:
            orchid = OrchidRecord.query.get_or_404(orchid_id)
            enhancement_data = json.loads(orchid.enhancement_data or '{}')
            
            edited_versions = enhancement_data.get('edited_versions', [])
            
            # Find and remove the version
            updated_versions = [v for v in edited_versions if v.get('version_id') != version_id]
            
            if len(updated_versions) == len(edited_versions):
                return {'error': 'Version not found'}
            
            enhancement_data['edited_versions'] = updated_versions
            orchid.enhancement_data = json.dumps(enhancement_data)
            
            # Update has_edited_versions flag
            orchid.has_edited_versions = len(updated_versions) > 0
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Edited version deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"Error deleting edited version: {e}")
            return {'error': str(e)}
    
    def get_orchids_with_edited_versions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get orchids that have edited versions available"""
        try:
            orchids = OrchidRecord.query.filter_by(has_edited_versions=True).limit(limit).all()
            
            result = []
            for orchid in orchids:
                enhancement_data = json.loads(orchid.enhancement_data or '{}')
                edited_versions = enhancement_data.get('edited_versions', [])
                
                result.append({
                    'id': orchid.id,
                    'name': orchid.scientific_name or orchid.display_name,
                    'original_url': orchid.image_url,
                    'version_count': len(edited_versions),
                    'last_edited': edited_versions[-1]['created_at'] if edited_versions else None,
                    'submitter': orchid.submitter_name
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error getting orchids with edited versions: {e}")
            return []
    
    def create_comparison_view(self, orchid_id: int) -> Dict[str, Any]:
        """Create a comparison view between original and edited versions"""
        try:
            history = self.get_editing_history(orchid_id)
            
            if 'error' in history:
                return history
            
            comparison = {
                'orchid_id': orchid_id,
                'orchid_name': history['orchid_name'],
                'original': {
                    'url': history['original_url'],
                    'label': 'Original Submission',
                    'source': 'Google Forms'
                },
                'edited_versions': []
            }
            
            for version in history['edited_versions']:
                comparison['edited_versions'].append({
                    'version_id': version['version_id'],
                    'url': version['url'],
                    'label': f"Edited {version['created_at'][:10]}",
                    'modifications': version['modifications'],
                    'notes': version.get('editor_notes', ''),
                    'created_at': version['created_at']
                })
            
            return comparison
            
        except Exception as e:
            logger.error(f"Error creating comparison view: {e}")
            return {'error': str(e)}