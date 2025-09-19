"""
User Weather Management Routes
Handles user ZIP code input and personalized weather display
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import UserLocation, WeatherData, WeatherAlert, UserOrchidCollection, OrchidRecord
from weather_service import WeatherService, get_coordinates_from_zip_code
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

user_weather_bp = Blueprint('user_weather', __name__, url_prefix='/my-weather')

@user_weather_bp.route('/')
@login_required
def my_weather_dashboard():
    """User's personalized weather dashboard"""
    user_locations = UserLocation.query.filter_by(user_id=current_user.id).all()
    
    weather_data = {}
    alerts = []
    
    for location in user_locations:
        # Get current weather
        current_weather = WeatherService.get_current_weather(
            location.latitude, location.longitude, location.name
        )
        if current_weather:
            weather_data[location.id] = current_weather
        
        # Get any active alerts for this location
        location_alerts = WeatherAlert.query.filter_by(
            location_id=location.id,
            is_active=True,
            user_id=current_user.id
        ).filter(WeatherAlert.expires_at > datetime.utcnow()).all()
        alerts.extend(location_alerts)
    
    return render_template('weather/my_weather.html', 
                         locations=user_locations,
                         weather_data=weather_data,
                         alerts=alerts)

@user_weather_bp.route('/add-location', methods=['GET', 'POST'])
@login_required
def add_location():
    """Add a new location by ZIP code"""
    if request.method == 'POST':
        zip_code = request.form.get('zip_code', '').strip()
        location_name = request.form.get('location_name', '').strip()
        country = request.form.get('country', 'US').strip()
        growing_type = request.form.get('growing_type', 'indoor')
        notes = request.form.get('notes', '').strip()
        
        if not zip_code:
            flash('ZIP code is required.', 'error')
            return render_template('weather/add_location.html')
        
        # Get coordinates from ZIP code
        location_data = get_coordinates_from_zip_code(zip_code, country)
        
        if not location_data:
            flash(f'Could not find location for ZIP code: {zip_code}', 'error')
            return render_template('weather/add_location.html')
        
        # Use provided name or default from geocoding
        if not location_name:
            location_name = location_data['name']
        
        # Check if user already has this location
        existing_location = UserLocation.query.filter_by(
            user_id=current_user.id,
            zip_code=zip_code
        ).first()
        
        if existing_location:
            flash(f'You already have a location for ZIP code: {zip_code}', 'warning')
            return redirect(url_for('user_weather.my_weather_dashboard'))
        
        # Create new user location
        new_location = UserLocation(
            user_id=current_user.id,
            name=location_name,
            latitude=location_data['latitude'],
            longitude=location_data['longitude'],
            city=location_data['city'],
            state_province=location_data['state_province'],
            country=location_data['country'],
            zip_code=zip_code,
            timezone=location_data['timezone'],
            growing_type=growing_type,
            microclimate_notes=notes,
            is_primary=UserLocation.query.filter_by(user_id=current_user.id).count() == 0  # First location is primary
        )
        
        try:
            db.session.add(new_location)
            db.session.commit()
            
            # Get initial weather data for this location
            weather = WeatherService.get_current_weather(
                new_location.latitude, new_location.longitude, new_location.name
            )
            
            flash(f'Successfully added location: {location_name} (ZIP: {zip_code})', 'success')
            return redirect(url_for('user_weather.my_weather_dashboard'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding user location: {str(e)}")
            flash('Error adding location. Please try again.', 'error')
    
    return render_template('weather/add_location.html')

@user_weather_bp.route('/location/<int:location_id>')
@login_required
def location_detail(location_id):
    """Detailed weather view for a specific location"""
    location = UserLocation.query.filter_by(id=location_id, user_id=current_user.id).first_or_404()
    
    # Get current weather
    current_weather = WeatherService.get_current_weather(
        location.latitude, location.longitude, location.name
    )
    
    # Get 7-day forecast
    forecast = WeatherService.get_weather_forecast(
        location.latitude, location.longitude, days=7, location_name=location.name
    )
    
    # Get recent weather history (last 7 days)
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=7)
    historical = WeatherService.get_historical_weather(
        location.latitude, location.longitude, start_date, end_date, location.name
    )
    
    # Get active alerts
    alerts = WeatherAlert.query.filter_by(
        location_id=location.id,
        user_id=current_user.id,
        is_active=True
    ).filter(WeatherAlert.expires_at > datetime.utcnow()).all()
    
    # Get growing conditions summary
    growing_summary = WeatherService.get_growing_conditions_summary(location, days=7)
    
    return render_template('weather/location_detail.html',
                         location=location,
                         current_weather=current_weather,
                         forecast=forecast,
                         historical=historical,
                         alerts=alerts,
                         growing_summary=growing_summary)

@user_weather_bp.route('/location/<int:location_id>/delete', methods=['POST'])
@login_required
def delete_location(location_id):
    """Delete a user location"""
    location = UserLocation.query.filter_by(id=location_id, user_id=current_user.id).first_or_404()
    
    try:
        # Delete associated alerts
        WeatherAlert.query.filter_by(location_id=location.id).delete()
        
        # Delete the location
        db.session.delete(location)
        db.session.commit()
        
        flash(f'Deleted location: {location.name}', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting location: {str(e)}")
        flash('Error deleting location. Please try again.', 'error')
    
    return redirect(url_for('user_weather.my_weather_dashboard'))

@user_weather_bp.route('/alerts/acknowledge/<int:alert_id>', methods=['POST'])
@login_required
def acknowledge_alert(alert_id):
    """Acknowledge a weather alert"""
    alert = WeatherAlert.query.filter_by(id=alert_id, user_id=current_user.id).first_or_404()
    
    alert.is_acknowledged = True
    alert.acknowledged_at = datetime.utcnow()
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Alert acknowledged'})

@user_weather_bp.route('/api/zip-lookup')
@login_required
def zip_lookup():
    """API endpoint to look up ZIP code coordinates"""
    zip_code = request.args.get('zip_code', '').strip()
    country = request.args.get('country', 'US').strip()
    
    if not zip_code:
        return jsonify({'error': 'ZIP code is required'}), 400
    
    location_data = get_coordinates_from_zip_code(zip_code, country)
    
    if location_data:
        return jsonify(location_data)
    else:
        return jsonify({'error': 'Location not found'}), 404

# Weather Widget API Endpoints
@user_weather_bp.route('/api/weather/current')
def api_current_weather():
    """API endpoint for current weather (for widgets)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        weather = WeatherService.get_current_weather(lat, lon)
        if weather:
            return jsonify({
                'temperature': weather.temperature,
                'humidity': weather.humidity,
                'wind_speed': weather.wind_speed,
                'wind_direction': weather.wind_direction,
                'pressure': weather.pressure,
                'weather_code': weather.weather_code,
                'description': weather.description,
                'temperature_max': weather.temperature_max,
                'temperature_min': weather.temperature_min,
                'vpd': weather.vpd,
                'recorded_at': weather.recorded_at.isoformat()
            })
        else:
            return jsonify({'error': 'Unable to fetch weather data'}), 500
            
    except Exception as e:
        logger.error(f"Error in weather API: {str(e)}")
        return jsonify({'error': 'Weather service unavailable'}), 500

@user_weather_bp.route('/api/weather/forecast')
def api_weather_forecast():
    """API endpoint for weather forecast (for widgets)"""
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    days = request.args.get('days', 5, type=int)
    
    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude required'}), 400
    
    try:
        forecast = WeatherService.get_weather_forecast(lat, lon, days)
        if forecast:
            return jsonify([{
                'date': day.recorded_at.isoformat(),
                'temperature_max': day.temperature_max,
                'temperature_min': day.temperature_min,
                'humidity': day.humidity,
                'precipitation': day.precipitation,
                'weather_code': day.weather_code,
                'description': day.description
            } for day in forecast])
        else:
            return jsonify({'error': 'Unable to fetch forecast data'}), 500
            
    except Exception as e:
        logger.error(f"Error in forecast API: {str(e)}")
        return jsonify({'error': 'Forecast service unavailable'}), 500

@user_weather_bp.route('/api/weather/zip/<zip_code>')
def api_weather_by_zip(zip_code):
    """API endpoint for weather by ZIP code (for widgets)"""
    country = request.args.get('country', 'US')
    
    # Get coordinates from ZIP
    location_data = get_coordinates_from_zip_code(zip_code, country)
    if not location_data:
        return jsonify({'error': 'ZIP code not found'}), 404
    
    try:
        # Get current weather
        weather = WeatherService.get_current_weather(
            location_data['latitude'], 
            location_data['longitude'], 
            location_data['name']
        )
        
        if weather:
            response_data = {
                'location': location_data,
                'weather': {
                    'temperature': weather.temperature,
                    'humidity': weather.humidity,
                    'wind_speed': weather.wind_speed,
                    'pressure': weather.pressure,
                    'weather_code': weather.weather_code,
                    'description': weather.description,
                    'temperature_max': weather.temperature_max,
                    'temperature_min': weather.temperature_min,
                    'vpd': weather.vpd
                }
            }
            return jsonify(response_data)
        else:
            return jsonify({'error': 'Unable to fetch weather data'}), 500
            
    except Exception as e:
        logger.error(f"Error in ZIP weather API: {str(e)}")
        return jsonify({'error': 'Weather service unavailable'}), 500

# User Orchid Collection Management for Weather Widget
@user_weather_bp.route('/api/user-orchids')
@login_required
def api_user_orchids():
    """Get user's orchid collection for weather widget"""
    try:
        # Get user's collections
        collections = UserOrchidCollection.query.filter_by(
            user_id=current_user.id,
            is_active=True,
            show_in_widget=True
        ).order_by(UserOrchidCollection.widget_priority.asc()).all()
        
        if not collections:
            # If no collections, suggest some popular orchids
            suggested_orchids = OrchidRecord.query.filter(
                OrchidRecord.climate_preference.isnot(None),
                OrchidRecord.image_url.isnot(None)
            ).order_by(OrchidRecord.view_count.desc()).limit(3).all()
            
            return jsonify({
                'user_orchids': [],
                'suggested_orchids': [{
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'image_url': orchid.image_url,
                    'region': orchid.region,
                    'climate_preference': orchid.climate_preference
                } for orchid in suggested_orchids]
            })
        
        user_orchids = []
        for collection in collections:
            orchid = collection.orchid
            if orchid:
                user_orchids.append({
                    'collection_id': collection.id,
                    'id': orchid.id,
                    'display_name': collection.collection_name or orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'image_url': orchid.image_url,
                    'region': orchid.region,
                    'climate_preference': orchid.climate_preference,
                    'temperature_range': orchid.temperature_range,
                    'is_primary': collection.is_primary,
                    'notes': collection.notes
                })
        
        return jsonify({'user_orchids': user_orchids})
        
    except Exception as e:
        logger.error(f"Error getting user orchids: {str(e)}")
        return jsonify({'error': 'Unable to load orchid collection'}), 500

@user_weather_bp.route('/collections')
def orchid_collections():
    """Public weather widget and orchid collections view - no login required"""
    # If user is logged in, show their collections
    if current_user.is_authenticated:
        collections = UserOrchidCollection.query.filter_by(
            user_id=current_user.id,
            is_active=True
        ).order_by(UserOrchidCollection.widget_priority.asc()).all()
    else:
        collections = []
    
    # Get available orchids to add to collection
    available_orchids = OrchidRecord.query.filter(
        OrchidRecord.climate_preference.isnot(None),
        OrchidRecord.image_url.isnot(None)
    ).order_by(OrchidRecord.display_name.asc()).limit(50).all()
    
    return render_template('weather/orchid_collections.html',
                         collections=collections,
                         available_orchids=available_orchids,
                         user_authenticated=current_user.is_authenticated)

@user_weather_bp.route('/collections/add', methods=['POST'])
@login_required
def add_orchid_to_collection():
    """Add an orchid to user's collection"""
    orchid_id = request.form.get('orchid_id', type=int)
    collection_name = request.form.get('collection_name', '').strip()
    notes = request.form.get('notes', '').strip()
    
    if not orchid_id:
        flash('Please select an orchid to add.', 'error')
        return redirect(url_for('user_weather.orchid_collections'))
    
    # Check if already in collection
    existing = UserOrchidCollection.query.filter_by(
        user_id=current_user.id,
        orchid_id=orchid_id
    ).first()
    
    if existing:
        flash('This orchid is already in your collection.', 'warning')
        return redirect(url_for('user_weather.orchid_collections'))
    
    # Get orchid details
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    # Create collection entry
    collection = UserOrchidCollection(
        user_id=current_user.id,
        orchid_id=orchid_id,
        collection_name=collection_name or orchid.display_name,
        notes=notes,
        is_primary=UserOrchidCollection.query.filter_by(user_id=current_user.id).count() == 0,
        widget_priority=UserOrchidCollection.query.filter_by(user_id=current_user.id).count() + 1
    )
    
    try:
        db.session.add(collection)
        db.session.commit()
        flash(f'Added {orchid.display_name} to your collection!', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding orchid to collection: {str(e)}")
        flash('Error adding orchid to collection.', 'error')
    
    return redirect(url_for('user_weather.orchid_collections'))