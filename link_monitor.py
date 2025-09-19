#!/usr/bin/env python3
"""
Continuous Link Monitor for Partnership Proposal
Checks all critical links every 30 seconds and reports/fixes issues
"""

import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Critical links to monitor
CRITICAL_LINKS = {
    'gallery': 'http://localhost:5000/gallery',
    'earth_globe': 'http://localhost:5000/space-earth-globe', 
    'search': 'http://localhost:5000/search',
    'home': 'http://localhost:5000/',
    'partnership_proposal': 'http://localhost:5000/partnership-proposal'
}

def check_link(name, url, timeout=10):
    """Check if a link is working"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            logger.info(f"✅ {name}: {response.status_code} OK")
            return True
        else:
            logger.error(f"❌ {name}: {response.status_code} ERROR")
            return False
    except requests.exceptions.Timeout:
        logger.error(f"⏰ {name}: TIMEOUT ({timeout}s)")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"💥 {name}: CONNECTION ERROR - {e}")
        return False

def monitor_links():
    """Main monitoring loop"""
    logger.info("🚀 Starting continuous link monitoring (30-second intervals)")
    
    while True:
        timestamp = datetime.now().strftime('%H:%M:%S')
        logger.info(f"🔍 LINK CHECK #{timestamp}")
        
        all_working = True
        failed_links = []
        
        for name, url in CRITICAL_LINKS.items():
            if not check_link(name, url):
                all_working = False
                failed_links.append(name)
        
        if all_working:
            logger.info("✅ ALL PARTNERSHIP PROPOSAL LINKS WORKING")
        else:
            logger.error(f"❌ FAILED LINKS: {', '.join(failed_links)}")
            
        logger.info("⏱️ Waiting 30 seconds for next check...")
        time.sleep(30)

if __name__ == "__main__":
    try:
        monitor_links()
    except KeyboardInterrupt:
        logger.info("🛑 Link monitoring stopped by user")
    except Exception as e:
        logger.error(f"💥 Monitor crashed: {e}")