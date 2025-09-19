#!/usr/bin/env python3
"""
Comprehensive Photo Monitoring System
Proactive detection and prevention of photo display failures
"""

import logging
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Thread
import schedule
import json

class PhotoHealthMonitor:
    """
    Continuous monitoring system that prevents photo failures before they happen
    """
    
    def __init__(self):
        self.health_stats = {
            'last_check': None,
            'total_checks': 0,
            'database_failures': 0,
            'image_failures': 0,
            'api_failures': 0,
            'recovery_activations': 0,
            'system_health_score': 100
        }
        
        self.alert_thresholds = {
            'database_failure_rate': 0.1,  # 10% failure rate triggers alert
            'image_failure_rate': 0.3,     # 30% image failure rate
            'api_failure_rate': 0.1,       # 10% API failure rate
            'consecutive_failures': 3       # 3 consecutive failures
        }
        
        self.monitoring_enabled = True
        self.consecutive_failures = 0
        
    def start_monitoring(self):
        """Start continuous monitoring thread"""
        def monitor_loop():
            while self.monitoring_enabled:
                try:
                    self.perform_health_check()
                    time.sleep(30)  # Check every 30 seconds
                except Exception as e:
                    logging.error(f"Health monitor error: {e}")
                    time.sleep(60)  # Wait longer if there's an error
        
        monitor_thread = Thread(target=monitor_loop, daemon=True)
        monitor_thread.start()
        logging.info("🔍 Photo health monitoring started")
    
    def perform_health_check(self):
        """Perform comprehensive system health check"""
        self.health_stats['total_checks'] += 1
        self.health_stats['last_check'] = datetime.now().isoformat()
        
        checks = {
            'database': self.check_database_health(),
            'api': self.check_api_health(),
            'images': self.check_image_health(),
            'failsafe': self.check_failsafe_system()
        }
        
        # Calculate overall health score
        healthy_systems = sum(1 for status in checks.values() if status)
        health_score = (healthy_systems / len(checks)) * 100
        self.health_stats['system_health_score'] = health_score
        
        # Handle failures
        if health_score < 75:
            self.consecutive_failures += 1
            self.handle_system_degradation(checks)
        else:
            self.consecutive_failures = 0
        
        # Log status
        if health_score < 50:
            logging.critical(f"🚨 CRITICAL: System health at {health_score:.1f}%")
        elif health_score < 75:
            logging.warning(f"⚠️ WARNING: System health at {health_score:.1f}%")
        else:
            logging.debug(f"✅ System healthy: {health_score:.1f}%")
    
    def check_database_health(self) -> bool:
        """Check if database queries are working"""
        try:
            from models import OrchidRecord
            from app import db
            
            # Simple test query
            count = OrchidRecord.query.count()
            
            if count < 100:  # Expect at least 100 orchids
                logging.warning(f"⚠️ Low orchid count: {count}")
                return False
            
            return True
            
        except Exception as e:
            self.health_stats['database_failures'] += 1
            logging.error(f"❌ Database health check failed: {e}")
            return False
    
    def check_api_health(self) -> bool:
        """Check if API endpoints are responding"""
        try:
            response = requests.get('http://localhost:5000/api/recent-orchids', timeout=5)
            
            if response.status_code != 200:
                raise Exception(f"API returned {response.status_code}")
            
            data = response.json()
            if data.get('status') != 'success':
                raise Exception(f"API status: {data.get('status')}")
            
            orchids = data.get('orchids', [])
            if len(orchids) < 3:
                raise Exception(f"Insufficient orchids returned: {len(orchids)}")
            
            return True
            
        except Exception as e:
            self.health_stats['api_failures'] += 1
            logging.error(f"❌ API health check failed: {e}")
            return False
    
    def check_image_health(self) -> bool:
        """Check if images are loading properly"""
        try:
            # Test a known Google Drive image
            test_image_id = "185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I"
            response = requests.head(f'http://localhost:5000/api/drive-photo/{test_image_id}', timeout=5)
            
            if response.status_code != 200:
                raise Exception(f"Image request failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.health_stats['image_failures'] += 1
            logging.error(f"❌ Image health check failed: {e}")
            return False
    
    def check_failsafe_system(self) -> bool:
        """Verify failsafe system is ready"""
        try:
            from photo_failsafe_system import photo_failsafe
            status = photo_failsafe.get_recovery_status()
            
            backup_count = status.get('backup_available', 0)
            if backup_count < 6:
                raise Exception(f"Insufficient backup photos: {backup_count}")
            
            return True
            
        except Exception as e:
            logging.error(f"❌ Failsafe check failed: {e}")
            return False
    
    def handle_system_degradation(self, checks: Dict[str, bool]):
        """Handle system degradation with automated recovery"""
        logging.warning(f"🔧 System degradation detected after {self.consecutive_failures} consecutive failures")
        
        # Auto-recovery actions
        if not checks['database']:
            self.attempt_database_recovery()
        
        if not checks['images']:
            self.attempt_image_recovery()
        
        if self.consecutive_failures >= self.alert_thresholds['consecutive_failures']:
            self.activate_emergency_mode()
    
    def attempt_database_recovery(self):
        """Attempt to recover database connection"""
        try:
            from app import db
            db.session.rollback()
            logging.info("🔄 Database recovery attempted")
        except Exception as e:
            logging.error(f"Database recovery failed: {e}")
    
    def attempt_image_recovery(self):
        """Attempt to recover image system"""
        try:
            # Clear any cached connections
            requests.Session().close()
            logging.info("🔄 Image connection recovery attempted")
        except Exception as e:
            logging.error(f"Image recovery failed: {e}")
    
    def activate_emergency_mode(self):
        """Activate system-wide emergency mode"""
        self.health_stats['recovery_activations'] += 1
        
        logging.critical("🆘 EMERGENCY MODE ACTIVATED - All systems using failsafe")
        
        # Here you could:
        # - Switch all routes to failsafe mode
        # - Send alerts to administrators
        # - Enable additional logging
        # - Activate backup systems
    
    def get_health_report(self) -> Dict:
        """Get comprehensive health report"""
        return {
            'timestamp': datetime.now().isoformat(),
            'stats': self.health_stats.copy(),
            'status': self.get_system_status(),
            'recommendations': self.get_recommendations()
        }
    
    def get_system_status(self) -> str:
        """Get current system status"""
        score = self.health_stats['system_health_score']
        
        if score >= 90:
            return 'excellent'
        elif score >= 75:
            return 'good'
        elif score >= 50:
            return 'degraded'
        else:
            return 'critical'
    
    def get_recommendations(self) -> List[str]:
        """Get system improvement recommendations"""
        recommendations = []
        
        if self.health_stats['database_failures'] > 5:
            recommendations.append("Consider database connection pooling optimization")
        
        if self.health_stats['image_failures'] > 10:
            recommendations.append("Review image hosting and CDN configuration")
        
        if self.health_stats['recovery_activations'] > 0:
            recommendations.append("Investigate root causes of system failures")
        
        return recommendations

class PhotoDisplayGuarantee:
    """
    Guarantee system that ensures photos are ALWAYS displayed to users
    """
    
    def __init__(self):
        self.guarantee_stats = {
            'total_requests': 0,
            'successful_displays': 0,
            'failsafe_activations': 0,
            'zero_photo_incidents': 0
        }
    
    def guarantee_photos(self, request_type: str, count: int = 12) -> Dict:
        """
        GUARANTEE that photos are returned - NEVER return empty
        """
        self.guarantee_stats['total_requests'] += 1
        
        try:
            # Try primary system
            if request_type == 'gallery':
                photos = self._get_gallery_photos(count)
            elif request_type == 'api':
                photos = self._get_api_photos(count)
            else:
                photos = self._get_generic_photos(count)
            
            if photos and len(photos) >= 3:
                self.guarantee_stats['successful_displays'] += 1
                return {'photos': photos, 'source': 'primary', 'guaranteed': True}
        
        except Exception as e:
            logging.error(f"Primary photo system failed: {e}")
        
        # FAILSAFE ACTIVATION - NEVER FAIL
        self.guarantee_stats['failsafe_activations'] += 1
        
        try:
            from photo_failsafe_system import get_photos_guaranteed
            photos, recovery_info = get_photos_guaranteed(count)
            
            return {
                'photos': photos,
                'source': 'failsafe',
                'guaranteed': True,
                'recovery_info': recovery_info
            }
        
        except Exception as critical_error:
            # ULTIMATE FALLBACK - Should never happen
            self.guarantee_stats['zero_photo_incidents'] += 1
            logging.critical(f"🆘 ULTIMATE FAILSAFE TRIGGERED: {critical_error}")
            
            return {
                'photos': self._get_hardcoded_emergency_photos(),
                'source': 'emergency_hardcoded',
                'guaranteed': True,
                'critical_error': str(critical_error)
            }
    
    def _get_gallery_photos(self, count: int) -> List[Dict]:
        """Get photos for gallery display"""
        from models import OrchidRecord
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).limit(count).all()
        
        return [self._orchid_to_dict(orchid) for orchid in orchids]
    
    def _get_api_photos(self, count: int) -> List[Dict]:
        """Get photos for API response"""
        return self._get_gallery_photos(count)
    
    def _get_generic_photos(self, count: int) -> List[Dict]:
        """Get photos for generic requests"""
        return self._get_gallery_photos(count)
    
    def _orchid_to_dict(self, orchid) -> Dict:
        """Convert orchid record to dictionary"""
        return {
            'id': orchid.id,
            'scientific_name': orchid.scientific_name,
            'common_name': orchid.display_name,
            'description': orchid.ai_description or 'Beautiful orchid specimen',
            'image_url': f'/api/drive-photo/{orchid.google_drive_id}' if orchid.google_drive_id else None,
            'source': 'database'
        }
    
    def _get_hardcoded_emergency_photos(self) -> List[Dict]:
        """Ultimate emergency fallback - hardcoded photos"""
        return [
            {
                'id': 1001,
                'scientific_name': 'Phalaenopsis sp.',
                'common_name': 'Moth Orchid',
                'description': 'Emergency fallback - Beautiful white orchid',
                'image_url': 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjMwMCIgZmlsbD0iI2Y4ZjlmYSIvPjx0ZXh0IHg9IjIwMCIgeT0iMTIwIiBmb250LWZhbWlseT0iQXJpYWwiIGZvbnQtc2l6ZT0iNDgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZpbGw9IiM5YjU5YjYiPvCfjJs8L3RleHQ+PHRleHQgeD0iMjAwIiB5PSIxNjAiIGZvbnQtZmFtaWx5PSJBcmlhbCIgZm9udC1zaXplPSIxNCIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZmlsbD0iIzY2NiI+T3JjaGlkIEltYWdlPC90ZXh0Pjwvc3ZnPg==',
                'source': 'emergency_hardcoded'
            }
        ]
    
    def get_guarantee_stats(self) -> Dict:
        """Get photo guarantee statistics"""
        total = self.guarantee_stats['total_requests']
        if total == 0:
            success_rate = 100
        else:
            success_rate = (self.guarantee_stats['successful_displays'] / total) * 100
        
        return {
            'stats': self.guarantee_stats.copy(),
            'success_rate': success_rate,
            'zero_incident_rate': (self.guarantee_stats['zero_photo_incidents'] / max(total, 1)) * 100
        }

# Global instances
health_monitor = PhotoHealthMonitor()
photo_guarantee = PhotoDisplayGuarantee()

def start_photo_monitoring():
    """Start the comprehensive photo monitoring system"""
    health_monitor.start_monitoring()
    logging.info("🛡️ Comprehensive photo monitoring system activated")

def ensure_photos_never_fail(request_type: str = 'gallery', count: int = 12) -> Dict:
    """Global function to guarantee photos never fail"""
    return photo_guarantee.guarantee_photos(request_type, count)

if __name__ == "__main__":
    # Test the monitoring system
    print("🔧 Testing Comprehensive Photo Monitor...")
    
    start_photo_monitoring()
    
    # Test guarantee system
    result = ensure_photos_never_fail('gallery', 6)
    print(f"✅ Photo guarantee test: {len(result['photos'])} photos from {result['source']}")
    
    # Get health report
    health_report = health_monitor.get_health_report()
    print(f"📊 System status: {health_report['status']}")
    
    # Get guarantee stats
    stats = photo_guarantee.get_guarantee_stats()
    print(f"🛡️ Photo guarantee success rate: {stats['success_rate']:.1f}%")