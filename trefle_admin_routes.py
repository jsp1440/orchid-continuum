"""
GBIF Ecosystem Enrichment Admin Routes
Administrative interface for managing GBIF ecosystem data batch enrichment
"""

import os
import json
import logging
from datetime import datetime
from functools import wraps
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from flask_login import login_required, current_user
from app import app, db
from models import OrchidRecord, TrefleEnrichmentTracker
from trefle_batch_enrichment_service import (
    trefle_batch_service, 
    create_enrichment_session,
    get_enrichment_session_status,
    list_enrichment_sessions,
    process_enrichment_batch,
    get_enrichment_statistics
)

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require proper Flask-Login admin authentication with role checks"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Require user to be logged in via Flask-Login
        if not current_user.is_authenticated:
            flash('Please log in to access admin features', 'error')
            return redirect(url_for('login'))
        
        # Check for admin role or session-based admin authentication fallback
        is_admin = (
            hasattr(current_user, 'is_admin') and current_user.is_admin or
            hasattr(current_user, 'role') and current_user.role == 'admin' or
            session.get('admin_authenticated')  # Fallback for existing admin sessions
        )
        
        if not is_admin:
            flash('Admin privileges required to access GBIF ecosystem enrichment features', 'error')
            return redirect(url_for('index'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/trefle-enrichment')
@admin_required
def admin_trefle_enrichment():
    """Main GBIF ecosystem enrichment admin page"""
    try:
        # Get overall statistics
        stats = get_enrichment_statistics()
        
        # Get recent sessions
        recent_sessions = list_enrichment_sessions(limit=10)
        
        # Get active session if any
        active_session = db.session.query(TrefleEnrichmentTracker)\
            .filter(TrefleEnrichmentTracker.status.in_(['pending', 'running', 'paused']))\
            .order_by(TrefleEnrichmentTracker.updated_at.desc())\
            .first()
        
        return render_template('admin/trefle_enrichment.html',
                             stats=stats,
                             recent_sessions=recent_sessions,
                             active_session=active_session.to_dict() if active_session else None)
    
    except Exception as e:
        logger.error(f"Error loading GBIF ecosystem enrichment admin: {str(e)}")
        flash(f"Error loading enrichment dashboard: {str(e)}", 'error')
        return redirect(url_for('admin'))

@app.route('/admin/trefle-enrichment/create-session', methods=['POST'])
@admin_required  
def create_trefle_enrichment_session():
    """Create a new GBIF ecosystem enrichment session"""
    try:
        session_name = request.form.get('session_name', f'Enrichment {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        priority_fcos = bool(request.form.get('priority_fcos'))
        force_update = bool(request.form.get('force_update'))
        batch_size = int(request.form.get('batch_size', 25))
        
        # Validate batch size
        if batch_size < 1 or batch_size > 100:
            flash('Batch size must be between 1 and 100', 'error')
            return redirect(url_for('admin_trefle_enrichment'))
        
        session_id = create_enrichment_session(
            session_name=session_name,
            priority_fcos_only=priority_fcos,
            force_update_existing=force_update,
            batch_size=batch_size
        )
        
        flash(f'Enrichment session "{session_name}" created successfully! Session ID: {session_id}', 'success')
        logger.info(f"✅ Created GBIF ecosystem enrichment session: {session_name} (ID: {session_id})")
        
        return redirect(url_for('admin_trefle_enrichment'))
        
    except Exception as e:
        logger.error(f"Error creating enrichment session: {str(e)}")
        flash(f"Error creating enrichment session: {str(e)}", 'error')
        return redirect(url_for('admin_trefle_enrichment'))

@app.route('/admin/trefle-enrichment/start-processing/<session_id>')
@admin_required
def start_trefle_processing(session_id):
    """Start processing a GBIF ecosystem enrichment session"""
    try:
        # Get session status
        session_status = get_enrichment_session_status(session_id)
        if not session_status:
            flash('Session not found', 'error')
            return redirect(url_for('admin_trefle_enrichment'))
        
        if session_status['status'] not in ['pending', 'paused']:
            flash(f'Cannot start processing - session status is: {session_status["status"]}', 'error')
            return redirect(url_for('admin_trefle_enrichment'))
        
        # Process first batch
        batch_size = int(request.args.get('batch_size', 25))
        result = process_enrichment_batch(session_id, max_records=batch_size)
        
        if result.get('error'):
            flash(f'Error processing batch: {result["error"]}', 'error')
        else:
            flash(f'Processed batch: {result["enriched"]} enriched, {result["failed"]} failed, {result["skipped"]} skipped', 'success')
            
            if result.get('rate_limited', 0) > 0:
                flash(f'Rate limit hit - processing paused. {result["rate_limited"]} records affected.', 'warning')
        
        logger.info(f"📊 Trefle batch processing result: {result}")
        
        return redirect(url_for('admin_trefle_enrichment'))
        
    except Exception as e:
        logger.error(f"Error starting Trefle processing: {str(e)}")
        flash(f"Error starting processing: {str(e)}", 'error')
        return redirect(url_for('admin_trefle_enrichment'))

@app.route('/admin/trefle-enrichment/api/statistics')
@admin_required
def api_trefle_statistics():
    """API endpoint for real-time Trefle enrichment statistics"""
    try:
        stats = get_enrichment_statistics()
        return jsonify({
            'success': True,
            'data': stats
        })
    except Exception as e:
        logger.error(f"Error getting Trefle statistics: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/trefle-enrichment/api/session-status/<session_id>')
@admin_required
def api_trefle_session_status(session_id):
    """API endpoint for session status"""
    try:
        status = get_enrichment_session_status(session_id)
        if not status:
            return jsonify({
                'success': False,
                'error': 'Session not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': status
        })
    except Exception as e:
        logger.error(f"Error getting session status: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/trefle-enrichment/api/process-batch/<session_id>', methods=['POST'])
@admin_required
def api_process_trefle_batch(session_id):
    """API endpoint to process a batch asynchronously"""
    try:
        max_records = int(request.json.get('max_records', 25))
        
        # Process batch with timeout protection
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Batch processing timed out")
        
        # Set timeout for batch processing (5 minutes)
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(300)  # 5 minutes timeout
        
        try:
            result = process_enrichment_batch(session_id, max_records=max_records)
        finally:
            signal.alarm(0)  # Clear timeout
        
        return jsonify({
            'success': True,
            'data': result
        })
    except TimeoutError:
        logger.error(f"Batch processing timed out for session {session_id}")
        return jsonify({
            'success': False,
            'error': 'Batch processing timed out - try smaller batch size'
        }), 408
    except Exception as e:
        logger.error(f"Error processing batch via API: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/trefle-enrichment/api/sessions')
@admin_required
def api_trefle_sessions():
    """API endpoint to list sessions"""
    try:
        limit = int(request.args.get('limit', 20))
        sessions = list_enrichment_sessions(limit=limit)
        
        return jsonify({
            'success': True,
            'data': sessions
        })
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/admin/trefle-enrichment/auto-process/<session_id>')
@admin_required
def auto_process_trefle_session(session_id):
    """Auto-process a session with multiple batches (respecting rate limits)"""
    try:
        total_processed = 0
        total_enriched = 0
        total_failed = 0
        
        while True:
            # Get current session status
            session_status = get_enrichment_session_status(session_id)
            if not session_status:
                break
            
            if session_status['status'] == 'completed':
                flash(f'Auto-processing completed! Total processed: {total_processed}, enriched: {total_enriched}', 'success')
                break
            elif session_status['status'] == 'paused':
                flash(f'Auto-processing paused due to rate limits. Processed: {total_processed} records so far.', 'warning')
                break
            elif session_status['status'] not in ['pending', 'running']:
                flash(f'Cannot continue - session status: {session_status["status"]}', 'error')
                break
            
            # Process next batch
            result = process_enrichment_batch(session_id, max_records=25)
            
            if result.get('error'):
                flash(f'Auto-processing stopped due to error: {result["error"]}', 'error')
                break
            
            total_processed += result.get('batch_size', 0)
            total_enriched += result.get('enriched', 0)
            total_failed += result.get('failed', 0)
            
            # If rate limited, stop
            if result.get('rate_limited', 0) > 0:
                flash(f'Auto-processing paused due to rate limits. Processed: {total_processed} records.', 'warning')
                break
            
            # Small delay between batches
            import time
            time.sleep(1)
        
        logger.info(f"🔄 Auto-processing session {session_id}: {total_processed} processed, {total_enriched} enriched")
        
        return redirect(url_for('admin_trefle_enrichment'))
        
    except Exception as e:
        logger.error(f"Error in auto-processing: {str(e)}")
        flash(f"Error in auto-processing: {str(e)}", 'error')
        return redirect(url_for('admin_trefle_enrichment'))

@app.route('/admin/trefle-enrichment/cancel-session/<session_id>')
@admin_required
def cancel_trefle_session(session_id):
    """Cancel a Trefle enrichment session"""
    try:
        tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
        if not tracker:
            flash('Session not found', 'error')
            return redirect(url_for('admin_trefle_enrichment'))
        
        tracker.status = 'cancelled'
        tracker.completed_at = datetime.utcnow()
        tracker.error_message = 'Cancelled by admin'
        db.session.commit()
        
        flash(f'Session "{tracker.session_name}" cancelled successfully', 'success')
        logger.info(f"❌ Cancelled Trefle enrichment session: {session_id}")
        
        return redirect(url_for('admin_trefle_enrichment'))
        
    except Exception as e:
        logger.error(f"Error cancelling session: {str(e)}")
        flash(f"Error cancelling session: {str(e)}", 'error')
        return redirect(url_for('admin_trefle_enrichment'))

@app.route('/admin/trefle-enrichment/test-connection')
@admin_required
def test_trefle_connection():
    """Test Trefle API connection"""
    try:
        from gbif_botanical_service import GBIFBotanicalService
        
        service = GBIFBotanicalService()
        if not service.enabled:
            flash('GBIF ecosystem service is ready - no API key required.', 'success')
            return redirect(url_for('admin_trefle_enrichment'))
        
        # Test with a common orchid genus
        test_result = service.search_plant_by_scientific_name('Phalaenopsis')
        
        if test_result and not test_result.get('rate_limit_exceeded'):
            flash('✅ GBIF API connection successful!', 'success')
            logger.info("✅ GBIF API connection test successful")
        elif test_result and test_result.get('rate_limit_exceeded'):
            flash(f'⚠️ GBIF API connection successful but rate limited: {test_result.get("error")}', 'warning')
        else:
            flash('❌ GBIF API connection failed', 'error')
        
        return redirect(url_for('admin_trefle_enrichment'))
        
    except Exception as e:
        logger.error(f"Error testing GBIF connection: {str(e)}")
        flash(f"Error testing GBIF connection: {str(e)}", 'error')
        return redirect(url_for('admin_trefle_enrichment'))

def register_trefle_admin_routes():
    """Register all Trefle admin routes with the Flask app"""
    logger.info("🌿 Trefle Admin Routes registered successfully")

# Auto-register routes when module is imported
register_trefle_admin_routes()