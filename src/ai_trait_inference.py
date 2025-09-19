#!/usr/bin/env python3
"""
AI-Enhanced Botanical Trait Inference Module
============================================

Enhances the existing streamlined SVO extraction system with sophisticated botanical
knowledge while maintaining the proven 17x performance advantage. Provides intelligent
trait inference and botanical context without replacing the core extraction logic.
"""

import re
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import json
from datetime import datetime

logger = logging.getLogger(__name__)

from load_glossary import OrchidGlossaryLoader, get_glossary_loader
from map_glossary_to_schema import GlossarySchemaMapper, get_schema_mapper

@dataclass
class BotanicalInference:
    """Container for AI-derived botanical inferences"""
    trait_category: str
    confidence: float
    measurement_potential: bool
    ai_derivable: bool
    supporting_terms: List[str] = field(default_factory=list)
    inferred_values: Dict[str, Any] = field(default_factory=dict)
    extraction_method: str = "pattern_matching"
    validation_status: str = "pending"  # pending, validated, rejected

@dataclass
class EnhancedSVO:
    """Enhanced SVO tuple with botanical intelligence"""
    # Original SVO data
    subject: str
    verb: str
    object: str
    context_text: str = ""
    
    # Enhanced botanical data
    botanical_inferences: List[BotanicalInference] = field(default_factory=list)
    detected_terms: List[str] = field(default_factory=list)
    categories_detected: Set[str] = field(default_factory=set)
    overall_confidence: float = 1.0
    botanical_relevance: float = 0.0
    measurement_data: Dict[str, Any] = field(default_factory=dict)
    
    # Integration metadata
    enhancement_timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_method: str = "streamlined_plus"

class BotanicalTraitInferenceEngine:
    """
    AI-powered botanical trait inference that enhances existing SVO extraction.
    Designed to integrate seamlessly with user_svo_script.py proven workflow.
    """
    
    def __init__(self, glossary_loader: Optional[OrchidGlossaryLoader] = None,
                 schema_mapper: Optional[GlossarySchemaMapper] = None):
        self.glossary_loader = glossary_loader or get_glossary_loader()
        self.schema_mapper = schema_mapper or get_schema_mapper()
        
        # Inference patterns optimized for orchid terminology
        self._trait_patterns = {}
        self._measurement_patterns = {}
        self._confidence_rules = {}
        self._enhancement_cache = {}
        
        # Performance optimization flags
        self.enable_caching = True
        self.max_cache_size = 1000
        
        self._initialize_inference_patterns()
    
    def _initialize_inference_patterns(self):
        """Initialize AI inference patterns for botanical trait detection"""
        
        # Floral organ inference patterns
        self._trait_patterns['floral_organ'] = {
            'patterns': [
                r'\b(labellum|lip)\b.*?\b(shows?|displays?|has|exhibits?)\b.*?\b(\w+)\b',
                r'\b(petals?|sepals?)\b.*?\b(are|is|appears?|looks?)\b.*?\b(\w+)\b',
                r'\b(column|gynostemium)\b.*?\b(features?|contains?|includes?)\b.*?\b(\w+)\b',
                r'\b(pollinia|anther)\b.*?\b(produces?|releases?|contains?)\b.*?\b(\w+)\b'
            ],
            'confidence_base': 0.8,
            'measurement_units': ['mm', 'cm', 'count'],
            'ai_derivable': True
        }
        
        # Vegetative trait patterns
        self._trait_patterns['vegetative'] = {
            'patterns': [
                r'\b(pseudobulb|bulb)\b.*?\b(grows?|reaches?|measures?)\b.*?\b(\d+(?:\.\d+)?)\s*(mm|cm|inches?)\b',
                r'\b(leaves?|leaf)\b.*?\b(shape|form)\b.*?\b(linear|lanceolate|ovate|oblong)\b',
                r'\b(roots?|rhizome)\b.*?\b(extends?|spreads?|grows?)\b.*?\b(\w+)\b',
                r'\b(aerial\s+roots?)\b.*?\b(absorb|collect|gather)\b.*?\b(\w+)\b'
            ],
            'confidence_base': 0.7,
            'measurement_units': ['mm', 'cm', 'microns'],
            'ai_derivable': True
        }
        
        # Color and pattern inference
        self._trait_patterns['phenotypic'] = {
            'patterns': [
                r'\b(color|colored|colours?)\b.*?\b(base|primary|main)\b.*?\b(\w+)\b',
                r'\b(markings?|patterns?)\b.*?\b(striped|spotted|blotched|tessellated)\b',
                r'\b(overlay|suffusion)\b.*?\b(color|tint|hue)\b.*?\b(\w+)\b',
                r'\b(saturation|intensity)\b.*?\b(vivid|pastel|bright|deep)\b'
            ],
            'confidence_base': 0.75,
            'measurement_units': ['RGB', 'HEX', 'scale'],
            'ai_derivable': True
        }
        
        # Measurement extraction patterns
        self._measurement_patterns = {
            'size_measurements': r'\b(\d+(?:\.\d+)?)\s*(mm|cm|inches?|m)\b',
            'count_measurements': r'\b(\d+)\s*(flowers?|blooms?|petals?|sepals?)\b',
            'ratio_measurements': r'\b(\d+(?:\.\d+)?)\s*(?::|to|ratio)\s*(\d+(?:\.\d+)?)\b',
            'percentage_measurements': r'\b(\d+(?:\.\d+)?)\s*%\b',
            'temperature_measurements': r'\b(\d+(?:\.\d+)?)\s*°?[CF]\b',
            'time_measurements': r'\b(\d+)\s*(days?|weeks?|months?)\b'
        }
        
        # Confidence calculation rules
        self._confidence_rules = {
            'exact_term_match': 0.3,
            'synonym_match': 0.2,
            'measurement_present': 0.25,
            'context_relevance': 0.15,
            'multiple_terms': 0.1,
            'scientific_terminology': 0.2
        }
    
    def infer_botanical_traits(self, svo_tuple: Tuple[str, str, str], 
                             context: str = "") -> EnhancedSVO:
        """
        Main inference method that enhances SVO tuples with botanical intelligence.
        Maintains compatibility with existing user_svo_script.py workflow.
        
        Args:
            svo_tuple: (subject, verb, object) tuple from existing extraction
            context: Additional context text for inference
            
        Returns:
            EnhancedSVO object with botanical inferences
        """
        subject, verb, obj = svo_tuple
        
        # Check cache for performance optimization
        cache_key = f"{subject}_{verb}_{obj}_{hash(context)}"
        if self.enable_caching and cache_key in self._enhancement_cache:
            return self._enhancement_cache[cache_key]
        
        # Create enhanced SVO object
        enhanced = EnhancedSVO(
            subject=subject,
            verb=verb,
            object=obj,
            context_text=context
        )
        
        # Full text for analysis
        full_text = f"{subject} {verb} {obj} {context}".lower()
        
        # Find botanical terms using glossary
        found_terms = self.glossary_loader.find_terms_in_text(full_text)
        enhanced.detected_terms = [term_name for term_name, _ in found_terms]
        
        # Extract categories and build inferences
        for term_name, term_data in found_terms:
            category = term_data.get('category', 'Unknown')
            enhanced.categories_detected.add(category)
            
            # Create botanical inference for each term
            inference = self._create_inference_from_term(
                term_name, term_data, full_text, enhanced
            )
            if inference:
                enhanced.botanical_inferences.append(inference)
        
        # Calculate overall botanical relevance
        enhanced.botanical_relevance = self._calculate_botanical_relevance(enhanced)
        
        # Extract measurement data
        enhanced.measurement_data = self._extract_measurements(full_text)
        
        # Apply confidence boosts based on botanical content
        enhanced.overall_confidence = self._calculate_enhanced_confidence(enhanced)
        
        # Cache result for performance
        if self.enable_caching:
            self._manage_cache(cache_key, enhanced)
        
        return enhanced
    
    def _create_inference_from_term(self, term_name: str, term_data: Dict, 
                                  full_text: str, enhanced_svo: EnhancedSVO) -> Optional[BotanicalInference]:
        """Create a botanical inference from a detected term"""
        
        category = term_data.get('category', 'Unknown')
        ai_derivable = term_data.get('ai_derivable', False)
        measurement_unit = term_data.get('measurement_unit', '')
        
        # Determine if measurement data is possible
        measurement_potential = measurement_unit not in ['text', 'qualitative', '']
        
        # Calculate base confidence
        confidence = 0.5  # Base confidence
        
        # Apply confidence rules
        if term_name.lower() in full_text:
            confidence += self._confidence_rules['exact_term_match']
        
        # Check for synonyms
        synonyms = term_data.get('synonyms', [])
        for synonym in synonyms:
            if synonym.lower() in full_text:
                confidence += self._confidence_rules['synonym_match']
                break
        
        # Check for measurements in text
        if measurement_potential and self._has_measurements(full_text):
            confidence += self._confidence_rules['measurement_present']
        
        # Scientific terminology boost
        if any(sci_term in full_text for sci_term in ['species', 'genus', 'hybrid', 'cultivar']):
            confidence += self._confidence_rules['scientific_terminology']
        
        # Context relevance (basic implementation)
        if category.lower() in enhanced_svo.context_text.lower():
            confidence += self._confidence_rules['context_relevance']
        
        confidence = min(1.0, confidence)
        
        # Extract specific values using patterns
        inferred_values = self._extract_specific_values(term_name, category, full_text)
        
        return BotanicalInference(
            trait_category=category,
            confidence=confidence,
            measurement_potential=measurement_potential,
            ai_derivable=ai_derivable,
            supporting_terms=[term_name] + synonyms,
            inferred_values=inferred_values,
            extraction_method="ai_pattern_analysis"
        )
    
    def _extract_specific_values(self, term_name: str, category: str, text: str) -> Dict[str, Any]:
        """Extract specific values for a botanical term from text"""
        
        values = {}
        
        # Size measurements
        size_matches = re.findall(self._measurement_patterns['size_measurements'], text, re.IGNORECASE)
        if size_matches:
            values['measurements'] = [{'value': float(m[0]), 'unit': m[1]} for m in size_matches]
        
        # Count measurements
        count_matches = re.findall(self._measurement_patterns['count_measurements'], text, re.IGNORECASE)
        if count_matches:
            values['counts'] = [{'count': int(m[0]), 'item': m[1]} for m in count_matches]
        
        # Color extraction (basic)
        color_words = ['red', 'blue', 'green', 'yellow', 'purple', 'white', 'pink', 'orange', 'brown', 'black']
        found_colors = [color for color in color_words if color in text.lower()]
        if found_colors:
            values['colors'] = found_colors
        
        # Category-specific extractions
        if category == 'Floral Organ':
            # Extract floral characteristics
            floral_descriptors = ['large', 'small', 'prominent', 'distinctive', 'beautiful', 'unusual']
            found_descriptors = [desc for desc in floral_descriptors if desc in text.lower()]
            if found_descriptors:
                values['descriptors'] = found_descriptors
        
        elif category == 'Vegetative':
            # Extract growth characteristics
            growth_words = ['grows', 'reaches', 'extends', 'spreads', 'develops']
            found_growth = [word for word in growth_words if word in text.lower()]
            if found_growth:
                values['growth_actions'] = found_growth
        
        return values
    
    def _has_measurements(self, text: str) -> bool:
        """Check if text contains measurement data"""
        for pattern in self._measurement_patterns.values():
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_measurements(self, text: str) -> Dict[str, Any]:
        """Extract all measurement data from text"""
        measurements = {}
        
        for measurement_type, pattern in self._measurement_patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                measurements[measurement_type] = matches
        
        return measurements
    
    def _calculate_botanical_relevance(self, enhanced_svo: EnhancedSVO) -> float:
        """Calculate overall botanical relevance score"""
        
        relevance = 0.0
        
        # Base relevance from term detection
        term_count = len(enhanced_svo.detected_terms)
        if term_count > 0:
            relevance += min(0.5, term_count * 0.1)
        
        # Category diversity bonus
        category_count = len(enhanced_svo.categories_detected)
        if category_count > 1:
            relevance += min(0.2, (category_count - 1) * 0.05)
        
        # Measurement data bonus
        if enhanced_svo.measurement_data:
            relevance += 0.2
        
        # AI-derivable traits bonus
        ai_derivable_count = sum(1 for inf in enhanced_svo.botanical_inferences if inf.ai_derivable)
        if ai_derivable_count > 0:
            relevance += min(0.3, ai_derivable_count * 0.1)
        
        return min(1.0, relevance)
    
    def _calculate_enhanced_confidence(self, enhanced_svo: EnhancedSVO) -> float:
        """Calculate enhanced confidence score with botanical boost"""
        
        base_confidence = enhanced_svo.overall_confidence
        
        # Botanical relevance boost
        botanical_boost = enhanced_svo.botanical_relevance * 0.2
        
        # High-confidence inference boost
        high_conf_inferences = sum(1 for inf in enhanced_svo.botanical_inferences if inf.confidence > 0.8)
        high_conf_boost = min(0.15, high_conf_inferences * 0.05)
        
        # Measurement data boost
        measurement_boost = 0.1 if enhanced_svo.measurement_data else 0.0
        
        total_confidence = base_confidence + botanical_boost + high_conf_boost + measurement_boost
        
        return min(1.0, total_confidence)
    
    def _manage_cache(self, cache_key: str, enhanced_svo: EnhancedSVO):
        """Manage enhancement cache with size limits"""
        
        if len(self._enhancement_cache) >= self.max_cache_size:
            # Remove oldest entries (simple FIFO)
            oldest_key = next(iter(self._enhancement_cache))
            del self._enhancement_cache[oldest_key]
        
        self._enhancement_cache[cache_key] = enhanced_svo
    
    def batch_enhance_svo_results(self, svo_results: List[Tuple[str, str, str]], 
                                contexts: Optional[List[str]] = None) -> List[EnhancedSVO]:
        """
        Batch process multiple SVO results for efficiency.
        Maintains compatibility with user_svo_script.py batch processing.
        """
        
        if contexts is None:
            contexts = [""] * len(svo_results)
        
        enhanced_results = []
        
        for i, svo_tuple in enumerate(svo_results):
            context = contexts[i] if i < len(contexts) else ""
            enhanced = self.infer_botanical_traits(svo_tuple, context)
            enhanced_results.append(enhanced)
        
        return enhanced_results
    
    def generate_enhancement_summary(self, enhanced_results: List[EnhancedSVO]) -> Dict[str, Any]:
        """Generate summary statistics for enhanced results"""
        
        if not enhanced_results:
            return {}
        
        # Calculate summary statistics
        total_enhanced = len(enhanced_results)
        botanical_relevant = sum(1 for r in enhanced_results if r.botanical_relevance > 0.5)
        high_confidence = sum(1 for r in enhanced_results if r.overall_confidence > 0.8)
        
        # Category distribution
        all_categories = []
        for result in enhanced_results:
            all_categories.extend(result.categories_detected)
        category_distribution = dict(Counter(all_categories))
        
        # Term frequency
        all_terms = []
        for result in enhanced_results:
            all_terms.extend(result.detected_terms)
        term_frequency = dict(Counter(all_terms).most_common(20))
        
        # Measurement statistics
        with_measurements = sum(1 for r in enhanced_results if r.measurement_data)
        
        summary = {
            'total_processed': total_enhanced,
            'botanically_relevant': botanical_relevant,
            'high_confidence': high_confidence,
            'relevance_rate': botanical_relevant / total_enhanced if total_enhanced > 0 else 0,
            'confidence_rate': high_confidence / total_enhanced if total_enhanced > 0 else 0,
            'category_distribution': category_distribution,
            'top_terms': term_frequency,
            'with_measurements': with_measurements,
            'measurement_rate': with_measurements / total_enhanced if total_enhanced > 0 else 0,
            'average_relevance': sum(r.botanical_relevance for r in enhanced_results) / total_enhanced,
            'average_confidence': sum(r.overall_confidence for r in enhanced_results) / total_enhanced
        }
        
        return summary
    
    def export_enhanced_results(self, enhanced_results: List[EnhancedSVO], 
                              format_type: str = 'json') -> str:
        """Export enhanced results in various formats"""
        
        if format_type == 'json':
            export_data = []
            for result in enhanced_results:
                export_item = {
                    'svo': {
                        'subject': result.subject,
                        'verb': result.verb,
                        'object': result.object,
                        'context': result.context_text
                    },
                    'botanical_enhancement': {
                        'detected_terms': result.detected_terms,
                        'categories': list(result.categories_detected),
                        'relevance_score': result.botanical_relevance,
                        'confidence_score': result.overall_confidence,
                        'inferences': [
                            {
                                'category': inf.trait_category,
                                'confidence': inf.confidence,
                                'measurement_potential': inf.measurement_potential,
                                'ai_derivable': inf.ai_derivable,
                                'inferred_values': inf.inferred_values
                            }
                            for inf in result.botanical_inferences
                        ],
                        'measurements': result.measurement_data,
                        'timestamp': result.enhancement_timestamp.isoformat()
                    }
                }
                export_data.append(export_item)
            
            return json.dumps(export_data, indent=2, ensure_ascii=False)
        
        # Add other format types as needed (CSV, XML, etc.)
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def get_inference_stats(self) -> Dict[str, Any]:
        """Get statistics about the inference engine"""
        
        return {
            'cache_size': len(self._enhancement_cache),
            'max_cache_size': self.max_cache_size,
            'trait_patterns_loaded': len(self._trait_patterns),
            'measurement_patterns_loaded': len(self._measurement_patterns),
            'confidence_rules_loaded': len(self._confidence_rules),
            'caching_enabled': self.enable_caching,
            'glossary_terms_available': len(self.glossary_loader._glossary_data.get('terms', {})) if (self.glossary_loader and hasattr(self.glossary_loader, '_glossary_data') and self.glossary_loader._glossary_data) else 0
        }


# Global inference engine instance
_global_inference_engine = None

def get_inference_engine() -> BotanicalTraitInferenceEngine:
    """Get global inference engine instance"""
    global _global_inference_engine
    if _global_inference_engine is None:
        _global_inference_engine = BotanicalTraitInferenceEngine()
    return _global_inference_engine


# Integration functions for user_svo_script.py compatibility
def enhance_svo_tuple(svo_tuple: Tuple[str, str, str], context: str = "") -> EnhancedSVO:
    """Convenience function for enhancing single SVO tuple"""
    engine = get_inference_engine()
    return engine.infer_botanical_traits(svo_tuple, context)

def enhance_svo_batch(svo_list: List[Tuple[str, str, str]], 
                     contexts: Optional[List[str]] = None) -> List[EnhancedSVO]:
    """Convenience function for batch enhancement compatible with user_svo_script.py"""
    engine = get_inference_engine()
    return engine.batch_enhance_svo_results(svo_list, contexts)


if __name__ == "__main__":
    # Test the inference engine
    engine = BotanicalTraitInferenceEngine()
    
    print("✅ Botanical Trait Inference Engine initialized!")
    print(f"📊 Engine stats: {engine.get_inference_stats()}")
    
    # Test single SVO enhancement
    test_svo = ("orchid", "displays", "labellum")
    test_context = "The beautiful Phalaenopsis orchid displays a prominent white labellum with purple markings measuring 3.2 cm across"
    
    enhanced = engine.infer_botanical_traits(test_svo, test_context)
    print(f"🌺 Enhanced SVO result:")
    print(f"  - Detected terms: {enhanced.detected_terms}")
    print(f"  - Categories: {list(enhanced.categories_detected)}")
    print(f"  - Botanical relevance: {enhanced.botanical_relevance:.2f}")
    print(f"  - Overall confidence: {enhanced.overall_confidence:.2f}")
    print(f"  - Inferences: {len(enhanced.botanical_inferences)}")
    print(f"  - Measurements: {enhanced.measurement_data}")
    
    # Test batch processing
    test_batch = [
        ("cattleya", "produces", "flowers"),
        ("dendrobium", "grows", "pseudobulbs"),
        ("paphiopedilum", "shows", "slipper")
    ]
    
    enhanced_batch = engine.batch_enhance_svo_results(test_batch)
    summary = engine.generate_enhancement_summary(enhanced_batch)
    print(f"🔬 Batch processing summary: {summary}")
    
    print("🎉 Inference engine test completed!")