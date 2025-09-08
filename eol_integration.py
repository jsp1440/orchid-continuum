#!/usr/bin/env python3
"""
Encyclopedia of Life (EOL) Integration Module
Integrates with EOL's open API and TraitBank to enhance orchid records with taxonomic and trait data
Enhanced for citizen science wild population analysis and conservation genetics
"""

import os
import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any
from datetime import datetime
from app import db
from models import OrchidRecord

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EOLIntegrator:
    """
    Encyclopedia of Life API integration for orchid data enhancement
    """
    
    def __init__(self):
        self.base_url = "https://eol.org/api"
        self.structured_api_base = "https://eol.org/service"
        self.api_key = os.environ.get('EOL_API_KEY')  # Power user JWT token
        self.rate_limit_delay = 2  # Seconds between requests (30/minute = 2 seconds)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society Continuum Platform (Conservation Research)',
            'Accept': 'application/json'
        })
        
        # Add JWT token if available
        if self.api_key:
            self.session.headers.update({
                'Authorization': f'JWT {self.api_key}'
            })
        
        # TraitBank categories for conservation genetics
        self.conservation_trait_categories = {
            'population_genetics': [
                'genetic diversity', 'effective population size', 'gene flow',
                'population structure', 'inbreeding coefficient', 'heterozygosity'
            ],
            'morphological_variation': [
                'flower size variation', 'color polymorphism', 'plant height variation',
                'flowering time variation', 'fruit set variation', 'pollinator specificity'
            ],
            'environmental_adaptation': [
                'elevation tolerance', 'soil pH tolerance', 'moisture requirements',
                'temperature tolerance', 'drought resistance', 'shade tolerance'
            ],
            'conservation_status': [
                'population trend', 'threats', 'habitat quality', 'fragmentation level',
                'protection status', 'cultivation status', 'recovery potential'
            ]
        }
        
    def search_eol_species(self, scientific_name: str) -> Optional[Dict]:
        """
        Search for a species in EOL database
        
        Args:
            scientific_name: Scientific name of the orchid (e.g., "Cattleya trianae")
            
        Returns:
            Dictionary with EOL search results or None if not found
        """
        try:
            url = f"{self.base_url}/search/1.0.json"
            params = {
                'q': scientific_name,
                'page': 1,
                'exact': True
            }
            
            logger.info(f"🔍 Searching EOL for: {scientific_name}")
            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('results') and len(data['results']) > 0:
                # Return the first (most relevant) result
                result = data['results'][0]
                logger.info(f"✅ Found EOL page {result.get('id')} for {scientific_name}")
                return result
            else:
                logger.warning(f"⚠️ No EOL results found for {scientific_name}")
                return None
                
        except Exception as e:
            logger.error(f"❌ EOL search failed for {scientific_name}: {str(e)}")
            return None
            
    def get_eol_page_data(self, page_id: str) -> Optional[Dict]:
        """
        Get detailed species information from EOL page
        
        Args:
            page_id: EOL page identifier
            
        Returns:
            Dictionary with detailed EOL page data
        """
        try:
            url = f"{self.base_url}/pages/1.0/{page_id}.json"
            params = {
                'images': 5,      # Get up to 5 images
                'videos': 0,      # No videos needed
                'sounds': 0,      # No sounds needed  
                'maps': 1,        # Get distribution maps
                'text': 5,        # Get text descriptions
                'details': True,  # Include detailed information
                'common_names': True,
                'synonyms': True
            }
            
            logger.info(f"📖 Fetching EOL page data for ID: {page_id}")
            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"✅ Retrieved EOL data for page {page_id}")
            return data
            
        except Exception as e:
            logger.error(f"❌ Failed to get EOL page {page_id}: {str(e)}")
            return None
            
    def extract_trait_data(self, eol_data: Dict) -> Dict:
        """
        Extract and organize trait data from EOL response
        
        Args:
            eol_data: Raw EOL API response data
            
        Returns:
            Organized trait data dictionary
        """
        traits = {
            'eol_page_id': eol_data.get('identifier'),
            'scientific_name': eol_data.get('scientificName'),
            'common_names': [],
            'synonyms': [],
            'descriptions': [],
            'images': [],
            'distribution': None,
            'taxonomic_concepts': [],
            'last_updated': datetime.now().isoformat()
        }
        
        # Extract common names
        if 'vernacularNames' in eol_data:
            for name in eol_data['vernacularNames']:
                if name.get('vernacularName'):
                    traits['common_names'].append({
                        'name': name['vernacularName'],
                        'language': name.get('language', 'unknown')
                    })
                    
        # Extract synonyms
        if 'synonyms' in eol_data:
            for synonym in eol_data['synonyms']:
                if synonym.get('synonym'):
                    traits['synonyms'].append(synonym['synonym'])
                    
        # Extract text descriptions
        if 'dataObjects' in eol_data:
            for obj in eol_data['dataObjects']:
                if obj.get('dataType') == 'http://purl.org/dc/dcmitype/Text':
                    description = {
                        'description': obj.get('description', ''),
                        'subject': obj.get('subject', ''),
                        'language': obj.get('language', 'en'),
                        'source': obj.get('source', ''),
                        'license': obj.get('license', '')
                    }
                    traits['descriptions'].append(description)
                    
                # Extract images
                elif obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage':
                    image = {
                        'url': obj.get('mediaURL', ''),
                        'thumb_url': obj.get('thumbURL', ''),
                        'title': obj.get('title', ''),
                        'source': obj.get('source', ''),
                        'license': obj.get('license', '')
                    }
                    traits['images'].append(image)
                    
        # Extract taxonomic concepts
        if 'taxonConcepts' in eol_data:
            for concept in eol_data['taxonConcepts']:
                taxonomic_concept = {
                    'name': concept.get('scientificName', ''),
                    'rank': concept.get('taxonRank', ''),
                    'source': concept.get('nameAccordingTo', ''),
                    'identifier': concept.get('identifier', '')
                }
                traits['taxonomic_concepts'].append(taxonomic_concept)
                
        return traits
        
    def update_orchid_with_eol_data(self, orchid_id: int, eol_traits: Dict) -> bool:
        """
        Update orchid record with EOL trait data
        
        Args:
            orchid_id: ID of the orchid record to update
            eol_traits: Extracted EOL trait data
            
        Returns:
            True if successful, False otherwise
        """
        try:
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                logger.error(f"❌ Orchid {orchid_id} not found")
                return False
                
            # Update EOL-specific fields
            orchid.eol_page_id = eol_traits.get('eol_page_id')
            orchid.eol_traits = json.dumps(eol_traits)
            
            # Update other fields if they're empty
            if not orchid.common_names and eol_traits.get('common_names'):
                common_names_list = [cn['name'] for cn in eol_traits['common_names'][:3]]
                orchid.common_names = ', '.join(common_names_list)
                
            # Enhance description if needed
            if eol_traits.get('descriptions') and len(eol_traits['descriptions']) > 0:
                best_description = eol_traits['descriptions'][0]['description']
                if len(best_description) > len(orchid.ai_description or ''):
                    orchid.ai_description = f"{orchid.ai_description}\n\nEOL Description: {best_description[:500]}..."
                    
            # Mark as EOL enhanced
            orchid.data_source = f"{orchid.data_source or 'Unknown'}, EOL"
            orchid.updated_at = datetime.now()
            
            db.session.commit()
            logger.info(f"✅ Updated orchid {orchid_id} with EOL data")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to update orchid {orchid_id}: {str(e)}")
            db.session.rollback()
            return False
            
    def enhance_all_orchids(self) -> Dict[str, int]:
        """
        Enhance all orchid records with EOL data
        
        Returns:
            Dictionary with enhancement statistics
        """
        stats = {
            'total_processed': 0,
            'successfully_enhanced': 0,
            'not_found_in_eol': 0,
            'errors': 0
        }
        
        # Get all orchids that don't have EOL data yet
        orchids = OrchidRecord.query.filter(
            (OrchidRecord.eol_page_id == None) | (OrchidRecord.eol_page_id == '')
        ).all()
        
        logger.info(f"🚀 Starting EOL enhancement for {len(orchids)} orchids")
        
        for orchid in orchids:
            stats['total_processed'] += 1
            
            try:
                # Search for the orchid in EOL
                search_result = self.search_eol_species(orchid.scientific_name)
                
                if search_result:
                    page_id = search_result.get('id')
                    
                    # Get detailed page data
                    page_data = self.get_eol_page_data(page_id)
                    
                    if page_data:
                        # Extract traits
                        traits = self.extract_trait_data(page_data)
                        
                        # Update orchid record
                        if self.update_orchid_with_eol_data(orchid.id, traits):
                            stats['successfully_enhanced'] += 1
                        else:
                            stats['errors'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    stats['not_found_in_eol'] += 1
                    
                # Rate limiting - be respectful to EOL
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"❌ Error processing orchid {orchid.id}: {str(e)}")
                stats['errors'] += 1
                
        logger.info(f"🎉 EOL enhancement completed: {stats}")
        return stats
        
    def get_enhancement_status(self) -> Dict:
        """
        Get status of EOL enhancement for all orchids
        
        Returns:
            Dictionary with enhancement status
        """
        total_orchids = OrchidRecord.query.count()
        enhanced_orchids = OrchidRecord.query.filter(
            OrchidRecord.eol_page_id != None,
            OrchidRecord.eol_page_id != ''
        ).count()
        
        status = {
            'total_orchids': total_orchids,
            'eol_enhanced': enhanced_orchids,
            'pending_enhancement': total_orchids - enhanced_orchids,
            'enhancement_percentage': round((enhanced_orchids / total_orchids * 100), 2) if total_orchids > 0 else 0
        }
        
        return status


def test_eol_integration():
    """
    Test function to verify EOL integration works
    """
    eol = EOLIntegrator()
    
    # Test with a known orchid
    test_species = "Cattleya trianae"
    
    print(f"🧪 Testing EOL integration with {test_species}")
    
    # Search for species
    search_result = eol.search_eol_species(test_species)
    if search_result:
        print(f"✅ Found EOL page: {search_result}")
        
        # Get page data
        page_data = eol.get_eol_page_data(search_result['id'])
        if page_data:
            print(f"✅ Retrieved page data")
            
            # Extract traits
            traits = eol.extract_trait_data(page_data)
            print(f"✅ Extracted traits: {len(traits.get('descriptions', []))} descriptions, {len(traits.get('images', []))} images")
            
            return True
    
    print("❌ EOL integration test failed")
    return False


# Create global instance for import
eol_integrator = EOLIntegrator()

if __name__ == "__main__":
    # Run test when called directly
    test_eol_integration()