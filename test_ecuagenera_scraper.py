#!/usr/bin/env python3
"""
Test script for Ecuagenera Comprehensive Scraper
Tests basic functionality with limited items per genus
"""

import sys
import os

# Add current directory to path to import our scraper
sys.path.insert(0, '.')

from ecuagenera_comprehensive_scraper import EcuaGeneraComprehensiveScraper
import logging

def test_small_batch():
    """Test scraper with very small batch sizes"""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("🧪 Starting Ecuagenera scraper test")
    
    # Create test scraper with small limits
    scraper = EcuaGeneraComprehensiveScraper(
        max_items_per_genus=3,  # Only 3 items per genus for testing
        request_delay=3.0,  # Longer delay during testing
        image_folder="test_ecuagenera_images",
        data_folder="test_ecuagenera_data"
    )
    
    try:
        # Test just one genus first
        logger.info("🧪 Testing with Cattleya genus only")
        
        # Test Cattleya scraping
        cattleya_data = scraper.scrape_genus("cattleya")
        
        if cattleya_data:
            logger.info(f"✅ Test successful! Collected {len(cattleya_data)} Cattleya items")
            
            # Print sample data
            if cattleya_data:
                sample = cattleya_data[0]
                logger.info("📋 Sample data structure:")
                logger.info(f"  Name: {sample.get('species_name', 'N/A')} {sample.get('hybrid_name', 'N/A')}")
                logger.info(f"  Description: {sample.get('description', 'N/A')[:100]}...")
                logger.info(f"  Price: {sample.get('price', 'N/A')}")
                logger.info(f"  Images: {len(sample.get('image_urls', []))} URLs, {len(sample.get('image_files', []))} downloaded")
                logger.info(f"  Features: {sample.get('botanical_features', [])}")
            
            # Save test data
            scraper.save_genus_data("cattleya", cattleya_data)
            
            return True
        else:
            logger.error("❌ Test failed - no data collected")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed with error: {str(e)}")
        return False

if __name__ == "__main__":
    success = test_small_batch()
    if success:
        print("✅ Test completed successfully!")
    else:
        print("❌ Test failed!")