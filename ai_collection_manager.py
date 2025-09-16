"""
AI Collection Manager - Holistic orchid collection tracking and analysis system
Provides intelligent collection management with trend analysis and proactive recommendations
"""

import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, session
from app import db
import json
from typing import Dict, List, Optional, Tuple
import statistics
from collections import defaultdict, Counter

logger = logging.getLogger(__name__)

# Create Blueprint
collection_manager_bp = Blueprint('collection_manager', __name__, url_prefix='/collection')

class OrchidCollection(db.Model):
    """User's orchid collection with environmental context"""
    __tablename__ = 'orchid_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(100), nullable=False)  # Session or user identifier
    collection_name = db.Column(db.String(200), default="My Orchid Collection")
    location = db.Column(db.String(200))  # Growing location
    climate_zone = db.Column(db.String(50))
    growing_environment = db.Column(db.String(100))  # greenhouse, windowsill, outdoor, etc.
    experience_level = db.Column(db.String(50))  # beginner, intermediate, advanced
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Environmental details (JSON)
    environment_details = db.Column(db.Text)  # humidity, temperature, lighting, etc.
    
    # Relationship to plants
    plants = db.relationship('CollectionPlant', backref='collection', lazy=True, cascade='all, delete-orphan')
    care_logs = db.relationship('CollectionCareLog', backref='collection', lazy=True, cascade='all, delete-orphan')

class CollectionPlant(db.Model):
    """Individual plant in a collection"""
    __tablename__ = 'collection_plants'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('orchid_collections.id'), nullable=False)
    
    # Plant identification
    plant_name = db.Column(db.String(200))  # User's name for the plant
    genus = db.Column(db.String(100))
    species = db.Column(db.String(100))
    hybrid = db.Column(db.String(200))
    
    # Plant details
    acquired_date = db.Column(db.Date)
    source = db.Column(db.String(200))  # Where acquired
    size_at_acquisition = db.Column(db.String(100))
    current_size = db.Column(db.String(100))
    
    # Location and grouping
    current_location = db.Column(db.String(200))  # Shelf, corner, etc.
    care_group = db.Column(db.String(100))  # AI-suggested grouping
    
    # Health tracking
    health_status = db.Column(db.String(50), default='healthy')  # healthy, stressed, recovering, etc.
    last_bloom = db.Column(db.Date)
    bloom_frequency = db.Column(db.String(100))
    
    # Care preferences (JSON)
    care_preferences = db.Column(db.Text)  # watering, fertilizing, etc.
    notes = db.Column(db.Text)
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to care logs
    care_logs = db.relationship('CollectionCareLog', backref='plant', lazy=True)

class CollectionCareLog(db.Model):
    """Care activity and observation logs"""
    __tablename__ = 'collection_care_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('orchid_collections.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('collection_plants.id'), nullable=True)  # Null for collection-wide activities
    
    # Activity details
    activity_type = db.Column(db.String(100), nullable=False)  # watering, fertilizing, repotting, observation
    activity_date = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Activity data (JSON)
    activity_details = db.Column(db.Text)  # fertilizer type, amount, observations, etc.
    
    # Observations
    plant_condition = db.Column(db.String(100))
    observations = db.Column(db.Text)
    photos = db.Column(db.Text)  # JSON array of photo URLs
    
    # Environmental conditions at time of activity
    temperature = db.Column(db.Float)
    humidity = db.Column(db.Float)
    light_level = db.Column(db.String(50))
    
    created_date = db.Column(db.DateTime, default=datetime.utcnow)

class CollectionRecommendation(db.Model):
    """AI-generated recommendations for collections"""
    __tablename__ = 'collection_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    collection_id = db.Column(db.Integer, db.ForeignKey('orchid_collections.id'), nullable=False)
    plant_id = db.Column(db.Integer, db.ForeignKey('collection_plants.id'), nullable=True)  # Null for collection-wide recommendations
    
    # Recommendation details
    recommendation_type = db.Column(db.String(100), nullable=False)  # care_grouping, seasonal_care, problem_prevention
    priority = db.Column(db.String(20), default='medium')  # low, medium, high, urgent
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    reasoning = db.Column(db.Text)  # AI's reasoning for the recommendation
    
    # Implementation details
    action_items = db.Column(db.Text)  # JSON array of specific actions
    estimated_benefit = db.Column(db.String(200))
    implementation_difficulty = db.Column(db.String(50))  # easy, moderate, challenging
    
    # Status tracking
    status = db.Column(db.String(50), default='active')  # active, implemented, dismissed, outdated
    created_date = db.Column(db.DateTime, default=datetime.utcnow)
    valid_until = db.Column(db.DateTime)  # When this recommendation expires
    
    # Feedback
    user_feedback = db.Column(db.String(20))  # helpful, not_helpful, implemented
    feedback_notes = db.Column(db.Text)

# Collection Management Routes
@collection_manager_bp.route('/')
def collection_dashboard():
    """AI Collection Management Dashboard"""
    user_id = session.get('user_id', 'demo_user')  # Use session or demo for development
    
    # Get or create user's collection
    collection = OrchidCollection.query.filter_by(user_id=user_id).first()
    if not collection:
        collection = OrchidCollection(
            user_id=user_id,
            collection_name="My AI-Tracked Collection",
            location="Not set",
            experience_level="beginner"
        )
        db.session.add(collection)
        db.session.commit()
    
    # Analyze collection
    analysis_result = collection_analyzer.analyze_collection(collection.id)
    
    if not analysis_result['success']:
        return render_template('collection/error.html', error=analysis_result['error'])
    
    # Get recommendations
    recommendations = CollectionRecommendation.query.filter_by(
        collection_id=collection.id,
        status='active'
    ).order_by(CollectionRecommendation.priority.desc()).all()
    
    return render_template('collection/ai_dashboard.html',
                         collection=collection,
                         analysis=analysis_result['analysis'],
                         recommendations=recommendations)

@collection_manager_bp.route('/api/load_demo', methods=['POST'])
def load_demo_data():
    """Load demonstration data for new collections"""
    user_id = session.get('user_id', 'demo_user')
    
    collection = OrchidCollection.query.filter_by(user_id=user_id).first()
    if not collection:
        return jsonify({'success': False, 'error': 'No collection found'})
    
    # Add sample plants
    demo_plants = [
        {
            'plant_name': 'Lady Slipper Beauty',
            'genus': 'Paphiopedilum',
            'species': 'callosum',
            'current_location': 'East Window',
            'health_status': 'healthy',
            'notes': 'Bloomed last spring, beautiful spotted petals'
        },
        {
            'plant_name': 'Moth Orchid Delight', 
            'genus': 'Phalaenopsis',
            'species': 'amabilis',
            'current_location': 'South Shelf',
            'health_status': 'healthy',
            'notes': 'Reliable bloomer, white flowers'
        },
        {
            'plant_name': 'Dancing Lady',
            'genus': 'Oncidium',
            'species': 'sphacelatum',
            'current_location': 'East Window',
            'health_status': 'stressed',
            'notes': 'Yellow leaves appearing, may need repotting'
        }
    ]
    
    for plant_data in demo_plants:
        existing = CollectionPlant.query.filter_by(
            collection_id=collection.id,
            plant_name=plant_data['plant_name']
        ).first()
        
        if not existing:
            plant = CollectionPlant(
                collection_id=collection.id,
                **plant_data
            )
            db.session.add(plant)
    
    # Add sample care logs
    demo_care_logs = [
        {
            'activity_type': 'watering',
            'observations': 'Plants looking healthy after last watering',
            'plant_condition': 'healthy'
        },
        {
            'activity_type': 'fertilizing',
            'observations': 'Applied diluted fertilizer to all plants',
            'plant_condition': 'healthy'
        }
    ]
    
    for log_data in demo_care_logs:
        care_log = CollectionCareLog(
            collection_id=collection.id,
            **log_data
        )
        db.session.add(care_log)
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Demo data loaded successfully'})

class AICollectionAnalyzer:
    """AI system for analyzing collections and generating insights"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def analyze_collection(self, collection_id: int) -> Dict:
        """Perform comprehensive collection analysis"""
        try:
            collection = OrchidCollection.query.get(collection_id)
            if not collection:
                return {'success': False, 'error': 'Collection not found'}
            
            analysis = {
                'collection_summary': self._get_collection_summary(collection),
                'health_trends': self._analyze_health_trends(collection),
                'care_patterns': self._analyze_care_patterns(collection),
                'grouping_suggestions': self._suggest_plant_groupings(collection),
                'seasonal_recommendations': self._generate_seasonal_recommendations(collection),
                'risk_assessments': self._assess_risks(collection),
                'optimization_opportunities': self._identify_optimizations(collection)
            }
            
            return {'success': True, 'analysis': analysis}
            
        except Exception as e:
            self.logger.error(f"Error analyzing collection {collection_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _get_collection_summary(self, collection: OrchidCollection) -> Dict:
        """Generate collection overview statistics"""
        plants = collection.plants
        total_plants = len(plants)
        
        if total_plants == 0:
            return {'total_plants': 0, 'message': 'No plants in collection yet'}
        
        # Basic statistics
        genus_counts = Counter([p.genus for p in plants if p.genus])
        health_distribution = Counter([p.health_status for p in plants])
        
        # Calculate collection metrics
        blooming_plants = len([p for p in plants if p.last_bloom and 
                              p.last_bloom > datetime.now().date() - timedelta(days=365)])
        
        recent_acquisitions = len([p for p in plants if p.acquired_date and 
                                  p.acquired_date > datetime.now().date() - timedelta(days=90)])
        
        return {
            'total_plants': total_plants,
            'genus_diversity': len(genus_counts),
            'most_common_genus': genus_counts.most_common(1)[0] if genus_counts else None,
            'health_distribution': dict(health_distribution),
            'blooming_rate': round((blooming_plants / total_plants) * 100, 1),
            'recent_acquisitions': recent_acquisitions,
            'collection_age_days': (datetime.now() - collection.created_date).days
        }
    
    def _analyze_health_trends(self, collection: OrchidCollection) -> Dict:
        """Analyze health patterns across the collection"""
        plants = collection.plants
        care_logs = CollectionCareLog.query.filter_by(collection_id=collection.id).all()
        
        # Group health issues by type and timing
        health_patterns = defaultdict(list)
        problem_clusters = defaultdict(int)
        
        for plant in plants:
            if plant.health_status != 'healthy':
                # Check for similar problems in care logs
                plant_logs = [log for log in care_logs if log.plant_id == plant.id]
                recent_issues = [log for log in plant_logs if 
                               log.activity_date > datetime.now() - timedelta(days=30) and
                               log.plant_condition and log.plant_condition != 'healthy']
                
                if recent_issues:
                    for issue in recent_issues:
                        health_patterns[plant.genus or 'Unknown'].append({
                            'plant_name': plant.plant_name,
                            'issue': issue.plant_condition,
                            'date': issue.activity_date.isoformat(),
                            'location': plant.current_location
                        })
                        problem_clusters[issue.plant_condition] += 1
        
        return {
            'patterns_by_genus': dict(health_patterns),
            'common_problems': dict(problem_clusters),
            'overall_health_score': self._calculate_health_score(plants),
            'trend_analysis': 'improving'  # This would be calculated from historical data
        }
    
    def _analyze_care_patterns(self, collection: OrchidCollection) -> Dict:
        """Analyze care frequency and effectiveness"""
        care_logs = CollectionCareLog.query.filter_by(collection_id=collection.id).all()
        
        # Group by activity type
        activity_frequency = defaultdict(list)
        care_effectiveness = {}
        
        for log in care_logs:
            activity_frequency[log.activity_type].append(log.activity_date)
        
        # Calculate average intervals between activities
        care_intervals = {}
        for activity_type, dates in activity_frequency.items():
            if len(dates) > 1:
                sorted_dates = sorted(dates)
                intervals = [(sorted_dates[i] - sorted_dates[i-1]).days 
                           for i in range(1, len(sorted_dates))]
                care_intervals[activity_type] = {
                    'avg_interval_days': round(statistics.mean(intervals), 1),
                    'consistency_score': round(1 / (statistics.stdev(intervals) / statistics.mean(intervals)), 2) if len(intervals) > 1 else 1.0,
                    'total_activities': len(dates)
                }
        
        return {
            'care_intervals': care_intervals,
            'most_frequent_activity': max(activity_frequency.keys(), key=lambda k: len(activity_frequency[k])) if activity_frequency else None,
            'care_consistency_score': self._calculate_care_consistency(care_intervals),
            'suggestions': self._generate_care_suggestions(care_intervals)
        }
    
    def _suggest_plant_groupings(self, collection: OrchidCollection) -> List[Dict]:
        """Suggest optimal plant groupings based on care needs and characteristics"""
        plants = collection.plants
        
        # Group by similar care requirements
        groupings = []
        
        # Group by genus (similar care needs)
        genus_groups = defaultdict(list)
        for plant in plants:
            genus_groups[plant.genus or 'Unknown'].append(plant)
        
        for genus, genus_plants in genus_groups.items():
            if len(genus_plants) > 1:
                groupings.append({
                    'group_type': 'genus_based',
                    'group_name': f"{genus} Care Group",
                    'plants': [{'id': p.id, 'name': p.plant_name, 'genus': p.genus} for p in genus_plants],
                    'reasoning': f"Plants of the same genus ({genus}) typically have similar care requirements",
                    'care_benefits': [
                        "Synchronized watering schedule",
                        "Similar fertilizer requirements",
                        "Consistent environmental needs"
                    ]
                })
        
        # Group by location (environmental optimization)
        location_groups = defaultdict(list)
        for plant in plants:
            if plant.current_location:
                location_groups[plant.current_location].append(plant)
        
        for location, location_plants in location_groups.items():
            if len(location_plants) > 2:
                groupings.append({
                    'group_type': 'location_based',
                    'group_name': f"{location} Environment Group",
                    'plants': [{'id': p.id, 'name': p.plant_name, 'location': p.current_location} for p in location_plants],
                    'reasoning': f"Plants in the same location ({location}) share environmental conditions",
                    'care_benefits': [
                        "Efficient care routing",
                        "Consistent environmental monitoring",
                        "Easier pest/disease management"
                    ]
                })
        
        return groupings
    
    def _generate_seasonal_recommendations(self, collection: OrchidCollection) -> Dict:
        """Generate season-specific recommendations"""
        current_month = datetime.now().month
        
        # Seasonal care recommendations (simplified - would be more sophisticated in practice)
        seasonal_advice = {
            'winter': {
                'watering': 'Reduce watering frequency as growth slows',
                'fertilizing': 'Use diluted fertilizer monthly or pause feeding',
                'humidity': 'Increase humidity due to indoor heating',
                'temperature': 'Watch for cold drafts and temperature drops'
            },
            'spring': {
                'watering': 'Resume regular watering as growth increases',
                'fertilizing': 'Begin regular feeding schedule',
                'humidity': 'Maintain consistent humidity levels',
                'repotting': 'Ideal time for repotting if needed'
            },
            'summer': {
                'watering': 'Increase watering frequency in hot weather',
                'fertilizing': 'Peak growing season - regular feeding',
                'ventilation': 'Ensure good air circulation',
                'shading': 'Provide extra shade during peak heat'
            },
            'fall': {
                'watering': 'Begin reducing watering frequency',
                'fertilizing': 'Reduce fertilizer to prepare for dormancy',
                'temperature': 'Monitor for cooler nighttime temperatures',
                'preparation': 'Prepare for winter growing conditions'
            }
        }
        
        # Determine current season
        if current_month in [12, 1, 2]:
            season = 'winter'
        elif current_month in [3, 4, 5]:
            season = 'spring'
        elif current_month in [6, 7, 8]:
            season = 'summer'
        else:
            season = 'fall'
        
        return {
            'current_season': season,
            'recommendations': seasonal_advice[season],
            'next_season_prep': f"Start preparing for {season} care adjustments"
        }
    
    def _assess_risks(self, collection: OrchidCollection) -> List[Dict]:
        """Identify potential risks in the collection"""
        risks = []
        plants = collection.plants
        
        # Check for overcrowding in locations
        location_counts = Counter([p.current_location for p in plants if p.current_location])
        for location, count in location_counts.items():
            if count > 10:  # Arbitrary threshold
                risks.append({
                    'risk_type': 'overcrowding',
                    'severity': 'medium',
                    'location': location,
                    'description': f"Too many plants ({count}) in {location} may reduce air circulation",
                    'recommendation': "Consider spreading plants or improving ventilation"
                })
        
        # Check for plants without recent care
        thirty_days_ago = datetime.now() - timedelta(days=30)
        care_logs = CollectionCareLog.query.filter_by(collection_id=collection.id).filter(
            CollectionCareLog.activity_date > thirty_days_ago
        ).all()
        
        plants_with_recent_care = {log.plant_id for log in care_logs if log.plant_id}
        neglected_plants = [p for p in plants if p.id not in plants_with_recent_care]
        
        if neglected_plants:
            risks.append({
                'risk_type': 'neglect',
                'severity': 'high' if len(neglected_plants) > 5 else 'medium',
                'description': f"{len(neglected_plants)} plants haven't received care in 30+ days",
                'plants': [p.plant_name for p in neglected_plants[:5]],  # Show first 5
                'recommendation': "Review and update care schedules for these plants"
            })
        
        return risks
    
    def _identify_optimizations(self, collection: OrchidCollection) -> List[Dict]:
        """Identify opportunities to optimize collection management"""
        optimizations = []
        plants = collection.plants
        
        # Suggest care schedule optimization
        if len(plants) > 5:
            optimizations.append({
                'optimization_type': 'care_scheduling',
                'title': 'Optimize Care Schedules',
                'description': 'Group plants with similar care needs to create efficient care routines',
                'potential_benefit': 'Save 20-30% time on collection maintenance',
                'implementation': 'Use suggested plant groupings and create batch care schedules'
            })
        
        # Environmental monitoring suggestion
        if collection.environment_details is None:
            optimizations.append({
                'optimization_type': 'environmental_monitoring',
                'title': 'Add Environmental Monitoring',
                'description': 'Track temperature, humidity, and light levels for better care decisions',
                'potential_benefit': 'Improved plant health and reduced problems',
                'implementation': 'Add basic monitoring tools and log environmental conditions'
            })
        
        return optimizations
    
    def _calculate_health_score(self, plants: List[CollectionPlant]) -> float:
        """Calculate overall collection health score (0-100)"""
        if not plants:
            return 0.0
        
        healthy_count = len([p for p in plants if p.health_status == 'healthy'])
        return round((healthy_count / len(plants)) * 100, 1)
    
    def _calculate_care_consistency(self, care_intervals: Dict) -> float:
        """Calculate care consistency score (0-10)"""
        if not care_intervals:
            return 0.0
        
        consistency_scores = [data['consistency_score'] for data in care_intervals.values()]
        return round(statistics.mean(consistency_scores), 1) if consistency_scores else 0.0
    
    def _generate_care_suggestions(self, care_intervals: Dict) -> List[str]:
        """Generate care improvement suggestions"""
        suggestions = []
        
        for activity_type, data in care_intervals.items():
            if data['consistency_score'] < 1.5:
                suggestions.append(f"Create a more consistent {activity_type} schedule")
            
            if activity_type == 'watering' and data['avg_interval_days'] > 14:
                suggestions.append("Consider more frequent watering checks")
            
            if activity_type == 'fertilizing' and data['avg_interval_days'] > 30:
                suggestions.append("Regular monthly fertilizing would benefit most orchids")
        
        return suggestions

# Initialize the analyzer
collection_analyzer = AICollectionAnalyzer()

def register_collection_manager_routes(app):
    """Register collection manager routes with Flask app"""
    app.register_blueprint(collection_manager_bp)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    logger.info("🌺 AI Collection Manager registered successfully")