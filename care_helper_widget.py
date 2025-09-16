#!/usr/bin/env python3
"""
Simple Care Helper Widget
========================
Natural language orchid care advisor using existing AI systems.
Provides conversational care advice accessible to regular users.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from flask import Blueprint, render_template, request, jsonify
from orchid_ai import get_weather_based_care_advice
from location_based_culture_system import LocationBasedCultureSystem
import openai
import os

logger = logging.getLogger(__name__)

care_helper_bp = Blueprint('care_helper', __name__, url_prefix='/care-helper')

class SimpleCareAdvisor:
    """Simple conversational care advisor for orchid problems"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        self.location_system = LocationBasedCultureSystem()
    
    def get_care_advice(self, user_question: str, location: str = None) -> Dict[str, Any]:
        """
        Get conversational care advice for orchid problems
        Uses existing AI backend but formats for simple conversation
        """
        try:
            # Extract key information from user question
            extracted_info = self._extract_question_details(user_question, location)
            
            # Get location data if provided
            location_data = None
            if location:
                location_data = self._parse_location(location)
            
            # Generate care advice using existing AI systems
            advice = self._generate_care_advice(extracted_info, location_data)
            
            return {
                'success': True,
                'advice': advice,
                'extracted_info': extracted_info,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating care advice: {e}")
            return {
                'success': False,
                'error': 'Unable to generate care advice at this time.',
                'timestamp': datetime.now().isoformat()
            }
    
    def _extract_question_details(self, question: str, location: str = None) -> Dict[str, Any]:
        """Extract orchid species, problem, and location from natural language"""
        try:
            if not self.openai_client:
                return {'species': 'unknown', 'problem': question, 'location': location}
            
            extraction_prompt = f"""
Extract key information from this orchid care question and return as JSON:

Question: "{question}"
Location: "{location or 'not specified'}"

Return in this exact format:
{{
    "orchid_species": "best guess at genus and species",
    "genus": "genus only if identifiable", 
    "problem_type": "yellowing leaves|root rot|not blooming|pest issue|general care|other",
    "symptoms": "list of symptoms mentioned",
    "location": "standardized location if provided",
    "urgency": "low|medium|high based on problem severity"
}}
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert at extracting orchid care information from natural language questions."},
                    {"role": "user", "content": extraction_prompt}
                ],
                max_tokens=300,
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            logger.warning(f"Could not extract question details: {e}")
            return {
                'orchid_species': 'unknown',
                'problem_type': 'general care',
                'symptoms': question,
                'location': location,
                'urgency': 'medium'
            }
    
    def _parse_location(self, location_str: str) -> Optional[Dict[str, Any]]:
        """Parse location string into structured data"""
        # Simple location parsing - could be enhanced with geocoding
        location_parts = [part.strip() for part in location_str.split(',')]
        
        if len(location_parts) >= 2:
            return {
                'city': location_parts[0],
                'state_or_region': location_parts[1],
                'country': location_parts[2] if len(location_parts) > 2 else 'USA',
                'raw_location': location_str
            }
        else:
            return {
                'raw_location': location_str,
                'city': location_str,
                'state_or_region': '',
                'country': 'USA'
            }
    
    def _generate_care_advice(self, extracted_info: Dict[str, Any], location_data: Optional[Dict[str, Any]]) -> str:
        """Generate conversational care advice using existing AI systems"""
        try:
            if not self.openai_client:
                return "AI service not available. Please check your API configuration."
            
            # Build context for AI response
            context_parts = []
            
            if extracted_info.get('orchid_species') != 'unknown':
                context_parts.append(f"Species: {extracted_info['orchid_species']}")
            
            if location_data:
                context_parts.append(f"Location: {location_data['raw_location']}")
            
            if extracted_info.get('symptoms'):
                context_parts.append(f"Problem: {extracted_info['symptoms']}")
            
            context = " | ".join(context_parts)
            
            # Generate care advice using GPT with orchid expertise
            advice_prompt = f"""
You are an expert orchid botanist providing care advice. A user has this orchid problem:

{context}

Provide helpful, practical care advice in a friendly conversational tone. Be specific about:
1. Most likely causes of the problem
2. Immediate actions to take
3. Location-specific considerations if location provided
4. Timeline for improvement
5. Prevention tips

Keep the response clear, actionable, and encouraging. If you're not certain about species identification, give general advice that would work for most orchids.
"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a friendly, expert orchid care advisor. Provide practical, encouraging advice."},
                    {"role": "user", "content": advice_prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI advice: {e}")
            return "I'm having trouble generating advice right now. Please try again later or consult with a local orchid expert."

# Initialize the care advisor
care_advisor = SimpleCareAdvisor()

@care_helper_bp.route('/')
def care_helper_interface():
    """Main care helper widget interface"""
    return render_template('care_helper/widget.html')

@care_helper_bp.route('/ask', methods=['POST'])
def ask_care_question():
    """Handle care questions via AJAX"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        location = data.get('location', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Please enter a question about your orchid.'})
        
        # Get care advice
        result = care_advisor.get_care_advice(question, location)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error handling care question: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to process your question. Please try again.'
        })

@care_helper_bp.route('/widget-embed')
def widget_embed():
    """Embeddable version of the care helper widget"""
    return render_template('care_helper/widget_embed.html')

def register_care_helper_routes(app):
    """Register care helper routes with Flask app"""
    app.register_blueprint(care_helper_bp)
    logger.info("🌺 Care Helper widget registered successfully")