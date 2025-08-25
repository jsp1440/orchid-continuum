#!/usr/bin/env python3
"""
Targeted Orchid GBIF Collection
==============================
Precisely targeted search for actual orchid species with images
Focuses on known orchid genera and scientific validation
"""

import requests
import json
import logging
import time
from typing import Dict, List, Optional, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TargetedOrchidGBIF:
    """
    Precisely targeted orchid collection from GBIF
    Focus on verified orchid genera and species
    """
    
    def __init__(self):
        self.base_url = "https://api.gbif.org/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five Cities Orchid Society - Targeted Collection/1.0',
            'Accept': 'application/json'
        })
        
        # Known major orchid genera for targeted searching
        self.major_orchid_genera = [
            'Phalaenopsis', 'Cattleya', 'Dendrobium', 'Oncidium', 'Cymbidium',
            'Paphiopedilum', 'Vanda', 'Orchis', 'Ophrys', 'Epidendrum',
            'Brassia', 'Miltonia', 'Odontoglossum', 'Masdevallia', 'Bulbophyllum',
            'Vanilla', 'Cypripedium', 'Laelia', 'Encyclia', 'Brassavola',
            'Aerides', 'Angraecum', 'Ascocenda', 'Bletilla', 'Calanthe',
            'Coelogyne', 'Dactylorhiza', 'Doritaenopsis', 'Grammatophyllum',
            'Lycaste', 'Maxillaria', 'Mormodes', 'Neottia', 'Platanthera',
            'Pleurothallis', 'Renanthera', 'Rhynchostylis', 'Sobralia',
            'Stanhopea', 'Zygopetalum'
        ]
        
        logger.info("🎯 Targeted Orchid GBIF collector initialized")
        logger.info(f"🌺 Targeting {len(self.major_orchid_genera)} major orchid genera")
    
    def search_genus_images(self, genus: str, limit: int = 50) -> Dict[str, Any]:
        """
        Search for images of a specific orchid genus
        """
        try:
            params = {
                'genus': genus,
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
            logger.error(f"❌ Error searching {genus}: {e}")
            return {}
    
    def verify_orchid_record(self, occurrence: Dict[str, Any]) -> bool:
        """
        Verify that a record is actually an orchid
        """
        family = occurrence.get('family', '').lower()
        scientific_name = occurrence.get('scientificName', '').lower()
        
        # Check if family is Orchidaceae
        if 'orchidaceae' in family:
            return True
        
        # Check if scientific name contains orchid terms
        orchid_terms = ['orchid', 'orchidaceae']
        if any(term in scientific_name for term in orchid_terms):
            return True
        
        # Check if genus is in our known list
        genus = occurrence.get('genus', '')
        if genus in self.major_orchid_genera:
            return True
        
        return False
    
    def process_orchid_record(self, occurrence: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a verified orchid occurrence into our format
        """
        try:
            # Verify it's actually an orchid
            if not self.verify_orchid_record(occurrence):
                return None
            
            # Extract media
            media_list = occurrence.get('media', [])
            if not media_list:
                return None
            
            primary_image = None
            for media in media_list:
                if media.get('type') == 'StillImage':
                    primary_image = {
                        'url': media.get('identifier'),
                        'title': media.get('title', ''),
                        'creator': media.get('creator', ''),
                        'license': media.get('license', ''),
                        'publisher': media.get('publisher', '')
                    }
                    break
            
            if not primary_image:
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
            
            # Collection data
            collector = occurrence.get('recordedBy', '')
            institution = occurrence.get('institutionCode', '')
            catalog_number = occurrence.get('catalogNumber', '')
            
            record = {
                'scientific_name': scientific_name,
                'genus': genus,
                'species': species,
                'family': 'Orchidaceae',
                'country': country,
                'locality': locality,
                'latitude': latitude,
                'longitude': longitude,
                'collector': collector,
                'institution': institution,
                'catalog_number': catalog_number,
                'gbif_id': occurrence.get('gbifID'),
                'gbif_key': occurrence.get('key'),
                'dataset_key': occurrence.get('datasetKey'),
                'source_url': f"https://www.gbif.org/occurrence/{occurrence.get('key')}",
                'image_url': primary_image['url'],
                'image_title': primary_image['title'],
                'image_creator': primary_image['creator'],
                'image_license': primary_image['license'],
                'image_publisher': primary_image['publisher'],
                'basis_of_record': occurrence.get('basisOfRecord', ''),
                'event_date': occurrence.get('eventDate'),
                'coordinate_precision': occurrence.get('coordinateUncertaintyInMeters'),
                'elevation': occurrence.get('elevation'),
                'habitat': occurrence.get('habitat', ''),
                'data_source': 'GBIF Targeted Orchid'
            }
            
            return record
            
        except Exception as e:
            logger.error(f"❌ Error processing orchid record: {e}")
            return None
    
    def collect_targeted_orchids(self, max_per_genus: int = 20, 
                               max_total: int = 500) -> Dict[str, Any]:
        """
        Collect verified orchid records with images from known genera
        """
        stats = {
            'genera_searched': 0,
            'genera_with_results': 0,
            'total_found': 0,
            'verified_orchids': 0,
            'with_images': 0,
            'records': []
        }
        
        logger.info(f"🚀 Starting targeted orchid collection")
        logger.info(f"   🎯 Max per genus: {max_per_genus}")
        logger.info(f"   📊 Max total: {max_total}")
        
        collected = 0
        
        for genus in self.major_orchid_genera:
            if collected >= max_total:
                break
            
            logger.info(f"🔍 Searching genus: {genus}")
            stats['genera_searched'] += 1
            
            # Search for this genus
            response = self.search_genus_images(genus, max_per_genus)
            
            if not response or 'results' not in response:
                logger.warning(f"   ⚠️ No data for {genus}")
                continue
            
            occurrences = response['results']
            genus_count = response.get('count', 0)
            
            if not occurrences:
                logger.info(f"   ❌ No images for {genus}")
                continue
            
            stats['genera_with_results'] += 1
            stats['total_found'] += genus_count
            
            logger.info(f"   ✅ Found {len(occurrences)} {genus} records ({genus_count:,} total)")
            
            # Process each occurrence
            genus_verified = 0
            for occurrence in occurrences:
                if collected >= max_total:
                    break
                
                # Process the record
                record = self.process_orchid_record(occurrence)
                
                if record:
                    stats['verified_orchids'] += 1
                    stats['with_images'] += 1
                    stats['records'].append(record)
                    genus_verified += 1
                    collected += 1
                    
                    logger.info(f"      🌺 {record['scientific_name']}")
            
            logger.info(f"   📋 {genus}: {genus_verified} verified orchids collected")
            time.sleep(0.3)  # Rate limiting
        
        logger.info(f"🎯 TARGETED COLLECTION COMPLETE!")
        logger.info(f"   🔍 Genera searched: {stats['genera_searched']}")
        logger.info(f"   ✅ Genera with results: {stats['genera_with_results']}")
        logger.info(f"   📊 Total found: {stats['total_found']:,}")
        logger.info(f"   🌺 Verified orchids: {stats['verified_orchids']}")
        logger.info(f"   📸 With images: {stats['with_images']}")
        
        return stats

def test_targeted_collection():
    """Test the targeted orchid collection"""
    collector = TargetedOrchidGBIF()
    
    # Test with a small sample first
    results = collector.collect_targeted_orchids(
        max_per_genus=5,
        max_total=50
    )
    
    return results

if __name__ == "__main__":
    test_results = test_targeted_collection()
    print(json.dumps(test_results, indent=2, default=str))