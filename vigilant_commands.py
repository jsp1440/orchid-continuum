#!/usr/bin/env python3
"""
Vigilant Commands - Command-line tools for vigilant monitoring
Use these commands to ensure the system stays healthy
"""

import subprocess
import sys
import time
from pathlib import Path

def vigilant_start():
    """Start vigilant monitoring with all safeguards"""
    print("🚨 STARTING VIGILANT MODE")
    print("=" * 50)
    
    # 1. Start vigilant monitoring
    print("1. Starting vigilant monitor...")
    subprocess.run([sys.executable, "-c", 
        "from vigilant_monitor import vigilant_monitor; vigilant_monitor.start_vigilant_monitoring(); import time; time.sleep(60)"
    ])
    
    # 2. Start scraping dashboard
    print("2. Starting scraping dashboard...")
    subprocess.run([sys.executable, "-c",
        "from scraping_dashboard import scraping_dashboard; scraping_dashboard.start_methodical_scraping(); import time; time.sleep(60)"
    ])
    
    print("✅ VIGILANT MODE ACTIVATED")

def vigilant_backup():
    """Force immediate database backup"""
    print("💾 FORCING DATABASE BACKUP")
    subprocess.run([sys.executable, "-c",
        "from vigilant_monitor import vigilant_monitor; print(vigilant_monitor.force_backup())"
    ])

def vigilant_status():
    """Show vigilant monitoring status"""
    print("📊 VIGILANT MONITOR STATUS")
    print("=" * 30)
    subprocess.run([sys.executable, "-c",
        """
from vigilant_monitor import vigilant_monitor
from scraping_dashboard import scraping_dashboard
import json

vm_stats = vigilant_monitor.get_monitor_stats()
sd_stats = scraping_dashboard.get_dashboard_stats()

print(f"Monitor Running: {vm_stats['is_running']}")
print(f"Total Checks: {vm_stats['total_checks']}")
print(f"DB Issues: {vm_stats['database_issues']}")
print(f"Image Issues: {vm_stats['image_issues']}")
print(f"Backups Created: {vm_stats['backups_created']}")
print(f"Uptime: {vm_stats['uptime_formatted']}")
print()
print(f"Scraping Running: {sd_stats['is_running']}")
print(f"Total Scraped: {sd_stats['total_scraped']}")
print(f"Success Rate: {sd_stats['success_rate']}%")
print(f"Current Cycle: {sd_stats['current_cycle']}")
        """
    ])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""
🚨 VIGILANT MONITOR COMMANDS

Usage: python vigilant_commands.py <command>

Commands:
  start   - Start vigilant monitoring (30-second checks)
  backup  - Force immediate database backup
  status  - Show current monitoring status
  
Examples:
  python vigilant_commands.py start
  python vigilant_commands.py backup
  python vigilant_commands.py status
        """)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "start":
        vigilant_start()
    elif command == "backup":
        vigilant_backup()
    elif command == "status":
        vigilant_status()
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)