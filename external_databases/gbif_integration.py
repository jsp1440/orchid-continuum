#!/usr/bin/env python3
"""
GBIF (Global Biodiversity Information Facility) Integration Module
==================================================================
Comprehensive integration with GBIF's API for orchid data enhancement
Enhanced for conservation research and global biodiversity analysis
"""

import os
import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GBIFIntegrator:
    """
    GBIF API integration for orchid data enhancement and global occurrence data
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.rate_limit_delay = 1  # GBIF allows generous rate limits
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society Continuum Platform (Research)',
            'Accept': 'application/json'
        })
        
        # Cache for commonly used data
        self.orchidaceae_family_key = None
        self._get_orchidaceae_key()
        
        # High-occurrence orchid genera for targeted searches
        self.target_genera = [
            'Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium', 'Cymbidium',
            'Orchis', 'Ophrys', 'Epidendrum', 'Bulbophyllum', 'Masdevallia',
            'Paphiopedilum', 'Vanda', 'Aerangis', 'Angraecum', 'Brassia',
            'Dactylorhiza', 'Platanthera', 'Gymnadenia', 'Epipactis', 'Vanilla'
        ]
        
        # Proven high-occurrence species for image searches
        self.target_species = [
            'Orchis maculata', 'Dactylorhiza maculata', 'Phalaenopsis amabilis',
            'Dendrobium nobile', 'Cattleya labiata', 'Vanilla planifolia',
            'Cypripedium calceolus', 'Ophrys apifera', 'Orchis mascula'
        ]
        
    def _get_orchidaceae_key(self):
        """Find the correct GBIF family key for Orchidaceae"""
        try:
            params = {
                'q': 'Orchidaceae',
                'rank': 'FAMILY',
                'limit': 10
            }
            
            response = self.session.get(f"{self.base_url}/species/search", 
                                       params=params, timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                families = data.get('results', [])
                
                for family in families:
                    if (family.get('scientificName') == 'Orchidaceae' and 
                        family.get('taxonomicStatus') == 'ACCEPTED'):
                        self.orchidaceae_family_key = family.get('key')
                        logger.info(f"🌺 Found Orchidaceae family key: {self.orchidaceae_family_key}")
                        return
                
                # Fallback - try any Orchidaceae entry
                for family in families:
                    if 'Orchidaceae' in family.get('scientificName', ''):
                        self.orchidaceae_family_key = family.get('key')
                        logger.warning(f"⚠️ Using fallback Orchidaceae key: {self.orchidaceae_family_key}")
                        return
            
            logger.error("❌ Could not find Orchidaceae family key!")
            self.orchidaceae_family_key = 3925978  # Known good key as fallback
            
        except Exception as e:
            logger.error(f"❌ Error finding family key: {e}")
            self.orchidaceae_family_key = 3925978  # Known good key as fallback
    
    def search_species(self, query: str, limit: int = 20) -> Optional[Dict]:
        """
        Search for orchid species in GBIF
        
        Args:
            query: Scientific name or common name to search for
            limit: Maximum number of results to return
            
        Returns:
            Dictionary with GBIF search results or None if error
        """
        try:
            params = {
                'q': query,
                'rank': ['SPECIES', 'SUBSPECIES', 'VARIETY'],
                'highertaxon': 'Orchidaceae',
                'limit': min(limit, 100)
            }
            
            logger.info(f"🔍 Searching GBIF species for: {query}")
            response = self.session.get(f"{self.base_url}/species/search", 
                                       params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            # Filter to ensure results are actually orchids
            orchid_results = []
            for result in data.get('results', []):
                if ('Orchidaceae' in str(result.get('family', '')) or 
                    'Orchidaceae' in str(result.get('familyKey', ''))):
                    orchid_results.append(result)
            
            if orchid_results:
                logger.info(f"✅ Found {len(orchid_results)} orchid species for '{query}'")
                return {
                    'count': len(orchid_results),
                    'results': orchid_results[:limit],
                    'query': query
                }
            else:
                logger.warning(f"⚠️ No orchid species found for '{query}'")
                return None
                
        except Exception as e:
            logger.error(f"❌ GBIF species search failed for '{query}': {str(e)}")
            return None
    
    def get_occurrences(self, scientific_name: str = None, species_key: str = None, 
                       limit: int = 50, with_images: bool = True) -> Optional[Dict]:
        """
        Get occurrence records for a species
        
        Args:
            scientific_name: Scientific name of the species
            species_key: GBIF species key (alternative to scientific_name)
            limit: Maximum number of occurrences to return
            with_images: Filter to only occurrences with images
            
        Returns:
            Dictionary with occurrence data or None if error
        """
        try:
            params = {
                'limit': min(limit, 300),
                'hasCoordinate': True,
                'hasGeospatialIssue': False
            }
            
            if scientific_name:
                params['scientificName'] = scientific_name
            elif species_key:
                params['speciesKey'] = species_key
            else:
                logger.error("❌ Must provide either scientific_name or species_key")
                return None
                
            if with_images:
                params['mediaType'] = 'StillImage'
                
            logger.info(f"🔍 Searching GBIF occurrences for: {scientific_name or species_key}")
            response = self.session.get(f"{self.base_url}/occurrence/search", 
                                       params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            
            # Process and enhance occurrence data
            processed_occurrences = []
            for occurrence in data.get('results', []):
                processed = self._process_occurrence(occurrence)
                if processed:
                    processed_occurrences.append(processed)
            
            if processed_occurrences:
                logger.info(f"✅ Found {len(processed_occurrences)} occurrences")
                return {
                    'count': data.get('count', 0),
                    'results': processed_occurrences,
                    'query': scientific_name or species_key
                }
            else:
                logger.warning(f"⚠️ No valid occurrences found")
                return None
                
        except Exception as e:
            logger.error(f"❌ GBIF occurrence search failed: {str(e)}")
            return None
    
    def get_taxonomy(self, species_key: str) -> Optional[Dict]:
        """
        Get detailed taxonomic information for a species
        
        Args:
            species_key: GBIF species key
            
        Returns:
            Dictionary with taxonomic data or None if error
        """
        try:
            # Get main species data
            response = self.session.get(f"{self.base_url}/species/{species_key}", timeout=15)
            response.raise_for_status()
            
            species_data = response.json()
            
            # Get vernacular names
            vernacular_response = self.session.get(
                f"{self.base_url}/species/{species_key}/vernacularNames", timeout=10)
            vernacular_names = []
            if vernacular_response.status_code == 200:
                vernacular_data = vernacular_response.json()
                vernacular_names = vernacular_data.get('results', [])
            
            # Get synonyms
            synonyms_response = self.session.get(
                f"{self.base_url}/species/{species_key}/synonyms", timeout=10)
            synonyms = []
            if synonyms_response.status_code == 200:
                synonyms_data = synonyms_response.json()
                synonyms = synonyms_data.get('results', [])
            
            taxonomy = {
                'gbif_key': species_key,
                'scientific_name': species_data.get('scientificName'),
                'canonical_name': species_data.get('canonicalName'),
                'author': species_data.get('authorship'),
                'rank': species_data.get('rank'),
                'taxonomic_status': species_data.get('taxonomicStatus'),
                'kingdom': species_data.get('kingdom'),
                'phylum': species_data.get('phylum'),
                'class': species_data.get('class'),
                'order': species_data.get('order'),
                'family': species_data.get('family'),
                'genus': species_data.get('genus'),
                'species': species_data.get('species'),
                'vernacular_names': vernacular_names,
                'synonyms': synonyms,
                'last_updated': datetime.now().isoformat()
            }
            
            logger.info(f"✅ Retrieved taxonomy for {species_data.get('scientificName')}")
            return taxonomy
            
        except Exception as e:
            logger.error(f"❌ Failed to get taxonomy for species {species_key}: {str(e)}")
            return None
    
    def _process_occurrence(self, occurrence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process and enhance GBIF occurrence data
        
        Args:
            occurrence: Raw GBIF occurrence record
            
        Returns:
            Processed occurrence data or None if invalid
        """
        try:
            # Verify it's an orchid
            family = occurrence.get('family', '').lower()
            if 'orchidaceae' not in family:
                return None
            
            # Extract location data
            latitude = occurrence.get('decimalLatitude')
            longitude = occurrence.get('decimalLongitude')
            country = occurrence.get('country')
            state_province = occurrence.get('stateProvince')
            locality = occurrence.get('locality')
            
            # Extract media information
            images = []
            media_list = occurrence.get('media', [])
            for media in media_list:
                if media.get('type') == 'StillImage':
                    image_data = {
                        'url': media.get('identifier'),
                        'title': media.get('title'),
                        'creator': media.get('creator'),
                        'license': media.get('license'),
                        'rights_holder': media.get('rightsHolder')
                    }
                    images.append(image_data)
            
            # Extract collection data
            collection_data = {
                'institution_code': occurrence.get('institutionCode'),
                'collection_code': occurrence.get('collectionCode'),
                'catalog_number': occurrence.get('catalogNumber'),
                'recorded_by': occurrence.get('recordedBy'),
                'record_number': occurrence.get('recordNumber'),
                'event_date': occurrence.get('eventDate'),
                'basis_of_record': occurrence.get('basisOfRecord')
            }
            
            processed = {
                'gbif_key': occurrence.get('key'),
                'scientific_name': occurrence.get('scientificName'),
                'taxonomic_status': occurrence.get('taxonomicStatus'),
                'kingdom': occurrence.get('kingdom'),
                'family': occurrence.get('family'),
                'genus': occurrence.get('genus'),
                'species': occurrence.get('species'),
                'subspecies': occurrence.get('subspecies'),
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'country': country,
                    'state_province': state_province,
                    'locality': locality,
                    'coordinate_uncertainty': occurrence.get('coordinateUncertaintyInMeters'),
                    'elevation': occurrence.get('elevation')
                },
                'images': images,
                'collection': collection_data,
                'dataset_key': occurrence.get('datasetKey'),
                'publisher': occurrence.get('publishingOrgKey'),
                'last_interpreted': occurrence.get('lastInterpreted'),
                'gbif_url': f"https://www.gbif.org/occurrence/{occurrence.get('key')}"
            }
            
            return processed
            
        except Exception as e:
            logger.error(f"❌ Error processing occurrence: {str(e)}")
            return None
    
    def search_high_occurrence_orchids(self, limit: int = 100) -> Dict[str, Any]:
        """
        Search for orchids with high occurrence rates and good image availability
        
        Args:
            limit: Maximum number of results per species
            
        Returns:
            Dictionary with high-quality orchid occurrence data
        """
        try:
            all_results = []
            
            for species in self.target_species[:5]:  # Limit to top 5 for performance
                time.sleep(self.rate_limit_delay)
                
                occurrences = self.get_occurrences(
                    scientific_name=species,
                    limit=min(limit, 50),
                    with_images=True
                )
                
                if occurrences and occurrences.get('results'):
                    all_results.extend(occurrences['results'])
                    logger.info(f"✅ Added {len(occurrences['results'])} records for {species}")
            
            return {
                'total_found': len(all_results),
                'results': all_results,
                'species_searched': self.target_species[:5],
                'search_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ High occurrence search failed: {str(e)}")
            return {'total_found': 0, 'results': [], 'error': str(e)}
    
    def get_species_images(self, scientific_name: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get images for a specific orchid species
        
        Args:
            scientific_name: Scientific name of the orchid
            limit: Maximum number of images to return
            
        Returns:
            List of image data dictionaries
        """
        try:
            occurrences = self.get_occurrences(
                scientific_name=scientific_name,
                limit=limit * 2,  # Get more occurrences to find images
                with_images=True
            )
            
            images = []
            if occurrences and occurrences.get('results'):
                for occurrence in occurrences['results']:
                    occurrence_images = occurrence.get('images', [])
                    for image in occurrence_images:
                        if len(images) >= limit:
                            break
                        
                        image_data = {
                            'url': image.get('url'),
                            'title': image.get('title'),
                            'creator': image.get('creator'),
                            'license': image.get('license'),
                            'rights_holder': image.get('rights_holder'),
                            'occurrence_key': occurrence.get('gbif_key'),
                            'location': occurrence.get('location', {}),
                            'source': 'GBIF'
                        }
                        images.append(image_data)
                    
                    if len(images) >= limit:
                        break
            
            logger.info(f"✅ Found {len(images)} images for {scientific_name}")
            return images
            
        except Exception as e:
            logger.error(f"❌ Error getting images for {scientific_name}: {str(e)}")
            return []
    
    def get_conservation_status(self, species_key: str) -> Dict[str, Any]:
        """
        Get conservation status information for a species
        
        Args:
            species_key: GBIF species key
            
        Returns:
            Dictionary with conservation status data
        """
        try:
            # Note: GBIF doesn't directly provide conservation status
            # This method provides framework for future IUCN integration
            
            # Get species data first
            species_data = self.get_taxonomy(species_key)
            if not species_data:
                return {}
            
            # Get occurrence count as a proxy for abundance
            occurrences = self.get_occurrences(species_key=species_key, limit=1)
            occurrence_count = occurrences.get('count', 0) if occurrences else 0
            
            # Basic conservation indicators based on occurrence data
            if occurrence_count == 0:
                status_indicator = 'No records'
            elif occurrence_count < 10:
                status_indicator = 'Very rare'
            elif occurrence_count < 100:
                status_indicator = 'Rare'
            elif occurrence_count < 1000:
                status_indicator = 'Uncommon'
            else:
                status_indicator = 'Common'
            
            return {
                'occurrence_count': occurrence_count,
                'status_indicator': status_indicator,
                'scientific_name': species_data.get('scientific_name'),
                'last_updated': datetime.now().isoformat(),
                'note': 'Based on GBIF occurrence data only'
            }
            
        except Exception as e:
            logger.error(f"❌ Error getting conservation status: {str(e)}")
            return {}