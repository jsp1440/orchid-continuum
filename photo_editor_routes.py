"""
Photo Editor Routes for Orchid Continuum
Web interface and API endpoints for advanced photo editing
"""

from flask import Blueprint, render_template, request, jsonify, send_file, session, redirect, url_for
from flask_login import login_required, current_user
import logging
import os
from datetime import datetime

from advanced_photo_editor import photo_editor, photo_editor_bp
from models import OrchidRecord, db
from admin_system import admin_required

logger = logging.getLogger(__name__)

@photo_editor_bp.route('/')
@login_required
def photo_editor_home():
    """Photo editor home page - list orchids available for editing"""
    try:
        # Get orchids with images
        orchids = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None)
        ).order_by(OrchidRecord.created_at.desc()).limit(50).all()
        
        # Get orchids with edited versions
        edited_orchids = []
        for orchid in orchids:
            if orchid.enhancement_data:
                try:
                    import json
                    enhancement_data = json.loads(orchid.enhancement_data)
                    if enhancement_data.get('edited_versions'):
                        edited_orchids.append({
                            'orchid': orchid,
                            'versions': len(enhancement_data['edited_versions'])
                        })
                except:
                    pass
        
        return render_template('photo_editor/home.html', 
                             orchids=orchids, 
                             edited_orchids=edited_orchids)
        
    except Exception as e:
        logger.error(f"Error loading photo editor home: {e}")
        return render_template('photo_editor/home.html', 
                             orchids=[], 
                             edited_orchids=[],
                             error=str(e))

@photo_editor_bp.route('/create-session/<int:orchid_id>')
@login_required
def create_editing_session(orchid_id):
    """Create a new photo editing session"""
    try:
        user_id = str(current_user.id) if current_user.is_authenticated else None
        result = photo_editor.create_editing_session(orchid_id, user_id)
        
        if result.get('success'):
            return redirect(url_for('photo_editor.edit_photo', session_id=result['session_id']))
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error creating editing session: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/edit/<session_id>')
@login_required
def edit_photo(session_id):
    """Photo editing interface"""
    try:
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data:
            return render_template('photo_editor/error.html', 
                                 error='Invalid or expired editing session')
        
        return render_template('photo_editor/editor.html', 
                             session_id=session_id,
                             session_data=session_data)
        
    except Exception as e:
        logger.error(f"Error loading photo editor: {e}")
        return render_template('photo_editor/error.html', error=str(e))

@photo_editor_bp.route('/api/adjust', methods=['POST'])
@login_required
def api_adjust_image():
    """API endpoint for basic image adjustments"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        result = photo_editor.apply_basic_adjustments(
            session_id=session_id,
            brightness=data.get('brightness', 1.0),
            contrast=data.get('contrast', 1.0),
            saturation=data.get('saturation', 1.0),
            sharpness=data.get('sharpness', 1.0)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error adjusting image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/crop', methods=['POST'])
@login_required
def api_crop_image():
    """API endpoint for cropping"""
    try:
        data = request.get_json()
        
        result = photo_editor.apply_crop(
            session_id=data.get('session_id'),
            x=data.get('x', 0),
            y=data.get('y', 0),
            width=data.get('width', 100),
            height=data.get('height', 100)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error cropping image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/resize', methods=['POST'])
@login_required
def api_resize_image():
    """API endpoint for resizing"""
    try:
        data = request.get_json()
        
        result = photo_editor.apply_resize(
            session_id=data.get('session_id'),
            new_width=data.get('new_width', 800),
            new_height=data.get('new_height', 600),
            maintain_aspect=data.get('maintain_aspect', True)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error resizing image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/filter', methods=['POST'])
@login_required
def api_apply_filter():
    """API endpoint for applying filters"""
    try:
        data = request.get_json()
        
        result = photo_editor.apply_filters(
            session_id=data.get('session_id'),
            filter_type=data.get('filter_type', 'sharpen'),
            intensity=data.get('intensity', 1.0)
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error applying filter: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/analyze', methods=['POST'])
@login_required
def api_analyze_plant():
    """API endpoint for AI plant analysis"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        result = photo_editor.analyze_plant_features(session_id)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error analyzing plant: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/save', methods=['POST'])
@login_required
def api_save_image():
    """API endpoint for saving edited images with caption and sharing options"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        save_options = data.get('save_options', {})
        
        result = photo_editor.save_edited_image(session_id, save_options)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/generate-caption', methods=['POST'])
@login_required
def api_generate_caption():
    """API endpoint for generating social media captions"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        include_analysis = data.get('include_analysis', False)
        
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        from models import OrchidRecord
        orchid = OrchidRecord.query.get(session_data['orchid_id'])
        if not orchid:
            return jsonify({'error': 'Orchid not found'}), 404
        
        caption = photo_editor.generate_social_caption(orchid, include_analysis)
        
        return jsonify({
            'success': True,
            'caption': caption,
            'botanical_info': {
                'scientific_name': orchid.scientific_name,
                'genus': orchid.genus,
                'species': orchid.species,
                'display_name': orchid.display_name
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating caption: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/create-captioned', methods=['POST'])
@login_required
def api_create_captioned():
    """API endpoint for creating captioned images"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        caption_options = data.get('caption_options', {})
        
        result = photo_editor.create_captioned_image(session_id, caption_options)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error creating captioned image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/check-permissions/<int:orchid_id>/<usage_type>')
@login_required
def api_check_permissions(orchid_id, usage_type):
    """API endpoint for checking usage permissions"""
    try:
        result = photo_editor.check_usage_permissions(orchid_id, usage_type)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking permissions: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/session/<session_id>/status')
@login_required
def api_session_status(session_id):
    """Get current session status"""
    try:
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        status = {
            'session_id': session_id,
            'orchid_name': session_data['orchid_name'],
            'operations_count': len(session_data['edit_history']),
            'filters_applied': session_data['filters_applied'],
            'has_analysis': 'analysis_data' in session_data,
            'created_at': session_data['created_at']
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/api/undo', methods=['POST'])
@login_required
def api_undo_operation():
    """Undo last operation"""
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data or not session_data['edit_history']:
            return jsonify({'error': 'Nothing to undo'}), 400
        
        # Remove last operation
        last_operation = session_data['edit_history'].pop()
        
        # Revert to previous image
        if session_data['edit_history']:
            # Use the image from the previous operation
            session_data['current_path'] = session_data['edit_history'][-1]['file_path']
        else:
            # Revert to original
            session_data['current_path'] = session_data['original_path']
        
        # Clean up file from removed operation
        if os.path.exists(last_operation['file_path']):
            os.remove(last_operation['file_path'])
        
        return jsonify({
            'success': True,
            'undone_operation': last_operation['operation'],
            'operations_remaining': len(session_data['edit_history'])
        })
        
    except Exception as e:
        logger.error(f"Error undoing operation: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/download/<session_id>')
@login_required
def download_current_image(session_id):
    """Download current edited image"""
    try:
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data:
            return jsonify({'error': 'Session not found'}), 404
        
        current_path = session_data['current_path']
        if not os.path.exists(current_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Generate download filename
        orchid_name = session_data['orchid_name'].replace(' ', '_')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        download_name = f"{orchid_name}_edited_{timestamp}.jpg"
        
        return send_file(current_path, 
                        as_attachment=True,
                        download_name=download_name,
                        mimetype='image/jpeg')
        
    except Exception as e:
        logger.error(f"Error downloading image: {e}")
        return jsonify({'error': str(e)}), 500

@photo_editor_bp.route('/gallery')
@login_required
def edited_gallery():
    """Gallery of edited orchid photos"""
    try:
        # Get all orchids with edited versions
        orchids = OrchidRecord.query.filter(
            OrchidRecord.enhancement_data.isnot(None)
        ).all()
        
        edited_orchids = []
        for orchid in orchids:
            try:
                import json
                enhancement_data = json.loads(orchid.enhancement_data)
                edited_versions = enhancement_data.get('edited_versions', [])
                
                if edited_versions:
                    edited_orchids.append({
                        'orchid': orchid,
                        'edited_versions': edited_versions,
                        'latest_edit': edited_versions[-1] if edited_versions else None
                    })
            except:
                continue
        
        return render_template('photo_editor/gallery.html', 
                             edited_orchids=edited_orchids)
        
    except Exception as e:
        logger.error(f"Error loading edited gallery: {e}")
        return render_template('photo_editor/gallery.html', 
                             edited_orchids=[],
                             error=str(e))

@photo_editor_bp.route('/compare/<int:orchid_id>')
@login_required
def compare_versions(orchid_id):
    """Compare original and edited versions"""
    try:
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        comparison_data = {
            'orchid': orchid,
            'original_url': orchid.image_url,
            'edited_versions': []
        }
        
        if orchid.enhancement_data:
            import json
            enhancement_data = json.loads(orchid.enhancement_data)
            comparison_data['edited_versions'] = enhancement_data.get('edited_versions', [])
        
        return render_template('photo_editor/compare.html', 
                             comparison=comparison_data)
        
    except Exception as e:
        logger.error(f"Error loading comparison: {e}")
        return render_template('photo_editor/error.html', error=str(e))

@photo_editor_bp.route('/api/cleanup-session/<session_id>', methods=['POST'])
@login_required
def api_cleanup_session(session_id):
    """Clean up editing session and temp files"""
    try:
        session_data = photo_editor.editing_sessions.get(session_id)
        if not session_data:
            return jsonify({'success': True, 'message': 'Session not found'})
        
        # Clean up temp files
        for operation in session_data['edit_history']:
            file_path = operation.get('file_path')
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        
        # Remove session from memory
        del photo_editor.editing_sessions[session_id]
        
        return jsonify({'success': True, 'message': 'Session cleaned up'})
        
    except Exception as e:
        logger.error(f"Error cleaning up session: {e}")
        return jsonify({'error': str(e)}), 500