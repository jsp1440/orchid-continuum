from flask import Blueprint, render_template, jsonify, request
from models import OrchidRecord
from app import db
import requests
import time
import logging

# Create blueprint
mycorrhizal_map_bp = Blueprint('mycorrhizal_map', __name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@mycorrhizal_map_bp.route('/orchid-mycorrhizal-map')
def orchid_mycorrhizal_map():
    """Display the interactive orchid-mycorrhizal fungi map"""
    return render_template('orchid_mycorrhizal_map.html')

@mycorrhizal_map_bp.route('/api/orchid-locations')
def api_orchid_locations():
    """API endpoint to get orchid locations for mapping"""
    try:
        # Get orchids with coordinates
        orchids = db.session.query(OrchidRecord).filter(
            OrchidRecord.decimal_latitude.isnot(None),
            OrchidRecord.decimal_longitude.isnot(None)
        ).all()
        
        orchid_data = []
        for orchid in orchids:
            orchid_data.append({
                'id': orchid.id,
                'scientific_name': orchid.scientific_name,
                'genus': orchid.genus,
                'species': orchid.species,
                'decimal_latitude': float(orchid.decimal_latitude) if orchid.decimal_latitude else None,
                'decimal_longitude': float(orchid.decimal_longitude) if orchid.decimal_longitude else None,
                'country': orchid.country,
                'data_source': orchid.data_source,
                'habitat': orchid.habitat,
                'image_url': orchid.image_url
            })
        
        return jsonify(orchid_data)
        
    except Exception as e:
        logger.error(f"Error fetching orchid locations: {e}")
        return jsonify({'error': 'Failed to fetch orchid locations'}), 500

@mycorrhizal_map_bp.route('/api/fungi-locations')
def api_fungi_locations():
    """API endpoint to get mycorrhizal fungi locations from GBIF"""
    try:
        # Get query parameters
        limit = request.args.get('limit', 50, type=int)
        genera = request.args.get('genera', 'Rhizoctonia,Tulasnella,Ceratobasidium,Sebacina').split(',')
        
        all_fungi = []
        
        for genus in genera[:3]:  # Limit to 3 genera to avoid timeout
            try:
                # Query GBIF for this fungal genus
                gbif_url = 'https://api.gbif.org/v1/occurrence/search'
                params = {
                    'genus': genus.strip(),
                    'kingdom': 'Fungi',
                    'hasCoordinate': 'true',
                    'limit': min(limit // len(genera), 20),
                    'offset': 0
                }
                
                response = requests.get(gbif_url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                for occurrence in data.get('results', []):
                    # Validate it's actually a fungus
                    if occurrence.get('kingdom') != 'Fungi':
                        continue
                        
                    lat = occurrence.get('decimalLatitude')
                    lng = occurrence.get('decimalLongitude')
                    
                    if not lat or not lng:
                        continue
                        
                    # Look for orchid association indicators
                    habitat = occurrence.get('habitat', '').lower()
                    locality = occurrence.get('locality', '').lower()
                    recorded_by = occurrence.get('recordedBy', '').lower()
                    
                    orchid_associated = any(keyword in f"{habitat} {locality} {recorded_by}" 
                                         for keyword in ['orchid', 'mycorrhiz', 'symbio', 'root'])
                    
                    fungi_record = {
                        'scientific_name': occurrence.get('scientificName', ''),
                        'genus': occurrence.get('genus', ''),
                        'species': occurrence.get('specificEpithet', ''),
                        'decimal_latitude': float(lat),
                        'decimal_longitude': float(lng),
                        'country': occurrence.get('country', ''),
                        'habitat': occurrence.get('habitat', ''),
                        'locality': occurrence.get('locality', ''),
                        'collector': occurrence.get('recordedBy', ''),
                        'gbif_id': occurrence.get('gbifID'),
                        'basis_of_record': occurrence.get('basisOfRecord', ''),
                        'orchid_associated': orchid_associated,
                        'data_source': 'GBIF'
                    }
                    
                    all_fungi.append(fungi_record)
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as genus_error:
                logger.warning(f"Error fetching {genus}: {genus_error}")
                continue
        
        logger.info(f"Retrieved {len(all_fungi)} fungi records")
        return jsonify(all_fungi[:limit])  # Return up to limit
        
    except Exception as e:
        logger.error(f"Error fetching fungi locations: {e}")
        return jsonify({'error': 'Failed to fetch fungi locations'}), 500

@mycorrhizal_map_bp.route('/api/symbiotic-analysis')
def api_symbiotic_analysis():
    """Analyze potential symbiotic relationships between orchids and fungi"""
    try:
        max_distance = request.args.get('max_distance', 50, type=float)  # km
        
        # Get orchid locations
        orchids = db.session.query(OrchidRecord).filter(
            OrchidRecord.decimal_latitude.isnot(None),
            OrchidRecord.decimal_longitude.isnot(None)
        ).all()
        
        # This would ideally get fungi from a fungi table or GBIF API
        # For now, return analysis structure
        
        analysis = {
            'total_orchids': len(orchids),
            'total_fungi': 0,  # Would be populated from fungi data
            'potential_relationships': [],
            'geographic_clusters': [],
            'distance_threshold': max_distance
        }
        
        # Add sample geographic clusters
        clusters = [
            {
                'region': 'California',
                'orchid_count': len([o for o in orchids if o.country == 'United States of America']),
                'common_genera': ['Cypripedium', 'Platanthera'],
                'fungi_genera': ['Rhizoctonia', 'Tulasnella'],
                'center_lat': 36.7783,
                'center_lng': -119.4179
            },
            {
                'region': 'Australia',
                'orchid_count': len([o for o in orchids if o.country == 'Australia']),
                'common_genera': ['Caladenia', 'Diuris'],
                'fungi_genera': ['Ceratobasidium', 'Tulasnella'],
                'center_lat': -25.2744,
                'center_lng': 133.7751
            }
        ]
        
        analysis['geographic_clusters'] = [c for c in clusters if c['orchid_count'] > 0]
        
        return jsonify(analysis)
        
    except Exception as e:
        logger.error(f"Error in symbiotic analysis: {e}")
        return jsonify({'error': 'Failed to analyze symbiotic relationships'}), 500

@mycorrhizal_map_bp.route('/api/fungi-genera-info')
def api_fungi_genera_info():
    """Get information about orchid-associated fungi genera"""
    
    fungi_info = {
        'Rhizoctonia': {
            'description': 'Most common orchid mycorrhizal fungi, essential for seed germination',
            'orchid_associations': ['Cypripedium', 'Orchis', 'Ophrys'],
            'habitat': 'Soil-dwelling, forms basidiospores',
            'importance': 'Critical for orchid seed germination and early development'
        },
        'Tulasnella': {
            'description': 'Important orchid symbionts, especially for terrestrial orchids',
            'orchid_associations': ['Spiranthes', 'Goodyera', 'Platanthera'],
            'habitat': 'Forest soils, decaying organic matter',
            'importance': 'Provides nutrients and water to adult orchids'
        },
        'Ceratobasidium': {
            'description': 'Anamorph stage of Thanatephorus, common epiphytic orchid symbiont',
            'orchid_associations': ['Dendrobium', 'Epidendrum', 'Oncidium'],
            'habitat': 'Tree bark, epiphytic environments',
            'importance': 'Essential for tropical epiphytic orchid survival'
        },
        'Sebacina': {
            'description': 'Sebacinoid fungi forming ectomycorrhizal relationships',
            'orchid_associations': ['Neottia', 'Corallorhiza'],
            'habitat': 'Forest ecosystems, associated with tree roots',
            'importance': 'Bridge between orchids and tree mycorrhizal networks'
        },
        'Waitea': {
            'description': 'Specialized orchid mycorrhizal fungi',
            'orchid_associations': ['Vanilla', 'Gastrodia'],
            'habitat': 'Tropical and subtropical regions',
            'importance': 'Important for rare and endangered orchid species'
        }
    }
    
    return jsonify(fungi_info)

# Register error handlers
@mycorrhizal_map_bp.errorhandler(404)
def not_found_error(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@mycorrhizal_map_bp.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500