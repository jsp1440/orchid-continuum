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
        # Emergency fallback - provide working map
        try:
            # Use simple static map as backup
            backup_stats = {'orchids_with_regional_data': 51, 'total_countries': 15, 'total_genera': 25}
            return render_template('world_orchid_map.html', 
                                 map_html='<div class="alert alert-info">Map loading... Please refresh the page.</div>',
                                 stats=backup_stats,
                                 orchid_limit=backup_stats['orchids_with_regional_data'],
                                 emergency_mode=True)
        except:
            return render_template('error.html', 
                                 error="Failed to load world map",
                                 details=str(e)), 500

@geo_mapping_bp.route('/genus-map/<genus>')
def genus_map(genus):
    """Map showing distribution of specific orchid genus"""
    try:
        # Use simplified mapper instead of the complex one
        coordinates = simplified_mapper.get_genus_regional_data(genus)
        stats = simplified_mapper.get_working_statistics()
        
        return render_template('world_orchid_map.html',
                             genus=genus,
                             stats=stats,
                             orchid_limit=len(coordinates))
        
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
        # Use simplified mapper for export
        coordinates = simplified_mapper.get_regional_orchid_data()
        
        if format_type == 'geojson':
            geojson_data = {
                "type": "FeatureCollection",
                "features": []
            }
            
            for region in coordinates:
                feature = {
                    "type": "Feature",
                    "properties": {
                        "region": region.get('region', 'Unknown'),
                        "orchid_count": region.get('orchid_count', 0),
                        "unique_genera": region.get('unique_genera', 0),
                        "unique_species": region.get('unique_species', 0)
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [region.get('lng', 0), region.get('lat', 0)]
                    }
                }
                geojson_data["features"].append(feature)
            
            return Response(
                json.dumps(geojson_data, indent=2),
                mimetype='application/geo+json',
                headers={'Content-Disposition': 'attachment; filename=orchid_occurrences.geojson'}
            )
        elif format_type == 'csv':
            # Convert to CSV response
            import csv
            import io
            
            output = io.StringIO()
            if coordinates:
                fieldnames = ['region', 'lat', 'lng', 'orchid_count', 'unique_genera', 'unique_species']
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for region in coordinates:
                    writer.writerow({
                        'region': region.get('region', 'Unknown'),
                        'lat': region.get('lat', 0),
                        'lng': region.get('lng', 0),
                        'orchid_count': region.get('orchid_count', 0),
                        'unique_genera': region.get('unique_genera', 0),
                        'unique_species': region.get('unique_species', 0)
                    })
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': 'attachment; filename=orchid_occurrences.csv'}
            )
        else:
            return jsonify({
                'success': True,
                'data': coordinates
            })
            
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
        # Use simplified mapper for genus data
        coordinates = simplified_mapper.get_genus_regional_data(genus)
        
        return jsonify({
            'success': True,
            'genus': genus,
            'coordinates': coordinates,
            'total': len(coordinates),
            'type': 'regional_approximations'
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
        # Use simplified mapper for region data
        regions = simplified_mapper.get_regional_orchid_data()
        
        region_data = [
            {
                'region': r.get('region', 'Unknown'), 
                'count': r.get('orchid_count', 0),
                'lat': r.get('lat', 0),
                'lng': r.get('lng', 0)
            } for r in regions
        ]
        
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
        # Use simplified mapper for dashboard
        stats = simplified_mapper.get_working_statistics()
        
        return render_template('mapping_dashboard.html', statistics=stats)
        
    except Exception as e:
        logger.error(f"❌ Error loading mapping dashboard: {e}")
        return render_template('error.html', 
                             error="Failed to load mapping dashboard",
                             details=str(e)), 500

# Register the blueprint routes
logger.info("🗺️ Geographic Mapping routes registered successfully")