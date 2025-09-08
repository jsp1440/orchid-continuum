"""
Science Lab Observation Data Integration Widget
Integrates field observations and research data into the scientific method platform
"""

import json
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, render_template, session
from sqlalchemy import text, func, and_, or_
from app import db, app
from models import OrchidRecord

logger = logging.getLogger(__name__)

science_obs_bp = Blueprint('science_lab_observations', __name__)

class ObservationDataIntegrator:
    """Integrates field observations with existing botanical data"""
    
    def __init__(self):
        self.observation_types = [
            'flowering_observation',
            'habitat_conditions', 
            'phenotype_measurement',
            'geographic_sighting',
            'cultivation_experiment',
            'pollinator_interaction',
            'environmental_data'
        ]
        
    def collect_field_observation(self, observation_data):
        """Process and integrate field observation data"""
        try:
            # Validate observation data
            validated_data = self._validate_observation(observation_data)
            
            # Match with existing orchid records
            matching_records = self._find_matching_records(validated_data)
            
            # Create observation entry
            observation_entry = self._create_observation_entry(validated_data, matching_records)
            
            # Update related statistics
            self._update_botany_lab_stats(observation_entry)
            
            return {
                'success': True,
                'observation_id': observation_entry['id'],
                'matched_records': len(matching_records),
                'observation_type': validated_data['type'],
                'timestamp': observation_entry['timestamp']
            }
            
        except Exception as e:
            logger.error(f"Error processing field observation: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _validate_observation(self, data):
        """Validate and standardize observation data"""
        required_fields = ['type', 'description', 'location']
        
        # Check required fields
        for field in required_fields:
            if field not in data or not data[field]:
                raise ValueError(f"Missing required field: {field}")
        
        # Standardize observation type
        if data['type'] not in self.observation_types:
            data['type'] = 'general_observation'
        
        # Add timestamp if not provided
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
        
        # Parse coordinates if provided
        if 'coordinates' in data:
            coords = data['coordinates']
            if isinstance(coords, str):
                try:
                    # Parse "lat,lng" format
                    lat, lng = map(float, coords.split(','))
                    data['latitude'] = lat
                    data['longitude'] = lng
                except:
                    logger.warning(f"Could not parse coordinates: {coords}")
        
        return data
    
    def _find_matching_records(self, observation_data):
        """Find orchid records that match the observation"""
        try:
            query = OrchidRecord.query
            matches = []
            
            # Match by scientific name if provided
            if 'scientific_name' in observation_data:
                scientific_match = query.filter(
                    OrchidRecord.scientific_name.ilike(f"%{observation_data['scientific_name']}%")
                ).first()
                if scientific_match:
                    matches.append(scientific_match)
            
            # Match by genus if provided
            if 'genus' in observation_data:
                genus_matches = query.filter(
                    OrchidRecord.genus.ilike(f"%{observation_data['genus']}%")
                ).limit(5).all()
                matches.extend(genus_matches)
            
            # Geographic matching if coordinates provided
            if 'latitude' in observation_data and 'longitude' in observation_data:
                lat = observation_data['latitude']
                lng = observation_data['longitude']
                
                # Find orchids within ~50km radius (approximately 0.5 degrees)
                geographic_matches = query.filter(
                    and_(
                        OrchidRecord.decimal_latitude.between(lat - 0.5, lat + 0.5),
                        OrchidRecord.decimal_longitude.between(lng - 0.5, lng + 0.5)
                    )
                ).limit(10).all()
                matches.extend(geographic_matches)
            
            # Remove duplicates while preserving order
            unique_matches = []
            seen_ids = set()
            for match in matches:
                if match.id not in seen_ids:
                    unique_matches.append(match)
                    seen_ids.add(match.id)
            
            return unique_matches[:10]  # Limit to top 10 matches
            
        except Exception as e:
            logger.error(f"Error finding matching records: {e}")
            return []
    
    def _create_observation_entry(self, validated_data, matching_records):
        """Create standardized observation entry"""
        observation_entry = {
            'id': f"obs_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': validated_data['timestamp'],
            'type': validated_data['type'],
            'description': validated_data['description'],
            'location': validated_data['location'],
            'observer': validated_data.get('observer', 'Anonymous'),
            'coordinates': {
                'latitude': validated_data.get('latitude'),
                'longitude': validated_data.get('longitude')
            },
            'environmental_conditions': validated_data.get('conditions', {}),
            'matched_orchids': [
                {
                    'id': record.id,
                    'scientific_name': record.scientific_name,
                    'genus': record.genus,
                    'species': record.species
                } for record in matching_records
            ],
            'confidence_score': self._calculate_confidence(validated_data, matching_records),
            'data_quality': self._assess_data_quality(validated_data)
        }
        
        # Store in session for widget display
        if 'recent_observations' not in session:
            session['recent_observations'] = []
        
        session['recent_observations'].insert(0, observation_entry)
        session['recent_observations'] = session['recent_observations'][:50]  # Keep last 50
        
        return observation_entry
    
    def _calculate_confidence(self, data, matches):
        """Calculate confidence score for the observation"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence based on data completeness
        if 'scientific_name' in data:
            confidence += 0.2
        if 'coordinates' in data or ('latitude' in data and 'longitude' in data):
            confidence += 0.2
        if 'environmental_conditions' in data or 'conditions' in data:
            confidence += 0.1
        
        # Increase confidence if we found matching records
        if matches:
            confidence += min(0.2, len(matches) * 0.02)
        
        return min(1.0, confidence)
    
    def _assess_data_quality(self, data):
        """Assess the quality of observation data"""
        quality_score = 0
        quality_factors = []
        
        # Check for key scientific fields
        if 'scientific_name' in data:
            quality_score += 25
            quality_factors.append('Scientific name provided')
        
        if 'coordinates' in data or ('latitude' in data and 'longitude' in data):
            quality_score += 25
            quality_factors.append('GPS coordinates included')
        
        if 'environmental_conditions' in data or 'conditions' in data:
            quality_score += 20
            quality_factors.append('Environmental data recorded')
        
        if len(data.get('description', '')) > 50:
            quality_score += 15
            quality_factors.append('Detailed description')
        
        if 'timestamp' in data:
            quality_score += 10
            quality_factors.append('Timestamp recorded')
        
        if 'observer' in data:
            quality_score += 5
            quality_factors.append('Observer identified')
        
        quality_level = 'Poor'
        if quality_score >= 80:
            quality_level = 'Excellent'
        elif quality_score >= 60:
            quality_level = 'Good'
        elif quality_score >= 40:
            quality_level = 'Fair'
        
        return {
            'score': quality_score,
            'level': quality_level,
            'factors': quality_factors
        }
    
    def _update_botany_lab_stats(self, observation_entry):
        """Update botany lab statistics with new observation"""
        try:
            # Update observation statistics in session
            if 'lab_stats' not in session:
                session['lab_stats'] = {
                    'total_observations': 0,
                    'observations_by_type': {},
                    'recent_activity': [],
                    'data_quality_distribution': {'Poor': 0, 'Fair': 0, 'Good': 0, 'Excellent': 0}
                }
            
            stats = session['lab_stats']
            
            # Update totals
            stats['total_observations'] += 1
            
            # Update by type
            obs_type = observation_entry['type']
            if obs_type not in stats['observations_by_type']:
                stats['observations_by_type'][obs_type] = 0
            stats['observations_by_type'][obs_type] += 1
            
            # Update quality distribution
            quality_level = observation_entry['data_quality']['level']
            stats['data_quality_distribution'][quality_level] += 1
            
            # Add to recent activity
            activity_entry = {
                'timestamp': observation_entry['timestamp'],
                'type': obs_type,
                'quality': quality_level,
                'matches': len(observation_entry['matched_orchids'])
            }
            stats['recent_activity'].insert(0, activity_entry)
            stats['recent_activity'] = stats['recent_activity'][:20]  # Keep last 20
            
            session['lab_stats'] = stats
            
        except Exception as e:
            logger.error(f"Error updating botany lab stats: {e}")
    
    def get_observation_summary(self):
        """Get summary of recent observations for widget display"""
        try:
            recent_obs = session.get('recent_observations', [])
            lab_stats = session.get('lab_stats', {})
            
            return {
                'total_observations': len(recent_obs),
                'recent_observations': recent_obs[:10],  # Last 10 for display
                'statistics': lab_stats,
                'quality_metrics': self._calculate_quality_metrics(recent_obs),
                'geographic_coverage': self._calculate_geographic_coverage(recent_obs)
            }
            
        except Exception as e:
            logger.error(f"Error getting observation summary: {e}")
            return {
                'total_observations': 0,
                'recent_observations': [],
                'statistics': {},
                'error': str(e)
            }
    
    def _calculate_quality_metrics(self, observations):
        """Calculate quality metrics for observations"""
        if not observations:
            return {'average_quality': 0, 'high_quality_count': 0}
        
        total_quality = sum(obs.get('data_quality', {}).get('score', 0) for obs in observations)
        average_quality = total_quality / len(observations)
        high_quality_count = sum(1 for obs in observations 
                               if obs.get('data_quality', {}).get('score', 0) >= 70)
        
        return {
            'average_quality': round(average_quality, 1),
            'high_quality_count': high_quality_count,
            'high_quality_percentage': round((high_quality_count / len(observations)) * 100, 1)
        }
    
    def _calculate_geographic_coverage(self, observations):
        """Calculate geographic coverage of observations"""
        locations = set()
        coordinates_count = 0
        
        for obs in observations:
            if 'location' in obs:
                locations.add(obs['location'])
            if obs.get('coordinates', {}).get('latitude'):
                coordinates_count += 1
        
        return {
            'unique_locations': len(locations),
            'gps_coverage': coordinates_count,
            'gps_percentage': round((coordinates_count / len(observations)) * 100, 1) if observations else 0
        }

# Initialize the integrator
observation_integrator = ObservationDataIntegrator()

@science_obs_bp.route('/api/submit-observation', methods=['POST'])
def submit_field_observation():
    """API endpoint to submit field observations"""
    try:
        observation_data = request.get_json()
        result = observation_integrator.collect_field_observation(observation_data)
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error in submit_field_observation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@science_obs_bp.route('/api/observation-summary')
def get_observation_summary():
    """Get summary of observations for dashboard"""
    try:
        summary = observation_integrator.get_observation_summary()
        return jsonify(summary)
    except Exception as e:
        logger.error(f"Error in get_observation_summary: {e}")
        return jsonify({'error': str(e)}), 500

@science_obs_bp.route('/widget/science-observations')
def science_observations_widget():
    """Standalone science observations widget"""
    try:
        summary = observation_integrator.get_observation_summary()
        return render_template('widgets/science_observations.html', 
                             widget_data=summary, 
                             standalone=True)
    except Exception as e:
        logger.error(f"Error in science_observations_widget: {e}")
        return render_template('widgets/science_observations.html', 
                             widget_data={'error': str(e)}, 
                             standalone=True)

@science_obs_bp.route('/science-lab-dashboard')
def science_lab_dashboard():
    """Full science lab dashboard with observation integration"""
    try:
        summary = observation_integrator.get_observation_summary()
        
        # Get botany lab statistics
        try:
            from botany_lab_stats import BotanyLabStats
            botany_stats = BotanyLabStats().get_comprehensive_stats()
        except ImportError:
            botany_stats = {'error': 'Botany lab stats not available'}
        
        return render_template('science_lab_dashboard.html', 
                             observation_data=summary,
                             botany_stats=botany_stats)
    except Exception as e:
        logger.error(f"Error in science_lab_dashboard: {e}")
        return render_template('science_lab_dashboard.html', 
                             observation_data={'error': str(e)},
                             botany_stats={'error': str(e)})

def register_science_observation_routes(app):
    """Register science observation routes with the Flask app"""
    # Check if blueprint is already registered
    if 'science_lab_observations' not in [bp.name for bp in app.blueprints.values()]:
        app.register_blueprint(science_obs_bp)
        logger.info("🔬 Science Observation Widget registered successfully")
    else:
        logger.info("🔬 Science Observation Widget already registered")

# Auto-register if running directly
if __name__ != '__main__':
    try:
        from app import app
        register_science_observation_routes(app)
    except Exception as e:
        logger.error(f"Failed to register science observation routes: {e}")