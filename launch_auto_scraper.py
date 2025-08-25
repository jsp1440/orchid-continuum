#!/usr/bin/env python3
"""
LAUNCH AUTO SCRAPER - Starts the complete auto-reconfiguring scraper system
Integrates Orchids.com, Ecuagenera, Andy's Orchids with existing scrapers
Reports every minute, reconfigures every 2 minutes
"""

import threading
import time
from auto_reconfiguring_scraper import AutoReconfiguringScraperManager
from multi_site_scraper_system import MultiSiteScraperSystem
from minute_progress_reporter import MinuteProgressReporter

def main():
    print("🚀 LAUNCHING COMPLETE AUTO-SCRAPING SYSTEM")
    print("=" * 60)
    print("🎯 Target: 200,000 orchid photos")
    print("⏰ Auto-reconfigures every 2 minutes")
    print("📊 Progress reports every 60 seconds")
    print("🔧 Conflict detection and flagging enabled")
    print()
    
    print("📋 INTEGRATED SCRAPERS:")
    print("  🌟 Ron Parsons (flowershots.net)")
    print("  🛒 Orchids.com (premium retailer)")
    print("  🌿 Ecuagenera.com (Ecuador specialists)")
    print("  🌺 Andy's Orchids (species specialists)")
    print("  📚 Baker Collection (orchidspecies.com)")
    print("  🌐 Internet Orchid Species")
    print()
    
    # Initialize systems
    auto_scraper = AutoReconfiguringScraperManager()
    multi_site_scraper = MultiSiteScraperSystem()
    progress_reporter = MinuteProgressReporter(target=200000)
    
    print("✅ All systems initialized!")
    print("🚀 Starting continuous operation...")
    print()
    
    try:
        # Start progress reporter in background
        progress_thread = threading.Thread(
            target=progress_reporter.run_continuous_reporting,
            daemon=True
        )
        progress_thread.start()
        
        # Start multi-site scraper
        multi_site_thread = threading.Thread(
            target=multi_site_scraper.run_continuous_collection,
            daemon=True
        )
        multi_site_thread.start()
        
        # Run auto-reconfiguring scraper in main thread
        auto_scraper.run_continuous_scraping()
        
    except KeyboardInterrupt:
        print("\n⏹️  Stopping auto-scraper system...")
        auto_scraper.stop()
        print("✅ System stopped gracefully")

if __name__ == "__main__":
    main()