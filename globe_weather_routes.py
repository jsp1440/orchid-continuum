"""
Enhanced Globe Weather Widget API Routes
Provides country-specific orchid data and solar activity information
"""

from flask import request, jsonify, Blueprint
from models import OrchidRecord, db
from sqlalchemy import func, or_
import logging
import random
import math
from datetime import datetime

logger = logging.getLogger(__name__)

# Create blueprint for globe weather routes
globe_weather_bp = Blueprint('globe_weather', __name__, url_prefix='/api')

@globe_weather_bp.route('/orchids-by-country')
def get_orchids_by_country():
    """API endpoint to get orchids from a specific country for the globe widget"""
    try:
        country = request.args.get('country')
        limit = int(request.args.get('limit', 10))
        
        if not country:
            return jsonify({
                'success': False,
                'error': 'Country parameter required'
            }), 400
        
        # Query orchids from the specified country/region
        orchids = OrchidRecord.query.filter(
            OrchidRecord.region.ilike(f'%{country}%'),
            or_(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.google_drive_id.isnot(None)
            ),
            OrchidRecord.validation_status != 'rejected'
        ).order_by(
            OrchidRecord.view_count.desc().nullslast(),
            OrchidRecord.created_at.desc()
        ).limit(limit).all()
        
        # Format orchid data for the widget
        orchid_data = []
        for orchid in orchids:
            # Determine image URL (prioritize Google Drive)
            image_url = orchid.image_url
            if orchid.google_drive_id:
                image_url = f"/api/drive-photo/{orchid.google_drive_id}"
            
            orchid_data.append({
                'id': orchid.id,
                'display_name': orchid.display_name or 'Unknown Orchid',
                'scientific_name': orchid.scientific_name,
                'image_url': image_url,
                'region': orchid.region,
                'climate_preference': orchid.climate_preference,
                'temperature_range': orchid.temperature_range,
                'light_requirements': orchid.light_requirements,
                'growth_habit': orchid.growth_habit,
                'cultural_notes': orchid.cultural_notes,
                'has_baker_data': bool(orchid.cultural_notes and 'BAKER' in orchid.cultural_notes.upper()) if orchid.cultural_notes else False
            })
        
        return jsonify({
            'success': True,
            'country': country,
            'orchids': orchid_data,
            'count': len(orchid_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching orchids for country {country}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch orchid data'
        }), 500

@globe_weather_bp.route('/solar-activity')
def get_solar_activity():
    """API endpoint to get current solar activity data"""
    try:
        # In a real implementation, this would fetch from NOAA Space Weather API
        # For now, return simulated data with realistic values
        
        # Generate realistic solar activity data
        activity_levels = ['Low', 'Moderate', 'High', 'Very High']
        activity_weights = [0.4, 0.35, 0.2, 0.05]  # More likely to be low/moderate
        
        activity_level = random.choices(activity_levels, weights=activity_weights)[0]
        
        # Generate correlated values based on activity level
        base_sunspots = {'Low': 20, 'Moderate': 60, 'High': 120, 'Very High': 180}
        sunspot_count = base_sunspots[activity_level] + random.randint(-15, 25)
        
        flare_levels = ['None', 'Low', 'Moderate', 'High', 'Extreme']
        if activity_level == 'Low':
            solar_flares = random.choice(['None', 'Low'])
        elif activity_level == 'Moderate':
            solar_flares = random.choice(['Low', 'Moderate'])
        elif activity_level == 'High':
            solar_flares = random.choice(['Moderate', 'High'])
        else:
            solar_flares = random.choice(['High', 'Extreme'])
        
        geomagnetic_states = ['Quiet', 'Unsettled', 'Active', 'Minor Storm', 'Major Storm']
        if activity_level in ['Low', 'Moderate']:
            geomagnetic = random.choice(['Quiet', 'Unsettled'])
        else:
            geomagnetic = random.choice(['Active', 'Minor Storm', 'Major Storm'])
        
        solar_data = {
            'timestamp': datetime.now().isoformat(),
            'activity_level': activity_level,
            'sunspot_count': max(0, sunspot_count),
            'solar_flares': solar_flares,
            'geomagnetic_activity': geomagnetic,
            'uv_index': random.randint(1, 11),
            'solar_wind_speed': random.randint(250, 800),  # km/s
            'solar_radio_flux': random.randint(65, 300),  # Solar Flux Units
            'planetary_k_index': random.randint(0, 9),
            'impact_on_weather': get_weather_impact_message(activity_level),
            'growing_advice': get_growing_advice_message(activity_level)
        }
        
        return jsonify({
            'success': True,
            'solar_data': solar_data
        })
        
    except Exception as e:
        logger.error(f"Error fetching solar activity data: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch solar data'
        }), 500

@globe_weather_bp.route('/photoperiod/<float:latitude>')
def get_photoperiod(latitude):
    """Calculate photoperiod (day length) for given latitude"""
    try:
        # Current day of year
        now = datetime.now()
        day_of_year = now.timetuple().tm_yday
        
        # Solar declination calculation
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle calculation
        lat_rad = math.radians(latitude)
        decl_rad = math.radians(declination)
        
        # Calculate sunrise hour angle
        try:
            hour_angle = math.acos(-math.tan(lat_rad) * math.tan(decl_rad))
            daylight_hours = 2 * hour_angle * 12 / math.pi
        except ValueError:
            # Handle polar day/night cases
            if latitude * declination > 0:
                daylight_hours = 24  # Polar day
            else:
                daylight_hours = 0   # Polar night
        
        # Solar noon elevation
        solar_elevation = 90 - abs(latitude - declination)
        
        # Calculate UV index approximation based on solar elevation
        if solar_elevation > 0:
            uv_index = max(0, min(11, int(solar_elevation / 10)))
        else:
            uv_index = 0
        
        return jsonify({
            'success': True,
            'latitude': latitude,
            'day_of_year': day_of_year,
            'daylight_hours': round(daylight_hours, 2),
            'solar_declination': round(declination, 2),
            'solar_elevation': round(solar_elevation, 2),
            'sunrise_angle': round(math.degrees(hour_angle), 2) if 'hour_angle' in locals() else None,
            'uv_index': uv_index,
            'season': get_season_for_latitude(latitude, day_of_year)
        })
        
    except Exception as e:
        logger.error(f"Error calculating photoperiod for latitude {latitude}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to calculate photoperiod'
        }), 500

@globe_weather_bp.route('/country-climate/<country_name>')
def get_country_climate(country_name):
    """Get climate data for a specific country"""
    try:
        # Simplified climate data for major orchid-growing countries
        climate_data = {
            'Colombia': {
                'avg_temp': 24,
                'humidity': 75,
                'rainfall': 1200,
                'climate_zone': 'Tropical',
                'growing_season': 'Year-round',
                'best_months': ['Mar', 'Apr', 'Sep', 'Oct']
            },
            'Ecuador': {
                'avg_temp': 21,
                'humidity': 80,
                'rainfall': 1500,
                'climate_zone': 'Tropical Highland',
                'growing_season': 'Year-round',
                'best_months': ['Feb', 'Mar', 'Oct', 'Nov']
            },
            'Brazil': {
                'avg_temp': 25,
                'humidity': 70,
                'rainfall': 1400,
                'climate_zone': 'Tropical',
                'growing_season': 'Oct-Mar',
                'best_months': ['Nov', 'Dec', 'Jan', 'Feb']
            },
            'Thailand': {
                'avg_temp': 28,
                'humidity': 75,
                'rainfall': 1200,
                'climate_zone': 'Tropical Monsoon',
                'growing_season': 'May-Oct',
                'best_months': ['Jun', 'Jul', 'Aug', 'Sep']
            },
            'Madagascar': {
                'avg_temp': 23,
                'humidity': 65,
                'rainfall': 800,
                'climate_zone': 'Tropical Dry',
                'growing_season': 'Nov-Apr',
                'best_months': ['Dec', 'Jan', 'Feb', 'Mar']
            },
            'Philippines': {
                'avg_temp': 27,
                'humidity': 80,
                'rainfall': 1800,
                'climate_zone': 'Tropical Maritime',
                'growing_season': 'Year-round',
                'best_months': ['Dec', 'Jan', 'Feb', 'Mar']
            }
        }
        
        country_climate = climate_data.get(country_name, {
            'avg_temp': 22,
            'humidity': 70,
            'rainfall': 1000,
            'climate_zone': 'Temperate',
            'growing_season': 'Spring-Fall',
            'best_months': ['Apr', 'May', 'Sep', 'Oct']
        })
        
        # Add current season information
        current_month = datetime.now().month
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        current_month_name = month_names[current_month - 1]
        
        is_growing_season = current_month_name in country_climate.get('best_months', [])
        
        return jsonify({
            'success': True,
            'country': country_name,
            'climate': country_climate,
            'current_month': current_month_name,
            'is_growing_season': is_growing_season,
            'growing_advice': get_country_growing_advice(country_name, country_climate, is_growing_season)
        })
        
    except Exception as e:
        logger.error(f"Error fetching climate data for {country_name}: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch climate data'
        }), 500

def get_weather_impact_message(activity_level):
    """Generate weather impact message based on solar activity level"""
    messages = {
        'Low': 'Minimal solar influence on weather patterns. Standard greenhouse conditions recommended.',
        'Moderate': 'Some solar influence on atmospheric temperatures. Monitor greenhouse heating/cooling.',
        'High': 'Increased solar radiation may affect temperature regulation. Adjust shade cloth as needed.',
        'Very High': 'Strong solar activity may cause temperature fluctuations. Provide extra protection for sensitive orchids.'
    }
    return messages.get(activity_level, 'Solar activity data unavailable.')

def get_growing_advice_message(activity_level):
    """Generate growing advice based on solar activity level"""
    advice = {
        'Low': 'Perfect conditions for most orchids. Maintain regular care routines.',
        'Moderate': 'Good growing conditions. Monitor for any stress signs in sensitive species.',
        'High': 'Provide extra shade for sensitive orchids. Increase ventilation to prevent overheating.',
        'Very High': 'Use shade cloth and ensure excellent air circulation. Watch for heat stress symptoms.'
    }
    return advice.get(activity_level, 'Maintain standard orchid care practices.')

def get_season_for_latitude(latitude, day_of_year):
    """Determine season based on latitude and day of year"""
    # Northern hemisphere seasons
    if latitude >= 0:
        if 80 <= day_of_year < 172:  # March 21 - June 20
            return 'Spring'
        elif 172 <= day_of_year < 266:  # June 21 - September 22
            return 'Summer'
        elif 266 <= day_of_year < 355:  # September 23 - December 20
            return 'Autumn'
        else:  # December 21 - March 20
            return 'Winter'
    else:
        # Southern hemisphere seasons (opposite)
        if 80 <= day_of_year < 172:
            return 'Autumn'
        elif 172 <= day_of_year < 266:
            return 'Winter'
        elif 266 <= day_of_year < 355:
            return 'Spring'
        else:
            return 'Summer'

def get_country_growing_advice(country_name, climate_data, is_growing_season):
    """Generate specific growing advice for a country"""
    base_advice = f"Based on {country_name}'s {climate_data['climate_zone']} climate "
    
    if is_growing_season:
        advice = base_advice + f"and current growing season, this is an excellent time for active growth. "
        advice += f"Maintain temperatures around {climate_data['avg_temp']}°C and {climate_data['humidity']}% humidity."
    else:
        advice = base_advice + "and current dormant season, reduce watering and maintain cooler conditions. "
        advice += "This is a good time for repotting and root care."
    
    return advice