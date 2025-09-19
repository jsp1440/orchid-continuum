import json
import os
import base64
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from openai import OpenAI
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
# Clean the API key to remove any shell export syntax
if OPENAI_API_KEY.startswith("export "):
    OPENAI_API_KEY = OPENAI_API_KEY.replace("export OPENAI_API_KEY=", "").strip().strip('"\'')
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def encode_image_to_base64(image_path):
    """Convert image to base64 for API submission"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return None

def extract_exif_metadata(image_path):
    """
    Extract EXIF metadata from image including GPS coordinates and photo date
    """
    try:
        image = Image.open(image_path)
        exif_data = image.getexif()
        
        if not exif_data:
            return {}
        
        metadata = {}
        
        # Extract basic EXIF data
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            
            # Extract photo date/time
            if tag == 'DateTime':
                try:
                    metadata['photo_datetime'] = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                    metadata['photo_date'] = metadata['photo_datetime'].date()
                    metadata['photo_time'] = metadata['photo_datetime'].time()
                except:
                    pass
            
            # Extract camera info
            elif tag == 'Make':
                metadata['camera_make'] = str(value)
            elif tag == 'Model':
                metadata['camera_model'] = str(value)
            elif tag == 'Software':
                metadata['software'] = str(value)
            
            # Extract GPS data
            elif tag == 'GPSInfo':
                gps_data = {}
                for gps_tag_id, gps_value in value.items():
                    gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                    gps_data[gps_tag] = gps_value
                
                # Parse GPS coordinates
                if 'GPSLatitude' in gps_data and 'GPSLatitudeRef' in gps_data:
                    lat = _convert_gps_coordinate(gps_data['GPSLatitude'])
                    if gps_data['GPSLatitudeRef'] == 'S':
                        lat = -lat
                    metadata['gps_latitude'] = lat
                
                if 'GPSLongitude' in gps_data and 'GPSLongitudeRef' in gps_data:
                    lon = _convert_gps_coordinate(gps_data['GPSLongitude'])
                    if gps_data['GPSLongitudeRef'] == 'W':
                        lon = -lon
                    metadata['gps_longitude'] = lon
                
                if 'GPSAltitude' in gps_data:
                    metadata['gps_altitude'] = float(gps_data['GPSAltitude'])
        
        return metadata
        
    except Exception as e:
        logger.error(f"Error extracting EXIF data: {e}")
        return {}

def _convert_gps_coordinate(coord_tuple):
    """Convert GPS coordinate from DMS format to decimal degrees"""
    try:
        degrees = float(coord_tuple[0])
        minutes = float(coord_tuple[1])
        seconds = float(coord_tuple[2])
        return degrees + (minutes / 60.0) + (seconds / 3600.0)
    except:
        return 0.0

def analyze_orchid_image(image_path):
    """
    Analyze orchid image using OpenAI Vision API to extract metadata
    Returns structured data about the orchid
    """
    try:
        # Encode image
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            raise Exception("Failed to encode image")
        
        # Prepare the prompt for enhanced orchid analysis
        system_prompt = """You are an expert orchid taxonomist and botanist with field research experience. Analyze this orchid image and provide comprehensive observational data in JSON format.

BOTANICAL IDENTIFICATION:
- scientific_name: The full scientific name if identifiable
- genus: The orchid genus
- species: The species name if identifiable  
- suggested_name: A display name for this orchid
- description: Detailed description of the flower, plant, and notable features
- confidence: Your confidence level (0.0 to 1.0) in the identification

FLOWERING ANALYSIS:
- is_flowering: true/false - Is this plant currently in flower?
- flowering_stage: "bud", "early_bloom", "peak_bloom", "late_bloom", "spent", "not_flowering"
- flower_count: Count visible flowers/buds (estimate if many)
- inflorescence_count: Number of flower spikes/stems
- flower_size_mm: Estimated flower diameter in millimeters
- flower_measurements: {"length_mm": X, "width_mm": Y, "depth_mm": Z} if measurable
- bloom_season_indicator: Based on visual cues, likely blooming season

HABITAT & GROWING ENVIRONMENT:
- growth_habit: "epiphytic", "terrestrial", "lithophytic", "semi-terrestrial"
- growing_environment: "wild_native", "naturalized", "cultivated_outdoor", "cultivated_greenhouse", "cultivated_indoor"
- substrate_type: "tree_bark", "rock", "soil", "moss", "artificial_medium", "unknown"
- mounting_evidence: Evidence of growing on trees, rocks, or ground
- natural_vs_cultivated: "native_wild", "naturalized_wild", "cultivated", "uncertain"

ENVIRONMENTAL CONDITIONS:
- light_conditions: "deep_shade", "filtered_light", "bright_indirect", "direct_sun", "artificial"
- humidity_indicators: Visual clues about humidity level (high/medium/low)
- temperature_indicators: Visual clues about temperature preference
- climate_preference: "cool", "intermediate", "warm", "hot"

PLANT MORPHOLOGY:
- leaf_form: Description of the leaves
- pseudobulb_presence: true/false if pseudobulbs are visible
- root_visibility: Description of visible roots (aerial, terrestrial)
- plant_maturity: "juvenile", "mature", "specimen_size"

LOCATION & CONTEXT:
- setting_type: "natural_forest", "botanical_garden", "home_collection", "nursery", "greenhouse", "outdoor_garden"
- companion_plants: Any other plants visible that indicate habitat
- elevation_indicators: Visual clues about elevation (if natural setting)

CULTURAL & RESEARCH NOTES:
- cultural_tips: Growing advice based on observed conditions
- notable_features: Any distinctive characteristics
- photoperiod_sensitivity: Likely sensitivity to day length changes
- bloom_triggers: Environmental factors that trigger flowering
- seasonal_requirements: Specific seasonal care needs
- conservation_status_clues: Any indicators of rarity or conservation concern

Analyze carefully and be specific. If you cannot determine something, mark as "unknown" or "uncertain". Focus on what you can actually observe in the image."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Please analyze this orchid image and provide the requested information in JSON format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=1500
        )
        
        # Parse the response
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        result = json.loads(content)
        
        # Ensure required fields have defaults
        defaults = {
            # Botanical Identification
            'suggested_name': 'Unknown Orchid',
            'scientific_name': None,
            'genus': None,
            'species': None,
            'description': 'Orchid identification pending',
            'confidence': 0.0,
            
            # Flowering Analysis
            'is_flowering': False,
            'flowering_stage': 'unknown',
            'flower_count': 0,
            'inflorescence_count': 0,
            'flower_size_mm': None,
            'flower_measurements': {},
            'bloom_season_indicator': 'unknown',
            
            # Habitat & Growing Environment
            'growth_habit': 'unknown',
            'growing_environment': 'unknown',
            'substrate_type': 'unknown',
            'mounting_evidence': 'unknown',
            'natural_vs_cultivated': 'uncertain',
            
            # Environmental Conditions
            'light_conditions': 'unknown',
            'humidity_indicators': 'unknown',
            'temperature_indicators': 'unknown',
            'climate_preference': 'unknown',
            
            # Plant Morphology
            'leaf_form': 'unknown',
            'pseudobulb_presence': False,
            'root_visibility': 'unknown',
            'plant_maturity': 'unknown',
            
            # Location & Context
            'setting_type': 'unknown',
            'companion_plants': 'unknown',
            'elevation_indicators': 'unknown',
            
            # Cultural & Research Notes
            'cultural_tips': None,
            'notable_features': None,
            'photoperiod_sensitivity': 'medium',
            'bloom_triggers': None,
            'seasonal_requirements': None,
            'conservation_status_clues': 'unknown',
            
            # Legacy fields
            'bloom_characteristics': None,
            'native_latitude': None,
            'metadata': {}
        }
        
        # Merge defaults with results
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
        
        # Extract EXIF metadata and merge with AI analysis
        exif_metadata = extract_exif_metadata(image_path)
        if exif_metadata:
            # Add EXIF data to result
            result['exif_data'] = exif_metadata
            
            # If flowering and we have photo date, use it as potential flowering time
            if result.get('is_flowering') and exif_metadata.get('photo_date'):
                result['flowering_photo_date'] = exif_metadata['photo_date'].isoformat()
                result['flowering_photo_datetime'] = exif_metadata['photo_datetime'].isoformat() if exif_metadata.get('photo_datetime') else None
            
            # Add GPS coordinates if available
            if exif_metadata.get('gps_latitude') and exif_metadata.get('gps_longitude'):
                result['photo_gps_coordinates'] = {
                    'latitude': exif_metadata['gps_latitude'],
                    'longitude': exif_metadata['gps_longitude'],
                    'altitude': exif_metadata.get('gps_altitude')
                }
                
            # Add camera/technical info
            if exif_metadata.get('camera_make') or exif_metadata.get('camera_model'):
                result['camera_info'] = {
                    'make': exif_metadata.get('camera_make'),
                    'model': exif_metadata.get('camera_model'),
                    'software': exif_metadata.get('software')
                }
        
        # Enhance with Baker culture data if this is a known species
        if result.get('scientific_name'):
            # Try direct Baker culture sheet first
            baker_advice = get_baker_culture_enhancement(result['scientific_name'])
            if baker_advice:
                result['baker_culture_notes'] = baker_advice
            else:
                # Try extrapolation from related species
                mock_orchid = type('MockOrchid', (), {
                    'scientific_name': result['scientific_name'],
                    'climate_preference': result.get('climate_preference'),
                    'growth_habit': result.get('growth_habit'),
                    'display_name': result.get('suggested_name')
                })()
                extrapolated_advice = extrapolate_baker_culture_data(mock_orchid)
                if extrapolated_advice:
                    result['baker_extrapolated_notes'] = extrapolated_advice
        
        # Add photoperiod analysis based on Baker Daylength Database
        photoperiod_data = calculate_photoperiod_requirements(result)
        if photoperiod_data:
            result['photoperiod_analysis'] = photoperiod_data
        
        logger.info(f"Successfully analyzed orchid image with confidence: {result.get('confidence', 0.0)}")
        return result
        
    except Exception as e:
        logger.error(f"Error analyzing orchid image: {str(e)}")
        return {
            'suggested_name': 'Unknown Orchid',
            'description': f'Error during AI analysis: {str(e)}',
            'confidence': 0.0,
            'metadata': {}
        }

def get_baker_culture_enhancement(scientific_name):
    """Get Baker culture sheet data for a specific orchid species"""
    try:
        from models import OrchidRecord
        
        # Find Baker culture sheet for this species
        baker_record = OrchidRecord.query.filter(
            OrchidRecord.scientific_name == scientific_name,
            OrchidRecord.photographer.like('%Baker%')
        ).first()
        
        if baker_record and baker_record.cultural_notes:
            return analyze_baker_culture_data(baker_record.cultural_notes)
        return None
        
    except Exception as e:
        logger.error(f"Error getting Baker culture enhancement: {str(e)}")
        return None

def extrapolate_baker_culture_data(target_orchid):
    """
    Extrapolate Baker culture knowledge to orchids without direct culture sheets
    Uses taxonomic relationships, climate preferences, and growth habits
    """
    try:
        from models import OrchidRecord
        from sqlalchemy import or_, and_
        
        if not target_orchid.scientific_name:
            return None
            
        # Extract genus from target orchid
        target_genus = target_orchid.scientific_name.split(' ')[0] if ' ' in target_orchid.scientific_name else target_orchid.scientific_name
        
        # Strategy 1: Find Baker culture sheets for same genus
        genus_matches = OrchidRecord.query.filter(
            OrchidRecord.photographer.like('%Baker%'),
            OrchidRecord.scientific_name.like(f'{target_genus} %')
        ).all()
        
        # Strategy 2: Find Baker culture sheets with similar climate preferences
        climate_matches = []
        if target_orchid.climate_preference:
            climate_matches = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%'),
                OrchidRecord.climate_preference == target_orchid.climate_preference
            ).limit(5).all()
        
        # Strategy 3: Find Baker culture sheets with similar growth habits
        growth_matches = []
        if target_orchid.growth_habit:
            growth_matches = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%'),
                OrchidRecord.growth_habit == target_orchid.growth_habit
            ).limit(3).all()
        
        # Strategy 4: Find Baker culture sheets from same geographic region (endemic area)
        endemic_matches = []
        if hasattr(target_orchid, 'region') and target_orchid.region:
            # Find Baker orchids from same region
            endemic_matches = OrchidRecord.query.filter(
                OrchidRecord.photographer.like('%Baker%'),
                OrchidRecord.region == target_orchid.region
            ).limit(5).all()
            
            # Also try broader geographic matching (continent/area)
            if not endemic_matches and target_orchid.region:
                # Extract broader geographic terms
                region_keywords = extract_geographic_keywords(target_orchid.region)
                for keyword in region_keywords:
                    broader_matches = OrchidRecord.query.filter(
                        OrchidRecord.photographer.like('%Baker%'),
                        OrchidRecord.region.like(f'%{keyword}%')
                    ).limit(3).all()
                    endemic_matches.extend(broader_matches)
        
        # Combine and analyze all relevant Baker data
        all_relevant = genus_matches + climate_matches + growth_matches + endemic_matches
        if not all_relevant:
            return None
            
        # Extract and synthesize cultural insights
        cultural_insights = []
        for record in all_relevant:
            if record.cultural_notes:
                analysis = analyze_baker_culture_data(record.cultural_notes)
                if analysis:
                    analysis['source_species'] = record.scientific_name
                    analysis['relationship'] = get_relationship_type(target_orchid, record)
                    cultural_insights.append(analysis)
        
        # Generate extrapolated recommendations
        if cultural_insights:
            return synthesize_baker_recommendations(target_orchid, cultural_insights)
        
        return None
        
    except Exception as e:
        logger.error(f"Error extrapolating Baker culture data: {str(e)}")
        return None

def extract_geographic_keywords(region_text):
    """Extract broader geographic keywords for matching"""
    if not region_text:
        return []
    
    keywords = []
    region_lower = region_text.lower()
    
    # Major geographic regions
    continent_mappings = {
        'south america': ['south america', 'brazil', 'ecuador', 'colombia', 'peru', 'venezuela'],
        'central america': ['central america', 'costa rica', 'panama', 'guatemala', 'mexico'],
        'africa': ['africa', 'madagascar', 'kenya', 'tanzania', 'south africa'],
        'asia': ['asia', 'thailand', 'vietnam', 'malaysia', 'indonesia', 'philippines'],
        'oceania': ['australia', 'new guinea', 'pacific', 'oceania']
    }
    
    for continent, countries in continent_mappings.items():
        if any(country in region_lower for country in countries):
            keywords.append(continent)
            break
    
    # Extract country names and major terms
    geographic_terms = ['america', 'asia', 'africa', 'tropical', 'subtropical', 'temperate', 'mountain', 'coastal']
    for term in geographic_terms:
        if term in region_lower:
            keywords.append(term)
    
    return list(set(keywords))

def get_relationship_type(target_orchid, baker_orchid):
    """Determine the taxonomic/ecological relationship between orchids"""
    target_genus = target_orchid.scientific_name.split(' ')[0] if target_orchid.scientific_name else ''
    baker_genus = baker_orchid.scientific_name.split(' ')[0] if baker_orchid.scientific_name else ''
    
    if target_genus == baker_genus:
        return 'same_genus'
    elif hasattr(target_orchid, 'region') and hasattr(baker_orchid, 'region') and target_orchid.region == baker_orchid.region:
        return 'same_region'
    elif target_orchid.climate_preference == baker_orchid.climate_preference:
        return 'similar_climate'
    elif target_orchid.growth_habit == baker_orchid.growth_habit:
        return 'similar_growth'
    elif hasattr(target_orchid, 'region') and hasattr(baker_orchid, 'region'):
        # Check for broader geographic relationship
        target_keywords = extract_geographic_keywords(target_orchid.region)
        baker_keywords = extract_geographic_keywords(baker_orchid.region)
        if any(keyword in baker_keywords for keyword in target_keywords):
            return 'endemic_region'
    else:
        return 'general_orchid'

def synthesize_baker_recommendations(target_orchid, cultural_insights):
    """
    Synthesize multiple Baker culture insights into recommendations for target orchid
    """
    try:
        # Prepare synthesis prompt
        system_prompt = """You are an expert orchid cultivation specialist synthesizing Charles & Margaret Baker culture sheet knowledge.

Create extrapolated growing recommendations for the target orchid based on related Baker culture data.

Consider in order of priority:
- Taxonomic relationships (same genus = highest priority)
- Geographic/endemic relationships (same region = high priority - Baker's regional expertise)
- Broader geographic area relationships (endemic to similar regions)
- Climate preference similarities
- Growth habit similarities
- Common patterns across related species

Baker's regional expertise is particularly valuable - orchids from the same geographic area often share:
- Seasonal rainfall patterns
- Temperature variations
- Humidity cycles
- Local growing conditions
- Regional cultivation techniques

Provide practical, actionable advice focusing on:
- Temperature and climate needs
- Humidity requirements
- Watering patterns
- Light requirements
- Seasonal care adjustments
- Regional growing considerations

Be conservative but recognize that Baker's geographic expertise applies broadly to endemic orchids."""

        target_info = {
            'name': target_orchid.display_name,
            'scientific_name': target_orchid.scientific_name,
            'climate_preference': target_orchid.climate_preference,
            'growth_habit': target_orchid.growth_habit,
            'temperature_range': target_orchid.temperature_range
        }
        
        insights_summary = []
        for insight in cultural_insights:
            insights_summary.append({
                'source': insight.get('source_species'),
                'relationship': insight.get('relationship'),
                'climate_data': insight.get('climate_requirements'),
                'humidity_data': insight.get('humidity_optimal'),
                'care_notes': insight.get('growing_recommendations')
            })
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Target orchid: {target_info}\\n\\nRelated Baker insights: {insights_summary}\\n\\nProvide extrapolated care recommendations:"}
            ],
            response_format={"type": "json_object"},
            max_tokens=600
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        extrapolated_data = json.loads(content)
        extrapolated_data['extrapolated'] = True
        extrapolated_data['source_count'] = len(cultural_insights)
        extrapolated_data['confidence_level'] = calculate_extrapolation_confidence(target_orchid, cultural_insights)
        
        return extrapolated_data
        
    except Exception as e:
        logger.error(f"Error synthesizing Baker recommendations: {str(e)}")
        return None

def calculate_extrapolation_confidence(target_orchid, cultural_insights):
    """Calculate confidence level for extrapolated recommendations"""
    if not cultural_insights:
        return 0.0
    
    confidence = 0.0
    for insight in cultural_insights:
        relationship = insight.get('relationship', '')
        if relationship == 'same_genus':
            confidence += 0.4  # Highest confidence
        elif relationship == 'same_region':
            confidence += 0.35  # High confidence for same endemic region
        elif relationship == 'endemic_region':
            confidence += 0.3   # Good confidence for broader geographic area
        elif relationship == 'similar_climate':
            confidence += 0.25  # Medium confidence
        elif relationship == 'similar_growth':
            confidence += 0.2   # Lower confidence
        else:
            confidence += 0.1   # Minimal confidence
    
    # Cap at 1.0 and adjust based on number of sources
    confidence = min(confidence, 1.0)
    if len(cultural_insights) >= 3:
        confidence *= 1.1  # Boost for multiple sources
    
    # Extra boost for endemic relationships (Baker's regional expertise)
    endemic_relationships = [i for i in cultural_insights if i.get('relationship') in ['same_region', 'endemic_region']]
    if len(endemic_relationships) >= 2:
        confidence *= 1.15  # Baker's regional expertise is highly valuable
    
    return min(confidence, 0.95)  # Conservative maximum

def analyze_baker_culture_data(cultural_notes):
    """
    Analyze Baker culture sheet data using AI to extract structured recommendations
    """
    try:
        if not cultural_notes or "BAKER'S CULTURE SHEET DATA" not in cultural_notes:
            return None
            
        system_prompt = """You are an expert orchid cultivation specialist analyzing Charles & Margaret Baker culture sheet data.
        
Extract and structure the following information from the culture notes:
        - climate_requirements: Specific temperature and climate needs
        - humidity_optimal: Ideal humidity range
        - seasonal_care: Care adjustments by season
        - weather_adaptations: How to adapt care based on weather conditions
        - growing_recommendations: Specific cultivation advice
        - risk_factors: Weather conditions to avoid
        - care_calendar: Monthly care schedule if mentioned
        
Provide actionable advice that can be used for weather-based growing recommendations.
        Return as structured JSON."""
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze this Baker culture data:\n\n{cultural_notes}"}
            ],
            response_format={"type": "json_object"},
            max_tokens=800
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        return json.loads(content)
        
    except Exception as e:
        logger.error(f"Error analyzing Baker culture data: {str(e)}")
        return None

def get_weather_based_care_advice(orchid_record, current_weather, forecast_data=None):
    """
    Generate AI-powered care advice based on Baker culture data and current weather
    """
    try:
        # Get Baker culture analysis if available
        baker_analysis = None
        if orchid_record.cultural_notes:
            baker_analysis = analyze_baker_culture_data(orchid_record.cultural_notes)
        
        # Prepare weather context
        weather_context = {
            'temperature': current_weather.get('temperature'),
            'humidity': current_weather.get('humidity'),
            'conditions': current_weather.get('description'),
            'forecast': forecast_data
        }
        
        system_prompt = """You are an expert orchid growing advisor. Provide specific care recommendations based on:
        1. Current weather conditions
        2. Baker culture sheet data (if available)
        3. Orchid species requirements
        
Provide practical, actionable advice for the next 2-3 days focusing on:
        - Watering adjustments
        - Humidity management 
        - Temperature protection
        - Light modifications
        - Ventilation needs
        
Be specific and practical. Limit to 2-3 key recommendations."""
        
        orchid_info = {
            'name': orchid_record.display_name,
            'scientific_name': orchid_record.scientific_name,
            'climate_preference': orchid_record.climate_preference,
            'temperature_range': orchid_record.temperature_range,
            'baker_culture_data': baker_analysis
        }
        
        response = openai_client.chat.completions.create(
            model="gpt-4o", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Weather: {weather_context}\n\nOrchid: {orchid_info}\n\nProvide care advice:"}
            ],
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        return content.strip()
        
    except Exception as e:
        logger.error(f"Error generating weather-based care advice: {str(e)}")
        return None

def extract_metadata_from_text(text_content):
    """
    Extract orchid metadata from scraped text content
    """
    try:
        prompt = f"""Analyze the following text content about orchids and extract structured metadata in JSON format.

Text content:
{text_content[:2000]}  # Limit text to avoid token limits

Please extract:
- orchid_names: List of orchid names mentioned
- cultural_information: Growing tips, care instructions
- botanical_details: Any technical botanical information
- locations: Geographic locations mentioned
- bloom_times: Flowering periods mentioned
- temperatures: Temperature requirements
- light_requirements: Light conditions mentioned
- watering_info: Watering instructions
- general_notes: Other relevant information

Return as JSON object."""

        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            max_tokens=1000
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        result = json.loads(content)
        return result
        
    except Exception as e:
        logger.error(f"Error extracting metadata from text: {str(e)}")
        return {'error': str(e)}

def classify_orchid_validity(image_path):
    """
    Determine if an image actually contains an orchid
    Returns confidence score and classification
    """
    try:
        base64_image = encode_image_to_base64(image_path)
        if not base64_image:
            return {'is_orchid': False, 'confidence': 0.0, 'reason': 'Image encoding failed'}
        
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert botanist. Analyze if this image contains an orchid flower or plant. Respond with JSON containing: is_orchid (boolean), confidence (0.0-1.0), and reason (explanation)."
                },
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": "Is this image an orchid? Please analyze and respond in JSON format."
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            response_format={"type": "json_object"},
            max_tokens=300
        )
        
        content = response.choices[0].message.content
        if not content:
            raise Exception("Empty response from AI model")
        result = json.loads(content)
        return result
        
    except Exception as e:
        logger.error(f"Error classifying orchid validity: {str(e)}")
        return {'is_orchid': False, 'confidence': 0.0, 'reason': f'Analysis error: {str(e)}'}

def calculate_photoperiod_requirements(ai_analysis):
    """
    Calculate photoperiod requirements based on AI analysis and Baker Daylength Database
    """
    try:
        from models import OrchidRecord
        
        # Get the Baker Daylength Database record
        daylength_db = OrchidRecord.query.filter(
            OrchidRecord.scientific_name.like('%Daylength%')
        ).filter_by(photographer='Charles and Margaret Baker').first()
        
        if not daylength_db or not daylength_db.cultural_notes:
            return None
        
        # Extract genus and potential native latitude from AI analysis
        genus = ai_analysis.get('genus', '')
        native_latitude = ai_analysis.get('native_latitude')
        photoperiod_sensitivity = ai_analysis.get('photoperiod_sensitivity', 'medium')
        climate_preference = ai_analysis.get('climate_preference', 'intermediate')
        
        # Generate photoperiod recommendations
        photoperiod_analysis = {
            'sensitivity_level': photoperiod_sensitivity,
            'recommended_daylight_hours': calculate_optimal_daylight(genus, climate_preference, native_latitude),
            'seasonal_variation': get_seasonal_daylight_pattern(genus, native_latitude),
            'bloom_photoperiod': get_bloom_triggering_daylight(genus, ai_analysis.get('bloom_triggers')),
            'cultivation_notes': generate_photoperiod_cultivation_notes(genus, photoperiod_sensitivity),
            'baker_daylength_reference': True,
            'data_source': 'Baker Orchid Daylength Database (25 latitudes, astronomical precision)'
        }
        
        return photoperiod_analysis
        
    except Exception as e:
        logger.error(f"Error calculating photoperiod requirements: {str(e)}")
        return None

def calculate_optimal_daylight(genus, climate_preference, native_latitude):
    """Calculate optimal daylight hours based on genus and climate"""
    # Default daylight recommendations based on orchid cultivation knowledge
    genus_daylight = {
        'Phalaenopsis': {'min': 11, 'max': 13, 'optimal': 12},  # Equatorial, stable photoperiod
        'Cattleya': {'min': 10, 'max': 14, 'optimal': 12.5},   # Tropical Americas, seasonal variation
        'Dendrobium': {'min': 9, 'max': 15, 'optimal': 12},    # Wide range, varies by species
        'Cymbidium': {'min': 8, 'max': 16, 'optimal': 14},     # Temperate, high seasonal variation
        'Oncidium': {'min': 10, 'max': 13, 'optimal': 11.5},   # Tropical, moderate variation
        'Paphiopedilum': {'min': 10, 'max': 12, 'optimal': 11},# Forest floor, stable low light
        'Vanda': {'min': 12, 'max': 14, 'optimal': 13},        # High light tropical
        'Miltonia': {'min': 10, 'max': 12, 'optimal': 11},     # Cloud forest, stable
        'Masdevallia': {'min': 9, 'max': 11, 'optimal': 10}    # Mountain, short days
    }
    
    base_daylight = genus_daylight.get(genus, {'min': 10, 'max': 14, 'optimal': 12})
    
    # Adjust based on climate preference
    climate_adjustments = {
        'cool': -0.5,      # Mountain species, shorter days
        'intermediate': 0,  # Balanced
        'warm': +0.5       # Lowland tropical, longer days
    }
    
    adjustment = climate_adjustments.get(climate_preference, 0)
    
    return {
        'minimum': base_daylight['min'] + adjustment,
        'maximum': base_daylight['max'] + adjustment,
        'optimal': base_daylight['optimal'] + adjustment,
        'notes': f'Optimal daylight for {genus} in {climate_preference} conditions'
    }

def get_seasonal_daylight_pattern(genus, native_latitude):
    """Determine seasonal daylight variation pattern"""
    # Latitude-based seasonal patterns
    if not native_latitude:
        # Default moderate seasonal pattern
        return {
            'pattern': 'moderate_seasonal',
            'winter_hours': 11,
            'summer_hours': 13,
            'variation': 2,
            'notes': 'Moderate seasonal daylight variation recommended'
        }
    
    # Parse latitude if provided as text
    try:
        if isinstance(native_latitude, str):
            # Extract numbers from text like "10-20°N" or "tropical 15°"
            import re
            numbers = re.findall(r'\d+', native_latitude)
            if numbers:
                lat_value = int(numbers[0])
            else:
                lat_value = 15  # Default tropical
        else:
            lat_value = int(native_latitude)
    except:
        lat_value = 15  # Default tropical
    
    # Seasonal patterns based on latitude
    if lat_value <= 10:  # Near equator
        return {
            'pattern': 'minimal_seasonal',
            'winter_hours': 11.5,
            'summer_hours': 12.5,
            'variation': 1,
            'notes': 'Minimal seasonal variation - near equatorial habitat'
        }
    elif lat_value <= 25:  # Tropical
        return {
            'pattern': 'moderate_seasonal',
            'winter_hours': 10.5,
            'summer_hours': 13.5,
            'variation': 3,
            'notes': 'Moderate seasonal variation - tropical habitat'
        }
    elif lat_value <= 40:  # Subtropical
        return {
            'pattern': 'strong_seasonal',
            'winter_hours': 9,
            'summer_hours': 15,
            'variation': 6,
            'notes': 'Strong seasonal variation - subtropical habitat'
        }
    else:  # Temperate
        return {
            'pattern': 'extreme_seasonal',
            'winter_hours': 8,
            'summer_hours': 16,
            'variation': 8,
            'notes': 'Extreme seasonal variation - temperate habitat'
        }

def get_bloom_triggering_daylight(genus, bloom_triggers):
    """Determine daylight hours that trigger blooming"""
    # Common bloom-triggering photoperiods by genus
    genus_bloom_triggers = {
        'Cattleya': {'type': 'shortening_days', 'trigger_hours': 11, 'season': 'fall'},
        'Cymbidium': {'type': 'lengthening_days', 'trigger_hours': 10, 'season': 'late_winter'},
        'Dendrobium': {'type': 'seasonal_change', 'trigger_hours': 12, 'season': 'spring'},
        'Phalaenopsis': {'type': 'stable_short', 'trigger_hours': 11.5, 'season': 'winter'},
        'Oncidium': {'type': 'moderate_change', 'trigger_hours': 12, 'season': 'variable'}
    }
    
    trigger_info = genus_bloom_triggers.get(genus, {
        'type': 'seasonal_change',
        'trigger_hours': 12,
        'season': 'spring'
    })
    
    # Enhance with AI-detected bloom triggers
    if bloom_triggers:
        if 'temperature drop' in bloom_triggers.lower():
            trigger_info['additional_trigger'] = 'Cool temperatures enhance photoperiod response'
        if 'dry period' in bloom_triggers.lower():
            trigger_info['additional_trigger'] = 'Dry season combined with shorter days'
        if 'seasonal light' in bloom_triggers.lower():
            trigger_info['photoperiod_critical'] = True
    
    return trigger_info

def generate_photoperiod_cultivation_notes(genus, sensitivity_level):
    """Generate specific cultivation notes for photoperiod management"""
    sensitivity_notes = {
        'high': [
            'Photoperiod is CRITICAL for blooming - must simulate natural seasonal changes',
            'Use programmable LED lights with precise timing controls',
            'Monitor daylight duration changes weekly during bloom season',
            'Artificial lighting schedules should match native habitat patterns'
        ],
        'medium': [
            'Moderate photoperiod sensitivity - seasonal changes helpful for blooming',
            'Provide gradual seasonal adjustments in artificial lighting',
            'Natural window light with supplemental evening lighting works well',
            'Adjust lighting schedule 15 minutes every 2 weeks during transitions'
        ],
        'low': [
            'Low photoperiod sensitivity - consistent lighting adequate',
            'Standard 12-hour light cycles work for most of the year',
            'Minor seasonal adjustments may improve blooming consistency',
            'Focus more on temperature and humidity than precise photoperiod'
        ]
    }
    
    base_notes = sensitivity_notes.get(sensitivity_level, sensitivity_notes['medium'])
    
    # Add genus-specific notes
    genus_specific = {
        'Cattleya': 'Many Cattleyas are short-day bloomers - reduce daylight in fall',
        'Cymbidium': 'Cool-growing Cymbidiums need long winter nights for spike initiation',
        'Dendrobium': 'Deciduous Dendrobiums require distinct seasonal photoperiod changes',
        'Phalaenopsis': 'Stable shorter days in winter help trigger blooming spikes'
    }
    
    if genus in genus_specific:
        base_notes.append(genus_specific[genus])
    
    return base_notes
