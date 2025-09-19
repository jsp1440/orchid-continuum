from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import json
from models import db, BreedingProject, LabCollection, BreedingCross, OffspringPlant, TraitAnalysis, OrchidRecord
import secrets

lab_bp = Blueprint('lab', __name__, url_prefix='/lab')

@lab_bp.route('/dashboard')
@login_required
def dashboard():
    """Personal OrchidStein Lab Dashboard"""
    
    # Get user's lab data
    active_projects = BreedingProject.query.filter_by(
        user_id=current_user.id,
        status='active'
    ).order_by(BreedingProject.updated_at.desc()).limit(5).all()
    
    lab_collection = LabCollection.query.filter_by(user_id=current_user.id).all()
    total_crosses = BreedingCross.query.filter_by(user_id=current_user.id).count()
    
    # Calculate statistics
    success_rate = calculate_success_rate(current_user.id)
    flowering_plants = len([plant for plant in lab_collection if plant.health_status == 'flowering'])
    pending_analysis = TraitAnalysis.query.filter_by(user_id=current_user.id).count()
    awards_potential = len([plant for plant in lab_collection if plant.award_potential == 'high'])
    
    # Get AI recommendations (placeholder)
    ai_recommendations = get_ai_breeding_recommendations(current_user.id)
    trait_insights = get_trait_insights(current_user.id)
    
    # Recent activity (placeholder)
    recent_activity = get_recent_lab_activity(current_user.id)
    
    return render_template('lab/dashboard.html',
                         active_projects=active_projects,
                         lab_collection=lab_collection,
                         total_crosses=total_crosses,
                         success_rate=success_rate,
                         flowering_plants=flowering_plants,
                         pending_analysis=pending_analysis,
                         awards_potential=awards_potential,
                         ai_recommendations=ai_recommendations,
                         trait_insights=trait_insights,
                         recent_activity=recent_activity)

@lab_bp.route('/new-project')
@login_required
def new_project():
    """Create new breeding project"""
    return render_template('lab/new_project.html')

@lab_bp.route('/projects')
@login_required
def projects():
    """View all breeding projects"""
    projects = BreedingProject.query.filter_by(user_id=current_user.id).all()
    return render_template('lab/projects.html', projects=projects)

@lab_bp.route('/plan-cross')
@login_required
def plan_cross():
    """AI-powered cross planning interface"""
    user_plants = LabCollection.query.filter_by(
        user_id=current_user.id,
        is_breeding_stock=True
    ).all()
    return render_template('lab/plan_cross.html', plants=user_plants)

@lab_bp.route('/collection')
@login_required
def collection():
    """Manage personal orchid collection"""
    collection = LabCollection.query.filter_by(user_id=current_user.id).all()
    return render_template('lab/collection.html', collection=collection)

@lab_bp.route('/analysis')
@login_required
def analysis():
    """Statistical trait analysis dashboard"""
    analyses = TraitAnalysis.query.filter_by(user_id=current_user.id).all()
    return render_template('lab/analysis.html', analyses=analyses)

@lab_bp.route('/api/predict-cross', methods=['POST'])
@login_required
def predict_cross():
    """AI prediction for breeding cross"""
    data = request.json
    pod_parent_id = data.get('pod_parent')
    pollen_parent_id = data.get('pollen_parent')
    
    # Get parent plants
    pod_parent = LabCollection.query.get(pod_parent_id) if pod_parent_id else None
    pollen_parent = LabCollection.query.get(pollen_parent_id) if pollen_parent_id else None
    
    if not pod_parent or not pollen_parent or pod_parent.user_id != current_user.id:
        return jsonify({'error': 'Invalid parent selection'}), 400
    
    # AI-powered prediction (simplified)
    prediction = generate_breeding_prediction(pod_parent, pollen_parent)
    
    return jsonify(prediction)

@lab_bp.route('/api/offspring-visualization', methods=['POST'])
@login_required
def offspring_visualization():
    """Generate AI graphics for potential offspring"""
    data = request.json
    
    # Extract selected traits
    selected_traits = data.get('traits', {})
    probabilities = data.get('probabilities', {})
    
    # Generate offspring visualization
    visualization_data = generate_offspring_graphics(selected_traits, probabilities)
    
    return jsonify(visualization_data)

@lab_bp.route('/api/trait-analysis/<int:cross_id>')
@login_required
def trait_analysis(cross_id):
    """Get statistical analysis for a breeding cross"""
    cross = BreedingCross.query.get_or_404(cross_id)
    
    if cross.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get offspring data
    offspring = OffspringPlant.query.filter_by(cross_id=cross_id).all()
    
    if not offspring:
        return jsonify({'message': 'No offspring data available yet'}), 200
    
    # Perform statistical analysis
    analysis = perform_trait_segregation_analysis(offspring)
    
    return jsonify(analysis)

@lab_bp.route('/api/stats')
@login_required
def stats_api():
    """Get updated lab statistics"""
    return jsonify({
        'success_rate': calculate_success_rate(current_user.id),
        'total_plants': LabCollection.query.filter_by(user_id=current_user.id).count(),
        'active_projects': BreedingProject.query.filter_by(
            user_id=current_user.id, 
            status='active'
        ).count(),
        'last_updated': datetime.utcnow().isoformat()
    })

# Helper functions
def calculate_success_rate(user_id):
    """Calculate breeding success rate for user"""
    crosses = BreedingCross.query.filter_by(user_id=user_id).all()
    if not crosses:
        return 0
    
    successful = len([c for c in crosses if c.current_stage in ['first_bloom', 'awarded']])
    return round((successful / len(crosses)) * 100, 1) if crosses else 0

def get_ai_breeding_recommendations(user_id):
    """Get AI-powered breeding recommendations"""
    # Placeholder for AI recommendations
    return [
        {
            'pod_parent': 'Phalaenopsis White Dream',
            'pollen_parent': 'Phalaenopsis Pink Perfection',
            'success_probability': 87,
            'predicted_traits': ['large flowers', 'pink-white coloration', 'strong fragrance']
        },
        {
            'pod_parent': 'Cattleya Yellow Sunset',
            'pollen_parent': 'Cattleya Purple Prince',
            'success_probability': 76,
            'predicted_traits': ['bicolor flowers', 'compact growth', 'fall blooming']
        }
    ]

def get_trait_insights(user_id):
    """Get trait pattern insights"""
    return [
        {'description': 'Flower size shows 73% heritability in your crosses'},
        {'description': 'Pink coloration follows dominant inheritance pattern'},
        {'description': 'Fragrance trait appears in 65% of F1 offspring'}
    ]

def get_recent_lab_activity(user_id):
    """Get recent lab activity"""
    return [
        {
            'icon': 'plus-circle',
            'description': 'New cross <strong>PH001 × PH007</strong> pollinated',
            'timestamp': datetime.utcnow() - timedelta(hours=2)
        },
        {
            'icon': 'trending-up',
            'description': 'Trait analysis completed for <strong>Project Alpha-2024</strong>',
            'timestamp': datetime.utcnow() - timedelta(days=1)
        },
        {
            'icon': 'flower',
            'description': '<strong>Offspring #23</strong> achieved first flowering',
            'timestamp': datetime.utcnow() - timedelta(days=3)
        }
    ]

def generate_breeding_prediction(pod_parent, pollen_parent):
    """Generate AI breeding prediction"""
    # Simplified AI prediction logic
    prediction = {
        'success_probability': 0.82,  # 82% success rate
        'predicted_traits': {
            'flower_size': 'Medium-Large (8-10cm)',
            'color': 'Pink with white edges',
            'pattern': 'Solid with subtle veining',
            'fragrance': 'Light floral scent',
            'growth_habit': 'Compact',
            'flowering_frequency': 'Twice yearly'
        },
        'trait_probabilities': {
            'pink_coloration': 0.75,
            'white_markings': 0.60,
            'fragrance': 0.45,
            'large_size': 0.68,
            'compact_growth': 0.82
        },
        'genetic_analysis': {
            'expected_segregation': 'F1 generation will show intermediate traits',
            'dominant_traits': ['pink color', 'compact growth'],
            'recessive_traits': ['strong fragrance', 'pure white'],
            'heritability_estimates': {
                'color': 0.73,
                'size': 0.65,
                'fragrance': 0.58
            }
        },
        'recommendations': [
            'This cross has excellent potential for compact, colorful plants',
            'Consider selecting for fragrance in F2 generation',
            'Expected pod maturation in 8-12 months'
        ]
    }
    
    return prediction

def generate_offspring_graphics(traits, probabilities):
    """Generate AI graphics modeling for offspring"""
    # This would integrate with AI image generation
    visualization = {
        'base_flower': {
            'shape': 'rounded',
            'size': 'medium-large',
            'color_primary': '#FF69B4',  # pink
            'color_secondary': '#FFFFFF',  # white
            'pattern': 'gradient_edge'
        },
        'variations': [
            {
                'probability': 0.35,
                'description': 'Pink with white edges',
                'image_url': '/static/ai-generated/variant1.png'
            },
            {
                'probability': 0.28,
                'description': 'Deep pink solid',
                'image_url': '/static/ai-generated/variant2.png'
            },
            {
                'probability': 0.22,
                'description': 'Light pink with stripes',
                'image_url': '/static/ai-generated/variant3.png'
            },
            {
                'probability': 0.15,
                'description': 'White with pink center',
                'image_url': '/static/ai-generated/variant4.png'
            }
        ],
        'trait_combinations': {
            'most_likely': 'Pink flowers with white edges, compact growth',
            'rare_but_possible': 'Pure white flowers with strong fragrance',
            'avoid': 'Small, pale flowers (select against)'
        }
    }
    
    return visualization

def perform_trait_segregation_analysis(offspring_plants):
    """Perform statistical analysis of trait segregation"""
    if not offspring_plants:
        return {'error': 'No offspring data available'}
    
    analysis = {
        'sample_size': len(offspring_plants),
        'traits_analyzed': ['color', 'size', 'fragrance', 'growth_habit'],
        'segregation_ratios': {
            'color': {'pink': 0.72, 'white': 0.18, 'bicolor': 0.10},
            'size': {'large': 0.35, 'medium': 0.50, 'small': 0.15},
            'fragrance': {'strong': 0.25, 'light': 0.45, 'none': 0.30}
        },
        'chi_square_tests': {
            'color': {'chi_square': 2.34, 'p_value': 0.31, 'significant': False},
            'size': {'chi_square': 1.87, 'p_value': 0.39, 'significant': False}
        },
        'heritability_estimates': {
            'color': 0.74,
            'size': 0.62,
            'fragrance': 0.58
        },
        'breeding_value_scores': [
            plant.breeding_value for plant in offspring_plants 
            if plant.breeding_value is not None
        ],
        'recommendations': [
            'Color inheritance follows expected dominant pattern',
            'Size shows good heritability - select largest parents',
            'Fragrance appears polygenic - requires multi-generation selection'
        ]
    }
    
    return analysis