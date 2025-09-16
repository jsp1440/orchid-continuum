#!/usr/bin/env python3
"""
SVO (Subject-Verb-Object) Parser Module

This module extracts Subject-Verb-Object tuples from orchid-related web content
using NLP techniques and pattern matching. Designed to identify care instructions,
growing conditions, and botanical relationships from scraped data.

Features:
- Advanced NLP-based SVO extraction
- Orchid-specific pattern recognition
- Confidence scoring for extracted tuples
- Multi-source content processing
- Quality filtering and validation
- Batch processing capabilities
"""

import re
import logging
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, field, asdict
from collections import Counter, defaultdict
import hashlib

# Import NLP libraries
try:
    import spacy
    from spacy import displacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False
    logging.warning("⚠️  spaCy not available - using fallback pattern matching")

from bs4 import BeautifulSoup, Comment
import html

# Import fetcher results
from .fetcher import FetchResult

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SVOTuple:
    """Represents an extracted Subject-Verb-Object tuple"""
    subject: str
    verb: str
    object: str
    confidence: float = 0.0
    source_url: str = ""
    source_category: str = ""
    context: str = ""  # Surrounding text for context
    extraction_method: str = ""  # nlp, pattern, hybrid
    raw_sentence: str = ""
    position_in_text: int = 0
    extracted_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """Clean up extracted text"""
        self.subject = self._clean_text(self.subject)
        self.verb = self._clean_text(self.verb)
        self.object = self._clean_text(self.object)
        self.context = self._clean_text(self.context)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        if not text:
            return ""
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove HTML entities
        text = html.unescape(text)
        
        # Remove special characters but keep botanical terms
        text = re.sub(r'[^\w\s\-\.\'°×]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    @property
    def tuple_id(self) -> str:
        """Generate unique ID for this tuple"""
        content = f"{self.subject}|{self.verb}|{self.object}|{self.source_url}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    @property
    def is_valid(self) -> bool:
        """Check if this is a valid tuple"""
        return (
            len(self.subject.strip()) >= 2 and
            len(self.verb.strip()) >= 2 and
            len(self.object.strip()) >= 2 and
            self.confidence >= 0.1
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['extracted_at'] = self.extracted_at.isoformat()
        result['tuple_id'] = self.tuple_id
        result['is_valid'] = self.is_valid
        return result
    
    def __str__(self) -> str:
        return f"SVOTuple('{self.subject}' → '{self.verb}' → '{self.object}', conf={self.confidence:.2f})"

class SVOParser:
    """Advanced SVO parser with NLP and pattern matching capabilities"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the SVO parser
        
        Args:
            config: Configuration dictionary from config.py
        """
        self.config = config
        self.svo_patterns = config.get('svo_patterns', {})
        self.quality_thresholds = config.get('quality_thresholds', {})
        
        # Initialize NLP pipeline
        self.nlp = None
        self._init_nlp()
        
        # Pattern matching regexes
        self._init_patterns()
        
        # Statistics tracking
        self.stats = {
            'processed_documents': 0,
            'extracted_tuples': 0,
            'valid_tuples': 0,
            'nlp_extractions': 0,
            'pattern_extractions': 0,
            'processing_time': 0.0
        }
    
    def _init_nlp(self):
        """Initialize spaCy NLP pipeline if available"""
        if not SPACY_AVAILABLE:
            logger.warning("📝 NLP disabled - using pattern matching only")
            return
            
        try:
            # Try to load English model
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("🧠 spaCy NLP pipeline initialized")
        except OSError:
            try:
                # Fallback to smaller model
                self.nlp = spacy.load("en_core_web_md")
                logger.info("🧠 spaCy NLP pipeline initialized (medium model)")
            except OSError:
                logger.warning("📝 spaCy models not found - using pattern matching only")
                self.nlp = None
    
    def _init_patterns(self):
        """Initialize regex patterns for orchid-specific extraction"""
        
        # Subject patterns (orchid-related terms)
        subject_terms = self.svo_patterns.get('subject_indicators', [])
        subject_pattern = '|'.join(re.escape(term) for term in subject_terms)
        
        # Verb patterns (action/condition terms) 
        verb_terms = self.svo_patterns.get('verb_indicators', [])
        verb_pattern = '|'.join(re.escape(term) for term in verb_terms)
        
        # Object patterns (care/environment terms)
        object_terms = self.svo_patterns.get('object_indicators', [])
        object_pattern = '|'.join(re.escape(term) for term in object_terms)
        
        # Compile comprehensive patterns
        self.patterns = {
            'simple_svo': re.compile(
                rf'\b([A-Z][a-z]*\s*(?:{subject_pattern})[a-z]*)\s+'
                rf'((?:{verb_pattern})[a-z]*)\s+'
                rf'([a-z]*\s*(?:{object_pattern})[a-z]*\s*[^.!?]*)',
                re.IGNORECASE | re.MULTILINE
            ),
            
            'care_instruction': re.compile(
                r'([A-Z][a-zA-Z\s]+?(?:orchid|hybrid|species|variety))\s+'
                r'(needs?|requires?|prefers?|grows?|blooms?)\s+'
                r'([a-z][^.!?]{10,100})',
                re.IGNORECASE
            ),
            
            'botanical_relationship': re.compile(
                r'([A-Z][a-zA-Z\s]+?)\s+'
                r'(is|are|produces?|develops?|forms?)\s+'
                r'(a\s+[a-z][^.!?]{5,80})',
                re.IGNORECASE
            ),
            
            'growing_condition': re.compile(
                r'([A-Z][a-zA-Z\s]*(?:orchid|plant)s?)\s+'
                r'(thrive|grow|prefer|require|need)\s+'
                r'(in\s+[^.!?]{5,100}|[^.!?]{5,100})',
                re.IGNORECASE
            ),
            
            'flowering_info': re.compile(
                r'([A-Z][a-zA-Z\s]+?)\s+'
                r'(flowers?|blooms?|produces?)\s+'
                r'([^.!?]{10,150})',
                re.IGNORECASE
            )
        }
    
    def extract_text_from_html(self, html_content: str) -> str:
        """Extract clean text from HTML content"""
        if not html_content.strip():
            return ""
            
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "meta", "link"]):
                script.decompose()
            
            # Remove comments
            for comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
                comment.extract()
            
            # Get text and clean it
            text = soup.get_text(separator=' ', strip=True)
            
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text)
            text = re.sub(r'\n+', '\n', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"❌ Error extracting text from HTML: {e}")
            return html_content  # Fallback to raw content
    
    def extract_svo_with_nlp(self, text: str, source_info: Dict[str, str]) -> List[SVOTuple]:
        """Extract SVO tuples using spaCy NLP"""
        if not self.nlp or not text.strip():
            return []
        
        tuples = []
        
        try:
            # Process text with spaCy
            doc = self.nlp(text)
            
            # Extract sentences and analyze dependency parse
            for sent in doc.sents:
                sent_text = sent.text.strip()
                if len(sent_text) < 20:  # Skip very short sentences
                    continue
                
                # Find subjects, verbs, and objects
                subjects = []
                verbs = []
                objects = []
                
                for token in sent:
                    # Subject detection (including compound subjects)
                    if token.dep_ in ['nsubj', 'nsubjpass', 'csubj', 'compound']:
                        if self._is_orchid_related(token.text):
                            subjects.append(token.text)
                    
                    # Verb detection (main verbs and auxiliaries)
                    elif token.dep_ in ['ROOT'] and token.pos_ in ['VERB']:
                        if self._is_care_verb(token.lemma_):
                            verbs.append(token.lemma_)
                    
                    # Object detection (direct objects, complements)
                    elif token.dep_ in ['dobj', 'pobj', 'attr', 'acomp']:
                        if self._is_care_object(token.text):
                            objects.append(token.text)
                
                # Create tuples from combinations
                for subject in subjects:
                    for verb in verbs:
                        for obj in objects:
                            confidence = self._calculate_nlp_confidence(
                                subject, verb, obj, sent_text
                            )
                            
                            if confidence >= self.quality_thresholds.get('min_svo_confidence', 0.5):
                                tuple_obj = SVOTuple(
                                    subject=subject,
                                    verb=verb,
                                    object=obj,
                                    confidence=confidence,
                                    source_url=source_info.get('url', ''),
                                    source_category=source_info.get('category', ''),
                                    context=sent_text,
                                    extraction_method='nlp',
                                    raw_sentence=sent_text,
                                    position_in_text=sent.start_char
                                )
                                tuples.append(tuple_obj)
                                self.stats['nlp_extractions'] += 1
        
        except Exception as e:
            logger.error(f"❌ NLP extraction error: {e}")
        
        return tuples
    
    def extract_svo_with_patterns(self, text: str, source_info: Dict[str, str]) -> List[SVOTuple]:
        """Extract SVO tuples using regex patterns"""
        if not text.strip():
            return []
        
        tuples = []
        
        for pattern_name, pattern in self.patterns.items():
            try:
                matches = pattern.finditer(text)
                
                for match in matches:
                    if len(match.groups()) >= 3:
                        subject, verb, obj = match.groups()[:3]
                        
                        # Calculate pattern-based confidence
                        confidence = self._calculate_pattern_confidence(
                            subject, verb, obj, pattern_name, match.group(0)
                        )
                        
                        if confidence >= self.quality_thresholds.get('min_svo_confidence', 0.3):
                            tuple_obj = SVOTuple(
                                subject=subject,
                                verb=verb,
                                object=obj,
                                confidence=confidence,
                                source_url=source_info.get('url', ''),
                                source_category=source_info.get('category', ''),
                                context=match.group(0),
                                extraction_method=f'pattern_{pattern_name}',
                                raw_sentence=match.group(0),
                                position_in_text=match.start()
                            )
                            tuples.append(tuple_obj)
                            self.stats['pattern_extractions'] += 1
                            
            except Exception as e:
                logger.error(f"❌ Pattern '{pattern_name}' extraction error: {e}")
        
        return tuples
    
    def _is_orchid_related(self, text: str) -> bool:
        """Check if text contains orchid-related terms"""
        orchid_terms = ['orchid', 'hybrid', 'species', 'variety', 'cultivar', 
                       'cattleya', 'phalaenopsis', 'dendrobium', 'oncidium',
                       'paphiopedilum', 'vanda', 'cymbidium', 'masdevallia']
        text_lower = text.lower()
        return any(term in text_lower for term in orchid_terms)
    
    def _is_care_verb(self, verb: str) -> bool:
        """Check if verb is care-related"""
        care_verbs = ['grow', 'bloom', 'flower', 'produce', 'develop', 'require', 
                     'need', 'prefer', 'thrive', 'like', 'want', 'enjoy']
        return verb.lower() in care_verbs
    
    def _is_care_object(self, text: str) -> bool:
        """Check if text contains care-related objects"""
        care_objects = ['light', 'water', 'temperature', 'humidity', 'fertilizer', 
                       'care', 'soil', 'potting', 'medium', 'drainage', 'air',
                       'warmth', 'cool', 'bright', 'shade', 'moisture']
        text_lower = text.lower()
        return any(obj in text_lower for obj in care_objects)
    
    def _calculate_nlp_confidence(self, subject: str, verb: str, obj: str, sentence: str) -> float:
        """Calculate confidence score for NLP-extracted tuples"""
        score = 0.0
        
        # Base confidence for NLP extraction
        score += 0.6
        
        # Bonus for orchid-related subjects
        if self._is_orchid_related(subject):
            score += 0.2
        
        # Bonus for care-related verbs
        if self._is_care_verb(verb):
            score += 0.1
        
        # Bonus for care-related objects
        if self._is_care_object(obj):
            score += 0.1
        
        # Length penalties/bonuses
        if len(sentence) > 200:
            score -= 0.1  # Very long sentences are less reliable
        elif 50 <= len(sentence) <= 150:
            score += 0.1  # Good length range
        
        return min(1.0, score)
    
    def _calculate_pattern_confidence(self, subject: str, verb: str, obj: str, 
                                    pattern_name: str, full_match: str) -> float:
        """Calculate confidence score for pattern-extracted tuples"""
        score = 0.0
        
        # Base confidence varies by pattern type
        pattern_confidence = {
            'care_instruction': 0.8,
            'botanical_relationship': 0.7,
            'growing_condition': 0.75,
            'flowering_info': 0.65,
            'simple_svo': 0.5
        }
        score += pattern_confidence.get(pattern_name, 0.4)
        
        # Quality adjustments
        if len(subject) < 3 or len(verb) < 3 or len(obj) < 3:
            score -= 0.2
        
        if len(full_match) > 300:
            score -= 0.1
        
        # Orchid specificity bonus
        if self._is_orchid_related(subject) and self._is_care_object(obj):
            score += 0.15
        
        return min(1.0, max(0.0, score))
    
    def deduplicate_tuples(self, tuples: List[SVOTuple]) -> List[SVOTuple]:
        """Remove duplicate and very similar tuples"""
        if not tuples:
            return []
        
        # Group by similarity
        seen = set()
        deduplicated = []
        
        for tuple_obj in tuples:
            # Create a normalized key for comparison
            key = (
                tuple_obj.subject.lower().strip(),
                tuple_obj.verb.lower().strip(),
                tuple_obj.object.lower().strip()[:50]  # Limit object length for comparison
            )
            
            if key not in seen:
                seen.add(key)
                deduplicated.append(tuple_obj)
        
        # Sort by confidence (highest first)
        deduplicated.sort(key=lambda x: x.confidence, reverse=True)
        
        logger.info(f"🔍 Deduplicated: {len(tuples)} → {len(deduplicated)} unique tuples")
        return deduplicated
    
    def filter_quality(self, tuples: List[SVOTuple]) -> List[SVOTuple]:
        """Filter tuples based on quality thresholds"""
        min_confidence = self.quality_thresholds.get('min_svo_confidence', 0.5)
        min_length = self.quality_thresholds.get('min_text_length', 10)
        max_length = self.quality_thresholds.get('max_text_length', 500)
        
        filtered = []
        for tuple_obj in tuples:
            # Check confidence threshold
            if tuple_obj.confidence < min_confidence:
                continue
                
            # Check text length
            total_length = len(tuple_obj.subject + tuple_obj.verb + tuple_obj.object)
            if total_length < min_length or total_length > max_length:
                continue
            
            # Check validity
            if not tuple_obj.is_valid:
                continue
            
            filtered.append(tuple_obj)
        
        logger.info(f"✨ Quality filtered: {len(tuples)} → {len(filtered)} high-quality tuples")
        return filtered

def parse_svo(fetch_results: List[FetchResult], config: Dict[str, Any]) -> List[SVOTuple]:
    """
    Main function to parse SVO tuples from fetched data
    
    Args:
        fetch_results: List of FetchResult objects from fetcher.fetch_all()
        config: Configuration dictionary (from config.CONFIG)
        
    Returns:
        List of SVOTuple objects containing extracted SVO tuples
    """
    logger.info("🧠 Starting SVO parsing pipeline")
    
    # Initialize parser
    parser = SVOParser(config)
    
    # Process all successful fetch results
    all_tuples = []
    successful_results = [r for r in fetch_results if r.success]
    
    logger.info(f"📄 Processing {len(successful_results)} successful fetch results")
    
    for i, result in enumerate(successful_results):
        try:
            # Extract clean text from HTML
            clean_text = parser.extract_text_from_html(result.content)
            
            if not clean_text.strip():
                logger.warning(f"⚠️  No text extracted from {result.url}")
                continue
            
            # Prepare source info
            source_info = {
                'url': result.url,
                'category': result.source_category,
                'domain': result.domain
            }
            
            # Extract tuples using both methods
            nlp_tuples = []
            pattern_tuples = []
            
            if parser.nlp:
                nlp_tuples = parser.extract_svo_with_nlp(clean_text, source_info)
            
            pattern_tuples = parser.extract_svo_with_patterns(clean_text, source_info)
            
            # Combine results
            document_tuples = nlp_tuples + pattern_tuples
            all_tuples.extend(document_tuples)
            
            parser.stats['processed_documents'] += 1
            parser.stats['extracted_tuples'] += len(document_tuples)
            
            if (i + 1) % 10 == 0 or (i + 1) == len(successful_results):
                logger.info(f"📊 Progress: {i + 1}/{len(successful_results)} documents | "
                           f"{len(all_tuples)} tuples extracted")
                           
        except Exception as e:
            logger.error(f"❌ Error processing {result.url}: {e}")
    
    # Post-processing
    logger.info("🔧 Post-processing extracted tuples...")
    
    # Deduplicate
    unique_tuples = parser.deduplicate_tuples(all_tuples)
    
    # Quality filtering
    high_quality_tuples = parser.filter_quality(unique_tuples)
    
    parser.stats['valid_tuples'] = len(high_quality_tuples)
    
    # Final summary
    logger.info("=" * 60)
    logger.info("🧠 SVO PARSING SUMMARY")
    logger.info(f"📄 Documents processed: {parser.stats['processed_documents']}")
    logger.info(f"🔍 Raw tuples extracted: {parser.stats['extracted_tuples']}")
    logger.info(f"🧠 NLP extractions: {parser.stats['nlp_extractions']}")
    logger.info(f"🔣 Pattern extractions: {parser.stats['pattern_extractions']}")
    logger.info(f"✨ Unique tuples: {len(unique_tuples)}")
    logger.info(f"⭐ High-quality tuples: {len(high_quality_tuples)}")
    logger.info("=" * 60)
    
    return high_quality_tuples

if __name__ == "__main__":
    # Test the parser module
    from .fetcher import fetch_all
    from config import URLS, CONFIG
    
    logger.info("🧪 Testing SVO parser module")
    
    # First fetch some data
    fetch_results = fetch_all(URLS, CONFIG)
    
    # Then parse SVO tuples
    svo_tuples = parse_svo(fetch_results, CONFIG)
    
    logger.info(f"✅ Test complete: extracted {len(svo_tuples)} SVO tuples")
    
    # Show some examples
    for i, tuple_obj in enumerate(svo_tuples[:5]):
        logger.info(f"Example {i+1}: {tuple_obj}")