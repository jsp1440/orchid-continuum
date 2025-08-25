import json
import os
import base64
from PIL import Image
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)

# the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "your-api-key-here")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

def encode_image_to_base64(image_path):
    """Convert image to base64 for API submission"""
    try:
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except Exception as e:
        logger.error(f"Error encoding image: {str(e)}")
        return None

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
        
        # Prepare the prompt for orchid analysis
        system_prompt = """You are an expert orchid taxonomist and botanist. Analyze this orchid image and provide detailed information in JSON format.

Please identify and extract the following information:
- scientific_name: The full scientific name if identifiable
- genus: The orchid genus
- species: The species name if identifiable  
- suggested_name: A display name for this orchid
- description: Detailed description of the flower, plant, and notable features
- confidence: Your confidence level (0.0 to 1.0) in the identification
- growth_habit: epiphytic, terrestrial, or lithophytic
- climate_preference: cool, intermediate, or warm
- bloom_characteristics: Details about the flowers
- leaf_form: Description of the leaves
- pseudobulb_presence: true/false if pseudobulbs are visible
- cultural_tips: Basic growing advice based on the orchid type
- notable_features: Any distinctive characteristics
- metadata: Any additional relevant botanical information

If you cannot identify the exact species, focus on genus-level identification and general orchid characteristics. Be honest about uncertainty levels."""

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
        result = json.loads(response.choices[0].message.content)
        
        # Ensure required fields have defaults
        defaults = {
            'suggested_name': 'Unknown Orchid',
            'scientific_name': None,
            'genus': None,
            'species': None,
            'description': 'Orchid identification pending',
            'confidence': 0.0,
            'growth_habit': None,
            'climate_preference': None,
            'bloom_characteristics': None,
            'leaf_form': None,
            'pseudobulb_presence': None,
            'cultural_tips': None,
            'notable_features': None,
            'metadata': {}
        }
        
        # Merge defaults with results
        for key, default_value in defaults.items():
            if key not in result:
                result[key] = default_value
        
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
        
        # Combine and analyze all relevant Baker data
        all_relevant = genus_matches + climate_matches + growth_matches
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

def get_relationship_type(target_orchid, baker_orchid):
    """Determine the taxonomic/ecological relationship between orchids"""
    target_genus = target_orchid.scientific_name.split(' ')[0] if target_orchid.scientific_name else ''
    baker_genus = baker_orchid.scientific_name.split(' ')[0] if baker_orchid.scientific_name else ''
    
    if target_genus == baker_genus:
        return 'same_genus'
    elif target_orchid.climate_preference == baker_orchid.climate_preference:
        return 'similar_climate'
    elif target_orchid.growth_habit == baker_orchid.growth_habit:
        return 'similar_growth'
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

Consider:
- Taxonomic relationships (same genus = highest priority)
- Climate preference similarities
- Growth habit similarities
- Common patterns across related species

Provide practical, actionable advice focusing on:
- Temperature and climate needs
- Humidity requirements
- Watering patterns
- Light requirements
- Seasonal care adjustments

Be conservative - only extrapolate what can be reasonably inferred from the related species data."""

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
        
        extrapolated_data = json.loads(response.choices[0].message.content)
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
            confidence += 0.4
        elif relationship == 'similar_climate':
            confidence += 0.3
        elif relationship == 'similar_growth':
            confidence += 0.2
        else:
            confidence += 0.1
    
    # Cap at 1.0 and adjust based on number of sources
    confidence = min(confidence, 1.0)
    if len(cultural_insights) >= 3:
        confidence *= 1.1  # Boost for multiple sources
    
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
        
        return json.loads(response.choices[0].message.content)
        
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
        
        return response.choices[0].message.content.strip()
        
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
        
        result = json.loads(response.choices[0].message.content)
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
        
        result = json.loads(response.choices[0].message.content)
        return result
        
    except Exception as e:
        logger.error(f"Error classifying orchid validity: {str(e)}")
        return {'is_orchid': False, 'confidence': 0.0, 'reason': f'Analysis error: {str(e)}'}
