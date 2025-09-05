#!/usr/bin/env python3
"""
Vigilant Database and Image Monitor
Continuous monitoring with 30-second checks and automatic recovery
"""

import os
import logging
import time
import threading
import shutil
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
import requests
import json
import sqlite3
from pathlib import Path

from models import OrchidRecord, db
from app import app

logger = logging.getLogger(__name__)

class VigilantMonitor:
    """Ultra-vigilant monitoring system for database and images"""
    
    def __init__(self):
        self.is_running = False
        self.check_interval = 30  # 30 seconds
        self.backup_interval = 300  # 5 minutes
        self.last_backup = None
        self.last_image_check = None
        self.connection_failures = 0
        self.image_failures = 0
        
        # Stats tracking
        self.stats = {
            'total_checks': 0,
            'database_issues': 0,
            'image_issues': 0,
            'connection_resets': 0,
            'backups_created': 0,
            'last_check': None,
            'uptime_start': datetime.now()
        }
        
        # Create backup directory
        self.backup_dir = Path('database_backups')
        self.backup_dir.mkdir(exist_ok=True)
        
    def start_vigilant_monitoring(self):
        """Start ultra-vigilant monitoring"""
        if self.is_running:
            logger.warning("Vigilant monitoring already running")
            return False
            
        self.is_running = True
        logger.info("🚨 STARTING VIGILANT MONITOR - 30-second checks")
        logger.info("📊 Monitoring: Database health, Image display, Connection stability")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._vigilant_loop, daemon=True)
        monitor_thread.start()
        
        return True
    
    def stop_monitoring(self):
        """Stop vigilant monitoring"""
        self.is_running = False
        logger.info("⏹️ Stopping vigilant monitoring")
    
    def _vigilant_loop(self):
        """Main vigilant monitoring loop"""
        while self.is_running:
            try:
                current_time = datetime.now()
                self.stats['total_checks'] += 1
                self.stats['last_check'] = current_time
                
                logger.info(f"🔍 VIGILANT CHECK #{self.stats['total_checks']} - {current_time.strftime('%H:%M:%S')}")
                
                # 1. Database Health Check
                db_healthy = self._check_database_health()
                
                # 2. Image Display Verification
                images_working = self._verify_image_display()
                
                # 3. Connection Stability Check
                connections_stable = self._check_connection_stability()
                
                # 4. Auto-backup if needed
                self._auto_backup_database()
                
                # 5. Report status
                self._report_vigilant_status(db_healthy, images_working, connections_stable)
                
                # 6. Sleep for 30 seconds
                time.sleep(self.check_interval)
                
            except Exception as e:
                logger.error(f"❌ VIGILANT MONITOR ERROR: {e}")
                time.sleep(10)  # Brief pause on error
    
    def _check_database_health(self) -> bool:
        """Check database connection and integrity"""
        try:
            with app.app_context():
                # Test basic query
                orchid_count = OrchidRecord.query.count()
                
                # Test database write capability (fix SQL syntax)
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                
                logger.info(f"✅ DB Health: {orchid_count} orchids, connection stable")
                return True
                
        except Exception as e:
            logger.error(f"❌ DATABASE ISSUE: {e}")
            self.stats['database_issues'] += 1
            self._reinitialize_database_connection()
            return False
    
    def _verify_image_display(self) -> bool:
        """Verify that REAL GALLERY images are loading correctly"""
        try:
            # Test the actual gallery/recent additions that users see
            response = requests.get('http://localhost:5000/api/recent-orchids', timeout=15)
            if response.status_code != 200:
                logger.error(f"❌ Gallery API failed: {response.status_code}")
                self.stats['image_issues'] += 1
                return False
            
            recent_orchids = response.json()
            if not recent_orchids or len(recent_orchids) == 0:
                logger.error("❌ No recent orchids found in gallery")
                self.stats['image_issues'] += 1
                return False
            
            # PRODUCTION-READY: Prioritize Google Drive images for reliable testing
            google_drive_orchids = [o for o in recent_orchids if o.get('google_drive_id')]
            external_orchids = [o for o in recent_orchids if not o.get('google_drive_id') and o.get('photo_url')]
            
            # Test Google Drive images first (production-ready), then externals for monitoring
            test_orchids = google_drive_orchids[:2] + external_orchids[:1]
            test_count = min(3, len(test_orchids))
            working_images = 0
            
            logger.info(f"🔍 Testing {len(google_drive_orchids)} Google Drive + {len(external_orchids)} external images")
            
            for orchid in test_orchids[:test_count]:
                try:
                    if orchid.get('google_drive_id'):
                        # Test Google Drive image
                        img_response = requests.get(f"http://localhost:5000/api/drive-photo/{orchid['google_drive_id']}", timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            working_images += 1
                        else:
                            logger.warning(f"⚠️ Failed to load image for orchid {orchid.get('id', 'unknown')}: {img_response.status_code}")
                    elif orchid.get('photo_url'):
                        # Test image proxy (what users actually see)
                        from urllib.parse import quote_plus
                        proxy_url = f"http://localhost:5000/api/proxy-image?url={quote_plus(orchid['photo_url'])}"
                        img_response = requests.get(proxy_url, timeout=10)
                        if img_response.status_code == 200 and len(img_response.content) > 1000:
                            working_images += 1
                        else:
                            logger.warning(f"⚠️ Failed to load photo URL for orchid {orchid.get('id', 'unknown')}: {img_response.status_code}")
                    else:
                        logger.warning(f"⚠️ Orchid {orchid.get('id', 'unknown')} has no image source")
                except Exception as e:
                    logger.warning(f"⚠️ Error testing orchid image: {e}")
            
            success_rate = (working_images / test_count) * 100 if test_count > 0 else 0
            
            if success_rate >= 70:  # At least 70% of gallery images working
                logger.info(f"✅ REAL Gallery Images: {success_rate:.0f}% working ({working_images}/{test_count})")
                return True
            else:
                logger.error(f"❌ REAL Gallery Images: Only {success_rate:.0f}% working ({working_images}/{test_count}) - USERS CAN'T SEE PHOTOS!")
                self.stats['image_issues'] += 1
                self._reinitialize_image_connections()
                return False
                
        except Exception as e:
            logger.error(f"❌ GALLERY IMAGE CHECK FAILED: {e}")
            self.stats['image_issues'] += 1
            return False
    
    def _check_connection_stability(self) -> bool:
        """Check overall connection stability"""
        try:
            # Test internal routes
            response = requests.get('http://localhost:5000/', timeout=10)
            if response.status_code == 200:
                logger.info("✅ Connections: Web server responsive")
                self.connection_failures = 0
                return True
            else:
                self.connection_failures += 1
                logger.warning(f"⚠️ Connections: Server returned {response.status_code}")
                return False
                
        except Exception as e:
            self.connection_failures += 1
            logger.error(f"❌ CONNECTION FAILED: {e}")
            
            if self.connection_failures >= 3:
                self._emergency_connection_reset()
            
            return False
    
    def _reinitialize_database_connection(self):
        """Reinitialize database connection"""
        try:
            logger.info("🔄 Reinitializing database connection...")
            
            with app.app_context():
                db.session.close()
                db.session.remove()
                # Reconnect (fix SQL syntax)
                from sqlalchemy import text
                db.session.execute(text("SELECT 1"))
                db.session.commit()
                
            self.stats['connection_resets'] += 1
            logger.info("✅ Database connection reinitialized")
            
        except Exception as e:
            logger.error(f"❌ Failed to reinitialize database: {e}")
    
    def _reinitialize_image_connections(self):
        """Reinitialize image serving connections"""
        try:
            logger.info("🔄 Reinitializing image connections...")
            
            # Clear any cached connections
            requests.Session().close()
            
            # Test image route again
            response = requests.get('http://localhost:5000/api/drive-photo/185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I', timeout=10)
            
            if response.status_code == 200:
                logger.info("✅ Image connections reinitialized")
            else:
                logger.warning(f"⚠️ Image reinit partial: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Failed to reinitialize images: {e}")
    
    def _emergency_connection_reset(self):
        """Emergency connection reset when failures accumulate"""
        logger.error("🚨 EMERGENCY: Multiple connection failures - resetting all connections")
        
        try:
            # Reset database
            self._reinitialize_database_connection()
            
            # Reset image connections
            self._reinitialize_image_connections()
            
            # Reset failure counter
            self.connection_failures = 0
            
            logger.info("✅ Emergency connection reset completed")
            
        except Exception as e:
            logger.error(f"❌ EMERGENCY RESET FAILED: {e}")
    
    def _auto_backup_database(self):
        """Automatically backup database every 5 minutes"""
        current_time = datetime.now()
        
        if (self.last_backup is None or 
            current_time - self.last_backup > timedelta(seconds=self.backup_interval)):
            
            self._create_database_backup()
            self.last_backup = current_time
    
    def _create_database_backup(self):
        """Create a timestamped database backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"orchid_db_backup_{timestamp}.db"
            backup_path = self.backup_dir / backup_filename
            
            # Get database path
            database_url = os.environ.get('DATABASE_URL', 'sqlite:///orchid_continuum.db')
            
            if database_url.startswith('sqlite:///'):
                source_db = database_url.replace('sqlite:///', '')
                
                # Copy database file
                shutil.copy2(source_db, backup_path)
                
                # Verify backup
                if backup_path.exists() and backup_path.stat().st_size > 1000:
                    self.stats['backups_created'] += 1
                    logger.info(f"✅ Database backup created: {backup_filename}")
                    
                    # Clean old backups (keep last 10)
                    self._cleanup_old_backups()
                else:
                    logger.error("❌ Backup verification failed")
            else:
                logger.info("ℹ️ PostgreSQL backup requires pg_dump")
                
        except Exception as e:
            logger.error(f"❌ Backup failed: {e}")
    
    def _cleanup_old_backups(self):
        """Keep only the 10 most recent backups"""
        try:
            backup_files = sorted(self.backup_dir.glob('orchid_db_backup_*.db'))
            
            if len(backup_files) > 10:
                for old_backup in backup_files[:-10]:
                    old_backup.unlink()
                    logger.info(f"🗑️ Cleaned old backup: {old_backup.name}")
                    
        except Exception as e:
            logger.error(f"❌ Backup cleanup failed: {e}")
    
    def _report_vigilant_status(self, db_healthy: bool, images_working: bool, connections_stable: bool):
        """Report current vigilant monitoring status"""
        status_icons = {
            True: "✅",
            False: "❌"
        }
        
        uptime = datetime.now() - self.stats['uptime_start']
        
        logger.info(f"📊 VIGILANT STATUS: DB {status_icons[db_healthy]} | Images {status_icons[images_working]} | Conn {status_icons[connections_stable]} | Uptime: {str(uptime).split('.')[0]}")
    
    def get_monitor_stats(self) -> Dict[str, Any]:
        """Get current monitoring statistics"""
        uptime = datetime.now() - self.stats['uptime_start']
        
        return {
            'is_running': self.is_running,
            'total_checks': self.stats['total_checks'],
            'database_issues': self.stats['database_issues'],
            'image_issues': self.stats['image_issues'],
            'connection_resets': self.stats['connection_resets'],
            'backups_created': self.stats['backups_created'],
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0],
            'last_check': self.stats['last_check'].strftime('%H:%M:%S') if self.stats['last_check'] else 'Never',
            'connection_failures': self.connection_failures,
            'check_interval': self.check_interval,
            'backup_interval': self.backup_interval
        }
    
    def force_backup(self) -> str:
        """Force immediate database backup"""
        try:
            self._create_database_backup()
            return "Backup created successfully"
        except Exception as e:
            return f"Backup failed: {e}"
    
    def get_backup_download_url(self) -> str:
        """Get URL for latest database backup"""
        try:
            backup_files = sorted(self.backup_dir.glob('orchid_db_backup_*.db'))
            
            if backup_files:
                latest_backup = backup_files[-1]
                return f"/admin/download-backup/{latest_backup.name}"
            else:
                return ""
                
        except Exception as e:
            logger.error(f"Error getting backup URL: {e}")
            return ""

# Global vigilant monitor instance
vigilant_monitor = VigilantMonitor()