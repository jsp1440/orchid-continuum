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
