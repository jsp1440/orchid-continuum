#!/usr/bin/env python3
"""
System Health Dashboard
Real-time monitoring dashboard for all Orchid Continuum features
"""

import requests
import time
import json
from datetime import datetime
from flask import Blueprint, render_template, jsonify, request
from threading import Thread
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Blueprint for health dashboard
health_bp = Blueprint('health', __name__, url_prefix='/health')

class SystemHealthMonitor:
    """Comprehensive system health monitoring"""
    
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.last_check = None
        self.health_history = []
        self.monitoring = False
        
        # Define critical features to monitor
        self.critical_features = {
            'core_pages': {
                'home_page': '/',
                'gallery': '/gallery',
                'search': '/search',
                'upload': '/upload',
                'admin': '/admin'
            },
            'themed_collections': {
                'themed_orchids': '/themed-orchids',
                'fragrant': '/themed-orchids/fragrant',
                'miniature': '/themed-orchids/miniature',
                'unusual': '/themed-orchids/unusual',
                'colorful': '/themed-orchids/colorful',
                'species': '/themed-orchids/species',
                'hybrids': '/themed-orchids/hybrids'
            },
            'interactive_features': {
                'global_map': '/orchid-map',
                'orchid_maps': '/orchid-maps',
                'orchid_explorer': '/orchid-explorer',
                'weather_widget': '/widgets/climate',
                'weather_comparison': '/weather-habitat/comparison'
            },
            'games': {
                'games_hub': '/games',
                'memory_game': '/games/memory',
                'puzzle_game': '/games/puzzle',
                'quiz_game': '/games/quiz'
            },
            'api_endpoints': {
                'recent_orchids': '/api/recent-orchids',
                'database_stats': '/api/database-stats',
                'themed_orchids': '/api/themed-orchids',
                'orchid_genera': '/api/orchid-genera',
                'featured_orchids': '/api/featured-orchids',
                'weather_api': '/api/weather?lat=35&lon=-120',
                'climate_data': '/widgets/climate-data',
                'coordinates': '/mapping/api/coordinates'
            }
        }
        
    def check_feature(self, name, endpoint, timeout=10):
        """Check if a specific feature is working"""
        try:
            url = f"{self.base_url}{endpoint}"
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = round(time.time() - start_time, 2)
            
            return {
                'name': name,
                'endpoint': endpoint,
                'status': response.status_code,
                'success': response.status_code == 200,
                'response_time': response_time,
                'size': len(response.content),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'name': name,
                'endpoint': endpoint,
                'status': 'ERROR',
                'success': False,
                'error': str(e),
                'response_time': None,
                'timestamp': datetime.now().isoformat()
            }
    
    def run_comprehensive_health_check(self):
        """Run comprehensive health check across all features"""
        logger.info("🔍 Running comprehensive health check...")
        
        results = {}
        overall_stats = {
            'timestamp': datetime.now().isoformat(),
            'total_features': 0,
            'working_features': 0,
            'failed_features': 0,
            'average_response_time': 0,
            'health_score': 0
        }
        
        total_response_time = 0
        response_count = 0
        
        # Check all feature categories
        for category, features in self.critical_features.items():
            category_results = {}
            category_working = 0
            
            for feature_name, endpoint in features.items():
                result = self.check_feature(feature_name, endpoint)
                category_results[feature_name] = result
                
                overall_stats['total_features'] += 1
                
                if result['success']:
                    overall_stats['working_features'] += 1
                    category_working += 1
                    
                    if result['response_time']:
                        total_response_time += result['response_time']
                        response_count += 1
                else:
                    overall_stats['failed_features'] += 1
            
            # Calculate category health
            category_health = (category_working / len(features)) * 100
            results[category] = {
                'features': category_results,
                'health_score': round(category_health, 1),
                'working_count': category_working,
                'total_count': len(features)
            }
        
        # Calculate overall metrics
        if overall_stats['total_features'] > 0:
            overall_stats['health_score'] = round(
                (overall_stats['working_features'] / overall_stats['total_features']) * 100, 1
            )
        
        if response_count > 0:
            overall_stats['average_response_time'] = round(total_response_time / response_count, 2)
        
        health_report = {
            'overall': overall_stats,
            'categories': results
        }
        
        # Store in history
        self.health_history.append(health_report)
        if len(self.health_history) > 100:  # Keep last 100 checks
            self.health_history.pop(0)
        
        self.last_check = datetime.now().isoformat()
        
        # Log summary
        logger.info(f"📊 Health Check Complete: {overall_stats['health_score']}% ({overall_stats['working_features']}/{overall_stats['total_features']})")
        
        if overall_stats['failed_features'] > 0:
            failed_features = []
            for category, data in results.items():
                for feature, result in data['features'].items():
                    if not result['success']:
                        failed_features.append(f"{category}.{feature}")
            
            logger.warning(f"❌ Failed Features: {', '.join(failed_features[:5])}")
        
        return health_report
    
    def get_latest_health(self):
        """Get latest health report"""
        if not self.health_history:
            return self.run_comprehensive_health_check()
        return self.health_history[-1]
    
    def start_continuous_monitoring(self, interval_minutes=10):
        """Start continuous health monitoring"""
        self.monitoring = True
        
        def monitor_loop():
            while self.monitoring:
                try:
                    self.run_comprehensive_health_check()
                    time.sleep(interval_minutes * 60)
                except Exception as e:
                    logger.error(f"❌ Monitoring error: {e}")
                    time.sleep(60)
        
        monitor_thread = Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info(f"🔄 Continuous monitoring started (every {interval_minutes} minutes)")
    
    def stop_monitoring(self):
        """Stop continuous monitoring"""
        self.monitoring = False
        logger.info("⏹️ Continuous monitoring stopped")

# Global monitor instance
health_monitor = SystemHealthMonitor()

# Routes for health dashboard
@health_bp.route('/')
def health_dashboard():
    """Health dashboard homepage"""
    return render_template('health/dashboard.html')

@health_bp.route('/api/status')
def api_health_status():
    """API endpoint for current health status"""
    health_report = health_monitor.get_latest_health()
    return jsonify(health_report)

@health_bp.route('/api/check')
def api_run_health_check():
    """API endpoint to trigger immediate health check"""
    health_report = health_monitor.run_comprehensive_health_check()
    return jsonify(health_report)

@health_bp.route('/api/history')
def api_health_history():
    """API endpoint for health history"""
    limit = request.args.get('limit', 10, type=int)
    history = health_monitor.health_history[-limit:] if health_monitor.health_history else []
    return jsonify({
        'history': history,
        'total_checks': len(health_monitor.health_history)
    })

@health_bp.route('/api/alerts')
def api_health_alerts():
    """API endpoint for health alerts"""
    latest = health_monitor.get_latest_health()
    alerts = []
    
    if latest['overall']['health_score'] < 70:
        alerts.append({
            'type': 'critical',
            'message': f"System health critically low: {latest['overall']['health_score']}%",
            'timestamp': latest['overall']['timestamp']
        })
    elif latest['overall']['health_score'] < 85:
        alerts.append({
            'type': 'warning',
            'message': f"System health needs attention: {latest['overall']['health_score']}%",
            'timestamp': latest['overall']['timestamp']
        })
    
    # Check for failed categories
    for category, data in latest['categories'].items():
        if data['health_score'] < 50:
            alerts.append({
                'type': 'error',
                'message': f"{category.replace('_', ' ').title()} category failing: {data['health_score']}%",
                'timestamp': latest['overall']['timestamp']
            })
    
    return jsonify({'alerts': alerts})

def start_health_monitoring():
    """Start the health monitoring system"""
    health_monitor.start_continuous_monitoring(interval_minutes=10)

def get_system_health():
    """Get current system health"""
    return health_monitor.get_latest_health()

if __name__ == "__main__":
    # Run health check when executed directly
    print("🔍 Running System Health Check...")
    report = health_monitor.run_comprehensive_health_check()
    
    print(f"\n📊 SYSTEM HEALTH REPORT")
    print(f"Overall Health: {report['overall']['health_score']}%")
    print(f"Working Features: {report['overall']['working_features']}/{report['overall']['total_features']}")
    print(f"Average Response Time: {report['overall']['average_response_time']}s")
    
    print(f"\n📋 CATEGORY BREAKDOWN:")
    for category, data in report['categories'].items():
        print(f"  - {category.replace('_', ' ').title()}: {data['health_score']}% ({data['working_count']}/{data['total_count']})")
    
    if report['overall']['failed_features'] > 0:
        print(f"\n❌ ISSUES FOUND:")
        for category, data in report['categories'].items():
            failed = [f for f, r in data['features'].items() if not r['success']]
            if failed:
                print(f"  - {category}: {', '.join(failed)}")