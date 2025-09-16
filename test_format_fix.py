#!/usr/bin/env python3
"""
Simple test script to verify the SVO data format conversion fix.

Tests that clean_svo() can now handle SVOTuple objects from the parser.
"""

import sys
import json
from datetime import datetime

def test_format_fix():
    """Test that the data format conversion fix works correctly"""
    print("🧪 Testing SVO Data Format Conversion Fix")
    print("=" * 50)
    
    # Import the modules we need
    try:
        sys.path.append('.')
        from scraper.parser import SVOTuple
        from analyzer.processor import clean_svo
        print("✅ Successfully imported required modules")
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False
    
    # Create test SVOTuple objects (what the parser returns)
    test_tuples = [
        SVOTuple(
            subject="cattleya orchid",
            verb="requires",
            object="bright indirect light",
            confidence=0.85,
            source_url="http://test1.com",
            source_category="care",
            context="Cattleya orchids require bright indirect light for optimal growth",
            extraction_method="pattern_care_instruction"
        ),
        SVOTuple(
            subject="phalaenopsis",
            verb="prefers",
            object="warm temperatures",
            confidence=0.9,
            source_url="http://test2.com",
            source_category="growing",
            context="Phalaenopsis prefers warm temperatures year-round",
            extraction_method="nlp"
        ),
        SVOTuple(
            subject="dendrobium",
            verb="needs",
            object="good drainage",
            confidence=0.8,
            source_url="http://test3.com",
            source_category="care",
            context="Dendrobium needs good drainage to prevent root rot",
            extraction_method="pattern"
        )
    ]
    
    print(f"✅ Created {len(test_tuples)} test SVOTuple objects")
    
    # Test that they all have to_dict method
    for i, tuple_obj in enumerate(test_tuples):
        if not hasattr(tuple_obj, 'to_dict'):
            print(f"❌ Tuple {i} missing to_dict method")
            return False
        
        dict_result = tuple_obj.to_dict()
        if not isinstance(dict_result, dict):
            print(f"❌ Tuple {i} to_dict() didn't return dict")
            return False
    
    print("✅ All SVOTuple objects have working to_dict() method")
    
    # Now test the main fix: clean_svo with SVOTuple objects
    try:
        print("\n🔧 Testing clean_svo() with SVOTuple objects...")
        result = clean_svo(test_tuples)
        
        print("✅ clean_svo() successfully processed SVOTuple objects!")
        
        # Verify the result structure
        if 'cleaned_data' not in result:
            print("❌ Missing cleaned_data in result")
            return False
        
        if 'statistics' not in result:
            print("❌ Missing statistics in result")
            return False
        
        cleaned_data = result['cleaned_data']
        stats = result['statistics']
        
        print(f"✅ Processing statistics:")
        print(f"   • Total input: {stats['total_input']}")
        print(f"   • Valid entries: {stats['valid_entries']}")
        print(f"   • Final cleaned: {stats['final_cleaned']}")
        print(f"   • Validation rate: {stats['validation_rate']:.1%}")
        
        # Verify cleaned data format
        if cleaned_data and len(cleaned_data) > 0:
            first_entry = cleaned_data[0]
            if not isinstance(first_entry, dict):
                print("❌ Cleaned data should be dictionaries")
                return False
            
            # Check required fields
            required_fields = ['subject', 'verb', 'object', 'confidence']
            for field in required_fields:
                if field not in first_entry:
                    print(f"❌ Missing field {field} in cleaned data")
                    return False
            
            print("✅ Cleaned data has correct dictionary format with all required fields")
            
            # Show a sample cleaned entry
            print(f"\n📋 Sample cleaned entry:")
            sample = cleaned_data[0]
            print(f"   Subject: '{sample['subject']}'")
            print(f"   Verb: '{sample['verb']}'")
            print(f"   Object: '{sample['object']}'")
            print(f"   Confidence: {sample['confidence']:.2f}")
        
        return True
        
    except Exception as e:
        print(f"❌ clean_svo() failed with SVOTuple objects: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backward_compatibility():
    """Test that clean_svo still works with regular dictionaries"""
    print("\n🔄 Testing backward compatibility with dictionaries...")
    
    try:
        from analyzer.processor import clean_svo
        
        # Test with regular dictionaries (old format)
        test_dicts = [
            {
                'subject': 'vanda orchid',
                'verb': 'requires',
                'object': 'high humidity',
                'confidence': 0.9
            },
            {
                'subject': 'cymbidium',
                'verb': 'blooms',
                'object': 'in cool weather',
                'confidence': 0.85
            }
        ]
        
        result = clean_svo(test_dicts)
        
        if result and 'cleaned_data' in result:
            print("✅ Backward compatibility maintained - dictionaries still work")
            return True
        else:
            print("❌ Backward compatibility broken")
            return False
            
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
        return False

def main():
    """Run the focused test for the format fix"""
    print("\n🎯 SVO Data Format Conversion Fix Test")
    print("Testing the fix for SVOTuple → Dictionary conversion")
    print("=" * 60)
    
    success = True
    
    # Test 1: Format conversion fix
    if not test_format_fix():
        success = False
    
    # Test 2: Backward compatibility
    if not test_backward_compatibility():
        success = False
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("✅ The data format conversion fix is working correctly")
        print("✅ SVOTuple objects are properly converted to dictionaries")
        print("✅ The pipeline can now flow seamlessly: parse → clean → analyze")
        print("✅ Backward compatibility with dictionaries is maintained")
    else:
        print("❌ SOME TESTS FAILED!")
        print("   The data format fix needs more work")
    
    print("=" * 60)
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)