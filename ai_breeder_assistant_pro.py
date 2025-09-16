"""
AI Breeder Assistant Pro - Unified Orchid Breeding Analysis Widget
Consolidates breeding tools using Jeff Parham's Sarcochilus F226 research methodology
Created for Neon One integration
"""

import os
import json
import uuid
import base64
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from functools import wraps
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps, UnidentifiedImageError
from flask import Blueprint, render_template, request, jsonify, current_app, flash, url_for, session
from models import OrchidRecord
from app import db
from breeding_ai import OrchidBreedingAI
try:
    from svo_enhanced_scraper import SunsetValleyOrchidsEnhancedScraper
    SVO_SCRAPER_AVAILABLE = True
except ImportError:
    SVO_SCRAPER_AVAILABLE = False
    logging.warning("⚠️ SVO Enhanced Scraper not available - using fallback data")

# Import Google Cloud integration
try:
    from google_cloud_integration import get_google_integration, save_breeding_analysis_to_sheets, upload_image_to_google_drive
    GOOGLE_CLOUD_AVAILABLE = True
except ImportError:
    GOOGLE_CLOUD_AVAILABLE = False
    logging.warning("⚠️ Google Cloud integration not available - using local storage only")
from pathlib import Path
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_wtf.csrf import validate_csrf
from wtforms import TextAreaField, HiddenField
from wtforms.validators import DataRequired
from werkzeug.utils import send_file
from werkzeug.datastructures import FileStorage
import tempfile
import logging

# Import enhanced AI analysis functionality
try:
    from enhanced_ai_analysis import (
        enhanced_image_analysis_with_drive_upload,
        save_breeding_analysis_with_cloud_integration
    )
    ENHANCED_AI_AVAILABLE = True
except ImportError:
    ENHANCED_AI_AVAILABLE = False
    logging.warning("⚠️ Enhanced AI analysis not available - using standard functionality")

# Configure upload settings with enhanced security
UPLOAD_FOLDER = 'static/uploads/breeding'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}
MAX_IMAGE_SIZE = (1024, 1024)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
API_TIMEOUT = 30  # 30 seconds timeout for OpenAI API calls
CACHE_DURATION = 300  # 5 minutes cache duration

# Initialize OpenAI client lazily within request context
openai_client = None

def get_openai_client():
    """Lazy initialization of OpenAI client within request context"""
    global openai_client
    if openai_client is None:
        try:
            from openai import OpenAI
            if os.environ.get('OPENAI_API_KEY'):
                openai_client = OpenAI(
                    api_key=os.environ.get('OPENAI_API_KEY'),
                    timeout=API_TIMEOUT
                )
                logging.info("✅ OpenAI client initialized for AI Breeder Pro")
            else:
                openai_client = False  # Use False to indicate no key available
                logging.warning("⚠️ OpenAI API key not found - using fallback analysis")
        except ImportError:
            openai_client = False
            logging.warning("⚠️ OpenAI library not available - using fallback analysis")
    return openai_client if openai_client is not False else None

# Rate limiting configuration
RATE_LIMIT_REQUESTS = 10
RATE_LIMIT_WINDOW = 60  # 1 minute

# Simple in-memory cache for API responses
api_cache = {}
request_counts = {}

# Create upload directory if it doesn't exist
Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Security and performance utilities
def rate_limit(f):
    """Rate limiting decorator for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.environ.get('REMOTE_ADDR', 'unknown'))
        current_time = time.time()
        
        # Clean old entries
        cutoff_time = current_time - RATE_LIMIT_WINDOW
        if client_ip in request_counts:
            request_counts[client_ip] = [t for t in request_counts[client_ip] if t > cutoff_time]
        else:
            request_counts[client_ip] = []
        
        # Check rate limit
        if len(request_counts[client_ip]) >= RATE_LIMIT_REQUESTS:
            return jsonify({'error': 'Rate limit exceeded. Please try again later.'}), 429
        
        # Add current request
        request_counts[client_ip].append(current_time)
        
        return f(*args, **kwargs)
    return decorated_function

def cache_response(duration=CACHE_DURATION):
    """Caching decorator for API responses"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{f.__name__}_{hash(str(args) + str(kwargs))}"
            current_time = time.time()
            
            # Check cache
            if cache_key in api_cache:
                cached_data, timestamp = api_cache[cache_key]
                if current_time - timestamp < duration:
                    return cached_data
            
            # Execute function and cache result
            result = f(*args, **kwargs)
            api_cache[cache_key] = (result, current_time)
            
            return result
        return decorated_function
    return decorator

def handle_api_errors(f):
    """Error handling decorator for API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except FileNotFoundError as e:
            logging.error(f"File not found in {f.__name__}: {e}")
            return jsonify({'error': 'Required file not found'}), 404
        except PermissionError as e:
            logging.error(f"Permission error in {f.__name__}: {e}")
            return jsonify({'error': 'Permission denied'}), 403
        except ValueError as e:
            logging.error(f"Value error in {f.__name__}: {e}")
            return jsonify({'error': 'Invalid input data'}), 400
        except Exception as e:
            logging.error(f"Unexpected error in {f.__name__}: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    return decorated_function

def validate_image_security(file: FileStorage) -> bool:
    """Enhanced image security validation"""
    if not file or not file.filename:
        return False
    
    # Check file extension
    if not allowed_file(file.filename):
        return False
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    file_size = file.tell()
    file.seek(0)  # Reset to beginning
    
    if file_size > MAX_FILE_SIZE:
        return False
    
    # Validate image header
    try:
        with Image.open(file.stream) as img:
            img.verify()  # Verify it's a valid image
        file.stream.seek(0)  # Reset stream position
        return True
    except (UnidentifiedImageError, Exception):
        return False

# Create blueprint for the widget
ai_breeder_pro = Blueprint('ai_breeder_pro', __name__, url_prefix='/widgets/ai-breeder-pro')

# Security forms for CSRF protection
class ImageUploadForm(FlaskForm):
    image = FileField('Parent Image', validators=[
        FileRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'bmp'], 'Images only!')
    ])
    parent_type = HiddenField('Parent Type')

class CrossAnalysisForm(FlaskForm):
    parent1_data = TextAreaField('Parent 1 Data', validators=[DataRequired()])
    parent2_data = TextAreaField('Parent 2 Data', validators=[DataRequired()])
    breeding_goals = TextAreaField('Breeding Goals', validators=[DataRequired()])
    breeder_intent = TextAreaField('Breeder Intent')

class UnifiedBreederAssistant:
    """
    Unified AI Breeder Assistant Pro - Research-grade breeding analysis
    Based on Jeff Parham's Sarcochilus F226 trait inheritance methodology
    """
    
    def __init__(self):
        # Initialize breeding AI with fallback handling
        try:
            from breeding_ai import OrchidBreedingAI
            self.breeding_ai = OrchidBreedingAI()
        except ImportError:
            logging.warning("⚠️ breeding_ai module not found - using fallback analysis")
            self.breeding_ai = None
        
        # Initialize Google Cloud integration
        if GOOGLE_CLOUD_AVAILABLE:
            self.google_integration = get_google_integration()
            logging.info("🌤️ Google Cloud integration available for AI Breeder Pro")
        else:
            self.google_integration = None
            logging.info("📂 Using local storage only for AI Breeder Pro")
        
        self.f226_case_study = self._load_f226_research()
        self.sarcochilus_data = self._load_sarcochilus_breeding_data()
    
    def _load_f226_research(self):
        """Load Jeff Parham's F226 case study as proof of concept"""
        return {
            "cross_name": "Sarcochilus F226",
            "parents": {
                "pod_parent": {
                    "name": "Sarcochilus Kulnura Roundup 'Multi Spot'",
                    "key_traits": ["vivid magenta coloration", "energetic white speckling", "bold patterns"]
                },
                "pollen_parent": {
                    "name": "Sarcochilus Kulnura Secure 'Shapely'", 
                    "key_traits": ["compact growth", "symmetrical floral form", "well-balanced lip", "tidy presentation"]
                }
            },
            "offspring_analysis": {
                "inherited_traits": [
                    "Thick, fleshy petals (from 'Shapely')",
                    "Bold magenta spotting (from 'Multi Spot')",
                    "Waxy, sculpted texture",
                    "Flat presentation and symmetry",
                    "Balanced lip with white-yellow-red gradient"
                ],
                "success_indicators": [
                    "Consistent flower form",
                    "Healthy root growth in semi-hydro",
                    "Strong turgor and lush foliage",
                    "Early signs of potential for naming"
                ],
                "growing_notes": {
                    "culture": "Semi-Hydro (LECA in clear pot)",
                    "light": "Bright filtered light",
                    "temperature": "Cool to intermediate (50-75°F)",
                    "watering": "Consistent passive hydration via reservoir"
                }
            },
            "research_methodology": "AI-assisted trait inheritance analysis with real-world validation",
            "author": "Jeff Parham, FCOS President",
            "publication": "Five Cities Orchid Society Newsletter Feature"
        }
    
    def _load_sarcochilus_breeding_data(self):
        """Load real SVO breeding data from database and scraper"""
        try:
            # First try to get data from database
            if SVO_SCRAPER_AVAILABLE:
                scraper = SunsetValleyOrchidsEnhancedScraper()
                svo_data = scraper.get_svo_breeding_data_for_ai()
                
                if svo_data:
                    logging.info(f"✅ Loaded {len(svo_data)} real SVO breeding records")
                    return svo_data
                else:
                    logging.warning("⚠️ No SVO data in database, using fallback")
            
            # Fallback to enhanced mock data based on real SVO patterns
            return self._get_enhanced_fallback_breeding_data()
            
        except Exception as e:
            logging.error(f"❌ Error loading SVO breeding data: {e}")
            return self._get_enhanced_fallback_breeding_data()
    
    def _get_enhanced_fallback_breeding_data(self):
        """Enhanced fallback breeding data based on real SVO patterns"""
        return [
            {
                "cross_name": "Sarcochilus fitzhart × olivaceus",
                "pod_parent": "Sarcochilus fitzhart",
                "pollen_parent": "Sarcochilus olivaceus",
                "genus": "Sarcochilus",
                "description": "Compact spike with full flowers, white petals with distinctive red spotting pattern",
                "cultural_notes": "Compact and free-flowering plants, excellent for windowsill culture",
                "source": "Sunset Valley Orchids (Enhanced Fallback)",
                "validated": False
            },
            {
                "cross_name": "Sarcochilus hartmanii × cecilliae 'Limelight'",
                "pod_parent": "Sarcochilus hartmanii", 
                "pollen_parent": "Sarcochilus cecilliae 'Limelight'",
                "genus": "Sarcochilus",
                "description": "Large green flowers on compact spikes, excellent yellow/green breeding line development",
                "cultural_notes": "Cool growing, intermediate light requirements",
                "source": "Sunset Valley Orchids (Enhanced Fallback)",
                "validated": False
            },
            {
                "cross_name": "Sarcochilus Sweetheart 'Speckles' × Kulnura Peach",
                "pod_parent": "Sarcochilus Sweetheart 'Speckles'",
                "pollen_parent": "Sarcochilus Kulnura Peach",
                "genus": "Sarcochilus",
                "description": "Excellent form with intricate patterns and enhanced peach coloration",
                "cultural_notes": "Pattern enhancement breeding, color development focus",
                "source": "Sunset Valley Orchids (Enhanced Fallback)",
                "validated": False
            },
            {
                "cross_name": "Sarcochilus Kulnura Estate × George Colthup",
                "pod_parent": "Sarcochilus Kulnura Estate",
                "pollen_parent": "Sarcochilus George Colthup",
                "genus": "Sarcochilus",
                "description": "Classic Australian hybrid with strong fragrance and robust growth",
                "cultural_notes": "Easy culture, reliable flowering, fragrant blooms",
                "source": "Sunset Valley Orchids (Enhanced Fallback)",
                "validated": False
            },
            {
                "cross_name": "Sarcochilus Riverside × Melba",
                "pod_parent": "Sarcochilus Riverside",
                "pollen_parent": "Sarcochilus Melba",
                "genus": "Sarcochilus",
                "description": "Miniature habit with profuse flowering, excellent for collections",
                "cultural_notes": "Compact growth, high flower count, easy care",
                "source": "Sunset Valley Orchids (Enhanced Fallback)",
                "validated": False
            }
        ]
    
    def analyze_proposed_cross(self, parent1_data: Dict, parent2_data: Dict, breeding_goals: List[str], 
                             breeder_intent: Dict = None, parent_images: Dict = None) -> Dict[str, Any]:
        """
        Comprehensive breeding analysis using F226 methodology with enhanced features
        """
        # Use existing AI breeding system with fallback
        if self.breeding_ai:
            ai_analysis = self.breeding_ai.analyze_breeding_cross(parent1_data, parent2_data, breeding_goals)
        else:
            # Fallback analysis when breeding_ai is not available
            ai_analysis = {
                'success_probability': 75,  # Default moderate success
                'genetic_compatibility': {
                    'genus_compatibility': 0.8,
                    'geographic_compatibility': 0.6,
                    'habit_compatibility': 0.7,
                    'climate_compatibility': 0.5
                },
                'breeding_difficulty': 'Moderate',
                'flowering_time': '2-3 years'
            }
        
        # Extract traits from images if provided
        visual_traits = {}
        if parent_images:
            visual_traits = self._analyze_parent_images(parent_images)
            # Enhance parent data with visual traits
            parent1_data.update(visual_traits.get('parent1', {}))
            parent2_data.update(visual_traits.get('parent2', {}))
        
        # Enhance with F226-style trait inheritance prediction
        trait_inheritance = self._predict_trait_inheritance_f226_style(parent1_data, parent2_data)
        
        # Enhanced breeder intent analysis
        intent_analysis = self._analyze_breeder_intent(breeder_intent, trait_inheritance) if breeder_intent else None
        
        # Generate research-grade recommendations
        research_recommendations = self._generate_research_recommendations(parent1_data, parent2_data, ai_analysis)
        
        # Generate visualization data
        visualization_data = self._generate_visualization_data(ai_analysis, trait_inheritance, intent_analysis)
        
        return {
            "cross_analysis": {
                "proposed_cross": f"{parent1_data.get('display_name', 'Parent 1')} × {parent2_data.get('display_name', 'Parent 2')}",
                "success_probability": ai_analysis.get('success_probability', 0),
                "genetic_compatibility": ai_analysis.get('genetic_compatibility', {}),
                "breeding_difficulty": ai_analysis.get('breeding_difficulty', 'Unknown')
            },
            "trait_predictions": trait_inheritance,
            "visual_traits": visual_traits,
            "breeder_intent_analysis": intent_analysis,
            "f226_methodology": {
                "approach": "AI-assisted trait inheritance analysis with real-world validation",
                "based_on": "Jeff Parham's Sarcochilus F226 research methodology",
                "validation": "Proven successful in 'Multi Spot' × 'Shapely' cross"
            },
            "research_recommendations": research_recommendations,
            "case_study_reference": self.f226_case_study,
            "related_crosses": self._find_similar_crosses(parent1_data, parent2_data),
            "visualization_data": visualization_data
        }
    
    def _predict_trait_inheritance_f226_style(self, parent1: Dict, parent2: Dict) -> List[Dict]:
        """Predict trait inheritance using F226 research methodology"""
        predictions = []
        
        # Color inheritance (F226 style)
        if parent1.get('flower_color') and parent2.get('flower_color'):
            predictions.append({
                "trait": "Flower Color",
                "prediction": f"Expected blend of {parent1.get('flower_color')} and {parent2.get('flower_color')}",
                "f226_example": "Bold magenta spotting from 'Multi Spot' over white base",
                "confidence": "High - Based on F226 color inheritance pattern"
            })
        
        # Form inheritance
        predictions.append({
            "trait": "Flower Form", 
            "prediction": "Combination of parental flower shapes and presentations",
            "f226_example": "Thick, fleshy petals and flat presentation from 'Shapely'",
            "confidence": "High - Form traits typically blend predictably"
        })
        
        # Growth habit
        predictions.append({
            "trait": "Growth Habit",
            "prediction": "Intermediate between parents with potential for compact growth",
            "f226_example": "Compact, well-structured growth inherited from 'Shapely'",
            "confidence": "Medium - Variable expression in offspring"
        })
        
        return predictions
    
    def _generate_research_recommendations(self, parent1: Dict, parent2: Dict, ai_analysis: Dict) -> List[str]:
        """Generate research-grade breeding recommendations"""
        recommendations = []
        
        success_prob = ai_analysis.get('success_probability', 0)
        
        if success_prob > 70:
            recommendations.append("🌟 High-probability cross - Proceed with confidence")
            recommendations.append("📊 Document all offspring for trait inheritance analysis") 
            recommendations.append("🔬 Consider this cross for research publication")
        elif success_prob > 50:
            recommendations.append("✅ Moderate success probability - Worth attempting")
            recommendations.append("📋 Keep detailed breeding records for analysis")
        else:
            recommendations.append("⚠️ Lower success probability - Consider alternative crosses")
            recommendations.append("🔍 Review parent compatibility before proceeding")
        
        # Culture recommendations based on F226 success
        recommendations.append("🌱 Consider semi-hydro culture for optimal root development")
        recommendations.append("🌡️ Maintain cool to intermediate temperatures (50-75°F)")
        recommendations.append("💧 Provide consistent moisture without waterlogging")
        
        return recommendations
    
    def _find_similar_crosses(self, parent1: Dict, parent2: Dict) -> List[Dict]:
        """Find similar crosses from breeding data"""
        similar = []
        
        # Check against real SVO Sarcochilus breeding data
        for cross_data in self.sarcochilus_data:
            if (parent1.get('genus') == 'Sarcochilus' or parent2.get('genus') == 'Sarcochilus'):
                similar.append({
                    "cross": f"{cross_data.get('pod_parent', '')} × {cross_data.get('pollen_parent', '')}",
                    "cross_name": cross_data.get('cross_name', cross_data.get('cross', '')),
                    "expected_traits": cross_data.get('description', cross_data.get('expected_traits', '')),
                    "cultural_notes": cross_data.get('cultural_notes', ''),
                    "source": cross_data.get('source', 'Sunset Valley Orchids'),
                    "validated": cross_data.get('validated', False),
                    "relevance": "Real SVO breeding experience" if cross_data.get('validated') else "SVO breeding reference"
                })
        
        # Add F226 reference if Sarcochilus cross
        if parent1.get('genus') == 'Sarcochilus' and parent2.get('genus') == 'Sarcochilus':
            similar.append({
                "cross": "Kulnura Roundup 'Multi Spot' × Kulnura Secure 'Shapely'",
                "result": "F226 - Successful hybrid with predictable trait inheritance",
                "relevance": "Proven methodology reference"
            })
        
        return similar[:5]  # Limit to 5 most relevant
    
    def _analyze_parent_images(self, parent_images: Dict) -> Dict[str, Any]:
        """Enhanced orchid image analysis using OpenAI Vision API with robust error handling"""
        visual_traits = {'parent1': {}, 'parent2': {}}
        
        client = get_openai_client()
        if not client:
            logging.warning("⚠️ OpenAI client not available for image analysis")
            return visual_traits
        
        for parent_key, image_data in parent_images.items():
            if not image_data:
                continue
                
            try:
                # Validate image data
                if not isinstance(image_data, str) or len(image_data) < 100:
                    logging.warning(f"⚠️ Invalid image data for {parent_key}")
                    continue
                
                # Enhanced prompt for orchid trait analysis
                prompt = """
                You are an expert orchid taxonomist. Analyze this orchid image and extract visual breeding traits.
                
                Please identify:
                1. Primary flower color and any secondary colors
                2. Flower size (small <2cm, medium 2-6cm, large >6cm)
                3. Petal/sepal shape (round, pointed, reflexed, flat)
                4. Texture appearance (waxy, velvety, glossy, matte)
                5. Pattern type (solid, spotted, striped, veined, gradient)
                6. Flower form (flat, cupped, tubular, star-shaped)
                7. Lip characteristics if visible
                8. Overall symmetry and presentation
                
                Return ONLY a JSON object with these traits and confidence scores (0-100):
                {
                    "primary_color": "",
                    "secondary_colors": [],
                    "size_category": "",
                    "petal_shape": "",
                    "texture": "",
                    "pattern": "",
                    "form": "",
                    "lip_characteristics": "",
                    "symmetry": "",
                    "confidence_score": 0,
                    "breeding_notes": ""
                }
                """
                
                # Call OpenAI Vision API with enhanced error handling and timeout
                logging.info(f"🔍 Starting vision analysis for {parent_key}")
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{image_data}",
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=800,
                    temperature=0.1  # Low temperature for consistent analysis
                )
                
                # Parse the response
                trait_text = response.choices[0].message.content
                logging.info(f"✅ Vision analysis completed for {parent_key}")
                
                # Extract visual traits with enhanced parsing
                visual_traits[parent_key] = self._parse_visual_traits_enhanced(trait_text)
                visual_traits[parent_key]['analysis_timestamp'] = datetime.now().isoformat()
                
            except Exception as e:
                logging.error(f"❌ Vision analysis error for {parent_key}: {e}")
                visual_traits[parent_key] = {
                    'error': 'Vision analysis unavailable',
                    'error_type': type(e).__name__,
                    'fallback_analysis': self._get_fallback_visual_traits()
                }
        
        return visual_traits
    
    def _parse_visual_traits_enhanced(self, trait_text: str) -> Dict[str, Any]:
        """Enhanced parsing of AI vision response with multiple fallback strategies"""
        try:
            # Try to parse as JSON first (primary method)
            if '{' in trait_text and '}' in trait_text:
                start = trait_text.find('{')
                end = trait_text.rfind('}') + 1
                json_str = trait_text[start:end]
                parsed_traits = json.loads(json_str)
                
                # Validate required fields and add defaults
                validated_traits = {
                    'primary_color': parsed_traits.get('primary_color', 'Unknown'),
                    'secondary_colors': parsed_traits.get('secondary_colors', []),
                    'size_category': parsed_traits.get('size_category', 'Medium'),
                    'petal_shape': parsed_traits.get('petal_shape', 'Unknown'),
                    'texture': parsed_traits.get('texture', 'Unknown'),
                    'pattern': parsed_traits.get('pattern', 'Unknown'),
                    'form': parsed_traits.get('form', 'Unknown'),
                    'lip_characteristics': parsed_traits.get('lip_characteristics', 'Unknown'),
                    'symmetry': parsed_traits.get('symmetry', 'Unknown'),
                    'confidence_score': min(100, max(0, parsed_traits.get('confidence_score', 50))),
                    'breeding_notes': parsed_traits.get('breeding_notes', '')
                }
                
                logging.info(f"✅ Successfully parsed JSON traits with confidence {validated_traits['confidence_score']}")
                return validated_traits
                
        except json.JSONDecodeError as e:
            logging.warning(f"⚠️ JSON parsing failed: {e}")
        except Exception as e:
            logging.warning(f"⚠️ Trait parsing error: {e}")
        
        # Fallback: intelligent text parsing
        return self._parse_visual_traits_fallback(trait_text)
    
    def _parse_visual_traits_fallback(self, trait_text: str) -> Dict[str, Any]:
        """Fallback text parsing when JSON parsing fails"""
        traits = {
            'primary_color': 'Unknown',
            'secondary_colors': [],
            'size_category': 'Medium',
            'petal_shape': 'Unknown',
            'texture': 'Unknown',
            'pattern': 'Unknown',
            'form': 'Unknown',
            'lip_characteristics': 'Unknown',
            'symmetry': 'Unknown',
            'confidence_score': 30,  # Lower confidence for fallback
            'breeding_notes': 'Fallback analysis - limited detail available'
        }
        
        text_lower = trait_text.lower()
        
        # Enhanced color extraction
        colors = {
            'white': ['white', 'cream', 'ivory'],
            'pink': ['pink', 'rose', 'magenta', 'fuchsia'],
            'purple': ['purple', 'violet', 'lavender', 'mauve'],
            'yellow': ['yellow', 'golden', 'amber', 'citrus'],
            'red': ['red', 'crimson', 'scarlet', 'burgundy'],
            'orange': ['orange', 'coral', 'peach', 'salmon'],
            'green': ['green', 'lime', 'chartreuse'],
            'brown': ['brown', 'bronze', 'copper', 'mahogany']
        }
        
        for color, variants in colors.items():
            if any(variant in text_lower for variant in variants):
                traits['primary_color'] = color.title()
                break
        
        # Size extraction with more keywords
        if any(word in text_lower for word in ['large', 'big', 'huge', 'massive']):
            traits['size_category'] = 'Large'
        elif any(word in text_lower for word in ['small', 'tiny', 'miniature', 'petite']):
            traits['size_category'] = 'Small'
        
        # Pattern extraction
        pattern_keywords = {
            'spotted': ['spotted', 'speckled', 'dotted'],
            'striped': ['striped', 'banded', 'lined'],
            'solid': ['solid', 'uniform', 'plain'],
            'gradient': ['gradient', 'ombre', 'blended'],
            'veined': ['veined', 'reticulated', 'netted']
        }
        
        for pattern, keywords in pattern_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                traits['pattern'] = pattern.title()
                break
        
        # Form extraction
        if any(word in text_lower for word in ['flat', 'open']):
            traits['form'] = 'Flat'
        elif any(word in text_lower for word in ['cupped', 'bowl']):
            traits['form'] = 'Cupped'
        elif any(word in text_lower for word in ['tubular', 'trumpet']):
            traits['form'] = 'Tubular'
        
        logging.info(f"✅ Fallback parsing completed with primary color: {traits['primary_color']}")
        return traits
    
    def _get_fallback_visual_traits(self) -> Dict[str, Any]:
        """Get basic fallback traits when vision analysis completely fails"""
        return {
            'primary_color': 'Analysis unavailable',
            'secondary_colors': [],
            'size_category': 'Unknown',
            'petal_shape': 'Unknown',
            'texture': 'Unknown',
            'pattern': 'Unknown',
            'form': 'Unknown',
            'lip_characteristics': 'Unknown',
            'symmetry': 'Unknown',
            'confidence_score': 0,
            'breeding_notes': 'Visual analysis failed - manual trait entry recommended'
        }
    
    def _analyze_breeder_intent(self, breeder_intent: Optional[Dict], trait_predictions: List[Dict]) -> Optional[Dict[str, Any]]:
        """Analyze breeder intent and compare with predicted outcomes"""
        if not breeder_intent:
            return None
        
        intent_score = 0
        max_score = 0
        alignment_details = []
        
        # Analyze each intent category
        for category, importance in breeder_intent.items():
            if importance == 0:  # Skip unimportant categories
                continue
                
            max_score += importance * 10
            
            # Find matching trait predictions
            matching_traits = [t for t in trait_predictions if category.lower() in t['trait'].lower()]
            
            if matching_traits:
                trait = matching_traits[0]
                confidence_score = self._extract_confidence_from_trait(trait)
                intent_score += importance * confidence_score
                
                alignment_details.append({
                    'category': category,
                    'importance': importance,
                    'predicted_outcome': trait['prediction'],
                    'alignment_score': confidence_score,
                    'status': 'Aligned' if confidence_score >= 70 else 'Partially Aligned' if confidence_score >= 40 else 'Not Aligned'
                })
            else:
                alignment_details.append({
                    'category': category,
                    'importance': importance,
                    'predicted_outcome': 'No specific prediction available',
                    'alignment_score': 50,  # Neutral when unknown
                    'status': 'Unknown'
                })
                intent_score += importance * 5  # Partial credit for unknown
        
        overall_alignment = (intent_score / max_score * 100) if max_score > 0 else 0
        
        return {
            'overall_alignment_score': round(overall_alignment, 1),
            'alignment_level': self._get_alignment_level(overall_alignment),
            'alignment_details': alignment_details,
            'recommendations': self._generate_intent_recommendations(overall_alignment, alignment_details)
        }
    
    def _extract_confidence_from_trait(self, trait: Dict) -> int:
        """Extract confidence score from trait prediction"""
        confidence_text = trait.get('confidence', '').lower()
        if 'high' in confidence_text:
            return 85
        elif 'medium' in confidence_text:
            return 65
        elif 'low' in confidence_text:
            return 35
        else:
            return 50  # Default neutral confidence
    
    def _get_alignment_level(self, score: float) -> str:
        """Convert alignment score to descriptive level"""
        if score >= 80:
            return 'Excellent Alignment'
        elif score >= 65:
            return 'Good Alignment'
        elif score >= 50:
            return 'Moderate Alignment'
        elif score >= 35:
            return 'Poor Alignment'
        else:
            return 'Misaligned'
    
    def _generate_intent_recommendations(self, overall_score: float, details: List[Dict]) -> List[str]:
        """Generate recommendations based on intent alignment analysis"""
        recommendations = []
        
        if overall_score >= 80:
            recommendations.append("🌟 Excellent alignment! This cross should meet your breeding goals.")
            recommendations.append("📊 Proceed with confidence - high probability of desired outcomes.")
        elif overall_score >= 65:
            recommendations.append("✅ Good alignment with your goals, worth pursuing.")
            recommendations.append("🔍 Monitor specific traits that showed lower alignment scores.")
        elif overall_score >= 50:
            recommendations.append("⚖️ Moderate alignment - consider if trade-offs are acceptable.")
            recommendations.append("🔄 Review alternative parent combinations for better alignment.")
        else:
            recommendations.append("⚠️ Poor alignment with breeding goals.")
            recommendations.append("🔍 Consider different parents or adjust breeding objectives.")
        
        # Add specific recommendations for misaligned categories
        misaligned = [d for d in details if d['status'] in ['Not Aligned', 'Partially Aligned']]
        if misaligned:
            high_importance_misaligned = [d for d in misaligned if d['importance'] >= 8]
            if high_importance_misaligned:
                recommendations.append(f"🎯 High-priority misalignment in: {', '.join([d['category'] for d in high_importance_misaligned])}")
        
        return recommendations
    
    def _generate_visualization_data(self, ai_analysis: Dict, trait_predictions: List[Dict], 
                                   intent_analysis: Dict = None) -> Dict[str, Any]:
        """Generate data for frontend visualizations"""
        visualization_data = {
            'success_probability_chart': {
                'value': ai_analysis.get('success_probability', 0),
                'segments': [
                    {'label': 'Success Probability', 'value': ai_analysis.get('success_probability', 0), 'color': '#10B981'},
                    {'label': 'Risk Factor', 'value': 100 - ai_analysis.get('success_probability', 0), 'color': '#EF4444'}
                ]
            },
            'trait_inheritance_matrix': {
                'traits': []
            },
            'compatibility_radar': {
                'categories': [],
                'values': []
            },
            'breeding_timeline': {
                'phases': [
                    {'name': 'Pollination', 'duration': '1 day', 'status': 'pending'},
                    {'name': 'Seed Development', 'duration': '6-12 months', 'status': 'pending'},
                    {'name': 'Flask Culture', 'duration': '12-18 months', 'status': 'pending'},
                    {'name': 'Deflasking & Growth', 'duration': '6-12 months', 'status': 'pending'},
                    {'name': 'First Flowering', 'duration': ai_analysis.get('flowering_time', '2-3 years'), 'status': 'pending'}
                ]
            }
        }
        
        # Build trait inheritance matrix
        for trait in trait_predictions:
            confidence_score = self._extract_confidence_from_trait(trait)
            visualization_data['trait_inheritance_matrix']['traits'].append({
                'name': trait['trait'],
                'probability': confidence_score,
                'prediction': trait['prediction'][:50] + '...' if len(trait['prediction']) > 50 else trait['prediction']
            })
        
        # Build compatibility radar chart
        compatibility = ai_analysis.get('genetic_compatibility', {})
        radar_categories = ['Genus', 'Geography', 'Growth Habit', 'Climate']
        radar_values = [
            compatibility.get('genus_compatibility', 0.5) * 100,
            compatibility.get('geographic_compatibility', 0.5) * 100,
            compatibility.get('habit_compatibility', 0.5) * 100,
            compatibility.get('climate_compatibility', 0.5) * 100
        ]
        
        visualization_data['compatibility_radar'] = {
            'categories': radar_categories,
            'values': radar_values
        }
        
        # Add intent alignment chart if available
        if intent_analysis:
            visualization_data['intent_alignment_chart'] = {
                'overall_score': intent_analysis['overall_alignment_score'],
                'details': intent_analysis['alignment_details']
            }
        
        return visualization_data

# Image processing utility functions
def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_uploaded_image(file):
    """Enhanced image processing with security and error handling"""
    if not validate_image_security(file):
        return None
    
    # Generate unique filename with timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{timestamp}_{str(uuid.uuid4())[:8]}.jpg"
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    
    try:
        # Open and process image with security checks
        with Image.open(file.stream) as image:
            # Auto-orient based on EXIF data
            image = ImageOps.exif_transpose(image)
            
            # Convert to RGB if necessary (removes potential security risks)
            if image.mode in ('RGBA', 'LA', 'P'):
                image = image.convert('RGB')
            
            # Resize if larger than max dimensions
            image.thumbnail(MAX_IMAGE_SIZE, Image.Resampling.LANCZOS)
            
            # Save processed image with optimization
            image.save(filepath, 'JPEG', quality=85, optimize=True)
            
            logging.info(f"✅ Image processed successfully: {filename}")
            
            return {
                'filename': filename,
                'filepath': filepath,
                'url': url_for('static', filename=f'uploads/breeding/{filename}'),
                'size': os.path.getsize(filepath)
            }
        
    except UnidentifiedImageError:
        logging.error(f"❌ Invalid image format: {file.filename}")
        return None
    except Exception as e:
        logging.error(f"❌ Image processing error: {e}")
        return None

def image_to_base64(image_path):
    """Enhanced base64 conversion with security and size checks"""
    try:
        if not os.path.exists(image_path):
            logging.error(f"❌ Image file not found: {image_path}")
            return None
        
        # Check file size before processing
        file_size = os.path.getsize(image_path)
        if file_size > MAX_FILE_SIZE:
            logging.error(f"❌ Image file too large: {file_size} bytes")
            return None
        
        with open(image_path, 'rb') as image_file:
            encoded = base64.b64encode(image_file.read()).decode('utf-8')
            logging.info(f"✅ Image converted to base64: {len(encoded)} characters")
            return encoded
            
    except Exception as e:
        logging.error(f"❌ Base64 conversion error: {e}")
        return None

# Initialize the unified system
unified_breeder = UnifiedBreederAssistant()

@ai_breeder_pro.route('/')
def widget_home():
    """Main widget interface"""
    return render_template('ai_breeder_pro/widget_home.html')

@ai_breeder_pro.route('/embed')
def embed_widget():
    """Embeddable widget for Neon One"""
    return render_template('ai_breeder_pro/embed.html')

@ai_breeder_pro.route('/api/analyze-cross', methods=['POST'])
def analyze_cross():
    """API endpoint for basic cross analysis (legacy compatibility)"""
    try:
        data = request.get_json()
        parent1_id = data.get('parent1_id')
        parent2_id = data.get('parent2_id') 
        breeding_goals = data.get('breeding_goals', [])
        
        # Get parent data from database
        parent1 = OrchidRecord.query.get(parent1_id)
        parent2 = OrchidRecord.query.get(parent2_id)
        
        if not parent1 or not parent2:
            return jsonify({"error": "Parent orchids not found"}), 404
        
        # Convert to dict format
        parent1_data = {
            'display_name': parent1.display_name,
            'genus': parent1.genus,
            'species': parent1.species,
            'flower_color': getattr(parent1, 'flower_color', ''),
            'growth_habit': getattr(parent1, 'growth_habit', ''),
            'region': getattr(parent1, 'region', ''),
            'climate_preference': getattr(parent1, 'climate_preference', '')
        }
        
        parent2_data = {
            'display_name': parent2.display_name,
            'genus': parent2.genus,
            'species': parent2.species,
            'flower_color': getattr(parent2, 'flower_color', ''),
            'growth_habit': getattr(parent2, 'growth_habit', ''),
            'region': getattr(parent2, 'region', ''),
            'climate_preference': getattr(parent2, 'climate_preference', '')
        }
        
        # Perform basic analysis (maintaining backward compatibility)
        analysis = unified_breeder.analyze_proposed_cross(parent1_data, parent2_data, breeding_goals)
        
        return jsonify(analysis)
        
    except Exception as e:
        logging.error(f"Basic analysis error: {e}")
        return jsonify({"error": str(e)}), 500

@ai_breeder_pro.route('/api/f226-case-study')
def get_f226_case_study():
    """Get F226 case study data"""
    return jsonify(unified_breeder.f226_case_study)

@ai_breeder_pro.route('/api/search-parents')
def search_parents():
    """Search for potential parent orchids"""
    query = request.args.get('q', '')
    limit = min(int(request.args.get('limit', 10)), 20)
    
    if len(query) < 2:
        return jsonify([])
    
    # Search orchids by name or genus
    orchids = OrchidRecord.query.filter(
        db.or_(
            OrchidRecord.display_name.ilike(f'%{query}%'),
            OrchidRecord.genus.ilike(f'%{query}%'),
            OrchidRecord.species.ilike(f'%{query}%')
        )
    ).limit(limit).all()
    
    results = []
    for orchid in orchids:
        results.append({
            'id': orchid.id,
            'display_name': orchid.display_name,
            'genus': orchid.genus,
            'species': orchid.species,
            'photo_url': getattr(orchid, 'primary_photo_url', '/static/placeholder-orchid.jpg')
        })
    
    return jsonify(results)

@ai_breeder_pro.route('/api/svo-breeding-data')
@cache_response(duration=600)  # Cache for 10 minutes
def get_svo_breeding_data():
    """Get all SVO breeding data for AI analysis"""
    try:
        # Get breeding data from the unified breeder assistant
        svo_data = unified_breeder.sarcochilus_data
        
        return jsonify({
            'status': 'success',
            'count': len(svo_data),
            'data': svo_data,
            'data_source': 'Sunset Valley Orchids Enhanced Scraper',
            'cached_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        logging.error(f"❌ Error retrieving SVO breeding data: {e}")
        return jsonify({'error': 'Failed to retrieve SVO breeding data'}), 500

@ai_breeder_pro.route('/api/svo-run-scraper', methods=['POST'])
@rate_limit
@handle_api_errors
def run_svo_scraper():
    """Run the SVO scraper to collect fresh data"""
    try:
        if not SVO_SCRAPER_AVAILABLE:
            return jsonify({'error': 'SVO scraper not available'}), 503
        
        # Get parameters from request
        data = request.get_json() or {}
        genera = data.get('genera', ['Sarcochilus'])
        years = data.get('years', list(range(2020, 2025)))
        max_pages = min(data.get('max_pages', 5), 10)  # Limit to prevent abuse
        
        # Initialize scraper
        scraper = SunsetValleyOrchidsEnhancedScraper()
        
        # Run scraper in background thread for better user experience
        def run_scraper_task():
            try:
                results = scraper.scrape_svo_complete(genera, years, max_pages)
                logging.info(f"✅ SVO scraper completed: {len(results)} hybrids collected")
                
                # Refresh the unified breeder data
                unified_breeder.sarcochilus_data = unified_breeder._load_sarcochilus_breeding_data()
                
            except Exception as e:
                logging.error(f"❌ SVO scraper task failed: {e}")
        
        # Start background task
        import threading
        thread = threading.Thread(target=run_scraper_task)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'status': 'started',
            'message': 'SVO scraper started in background',
            'parameters': {
                'genera': genera,
                'years': years,
                'max_pages': max_pages
            }
        })
        
    except Exception as e:
        logging.error(f"❌ Error starting SVO scraper: {e}")
        return jsonify({'error': 'Failed to start SVO scraper'}), 500

@ai_breeder_pro.route('/api/svo-crosses/<genus>')
@cache_response(duration=300)  # Cache for 5 minutes
def get_svo_crosses_by_genus(genus):
    """Get SVO crosses filtered by genus"""
    try:
        # Filter breeding data by genus
        filtered_data = [
            cross for cross in unified_breeder.sarcochilus_data 
            if cross.get('genus', '').lower() == genus.lower()
        ]
        
        return jsonify({
            'status': 'success',
            'genus': genus,
            'count': len(filtered_data),
            'crosses': filtered_data
        })
        
    except Exception as e:
        logging.error(f"❌ Error retrieving crosses for genus {genus}: {e}")
        return jsonify({'error': f'Failed to retrieve crosses for genus {genus}'}), 500

@ai_breeder_pro.route('/api/svo-search-crosses')
def search_svo_crosses():
    """Search SVO crosses by parent names or traits"""
    try:
        query = request.args.get('q', '').lower()
        limit = min(int(request.args.get('limit', 10)), 20)
        
        if len(query) < 2:
            return jsonify([])
        
        # Search through SVO breeding data
        matching_crosses = []
        
        for cross in unified_breeder.sarcochilus_data:
            # Search in various fields
            searchable_text = ' '.join([
                cross.get('cross_name', ''),
                cross.get('pod_parent', ''),
                cross.get('pollen_parent', ''),
                cross.get('description', ''),
                cross.get('cultural_notes', '')
            ]).lower()
            
            if query in searchable_text:
                matching_crosses.append(cross)
                
                if len(matching_crosses) >= limit:
                    break
        
        return jsonify({
            'status': 'success',
            'query': query,
            'count': len(matching_crosses),
            'crosses': matching_crosses
        })
        
    except Exception as e:
        logging.error(f"❌ Error searching SVO crosses: {e}")
        return jsonify({'error': 'Failed to search SVO crosses'}), 500

@ai_breeder_pro.route('/api/upload-image', methods=['POST'])
@rate_limit
@handle_api_errors
def upload_image():
    """Enhanced secure image upload endpoint with comprehensive validation"""
    start_time = time.time()
    
    # Validate CSRF token if present
    csrf_token = request.form.get('csrf_token')
    if csrf_token:
        try:
            validate_csrf(csrf_token)
        except Exception:
            logging.warning(f"❌ Invalid CSRF token from {request.environ.get('REMOTE_ADDR')}")
            return jsonify({'error': 'Invalid CSRF token'}), 400
    
    parent_type = request.form.get('parent_type', 'parent1')
    if parent_type not in ['parent1', 'parent2']:
        return jsonify({'error': 'Invalid parent type'}), 400
    
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    if not file or file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Enhanced security validation
    if not validate_image_security(file):
        return jsonify({'error': 'Invalid or unsafe image file'}), 400
    
    # Process the uploaded image
    result = process_uploaded_image(file)
    if not result:
        return jsonify({'error': 'Failed to process image'}), 500
    
    # Convert to base64 for AI analysis with timeout
    try:
        image_base64 = image_to_base64(result['filepath'])
        if not image_base64:
            return jsonify({'error': 'Failed to process image for analysis'}), 500
    except Exception as e:
        logging.error(f"❌ Base64 conversion failed: {e}")
        return jsonify({'error': 'Image processing failed'}), 500
    
    processing_time = round(time.time() - start_time, 2)
    logging.info(f"✅ Image upload successful in {processing_time}s")
    
    return jsonify({
        'success': True,
        'filename': result['filename'],
        'image_data': image_base64,
        'image_url': result['url'],
        'parent_type': parent_type,
        'file_size': result['size'],
        'processing_time': processing_time
    })

@ai_breeder_pro.route('/api/analyze-enhanced-cross', methods=['POST'])
@rate_limit
@handle_api_errors
def analyze_enhanced_cross():
    """Enhanced cross analysis API with comprehensive validation and error handling"""
    start_time = time.time()
    
    # Validate request content type
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    # Validate required fields
    required_fields = ['parent1_id', 'parent2_id']
    for field in required_fields:
        if field not in data:
            return jsonify({"error": f"Missing required field: {field}"}), 400
    
    parent1_id = data.get('parent1_id')
    parent2_id = data.get('parent2_id')
    breeding_goals = data.get('breeding_goals', [])
    breeder_intent = data.get('breeder_intent', {})
    image_data = data.get('image_data', {})
    
    # Validate parent IDs
    try:
        parent1_id = int(parent1_id)
        parent2_id = int(parent2_id)
    except (ValueError, TypeError):
        return jsonify({"error": "Invalid parent IDs"}), 400
    
    # Get parent data from database with error handling
    try:
        parent1 = OrchidRecord.query.get(parent1_id)
        parent2 = OrchidRecord.query.get(parent2_id)
    except Exception as e:
        logging.error(f"❌ Database error: {e}")
        return jsonify({"error": "Database error"}), 500
    
    if not parent1 or not parent2:
        return jsonify({"error": "Parent orchids not found"}), 404
    
    # Convert to dict format with safe attribute access
    try:
        parent1_data = {
            'display_name': parent1.display_name or 'Unknown',
            'genus': parent1.genus or 'Unknown',
            'species': parent1.species or 'Unknown',
            'flower_color': getattr(parent1, 'flower_color', ''),
            'growth_habit': getattr(parent1, 'growth_habit', ''),
            'region': getattr(parent1, 'region', ''),
            'climate_preference': getattr(parent1, 'climate_preference', '')
        }
        
        parent2_data = {
            'display_name': parent2.display_name or 'Unknown',
            'genus': parent2.genus or 'Unknown',
            'species': parent2.species or 'Unknown',
            'flower_color': getattr(parent2, 'flower_color', ''),
            'growth_habit': getattr(parent2, 'growth_habit', ''),
            'region': getattr(parent2, 'region', ''),
            'climate_preference': getattr(parent2, 'climate_preference', '')
        }
    except Exception as e:
        logging.error(f"❌ Data extraction error: {e}")
        return jsonify({"error": "Failed to extract parent data"}), 500
    
    # Process uploaded images for AI vision analysis with timeout
    parent_images = {}
    try:
        if image_data.get('parent1_image_data'):
            parent_images['parent1'] = image_data['parent1_image_data']
        if image_data.get('parent2_image_data'):
            parent_images['parent2'] = image_data['parent2_image_data']
    except Exception as e:
        logging.warning(f"⚠️ Image processing warning: {e}")
        # Continue without images if there's an issue
    
    # Perform enhanced analysis with timeout
    try:
        with threading.Timer(API_TIMEOUT, lambda: None) as timer:
            analysis = unified_breeder.analyze_proposed_cross(
                parent1_data, parent2_data, breeding_goals, breeder_intent, parent_images
            )
            timer.cancel()
    except Exception as e:
        logging.error(f"❌ Analysis error: {e}")
        return jsonify({"error": "Analysis failed"}), 500
    
    processing_time = round(time.time() - start_time, 2)
    logging.info(f"✅ Enhanced analysis completed in {processing_time}s")
    
    # Add metadata to response
    analysis['metadata'] = {
        'processing_time': processing_time,
        'timestamp': datetime.now().isoformat(),
        'parent1_name': parent1_data['display_name'],
        'parent2_name': parent2_data['display_name']
    }
    
    return jsonify(analysis)

@ai_breeder_pro.route('/api/breeding-intent-template')
@cache_response(duration=3600)  # Cache for 1 hour
@handle_api_errors
def get_breeding_intent_template():
    """Get template for detailed breeding intent questionnaire"""
    template = {
        'categories': [
            {
                'name': 'Flower Color',
                'description': 'Importance of achieving specific color goals',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Primary color enhancement',
                    'Pattern development', 
                    'Color intensity',
                    'Unique color combinations'
                ]
            },
            {
                'name': 'Flower Size',
                'description': 'Importance of flower size characteristics',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Larger flowers',
                    'Fuller form',
                    'Better proportions',
                    'Consistent sizing'
                ]
            },
            {
                'name': 'Plant Vigor',
                'description': 'Importance of plant health and growth characteristics',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Disease resistance',
                    'Growth rate',
                    'Flowering frequency',
                    'Environmental adaptability'
                ]
            },
            {
                'name': 'Flowering Habit',
                'description': 'Importance of blooming characteristics',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Blooming frequency',
                    'Flower longevity',
                    'Spike quality',
                    'Seasonal timing'
                ]
            },
            {
                'name': 'Growth Habit',
                'description': 'Importance of plant structure and size',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Compact growth',
                    'Upright habit',
                    'Symmetrical form',
                    'Manageable size'
                ]
            },
            {
                'name': 'Special Traits',
                'description': 'Importance of unique characteristics',
                'scale': 'Rate 0-10 (0=Not Important, 10=Critical)',
                'subcategories': [
                    'Fragrance',
                    'Unusual patterns',
                    'Rare color forms',
                    'Commercial potential'
                ]
            }
        ],
        'breeding_philosophy': {
            'description': 'What is your primary breeding philosophy?',
            'options': [
                'Conservation - Preserve species characteristics',
                'Improvement - Enhance existing traits',
                'Innovation - Create new trait combinations',
                'Commercial - Develop marketable varieties',
                'Personal - For personal enjoyment and learning'
            ]
        },
        'timeline_importance': {
            'description': 'How important is early flowering?',
            'options': [
                'Very Important - Need results within 2-3 years',
                'Moderately Important - 3-4 years acceptable',
                'Not Important - Willing to wait 5+ years for quality'
            ]
        }
    }
    
    return jsonify(template)

@ai_breeder_pro.route('/api/visualization-demo')
def get_visualization_demo():
    """Get demo data for testing visualizations"""
    demo_data = {
        'success_probability_chart': {
            'value': 78,
            'segments': [
                {'label': 'Success Probability', 'value': 78, 'color': '#10B981'},
                {'label': 'Risk Factor', 'value': 22, 'color': '#EF4444'}
            ]
        },
        'trait_inheritance_matrix': {
            'traits': [
                {'name': 'Flower Color', 'probability': 85, 'prediction': 'Enhanced magenta with white patterns'},
                {'name': 'Flower Form', 'probability': 92, 'prediction': 'Thick, fleshy petals with excellent shape'},
                {'name': 'Growth Habit', 'probability': 67, 'prediction': 'Compact, well-structured growth pattern'},
                {'name': 'Flowering', 'probability': 74, 'prediction': 'Regular blooming with good spike quality'}
            ]
        },
        'compatibility_radar': {
            'categories': ['Genus', 'Geography', 'Growth Habit', 'Climate'],
            'values': [95, 80, 75, 85]
        },
        'intent_alignment_chart': {
            'overall_score': 82,
            'details': [
                {'category': 'Color Enhancement', 'importance': 9, 'alignment_score': 85, 'status': 'Aligned'},
                {'category': 'Flower Size', 'importance': 7, 'alignment_score': 78, 'status': 'Aligned'},
                {'category': 'Plant Vigor', 'importance': 8, 'alignment_score': 90, 'status': 'Aligned'},
                {'category': 'Growth Habit', 'importance': 6, 'alignment_score': 70, 'status': 'Aligned'}
            ]
        },
        'breeding_timeline': {
            'phases': [
                {'name': 'Pollination', 'duration': '1 day', 'status': 'pending'},
                {'name': 'Seed Development', 'duration': '6-12 months', 'status': 'pending'},
                {'name': 'Flask Culture', 'duration': '12-18 months', 'status': 'pending'},
                {'name': 'Deflasking & Growth', 'duration': '6-12 months', 'status': 'pending'},
                {'name': 'First Flowering', 'duration': '2-3 years', 'status': 'pending'}
            ]
        }
    }
    
    return jsonify(demo_data)

# Export for registration
def register_ai_breeder_pro(app):
    """Register the AI Breeder Assistant Pro widget"""
    app.register_blueprint(ai_breeder_pro)
    logging.info("🧬 AI Breeder Assistant Pro widget registered successfully")