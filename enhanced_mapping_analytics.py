#!/usr/bin/env python3
"""
Enhanced Mapping Analytics System
=================================
Advanced species density heat maps and habitat correlation analysis
Part of The Orchid Continuum - Five Cities Orchid Society

Features:
- Biodiversity hotspot identification
- Species density clustering and analysis
- Climate-habitat correlation mapping
- Geographic diversity metrics
- Conservation priority area identification
"""

import numpy as np
import pandas as pd
from scipy import spatial
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import folium
from folium.plugins import HeatMap, MarkerCluster
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from app import app, db
from models import OrchidRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedMappingAnalytics:
    """
    Advanced mapping analytics for orchid distribution and biodiversity patterns
    """
    
    def __init__(self):
        self.min_cluster_size = 3
        self.eps_degrees = 0.5  # Roughly 55km at equator
        
        logger.info("🔬 Enhanced Mapping Analytics system initialized")
    
    def identify_biodiversity_hotspots(self, min_species: int = 10) -> List[Dict[str, Any]]:
        """
        Identify biodiversity hotspots with high orchid species concentration
        
        Args:
            min_species: Minimum species count to qualify as hotspot
            
        Returns:
            List of biodiversity hotspots with metrics
        """
        try:
            with app.app_context():
                # Get orchid coordinates and species data
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None),
                    OrchidRecord.scientific_name.isnot(None)
                ).all()
                
                if len(orchids) < min_species:
                    return []
                
                # Create coordinate matrix for clustering
                coordinates = np.array([[float(o.latitude), float(o.longitude)] for o in orchids])
                
                # Apply DBSCAN clustering to find dense regions
                scaler = StandardScaler()
                coords_scaled = scaler.fit_transform(coordinates)
                
                clustering = DBSCAN(eps=0.1, min_samples=min_species).fit(coords_scaled)
                labels = clustering.labels_
                
                hotspots = []
                unique_labels = set(labels)
                
                for label in unique_labels:
                    if label == -1:  # Noise points
                        continue
                    
                    # Get orchids in this cluster
                    cluster_mask = labels == label
                    cluster_orchids = [orchids[i] for i in range(len(orchids)) if cluster_mask[i]]
                    
                    if len(cluster_orchids) < min_species:
                        continue
                    
                    # Calculate cluster metrics
                    cluster_coords = coordinates[cluster_mask]
                    center_lat = float(np.mean(cluster_coords[:, 0]))
                    center_lng = float(np.mean(cluster_coords[:, 1]))
                    
                    # Species diversity metrics
                    species_set = set()
                    genera_set = set()
                    for orchid in cluster_orchids:
                        if orchid.scientific_name:
                            species_set.add(orchid.scientific_name)
                        if orchid.genus:
                            genera_set.add(orchid.genus)
                    
                    # Calculate geographic spread
                    lat_range = float(np.max(cluster_coords[:, 0]) - np.min(cluster_coords[:, 0]))
                    lng_range = float(np.max(cluster_coords[:, 1]) - np.min(cluster_coords[:, 1]))
                    area_estimate = lat_range * lng_range * 111.32 * 111.32  # Rough km²
                    
                    hotspot = {
                        'id': f'hotspot_{label}',
                        'center_lat': center_lat,
                        'center_lng': center_lng,
                        'total_specimens': len(cluster_orchids),
                        'unique_species': len(species_set),
                        'unique_genera': len(genera_set),
                        'species_density': len(species_set) / area_estimate if area_estimate > 0 else 0,
                        'area_km2': area_estimate,
                        'lat_range': lat_range,
                        'lng_range': lng_range,
                        'diversity_index': len(species_set) / len(cluster_orchids) if len(cluster_orchids) > 0 else 0,
                        'dominant_genera': list(genera_set)[:5],
                        'regions': list(set(o.region for o in cluster_orchids if o.region))[:3]
                    }
                    
                    hotspots.append(hotspot)
                
                # Sort by species diversity
                hotspots.sort(key=lambda x: x['unique_species'], reverse=True)
                
                logger.info(f"🌟 Identified {len(hotspots)} biodiversity hotspots")
                return hotspots
                
        except Exception as e:
            logger.error(f"❌ Error identifying biodiversity hotspots: {e}")
            return []
    
    def analyze_habitat_correlations(self) -> Dict[str, Any]:
        """
        Analyze correlations between orchid distribution and habitat types
        
        Returns:
            Habitat correlation analysis results
        """
        try:
            with app.app_context():
                # Get orchids with habitat and location data
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None),
                    OrchidRecord.native_habitat.isnot(None)
                ).all()
                
                if not orchids:
                    return {'error': 'No habitat data available'}
                
                # Analyze habitat types
                habitat_analysis = {}
                habitat_coordinates = {}
                
                for orchid in orchids:
                    habitat = orchid.native_habitat.strip().lower()
                    if not habitat or habitat == 'unknown':
                        continue
                    
                    # Simplified habitat categorization
                    if 'tropical' in habitat or 'rainforest' in habitat:
                        habitat_type = 'tropical_forest'
                    elif 'temperate' in habitat or 'deciduous' in habitat:
                        habitat_type = 'temperate_forest'
                    elif 'mountain' in habitat or 'alpine' in habitat or 'elevation' in habitat:
                        habitat_type = 'montane'
                    elif 'coastal' in habitat or 'marine' in habitat:
                        habitat_type = 'coastal'
                    elif 'grassland' in habitat or 'prairie' in habitat:
                        habitat_type = 'grassland'
                    elif 'desert' in habitat or 'arid' in habitat:
                        habitat_type = 'arid'
                    else:
                        habitat_type = 'other'
                    
                    if habitat_type not in habitat_analysis:
                        habitat_analysis[habitat_type] = {
                            'count': 0,
                            'species': set(),
                            'genera': set(),
                            'regions': set(),
                            'coordinates': []
                        }
                    
                    habitat_analysis[habitat_type]['count'] += 1
                    if orchid.scientific_name:
                        habitat_analysis[habitat_type]['species'].add(orchid.scientific_name)
                    if orchid.genus:
                        habitat_analysis[habitat_type]['genera'].add(orchid.genus)
                    if orchid.region:
                        habitat_analysis[habitat_type]['regions'].add(orchid.region)
                    
                    habitat_analysis[habitat_type]['coordinates'].append([
                        float(orchid.latitude), float(orchid.longitude)
                    ])
                
                # Calculate habitat metrics
                habitat_metrics = {}
                total_specimens = sum(data['count'] for data in habitat_analysis.values())
                
                for habitat_type, data in habitat_analysis.items():
                    coordinates = np.array(data['coordinates'])
                    
                    # Geographic spread
                    if len(coordinates) > 1:
                        lat_spread = float(np.std(coordinates[:, 0]))
                        lng_spread = float(np.std(coordinates[:, 1]))
                        geographic_spread = lat_spread + lng_spread
                    else:
                        geographic_spread = 0
                    
                    habitat_metrics[habitat_type] = {
                        'specimen_count': data['count'],
                        'percentage_of_total': (data['count'] / total_specimens) * 100,
                        'unique_species': len(data['species']),
                        'unique_genera': len(data['genera']),
                        'regions_present': len(data['regions']),
                        'geographic_spread': geographic_spread,
                        'species_per_specimen': len(data['species']) / data['count'] if data['count'] > 0 else 0,
                        'dominant_regions': list(data['regions'])[:5],
                        'sample_genera': list(data['genera'])[:8]
                    }
                
                # Sort by specimen count
                sorted_habitats = sorted(habitat_metrics.items(), key=lambda x: x[1]['specimen_count'], reverse=True)
                
                analysis_results = {
                    'total_specimens_analyzed': total_specimens,
                    'habitat_types_found': len(habitat_metrics),
                    'habitat_breakdown': dict(sorted_habitats),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'most_diverse_habitat': max(habitat_metrics.keys(), key=lambda k: habitat_metrics[k]['unique_species']) if habitat_metrics else None,
                    'most_widespread_habitat': max(habitat_metrics.keys(), key=lambda k: habitat_metrics[k]['geographic_spread']) if habitat_metrics else None
                }
                
                logger.info(f"🌿 Analyzed habitat correlations for {total_specimens} specimens across {len(habitat_metrics)} habitat types")
                return analysis_results
                
        except Exception as e:
            logger.error(f"❌ Error analyzing habitat correlations: {e}")
            return {'error': str(e)}
    
    def create_species_density_heatmap(self, genus_filter: Optional[str] = None) -> folium.Map:
        """
        Create advanced species density heat map with optional genus filtering
        
        Args:
            genus_filter: Optional genus to filter by
            
        Returns:
            Folium map with species density visualization
        """
        try:
            with app.app_context():
                # Build query
                query = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None)
                )
                
                if genus_filter:
                    query = query.filter(OrchidRecord.genus == genus_filter)
                
                orchids = query.all()
                
                if not orchids:
                    # Return empty map
                    return folium.Map(location=[20.0, 0.0], zoom_start=2)
                
                # Create base map
                center_lat = sum(float(o.latitude) for o in orchids) / len(orchids)
                center_lng = sum(float(o.longitude) for o in orchids) / len(orchids)
                
                density_map = folium.Map(
                    location=[center_lat, center_lng],
                    zoom_start=4,
                    tiles='CartoDB Positron'
                )
                
                # Add multiple tile layers
                folium.TileLayer('OpenStreetMap').add_to(density_map)
                folium.TileLayer('CartoDB Dark_Matter', name='Dark Theme').add_to(density_map)
                
                # Prepare heat map data with different intensities
                heat_data = []
                
                # Create grid-based density calculation
                grid_size = 0.5  # degrees
                density_grid = {}
                
                for orchid in orchids:
                    lat_grid = round(float(orchid.latitude) / grid_size) * grid_size
                    lng_grid = round(float(orchid.longitude) / grid_size) * grid_size
                    grid_key = (lat_grid, lng_grid)
                    
                    if grid_key not in density_grid:
                        density_grid[grid_key] = {'count': 0, 'species': set()}
                    
                    density_grid[grid_key]['count'] += 1
                    if orchid.scientific_name:
                        density_grid[grid_key]['species'].add(orchid.scientific_name)
                
                # Convert to heat map data
                max_density = max(cell['count'] for cell in density_grid.values()) if density_grid else 1
                
                for (lat, lng), data in density_grid.items():
                    intensity = data['count'] / max_density
                    species_count = len(data['species'])
                    
                    # Use species diversity as heat intensity
                    heat_intensity = min(species_count / 10.0, 1.0)  # Normalize to 0-1
                    heat_data.append([lat, lng, heat_intensity])
                
                # Add heat map layer
                HeatMap(
                    heat_data,
                    name='Species Density Heat Map',
                    min_opacity=0.4,
                    max_zoom=18,
                    radius=25,
                    blur=15,
                    gradient={
                        0.2: 'blue',
                        0.4: 'cyan', 
                        0.6: 'lime',
                        0.8: 'yellow',
                        1.0: 'red'
                    }
                ).add_to(density_map)
                
                # Add biodiversity hotspots
                hotspots = self.identify_biodiversity_hotspots(min_species=5)
                
                for hotspot in hotspots[:10]:  # Top 10 hotspots
                    folium.CircleMarker(
                        location=[hotspot['center_lat'], hotspot['center_lng']],
                        radius=min(hotspot['unique_species'], 20),
                        popup=f"""
                        <b>Biodiversity Hotspot</b><br>
                        Species: {hotspot['unique_species']}<br>
                        Specimens: {hotspot['total_specimens']}<br>
                        Genera: {hotspot['unique_genera']}<br>
                        Density: {hotspot['species_density']:.2f} species/km²
                        """,
                        color='purple',
                        fill=True,
                        fillColor='purple',
                        fillOpacity=0.6
                    ).add_to(density_map)
                
                # Add layer control
                folium.LayerControl().add_to(density_map)
                
                logger.info(f"🗺️ Created species density heat map with {len(orchids)} orchids and {len(hotspots)} hotspots")
                return density_map
                
        except Exception as e:
            logger.error(f"❌ Error creating species density heat map: {e}")
            return folium.Map(location=[20.0, 0.0], zoom_start=2)
    
    def calculate_diversity_metrics(self) -> Dict[str, Any]:
        """
        Calculate comprehensive diversity metrics across regions
        
        Returns:
            Diversity metrics and statistics
        """
        try:
            with app.app_context():
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.latitude.isnot(None),
                    OrchidRecord.longitude.isnot(None),
                    OrchidRecord.scientific_name.isnot(None)
                ).all()
                
                if not orchids:
                    return {'error': 'No data available for diversity calculations'}
                
                # Regional diversity analysis
                regional_diversity = {}
                
                for orchid in orchids:
                    region = orchid.region or 'Unknown'
                    
                    if region not in regional_diversity:
                        regional_diversity[region] = {
                            'species': set(),
                            'genera': set(),
                            'specimens': 0,
                            'coordinates': []
                        }
                    
                    regional_diversity[region]['specimens'] += 1
                    if orchid.scientific_name:
                        regional_diversity[region]['species'].add(orchid.scientific_name)
                    if orchid.genus:
                        regional_diversity[region]['genera'].add(orchid.genus)
                    regional_diversity[region]['coordinates'].append([
                        float(orchid.latitude), float(orchid.longitude)
                    ])
                
                # Calculate diversity indices
                diversity_indices = {}
                
                for region, data in regional_diversity.items():
                    species_count = len(data['species'])
                    genera_count = len(data['genera'])
                    specimen_count = data['specimens']
                    
                    # Shannon diversity index approximation
                    if specimen_count > 0:
                        species_evenness = species_count / specimen_count
                        shannon_estimate = -sum((1/species_count) * np.log(1/species_count) for _ in range(species_count)) if species_count > 1 else 0
                    else:
                        species_evenness = 0
                        shannon_estimate = 0
                    
                    # Geographic diversity (spread)
                    if len(data['coordinates']) > 1:
                        coords_array = np.array(data['coordinates'])
                        lat_spread = float(np.std(coords_array[:, 0]))
                        lng_spread = float(np.std(coords_array[:, 1]))
                        geographic_diversity = lat_spread + lng_spread
                    else:
                        geographic_diversity = 0
                    
                    diversity_indices[region] = {
                        'species_count': species_count,
                        'genera_count': genera_count,
                        'specimen_count': specimen_count,
                        'species_per_specimen': species_evenness,
                        'genera_per_species': genera_count / species_count if species_count > 0 else 0,
                        'shannon_diversity_estimate': shannon_estimate,
                        'geographic_diversity': geographic_diversity,
                        'diversity_rank': 0  # Will be calculated below
                    }
                
                # Rank regions by diversity
                sorted_regions = sorted(diversity_indices.items(), key=lambda x: x[1]['species_count'], reverse=True)
                
                for rank, (region, data) in enumerate(sorted_regions, 1):
                    diversity_indices[region]['diversity_rank'] = rank
                
                # Global statistics
                all_species = set()
                all_genera = set()
                for orchid in orchids:
                    if orchid.scientific_name:
                        all_species.add(orchid.scientific_name)
                    if orchid.genus:
                        all_genera.add(orchid.genus)
                
                global_stats = {
                    'total_specimens': len(orchids),
                    'total_species': len(all_species),
                    'total_genera': len(all_genera),
                    'regions_analyzed': len(diversity_indices),
                    'average_species_per_region': len(all_species) / len(diversity_indices) if diversity_indices else 0,
                    'most_diverse_region': sorted_regions[0][0] if sorted_regions else None,
                    'least_diverse_region': sorted_regions[-1][0] if sorted_regions else None
                }
                
                results = {
                    'global_statistics': global_stats,
                    'regional_diversity': dict(sorted_regions),
                    'analysis_timestamp': datetime.now().isoformat(),
                    'diversity_summary': {
                        'highest_species_count': sorted_regions[0][1]['species_count'] if sorted_regions else 0,
                        'lowest_species_count': sorted_regions[-1][1]['species_count'] if sorted_regions else 0,
                        'average_geographic_spread': np.mean([d[1]['geographic_diversity'] for d in sorted_regions]) if sorted_regions else 0
                    }
                }
                
                logger.info(f"📊 Calculated diversity metrics for {len(orchids)} specimens across {len(diversity_indices)} regions")
                return results
                
        except Exception as e:
            logger.error(f"❌ Error calculating diversity metrics: {e}")
            return {'error': str(e)}

def get_enhanced_mapping_data() -> Dict[str, Any]:
    """
    Get comprehensive enhanced mapping data for APIs
    
    Returns:
        Enhanced mapping analytics data
    """
    analytics = EnhancedMappingAnalytics()
    
    return {
        'biodiversity_hotspots': analytics.identify_biodiversity_hotspots(),
        'habitat_correlations': analytics.analyze_habitat_correlations(),
        'diversity_metrics': analytics.calculate_diversity_metrics(),
        'analysis_timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Test enhanced mapping analytics
    with app.app_context():
        analytics = EnhancedMappingAnalytics()
        
        print("🔬 Testing Enhanced Mapping Analytics System")
        print("=" * 50)
        
        # Test biodiversity hotspots
        hotspots = analytics.identify_biodiversity_hotspots()
        print(f"🌟 Found {len(hotspots)} biodiversity hotspots")
        
        if hotspots:
            top_hotspot = hotspots[0]
            print(f"Top hotspot: {top_hotspot['unique_species']} species, {top_hotspot['total_specimens']} specimens")
        
        # Test habitat correlations
        habitat_analysis = analytics.analyze_habitat_correlations()
        if 'habitat_breakdown' in habitat_analysis:
            print(f"🌿 Analyzed {habitat_analysis['habitat_types_found']} habitat types")
        
        # Test diversity metrics
        diversity_metrics = analytics.calculate_diversity_metrics()
        if 'global_statistics' in diversity_metrics:
            stats = diversity_metrics['global_statistics']
            print(f"📊 Global diversity: {stats['total_species']} species across {stats['regions_analyzed']} regions")
        
        print("✅ Enhanced mapping analytics test complete")