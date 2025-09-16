#!/usr/bin/env python3
"""
🌸 Breeder Pro+ Pipeline Web Interface
Admin routes for managing and monitoring Breeder Pro+ orchestrator pipelines
"""

import os
import json
import logging
import threading
import traceback
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from app import app, db
from models import PipelineRun, PipelineStep, PipelineTemplate, PipelineSchedule, User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create blueprint for Breeder Pro+ routes
breeder_pro_bp = Blueprint('breeder_pro', __name__, url_prefix='/admin/breeder-pro')

# Import orchestrator with error handling
try:
    from breeder_pro_orchestrator import BreederProOrchestrator, PipelineProgress
    ORCHESTRATOR_AVAILABLE = True
    logger.info("✅ Breeder Pro+ Orchestrator imported successfully")
except ImportError as e:
    ORCHESTRATOR_AVAILABLE = False
    logger.warning(f"⚠️ Breeder Pro+ Orchestrator not available: {e}")
    
    # Create mock classes for when orchestrator is not available
    class BreederProOrchestrator:
        def __init__(self, config=None):
            self.config = config or {}
        
        def run_pipeline(self, *args, **kwargs):
            raise RuntimeError("Orchestrator not available - missing dependencies")
    
    class PipelineProgress:
        def __init__(self):
            self.pipeline_id = "mock-pipeline"

# Global registry for active pipeline threads
active_pipelines = {}

def check_admin_access():
    """Check if current user has admin access"""
    if not current_user.is_authenticated:
        return False
    return getattr(current_user, 'is_admin', False)

@breeder_pro_bp.route('/')
@login_required
def dashboard():
    """Main Breeder Pro+ dashboard"""
    if not check_admin_access():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    # Get recent pipeline runs
    recent_runs = PipelineRun.get_recent_runs(limit=10)
    active_runs = PipelineRun.get_active_runs()
    templates = PipelineTemplate.get_active_templates()
    
    # Pipeline statistics
    total_runs = PipelineRun.query.count()
    successful_runs = PipelineRun.query.filter_by(status='completed').count()
    failed_runs = PipelineRun.query.filter_by(status='failed').count()
    
    stats = {
        'total_runs': total_runs,
        'successful_runs': successful_runs,
        'failed_runs': failed_runs,
        'success_rate': (successful_runs / total_runs * 100) if total_runs > 0 else 0,
        'active_pipelines': len(active_runs),
        'orchestrator_available': ORCHESTRATOR_AVAILABLE
    }
    
    return render_template('admin/breeder_pro/dashboard.html',
                         recent_runs=recent_runs,
                         active_runs=active_runs,
                         templates=templates,
                         stats=stats)

@breeder_pro_bp.route('/start-pipeline', methods=['POST'])
@login_required
def start_pipeline():
    """Start a new pipeline run"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    if not ORCHESTRATOR_AVAILABLE:
        return jsonify({'error': 'Orchestrator not available - missing dependencies'}), 503
    
    try:
        # Get request parameters
        data = request.get_json() or {}
        pipeline_name = data.get('name', f'Pipeline Run {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        template_id = data.get('template_id')
        custom_config = data.get('config', {})
        notification_emails = data.get('notification_emails', [])
        
        # Load template if specified
        config = {}
        if template_id:
            template = PipelineTemplate.query.get(template_id)
            if template:
                config = template.config.copy()
                template.usage_count += 1
                db.session.commit()
        
        # Merge custom config
        config.update(custom_config)
        
        # Create pipeline run record
        pipeline_run = PipelineRun(
            name=pipeline_name,
            started_by_user_id=current_user.id,
            config=config,
            status='queued',
            notification_emails=notification_emails,
            total_operations=estimate_total_operations(config)
        )
        db.session.add(pipeline_run)
        db.session.commit()
        
        # Create pipeline steps
        steps = get_pipeline_steps(config)
        for i, step_name in enumerate(steps):
            step = PipelineStep(
                pipeline_run_id=pipeline_run.id,
                step_name=step_name,
                step_order=i + 1,
                status='pending'
            )
            db.session.add(step)
        db.session.commit()
        
        # Start pipeline in background thread
        thread = threading.Thread(
            target=run_pipeline_async,
            args=(pipeline_run.pipeline_id, config),
            daemon=True
        )
        thread.start()
        
        # Track active pipeline
        active_pipelines[pipeline_run.pipeline_id] = {
            'thread': thread,
            'started_at': datetime.utcnow(),
            'pipeline_run': pipeline_run
        }
        
        logger.info(f"🚀 Started pipeline: {pipeline_name} (ID: {pipeline_run.pipeline_id})")
        
        return jsonify({
            'success': True,
            'pipeline_id': pipeline_run.pipeline_id,
            'pipeline_run_id': pipeline_run.id,
            'message': f'Pipeline "{pipeline_name}" started successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error starting pipeline: {e}")
        return jsonify({'error': f'Failed to start pipeline: {str(e)}'}), 500

@breeder_pro_bp.route('/pipeline/<pipeline_id>/status')
@login_required
def pipeline_status(pipeline_id):
    """Get pipeline status and progress"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        pipeline_run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
        if not pipeline_run:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        # Get pipeline steps
        steps = PipelineStep.query.filter_by(pipeline_run_id=pipeline_run.id)\
                                  .order_by(PipelineStep.step_order).all()
        
        # Check if thread is still active
        is_thread_active = pipeline_id in active_pipelines
        
        response = {
            'pipeline': pipeline_run.to_dict(),
            'steps': [step.to_dict() for step in steps],
            'is_active': is_thread_active,
            'thread_info': None
        }
        
        if is_thread_active:
            thread_info = active_pipelines[pipeline_id]
            response['thread_info'] = {
                'started_at': thread_info['started_at'].isoformat(),
                'is_alive': thread_info['thread'].is_alive()
            }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline status: {e}")
        return jsonify({'error': str(e)}), 500

@breeder_pro_bp.route('/pipeline/<pipeline_id>/cancel', methods=['POST'])
@login_required
def cancel_pipeline(pipeline_id):
    """Cancel a running pipeline"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        pipeline_run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
        if not pipeline_run:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        # Update pipeline status
        pipeline_run.status = 'cancelled'
        pipeline_run.completed_at = datetime.utcnow()
        pipeline_run.duration_seconds = int((pipeline_run.completed_at - pipeline_run.started_at).total_seconds())
        db.session.commit()
        
        # Remove from active pipelines (thread will naturally terminate)
        if pipeline_id in active_pipelines:
            del active_pipelines[pipeline_id]
        
        logger.info(f"🛑 Cancelled pipeline: {pipeline_run.name} (ID: {pipeline_id})")
        
        return jsonify({
            'success': True,
            'message': f'Pipeline "{pipeline_run.name}" cancelled successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ Error cancelling pipeline: {e}")
        return jsonify({'error': str(e)}), 500

@breeder_pro_bp.route('/pipeline/<int:run_id>/details')
@login_required
def pipeline_details(run_id):
    """Get detailed pipeline information"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        pipeline_run = PipelineRun.query.get(run_id)
        if not pipeline_run:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        # Get all steps with details
        steps = PipelineStep.query.filter_by(pipeline_run_id=run_id)\
                                  .order_by(PipelineStep.step_order).all()
        
        return render_template('admin/breeder_pro/pipeline_details.html',
                             pipeline=pipeline_run,
                             steps=steps)
        
    except Exception as e:
        logger.error(f"❌ Error getting pipeline details: {e}")
        flash(f'Error loading pipeline details: {str(e)}', 'error')
        return redirect(url_for('breeder_pro.dashboard'))

@breeder_pro_bp.route('/pipeline/<int:run_id>/download/<file_type>')
@login_required
def download_pipeline_file(run_id, file_type):
    """Download pipeline output files"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        pipeline_run = PipelineRun.query.get(run_id)
        if not pipeline_run:
            return jsonify({'error': 'Pipeline not found'}), 404
        
        file_path = None
        if file_type == 'log' and pipeline_run.log_file_path:
            file_path = pipeline_run.log_file_path
        elif file_type == 'report' and pipeline_run.report_files:
            # Get first report file
            report_files = pipeline_run.report_files
            if isinstance(report_files, list) and len(report_files) > 0:
                file_path = report_files[0]
        elif file_type == 'data' and pipeline_run.data_files:
            # Get first data file
            data_files = pipeline_run.data_files
            if isinstance(data_files, list) and len(data_files) > 0:
                file_path = data_files[0]
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({'error': 'File not found'}), 404
        
        return send_file(file_path, as_attachment=True)
        
    except Exception as e:
        logger.error(f"❌ Error downloading file: {e}")
        return jsonify({'error': str(e)}), 500

@breeder_pro_bp.route('/templates')
@login_required
def templates():
    """Manage pipeline templates"""
    if not check_admin_access():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    templates = PipelineTemplate.get_active_templates()
    return render_template('admin/breeder_pro/templates.html', templates=templates)

@breeder_pro_bp.route('/templates/create', methods=['GET', 'POST'])
@login_required
def create_template():
    """Create a new pipeline template"""
    if not check_admin_access():
        flash('Admin access required.', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            data = request.get_json() or request.form.to_dict()
            
            template = PipelineTemplate(
                name=data['name'],
                description=data.get('description', ''),
                config=json.loads(data['config']) if isinstance(data['config'], str) else data['config'],
                steps=json.loads(data['steps']) if isinstance(data['steps'], str) else data['steps'],
                created_by_user_id=current_user.id,
                is_default=data.get('is_default', False)
            )
            
            db.session.add(template)
            db.session.commit()
            
            logger.info(f"✅ Created template: {template.name}")
            
            if request.is_json:
                return jsonify({'success': True, 'template_id': template.id})
            else:
                flash(f'Template "{template.name}" created successfully', 'success')
                return redirect(url_for('breeder_pro.templates'))
                
        except Exception as e:
            logger.error(f"❌ Error creating template: {e}")
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            else:
                flash(f'Error creating template: {str(e)}', 'error')
    
    return render_template('admin/breeder_pro/create_template.html')

@breeder_pro_bp.route('/api/active-pipelines')
@login_required
def api_active_pipelines():
    """API endpoint for active pipelines (for real-time updates)"""
    if not check_admin_access():
        return jsonify({'error': 'Admin access required'}), 403
    
    try:
        active_runs = PipelineRun.get_active_runs()
        return jsonify({
            'active_pipelines': [run.to_dict() for run in active_runs],
            'count': len(active_runs)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def run_pipeline_async(pipeline_id, config):
    """Run pipeline in background thread"""
    pipeline_run = None
    try:
        with app.app_context():
            # Get pipeline run
            pipeline_run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
            if not pipeline_run:
                logger.error(f"❌ Pipeline run not found: {pipeline_id}")
                return
            
            # Update status
            pipeline_run.status = 'running'
            pipeline_run.stage = 'initializing'
            db.session.commit()
            
            # Initialize orchestrator
            orchestrator = BreederProOrchestrator(config=config)
            
            # Create progress callback
            def progress_callback(stage, progress, success_count=None, error_count=None, step_data=None):
                try:
                    with app.app_context():
                        # Update pipeline run
                        run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
                        if run:
                            run.update_progress(stage, progress, success_count, error_count)
                            
                            # Update current step
                            current_step = PipelineStep.query.filter_by(
                                pipeline_run_id=run.id,
                                step_name=stage,
                                status='running'
                            ).first()
                            
                            if not current_step:
                                # Find pending step for this stage
                                current_step = PipelineStep.query.filter_by(
                                    pipeline_run_id=run.id,
                                    step_name=stage,
                                    status='pending'
                                ).first()
                                if current_step:
                                    current_step.start_step()
                            
                            if current_step:
                                current_step.update_progress(
                                    progress,
                                    items_processed=success_count + error_count if success_count and error_count else None,
                                    items_successful=success_count,
                                    items_failed=error_count
                                )
                                if step_data:
                                    current_step.step_data = step_data
                                    db.session.commit()
                                    
                except Exception as e:
                    logger.error(f"❌ Error in progress callback: {e}")
            
            # Run the pipeline
            result = orchestrator.run_pipeline(
                genera=['Cattleya', 'Dendrobium'],  # Default genera
                progress_callback=progress_callback,
                email_results=bool(pipeline_run.notification_emails)
            )
            
            # Update final status
            with app.app_context():
                run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
                if run:
                    if result.get('success', False):
                        run.mark_completed(success=True)
                        run.report_files = result.get('report_files', [])
                        run.data_files = result.get('data_files', [])
                        run.log_file_path = result.get('log_file')
                        run.email_sent = result.get('email_sent', False)
                    else:
                        run.mark_completed(success=False, error_message=result.get('error_message'))
                    
                    db.session.commit()
                    
                    # Complete all remaining steps
                    pending_steps = PipelineStep.query.filter_by(
                        pipeline_run_id=run.id,
                        status='pending'
                    ).all()
                    for step in pending_steps:
                        step.complete_step(success=result.get('success', False))
            
            logger.info(f"✅ Pipeline completed: {pipeline_id}")
            
    except Exception as e:
        logger.error(f"❌ Pipeline execution error: {e}")
        logger.error(traceback.format_exc())
        
        # Update pipeline with error
        try:
            with app.app_context():
                if pipeline_run:
                    run = PipelineRun.query.filter_by(pipeline_id=pipeline_id).first()
                    if run:
                        run.mark_completed(success=False, error_message=str(e))
                        run.error_details = {'traceback': traceback.format_exc()}
                        db.session.commit()
        except Exception as db_error:
            logger.error(f"❌ Error updating pipeline status: {db_error}")
    
    finally:
        # Clean up active pipeline tracking
        if pipeline_id in active_pipelines:
            del active_pipelines[pipeline_id]

def estimate_total_operations(config):
    """Estimate total operations for progress tracking"""
    # Simple estimation based on configuration
    base_operations = 100  # Base operations for setup
    
    # Add operations for each genus
    genera = config.get('genera', ['Cattleya'])
    genus_operations = len(genera) * 50
    
    # Add operations for analysis
    analysis_operations = 200 if config.get('detailed_analysis', True) else 100
    
    # Add operations for reporting
    report_operations = 50
    
    return base_operations + genus_operations + analysis_operations + report_operations

def get_pipeline_steps(config):
    """Get list of pipeline steps based on configuration"""
    steps = ['initializing', 'scraping']
    
    if config.get('upload_to_drive', True):
        steps.append('upload')
    
    if config.get('detailed_analysis', True):
        steps.append('analysis')
    
    steps.extend(['reporting', 'email'])
    
    return steps

# Register the blueprint
app.register_blueprint(breeder_pro_bp)
logger.info("🌸 Breeder Pro+ admin routes registered successfully")