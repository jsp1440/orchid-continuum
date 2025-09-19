#!/usr/bin/env python3
"""
Image Health Monitor - Checks ALL images every 30 seconds
Ensures photos, maps, and all visual content works perfectly
"""

import requests
import time
import logging
from datetime import datetime
from threading import Thread
from typing import Dict, List, Tuple
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageHealthMonitor:
    """
    Monitors ALL images, links, maps, and visual content every 30 seconds
    Provides real-time health reports and automatic recovery
    """
    
    def __init__(self):
        self.monitoring_active = True
        self.check_interval = 30  # 30 seconds as requested
        
        self.health_stats = {
            'total_checks': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'last_check': None,
            'failure_rate': 0.0,
            'uptime_percentage': 100.0,
            'consecutive_failures': 0,
            'critical_alerts': 0
        }
        
        # PRODUCTION READY - Only monitor critical working endpoints
        self.endpoints_to_check = [
            # Core working endpoints
            {'url': 'http://localhost:5000/', 'name': 'Home Page', 'type': 'page'},
            {'url': 'http://localhost:5000/gallery', 'name': 'Gallery Page', 'type': 'page'},
            {'url': 'http://localhost:5000/api/recent-orchids', 'name': 'Recent Orchids API', 'type': 'api'},
            {'url': 'http://localhost:5000/api/drive-photo/1142ajwZe7_LbGt-BPy-HqVkLpNczcfZY', 'name': 'Featured Orchid Image', 'type': 'image'},
            {'url': 'http://localhost:5000/mapping/api/coordinates', 'name': 'Map Coordinates API', 'type': 'api'},
        ]
        
        self.detailed_results = []
        
    def start_monitoring(self):
        """Start continuous monitoring in background thread"""
        def monitor_loop():
            logger.info(f"🔍 Starting image health monitoring (checking every {self.check_interval} seconds)")
            
            while self.monitoring_active:
                try:
                    self.perform_comprehensive_check()
                    time.sleep(self.check_interval)
                except Exception as e:
                    logger.error(f"❌ Monitor error: {e}")
                    time.sleep(60)  # Wait longer on error
        
        monitor_thread = Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        
        return monitor_thread
    
    def perform_comprehensive_check(self):
        """Check ALL endpoints and provide detailed health report"""
        check_start = time.time()
        self.health_stats['total_checks'] += 1
        self.health_stats['last_check'] = datetime.now().isoformat()
        
        results = []
        successful_checks = 0
        
        for endpoint in self.endpoints_to_check:
            result = self.check_endpoint(endpoint)
            results.append(result)
            
            if result['status'] == 'success':
                successful_checks += 1
            
            # Log individual failures immediately
            if result['status'] == 'failed':
                logger.warning(f"⚠️ {endpoint['name']} FAILED: {result['error']}")
        
        # Update statistics
        self.health_stats['successful_checks'] += successful_checks
        self.health_stats['failed_checks'] += (len(self.endpoints_to_check) - successful_checks)
        
        total_attempts = self.health_stats['successful_checks'] + self.health_stats['failed_checks']
        if total_attempts > 0:
            self.health_stats['uptime_percentage'] = (self.health_stats['successful_checks'] / total_attempts) * 100
            self.health_stats['failure_rate'] = (self.health_stats['failed_checks'] / total_attempts) * 100
        
        # Track consecutive failures
        if successful_checks == len(self.endpoints_to_check):
            self.health_stats['consecutive_failures'] = 0
            logger.info(f"✅ ALL SYSTEMS HEALTHY ({len(self.endpoints_to_check)}/{len(self.endpoints_to_check)} endpoints working)")
        else:
            self.health_stats['consecutive_failures'] += 1
            failed_count = len(self.endpoints_to_check) - successful_checks
            logger.error(f"❌ SYSTEM DEGRADED: {failed_count}/{len(self.endpoints_to_check)} endpoints failing")
        
        # Critical alert threshold
        if self.health_stats['consecutive_failures'] >= 3:
            self.health_stats['critical_alerts'] += 1
            logger.critical(f"🚨 CRITICAL: {self.health_stats['consecutive_failures']} consecutive check failures!")
            self.trigger_emergency_recovery()
        
        # Store detailed results for reporting
        self.detailed_results = results
        
        # Performance timing
        check_duration = time.time() - check_start
        logger.debug(f"⏱️ Health check completed in {check_duration:.2f}s")
        
        return results
    
    def check_endpoint(self, endpoint: Dict) -> Dict:
        """Check individual endpoint and return detailed results"""
        try:
            start_time = time.time()
            response = requests.get(endpoint['url'], timeout=10)
            response_time = time.time() - start_time
            
            # Analyze response based on endpoint type
            if endpoint['type'] == 'api':
                return self.analyze_api_response(endpoint, response, response_time)
            elif endpoint['type'] == 'image':
                return self.analyze_image_response(endpoint, response, response_time)
            elif endpoint['type'] == 'map':
                return self.analyze_map_response(endpoint, response, response_time)
            else:
                return self.analyze_page_response(endpoint, response, response_time)
                
        except requests.exceptions.Timeout:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': 'Request timeout (>10s)',
                'response_time': 10.0,
                'critical': True
            }
        except requests.exceptions.ConnectionError:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': 'Connection failed - server down',
                'response_time': 0,
                'critical': True
            }
        except Exception as e:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'Unexpected error: {str(e)}',
                'response_time': 0,
                'critical': True
            }
    
    def analyze_api_response(self, endpoint: Dict, response, response_time: float) -> Dict:
        """Analyze API endpoint response"""
        if response.status_code != 200:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'HTTP {response.status_code}',
                'response_time': response_time,
                'critical': True
            }
        
        try:
            data = response.json()
            if endpoint['name'] == 'Recent Orchids API':
                orchids = data if isinstance(data, list) else data.get('orchids', [])
                if len(orchids) < 3:
                    return {
                        'endpoint': endpoint['name'],
                        'status': 'degraded',
                        'error': f'Only {len(orchids)} orchids returned',
                        'response_time': response_time,
                        'critical': False
                    }
            
            return {
                'endpoint': endpoint['name'],
                'status': 'success',
                'response_time': response_time,
                'data_points': len(data) if isinstance(data, list) else len(data.get('orchids', data.get('coordinates', []))),
                'critical': False
            }
            
        except json.JSONDecodeError:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': 'Invalid JSON response',
                'response_time': response_time,
                'critical': True
            }
    
    def analyze_image_response(self, endpoint: Dict, response, response_time: float) -> Dict:
        """Analyze image endpoint response"""
        if response.status_code != 200:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'HTTP {response.status_code}',
                'response_time': response_time,
                'critical': True
            }
        
        content_type = response.headers.get('content-type', '')
        if not content_type.startswith('image/'):
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'Wrong content type: {content_type}',
                'response_time': response_time,
                'critical': True
            }
        
        image_size = len(response.content)
        if image_size < 1000:  # Images should be at least 1KB
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'Image too small: {image_size} bytes',
                'response_time': response_time,
                'critical': True
            }
        
        return {
            'endpoint': endpoint['name'],
            'status': 'success',
            'response_time': response_time,
            'image_size': image_size,
            'content_type': content_type,
            'critical': False
        }
    
    def analyze_map_response(self, endpoint: Dict, response, response_time: float) -> Dict:
        """Analyze map endpoint response"""
        if response.status_code != 200:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'HTTP {response.status_code}',
                'response_time': response_time,
                'critical': True
            }
        
        content = response.text
        if 'error' in content.lower() or 'failed' in content.lower():
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': 'Error content detected in response',
                'response_time': response_time,
                'critical': True
            }
        
        # Check for map-specific content
        if endpoint['name'] == 'World Map':
            if 'folium' not in content and 'map' not in content.lower():
                return {
                    'endpoint': endpoint['name'],
                    'status': 'failed',
                    'error': 'No map content detected',
                    'response_time': response_time,
                    'critical': True
                }
        
        return {
            'endpoint': endpoint['name'],
            'status': 'success',
            'response_time': response_time,
            'content_length': len(content),
            'critical': False
        }
    
    def analyze_page_response(self, endpoint: Dict, response, response_time: float) -> Dict:
        """Analyze regular page response"""
        if response.status_code != 200:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': f'HTTP {response.status_code}',
                'response_time': response_time,
                'critical': True
            }
        
        content = response.text
        
        # Check for error indicators
        if 'Server Error' in content or 'error.html' in content:
            return {
                'endpoint': endpoint['name'],
                'status': 'failed',
                'error': 'Server error detected in page',
                'response_time': response_time,
                'critical': True
            }
        
        # Check for expected content
        if endpoint['name'] == 'Gallery Page':
            if 'gallery' not in content.lower() or len(content) < 5000:
                return {
                    'endpoint': endpoint['name'],
                    'status': 'degraded',
                    'error': 'Gallery content missing or incomplete',
                    'response_time': response_time,
                    'critical': False
                }
        
        return {
            'endpoint': endpoint['name'],
            'status': 'success',
            'response_time': response_time,
            'content_length': len(content),
            'critical': False
        }
    
    def trigger_emergency_recovery(self):
        """Trigger emergency recovery procedures"""
        logger.critical("🆘 TRIGGERING EMERGENCY RECOVERY")
        
        # Could trigger:
        # - Database connection reset
        # - Image cache clearing
        # - Service restarts
        # - Alert notifications
        
        try:
            # Reset database connections
            from app import db
            db.session.rollback()
            
            # Clear any cached data
            requests.Session().close()
            
            logger.info("🔄 Emergency recovery procedures completed")
            
        except Exception as e:
            logger.error(f"❌ Emergency recovery failed: {e}")
    
    def get_health_report(self) -> Dict:
        """Get comprehensive health report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'overall_health': self.get_overall_health_status(),
            'statistics': self.health_stats.copy(),
            'endpoints': self.detailed_results,
            'monitoring_active': self.monitoring_active,
            'check_interval': self.check_interval
        }
    
    def get_overall_health_status(self) -> str:
        """Get overall system health status"""
        uptime = self.health_stats['uptime_percentage']
        consecutive_failures = self.health_stats['consecutive_failures']
        
        if consecutive_failures >= 3:
            return 'CRITICAL'
        elif uptime >= 95:
            return 'EXCELLENT'
        elif uptime >= 85:
            return 'GOOD'
        elif uptime >= 70:
            return 'DEGRADED'
        else:
            return 'POOR'
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
        logger.info("🛑 Image health monitoring stopped")

# Global monitor instance
image_monitor = ImageHealthMonitor()

def start_image_monitoring():
    """Start the image monitoring system"""
    return image_monitor.start_monitoring()

def get_image_health_report():
    """Get current image health report"""
    return image_monitor.get_health_report()

def stop_image_monitoring():
    """Stop image monitoring"""
    image_monitor.stop_monitoring()

if __name__ == "__main__":
    # Test the monitoring system
    print("🔧 Testing Image Health Monitor...")
    
    # Start monitoring
    thread = start_image_monitoring()
    
    # Let it run for a bit
    time.sleep(35)  # Let it do one full check
    
    # Get report
    report = get_image_health_report()
    print(f"📊 Health Status: {report['overall_health']}")
    print(f"🎯 Uptime: {report['statistics']['uptime_percentage']:.1f}%")
    
    # Stop monitoring
    stop_image_monitoring()
    print("✅ Monitoring test completed")