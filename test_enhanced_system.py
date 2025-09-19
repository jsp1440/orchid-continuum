#!/usr/bin/env python3
"""
Test Suite for Enhanced Orchid Terminology Integration System
============================================================

Demonstrates the enhanced system functionality and validates integration
with existing SVO extraction while maintaining performance advantages.
"""

import sys
import os
sys.path.append('src')

from load_glossary import get_glossary_loader
from map_glossary_to_schema import get_schema_mapper
from ai_trait_inference import get_inference_engine
import time
import json

def test_glossary_loading():
    """Test botanical glossary loading functionality"""
    print("🔬 Testing Glossary Loading...")
    
    loader = get_glossary_loader()
    stats = loader.get_stats()
    
    print(f"✅ Loaded {stats['total_terms']} botanical terms")
    print(f"📊 Categories: {list(stats['categories'].keys())}")
    print(f"🤖 AI-derivable terms: {stats['ai_derivable_count']}")
    
    # Test term lookup
    labellum_info = loader.get_term_info("Labellum (Lip)")
    if labellum_info:
        print(f"🔍 Found 'Labellum': {labellum_info['definition'][:100]}...")
    
    # Test text analysis
    test_text = "The orchid labellum shows beautiful purple petals with distinctive markings"
    found_terms = loader.find_terms_in_text(test_text)
    print(f"🌺 Found {len(found_terms)} terms in text: {[t[0] for t in found_terms]}")
    
    return len(found_terms) > 0

def test_schema_mapping():
    """Test schema mapping functionality"""
    print("\n🗄️ Testing Schema Mapping...")
    
    mapper = get_schema_mapper()
    stats = mapper.get_stats()
    
    print(f"✅ Initialized {stats['total_mappings']} mappings")
    print(f"📊 SVO mappings: {stats['svo_mappings']}, Taxonomy mappings: {stats['taxonomy_mappings']}")
    
    # Test SVO enhancement
    test_svo = {
        'subject': 'orchid',
        'verb': 'displays',
        'object': 'labellum',
        'context_text': 'The beautiful orchid displays a prominent labellum with purple markings',
        'confidence_score': 0.8,
        'relevance_score': 0.6
    }
    
    enhanced = mapper.enhance_svo_result(test_svo)
    print(f"🧬 Enhanced SVO - Botanical category: {enhanced.get('botanical_category')}")
    print(f"🔬 Scientific term detected: {enhanced.get('is_scientific_term')}")
    print(f"📈 Enhanced relevance: {enhanced.get('relevance_score'):.2f}")
    
    return enhanced.get('is_scientific_term', False)

def test_ai_inference():
    """Test AI trait inference functionality"""
    print("\n🤖 Testing AI Trait Inference...")
    
    engine = get_inference_engine()
    stats = engine.get_inference_stats()
    
    print(f"✅ Inference engine with {stats['trait_patterns_loaded']} patterns")
    print(f"🧠 Cache size: {stats['cache_size']}/{stats['max_cache_size']}")
    
    # Test single SVO enhancement
    test_svo = ("Phalaenopsis", "displays", "labellum")
    test_context = "The beautiful Phalaenopsis orchid displays a prominent white labellum with purple markings measuring 3.2 cm across"
    
    enhanced = engine.infer_botanical_traits(test_svo, test_context)
    print(f"🌺 Enhanced SVO:")
    print(f"  - Terms detected: {enhanced.detected_terms}")
    print(f"  - Categories: {list(enhanced.categories_detected)}")
    print(f"  - Botanical relevance: {enhanced.botanical_relevance:.2f}")
    print(f"  - Overall confidence: {enhanced.overall_confidence:.2f}")
    print(f"  - Inferences: {len(enhanced.botanical_inferences)}")
    print(f"  - Measurements: {bool(enhanced.measurement_data)}")
    
    # Test batch processing
    test_batch = [
        ("cattleya", "produces", "flowers"),
        ("dendrobium", "grows", "pseudobulbs"),
        ("paphiopedilum", "shows", "slipper")
    ]
    
    enhanced_batch = engine.batch_enhance_svo_results(test_batch)
    summary = engine.generate_enhancement_summary(enhanced_batch)
    print(f"🔬 Batch summary: {summary['botanically_relevant']}/{summary['total_processed']} relevant")
    
    return enhanced.botanical_relevance > 0

def test_performance_comparison():
    """Test performance comparison with and without enhancement"""
    print("\n⚡ Testing Performance Impact...")
    
    # Test data
    svo_tuples = [
        ("orchid", "displays", "labellum"),
        ("cattleya", "produces", "flowers"),
        ("dendrobium", "grows", "pseudobulbs"),
        ("phalaenopsis", "shows", "petals"),
        ("paphiopedilum", "has", "slipper"),
        ("oncidium", "creates", "sprays"),
        ("cymbidium", "develops", "spikes"),
        ("vanda", "exhibits", "roots")
    ]
    
    contexts = [
        "The orchid displays a beautiful labellum with distinctive markings",
        "Cattleya produces large fragrant flowers in spring",
        "Dendrobium grows tall pseudobulbs with multiple nodes", 
        "Phalaenopsis shows elegant white petals year-round",
        "Paphiopedilum has a distinctive slipper-shaped lip",
        "Oncidium creates cascading sprays of small flowers",
        "Cymbidium develops long flower spikes in winter",
        "Vanda exhibits thick aerial roots for nutrients"
    ]
    
    # Test with enhancement
    engine = get_inference_engine()
    
    start_time = time.time()
    enhanced_results = engine.batch_enhance_svo_results(svo_tuples, contexts)
    enhanced_time = time.time() - start_time
    
    print(f"✅ Enhanced processing: {len(enhanced_results)} items in {enhanced_time:.3f}s")
    print(f"📊 Rate: {len(enhanced_results)/enhanced_time:.1f} items/second")
    
    botanical_count = sum(1 for r in enhanced_results if r.botanical_relevance > 0.5)
    print(f"🌺 Botanically relevant results: {botanical_count}/{len(enhanced_results)}")
    
    # Calculate enhancement value
    enhancement_overhead = enhanced_time / len(enhanced_results) * 1000  # ms per item
    print(f"⚡ Enhancement overhead: {enhancement_overhead:.1f}ms per SVO tuple")
    
    if enhancement_overhead < 10:
        print("🎉 Excellent performance - minimal overhead!")
    elif enhancement_overhead < 50:
        print("✅ Good performance - acceptable overhead")
    else:
        print("⚠️ High overhead - optimization needed")
    
    return enhancement_overhead < 50

def test_integration_workflow():
    """Test the complete integration workflow"""
    print("\n🔄 Testing Complete Integration Workflow...")
    
    # Simulate the complete workflow
    print("1. Loading botanical terminology...")
    loader = get_glossary_loader()
    
    print("2. Initializing schema mappings...")
    mapper = get_schema_mapper()
    
    print("3. Starting AI inference engine...")
    engine = get_inference_engine()
    
    print("4. Processing sample orchid text...")
    
    # Sample orchid description text
    sample_text = """
    The Phalaenopsis amabilis orchid displays beautiful white petals with a distinctive
    yellow labellum. The flower measures approximately 8 cm across with thick substance
    and glossy texture. The plant grows aerial roots and produces flowers on arching
    inflorescences that can reach 60 cm in length. This species shows excellent form
    and presentation, making it popular for judging competitions.
    """
    
    # Extract potential SVO tuples (simplified)
    potential_svos = [
        ("Phalaenopsis", "displays", "petals"),
        ("flower", "measures", "8cm"),
        ("plant", "grows", "roots"),
        ("species", "shows", "form"),
        ("inflorescence", "reaches", "60cm")
    ]
    
    print(f"5. Enhancing {len(potential_svos)} SVO tuples...")
    
    # Process through the enhancement pipeline
    enhanced_results = []
    for svo in potential_svos:
        # AI inference
        enhanced = engine.infer_botanical_traits(svo, sample_text)
        
        # Schema mapping  
        svo_data = {
            'subject': enhanced.subject,
            'verb': enhanced.verb,
            'object': enhanced.object,
            'context_text': enhanced.context_text[:200],
            'confidence_score': enhanced.overall_confidence,
            'relevance_score': enhanced.botanical_relevance
        }
        
        mapped = mapper.enhance_svo_result(svo_data)
        enhanced_results.append(mapped)
    
    # Generate summary
    scientific_terms = sum(1 for r in enhanced_results if r.get('is_scientific_term'))
    high_relevance = sum(1 for r in enhanced_results if r.get('relevance_score', 0) > 0.7)
    
    print(f"✅ Integration complete!")
    print(f"📊 Results:")
    print(f"  - Total processed: {len(enhanced_results)}")
    print(f"  - Scientific terms detected: {scientific_terms}")
    print(f"  - High relevance results: {high_relevance}")
    
    # Show detailed results for first few
    print(f"📋 Sample enhanced results:")
    for i, result in enumerate(enhanced_results[:3]):
        print(f"  {i+1}. '{result['subject']} {result['verb']} {result['object']}'")
        print(f"     - Category: {result.get('botanical_category', 'None')}")
        print(f"     - Confidence: {result.get('confidence_score', 0):.2f}")
        print(f"     - Relevance: {result.get('relevance_score', 0):.2f}")
    
    return scientific_terms > 0 and high_relevance > 0

def generate_test_report():
    """Generate comprehensive test report"""
    print("\n" + "="*60)
    print("🧪 ENHANCED ORCHID TERMINOLOGY SYSTEM TEST REPORT")
    print("="*60)
    
    tests = [
        ("Glossary Loading", test_glossary_loading),
        ("Schema Mapping", test_schema_mapping), 
        ("AI Inference", test_ai_inference),
        ("Performance Impact", test_performance_comparison),
        ("Integration Workflow", test_integration_workflow)
    ]
    
    results = {}
    total_time = time.time()
    
    for test_name, test_func in tests:
        print(f"\n🔬 Running: {test_name}")
        print("-" * 40)
        
        start_time = time.time()
        try:
            success = test_func()
            test_time = time.time() - start_time
            results[test_name] = {
                'status': 'PASSED' if success else 'FAILED',
                'time': test_time,
                'success': success
            }
        except Exception as e:
            test_time = time.time() - start_time
            results[test_name] = {
                'status': 'ERROR',
                'time': test_time,
                'success': False,
                'error': str(e)
            }
            print(f"❌ Error: {str(e)}")
    
    total_time = time.time() - total_time
    
    # Generate final report
    print("\n" + "="*60)
    print("📊 TEST SUMMARY REPORT")
    print("="*60)
    
    passed = sum(1 for r in results.values() if r['success'])
    total = len(results)
    
    print(f"Overall Status: {passed}/{total} tests passed")
    print(f"Total Test Time: {total_time:.2f} seconds")
    
    for test_name, result in results.items():
        status_icon = "✅" if result['success'] else "❌"
        print(f"{status_icon} {test_name}: {result['status']} ({result['time']:.2f}s)")
        
        if not result['success'] and 'error' in result:
            print(f"   Error: {result['error']}")
    
    print(f"\n🎉 System Status: {'OPERATIONAL' if passed == total else 'NEEDS ATTENTION'}")
    
    # Save results
    with open('test_results.json', 'w') as f:
        json.dump({
            'summary': {
                'passed': passed,
                'total': total,
                'success_rate': passed / total,
                'total_time': total_time
            },
            'detailed_results': results,
            'timestamp': time.time()
        }, f, indent=2)
    
    print(f"📄 Detailed results saved to: test_results.json")
    
    return passed == total

if __name__ == "__main__":
    print("🌺 Enhanced Orchid Terminology Integration System")
    print("🧪 Comprehensive Test Suite")
    print("=" * 60)
    
    success = generate_test_report()
    
    if success:
        print("\n🎉 All tests passed! System is ready for production use.")
        exit(0)
    else:
        print("\n⚠️ Some tests failed. Please review the results above.")
        exit(1)