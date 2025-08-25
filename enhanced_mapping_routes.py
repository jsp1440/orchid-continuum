#!/usr/bin/env python3
"""
Enhanced Mapping Routes
======================
Flask routes for advanced species density and habitat correlation analysis
Part of The Orchid Continuum - Five Cities Orchid Society
"""

from flask import Blueprint, render_template, jsonify, request, Response
from simplified_analytics import simplified_analytics
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
enhanced_mapping_bp = Blueprint('enhanced_mapping', __name__, url_prefix='/enhanced-mapping')

@enhanced_mapping_bp.route('/')
def enhanced_mapping_home():
    """Enhanced mapping analytics home page"""
    return render_template('enhanced_mapping.html')

@enhanced_mapping_bp.route('/biodiversity-hotspots')
def biodiversity_hotspots():
    """Interactive biodiversity hotspot analysis"""
    try:
        analytics = EnhancedMappingAnalytics()
        hotspots = analytics.identify_biodiversity_hotspots()
        
        return render_template('biodiversity_hotspots.html', hotspots=hotspots)
        
    except Exception as e:
        logger.error(f"❌ Error loading biodiversity hotspots: {e}")
        return render_template('error.html', 
                             error="Failed to load biodiversity hotspots",
                             details=str(e)), 500

@enhanced_mapping_bp.route('/species-density')
def species_density():
    """Advanced species density heat map"""
    try:
        genus_filter = request.args.get('genus')
        
        analytics = EnhancedMappingAnalytics()
        density_map = analytics.create_species_density_heatmap(genus_filter=genus_filter)
        
        return render_template('species_density.html',
                             map_html=density_map._repr_html_(),
                             genus_filter=genus_filter)
        
    except Exception as e:
        logger.error(f"❌ Error creating species density map: {e}")
        return render_template('error.html', 
                             error="Failed to load species density map",
                             details=str(e)), 500

@enhanced_mapping_bp.route('/habitat-correlations')
def habitat_correlations():
    """Habitat correlation analysis dashboard"""
    try:
        analytics = EnhancedMappingAnalytics()
        habitat_data = analytics.analyze_habitat_correlations()
        
        return render_template('habitat_correlations.html',
                             habitat_data=habitat_data)
        
    except Exception as e:
        logger.error(f"❌ Error loading habitat correlations: {e}")
        return render_template('error.html', 
                             error="Failed to load habitat correlation analysis",
                             details=str(e)), 500

@enhanced_mapping_bp.route('/diversity-metrics')
def diversity_metrics():
    """Regional diversity metrics dashboard"""
    try:
        analytics = EnhancedMappingAnalytics()
        diversity_data = analytics.calculate_diversity_metrics()
        
        return render_template('diversity_metrics.html',
                             diversity_data=diversity_data)
        
    except Exception as e:
        logger.error(f"❌ Error loading diversity metrics: {e}")
        return render_template('error.html', 
                             error="Failed to load diversity metrics",
                             details=str(e)), 500

@enhanced_mapping_bp.route('/api/hotspots')
def api_hotspots():
    """API endpoint for biodiversity hotspot data"""
    try:
        min_species = request.args.get('min_species', 10, type=int)
        
        analytics = EnhancedMappingAnalytics()
        hotspots = analytics.identify_biodiversity_hotspots(min_species=min_species)
        
        return jsonify({
            'success': True,
            'hotspots': hotspots,
            'total_hotspots': len(hotspots),
            'min_species_threshold': min_species
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting biodiversity hotspots: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_mapping_bp.route('/api/habitat-analysis')
def api_habitat_analysis():
    """API endpoint for habitat correlation analysis"""
    try:
        analytics = EnhancedMappingAnalytics()
        habitat_data = analytics.analyze_habitat_correlations()
        
        return jsonify({
            'success': True,
            'habitat_analysis': habitat_data
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting habitat analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_mapping_bp.route('/api/diversity-metrics')
def api_diversity_metrics():
    """API endpoint for regional diversity metrics"""
    try:
        analytics = EnhancedMappingAnalytics()
        diversity_data = analytics.calculate_diversity_metrics()
        
        return jsonify({
            'success': True,
            'diversity_metrics': diversity_data
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting diversity metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_mapping_bp.route('/api/comprehensive-analysis')
def api_comprehensive_analysis():
    """API endpoint for complete enhanced mapping analysis"""
    try:
        comprehensive_data = get_enhanced_mapping_data()
        
        return jsonify({
            'success': True,
            'comprehensive_analysis': comprehensive_data,
            'analysis_components': [
                'biodiversity_hotspots',
                'habitat_correlations', 
                'diversity_metrics'
            ]
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting comprehensive analysis: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_mapping_bp.route('/api/species-density-data')
def api_species_density_data():
    """API endpoint for species density data"""
    try:
        genus_filter = request.args.get('genus')
        grid_size = request.args.get('grid_size', 0.5, type=float)
        
        # This would return structured density data for visualization
        # Implementation would be similar to the heat map creation but return data instead of map
        
        return jsonify({
            'success': True,
            'message': 'Species density data endpoint',
            'genus_filter': genus_filter,
            'grid_size': grid_size,
            'note': 'Full implementation would return density grid data'
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting species density data: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_mapping_bp.route('/conservation-priorities')
def conservation_priorities():
    """Conservation priority analysis based on biodiversity data"""
    try:
        analytics = EnhancedMappingAnalytics()
        
        # Get biodiversity hotspots for conservation priority
        hotspots = analytics.identify_biodiversity_hotspots(min_species=5)
        
        # Calculate conservation priority scores
        for hotspot in hotspots:
            # Simple priority score based on species count and rarity
            priority_score = (
                hotspot['unique_species'] * 2 +
                hotspot['diversity_index'] * 10 +
                (1 / (hotspot['area_km2'] + 1)) * 100  # Smaller areas get higher priority
            )
            hotspot['conservation_priority_score'] = round(priority_score, 2)
        
        # Sort by priority score
        hotspots.sort(key=lambda x: x['conservation_priority_score'], reverse=True)
        
        return render_template('conservation_priorities.html',
                             priority_areas=hotspots)
        
    except Exception as e:
        logger.error(f"❌ Error loading conservation priorities: {e}")
        return render_template('error.html', 
                             error="Failed to load conservation priority analysis",
                             details=str(e)), 500

@enhanced_mapping_bp.route('/dashboard')
def enhanced_dashboard():
    """Comprehensive enhanced mapping dashboard"""
    try:
        # Get simplified analytics data
        comprehensive_data = simplified_analytics.get_comprehensive_stats()
        summary_stats = comprehensive_data['summary_stats']
        
        return render_template('enhanced_mapping_dashboard.html',
                             summary_stats=summary_stats,
                             comprehensive_data=comprehensive_data)
        
    except Exception as e:
        logger.error(f"❌ Error loading enhanced mapping dashboard: {e}")
        return render_template('enhanced_mapping_dashboard.html',
                             summary_stats={'total_hotspots': 0, 'habitat_types': 0, 'regions_analyzed': 0, 'most_diverse_habitat': 'Loading'},
                             comprehensive_data={})

# Register the blueprint routes
logger.info("🔬 Enhanced Mapping routes registered successfully")