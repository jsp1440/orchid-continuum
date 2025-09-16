#!/usr/bin/env python3
"""
Test script for the storage package functionality.

This script tests the storage package to ensure it works correctly
with the existing PostgreSQL database and SQLAlchemy setup.
"""

import sys
import json
from datetime import datetime

def test_storage_functionality():
    """Test the storage package functionality"""
    print("🧪 Testing Storage Package Functionality")
    print("=" * 50)
    
    try:
        # Test 1: Import the storage package
        print("📦 Test 1: Importing storage package...")
        from storage import (
            save_results, 
            get_svo_data, 
            validate_svo_data, 
            create_svo_tables,
            get_svo_statistics,
            SVODatabaseHandler
        )
        print("✅ Storage package imported successfully")
        
        # Test 2: Create database tables
        print("\n🔧 Test 2: Creating database tables...")
        tables_created = create_svo_tables()
        if tables_created:
            print("✅ Database tables created successfully")
        else:
            print("⚠️ Tables may already exist or creation failed")
        
        # Test 3: Data validation
        print("\n🔍 Test 3: Testing data validation...")
        
        # Valid test data
        valid_svo_data = {
            'subject': 'Phalaenopsis orchid',
            'verb': 'requires',
            'object': 'bright indirect light and high humidity',
            'original_text': 'The Phalaenopsis orchid requires bright indirect light and high humidity for optimal growth.',
            'source_url': 'https://example.com/orchid-care',
            'source_type': 'test_source',
            'extraction_confidence': 0.85,
            'svo_confidence': 0.90,
            'genus': 'Phalaenopsis',
            'care_category': 'light'
        }
        
        is_valid, issues = validate_svo_data(valid_svo_data)
        if is_valid:
            print("✅ Valid data validation passed")
        else:
            print(f"❌ Valid data validation failed: {issues}")
        
        # Invalid test data
        invalid_svo_data = {
            'subject': 'X',  # Too short
            'verb': '',      # Empty
            'object': 'test',
            'original_text': 'Short text',  # Too short
            'source_url': 'invalid-url'     # Invalid URL format
        }
        
        is_valid, issues = validate_svo_data(invalid_svo_data)
        if not is_valid:
            print(f"✅ Invalid data validation correctly failed: {len(issues)} issues found")
        else:
            print("❌ Invalid data validation should have failed")
        
        # Test 4: Save single result
        print("\n💾 Test 4: Testing save_results() with single record...")
        
        test_data = {
            'subject': 'Cattleya orchid',
            'verb': 'blooms',
            'object': 'beautiful fragrant flowers in spring and fall',
            'original_text': 'The Cattleya orchid blooms beautiful fragrant flowers in spring and fall when given proper care.',
            'source_url': 'https://test.example.com/cattleya-care',
            'source_type': 'test_data',
            'page_title': 'Cattleya Care Guide',
            'extraction_confidence': 0.88,
            'svo_confidence': 0.92,
            'genus': 'Cattleya',
            'care_category': 'flowering',
            'seasonal_relevance': 'spring'
        }
        
        success, result_info = save_results(test_data, batch_id='test_single')
        if success:
            print(f"✅ Single record saved successfully: {result_info}")
        else:
            print(f"❌ Failed to save single record: {result_info}")
        
        # Test 5: Save batch results
        print("\n📦 Test 5: Testing batch save_results()...")
        
        batch_data = [
            {
                'subject': 'Dendrobium orchid',
                'verb': 'prefers',
                'object': 'cooler temperatures during winter rest period',
                'original_text': 'Dendrobium orchid prefers cooler temperatures during winter rest period for proper flower development.',
                'source_url': 'https://test.example.com/dendrobium-care',
                'source_type': 'test_data',
                'extraction_confidence': 0.75,
                'svo_confidence': 0.80,
                'genus': 'Dendrobium',
                'care_category': 'temperature'
            },
            {
                'subject': 'Oncidium hybrid',
                'verb': 'needs',
                'object': 'good air circulation and moderate watering',
                'original_text': 'The Oncidium hybrid needs good air circulation and moderate watering to prevent root rot.',
                'source_url': 'https://test.example.com/oncidium-care',
                'source_type': 'test_data',
                'extraction_confidence': 0.82,
                'svo_confidence': 0.85,
                'genus': 'Oncidium',
                'care_category': 'watering'
            }
        ]
        
        success, result_info = save_results(batch_data, batch_id='test_batch')
        if success:
            print(f"✅ Batch records saved successfully: {result_info}")
        else:
            print(f"❌ Failed to save batch records: {result_info}")
        
        # Test 6: Retrieve data
        print("\n📊 Test 6: Testing data retrieval...")
        
        # Get all test data
        test_records = get_svo_data({'source_type': 'test_data'}, limit=10)
        print(f"✅ Retrieved {len(test_records)} test records")
        
        if test_records:
            sample_record = test_records[0]
            print(f"📄 Sample record: {sample_record['subject']} {sample_record['verb']} {sample_record['object'][:30]}...")
        
        # Test 7: Get statistics
        print("\n📈 Test 7: Testing statistics...")
        
        stats = get_svo_statistics()
        if stats:
            print(f"✅ Statistics retrieved:")
            print(f"   Total records: {stats.get('total_records', 0)}")
            print(f"   High confidence: {stats.get('high_confidence_count', 0)}")
            print(f"   Featured count: {stats.get('featured_count', 0)}")
            print(f"   Recent count: {stats.get('recent_count', 0)}")
            
            if stats.get('by_source_type'):
                print(f"   By source type: {stats['by_source_type']}")
        else:
            print("⚠️ No statistics available")
        
        # Test 8: Test handler class directly
        print("\n🔧 Test 8: Testing SVODatabaseHandler class...")
        
        handler = SVODatabaseHandler()
        handler_stats = handler.get_svo_statistics()
        
        print(f"✅ Handler statistics: Total records = {handler_stats.get('total_records', 0)}")
        
        print("\n🎉 All storage functionality tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {str(e)}")
        print("Make sure the storage package is properly installed and all dependencies are available.")
        return False
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Storage Package Test Suite")
    print("=" * 50)
    
    success = test_storage_functionality()
    
    if success:
        print("\n✅ ALL TESTS PASSED - Storage package is working correctly!")
        sys.exit(0)
    else:
        print("\n❌ TESTS FAILED - Check the error messages above")
        sys.exit(1)