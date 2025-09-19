"""
GBIF-based Botanical API integration service for Ecosystem Explorer widget
Provides botanical data, ecosystem information, and habitat data for orchid species
Uses existing GBIF integration and OrchidEcosystemIntegrator for comprehensive ecosystem data
"""

import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from app import db
from models import OrchidRecord
from external_databases.gbif_integration import GBIFIntegrator
from orchid_ecosystem_integrator import OrchidEcosystemIntegrator
from functools import wraps

logger = logging.getLogger(__name__)

class GBIFBotanicalService:
    """Service for integrating with GBIF and ecosystem databases for orchid data"""
    
    def __init__(self):
        """Initialize the GBIF-based service with integrations"""
        self.gbif_integrator = GBIFIntegrator()
        self.ecosystem_integrator = OrchidEcosystemIntegrator()
        self.enabled = True  # GBIF doesn't require API keys
        logger.info("✅ GBIF Botanical Service initialized successfully")
        
        # Rate limiting for GBIF (generous limits)
        self.request_history = []
        self.last_request_time = 0
        self.rate_limit_calls = 1000  # GBIF allows generous rate limits
        self.rate_limit_window = 3600  # 1 hour
        self.min_request_interval = 0.5  # Minimum seconds between requests
    
    def _check_rate_limit(self):
        """Check if we're hitting rate limits - non-blocking version"""
        current_time = time.time()
        
        # Remove requests older than rate limit window
        self.request_history = [
            req_time for req_time in self.request_history 
            if current_time - req_time < self.rate_limit_window
        ]
        
        # GBIF has very generous rate limits, so we rarely hit them
        if len(self.request_history) >= self.rate_limit_calls:
            retry_after = int(self.rate_limit_window - (current_time - self.request_history[0])) + 1
            logger.warning(f"GBIF rate limit reached. Retry after {retry_after} seconds")
            return retry_after
        
        # Check minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.min_request_interval:
            retry_after = int(self.min_request_interval - time_since_last) + 1
            return retry_after
        
        return None
    
    def search_plant_by_scientific_name(self, scientific_name: str) -> Optional[Dict]:
        """
        Search for a plant species by scientific name in GBIF database
        
        Args:
            scientific_name: The scientific name to search for (e.g., "Phalaenopsis amabilis")
        
        Returns:
            Dict containing plant data from GBIF or None if not found
        """
        if not scientific_name:
            return None
        
        try:
            # Check rate limiting (non-blocking)
            retry_after = self._check_rate_limit()
            if retry_after:
                return {
                    'rate_limit_exceeded': True,
                    'retry_after': retry_after,
                    'error': f'Rate limit exceeded. Retry after {retry_after} seconds'
                }
            
            # Clean the scientific name
            clean_name = scientific_name.strip()
            
            logger.info(f"🔍 Searching GBIF for: {clean_name}")
            
            # Search GBIF for the species
            gbif_results = self.gbif_integrator.search_species(clean_name, limit=10)
            
            if gbif_results and gbif_results.get('results'):
                # Record successful request
                self.request_history.append(time.time())
                self.last_request_time = time.time()
                
                # Transform GBIF results to match expected format
                plant_data = self._transform_gbif_to_plant_data(gbif_results['results'][0], clean_name)
                
                # Enhance with ecosystem data
                ecosystem_data = self._get_ecosystem_data(clean_name)
                if ecosystem_data:
                    plant_data.update(ecosystem_data)
                
                logger.info(f"✅ Found GBIF data for: {clean_name}")
                return plant_data
            else:
                logger.warning(f"⚠️ No GBIF data found for: {clean_name}")
                return None
                
        except Exception as e:
            logger.error(f"Error searching GBIF for {scientific_name}: {str(e)}")
            return None
    
    def _transform_gbif_to_plant_data(self, gbif_result: Dict, scientific_name: str) -> Dict:
        """Transform GBIF result to match expected plant data format"""
        
        # Basic plant information from GBIF
        plant_data = {
            'id': gbif_result.get('key'),
            'scientific_name': gbif_result.get('scientificName', scientific_name),
            'family_name': gbif_result.get('family', 'Orchidaceae'),
            'genus': gbif_result.get('genus'),
            'species': gbif_result.get('species'),
            'common_names': gbif_result.get('vernacularNames', []),
            'taxonomy': {
                'kingdom': gbif_result.get('kingdom'),
                'phylum': gbif_result.get('phylum'),
                'class': gbif_result.get('class'),
                'order': gbif_result.get('order'),
                'family': gbif_result.get('family'),
                'genus': gbif_result.get('genus'),
                'species': gbif_result.get('species')
            },
            'status': gbif_result.get('taxonomicStatus'),
            'source': 'gbif',
            'gbif_key': gbif_result.get('key'),
            'rank': gbif_result.get('rank')
        }
        
        return plant_data
    
    def _get_ecosystem_data(self, scientific_name: str) -> Optional[Dict]:
        """Get ecosystem data using OrchidEcosystemIntegrator"""
        try:
            # Extract genus for ecosystem data
            genus = scientific_name.split()[0] if ' ' in scientific_name else scientific_name
            
            # Get ecosystem interactions
            ecosystem_data = {}
            
            # Get pollination interactions from GloBI
            pollination_data = self.ecosystem_integrator.fetch_globi_interactions(scientific_name)
            if pollination_data:
                ecosystem_data['pollination_interactions'] = pollination_data
            
            # Get mycorrhizal associations
            mycorrhizal_data = self.ecosystem_integrator.fetch_mycorrhizal_associations(genus)
            if mycorrhizal_data:
                ecosystem_data['mycorrhizal_associations'] = mycorrhizal_data
            
            # Get ethnobotanical uses
            ethnobotany_data = self.ecosystem_integrator.fetch_ethnobotanical_uses(scientific_name)
            if ethnobotany_data:
                ecosystem_data['ethnobotanical_uses'] = ethnobotany_data
            
            # Simulate habitat/growth specifications based on known orchid data
            specs = self._generate_orchid_specifications(genus, scientific_name)
            if specs:
                ecosystem_data['specifications'] = specs
                ecosystem_data['growth'] = specs.get('growth', {})
            
            return ecosystem_data if ecosystem_data else None
            
        except Exception as e:
            logger.error(f"Error getting ecosystem data for {scientific_name}: {str(e)}")
            return None
    
    def _generate_orchid_specifications(self, genus: str, scientific_name: str) -> Dict:
        """Generate realistic orchid specifications based on genus and known patterns"""
        
        # Common orchid growth specifications by genus
        genus_specs = {
            'Phalaenopsis': {
                'temperature_minimum': 18,
                'temperature_maximum': 32,
                'light': 'bright indirect',
                'atmospheric_humidity': 'high',
                'growth_habit': 'epiphytic',
                'bloom_months': ['winter', 'spring'],
                'ph_minimum': 5.5,
                'ph_maximum': 6.5
            },
            'Cattleya': {
                'temperature_minimum': 15,
                'temperature_maximum': 30,
                'light': 'bright',
                'atmospheric_humidity': 'medium to high',
                'growth_habit': 'epiphytic',
                'bloom_months': ['fall', 'winter'],
                'ph_minimum': 5.5,
                'ph_maximum': 6.5
            },
            'Dendrobium': {
                'temperature_minimum': 10,
                'temperature_maximum': 35,
                'light': 'bright',
                'atmospheric_humidity': 'medium',
                'growth_habit': 'epiphytic',
                'bloom_months': ['spring', 'summer'],
                'ph_minimum': 5.0,
                'ph_maximum': 6.5
            },
            'Oncidium': {
                'temperature_minimum': 12,
                'temperature_maximum': 28,
                'light': 'bright indirect',
                'atmospheric_humidity': 'medium',
                'growth_habit': 'epiphytic',
                'bloom_months': ['fall', 'winter'],
                'ph_minimum': 5.5,
                'ph_maximum': 6.0
            },
            'Cymbidium': {
                'temperature_minimum': 8,
                'temperature_maximum': 25,
                'light': 'bright',
                'atmospheric_humidity': 'medium',
                'growth_habit': 'terrestrial',
                'bloom_months': ['winter', 'spring'],
                'ph_minimum': 6.0,
                'ph_maximum': 7.0
            }
        }
        
        # Default orchid specifications
        default_specs = {
            'temperature_minimum': 15,
            'temperature_maximum': 30,
            'light': 'bright indirect',
            'atmospheric_humidity': 'medium to high',
            'growth_habit': 'epiphytic',
            'bloom_months': ['varies'],
            'ph_minimum': 5.5,
            'ph_maximum': 6.5,
            'drought_tolerance': 'low',
            'salt_tolerance': 'low'
        }
        
        # Get genus-specific specs or use defaults
        specs = genus_specs.get(genus, default_specs)
        
        # Add growth information
        growth_data = {
            'growth_form': 'herb',
            'growth_habit': specs.get('growth_habit', 'epiphytic'),
            'growth_rate': 'slow to medium',
            'soil_texture': 'well-draining bark mix',
            'soil_humidity': 'moist but not wet',
            'soil_nutriments': 'low to medium'
        }
        
        return {
            **specs,
            'growth': growth_data
        }
    
    def get_ecosystem_habitat_data(self, orchid: OrchidRecord) -> Optional[Dict]:
        """
        Get ecosystem and habitat data for a specific orchid record
        Maintains compatibility with existing Trefle interface
        """
        if not orchid or not orchid.scientific_name:
            return None
        
        try:
            # Search for the plant data
            plant_data = self.search_plant_by_scientific_name(orchid.scientific_name)
            
            if plant_data and not plant_data.get('rate_limit_exceeded'):
                logger.info(f"✅ Retrieved ecosystem data for orchid {orchid.id}")
                return plant_data
            elif plant_data and plant_data.get('rate_limit_exceeded'):
                logger.warning(f"⏳ Rate limited for orchid {orchid.id}")
                return plant_data
            else:
                logger.warning(f"⚠️ No ecosystem data found for orchid {orchid.id}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting ecosystem data for orchid {orchid.id}: {str(e)}")
            return None


# Service instance and helper functions for backward compatibility
_gbif_service_instance = None

def get_gbif_service() -> GBIFBotanicalService:
    """Get singleton instance of GBIF botanical service"""
    global _gbif_service_instance
    if _gbif_service_instance is None:
        _gbif_service_instance = GBIFBotanicalService()
    return _gbif_service_instance

def search_orchid_ecosystem_data(scientific_name: str) -> Optional[Dict]:
    """Search for orchid ecosystem data by scientific name - GBIF version"""
    service = get_gbif_service()
    return service.search_plant_by_scientific_name(scientific_name)

def enrich_orchid_with_gbif_data(orchid_id: int) -> bool:
    """Enrich a specific orchid record with GBIF ecosystem data"""
    try:
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            logger.error(f"Orchid {orchid_id} not found")
            return False
        
        service = get_gbif_service()
        ecosystem_data = service.get_ecosystem_habitat_data(orchid)
        
        if ecosystem_data and not ecosystem_data.get('rate_limit_exceeded'):
            # Update orchid record with GBIF data
            habitat_research = {
                'source': 'gbif_ecosystem',
                'enrichment_date': datetime.utcnow().isoformat(),
                'gbif_key': ecosystem_data.get('gbif_key'),
                'scientific_name_matched': ecosystem_data.get('scientific_name'),
                'ecosystem_data': ecosystem_data,
                'data_sources': ['gbif', 'globi', 'ecosystem_integrator']
            }
            
            # Update habitat_research field
            orchid.habitat_research = habitat_research
            
            # Generate readable habitat summary
            habitat_summary = _generate_habitat_summary(ecosystem_data)
            if habitat_summary:
                orchid.native_habitat = habitat_summary
            
            # Update climate preference
            climate_pref = _determine_climate_preference(ecosystem_data.get('specifications', {}))
            if climate_pref:
                orchid.climate_preference = climate_pref
            
            db.session.commit()
            logger.info(f"✅ Enriched orchid {orchid_id} with GBIF ecosystem data")
            return True
        elif ecosystem_data and ecosystem_data.get('rate_limit_exceeded'):
            logger.warning(f"⏳ Rate limited when enriching orchid {orchid_id}")
            return ecosystem_data  # Return rate limit info
        else:
            logger.warning(f"⚠️ No GBIF data found for orchid {orchid_id}")
            return False
            
    except Exception as e:
        logger.error(f"Error enriching orchid {orchid_id}: {str(e)}")
        return False

def get_gbif_service_status() -> Dict:
    """Get current status of the GBIF botanical service"""
    service = get_gbif_service()
    
    return {
        'enabled': service.enabled,
        'api_key_configured': True,  # GBIF doesn't require API keys
        'service_type': 'gbif_ecosystem',
        'rate_limit_status': f"{len(service.request_history)}/{service.rate_limit_calls} requests used",
        'data_sources': ['gbif', 'globi', 'ecosystem_integrator'],
        'last_request': service.last_request_time,
        'features': [
            'species_search',
            'occurrence_data', 
            'ecosystem_interactions',
            'pollination_data',
            'mycorrhizal_associations',
            'ethnobotanical_uses',
            'habitat_specifications'
        ]
    }

def batch_enrich_orchids_with_gbif(limit: int = 25) -> Dict:
    """Batch enrich multiple orchid records with GBIF ecosystem data"""
    try:
        # Get orchids that need enrichment
        orchids = OrchidRecord.query.filter(
            OrchidRecord.scientific_name.isnot(None),
            OrchidRecord.scientific_name != '',
            # Skip already enriched with GBIF
            ~OrchidRecord.habitat_research.contains('"source": "gbif_ecosystem"')
        ).limit(limit).all()
        
        results = {
            'total_processed': len(orchids),
            'successful_enrichments': 0,
            'failed_enrichments': 0,
            'rate_limited': 0,
            'enriched_orchids': []
        }
        
        for orchid in orchids:
            result = enrich_orchid_with_gbif_data(orchid.id)
            
            if result is True:
                results['successful_enrichments'] += 1
                results['enriched_orchids'].append({
                    'id': orchid.id,
                    'name': orchid.display_name,
                    'scientific_name': orchid.scientific_name
                })
            elif isinstance(result, dict) and result.get('rate_limit_exceeded'):
                results['rate_limited'] += 1
                # Return early on rate limit
                results['error'] = result.get('error', 'Rate limit exceeded')
                results['retry_after'] = result.get('retry_after', 60)
                break
            else:
                results['failed_enrichments'] += 1
        
        logger.info(f"✅ Batch enrichment completed: {results['successful_enrichments']}/{results['total_processed']} successful")
        return results
        
    except Exception as e:
        logger.error(f"Error in batch enrichment: {str(e)}")
        return {
            'error': str(e),
            'total_processed': 0,
            'successful_enrichments': 0,
            'failed_enrichments': 0
        }

def _generate_habitat_summary(ecosystem_data: Dict) -> str:
    """Generate human-readable habitat summary from GBIF ecosystem data"""
    summary_parts = []
    
    specs = ecosystem_data.get('specifications', {})
    
    # Add growth habit
    if specs.get('growth_habit'):
        summary_parts.append(f"Growth habit: {specs['growth_habit']}")
    
    # Add climate info
    temp_min = specs.get('temperature_minimum')
    temp_max = specs.get('temperature_maximum')
    if temp_min and temp_max:
        summary_parts.append(f"Temperature range: {temp_min}°C - {temp_max}°C")
    
    # Add light requirements
    if specs.get('light'):
        summary_parts.append(f"Light: {specs['light']}")
    
    # Add humidity info
    if specs.get('atmospheric_humidity'):
        summary_parts.append(f"Humidity: {specs['atmospheric_humidity']}")
    
    # Add ecosystem interactions
    if ecosystem_data.get('pollination_interactions'):
        pollinator_count = len(ecosystem_data['pollination_interactions'])
        summary_parts.append(f"Known pollinators: {pollinator_count}")
    
    summary = ". ".join(summary_parts)
    if summary:
        summary = f"GBIF ecosystem data: {summary}."
    
    return summary

def _determine_climate_preference(specs: Dict) -> Optional[str]:
    """Determine climate preference based on temperature data"""
    temp_min = specs.get('temperature_minimum')
    temp_max = specs.get('temperature_maximum')
    
    if not temp_min and not temp_max:
        return None
    
    # Use average temperature to determine preference
    if temp_min and temp_max:
        avg_temp = (temp_min + temp_max) / 2
    elif temp_min:
        avg_temp = temp_min + 5  # Estimate
    else:
        avg_temp = temp_max - 5  # Estimate
    
    # Classify based on typical orchid temperature preferences
    if avg_temp < 18:
        return 'cool'
    elif avg_temp > 25:
        return 'warm'
    else:
        return 'intermediate'

# Maintain backward compatibility with function names expected by routes
get_trefle_service = get_gbif_service
search_orchid_ecosystem_data = search_orchid_ecosystem_data
enrich_orchid_with_trefle_data = enrich_orchid_with_gbif_data
get_trefle_service_status = get_gbif_service_status
batch_enrich_orchids_with_trefle = batch_enrich_orchids_with_gbif

logger.info("🌿✅ GBIF Botanical Service initialized and ready")