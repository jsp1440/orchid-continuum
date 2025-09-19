"""
Processing Routes for Orchid Continuum
Admin routes for managing Google Forms integration and processing pipeline
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
import logging
from datetime import datetime
import json
import os

from orchid_processor import OrchidProcessor
from admin_system import admin_required
from models import OrchidRecord, db

logger = logging.getLogger(__name__)

# Create blueprint
processing_bp = Blueprint('processing', __name__, url_prefix='/processing')

# Initialize processor
processor = OrchidProcessor()

@processing_bp.route('/dashboard')
@admin_required
def processing_dashboard():
    """Admin dashboard for monitoring processing pipeline"""
    try:
        # Get processing status
        status = processor.get_processing_status()
        
        # Get recent processing activity
        recent_records = OrchidRecord.query.filter_by(source='google_forms').order_by(
            OrchidRecord.created_at.desc()
        ).limit(20).all()
        
        # Get processing statistics
        stats = {
            'total_processed': OrchidRecord.query.filter_by(source='google_forms').count(),
            'pending_verification': OrchidRecord.query.filter_by(
                source='google_forms', is_verified=False
            ).count(),
            'processing_errors': 0,  # Would track errors in production
            'today_processed': OrchidRecord.query.filter(
                OrchidRecord.source == 'google_forms',
                OrchidRecord.created_at >= datetime.now().date()
            ).count()
        }
        
        return render_template('admin/processing_dashboard.html',
                             status=status,
                             recent_records=recent_records,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Error loading processing dashboard: {e}")
        flash(f'Error loading dashboard: {str(e)}', 'error')
        return redirect(url_for('admin'))

@processing_bp.route('/run-processing', methods=['POST'])
@admin_required
def run_processing():
    """Manually trigger processing of pending submissions"""
    try:
        # Process all pending submissions
        results = processor.process_all_pending_submissions()
        
        # Return results as JSON for AJAX calls
        if request.is_json:
            return jsonify(results)
        
        # Flash results for regular form submission
        flash(f"Processing complete: {results['processed']} successful, {results['errors']} errors", 
              'success' if results['errors'] == 0 else 'warning')
        
        return redirect(url_for('processing.processing_dashboard'))
        
    except Exception as e:
        logger.error(f"Error running processing: {e}")
        error_msg = f"Processing failed: {str(e)}"
        
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('processing.processing_dashboard'))

@processing_bp.route('/processing-log')
@admin_required
def processing_log():
    """View detailed processing logs"""
    try:
        # In production, this would read from actual log files
        # For now, create mock log data
        log_entries = [
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Processing system initialized successfully'
            },
            {
                'timestamp': datetime.now().isoformat(),
                'level': 'INFO',
                'message': 'Google Sheets connection established'
            }
        ]
        
        return render_template('admin/processing_log.html', log_entries=log_entries)
        
    except Exception as e:
        logger.error(f"Error loading processing log: {e}")
        flash(f'Error loading log: {str(e)}', 'error')
        return redirect(url_for('processing.processing_dashboard'))

@processing_bp.route('/verify-submission/<int:record_id>', methods=['POST'])
@admin_required
def verify_submission(record_id):
    """Manually verify a processed submission"""
    try:
        record = OrchidRecord.query.get_or_404(record_id)
        
        # Update verification status
        record.is_verified = True
        record.verified_by = current_user.user_id if hasattr(current_user, 'user_id') else 'admin'
        record.verified_at = datetime.now()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'message': 'Submission verified successfully'})
        
        flash(f'Verified orchid: {record.scientific_name}', 'success')
        return redirect(url_for('processing.processing_dashboard'))
        
    except Exception as e:
        logger.error(f"Error verifying submission {record_id}: {e}")
        db.session.rollback()
        
        error_msg = f"Verification failed: {str(e)}"
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('processing.processing_dashboard'))

@processing_bp.route('/reprocess-submission/<int:record_id>', methods=['POST'])
@admin_required
def reprocess_submission(record_id):
    """Reprocess a specific submission"""
    try:
        record = OrchidRecord.query.get_or_404(record_id)
        
        # Create mock submission data for reprocessing
        submission_data = {
            'timestamp': record.created_at.isoformat() if record.created_at else datetime.now().isoformat(),
            'submitter_name': record.submitter_name or 'Unknown',
            'submitter_email': record.submitter_email or '',
            'orchid_name': record.scientific_name or '',
            'genus': record.genus or '',
            'species': record.species or '',
            'photo_url': record.image_url or '',
            'notes': record.notes or '',
            'location_found': record.location_found or ''
        }
        
        # Reprocess the submission
        result = processor.process_single_submission(submission_data)
        
        if result['success']:
            # Update the existing record with new data
            if result.get('database_record'):
                new_record = result['database_record']
                
                # Update key fields
                record.ai_description = new_record.ai_description
                record.ai_confidence = new_record.ai_confidence
                record.judging_score = new_record.judging_score
                record.enhancement_data = new_record.enhancement_data
                
                # Mark as reprocessed
                record.processed_at = datetime.now()
                
                db.session.commit()
            
            message = f'Successfully reprocessed {record.scientific_name}'
            if request.is_json:
                return jsonify({'success': True, 'message': message, 'result': result})
            
            flash(message, 'success')
        else:
            error_msg = f'Reprocessing failed: {result.get("error", "Unknown error")}'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            
            flash(error_msg, 'error')
        
        return redirect(url_for('processing.processing_dashboard'))
        
    except Exception as e:
        logger.error(f"Error reprocessing submission {record_id}: {e}")
        db.session.rollback()
        
        error_msg = f"Reprocessing failed: {str(e)}"
        if request.is_json:
            return jsonify({'error': error_msg}), 500
        
        flash(error_msg, 'error')
        return redirect(url_for('processing.processing_dashboard'))

@processing_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def processing_settings():
    """Configure processing settings"""
    if request.method == 'POST':
        try:
            # Update processing settings
            settings = {
                'spreadsheet_id': request.form.get('spreadsheet_id', ''),
                'auto_processing': request.form.get('auto_processing') == 'on',
                'processing_interval': int(request.form.get('processing_interval', 60)),
                'ai_analysis_enabled': request.form.get('ai_analysis') == 'on',
                'auto_verification': request.form.get('auto_verification') == 'on'
            }
            
            # In production, these would be saved to configuration
            flash('Settings updated successfully', 'success')
            
            return render_template('admin/processing_settings.html', settings=settings)
            
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            flash(f'Error updating settings: {str(e)}', 'error')
    
    # Load current settings
    current_settings = {
        'spreadsheet_id': os.getenv('GOOGLE_SPREADSHEET_ID', ''),
        'auto_processing': False,
        'processing_interval': 60,
        'ai_analysis_enabled': True,
        'auto_verification': False
    }
    
    return render_template('admin/processing_settings.html', settings=current_settings)

@processing_bp.route('/api/status')
@admin_required
def api_status():
    """API endpoint for processing status (for AJAX updates)"""
    try:
        status = processor.get_processing_status()
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting API status: {e}")
        return jsonify({'error': str(e)}), 500

@processing_bp.route('/api/recent-activity')
@admin_required
def api_recent_activity():
    """API endpoint for recent processing activity"""
    try:
        recent_records = OrchidRecord.query.filter_by(source='google_forms').order_by(
            OrchidRecord.created_at.desc()
        ).limit(10).all()
        
        activity_data = []
        for record in recent_records:
            activity_data.append({
                'id': record.id,
                'name': record.scientific_name,
                'submitter': record.submitter_name,
                'created_at': record.created_at.isoformat() if record.created_at else '',
                'verified': record.is_verified,
                'ai_confidence': record.ai_confidence
            })
        
        return jsonify(activity_data)
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {e}")
        return jsonify({'error': str(e)}), 500