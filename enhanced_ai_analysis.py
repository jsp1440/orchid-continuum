#!/usr/bin/env python3
"""
Enhanced AI Analysis Methods for AI Breeder Pro
Implements the improved image analysis approach from orchid_continuum.py script
Integrates Google Cloud functionality for comprehensive breeding analysis
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import base64
from io import BytesIO

# Setup logging
logger = logging.getLogger(__name__)

def enhanced_image_analysis_with_drive_upload(image_data: bytes, filename: str, 
                                            breeder_notes: str = "", 
                                            google_integration = None) -> Dict[str, Any]:
    """
    Enhanced image analysis with Google Drive upload and AI analysis
    Based on the improved approach from orchid_continuum.py
    """
    try:
        # Upload image to Google Drive if available
        drive_url = None
        if google_integration and google_integration.is_available():
            drive_url = google_integration.upload_image_to_drive(image_data, filename)
            if drive_url:
                logger.info(f"📸 Uploaded {filename} to Google Drive: {drive_url}")
        
        # Enhanced AI analysis using the improved approach
        ai_analysis_result = perform_enhanced_ai_analysis(
            image_data=image_data,
            image_url=drive_url,
            breeder_notes=breeder_notes,
            filename=filename
        )
        
        return {
            'local_analysis': ai_analysis_result,
            'drive_url': drive_url,
            'uploaded_successfully': drive_url is not None,
            'filename': filename,
            'analysis_timestamp': datetime.now().isoformat(),
            'enhanced_features': True
        }
        
    except Exception as e:
        logger.error(f"❌ Enhanced image analysis failed: {e}")
        return {
            'error': str(e),
            'uploaded_successfully': False,
            'enhanced_features': False
        }

def perform_enhanced_ai_analysis(image_data: bytes, image_url: str = None, 
                               breeder_notes: str = "", filename: str = "") -> Dict[str, Any]:
    """
    Perform enhanced AI analysis using the improved approach from orchid_continuum.py
    """
    try:
        # Get OpenAI client (using the same lazy initialization pattern)
        from ai_breeder_assistant_pro import get_openai_client
        client = get_openai_client()
        
        if not client:
            return get_fallback_analysis(breeder_notes, filename)
        
        # Enhanced prompt based on orchid_continuum.py approach
        analysis_prompt = create_enhanced_analysis_prompt(image_url, breeder_notes, filename)
        
        # Prepare image for analysis
        image_base64 = None
        if image_data:
            image_base64 = base64.b64encode(image_data).decode('utf-8')
        
        # Enhanced AI analysis with image vision
        response = client.chat.completions.create(
            model="gpt-4o",  # Use vision-capable model
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": analysis_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}" if image_base64 else image_url
                            }
                        } if (image_base64 or image_url) else {"type": "text", "text": "No image provided for analysis."}
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Parse and structure the AI response
        structured_analysis = parse_enhanced_ai_response(ai_response, breeder_notes)
        
        logger.info(f"✅ Enhanced AI analysis completed for {filename}")
        return structured_analysis
        
    except Exception as e:
        logger.error(f"❌ AI analysis failed: {e}")
        return get_fallback_analysis(breeder_notes, filename, error=str(e))

def create_enhanced_analysis_prompt(image_url: str, breeder_notes: str, filename: str) -> str:
    """
    Create enhanced analysis prompt based on orchid_continuum.py approach
    """
    base_url_text = f"Image URL: {image_url}" if image_url else "Analyzing uploaded image"
    
    prompt = f"""
    Analyze this orchid breeding image with comprehensive detail: {base_url_text}
    
    **Breeding Context:**
    Filename: {filename}
    Breeder Notes: {breeder_notes}
    
    **Analysis Requirements:**
    
    1. **Morphological Analysis:**
       - Flower form, size, and symmetry
       - Petal and sepal characteristics
       - Lip structure and coloration patterns
       - Column and reproductive structures
       - Overall plant habit and growth pattern
    
    2. **Inheritance Pattern Prediction:**
       - Predicted traits from visible parent characteristics
       - Color inheritance patterns and dominance
       - Size and shape trait expression
       - Flowering habit and timing predictions
       - Vigor and growth characteristics
    
    3. **Breeding Success Indicators:**
       - Flower quality assessment (1-10 scale)
       - Genetic diversity indicators
       - Potential for naming/registration
       - Commercial viability assessment
       - Breeding line development potential
    
    4. **Cultural Requirements Prediction:**
       - Light requirements based on morphology
       - Temperature preferences from parent characteristics
       - Watering and humidity needs
       - Potting medium recommendations
       - Growth habit implications for culture
    
    5. **Breeder Intent Alignment:**
       - Compare observed traits with breeder goals: {breeder_notes}
       - Assess achievement of breeding objectives
       - Identify unexpected positive traits
       - Note areas for improvement in future crosses
       - Success probability for naming (percentage)
    
    6. **Research-Grade Recommendations:**
       - Future breeding directions
       - Line development strategies
       - Cultural optimization suggestions
       - Documentation and record-keeping advice
       - Timeline for evaluation and decisions
    
    **Output Format:**
    Provide detailed analysis in JSON-compatible structure with specific scores, predictions, and actionable recommendations. Focus on practical breeding insights and measurable outcomes.
    """
    
    return prompt

def parse_enhanced_ai_response(ai_response: str, breeder_notes: str) -> Dict[str, Any]:
    """
    Parse and structure the enhanced AI response into usable data
    """
    try:
        # Try to extract JSON if present
        if '{' in ai_response and '}' in ai_response:
            start_idx = ai_response.find('{')
            end_idx = ai_response.rfind('}') + 1
            json_str = ai_response[start_idx:end_idx]
            try:
                structured_data = json.loads(json_str)
                return enhance_parsed_structure(structured_data, ai_response)
            except json.JSONDecodeError:
                pass
        
        # Fallback to text parsing
        return parse_text_response(ai_response, breeder_notes)
        
    except Exception as e:
        logger.error(f"❌ Error parsing AI response: {e}")
        return get_fallback_analysis(breeder_notes, "unknown", error=str(e))

def enhance_parsed_structure(data: Dict[str, Any], full_response: str) -> Dict[str, Any]:
    """
    Enhance parsed JSON structure with additional metadata
    """
    enhanced = {
        'analysis_type': 'enhanced_ai_vision',
        'analysis_timestamp': datetime.now().isoformat(),
        'full_response': full_response,
        'structured_data': data,
        'quality_score': extract_quality_score(data, full_response),
        'breeding_recommendations': extract_recommendations(data, full_response),
        'success_probability': extract_success_probability(data, full_response),
        'trait_predictions': extract_trait_predictions(data, full_response),
        'cultural_requirements': extract_cultural_requirements(data, full_response)
    }
    
    return enhanced

def parse_text_response(response: str, breeder_notes: str) -> Dict[str, Any]:
    """
    Parse text-based AI response when JSON parsing fails
    """
    sections = response.split('\n\n')
    
    parsed = {
        'analysis_type': 'enhanced_ai_text',
        'analysis_timestamp': datetime.now().isoformat(),
        'full_response': response,
        'morphological_analysis': extract_section(sections, 'morphological', 'flower'),
        'inheritance_predictions': extract_section(sections, 'inheritance', 'trait'),
        'breeding_assessment': extract_section(sections, 'breeding', 'success'),
        'cultural_requirements': extract_section(sections, 'cultural', 'requirement'),
        'breeder_alignment': extract_section(sections, 'breeder', 'intent'),
        'recommendations': extract_section(sections, 'recommendation', 'suggest'),
        'quality_score': extract_numeric_score(response),
        'success_probability': extract_probability(response),
    }
    
    return parsed

def extract_section(sections: List[str], *keywords: str) -> str:
    """Extract relevant section based on keywords"""
    for section in sections:
        if any(keyword.lower() in section.lower() for keyword in keywords):
            return section.strip()
    return ""

def extract_quality_score(data: Dict[str, Any], text: str) -> float:
    """Extract quality score from structured data or text"""
    if isinstance(data, dict):
        score = data.get('quality_score') or data.get('flower_quality') or data.get('overall_score')
        if score:
            return float(score)
    
    return extract_numeric_score(text)

def extract_numeric_score(text: str) -> float:
    """Extract numeric score from text"""
    import re
    
    # Look for score patterns
    patterns = [
        r'(\d+(?:\.\d+)?)/10',
        r'score.*?(\d+(?:\.\d+)?)',
        r'quality.*?(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)%'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            # Normalize to 0-10 scale if needed
            if score > 10:
                score = score / 10
            return min(10.0, max(0.0, score))
    
    return 7.5  # Default moderate score

def extract_success_probability(data: Dict[str, Any], text: str) -> float:
    """Extract success probability"""
    if isinstance(data, dict):
        prob = data.get('success_probability') or data.get('breeding_success')
        if prob:
            return float(prob)
    
    return extract_probability(text)

def extract_probability(text: str) -> float:
    """Extract probability percentage from text"""
    import re
    
    patterns = [
        r'(\d+(?:\.\d+)?)%.*?success',
        r'success.*?(\d+(?:\.\d+)?)%',
        r'probability.*?(\d+(?:\.\d+)?)%'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return 75.0  # Default moderate probability

def extract_recommendations(data: Dict[str, Any], text: str) -> List[str]:
    """Extract breeding recommendations"""
    if isinstance(data, dict):
        recs = data.get('recommendations') or data.get('breeding_recommendations')
        if recs and isinstance(recs, list):
            return recs
    
    # Extract from text
    import re
    lines = text.split('\n')
    recommendations = []
    
    for line in lines:
        if any(word in line.lower() for word in ['recommend', 'suggest', 'should', 'consider']):
            recommendations.append(line.strip())
    
    return recommendations[:5]  # Limit to top 5

def extract_trait_predictions(data: Dict[str, Any], text: str) -> List[Dict[str, str]]:
    """Extract trait predictions"""
    predictions = []
    
    if isinstance(data, dict):
        traits = data.get('trait_predictions') or data.get('inheritance_patterns')
        if traits:
            return traits if isinstance(traits, list) else [traits]
    
    # Extract from text
    import re
    trait_keywords = ['color', 'size', 'shape', 'vigor', 'flowering', 'fragrance', 'pattern']
    
    for keyword in trait_keywords:
        pattern = rf'{keyword}.*?([^.]+\.)' 
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            predictions.append({
                'trait': keyword,
                'prediction': match.strip()
            })
    
    return predictions

def extract_cultural_requirements(data: Dict[str, Any], text: str) -> Dict[str, str]:
    """Extract cultural requirements"""
    if isinstance(data, dict):
        culture = data.get('cultural_requirements') or data.get('culture')
        if culture:
            return culture
    
    # Extract from text
    requirements = {}
    import re
    
    culture_patterns = {
        'light': r'light.*?([^.]+\.)',
        'temperature': r'temperature.*?([^.]+\.)',
        'water': r'water.*?([^.]+\.)',
        'humidity': r'humidity.*?([^.]+\.)',
        'medium': r'medium.*?([^.]+\.)'
    }
    
    for key, pattern in culture_patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            requirements[key] = match.group(1).strip()
    
    return requirements

def get_fallback_analysis(breeder_notes: str, filename: str, error: str = None) -> Dict[str, Any]:
    """
    Provide fallback analysis when AI analysis fails
    """
    return {
        'analysis_type': 'fallback',
        'analysis_timestamp': datetime.now().isoformat(),
        'filename': filename,
        'breeder_notes': breeder_notes,
        'error': error,
        'quality_score': 6.0,
        'success_probability': 65.0,
        'fallback_recommendations': [
            "📸 High-quality images recommended for detailed analysis",
            "🔬 Manual evaluation of flower characteristics suggested",
            "📊 Document key traits for future reference",
            "🌱 Monitor growth patterns and flowering behavior",
            "📝 Maintain detailed breeding records"
        ],
        'note': 'AI analysis unavailable - using fallback assessment'
    }

def save_breeding_analysis_with_cloud_integration(analysis_data: Dict[str, Any], 
                                                google_integration = None) -> bool:
    """
    Save breeding analysis data to Google Sheets with cloud integration
    """
    try:
        if not google_integration or not google_integration.is_available():
            logger.warning("⚠️ Google Cloud integration not available for data persistence")
            return False
        
        # Prepare breeding data for Google Sheets
        breeding_data = {
            'hybrid_name': analysis_data.get('filename', 'Unknown'),
            'parent1': extract_parent_from_analysis(analysis_data, 1),
            'parent2': extract_parent_from_analysis(analysis_data, 2),
            'genus': 'Sarcochilus',  # Default, could be enhanced with detection
            'breeder_notes': analysis_data.get('breeder_notes', ''),
            'ai_analysis': json.dumps(analysis_data, indent=2),
            'image_urls': analysis_data.get('drive_url', ''),
            'source': 'AI Breeder Pro Enhanced',
            'success_rating': str(analysis_data.get('success_probability', 0)),
            'vigor_notes': extract_vigor_notes(analysis_data),
            'color_notes': extract_color_notes(analysis_data),
            'size_notes': extract_size_notes(analysis_data)
        }
        
        success = google_integration.save_breeding_data(breeding_data)
        if success:
            logger.info(f"✅ Saved breeding analysis to Google Sheets: {breeding_data['hybrid_name']}")
        
        return success
        
    except Exception as e:
        logger.error(f"❌ Failed to save breeding analysis to cloud: {e}")
        return False

def extract_parent_from_analysis(analysis_data: Dict[str, Any], parent_num: int) -> str:
    """Extract parent information from analysis data"""
    notes = analysis_data.get('breeder_notes', '')
    
    # Look for parent patterns in breeder notes
    import re
    patterns = [
        r'parent\s*' + str(parent_num) + r'.*?([^,\n]+)',
        r'(?:×|x)\s*([^,\n]+)' if parent_num == 2 else r'([^×x,\n]+)\s*(?:×|x)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, notes, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return f"Parent {parent_num} (from {analysis_data.get('filename', 'unknown')})"

def extract_vigor_notes(analysis_data: Dict[str, Any]) -> str:
    """Extract vigor-related notes from analysis"""
    text = str(analysis_data.get('full_response', ''))
    vigor_keywords = ['vigor', 'growth', 'robust', 'healthy', 'strong', 'weak']
    
    vigor_sentences = []
    for sentence in text.split('.'):
        if any(keyword in sentence.lower() for keyword in vigor_keywords):
            vigor_sentences.append(sentence.strip())
    
    return '. '.join(vigor_sentences[:2])  # Top 2 vigor-related sentences

def extract_color_notes(analysis_data: Dict[str, Any]) -> str:
    """Extract color-related notes from analysis"""
    text = str(analysis_data.get('full_response', ''))
    color_keywords = ['color', 'colour', 'red', 'white', 'yellow', 'pink', 'purple', 'green', 'pattern', 'spot']
    
    color_sentences = []
    for sentence in text.split('.'):
        if any(keyword in sentence.lower() for keyword in color_keywords):
            color_sentences.append(sentence.strip())
    
    return '. '.join(color_sentences[:2])  # Top 2 color-related sentences

def extract_size_notes(analysis_data: Dict[str, Any]) -> str:
    """Extract size-related notes from analysis"""
    text = str(analysis_data.get('full_response', ''))
    size_keywords = ['size', 'large', 'small', 'compact', 'miniature', 'standard', 'dimension']
    
    size_sentences = []
    for sentence in text.split('.'):
        if any(keyword in sentence.lower() for keyword in size_keywords):
            size_sentences.append(sentence.strip())
    
    return '. '.join(size_sentences[:2])  # Top 2 size-related sentences