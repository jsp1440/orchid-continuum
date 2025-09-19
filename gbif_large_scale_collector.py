#!/usr/bin/env python3
"""
GBIF Large-Scale Collection System
=================================
Enhanced orchid data collection for 10,000+ records with priority country targeting
Part of The Orchid Continuum - Five Cities Orchid Society

Features:
- Multi-batch processing for large collections
- Priority country targeting (US, Brazil, Colombia, Ecuador, Australia)
- Enhanced error handling and recovery
- Real-time progress tracking
- Geographic mapping preparation
"""

import requests
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from app import app, db
from models import OrchidRecord
from gbif_orchid_scraper import GBIFOrchidIntegrator

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GBIFLargeScaleCollector:
    """
    Large-scale GBIF collection system for 10,000+ orchid records
    """
    
    def __init__(self):
        self.integrator = GBIFOrchidIntegrator()
        self.priority_countries = {
            'US': {'name': 'United States', 'target': 3000},
            'BR': {'name': 'Brazil', 'target': 2500},
            'CO': {'name': 'Colombia', 'target': 2000},
            'EC': {'name': 'Ecuador', 'target': 1500},
            'AU': {'name': 'Australia', 'target': 1000},
            'PE': {'name': 'Peru', 'target': 1000},
            'MX': {'name': 'Mexico', 'target': 800},
            'VE': {'name': 'Venezuela', 'target': 700},
            'CR': {'name': 'Costa Rica', 'target': 500},
            'GT': {'name': 'Guatemala', 'target': 400}
        }
        
        logger.info("🌍 Large-Scale GBIF Collector initialized - ready for 10,000+ records")
    
    def collect_by_priority_countries(self, total_target: int = 10000) -> Dict[str, Any]:
        """
        Collect orchids from priority countries with proportional targeting
        
        Args:
            total_target: Total orchid records to collect across all countries
            
        Returns:
            Comprehensive collection statistics
        """
        overall_stats = {
            'total_target': total_target,
            'total_collected': 0,
            'total_saved': 0,
            'total_duplicates': 0,
            'total_errors': 0,
            'countries_processed': 0,
            'country_stats': {},
            'start_time': datetime.now(),
            'completion_time': None
        }
        
        logger.info(f"🚀 LARGE-SCALE COLLECTION STARTED - Target: {total_target:,} orchid records")
        logger.info(f"📍 Priority Countries: {', '.join(self.priority_countries.keys())}")
        
        try:
            for country_code, config in self.priority_countries.items():
                country_name = config['name']
                # Calculate proportional target
                country_target = min(int((config['target'] / 12400) * total_target), config['target'])
                
                if overall_stats['total_collected'] >= total_target:
                    logger.info(f"🎯 Target reached! Stopping collection.")
                    break
                
                logger.info(f"")
                logger.info(f"🇺🇸 Starting {country_name} collection - Target: {country_target:,} records")
                
                # Collect from this country
                country_stats = self.collect_country_batch(
                    country=country_code,
                    target_records=country_target
                )
                
                # Update overall statistics
                overall_stats['country_stats'][country_code] = {
                    'name': country_name,
                    'target': country_target,
                    'collected': country_stats['processed'],
                    'saved': country_stats['saved'],
                    'duplicates': country_stats['duplicates'],
                    'errors': country_stats['errors']
                }
                
                overall_stats['total_collected'] += country_stats['processed']
                overall_stats['total_saved'] += country_stats['saved']
                overall_stats['total_duplicates'] += country_stats['duplicates']
                overall_stats['total_errors'] += country_stats['errors']
                overall_stats['countries_processed'] += 1
                
                logger.info(f"✅ {country_name}: {country_stats['saved']:,} new records saved")
                
                # Brief pause between countries
                time.sleep(2)
            
            overall_stats['completion_time'] = datetime.now()
            duration = overall_stats['completion_time'] - overall_stats['start_time']
            
            logger.info(f"")
            logger.info(f"🎉 LARGE-SCALE COLLECTION COMPLETE!")
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   🌍 Countries processed: {overall_stats['countries_processed']}")
            logger.info(f"   📈 Records collected: {overall_stats['total_collected']:,}")
            logger.info(f"   💾 New records saved: {overall_stats['total_saved']:,}")
            logger.info(f"   ⚠️ Duplicates skipped: {overall_stats['total_duplicates']:,}")
            logger.info(f"   ❌ Errors: {overall_stats['total_errors']}")
            logger.info(f"   ⏱️ Duration: {duration}")
            
            return overall_stats
            
        except Exception as e:
            logger.error(f"❌ Large-scale collection error: {e}")
            overall_stats['error'] = str(e)
            return overall_stats
    
    def collect_country_batch(self, country: str, target_records: int = 1000) -> Dict[str, int]:
        """
        Collect orchids from a specific country with multi-batch processing
        
        Args:
            country: ISO country code
            target_records: Target number of records for this country
            
        Returns:
            Country-specific collection statistics
        """
        stats = {
            'total_found': 0,
            'processed': 0,
            'saved': 0,
            'duplicates': 0,
            'errors': 0,
            'batches': 0
        }
        
        try:
            batch_size = 300  # Optimal batch size for GBIF API stability
            offset = 0
            collected = 0
            
            while collected < target_records:
                remaining = target_records - collected
                current_batch_size = min(batch_size, remaining)
                
                logger.info(f"   📦 Batch {stats['batches'] + 1}: Fetching {current_batch_size} records (offset: {offset})")
                
                # Use existing integrator for actual collection
                batch_stats = self.integrator.collect_orchid_batch(
                    batch_size=current_batch_size,
                    max_records=current_batch_size,
                    country=country
                )
                
                # Update statistics
                stats['total_found'] = batch_stats.get('total_found', stats['total_found'])
                stats['processed'] += batch_stats.get('processed', 0)
                stats['saved'] += batch_stats.get('saved', 0)
                stats['duplicates'] += batch_stats.get('duplicates', 0)
                stats['errors'] += batch_stats.get('errors', 0)
                stats['batches'] += 1
                
                # Check if we got any records
                batch_processed = batch_stats.get('processed', 0)
                if batch_processed == 0:
                    logger.warning(f"   ⚠️ No records in batch - stopping country collection")
                    break
                
                collected += batch_processed
                offset += current_batch_size
                
                # Brief pause between batches
                time.sleep(1)
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ Country batch error for {country}: {e}")
            stats['errors'] += 1
            return stats
    
    def get_country_availability(self) -> Dict[str, int]:
        """
        Check available orchid records for each priority country
        
        Returns:
            Dictionary of country codes and available record counts
        """
        availability = {}
        
        logger.info("🔍 Checking orchid availability by country...")
        
        for country_code, config in self.priority_countries.items():
            try:
                # Search for count only
                response = self.integrator.session.get(
                    f"{self.integrator.base_url}/occurrence/count",
                    params={
                        'familyKey': 7711,  # Orchidaceae
                        'hasCoordinate': True,
                        'country': country_code
                    },
                    timeout=15
                )
                
                if response.status_code == 200:
                    count = response.json()
                    availability[country_code] = {
                        'name': config['name'],
                        'available': count,
                        'target': config['target']
                    }
                    logger.info(f"   🇺🇸 {config['name']}: {count:,} available records")
                else:
                    availability[country_code] = {
                        'name': config['name'],
                        'available': 0,
                        'target': config['target']
                    }
                
                time.sleep(0.2)  # Rate limiting
                
            except Exception as e:
                logger.error(f"❌ Error checking {config['name']}: {e}")
                availability[country_code] = {
                    'name': config['name'],
                    'available': 0,
                    'target': config['target']
                }
        
        return availability

def run_large_scale_collection(target_records: int = 10000) -> Dict[str, Any]:
    """
    Main function to run large-scale orchid collection
    
    Args:
        target_records: Total target records to collect
        
    Returns:
        Complete collection statistics
    """
    with app.app_context():
        collector = GBIFLargeScaleCollector()
        
        # Check availability first
        logger.info("📊 Checking country availability...")
        availability = collector.get_country_availability()
        
        total_available = sum(info['available'] for info in availability.values())
        logger.info(f"📈 Total available orchid records: {total_available:,}")
        
        if total_available < target_records:
            logger.warning(f"⚠️ Target ({target_records:,}) exceeds availability ({total_available:,})")
            target_records = min(target_records, total_available)
        
        # Start large-scale collection
        results = collector.collect_by_priority_countries(target_records)
        results['availability'] = availability
        
        return results

if __name__ == "__main__":
    # Test run
    results = run_large_scale_collection(1000)  # Test with 1000 records
    print(json.dumps(results, indent=2, default=str))