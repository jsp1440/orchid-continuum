#!/usr/bin/env python3
"""
Test Validation System
======================
Tests the integrated validation system to ensure it properly rejects invalid orchid data
before it reaches the database.
"""

import logging
from datetime import datetime
from validation_integration import ScraperValidationSystem, create_validated_orchid_record

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_validation_system():
    """Test the validation system with various data samples"""
    
    logger.info("🧪 TESTING VALIDATION SYSTEM")
    logger.info("=" * 50)
    
    # Test data: mix of valid and invalid records
    test_records = [
        # VALID ORCHID RECORDS (should pass validation)
        {
            'name': 'Valid Cattleya',
            'data': {
                'genus': 'Cattleya',
                'species': 'labiata',
                'display_name': 'Cattleya labiata',
                'scientific_name': 'Cattleya labiata',
                'ingestion_source': 'validation_test'
            },
            'expected': True
        },
        {
            'name': 'Valid Phalaenopsis',
            'data': {
                'genus': 'Phalaenopsis',
                'species': 'amabilis',
                'display_name': 'Phalaenopsis amabilis',
                'scientific_name': 'Phalaenopsis amabilis',
                'ingestion_source': 'validation_test'
            },
            'expected': True
        },
        {
            'name': 'Valid Dendrobium',
            'data': {
                'genus': 'Dendrobium',
                'species': 'nobile',
                'display_name': 'Dendrobium nobile',
                'scientific_name': 'Dendrobium nobile',
                'ingestion_source': 'validation_test'
            },
            'expected': True
        },
        
        # INVALID RECORDS (should fail validation)
        {
            'name': 'Invalid wasp family',
            'data': {
                'genus': 'Trichogrammatidae',
                'species': 'unknown',
                'display_name': 'Trichogrammatidae wasp',
                'scientific_name': 'Trichogrammatidae species',
                'ingestion_source': 'validation_test'
            },
            'expected': False
        },
        {
            'name': 'Invalid random genus',
            'data': {
                'genus': 'InvalidOrchidGenus',
                'species': 'fake',
                'display_name': 'InvalidOrchidGenus fake',
                'scientific_name': 'InvalidOrchidGenus fake',
                'ingestion_source': 'validation_test'
            },
            'expected': False
        },
        {
            'name': 'Empty genus',
            'data': {
                'genus': '',
                'species': 'unknown',
                'display_name': 'Unknown orchid',
                'scientific_name': 'Unknown orchid',
                'ingestion_source': 'validation_test'
            },
            'expected': False
        },
        
        # AUTO-CORRECTABLE RECORDS (should pass after correction)
        {
            'name': 'Abbreviated Cattleya (C)',
            'data': {
                'genus': 'C',
                'species': 'mossiae',
                'display_name': 'C. mossiae',
                'scientific_name': 'C. mossiae',
                'ingestion_source': 'validation_test'
            },
            'expected': True  # Should be auto-corrected to 'Cattleya'
        },
        {
            'name': 'Abbreviated Phalaenopsis (Phal)',
            'data': {
                'genus': 'Phal',
                'species': 'stuartiana',
                'display_name': 'Phal stuartiana',
                'scientific_name': 'Phal stuartiana',
                'ingestion_source': 'validation_test'
            },
            'expected': True  # Should be auto-corrected to 'Phalaenopsis'
        }
    ]
    
    # Run validation tests
    test_results = {
        'total_tests': len(test_records),
        'passed': 0,
        'failed': 0,
        'auto_corrected': 0,
        'details': []
    }
    
    for test in test_records:
        logger.info(f"🔍 Testing: {test['name']}")
        
        # Test validation
        validated_data = create_validated_orchid_record(test['data'], "validation_test")
        
        # Check result
        is_valid = validated_data is not None
        expected = test['expected']
        
        test_result = {
            'name': test['name'],
            'expected': expected,
            'actual': is_valid,
            'passed': is_valid == expected,
            'original_genus': test['data']['genus'],
            'corrected_genus': validated_data.get('genus') if validated_data else None
        }
        
        if test_result['passed']:
            test_results['passed'] += 1
            
            # Check if auto-correction occurred
            if validated_data and validated_data.get('genus') != test['data']['genus']:
                test_results['auto_corrected'] += 1
                logger.info(f"   ✅ PASSED (auto-corrected: {test['data']['genus']} → {validated_data['genus']})")
            else:
                logger.info(f"   ✅ PASSED ({expected})")
        else:
            test_results['failed'] += 1
            logger.error(f"   ❌ FAILED (expected: {expected}, got: {is_valid})")
        
        test_results['details'].append(test_result)
    
    # Generate comprehensive test report
    logger.info("📊 VALIDATION TEST RESULTS")
    logger.info("=" * 40)
    logger.info(f"Total tests: {test_results['total_tests']}")
    logger.info(f"Passed: {test_results['passed']}")
    logger.info(f"Failed: {test_results['failed']}")
    logger.info(f"Auto-corrected: {test_results['auto_corrected']}")
    logger.info(f"Success rate: {(test_results['passed'] / test_results['total_tests'] * 100):.1f}%")
    
    # Show detailed results
    logger.info("\n📋 DETAILED TEST RESULTS:")
    for result in test_results['details']:
        status = "✅ PASS" if result['passed'] else "❌ FAIL"
        correction = f" (corrected: {result['original_genus']} → {result['corrected_genus']})" if result['corrected_genus'] and result['corrected_genus'] != result['original_genus'] else ""
        logger.info(f"  {status} | {result['name']}{correction}")
    
    # Test validation statistics
    validator = ScraperValidationSystem()
    validation_report = validator.get_validation_report()
    
    logger.info("\n🔍 VALIDATION SYSTEM STATUS:")
    logger.info(f"  Taxonomy verifier loaded: {validation_report['taxonomy_status']['verifier_loaded']}")
    logger.info(f"  Available genera in taxonomy: {validation_report['taxonomy_status']['available_genera']}")
    
    return test_results

def test_scraper_integration():
    """Test that scrapers would properly reject bad data"""
    
    logger.info("\n🔧 TESTING SCRAPER INTEGRATION")
    logger.info("=" * 40)
    
    # Simulate what would happen if scrapers tried to import bad data
    bad_scraper_data = [
        {
            'scraper': 'gary_scraper',
            'data': {
                'genus': 'Trichogrammatidae',  # Wasp family
                'display_name': 'Trichogrammatidae wasp',
                'ingestion_source': 'gary_test'
            }
        },
        {
            'scraper': 'svo_scraper', 
            'data': {
                'genus': 'InvalidGenus',
                'display_name': 'Invalid specimen',
                'ingestion_source': 'svo_test'
            }
        },
        {
            'scraper': 'roberta_fox_scraper',
            'data': {
                'genus': 'NonOrchidFamily',
                'display_name': 'Non-orchid plant',
                'ingestion_source': 'roberta_fox_test'
            }
        }
    ]
    
    rejected_count = 0
    for test_data in bad_scraper_data:
        validated = create_validated_orchid_record(test_data['data'], test_data['scraper'])
        if validated is None:
            rejected_count += 1
            logger.info(f"   ✅ {test_data['scraper']} correctly rejected: {test_data['data']['genus']}")
        else:
            logger.error(f"   ❌ {test_data['scraper']} incorrectly accepted: {test_data['data']['genus']}")
    
    logger.info(f"\n📊 SCRAPER INTEGRATION TEST: {rejected_count}/{len(bad_scraper_data)} bad records properly rejected")
    
    return rejected_count == len(bad_scraper_data)

if __name__ == "__main__":
    # Run comprehensive validation tests
    test_results = test_validation_system()
    
    # Test scraper integration
    scraper_test_passed = test_scraper_integration()
    
    # Final summary
    logger.info("\n🎯 FINAL VALIDATION SYSTEM TEST SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Core validation tests: {test_results['passed']}/{test_results['total_tests']} passed")
    logger.info(f"Auto-correction working: {test_results['auto_corrected']} tests corrected")
    logger.info(f"Scraper integration: {'✅ WORKING' if scraper_test_passed else '❌ FAILED'}")
    
    overall_success = (test_results['failed'] == 0) and scraper_test_passed
    logger.info(f"Overall validation system: {'✅ FULLY FUNCTIONAL' if overall_success else '❌ NEEDS ATTENTION'}")
    
    if overall_success:
        logger.info("\n🔒 VALIDATION SYSTEM IS READY FOR PRODUCTION")
        logger.info("   - Automatically rejects non-orchid data")
        logger.info("   - Auto-corrects common abbreviations") 
        logger.info("   - Prevents wasp families from entering database")
        logger.info("   - All scrapers now protected by validation")
    else:
        logger.error("\n⚠️ VALIDATION SYSTEM NEEDS FIXES BEFORE PRODUCTION USE")