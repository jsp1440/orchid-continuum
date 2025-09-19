#!/usr/bin/env python3
"""
Orchid Geographic Mapping System
===============================
Interactive world maps showing orchid distribution and occurrence patterns
Part of The Orchid Continuum - Five Cities Orchid Society

Features:
- Interactive world maps with orchid occurrence points
- Species density heat maps and clustering
- Geographic filtering by region, country, genus
- Distribution pattern analysis
- GBIF data integration with 35,000+ specimens
"""

import folium
import json
import pandas as pd
from folium.plugins import MarkerCluster, HeatMap
from flask import Flask, jsonify, render_template
from app import app, db
from models import OrchidRecord
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrchidGeographicMapper:
    """
    Geographic mapping system for orchid distribution visualization
    """
    
    def __init__(self):
        self.default_center = [20.0, 0.0]  # World center
        self.default_zoom = 2
        
        logger.info("🗺️ Orchid Geographic Mapping system initialized")
    
    def get_orchid_coordinates(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get orchid coordinates from database for mapping
        
        Args:
            limit: Optional limit on number of records
            
        Returns:
            List of orchid coordinate data
        """
        try:
            with app.app_context():
                query = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None)
                )
                
                if limit:
                    query = query.limit(limit)
                
                orchids = query.all()
                
                coordinates = []
                for orchid in orchids:
                    if orchid.latitude and orchid.longitude:
                        coordinates.append({
                            'id': orchid.id,
                            'lat': float(orchid.latitude),
                            'lng': float(orchid.longitude),
                            'scientific_name': orchid.scientific_name or 'Unknown',
                            'genus': orchid.genus or 'Unknown',
                            'species': orchid.species or 'Unknown',
                            'region': orchid.region or 'Unknown',
                            'native_habitat': orchid.native_habitat or 'Unknown',
                            'ingestion_source': orchid.ingestion_source or 'Unknown',
                            'display_name': orchid.display_name or orchid.scientific_name
                        })
                
                logger.info(f"📍 Retrieved {len(coordinates)} orchid coordinates for mapping")
                return coordinates
                
        except Exception as e:
            logger.error(f"❌ Error retrieving orchid coordinates: {e}")
            return []
    
    def create_interactive_world_map(self, orchid_limit: Optional[int] = 1000) -> folium.Map:
        """
        Create interactive world map with orchid occurrence points
        
        Args:
            orchid_limit: Limit number of orchids for performance
            
        Returns:
            Folium map object with orchid data
        """
        try:
            # Get orchid coordinates
            coordinates = self.get_orchid_coordinates(limit=orchid_limit)
            
            # Create base map
            world_map = folium.Map(
                location=self.default_center,
                zoom_start=self.default_zoom,
                tiles='OpenStreetMap',
                control_scale=True
            )
            
            # Add custom tile layers
            folium.TileLayer(
                'CartoDB Positron',
                name='Light Theme',
                control=True
            ).add_to(world_map)
            
            folium.TileLayer(
                'CartoDB Dark_Matter',
                name='Dark Theme',
                control=True
            ).add_to(world_map)
            
            if coordinates:
                # Create marker cluster for performance
                marker_cluster = MarkerCluster(
                    name="Orchid Occurrences",
                    overlay=True,
                    control=True
                ).add_to(world_map)
                
                # Add orchid markers
                for coord in coordinates:
                    popup_html = f"""
                    <div style="width: 250px;">
                        <h5 style="color: #2E7D32; font-weight: bold;">{coord['scientific_name']}</h5>
                        <p><strong>Genus:</strong> {coord['genus']}<br>
                           <strong>Species:</strong> {coord['species']}<br>
                           <strong>Region:</strong> {coord['region']}<br>
                           <strong>Habitat:</strong> {coord['native_habitat']}<br>
                           <strong>Source:</strong> {coord['ingestion_source']}</p>
                        <p><small>ID: {coord['id']}</small></p>
                    </div>
                    """
                    
                    folium.Marker(
                        location=[coord['lat'], coord['lng']],
                        popup=folium.Popup(popup_html, max_width=300),
                        tooltip=coord['scientific_name'],
                        icon=folium.Icon(
                            icon='leaf',
                            prefix='fa',
                            color='green'
                        )
                    ).add_to(marker_cluster)
                
                # Add heat map layer
                heat_data = [[coord['lat'], coord['lng']] for coord in coordinates]
                HeatMap(
                    heat_data,
                    name='Species Density Heat Map',
                    overlay=True,
                    control=True,
                    radius=15,
                    blur=10
                ).add_to(world_map)
                
                logger.info(f"🌍 Created world map with {len(coordinates)} orchid occurrences")
            
            # Add layer control
            folium.LayerControl().add_to(world_map)
            
            return world_map
            
        except Exception as e:
            logger.error(f"❌ Error creating world map: {e}")
            # Return basic map on error
            return folium.Map(location=self.default_center, zoom_start=self.default_zoom)
    
    def create_genus_distribution_map(self, genus: str) -> folium.Map:
        """
        Create map showing distribution of a specific genus
        
        Args:
            genus: Orchid genus to map
            
        Returns:
            Folium map focused on genus distribution
        """
        try:
            with app.app_context():
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.genus == genus,
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None)
                ).all()
                
                if not orchids:
                    logger.warning(f"⚠️ No coordinates found for genus: {genus}")
                    return folium.Map(location=self.default_center, zoom_start=self.default_zoom)
                
                coordinates = []
                for orchid in orchids:
                    coordinates.append({
                        'lat': float(orchid.latitude),
                        'lng': float(orchid.longitude),
                        'scientific_name': orchid.scientific_name or 'Unknown',
                        'region': orchid.region or 'Unknown',
                        'habitat': orchid.native_habitat or 'Unknown'
                    })
                
                # Calculate map center based on coordinates
                avg_lat = sum(c['lat'] for c in coordinates) / len(coordinates)
                avg_lng = sum(c['lng'] for c in coordinates) / len(coordinates)
                
                # Create genus-focused map
                genus_map = folium.Map(
                    location=[avg_lat, avg_lng],
                    zoom_start=5,
                    tiles='OpenStreetMap'
                )
                
                # Add genus markers
                for coord in coordinates:
                    folium.CircleMarker(
                        location=[coord['lat'], coord['lng']],
                        radius=8,
                        popup=f"""
                        <b>{coord['scientific_name']}</b><br>
                        Region: {coord['region']}<br>
                        Habitat: {coord['habitat']}
                        """,
                        color='purple',
                        fill=True,
                        fillColor='purple',
                        fillOpacity=0.6
                    ).add_to(genus_map)
                
                logger.info(f"🌸 Created genus map for {genus} with {len(coordinates)} occurrences")
                return genus_map
                
        except Exception as e:
            logger.error(f"❌ Error creating genus map for {genus}: {e}")
            return folium.Map(location=self.default_center, zoom_start=self.default_zoom)
    
    def get_geographic_statistics(self) -> Dict[str, Any]:
        """
        Get geographic distribution statistics
        
        Returns:
            Dictionary with geographic statistics
        """
        try:
            with app.app_context():
                stats = {}
                
                # Total orchids with coordinates
                total_with_coords = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None)
                ).count()
                
                # Total orchids
                total_orchids = OrchidRecord.query.count()
                
                # Top regions
                region_counts = db.session.query(
                    OrchidRecord.region,
                    db.func.count(OrchidRecord.id).label('count')
                ).filter(
                    OrchidRecord.region.isnot(None),
                    OrchidRecord.latitude.isnot(None)
                ).group_by(OrchidRecord.region).order_by(
                    db.func.count(OrchidRecord.id).desc()
                ).limit(10).all()
                
                # Top genera by geographic spread
                genus_counts = db.session.query(
                    OrchidRecord.genus,
                    db.func.count(OrchidRecord.id).label('count')
                ).filter(
                    OrchidRecord.genus.isnot(None),
                    OrchidRecord.latitude.isnot(None)
                ).group_by(OrchidRecord.genus).order_by(
                    db.func.count(OrchidRecord.id).desc()
                ).limit(10).all()
                
                stats = {
                    'total_orchids': total_orchids,
                    'with_coordinates': total_with_coords,
                    'coordinate_coverage': round((total_with_coords / total_orchids) * 100, 1) if total_orchids > 0 else 0,
                    'top_regions': [{'region': r.region, 'count': r.count} for r in region_counts],
                    'top_genera': [{'genus': g.genus, 'count': g.count} for g in genus_counts],
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
                logger.info(f"📊 Geographic statistics: {total_with_coords} orchids with coordinates ({stats['coordinate_coverage']}% coverage)")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error getting geographic statistics: {e}")
            return {
                'total_orchids': 0,
                'with_coordinates': 0,
                'coordinate_coverage': 0,
                'error': str(e)
            }
    
    def export_geographic_data(self, format_type: str = 'geojson') -> Dict[str, Any]:
        """
        Export orchid geographic data in various formats
        
        Args:
            format_type: Export format ('geojson', 'csv', 'kml')
            
        Returns:
            Exported data in requested format
        """
        try:
            coordinates = self.get_orchid_coordinates()
            
            if format_type == 'geojson':
                features = []
                for coord in coordinates:
                    feature = {
                        "type": "Feature",
                        "geometry": {
                            "type": "Point",
                            "coordinates": [coord['lng'], coord['lat']]
                        },
                        "properties": {
                            "id": coord['id'],
                            "scientific_name": coord['scientific_name'],
                            "genus": coord['genus'],
                            "species": coord['species'],
                            "region": coord['region'],
                            "habitat": coord['native_habitat'],
                            "source": coord['ingestion_source']
                        }
                    }
                    features.append(feature)
                
                geojson_data = {
                    "type": "FeatureCollection",
                    "features": features,
                    "metadata": {
                        "total_features": len(features),
                        "export_timestamp": datetime.now().isoformat(),
                        "source": "The Orchid Continuum - Five Cities Orchid Society"
                    }
                }
                
                logger.info(f"📁 Exported {len(features)} orchids as GeoJSON")
                return geojson_data
                
            elif format_type == 'csv':
                # Convert to CSV-friendly format
                csv_data = []
                for coord in coordinates:
                    csv_data.append({
                        'id': coord['id'],
                        'scientific_name': coord['scientific_name'],
                        'genus': coord['genus'],
                        'species': coord['species'],
                        'latitude': coord['lat'],
                        'longitude': coord['lng'],
                        'region': coord['region'],
                        'habitat': coord['native_habitat'],
                        'source': coord['ingestion_source']
                    })
                
                logger.info(f"📄 Exported {len(csv_data)} orchids as CSV data")
                return {'data': csv_data, 'format': 'csv'}
                
            else:
                logger.warning(f"⚠️ Unsupported export format: {format_type}")
                return {'error': f'Unsupported format: {format_type}'}
                
        except Exception as e:
            logger.error(f"❌ Error exporting geographic data: {e}")
            return {'error': str(e)}

def create_world_orchid_map(limit: int = 1000) -> str:
    """
    Create world orchid map and return HTML
    
    Args:
        limit: Maximum orchids to display
        
    Returns:
        HTML string of the map
    """
    mapper = OrchidGeographicMapper()
    world_map = mapper.create_interactive_world_map(orchid_limit=limit)
    return world_map._repr_html_()

def get_orchid_geographic_data() -> Dict[str, Any]:
    """
    Get orchid geographic data for API endpoints
    
    Returns:
        Geographic data and statistics
    """
    mapper = OrchidGeographicMapper()
    coordinates = mapper.get_orchid_coordinates(limit=500)  # Limit for API performance
    stats = mapper.get_geographic_statistics()
    
    return {
        'coordinates': coordinates,
        'statistics': stats,
        'total_mapped': len(coordinates)
    }

if __name__ == "__main__":
    # Test the mapping system
    with app.app_context():
        mapper = OrchidGeographicMapper()
        
        print("🗺️ Testing Orchid Geographic Mapping System")
        print("=" * 50)
        
        # Test statistics
        stats = mapper.get_geographic_statistics()
        print(f"📊 Total orchids: {stats['total_orchids']}")
        print(f"📍 With coordinates: {stats['with_coordinates']}")
        print(f"📈 Coverage: {stats['coordinate_coverage']}%")
        
        # Test coordinate retrieval
        coordinates = mapper.get_orchid_coordinates(limit=10)
        print(f"🌍 Sample coordinates: {len(coordinates)}")
        
        if coordinates:
            print(f"📍 First orchid: {coordinates[0]['scientific_name']} at ({coordinates[0]['lat']}, {coordinates[0]['lng']})")
        
        print("✅ Geographic mapping system test complete")