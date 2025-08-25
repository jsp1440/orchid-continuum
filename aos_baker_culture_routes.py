"""
Routes for AOS-Baker Culture Sheet Generation System
Integrated with location-based recommendations and expert comparison
"""

from flask import Blueprint, request, jsonify, render_template
from location_based_culture_system import LocationBasedCultureSystem, detect_user_location, get_available_orchid_species
import logging

logger = logging.getLogger(__name__)

# Create blueprint for culture sheet routes
culture_bp = Blueprint('culture_sheets', __name__, url_prefix='/culture')

@culture_bp.route('/species')
def available_species():
    """Get list of available orchid species for culture sheet generation"""
    try:
        species_list = get_available_orchid_species()
        return jsonify({
            'available_species': species_list[:50],  # Limit to first 50 for demo
            'total_count': len(species_list),
            'note': 'Species with Baker and/or AOS culture data available'
        })
    except Exception as e:
        logger.error(f"Error getting available species: {str(e)}")
        return jsonify({'error': str(e)}), 500

@culture_bp.route('/generate', methods=['POST'])
def generate_culture_sheet():
    """Generate location-specific culture sheet with expert comparison"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        orchid_species = data.get('species')
        user_location = data.get('location')
        
        if not orchid_species:
            return jsonify({'error': 'Orchid species required'}), 400
        
        if not user_location:
            # Use default location detection
            user_location = detect_user_location()
        
        # Generate the comprehensive culture sheet
        culture_system = LocationBasedCultureSystem()
        culture_sheet = culture_system.generate_location_culture_sheet(orchid_species, user_location)
        
        if 'error' in culture_sheet:
            return jsonify(culture_sheet), 400
        
        return jsonify({
            'success': True,
            'culture_sheet': culture_sheet,
            'generation_info': {
                'species': orchid_species,
                'location': user_location.get('city', 'Unknown'),
                'data_sources_used': culture_sheet.get('data_sources', []),
                'expert_comparison_performed': 'expert_comparison' in culture_sheet
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating culture sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@culture_bp.route('/demo')
def demo_culture_sheet():
    """Demo route showing culture sheet generation with expert comparison"""
    try:
        # Use Phalaenopsis as demo species (likely to have both Baker and AOS data)
        demo_species = "Phalaenopsis"
        demo_location = {
            'city': 'San Francisco, CA',
            'latitude': 37.7749,
            'longitude': -122.4194
        }
        
        culture_system = LocationBasedCultureSystem()
        culture_sheet = culture_system.generate_location_culture_sheet(demo_species, demo_location)
        
        return jsonify({
            'demo': True,
            'culture_sheet': culture_sheet,
            'note': 'Demonstration culture sheet showing Baker/AOS expert comparison system'
        })
        
    except Exception as e:
        logger.error(f"Error generating demo culture sheet: {str(e)}")
        return jsonify({'error': str(e)}), 500

@culture_bp.route('/compare/<species>')
def compare_expert_sources(species):
    """Compare Baker vs AOS recommendations for a specific species"""
    try:
        culture_system = LocationBasedCultureSystem()
        
        # Get both expert sources
        baker_data = culture_system._get_baker_culture_data(species)
        aos_data = culture_system._get_aos_culture_data(species)
        
        # Mock location for comparison
        mock_location = {'latitude': 37.7749, 'longitude': -122.4194}
        mock_adaptations = {'note': 'Location adaptations would appear here'}
        
        # Generate comparison
        comparison = culture_system._compare_expert_recommendations(baker_data, aos_data, mock_adaptations)
        
        return jsonify({
            'species': species,
            'baker_available': baker_data.get('available', False),
            'aos_available': aos_data.get('available', False),
            'expert_comparison': comparison,
            'sources': {
                'baker': baker_data,
                'aos': aos_data
            }
        })
        
    except Exception as e:
        logger.error(f"Error comparing expert sources: {str(e)}")
        return jsonify({'error': str(e)}), 500

@culture_bp.route('/location/detect', methods=['POST'])
def detect_location():
    """Detect or set user location for culture sheet generation"""
    try:
        data = request.get_json() if request.is_json else {}
        
        if data.get('latitude') and data.get('longitude'):
            # User provided specific location
            location = {
                'city': data.get('city', 'Custom Location'),
                'latitude': data.get('latitude'),
                'longitude': data.get('longitude'),
                'detected': False,
                'source': 'User Provided'
            }
        else:
            # Use detection system
            location = detect_user_location()
        
        return jsonify({
            'location': location,
            'climate_analysis': LocationBasedCultureSystem()._analyze_location_climate(location) if location.get('latitude') else None
        })
        
    except Exception as e:
        logger.error(f"Error detecting location: {str(e)}")
        return jsonify({'error': str(e)}), 500

def register_culture_routes(app):
    """Register culture sheet routes with the Flask app"""
    app.register_blueprint(culture_bp)
    logger.info("AOS-Baker Culture Sheet routes registered successfully")