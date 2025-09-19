#!/usr/bin/env python3
"""
Quick test runner for enhanced flowering & geographic collection
"""

from app import app
from enhanced_flowering_geographic_scraper import FloweringGeographicScraper
from database_metadata_tracker import DatabaseMetadataTracker
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_enhanced_collection():
    """Test the enhanced collection system"""
    print("🌸📍 TESTING ENHANCED FLOWERING & GEOGRAPHIC COLLECTION")
    print("=" * 60)
    
    with app.app_context():
        # First, get baseline stats
        tracker = DatabaseMetadataTracker()
        baseline = tracker.get_current_stats()
        
        print(f"📊 BASELINE DATABASE STATS:")
        print(f"   Total Records: {baseline['total_records']:,}")
        print(f"   With Flowering Dates: {baseline['with_bloom_time']:,} ({baseline['bloom_completeness']:.1f}%)")
        print(f"   With Coordinates: {baseline['with_coordinates']:,} ({baseline['coord_completeness']:.1f}%)")
        print(f"   With BOTH (Target): {baseline['with_both']:,} ({baseline['both_completeness']:.1f}%)")
        print()
        
        # Run enhanced collection
        print("🚀 STARTING ENHANCED COLLECTION...")
        scraper = FloweringGeographicScraper()
        results = scraper.run_enhanced_collection()
        
        print()
        print("✅ COLLECTION COMPLETED!")
        print(f"   Records processed: {results['total_processed']}")
        print(f"   Enhanced with flowering dates: {results['with_flowering_dates']}")
        print(f"   Enhanced with coordinates: {results['with_coordinates']}")
        print(f"   Enhanced with BOTH: {results['with_both']}")
        print(f"   Endemic species found: {results['endemic_species']}")
        print(f"   Cross-latitude candidates: {results['cross_latitude_candidates']}")
        print()
        
        # Get updated stats
        updated = tracker.get_current_stats()
        
        print(f"📈 UPDATED DATABASE STATS:")
        print(f"   Total Records: {updated['total_records']:,} (+{updated['total_records'] - baseline['total_records']})")
        print(f"   With Flowering Dates: {updated['with_bloom_time']:,} ({updated['bloom_completeness']:.1f}%) (+{updated['with_bloom_time'] - baseline['with_bloom_time']})")
        print(f"   With Coordinates: {updated['with_coordinates']:,} ({updated['coord_completeness']:.1f}%) (+{updated['with_coordinates'] - baseline['with_coordinates']})")
        print(f"   With BOTH (Target): {updated['with_both']:,} ({updated['both_completeness']:.1f}%) (+{updated['with_both'] - baseline['with_both']})")
        print()
        
        # Show improvement
        improvement = updated['both_completeness'] - baseline['both_completeness']
        print(f"🎯 TARGET IMPROVEMENT: +{improvement:.2f}% completion rate")
        
        if improvement > 0:
            print("✅ SUCCESS: Database metadata completeness improved!")
        else:
            print("ℹ️  INFO: No new records with both flowering dates and coordinates found")
        
        print("=" * 60)
        
        return results

if __name__ == "__main__":
    test_enhanced_collection()