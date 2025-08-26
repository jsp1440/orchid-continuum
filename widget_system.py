"""
Orchid Continuum Widget System
Creates embeddable widgets for external website integration
"""

from flask import Blueprint, render_template, request, jsonify, Response
from models import OrchidRecord, UserLocation, UserOrchidCollection, db
from sqlalchemy import func, or_
import json
from datetime import datetime
from weather_service import WeatherService

# Create blueprint for widget system
widget_bp = Blueprint('widgets', __name__, url_prefix='/widgets')

class OrchidWidgetSystem:
    """Manages embeddable widgets for external integration"""
    
    def __init__(self):
        self.widget_types = {
            'gallery': 'Orchid Gallery Widget',
            'search': 'Orchid Search Widget', 
            'comparison': 'Orchid Comparison Widget',
            'identifier': 'Orchid Identifier Widget',
            'citation': 'Citation Generator Widget',
            'featured': 'Featured Orchid Widget',
            'mission': 'Mission & Support Widget',
            'map': 'World Map Widget',
            'weather': 'Orchid Weather Comparison Widget',
            'enhanced_globe': 'Enhanced Globe Weather Widget'
        }
    
    def get_widget_data(self, widget_type: str, **kwargs):
        """Get data for specific widget type"""
        if widget_type == 'gallery':
            return self._get_gallery_data(**kwargs)
        elif widget_type == 'search':
            return self._get_search_data(**kwargs)
        elif widget_type == 'featured':
            return self._get_featured_data(**kwargs)
        elif widget_type == 'comparison':
            return self._get_comparison_data(**kwargs)
        elif widget_type == 'mission':
            return self._get_mission_data(**kwargs)
        elif widget_type == 'map':
            return self._get_map_data(**kwargs)
        elif widget_type == 'weather':
            return self._get_weather_data(**kwargs)
        elif widget_type == 'enhanced_globe':
            return self._get_enhanced_globe_data(**kwargs)
        else:
            return {'error': 'Unknown widget type'}
    
    def _get_gallery_data(self, limit=6, genus=None, **kwargs):
        """Get orchid gallery data for widget"""
        query = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.validation_status != 'rejected'
        )
        
        if genus:
            query = query.filter(OrchidRecord.genus.ilike(f'%{genus}%'))
        
        orchids = query.limit(limit).all()
        
        return {
            'orchids': [
                {
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': orchid.image_url,
                    'ai_description': orchid.ai_description[:100] + '...' if orchid.ai_description else None
                } for orchid in orchids
            ],
            'total_count': OrchidRecord.query.count()
        }
    
    def _get_search_data(self, query=None, **kwargs):
        """Get search results for widget"""
        if not query:
            return {'orchids': [], 'count': 0}
        
        search_query = OrchidRecord.query.filter(
            or_(
                OrchidRecord.display_name.ilike(f'%{query}%'),
                OrchidRecord.scientific_name.ilike(f'%{query}%'),
                OrchidRecord.genus.ilike(f'%{query}%'),
                OrchidRecord.species.ilike(f'%{query}%')
            ),
            OrchidRecord.validation_status != 'rejected'
        ).limit(10)
        
        orchids = search_query.all()
        
        return {
            'orchids': [
                {
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'image_url': orchid.image_url
                } for orchid in orchids
            ],
            'count': len(orchids),
            'query': query
        }
    
    def _get_featured_data(self, **kwargs):
        """Get featured orchid data"""
        featured_orchid = OrchidRecord.query.filter(
            OrchidRecord.is_featured == True,
            OrchidRecord.image_url.isnot(None)
        ).first()
        
        if not featured_orchid:
            # Get a random orchid with image
            featured_orchid = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None)
            ).order_by(func.random()).first()
        
        if featured_orchid:
            return {
                'orchid': {
                    'id': featured_orchid.id,
                    'display_name': featured_orchid.display_name,
                    'scientific_name': featured_orchid.scientific_name,
                    'genus': featured_orchid.genus,
                    'species': featured_orchid.species,
                    'image_url': featured_orchid.image_url,
                    'ai_description': featured_orchid.ai_description,
                    'growth_habit': featured_orchid.growth_habit,
                    'native_habitat': featured_orchid.native_habitat
                }
            }
        return {'orchid': None}
    
    def _get_comparison_data(self, **kwargs):
        """Get data for comparison widget"""
        recent_orchids = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None)
        ).order_by(OrchidRecord.created_at.desc()).limit(4).all()
        
        return {
            'orchids': [
                {
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': orchid.image_url
                } for orchid in recent_orchids
            ]
        }
    
    def _get_mission_data(self, **kwargs):
        """Get data for mission widget"""
        total_orchids = OrchidRecord.query.count()
        total_genera = db.session.query(func.count(func.distinct(OrchidRecord.genus))).filter(
            OrchidRecord.genus.isnot(None)
        ).scalar()
        
        return {
            'stats': {
                'total_orchids': total_orchids,
                'total_genera': total_genera,
                'features_count': 6  # Number of active features
            },
            'mission': {
                'title': 'The Orchid Continuum Project',
                'description': 'A visionary, AI-integrated digital ecosystem for orchid conservation and education',
                'status': 'Active Development'
            }
        }
    
    def _get_map_data(self, **kwargs):
        """Get map widget configuration data"""
        import uuid
        return {
            'widget_id': str(uuid.uuid4())[:8],  # Short unique ID for widget instances
            'api_base_url': kwargs.get('api_base_url', '/api'),
            'full_map_url': kwargs.get('full_map_url', '/map'),
            'base_url': kwargs.get('base_url', ''),
            'map_height': kwargs.get('height', '400px'),
            'enable_clustering': kwargs.get('clustering', True),
            'max_zoom': kwargs.get('max_zoom', 10),
            'initial_zoom': kwargs.get('initial_zoom', 2)
        }
    
    def _get_weather_data(self, **kwargs):
        """Get orchid weather comparison data for widget"""
        import uuid
        
        # Get user ID if provided (for user-specific collections)
        user_id = kwargs.get('user_id')
        location = kwargs.get('location', 'auto')  # auto-detect or specific location
        
        # Get user's orchid collection if user_id provided
        if user_id:
            user_collections = UserOrchidCollection.query.filter_by(
                user_id=user_id,
                is_active=True,
                show_in_widget=True
            ).order_by(UserOrchidCollection.widget_priority.asc()).limit(4).all()
            
            orchids_to_show = []
            for collection in user_collections:
                if collection.orchid:
                    orchids_to_show.append(collection.orchid)
        else:
            # For public widget, get diverse orchids with good climate data
            orchids_to_show = OrchidRecord.query.filter(
                OrchidRecord.climate_preference.isnot(None),
                OrchidRecord.region.isnot(None),
                OrchidRecord.image_url.isnot(None)
            ).order_by(OrchidRecord.view_count.desc()).limit(6).all()
        
        # Climate comparison data with more detailed native habitat info
        climate_mappings = {
            'cool': {
                'temp_range': '10-20°C',
                'humidity': '60-80%', 
                'color': '#4CAF50',
                'optimal_temp_min': 10,
                'optimal_temp_max': 20,
                'optimal_humidity_min': 60,
                'optimal_humidity_max': 80
            },
            'intermediate': {
                'temp_range': '18-28°C',
                'humidity': '50-70%',
                'color': '#2196F3',
                'optimal_temp_min': 18,
                'optimal_temp_max': 28,
                'optimal_humidity_min': 50,
                'optimal_humidity_max': 70
            },
            'warm': {
                'temp_range': '20-35°C',
                'humidity': '60-85%',
                'color': '#FF9800',
                'optimal_temp_min': 20,
                'optimal_temp_max': 35,
                'optimal_humidity_min': 60,
                'optimal_humidity_max': 85
            }
        }
        
        widget_data = {
            'widget_id': str(uuid.uuid4())[:8],
            'location_mode': location,
            'user_id': user_id,
            'orchids': [
                {
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'image_url': orchid.image_url,
                    'region': orchid.region or 'Tropical',
                    'climate_preference': orchid.climate_preference or 'intermediate',
                    'climate_data': climate_mappings.get(orchid.climate_preference or 'intermediate', climate_mappings['intermediate']),
                    'temperature_range': orchid.temperature_range,
                    'light_requirements': orchid.light_requirements or 'Bright indirect',
                    'growth_habit': orchid.growth_habit or 'epiphytic',
                    'cultural_notes': orchid.cultural_notes,
                    'has_baker_data': bool(orchid.cultural_notes and 'BAKER' in orchid.cultural_notes)
                } for orchid in orchids_to_show
            ],
            'climate_mappings': climate_mappings,
            'widget_config': {
                'width': '280px',
                'max_orchids': 3,
                'show_forecast': True,
                'show_care_advice': True,
                'auto_location': True
            }
        }
        
        return widget_data
    
    def _get_enhanced_globe_data(self, **kwargs):
        """Get enhanced globe weather widget data with country-orchid mapping"""
        import uuid
        from sqlalchemy import func, distinct
        
        # Get user ID if provided
        user_id = kwargs.get('user_id')
        
        # Get orchids with location data
        orchids_query = OrchidRecord.query.filter(
            OrchidRecord.region.isnot(None),
            OrchidRecord.region != 'Unknown',
            or_(OrchidRecord.image_url.isnot(None), OrchidRecord.google_drive_id.isnot(None))
        )
        
        # If user_id provided, prioritize user's collection
        if user_id:
            user_orchids = UserOrchidCollection.query.filter_by(
                user_id=user_id, is_active=True
            ).join(OrchidRecord).filter(
                OrchidRecord.region.isnot(None),
                or_(OrchidRecord.image_url.isnot(None), OrchidRecord.google_drive_id.isnot(None))
            ).all()
            
            if user_orchids:
                orchids = [uc.orchid for uc in user_orchids[:10]]
            else:
                orchids = orchids_query.limit(10).all()
        else:
            orchids = orchids_query.limit(20).all()
        
        # Get countries with orchid counts
        countries_with_orchids = db.session.query(
            OrchidRecord.region,
            func.count(OrchidRecord.id).label('orchid_count')
        ).filter(
            OrchidRecord.region.isnot(None),
            OrchidRecord.region != 'Unknown'
        ).group_by(OrchidRecord.region).all()
        
        # Country coordinate mapping (simplified - in real app would use geocoding API)
        country_coordinates = {
            'Colombia': {'lat': 4.5709, 'lng': -74.2973},
            'Ecuador': {'lat': -1.8312, 'lng': -78.1834},
            'Brazil': {'lat': -14.2350, 'lng': -51.9253},
            'Thailand': {'lat': 15.8700, 'lng': 100.9925},
            'Madagascar': {'lat': -18.7669, 'lng': 46.8691},
            'Philippines': {'lat': 12.8797, 'lng': 121.7740},
            'Peru': {'lat': -9.1900, 'lng': -75.0152},
            'Venezuela': {'lat': 6.4238, 'lng': -66.5897},
            'Malaysia': {'lat': 4.2105, 'lng': 101.9758},
            'Indonesia': {'lat': -0.7893, 'lng': 113.9213},
            'India': {'lat': 20.5937, 'lng': 78.9629},
            'Mexico': {'lat': 23.6345, 'lng': -102.5528}
        }
        
        # Prepare orchid data with enhanced metadata
        enhanced_orchids = []
        for orchid in orchids:
            # Get image URL (prioritize Google Drive)
            image_url = orchid.image_url
            if orchid.google_drive_id:
                image_url = f"/api/drive-photo/{orchid.google_drive_id}"
            
            enhanced_orchids.append({
                'id': orchid.id,
                'display_name': orchid.display_name or 'Unknown Orchid',
                'scientific_name': orchid.scientific_name,
                'image_url': image_url,
                'region': orchid.region,
                'climate_preference': orchid.climate_preference or 'intermediate',
                'temperature_range': orchid.temperature_range,
                'light_requirements': orchid.light_requirements,
                'growth_habit': orchid.growth_habit,
                'cultural_notes': orchid.cultural_notes,
                'country_coordinates': country_coordinates.get(orchid.region, None),
                'has_baker_data': bool(orchid.cultural_notes and 'BAKER' in orchid.cultural_notes.upper())
            })
        
        # Solar activity data (in real implementation, fetch from NOAA Space Weather API)
        solar_data = {
            'activity_level': 'Moderate',
            'sunspot_count': 45,
            'solar_flares': 'Low',
            'geomagnetic_activity': 'Quiet',
            'uv_index': 6,
            'solar_wind_speed': 350  # km/s
        }
        
        widget_data = {
            'widget_id': str(uuid.uuid4())[:8],
            'user_id': user_id,
            'orchids': enhanced_orchids,
            'countries_with_orchids': [
                {
                    'name': country.region,
                    'orchid_count': country.orchid_count,
                    'coordinates': country_coordinates.get(country.region, None)
                }
                for country in countries_with_orchids
                if country_coordinates.get(country.region)
            ],
            'solar_data': solar_data,
            'globe_config': {
                'auto_rotation_delay': 60000,  # 1 minute in milliseconds
                'rotation_speed': 1.0,
                'tilt_angle': 23.5,  # Earth's axial tilt
                'enable_day_night': True,
                'show_country_highlights': True,
                'enable_solar_activity': True
            },
            'interaction_data': {
                'total_countries': len(countries_with_orchids),
                'total_orchids': sum(c.orchid_count for c in countries_with_orchids),
                'featured_regions': ['Colombia', 'Ecuador', 'Thailand', 'Madagascar'],
                'climate_zones': ['Tropical', 'Subtropical', 'Temperate']
            }
        }
        
        return widget_data

# Initialize widget system
widget_system = OrchidWidgetSystem()

@widget_bp.route('/embed/<widget_type>')
def embed_widget(widget_type):
    """Generate embeddable widget HTML"""
    if widget_type not in widget_system.widget_types:
        return "Invalid widget type", 404
    
    # Get widget parameters from URL
    params = dict(request.args)
    
    # Get widget data
    widget_data = widget_system.get_widget_data(widget_type, **params)
    
    # Render widget template
    return render_template(
        f'widgets/{widget_type}_widget.html',
        widget_data=widget_data,
        params=params,
        widget_type=widget_type
    )

@widget_bp.route('/api/<widget_type>')
def widget_api(widget_type):
    """API endpoint for widget data"""
    params = dict(request.args)
    widget_data = widget_system.get_widget_data(widget_type, **params)
    
    return jsonify({
        'success': True,
        'widget_type': widget_type,
        'data': widget_data,
        'generated_at': datetime.now().isoformat()
    })

@widget_bp.route('/js/<widget_type>.js')
def widget_javascript(widget_type):
    """Generate JavaScript for specific widget"""
    js_content = render_template(f'widgets/{widget_type}_widget.js', widget_type=widget_type)
    
    return Response(
        js_content,
        mimetype='application/javascript',
        headers={'Cache-Control': 'no-cache'}
    )

@widget_bp.route('/css/widgets.css')
def widget_css():
    """Generate CSS for all widgets"""
    css_content = render_template('widgets/widgets.css')
    
    return Response(
        css_content,
        mimetype='text/css',
        headers={'Cache-Control': 'no-cache'}
    )

@widget_bp.route('/')
def widget_showcase():
    """Show all available widgets and integration code"""
    return render_template('widgets/showcase.html', 
                         widget_types=widget_system.widget_types)

@widget_bp.route('/integration/<widget_type>')
def widget_integration_code(widget_type):
    """Get integration code for specific widget"""
    if widget_type not in widget_system.widget_types:
        return "Invalid widget type", 404
    
    return render_template('widgets/integration.html',
                         widget_type=widget_type,
                         widget_name=widget_system.widget_types[widget_type])