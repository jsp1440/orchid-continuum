"""
Trefle Botanical API integration service for Ecosystem Explorer widget
Provides botanical data, ecosystem information, and habitat data for orchid species
"""

import requests
import json
import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from app import db
from models import OrchidRecord
from functools import wraps

logger = logging.getLogger(__name__)

class TrefleBotanicalService:
    """Service for integrating with Trefle.io botanical database"""
    
    BASE_URL = "https://trefle.io/api/v1"
    PLANTS_ENDPOINT = f"{BASE_URL}/plants"
    SPECIES_ENDPOINT = f"{BASE_URL}/species"
    
    # Rate limiting configuration
    RATE_LIMIT_CALLS = 120  # Max calls per hour for free tier
    RATE_LIMIT_WINDOW = 3600  # 1 hour in seconds
    MIN_REQUEST_INTERVAL = 0.5  # Minimum seconds between requests
    
    def __init__(self):
        """Initialize the Trefle service with API key from environment"""
        self.api_key = os.environ.get('TREFLE_API_KEY')
        if not self.api_key:
            logger.warning("TREFLE_API_KEY environment variable not set. Trefle integration disabled.")
            self.enabled = False
        else:
            self.enabled = True
            logger.info("✅ Trefle Botanical Service initialized successfully")
        
        # Rate limiting tracking
        self.request_history = []
        self.last_request_time = 0
    
    def _check_rate_limit(self):
        """Check if we're hitting rate limits - non-blocking version"""
        if not self.enabled:
            return None
        
        current_time = time.time()
        
        # Remove requests older than rate limit window
        self.request_history = [
            req_time for req_time in self.request_history 
            if current_time - req_time < self.RATE_LIMIT_WINDOW
        ]
        
        # Check if we've exceeded rate limit
        if len(self.request_history) >= self.RATE_LIMIT_CALLS:
            retry_after = int(self.RATE_LIMIT_WINDOW - (current_time - self.request_history[0])) + 1
            logger.warning(f"Rate limit reached. Retry after {retry_after} seconds")
            return retry_after
        
        # Check minimum interval between requests
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.MIN_REQUEST_INTERVAL:
            retry_after = int(self.MIN_REQUEST_INTERVAL - time_since_last) + 1
            logger.warning(f"Request interval too short. Retry after {retry_after} seconds")
            return retry_after
        
        return None
    
    def _make_api_request(self, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make a rate-limited API request to Trefle"""
        if not self.enabled:
            logger.warning("Trefle API not enabled - check TREFLE_API_KEY environment variable")
            return None
        
        try:
            # Check rate limiting (non-blocking)
            retry_after = self._check_rate_limit()
            if retry_after:
                # Return a special response indicating rate limit hit
                return {
                    'rate_limit_exceeded': True,
                    'retry_after': retry_after,
                    'error': f'Rate limit exceeded. Retry after {retry_after} seconds'
                }
            
            # Prepare parameters
            if params is None:
                params = {}
            
            params['token'] = self.api_key
            
            # Make request
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                # Record successful request
                self.request_history.append(time.time())
                self.last_request_time = time.time()
                return response.json()
            elif response.status_code == 401:
                logger.error("Trefle API authentication failed - check TREFLE_API_KEY")
                return None
            elif response.status_code == 429:
                logger.warning("Trefle API rate limit exceeded by server")
                retry_after = response.headers.get('Retry-After', '60')
                return {
                    'rate_limit_exceeded': True,
                    'retry_after': int(retry_after),
                    'error': f'Server rate limit exceeded. Retry after {retry_after} seconds'
                }
            else:
                logger.error(f"Trefle API request failed: {response.status_code} - {response.text}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error making Trefle API request: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Trefle API request: {str(e)}")
            return None
    
    def search_plant_by_scientific_name(self, scientific_name: str) -> Optional[Dict]:
        """
        Search for a plant species by scientific name in Trefle database
        
        Args:
            scientific_name: The scientific name to search for (e.g., "Phalaenopsis amabilis")
        
        Returns:
            Dict containing plant data from Trefle or None if not found
        """
        if not scientific_name or not self.enabled:
            return None
        
        try:
            # Clean the scientific name
            clean_name = scientific_name.strip()
            
            # Search parameters
            params = {
                'q': clean_name,
                'filter[family]': 'Orchidaceae',  # Filter to orchids only
                'page[size]': 10  # Limit results
            }
            
            logger.info(f"🔍 Searching Trefle for orchid: {clean_name}")
            
            # Make API request
            data = self._make_api_request(self.PLANTS_ENDPOINT, params)
            
            # Check for rate limit response first
            if data and data.get('rate_limit_exceeded'):
                # Propagate rate limit status instead of treating as "no results"
                logger.warning(f"🚫 Rate limit exceeded for: {clean_name}")
                return {
                    'status': 'rate_limited',
                    'retry_after': data.get('retry_after'),
                    'error': data.get('error'),
                    'scientific_name': clean_name
                }
            
            if not data or not data.get('data'):
                logger.info(f"❌ No Trefle results found for: {clean_name}")
                return None
            
            # Look for exact or close matches
            for plant in data['data']:
                if plant.get('scientific_name'):
                    plant_name = plant['scientific_name'].lower()
                    search_name = clean_name.lower()
                    
                    # Exact match
                    if plant_name == search_name:
                        logger.info(f"✅ Found exact Trefle match: {plant['scientific_name']}")
                        return self._enrich_plant_data(plant)
                    
                    # Partial match (genus + species)
                    if ' ' in search_name and plant_name.startswith(search_name.split()[0]):
                        genus_species = ' '.join(search_name.split()[:2])
                        if plant_name.startswith(genus_species):
                            logger.info(f"✅ Found genus+species Trefle match: {plant['scientific_name']}")
                            return self._enrich_plant_data(plant)
            
            # If no exact match, return the first orchid result
            first_result = data['data'][0]
            if first_result.get('family_name', '').lower() == 'orchidaceae':
                logger.info(f"🟡 Using closest Trefle orchid match: {first_result.get('scientific_name')}")
                return self._enrich_plant_data(first_result)
            
            logger.info(f"❌ No suitable orchid matches in Trefle for: {clean_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error searching Trefle for {scientific_name}: {str(e)}")
            return None
    
    def _enrich_plant_data(self, plant_data: Dict) -> Dict:
        """
        Enrich basic plant data with detailed species information
        
        Args:
            plant_data: Basic plant data from search results
        
        Returns:
            Enriched plant data with detailed ecosystem information
        """
        if not plant_data.get('id') or not self.enabled:
            return plant_data
        
        try:
            # Get detailed species information
            species_url = f"{self.BASE_URL}/plants/{plant_data['id']}"
            detailed_data = self._make_api_request(species_url)
            
            if detailed_data and detailed_data.get('data'):
                # Merge basic and detailed data
                enriched_data = {**plant_data, **detailed_data['data']}
                logger.info(f"✅ Enriched plant data for: {enriched_data.get('scientific_name')}")
                return enriched_data
            else:
                logger.warning(f"Failed to get detailed data for plant ID: {plant_data['id']}")
                return plant_data
            
        except Exception as e:
            logger.error(f"Error enriching plant data: {str(e)}")
            return plant_data
    
    def get_ecosystem_habitat_data(self, orchid_record: OrchidRecord) -> Dict:
        """
        Retrieve comprehensive ecosystem and habitat data for an orchid
        
        Args:
            orchid_record: OrchidRecord instance to get ecosystem data for
        
        Returns:
            Dict containing ecosystem and habitat information
        """
        if not orchid_record or not self.enabled:
            return {}
        
        try:
            # Try different name variations for better matching
            names_to_try = []
            
            if hasattr(orchid_record, 'scientific_name') and orchid_record.scientific_name:
                names_to_try.append(orchid_record.scientific_name)
            
            if (hasattr(orchid_record, 'genus') and orchid_record.genus and 
                hasattr(orchid_record, 'species') and orchid_record.species):
                genus_species = f"{orchid_record.genus} {orchid_record.species}"
                if genus_species not in names_to_try:
                    names_to_try.append(genus_species)
            
            if orchid_record.display_name and orchid_record.display_name != orchid_record.scientific_name:
                names_to_try.append(orchid_record.display_name)
            
            logger.info(f"🌿 Getting ecosystem data for orchid ID {orchid_record.id}: {names_to_try}")
            
            # Try each name variation
            plant_data = None
            for name in names_to_try:
                plant_data = self.search_plant_by_scientific_name(name)
                if plant_data:
                    # Check if this is a rate limit response
                    if isinstance(plant_data, dict) and plant_data.get('rate_limit_exceeded'):
                        logger.warning(f"Rate limit hit while searching for orchid {orchid_record.id}")
                        return plant_data  # Return rate limit info to caller
                    break
            
            if not plant_data:
                logger.info(f"❌ No Trefle data found for orchid {orchid_record.id}")
                return {}
            
            # Extract ecosystem information
            ecosystem_data = self._extract_ecosystem_data(plant_data, orchid_record)
            
            logger.info(f"✅ Retrieved ecosystem data for orchid {orchid_record.id}")
            return ecosystem_data
            
        except Exception as e:
            logger.error(f"Error getting ecosystem data for orchid {orchid_record.id}: {str(e)}")
            return {}
    
    def _extract_ecosystem_data(self, plant_data: Dict, orchid_record: OrchidRecord) -> Dict:
        """
        Extract and format ecosystem data from Trefle plant data
        
        Args:
            plant_data: Raw plant data from Trefle API
            orchid_record: The orchid record being enriched
        
        Returns:
            Formatted ecosystem data for integration with OrchidRecord
        """
        try:
            ecosystem_data = {
                'trefle_id': plant_data.get('id'),
                'trefle_scientific_name': plant_data.get('scientific_name'),
                'trefle_common_name': plant_data.get('common_name'),
                'family_name': plant_data.get('family_name'),
                'genus_name': plant_data.get('genus_name'),
                'updated_at': datetime.utcnow().isoformat(),
                'data_source': 'trefle.io',
                
                # Growth characteristics
                'growth_form': plant_data.get('main_species', {}).get('growth', {}),
                'flower_characteristics': plant_data.get('main_species', {}).get('flower', {}),
                'foliage_characteristics': plant_data.get('main_species', {}).get('foliage', {}),
                
                # Environmental requirements  
                'light_requirements': self._extract_light_data(plant_data),
                'water_requirements': self._extract_water_data(plant_data),
                'soil_requirements': self._extract_soil_data(plant_data),
                'climate_data': self._extract_climate_data(plant_data),
                
                # Distribution and habitat
                'native_distribution': plant_data.get('main_species', {}).get('distribution', {}),
                'habitat_description': self._extract_habitat_description(plant_data),
                
                # Conservation and status
                'conservation_status': plant_data.get('main_species', {}).get('status', {}),
                
                # Ecological relationships
                'ecological_niche': self._extract_ecological_niche(plant_data),
                
                # Raw Trefle data for reference
                'raw_trefle_data': plant_data
            }
            
            # Add specific orchid ecosystem insights
            ecosystem_data['orchid_ecosystem_insights'] = self._generate_orchid_insights(ecosystem_data, orchid_record)
            
            return ecosystem_data
            
        except Exception as e:
            logger.error(f"Error extracting ecosystem data: {str(e)}")
            return {'error': str(e), 'data_source': 'trefle.io'}
    
    def _extract_light_data(self, plant_data: Dict) -> Dict:
        """Extract light requirement information"""
        try:
            specifications = plant_data.get('main_species', {}).get('specifications', {})
            return {
                'light_minimum': specifications.get('light'),
                'shade_tolerance': specifications.get('shade_tolerance'),
                'recommendations': 'Orchids typically prefer bright, indirect light'
            }
        except:
            return {}
    
    def _extract_water_data(self, plant_data: Dict) -> Dict:
        """Extract water requirement information"""
        try:
            specifications = plant_data.get('main_species', {}).get('specifications', {})
            return {
                'drought_tolerance': specifications.get('drought_tolerance'),
                'moisture_requirements': specifications.get('moisture_use'),
                'recommendations': 'Most orchids prefer good drainage with regular watering'
            }
        except:
            return {}
    
    def _extract_soil_data(self, plant_data: Dict) -> Dict:
        """Extract soil and substrate requirements"""
        try:
            specifications = plant_data.get('main_species', {}).get('specifications', {})
            return {
                'soil_requirements': specifications.get('soil_nutriments'),
                'ph_requirements': specifications.get('soil_ph'),
                'substrate_notes': 'Orchids typically grow as epiphytes or in well-draining organic substrates'
            }
        except:
            return {}
    
    def _extract_climate_data(self, plant_data: Dict) -> Dict:
        """Extract climate and temperature information"""
        try:
            specifications = plant_data.get('main_species', {}).get('specifications', {})
            growth = plant_data.get('main_species', {}).get('growth', {})
            
            return {
                'temperature_minimum': specifications.get('temperature_minimum'),
                'bloom_months': specifications.get('bloom_months'),
                'growth_months': specifications.get('growth_months'),
                'growth_rate': growth.get('growth_rate'),
                'hardiness_zones': growth.get('maximum_height', {})  # May contain zone info
            }
        except:
            return {}
    
    def _extract_habitat_description(self, plant_data: Dict) -> str:
        """Generate habitat description from Trefle data"""
        try:
            habitat_parts = []
            
            # Add family context
            family = plant_data.get('family_name')
            if family == 'Orchidaceae':
                habitat_parts.append("Member of the diverse orchid family (Orchidaceae)")
            
            # Add distribution
            distribution = plant_data.get('main_species', {}).get('distribution', {})
            if distribution.get('native'):
                native_areas = distribution['native']
                if isinstance(native_areas, list):
                    habitat_parts.append(f"Native to: {', '.join(native_areas)}")
            
            # Add growth characteristics
            growth = plant_data.get('main_species', {}).get('growth', {})
            if growth.get('growth_form'):
                habitat_parts.append(f"Growth form: {growth['growth_form']}")
            
            return '. '.join(habitat_parts) if habitat_parts else "Habitat data available from Trefle botanical database"
            
        except Exception as e:
            return f"Habitat information retrieved from Trefle (processing error: {str(e)})"
    
    def _extract_ecological_niche(self, plant_data: Dict) -> Dict:
        """Extract ecological niche information"""
        try:
            return {
                'pollination_method': 'Unknown - orchids have diverse pollination strategies',
                'ecological_role': 'Orchids play important roles in their ecosystems as both pollinators and habitat indicators',
                'associated_species': 'Often found with specific mycorrhizal fungi',
                'habitat_requirements': 'Varies by species - from tropical rainforests to temperate woodlands'
            }
        except:
            return {}
    
    def _generate_orchid_insights(self, ecosystem_data: Dict, orchid_record: OrchidRecord) -> Dict:
        """Generate orchid-specific ecosystem insights"""
        try:
            insights = {
                'epiphytic_adaptations': 'Many orchids are epiphytes with aerial roots for water/nutrient absorption',
                'mycorrhizal_relationships': 'Orchids depend on mycorrhizal fungi for germination and growth',
                'pollination_specialization': 'Often highly specialized pollination relationships',
                'conservation_importance': 'Orchids are indicators of ecosystem health and biodiversity'
            }
            
            # Add specific insights based on existing orchid data
            if orchid_record.growth_habit:
                if 'epiphytic' in orchid_record.growth_habit.lower():
                    insights['growth_strategy'] = 'Epiphytic - grows on other plants for support and light access'
                elif 'terrestrial' in orchid_record.growth_habit.lower():
                    insights['growth_strategy'] = 'Terrestrial - grows in soil with specialized root systems'
                elif 'lithophytic' in orchid_record.growth_habit.lower():
                    insights['growth_strategy'] = 'Lithophytic - grows on rocks in thin organic matter'
            
            if orchid_record.native_habitat:
                insights['habitat_specificity'] = f"Native habitat: {orchid_record.native_habitat}"
            
            return insights
            
        except Exception as e:
            return {'error': f"Error generating insights: {str(e)}"}
    
    def enrich_orchid_with_ecosystem_data(self, orchid_id: int) -> bool:
        """
        Enrich a specific orchid record with ecosystem data from Trefle
        
        Args:
            orchid_id: ID of the OrchidRecord to enrich
        
        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.warning("Trefle service not enabled - cannot enrich orchid data")
            return False
        
        try:
            # Get the orchid record
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                logger.error(f"Orchid record not found: {orchid_id}")
                return False
            
            # Get ecosystem data
            ecosystem_data = self.get_ecosystem_habitat_data(orchid)
            
            # Check for rate limit response
            if isinstance(ecosystem_data, dict) and ecosystem_data.get('rate_limit_exceeded'):
                logger.warning(f"Rate limit hit for orchid {orchid_id} - data not persisted")
                return {'rate_limit_exceeded': True, 'retry_after': ecosystem_data.get('retry_after', 60)}
            
            if not ecosystem_data:
                logger.info(f"No ecosystem data available for orchid {orchid_id}")
                return False
            
            # Update the orchid record with ecosystem data
            if ecosystem_data.get('habitat_description'):
                # Enhance existing habitat info or add new
                if orchid.native_habitat:
                    orchid.native_habitat = f"{orchid.native_habitat} | Trefle: {ecosystem_data['habitat_description']}"
                else:
                    orchid.native_habitat = ecosystem_data['habitat_description']
            
            # Update habitat research JSON field with comprehensive data
            if orchid.habitat_research:
                try:
                    existing_research = json.loads(orchid.habitat_research) if isinstance(orchid.habitat_research, str) else orchid.habitat_research
                except:
                    existing_research = {}
            else:
                existing_research = {}
            
            # Add Trefle ecosystem data to research
            existing_research['trefle_ecosystem_data'] = ecosystem_data
            orchid.habitat_research = existing_research
            
            # Update other relevant fields if they're empty
            if not orchid.climate_preference and ecosystem_data.get('climate_data'):
                climate_data = ecosystem_data['climate_data']
                if climate_data.get('temperature_minimum'):
                    temp_min = climate_data['temperature_minimum']
                    if temp_min < 10:
                        orchid.climate_preference = 'cool'
                    elif temp_min > 18:
                        orchid.climate_preference = 'warm'
                    else:
                        orchid.climate_preference = 'intermediate'
            
            # Save changes
            db.session.commit()
            
            logger.info(f"✅ Successfully enriched orchid {orchid_id} with Trefle ecosystem data")
            return True
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error enriching orchid {orchid_id} with ecosystem data: {str(e)}")
            return False
    
    def batch_enrich_orchids(self, limit: int = 50, skip_existing: bool = True) -> Dict:
        """
        Batch enrich orchid records with ecosystem data
        
        Args:
            limit: Maximum number of orchids to process
            skip_existing: Skip orchids that already have Trefle data
        
        Returns:
            Dict with processing statistics
        """
        if not self.enabled:
            return {'error': 'Trefle service not enabled'}
        
        try:
            # Get orchids to process
            query = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.isnot(None),
                OrchidRecord.genus.isnot(None)
            )
            
            if skip_existing:
                # Skip orchids that already have Trefle data
                query = query.filter(
                    ~OrchidRecord.habitat_research.contains('"trefle_ecosystem_data"')
                )
            
            orchids_to_process = query.limit(limit).all()
            
            logger.info(f"🚀 Starting batch enrichment of {len(orchids_to_process)} orchids with Trefle data")
            
            results = {
                'total_processed': 0,
                'successful_enrichments': 0,
                'failed_enrichments': 0,
                'skipped': 0,
                'started_at': datetime.utcnow().isoformat(),
                'orchid_ids_processed': []
            }
            
            for orchid in orchids_to_process:
                try:
                    enrichment_result = self.enrich_orchid_with_ecosystem_data(orchid.id)
                    
                    # Check for rate limit response
                    if isinstance(enrichment_result, dict) and enrichment_result.get('rate_limit_exceeded'):
                        logger.warning(f"Rate limit hit during batch processing at orchid {orchid.id}")
                        results['error'] = 'Rate limit exceeded during batch processing'
                        results['retry_after'] = enrichment_result.get('retry_after', 60)
                        results['completed_at'] = datetime.utcnow().isoformat()
                        return results  # Return early with rate limit info
                    
                    if enrichment_result:
                        results['successful_enrichments'] += 1
                        results['orchid_ids_processed'].append(orchid.id)
                        logger.info(f"✅ Enriched orchid {orchid.id}: {orchid.display_name}")
                    else:
                        results['failed_enrichments'] += 1
                        logger.info(f"❌ Failed to enrich orchid {orchid.id}: {orchid.display_name}")
                    
                    results['total_processed'] += 1
                    
                    # Rate limiting is now handled in _check_rate_limit() - no blocking delays
                    
                except Exception as e:
                    results['failed_enrichments'] += 1
                    results['total_processed'] += 1
                    logger.error(f"Error processing orchid {orchid.id}: {str(e)}")
            
            results['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info(f"🎉 Batch enrichment completed: {results['successful_enrichments']}/{results['total_processed']} orchids successfully enriched")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch enrichment: {str(e)}")
            return {'error': str(e)}
    
    def get_service_status(self) -> Dict:
        """Get current status of the Trefle service"""
        return {
            'enabled': self.enabled,
            'api_key_configured': bool(self.api_key),
            'recent_requests': len(self.request_history),
            'rate_limit_status': f"{len(self.request_history)}/{self.RATE_LIMIT_CALLS} requests in last hour",
            'service_info': {
                'base_url': self.BASE_URL,
                'rate_limit_calls_per_hour': self.RATE_LIMIT_CALLS,
                'min_request_interval_seconds': self.MIN_REQUEST_INTERVAL
            }
        }

# Create global service instance
trefle_service = TrefleBotanicalService()

# Helper functions for route integration
def get_trefle_service() -> TrefleBotanicalService:
    """Get the global Trefle service instance"""
    return trefle_service

def search_orchid_ecosystem_data(scientific_name: str) -> Optional[Dict]:
    """
    Helper function to search for orchid ecosystem data by scientific name
    
    Args:
        scientific_name: Scientific name of the orchid
    
    Returns:
        Dict containing ecosystem data or None if not found
    """
    if not trefle_service.enabled:
        return None
    
    plant_data = trefle_service.search_plant_by_scientific_name(scientific_name)
    if not plant_data:
        return None
    
    # Create a mock orchid record for ecosystem data extraction
    class MockOrchid:
        def __init__(self, scientific_name):
            self.scientific_name = scientific_name
            self.genus = scientific_name.split()[0] if ' ' in scientific_name else scientific_name
            self.species = scientific_name.split()[1] if ' ' in scientific_name and len(scientific_name.split()) > 1 else None
            self.display_name = scientific_name
            self.native_habitat = None
            self.growth_habit = None
    
    mock_orchid = MockOrchid(scientific_name)
    return trefle_service._extract_ecosystem_data(plant_data, mock_orchid)

def enrich_orchid_with_trefle_data(orchid_id: int) -> bool:
    """
    Helper function to enrich an orchid with Trefle ecosystem data
    
    Args:
        orchid_id: ID of the OrchidRecord to enrich
    
    Returns:
        True if successful, False otherwise
    """
    return trefle_service.enrich_orchid_with_ecosystem_data(orchid_id)

def get_trefle_service_status() -> Dict:
    """Helper function to get Trefle service status"""
    return trefle_service.get_service_status()

def batch_enrich_orchids_with_trefle(limit: int = 50) -> Dict:
    """
    Helper function for batch enriching orchids with Trefle data
    
    Args:
        limit: Maximum number of orchids to process
    
    Returns:
        Dict with processing results
    """
    return trefle_service.batch_enrich_orchids(limit=limit)