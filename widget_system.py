"""
Orchid Continuum Widget System
Creates embeddable widgets for external website integration
"""

from flask import Blueprint, render_template, request, jsonify, Response
from models import OrchidRecord, db
from sqlalchemy import func, or_
import json
from datetime import datetime

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
            'featured': 'Featured Orchid Widget'
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