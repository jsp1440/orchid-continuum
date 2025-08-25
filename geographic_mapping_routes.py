#!/usr/bin/env python3
"""
Geographic Mapping Routes
========================
Flask routes for interactive orchid geographic mapping system
Part of The Orchid Continuum - Five Cities Orchid Society
"""

from flask import Blueprint, render_template, jsonify, request, Response
from simplified_orchid_mapping import simplified_mapper
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
geo_mapping_bp = Blueprint('geographic_mapping', __name__, url_prefix='/mapping')

@geo_mapping_bp.route('/')
def mapping_home():
    """Main geographic mapping interface"""
    return render_template('orchid_mapping.html')

@geo_mapping_bp.route('/world-map')
def world_map():
    """Interactive world map of orchid occurrences"""
    try:
        # Create working world map
        world_map_obj = simplified_mapper.create_working_world_map()
        
        # Get statistics
        stats = simplified_mapper.get_working_statistics()
        
        return render_template('world_orchid_map.html', 
                             map_html=world_map_obj._repr_html_(),
                             stats=stats,
                             orchid_limit=stats['orchids_with_regional_data'])
        
    except Exception as e:
        logger.error(f"❌ Error creating world map: {e}")
        return render_template('error.html', 
                             error="Failed to load world map",
                             details=str(e)), 500

@geo_mapping_bp.route('/genus-map/<genus>')
def genus_map(genus):
    """Map showing distribution of specific orchid genus"""
    try:
        mapper = OrchidGeographicMapper()
        genus_map_obj = mapper.create_genus_distribution_map(genus)
        
        return render_template('genus_map.html',
                             genus=genus,
                             map_html=genus_map_obj._repr_html_())
        
    except Exception as e:
        logger.error(f"❌ Error creating genus map for {genus}: {e}")
        return render_template('error.html', 
                             error=f"Failed to load map for genus {genus}",
                             details=str(e)), 500

@geo_mapping_bp.route('/api/coordinates')
def api_coordinates():
    """API endpoint for orchid coordinate data"""
    try:
        # Get regional coordinate data
        coordinates = simplified_mapper.get_regional_orchid_data()
        
        return jsonify({
            'success': True,
            'coordinates': coordinates,
            'total': len(coordinates),
            'type': 'regional_approximations'
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting coordinates: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@geo_mapping_bp.route('/api/statistics')
def api_statistics():
    """API endpoint for geographic statistics"""
    try:
        stats = simplified_mapper.get_working_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@geo_mapping_bp.route('/api/export/<format_type>')
def api_export(format_type):
    """API endpoint for exporting geographic data"""
    try:
        mapper = OrchidGeographicMapper()
        exported_data = mapper.export_geographic_data(format_type=format_type)
        
        if 'error' in exported_data:
            return jsonify({
                'success': False,
                'error': exported_data['error']
            }), 400
        
        if format_type == 'geojson':
            return Response(
                json.dumps(exported_data, indent=2),
                mimetype='application/geo+json',
                headers={'Content-Disposition': 'attachment; filename=orchid_occurrences.geojson'}
            )
        elif format_type == 'csv':
            # Convert to CSV response
            import csv
            import io
            
            output = io.StringIO()
            if exported_data['data']:
                fieldnames = exported_data['data'][0].keys()
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(exported_data['data'])
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=orchid_occurrences.csv'}
            )
        else:
            return jsonify(exported_data)
            
    except Exception as e:
        logger.error(f"❌ API error exporting {format_type}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@geo_mapping_bp.route('/api/genus/<genus>/coordinates')
def api_genus_coordinates(genus):
    """API endpoint for specific genus coordinates"""
    try:
        mapper = OrchidGeographicMapper()
        
        with mapper.app.app_context():
            from models import OrchidRecord
            orchids = OrchidRecord.query.filter(
                OrchidRecord.genus == genus,
                OrchidRecord.latitude.isnot(None),
                OrchidRecord.longitude.isnot(None)
            ).all()
            
            coordinates = []
            for orchid in orchids:
                coordinates.append({
                    'id': orchid.id,
                    'lat': float(orchid.latitude),
                    'lng': float(orchid.longitude),
                    'scientific_name': orchid.scientific_name or 'Unknown',
                    'species': orchid.species or 'Unknown',
                    'region': orchid.region or 'Unknown',
                    'habitat': orchid.native_habitat or 'Unknown'
                })
        
        return jsonify({
            'success': True,
            'genus': genus,
            'coordinates': coordinates,
            'total': len(coordinates)
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting coordinates for genus {genus}: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@geo_mapping_bp.route('/api/regions')
def api_regions():
    """API endpoint for available regions with orchid data"""
    try:
        mapper = OrchidGeographicMapper()
        
        with mapper.app.app_context():
            from models import OrchidRecord
            regions = mapper.db.session.query(
                OrchidRecord.region,
                mapper.db.func.count(OrchidRecord.id).label('count')
            ).filter(
                OrchidRecord.region.isnot(None),
                OrchidRecord.latitude.isnot(None)
            ).group_by(OrchidRecord.region).order_by(
                mapper.db.func.count(OrchidRecord.id).desc()
            ).all()
            
            region_data = [{'region': r.region, 'count': r.count} for r in regions]
        
        return jsonify({
            'success': True,
            'regions': region_data,
            'total_regions': len(region_data)
        })
        
    except Exception as e:
        logger.error(f"❌ API error getting regions: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@geo_mapping_bp.route('/help')
def mapping_help():
    """Help and documentation for geographic mapping"""
    return render_template('mapping_help.html')

@geo_mapping_bp.route('/dashboard')
def mapping_dashboard():
    """Geographic mapping dashboard with analytics"""
    try:
        mapper = OrchidGeographicMapper()
        stats = mapper.get_geographic_statistics()
        
        return render_template('mapping_dashboard.html', statistics=stats)
        
    except Exception as e:
        logger.error(f"❌ Error loading mapping dashboard: {e}")
        return render_template('error.html', 
                             error="Failed to load mapping dashboard",
                             details=str(e)), 500

# Register the blueprint routes
logger.info("🗺️ Geographic Mapping routes registered successfully")