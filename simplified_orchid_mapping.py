#!/usr/bin/env python3
"""
Simplified Orchid Geographic Mapping System
===========================================
Working world map using regional data instead of coordinates
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import folium
import json
import logging
from folium.plugins import MarkerCluster, HeatMap
from flask import Flask, jsonify, render_template
from app import app, db
from models import OrchidRecord
from datetime import datetime
from typing import Dict, List, Optional, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedOrchidMapper:
    """
    Simplified geographic mapping using regional data and sample coordinates
    """
    
    def __init__(self):
        self.default_center = [20.0, 0.0]  # World center
        self.default_zoom = 2
        
        # Sample coordinates for regions (until we get GBIF coordinate data)
        self.region_coordinates = {
            'North America': [45.0, -100.0],
            'South America': [-15.0, -60.0],
            'Central America': [15.0, -85.0],
            'Europe': [50.0, 10.0],
            'Asia': [35.0, 105.0],
            'Southeast Asia': [10.0, 110.0],
            'Africa': [0.0, 20.0],
            'Australia': [-25.0, 135.0],
            'Oceania': [-20.0, 145.0],
            'Madagascar': [-18.0, 47.0],
            'Caribbean': [18.0, -75.0],
            'Pacific Islands': [-10.0, -150.0]
        }
        
        logger.info("🗺️ Simplified Orchid Geographic Mapping system initialized")
    
    def get_regional_orchid_data(self) -> List[Dict[str, Any]]:
        """
        Get orchid data organized by regions
        
        Returns:
            List of regional orchid data with sample coordinates
        """
        try:
            with app.app_context():
                # Get orchids grouped by region
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.region.isnot(None)
                ).all()
                
                regional_data = {}
                
                for orchid in orchids:
                    region = orchid.region.strip() if orchid.region else 'Unknown'
                    
                    if region not in regional_data:
                        regional_data[region] = {
                            'orchids': [],
                            'count': 0,
                            'genera': set(),
                            'species': set()
                        }
                    
                    regional_data[region]['orchids'].append({
                        'id': orchid.id,
                        'scientific_name': orchid.scientific_name or 'Unknown',
                        'genus': orchid.genus or 'Unknown',
                        'species': orchid.species or 'Unknown',
                        'display_name': orchid.display_name or orchid.scientific_name,
                        'native_habitat': orchid.native_habitat or 'Unknown',
                        'ingestion_source': orchid.ingestion_source or 'Unknown'
                    })
                    
                    regional_data[region]['count'] += 1
                    if orchid.genus:
                        regional_data[region]['genera'].add(orchid.genus)
                    if orchid.scientific_name:
                        regional_data[region]['species'].add(orchid.scientific_name)
                
                # Convert to list with coordinates
                map_data = []
                for region, data in regional_data.items():
                    # Get approximate coordinates for region
                    coords = self.region_coordinates.get(region, [0.0, 0.0])
                    
                    map_data.append({
                        'region': region,
                        'lat': coords[0],
                        'lng': coords[1],
                        'orchid_count': data['count'],
                        'unique_genera': len(data['genera']),
                        'unique_species': len(data['species']),
                        'sample_orchids': data['orchids'][:10]  # First 10 for popup
                    })
                
                logger.info(f"📍 Retrieved {len(map_data)} regional orchid distributions")
                return map_data
                
        except Exception as e:
            logger.error(f"❌ Error retrieving regional orchid data: {e}")
            return []
    
    def get_genus_regional_data(self, genus: str) -> List[Dict[str, Any]]:
        """
        Get orchid data for a specific genus organized by regions
        
        Args:
            genus: The orchid genus to filter by
            
        Returns:
            List of regional orchid data for the specified genus
        """
        try:
            with app.app_context():
                # Get orchids for specific genus grouped by region
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.genus == genus,
                    OrchidRecord.region.isnot(None)
                ).all()
                
                regional_data = {}
                
                for orchid in orchids:
                    region = orchid.region.strip() if orchid.region else 'Unknown'
                    
                    if region not in regional_data:
                        regional_data[region] = {
                            'orchids': [],
                            'count': 0,
                            'species': set()
                        }
                    
                    regional_data[region]['orchids'].append({
                        'id': orchid.id,
                        'scientific_name': orchid.scientific_name or 'Unknown',
                        'genus': orchid.genus or 'Unknown',
                        'species': orchid.species or 'Unknown',
                        'display_name': orchid.display_name or orchid.scientific_name,
                        'native_habitat': orchid.native_habitat or 'Unknown'
                    })
                    
                    regional_data[region]['count'] += 1
                    if orchid.scientific_name:
                        regional_data[region]['species'].add(orchid.scientific_name)
                
                # Convert to list with coordinates
                map_data = []
                for region, data in regional_data.items():
                    coords = self.region_coordinates.get(region, [0.0, 0.0])
                    
                    map_data.append({
                        'region': region,
                        'lat': coords[0],
                        'lng': coords[1],
                        'orchid_count': data['count'],
                        'unique_genera': 1,  # Only one genus
                        'unique_species': len(data['species']),
                        'sample_orchids': data['orchids'][:10],
                        'genus': genus
                    })
                
                logger.info(f"📍 Retrieved {len(map_data)} regional distributions for genus {genus}")
                return map_data
                
        except Exception as e:
            logger.error(f"❌ Error retrieving genus regional data for {genus}: {e}")
            return []
    
    def create_working_world_map(self) -> folium.Map:
        """
        Create working world map with regional orchid distributions
        
        Returns:
            Folium map object with regional orchid data
        """
        try:
            # Get regional orchid data
            regional_data = self.get_regional_orchid_data()
            
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
            
            if regional_data:
                # Create marker cluster for regional data
                marker_cluster = MarkerCluster(
                    name="Regional Orchid Distributions",
                    overlay=True,
                    control=True
                ).add_to(world_map)
                
                # Add regional markers
                for region in regional_data:
                    # Create popup content
                    popup_content = f"""
                    <div style="width:300px">
                        <h4><strong>{region}</strong></h4>
                        <p><strong>Total Orchids:</strong> {region['orchid_count']:,}</p>
                        <p><strong>Unique Genera:</strong> {region['unique_genera']}</p>
                        <p><strong>Unique Species:</strong> {region['unique_species']}</p>
                        <hr>
                        <h5>Sample Species:</h5>
                        <ul>
                    """
                    
                    for orchid in region['sample_orchids'][:5]:
                        popup_content += f"<li><em>{orchid['scientific_name']}</em></li>"
                    
                    popup_content += """
                        </ul>
                        <small>Regional distribution data - precise coordinates coming soon!</small>
                    </div>
                    """
                    
                    # Determine marker color based on orchid count
                    if region['orchid_count'] > 100:
                        color = 'red'  # High diversity
                        icon = 'star'
                    elif region['orchid_count'] > 50:
                        color = 'orange'  # Medium diversity
                        icon = 'leaf'
                    else:
                        color = 'green'  # Lower diversity
                        icon = 'tree'
                    
                    folium.Marker(
                        location=[region['lat'], region['lng']],
                        popup=folium.Popup(popup_content, max_width=300),
                        tooltip=f"{region['region']}: {region['orchid_count']} orchids",
                        icon=folium.Icon(
                            color=color,
                            icon=icon,
                            prefix='fa'
                        )
                    ).add_to(marker_cluster)
                
                # Add heat map layer (approximate)
                heat_data = [[region['lat'], region['lng'], region['orchid_count']] for region in regional_data]
                
                HeatMap(
                    heat_data,
                    name='Orchid Density (Regional)',
                    overlay=True,
                    control=True,
                    show=False  # Hidden by default
                ).add_to(world_map)
            
            else:
                # Add sample orchid locations if no data
                sample_locations = [
                    [38.9, -77.0, "North America - Sample Location"],
                    [-23.5, -46.6, "South America - Sample Location"], 
                    [51.5, -0.1, "Europe - Sample Location"],
                    [35.7, 139.7, "Asia - Sample Location"],
                    [-33.9, 151.2, "Australia - Sample Location"]
                ]
                
                for lat, lng, name in sample_locations:
                    folium.Marker(
                        location=[lat, lng],
                        popup=f"<b>{name}</b><br>Sample orchid distribution area<br><small>Precise data coming soon!</small>",
                        tooltip=name,
                        icon=folium.Icon(color='blue', icon='leaf', prefix='fa')
                    ).add_to(world_map)
            
            # Add layer control
            folium.LayerControl().add_to(world_map)
            
            # Add custom legend
            legend_html = '''
                <div style="position: fixed; 
                           bottom: 50px; right: 50px; width: 200px; height: 120px; 
                           background-color: white; border:2px solid grey; z-index:9999; 
                           font-size:14px; padding: 10px">
                <h5>Orchid Distribution</h5>
                <p><i class="fa fa-star" style="color:red"></i> High Diversity (100+)</p>
                <p><i class="fa fa-leaf" style="color:orange"></i> Medium Diversity (50+)</p>
                <p><i class="fa fa-tree" style="color:green"></i> Lower Diversity</p>
                <small>Regional data - coordinates coming soon!</small>
                </div>
            '''
            world_map.get_root().html.add_child(folium.Element(legend_html))
            
            logger.info("🗺️ Working world map created successfully!")
            return world_map
            
        except Exception as e:
            logger.error(f"❌ Error creating world map: {e}")
            # Return empty map as fallback
            return folium.Map(location=self.default_center, zoom_start=self.default_zoom)
    
    def get_working_statistics(self) -> Dict[str, Any]:
        """
        Get working geographic statistics
        """
        try:
            with app.app_context():
                total_orchids = OrchidRecord.query.count()
                regional_count = OrchidRecord.query.filter(
                    OrchidRecord.region.isnot(None)
                ).count()
                
                # Count unique genera and species
                unique_genera = OrchidRecord.query.filter(
                    OrchidRecord.genus.isnot(None)
                ).distinct(OrchidRecord.genus).count()
                
                unique_species = OrchidRecord.query.filter(
                    OrchidRecord.scientific_name.isnot(None)
                ).distinct(OrchidRecord.scientific_name).count()
                
                return {
                    'total_orchids': total_orchids,
                    'orchids_with_regional_data': regional_count,
                    'coverage_percentage': (regional_count / total_orchids) * 100 if total_orchids > 0 else 0,
                    'unique_genera': unique_genera,
                    'unique_species': unique_species,
                    'coordinate_precision': 'Regional approximations (precise coordinates coming soon)',
                    'last_updated': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting geographic statistics: {e}")
            return {
                'total_orchids': 0,
                'orchids_with_regional_data': 0,
                'coverage_percentage': 0,
                'unique_genera': 0,
                'unique_species': 0,
                'coordinate_precision': 'Error loading data'
            }

# Create global instance
simplified_mapper = SimplifiedOrchidMapper()

if __name__ == "__main__":
    with app.app_context():
        print("🗺️ Testing Simplified Orchid Mapping")
        print("=" * 50)
        
        # Test regional data
        regional_data = simplified_mapper.get_regional_orchid_data()
        print(f"📍 Regional distributions: {len(regional_data)}")
        
        # Test statistics
        stats = simplified_mapper.get_working_statistics()
        print(f"📊 Total orchids: {stats['total_orchids']}")
        print(f"🌍 Regional coverage: {stats['coverage_percentage']:.1f}%")
        
        print("✅ Simplified mapping system test complete")