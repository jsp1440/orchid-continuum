#!/usr/bin/env python3
"""
📊 DATA PROGRESS DASHBOARD
Real-time monitoring of data collection from all sources
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request
from enhanced_data_collection_system import get_collection_progress, get_source_analytics

# Configure logging
logger = logging.getLogger(__name__)

data_dashboard_bp = Blueprint('data_dashboard', __name__)

@data_dashboard_bp.route('/admin/data-progress')
def data_progress_dashboard():
    """Data collection progress dashboard"""
    return render_template('data_progress_dashboard.html')

@data_dashboard_bp.route('/api/collection-progress')
def collection_progress_api():
    """API endpoint for collection progress"""
    try:
        progress = get_collection_progress()
        return jsonify(progress)
    except Exception as e:
        logger.error(f"Failed to get collection progress: {e}")
        return jsonify({'error': str(e)}), 500

@data_dashboard_bp.route('/api/source-analytics')
def source_analytics_api():
    """API endpoint for source analytics"""
    try:
        analytics = get_source_analytics()
        return jsonify(analytics)
    except Exception as e:
        logger.error(f"Failed to get source analytics: {e}")
        return jsonify({'error': str(e)}), 500

@data_dashboard_bp.route('/api/collection-stats')
def collection_stats_api():
    """API endpoint for collection statistics"""
    try:
        progress = get_collection_progress()
        analytics = get_source_analytics()
        
        stats = {
            'total_sources': len(analytics),
            'active_sources': sum(1 for s in analytics.values() if s['status'] == 'active'),
            'total_records': sum(s['total_records'] for s in analytics.values()),
            'top_performers': list(analytics.items())[:3],
            'recent_activity': progress.get('progress_data', {}),
            'collection_rate': calculate_collection_rate(analytics)
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Failed to get collection stats: {e}")
        return jsonify({'error': str(e)}), 500

def calculate_collection_rate(analytics):
    """Calculate records per hour collection rate"""
    total_records = sum(s['total_records'] for s in analytics.values())
    
    # Estimate based on recent activity (simplified)
    hours_active = 24  # Assume 24 hours of activity
    rate = total_records / hours_active if hours_active > 0 else 0
    
    return round(rate, 2)