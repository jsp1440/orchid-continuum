#!/usr/bin/env python3
"""
AI Orchid Chat Interface
========================
Direct AI communication system for orchid image analysis and data interaction.
Uses GPT-5 with vision capabilities for real-time orchid analysis.
"""

import json
import os
import base64
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, session
from openai import OpenAI
from models import OrchidRecord, OrchidTaxonomy
from app import db
from sqlalchemy import or_, func
import requests
from io import BytesIO

logger = logging.getLogger(__name__)

# Initialize OpenAI with GPT-5 (the newest OpenAI model released August 7, 2025)
# do not change this unless explicitly requested by the user
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

ai_chat_bp = Blueprint('ai_chat', __name__, url_prefix='/ai-chat')

class OrchidAI:
    """AI system for orchid analysis and data interaction"""
    
    def __init__(self):
        self.conversation_history = []
        self.system_prompt = """You are an expert orchid botanist and AI assistant specializing in orchid identification, cultivation, and research. You have access to a comprehensive orchid database with thousands of species and can analyze orchid images in real-time.

Your capabilities include:
- Identifying orchid species from images
- Providing detailed information about orchid care, habitat, and characteristics
- Analyzing flowering patterns, growth habits, and health
- Querying the orchid database for specific information
- Offering cultivation advice and troubleshooting
- Explaining taxonomy and botanical relationships

Always provide accurate, scientific information while being accessible to both beginners and experts. When analyzing images, be specific about what you observe and confident in your identifications when certain."""

    def analyze_orchid_image(self, image_url: str, user_question: str = None) -> Dict[str, Any]:
        """Analyze an orchid image using GPT-5 vision"""
        try:
            # Prepare the message
            message_content = [
                {
                    "type": "text",
                    "text": f"""As an expert orchid botanist, analyze this orchid image in detail. Provide:

1. **Species Identification**: Best guess for genus and species
2. **Confidence Level**: How certain you are (1-10 scale)
3. **Key Characteristics**: Notable features you observe
4. **Flowering Status**: Current flowering stage if visible
5. **Health Assessment**: Overall plant condition
6. **Growing Conditions**: Apparent environment/setup
7. **Care Recommendations**: Specific advice based on what you see

{f'User asked: {user_question}' if user_question else ''}

Format your response as detailed observations with scientific accuracy."""
                },
                {
                    "type": "image_url",
                    "image_url": {"url": image_url}
                }
            ]

            response = openai_client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message_content}
                ],
                max_tokens=1000,
                temperature=0.3
            )

            analysis = response.choices[0].message.content
            
            # Log the analysis
            logger.info(f"🤖 AI analyzed orchid image: {len(analysis)} chars")
            
            return {
                'success': True,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-5'
            }
            
        except Exception as e:
            logger.error(f"❌ Error analyzing orchid image: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def chat_with_data(self, user_message: str, context: Dict = None) -> Dict[str, Any]:
        """Chat with AI about orchid data and provide intelligent responses"""
        try:
            # Get relevant orchid data based on the question
            orchid_context = self._get_relevant_orchid_data(user_message)
            
            # Build enhanced prompt with database context
            enhanced_prompt = f"""User question: {user_message}

Available orchid database context:
{json.dumps(orchid_context, indent=2)}

Please provide a helpful response based on the orchid data available. If the user is asking about specific orchids, reference the database information. If they're asking general questions, use your botanical expertise."""

            response = openai_client.chat.completions.create(
                model="gpt-5",  # the newest OpenAI model is "gpt-5" which was released August 7, 2025
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": enhanced_prompt}
                ],
                max_tokens=800,
                temperature=0.4
            )

            ai_response = response.choices[0].message.content
            
            return {
                'success': True,
                'response': ai_response,
                'context_used': orchid_context,
                'timestamp': datetime.now().isoformat(),
                'model': 'gpt-5'
            }
            
        except Exception as e:
            logger.error(f"❌ Error in AI chat: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def _get_relevant_orchid_data(self, query: str) -> Dict[str, Any]:
        """Get relevant orchid data from database based on user query"""
        try:
            query_lower = query.lower()
            context = {
                'total_orchids': 0,
                'matching_orchids': [],
                'genera_stats': {},
                'flowering_data': {}
            }
            
            # Get total count
            context['total_orchids'] = OrchidRecord.query.count()
            
            # Search for relevant orchids based on query terms
            search_terms = []
            
            # Common orchid genera
            orchid_genera = ['cattleya', 'phalaenopsis', 'dendrobium', 'oncidium', 'vanda', 
                           'paphiopedilum', 'cymbidium', 'epidendrum', 'brassia', 'miltonia']
            
            for genus in orchid_genera:
                if genus in query_lower:
                    search_terms.append(genus)
            
            # Other botanical terms
            botanical_terms = ['flowering', 'bloom', 'flower', 'species', 'hybrid', 'care', 
                             'habitat', 'native', 'epiphyte', 'terrestrial']
            
            # Search database
            if search_terms:
                orchids = OrchidRecord.query.filter(
                    or_(*[OrchidRecord.genus.ilike(f'%{term}%') for term in search_terms])
                ).limit(10).all()
                
                context['matching_orchids'] = [{
                    'id': o.id,
                    'display_name': o.display_name,
                    'genus': o.genus,
                    'species': o.species,
                    'native_habitat': o.native_habitat,
                    'bloom_time': o.bloom_time,
                    'growth_habit': o.growth_habit,
                    'is_flowering': o.is_flowering,
                    'ai_description': o.ai_description[:200] if o.ai_description else None
                } for o in orchids]
            
            # Get genera statistics
            genera_stats = db.session.query(
                OrchidRecord.genus, 
                func.count(OrchidRecord.id)
            ).group_by(OrchidRecord.genus).limit(10).all()
            
            context['genera_stats'] = {genus: count for genus, count in genera_stats}
            
            # Get flowering statistics
            flowering_orchids = OrchidRecord.query.filter(OrchidRecord.is_flowering == True).count()
            context['flowering_data'] = {
                'currently_flowering': flowering_orchids,
                'percentage': round((flowering_orchids / context['total_orchids']) * 100, 1) if context['total_orchids'] > 0 else 0
            }
            
            return context
            
        except Exception as e:
            logger.error(f"❌ Error getting orchid data: {e}")
            return {'error': str(e)}

# Global AI instance
orchid_ai = OrchidAI()

@ai_chat_bp.route('/')
def ai_chat_interface():
    """Main AI chat interface"""
    return render_template('ai_chat/interface.html')

@ai_chat_bp.route('/chat', methods=['POST'])
def handle_chat():
    """Handle chat messages from user"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Process chat with AI
        response = orchid_ai.chat_with_data(user_message)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"❌ Error handling chat: {e}")
        return jsonify({'error': str(e)}), 500

@ai_chat_bp.route('/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze an orchid image with AI"""
    try:
        data = request.get_json()
        image_url = data.get('image_url', '')
        user_question = data.get('question', '')
        orchid_id = data.get('orchid_id', None)
        
        if not image_url:
            return jsonify({'error': 'No image URL provided'}), 400
        
        # If orchid_id provided, get additional context
        context = {}
        if orchid_id:
            orchid = OrchidRecord.query.get(orchid_id)
            if orchid:
                context = {
                    'display_name': orchid.display_name,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'existing_ai_description': orchid.ai_description
                }
        
        # Analyze with AI
        result = orchid_ai.analyze_orchid_image(image_url, user_question)
        result['context'] = context
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"❌ Error analyzing image: {e}")
        return jsonify({'error': str(e)}), 500

@ai_chat_bp.route('/orchid-suggestions')
def get_orchid_suggestions():
    """Get orchid suggestions for analysis"""
    try:
        # Get recent orchids with images
        orchids = OrchidRecord.query.filter(
            or_(
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.image_url.isnot(None)
            )
        ).order_by(OrchidRecord.id.desc()).limit(12).all()
        
        suggestions = []
        for orchid in orchids:
            image_url = None
            if orchid.google_drive_id:
                image_url = f"/api/drive-photo/{orchid.google_drive_id}"
            elif orchid.image_url:
                image_url = orchid.image_url
                
            if image_url:
                suggestions.append({
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'image_url': image_url,
                    'has_ai_analysis': bool(orchid.ai_description)
                })
        
        return jsonify(suggestions)
        
    except Exception as e:
        logger.error(f"❌ Error getting orchid suggestions: {e}")
        return jsonify({'error': str(e)}), 500

def register_ai_chat_routes(app):
    """Register AI chat routes with Flask app"""
    app.register_blueprint(ai_chat_bp)
    logger.info("🤖 AI Orchid Chat interface registered successfully")