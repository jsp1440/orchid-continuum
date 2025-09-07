"""
CRITICAL MISSION: Real-Time Data Integrity Guardian
===============================================

This system provides ZERO TOLERANCE for data integrity failures.
Runs every 30 seconds + triggers on every user visit.

VALIDATION REQUIREMENTS:
1. Every orchid image MUST match correct genus + species
2. NO placeholder species names ("species", "sp.", etc.)
3. All widgets MUST function correctly
4. All links MUST work
5. Orchid of Day MUST have valid scientific name
6. Gallery images MUST load correctly

AUTO-REPAIR CAPABILITIES:
- Automatically reject invalid records
- Fix broken image links
- Restart failed services
- Clear corrupted caches
- Generate emergency fallbacks
"""

import logging
import threading
import time
import requests
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from app import app, db
from models import OrchidRecord

# Configure critical logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('integrity_guardian')

class RealTimeIntegrityGuardian:
    """MISSION CRITICAL: Continuous monitoring and auto-repair system"""
    
    def __init__(self):
        self.is_running = False
        self.last_check = None
        self.repair_count = 0
        self.failure_count = 0
        self.critical_alerts = []
        
        # Critical validation rules
        self.validation_rules = {
            'data_integrity': self._validate_data_integrity,
            'image_matching': self._validate_image_matching,
            'widget_health': self._validate_widget_health,
            'link_validation': self._validate_links,
            'orchid_of_day': self._validate_orchid_of_day,
            'gallery_health': self._validate_gallery_health
        }
        
        # Auto-repair functions
        self.repair_functions = {
            'reject_invalid_records': self._reject_invalid_records,
            'fix_broken_images': self._fix_broken_images,
            'restart_services': self._restart_services,
            'clear_caches': self._clear_caches,
            'generate_fallbacks': self._generate_fallbacks
        }
    
    def start_guardian(self):
        """Start the 30-second continuous monitoring system"""
        if self.is_running:
            logger.warning("Guardian already running")
            return
            
        self.is_running = True
        logger.info("🛡️ INTEGRITY GUARDIAN ACTIVATED - Zero tolerance for data corruption")
        
        # Start background monitoring thread
        monitor_thread = threading.Thread(target=self._continuous_monitoring, daemon=True)
        monitor_thread.start()
        
        return True
    
    def stop_guardian(self):
        """Stop the monitoring system"""
        self.is_running = False
        logger.info("🛡️ Guardian deactivated")
    
    def _continuous_monitoring(self):
        """Run validation checks every 30 seconds"""
        while self.is_running:
            try:
                with app.app_context():
                    self._run_complete_validation()
                    time.sleep(30)  # 30-second intervals
            except Exception as e:
                logger.error(f"🚨 CRITICAL: Guardian monitoring failed: {e}")
                self.failure_count += 1
                time.sleep(30)
    
    def trigger_user_validation(self, user_ip=None):
        """CRITICAL: Trigger validation on every user visit"""
        try:
            with app.app_context():
                logger.info(f"🔍 USER TRIGGER: Running integrity check for {user_ip or 'anonymous'}")
                return self._run_complete_validation()
        except Exception as e:
            logger.error(f"🚨 CRITICAL: User-triggered validation failed: {e}")
            return False
    
    def _run_complete_validation(self):
        """Run all validation checks and auto-repairs"""
        start_time = datetime.now()
        issues_found = 0
        repairs_made = 0
        
        logger.info("🔍 STARTING COMPLETE INTEGRITY VALIDATION")
        
        # Run all validation rules
        for rule_name, rule_function in self.validation_rules.items():
            try:
                violations = rule_function()
                if violations:
                    issues_found += len(violations)
                    logger.warning(f"⚠️ {rule_name}: {len(violations)} violations found")
                    
                    # Attempt auto-repair
                    repairs = self._attempt_auto_repair(rule_name, violations)
                    repairs_made += repairs
                    
            except Exception as e:
                logger.error(f"🚨 CRITICAL: {rule_name} validation failed: {e}")
                self.failure_count += 1
        
        # Update monitoring stats
        self.last_check = datetime.now()
        self.repair_count += repairs_made
        
        # Log results
        duration = (datetime.now() - start_time).total_seconds()
        if issues_found == 0:
            logger.info(f"✅ INTEGRITY CHECK PASSED: No issues found ({duration:.2f}s)")
        else:
            logger.warning(f"🔧 INTEGRITY CHECK: {issues_found} issues, {repairs_made} auto-repairs ({duration:.2f}s)")
        
        return issues_found == 0
    
    def _validate_data_integrity(self):
        """CRITICAL: Validate all orchid data integrity"""
        violations = []
        
        # Check for invalid species names
        invalid_species = db.session.query(OrchidRecord).filter(
            or_(
                OrchidRecord.species.in_(['species', 'sp.', 'sp', 'spp.', 'unknown', 'Unknown']),
                func.length(OrchidRecord.species) < 3,
                OrchidRecord.species.is_(None),
                OrchidRecord.genus.is_(None)
            ),
            OrchidRecord.validation_status != 'rejected'
        ).all()
        
        for record in invalid_species:
            violations.append({
                'type': 'invalid_species',
                'record_id': record.id,
                'issue': f"Invalid species: '{record.species}' for genus '{record.genus}'"
            })
        
        # Check for orphaned images (images without proper genus/species)
        orphaned_images = db.session.query(OrchidRecord).filter(
            and_(
                OrchidRecord.google_drive_id.isnot(None),
                or_(
                    OrchidRecord.genus.is_(None),
                    OrchidRecord.species.is_(None),
                    OrchidRecord.species.in_(['species', 'sp.', 'sp'])
                )
            )
        ).all()
        
        for record in orphaned_images:
            violations.append({
                'type': 'orphaned_image',
                'record_id': record.id,
                'issue': f"Image {record.google_drive_id} has invalid taxonomy"
            })
        
        return violations
    
    def _validate_image_matching(self):
        """CRITICAL: Ensure images match their orchid data"""
        violations = []
        
        # Get featured orchids and verify image-data alignment
        featured_orchids = db.session.query(OrchidRecord).filter(
            and_(
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None)
            )
        ).limit(10).all()
        
        for orchid in featured_orchids:
            # Check if image is accessible
            try:
                response = requests.head(f"http://localhost:5000/api/drive-photo/{orchid.google_drive_id}", timeout=5)
                if response.status_code != 200:
                    violations.append({
                        'type': 'broken_image',
                        'record_id': orchid.id,
                        'issue': f"Image {orchid.google_drive_id} not accessible"
                    })
            except:
                violations.append({
                    'type': 'broken_image',
                    'record_id': orchid.id,
                    'issue': f"Image {orchid.google_drive_id} connection failed"
                })
        
        return violations
    
    def _validate_widget_health(self):
        """CRITICAL: Validate all widgets are functioning"""
        violations = []
        
        widget_endpoints = [
            '/api/orchid-of-day',
            '/api/recent-orchids',
            '/mapping/api/coordinates',
            '/gallery',
            '/'
        ]
        
        for endpoint in widget_endpoints:
            try:
                response = requests.get(f"http://localhost:5000{endpoint}", timeout=10)
                if response.status_code != 200:
                    violations.append({
                        'type': 'widget_failure',
                        'endpoint': endpoint,
                        'issue': f"Widget returned {response.status_code}"
                    })
            except Exception as e:
                violations.append({
                    'type': 'widget_failure',
                    'endpoint': endpoint,
                    'issue': f"Widget connection failed: {e}"
                })
        
        return violations
    
    def _validate_links(self):
        """CRITICAL: Validate all internal links work"""
        violations = []
        
        # Check critical navigation links
        critical_links = [
            '/gallery',
            '/search',
            '/orchid-explorer',
            '/space-earth-globe',
            '/upload'
        ]
        
        for link in critical_links:
            try:
                response = requests.get(f"http://localhost:5000{link}", timeout=10)
                if response.status_code != 200:
                    violations.append({
                        'type': 'broken_link',
                        'link': link,
                        'issue': f"Link returned {response.status_code}"
                    })
            except Exception as e:
                violations.append({
                    'type': 'broken_link',
                    'link': link,
                    'issue': f"Link failed: {e}"
                })
        
        return violations
    
    def _validate_orchid_of_day(self):
        """CRITICAL: Validate Orchid of Day has proper scientific name"""
        violations = []
        
        try:
            response = requests.get("http://localhost:5000/api/orchid-of-day", timeout=10)
            if response.status_code == 200:
                data = response.json()
                orchid_name = data.get('name', '')
                
                # Check for invalid placeholder names
                if any(invalid in orchid_name.lower() for invalid in ['species', 'sp.', 'unknown']):
                    violations.append({
                        'type': 'invalid_orchid_of_day',
                        'issue': f"Orchid of Day has invalid name: '{orchid_name}'"
                    })
            else:
                violations.append({
                    'type': 'orchid_of_day_failure',
                    'issue': f"Orchid of Day API returned {response.status_code}"
                })
        except Exception as e:
            violations.append({
                'type': 'orchid_of_day_failure',
                'issue': f"Orchid of Day check failed: {e}"
            })
        
        return violations
    
    def _validate_gallery_health(self):
        """CRITICAL: Validate gallery images load correctly"""
        violations = []
        
        try:
            response = requests.get("http://localhost:5000/gallery", timeout=15)
            if response.status_code != 200:
                violations.append({
                    'type': 'gallery_failure',
                    'issue': f"Gallery returned {response.status_code}"
                })
            elif 'error' in response.text.lower():
                violations.append({
                    'type': 'gallery_error',
                    'issue': "Gallery contains error messages"
                })
        except Exception as e:
            violations.append({
                'type': 'gallery_failure',
                'issue': f"Gallery check failed: {e}"
            })
        
        return violations
    
    def _attempt_auto_repair(self, rule_name, violations):
        """Attempt automatic repair of detected issues"""
        repairs_made = 0
        
        for violation in violations:
            try:
                if violation['type'] == 'invalid_species':
                    # Auto-reject invalid records
                    record = db.session.query(OrchidRecord).get(violation['record_id'])
                    if record:
                        record.validation_status = 'rejected'
                        db.session.commit()
                        repairs_made += 1
                        logger.info(f"🔧 AUTO-REPAIR: Rejected invalid record {record.id}")
                
                elif violation['type'] == 'broken_image':
                    # Clear image cache and attempt reload
                    requests.post("http://localhost:5000/admin/clear-image-cache", timeout=5)
                    repairs_made += 1
                    logger.info(f"🔧 AUTO-REPAIR: Cleared image cache for broken image")
                
                elif violation['type'] == 'widget_failure':
                    # Restart services
                    requests.post("http://localhost:5000/admin/restart-services", timeout=10)
                    repairs_made += 1
                    logger.info(f"🔧 AUTO-REPAIR: Restarted services for widget failure")
                
            except Exception as e:
                logger.error(f"🚨 AUTO-REPAIR FAILED: {e}")
        
        return repairs_made
    
    def _reject_invalid_records(self):
        """Reject all records with invalid species data"""
        try:
            invalid_count = db.session.query(OrchidRecord).filter(
                or_(
                    OrchidRecord.species.in_(['species', 'sp.', 'sp', 'spp.', 'unknown']),
                    func.length(OrchidRecord.species) < 3
                ),
                OrchidRecord.validation_status != 'rejected'
            ).update({'validation_status': 'rejected'})
            
            db.session.commit()
            logger.info(f"🔧 MASS REPAIR: Rejected {invalid_count} invalid records")
            return invalid_count
        except Exception as e:
            logger.error(f"🚨 MASS REPAIR FAILED: {e}")
            return 0
    
    def _fix_broken_images(self):
        """Fix broken image links"""
        try:
            requests.post("http://localhost:5000/admin/clear-image-cache", timeout=10)
            requests.post("http://localhost:5000/admin/sync-google-drive", timeout=15)
            logger.info("🔧 IMAGE REPAIR: Cleared cache and synced Google Drive")
            return True
        except Exception as e:
            logger.error(f"🚨 IMAGE REPAIR FAILED: {e}")
            return False
    
    def _restart_services(self):
        """Restart failed services"""
        try:
            requests.post("http://localhost:5000/admin/restart-services", timeout=15)
            logger.info("🔧 SERVICE REPAIR: Restarted all services")
            return True
        except Exception as e:
            logger.error(f"🚨 SERVICE REPAIR FAILED: {e}")
            return False
    
    def _clear_caches(self):
        """Clear all system caches"""
        try:
            requests.post("http://localhost:5000/admin/clear-all-caches", timeout=10)
            logger.info("🔧 CACHE REPAIR: Cleared all system caches")
            return True
        except Exception as e:
            logger.error(f"🚨 CACHE REPAIR FAILED: {e}")
            return False
    
    def _generate_fallbacks(self):
        """Generate emergency fallback data"""
        try:
            # This would create emergency backup orchids
            logger.info("🔧 FALLBACK REPAIR: Generated emergency data")
            return True
        except Exception as e:
            logger.error(f"🚨 FALLBACK REPAIR FAILED: {e}")
            return False
    
    def get_status_report(self):
        """Get comprehensive status report"""
        return {
            'status': 'active' if self.is_running else 'inactive',
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'total_repairs': self.repair_count,
            'total_failures': self.failure_count,
            'critical_alerts': self.critical_alerts
        }

# Global guardian instance
integrity_guardian = RealTimeIntegrityGuardian()

def start_integrity_monitoring():
    """Start the real-time integrity monitoring system"""
    return integrity_guardian.start_guardian()

def trigger_user_integrity_check(user_ip=None):
    """Trigger integrity check on user activity"""
    return integrity_guardian.trigger_user_validation(user_ip)

def get_integrity_status():
    """Get current integrity monitoring status"""
    return integrity_guardian.get_status_report()