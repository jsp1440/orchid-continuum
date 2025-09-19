"""
SVO Processing Pipeline - Main Orchestrator
Clean, modular approach for orchid data Subject-Verb-Object extraction and analysis
"""

from config import URLS, CONFIG
from scraper.fetcher import fetch_all
from scraper.parser import parse_svo
from analyzer.processor import clean_svo
from analyzer.analyzer import analyze_svo
from analyzer.visualizer import visualize_svo
from storage.db_handler import save_results

import logging
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Main SVO processing pipeline following the 6-step approach:
    1. Fetch raw data
    2. Parse raw HTML/JSON into SVO tuples
    3. Clean & normalize
    4. Analyze patterns
    5. Visualize
    6. Save structured data
    """
    start_time = time.time()
    logger.info("🌸 Starting SVO Processing Pipeline...")
    
    try:
        # Step 1: Fetch raw data
        logger.info("🔍 Step 1: Fetching raw data from configured URLs...")
        raw_data = fetch_all(URLS, CONFIG)
        logger.info(f"✅ Step 1 Complete: Fetched data from {len(raw_data)} sources")
        
        # Step 2: Parse raw HTML/JSON into SVO tuples
        logger.info("📝 Step 2: Parsing raw data into SVO tuples...")
        svo_data = parse_svo(raw_data, CONFIG)
        logger.info(f"✅ Step 2 Complete: Extracted {len(svo_data)} SVO tuples")
        
        # Step 3: Clean & normalize
        logger.info("🧹 Step 3: Cleaning and normalizing SVO data...")
        cleaned_result = clean_svo(svo_data, CONFIG)
        cleaned_svo = cleaned_result['cleaned_data']  # Extract cleaned data from result dict
        logger.info(f"✅ Step 3 Complete: Cleaned {len(cleaned_svo)} SVO entries")
        
        # Step 4: Analyze patterns
        logger.info("🔬 Step 4: Analyzing SVO patterns and extracting insights...")
        analysis_results = analyze_svo(cleaned_svo, CONFIG)  # Pass cleaned data directly
        logger.info(f"✅ Step 4 Complete: Generated analysis with {len(analysis_results.get('insights', []))} insights")
        
        # Step 5: Visualize
        logger.info("📊 Step 5: Creating visualizations...")
        visualization_results = visualize_svo(analysis_results, cleaned_svo, CONFIG)
        logger.info(f"✅ Step 5 Complete: Generated {len(visualization_results.get('charts', []))} visualizations")
        
        # Step 6: Save structured data
        logger.info("💾 Step 6: Saving results to database...")
        save_results(cleaned_svo)  # Pass cleaned data for database saving
        logger.info("✅ Step 6 Complete: Data saved to database successfully")
        
        # Summary
        elapsed_time = time.time() - start_time
        logger.info(f"🎉 SVO Pipeline Complete!")
        logger.info(f"📊 Summary:")
        logger.info(f"   - Sources processed: {len(raw_data)}")
        logger.info(f"   - SVO tuples extracted: {len(svo_data)}")
        logger.info(f"   - Clean entries: {len(cleaned_svo)}")
        logger.info(f"   - Insights generated: {len(analysis_results.get('insights', []))}")
        logger.info(f"   - Visualizations created: {len(visualization_results.get('charts', []))}")
        logger.info(f"   - Processing time: {elapsed_time:.2f} seconds")
        
        return {
            'success': True,
            'raw_data': raw_data,
            'svo_data': svo_data,
            'cleaned_svo': cleaned_svo,
            'analysis_results': analysis_results,
            'visualization_results': visualization_results,
            'processing_time': elapsed_time,
            'summary': {
                'sources_processed': len(raw_data),
                'svo_tuples_extracted': len(svo_data),
                'clean_entries': len(cleaned_svo),
                'insights_generated': len(analysis_results.get('insights', [])),
                'visualizations_created': len(visualization_results.get('charts', []))
            }
        }
        
    except Exception as e:
        elapsed_time = time.time() - start_time
        logger.error(f"❌ SVO Pipeline Failed: {str(e)}")
        logger.error(f"   - Processing time before failure: {elapsed_time:.2f} seconds")
        
        return {
            'success': False,
            'error': str(e),
            'processing_time': elapsed_time
        }

def run_svo_pipeline(urls=None, config_override=None):
    """
    Convenience function to run the SVO pipeline with optional overrides
    
    Args:
        urls (dict): Optional URL override (defaults to config.URLS)
        config_override (dict): Optional configuration overrides
        
    Returns:
        dict: Pipeline results with success status and data
    """
    # Use existing CONFIG import
    
    # Apply any configuration overrides
    if config_override:
        CONFIG.update(config_override)
        
    # Use provided URLs or default from config
    if urls:
        # Temporarily override URLS
        original_urls = URLS.copy()
        URLS.update(urls)
        try:
            return main()
        finally:
            # Restore original URLs
            URLS.clear()
            URLS.update(original_urls)
    else:
        return main()

if __name__ == "__main__":
    # Run the complete pipeline
    result = main()
    
    # Print final status
    if result['success']:
        print(f"\n🎉 SVO Pipeline completed successfully in {result['processing_time']:.2f} seconds")
        print(f"📊 Processed {result['summary']['sources_processed']} sources")
        print(f"📝 Extracted {result['summary']['svo_tuples_extracted']} SVO tuples")
        print(f"🧹 Cleaned {result['summary']['clean_entries']} entries")
        print(f"🔬 Generated {result['summary']['insights_generated']} insights")
        print(f"📊 Created {result['summary']['visualizations_created']} visualizations")
    else:
        print(f"\n❌ SVO Pipeline failed: {result['error']}")
        print(f"⏱️ Failed after {result['processing_time']:.2f} seconds")