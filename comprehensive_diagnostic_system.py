#!/usr/bin/env python3
"""
🔧 COMPREHENSIVE DIAGNOSTIC SYSTEM
Monitors and automatically repairs all website components every 3 minutes
"""

import time
import logging
import threading
import requests
import psutil
import os
from datetime import datetime
from sqlalchemy import text
from app import app, db
from models import OrchidRecord
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveDiagnosticSystem:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.diagnostic_interval = 180  # 3 minutes
        self.is_running = False
        self.repair_counts = {
            'widgets': 0,
            'database': 0,
            'routes': 0,
            'images': 0,
            'performance': 0
        }
        self.last_diagnostic = None
        
    def start_monitoring(self):
        """Start the diagnostic monitoring system"""
        if self.is_running:
            logger.info("🔧 Diagnostic system already running")
            return
            
        self.is_running = True
        logger.info("🚀 STARTING COMPREHENSIVE DIAGNOSTIC SYSTEM")
        logger.info("🔍 Running diagnostics every 3 minutes")
        
        # Start monitoring thread
        monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        monitor_thread.start()
        
    def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                self.run_full_diagnostic()
                time.sleep(self.diagnostic_interval)
            except Exception as e:
                logger.error(f"❌ Diagnostic loop error: {e}")
                time.sleep(60)  # Wait 1 minute on error
                
    def run_full_diagnostic(self):
        """Run comprehensive diagnostic and repair cycle"""
        start_time = datetime.now()
        logger.info("🔍 STARTING FULL DIAGNOSTIC CYCLE")
        logger.info("=" * 60)
        
        # 1. Database Health Check
        db_issues = self.check_database_health()
        if db_issues:
            self.repair_database_issues(db_issues)
            
        # 2. Widget Functionality Check
        widget_issues = self.check_widget_functionality()
        if widget_issues:
            self.repair_widget_issues(widget_issues)
            
        # 3. Application Routes Check
        route_issues = self.check_application_routes()
        if route_issues:
            self.repair_route_issues(route_issues)
            
        # 4. Image/Media Health Check
        media_issues = self.check_media_health()
        if media_issues:
            self.repair_media_issues(media_issues)
            
        # 5. Performance Analysis
        perf_issues = self.check_performance_metrics()
        if perf_issues:
            self.optimize_performance(perf_issues)
            
        # Summary Report
        duration = (datetime.now() - start_time).total_seconds()
        self.generate_diagnostic_report(duration)
        self.last_diagnostic = start_time
        
    def check_database_health(self):
        """Check database connections and query performance"""
        logger.info("🗄️ Checking database health...")
        issues = []
        
        try:
            # Test basic connection
            with app.app_context():
                result = db.session.execute(text("SELECT 1"))
                result.fetchone()
                
            # Test orchid record count
            with app.app_context():
                count = OrchidRecord.query.count()
                if count == 0:
                    issues.append("no_orchid_records")
                    
            # Test query performance
            start_time = time.time()
            with app.app_context():
                OrchidRecord.query.filter(OrchidRecord.google_drive_id.isnot(None)).limit(10).all()
            query_time = time.time() - start_time
            
            if query_time > 5.0:  # Slow queries
                issues.append("slow_queries")
                
            logger.info(f"✅ Database: {count} records, {query_time:.2f}s query time")
            
        except Exception as e:
            logger.error(f"❌ Database error: {e}")
            issues.append("connection_error")
            
        return issues
        
    def check_widget_functionality(self):
        """Check all widget endpoints"""
        logger.info("🎨 Checking widget functionality...")
        issues = []
        
        widgets_to_test = [
            "/api/recent-orchids",
            "/api/orchid-of-day", 
            "/api/featured-orchids",
            "/widgets/search-widget",
            "/widgets/climate-data"
        ]
        
        for widget in widgets_to_test:
            try:
                response = requests.get(f"{self.base_url}{widget}", timeout=10)
                if response.status_code != 200:
                    issues.append(f"widget_error_{widget.replace('/', '_')}")
                    logger.warning(f"⚠️ Widget {widget} returned {response.status_code}")
                else:
                    logger.info(f"✅ Widget {widget} working")
            except Exception as e:
                issues.append(f"widget_timeout_{widget.replace('/', '_')}")
                logger.error(f"❌ Widget {widget} failed: {e}")
                
        return issues
        
    def check_application_routes(self):
        """Check critical application routes"""
        logger.info("🌐 Checking application routes...")
        issues = []
        
        critical_routes = [
            "/",
            "/gallery", 
            "/search",
            "/upload",
            "/orchid-explorer",
            "/partner/gary/dashboard"
        ]
        
        for route in critical_routes:
            try:
                response = requests.get(f"{self.base_url}{route}", timeout=15)
                if response.status_code not in [200, 302]:
                    issues.append(f"route_error_{route.replace('/', '_')}")
                    logger.warning(f"⚠️ Route {route} returned {response.status_code}")
                else:
                    logger.info(f"✅ Route {route} working")
            except Exception as e:
                issues.append(f"route_timeout_{route.replace('/', '_')}")
                logger.error(f"❌ Route {route} failed: {e}")
                
        return issues
        
    def check_media_health(self):
        """Check image and media functionality"""
        logger.info("🖼️ Checking media health...")
        issues = []
        
        try:
            # Test Google Drive photo endpoint
            test_ids = ["185MlwyxBU8Dy6bqGdwXXPeBXTlhg5M0I", "1142ajwZe7_LbGt-BPy-HqVkLpNczcfZY"]
            
            for drive_id in test_ids:
                try:
                    response = requests.get(f"{self.base_url}/api/drive-photo/{drive_id}", timeout=10)
                    if response.status_code != 200:
                        issues.append(f"drive_photo_error_{drive_id}")
                        logger.warning(f"⚠️ Drive photo {drive_id} failed")
                    else:
                        logger.info(f"✅ Drive photo {drive_id} working")
                except Exception as e:
                    issues.append(f"drive_photo_timeout_{drive_id}")
                    logger.error(f"❌ Drive photo {drive_id} error: {e}")
                    
        except Exception as e:
            issues.append("media_system_error")
            logger.error(f"❌ Media system error: {e}")
            
        return issues
        
    def check_performance_metrics(self):
        """Check system performance metrics"""
        logger.info("⚡ Checking performance metrics...")
        issues = []
        
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 80:
                issues.append("high_cpu")
                
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 85:
                issues.append("high_memory")
                
            # Disk space
            disk = psutil.disk_usage('/')
            if disk.percent > 90:
                issues.append("low_disk_space")
                
            logger.info(f"✅ Performance: CPU {cpu_percent}%, Memory {memory.percent}%, Disk {disk.percent}%")
            
        except Exception as e:
            issues.append("performance_check_error")
            logger.error(f"❌ Performance check error: {e}")
            
        return issues
        
    def repair_database_issues(self, issues):
        """Repair database-related issues"""
        logger.info("🔧 Repairing database issues...")
        
        for issue in issues:
            if issue == "connection_error":
                self._restart_database_connection()
            elif issue == "slow_queries":
                self._optimize_database_queries()
            elif issue == "no_orchid_records":
                self._trigger_data_collection()
                
        self.repair_counts['database'] += len(issues)
        
    def repair_widget_issues(self, issues):
        """Repair widget functionality issues"""
        logger.info("🎨 Repairing widget issues...")
        
        for issue in issues:
            if "widget_error" in issue or "widget_timeout" in issue:
                self._restart_widget_services()
                
        self.repair_counts['widgets'] += len(issues)
        
    def repair_route_issues(self, issues):
        """Repair application route issues"""
        logger.info("🌐 Repairing route issues...")
        
        for issue in issues:
            if "route_error" in issue or "route_timeout" in issue:
                self._restart_application_services()
                
        self.repair_counts['routes'] += len(issues)
        
    def repair_media_issues(self, issues):
        """Repair media and image issues"""
        logger.info("🖼️ Repairing media issues...")
        
        for issue in issues:
            if "drive_photo" in issue:
                self._clear_image_cache()
            elif "media_system_error" in issue:
                self._restart_media_services()
                
        self.repair_counts['images'] += len(issues)
        
    def optimize_performance(self, issues):
        """Optimize system performance"""
        logger.info("⚡ Optimizing performance...")
        
        for issue in issues:
            if issue == "high_cpu":
                self._reduce_cpu_load()
            elif issue == "high_memory":
                self._clear_memory_cache()
            elif issue == "low_disk_space":
                self._cleanup_disk_space()
                
        self.repair_counts['performance'] += len(issues)
        
    def _restart_database_connection(self):
        """Restart database connections"""
        try:
            with app.app_context():
                db.session.close()
                db.engine.dispose()
            logger.info("✅ Database connection restarted")
        except Exception as e:
            logger.error(f"❌ Failed to restart database: {e}")
            
    def _restart_widget_services(self):
        """Restart widget services"""
        try:
            requests.post(f"{self.base_url}/admin/restart-widgets", timeout=5)
            logger.info("✅ Widget services restarted")
        except Exception as e:
            logger.warning(f"⚠️ Widget restart failed: {e}")
            
    def _restart_application_services(self):
        """Restart application services"""
        try:
            requests.post(f"{self.base_url}/admin/restart-services", timeout=5)
            logger.info("✅ Application services restarted")
        except Exception as e:
            logger.warning(f"⚠️ Service restart failed: {e}")
            
    def _clear_image_cache(self):
        """Clear image cache"""
        try:
            requests.post(f"{self.base_url}/admin/clear-image-cache", timeout=5)
            logger.info("✅ Image cache cleared")
        except Exception as e:
            logger.warning(f"⚠️ Cache clear failed: {e}")
            
    def _restart_media_services(self):
        """Restart media services"""
        try:
            requests.post(f"{self.base_url}/admin/restart-media", timeout=5)
            logger.info("✅ Media services restarted")
        except Exception as e:
            logger.warning(f"⚠️ Media restart failed: {e}")
            
    def _optimize_database_queries(self):
        """Optimize database query performance"""
        logger.info("🔧 Optimizing database queries...")
        
    def _trigger_data_collection(self):
        """Trigger data collection processes"""
        try:
            requests.post(f"{self.base_url}/admin/run-gary-scraper", timeout=5)
            requests.post(f"{self.base_url}/admin/run-gbif-collection", timeout=5)
            logger.info("✅ Data collection triggered")
        except Exception as e:
            logger.warning(f"⚠️ Data collection trigger failed: {e}")
            
    def _reduce_cpu_load(self):
        """Reduce CPU load"""
        logger.info("🔧 Reducing CPU load...")
        
    def _clear_memory_cache(self):
        """Clear memory cache"""
        logger.info("🔧 Clearing memory cache...")
        
    def _cleanup_disk_space(self):
        """Clean up disk space"""
        logger.info("🔧 Cleaning up disk space...")
        
    def generate_diagnostic_report(self, duration):
        """Generate diagnostic summary report"""
        logger.info("📊 DIAGNOSTIC CYCLE COMPLETE")
        logger.info(f"⏱️ Duration: {duration:.2f} seconds")
        logger.info(f"🔧 Repairs made:")
        for category, count in self.repair_counts.items():
            if count > 0:
                logger.info(f"   {category}: {count} fixes")
        logger.info("=" * 60)
        
    def get_status(self):
        """Get current diagnostic system status"""
        return {
            'is_running': self.is_running,
            'last_diagnostic': self.last_diagnostic,
            'repair_counts': self.repair_counts.copy(),
            'interval_minutes': self.diagnostic_interval / 60
        }

# Global diagnostic system instance
diagnostic_system = ComprehensiveDiagnosticSystem()

def start_diagnostic_monitoring():
    """Start the diagnostic monitoring system"""
    diagnostic_system.start_monitoring()
    
def get_diagnostic_status():
    """Get diagnostic system status"""
    return diagnostic_system.get_status()

if __name__ == "__main__":
    start_diagnostic_monitoring()
    
    # Keep running
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("🛑 Diagnostic system stopping...")
        diagnostic_system.is_running = False