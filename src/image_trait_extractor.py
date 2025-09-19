#!/usr/bin/env python3
"""
Advanced Image Trait Extraction Module
=====================================

Implements OpenAI Vision-powered trait extraction for orchid specimens with sophisticated
confidence scoring, validation, and ensemble methods. Designed for research-grade accuracy
in botanical trait inference from photographic evidence.

Key Features:
- OpenAI GPT-4 Vision API integration with secure key management
- Weighted ensemble combining AI, glossary, and heuristic methods  
- Advanced confidence scoring with botanical validation
- Image hash-based caching and intelligent rate limiting
- Trait normalization to canonical botanical schema
"""

import os
import json
import logging
import hashlib
import time
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import base64
import re
from collections import defaultdict

# OpenAI integration
try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Image processing
try:
    from PIL import Image, ImageStat
    import io
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

# Botanical modules
try:
    from load_glossary import get_glossary_loader
    from ai_trait_inference import get_inference_engine
    BOTANICAL_AVAILABLE = True
except ImportError:
    BOTANICAL_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class TraitExtraction:
    """Container for extracted trait information with confidence and validation"""
    trait_name: str
    value: str
    confidence: float
    extraction_method: str  # 'openai_vision', 'glossary_match', 'heuristic'
    validation_status: str  # 'validated', 'pending', 'rejected', 'needs_review'
    supporting_evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ImageAnalysisResult:
    """Complete analysis result for an orchid image"""
    image_path: str
    image_hash: str
    extracted_traits: List[TraitExtraction] = field(default_factory=list)
    overall_confidence: float = 0.0
    processing_time: float = 0.0
    ensemble_weights: Dict[str, float] = field(default_factory=dict)
    validation_summary: Dict[str, int] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    
class AdvancedImageTraitExtractor:
    """
    Research-grade orchid trait extraction using ensemble AI methods.
    Combines OpenAI Vision, botanical glossary matching, and heuristic analysis.
    """
    
    def __init__(self, 
                 cache_dir: str = "data/cache/image_analysis",
                 rate_limit_requests_per_minute: int = 10,
                 ensemble_weights: Optional[Dict[str, float]] = None):
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting
        self.rate_limit = rate_limit_requests_per_minute
        self.request_times = []
        
        # Ensemble configuration (weights must sum to 1.0)
        self.ensemble_weights = ensemble_weights or {
            'openai_vision': 0.40,
            'glossary_match': 0.40, 
            'heuristic': 0.20
        }
        
        # Validate ensemble weights
        if abs(sum(self.ensemble_weights.values()) - 1.0) > 0.01:
            raise ValueError("Ensemble weights must sum to 1.0")
        
        # Initialize components
        self._initialize_openai()
        self._initialize_botanical_components()
        self._load_trait_schemas()
        
        # Performance tracking
        self.analysis_stats = {
            'total_analyses': 0,
            'cache_hits': 0,
            'openai_calls': 0,
            'avg_processing_time': 0.0,
            'confidence_distribution': defaultdict(int)
        }
        
    def _initialize_openai(self):
        """Initialize OpenAI client with secure API key management"""
        self.openai_client = None
        self.openai_available = OPENAI_AVAILABLE
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI library not available - vision analysis disabled")
            return
            
        # Use Replit's secure OpenAI integration
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found - vision analysis disabled")
            self.openai_available = False
            return
            
        try:
            self.openai_client = OpenAI(api_key=api_key)
            logger.info("✅ OpenAI Vision client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            self.openai_available = False
    
    def _initialize_botanical_components(self):
        """Initialize botanical glossary and inference components"""
        self.glossary_loader = None
        self.inference_engine = None
        self.botanical_available = BOTANICAL_AVAILABLE
        
        if not BOTANICAL_AVAILABLE:
            logger.warning("Botanical components not available - using basic analysis")
            return
            
        try:
            self.glossary_loader = get_glossary_loader()
            self.inference_engine = get_inference_engine()
            logger.info("✅ Botanical components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize botanical components: {e}")
            self.botanical_available = False
    
    def _load_trait_schemas(self):
        """Load canonical trait schemas for normalization"""
        self.trait_schemas = {
            'flower_color': {
                'canonical_values': [
                    'white', 'yellow', 'orange', 'red', 'pink', 'purple', 'lavender', 
                    'blue', 'green', 'brown', 'black', 'multicolored', 'spotted', 'striped'
                ],
                'measurement_type': 'categorical',
                'validation_rules': ['color_name_required', 'no_empty_values']
            },
            'flower_shape': {
                'canonical_values': [
                    'flat', 'cupped', 'reflexed', 'twisted', 'tubular', 'bell_shaped',
                    'star_shaped', 'round', 'oval', 'irregular', 'clustered'
                ],
                'measurement_type': 'categorical',
                'validation_rules': ['shape_descriptor_required']
            },
            'flower_size': {
                'canonical_values': ['tiny', 'small', 'medium', 'large', 'very_large'],
                'measurement_type': 'ordinal',
                'validation_rules': ['size_category_required'],
                'measurement_units': ['mm', 'cm', 'inches']
            },
            'petal_count': {
                'canonical_values': ['3', '4', '5', '6', '8', 'many'],
                'measurement_type': 'count',
                'validation_rules': ['numeric_or_category']
            },
            'fragrance': {
                'canonical_values': [
                    'none', 'light', 'moderate', 'strong', 'sweet', 'spicy', 
                    'floral', 'citrus', 'musky', 'unpleasant'
                ],
                'measurement_type': 'categorical',
                'validation_rules': ['fragrance_descriptor_required']
            },
            'growth_habit': {
                'canonical_values': [
                    'epiphytic', 'terrestrial', 'lithophytic', 'climbing', 
                    'compact', 'spreading', 'erect', 'pendulous'
                ],
                'measurement_type': 'categorical',
                'validation_rules': ['habit_type_required']
            }
        }
    
    def extract_traits_from_image(self, image_path: str, 
                                specimen_name: Optional[str] = None,
                                use_cache: bool = True) -> ImageAnalysisResult:
        """
        Extract botanical traits from orchid image using ensemble AI methods.
        
        Args:
            image_path: Path to orchid image
            specimen_name: Optional specimen identifier for context
            use_cache: Whether to use cached results
            
        Returns:
            ImageAnalysisResult with extracted traits and confidence scores
        """
        start_time = time.time()
        
        # Generate image hash for caching
        image_hash = self._calculate_image_hash(image_path)
        
        # Check cache first
        if use_cache:
            cached_result = self._load_from_cache(image_hash)
            if cached_result:
                self.analysis_stats['cache_hits'] += 1
                logger.info(f"📦 Cache hit for image {image_path}")
                return cached_result
        
        # Initialize result object
        result = ImageAnalysisResult(
            image_path=image_path,
            image_hash=image_hash,
            ensemble_weights=self.ensemble_weights.copy()
        )
        
        try:
            # Method 1: OpenAI Vision Analysis (40% weight)
            openai_traits = self._extract_via_openai_vision(image_path, specimen_name)
            
            # Method 2: Botanical Glossary Matching (40% weight)  
            glossary_traits = self._extract_via_glossary_matching(image_path, specimen_name)
            
            # Method 3: Heuristic Analysis (20% weight)
            heuristic_traits = self._extract_via_heuristics(image_path, specimen_name)
            
            # Combine results using weighted ensemble
            result.extracted_traits = self._combine_ensemble_results(
                openai_traits, glossary_traits, heuristic_traits
            )
            
            # Calculate overall confidence and validation summary
            result.overall_confidence = self._calculate_overall_confidence(result.extracted_traits)
            result.validation_summary = self._calculate_validation_summary(result.extracted_traits)
            
        except Exception as e:
            error_msg = f"Error during trait extraction: {str(e)}"
            logger.error(error_msg)
            result.errors.append(error_msg)
        
        # Record processing time
        result.processing_time = time.time() - start_time
        
        # Update statistics
        self.analysis_stats['total_analyses'] += 1
        self.analysis_stats['avg_processing_time'] = (
            (self.analysis_stats['avg_processing_time'] * (self.analysis_stats['total_analyses'] - 1) + 
             result.processing_time) / self.analysis_stats['total_analyses']
        )
        
        # Cache result
        if use_cache:
            self._save_to_cache(image_hash, result)
        
        logger.info(f"✅ Trait extraction completed for {image_path} in {result.processing_time:.2f}s")
        logger.info(f"🎯 Overall confidence: {result.overall_confidence:.3f}")
        
        return result
    
    def _extract_via_openai_vision(self, image_path: str, 
                                 specimen_name: Optional[str]) -> List[TraitExtraction]:
        """Extract traits using OpenAI GPT-4 Vision API"""
        
        if not self.openai_available or not self.openai_client:
            logger.warning("OpenAI Vision not available - skipping")
            return []
        
        # Rate limiting
        self._enforce_rate_limit()
        
        try:
            # Encode image to base64
            base64_image = self._encode_image_to_base64(image_path)
            
            # Construct specialized prompt for orchid analysis
            prompt = self._build_orchid_analysis_prompt(specimen_name)
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=800,
                temperature=0.1  # Low temperature for consistency
            )
            
            self.analysis_stats['openai_calls'] += 1
            
            # Parse response into trait extractions
            traits = self._parse_openai_response(response.choices[0].message.content)
            
            logger.info(f"🤖 OpenAI Vision extracted {len(traits)} traits")
            return traits
            
        except Exception as e:
            logger.error(f"OpenAI Vision analysis failed: {e}")
            return []
    
    def _extract_via_glossary_matching(self, image_path: str, 
                                     specimen_name: Optional[str]) -> List[TraitExtraction]:
        """Extract traits using botanical glossary and inference engine"""
        
        if not self.botanical_available or not self.inference_engine:
            logger.warning("Botanical components not available - skipping glossary matching")
            return []
        
        try:
            # Create context description from image filename and specimen name
            filename = Path(image_path).stem
            context = f"Orchid specimen {specimen_name or filename} showing botanical characteristics"
            
            # Use inference engine to analyze
            enhanced_svo = self.inference_engine.infer_botanical_traits(
                ('orchid', 'displays', 'morphological_features'), 
                context
            )
            
            # Convert botanical inferences to trait extractions
            traits = []
            for inference in enhanced_svo.botanical_inferences:
                # Map botanical categories to trait names
                trait_mappings = {
                    'Phenotypic Trait': ['flower_color', 'fragrance'],
                    'Floral Organ': ['flower_shape', 'petal_count'],
                    'Quantitative Trait': ['flower_size'],
                    'Vegetative': ['growth_habit']
                }
                
                category = inference.trait_category
                possible_traits = trait_mappings.get(category, [])
                
                for trait_name in possible_traits:
                    # Extract values from inference
                    inferred_values = inference.inferred_values
                    value = self._extract_trait_value(trait_name, inferred_values, filename)
                    
                    if value:
                        trait = TraitExtraction(
                            trait_name=trait_name,
                            value=value,
                            confidence=inference.confidence,
                            extraction_method='glossary_match',
                            validation_status='pending',
                            supporting_evidence=inference.supporting_terms,
                            metadata={
                                'category': category,
                                'inference_method': inference.extraction_method,
                                'botanical_relevance': enhanced_svo.botanical_relevance
                            }
                        )
                        traits.append(trait)
            
            logger.info(f"📚 Glossary matching extracted {len(traits)} traits")
            return traits
            
        except Exception as e:
            logger.error(f"Glossary matching failed: {e}")
            return []
    
    def _extract_via_heuristics(self, image_path: str, 
                              specimen_name: Optional[str]) -> List[TraitExtraction]:
        """Extract traits using heuristic rules and image analysis"""
        
        traits = []
        
        try:
            # Basic image analysis for color detection
            if IMAGE_PROCESSING_AVAILABLE:
                color_traits = self._analyze_image_colors(image_path)
                traits.extend(color_traits)
            
            # Filename-based heuristics
            filename_traits = self._analyze_filename_patterns(image_path, specimen_name)
            traits.extend(filename_traits)
            
            # Size estimation from image dimensions
            size_traits = self._estimate_size_from_image(image_path)
            traits.extend(size_traits)
            
            logger.info(f"🧠 Heuristic analysis extracted {len(traits)} traits")
            return traits
            
        except Exception as e:
            logger.error(f"Heuristic analysis failed: {e}")
            return []
    
    def _build_orchid_analysis_prompt(self, specimen_name: Optional[str]) -> str:
        """Build specialized prompt for orchid trait analysis"""
        
        base_prompt = """You are a world-renowned orchid taxonomist analyzing a high-resolution photograph of an orchid specimen. Please provide a detailed botanical analysis focusing on the following traits:

1. **Flower Color**: Describe the primary and secondary colors, including any patterns, spots, or color variations
2. **Flower Shape**: Describe the overall form (flat, cupped, reflexed, etc.) and specific floral organ shapes
3. **Flower Size**: Estimate relative size (tiny/small/medium/large/very_large) 
4. **Petal Count**: Count the visible petals and sepals
5. **Fragrance**: If detectable from visual cues, note any fragrance indicators
6. **Growth Habit**: Determine if epiphytic, terrestrial, or other growth pattern from visible plant structure

Please format your response as a JSON object with these exact keys:
```json
{
    "flower_color": "primary color description",
    "flower_shape": "shape description", 
    "flower_size": "size category",
    "petal_count": "number or description",
    "fragrance": "fragrance assessment or unknown",
    "growth_habit": "growth pattern",
    "confidence_notes": "factors affecting confidence in each assessment"
}
```

Focus on observable botanical characteristics and provide confidence indicators for each trait."""
        
        if specimen_name:
            base_prompt += f"\n\nSpecimen context: {specimen_name}"
        
        return base_prompt
    
    def _parse_openai_response(self, response_text: str) -> List[TraitExtraction]:
        """Parse OpenAI response into structured trait extractions"""
        
        traits = []
        
        try:
            # Extract JSON from response
            json_match = re.search(r'```json\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if not json_match:
                # Try to find JSON without code blocks
                json_match = re.search(r'(\{.*?\})', response_text, re.DOTALL)
            
            if json_match:
                json_data = json.loads(json_match.group(1))
                
                # Convert each trait to TraitExtraction
                confidence_notes = json_data.get('confidence_notes', '')
                
                for trait_name, value in json_data.items():
                    if trait_name == 'confidence_notes':
                        continue
                        
                    if value and value.lower() not in ['unknown', 'unclear', 'not visible']:
                        # Calculate confidence based on response quality
                        confidence = self._calculate_openai_confidence(value, confidence_notes)
                        
                        trait = TraitExtraction(
                            trait_name=trait_name,
                            value=str(value),
                            confidence=confidence,
                            extraction_method='openai_vision',
                            validation_status='pending',
                            supporting_evidence=[confidence_notes],
                            metadata={'raw_response': response_text}
                        )
                        traits.append(trait)
            
        except Exception as e:
            logger.error(f"Failed to parse OpenAI response: {e}")
            # Fallback: try to extract traits from free text
            traits = self._extract_traits_from_text(response_text)
        
        return traits
    
    def _combine_ensemble_results(self, openai_traits: List[TraitExtraction], 
                                glossary_traits: List[TraitExtraction],
                                heuristic_traits: List[TraitExtraction]) -> List[TraitExtraction]:
        """Combine results from all methods using weighted ensemble"""
        
        # Group traits by name
        trait_groups = defaultdict(list)
        
        for trait in openai_traits + glossary_traits + heuristic_traits:
            trait_groups[trait.trait_name].append(trait)
        
        # Combine each trait group
        combined_traits = []
        for trait_name, trait_list in trait_groups.items():
            combined_trait = self._resolve_trait_conflicts(trait_name, trait_list)
            if combined_trait:
                combined_traits.append(combined_trait)
        
        return combined_traits
    
    def _resolve_trait_conflicts(self, trait_name: str, 
                               trait_list: List[TraitExtraction]) -> Optional[TraitExtraction]:
        """Resolve conflicts between different extraction methods for the same trait"""
        
        if not trait_list:
            return None
        
        # Calculate weighted confidence for each unique value
        value_scores = defaultdict(float)
        value_evidence = defaultdict(list)
        
        for trait in trait_list:
            method_weight = self.ensemble_weights.get(trait.extraction_method, 0.0)
            weighted_confidence = trait.confidence * method_weight
            
            # Normalize trait value
            normalized_value = self._normalize_trait_value(trait_name, trait.value)
            
            value_scores[normalized_value] += weighted_confidence
            value_evidence[normalized_value].extend(trait.supporting_evidence)
        
        # Select best value
        if not value_scores:
            return None
            
        best_value = max(value_scores.keys(), key=lambda x: value_scores[x])
        best_confidence = min(value_scores[best_value], 1.0)
        
        # Determine validation status
        validation_status = 'validated' if best_confidence > 0.7 else 'pending'
        if best_confidence < 0.3:
            validation_status = 'needs_review'
        
        return TraitExtraction(
            trait_name=trait_name,
            value=best_value,
            confidence=best_confidence,
            extraction_method='ensemble',
            validation_status=validation_status,
            supporting_evidence=value_evidence[best_value],
            metadata={
                'ensemble_scores': dict(value_scores),
                'method_count': len(trait_list),
                'unanimous_agreement': len(set(t.value for t in trait_list)) == 1
            }
        )
    
    def _calculate_image_hash(self, image_path: str) -> str:
        """Calculate hash of image for caching"""
        try:
            with open(image_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception:
            return hashlib.md5(image_path.encode()).hexdigest()
    
    def _load_from_cache(self, image_hash: str) -> Optional[ImageAnalysisResult]:
        """Load cached analysis result"""
        cache_file = self.cache_dir / f"{image_hash}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                return self._deserialize_result(data)
            except Exception as e:
                logger.warning(f"Failed to load cache: {e}")
        return None
    
    def _save_to_cache(self, image_hash: str, result: ImageAnalysisResult):
        """Save analysis result to cache"""
        cache_file = self.cache_dir / f"{image_hash}.json"
        try:
            serialized = self._serialize_result(result)
            with open(cache_file, 'w') as f:
                json.dump(serialized, f, indent=2, default=str)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def _enforce_rate_limit(self):
        """Enforce OpenAI API rate limiting"""
        current_time = time.time()
        
        # Remove requests older than 1 minute
        self.request_times = [t for t in self.request_times 
                            if current_time - t < 60]
        
        # Check if we're at the rate limit
        if len(self.request_times) >= self.rate_limit:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logger.info(f"⏳ Rate limiting: sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        self.request_times.append(current_time)
    
    def _encode_image_to_base64(self, image_path: str) -> str:
        """Encode image to base64 for OpenAI API"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _calculate_openai_confidence(self, value: str, confidence_notes: str) -> float:
        """Calculate confidence score for OpenAI responses"""
        base_confidence = 0.8  # High base confidence for GPT-4 Vision
        
        # Reduce confidence for uncertain language
        uncertain_words = ['unclear', 'possibly', 'maybe', 'uncertain', 'difficult', 'hard to see']
        uncertainty_penalty = sum(0.1 for word in uncertain_words if word in confidence_notes.lower())
        
        # Boost confidence for detailed descriptions
        detail_bonus = min(0.1, len(value.split()) * 0.02)
        
        confidence = base_confidence - uncertainty_penalty + detail_bonus
        return max(0.1, min(1.0, confidence))
    
    def _extract_traits_from_text(self, text: str) -> List[TraitExtraction]:
        """Fallback method to extract traits from free text"""
        traits = []
        
        # Simple pattern matching for common traits
        patterns = {
            'flower_color': r'(red|blue|green|yellow|purple|white|pink|orange|brown|black|multicolored)',
            'flower_size': r'(tiny|small|medium|large|very large)',
            'fragrance': r'(fragrant|aromatic|no scent|odorless|sweet|spicy)',
            'flower_shape': r'(flat|cupped|reflexed|twisted|tubular|star|round)'
        }
        
        for trait_name, pattern in patterns.items():
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                trait = TraitExtraction(
                    trait_name=trait_name,
                    value=matches[0],
                    confidence=0.6,  # Lower confidence for text extraction
                    extraction_method='openai_vision',
                    validation_status='needs_review',
                    supporting_evidence=[f"Extracted from: {text[:100]}..."]
                )
                traits.append(trait)
        
        return traits
    
    def _normalize_trait_value(self, trait_name: str, value: str) -> str:
        """Normalize trait values to canonical schema"""
        if trait_name not in self.trait_schemas:
            return str(value).lower().strip()
        
        schema = self.trait_schemas[trait_name]
        canonical_values = schema['canonical_values']
        
        value_lower = str(value).lower().strip()
        
        # Direct match
        if value_lower in canonical_values:
            return value_lower
        
        # Fuzzy matching for close values
        for canonical in canonical_values:
            if canonical in value_lower or value_lower in canonical:
                return canonical
        
        # Return original if no match found
        return value_lower
    
    def _extract_trait_value(self, trait_name: str, inferred_values: Dict, filename: str) -> Optional[str]:
        """Extract specific trait value from inference results"""
        
        # Map trait names to inference value keys
        trait_mappings = {
            'flower_color': ['colors', 'color'],
            'flower_shape': ['descriptors', 'shape'],
            'flower_size': ['measurements', 'size'],
            'fragrance': ['fragrance', 'odor'],
            'growth_habit': ['growth_actions', 'habit']
        }
        
        possible_keys = trait_mappings.get(trait_name, [])
        
        for key in possible_keys:
            if key in inferred_values:
                value = inferred_values[key]
                if isinstance(value, list) and value:
                    return str(value[0])
                elif value:
                    return str(value)
        
        # Fallback to filename analysis
        if trait_name == 'flower_color':
            colors = ['red', 'blue', 'green', 'yellow', 'purple', 'white', 'pink', 'orange']
            for color in colors:
                if color in filename.lower():
                    return color
        
        return None
    
    def _analyze_image_colors(self, image_path: str) -> List[TraitExtraction]:
        """Analyze dominant colors in image"""
        if not IMAGE_PROCESSING_AVAILABLE:
            return []
        
        try:
            with Image.open(image_path) as img:
                # Convert to RGB if needed
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Get dominant colors
                img_small = img.resize((150, 150))
                result = img_small.quantize(colors=5)
                
                # Get the most common color (excluding background)
                colors = result.getcolors()
                if colors:
                    # Sort by frequency, skip first (likely background)
                    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                    if len(sorted_colors) > 1:
                        dominant_color = sorted_colors[1][1]  # Second most common
                    else:
                        dominant_color = sorted_colors[0][1]
                    
                    # Convert to RGB
                    rgb = result.palette.getcolor(dominant_color)
                    color_name = self._rgb_to_color_name(rgb)
                    
                    return [TraitExtraction(
                        trait_name='flower_color',
                        value=color_name,
                        confidence=0.6,
                        extraction_method='heuristic',
                        validation_status='pending',
                        supporting_evidence=[f"RGB: {rgb}"],
                        metadata={'rgb_values': rgb}
                    )]
        except Exception as e:
            logger.warning(f"Color analysis failed: {e}")
        
        return []
    
    def _rgb_to_color_name(self, rgb: Tuple[int, int, int]) -> str:
        """Convert RGB values to color name"""
        r, g, b = rgb
        
        # Simple color classification
        if r > 200 and g > 200 and b > 200:
            return 'white'
        elif r < 50 and g < 50 and b < 50:
            return 'black'
        elif r > g and r > b:
            return 'red' if r > 150 else 'brown'
        elif g > r and g > b:
            return 'green'
        elif b > r and b > g:
            return 'blue'
        elif r > 150 and g > 150:
            return 'yellow'
        elif r > 150 and b > 150:
            return 'purple'
        else:
            return 'multicolored'
    
    def _analyze_filename_patterns(self, image_path: str, specimen_name: Optional[str]) -> List[TraitExtraction]:
        """Extract traits from filename patterns"""
        traits = []
        filename = Path(image_path).stem.lower()
        full_text = f"{filename} {specimen_name or ''}".lower()
        
        # Pattern-based extraction
        trait_patterns = {
            'flower_color': {
                'red': ['red', 'crimson', 'scarlet'],
                'blue': ['blue', 'azure', 'navy'],
                'purple': ['purple', 'violet', 'magenta', 'lavender'],
                'yellow': ['yellow', 'gold', 'amber'],
                'white': ['white', 'cream', 'ivory'],
                'pink': ['pink', 'rose'],
                'green': ['green', 'lime'],
                'orange': ['orange', 'coral']
            },
            'flower_size': {
                'large': ['large', 'big', 'giant'],
                'small': ['small', 'mini', 'tiny'],
                'medium': ['medium', 'mid']
            },
            'growth_habit': {
                'epiphytic': ['epiphytic', 'tree'],
                'terrestrial': ['terrestrial', 'ground']
            }
        }
        
        for trait_name, patterns in trait_patterns.items():
            for value, keywords in patterns.items():
                if any(keyword in full_text for keyword in keywords):
                    traits.append(TraitExtraction(
                        trait_name=trait_name,
                        value=value,
                        confidence=0.7,
                        extraction_method='heuristic',
                        validation_status='pending',
                        supporting_evidence=[f"Filename pattern: {filename}"]
                    ))
                    break
        
        return traits
    
    def _estimate_size_from_image(self, image_path: str) -> List[TraitExtraction]:
        """Estimate flower size from image dimensions"""
        if not IMAGE_PROCESSING_AVAILABLE:
            return []
        
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Very rough size estimation based on image resolution
                # This is quite approximate and would need calibration
                pixel_area = width * height
                
                if pixel_area > 2000000:  # > 2MP
                    size_category = 'large'
                    confidence = 0.4
                elif pixel_area > 500000:   # > 0.5MP
                    size_category = 'medium'
                    confidence = 0.3
                else:
                    size_category = 'small'
                    confidence = 0.3
                
                return [TraitExtraction(
                    trait_name='flower_size',
                    value=size_category,
                    confidence=confidence,
                    extraction_method='heuristic',
                    validation_status='needs_review',
                    supporting_evidence=[f"Image dimensions: {width}x{height}"],
                    metadata={'image_dimensions': (width, height), 'pixel_area': pixel_area}
                )]
        except Exception:
            pass
        
        return []
    
    def _calculate_overall_confidence(self, traits: List[TraitExtraction]) -> float:
        """Calculate weighted overall confidence score"""
        if not traits:
            return 0.0
        
        # Weight by extraction method
        method_weights = {
            'ensemble': 1.0,
            'openai_vision': 0.9,
            'glossary_match': 0.8,
            'heuristic': 0.6
        }
        
        weighted_confidences = []
        for trait in traits:
            method_weight = method_weights.get(trait.extraction_method, 0.5)
            weighted_confidence = trait.confidence * method_weight
            weighted_confidences.append(weighted_confidence)
        
        return np.mean(weighted_confidences)
    
    def _calculate_validation_summary(self, traits: List[TraitExtraction]) -> Dict[str, int]:
        """Calculate summary of validation statuses"""
        summary = defaultdict(int)
        for trait in traits:
            summary[trait.validation_status] += 1
        return dict(summary)
    
    def _identify_strong_correlations(self, pearson_corr: np.ndarray, spearman_corr: np.ndarray,
                                   p_values_pearson: np.ndarray, p_values_spearman: np.ndarray,
                                   alpha_corrected: float, trait_columns: List[str]) -> List[Dict]:
        """Identify statistically significant strong correlations"""
        
        strong_correlations = []
        n_traits = len(trait_columns)
        
        for i in range(n_traits):
            for j in range(i+1, n_traits):
                pearson_r = pearson_corr[i, j]
                spearman_r = spearman_corr[i, j]
                p_pearson = p_values_pearson[i, j]
                p_spearman = p_values_spearman[i, j]
                
                # Check for strong correlations (|r| > 0.7) that are significant
                if (abs(pearson_r) > 0.7 and p_pearson < alpha_corrected) or \
                   (abs(spearman_r) > 0.7 and p_spearman < alpha_corrected):
                    
                    strong_correlations.append({
                        'trait1': trait_columns[i],
                        'trait2': trait_columns[j],
                        'pearson_r': pearson_r,
                        'spearman_r': spearman_r,
                        'pearson_p': p_pearson,
                        'spearman_p': p_spearman,
                        'significant_pearson': p_pearson < alpha_corrected,
                        'significant_spearman': p_spearman < alpha_corrected
                    })
        
        return strong_correlations
    
    def _serialize_result(self, result: ImageAnalysisResult) -> Dict:
        """Serialize result for caching"""
        return {
            'image_path': result.image_path,
            'image_hash': result.image_hash,
            'extracted_traits': [
                {
                    'trait_name': t.trait_name,
                    'value': t.value,
                    'confidence': t.confidence,
                    'extraction_method': t.extraction_method,
                    'validation_status': t.validation_status,
                    'supporting_evidence': t.supporting_evidence,
                    'metadata': t.metadata,
                    'timestamp': t.timestamp.isoformat()
                } for t in result.extracted_traits
            ],
            'overall_confidence': result.overall_confidence,
            'processing_time': result.processing_time,
            'ensemble_weights': result.ensemble_weights,
            'validation_summary': result.validation_summary,
            'errors': result.errors
        }
    
    def _deserialize_result(self, data: Dict) -> ImageAnalysisResult:
        """Deserialize cached result"""
        traits = []
        for t_data in data.get('extracted_traits', []):
            trait = TraitExtraction(
                trait_name=t_data['trait_name'],
                value=t_data['value'],
                confidence=t_data['confidence'],
                extraction_method=t_data['extraction_method'],
                validation_status=t_data['validation_status'],
                supporting_evidence=t_data['supporting_evidence'],
                metadata=t_data['metadata'],
                timestamp=datetime.fromisoformat(t_data['timestamp'])
            )
            traits.append(trait)
        
        return ImageAnalysisResult(
            image_path=data['image_path'],
            image_hash=data['image_hash'],
            extracted_traits=traits,
            overall_confidence=data['overall_confidence'],
            processing_time=data['processing_time'],
            ensemble_weights=data['ensemble_weights'],
            validation_summary=data['validation_summary'],
            errors=data['errors']
        )
    
    def get_analysis_stats(self) -> Dict[str, Any]:
        """Get comprehensive analysis statistics"""
        return {
            **self.analysis_stats,
            'cache_hit_rate': (self.analysis_stats['cache_hits'] / 
                             max(self.analysis_stats['total_analyses'], 1)),
            'openai_usage_rate': (self.analysis_stats['openai_calls'] / 
                                max(self.analysis_stats['total_analyses'], 1)),
            'ensemble_weights': self.ensemble_weights,
            'components_available': {
                'openai_vision': self.openai_available,
                'botanical_glossary': self.botanical_available,
                'image_processing': IMAGE_PROCESSING_AVAILABLE
            }
        }

# Convenience functions for easy integration
def extract_traits_from_image(image_path: str, 
                            specimen_name: Optional[str] = None) -> ImageAnalysisResult:
    """Convenience function for single image analysis"""
    extractor = AdvancedImageTraitExtractor()
    return extractor.extract_traits_from_image(image_path, specimen_name)

def batch_extract_traits(image_paths: List[str], 
                        specimen_names: Optional[List[str]] = None) -> List[ImageAnalysisResult]:
    """Convenience function for batch analysis"""
    extractor = AdvancedImageTraitExtractor()
    results = []
    
    for i, image_path in enumerate(image_paths):
        specimen_name = specimen_names[i] if specimen_names and i < len(specimen_names) else None
        result = extractor.extract_traits_from_image(image_path, specimen_name)
        results.append(result)
    
    return results