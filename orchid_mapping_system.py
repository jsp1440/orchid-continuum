#!/usr/bin/env python3
"""
Advanced Orchid Mapping System with Topological Data
Creates interactive maps showing orchid distributions, species density, and biogeographic patterns
"""

import folium
import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Point
import json
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

from models import OrchidRecord, db
from app import app

logger = logging.getLogger(__name__)

class OrchidMappingSystem:
    """Advanced mapping system for orchid geographic and thematic data"""
    
    def __init__(self):
        self.world_bounds = {
            'min_lat': -60,
            'max_lat': 80,
            'min_lon': -180,
            'max_lon': 180
        }
        
        # Biogeographic regions for orchids
        self.orchid_regions = {
            'Neotropics': {
                'bounds': [(-60, -120), (25, -30)],
                'color': '#FF6B6B',
                'description': 'Central and South America - highest orchid diversity'
            },
            'Southeast Asia': {
                'bounds': [(-10, 90), (30, 150)],
                'color': '#4ECDC4', 
                'description': 'Malaysia, Indonesia, Philippines - epiphyte haven'
            },
            'Madagascar & Africa': {
                'bounds': [(-35, 10), (20, 55)],
                'color': '#45B7D1',
                'description': 'Endemic species and unique adaptations'
            },
            'North America': {
                'bounds': [(25, -125), (70, -65)],
                'color': '#96CEB4',
                'description': 'Temperate orchids and prairies'
            },
            'Europe & Mediterranean': {
                'bounds': [(35, -10), (70, 45)],
                'color': '#FECA57',
                'description': 'Terrestrial orchids and alpine species'
            },
            'Oceania': {
                'bounds': [(-50, 110), (-10, 180)],
                'color': '#FF9FF3',
                'description': 'Australia, New Zealand - unique genera'
            }
        }
        
    def create_world_orchid_map(self) -> folium.Map:
        """Create comprehensive world map of orchid distributions"""
        
        # Center map on global view
        world_map = folium.Map(
            location=[20, 0],
            zoom_start=2,
            tiles='OpenStreetMap',
            attr='Orchid Continuum Mapping System'
        )
        
        # Add topographical basemap option
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Physical_Map/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Physical Map',
            name='Topographical',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        # Add satellite imagery option
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Imagery',
            name='Satellite',
            overlay=False,
            control=True
        ).add_to(world_map)
        
        return world_map
    
    def add_biogeographic_regions(self, map_obj: folium.Map):
        """Add orchid biogeographic regions to map"""
        
        for region_name, region_data in self.orchid_regions.items():
            bounds = region_data['bounds']
            
            # Create rectangle for region
            folium.Rectangle(
                bounds=bounds,
                popup=folium.Popup(
                    f"""
                    <h5>{region_name}</h5>
                    <p>{region_data['description']}</p>
                    <small>Major orchid biogeographic region</small>
                    """,
                    max_width=300
                ),
                tooltip=f"{region_name} - {region_data['description'][:50]}...",
                color=region_data['color'],
                weight=2,
                opacity=0.8,
                fillOpacity=0.1
            ).add_to(map_obj)
    
    def get_orchid_coordinates(self) -> List[Dict]:
        """Extract orchid location data from database"""
        orchid_locations = []
        
        with app.app_context():
            try:
                # Get orchids with geographic data
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.region.isnot(None)
                ).all()
                
                # Regional coordinate mappings (approximate centers)
                region_coords = {
                    'south america': (-15.0, -60.0),
                    'central america': (10.0, -85.0),
                    'north america': (45.0, -100.0),
                    'southeast asia': (0.0, 110.0),
                    'asia': (30.0, 100.0),
                    'africa': (0.0, 20.0),
                    'madagascar': (-19.0, 47.0),
                    'europe': (50.0, 10.0),
                    'mediterranean': (40.0, 20.0),
                    'australia': (-25.0, 135.0),
                    'new zealand': (-41.0, 174.0),
                    'oceania': (-15.0, 160.0),
                    'caribbean': (18.0, -75.0),
                    'andean': (-10.0, -70.0),
                    'brazilian': (-15.0, -50.0),
                    'himalayan': (28.0, 85.0),
                    'borneo': (1.0, 114.0),
                    'sumatra': (0.0, 102.0),
                    'java': (-7.0, 110.0),
                    'philippines': (13.0, 122.0),
                    'papua new guinea': (-6.0, 147.0)
                }
                
                for orchid in orchids:
                    if orchid.region:
                        region_key = orchid.region.lower().strip()
                        
                        # Find matching region
                        coords = None
                        for region, coord in region_coords.items():
                            if region in region_key or region_key in region:
                                coords = coord
                                break
                        
                        if coords:
                            # Add some random offset to avoid exact overlaps
                            lat_offset = np.random.uniform(-2, 2)
                            lon_offset = np.random.uniform(-2, 2)
                            
                            orchid_locations.append({
                                'id': orchid.id,
                                'name': orchid.display_name or orchid.scientific_name,
                                'genus': orchid.genus,
                                'species': orchid.species,
                                'region': orchid.region,
                                'lat': coords[0] + lat_offset,
                                'lon': coords[1] + lon_offset,
                                'photographer': orchid.photographer,
                                'source': orchid.ingestion_source,
                                'image_url': orchid.image_url,
                                'google_drive_id': orchid.google_drive_id
                            })
                
                logger.info(f"Generated coordinates for {len(orchid_locations)} orchids")
                return orchid_locations
                
            except Exception as e:
                logger.error(f"Error extracting orchid coordinates: {e}")
                return []
    
    def add_orchid_markers(self, map_obj: folium.Map, orchid_data: List[Dict]):
        """Add orchid location markers to map"""
        
        # Create marker clusters by genus
        genus_clusters = {}
        genus_colors = {
            'Cattleya': '#FF6B6B',
            'Phalaenopsis': '#4ECDC4',
            'Dendrobium': '#45B7D1',
            'Oncidium': '#96CEB4',
            'Paphiopedilum': '#FECA57',
            'Cymbidium': '#FF9FF3',
            'Laelia': '#F8B500',
            'Epidendrum': '#6C5CE7',
            'Bulbophyllum': '#A8E6CF',
            'Masdevallia': '#FFB6C1'
        }
        
        for orchid in orchid_data:
            genus = orchid.get('genus', 'Unknown')
            
            if genus not in genus_clusters:
                cluster_color = genus_colors.get(genus, '#74B9FF')
                genus_clusters[genus] = folium.plugins.MarkerCluster(
                    name=f"{genus} ({genus} species)",
                    overlay=True,
                    control=True
                ).add_to(map_obj)
            
            # Create popup content with image if available
            popup_content = f"""
            <div style="width: 250px;">
                <h6><strong>{orchid['name']}</strong></h6>
                <p><strong>Genus:</strong> {orchid.get('genus', 'Unknown')}<br>
                <strong>Region:</strong> {orchid.get('region', 'Unknown')}<br>
                <strong>Source:</strong> {orchid.get('source', 'Unknown')}</p>
            """
            
            if orchid.get('google_drive_id'):
                popup_content += f'<img src="/api/drive-photo/{orchid["google_drive_id"]}" style="width: 200px; height: 150px; object-fit: cover; border-radius: 5px;">'
            elif orchid.get('image_url'):
                popup_content += f'<img src="{orchid["image_url"]}" style="width: 200px; height: 150px; object-fit: cover; border-radius: 5px;">'
            
            popup_content += f'<p><a href="/orchid/{orchid["id"]}" target="_blank" class="btn btn-sm btn-primary">View Details</a></p></div>'
            
            # Add marker to appropriate cluster
            folium.Marker(
                location=[orchid['lat'], orchid['lon']],
                popup=folium.Popup(popup_content, max_width=300),
                tooltip=f"{orchid['name']} - {orchid.get('region', 'Unknown')}",
                icon=folium.Icon(
                    color='green' if orchid.get('google_drive_id') else 'blue',
                    icon='leaf',
                    prefix='fa'
                )
            ).add_to(genus_clusters[genus])
    
    def create_species_density_heatmap(self, map_obj: folium.Map, orchid_data: List[Dict]):
        """Create heatmap showing orchid species density"""
        
        # Prepare data for heatmap
        heat_data = []
        for orchid in orchid_data:
            # Add weight based on genus rarity (rough approximation)
            genus_weights = {
                'Bulbophyllum': 3,  # Very diverse genus
                'Dendrobium': 3,
                'Epidendrum': 2,
                'Cattleya': 1.5,    # Popular but less diverse
                'Phalaenopsis': 1.2
            }
            
            weight = genus_weights.get(orchid.get('genus', ''), 1.0)
            heat_data.append([orchid['lat'], orchid['lon'], weight])
        
        # Add heatmap layer
        from folium.plugins import HeatMap
        HeatMap(
            heat_data,
            name='Species Density',
            min_opacity=0.3,
            max_zoom=18,
            radius=25,
            blur=15,
            gradient={
                0.0: 'blue',
                0.3: 'cyan', 
                0.5: 'lime',
                0.7: 'yellow',
                1.0: 'red'
            }
        ).add_to(map_obj)
    
    def add_elevation_contours(self, map_obj: folium.Map):
        """Add elevation contour overlay for topographical context"""
        
        # Add terrain/elevation layer
        folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Terrain_Base/MapServer/tile/{z}/{y}/{x}',
            attr='Esri World Terrain',
            name='Terrain Contours',
            overlay=True,
            control=True,
            opacity=0.7
        ).add_to(map_obj)
    
    def generate_comprehensive_map(self) -> str:
        """Generate complete orchid mapping system with all features"""
        
        # Create base map
        orchid_map = self.create_world_orchid_map()
        
        # Add biogeographic regions
        self.add_biogeographic_regions(orchid_map)
        
        # Get orchid location data
        orchid_data = self.get_orchid_coordinates()
        
        if orchid_data:
            # Add orchid markers
            self.add_orchid_markers(orchid_map, orchid_data)
            
            # Add species density heatmap
            self.create_species_density_heatmap(orchid_map, orchid_data)
        
        # Add elevation contours
        self.add_elevation_contours(orchid_map)
        
        # Add layer control
        folium.LayerControl().add_to(orchid_map)
        
        # Add map title and info
        title_html = '''
        <div style="position: fixed; 
                    top: 10px; left: 50px; width: 350px; height: 80px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:14px; padding: 10px; border-radius: 5px;">
        <h4>🌺 Orchid Continuum World Map</h4>
        <p><strong>4,173+ orchid species</strong> from global collections<br>
        <small>🔵 Specimens with photos | 🟢 Google Drive images | 📍 Clustered by genus</small></p>
        </div>
        '''
        orchid_map.get_root().html.add_child(folium.Element(title_html))
        
        # Add legend for biogeographic regions
        legend_html = '''
        <div style="position: fixed; 
                    bottom: 20px; left: 20px; width: 300px; height: 200px; 
                    background-color: white; border:2px solid grey; z-index:9999; 
                    font-size:12px; padding: 10px; border-radius: 5px; overflow-y: auto;">
        <h5>🌍 Biogeographic Regions</h5>
        '''
        
        for region, data in self.orchid_regions.items():
            legend_html += f'<p><span style="color: {data["color"]};">■</span> <strong>{region}</strong><br><small>{data["description"]}</small></p>'
        
        legend_html += '</div>'
        orchid_map.get_root().html.add_child(folium.Element(legend_html))
        
        return orchid_map._repr_html_()

# Global instance
mapping_system = OrchidMappingSystem()

def get_orchid_map_html():
    """Get HTML for complete orchid mapping system"""
    return mapping_system.generate_comprehensive_map()