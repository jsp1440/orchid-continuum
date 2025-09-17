#!/usr/bin/env python3
"""
External Orchid Databases Integration
=====================================
GBIF and iNaturalist API clients for comprehensive orchid data integration
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import requests
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlencode
import os

logger = logging.getLogger(__name__)

class GBIFClient:
    """
    Client for Global Biodiversity Information Facility (GBIF) API
    Provides access to orchid occurrence data, images, and taxonomic information
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.orchidaceae_family_key = 7711  # GBIF key for Orchidaceae family
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (https://orchidcontinuum.org)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.1  # 100ms between requests
        
        logger.info("🌐 GBIF API client initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make authenticated request to GBIF API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data or None if error
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"GBIF API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"GBIF API request failed: {e}")
            return None
    
    def search_species(self, scientific_name: str, limit: int = 20) -> List[Dict]:
        """
        Search for orchid species in GBIF taxonomy
        
        Args:
            scientific_name: Scientific name to search for
            limit: Maximum number of results
            
        Returns:
            List of species information dictionaries
        """
        try:
            params = {
                'q': scientific_name,
                'familyKey': self.orchidaceae_family_key,
                'rank': 'SPECIES',
                'limit': limit
            }
            
            data = self._make_request('species/search', params)
            if not data:
                return []
            
            species_list = []
            for result in data.get('results', []):
                species_info = {
                    'gbif_key': result.get('key'),
                    'scientific_name': result.get('scientificName'),
                    'canonical_name': result.get('canonicalName'),
                    'genus': result.get('genus'),
                    'species': result.get('species'),
                    'authorship': result.get('authorship'),
                    'taxonomic_status': result.get('taxonomicStatus'),
                    'rank': result.get('rank'),
                    'kingdom': result.get('kingdom'),
                    'phylum': result.get('phylum'),
                    'class': result.get('class'),
                    'order': result.get('order'),
                    'family': result.get('family'),
                    'num_occurrences': result.get('numOccurrences', 0),
                    'source': 'gbif'
                }
                species_list.append(species_info)
            
            logger.info(f"🔍 Found {len(species_list)} GBIF species matches for '{scientific_name}'")
            return species_list
            
        except Exception as e:
            logger.error(f"GBIF species search failed: {e}")
            return []
    
    def get_species_details(self, gbif_key: int) -> Optional[Dict]:
        """
        Get detailed information for a species by GBIF key
        
        Args:
            gbif_key: GBIF taxonomic key
            
        Returns:
            Detailed species information or None
        """
        try:
            data = self._make_request(f'species/{gbif_key}')
            if not data:
                return None
            
            details = {
                'gbif_key': data.get('key'),
                'scientific_name': data.get('scientificName'),
                'canonical_name': data.get('canonicalName'),
                'genus': data.get('genus'),
                'species': data.get('species'),
                'authorship': data.get('authorship'),
                'taxonomic_status': data.get('taxonomicStatus'),
                'rank': data.get('rank'),
                'kingdom': data.get('kingdom'),
                'phylum': data.get('phylum'),
                'class': data.get('class'),
                'order': data.get('order'),
                'family': data.get('family'),
                'nomenclatural_status': data.get('nomenclaturalStatus', []),
                'synonyms': data.get('synonyms', []),
                'vernacular_names': data.get('vernacularNames', []),
                'descriptions': data.get('descriptions', []),
                'distributions': data.get('distributions', []),
                'source': 'gbif'
            }
            
            logger.info(f"📄 Retrieved GBIF details for key {gbif_key}")
            return details
            
        except Exception as e:
            logger.error(f"GBIF species details failed: {e}")
            return None
    
    def get_occurrences_with_images(self, gbif_key: int, limit: int = 50) -> List[Dict]:
        """
        Get occurrence records with images for a species
        
        Args:
            gbif_key: GBIF taxonomic key
            limit: Maximum number of occurrences
            
        Returns:
            List of occurrence records with image data
        """
        try:
            params = {
                'taxonKey': gbif_key,
                'hasCoordinate': True,
                'mediaType': 'StillImage',
                'limit': limit
            }
            
            data = self._make_request('occurrence/search', params)
            if not data:
                return []
            
            occurrences = []
            for record in data.get('results', []):
                
                # Extract occurrence data
                occurrence = {
                    'gbif_occurrence_key': record.get('key'),
                    'species_key': record.get('speciesKey'),
                    'scientific_name': record.get('scientificName'),
                    'decimal_latitude': record.get('decimalLatitude'),
                    'decimal_longitude': record.get('decimalLongitude'),
                    'country': record.get('country'),
                    'state_province': record.get('stateProvince'),
                    'locality': record.get('locality'),
                    'event_date': record.get('eventDate'),
                    'recorded_by': record.get('recordedBy'),
                    'collection_code': record.get('collectionCode'),
                    'catalog_number': record.get('catalogNumber'),
                    'basis_of_record': record.get('basisOfRecord'),
                    'occurrence_status': record.get('occurrenceStatus'),
                    'establishment_means': record.get('establishmentMeans'),
                    'license': record.get('license'),
                    'data_source': 'gbif',
                    'media': []
                }
                
                # Extract media/images
                if 'media' in record:
                    for media_item in record['media']:
                        if media_item.get('type') == 'StillImage':
                            media_info = {
                                'identifier': media_item.get('identifier'),
                                'title': media_item.get('title'),
                                'description': media_item.get('description'),
                                'creator': media_item.get('creator'),
                                'license': media_item.get('license'),
                                'rights_holder': media_item.get('rightsHolder'),
                                'format': media_item.get('format'),
                                'type': media_item.get('type')
                            }
                            occurrence['media'].append(media_info)
                
                if occurrence['media']:  # Only include if has images
                    occurrences.append(occurrence)
            
            logger.info(f"🖼️ Found {len(occurrences)} GBIF occurrences with images for key {gbif_key}")
            return occurrences
            
        except Exception as e:
            logger.error(f"GBIF occurrences search failed: {e}")
            return []


class iNaturalistClient:
    """
    Client for iNaturalist API
    Provides access to citizen science orchid observations and images
    """
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self.orchidaceae_taxon_id = 47217  # iNaturalist taxon ID for Orchidaceae
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum/1.0 (https://orchidcontinuum.org)',
            'Accept': 'application/json'
        })
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 0.2  # 200ms between requests
        
        logger.info("🦋 iNaturalist API client initialized")
    
    def _rate_limit(self):
        """Enforce rate limiting between API requests"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            time.sleep(self.min_request_interval - time_since_last)
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """
        Make request to iNaturalist API
        
        Args:
            endpoint: API endpoint path
            params: Query parameters
            
        Returns:
            JSON response data or None if error
        """
        try:
            self._rate_limit()
            
            url = f"{self.base_url}/{endpoint}"
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"iNaturalist API error {response.status_code}: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"iNaturalist API request failed: {e}")
            return None
    
    def search_taxa(self, scientific_name: str, limit: int = 20) -> List[Dict]:
        """
        Search for orchid taxa in iNaturalist
        
        Args:
            scientific_name: Scientific name to search for
            limit: Maximum number of results
            
        Returns:
            List of taxa information dictionaries
        """
        try:
            params = {
                'q': scientific_name,
                'rank': 'species',
                'is_active': True,
                'per_page': limit
            }
            
            data = self._make_request('taxa', params)
            if not data:
                return []
            
            taxa_list = []
            for result in data.get('results', []):
                # Check if this taxon is under Orchidaceae
                ancestors = result.get('ancestor_ids', [])
                if self.orchidaceae_taxon_id not in ancestors:
                    continue
                
                taxon_info = {
                    'inaturalist_taxon_id': result.get('id'),
                    'scientific_name': result.get('name'),
                    'rank': result.get('rank'),
                    'common_name': result.get('preferred_common_name'),
                    'observations_count': result.get('observations_count', 0),
                    'wikipedia_url': result.get('wikipedia_url'),
                    'extinct': result.get('extinct', False),
                    'iconic_taxon_name': result.get('iconic_taxon_name'),
                    'conservation_status': result.get('conservation_status'),
                    'establishment_means': result.get('establishment_means'),
                    'source': 'inaturalist'
                }
                
                # Extract taxonomy hierarchy
                if 'ancestors' in result:
                    for ancestor in result['ancestors']:
                        rank = ancestor.get('rank')
                        name = ancestor.get('name')
                        if rank == 'genus':
                            taxon_info['genus'] = name
                        elif rank == 'species':
                            taxon_info['species'] = name.split()[-1] if ' ' in name else name
                
                taxa_list.append(taxon_info)
            
            logger.info(f"🔍 Found {len(taxa_list)} iNaturalist taxa matches for '{scientific_name}'")
            return taxa_list
            
        except Exception as e:
            logger.error(f"iNaturalist taxa search failed: {e}")
            return []
    
    def get_taxon_details(self, taxon_id: int) -> Optional[Dict]:
        """
        Get detailed information for a taxon by iNaturalist ID
        
        Args:
            taxon_id: iNaturalist taxon ID
            
        Returns:
            Detailed taxon information or None
        """
        try:
            data = self._make_request(f'taxa/{taxon_id}')
            if not data:
                return None
            
            result = data.get('results', [])
            if not result:
                return None
            
            taxon = result[0]
            details = {
                'inaturalist_taxon_id': taxon.get('id'),
                'scientific_name': taxon.get('name'),
                'rank': taxon.get('rank'),
                'common_name': taxon.get('preferred_common_name'),
                'observations_count': taxon.get('observations_count', 0),
                'wikipedia_url': taxon.get('wikipedia_url'),
                'wikipedia_summary': taxon.get('wikipedia_summary'),
                'extinct': taxon.get('extinct', False),
                'iconic_taxon_name': taxon.get('iconic_taxon_name'),
                'conservation_status': taxon.get('conservation_status'),
                'establishment_means': taxon.get('establishment_means'),
                'complete_species_count': taxon.get('complete_species_count'),
                'source': 'inaturalist'
            }
            
            # Extract taxonomy hierarchy
            if 'ancestors' in taxon:
                for ancestor in taxon['ancestors']:
                    rank = ancestor.get('rank')
                    name = ancestor.get('name')
                    if rank == 'genus':
                        details['genus'] = name
                    elif rank == 'species':
                        details['species'] = name.split()[-1] if ' ' in name else name
            
            logger.info(f"📄 Retrieved iNaturalist details for taxon {taxon_id}")
            return details
            
        except Exception as e:
            logger.error(f"iNaturalist taxon details failed: {e}")
            return None
    
    def get_observations_with_photos(self, taxon_id: int, quality_grade: str = 'research', 
                                   limit: int = 50) -> List[Dict]:
        """
        Get observations with photos for a taxon
        
        Args:
            taxon_id: iNaturalist taxon ID
            quality_grade: Quality filter ('research', 'needs_id', 'casual')
            limit: Maximum number of observations
            
        Returns:
            List of observation records with photo data
        """
        try:
            params = {
                'taxon_id': taxon_id,
                'quality_grade': quality_grade,
                'photos': True,
                'geo': True,
                'per_page': limit,
                'order': 'desc',
                'order_by': 'created_at'
            }
            
            data = self._make_request('observations', params)
            if not data:
                return []
            
            observations = []
            for record in data.get('results', []):
                
                observation = {
                    'inaturalist_observation_id': record.get('id'),
                    'taxon_id': record.get('taxon', {}).get('id') if record.get('taxon') else None,
                    'scientific_name': record.get('taxon', {}).get('name') if record.get('taxon') else None,
                    'common_name': record.get('taxon', {}).get('preferred_common_name') if record.get('taxon') else None,
                    'observed_on': record.get('observed_on'),
                    'created_at': record.get('created_at'),
                    'quality_grade': record.get('quality_grade'),
                    'identifications_count': record.get('identifications_count', 0),
                    'comments_count': record.get('comments_count', 0),
                    'description': record.get('description'),
                    'place_guess': record.get('place_guess'),
                    'latitude': record.get('location', '').split(',')[0] if record.get('location') else None,
                    'longitude': record.get('location', '').split(',')[1] if record.get('location') and ',' in record.get('location', '') else None,
                    'positional_accuracy': record.get('positional_accuracy'),
                    'license_code': record.get('license_code'),
                    'data_source': 'inaturalist',
                    'photos': []
                }
                
                # Extract photo data
                if 'photos' in record:
                    for photo in record['photos']:
                        photo_info = {
                            'id': photo.get('id'),
                            'license_code': photo.get('license_code'),
                            'attribution': photo.get('attribution'),
                            'url': photo.get('url'),
                            'original_dimensions': photo.get('original_dimensions'),
                            'sizes': {}
                        }
                        
                        # Extract different size URLs
                        for size_key, size_data in photo.items():
                            if size_key.startswith('url') and size_data:
                                size_name = size_key.replace('url_', '') or 'original'
                                photo_info['sizes'][size_name] = size_data
                        
                        observation['photos'].append(photo_info)
                
                if observation['photos']:  # Only include if has photos
                    observations.append(observation)
            
            logger.info(f"🖼️ Found {len(observations)} iNaturalist observations with photos for taxon {taxon_id}")
            return observations
            
        except Exception as e:
            logger.error(f"iNaturalist observations search failed: {e}")
            return []


class ExternalOrchidDatabaseManager:
    """
    Manager class coordinating GBIF and iNaturalist integrations
    """
    
    def __init__(self):
        self.gbif_client = GBIFClient()
        self.inaturalist_client = iNaturalistClient()
        
        logger.info("🌍 External Orchid Database Manager initialized")
    
    def search_all_databases(self, scientific_name: str, limit_per_source: int = 10) -> Dict[str, List]:
        """
        Search both GBIF and iNaturalist for a species
        
        Args:
            scientific_name: Scientific name to search for
            limit_per_source: Maximum results per database
            
        Returns:
            Dictionary with results from both sources
        """
        try:
            logger.info(f"🔍 Searching all databases for '{scientific_name}'")
            
            # Search both databases in parallel (could be optimized with threading)
            gbif_results = self.gbif_client.search_species(scientific_name, limit_per_source)
            inaturalist_results = self.inaturalist_client.search_taxa(scientific_name, limit_per_source)
            
            results = {
                'gbif': gbif_results,
                'inaturalist': inaturalist_results,
                'total_found': len(gbif_results) + len(inaturalist_results),
                'search_term': scientific_name,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"📊 Combined search found {results['total_found']} results across databases")
            return results
            
        except Exception as e:
            logger.error(f"Combined database search failed: {e}")
            return {'gbif': [], 'inaturalist': [], 'total_found': 0}
    
    def get_comprehensive_species_data(self, scientific_name: str) -> Dict[str, Any]:
        """
        Get comprehensive data about a species from all sources
        
        Args:
            scientific_name: Scientific name to research
            
        Returns:
            Combined data from all sources
        """
        try:
            logger.info(f"📚 Gathering comprehensive data for '{scientific_name}'")
            
            # Search all databases
            search_results = self.search_all_databases(scientific_name, limit_per_source=5)
            
            comprehensive_data = {
                'scientific_name': scientific_name,
                'timestamp': datetime.now().isoformat(),
                'sources': {
                    'gbif': {},
                    'inaturalist': {}
                },
                'images': [],
                'occurrences': [],
                'taxonomy': {},
                'summary': {}
            }
            
            # Get detailed GBIF data
            if search_results['gbif']:
                best_gbif_match = search_results['gbif'][0]  # Take first result
                gbif_key = best_gbif_match['gbif_key']
                
                gbif_details = self.gbif_client.get_species_details(gbif_key)
                gbif_occurrences = self.gbif_client.get_occurrences_with_images(gbif_key, limit=25)
                
                comprehensive_data['sources']['gbif'] = {
                    'species_details': gbif_details,
                    'occurrences_with_images': gbif_occurrences,
                    'search_results': search_results['gbif']
                }
                
                # Extract images from GBIF
                for occurrence in gbif_occurrences:
                    for media in occurrence.get('media', []):
                        comprehensive_data['images'].append({
                            'source': 'gbif',
                            'url': media.get('identifier'),
                            'title': media.get('title'),
                            'creator': media.get('creator'),
                            'license': media.get('license'),
                            'occurrence_data': occurrence
                        })
            
            # Get detailed iNaturalist data
            if search_results['inaturalist']:
                best_inat_match = search_results['inaturalist'][0]  # Take first result
                taxon_id = best_inat_match['inaturalist_taxon_id']
                
                inat_details = self.inaturalist_client.get_taxon_details(taxon_id)
                inat_observations = self.inaturalist_client.get_observations_with_photos(taxon_id, limit=25)
                
                comprehensive_data['sources']['inaturalist'] = {
                    'taxon_details': inat_details,
                    'observations_with_photos': inat_observations,
                    'search_results': search_results['inaturalist']
                }
                
                # Extract images from iNaturalist
                for observation in inat_observations:
                    for photo in observation.get('photos', []):
                        comprehensive_data['images'].append({
                            'source': 'inaturalist',
                            'url': photo.get('url'),
                            'sizes': photo.get('sizes', {}),
                            'license': photo.get('license_code'),
                            'attribution': photo.get('attribution'),
                            'observation_data': observation
                        })
            
            # Create summary
            comprehensive_data['summary'] = {
                'total_images': len(comprehensive_data['images']),
                'gbif_occurrences': len(comprehensive_data['sources']['gbif'].get('occurrences_with_images', [])),
                'inaturalist_observations': len(comprehensive_data['sources']['inaturalist'].get('observations_with_photos', [])),
                'has_gbif_data': bool(comprehensive_data['sources']['gbif']),
                'has_inaturalist_data': bool(comprehensive_data['sources']['inaturalist'])
            }
            
            logger.info(f"✅ Comprehensive data gathered: {comprehensive_data['summary']['total_images']} images from external sources")
            return comprehensive_data
            
        except Exception as e:
            logger.error(f"Comprehensive species data gathering failed: {e}")
            return {'error': str(e)}


# Initialize global manager instance
external_db_manager = ExternalOrchidDatabaseManager()

def get_external_db_manager() -> ExternalOrchidDatabaseManager:
    """Get the global external database manager instance"""
    return external_db_manager