#!/usr/bin/env python3
"""
Glossary to Database Schema Mapping Module
==========================================

Maps botanical glossary terms to existing database models (SvoResult, OrchidTaxonomy)
for enhanced integration and data consistency. Provides seamless integration with
the existing high-performance Flask/SQLAlchemy system.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Import database models (will be imported from main app context)
try:
    from models import SvoResult, OrchidTaxonomy, SvoAnalysisSession, db
except ImportError:
    logger.warning("Database models not available in standalone mode")
    SvoResult = None
    OrchidTaxonomy = None
    SvoAnalysisSession = None
    db = None

from load_glossary import OrchidGlossaryLoader, get_glossary_loader

class TermCategory(Enum):
    """Enumeration of botanical term categories"""
    FLORAL_ORGAN = "Floral Organ"
    JUDGING_TRAIT = "Judging Trait"
    QUANTITATIVE_TRAIT = "Quantitative Trait"
    VEGETATIVE = "Vegetative"
    PHENOTYPIC_TRAIT = "Phenotypic Trait"
    MORPHOLOGICAL = "Morphological"
    PHENOLOGICAL = "Phenological"
    TAXONOMIC = "Taxonomic"

@dataclass
class TermMapping:
    """Mapping information between glossary terms and database fields"""
    term_name: str
    category: str
    db_model: str
    db_field: str
    data_type: str
    measurement_unit: str
    ai_derivable: bool
    extraction_pattern: Optional[str] = None
    validation_rules: Optional[Dict] = None

class GlossarySchemaMapper:
    """
    Maps botanical glossary terms to database schema for enhanced SVO analysis.
    Provides seamless integration with existing models while adding botanical intelligence.
    """
    
    def __init__(self, glossary_loader: Optional[OrchidGlossaryLoader] = None):
        self.glossary_loader = glossary_loader or get_glossary_loader()
        self._mappings = {}
        self._field_mappings = {}
        self._enhancement_rules = {}
        self._initialized = False
        
    def initialize_mappings(self) -> bool:
        """Initialize the mappings between glossary terms and database schema"""
        if self._initialized:
            return True
            
        try:
            self._build_svo_result_mappings()
            self._build_orchid_taxonomy_mappings()
            self._build_enhancement_rules()
            self._initialized = True
            logger.info("Schema mappings initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing schema mappings: {str(e)}")
            return False
    
    def _build_svo_result_mappings(self):
        """Build mappings for SvoResult model enhancements"""
        
        # Core SVO fields that can be enhanced with botanical knowledge
        svo_mappings = {
            # Botanical categorization fields
            'botanical_category': {
                'terms': ['Floral Organ', 'Judging Trait', 'Vegetative', 'Phenotypic Trait'],
                'data_type': 'string',
                'ai_derivable': True,
                'extraction_method': 'category_detection'
            },
            
            'is_scientific_term': {
                'terms': 'all',  # Any glossary term detection
                'data_type': 'boolean', 
                'ai_derivable': True,
                'extraction_method': 'term_presence'
            },
            
            'relevance_score': {
                'terms': 'all',
                'data_type': 'float',
                'ai_derivable': True,
                'extraction_method': 'confidence_calculation'
            },
            
            'confidence_score': {
                'terms': 'measurement',  # Terms with measurement units
                'data_type': 'float',
                'ai_derivable': True,
                'extraction_method': 'botanical_confidence_boost'
            }
        }
        
        self._field_mappings['SvoResult'] = svo_mappings
        
        # Build specific term mappings for SvoResult
        if self.glossary_loader and hasattr(self.glossary_loader, '_glossary_data') and self.glossary_loader._glossary_data:
            for term_name, term_data in self.glossary_loader._glossary_data.get('terms', {}).items():
                if term_data:
                    category = term_data.get('category')
                    measurement_unit = term_data.get('measurement_unit', '')
                    ai_derivable = term_data.get('ai_derivable', False)
                    
                    mapping = TermMapping(
                        term_name=term_name,
                        category=category,
                        db_model='SvoResult',
                        db_field='botanical_category',
                        data_type='string',
                        measurement_unit=measurement_unit,
                        ai_derivable=ai_derivable,
                        extraction_pattern=self._generate_extraction_pattern(term_name, term_data)
                    )
                    
                    self._mappings[f"svo_{term_name.lower().replace(' ', '_')}"] = mapping
    
    def _build_orchid_taxonomy_mappings(self):
        """Build mappings for OrchidTaxonomy model enhancements"""
        
        taxonomy_mappings = {
            'genus': {
                'terms': ['Taxonomic'],
                'data_type': 'string',
                'ai_derivable': False,
                'extraction_method': 'genus_extraction'
            },
            
            'species': {
                'terms': ['Taxonomic'],
                'data_type': 'string', 
                'ai_derivable': False,
                'extraction_method': 'species_extraction'
            },
            
            'synonyms': {
                'terms': ['Grex', 'Cultivar'],
                'data_type': 'json',
                'ai_derivable': True,
                'extraction_method': 'synonym_detection'
            },
            
            'common_names': {
                'terms': ['Taxonomic'],
                'data_type': 'json',
                'ai_derivable': True,
                'extraction_method': 'common_name_extraction'
            }
        }
        
        self._field_mappings['OrchidTaxonomy'] = taxonomy_mappings
        
        # Build specific mappings for taxonomic terms
        taxonomic_terms = self.glossary_loader.get_category_terms('Taxonomic')
        for term_name, term_data in taxonomic_terms.items():
            mapping = TermMapping(
                term_name=term_name,
                category='Taxonomic',
                db_model='OrchidTaxonomy',
                db_field='synonyms',  # Most taxonomic terms affect synonyms
                data_type='json',
                measurement_unit=term_data.get('measurement_unit', ''),
                ai_derivable=term_data.get('ai_derivable', False)
            )
            
            self._mappings[f"tax_{term_name.lower().replace(' ', '_')}"] = mapping
    
    def _build_enhancement_rules(self):
        """Build rules for enhancing SVO analysis with botanical knowledge"""
        
        self._enhancement_rules = {
            'floral_description': {
                'categories': ['Floral Organ', 'Phenotypic Trait'],
                'confidence_boost': 0.3,
                'relevance_threshold': 0.7,
                'required_terms': ['labellum', 'petals', 'sepals']
            },
            
            'growth_characteristics': {
                'categories': ['Vegetative', 'Morphological'],
                'confidence_boost': 0.2,
                'relevance_threshold': 0.6,
                'required_terms': ['pseudobulb', 'rhizome', 'root']
            },
            
            'judging_qualities': {
                'categories': ['Judging Trait', 'Quantitative Trait'],
                'confidence_boost': 0.25,
                'relevance_threshold': 0.8,
                'required_terms': ['form', 'substance', 'presentation']
            },
            
            'measurement_data': {
                'categories': ['Quantitative Trait'],
                'confidence_boost': 0.4,
                'relevance_threshold': 0.9,
                'measurement_required': True
            }
        }
    
    def _generate_extraction_pattern(self, term_name: str, term_data: Dict) -> str:
        """Generate regex pattern for extracting term from text"""
        # Base pattern for the term itself
        term_pattern = term_name.lower().replace('(', r'\(?').replace(')', r'\)?')
        
        # Add synonym patterns
        synonyms = term_data.get('synonyms', [])
        if synonyms:
            synonym_patterns = '|'.join([syn.lower() for syn in synonyms if syn != 'none'])
            if synonym_patterns:
                term_pattern = f"({term_pattern}|{synonym_patterns})"
        
        # Word boundary pattern for accurate matching
        return fr"\b{term_pattern}\b"
    
    def enhance_svo_result(self, svo_result_data: Dict) -> Dict:
        """
        Enhance SVO result data with botanical terminology mappings.
        
        Args:
            svo_result_data: Raw SVO data dictionary
            
        Returns:
            Enhanced SVO data with botanical categorization
        """
        if not self._initialized:
            self.initialize_mappings()
        
        enhanced_data = svo_result_data.copy()
        
        # Extract text for analysis
        subject = svo_result_data.get('subject', '')
        verb = svo_result_data.get('verb', '')
        obj = svo_result_data.get('object', '')
        context = svo_result_data.get('context_text', '')
        
        full_text = f"{subject} {verb} {obj} {context}"
        
        # Find botanical terms
        found_terms = self.glossary_loader.find_terms_in_text(full_text)
        
        if found_terms:
            # Determine botanical category
            categories_found = [term_data.get('category') for _, term_data in found_terms]
            most_common_category = max(set(categories_found), key=categories_found.count)
            enhanced_data['botanical_category'] = most_common_category
            
            # Mark as scientific term
            enhanced_data['is_scientific_term'] = True
            
            # Calculate enhanced relevance score
            base_relevance = enhanced_data.get('relevance_score', 0.5)
            botanical_boost = min(0.4, len(found_terms) * 0.1)
            enhanced_data['relevance_score'] = min(1.0, base_relevance + botanical_boost)
            
            # Apply enhancement rules
            for rule_name, rule_config in self._enhancement_rules.items():
                if most_common_category in rule_config.get('categories', []):
                    confidence_boost = rule_config.get('confidence_boost', 0.0)
                    current_confidence = enhanced_data.get('confidence_score', 1.0)
                    enhanced_data['confidence_score'] = min(1.0, current_confidence + confidence_boost)
                    break
            
            # Add metadata about found terms
            enhanced_data['botanical_terms_detected'] = [term_name for term_name, _ in found_terms]
            enhanced_data['botanical_enhancement_applied'] = True
        
        else:
            enhanced_data['is_scientific_term'] = False
            enhanced_data['botanical_enhancement_applied'] = False
        
        return enhanced_data
    
    def extract_taxonomy_info(self, text: str) -> Dict:
        """
        Extract taxonomy information from text for OrchidTaxonomy model.
        
        Args:
            text: Text to extract taxonomy info from
            
        Returns:
            Dictionary with taxonomy information
        """
        if not self._initialized:
            self.initialize_mappings()
        
        taxonomy_info = {
            'genus_candidates': [],
            'species_candidates': [],
            'common_names': [],
            'taxonomic_terms_found': [],
            'confidence': 0.0
        }
        
        # Find taxonomic terms
        taxonomic_terms = self.glossary_loader.find_terms_in_text(text, ['Taxonomic'])
        
        for term_name, term_data in taxonomic_terms:
            taxonomy_info['taxonomic_terms_found'].append(term_name)
            
            # Extract genus/species patterns (basic implementation)
            # This would be enhanced with more sophisticated NLP
            words = text.lower().split()
            for i, word in enumerate(words):
                if word.istitle() and i < len(words) - 1:
                    next_word = words[i + 1]
                    if next_word.islower():
                        taxonomy_info['genus_candidates'].append(word.capitalize())
                        taxonomy_info['species_candidates'].append(next_word.lower())
        
        taxonomy_info['confidence'] = min(1.0, len(taxonomic_terms) * 0.2)
        
        return taxonomy_info
    
    def get_field_mappings(self, model_name: str) -> Dict:
        """Get field mappings for a specific model"""
        if not self._initialized:
            self.initialize_mappings()
        return self._field_mappings.get(model_name, {})
    
    def get_term_mapping(self, term_name: str) -> Optional[TermMapping]:
        """Get mapping information for a specific term"""
        if not self._initialized:
            self.initialize_mappings()
        
        # Try different key formats
        key_variations = [
            f"svo_{term_name.lower().replace(' ', '_')}",
            f"tax_{term_name.lower().replace(' ', '_')}",
            term_name.lower().replace(' ', '_')
        ]
        
        for key in key_variations:
            if key in self._mappings:
                return self._mappings[key]
        
        return None
    
    def validate_enhanced_data(self, enhanced_data: Dict, model_name: str) -> Tuple[bool, List[str]]:
        """
        Validate enhanced data against model constraints.
        
        Args:
            enhanced_data: Enhanced data dictionary
            model_name: Target model name
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        field_mappings = self.get_field_mappings(model_name)
        
        for field_name, field_config in field_mappings.items():
            if field_name in enhanced_data:
                value = enhanced_data[field_name]
                data_type = field_config.get('data_type')
                
                # Type validation
                if data_type == 'float' and not isinstance(value, (int, float)):
                    errors.append(f"Field {field_name} must be numeric, got {type(value)}")
                elif data_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field {field_name} must be boolean, got {type(value)}")
                elif data_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field {field_name} must be string, got {type(value)}")
                
                # Range validation for numeric fields
                if data_type == 'float' and isinstance(value, (int, float)):
                    if field_name in ['confidence_score', 'relevance_score'] and not 0 <= value <= 1:
                        errors.append(f"Field {field_name} must be between 0 and 1, got {value}")
        
        return len(errors) == 0, errors
    
    def get_stats(self) -> Dict:
        """Get mapping statistics"""
        if not self._initialized:
            self.initialize_mappings()
            
        return {
            'total_mappings': len(self._mappings),
            'svo_mappings': len([k for k in self._mappings.keys() if k.startswith('svo_')]),
            'taxonomy_mappings': len([k for k in self._mappings.keys() if k.startswith('tax_')]),
            'enhancement_rules': len(self._enhancement_rules),
            'supported_models': list(self._field_mappings.keys())
        }


# Global mapper instance
_global_mapper = None

def get_schema_mapper() -> GlossarySchemaMapper:
    """Get global schema mapper instance"""
    global _global_mapper
    if _global_mapper is None:
        _global_mapper = GlossarySchemaMapper()
        _global_mapper.initialize_mappings()
    return _global_mapper


# Convenience functions for integration
def enhance_svo_with_schema(svo_data: Dict) -> Dict:
    """Convenience function to enhance SVO data with schema mapping"""
    mapper = get_schema_mapper()
    return mapper.enhance_svo_result(svo_data)

def extract_taxonomy_from_text(text: str) -> Dict:
    """Convenience function to extract taxonomy info from text"""
    mapper = get_schema_mapper()
    return mapper.extract_taxonomy_info(text)


if __name__ == "__main__":
    # Test the schema mapper
    mapper = GlossarySchemaMapper()
    
    if mapper.initialize_mappings():
        print("✅ Schema mappings initialized!")
        print(f"📊 Stats: {mapper.get_stats()}")
        
        # Test SVO enhancement
        test_svo = {
            'subject': 'orchid',
            'verb': 'displays',
            'object': 'labellum',
            'context_text': 'The beautiful orchid displays a prominent labellum with distinctive petals',
            'confidence_score': 0.8,
            'relevance_score': 0.6
        }
        
        enhanced = mapper.enhance_svo_result(test_svo)
        print(f"🧬 Enhanced SVO: {enhanced}")
        
        # Test taxonomy extraction
        taxonomy_text = "Phalaenopsis amabilis shows beautiful white flowers"
        taxonomy_info = mapper.extract_taxonomy_info(taxonomy_text)
        print(f"🔬 Taxonomy info: {taxonomy_info}")
        
    else:
        print("❌ Failed to initialize mappings")