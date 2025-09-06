"""
Breeding Assistant API Routes
Created by Jeffery S. Parham - The Orchid Continuum
"""

from flask import render_template, request, jsonify
from sqlalchemy import and_, or_
from app import app, db
from models import OrchidRecord
from breeding_ai import breeding_ai
import logging

logger = logging.getLogger(__name__)

# ===================================================================
# BREEDING ASSISTANCE ROUTES
# ===================================================================

@app.route('/breeding-assistant')
def breeding_assistant():
    """Main breeding assistant interface"""
    return render_template('breeding_assistance.html')

@app.route('/breeder-assist-prototype')
def breeder_assist_prototype():
    """Comprehensive single-file breeder assist prototype"""
    from flask import send_from_directory
    return send_from_directory('static', 'orchid_continuum_breeder_assist.html')

@app.route('/api/breeding-parents')
def api_breeding_parents():
    """Get list of potential breeding parents"""
    try:
        # Get suitable breeding parents from database with high-quality data
        parents = db.session.query(OrchidRecord).filter(
            and_(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None),
                OrchidRecord.display_name.isnot(None),
                OrchidRecord.validation_status == 'approved',
                or_(
                    OrchidRecord.parentage_formula.isnot(None),
                    OrchidRecord.is_species == True
                )
            )
        ).limit(100).all()
        
        parent_data = []
        for parent in parents:
            parent_data.append({
                'id': parent.id,
                'display_name': parent.display_name,
                'genus': parent.genus,
                'species': parent.species,
                'region': parent.region,
                'climate_preference': parent.climate_preference,
                'growth_habit': parent.growth_habit,
                'parentage_formula': parent.parentage_formula
            })
        
        return jsonify(parent_data)
        
    except Exception as e:
        logger.error(f"Error fetching breeding parents: {e}")
        # Return sample data for demonstration
        return jsonify(breeding_ai.get_breeding_parents())

@app.route('/api/analyze-breeding-cross', methods=['POST'])
def api_analyze_breeding_cross():
    """Analyze a proposed breeding cross using AI"""
    try:
        data = request.get_json()
        parent1_id = data.get('parent1_id')
        parent2_id = data.get('parent2_id')
        desired_traits = data.get('desired_traits', [])
        
        # Get parent data from database
        parent1 = db.session.get(OrchidRecord, parent1_id)
        parent2 = db.session.get(OrchidRecord, parent2_id)
        
        if not parent1 or not parent2:
            return jsonify({'error': 'Invalid parent selection'}), 400
        
        # Convert to dictionary format for AI analysis
        parent1_data = {
            'id': parent1.id,
            'display_name': parent1.display_name,
            'genus': parent1.genus,
            'species': parent1.species,
            'region': parent1.region or 'Unknown',
            'climate_preference': parent1.climate_preference or 'Unknown',
            'growth_habit': parent1.growth_habit or 'Unknown'
        }
        
        parent2_data = {
            'id': parent2.id,
            'display_name': parent2.display_name,
            'genus': parent2.genus,
            'species': parent2.species,
            'region': parent2.region or 'Unknown',
            'climate_preference': parent2.climate_preference or 'Unknown',
            'growth_habit': parent2.growth_habit or 'Unknown'
        }
        
        # Perform AI analysis
        analysis_result = breeding_ai.analyze_breeding_cross(parent1_data, parent2_data, desired_traits)
        
        return jsonify(analysis_result)
        
    except Exception as e:
        logger.error(f"Error analyzing breeding cross: {e}")
        return jsonify({'error': 'Analysis failed', 'message': str(e)}), 500

@app.route('/api/breeding-compatibility-matrix')
def api_breeding_compatibility_matrix():
    """Get breeding compatibility matrix data"""
    try:
        matrix_data = breeding_ai.get_breeding_compatibility_matrix()
        return jsonify(matrix_data)
        
    except Exception as e:
        logger.error(f"Error getting compatibility matrix: {e}")
        return jsonify({'error': 'Failed to load compatibility matrix'}), 500

@app.route('/api/breeding-recommendations/<int:orchid_id>')
def api_breeding_recommendations(orchid_id):
    """Get breeding recommendations for a specific orchid"""
    try:
        orchid = db.session.get(OrchidRecord, orchid_id)
        if not orchid:
            return jsonify({'error': 'Orchid not found'}), 404
        
        # Find compatible breeding partners
        compatible_partners = db.session.query(OrchidRecord).filter(
            and_(
                OrchidRecord.id != orchid_id,
                OrchidRecord.genus == orchid.genus,  # Start with same genus
                OrchidRecord.validation_status == 'approved'
            )
        ).limit(10).all()
        
        recommendations = []
        for partner in compatible_partners:
            partner_data = {
                'id': partner.id,
                'display_name': partner.display_name,
                'genus': partner.genus,
                'compatibility_score': 85,  # Would calculate based on AI analysis
                'expected_traits': ['Enhanced vigor', 'Improved flowering'],
                'success_probability': 78
            }
            recommendations.append(partner_data)
        
        return jsonify(recommendations)
        
    except Exception as e:
        logger.error(f"Error getting breeding recommendations: {e}")
        return jsonify({'error': 'Failed to generate recommendations'}), 500

@app.route('/api/inheritance-analysis/<trait>')
def api_inheritance_analysis(trait):
    """Get inheritance pattern analysis for a specific trait"""
    try:
        # Sample inheritance data - would be replaced with real genetic analysis
        inheritance_data = {
            'trait': trait,
            'inheritance_pattern': 'Polygenic',
            'heritability': 0.75,
            'environmental_influence': 0.25,
            'dominant_alleles': ['A', 'B'],
            'recessive_alleles': ['a', 'b'],
            'expected_ratios': {
                'AA': 25,
                'Aa': 50,
                'aa': 25
            },
            'breeding_recommendations': [
                f'For enhanced {trait}, select parents with complementary genetic backgrounds',
                'Consider environmental factors during seed development',
                'Multiple generations may be needed for trait fixation'
            ]
        }
        
        return jsonify(inheritance_data)
        
    except Exception as e:
        logger.error(f"Error analyzing inheritance for {trait}: {e}")
        return jsonify({'error': 'Analysis failed'}), 500

@app.route('/api/breeding-statistics')
def api_breeding_statistics():
    """Get overall breeding program statistics"""
    try:
        # Get statistics from database
        total_crosses = db.session.query(OrchidRecord).filter(
            OrchidRecord.parentage_formula.isnot(None)
        ).count()
        
        genera_count = db.session.query(OrchidRecord.genus).distinct().count()
        
        successful_crosses = db.session.query(OrchidRecord).filter(
            and_(
                OrchidRecord.parentage_formula.isnot(None),
                OrchidRecord.validation_status == 'approved'
            )
        ).count()
        
        stats = {
            'total_crosses': total_crosses,
            'genera_represented': genera_count,
            'successful_crosses': successful_crosses,
            'success_rate': round((successful_crosses / max(total_crosses, 1)) * 100, 1),
            'average_flowering_time': '3.2 years',
            'most_successful_genus': 'Phalaenopsis',
            'recent_trends': [
                'Increased interest in intergeneric crosses',
                'Focus on climate-adaptive traits',
                'Conservation breeding programs growing'
            ]
        }
        
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting breeding statistics: {e}")
        return jsonify({'error': 'Failed to load statistics'}), 500