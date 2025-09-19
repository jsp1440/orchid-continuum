"""
SVO Data Processing and Cleaning Module

This module provides functions for cleaning, normalizing, and preprocessing
Subject-Verb-Object data extracted from orchid care sources.

Functions:
- clean_svo(): Main cleaning and normalization function
- normalize_text(): Text normalization utilities
- extract_patterns(): Pattern extraction helpers
- validate_svo(): Data validation functions
"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union, Optional, Any
from dataclasses import dataclass
from collections import Counter
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import SVOTuple from scraper.parser to maintain consistency
from scraper.parser import SVOTuple

class SVOProcessor:
    """Main class for SVO data processing and cleaning"""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize processor with configuration"""
        self.config = config or self._get_default_config()
        self.subject_patterns = self._compile_patterns('subject_indicators')
        self.verb_patterns = self._compile_patterns('verb_indicators') 
        self.object_patterns = self._compile_patterns('object_indicators')
        
    def _get_default_config(self) -> Dict:
        """Get default configuration for processing"""
        return {
            'svo_patterns': {
                'subject_indicators': ['orchid', 'hybrid', 'species', 'variety', 'cultivar'],
                'verb_indicators': ['grows', 'blooms', 'flowers', 'produces', 'develops', 'requires'],
                'object_indicators': ['light', 'water', 'temperature', 'humidity', 'fertilizer', 'care']
            },
            'quality_thresholds': {
                'min_svo_confidence': 0.7,
                'min_text_length': 20,
                'max_text_length': 1000
            },
            'normalization': {
                'lowercase': True,
                'remove_punctuation': True,
                'standardize_terms': True
            }
        }
    
    def _compile_patterns(self, pattern_type: str) -> List[re.Pattern]:
        """Compile regex patterns for matching"""
        indicators = self.config['svo_patterns'].get(pattern_type, [])
        patterns = []
        for indicator in indicators:
            # Create case-insensitive patterns with word boundaries
            pattern = re.compile(rf'\b{re.escape(indicator)}\b', re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def normalize_text(self, text: str) -> str:
        """Normalize text according to configuration"""
        if not isinstance(text, str):
            return ""
            
        normalized = text.strip()
        
        # Use safe config access with defaults
        normalization_config = self.config.get('normalization', {})
        
        if normalization_config.get('lowercase', True):
            normalized = normalized.lower()
            
        if normalization_config.get('remove_punctuation', True):
            # Keep essential punctuation, remove excessive
            normalized = re.sub(r'[^\w\s\-\.]', ' ', normalized)
            normalized = re.sub(r'\s+', ' ', normalized)
            
        if normalization_config.get('standardize_terms', True):
            normalized = self._standardize_terms(normalized)
            
        return normalized.strip()
    
    def _standardize_terms(self, text: str) -> str:
        """Standardize common orchid care terms"""
        standardizations = {
            'temp': 'temperature',
            'temps': 'temperature', 
            'watering': 'water',
            'lighting': 'light',
            'fertilizing': 'fertilizer',
            'blooming': 'blooms',
            'flowering': 'flowers'
        }
        
        for old_term, new_term in standardizations.items():
            text = re.sub(rf'\b{old_term}\b', new_term, text, flags=re.IGNORECASE)
            
        return text
    
    def extract_svo_candidates(self, text: str) -> List[Dict]:
        """Extract potential SVO triples from text"""
        normalized_text = self.normalize_text(text)
        sentences = re.split(r'[.!?]+', normalized_text)
        
        candidates = []
        
        for sentence in sentences:
            min_length = self.config.get('quality_thresholds', {}).get('min_text_length', 20)
            if len(sentence.strip()) < min_length:
                continue
                
            # Find subjects, verbs, objects
            subjects = self._find_matches(sentence, self.subject_patterns)
            verbs = self._find_matches(sentence, self.verb_patterns)
            objects = self._find_matches(sentence, self.object_patterns)
            
            # Create SVO combinations
            for subject in subjects:
                for verb in verbs:
                    for obj in objects:
                        confidence = self._calculate_confidence(subject, verb, obj, sentence)
                        min_confidence = self.config.get('quality_thresholds', {}).get('min_svo_confidence', 0.7)
                        if confidence >= min_confidence:
                            candidates.append({
                                'subject': subject,
                                'verb': verb,
                                'object': obj,
                                'confidence': confidence,
                                'sentence': sentence.strip()
                            })
        
        return candidates
    
    def _find_matches(self, text: str, patterns: List[re.Pattern]) -> List[str]:
        """Find pattern matches in text"""
        matches = []
        for pattern in patterns:
            found = pattern.findall(text)
            matches.extend(found)
        return list(set(matches))  # Remove duplicates
    
    def _calculate_confidence(self, subject: str, verb: str, obj: str, sentence: str) -> float:
        """Calculate confidence score for SVO triple"""
        base_score = 0.5
        
        # Boost for proximity (closer words = higher confidence)
        words = sentence.split()
        try:
            subj_idx = next(i for i, w in enumerate(words) if subject.lower() in w.lower())
            verb_idx = next(i for i, w in enumerate(words) if verb.lower() in w.lower())
            obj_idx = next(i for i, w in enumerate(words) if obj.lower() in w.lower())
            
            # Calculate proximity score
            max_dist = max(abs(verb_idx - subj_idx), abs(obj_idx - verb_idx))
            proximity_score = max(0, (10 - max_dist) / 10)
            
            base_score += proximity_score * 0.3
            
        except StopIteration:
            # If we can't find positions, use base score
            pass
        
        # Boost for sentence coherence
        if len(sentence.split()) >= 5:  # Complete sentences
            base_score += 0.1
            
        # Boost for orchid-specific context
        orchid_terms = ['orchid', 'plant', 'flower', 'bloom', 'care', 'grow']
        context_matches = sum(1 for term in orchid_terms if term in sentence.lower())
        base_score += min(context_matches * 0.05, 0.2)
        
        return min(base_score, 1.0)  # Cap at 1.0
    
    def validate_svo(self, svo_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """Validate SVO data and separate valid/invalid entries"""
        valid_entries = []
        invalid_entries = []
        
        for entry in svo_data:
            is_valid = True
            validation_errors = []
            
            # Check required fields
            required_fields = ['subject', 'verb', 'object', 'confidence']
            for field in required_fields:
                if field not in entry or not entry[field]:
                    is_valid = False
                    validation_errors.append(f"Missing or empty {field}")
            
            # Check confidence threshold
            if 'confidence' in entry:
                if entry['confidence'] < self.config['quality_thresholds']['min_svo_confidence']:
                    is_valid = False
                    validation_errors.append(f"Confidence {entry['confidence']} below threshold")
            
            # Check text lengths
            for field in ['subject', 'verb', 'object']:
                if field in entry and isinstance(entry[field], str):
                    if len(entry[field]) < 2:
                        is_valid = False
                        validation_errors.append(f"{field} too short")
            
            if is_valid:
                valid_entries.append(entry)
            else:
                entry['validation_errors'] = validation_errors
                invalid_entries.append(entry)
        
        logger.info(f"Validation complete: {len(valid_entries)} valid, {len(invalid_entries)} invalid")
        return valid_entries, invalid_entries
    
    def deduplicate_svo(self, svo_data: List[Dict]) -> List[Dict]:
        """Remove duplicate SVO entries"""
        seen = set()
        deduplicated = []
        
        for entry in svo_data:
            # Create a key for deduplication
            key = (
                entry.get('subject', '').lower(),
                entry.get('verb', '').lower(), 
                entry.get('object', '').lower()
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(entry)
        
        logger.info(f"Deduplication: {len(svo_data)} -> {len(deduplicated)} entries")
        return deduplicated

def clean_svo(data: Union[List[Dict], pd.DataFrame, str, List[Any]], config: Optional[Dict] = None) -> Dict:
    """
    Main function for cleaning and normalizing SVO data.
    
    Args:
        data: Input data (list of dicts, DataFrame, text string, or list of SVOTuple objects)
        config: Optional configuration dictionary
        
    Returns:
        Dictionary containing cleaned data and processing statistics
    """
    processor = SVOProcessor(config)
    
    # Handle different input types
    if isinstance(data, str):
        # Extract SVO from text
        svo_candidates = processor.extract_svo_candidates(data)
        raw_data = svo_candidates
    elif isinstance(data, pd.DataFrame):
        # Convert DataFrame to list of dicts
        raw_data = data.to_dict('records')
    elif isinstance(data, list):
        # Check if list contains SVOTuple objects (has to_dict method)
        if data and hasattr(data[0], 'to_dict') and callable(getattr(data[0], 'to_dict')):
            # Convert SVOTuple objects to dictionaries
            logger.info(f"Converting {len(data)} SVOTuple objects to dictionary format")
            raw_data = [item.to_dict() for item in data]
        else:
            # Assume it's already a list of dictionaries
            raw_data = data
    else:
        raise ValueError(f"Unsupported data type: {type(data)}")
    
    # Process the data
    logger.info(f"Processing {len(raw_data)} SVO entries")
    
    # Validate data
    valid_data, invalid_data = processor.validate_svo(raw_data)
    
    # Deduplicate
    cleaned_data = processor.deduplicate_svo(valid_data)
    
    # Normalize text fields
    for entry in cleaned_data:
        entry['subject'] = processor.normalize_text(entry['subject'])
        entry['verb'] = processor.normalize_text(entry['verb'])
        entry['object'] = processor.normalize_text(entry['object'])
    
    # Calculate statistics
    stats = {
        'total_input': len(raw_data),
        'valid_entries': len(valid_data),
        'invalid_entries': len(invalid_data),
        'final_cleaned': len(cleaned_data),
        'deduplication_rate': (len(valid_data) - len(cleaned_data)) / max(len(valid_data), 1),
        'validation_rate': len(valid_data) / max(len(raw_data), 1),
        'subject_diversity': len(set(entry['subject'] for entry in cleaned_data)),
        'verb_diversity': len(set(entry['verb'] for entry in cleaned_data)),
        'object_diversity': len(set(entry['object'] for entry in cleaned_data)),
        'avg_confidence': np.mean([entry['confidence'] for entry in cleaned_data]) if cleaned_data else 0
    }
    
    result = {
        'cleaned_data': cleaned_data,
        'invalid_data': invalid_data,
        'statistics': stats,
        'processor_config': processor.config
    }
    
    logger.info(f"Cleaning complete: {stats['final_cleaned']} clean entries, "
               f"{stats['validation_rate']:.2%} validation rate")
    
    return result