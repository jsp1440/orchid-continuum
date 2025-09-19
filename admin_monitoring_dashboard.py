#!/usr/bin/env python3
"""
Real-Time Admin Monitoring Dashboard
Live monitoring window for widget performance and member feedback
"""

import os
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from flask import Blueprint, render_template, request, jsonify, session
import requests
from sqlalchemy import func, desc, and_

from app import app, db
from models import (OrchidRecord, MemberFeedback, PhotoFlag, WidgetStatus, 
                   AnalyticsEntry, User)

logger = logging.getLogger(__name__)

# Create blueprint
monitoring_bp = Blueprint('monitoring', __name__)

class AdminMonitoringSystem:
    """Real-time monitoring system for admin dashboard"""
    
    def __init__(self):
        self.widget_endpoints = {
            'featured': '/widget/featured',
            'gallery': '/widget/gallery', 
            'discovery': '/widget/discovery',
            'orchid_of_day': '/widget/orchid-of-the-day'
        }
        
        self.api_endpoints = {
            'recent_orchids': '/api/recent-orchids',
            'drive_photo': '/api/drive-photo/185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I',
            'featured_orchid': '/api/featured-orchid',
            'coordinates': '/mapping/api/coordinates'
        }

    def perform_comprehensive_widget_diagnostic(self) -> Dict[str, Any]:
        """Perform comprehensive diagnostic of all widgets and APIs"""
        try:
            diagnostic_results = {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'healthy',
                'widgets': {},
                'apis': {},
                'database': {},
                'images': {},
                'issues': []
            }
            
            # Test all widgets
            for widget_name, endpoint in self.widget_endpoints.items():
                widget_result = self._test_widget_endpoint(widget_name, endpoint)
                diagnostic_results['widgets'][widget_name] = widget_result
                
                if widget_result['status'] != 'healthy':
                    diagnostic_results['overall_status'] = 'degraded'
                    diagnostic_results['issues'].append(f"Widget {widget_name}: {widget_result['error']}")
            
            # Test core APIs
            for api_name, endpoint in self.api_endpoints.items():
                api_result = self._test_api_endpoint(api_name, endpoint)
                diagnostic_results['apis'][api_name] = api_result
                
                if api_result['status'] != 'healthy':
                    diagnostic_results['overall_status'] = 'degraded'
                    diagnostic_results['issues'].append(f"API {api_name}: {api_result['error']}")
            
            # Database health check
            db_result = self._test_database_health()
            diagnostic_results['database'] = db_result
            
            if db_result['status'] != 'healthy':
                diagnostic_results['overall_status'] = 'critical'
                diagnostic_results['issues'].append(f"Database: {db_result['error']}")
            
            # Image system health
            image_result = self._test_image_system()
            diagnostic_results['images'] = image_result
            
            # Update widget status records
            self._update_widget_status_records(diagnostic_results)
            
            return diagnostic_results
            
        except Exception as e:
            logger.error(f"Error in comprehensive diagnostic: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'overall_status': 'critical',
                'error': str(e),
                'widgets': {},
                'apis': {},
                'database': {'status': 'unknown'},
                'images': {'status': 'unknown'},
                'issues': [f"Diagnostic system error: {str(e)}"]
            }

    def _test_widget_endpoint(self, widget_name: str, endpoint: str) -> Dict[str, Any]:
        """Test individual widget endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f'http://localhost:5000{endpoint}', timeout=10)
            response_time = int((time.time() - start_time) * 1000)  # milliseconds
            
            if response.status_code == 200:
                content_length = len(response.content)
                return {
                    'status': 'healthy',
                    'response_time_ms': response_time,
                    'content_length': content_length,
                    'last_checked': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'degraded',
                    'response_time_ms': response_time,
                    'error': f'HTTP {response.status_code}',
                    'last_checked': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'down',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    def _test_api_endpoint(self, api_name: str, endpoint: str) -> Dict[str, Any]:
        """Test individual API endpoint"""
        try:
            start_time = time.time()
            response = requests.get(f'http://localhost:5000{endpoint}', timeout=10)
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                # Try to parse JSON for API endpoints
                try:
                    data = response.json()
                    record_count = len(data) if isinstance(data, list) else 1
                    return {
                        'status': 'healthy',
                        'response_time_ms': response_time,
                        'record_count': record_count,
                        'last_checked': datetime.now().isoformat()
                    }
                except json.JSONDecodeError:
                    # Not JSON, probably binary (like images)
                    return {
                        'status': 'healthy',
                        'response_time_ms': response_time,
                        'content_size': len(response.content),
                        'last_checked': datetime.now().isoformat()
                    }
            else:
                return {
                    'status': 'degraded',
                    'response_time_ms': response_time,
                    'error': f'HTTP {response.status_code}',
                    'last_checked': datetime.now().isoformat()
                }
                
        except Exception as e:
            return {
                'status': 'down',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    def _test_database_health(self) -> Dict[str, Any]:
        """Test database connectivity and performance"""
        try:
            start_time = time.time()
            
            # Test basic query
            orchid_count = OrchidRecord.query.count()
            user_count = User.query.count() if hasattr(User, 'query') else 0
            feedback_count = MemberFeedback.query.count()
            flag_count = PhotoFlag.query.count()
            
            # Test write capability
            from sqlalchemy import text
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            
            query_time = int((time.time() - start_time) * 1000)
            
            return {
                'status': 'healthy',
                'response_time_ms': query_time,
                'orchid_count': orchid_count,
                'user_count': user_count,
                'feedback_count': feedback_count,
                'flag_count': flag_count,
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    def _test_image_system(self) -> Dict[str, Any]:
        """Test image loading system with Google Drive and external images"""
        try:
            # Test Google Drive images (production-ready)
            google_drive_test = self._test_api_endpoint('drive_test', '/api/drive-photo/185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I')
            
            # Get recent orchids to test variety of image sources
            recent_response = requests.get('http://localhost:5000/api/recent-orchids', timeout=10)
            if recent_response.status_code != 200:
                return {
                    'status': 'degraded',
                    'error': 'Cannot access recent orchids API',
                    'google_drive_status': google_drive_test['status']
                }
            
            recent_orchids = recent_response.json()
            google_drive_orchids = [o for o in recent_orchids if o.get('google_drive_id')]
            external_orchids = [o for o in recent_orchids if not o.get('google_drive_id') and o.get('photo_url')]
            
            # Test sample of each type
            google_drive_working = 0
            google_drive_tested = min(3, len(google_drive_orchids))
            
            for orchid in google_drive_orchids[:google_drive_tested]:
                try:
                    img_response = requests.get(f"http://localhost:5000/api/drive-photo/{orchid['google_drive_id']}", timeout=5)
                    if img_response.status_code == 200 and len(img_response.content) > 1000:
                        google_drive_working += 1
                except:
                    pass
            
            # Test external images (these may fail due to security - that's expected)
            external_working = 0
            external_tested = min(2, len(external_orchids))
            
            for orchid in external_orchids[:external_tested]:
                try:
                    from urllib.parse import quote_plus
                    proxy_url = f"http://localhost:5000/api/proxy-image?url={quote_plus(orchid['photo_url'])}"
                    img_response = requests.get(proxy_url, timeout=5)
                    if img_response.status_code == 200 and len(img_response.content) > 1000:
                        external_working += 1
                except:
                    pass
            
            google_drive_rate = (google_drive_working / google_drive_tested * 100) if google_drive_tested > 0 else 0
            external_rate = (external_working / external_tested * 100) if external_tested > 0 else 0
            
            # Status is healthy if Google Drive images work (production images)
            if google_drive_rate >= 80:
                status = 'healthy'
            elif google_drive_rate >= 50:
                status = 'degraded'
            else:
                status = 'critical'
            
            return {
                'status': status,
                'google_drive_success_rate': google_drive_rate,
                'google_drive_working': google_drive_working,
                'google_drive_tested': google_drive_tested,
                'external_success_rate': external_rate,
                'external_working': external_working,
                'external_tested': external_tested,
                'total_orchids_with_images': len(google_drive_orchids) + len(external_orchids),
                'production_ready_images': len(google_drive_orchids),
                'last_checked': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'status': 'critical',
                'error': str(e),
                'last_checked': datetime.now().isoformat()
            }

    def _update_widget_status_records(self, diagnostic_results: Dict[str, Any]):
        """Update database widget status records"""
        try:
            for widget_name, widget_data in diagnostic_results.get('widgets', {}).items():
                # Find or create widget status record
                status_record = WidgetStatus.query.filter_by(widget_name=widget_name).first()
                if not status_record:
                    status_record = WidgetStatus(widget_name=widget_name)
                    db.session.add(status_record)
                
                # Update status
                status_record.status = widget_data.get('status', 'unknown')
                status_record.response_time_ms = widget_data.get('response_time_ms')
                status_record.last_error = widget_data.get('error')
                status_record.last_checked = datetime.now()
                
                # Update success rate (simplified)
                if widget_data.get('status') == 'healthy':
                    status_record.success_rate = min(100.0, status_record.success_rate + 1)
                else:
                    status_record.error_count += 1
                    status_record.success_rate = max(0.0, status_record.success_rate - 5)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error updating widget status records: {e}")
            db.session.rollback()

    def get_live_dashboard_data(self) -> Dict[str, Any]:
        """Get live data for admin monitoring dashboard"""
        try:
            # Get widget statuses
            widget_statuses = {}
            for status_record in WidgetStatus.query.all():
                widget_statuses[status_record.widget_name] = {
                    'status': status_record.status,
                    'response_time_ms': status_record.response_time_ms,
                    'success_rate': status_record.success_rate,
                    'error_count': status_record.error_count,
                    'last_checked': status_record.last_checked.isoformat() if status_record.last_checked else None
                }
            
            # Get recent feedback/flags
            recent_feedback = MemberFeedback.query.filter(
                MemberFeedback.created_at >= datetime.now() - timedelta(hours=24)
            ).order_by(desc(MemberFeedback.created_at)).limit(10).all()
            
            recent_flags = PhotoFlag.query.filter(
                PhotoFlag.created_at >= datetime.now() - timedelta(hours=24)
            ).order_by(desc(PhotoFlag.created_at)).limit(10).all()
            
            # System stats
            system_stats = {
                'total_orchids': OrchidRecord.query.count(),
                'total_users': User.query.count() if hasattr(User, 'query') else 0,
                'open_feedback': MemberFeedback.query.filter_by(status='open').count(),
                'pending_flags': PhotoFlag.query.filter_by(status='pending').count(),
                'uptime_start': datetime.now() - timedelta(hours=12),  # Placeholder
            }
            
            return {
                'timestamp': datetime.now().isoformat(),
                'widget_statuses': widget_statuses,
                'recent_feedback': [{
                    'id': f.id,
                    'type': f.feedback_type,
                    'severity': f.severity,
                    'description': f.description[:100] + ('...' if len(f.description) > 100 else ''),
                    'created_at': f.created_at.isoformat()
                } for f in recent_feedback],
                'recent_flags': [{
                    'id': f.id,
                    'orchid_id': f.orchid_id,
                    'reason': f.flag_reason,
                    'status': f.status,
                    'created_at': f.created_at.isoformat()
                } for f in recent_flags],
                'system_stats': system_stats
            }
            
        except Exception as e:
            logger.error(f"Error getting live dashboard data: {e}")
            return {
                'timestamp': datetime.now().isoformat(),
                'error': str(e)
            }

# Initialize monitoring system
monitoring_system = AdminMonitoringSystem()

# ==============================================================================
# ROUTES
# ==============================================================================

@monitoring_bp.route('/admin/monitoring')
def admin_monitoring_dashboard():
    """Admin monitoring dashboard page"""
    return render_template('admin/monitoring_dashboard.html')

@monitoring_bp.route('/api/admin/comprehensive-diagnostic')
def comprehensive_diagnostic():
    """Perform comprehensive system diagnostic"""
    try:
        results = monitoring_system.perform_comprehensive_widget_diagnostic()
        return jsonify(results)
    except Exception as e:
        logger.error(f"Error in comprehensive diagnostic endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/admin/live-dashboard-data')
def live_dashboard_data():
    """Get live dashboard data"""
    try:
        data = monitoring_system.get_live_dashboard_data()
        return jsonify(data)
    except Exception as e:
        logger.error(f"Error in live dashboard data endpoint: {e}")
        return jsonify({'error': str(e)}), 500

@monitoring_bp.route('/api/admin/widget-test/<widget_name>')
def test_specific_widget(widget_name):
    """Test specific widget on demand"""
    try:
        if widget_name not in monitoring_system.widget_endpoints:
            return jsonify({'error': 'Widget not found'}), 404
        
        endpoint = monitoring_system.widget_endpoints[widget_name]
        result = monitoring_system._test_widget_endpoint(widget_name, endpoint)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error testing widget {widget_name}: {e}")
        return jsonify({'error': str(e)}), 500

# Register monitoring system
def register_monitoring_system():
    """Register the monitoring system with the main app"""
    app.register_blueprint(monitoring_bp)
    logger.info("Admin Monitoring Dashboard registered successfully")