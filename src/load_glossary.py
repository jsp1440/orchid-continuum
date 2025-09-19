#!/usr/bin/env python3
"""
Orchid Botanical Glossary Loader Module
=======================================

Efficient loading and caching of botanical terminology for enhanced SVO analysis.
Provides fast lookups and term matching capabilities while integrating seamlessly
with the existing high-performance SVO extraction system.
"""

import json
import os
import logging
import csv
from pathlib import Path
from functools import lru_cache
from typing import Dict, List, Optional, Set, Tuple
import re
from collections import defaultdict

logger = logging.getLogger(__name__)

class OrchidGlossaryLoader:
    """
    High-performance botanical glossary loader with caching and fast lookups.
    Designed to enhance SVO analysis without compromising the 17x performance advantage.
    """
    
    def __init__(self, glossary_path: str = 'data/glossary/Orchid_Floral_Glossary_Master.json'):
        self.glossary_path = glossary_path
        self._glossary_data = None
        self._terms_cache = {}
        self._lookup_cache = {}
        self._pattern_cache = {}
        self.loaded = False
        
        # Performance optimization: pre-compiled regex patterns
        self._word_pattern = re.compile(r'\b\w+\b', re.IGNORECASE)
        self._clean_pattern = re.compile(r'[^\w\s]')
        
    def load_glossary(self, force_reload: bool = False) -> bool:
        """
        Load the botanical glossary from JSON file with caching.
        
        Args:
            force_reload: Force reload even if already loaded
            
        Returns:
            bool: True if loaded successfully, False otherwise
        """
        if self.loaded and not force_reload:
            return True
            
        try:
            if not os.path.exists(self.glossary_path):
                logger.error(f"Glossary file not found: {self.glossary_path}")
                return False
                
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                self._glossary_data = json.load(f)
                
            # Build optimized lookup structures
            self._build_lookup_caches()
            
            self.loaded = True
            logger.info(f"Successfully loaded {len(self._glossary_data['terms'])} botanical terms")
            return True
            
        except Exception as e:
            logger.error(f"Error loading glossary: {str(e)}")
            return False
    
    def load_glossary_csv(self, csv_path: str, force_reload: bool = False) -> bool:
        """
        Load the botanical glossary from CSV file with robust validation.
        
        Args:
            csv_path: Path to CSV file
            force_reload: Force reload even if already loaded
            
        Returns:
            bool: True if loaded successfully with ≥50 terms, False otherwise
        """
        if self.loaded and not force_reload:
            return True
            
        try:
            if not os.path.exists(csv_path):
                logger.error(f"CSV glossary file not found: {csv_path}")
                return False
                
            # Parse CSV and convert to expected JSON structure
            terms = {}
            term_count = 0
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    term_name = row.get('Term', '').strip()
                    if not term_name:
                        continue
                        
                    # Parse synonyms (handle various formats)
                    synonyms_str = row.get('Synonyms', '')
                    synonyms = []
                    if synonyms_str and synonyms_str.lower() not in ['none', 'n/a', '']:
                        # Split by common delimiters
                        synonyms = [s.strip() for s in re.split(r'[;,|]', synonyms_str) if s.strip()]
                    
                    # Parse AI_Derivable (handle boolean conversion)
                    ai_derivable_str = row.get('AI_Derivable', 'False').strip()
                    ai_derivable = ai_derivable_str.lower() in ['true', '1', 'yes']
                    
                    # Build term data structure
                    terms[term_name] = {
                        'category': row.get('Category', '').strip(),
                        'definition': row.get('Definition', '').strip(),
                        'synonyms': synonyms,
                        'search_variants': synonyms,  # Use synonyms as search variants
                        'standard_source': row.get('Standard Source', '').strip(),
                        'ai_derivable': ai_derivable,
                        'measurement_unit': row.get('Measurement Unit', '').strip()
                    }
                    
                    term_count += 1
            
            # Validation: require at least 50 terms
            if term_count < 50:
                logger.error(f"CSV validation failed: only {term_count} terms found, minimum 50 required")
                return False
            
            # Create expected JSON structure
            self._glossary_data = {
                'metadata': {
                    'source': 'CSV import',
                    'version': '1.0',
                    'term_count': term_count,
                    'source_file': csv_path
                },
                'terms': terms
            }
            
            # Build optimized lookup structures
            self._build_lookup_caches()
            
            self.loaded = True
            logger.info(f"✅ Successfully loaded {term_count} botanical terms from CSV")
            logger.info(f"📊 Categories: {len(set(t.get('category', '') for t in terms.values() if t.get('category')))}")
            logger.info(f"🔬 AI derivable terms: {sum(1 for t in terms.values() if t.get('ai_derivable', False))}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading CSV glossary: {str(e)}")
            return False
    
    def _build_lookup_caches(self):
        """Build optimized lookup caches for fast term matching"""
        if not self._glossary_data:
            return
            
        # Clear existing caches
        self._terms_cache.clear()
        self._lookup_cache.clear()
        self._pattern_cache.clear()
        
        terms = self._glossary_data.get('terms', {})
        
        # Build terms cache by category for faster filtering
        for term_name, term_data in terms.items():
            category = term_data.get('category', 'Unknown')
            if category not in self._terms_cache:
                self._terms_cache[category] = {}
            self._terms_cache[category][term_name] = term_data
            
        # Build optimized lookup index for substring matching
        for term_name, term_data in terms.items():
            # Primary term
            key = term_name.lower()
            self._lookup_cache[key] = term_name
            
            # Synonyms
            for synonym in term_data.get('synonyms', []):
                syn_key = synonym.lower()
                self._lookup_cache[syn_key] = term_name
                
            # Search variants
            for variant in term_data.get('search_variants', []):
                var_key = variant.lower()
                if var_key not in self._lookup_cache:
                    self._lookup_cache[var_key] = term_name
        
        logger.debug(f"Built lookup cache with {len(self._lookup_cache)} entries")
    
    @lru_cache(maxsize=1000)
    def get_term_info(self, term: str) -> Optional[Dict]:
        """
        Get complete information for a botanical term.
        
        Args:
            term: The term to look up
            
        Returns:
            Dict with term information or None if not found
        """
        if not self.loaded:
            self.load_glossary()
            
        if not self._glossary_data:
            return None
            
        # Direct lookup first
        term_data = self._glossary_data['terms'].get(term)
        if term_data:
            return term_data
            
        # Try lowercase lookup
        term_lower = term.lower()
        canonical_term = self._lookup_cache.get(term_lower)
        if canonical_term:
            return self._glossary_data['terms'].get(canonical_term)
            
        return None
    
    def find_terms_in_text(self, text: str, categories: Optional[List[str]] = None) -> List[Tuple[str, Dict]]:
        """
        Find botanical terms present in given text.
        Optimized for SVO analysis integration.
        
        Args:
            text: Text to search for botanical terms
            categories: Optional list of categories to filter by
            
        Returns:
            List of tuples (found_term, term_info)
        """
        if not self.loaded:
            self.load_glossary()
            
        if not text or not self._glossary_data:
            return []
            
        found_terms = []
        text_lower = text.lower()
        
        # Fast word-based matching
        words = set(self._word_pattern.findall(text_lower))
        
        # Check each word against our lookup cache
        for word in words:
            canonical_term = self._lookup_cache.get(word)
            if canonical_term:
                term_info = self._glossary_data['terms'][canonical_term]
                
                # Filter by category if specified
                if categories and term_info.get('category') not in categories:
                    continue
                    
                found_terms.append((canonical_term, term_info))
        
        # Check for multi-word terms (more expensive, so we do this second)
        for lookup_key, canonical_term in self._lookup_cache.items():
            if ' ' in lookup_key and lookup_key in text_lower:
                if canonical_term not in [t[0] for t in found_terms]:  # Avoid duplicates
                    term_info = self._glossary_data['terms'][canonical_term]
                    
                    # Filter by category if specified
                    if categories and term_info.get('category') not in categories:
                        continue
                        
                    found_terms.append((canonical_term, term_info))
        
        return found_terms
    
    def get_category_terms(self, category: str) -> Dict[str, Dict]:
        """
        Get all terms for a specific category.
        
        Args:
            category: Category name (e.g., 'Floral Organ', 'Judging Trait')
            
        Returns:
            Dict of terms in the category
        """
        if not self.loaded:
            self.load_glossary()
            
        return self._terms_cache.get(category, {})
    
    def get_all_categories(self) -> List[str]:
        """Get list of all available categories"""
        if not self.loaded:
            self.load_glossary()
            
        return list(self._terms_cache.keys()) if self._terms_cache else []
    
    def get_ai_derivable_terms(self) -> Dict[str, Dict]:
        """Get terms that are AI-derivable for enhanced analysis"""
        if not self.loaded:
            self.load_glossary()
            
        ai_terms = {}
        if self._glossary_data:
            for term_name, term_data in self._glossary_data.get('terms', {}).items():
                if term_data and term_data.get('ai_derivable', False):
                    ai_terms[term_name] = term_data
                
        return ai_terms
    
    def get_measurement_terms(self) -> Dict[str, Dict]:
        """Get terms with measurement units for quantitative analysis"""
        if not self.loaded:
            self.load_glossary()
            
        measurement_terms = {}
        if self._glossary_data:
            for term_name, term_data in self._glossary_data.get('terms', {}).items():
                if term_data:
                    measurement_unit = term_data.get('measurement_unit', '')
                    if measurement_unit and measurement_unit not in ['text', 'qualitative']:
                        measurement_terms[term_name] = term_data
                
        return measurement_terms
    
    def enhance_svo_tuple(self, subject: str, verb: str, obj: str) -> Dict:
        """
        Enhance an SVO tuple with botanical terminology information.
        Designed to integrate with existing SVO extraction workflow.
        
        Args:
            subject: Subject from SVO tuple
            verb: Verb from SVO tuple
            obj: Object from SVO tuple
            
        Returns:
            Dict with enhancement information
        """
        enhancement = {
            'original_svo': (subject, verb, obj),
            'botanical_terms_found': [],
            'categories_detected': set(),
            'measurement_potential': False,
            'ai_derivable_traits': [],
            'confidence_boost': 0.0
        }
        
        # Analyze each component
        full_text = f"{subject} {verb} {obj}"
        found_terms = self.find_terms_in_text(full_text)
        
        for term_name, term_info in found_terms:
            enhancement['botanical_terms_found'].append(term_name)
            enhancement['categories_detected'].add(term_info.get('category'))
            
            if term_info.get('ai_derivable', False):
                enhancement['ai_derivable_traits'].append(term_name)
                
            measurement_unit = term_info.get('measurement_unit', '')
            if measurement_unit and measurement_unit not in ['text', 'qualitative']:
                enhancement['measurement_potential'] = True
        
        # Calculate confidence boost based on botanical relevance
        enhancement['confidence_boost'] = min(0.3, len(found_terms) * 0.1)
        enhancement['categories_detected'] = list(enhancement['categories_detected'])
        
        return enhancement
    
    def get_stats(self) -> Dict:
        """Get statistics about the loaded glossary"""
        if not self.loaded:
            self.load_glossary()
            
        if not self._glossary_data:
            return {}
            
        metadata = self._glossary_data.get('metadata', {})
        return {
            'total_terms': metadata.get('total_terms', 0),
            'categories': metadata.get('categories', {}),
            'ai_derivable_count': metadata.get('ai_derivable_count', 0),
            'measurement_units': metadata.get('measurement_units', []),
            'cache_size': len(self._lookup_cache)
        }


# Global instance for efficient reuse
_global_glossary_loader = None

def get_glossary_loader() -> OrchidGlossaryLoader:
    """Get the global glossary loader instance"""
    global _global_glossary_loader
    if _global_glossary_loader is None:
        _global_glossary_loader = OrchidGlossaryLoader()
        _global_glossary_loader.load_glossary()
    return _global_glossary_loader

def find_botanical_terms(text: str, categories: Optional[List[str]] = None) -> List[Tuple[str, Dict]]:
    """Convenience function for finding botanical terms in text"""
    loader = get_glossary_loader()
    return loader.find_terms_in_text(text, categories)

def enhance_svo_with_botany(subject: str, verb: str, obj: str) -> Dict:
    """Convenience function for enhancing SVO tuples with botanical knowledge"""
    loader = get_glossary_loader()
    return loader.enhance_svo_tuple(subject, verb, obj)


# Example usage and testing
if __name__ == "__main__":
    # Test the glossary loader
    loader = OrchidGlossaryLoader()
    
    if loader.load_glossary():
        print("✅ Glossary loaded successfully!")
        print(f"📊 Stats: {loader.get_stats()}")
        
        # Test term lookup
        test_term = loader.get_term_info("Labellum")
        if test_term:
            print(f"🔍 Found term 'Labellum': {test_term['definition']}")
        
        # Test text analysis
        test_text = "The orchid labellum shows beautiful purple petals with distinctive markings"
        found = loader.find_terms_in_text(test_text)
        print(f"🌺 Found {len(found)} botanical terms in test text: {[t[0] for t in found]}")
        
        # Test SVO enhancement
        enhancement = loader.enhance_svo_tuple("orchid", "displays", "petals")
        print(f"🧬 SVO enhancement: {enhancement}")
        
    else:
        print("❌ Failed to load glossary")