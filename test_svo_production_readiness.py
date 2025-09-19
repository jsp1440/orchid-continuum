#!/usr/bin/env python3
"""
Production Readiness Test for SVO Visualization System

This test verifies that all the production fixes are working correctly:
1. Config compatibility and merging
2. Robust error handling and graceful degradation
3. Database model integration
4. Save results with proper app context
5. Comprehensive error handling for imports and KeyErrors
"""

import sys
import os
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_config_compatibility():
    """Test that config merging works correctly"""
    print("🧪 Testing config compatibility and merging...")
    
    try:
        # Import with error handling
        from analyzer.visualizer import _merge_visualization_config
        
        # Test 1: No config provided (should use defaults)
        config1 = _merge_visualization_config(None)
        assert isinstance(config1, dict), "Config should be a dictionary"
        assert 'style' in config1, "Config should have style section"
        assert 'colors' in config1, "Config should have colors section"
        print("✅ Test 1 passed: Default config generation works")
        
        # Test 2: User config merging
        user_config = {
            'style': {'figure_size': (10, 6)},
            'colors': {'primary': '#FF0000'}
        }
        config2 = _merge_visualization_config(user_config)
        assert config2['style']['figure_size'] == (10, 6), "User config should override defaults"
        assert config2['colors']['primary'] == '#FF0000', "User colors should override defaults"
        print("✅ Test 2 passed: User config merging works")
        
        # Test 3: Global CONFIG integration (should handle missing CONFIG gracefully)
        config3 = _merge_visualization_config({})
        assert isinstance(config3, dict), "Should handle missing global CONFIG"
        print("✅ Test 3 passed: Global CONFIG integration works")
        
        return True
        
    except Exception as e:
        print(f"❌ Config compatibility test failed: {str(e)}")
        return False

def test_error_handling():
    """Test robust error handling and graceful degradation"""
    print("🧪 Testing error handling and graceful degradation...")
    
    try:
        from analyzer.visualizer import visualize_svo, _create_fallback_visualization, _create_fallback_chart
        
        # Test 1: Invalid input data
        result1 = visualize_svo(None)
        assert isinstance(result1, dict), "Should return dict even with None input"
        print("✅ Test 1 passed: Handles None input gracefully")
        
        # Test 2: Empty analysis results
        result2 = visualize_svo({})
        assert isinstance(result2, dict), "Should return dict even with empty input"
        print("✅ Test 2 passed: Handles empty input gracefully")
        
        # Test 3: Malformed data
        bad_data = {'invalid': 'data'}
        result3 = visualize_svo(bad_data)
        assert isinstance(result3, dict), "Should handle malformed data"
        print("✅ Test 3 passed: Handles malformed data gracefully")
        
        # Test 4: Fallback visualization creation
        fallback = _create_fallback_visualization("Test error message")
        assert isinstance(fallback, dict), "Fallback should return dict"
        print("✅ Test 4 passed: Fallback visualization works")
        
        # Test 5: Fallback chart creation
        fallback_chart = _create_fallback_chart("test_chart", "Test error")
        assert isinstance(fallback_chart, dict), "Fallback chart should return dict"
        print("✅ Test 5 passed: Fallback chart creation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Error handling test failed: {str(e)}")
        return False

def test_database_integration():
    """Test database model integration"""
    print("🧪 Testing database model integration...")
    
    try:
        # Test import
        from storage.db_handler import SVODatabaseHandler, save_results, validate_svo_data
        from models import SVOExtractedData
        
        # Test 1: Database handler initialization
        handler = SVODatabaseHandler()
        assert hasattr(handler, 'batch_size'), "Handler should have batch_size"
        assert hasattr(handler, 'quality_thresholds'), "Handler should have quality_thresholds"
        print("✅ Test 1 passed: Database handler initializes correctly")
        
        # Test 2: SVO data validation
        valid_data = {
            'subject': 'Cattleya orchid',
            'verb': 'requires',
            'object': 'bright indirect light for optimal flowering',
            'original_text': 'Cattleya orchids require bright indirect light for optimal flowering.',
            'source_url': 'https://example.com/test',
            'extraction_confidence': 0.85,
            'svo_confidence': 0.9
        }
        is_valid, issues = validate_svo_data(valid_data)
        assert is_valid, f"Valid data should pass validation: {issues}"
        print("✅ Test 2 passed: SVO data validation works")
        
        # Test 3: Invalid data handling
        invalid_data = {'subject': 'test'}  # Missing required fields
        is_valid, issues = validate_svo_data(invalid_data)
        assert not is_valid, "Invalid data should fail validation"
        assert len(issues) > 0, "Should return validation issues"
        print("✅ Test 3 passed: Invalid data validation works")
        
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {str(e)}")
        return False

def test_save_results_with_context():
    """Test save_results with proper app context handling"""
    print("🧪 Testing save_results with app context...")
    
    try:
        from storage.db_handler import save_results
        
        # Test 1: None input handling
        success, result_info = save_results(None)
        assert not success, "Should fail with None input"
        assert 'error' in result_info, "Should return error information"
        print("✅ Test 1 passed: Handles None input correctly")
        
        # Test 2: Empty list handling
        success, result_info = save_results([])
        assert not success, "Should fail with empty list"
        assert 'error' in result_info, "Should return error information"
        print("✅ Test 2 passed: Handles empty list correctly")
        
        # Test 3: Invalid data type handling
        success, result_info = save_results("invalid")
        assert not success, "Should fail with invalid data type"
        assert 'error' in result_info, "Should return error information"
        print("✅ Test 3 passed: Handles invalid data type correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Save results test failed: {str(e)}")
        return False

def test_import_error_handling():
    """Test comprehensive error handling for imports"""
    print("🧪 Testing import error handling...")
    
    try:
        # Test that the modules import correctly with error handling
        from analyzer import visualizer
        from storage import db_handler
        
        # Test that fallback mechanisms work
        assert hasattr(visualizer, 'CONFIG'), "Should have CONFIG (even if fallback)"
        print("✅ Test 1 passed: Import error handling works")
        
        # Test database handler imports
        handler = db_handler.SVODatabaseHandler()
        assert hasattr(handler, 'quality_thresholds'), "Should have quality thresholds"
        print("✅ Test 2 passed: Database handler import works")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error handling test failed: {str(e)}")
        return False

def test_production_scenario():
    """Test a realistic production scenario"""
    print("🧪 Testing realistic production scenario...")
    
    try:
        from analyzer.visualizer import visualize_svo
        
        # Create realistic analysis results
        analysis_results = {
            'frequency_analysis': {
                'subject_frequencies': {
                    'Cattleya': 10,
                    'Phalaenopsis': 8,
                    'Dendrobium': 6
                },
                'verb_frequencies': {
                    'requires': 15,
                    'grows': 12,
                    'blooms': 8
                },
                'object_frequencies': {
                    'bright light': 12,
                    'high humidity': 10,
                    'good drainage': 8
                }
            },
            'meta': {
                'total_entries': 24,
                'avg_confidence': 0.85,
                'analysis_completeness': 0.92,
                'diversity_scores': {
                    'subject_diversity': 0.75,
                    'verb_diversity': 0.68,
                    'object_diversity': 0.82
                }
            }
        }
        
        svo_data = [
            {
                'subject': 'Cattleya',
                'verb': 'requires',
                'object': 'bright light'
            },
            {
                'subject': 'Phalaenopsis',
                'verb': 'grows',
                'object': 'in low light'
            }
        ]
        
        # Test visualization creation
        figures = visualize_svo(analysis_results, svo_data)
        assert isinstance(figures, dict), "Should return dictionary of figures"
        assert len(figures) > 0, "Should create at least one figure"
        print("✅ Production scenario test passed: Created visualizations successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Production scenario test failed: {str(e)}")
        return False

def main():
    """Run all production readiness tests"""
    print("🚀 Starting SVO Production Readiness Tests\n")
    
    tests = [
        ("Config Compatibility", test_config_compatibility),
        ("Error Handling", test_error_handling),
        ("Database Integration", test_database_integration),
        ("Save Results Context", test_save_results_with_context),
        ("Import Error Handling", test_import_error_handling),
        ("Production Scenario", test_production_scenario)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"Running: {test_name}")
        print(f"{'='*60}")
        
        try:
            if test_func():
                print(f"✅ {test_name}: PASSED")
                passed += 1
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: FAILED with exception: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED - SYSTEM IS PRODUCTION READY!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - REVIEW NEEDED")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)