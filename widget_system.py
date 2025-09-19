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
            'enhanced_globe': 'Enhanced Globe Weather Widget',
            'climate': 'Climate Habitat Comparator Widget',
            'trivia': 'Orchid Trivia Challenge Widget',
            'mahjong': 'Orchid Mahjong Game Widget',
            'orchid_explorer_pro': 'Orchid Explorer Pro - Geographic & Climate Suite',
            'discovery_center': 'Discovery Center - Search, Browse & Identify Hub',
            'learning_games': 'Learning Games - Multi-Game Educational Suite',
            'research_hub': 'Research Hub - Analysis & Citation Tools',
            'ecosystem_explorer': 'Ecosystem Explorer - Plant Species Lookup & Habitat Data'
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
        elif widget_type == 'climate':
            return self._get_climate_data(**kwargs)
        elif widget_type == 'trivia':
            return self._get_trivia_data(**kwargs)
        elif widget_type == 'mahjong':
            return self._get_mahjong_data(**kwargs)
        elif widget_type == 'orchid_explorer_pro':
            return self._get_orchid_explorer_pro_data(**kwargs)
        elif widget_type == 'discovery_center':
            return self._get_discovery_center_data(**kwargs)
        elif widget_type == 'learning_games':
            return self._get_learning_games_data(**kwargs)
        elif widget_type == 'research_hub':
            return self._get_research_hub_data(**kwargs)
        elif widget_type == 'ecosystem_explorer':
            return self._get_ecosystem_explorer_data(**kwargs)
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
    
    def _get_climate_data(self, orchid_id=None, mode="seasonal", user_lat=None, user_lon=None, **kwargs):
        """Get climate comparison data for widget"""
        # Get orchid habitat data
        orchid = None
        if orchid_id:
            orchid = OrchidRecord.query.get(orchid_id)
        
        if not orchid:
            # Get a featured or random orchid with location data
            orchid = OrchidRecord.query.filter(
                OrchidRecord.decimal_latitude.isnot(None),
                OrchidRecord.decimal_longitude.isnot(None)
            ).first()
        
        if not orchid:
            return {'error': 'No orchid with habitat location found'}
        
        # Default user location (San Francisco for demo)
        user_location = {
            'lat': float(user_lat) if user_lat else 37.7749,
            'lon': float(user_lon) if user_lon else -122.4194,
            'elev': 50  # meters
        }
        
        # Orchid habitat location
        habitat_location = {
            'lat': float(orchid.decimal_latitude),
            'lon': float(orchid.decimal_longitude), 
            'elev': 100  # Default elevation for now
        }
        
        # Check if this is a 35th parallel orchid
        orchid_near_35 = abs(habitat_location['lat']) >= 32 and abs(habitat_location['lat']) <= 38
        user_near_35 = abs(user_location['lat']) >= 32 and abs(user_location['lat']) <= 38
        
        return {
            'orchid': {
                'id': orchid.id,
                'display_name': orchid.display_name,
                'scientific_name': orchid.scientific_name,
                'image_url': orchid.image_url,
                'habitat_location': habitat_location
            },
            'user_location': user_location,
            'mode': mode,
            'parallel35_connection': orchid_near_35 or user_near_35,
            'both_near_35': orchid_near_35 and user_near_35,
            'comparison_modes': [
                {'id': 'calendar', 'name': 'Calendar (Raw)', 'description': 'Direct day-to-day comparison'},
                {'id': 'seasonal', 'name': 'Seasonal (Default)', 'description': 'Hemisphere-adjusted seasonal comparison'},
                {'id': 'photoperiod', 'name': 'Photoperiod', 'description': 'Solar time and daylight matched'},
                {'id': 'parallel35', 'name': '35th Parallel', 'description': 'Special mode for 35°N latitude orchids'}
            ]
        }
    
    def _get_trivia_data(self, **kwargs):
        """Get trivia game data for widget"""
        # Sample trivia questions from the orchid database
        sample_questions = [
            {
                "category": "Basic Knowledge",
                "difficulty": "easy",
                "question": "What is the most common orchid found in grocery stores?",
                "options": ["Phalaenopsis", "Cattleya", "Dendrobium", "Oncidium"],
                "correct": 0,
                "explanation": "Phalaenopsis, also called 'Moth Orchids', are the most popular orchids sold commercially.",
                "points": 10,
                "image": "images/phalaenopsis_moth_orchid.jpg"
            },
            {
                "category": "Colors",
                "difficulty": "easy", 
                "question": "Which color do orchids NOT naturally produce?",
                "options": ["Blue", "Purple", "White", "Yellow"],
                "correct": 0,
                "explanation": "True blue orchids don't exist naturally - blue orchids are typically dyed.",
                "points": 10,
                "image": "images/blue_orchid_dyed.jpg"
            },
            {
                "category": "Growing",
                "difficulty": "easy",
                "question": "What do most orchids grow on in nature?",
                "options": ["Soil", "Trees", "Rocks", "Water"],
                "correct": 1,
                "explanation": "Most orchids are epiphytes, meaning they grow on trees and get nutrients from the air and rain.",
                "points": 10,
                "image": "images/epiphyte_orchid_tree.jpg"
            },
            {
                "category": "Anatomy",
                "difficulty": "medium",
                "question": "What is the specialized lip petal of an orchid called?",
                "options": ["Labellum", "Column", "Pollinia", "Sepals"],
                "correct": 0,
                "explanation": "The labellum is the modified lip petal that often serves as a landing platform for pollinators.",
                "points": 20,
                "image": "images/orchid_labellum_anatomy.jpg"
            },
            {
                "category": "Biology",
                "difficulty": "medium",
                "question": "What are keikis in orchid growing?",
                "options": ["Diseases", "Baby plants", "Fertilizers", "Pot types"],
                "correct": 1,
                "explanation": "Keiki is Hawaiian for 'baby' - these are small plantlets that grow on the mother plant.",
                "points": 20,
                "image": "images/orchid_keiki_baby.jpg"
            }
        ]
        return {'questions': sample_questions}
    
    def _get_mahjong_data(self, **kwargs):
        """Get Mahjong game data for widget"""
        # Generate orchid-themed mahjong tiles
        orchid_tiles = [
            # Cattleya suit (purple theme)
            {'id': 'cattleya_1', 'suit': 'cattleya', 'number': 1, 'symbol': '🌺', 'color': '#9B59B6', 'name': 'Cattleya trianae'},
            {'id': 'cattleya_2', 'suit': 'cattleya', 'number': 2, 'symbol': '🌺', 'color': '#9B59B6', 'name': 'Cattleya mossiae'},
            {'id': 'cattleya_3', 'suit': 'cattleya', 'number': 3, 'symbol': '🌺', 'color': '#9B59B6', 'name': 'Cattleya warscewiczii'},
            {'id': 'cattleya_4', 'suit': 'cattleya', 'number': 4, 'symbol': '🌺', 'color': '#9B59B6', 'name': 'Cattleya maxima'},
            
            # Dendrobium suit (blue theme)
            {'id': 'dendrobium_1', 'suit': 'dendrobium', 'number': 1, 'symbol': '💐', 'color': '#3498DB', 'name': 'Dendrobium nobile'},
            {'id': 'dendrobium_2', 'suit': 'dendrobium', 'number': 2, 'symbol': '💐', 'color': '#3498DB', 'name': 'Dendrobium kingianum'},
            {'id': 'dendrobium_3', 'suit': 'dendrobium', 'number': 3, 'symbol': '💐', 'color': '#3498DB', 'name': 'Dendrobium phalaenopsis'},
            {'id': 'dendrobium_4', 'suit': 'dendrobium', 'number': 4, 'symbol': '💐', 'color': '#3498DB', 'name': 'Dendrobium spectabile'},
            
            # Phalaenopsis suit (pink theme)
            {'id': 'phalaenopsis_1', 'suit': 'phalaenopsis', 'number': 1, 'symbol': '🦋', 'color': '#E91E63', 'name': 'Phalaenopsis amabilis'},
            {'id': 'phalaenopsis_2', 'suit': 'phalaenopsis', 'number': 2, 'symbol': '🦋', 'color': '#E91E63', 'name': 'Phalaenopsis schilleriana'},
            {'id': 'phalaenopsis_3', 'suit': 'phalaenopsis', 'number': 3, 'symbol': '🦋', 'color': '#E91E63', 'name': 'Phalaenopsis stuartiana'},
            {'id': 'phalaenopsis_4', 'suit': 'phalaenopsis', 'number': 4, 'symbol': '🦋', 'color': '#E91E63', 'name': 'Phalaenopsis aphrodite'},
            
            # Honor tiles (AOS Awards)
            {'id': 'am_aos', 'suit': 'honors', 'type': 'AM/AOS', 'symbol': '🏆', 'color': '#F39C12', 'name': 'Award of Merit'},
            {'id': 'fcc_aos', 'suit': 'honors', 'type': 'FCC/AOS', 'symbol': '🥇', 'color': '#E74C3C', 'name': 'First Class Certificate'},
            {'id': 'hcc_aos', 'suit': 'honors', 'type': 'HCC/AOS', 'symbol': '🎖️', 'color': '#27AE60', 'name': 'Highly Commended Certificate'},
            {'id': 'cbr_aos', 'suit': 'honors', 'type': 'CBR/AOS', 'symbol': '📜', 'color': '#8E44AD', 'name': 'Certificate of Botanical Recognition'},
            
            # Dragon tiles (Growing Conditions)
            {'id': 'temp_dragon', 'suit': 'dragons', 'type': 'Temperature', 'symbol': '🌡️', 'color': '#E67E22', 'name': 'Temperature Control'},
            {'id': 'light_dragon', 'suit': 'dragons', 'type': 'Light', 'symbol': '☀️', 'color': '#F1C40F', 'name': 'Light Requirements'},
            {'id': 'water_dragon', 'suit': 'dragons', 'type': 'Water', 'symbol': '💧', 'color': '#3498DB', 'name': 'Watering Schedule'}
        ]
        return {'tiles': orchid_tiles}
    
    def _get_orchid_explorer_pro_data(self, **kwargs):
        """Get combined geographic and climate data"""
        return {
            'globe_data': {'countries': [], 'hotspots': []},
            'weather_data': {'location': 'Unknown', 'climate': 'Temperate'},
            'climate_zones': []
        }
    
    def _get_discovery_center_data(self, **kwargs):
        """Get combined search, gallery, and identification data"""
        return {
            'featured_orchid': {'name': 'Cattleya trianae', 'country': 'Colombia'},
            'recent_searches': [],
            'gallery_items': [],
            'stats': {'total': 247, 'genera': 42, 'species': 189}
        }
    
    def _get_learning_games_data(self, **kwargs):
        """Get combined gaming data"""
        return {
            'trivia_questions': [],
            'mahjong_tiles': [],
            'memory_cards': [],
            'quiz_data': []
        }
    
    def _get_research_hub_data(self, **kwargs):
        """Get combined research and citation data"""
        return {
            'comparison_tools': [],
            'citation_formats': ['APA', 'MLA', 'Chicago', 'BibTeX'],
            'analysis_data': {'specimens': 247, 'diversity_index': 3.47},
            'export_options': ['CSV', 'JSON', 'PDF', 'LaTeX']
        }

    def _get_ecosystem_explorer_data(self, **kwargs):
        """Get data for ecosystem explorer widget"""
        try:
            total_orchids = OrchidRecord.query.count()
            
            # Get sample orchids with diverse genera for suggestions
            sample_orchids = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.isnot(None),
                OrchidRecord.validation_status != 'rejected'
            ).distinct(OrchidRecord.genus).limit(20).all()
            
            # Build suggested species list
            suggestions = []
            for orchid in sample_orchids:
                if orchid.scientific_name:
                    suggestions.append({
                        'id': orchid.id,
                        'scientific_name': orchid.scientific_name,
                        'display_name': orchid.display_name,
                        'genus': orchid.genus,
                        'species': orchid.species
                    })
            
            return {
                'title': 'Ecosystem Explorer - Botanical Research & Habitat Analysis',
                'orchid_count': total_orchids,
                'suggested_species': suggestions,
                'trefle_enabled': True,  # This will be determined by the Trefle service
                'widget_id': kwargs.get('widget_id', 'ecosystem-explorer'),
                'search_examples': [
                    'Phalaenopsis amabilis',
                    'Dendrobium nobile', 
                    'Cattleya labiata',
                    'Vanda coerulea',
                    'Oncidium flexuosum'
                ]
            }
        except Exception as e:
            return {'error': f"Error getting ecosystem explorer data: {str(e)}"}

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