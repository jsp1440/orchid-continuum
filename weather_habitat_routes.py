"""
Weather/Habitat Comparison Widget Routes
Provides routes for comparing local growing conditions with orchid native habitats
"""

from flask import Blueprint, request, jsonify, render_template
from flask_login import current_user, login_required
from datetime import datetime, timedelta
import logging

from weather_habitat_comparison_widget import (
    WeatherHabitatComparison, ComparisonMode, LocationData, WeatherConditions,
    get_user_location_from_ip, get_orchid_habitat_location, estimate_habitat_from_region
)
from weather_service import WeatherService
from models import OrchidRecord

logger = logging.getLogger(__name__)

# Create blueprint for weather/habitat comparison routes
weather_habitat_bp = Blueprint('weather_habitat', __name__, url_prefix='/weather-habitat')

@weather_habitat_bp.route('/compare/<int:orchid_id>')
def compare_orchid_habitat(orchid_id):
    """Main weather/habitat comparison page for a specific orchid"""
    try:
        # Get orchid record
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Get user location (from profile or IP)
        user_location = get_user_location_from_ip()  # Default fallback
        
        # Try to get user's preferred location if logged in
        if current_user.is_authenticated:
            from models import UserLocation
            user_locations = UserLocation.query.filter_by(user_id=current_user.id, is_primary=True).first()
            if user_locations:
                user_location = LocationData(
                    latitude=user_locations.latitude,
                    longitude=user_locations.longitude,
                    city=user_locations.name,
                    elevation=getattr(user_locations, 'elevation', None)
                )
        
        # Get orchid habitat location
        habitat_location = get_orchid_habitat_location(orchid_id)
        if not habitat_location:
            habitat_location = estimate_habitat_from_region(orchid.region or "Southeast Asia", orchid.genus)
        
        return render_template('weather_habitat/comparison.html',
                             orchid=orchid,
                             user_location=user_location.__dict__ if user_location else None,
                             habitat_location=habitat_location.__dict__ if habitat_location else None)
        
    except Exception as e:
        logger.error(f"Error in orchid habitat comparison: {str(e)}")
        return render_template('error.html', error="Unable to load habitat comparison"), 500

@weather_habitat_bp.route('/api/compare', methods=['POST'])
def api_compare_conditions():
    """API endpoint for weather/habitat comparison"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Parse user location
        user_loc_data = data.get('user_location')
        if not user_loc_data:
            return jsonify({'error': 'User location required'}), 400
        
        user_location = LocationData(
            latitude=user_loc_data['latitude'],
            longitude=user_loc_data['longitude'],
            city=user_loc_data.get('city'),
            elevation=user_loc_data.get('elevation')
        )
        
        # Parse habitat location
        habitat_loc_data = data.get('habitat_location')
        if not habitat_loc_data:
            return jsonify({'error': 'Habitat location required'}), 400
        
        habitat_location = LocationData(
            latitude=habitat_loc_data['latitude'],
            longitude=habitat_loc_data['longitude'],
            city=habitat_loc_data.get('city'),
            elevation=habitat_loc_data.get('elevation')
        )
        
        # Get current local weather
        weather_data = WeatherService.get_current_weather(
            user_location.latitude, user_location.longitude, user_location.city
        )
        
        if not weather_data:
            return jsonify({'error': 'Unable to fetch current weather'}), 500
        
        local_weather = WeatherConditions(
            temperature=weather_data.temperature or 20.0,
            humidity=weather_data.humidity or 60.0,
            pressure=weather_data.pressure,
            wind_speed=weather_data.wind_speed,
            timestamp=weather_data.recorded_at
        )
        
        # Parse comparison mode
        mode_str = data.get('mode', 'seasonal')
        try:
            mode = ComparisonMode(mode_str)
        except ValueError:
            mode = ComparisonMode.SEASONAL
        
        # Parse environment type
        environment_type = data.get('environment_type', 'greenhouse')
        
        # Perform comparison
        comparison = WeatherHabitatComparison()
        result = comparison.compare_conditions(
            user_location, habitat_location, local_weather, mode, environment_type
        )
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in API comparison: {str(e)}")
        return jsonify({'error': str(e)}), 500

@weather_habitat_bp.route('/api/orchid/<int:orchid_id>/habitat')
def api_get_orchid_habitat(orchid_id):
    """Get habitat location data for a specific orchid"""
    try:
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Get habitat location
        habitat_location = get_orchid_habitat_location(orchid_id)
        if not habitat_location:
            habitat_location = estimate_habitat_from_region(orchid.region or "Southeast Asia", orchid.genus)
        
        return jsonify({
            'orchid_id': orchid_id,
            'orchid_name': orchid.scientific_name or orchid.display_name,
            'habitat_location': habitat_location.__dict__ if habitat_location else None,
            'confidence': 'medium' if habitat_location else 'low'
        })
        
    except Exception as e:
        logger.error(f"Error getting orchid habitat: {str(e)}")
        return jsonify({'error': str(e)}), 500

@weather_habitat_bp.route('/widget/<int:orchid_id>')
def embedded_widget(orchid_id):
    """Embeddable widget version of the comparison"""
    try:
        orchid = OrchidRecord.query.get_or_404(orchid_id)
        
        # Get locations
        user_location = get_user_location_from_ip()
        habitat_location = get_orchid_habitat_location(orchid_id)
        if not habitat_location:
            habitat_location = estimate_habitat_from_region(orchid.region or "Southeast Asia", orchid.genus)
        
        return render_template('weather_habitat/widget.html',
                             orchid=orchid,
                             user_location=user_location.__dict__ if user_location else None,
                             habitat_location=habitat_location.__dict__ if habitat_location else None,
                             widget_mode=True)
        
    except Exception as e:
        logger.error(f"Error in embedded widget: {str(e)}")
        return render_template('error.html', error="Unable to load widget"), 500

@weather_habitat_bp.route('/demo')
def demo_comparison():
    """Demo page showing the weather/habitat comparison system"""
    try:
        # Use demo orchid and locations
        demo_orchid = {
            'id': 1,
            'scientific_name': 'Phalaenopsis amabilis',
            'display_name': 'Moon Orchid',
            'genus': 'Phalaenopsis',
            'region': 'Southeast Asia'
        }
        
        # Demo locations
        user_location = LocationData(
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco, CA"
        )
        
        habitat_location = LocationData(
            latitude=1.3521,
            longitude=103.8198,
            city="Southeast Asia"
        )
        
        # Get current weather for demo
        weather_data = WeatherService.get_current_weather(
            user_location.latitude, user_location.longitude, user_location.city
        )
        
        # Perform demo comparison
        if weather_data:
            local_weather = WeatherConditions(
                temperature=weather_data.temperature or 18.0,
                humidity=weather_data.humidity or 65.0,
                timestamp=datetime.now()
            )
            
            comparison = WeatherHabitatComparison()
            demo_result = comparison.compare_conditions(
                user_location, habitat_location, local_weather, ComparisonMode.SEASONAL, "greenhouse"
            )
        else:
            demo_result = {'error': 'Weather data unavailable for demo'}
        
        return render_template('weather_habitat/demo.html',
                             orchid=demo_orchid,
                             user_location=user_location.__dict__,
                             habitat_location=habitat_location.__dict__,
                             demo_result=demo_result)
        
    except Exception as e:
        logger.error(f"Error in demo comparison: {str(e)}")
        return render_template('error.html', error="Unable to load demo"), 500

@weather_habitat_bp.route('/api/user-location', methods=['POST'])
def api_set_user_location():
    """Set or update user location for comparisons"""
    try:
        data = request.get_json()
        
        # Support different input methods
        if data.get('zip_code'):
            from weather_service import get_coordinates_from_zip_code
            location_data = get_coordinates_from_zip_code(data['zip_code'], data.get('country', 'US'))
            if not location_data:
                return jsonify({'error': 'Invalid ZIP code'}), 400
            
            user_location = LocationData(
                latitude=location_data['latitude'],
                longitude=location_data['longitude'],
                city=location_data['name']
            )
        
        elif data.get('city'):
            from weather_service import get_coordinates_from_location
            coords = get_coordinates_from_location(data['city'])
            if not coords:
                return jsonify({'error': 'City not found'}), 400
            
            user_location = LocationData(
                latitude=coords[0],
                longitude=coords[1],
                city=data['city']
            )
        
        elif data.get('latitude') and data.get('longitude'):
            user_location = LocationData(
                latitude=data['latitude'],
                longitude=data['longitude'],
                city=data.get('city', 'Custom Location')
            )
        
        else:
            return jsonify({'error': 'Location data required (zip_code, city, or coordinates)'}), 400
        
        # Store in session or user profile if logged in
        if current_user.is_authenticated:
            # Could save to user preferences here
            pass
        
        return jsonify({
            'success': True,
            'location': user_location.__dict__,
            'message': 'Location updated successfully'
        })
        
    except Exception as e:
        logger.error(f"Error setting user location: {str(e)}")
        return jsonify({'error': str(e)}), 500

def register_weather_habitat_routes(app):
    """Register weather habitat comparison routes with the Flask app"""
    app.register_blueprint(weather_habitat_bp)
    logger.info("Weather/Habitat Comparison routes registered successfully")