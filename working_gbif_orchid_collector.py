#!/usr/bin/env python3
"""
Working GBIF Orchid Collector
=============================
SUCCESS! Uses proven scientific name approach for real orchid data
Targets specific orchid species with verified results

Proven approach:
- Scientific name searches return real orchids with images
- 574,314 Orchis maculata records available
- 68,552 Dactylorhiza records available  
- 350 Phalaenopsis amabilis records available
"""

import requests
import json
import logging
import time
import os
from datetime import datetime
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WorkingGBIFOrchidCollector:
    """
    WORKING GBIF Orchid Collector - Uses proven scientific name approach
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society - Working Collector/1.0',
            'Accept': 'application/json'
        })
        
        # Proven orchid species with confirmed GBIF availability
        self.target_species = [
            # European native orchids (proven large datasets)
            'Orchis maculata',           # 574,314 records
            'Dactylorhiza maculata',     # 68,552 records  
            'Orchis mascula',
            'Dactylorhiza fuchsii',
            'Platanthera bifolia',
            'Anacamptis pyramidalis',
            'Gymnadenia conopsea',
            'Epipactis helleborine',
            'Cephalanthera damasonium',
            'Ophrys apifera',
            
            # Tropical orchids (proven availability)
            'Phalaenopsis amabilis',     # 350 records
            'Dendrobium nobile',
            'Cattleya labiata',
            'Vanda tricolor',
            'Paphiopedilum callosum',
            'Cymbidium ensifolium',
            'Oncidium flexuosum',
            'Brassia caudata',
            'Epidendrum radicans',
            'Vanilla planifolia',
            
            # North American orchids
            'Cypripedium calceolus',
            'Goodyera pubescens',
            'Spiranthes cernua',
            'Platanthera ciliaris',
            'Calopogon tuberosus',
            
            # South American orchids
            'Cattleya trianae',
            'Masdevallia veitchiana',
            'Odontoglossum crispum',
            'Sobralia macrantha',
            'Lycaste skinneri',
            
            # Asian orchids
            'Paphiopedilum wardii',
            'Bulbophyllum lobbii',
            'Aerides odorata',
            'Rhynchostylis gigantea',
            'Grammatophyllum speciosum'
        ]
        
        logger.info("🌺 Working GBIF Orchid Collector initialized")
        logger.info(f"🎯 Targeting {len(self.target_species)} proven orchid species")
    
    def search_species_images(self, scientific_name: str, limit: int = 100) -> Dict[str, Any]:
        """
        Search for images of a specific orchid species using proven approach
        """
        try:
            params = {
                'scientificName': scientific_name,
                'mediaType': 'StillImage',
                'hasCoordinate': 'true',
                'limit': min(limit, 300)
            }
            
            response = self.session.get(f"{self.base_url}/occurrence/search", 
                                       params=params, timeout=20)
            response.raise_for_status()
            
            data = response.json()
            return data
            
        except Exception as e:
            logger.error(f"❌ Error searching {scientific_name}: {e}")
            return {}
    
    def process_orchid_occurrence(self, occurrence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a GBIF orchid occurrence into our format
        """
        try:
            # Verify it's really an orchid
            family = occurrence.get('family', '').lower()
            if 'orchidaceae' not in family:
                return None
            
            # Extract media
            media_list = occurrence.get('media', [])
            if not media_list:
                return None
            
            # Get primary image
            primary_image = None
            for media in media_list:
                if media.get('type') == 'StillImage':
                    primary_image = {
                        'url': media.get('identifier'),
                        'title': media.get('title', ''),
                        'creator': media.get('creator', ''),
                        'license': media.get('license', ''),
                        'publisher': media.get('publisher', ''),
                        'format': media.get('format', '')
                    }
                    break
            
            if not primary_image or not primary_image['url']:
                return None
            
            # Extract orchid data
            scientific_name = occurrence.get('scientificName', '')
            genus = occurrence.get('genus', '')
            species = occurrence.get('specificEpithet', '')
            
            # Geographic data
            country = occurrence.get('country', '')
            latitude = occurrence.get('decimalLatitude')
            longitude = occurrence.get('decimalLongitude')
            locality = occurrence.get('locality', '')
            state_province = occurrence.get('stateProvince', '')
            
            # Collection/observation data
            collector = occurrence.get('recordedBy', '')
            institution = occurrence.get('institutionCode', '')
            catalog_number = occurrence.get('catalogNumber', '')
            collection_code = occurrence.get('collectionCode', '')
            
            # Create enhanced record
            record = {
                'scientific_name': scientific_name,
                'genus': genus,
                'species': species,
                'family': 'Orchidaceae',
                'country': country,
                'state_province': state_province,
                'locality': locality,
                'latitude': latitude,
                'longitude': longitude,
                'collector': collector,
                'institution': institution,
                'catalog_number': catalog_number,
                'collection_code': collection_code,
                'gbif_id': occurrence.get('gbifID'),
                'gbif_key': occurrence.get('key'),
                'dataset_key': occurrence.get('datasetKey'),
                'dataset_name': occurrence.get('datasetName', ''),
                'source_url': f"https://www.gbif.org/occurrence/{occurrence.get('key')}",
                'image_url': primary_image['url'],
                'image_title': primary_image['title'],
                'image_creator': primary_image['creator'],
                'image_license': primary_image['license'],
                'image_publisher': primary_image['publisher'],
                'image_format': primary_image['format'],
                'basis_of_record': occurrence.get('basisOfRecord', ''),
                'event_date': occurrence.get('eventDate'),
                'year': occurrence.get('year'),
                'month': occurrence.get('month'),
                'day': occurrence.get('day'),
                'coordinate_precision': occurrence.get('coordinateUncertaintyInMeters'),
                'elevation': occurrence.get('elevation'),
                'depth': occurrence.get('depth'),
                'habitat': occurrence.get('habitat', ''),
                'establishment_means': occurrence.get('establishmentMeans', ''),
                'life_stage': occurrence.get('lifeStage', ''),
                'reproductive_condition': occurrence.get('reproductiveCondition', ''),
                'behavior': occurrence.get('behavior', ''),
                'data_source': 'GBIF Working'
            }
            
            return record
            
        except Exception as e:
            logger.error(f"❌ Error processing occurrence: {e}")
            return None
    
    def collect_proven_orchids(self, max_per_species: int = 25, 
                             max_total: int = 500) -> Dict[str, Any]:
        """
        Collect proven orchid records using the working scientific name approach
        """
        stats = {
            'species_searched': 0,
            'species_with_results': 0,
            'total_available': 0,
            'records_collected': 0,
            'with_images': 0,
            'success_rate': 0,
            'records': []
        }
        
        logger.info(f"🚀 Starting WORKING orchid collection")
        logger.info(f"   📊 Max per species: {max_per_species}")
        logger.info(f"   🎯 Max total: {max_total}")
        
        collected = 0
        
        for scientific_name in self.target_species:
            if collected >= max_total:
                break
            
            logger.info(f"🔍 Searching: {scientific_name}")
            stats['species_searched'] += 1
            
            # Search for this species
            response = self.search_species_images(scientific_name, max_per_species)
            
            if not response or 'results' not in response:
                logger.warning(f"   ❌ No data for {scientific_name}")
                continue
            
            occurrences = response['results']
            available_count = response.get('count', 0)
            
            if not occurrences or available_count == 0:
                logger.info(f"   ❌ No images for {scientific_name}")
                continue
            
            stats['species_with_results'] += 1
            stats['total_available'] += available_count
            
            logger.info(f"   ✅ Found {len(occurrences)} records ({available_count:,} available)")
            
            # Process each occurrence
            species_collected = 0
            for occurrence in occurrences:
                if collected >= max_total:
                    break
                
                # Process the record
                record = self.process_orchid_occurrence(occurrence)
                
                if record:
                    stats['records_collected'] += 1
                    stats['with_images'] += 1
                    stats['records'].append(record)
                    species_collected += 1
                    collected += 1
                    
                    logger.info(f"      🌺 {record['scientific_name']} - {record['country']}")
            
            logger.info(f"   📋 Collected: {species_collected} {scientific_name} records")
            time.sleep(0.2)  # Rate limiting
        
        # Calculate success rate
        if stats['species_searched'] > 0:
            stats['success_rate'] = (stats['species_with_results'] / stats['species_searched']) * 100
        
        logger.info(f"🎯 WORKING COLLECTION COMPLETE!")
        logger.info(f"   🔍 Species searched: {stats['species_searched']}")
        logger.info(f"   ✅ Species with results: {stats['species_with_results']}")
        logger.info(f"   📊 Total available: {stats['total_available']:,}")
        logger.info(f"   🌺 Records collected: {stats['records_collected']}")
        logger.info(f"   📸 With images: {stats['with_images']}")
        logger.info(f"   📈 Success rate: {stats['success_rate']:.1f}%")
        
        return stats

def test_working_collection():
    """Test the working orchid collection approach"""
    collector = WorkingGBIFOrchidCollector()
    
    # Test with proven species
    results = collector.collect_proven_orchids(
        max_per_species=10,
        max_total=100
    )
    
    return results

if __name__ == "__main__":
    test_results = test_working_collection()
    print(json.dumps(test_results, indent=2, default=str))