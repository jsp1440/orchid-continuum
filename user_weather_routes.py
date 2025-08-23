"""
User Weather Management Routes
Handles user ZIP code input and personalized weather display
"""

from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from models import UserLocation, WeatherData, WeatherAlert
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