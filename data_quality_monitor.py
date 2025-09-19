#!/usr/bin/env python3
"""
Real-time Data Quality Monitor
Continuous monitoring and alerting for orchid data quality issues
"""

import time
import logging
from datetime import datetime, timedelta
from threading import Thread
from orchid_data_quality_system import quality_system

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataQualityMonitor:
    """Real-time monitoring system for data quality"""
    
    def __init__(self):
        self.monitoring = False
        self.check_interval = 300  # 5 minutes
        self.quality_threshold = 85  # Minimum acceptable quality score
        self.last_quality_score = None
        
    def start_monitoring(self):
        """Start continuous monitoring"""
        self.monitoring = True
        monitor_thread = Thread(target=self._monitor_loop, daemon=True)
        monitor_thread.start()
        logger.info("🔍 Data quality monitoring started")
        
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        logger.info("⏹️ Data quality monitoring stopped")
        
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            try:
                # Check current quality
                status = quality_system.monitor_quality_changes()
                current_score = status['quality_score']
                
                # Alert on quality degradation
                if self.last_quality_score is not None:
                    if current_score < self.last_quality_score - 5:
                        logger.warning(f"🚨 QUALITY ALERT: Score dropped from {self.last_quality_score}% to {current_score}%")
                
                # Alert on low quality
                if current_score < self.quality_threshold:
                    logger.error(f"❌ CRITICAL: Data quality at {current_score}% (threshold: {self.quality_threshold}%)")
                    
                    # Auto-correct if quality is very low
                    if current_score < 70:
                        logger.info("🔧 Auto-correcting critical quality issues...")
                        corrections = quality_system.auto_correct_database(dry_run=False)
                        if corrections:
                            logger.info(f"✅ Applied {len(corrections)} emergency corrections")
                
                self.last_quality_score = current_score
                
                # Log status
                if status['needs_attention']:
                    logger.warning(f"⚠️ Quality needs attention: {current_score}%")
                else:
                    logger.info(f"✅ Quality OK: {current_score}%")
                    
            except Exception as e:
                logger.error(f"❌ Monitoring error: {e}")
                
            time.sleep(self.check_interval)

# Global monitor instance
data_monitor = DataQualityMonitor()

def start_quality_monitoring():
    """Start the quality monitoring system"""
    data_monitor.start_monitoring()

def stop_quality_monitoring():
    """Stop the quality monitoring system"""
    data_monitor.stop_monitoring()

if __name__ == "__main__":
    # Start monitoring when run directly
    start_quality_monitoring()
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_quality_monitoring()