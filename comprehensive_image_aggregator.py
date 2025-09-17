#!/usr/bin/env python3
"""
Comprehensive Image Aggregation System
======================================
Aggregates orchid images from local database, GBIF, and iNaturalist
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import Flask, request, jsonify, session
from app import app, db
from models import OrchidRecord, OrchidTaxonomy
from external_orchid_databases import get_external_db_manager
from sqlalchemy import or_, and_, func
import hashlib
import urllib.parse

logger = logging.getLogger(__name__)

class ComprehensiveImageAggregator:
    """
    Aggregates orchid images from multiple sources with comprehensive metadata
    """
    
    def __init__(self):
        self.external_db = get_external_db_manager()
        self.cache_duration = timedelta(hours=6)  # Cache external data for 6 hours
        self.image_cache = {}
        
        logger.info("🖼️ Comprehensive Image Aggregator initialized")
    
    def get_all_images_for_species(self, scientific_name: str, limit_per_source: int = 20) -> Dict[str, Any]:
        """
        Get all available images for a species from all sources
        
        Args:
            scientific_name: Scientific name to search for
            limit_per_source: Maximum images per source
            
        Returns:
            Comprehensive image data from all sources
        """
        try:
            logger.info(f"🔍 Aggregating images for '{scientific_name}'")
            
            # Create cache key
            cache_key = f"images_{scientific_name}_{limit_per_source}"
            if cache_key in self.image_cache:
                cache_data = self.image_cache[cache_key]
                if datetime.now() - cache_data['timestamp'] < self.cache_duration:
                    logger.info(f"📦 Using cached images for '{scientific_name}'")
                    return cache_data['data']
            
            aggregated_images = {
                'scientific_name': scientific_name,
                'timestamp': datetime.now().isoformat(),
                'sources': {
                    'local': {
                        'images': [],
                        'count': 0,
                        'metadata': {}
                    },
                    'gbif': {
                        'images': [],
                        'count': 0,
                        'metadata': {}
                    },
                    'inaturalist': {
                        'images': [],
                        'count': 0,
                        'metadata': {}
                    }
                },
                'summary': {
                    'total_images': 0,
                    'sources_available': [],
                    'best_quality_images': [],
                    'research_grade_count': 0,
                    'with_coordinates': 0
                }
            }
            
            # Get local images
            local_images = self._get_local_images(scientific_name, limit_per_source)
            aggregated_images['sources']['local'] = local_images
            
            # Get external images
            if scientific_name:
                external_data = self.external_db.get_comprehensive_species_data(scientific_name)
                
                # Process GBIF images
                if external_data.get('sources', {}).get('gbif'):
                    gbif_images = self._process_gbif_images(
                        external_data['sources']['gbif'], 
                        limit_per_source
                    )
                    aggregated_images['sources']['gbif'] = gbif_images
                
                # Process iNaturalist images
                if external_data.get('sources', {}).get('inaturalist'):
                    inat_images = self._process_inaturalist_images(
                        external_data['sources']['inaturalist'], 
                        limit_per_source
                    )
                    aggregated_images['sources']['inaturalist'] = inat_images
            
            # Create summary
            aggregated_images['summary'] = self._create_image_summary(aggregated_images)
            
            # Cache the results
            self.image_cache[cache_key] = {
                'timestamp': datetime.now(),
                'data': aggregated_images
            }
            
            logger.info(f"✅ Aggregated {aggregated_images['summary']['total_images']} images from {len(aggregated_images['summary']['sources_available'])} sources")
            return aggregated_images
            
        except Exception as e:
            logger.error(f"❌ Image aggregation failed for '{scientific_name}': {e}")
            return self._create_empty_result(scientific_name)
    
    def _get_local_images(self, scientific_name: str, limit: int) -> Dict[str, Any]:
        """Get images from local database"""
        try:
            with app.app_context():
                # Search for orchids with this scientific name
                orchids = OrchidRecord.query.filter(
                    or_(
                        OrchidRecord.scientific_name.ilike(f'%{scientific_name}%'),
                        OrchidRecord.display_name.ilike(f'%{scientific_name}%')
                    ),
                    or_(
                        OrchidRecord.image_url.isnot(None),
                        OrchidRecord.google_drive_id.isnot(None),
                        OrchidRecord.image_filename.isnot(None)
                    )
                ).limit(limit).all()
                
                local_images = []
                for orchid in orchids:
                    image_info = {
                        'id': orchid.id,
                        'title': orchid.display_name or orchid.scientific_name,
                        'scientific_name': orchid.scientific_name,
                        'genus': orchid.genus,
                        'species': orchid.species,
                        'url': self._get_orchid_image_url(orchid),
                        'thumbnail_url': self._get_orchid_thumbnail_url(orchid),
                        'photographer': orchid.photographer,
                        'image_source': orchid.image_source,
                        'license': 'Local Collection',
                        'attribution': f"Photo by {orchid.photographer}" if orchid.photographer else "Orchid Continuum Collection",
                        'coordinates': {
                            'latitude': orchid.decimal_latitude,
                            'longitude': orchid.decimal_longitude
                        } if orchid.decimal_latitude and orchid.decimal_longitude else None,
                        'location': {
                            'country': orchid.country,
                            'state_province': orchid.state_province,
                            'locality': orchid.locality,
                            'region': orchid.region
                        },
                        'metadata': {
                            'is_flowering': orchid.is_flowering,
                            'flowering_stage': orchid.flowering_stage,
                            'growth_habit': orchid.growth_habit,
                            'ai_description': orchid.ai_description,
                            'ai_confidence': orchid.ai_confidence,
                            'created_at': orchid.created_at.isoformat() if orchid.created_at else None
                        },
                        'source': 'local',
                        'quality_grade': 'collection',
                        'has_coordinates': bool(orchid.decimal_latitude and orchid.decimal_longitude)
                    }
                    local_images.append(image_info)
                
                return {
                    'images': local_images,
                    'count': len(local_images),
                    'metadata': {
                        'source': 'local_database',
                        'total_records': len(orchids),
                        'collection_name': 'Orchid Continuum'
                    }
                }
                
        except Exception as e:
            logger.error(f"❌ Error getting local images: {e}")
            return {'images': [], 'count': 0, 'metadata': {}}
    
    def _process_gbif_images(self, gbif_data: Dict, limit: int) -> Dict[str, Any]:
        """Process GBIF occurrence data for images"""
        try:
            gbif_images = []
            occurrences = gbif_data.get('occurrences_with_images', [])
            
            for occurrence in occurrences[:limit]:
                for media in occurrence.get('media', []):
                    image_info = {
                        'title': media.get('title', 'GBIF Occurrence Image'),
                        'scientific_name': occurrence.get('scientific_name'),
                        'url': media.get('identifier'),
                        'thumbnail_url': media.get('identifier'),  # GBIF doesn't provide thumbnails
                        'photographer': media.get('creator'),
                        'license': media.get('license', 'Unknown'),
                        'rights_holder': media.get('rightsHolder'),
                        'attribution': f"© {media.get('rightsHolder', 'Unknown')} via GBIF",
                        'coordinates': {
                            'latitude': occurrence.get('decimal_latitude'),
                            'longitude': occurrence.get('decimal_longitude')
                        } if occurrence.get('decimal_latitude') else None,
                        'location': {
                            'country': occurrence.get('country'),
                            'state_province': occurrence.get('state_province'),
                            'locality': occurrence.get('locality')
                        },
                        'metadata': {
                            'gbif_occurrence_key': occurrence.get('gbif_occurrence_key'),
                            'basis_of_record': occurrence.get('basis_of_record'),
                            'event_date': occurrence.get('event_date'),
                            'recorded_by': occurrence.get('recorded_by'),
                            'collection_code': occurrence.get('collection_code'),
                            'catalog_number': occurrence.get('catalog_number'),
                            'establishment_means': occurrence.get('establishment_means'),
                            'occurrence_status': occurrence.get('occurrence_status')
                        },
                        'source': 'gbif',
                        'quality_grade': 'research',
                        'has_coordinates': bool(occurrence.get('decimal_latitude'))
                    }
                    gbif_images.append(image_info)
            
            return {
                'images': gbif_images,
                'count': len(gbif_images),
                'metadata': {
                    'source': 'gbif',
                    'total_occurrences': len(occurrences),
                    'with_media': len([o for o in occurrences if o.get('media')])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing GBIF images: {e}")
            return {'images': [], 'count': 0, 'metadata': {}}
    
    def _process_inaturalist_images(self, inat_data: Dict, limit: int) -> Dict[str, Any]:
        """Process iNaturalist observation data for images"""
        try:
            inat_images = []
            observations = inat_data.get('observations_with_photos', [])
            
            for observation in observations[:limit]:
                for photo in observation.get('photos', []):
                    # Get best available image size
                    best_url = self._get_best_inaturalist_image_url(photo)
                    thumb_url = photo.get('sizes', {}).get('small', best_url)
                    
                    image_info = {
                        'title': f"iNaturalist Observation {observation.get('inaturalist_observation_id')}",
                        'scientific_name': observation.get('scientific_name'),
                        'common_name': observation.get('common_name'),
                        'url': best_url,
                        'thumbnail_url': thumb_url,
                        'photographer': photo.get('attribution', '').split('(c)')[1].strip() if '(c)' in photo.get('attribution', '') else 'iNaturalist User',
                        'license': photo.get('license_code', 'Unknown'),
                        'attribution': photo.get('attribution', 'iNaturalist Community'),
                        'coordinates': {
                            'latitude': float(observation.get('latitude')) if observation.get('latitude') else None,
                            'longitude': float(observation.get('longitude')) if observation.get('longitude') else None
                        } if observation.get('latitude') else None,
                        'location': {
                            'place_guess': observation.get('place_guess')
                        },
                        'metadata': {
                            'inaturalist_observation_id': observation.get('inaturalist_observation_id'),
                            'observed_on': observation.get('observed_on'),
                            'quality_grade': observation.get('quality_grade'),
                            'identifications_count': observation.get('identifications_count'),
                            'comments_count': observation.get('comments_count'),
                            'description': observation.get('description'),
                            'positional_accuracy': observation.get('positional_accuracy'),
                            'photo_id': photo.get('id')
                        },
                        'source': 'inaturalist',
                        'quality_grade': observation.get('quality_grade', 'unknown'),
                        'has_coordinates': bool(observation.get('latitude'))
                    }
                    inat_images.append(image_info)
            
            return {
                'images': inat_images,
                'count': len(inat_images),
                'metadata': {
                    'source': 'inaturalist',
                    'total_observations': len(observations),
                    'research_grade': len([o for o in observations if o.get('quality_grade') == 'research']),
                    'with_photos': len([o for o in observations if o.get('photos')])
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error processing iNaturalist images: {e}")
            return {'images': [], 'count': 0, 'metadata': {}}
    
    def _get_best_inaturalist_image_url(self, photo: Dict) -> str:
        """Get the best available image URL from iNaturalist photo sizes"""
        sizes = photo.get('sizes', {})
        
        # Preference order for image sizes
        preferred_sizes = ['large', 'medium', 'small', 'thumb', 'square']
        
        for size in preferred_sizes:
            if size in sizes and sizes[size]:
                return sizes[size]
        
        # Fallback to the main URL
        return photo.get('url', '')
    
    def _get_orchid_image_url(self, orchid: 'OrchidRecord') -> str:
        """Get the primary image URL for a local orchid record"""
        if orchid.google_drive_id:
            return f"/api/drive-photo/{orchid.google_drive_id}"
        elif orchid.image_url:
            return orchid.image_url
        elif orchid.image_filename:
            return f"/static/uploads/{orchid.image_filename}"
        return "/static/images/orchid_placeholder.png"
    
    def _get_orchid_thumbnail_url(self, orchid: 'OrchidRecord') -> str:
        """Get thumbnail URL for a local orchid record"""
        # For now, return the same as primary image
        # Could be enhanced to generate actual thumbnails
        return self._get_orchid_image_url(orchid)
    
    def _create_image_summary(self, aggregated_images: Dict) -> Dict[str, Any]:
        """Create summary statistics for aggregated images"""
        try:
            sources = aggregated_images['sources']
            
            total_images = sum(source['count'] for source in sources.values())
            sources_available = [name for name, source in sources.items() if source['count'] > 0]
            
            # Collect best quality images from all sources
            best_quality_images = []
            research_grade_count = 0
            with_coordinates = 0
            
            for source_name, source_data in sources.items():
                for image in source_data['images']:
                    # Count research grade images
                    if image.get('quality_grade') in ['research', 'collection']:
                        research_grade_count += 1
                    
                    # Count images with coordinates
                    if image.get('has_coordinates'):
                        with_coordinates += 1
                    
                    # Add to best quality if high quality
                    if (image.get('quality_grade') in ['research', 'collection'] and 
                        len(best_quality_images) < 10):
                        best_quality_images.append(image)
            
            return {
                'total_images': total_images,
                'sources_available': sources_available,
                'best_quality_images': best_quality_images,
                'research_grade_count': research_grade_count,
                'with_coordinates': with_coordinates,
                'source_breakdown': {
                    'local': sources['local']['count'],
                    'gbif': sources['gbif']['count'],
                    'inaturalist': sources['inaturalist']['count']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ Error creating image summary: {e}")
            return {
                'total_images': 0,
                'sources_available': [],
                'best_quality_images': [],
                'research_grade_count': 0,
                'with_coordinates': 0
            }
    
    def _create_empty_result(self, scientific_name: str) -> Dict[str, Any]:
        """Create empty result structure for failed queries"""
        return {
            'scientific_name': scientific_name,
            'timestamp': datetime.now().isoformat(),
            'sources': {
                'local': {'images': [], 'count': 0, 'metadata': {}},
                'gbif': {'images': [], 'count': 0, 'metadata': {}},
                'inaturalist': {'images': [], 'count': 0, 'metadata': {}}
            },
            'summary': {
                'total_images': 0,
                'sources_available': [],
                'best_quality_images': [],
                'research_grade_count': 0,
                'with_coordinates': 0
            },
            'error': 'Failed to aggregate images'
        }
    
    def get_collection_gallery(self, collection_orchids: List[int], 
                             include_external: bool = True) -> Dict[str, Any]:
        """
        Create a gallery view for user's collection with external images
        
        Args:
            collection_orchids: List of orchid IDs in user's collection
            include_external: Whether to include external database images
            
        Returns:
            Gallery data for collection
        """
        try:
            logger.info(f"📸 Creating collection gallery for {len(collection_orchids)} orchids")
            
            gallery_data = {
                'collection_size': len(collection_orchids),
                'galleries': {},
                'summary': {
                    'total_images': 0,
                    'orchids_with_images': 0,
                    'external_images': 0
                }
            }
            
            with app.app_context():
                orchids = OrchidRecord.query.filter(
                    OrchidRecord.id.in_(collection_orchids)
                ).all()
                
                for orchid in orchids:
                    orchid_key = f"orchid_{orchid.id}"
                    scientific_name = orchid.scientific_name or orchid.display_name
                    
                    if include_external and scientific_name:
                        # Get comprehensive images for this orchid
                        orchid_images = self.get_all_images_for_species(scientific_name, limit_per_source=5)
                    else:
                        # Get only local images
                        orchid_images = {
                            'sources': {
                                'local': self._get_local_images(scientific_name, 5)
                            }
                        }
                    
                    gallery_data['galleries'][orchid_key] = {
                        'orchid_info': {
                            'id': orchid.id,
                            'display_name': orchid.display_name,
                            'scientific_name': orchid.scientific_name,
                            'genus': orchid.genus,
                            'species': orchid.species
                        },
                        'images': orchid_images
                    }
                    
                    # Update summary
                    total_orchid_images = sum(
                        source['count'] for source in orchid_images.get('sources', {}).values()
                    )
                    if total_orchid_images > 0:
                        gallery_data['summary']['orchids_with_images'] += 1
                        gallery_data['summary']['total_images'] += total_orchid_images
                        
                        if include_external:
                            external_count = (
                                orchid_images.get('sources', {}).get('gbif', {}).get('count', 0) +
                                orchid_images.get('sources', {}).get('inaturalist', {}).get('count', 0)
                            )
                            gallery_data['summary']['external_images'] += external_count
            
            logger.info(f"✅ Collection gallery created: {gallery_data['summary']['total_images']} total images")
            return gallery_data
            
        except Exception as e:
            logger.error(f"❌ Collection gallery creation failed: {e}")
            return {'error': str(e)}


# Initialize global aggregator instance
image_aggregator = ComprehensiveImageAggregator()

def get_image_aggregator() -> ComprehensiveImageAggregator:
    """Get the global image aggregator instance"""
    return image_aggregator