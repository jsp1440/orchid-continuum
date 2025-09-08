"""
AI Breeder Assistant Pro - Unified Orchid Breeding Analysis Widget
Consolidates breeding tools using Jeff Parham's Sarcochilus F226 research methodology
Created for Neon One integration
"""

import os
import json
import openai
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import Blueprint, render_template, request, jsonify, current_app
from models import OrchidRecord
from app import db
from breeding_ai import OrchidBreedingAI

# Initialize OpenAI client
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Create blueprint for the widget
ai_breeder_pro = Blueprint('ai_breeder_pro', __name__, url_prefix='/widgets/ai-breeder-pro')

class UnifiedBreederAssistant:
    """
    Unified AI Breeder Assistant Pro - Research-grade breeding analysis
    Based on Jeff Parham's Sarcochilus F226 trait inheritance methodology
    """
    
    def __init__(self):
        self.breeding_ai = OrchidBreedingAI()
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
        """Load Scott Barrita Sarcochilus breeding collection"""
        # This would load from sarcochilus_data_inserter.py data
        return [
            {
                "cross": "fitzhart × olivaceus",
                "expected_traits": "compact spike, full flowers, white with red spotting",
                "breeding_goal": "compact and free-flowering plants"
            },
            {
                "cross": "hartmanii × cecilliae 'Limelight'",
                "expected_traits": "large green flowers on compact spikes", 
                "breeding_goal": "yellow/green breeding line"
            },
            {
                "cross": "Sweetheart 'Speckles' × Kulnura Peach",
                "expected_traits": "excellent form with patterns and peach colors",
                "breeding_goal": "patterned flowers with color enhancement"
            }
        ]
    
    def analyze_proposed_cross(self, parent1_data: Dict, parent2_data: Dict, breeding_goals: List[str]) -> Dict[str, Any]:
        """
        Comprehensive breeding analysis using F226 methodology
        """
        # Use existing AI breeding system
        ai_analysis = self.breeding_ai.analyze_breeding_cross(parent1_data, parent2_data, breeding_goals)
        
        # Enhance with F226-style trait inheritance prediction
        trait_inheritance = self._predict_trait_inheritance_f226_style(parent1_data, parent2_data)
        
        # Generate research-grade recommendations
        research_recommendations = self._generate_research_recommendations(parent1_data, parent2_data, ai_analysis)
        
        return {
            "cross_analysis": {
                "proposed_cross": f"{parent1_data.get('display_name', 'Parent 1')} × {parent2_data.get('display_name', 'Parent 2')}",
                "success_probability": ai_analysis.get('success_probability', 0),
                "genetic_compatibility": ai_analysis.get('genetic_compatibility', {}),
                "breeding_difficulty": ai_analysis.get('breeding_difficulty', 'Unknown')
            },
            "trait_predictions": trait_inheritance,
            "f226_methodology": {
                "approach": "AI-assisted trait inheritance analysis with real-world validation",
                "based_on": "Jeff Parham's Sarcochilus F226 research methodology",
                "validation": "Proven successful in 'Multi Spot' × 'Shapely' cross"
            },
            "research_recommendations": research_recommendations,
            "case_study_reference": self.f226_case_study,
            "related_crosses": self._find_similar_crosses(parent1_data, parent2_data)
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
        
        # Check against Sarcochilus breeding data
        for cross_data in self.sarcochilus_data:
            if (parent1.get('genus') == 'Sarcochilus' or parent2.get('genus') == 'Sarcochilus'):
                similar.append({
                    "cross": cross_data['cross'],
                    "expected_traits": cross_data['expected_traits'],
                    "relevance": "Same genus breeding experience"
                })
        
        # Add F226 reference if Sarcochilus cross
        if parent1.get('genus') == 'Sarcochilus' and parent2.get('genus') == 'Sarcochilus':
            similar.append({
                "cross": "Kulnura Roundup 'Multi Spot' × Kulnura Secure 'Shapely'",
                "result": "F226 - Successful hybrid with predictable trait inheritance",
                "relevance": "Proven methodology reference"
            })
        
        return similar[:5]  # Limit to 5 most relevant

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
    """API endpoint for cross analysis"""
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
            'region': getattr(parent1, 'region', '')
        }
        
        parent2_data = {
            'display_name': parent2.display_name,
            'genus': parent2.genus,
            'species': parent2.species,
            'flower_color': getattr(parent2, 'flower_color', ''),
            'growth_habit': getattr(parent2, 'growth_habit', ''),
            'region': getattr(parent2, 'region', '')
        }
        
        # Perform analysis
        analysis = unified_breeder.analyze_proposed_cross(parent1_data, parent2_data, breeding_goals)
        
        return jsonify(analysis)
        
    except Exception as e:
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

# Export for registration
def register_ai_breeder_pro(app):
    """Register the AI Breeder Assistant Pro widget"""
    app.register_blueprint(ai_breeder_pro)
    current_app.logger.info("🧬 AI Breeder Assistant Pro widget registered successfully")