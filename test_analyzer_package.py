#!/usr/bin/env python3
"""
Test Script for SVO Analyzer Package

This script tests all three main modules of the analyzer package:
- processor.clean_svo()
- analyzer.analyze_svo()
- visualizer.visualize_svo()

Run this script to verify the package functionality.
"""

import sys
import os
import json
from typing import Dict, List

# Add current directory to path to import analyzer package
sys.path.append('.')

def create_test_data() -> List[str]:
    """Create sample orchid care text for testing"""
    test_texts = [
        "Cattleya orchids require bright light and warm temperatures",
        "Phalaenopsis species grows well in humid conditions with filtered light", 
        "Dendrobium hybrids need good drainage and regular watering",
        "Orchid plants bloom best with proper fertilizer and care",
        "Vanda orchids develop strong roots in high humidity environments",
        "Cymbidium varieties produce beautiful flowers in cool temperatures",
        "Paphiopedilum species requires consistent moisture and indirect light",
        "Oncidium orchids grow rapidly with adequate water and nutrients",
        "Miltonia hybrids flower profusely in moderate light conditions",
        "Zygopetalum plants need regular feeding and proper air circulation"
    ]
    return test_texts

def test_processor():
    """Test the processor.clean_svo() function"""
    print("🧹 Testing SVO Processor...")
    
    try:
        from analyzer.processor import clean_svo
        
        # Test with text input
        test_texts = create_test_data()
        combined_text = " ".join(test_texts)
        
        print(f"   Input: {len(test_texts)} sample texts")
        result = clean_svo(combined_text)
        
        print(f"   ✅ Processed {result['statistics']['total_input']} input entries")
        print(f"   ✅ Generated {result['statistics']['final_cleaned']} clean SVO entries")
        print(f"   ✅ Validation rate: {result['statistics']['validation_rate']:.1%}")
        print(f"   ✅ Average confidence: {result['statistics']['avg_confidence']:.2f}")
        
        # Display sample results
        if result['cleaned_data']:
            print("   📋 Sample SVO entries:")
            for i, entry in enumerate(result['cleaned_data'][:3]):
                print(f"      {i+1}. S: '{entry['subject']}' | V: '{entry['verb']}' | O: '{entry['object']}' (conf: {entry['confidence']:.2f})")
        
        return result['cleaned_data']
        
    except Exception as e:
        print(f"   ❌ Processor test failed: {e}")
        return None

def test_analyzer(cleaned_data: List[Dict]):
    """Test the analyzer.analyze_svo() function"""
    print("📊 Testing SVO Analyzer...")
    
    if not cleaned_data:
        print("   ⚠️ No cleaned data available for analysis")
        return None
    
    try:
        from analyzer.analyzer import analyze_svo
        
        print(f"   Input: {len(cleaned_data)} cleaned SVO entries")
        analysis_results = analyze_svo(cleaned_data)
        
        # Check analysis components
        components = ['frequency_analysis', 'correlation_analysis', 'cluster_analysis', 
                     'care_categories', 'insights', 'recommendations']
        
        for component in components:
            if component in analysis_results and analysis_results[component]:
                if component == 'insights':
                    count = len(analysis_results[component])
                    print(f"   ✅ Generated {count} insights")
                elif component == 'recommendations':
                    count = len(analysis_results[component])
                    print(f"   ✅ Generated {count} recommendations")
                else:
                    print(f"   ✅ {component.replace('_', ' ').title()}: completed")
        
        # Display sample insights
        if analysis_results.get('insights'):
            print("   💡 Sample insights:")
            for i, insight in enumerate(analysis_results['insights'][:3]):
                print(f"      {i+1}. {insight}")
        
        # Display sample recommendations
        if analysis_results.get('recommendations'):
            print("   📋 Sample recommendations:")
            for i, rec in enumerate(analysis_results['recommendations'][:2]):
                print(f"      {i+1}. {rec}")
        
        return analysis_results
        
    except Exception as e:
        print(f"   ❌ Analyzer test failed: {e}")
        return None

def test_visualizer(analysis_results: Dict, svo_data: List[Dict]):
    """Test the visualizer.visualize_svo() function"""
    print("📈 Testing SVO Visualizer...")
    
    if not analysis_results:
        print("   ⚠️ No analysis results available for visualization")
        return False
    
    try:
        from analyzer.visualizer import visualize_svo
        
        print(f"   Input: Analysis results + {len(svo_data)} SVO entries")
        
        # Configure for testing (no actual file output)
        test_config = {
            'output': {
                'format': 'png',
                'save_path': './test_visualizations/',
                'return_base64': False
            },
            'style': {
                'figure_size': (10, 6),  # Smaller for testing
                'dpi': 150  # Lower DPI for faster processing
            }
        }
        
        figures = visualize_svo(analysis_results, svo_data, test_config)
        
        print(f"   ✅ Generated {len(figures)} visualization figures")
        
        # List generated visualizations
        for fig_name, fig in figures.items():
            print(f"      📊 {fig_name.replace('_', ' ').title()}")
        
        # Close figures to free memory
        import matplotlib.pyplot as plt
        plt.close('all')
        
        return True
        
    except Exception as e:
        print(f"   ❌ Visualizer test failed: {e}")
        return False

def test_package_imports():
    """Test that all package imports work correctly"""
    print("📦 Testing Package Imports...")
    
    try:
        # Test main package import
        import analyzer
        print("   ✅ Main package import successful")
        
        # Test individual function imports
        from analyzer import clean_svo, analyze_svo, visualize_svo
        print("   ✅ Main function imports successful")
        
        # Test module imports
        from analyzer.processor import SVOProcessor
        from analyzer.analyzer import SVOAnalyzer  
        from analyzer.visualizer import SVOVisualizer
        print("   ✅ Class imports successful")
        
        # Test package metadata
        print(f"   ✅ Package version: {analyzer.__version__}")
        print(f"   ✅ Available functions: {analyzer.__all__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import test failed: {e}")
        return False

def run_comprehensive_test():
    """Run comprehensive test of the entire analyzer package"""
    print("=" * 60)
    print("🔬 SVO ANALYZER PACKAGE COMPREHENSIVE TEST")
    print("=" * 60)
    
    # Test imports first
    if not test_package_imports():
        print("\n❌ Package import failed. Cannot continue testing.")
        return False
    
    print()
    
    # Test processor
    cleaned_data = test_processor()
    if not cleaned_data:
        print("\n❌ Processor test failed. Cannot continue testing.")
        return False
    
    print()
    
    # Test analyzer  
    analysis_results = test_analyzer(cleaned_data)
    if not analysis_results:
        print("\n❌ Analyzer test failed. Cannot continue testing.")
        return False
    
    print()
    
    # Test visualizer
    viz_success = test_visualizer(analysis_results, cleaned_data)
    if not viz_success:
        print("\n❌ Visualizer test failed.")
        return False
    
    print()
    print("=" * 60)
    print("✅ ALL TESTS PASSED! SVO Analyzer Package is working correctly.")
    print("=" * 60)
    
    # Print summary statistics
    print("\n📊 TEST SUMMARY:")
    print(f"   • Cleaned SVO entries: {len(cleaned_data)}")
    print(f"   • Analysis insights: {len(analysis_results.get('insights', []))}")
    print(f"   • Recommendations: {len(analysis_results.get('recommendations', []))}")
    print(f"   • Visualizations: Generated multiple charts and graphs")
    
    # Print usage example
    print("\n💡 USAGE EXAMPLE:")
    print("""
    from analyzer import clean_svo, analyze_svo, visualize_svo
    
    # Step 1: Clean your SVO data
    text = "Cattleya orchids require bright light and warm temperatures"
    cleaned = clean_svo(text)
    
    # Step 2: Analyze patterns
    analysis = analyze_svo(cleaned['cleaned_data'])
    
    # Step 3: Create visualizations
    figures = visualize_svo(analysis, cleaned['cleaned_data'])
    """)
    
    return True

def save_test_results(cleaned_data, analysis_results):
    """Save test results for inspection"""
    try:
        test_results = {
            'cleaned_data_sample': cleaned_data[:5],  # Save first 5 entries
            'analysis_summary': {
                'insights_count': len(analysis_results.get('insights', [])),
                'recommendations_count': len(analysis_results.get('recommendations', [])),
                'sample_insights': analysis_results.get('insights', [])[:3],
                'sample_recommendations': analysis_results.get('recommendations', [])[:3],
                'meta': analysis_results.get('meta', {})
            }
        }
        
        with open('test_results.json', 'w') as f:
            json.dump(test_results, f, indent=2, default=str)
        
        print(f"📄 Test results saved to test_results.json")
        
    except Exception as e:
        print(f"⚠️  Could not save test results: {e}")

if __name__ == "__main__":
    """Run the comprehensive test when script is executed directly"""
    success = run_comprehensive_test()
    
    if not success:
        sys.exit(1)
    
    print("\n🎉 SVO Analyzer Package is ready for use!")