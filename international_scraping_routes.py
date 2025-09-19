#!/usr/bin/env python3
"""
International Orchid Scraping Management Routes
Admin interface for managing international data collection
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import logging
import json
from datetime import datetime
from typing import Dict, Any
import threading

from source_adapter_system import IngestionOrchestrator
from models import ScrapingLog, OrchidRecord, db

logger = logging.getLogger(__name__)

# Create blueprint
international_scraping_bp = Blueprint('international_scraping', __name__, url_prefix='/admin/international')

# Global orchestrator instance
orchestrator = IngestionOrchestrator()
active_collections = {}  # Track active collection processes

@international_scraping_bp.route('/')
def dashboard():
    """International scraping dashboard"""
    try:
        # Get recent scraping logs
        recent_logs = ScrapingLog.query.filter(
            ScrapingLog.source.like('international_%')
        ).order_by(ScrapingLog.created_at.desc()).limit(20).all()
        
        # Get statistics
        stats = get_collection_statistics()
        
        # Get available sources
        available_sources = list(orchestrator.adapters.keys())
        
        return render_template('admin/international_scraping_dashboard.html',
                             recent_logs=recent_logs,
                             stats=stats,
                             available_sources=available_sources,
                             active_collections=active_collections)
    
    except Exception as e:
        logger.error(f"Error loading international scraping dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('admin_system.admin_dashboard'))

@international_scraping_bp.route('/start-collection', methods=['POST'])
def start_collection():
    """Start international collection process"""
    try:
        data = request.get_json()
        source_ids = data.get('sources', [])
        max_records = int(data.get('max_records', 100))
        
        if not source_ids:
            return jsonify({'success': False, 'error': 'No sources selected'})
        
        # Validate sources
        invalid_sources = [s for s in source_ids if s not in orchestrator.adapters]
        if invalid_sources:
            return jsonify({
                'success': False, 
                'error': f'Invalid sources: {", ".join(invalid_sources)}'
            })
        
        # Create collection ID for tracking
        collection_id = f"collection_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Start collection in background thread
        collection_thread = threading.Thread(
            target=run_collection_background,
            args=(collection_id, source_ids, max_records)
        )
        collection_thread.daemon = True
        collection_thread.start()
        
        active_collections[collection_id] = {
            'sources': source_ids,
            'max_records': max_records,
            'status': 'running',
            'started_at': datetime.now(),
            'progress': {}
        }
        
        logger.info(f"🚀 Started international collection {collection_id} for sources: {source_ids}")
        
        return jsonify({
            'success': True,
            'collection_id': collection_id,
            'message': f'Collection started for {len(source_ids)} sources'
        })
        
    except Exception as e:
        logger.error(f"Error starting collection: {e}")
        return jsonify({'success': False, 'error': str(e)})

@international_scraping_bp.route('/collection-status/<collection_id>')
def get_collection_status(collection_id):
    """Get status of a running collection"""
    try:
        if collection_id not in active_collections:
            return jsonify({'success': False, 'error': 'Collection not found'})
        
        collection = active_collections[collection_id]
        return jsonify({
            'success': True,
            'collection': collection
        })
        
    except Exception as e:
        logger.error(f"Error getting collection status: {e}")
        return jsonify({'success': False, 'error': str(e)})

@international_scraping_bp.route('/test-source/<source_id>')
def test_source(source_id):
    """Test connection to a specific source"""
    try:
        if source_id not in orchestrator.adapters:
            return jsonify({'success': False, 'error': 'Invalid source'})
        
        adapter = orchestrator.adapters[source_id]
        source_info = adapter.get_source_info()
        
        # Test discovery
        taxa = adapter.discover_taxa(limit=5)
        
        test_result = {
            'source_info': {
                'name': source_info.source_name,
                'url': source_info.url,
                'country': source_info.country
            },
            'taxa_discovered': len(taxa),
            'sample_taxa': taxa[:3] if taxa else [],
            'status': 'success' if taxa else 'warning'
        }
        
        logger.info(f"✅ Source test {source_id}: {len(taxa)} taxa discovered")
        
        return jsonify({
            'success': True,
            'test_result': test_result
        })
        
    except Exception as e:
        logger.error(f"Error testing source {source_id}: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'test_result': {'status': 'error'}
        })

@international_scraping_bp.route('/source-info')
def get_source_info():
    """Get information about all available sources"""
    try:
        sources_info = []
        
        for source_id, adapter in orchestrator.adapters.items():
            source_meta = adapter.get_source_info()
            sources_info.append({
                'id': source_id,
                'name': source_meta.source_name,
                'url': source_meta.url,
                'country': source_meta.country,
                'license': source_meta.license,
                'rights_holder': source_meta.rights_holder
            })
        
        return jsonify({
            'success': True,
            'sources': sources_info
        })
        
    except Exception as e:
        logger.error(f"Error getting source info: {e}")
        return jsonify({'success': False, 'error': str(e)})

@international_scraping_bp.route('/collection-logs')
def get_collection_logs():
    """Get recent collection logs"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        logs_query = ScrapingLog.query.filter(
            ScrapingLog.source.like('international_%')
        ).order_by(ScrapingLog.created_at.desc())
        
        logs = logs_query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        logs_data = []
        for log in logs.items:
            logs_data.append({
                'id': log.id,
                'source': log.source,
                'url': log.url,
                'status': log.status,
                'items_found': log.items_found,
                'items_processed': log.items_processed,
                'error_message': log.error_message,
                'created_at': log.created_at.isoformat() if log.created_at else None
            })
        
        return jsonify({
            'success': True,
            'logs': logs_data,
            'pagination': {
                'page': logs.page,
                'pages': logs.pages,
                'per_page': logs.per_page,
                'total': logs.total,
                'has_next': logs.has_next,
                'has_prev': logs.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting collection logs: {e}")
        return jsonify({'success': False, 'error': str(e)})

def run_collection_background(collection_id: str, source_ids: list, max_records: int):
    """Run collection process in background"""
    try:
        logger.info(f"🔄 Background collection {collection_id} starting...")
        
        # Update status
        active_collections[collection_id]['status'] = 'running'
        
        # Run the collection
        results = orchestrator.run_collection(source_ids, max_records_per_source=max_records)
        
        # Update final status
        active_collections[collection_id]['status'] = 'completed'
        active_collections[collection_id]['results'] = results
        active_collections[collection_id]['completed_at'] = datetime.now()
        
        logger.info(f"✅ Background collection {collection_id} completed: {results}")
        
    except Exception as e:
        logger.error(f"❌ Background collection {collection_id} failed: {e}")
        active_collections[collection_id]['status'] = 'error'
        active_collections[collection_id]['error'] = str(e)

def get_collection_statistics() -> Dict[str, Any]:
    """Get statistics about international collections"""
    try:
        # Count records by international source
        international_records = db.session.query(
            OrchidRecord.ingestion_source,
            db.func.count(OrchidRecord.id).label('count')
        ).filter(
            OrchidRecord.ingestion_source.like('international_%')
        ).group_by(OrchidRecord.ingestion_source).all()
        
        source_counts = {record[0]: record[1] for record in international_records}
        
        # Get recent activity
        recent_logs = ScrapingLog.query.filter(
            ScrapingLog.source.like('international_%')
        ).filter(
            ScrapingLog.created_at >= datetime.now().replace(day=1)  # This month
        ).count()
        
        # Total international records
        total_international = sum(source_counts.values())
        
        return {
            'total_international_records': total_international,
            'source_breakdown': source_counts,
            'recent_collections': recent_logs,
            'active_collections': len([c for c in active_collections.values() if c['status'] == 'running'])
        }
        
    except Exception as e:
        logger.error(f"Error getting collection statistics: {e}")
        return {
            'total_international_records': 0,
            'source_breakdown': {},
            'recent_collections': 0,
            'active_collections': 0
        }

# API endpoints for AJAX requests
@international_scraping_bp.route('/api/dashboard-data')
def api_dashboard_data():
    """Get dashboard data via API"""
    try:
        stats = get_collection_statistics()
        available_sources = list(orchestrator.adapters.keys())
        
        return jsonify({
            'success': True,
            'stats': stats,
            'available_sources': available_sources,
            'active_collections': len([c for c in active_collections.values() if c['status'] == 'running'])
        })
        
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        return jsonify({'success': False, 'error': str(e)})

@international_scraping_bp.route('/stop-collection/<collection_id>', methods=['POST'])
def stop_collection(collection_id):
    """Stop a running collection (placeholder - actual implementation would need thread management)"""
    try:
        if collection_id not in active_collections:
            return jsonify({'success': False, 'error': 'Collection not found'})
        
        # For now, just mark as stopped (proper implementation would need thread interruption)
        active_collections[collection_id]['status'] = 'stopped'
        active_collections[collection_id]['stopped_at'] = datetime.now()
        
        return jsonify({
            'success': True,
            'message': f'Collection {collection_id} stopped'
        })
        
    except Exception as e:
        logger.error(f"Error stopping collection: {e}")
        return jsonify({'success': False, 'error': str(e)})