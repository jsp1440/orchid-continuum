#!/usr/bin/env python3
"""
Processing Monitor Routes
========================
Flask routes for the real-time processing pipeline monitor
- SSE streaming endpoints for live updates
- JSON API endpoints for dashboard data
- Error management and resolution endpoints
"""

import json
import uuid
import time
import queue
from flask import Blueprint, render_template, Response, jsonify, request, stream_template, stream_with_context
from processing_pipeline_monitor import pipeline_monitor, ProcessingStage, ProcessingStatus, ErrorType
import logging

logger = logging.getLogger(__name__)

# Create blueprint for processing monitor routes
processing_monitor_bp = Blueprint('processing_monitor', __name__, url_prefix='/admin/processing')

@processing_monitor_bp.route('/monitor')
def monitor_dashboard():
    """Main processing monitor dashboard"""
    return render_template('admin/processing_monitor.html')

@processing_monitor_bp.route('/stream')
def event_stream():
    """Server-Sent Events endpoint for real-time updates"""
    subscriber_id = str(uuid.uuid4())
    # Capture Last-Event-ID before generator starts
    last_event_id = request.headers.get('Last-Event-ID')
    
    def generate():
        # Subscribe to events
        event_queue = pipeline_monitor.subscribe_to_events(subscriber_id)
        
        try:
            # Send initial connection event
            yield f"data: {json.dumps({'type': 'connected', 'subscriber_id': subscriber_id})}\n\n"
            
            # Handle Last-Event-ID for replay
            if last_event_id:
                # Send missed events from database
                try:
                    since_id = int(last_event_id)
                    missed_events = pipeline_monitor.get_recent_events(limit=100)
                    for event in reversed(missed_events):  # Send in chronological order
                        if event['id'] > since_id:
                            yield f"id: {event['id']}\n"
                            yield f"data: {json.dumps(event)}\n\n"
                except (ValueError, TypeError):
                    logger.warning(f"Invalid Last-Event-ID: {last_event_id}")
            
            # Stream live events
            while True:
                try:
                    # Wait for new event with timeout for keepalive
                    event_data = event_queue.get(timeout=15)
                    
                    # Send event with ID for replay support
                    yield f"id: {event_data['id']}\n"
                    yield f"data: {json.dumps(event_data)}\n\n"
                    
                except queue.Empty:
                    # Send keepalive on timeout
                    yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': time.time()})}\n\n"
                    
        except GeneratorExit:
            # Client disconnected
            pipeline_monitor.unsubscribe_from_events(subscriber_id)
            logger.info(f"📡 Client disconnected: {subscriber_id}")
        except Exception as e:
            logger.error(f"❌ SSE stream error: {e}")
            pipeline_monitor.unsubscribe_from_events(subscriber_id)
    
    response = Response(stream_with_context(generate)(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['Connection'] = 'keep-alive'
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['X-Accel-Buffering'] = 'no'  # Prevent proxy buffering
    return response

@processing_monitor_bp.route('/summary')
def processing_summary():
    """Get current processing summary statistics"""
    try:
        summary = pipeline_monitor.get_processing_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error getting processing summary: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/recent')
def recent_events():
    """Get recent processing events"""
    try:
        limit = request.args.get('limit', 50, type=int)
        events = pipeline_monitor.get_recent_events(limit=limit)
        return jsonify(events)
    except Exception as e:
        logger.error(f"Error getting recent events: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/errors')
def recent_errors():
    """Get recent error events"""
    try:
        limit = request.args.get('limit', 20, type=int)
        resolved = request.args.get('resolved', 'false').lower() == 'true'
        errors = pipeline_monitor.get_recent_errors(limit=limit, resolved=resolved)
        return jsonify(errors)
    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/metrics')
def processing_metrics():
    """Get processing metrics for charts"""
    try:
        # Get hourly metrics for the last 24 hours
        import sqlite3
        from datetime import datetime, timedelta
        
        with sqlite3.connect(pipeline_monitor.db_path) as conn:
            cursor = conn.cursor()
            
            # Get hourly processing counts
            cursor.execute("""
                SELECT 
                    datetime(created_at, 'start of hour') as hour,
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                    AVG(latency_ms) as avg_latency
                FROM processing_events 
                WHERE created_at >= datetime('now', '-24 hours')
                GROUP BY datetime(created_at, 'start of hour')
                ORDER BY hour
            """)
            
            hourly_data = []
            for row in cursor.fetchall():
                hourly_data.append({
                    'hour': row[0],
                    'total': row[1],
                    'success': row[2],
                    'errors': row[3],
                    'avg_latency': row[4] if row[4] else 0
                })
            
            # Get stage breakdown
            cursor.execute("""
                SELECT stage, COUNT(*) as count
                FROM processing_events 
                WHERE created_at >= datetime('now', '-1 hour')
                GROUP BY stage
            """)
            
            stage_breakdown = dict(cursor.fetchall())
            
        return jsonify({
            'hourly_data': hourly_data,
            'stage_breakdown': stage_breakdown,
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting processing metrics: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/errors/<int:error_id>/resolve', methods=['POST'])
def resolve_error(error_id):
    """Mark an error as resolved"""
    try:
        data = request.get_json(silent=True) or {}
        action = data.get('action', 'acknowledge')
        
        import sqlite3
        with sqlite3.connect(pipeline_monitor.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE error_events 
                SET resolved = TRUE 
                WHERE id = ?
            """, (error_id,))
            conn.commit()
            
            if cursor.rowcount > 0:
                logger.info(f"✅ Error {error_id} resolved with action: {action}")
                return jsonify({'success': True, 'action': action})
            else:
                return jsonify({'error': 'Error not found'}), 404
                
    except Exception as e:
        logger.error(f"Error resolving error {error_id}: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/errors/<int:error_id>/retry', methods=['POST'])
def retry_failed_processing(error_id):
    """Retry processing for a failed item"""
    try:
        import sqlite3
        with sqlite3.connect(pipeline_monitor.db_path) as conn:
            cursor = conn.cursor()
            
            # Get error details
            cursor.execute("""
                SELECT orchid_id, correlation_id, stage 
                FROM error_events 
                WHERE id = ?
            """, (error_id,))
            
            error_details = cursor.fetchone()
            if not error_details:
                return jsonify({'error': 'Error not found'}), 404
            
            orchid_id, correlation_id, stage = error_details
            
            # Log retry event
            pipeline_monitor.log_event(
                orchid_id=orchid_id,
                stage=ProcessingStage.STARTED,
                status=ProcessingStatus.PENDING,
                correlation_id=f"retry_{correlation_id}",
                details={'retry_from_error': error_id, 'original_failed_stage': stage}
            )
            
            # Mark original error as resolved
            cursor.execute("""
                UPDATE error_events 
                SET resolved = TRUE 
                WHERE id = ?
            """, (error_id,))
            conn.commit()
            
        logger.info(f"🔄 Retry initiated for error {error_id}, orchid {orchid_id}")
        return jsonify({'success': True, 'message': f'Retry initiated for orchid {orchid_id}'})
        
    except Exception as e:
        logger.error(f"Error retrying processing for error {error_id}: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/test-event', methods=['POST'])
def test_event():
    """Test endpoint to generate sample events for testing"""
    try:
        # Generate a test processing event
        test_orchid_id = 999999  # Use fake ID for testing
        correlation_id = f"test_{int(time.time())}"
        
        # Simulate a processing pipeline
        stages = [
            (ProcessingStage.STARTED, ProcessingStatus.PENDING),
            (ProcessingStage.AI_ANALYSIS, ProcessingStatus.SUCCESS),
            (ProcessingStage.METADATA, ProcessingStatus.SUCCESS),
            (ProcessingStage.VALIDATION, ProcessingStatus.SUCCESS),
            (ProcessingStage.DB_WRITE, ProcessingStatus.SUCCESS),
            (ProcessingStage.COMPLETED, ProcessingStatus.SUCCESS)
        ]
        
        for stage, status in stages:
            pipeline_monitor.log_event(
                orchid_id=test_orchid_id,
                stage=stage,
                status=status,
                correlation_id=correlation_id,
                details={'test_event': True, 'stage_info': f'Test {stage.value}'},
                latency_ms=100 + (hash(stage.value) % 500)  # Random latency
            )
            time.sleep(0.1)  # Small delay between stages
        
        return jsonify({'success': True, 'message': 'Test events generated'})
        
    except Exception as e:
        logger.error(f"Error generating test events: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/analyzed-orchids')
def get_analyzed_orchids():
    """Get orchids with AI analysis results for viewing"""
    try:
        from models import OrchidRecord
        from sqlalchemy import or_
        
        # Get recently analyzed orchids with AI data
        analyzed_orchids = OrchidRecord.query.filter(
            OrchidRecord.ai_description.isnot(None)
        ).order_by(OrchidRecord.id.desc()).limit(50).all()
        
        orchid_data = []
        for orchid in analyzed_orchids:
            # Construct image URL
            image_url = None
            if orchid.google_drive_id:
                image_url = f"/api/drive-photo/{orchid.google_drive_id}"
            elif orchid.image_url:
                image_url = orchid.image_url
            
            orchid_data.append({
                'id': orchid.id,
                'display_name': orchid.display_name,
                'genus': orchid.genus,
                'species': orchid.species,
                'image_url': image_url,
                'ai_description': orchid.ai_description,
                'ai_confidence': orchid.ai_confidence,
                'ai_extracted_metadata': orchid.ai_extracted_metadata,
                'is_flowering': orchid.is_flowering,
                'flower_count': orchid.flower_count,
                'flowering_stage': orchid.flowering_stage,
                'growth_habit': orchid.growth_habit,
                'native_habitat': orchid.native_habitat,
                'bloom_time': orchid.bloom_time
            })
        
        return jsonify(orchid_data)
        
    except Exception as e:
        logger.error(f"Error getting analyzed orchids: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/orchid-analysis/<int:orchid_id>')
def get_orchid_analysis_details(orchid_id):
    """Get detailed AI analysis for a specific orchid"""
    try:
        from models import OrchidRecord
        import json
        
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Parse AI extracted metadata if it exists
        ai_metadata = None
        if orchid.ai_extracted_metadata:
            try:
                ai_metadata = json.loads(orchid.ai_extracted_metadata)
            except (json.JSONDecodeError, TypeError):
                ai_metadata = {'raw': orchid.ai_extracted_metadata}
        
        # Construct image URL
        image_url = None
        if orchid.google_drive_id:
            image_url = f"/api/drive-photo/{orchid.google_drive_id}"
        elif orchid.image_url:
            image_url = orchid.image_url
        
        analysis_data = {
            'orchid_info': {
                'id': orchid.id,
                'display_name': orchid.display_name,
                'scientific_name': orchid.scientific_name,
                'genus': orchid.genus,
                'species': orchid.species,
                'author': orchid.author,
                'image_url': image_url
            },
            'ai_analysis': {
                'description': orchid.ai_description,
                'confidence': orchid.ai_confidence,
                'extracted_metadata': ai_metadata,
                'flowering_analysis': {
                    'is_flowering': orchid.is_flowering,
                    'flowering_stage': orchid.flowering_stage,
                    'flower_count': orchid.flower_count,
                    'bloom_season_indicator': orchid.bloom_season_indicator
                }
            },
            'habitat_analysis': {
                'native_habitat': orchid.native_habitat,
                'growth_habit': orchid.growth_habit,
                'climate_preference': orchid.climate_preference,
                'growing_environment': orchid.growing_environment,
                'substrate_type': orchid.substrate_type
            },
            'geographic_data': {
                'country': orchid.country,
                'region': orchid.region,
                'decimal_latitude': orchid.decimal_latitude,
                'decimal_longitude': orchid.decimal_longitude
            }
        }
        
        return jsonify(analysis_data)
        
    except Exception as e:
        logger.error(f"Error getting orchid analysis details: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/start-ai-processing', methods=['POST'])
def start_ai_processing():
    """Start AI batch processing of orchid images with real-time monitoring"""
    try:
        from ai_batch_processor import AIBatchProcessor
        from threading import Thread
        
        # Get processing options
        data = request.get_json(silent=True) or {}
        limit = data.get('limit', None)
        
        # Initialize batch processor
        processor = AIBatchProcessor()
        
        # Start processing in background thread with pipeline monitoring
        def monitored_processing():
            # Override the processor's logging to emit events to our pipeline monitor
            original_process_orchid = processor._process_single_orchid
            
            def monitored_process_orchid(orchid):
                correlation_id = f"ai_batch_{orchid.id}_{int(time.time())}"
                
                # Log start event
                pipeline_monitor.log_event(
                    orchid_id=orchid.id,
                    stage=ProcessingStage.STARTED,
                    status=ProcessingStatus.PENDING,
                    correlation_id=correlation_id,
                    details={'orchid_name': orchid.display_name, 'genus': orchid.genus}
                )
                
                try:
                    # Log AI analysis start
                    pipeline_monitor.log_event(
                        orchid_id=orchid.id,
                        stage=ProcessingStage.AI_ANALYSIS,
                        status=ProcessingStatus.PENDING,
                        correlation_id=correlation_id
                    )
                    
                    # Call original processing
                    result = original_process_orchid(orchid)
                    
                    if result.get('success'):
                        # Log successful stages
                        pipeline_monitor.log_event(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.AI_ANALYSIS,
                            status=ProcessingStatus.SUCCESS,
                            correlation_id=correlation_id,
                            details={'ai_confidence': result.get('confidence')},
                            latency_ms=result.get('processing_time_ms')
                        )
                        
                        pipeline_monitor.log_event(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.METADATA,
                            status=ProcessingStatus.SUCCESS,
                            correlation_id=correlation_id
                        )
                        
                        pipeline_monitor.log_event(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.VALIDATION,
                            status=ProcessingStatus.SUCCESS,
                            correlation_id=correlation_id
                        )
                        
                        pipeline_monitor.log_event(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.DB_WRITE,
                            status=ProcessingStatus.SUCCESS,
                            correlation_id=correlation_id
                        )
                        
                        pipeline_monitor.log_event(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.COMPLETED,
                            status=ProcessingStatus.SUCCESS,
                            correlation_id=correlation_id
                        )
                    else:
                        # Log error
                        error_msg = result.get('error', 'Unknown AI processing error')
                        pipeline_monitor.log_error(
                            orchid_id=orchid.id,
                            stage=ProcessingStage.AI_ANALYSIS,
                            error_message=error_msg,
                            correlation_id=correlation_id
                        )
                    
                    return result
                    
                except Exception as e:
                    # Log processing error
                    pipeline_monitor.log_error(
                        orchid_id=orchid.id,
                        stage=ProcessingStage.AI_ANALYSIS,
                        error_message=str(e),
                        correlation_id=correlation_id,
                        stack=str(e.__traceback__) if hasattr(e, '__traceback__') else None
                    )
                    raise
            
            # Monkey patch the processor to use our monitored version
            processor._process_single_orchid = monitored_process_orchid
            
            # Start the actual processing
            processor.start_batch_analysis(limit=limit)
        
        # Start processing thread
        processing_thread = Thread(target=monitored_processing, daemon=True)
        processing_thread.start()
        
        logger.info(f"🚀 Started AI batch processing with real-time monitoring (limit: {limit})")
        return jsonify({
            'success': True, 
            'message': f'AI batch processing started with real-time monitoring',
            'limit': limit
        })
        
    except Exception as e:
        logger.error(f"Error starting AI processing: {e}")
        return jsonify({'error': str(e)}), 500

@processing_monitor_bp.route('/test-error', methods=['POST'])
def test_error():
    """Test endpoint to generate sample error for testing"""
    try:
        test_orchid_id = 999998  # Use fake ID for testing
        
        pipeline_monitor.log_error(
            orchid_id=test_orchid_id,
            stage=ProcessingStage.AI_ANALYSIS,
            error_message="Connection timeout while calling OpenAI API",
            correlation_id=f"test_error_{int(time.time())}",
            stack="Traceback: ... (test error stack trace)",
            error_type=ErrorType.NETWORK_TIMEOUT
        )
        
        return jsonify({'success': True, 'message': 'Test error generated'})
        
    except Exception as e:
        logger.error(f"Error generating test error: {e}")
        return jsonify({'error': str(e)}), 500

# Helper function to register the blueprint
def register_processing_monitor_routes(app):
    """Register processing monitor routes with Flask app"""
    app.register_blueprint(processing_monitor_bp)
    logger.info("🔍 Processing Monitor routes registered successfully")