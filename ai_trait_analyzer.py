#!/usr/bin/env python3
"""
AI Trait Analyzer - OpenAI-Powered Orchid Trait Analysis and Inheritance Patterns
Advanced trait extraction, inheritance analysis, and batch processing system
Created for Orchid Continuum - Breeding Assistant Pro Integration
"""

import os
import json
import uuid
import base64
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Configure logging
logger = logging.getLogger(__name__)

# Import OpenAI (no fallbacks - fail fast if missing)
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError as e:
    error_msg = f"CRITICAL: OpenAI library not available: {e}"
    logger.error(error_msg)
    logger.error("AI trait analysis requires: openai")
    logger.error("Install with: pip install openai")
    raise RuntimeError(error_msg)

# Constants
API_TIMEOUT = 45  # Extended timeout for complex trait analysis
MAX_RETRIES = 3
RATE_LIMIT_DELAY = 1.0  # Delay between API calls
BATCH_SIZE = 5  # Number of concurrent analyses
MAX_IMAGE_SIZE = 1024 * 1024  # 1MB max image size for API

class TraitCategory(Enum):
    """Categories of orchid traits for analysis"""
    COLOR = "color"
    PATTERN = "pattern"
    SHAPE = "shape"
    SIZE = "size"
    TEXTURE = "texture"
    FRAGRANCE = "fragrance"
    MORPHOLOGY = "morphology"

class InheritancePattern(Enum):
    """Types of inheritance patterns"""
    DOMINANT = "dominant"
    RECESSIVE = "recessive"
    CODOMINANT = "codominant"
    POLYGENIC = "polygenic"
    EPISTATIC = "epistatic"
    INTERMEDIATE = "intermediate"
    UNKNOWN = "unknown"

@dataclass
class TraitAnalysis:
    """Structured data for individual trait analysis"""
    trait_id: str
    category: TraitCategory
    name: str
    description: str
    confidence: float  # 0.0 to 1.0
    dominant_expression: bool
    genetic_markers: List[str]
    inheritance_pattern: InheritancePattern
    phenotype_variations: List[str]
    breeding_value: float  # 1.0 to 10.0
    stability_score: float  # How stable this trait is in breeding
    environmental_factors: List[str]
    measurement_data: Dict[str, Any]
    ai_analysis_metadata: Dict[str, Any]

@dataclass
class InheritancePrediction:
    """Predictions for trait inheritance in offspring"""
    trait_combination: str
    parent1_contribution: float  # 0.0 to 1.0
    parent2_contribution: float  # 0.0 to 1.0
    predicted_expression: str
    probability_dominant: float
    probability_recessive: float
    hybrid_vigor_factor: float
    expected_variations: List[str]
    breeding_recommendation: str
    confidence_level: float

@dataclass
class BatchAnalysisResult:
    """Results from batch trait analysis"""
    batch_id: str
    total_images: int
    successful_analyses: int
    failed_analyses: int
    start_time: datetime
    completion_time: Optional[datetime]
    trait_analyses: List[TraitAnalysis]
    summary_statistics: Dict[str, Any]
    processing_errors: List[str]

class OpenAITraitAnalyzer:
    """
    Advanced OpenAI-powered trait analyzer using GPT-4o vision capabilities
    Provides comprehensive orchid trait extraction and inheritance analysis
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the trait analyzer with OpenAI integration"""
        self.api_key = api_key or os.environ.get('OPENAI_API_KEY')
        self.client = None
        self.rate_limiter = time.time()
        self.analysis_cache = {}
        self.batch_processors = {}
        
        # Initialize OpenAI client
        self._init_openai_client()
        
        # Load trait analysis models and patterns
        self.trait_patterns = self._load_trait_patterns()
        self.inheritance_models = self._load_inheritance_models()
        
        logger.info("🧬 AI Trait Analyzer initialized with GPT-4o vision capabilities")
    
    def _init_openai_client(self) -> None:
        """Initialize OpenAI client with strict validation"""
        if not self.api_key:
            error_msg = "CRITICAL: OpenAI API key not found - set OPENAI_API_KEY environment variable"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
            
        try:
            self.client = OpenAI(
                api_key=self.api_key,
                timeout=API_TIMEOUT
            )
            logger.info("✅ OpenAI client initialized successfully")
        except Exception as e:
            error_msg = f"CRITICAL: Failed to initialize OpenAI client: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _load_trait_patterns(self) -> Dict[str, Any]:
        """Load orchid trait analysis patterns and models"""
        return {
            'color_patterns': {
                'primary_colors': ['red', 'pink', 'white', 'yellow', 'purple', 'green', 'blue', 'orange'],
                'pattern_types': ['solid', 'spotted', 'striped', 'mottled', 'gradient', 'bicolor', 'multicolor'],
                'intensity_levels': ['pale', 'light', 'medium', 'intense', 'deep', 'vivid']
            },
            'shape_patterns': {
                'flower_shapes': ['round', 'star', 'triangular', 'flat', 'cupped', 'reflexed', 'twisted'],
                'petal_forms': ['broad', 'narrow', 'pointed', 'rounded', 'wavy', 'flat', 'recurved'],
                'lip_types': ['simple', 'complex', 'fringed', 'pouched', 'spur', 'bearded']
            },
            'size_categories': {
                'miniature': {'flower_size': '<2.5cm', 'plant_size': '<15cm'},
                'compact': {'flower_size': '2.5-5cm', 'plant_size': '15-30cm'},
                'standard': {'flower_size': '5-10cm', 'plant_size': '30-60cm'},
                'large': {'flower_size': '10-15cm', 'plant_size': '60-100cm'},
                'specimen': {'flower_size': '>15cm', 'plant_size': '>100cm'}
            }
        }
    
    def _load_inheritance_models(self) -> Dict[str, Any]:
        """Load inheritance pattern models for trait prediction"""
        return {
            'color_inheritance': {
                'red': {'dominance': 0.7, 'stability': 0.8},
                'white': {'dominance': 0.3, 'stability': 0.9},
                'purple': {'dominance': 0.6, 'stability': 0.7},
                'yellow': {'dominance': 0.4, 'stability': 0.6}
            },
            'pattern_inheritance': {
                'spotted': {'dominance': 0.8, 'stability': 0.6},
                'striped': {'dominance': 0.5, 'stability': 0.7},
                'solid': {'dominance': 0.2, 'stability': 0.9}
            },
            'size_inheritance': {
                'type': 'polygenic',
                'heritability': 0.65,
                'environmental_factor': 0.35
            }
        }
    
    async def analyze_traits_from_image(self, image_data: Union[bytes, str], 
                                      analysis_goals: Optional[List[str]] = None,
                                      breeding_context: Optional[Dict[str, Any]] = None) -> List[TraitAnalysis]:
        """
        Comprehensive trait analysis from orchid image using GPT-4o vision
        
        Args:
            image_data: Image as bytes or base64 string
            analysis_goals: Specific traits to focus on
            breeding_context: Parent information for inheritance analysis
            
        Returns:
            List of TraitAnalysis objects with comprehensive trait data
        """
        if not self.client:
            return self._get_fallback_trait_analysis()
        
        try:
            # Prepare image data
            image_base64 = self._prepare_image_data(image_data)
            if not image_base64:
                raise ValueError("Failed to process image data")
            
            # Create comprehensive analysis prompt
            analysis_prompt = self._create_trait_analysis_prompt(analysis_goals, breeding_context)
            
            # Rate limiting
            await self._apply_rate_limit()
            
            # Call OpenAI GPT-4o vision API
            response = await self._call_openai_vision_api(image_base64, analysis_prompt)
            
            # Parse and structure the response
            trait_analyses = self._parse_trait_response(response, breeding_context)
            
            # Cache the results
            cache_key = self._generate_cache_key(image_data, analysis_goals)
            self.analysis_cache[cache_key] = trait_analyses
            
            logger.info(f"✅ Successfully analyzed {len(trait_analyses)} traits from image")
            return trait_analyses
            
        except Exception as e:
            logger.error(f"❌ Trait analysis failed: {e}")
            return self._get_fallback_trait_analysis()
    
    def _create_trait_analysis_prompt(self, analysis_goals: Optional[List[str]], 
                                    breeding_context: Optional[Dict[str, Any]]) -> str:
        """Create comprehensive prompt for trait analysis"""
        
        goals_text = f"Focus areas: {', '.join(analysis_goals)}" if analysis_goals else "Comprehensive analysis"
        breeding_text = ""
        
        if breeding_context:
            breeding_text = f"""
            
            **BREEDING CONTEXT:**
            Parent 1: {breeding_context.get('parent1_name', 'Unknown')}
            Parent 2: {breeding_context.get('parent2_name', 'Unknown')}
            Breeding Goals: {breeding_context.get('breeding_goals', 'General improvement')}
            """
        
        return f"""
        You are an expert orchid geneticist and trait analyst with advanced knowledge of orchid breeding and inheritance patterns.
        
        Analyze this orchid image and provide comprehensive trait analysis in JSON format.
        
        **ANALYSIS REQUIREMENTS:**
        {goals_text}
        {breeding_text}
        
        **TRAIT CATEGORIES TO ANALYZE:**
        
        1. **COLOR ANALYSIS:**
           - Primary colors (RGB values if possible)
           - Secondary/accent colors
           - Color patterns (solid, spotted, striped, gradient)
           - Color intensity and saturation levels
           - Unique color combinations or rare expressions
           - Color stability indicators
           - Potential color inheritance patterns
        
        2. **PATTERN ANALYSIS:**
           - Pattern types (spots, stripes, veining, mottling)
           - Pattern density and distribution
           - Pattern regularity vs randomness
           - Contrasting pattern elements
           - Pattern dominance characteristics
           - Breeding potential for pattern improvement
        
        3. **SHAPE AND MORPHOLOGY:**
           - Overall flower shape and form
           - Petal and sepal characteristics
           - Lip structure and complexity
           - Column and reproductive structures
           - Flower symmetry and proportion
           - Size measurements (estimate in cm)
           - Growth habit indicators
        
        4. **TEXTURE ANALYSIS:**
           - Petal texture (waxy, velvety, crystalline, glossy)
           - Surface patterns and micro-structures
           - Thickness and substance quality
           - Light reflection properties
           - Durability indicators
        
        5. **GENETIC MARKERS:**
           - Visible genetic indicators
           - Trait dominance signs
           - Recessive trait expressions
           - Hybrid vigor indicators
           - Potential breeding value
           - Stability prediction
        
        6. **BREEDING ASSESSMENT:**
           - Overall breeding quality (1-10 scale)
           - Unique or desirable traits
           - Potential for trait improvement
           - Breeding line development value
           - Conservation significance
           - Commercial potential
        
        **OUTPUT FORMAT:**
        Return JSON with this exact structure:
        {{
          "traits": [
            {{
              "trait_id": "unique_identifier",
              "category": "color|pattern|shape|size|texture|morphology",
              "name": "trait_name",
              "description": "detailed_description",
              "confidence": 0.0-1.0,
              "dominant_expression": true|false,
              "genetic_markers": ["marker1", "marker2"],
              "inheritance_pattern": "dominant|recessive|codominant|polygenic|intermediate",
              "phenotype_variations": ["variation1", "variation2"],
              "breeding_value": 1.0-10.0,
              "stability_score": 0.0-1.0,
              "environmental_factors": ["factor1", "factor2"],
              "measurement_data": {{"size_cm": X, "intensity": Y}},
              "ai_analysis_metadata": {{"model": "gpt-4o", "timestamp": "ISO_datetime"}}
            }}
          ],
          "summary": {{
            "overall_quality": 1.0-10.0,
            "breeding_potential": "excellent|good|moderate|poor",
            "unique_traits_count": X,
            "dominant_traits": ["trait1", "trait2"],
            "breeding_recommendations": "detailed_recommendations",
            "inheritance_predictions": "inheritance_analysis"
          }}
        }}
        
        **ANALYSIS GUIDELINES:**
        - Be precise and specific in measurements and descriptions
        - Provide confidence scores based on image clarity and trait visibility
        - Consider both genetic and environmental factors
        - Focus on breeding-relevant characteristics
        - Identify rare or unique trait expressions
        - Assess commercial and conservation value
        - Predict trait stability in breeding programs
        """
    
    async def _call_openai_vision_api(self, image_base64: str, prompt: str) -> Dict[str, Any]:
        """Call OpenAI GPT-4o vision API with error handling and retries"""
        
        for attempt in range(MAX_RETRIES):
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_base64}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    response_format={"type": "json_object"},
                    max_tokens=2000,
                    temperature=0.3  # Lower temperature for more consistent analysis
                )
                
                return json.loads(response.choices[0].message.content)
                
            except Exception as e:
                logger.warning(f"⚠️ API call attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES - 1:
                    await asyncio.sleep(RATE_LIMIT_DELAY * (attempt + 1))
                else:
                    raise e
    
    def _parse_trait_response(self, response: Dict[str, Any], 
                            breeding_context: Optional[Dict[str, Any]]) -> List[TraitAnalysis]:
        """Parse OpenAI response into structured TraitAnalysis objects"""
        
        trait_analyses = []
        
        try:
            traits_data = response.get('traits', [])
            
            for trait_data in traits_data:
                trait = TraitAnalysis(
                    trait_id=trait_data.get('trait_id', str(uuid.uuid4())),
                    category=TraitCategory(trait_data.get('category', 'morphology')),
                    name=trait_data.get('name', 'Unknown Trait'),
                    description=trait_data.get('description', ''),
                    confidence=float(trait_data.get('confidence', 0.5)),
                    dominant_expression=bool(trait_data.get('dominant_expression', False)),
                    genetic_markers=trait_data.get('genetic_markers', []),
                    inheritance_pattern=InheritancePattern(
                        trait_data.get('inheritance_pattern', 'unknown')
                    ),
                    phenotype_variations=trait_data.get('phenotype_variations', []),
                    breeding_value=float(trait_data.get('breeding_value', 5.0)),
                    stability_score=float(trait_data.get('stability_score', 0.5)),
                    environmental_factors=trait_data.get('environmental_factors', []),
                    measurement_data=trait_data.get('measurement_data', {}),
                    ai_analysis_metadata={
                        'model': 'gpt-4o',
                        'timestamp': datetime.now().isoformat(),
                        'breeding_context': breeding_context,
                        'api_version': 'v1'
                    }
                )
                
                trait_analyses.append(trait)
                
        except Exception as e:
            logger.error(f"❌ Error parsing trait response: {e}")
            return self._get_fallback_trait_analysis()
        
        return trait_analyses
    
    async def predict_inheritance_patterns(self, parent1_traits: List[TraitAnalysis],
                                         parent2_traits: List[TraitAnalysis],
                                         breeding_goals: List[str]) -> List[InheritancePrediction]:
        """
        Predict trait inheritance patterns for breeding cross
        
        Args:
            parent1_traits: Traits from first parent
            parent2_traits: Traits from second parent
            breeding_goals: Desired traits in offspring
            
        Returns:
            List of inheritance predictions for each trait combination
        """
        
        predictions = []
        
        try:
            # Group traits by category for analysis
            parent1_by_category = self._group_traits_by_category(parent1_traits)
            parent2_by_category = self._group_traits_by_category(parent2_traits)
            
            # Analyze each trait category
            for category in TraitCategory:
                p1_traits = parent1_by_category.get(category, [])
                p2_traits = parent2_by_category.get(category, [])
                
                if p1_traits or p2_traits:
                    category_predictions = await self._predict_category_inheritance(
                        category, p1_traits, p2_traits, breeding_goals
                    )
                    predictions.extend(category_predictions)
            
            # Add cross-trait interaction predictions
            interaction_predictions = await self._predict_trait_interactions(
                parent1_traits, parent2_traits, breeding_goals
            )
            predictions.extend(interaction_predictions)
            
            logger.info(f"✅ Generated {len(predictions)} inheritance predictions")
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Inheritance prediction failed: {e}")
            return []
    
    async def _predict_category_inheritance(self, category: TraitCategory,
                                          p1_traits: List[TraitAnalysis],
                                          p2_traits: List[TraitAnalysis],
                                          breeding_goals: List[str]) -> List[InheritancePrediction]:
        """Predict inheritance for specific trait category"""
        
        if not self.client:
            return []
        
        try:
            # Create inheritance analysis prompt
            prompt = f"""
            Analyze trait inheritance for {category.value} traits in orchid breeding cross.
            
            **PARENT 1 TRAITS:**
            {json.dumps([asdict(trait) for trait in p1_traits], indent=2)}
            
            **PARENT 2 TRAITS:**
            {json.dumps([asdict(trait) for trait in p2_traits], indent=2)}
            
            **BREEDING GOALS:**
            {', '.join(breeding_goals)}
            
            Predict inheritance patterns using orchid genetics knowledge:
            - Mendelian inheritance patterns
            - Polygenic traits
            - Epistatic interactions
            - Hybrid vigor effects
            - Environmental influences
            
            Return JSON with inheritance predictions including probabilities, 
            dominant/recessive expressions, and breeding recommendations.
            
            Format:
            {{
              "predictions": [
                {{
                  "trait_combination": "description",
                  "parent1_contribution": 0.0-1.0,
                  "parent2_contribution": 0.0-1.0,
                  "predicted_expression": "description",
                  "probability_dominant": 0.0-1.0,
                  "probability_recessive": 0.0-1.0,
                  "hybrid_vigor_factor": 0.0-2.0,
                  "expected_variations": ["variation1", "variation2"],
                  "breeding_recommendation": "recommendation",
                  "confidence_level": 0.0-1.0
                }}
              ]
            }}
            """
            
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                max_tokens=1500,
                temperature=0.4
            )
            
            result = json.loads(response.choices[0].message.content)
            predictions = []
            
            for pred_data in result.get('predictions', []):
                prediction = InheritancePrediction(
                    trait_combination=pred_data.get('trait_combination', ''),
                    parent1_contribution=float(pred_data.get('parent1_contribution', 0.5)),
                    parent2_contribution=float(pred_data.get('parent2_contribution', 0.5)),
                    predicted_expression=pred_data.get('predicted_expression', ''),
                    probability_dominant=float(pred_data.get('probability_dominant', 0.5)),
                    probability_recessive=float(pred_data.get('probability_recessive', 0.5)),
                    hybrid_vigor_factor=float(pred_data.get('hybrid_vigor_factor', 1.0)),
                    expected_variations=pred_data.get('expected_variations', []),
                    breeding_recommendation=pred_data.get('breeding_recommendation', ''),
                    confidence_level=float(pred_data.get('confidence_level', 0.5))
                )
                predictions.append(prediction)
            
            return predictions
            
        except Exception as e:
            logger.error(f"❌ Category inheritance prediction failed: {e}")
            return []
    
    async def _predict_trait_interactions(self, parent1_traits: List[TraitAnalysis],
                                        parent2_traits: List[TraitAnalysis],
                                        breeding_goals: List[str]) -> List[InheritancePrediction]:
        """Predict complex trait interactions and epistatic effects"""
        
        # Simplified implementation - would be expanded with genetic interaction models
        interactions = []
        
        # Example: Color-pattern interactions
        p1_colors = [t for t in parent1_traits if t.category == TraitCategory.COLOR]
        p1_patterns = [t for t in parent1_traits if t.category == TraitCategory.PATTERN]
        p2_colors = [t for t in parent2_traits if t.category == TraitCategory.COLOR]
        p2_patterns = [t for t in parent2_traits if t.category == TraitCategory.PATTERN]
        
        if p1_colors and p1_patterns and p2_colors and p2_patterns:
            # Predict color-pattern interaction
            interaction = InheritancePrediction(
                trait_combination="Color-Pattern Interaction",
                parent1_contribution=0.5,
                parent2_contribution=0.5,
                predicted_expression="Complex interaction between color and pattern traits",
                probability_dominant=0.6,
                probability_recessive=0.4,
                hybrid_vigor_factor=1.2,
                expected_variations=["Enhanced pattern contrast", "Novel color-pattern combinations"],
                breeding_recommendation="Monitor for epistatic effects between color and pattern genes",
                confidence_level=0.7
            )
            interactions.append(interaction)
        
        return interactions
    
    async def batch_analyze_traits(self, image_paths: List[str],
                                 analysis_goals: Optional[List[str]] = None,
                                 breeding_context: Optional[Dict[str, Any]] = None,
                                 progress_callback: Optional[callable] = None) -> BatchAnalysisResult:
        """
        Batch process multiple orchid images for trait analysis
        
        Args:
            image_paths: List of image file paths
            analysis_goals: Specific traits to focus on
            breeding_context: Parent information for inheritance analysis
            progress_callback: Function to call with progress updates
            
        Returns:
            BatchAnalysisResult with comprehensive batch analysis data
        """
        
        batch_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        logger.info(f"🔄 Starting batch trait analysis for {len(image_paths)} images (Batch ID: {batch_id})")
        
        batch_result = BatchAnalysisResult(
            batch_id=batch_id,
            total_images=len(image_paths),
            successful_analyses=0,
            failed_analyses=0,
            start_time=start_time,
            completion_time=None,
            trait_analyses=[],
            summary_statistics={},
            processing_errors=[]
        )
        
        # Store batch processor
        self.batch_processors[batch_id] = batch_result
        
        try:
            # Process images in batches with thread pool
            with ThreadPoolExecutor(max_workers=BATCH_SIZE) as executor:
                
                # Submit all tasks
                future_to_path = {}
                for i, image_path in enumerate(image_paths):
                    future = executor.submit(
                        self._process_single_image_sync,
                        image_path, analysis_goals, breeding_context
                    )
                    future_to_path[future] = (image_path, i)
                
                # Process completed tasks
                for future in as_completed(future_to_path):
                    image_path, index = future_to_path[future]
                    
                    try:
                        traits = future.result()
                        batch_result.trait_analyses.extend(traits)
                        batch_result.successful_analyses += 1
                        
                        logger.info(f"✅ Analyzed image {index + 1}/{len(image_paths)}: {image_path}")
                        
                    except Exception as e:
                        batch_result.failed_analyses += 1
                        error_msg = f"Failed to analyze {image_path}: {str(e)}"
                        batch_result.processing_errors.append(error_msg)
                        logger.error(f"❌ {error_msg}")
                    
                    # Progress callback
                    if progress_callback:
                        progress = (batch_result.successful_analyses + batch_result.failed_analyses) / len(image_paths)
                        progress_callback(batch_id, progress, batch_result)
            
            # Generate summary statistics
            batch_result.summary_statistics = self._generate_batch_statistics(batch_result)
            batch_result.completion_time = datetime.now()
            
            logger.info(f"✅ Batch analysis complete: {batch_result.successful_analyses}/{len(image_paths)} successful")
            return batch_result
            
        except Exception as e:
            logger.error(f"❌ Batch analysis failed: {e}")
            batch_result.processing_errors.append(str(e))
            batch_result.completion_time = datetime.now()
            return batch_result
    
    def _process_single_image_sync(self, image_path: str,
                                 analysis_goals: Optional[List[str]],
                                 breeding_context: Optional[Dict[str, Any]]) -> List[TraitAnalysis]:
        """Synchronous wrapper for async image analysis"""
        
        # Load image data
        try:
            with open(image_path, 'rb') as f:
                image_data = f.read()
        except Exception as e:
            logger.error(f"❌ Failed to load image {image_path}: {e}")
            return []
        
        # Run async analysis in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(
                self.analyze_traits_from_image(image_data, analysis_goals, breeding_context)
            )
        finally:
            loop.close()
    
    def get_batch_progress(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """Get progress information for a batch analysis"""
        
        batch_result = self.batch_processors.get(batch_id)
        if not batch_result:
            return None
        
        total_processed = batch_result.successful_analyses + batch_result.failed_analyses
        progress_percentage = (total_processed / batch_result.total_images) * 100 if batch_result.total_images > 0 else 0
        
        return {
            'batch_id': batch_id,
            'total_images': batch_result.total_images,
            'processed': total_processed,
            'successful': batch_result.successful_analyses,
            'failed': batch_result.failed_analyses,
            'progress_percentage': progress_percentage,
            'start_time': batch_result.start_time.isoformat(),
            'completion_time': batch_result.completion_time.isoformat() if batch_result.completion_time else None,
            'is_complete': batch_result.completion_time is not None,
            'errors': batch_result.processing_errors
        }
    
    # Helper methods
    def _prepare_image_data(self, image_data: Union[bytes, str]) -> Optional[str]:
        """Prepare image data for API submission"""
        try:
            if isinstance(image_data, str):
                # Assume it's already base64
                return image_data
            elif isinstance(image_data, bytes):
                # Check image size
                if len(image_data) > MAX_IMAGE_SIZE:
                    logger.warning(f"⚠️ Image size {len(image_data)} bytes exceeds maximum {MAX_IMAGE_SIZE}")
                    # Could implement image compression here
                
                return base64.b64encode(image_data).decode('utf-8')
            else:
                raise ValueError("Invalid image data type")
        except Exception as e:
            logger.error(f"❌ Failed to prepare image data: {e}")
            return None
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.rate_limiter
        
        if time_since_last < RATE_LIMIT_DELAY:
            sleep_time = RATE_LIMIT_DELAY - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.rate_limiter = time.time()
    
    def _generate_cache_key(self, image_data: Union[bytes, str], 
                          analysis_goals: Optional[List[str]]) -> str:
        """Generate cache key for analysis results"""
        import hashlib
        
        # Create hash of image data
        if isinstance(image_data, bytes):
            image_hash = hashlib.md5(image_data).hexdigest()
        else:
            image_hash = hashlib.md5(image_data.encode()).hexdigest()
        
        # Add analysis goals to key
        goals_str = ','.join(sorted(analysis_goals)) if analysis_goals else 'default'
        
        return f"{image_hash}_{hashlib.md5(goals_str.encode()).hexdigest()}"
    
    def _group_traits_by_category(self, traits: List[TraitAnalysis]) -> Dict[TraitCategory, List[TraitAnalysis]]:
        """Group traits by category for analysis"""
        grouped = {}
        for trait in traits:
            if trait.category not in grouped:
                grouped[trait.category] = []
            grouped[trait.category].append(trait)
        return grouped
    
    def _generate_batch_statistics(self, batch_result: BatchAnalysisResult) -> Dict[str, Any]:
        """Generate summary statistics for batch analysis"""
        
        if not batch_result.trait_analyses:
            return {}
        
        # Trait distribution
        trait_counts = {}
        confidence_scores = []
        breeding_values = []
        
        for trait in batch_result.trait_analyses:
            category = trait.category.value
            trait_counts[category] = trait_counts.get(category, 0) + 1
            confidence_scores.append(trait.confidence)
            breeding_values.append(trait.breeding_value)
        
        # Calculate statistics
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        avg_breeding_value = sum(breeding_values) / len(breeding_values)
        
        return {
            'trait_distribution': trait_counts,
            'average_confidence': round(avg_confidence, 3),
            'average_breeding_value': round(avg_breeding_value, 2),
            'total_traits_analyzed': len(batch_result.trait_analyses),
            'success_rate': batch_result.successful_analyses / batch_result.total_images,
            'dominant_traits': len([t for t in batch_result.trait_analyses if t.dominant_expression]),
            'high_value_traits': len([t for t in batch_result.trait_analyses if t.breeding_value >= 8.0])
        }
    
    def _get_fallback_trait_analysis(self) -> List[TraitAnalysis]:
        """Generate fallback trait analysis when AI is unavailable"""
        
        fallback_traits = [
            TraitAnalysis(
                trait_id=str(uuid.uuid4()),
                category=TraitCategory.COLOR,
                name="Basic Color Analysis",
                description="Fallback color analysis - AI unavailable",
                confidence=0.3,
                dominant_expression=False,
                genetic_markers=[],
                inheritance_pattern=InheritancePattern.UNKNOWN,
                phenotype_variations=["Variable"],
                breeding_value=5.0,
                stability_score=0.5,
                environmental_factors=["Light", "Temperature"],
                measurement_data={},
                ai_analysis_metadata={
                    'model': 'fallback',
                    'timestamp': datetime.now().isoformat(),
                    'note': 'AI analysis unavailable'
                }
            )
        ]
        
        return fallback_traits

# Global analyzer instance
trait_analyzer = None

def get_trait_analyzer() -> OpenAITraitAnalyzer:
    """Get global trait analyzer instance"""
    global trait_analyzer
    if trait_analyzer is None:
        trait_analyzer = OpenAITraitAnalyzer()
    return trait_analyzer

# Utility functions for external integration
def analyze_orchid_traits(image_data: Union[bytes, str],
                         analysis_goals: Optional[List[str]] = None,
                         breeding_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Convenient function for single orchid trait analysis
    Returns trait data as dictionaries for JSON serialization
    """
    analyzer = get_trait_analyzer()
    
    # Run async analysis in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        traits = loop.run_until_complete(
            analyzer.analyze_traits_from_image(image_data, analysis_goals, breeding_context)
        )
        return [asdict(trait) for trait in traits]
    finally:
        loop.close()

def predict_inheritance(parent1_traits: List[Dict[str, Any]],
                       parent2_traits: List[Dict[str, Any]],
                       breeding_goals: List[str]) -> List[Dict[str, Any]]:
    """
    Convenient function for inheritance prediction
    Takes trait dictionaries and returns prediction dictionaries
    """
    analyzer = get_trait_analyzer()
    
    # Convert dictionaries back to TraitAnalysis objects
    p1_traits = [TraitAnalysis(**trait) for trait in parent1_traits]
    p2_traits = [TraitAnalysis(**trait) for trait in parent2_traits]
    
    # Run async prediction in sync context
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        predictions = loop.run_until_complete(
            analyzer.predict_inheritance_patterns(p1_traits, p2_traits, breeding_goals)
        )
        return [asdict(prediction) for prediction in predictions]
    finally:
        loop.close()

if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    # Test trait analyzer initialization
    analyzer = get_trait_analyzer()
    print("🧬 AI Trait Analyzer initialized successfully")
    
    # Example batch progress tracking
    def progress_callback(batch_id: str, progress: float, batch_result: BatchAnalysisResult):
        print(f"📊 Batch {batch_id}: {progress*100:.1f}% complete ({batch_result.successful_analyses} successful)")
    
    print("✅ AI Trait Analyzer module ready for integration")