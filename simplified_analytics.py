#!/usr/bin/env python3
"""
Simplified Analytics System
==========================
Analytics that work with the existing OrchidRecord database structure
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from app import app, db
from models import OrchidRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimplifiedAnalytics:
    """
    Simplified analytics using region and habitat data instead of coordinates
    """
    
    def __init__(self):
        logger.info("📊 Simplified Analytics system initialized")
    
    def get_regional_analysis(self) -> Dict[str, Any]:
        """
        Analyze orchid distribution by region
        """
        try:
            with app.app_context():
                # Regional distribution analysis
                regional_stats = db.session.query(
                    OrchidRecord.region,
                    db.func.count(OrchidRecord.id).label('total_orchids'),
                    db.func.count(db.func.distinct(OrchidRecord.scientific_name)).label('unique_species'),
                    db.func.count(db.func.distinct(OrchidRecord.genus)).label('unique_genera')
                ).filter(
                    OrchidRecord.region.isnot(None)
                ).group_by(OrchidRecord.region).order_by(
                    db.func.count(OrchidRecord.id).desc()
                ).all()
                
                regions = []
                for region_data in regional_stats:
                    regions.append({
                        'region': region_data.region,
                        'total_orchids': region_data.total_orchids,
                        'unique_species': region_data.unique_species,
                        'unique_genera': region_data.unique_genera,
                        'diversity_ratio': region_data.unique_species / region_data.total_orchids if region_data.total_orchids > 0 else 0
                    })
                
                return {
                    'regions': regions,
                    'total_regions': len(regions),
                    'analysis_timestamp': datetime.now().isoformat()
                }
                
        except Exception as e:
            logger.error(f"❌ Error in regional analysis: {e}")
            return {'error': str(e), 'regions': []}
    
    def get_habitat_analysis(self) -> Dict[str, Any]:
        """
        Analyze orchid distribution by habitat
        """
        try:
            with app.app_context():
                # Get orchids with habitat data
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.native_habitat.isnot(None)
                ).all()
                
                habitat_stats = {}
                
                for orchid in orchids:
                    habitat = orchid.native_habitat.strip().lower() if orchid.native_habitat else 'unknown'
                    
                    # Simplified habitat categorization
                    if 'tropical' in habitat or 'rainforest' in habitat:
                        habitat_type = 'Tropical Forest'
                    elif 'temperate' in habitat or 'deciduous' in habitat:
                        habitat_type = 'Temperate Forest'
                    elif 'mountain' in habitat or 'alpine' in habitat or 'elevation' in habitat:
                        habitat_type = 'Montane'
                    elif 'coastal' in habitat or 'marine' in habitat:
                        habitat_type = 'Coastal'
                    elif 'grassland' in habitat or 'prairie' in habitat:
                        habitat_type = 'Grassland'
                    elif 'desert' in habitat or 'arid' in habitat:
                        habitat_type = 'Arid'
                    else:
                        habitat_type = 'Other'
                    
                    if habitat_type not in habitat_stats:
                        habitat_stats[habitat_type] = {
                            'count': 0,
                            'species': set(),
                            'genera': set()
                        }
                    
                    habitat_stats[habitat_type]['count'] += 1
                    if orchid.scientific_name:
                        habitat_stats[habitat_type]['species'].add(orchid.scientific_name)
                    if orchid.genus:
                        habitat_stats[habitat_type]['genera'].add(orchid.genus)
                
                # Convert sets to counts for JSON serialization
                habitat_breakdown = {}
                total_specimens = sum(data['count'] for data in habitat_stats.values())
                
                for habitat_type, data in habitat_stats.items():
                    habitat_breakdown[habitat_type] = {
                        'specimen_count': data['count'],
                        'percentage_of_total': (data['count'] / total_specimens) * 100 if total_specimens > 0 else 0,
                        'unique_species': len(data['species']),
                        'unique_genera': len(data['genera'])
                    }
                
                return {
                    'habitat_breakdown': habitat_breakdown,
                    'habitat_types_found': len(habitat_breakdown),
                    'total_specimens_analyzed': total_specimens,
                    'most_diverse_habitat': max(habitat_breakdown.keys(), key=lambda k: habitat_breakdown[k]['unique_species']) if habitat_breakdown else None
                }
                
        except Exception as e:
            logger.error(f"❌ Error in habitat analysis: {e}")
            return {'error': str(e), 'habitat_breakdown': {}}
    
    def get_diversity_hotspots(self) -> List[Dict[str, Any]]:
        """
        Identify diversity hotspots by region (simplified version)
        """
        try:
            regional_data = self.get_regional_analysis()
            
            if 'error' in regional_data:
                return []
            
            # Sort regions by unique species count to find hotspots
            hotspots = []
            for region_data in regional_data['regions']:
                if region_data['unique_species'] >= 5:  # Minimum threshold
                    hotspots.append({
                        'region': region_data['region'],
                        'unique_species': region_data['unique_species'],
                        'total_specimens': region_data['total_orchids'],
                        'unique_genera': region_data['unique_genera'],
                        'diversity_score': region_data['diversity_ratio'] * region_data['unique_species'],
                        'type': 'Regional Hotspot'
                    })
            
            # Sort by diversity score
            hotspots.sort(key=lambda x: x['diversity_score'], reverse=True)
            
            return hotspots
            
        except Exception as e:
            logger.error(f"❌ Error identifying diversity hotspots: {e}")
            return []
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics for dashboard
        """
        regional_analysis = self.get_regional_analysis()
        habitat_analysis = self.get_habitat_analysis()
        diversity_hotspots = self.get_diversity_hotspots()
        
        return {
            'regional_analysis': regional_analysis,
            'habitat_analysis': habitat_analysis,
            'diversity_hotspots': diversity_hotspots,
            'summary_stats': {
                'total_hotspots': len(diversity_hotspots),
                'habitat_types': habitat_analysis.get('habitat_types_found', 0),
                'regions_analyzed': regional_analysis.get('total_regions', 0),
                'most_diverse_habitat': habitat_analysis.get('most_diverse_habitat', 'Unknown')
            },
            'analysis_timestamp': datetime.now().isoformat()
        }

# Create simplified analytics instance
simplified_analytics = SimplifiedAnalytics()

if __name__ == "__main__":
    with app.app_context():
        print("📊 Testing Simplified Analytics")
        print("=" * 50)
        
        # Test regional analysis
        regional = simplified_analytics.get_regional_analysis()
        print(f"🌍 Found {regional.get('total_regions', 0)} regions")
        
        # Test habitat analysis  
        habitat = simplified_analytics.get_habitat_analysis()
        print(f"🌿 Found {habitat.get('habitat_types_found', 0)} habitat types")
        
        # Test diversity hotspots
        hotspots = simplified_analytics.get_diversity_hotspots()
        print(f"⭐ Found {len(hotspots)} diversity hotspots")
        
        print("✅ Simplified analytics test complete")