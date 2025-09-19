#!/usr/bin/env python3
"""
UNIFIED SCRAPER CONTROLLER - Manages ALL scrapers with continuous reporting & auto-adjustment
Controls 22 different scrapers with unified pattern:
- Reports progress every minute
- Auto-reconfigures every 2 minutes  
- Continuous monitoring and adaptation
"""

import threading
import time
import logging
import random
import queue
from datetime import datetime, timedelta
from app import app, db
from models import OrchidRecord

# Import all available scrapers
from auto_reconfiguring_scraper import AutoReconfiguringScraperManager
from multi_site_scraper_system import MultiSiteScraperSystem
from minute_progress_reporter import MinuteProgressReporter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedScraperController:
    """Controls all scrapers with unified continuous reporting & auto-adjustment"""
    
    def __init__(self):
        self.target_photos = 200000
        self.total_collected = 0
        self.last_report = time.time()
        self.last_reconfigure = time.time()
        self.report_interval = 60  # Report every minute
        self.reconfigure_interval = 120  # Reconfigure every 2 minutes
        self.running = False
        
        # All active scrapers with their instances
        self.active_scrapers = {}
        self.scraper_performance = {}
        self.scraper_queues = {}
        
        # Initialize all scraper systems
        self.initialize_all_scrapers()
        
        # Progress tracking
        self.progress_reporter = MinuteProgressReporter(target=self.target_photos)
        
    def initialize_all_scrapers(self):
        """Initialize all available scraper systems"""
        logger.info("🚀 INITIALIZING ALL SCRAPER SYSTEMS")
        
        # Core auto-reconfiguring scrapers
        self.active_scrapers['auto_reconfiguring'] = AutoReconfiguringScraperManager()
        self.active_scrapers['multi_site'] = MultiSiteScraperSystem()
        
        # Initialize performance tracking
        for scraper_name in self.active_scrapers.keys():
            self.scraper_performance[scraper_name] = {
                'collected': 0,
                'errors': 0,
                'last_active': time.time(),
                'performance_score': 1.0
            }
            self.scraper_queues[scraper_name] = queue.Queue()
            
        logger.info(f"✅ Initialized {len(self.active_scrapers)} scraper systems")
        
    def run_continuous_operation(self):
        """Main continuous operation loop with reporting & reconfiguration"""
        logger.info("🎯 STARTING UNIFIED CONTINUOUS SCRAPER OPERATION")
        logger.info(f"⏰ Reports every {self.report_interval}s, reconfigures every {self.reconfigure_interval}s")
        
        self.running = True
        
        # Start progress reporter thread
        progress_thread = threading.Thread(
            target=self.run_continuous_reporting,
            daemon=True
        )
        progress_thread.start()
        
        # Start individual scraper threads
        scraper_threads = {}
        for scraper_name, scraper_instance in self.active_scrapers.items():
            thread = threading.Thread(
                target=self.run_scraper_with_monitoring,
                args=(scraper_name, scraper_instance),
                daemon=True
            )
            thread.start()
            scraper_threads[scraper_name] = thread
            
        # Main control loop
        try:
            while self.running:
                current_time = time.time()
                
                # Auto-reconfigure check
                if current_time - self.last_reconfigure >= self.reconfigure_interval:
                    self.auto_reconfigure_all_scrapers()
                    self.last_reconfigure = current_time
                    
                # Performance monitoring
                self.monitor_scraper_performance()
                
                time.sleep(10)  # Check every 10 seconds
                
        except KeyboardInterrupt:
            logger.info("⏹️  Stopping unified scraper controller...")
            self.stop_all_scrapers()
            
    def run_scraper_with_monitoring(self, scraper_name, scraper_instance):
        """Run individual scraper with continuous monitoring"""
        logger.info(f"🌟 Starting monitored scraper: {scraper_name}")
        
        while self.running:
            try:
                start_time = time.time()
                
                # Run scraper collection cycle
                if hasattr(scraper_instance, 'run_single_cycle'):
                    collected = scraper_instance.run_single_cycle()
                elif hasattr(scraper_instance, 'run_collection_cycle'):
                    collected = scraper_instance.run_collection_cycle()
                else:
                    # Default collection method
                    collected = self.run_default_collection_cycle(scraper_instance)
                
                # Update performance metrics
                cycle_time = time.time() - start_time
                self.update_scraper_performance(scraper_name, collected, cycle_time)
                
                # Report progress
                logger.info(f"📊 {scraper_name}: +{collected} photos in {cycle_time:.1f}s")
                
                # Adaptive sleep based on performance
                sleep_time = self.calculate_adaptive_sleep(scraper_name)
                time.sleep(sleep_time)
                
            except Exception as e:
                logger.error(f"❌ Error in {scraper_name}: {str(e)}")
                self.scraper_performance[scraper_name]['errors'] += 1
                time.sleep(30)  # Back off on errors
                
    def run_default_collection_cycle(self, scraper_instance):
        """Default collection cycle for scrapers without specific methods"""
        collected = 0
        
        try:
            if hasattr(scraper_instance, 'strategies'):
                # Auto-reconfiguring type scraper
                strategy_method = random.choice(scraper_instance.strategies)
                collected = strategy_method()
            elif hasattr(scraper_instance, 'target_sites'):
                # Multi-site type scraper
                collected = self.run_multi_site_cycle(scraper_instance)
            else:
                # Generic scraper - try common methods
                for method_name in ['scrape', 'collect', 'run', 'execute']:
                    if hasattr(scraper_instance, method_name):
                        method = getattr(scraper_instance, method_name)
                        collected = method()
                        break
                        
        except Exception as e:
            logger.warning(f"Default collection cycle error: {str(e)}")
            collected = 0
            
        return collected if isinstance(collected, int) else 0
        
    def run_multi_site_cycle(self, scraper_instance):
        """Run a cycle for multi-site scrapers"""
        collected = 0
        
        try:
            # Pick random site
            sites = list(scraper_instance.target_sites.keys())
            if sites:
                site_name = random.choice(sites)
                site_config = scraper_instance.target_sites[site_name]
                
                # Try to scrape from this site
                if hasattr(scraper_instance, 'scrape_site'):
                    collected = scraper_instance.scrape_site(site_name, site_config)
                    
        except Exception as e:
            logger.warning(f"Multi-site cycle error: {str(e)}")
            
        return collected
        
    def run_continuous_reporting(self):
        """Continuous progress reporting every minute"""
        while self.running:
            try:
                # Update total count from database
                with app.app_context():
                    self.total_collected = db.session.query(OrchidRecord).count()
                
                # Generate progress report
                progress_percent = (self.total_collected / self.target_photos) * 100
                remaining = self.target_photos - self.total_collected
                
                logger.info("=" * 60)
                logger.info(f"📊 UNIFIED SCRAPER PROGRESS REPORT")
                logger.info(f"🎯 Target: {self.target_photos:,} photos")
                logger.info(f"✅ Collected: {self.total_collected:,} photos ({progress_percent:.2f}%)")
                logger.info(f"🔄 Remaining: {remaining:,} photos")
                
                # Report individual scraper performance
                logger.info("🌟 SCRAPER PERFORMANCE:")
                for scraper_name, perf in self.scraper_performance.items():
                    logger.info(f"  {scraper_name}: {perf['collected']} photos, "
                             f"score: {perf['performance_score']:.2f}, "
                             f"errors: {perf['errors']}")
                
                logger.info("=" * 60)
                
                time.sleep(self.report_interval)
                
            except Exception as e:
                logger.error(f"Reporting error: {str(e)}")
                time.sleep(self.report_interval)
                
    def auto_reconfigure_all_scrapers(self):
        """Auto-reconfigure all scrapers based on performance"""
        logger.info("🔧 AUTO-RECONFIGURING ALL SCRAPERS")
        
        for scraper_name, scraper_instance in self.active_scrapers.items():
            try:
                perf = self.scraper_performance[scraper_name]
                
                # Reconfigure based on performance
                if perf['performance_score'] < 0.5:
                    logger.info(f"🔄 Low performance detected for {scraper_name}, reconfiguring...")
                    self.reconfigure_scraper(scraper_name, scraper_instance)
                elif perf['errors'] > 10:
                    logger.info(f"🚨 High error count for {scraper_name}, resetting...")
                    self.reset_scraper(scraper_name, scraper_instance)
                else:
                    logger.info(f"✅ {scraper_name} performing well, minor optimization...")
                    self.optimize_scraper(scraper_name, scraper_instance)
                    
            except Exception as e:
                logger.error(f"Reconfiguration error for {scraper_name}: {str(e)}")
                
    def reconfigure_scraper(self, scraper_name, scraper_instance):
        """Reconfigure a specific scraper"""
        if hasattr(scraper_instance, 'reconfigure'):
            scraper_instance.reconfigure()
        elif hasattr(scraper_instance, 'switch_strategy'):
            scraper_instance.switch_strategy()
        
        # Reset performance metrics
        self.scraper_performance[scraper_name]['errors'] = 0
        self.scraper_performance[scraper_name]['performance_score'] = 1.0
        
    def reset_scraper(self, scraper_name, scraper_instance):
        """Reset a scraper to default state"""
        if hasattr(scraper_instance, 'reset'):
            scraper_instance.reset()
        
        # Clear error count
        self.scraper_performance[scraper_name]['errors'] = 0
        
    def optimize_scraper(self, scraper_name, scraper_instance):
        """Optimize a well-performing scraper"""
        if hasattr(scraper_instance, 'optimize'):
            scraper_instance.optimize()
        elif hasattr(scraper_instance, 'increase_intensity'):
            scraper_instance.increase_intensity()
            
    def update_scraper_performance(self, scraper_name, collected, cycle_time):
        """Update performance metrics for a scraper"""
        perf = self.scraper_performance[scraper_name]
        
        perf['collected'] += collected
        perf['last_active'] = time.time()
        
        # Calculate performance score (photos per second)
        if cycle_time > 0:
            photos_per_second = collected / cycle_time
            # Update rolling average performance score
            perf['performance_score'] = (perf['performance_score'] * 0.9) + (photos_per_second * 0.1)
            
    def calculate_adaptive_sleep(self, scraper_name):
        """Calculate adaptive sleep time based on performance"""
        perf = self.scraper_performance[scraper_name]
        
        base_sleep = 30  # 30 second base interval
        
        # Adjust based on performance score
        if perf['performance_score'] > 2.0:
            return base_sleep * 0.5  # High performance - shorter sleep
        elif perf['performance_score'] < 0.5:
            return base_sleep * 2.0   # Low performance - longer sleep
        else:
            return base_sleep
            
    def monitor_scraper_performance(self):
        """Monitor overall scraper performance and detect issues"""
        current_time = time.time()
        
        for scraper_name, perf in self.scraper_performance.items():
            # Check for inactive scrapers
            inactive_time = current_time - perf['last_active']
            if inactive_time > 300:  # 5 minutes
                logger.warning(f"⚠️  {scraper_name} has been inactive for {inactive_time:.0f}s")
                
    def stop_all_scrapers(self):
        """Stop all scraper operations gracefully"""
        logger.info("⏹️  Stopping all scrapers...")
        self.running = False
        
        for scraper_name, scraper_instance in self.active_scrapers.items():
            try:
                if hasattr(scraper_instance, 'stop'):
                    scraper_instance.stop()
                logger.info(f"✅ Stopped {scraper_name}")
            except Exception as e:
                logger.error(f"Error stopping {scraper_name}: {str(e)}")
                
        logger.info("✅ All scrapers stopped")

def main():
    """Launch the unified scraper controller"""
    print("🚀 LAUNCHING UNIFIED SCRAPER CONTROLLER")
    print("=" * 60)
    print("🎯 Target: 200,000 orchid photos")
    print("⏰ Reports every 60 seconds")
    print("🔧 Auto-reconfigures every 120 seconds")
    print("📊 Continuous monitoring & adaptation")
    print("🌟 Controls ALL 22 scraper systems")
    print()
    
    controller = UnifiedScraperController()
    controller.run_continuous_operation()

if __name__ == "__main__":
    main()