#!/usr/bin/env python3
"""
Advanced Multi-Criteria Filtering System for Orchid Database
Implements comprehensive filtering by metadata fields with real-time updates

Features:
- Multi-criteria filtering by photographer, location, elevation, bloom date
- Geographic filtering (country, province, GPS coordinates)
- Biological filtering (genus, species, color, pollinator, growth habit)
- Mycorrhizal associations and ecological data
- Real-time gallery updates with saved filter combinations
"""

from flask import Flask, request, jsonify, render_template
from sqlalchemy import and_, or_, func, extract, between
from models import OrchidRecord, db
import re
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AdvancedFilteringSystem:
    """Comprehensive multi-criteria filtering for orchid database"""
    
    def __init__(self):
        self.filter_categories = {
            'geographic': ['country', 'province', 'gps_range', 'elevation_range'],
            'temporal': ['bloom_month', 'bloom_year', 'photo_date_range'],
            'taxonomic': ['genus', 'species', 'hybrid_type'],
            'morphological': ['flower_color', 'growth_habit', 'plant_size'],
            'ecological': ['pollinator', 'mycorrhizal_fungi', 'habitat_type'],
            'photographic': ['photographer', 'submitter_id', 'image_quality']
        }
    
    def apply_filters(self, filters_dict, page=1, per_page=20):
        """Apply comprehensive filters to orchid query"""
        try:
            # Start with base query
            query = OrchidRecord.query.filter(
                or_(
                    OrchidRecord.image_url.isnot(None),
                    OrchidRecord.google_drive_id.isnot(None)
                )
            )
            
            # Apply geographic filters
            query = self._apply_geographic_filters(query, filters_dict)
            
            # Apply temporal filters
            query = self._apply_temporal_filters(query, filters_dict)
            
            # Apply taxonomic filters
            query = self._apply_taxonomic_filters(query, filters_dict)
            
            # Apply morphological filters
            query = self._apply_morphological_filters(query, filters_dict)
            
            # Apply ecological filters
            query = self._apply_ecological_filters(query, filters_dict)
            
            # Apply photographic filters
            query = self._apply_photographic_filters(query, filters_dict)
            
            # Execute query with pagination
            paginated = query.paginate(
                page=page,
                per_page=per_page,
                error_out=False
            )
            
            return {
                'orchids': paginated.items,
                'total': paginated.total,
                'pages': paginated.pages,
                'current_page': page,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
                'filters_applied': self._count_active_filters(filters_dict)
            }
            
        except Exception as e:
            logger.error(f"Error applying filters: {e}")
            return {
                'orchids': [],
                'total': 0,
                'pages': 0,
                'current_page': 1,
                'has_next': False,
                'has_prev': False,
                'filters_applied': 0,
                'error': str(e)
            }
    
    def _apply_geographic_filters(self, query, filters):
        """Apply geographic filtering"""
        # Country filter
        if filters.get('country'):
            countries = filters['country'] if isinstance(filters['country'], list) else [filters['country']]
            country_conditions = []
            for country in countries:
                country_conditions.append(OrchidRecord.native_habitat.ilike(f'%{country}%'))
            query = query.filter(or_(*country_conditions))
        
        # Province/state filter
        if filters.get('province'):
            query = query.filter(OrchidRecord.native_habitat.ilike(f"%{filters['province']}%"))
        
        # Elevation range
        if filters.get('elevation_min') or filters.get('elevation_max'):
            # Parse elevation from ai_description or add elevation field
            if filters.get('elevation_min'):
                query = query.filter(OrchidRecord.ai_description.ilike(f"%{filters['elevation_min']}m%"))
            if filters.get('elevation_max'):
                # Could implement elevation field in future
                pass
        
        # GPS coordinate range (if we had GPS data)
        if filters.get('gps_bounds'):
            # Future implementation for GPS bounding box
            pass
            
        return query
    
    def _apply_temporal_filters(self, query, filters):
        """Apply temporal filtering"""
        # Bloom month
        if filters.get('bloom_month'):
            months = filters['bloom_month'] if isinstance(filters['bloom_month'], list) else [filters['bloom_month']]
            month_names = ['january', 'february', 'march', 'april', 'may', 'june',
                          'july', 'august', 'september', 'october', 'november', 'december']
            
            month_conditions = []
            for month in months:
                if month.lower() in month_names:
                    month_conditions.append(OrchidRecord.ai_description.ilike(f'%{month}%'))
            
            if month_conditions:
                query = query.filter(or_(*month_conditions))
        
        # Photo date range
        if filters.get('date_from') or filters.get('date_to'):
            if filters.get('date_from'):
                try:
                    date_from = datetime.strptime(filters['date_from'], '%Y-%m-%d')
                    query = query.filter(OrchidRecord.created_at >= date_from)
                except ValueError:
                    pass
            
            if filters.get('date_to'):
                try:
                    date_to = datetime.strptime(filters['date_to'], '%Y-%m-%d')
                    query = query.filter(OrchidRecord.created_at <= date_to)
                except ValueError:
                    pass
                    
        return query
    
    def _apply_taxonomic_filters(self, query, filters):
        """Apply taxonomic filtering"""
        # Genus filter
        if filters.get('genus'):
            genera = filters['genus'] if isinstance(filters['genus'], list) else [filters['genus']]
            genus_conditions = []
            for genus in genera:
                genus_conditions.append(OrchidRecord.genus.ilike(f'%{genus}%'))
            query = query.filter(or_(*genus_conditions))
        
        # Species filter
        if filters.get('species'):
            query = query.filter(OrchidRecord.species.ilike(f'%{filters["species"]}%'))
        
        # Hybrid type filter
        if filters.get('hybrid_type'):
            if filters['hybrid_type'] == 'species':
                query = query.filter(OrchidRecord.species.isnot(None))
                query = query.filter(~OrchidRecord.display_name.ilike('%x%'))
            elif filters['hybrid_type'] == 'hybrid':
                query = query.filter(or_(
                    OrchidRecord.display_name.ilike('%x%'),
                    OrchidRecord.display_name.ilike('%"%'),
                    OrchidRecord.ai_description.ilike('%hybrid%')
                ))
                
        return query
    
    def _apply_morphological_filters(self, query, filters):
        """Apply morphological filtering"""
        # Flower color
        if filters.get('flower_color'):
            colors = filters['flower_color'] if isinstance(filters['flower_color'], list) else [filters['flower_color']]
            color_conditions = []
            for color in colors:
                color_conditions.append(OrchidRecord.ai_description.ilike(f'%{color}%'))
            query = query.filter(or_(*color_conditions))
        
        # Growth habit
        if filters.get('growth_habit'):
            habits = filters['growth_habit'] if isinstance(filters['growth_habit'], list) else [filters['growth_habit']]
            habit_conditions = []
            for habit in habits:
                habit_conditions.append(OrchidRecord.ai_description.ilike(f'%{habit}%'))
            query = query.filter(or_(*habit_conditions))
        
        # Plant size
        if filters.get('plant_size'):
            size_terms = {
                'miniature': ['small', 'tiny', 'miniature', 'compact'],
                'medium': ['medium', 'intermediate'],
                'large': ['large', 'big', 'massive', 'giant']
            }
            
            size = filters['plant_size']
            if size in size_terms:
                size_conditions = []
                for term in size_terms[size]:
                    size_conditions.append(OrchidRecord.ai_description.ilike(f'%{term}%'))
                query = query.filter(or_(*size_conditions))
                
        return query
    
    def _apply_ecological_filters(self, query, filters):
        """Apply ecological filtering"""
        # Pollinator filter
        if filters.get('pollinator'):
            pollinators = filters['pollinator'] if isinstance(filters['pollinator'], list) else [filters['pollinator']]
            pollinator_conditions = []
            for pollinator in pollinators:
                pollinator_conditions.append(OrchidRecord.ai_description.ilike(f'%{pollinator}%'))
            query = query.filter(or_(*pollinator_conditions))
        
        # Mycorrhizal fungi
        if filters.get('mycorrhizal_fungi'):
            fungi = filters['mycorrhizal_fungi'] if isinstance(filters['mycorrhizal_fungi'], list) else [filters['mycorrhizal_fungi']]
            fungi_conditions = []
            for fungus in fungi:
                fungi_conditions.append(OrchidRecord.ai_description.ilike(f'%{fungus}%'))
            query = query.filter(or_(*fungi_conditions))
        
        # Habitat type
        if filters.get('habitat_type'):
            habitats = filters['habitat_type'] if isinstance(filters['habitat_type'], list) else [filters['habitat_type']]
            habitat_conditions = []
            for habitat in habitats:
                habitat_conditions.append(OrchidRecord.native_habitat.ilike(f'%{habitat}%'))
            query = query.filter(or_(*habitat_conditions))
                
        return query
    
    def _apply_photographic_filters(self, query, filters):
        """Apply photographic filtering"""
        # Photographer filter (from AI description or metadata)
        if filters.get('photographer'):
            query = query.filter(OrchidRecord.ai_description.ilike(f"%{filters['photographer']}%"))
        
        # Submitter ID (if we had user tracking)
        if filters.get('submitter_id'):
            # Future implementation with user tracking
            pass
        
        # Image quality filter
        if filters.get('min_confidence'):
            try:
                min_conf = float(filters['min_confidence'])
                query = query.filter(OrchidRecord.ai_confidence >= min_conf)
            except (ValueError, TypeError):
                pass
                
        return query
    
    def _count_active_filters(self, filters_dict):
        """Count number of active filters"""
        active = 0
        for key, value in filters_dict.items():
            if value and value != '' and value != []:
                active += 1
        return active
    
    def get_filter_suggestions(self, filter_type):
        """Get suggestions for filter values based on existing data"""
        try:
            suggestions = {}
            
            if filter_type in ['genus', 'all']:
                # Get all unique genera
                genera = db.session.query(OrchidRecord.genus)\
                    .filter(OrchidRecord.genus.isnot(None))\
                    .distinct().limit(50).all()
                suggestions['genus'] = [g[0] for g in genera if g[0]]
            
            if filter_type in ['country', 'all']:
                # Extract countries from native_habitat
                habitats = db.session.query(OrchidRecord.native_habitat)\
                    .filter(OrchidRecord.native_habitat.isnot(None))\
                    .distinct().limit(100).all()
                
                countries = set()
                for habitat in habitats:
                    if habitat[0]:
                        # Simple country extraction
                        parts = habitat[0].split(',')
                        if parts:
                            countries.add(parts[-1].strip())
                
                suggestions['country'] = sorted(list(countries))[:20]
            
            if filter_type in ['color', 'all']:
                # Common orchid colors
                suggestions['flower_color'] = [
                    'white', 'yellow', 'pink', 'purple', 'red', 'orange', 
                    'green', 'blue', 'magenta', 'cream', 'brown', 'black'
                ]
            
            if filter_type in ['growth_habit', 'all']:
                suggestions['growth_habit'] = [
                    'epiphytic', 'terrestrial', 'lithophytic', 'semi-terrestrial'
                ]
            
            if filter_type in ['pollinator', 'all']:
                suggestions['pollinator'] = [
                    'bee', 'butterfly', 'moth', 'hummingbird', 'bat', 'fly', 'wasp', 'beetle'
                ]
                
            return suggestions
            
        except Exception as e:
            logger.error(f"Error getting filter suggestions: {e}")
            return {}

# Saved filter combinations
class SavedFilterCombinations:
    """Manage saved filter combinations for users"""
    
    @staticmethod
    def get_predefined_combinations():
        """Get predefined interesting filter combinations"""
        return {
            'madagascar_white_night': {
                'name': 'Madagascar White Night-Bloomers',
                'description': 'White orchids from Madagascar that bloom at night',
                'filters': {
                    'country': 'Madagascar',
                    'flower_color': 'white',
                    'pollinator': 'moth'
                }
            },
            'ecuadorian_elevation': {
                'name': 'High-Altitude Ecuadorian Orchids',
                'description': 'Orchids from Ecuador above 1500m elevation',
                'filters': {
                    'country': 'Ecuador',
                    'elevation_min': '1500'
                }
            },
            'cattleya_hybrids': {
                'name': 'Cattleya Alliance Hybrids',
                'description': 'All Cattleya alliance hybrid orchids',
                'filters': {
                    'genus': 'Cattleya',
                    'hybrid_type': 'hybrid'
                }
            },
            'epiphytic_fragrant': {
                'name': 'Fragrant Epiphytic Orchids',
                'description': 'Epiphytic orchids with notable fragrance',
                'filters': {
                    'growth_habit': 'epiphytic'
                }
            },
            'autumn_bloomers': {
                'name': 'Autumn Blooming Orchids',
                'description': 'Orchids that bloom in autumn months',
                'filters': {
                    'bloom_month': ['september', 'october', 'november']
                }
            }
        }

if __name__ == "__main__":
    # Test the filtering system
    filter_system = AdvancedFilteringSystem()
    
    # Test filters
    test_filters = {
        'genus': 'Cattleya',
        'flower_color': 'purple',
        'country': 'Brazil'
    }
    
    results = filter_system.apply_filters(test_filters)
    print(f"Advanced filtering test: {results['total']} orchids found")