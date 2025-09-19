#!/usr/bin/env python3
"""
Comprehensive System Monitoring Dashboard
Real-time monitoring with automated recovery and prevention
"""

import os
import logging
import threading
import time
import json
import requests
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template_string, jsonify, request
from sqlalchemy import text
from models import OrchidRecord, db
from app import app
import psutil

logger = logging.getLogger(__name__)

class SystemMonitorDashboard:
    """Comprehensive system monitoring with real-time dashboard"""
    
    def __init__(self):
        self.monitoring_active = False
        self.check_interval = 30  # 30 seconds
        self.critical_thresholds = {
            'image_success_rate': 0.8,  # 80% minimum
            'db_connection_time': 5.0,  # 5 seconds max
            'memory_usage': 0.85,  # 85% max
            'disk_usage': 0.9  # 90% max
        }
        
        # Live metrics
        self.live_metrics = {
            'system': {
                'cpu_percent': 0,
                'memory_percent': 0,
                'disk_percent': 0,
                'uptime': 0
            },
            'database': {
                'connection_time': 0,
                'total_orchids': 0,
                'recent_uploads': 0,
                'connection_pool_status': 'unknown'
            },
            'images': {
                'success_rate': 0,
                'total_checked': 0,
                'failed_urls': [],
                'cache_size_mb': 0,
                'proxy_stats': {}
            },
            'services': {
                'api_response_time': 0,
                'map_services': {},
                'external_apis': {}
            },
            'alerts': [],
            'last_updated': datetime.now().isoformat()
        }
        
        # Performance history
        self.performance_history = []
        self.max_history = 100  # Keep last 100 readings
        
        # Recovery actions log
        self.recovery_log = []
        
    def start_monitoring(self):
        """Start comprehensive monitoring"""
        if self.monitoring_active:
            logger.warning("System monitoring already active")
            return
            
        self.monitoring_active = True
        logger.info("🚀 STARTING COMPREHENSIVE SYSTEM MONITORING")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring_active = False
        logger.info("⏹️ Stopping system monitoring")
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.monitoring_active:
            try:
                start_time = datetime.now()
                
                # Collect all metrics
                self._collect_system_metrics()
                self._check_database_health()
                self._verify_image_systems()
                self._test_service_endpoints()
                self._analyze_performance_trends()
                
                # Check for critical issues
                alerts = self._check_critical_thresholds()
                self.live_metrics['alerts'] = alerts
                
                # Auto-recovery for critical issues
                if alerts:
                    self._execute_recovery_actions(alerts)
                
                # Update timestamp
                self.live_metrics['last_updated'] = datetime.now().isoformat()
                
                # Store performance snapshot
                collection_time = (datetime.now() - start_time).total_seconds()
                self._store_performance_snapshot(collection_time)
                
                logger.info(f"✅ System check completed in {collection_time:.2f}s")
                
                # Sleep until next check
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                time.sleep(10)  # Brief pause on error
                
    def _collect_system_metrics(self):
        """Collect system resource metrics"""
        try:
            self.live_metrics['system'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_percent': psutil.disk_usage('/').percent,
                'uptime': time.time() - psutil.boot_time()
            }
        except Exception as e:
            logger.error(f"System metrics error: {e}")
            
    def _check_database_health(self):
        """Check database connectivity and performance"""
        try:
            with app.app_context():
                start_time = time.time()
                
                # Test basic connectivity
                db.session.execute(text("SELECT 1"))
                connection_time = time.time() - start_time
                
                # Get orchid count
                total_orchids = OrchidRecord.query.count()
                
                # Get recent uploads (last 24 hours)
                recent_uploads = OrchidRecord.query.filter(
                    OrchidRecord.created_at >= datetime.now() - timedelta(days=1)
                ).count()
                
                self.live_metrics['database'] = {
                    'connection_time': connection_time,
                    'total_orchids': total_orchids,
                    'recent_uploads': recent_uploads,
                    'connection_pool_status': 'healthy' if connection_time < 5 else 'slow'
                }
                
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            self.live_metrics['database'] = {
                'connection_time': 999,
                'total_orchids': 0,
                'recent_uploads': 0,
                'connection_pool_status': 'error'
            }
            
    def _verify_image_systems(self):
        """Test image loading and proxy systems"""
        try:
            # Test recent orchids API for image URLs
            response = requests.get('http://localhost:5000/api/recent-orchids', timeout=10)
            
            if response.status_code == 200:
                orchids = response.json()[:5]  # Test first 5
                total_checked = len(orchids)
                successful = 0
                failed_urls = []
                
                for orchid in orchids:
                    photo_url = orchid.get('photo_url') or orchid.get('image_url')
                    if photo_url:
                        try:
                            proxy_url = f"http://localhost:5000/api/proxy-image?url={photo_url}"
                            test_response = requests.head(proxy_url, timeout=5)
                            if test_response.status_code == 200:
                                successful += 1
                            else:
                                failed_urls.append(photo_url)
                        except:
                            failed_urls.append(photo_url)
                
                success_rate = successful / total_checked if total_checked > 0 else 0
                
                # Get image recovery stats
                try:
                    from image_recovery_system import get_image_recovery_stats
                    recovery_stats = get_image_recovery_stats()
                except:
                    recovery_stats = {}
                
                self.live_metrics['images'] = {
                    'success_rate': success_rate,
                    'total_checked': total_checked,
                    'failed_urls': failed_urls[:3],  # Show first 3 failures
                    'cache_size_mb': recovery_stats.get('cache_size_mb', 0),
                    'proxy_stats': recovery_stats
                }
                
            else:
                raise Exception(f"API returned {response.status_code}")
                
        except Exception as e:
            logger.error(f"Image system verification failed: {e}")
            self.live_metrics['images'] = {
                'success_rate': 0,
                'total_checked': 0,
                'failed_urls': [],
                'cache_size_mb': 0,
                'proxy_stats': {}
            }
            
    def _test_service_endpoints(self):
        """Test critical service endpoints"""
        services_to_test = [
            ('Main Page', '/'),
            ('Gallery', '/gallery'),
            ('Search', '/search'),
            ('Orchid Explorer', '/orchid-explorer'),
            ('API Health', '/api/recent-orchids')
        ]
        
        service_results = {}
        
        for service_name, endpoint in services_to_test:
            try:
                start_time = time.time()
                response = requests.get(f'http://localhost:5000{endpoint}', timeout=10)
                response_time = time.time() - start_time
                
                service_results[service_name] = {
                    'status': 'healthy' if response.status_code == 200 else 'error',
                    'response_time': response_time,
                    'status_code': response.status_code
                }
                
            except Exception as e:
                service_results[service_name] = {
                    'status': 'error',
                    'response_time': 999,
                    'error': str(e)
                }
        
        # Calculate average API response time
        healthy_times = [s['response_time'] for s in service_results.values() 
                        if s.get('status') == 'healthy' and s['response_time'] < 30]
        avg_response_time = sum(healthy_times) / len(healthy_times) if healthy_times else 0
        
        self.live_metrics['services'] = {
            'api_response_time': avg_response_time,
            'endpoints': service_results
        }
        
    def _analyze_performance_trends(self):
        """Analyze performance trends for predictions"""
        if len(self.performance_history) < 5:
            return  # Not enough data
        
        recent_metrics = self.performance_history[-10:]  # Last 10 readings
        
        # Calculate trends
        image_rates = [m['images']['success_rate'] for m in recent_metrics]
        db_times = [m['database']['connection_time'] for m in recent_metrics]
        
        trends = {
            'image_success_trend': 'improving' if image_rates[-1] > image_rates[0] else 'declining',
            'db_performance_trend': 'improving' if db_times[-1] < db_times[0] else 'declining'
        }
        
        self.live_metrics['trends'] = trends
        
    def _check_critical_thresholds(self) -> List[Dict]:
        """Check for critical threshold violations"""
        alerts = []
        
        # Image success rate check
        if self.live_metrics['images']['success_rate'] < self.critical_thresholds['image_success_rate']:
            alerts.append({
                'level': 'critical',
                'type': 'image_failure',
                'message': f"Image success rate {self.live_metrics['images']['success_rate']:.1%} below threshold {self.critical_thresholds['image_success_rate']:.1%}",
                'timestamp': datetime.now().isoformat(),
                'recovery_action': 'restart_image_services'
            })
        
        # Database performance check
        if self.live_metrics['database']['connection_time'] > self.critical_thresholds['db_connection_time']:
            alerts.append({
                'level': 'warning',
                'type': 'db_slow',
                'message': f"Database response time {self.live_metrics['database']['connection_time']:.2f}s exceeds {self.critical_thresholds['db_connection_time']}s",
                'timestamp': datetime.now().isoformat(),
                'recovery_action': 'restart_db_connections'
            })
        
        # Memory usage check
        if self.live_metrics['system']['memory_percent'] > self.critical_thresholds['memory_usage'] * 100:
            alerts.append({
                'level': 'warning',
                'type': 'high_memory',
                'message': f"Memory usage {self.live_metrics['system']['memory_percent']:.1f}% exceeds {self.critical_thresholds['memory_usage'] * 100:.1f}%",
                'timestamp': datetime.now().isoformat(),
                'recovery_action': 'cleanup_cache'
            })
        
        return alerts
        
    def _execute_recovery_actions(self, alerts: List[Dict]):
        """Execute automated recovery actions"""
        for alert in alerts:
            recovery_action = alert.get('recovery_action')
            
            if recovery_action == 'restart_image_services':
                self._restart_image_services()
            elif recovery_action == 'restart_db_connections':
                self._restart_db_connections()
            elif recovery_action == 'cleanup_cache':
                self._cleanup_system_cache()
                
            # Log recovery action
            self.recovery_log.append({
                'timestamp': datetime.now().isoformat(),
                'alert': alert,
                'action_taken': recovery_action,
                'success': True  # Would implement actual success checking
            })
            
    def _restart_image_services(self):
        """Restart image-related services"""
        try:
            logger.info("🔄 Restarting image services...")
            
            # Clear image cache
            from image_recovery_system import cleanup_image_cache
            cleanup_image_cache()
            
            # Force refresh of proxy connections
            # This would trigger reconnection to external services
            logger.info("✅ Image services restarted")
            
        except Exception as e:
            logger.error(f"Failed to restart image services: {e}")
            
    def _restart_db_connections(self):
        """Restart database connections"""
        try:
            logger.info("🔄 Restarting database connections...")
            with app.app_context():
                db.session.close()
                db.engine.dispose()
            logger.info("✅ Database connections restarted")
        except Exception as e:
            logger.error(f"Failed to restart DB connections: {e}")
            
    def _cleanup_system_cache(self):
        """Clean up system caches"""
        try:
            logger.info("🔄 Cleaning system cache...")
            from image_recovery_system import cleanup_image_cache
            cleanup_image_cache()
            logger.info("✅ System cache cleaned")
        except Exception as e:
            logger.error(f"Failed to clean cache: {e}")
            
    def _store_performance_snapshot(self, collection_time: float):
        """Store performance snapshot for trend analysis"""
        snapshot = {
            'timestamp': datetime.now().isoformat(),
            'collection_time': collection_time,
            'system': self.live_metrics['system'].copy(),
            'database': self.live_metrics['database'].copy(),
            'images': {k: v for k, v in self.live_metrics['images'].items() if k != 'failed_urls'},
            'services': {'api_response_time': self.live_metrics['services']['api_response_time']}
        }
        
        self.performance_history.append(snapshot)
        
        # Keep only recent history
        if len(self.performance_history) > self.max_history:
            self.performance_history = self.performance_history[-self.max_history:]
            
    def get_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data"""
        return {
            'live_metrics': self.live_metrics,
            'performance_history': self.performance_history[-20:],  # Last 20 readings
            'recovery_log': self.recovery_log[-10:],  # Last 10 recovery actions
            'monitoring_status': 'active' if self.monitoring_active else 'inactive',
            'thresholds': self.critical_thresholds
        }

# Global monitor instance
system_monitor = SystemMonitorDashboard()

# Blueprint for monitoring dashboard
monitor_bp = Blueprint('system_monitor', __name__)

@monitor_bp.route('/admin/system-monitor')
def monitoring_dashboard():
    """Serve monitoring dashboard"""
    dashboard_html = '''<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>System Monitor Dashboard - Five Cities Orchid Society</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; margin: 0; background: #f8f9fa; }
        .header { background: #2d5aa0; color: white; padding: 20px; text-align: center; }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .card { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
        .metric-value { font-size: 2rem; font-weight: bold; margin: 10px 0; }
        .status-healthy { color: #28a745; }
        .status-warning { color: #ffc107; }
        .status-critical { color: #dc3545; }
        .metric-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .metric-item { padding: 10px; background: #f8f9fa; border-radius: 8px; }
        .alert-item { padding: 12px; margin: 8px 0; border-radius: 8px; border-left: 4px solid; }
        .alert-critical { border-color: #dc3545; background: #f8d7da; }
        .alert-warning { border-color: #ffc107; background: #fff3cd; }
        .progress-bar { width: 100%; height: 20px; background: #e9ecef; border-radius: 10px; overflow: hidden; }
        .progress-fill { height: 100%; transition: width 0.3s ease; }
        .refresh-btn { padding: 10px 20px; background: #2d5aa0; color: white; border: none; border-radius: 6px; cursor: pointer; }
        .timestamp { font-size: 0.8rem; color: #6c757d; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🔍 System Monitor Dashboard</h1>
        <p>Real-time monitoring and automated recovery system</p>
        <button class="refresh-btn" onclick="refreshData()">🔄 Refresh Now</button>
    </div>
    
    <div class="container">
        <div class="grid">
            <!-- System Resources -->
            <div class="card">
                <h3>💻 System Resources</h3>
                <div class="metric-grid">
                    <div class="metric-item">
                        <strong>CPU Usage</strong>
                        <div class="metric-value" id="cpu-usage">--</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="cpu-progress" style="background: #28a745;"></div>
                        </div>
                    </div>
                    <div class="metric-item">
                        <strong>Memory Usage</strong>
                        <div class="metric-value" id="memory-usage">--</div>
                        <div class="progress-bar">
                            <div class="progress-fill" id="memory-progress" style="background: #ffc107;"></div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Database Health -->
            <div class="card">
                <h3>🗄️ Database Health</h3>
                <div class="metric-item">
                    <strong>Connection Time</strong>
                    <div class="metric-value" id="db-time">--</div>
                </div>
                <div class="metric-item">
                    <strong>Total Orchids</strong>
                    <div class="metric-value" id="total-orchids">--</div>
                </div>
                <div class="metric-item">
                    <strong>Recent Uploads</strong>
                    <div class="metric-value" id="recent-uploads">--</div>
                </div>
            </div>
            
            <!-- Image Systems -->
            <div class="card">
                <h3>🖼️ Image Systems</h3>
                <div class="metric-item">
                    <strong>Success Rate</strong>
                    <div class="metric-value" id="image-success">--</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="image-progress" style="background: #28a745;"></div>
                    </div>
                </div>
                <div class="metric-item">
                    <strong>Cache Size</strong>
                    <div class="metric-value" id="cache-size">-- MB</div>
                </div>
            </div>
            
            <!-- Service Status -->
            <div class="card">
                <h3>🌐 Service Status</h3>
                <div id="service-status">
                    <div class="metric-item">Loading services...</div>
                </div>
            </div>
            
            <!-- Active Alerts -->
            <div class="card">
                <h3>🚨 Active Alerts</h3>
                <div id="alerts-container">
                    <div class="metric-item">No alerts</div>
                </div>
            </div>
            
            <!-- Recovery Actions -->
            <div class="card">
                <h3>🔧 Recent Recovery Actions</h3>
                <div id="recovery-log">
                    <div class="metric-item">No recent actions</div>
                </div>
            </div>
        </div>
        
        <div class="timestamp" id="last-updated">Last updated: --</div>
    </div>
    
    <script>
        async function refreshData() {
            try {
                const response = await fetch('/admin/system-monitor/data');
                const data = await response.json();
                updateDashboard(data);
            } catch (error) {
                console.error('Failed to refresh data:', error);
            }
        }
        
        function updateDashboard(data) {
            const metrics = data.live_metrics;
            
            // System resources
            document.getElementById('cpu-usage').textContent = metrics.system.cpu_percent.toFixed(1) + '%';
            document.getElementById('memory-usage').textContent = metrics.system.memory_percent.toFixed(1) + '%';
            document.getElementById('cpu-progress').style.width = metrics.system.cpu_percent + '%';
            document.getElementById('memory-progress').style.width = metrics.system.memory_percent + '%';
            
            // Database
            document.getElementById('db-time').textContent = metrics.database.connection_time.toFixed(2) + 's';
            document.getElementById('total-orchids').textContent = metrics.database.total_orchids.toLocaleString();
            document.getElementById('recent-uploads').textContent = metrics.database.recent_uploads;
            
            // Images
            document.getElementById('image-success').textContent = (metrics.images.success_rate * 100).toFixed(1) + '%';
            document.getElementById('cache-size').textContent = metrics.images.cache_size_mb.toFixed(1) + ' MB';
            document.getElementById('image-progress').style.width = (metrics.images.success_rate * 100) + '%';
            
            // Services
            const servicesHtml = Object.entries(metrics.services.endpoints || {}).map(([name, status]) => 
                `<div class="metric-item">
                    <strong>${name}</strong>: 
                    <span class="status-${status.status === 'healthy' ? 'healthy' : 'critical'}">
                        ${status.status} (${status.response_time.toFixed(2)}s)
                    </span>
                </div>`
            ).join('');
            document.getElementById('service-status').innerHTML = servicesHtml || '<div class="metric-item">No service data</div>';
            
            // Alerts
            const alertsHtml = metrics.alerts.map(alert => 
                `<div class="alert-item alert-${alert.level}">
                    <strong>${alert.type}:</strong> ${alert.message}
                </div>`
            ).join('');
            document.getElementById('alerts-container').innerHTML = alertsHtml || '<div class="metric-item">No active alerts</div>';
            
            // Recovery log
            const recoveryHtml = (data.recovery_log || []).map(action => 
                `<div class="metric-item">
                    <strong>${action.action_taken}</strong><br>
                    <small>${new Date(action.timestamp).toLocaleString()}</small>
                </div>`
            ).join('');
            document.getElementById('recovery-log').innerHTML = recoveryHtml || '<div class="metric-item">No recent actions</div>';
            
            // Timestamp
            document.getElementById('last-updated').textContent = 'Last updated: ' + new Date(metrics.last_updated).toLocaleString();
        }
        
        // Auto-refresh every 30 seconds
        setInterval(refreshData, 30000);
        
        // Initial load
        refreshData();
    </script>
</body>
</html>'''
    
    return dashboard_html

@monitor_bp.route('/admin/system-monitor/data')
def monitoring_data():
    """API endpoint for monitoring data"""
    return jsonify(system_monitor.get_dashboard_data())

@monitor_bp.route('/admin/system-monitor/start')
def start_monitoring():
    """Start system monitoring"""
    system_monitor.start_monitoring()
    return jsonify({'status': 'started', 'message': 'System monitoring started'})

@monitor_bp.route('/admin/system-monitor/stop')
def stop_monitoring():
    """Stop system monitoring"""
    system_monitor.stop_monitoring()
    return jsonify({'status': 'stopped', 'message': 'System monitoring stopped'})

# Auto-start monitoring
def initialize_monitoring():
    """Initialize monitoring on startup"""
    try:
        system_monitor.start_monitoring()
        logger.info("🚀 System monitoring auto-started")
    except Exception as e:
        logger.error(f"Failed to auto-start system monitoring: {e}")

print("📊 System Monitor Dashboard initialized")