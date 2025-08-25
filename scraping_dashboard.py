#!/usr/bin/env python3
"""
Advanced Scraping Dashboard - Real-time monitoring and control
Methodical one-plant-at-a-time approach across all databases
"""

import logging
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import os

# Scraper imports with fallbacks
try:
    from gary_yong_gee_scraper import GaryYongGeeScraper
except ImportError:
    class GaryYongGeeScraper: 
        def scrape_single_orchid_page(self): return None

try:
    from roberta_fox_scraper import RobertaFoxScraper  
except ImportError:
    class RobertaFoxScraper:
        def scrape_single_orchid(self): return None

try:
    from international_orchid_scraper import InternationalOrchidScraper
except ImportError:
    class InternationalOrchidScraper:
        def scrape_single_species(self, source=None): return None

try:
    from advanced_orchid_scrapers import EcuageneraScraper, AndysOrchidsScraper
except ImportError:
    class EcuageneraScraper:
        def scrape_single_product(self): return None
    class AndysOrchidsScraper:
        def scrape_single_orchid(self): return None

try:
    from ron_parsons_scraper import RonParsonsScraper
except ImportError:
    class RonParsonsScraper:
        def scrape_single_image(self): return None

logger = logging.getLogger(__name__)

class ScrapingDashboard:
    """Advanced scraping dashboard with real-time monitoring"""
    
    def __init__(self):
        self.scrapers = {
            'gary_yong_gee': GaryYongGeeScraper(),
            'roberta_fox': RobertaFoxScraper(),
            'orchidspecies': InternationalOrchidScraper(),
            'singapore_botanic': InternationalOrchidScraper(),
            'kew_gardens': InternationalOrchidScraper(),
            'orchidwire': InternationalOrchidScraper(),
            'australian_terrestrial': InternationalOrchidScraper(),
            'ecuagenera': EcuageneraScraper(),
            'andys_orchids': AndysOrchidsScraper(),
            'ron_parsons': RonParsonsScraper()
        }
        
        self.stats = {
            'total_scraped': 0,
            'session_start': datetime.now(),
            'last_update': None,
            'current_scraper': None,
            'current_plant': None,
            'errors': 0,
            'successes': 0,
            'scraper_stats': {}
        }
        
        self.is_running = False
        self.current_cycle = 0
        self.reinitialize_interval = 9  # seconds
        
        # Initialize scraper stats
        for scraper_name in self.scrapers.keys():
            self.stats['scraper_stats'][scraper_name] = {
                'plants_found': 0,
                'images_collected': 0,
                'last_run': None,
                'status': 'idle',
                'errors': 0
            }
    
    def start_methodical_scraping(self):
        """Start methodical one-plant-at-a-time scraping"""
        if self.is_running:
            logger.warning("Scraping already in progress")
            return False
            
        self.is_running = True
        logger.info("🚀 Starting methodical scraping - one plant at a time")
        
        # Start in background thread
        scraping_thread = threading.Thread(target=self._run_methodical_scraping, daemon=True)
        scraping_thread.start()
        
        return True
    
    def stop_scraping(self):
        """Stop all scraping operations"""
        self.is_running = False
        logger.info("⏹️  Stopping all scraping operations")
    
    def _run_methodical_scraping(self):
        """Main methodical scraping loop"""
        scraper_names = list(self.scrapers.keys())
        scraper_index = 0
        
        while self.is_running:
            try:
                # Get current scraper
                current_scraper_name = scraper_names[scraper_index]
                scraper = self.scrapers[current_scraper_name]
                
                self.stats['current_scraper'] = current_scraper_name
                self.stats['scraper_stats'][current_scraper_name]['status'] = 'active'
                
                logger.info(f"🔍 Running {current_scraper_name} - Cycle {self.current_cycle + 1}")
                
                # Run single plant collection
                result = self._scrape_single_plant(scraper, current_scraper_name)
                
                if result['success']:
                    self.stats['successes'] += 1
                    self.stats['scraper_stats'][current_scraper_name]['plants_found'] += 1
                    self.stats['scraper_stats'][current_scraper_name]['images_collected'] += result.get('images', 0)
                    logger.info(f"✅ {current_scraper_name}: Found {result.get('images', 0)} images")
                else:
                    self.stats['errors'] += 1
                    self.stats['scraper_stats'][current_scraper_name]['errors'] += 1
                    logger.warning(f"❌ {current_scraper_name}: {result.get('error', 'Unknown error')}")
                
                # Update stats
                self.stats['scraper_stats'][current_scraper_name]['last_run'] = datetime.now()
                self.stats['scraper_stats'][current_scraper_name]['status'] = 'idle'
                self.stats['last_update'] = datetime.now()
                self.stats['total_scraped'] += 1
                
                # Move to next scraper
                scraper_index = (scraper_index + 1) % len(scraper_names)
                
                # If we've completed a full cycle through all scrapers
                if scraper_index == 0:
                    self.current_cycle += 1
                    logger.info(f"🔄 Completed cycle {self.current_cycle} - Reinitializing...")
                    time.sleep(self.reinitialize_interval)
                
                # Brief pause between individual scraper runs
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error in methodical scraping: {e}")
                time.sleep(5)
    
    def _scrape_single_plant(self, scraper, scraper_name: str) -> Dict[str, Any]:
        """Scrape a single plant from the given scraper"""
        try:
            result = {'success': False, 'images': 0, 'error': None}
            
            if scraper_name == 'gary_yong_gee':
                data = scraper.scrape_single_orchid_page()
                if data:
                    result = {'success': True, 'images': 1 if data.get('image_url') else 0}
                    
            elif scraper_name == 'roberta_fox':
                data = scraper.scrape_single_orchid()
                if data:
                    result = {'success': True, 'images': len(data.get('images', []))}
                    
            elif scraper_name in ['orchidspecies', 'singapore_botanic', 'kew_gardens', 'orchidwire', 'australian_terrestrial']:
                # Use international scraper for these sources
                data = scraper.scrape_single_species(source=scraper_name)
                if data:
                    result = {'success': True, 'images': 1 if data.get('image_url') else 0}
                    
            elif scraper_name == 'ecuagenera':
                data = scraper.scrape_single_product()
                if data:
                    result = {'success': True, 'images': 1 if data.get('image_url') else 0}
                    
            elif scraper_name == 'andys_orchids':
                data = scraper.scrape_single_orchid()
                if data:
                    result = {'success': True, 'images': 1 if data.get('image_url') else 0}
                    
            elif scraper_name == 'ron_parsons':
                data = scraper.scrape_single_image()
                if data:
                    result = {'success': True, 'images': 1 if data.get('image_url') else 0}
            
            return result
            
        except Exception as e:
            return {'success': False, 'images': 0, 'error': str(e)}
    
    def get_dashboard_stats(self) -> Dict[str, Any]:
        """Get current dashboard statistics"""
        uptime = datetime.now() - self.stats['session_start']
        
        return {
            'is_running': self.is_running,
            'uptime_seconds': int(uptime.total_seconds()),
            'uptime_formatted': str(uptime).split('.')[0],
            'current_cycle': self.current_cycle,
            'total_scraped': self.stats['total_scraped'],
            'current_scraper': self.stats['current_scraper'],
            'current_plant': self.stats['current_plant'],
            'successes': self.stats['successes'],
            'errors': self.stats['errors'],
            'success_rate': round((self.stats['successes'] / max(self.stats['total_scraped'], 1)) * 100, 1),
            'last_update': self.stats['last_update'].strftime('%H:%M:%S') if self.stats['last_update'] else 'Never',
            'scraper_stats': self.stats['scraper_stats'],
            'next_reinitialize': self.reinitialize_interval
        }
    
    def get_scraper_status(self, scraper_name: str) -> Dict[str, Any]:
        """Get detailed status for a specific scraper"""
        if scraper_name not in self.scrapers:
            return {'error': 'Scraper not found'}
            
        return self.stats['scraper_stats'].get(scraper_name, {})
    
    def manual_trigger_scraper(self, scraper_name: str) -> Dict[str, Any]:
        """Manually trigger a specific scraper"""
        if scraper_name not in self.scrapers:
            return {'success': False, 'error': 'Scraper not found'}
            
        try:
            scraper = self.scrapers[scraper_name]
            result = self._scrape_single_plant(scraper, scraper_name)
            
            # Update stats
            if result['success']:
                self.stats['scraper_stats'][scraper_name]['plants_found'] += 1
                self.stats['scraper_stats'][scraper_name]['images_collected'] += result.get('images', 0)
            else:
                self.stats['scraper_stats'][scraper_name]['errors'] += 1
                
            self.stats['scraper_stats'][scraper_name]['last_run'] = datetime.now()
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

# Global dashboard instance
scraping_dashboard = ScrapingDashboard()