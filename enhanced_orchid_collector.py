"""
Enhanced Orchid Data Collection System
Optimized for complete data transfer including pollinators and companion plants
"""

import requests
import time
import json
from sqlalchemy import create_engine, text, inspect
import os
from typing import Dict, List, Any, Optional

class EnhancedOrchidEcosystemCollector:
    """Comprehensive collector for orchids, pollinators, and companion species"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Five-Cities-Orchid-Society/1.0',
            'Accept': 'application/json'
        })
        self.database_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url) if self.database_url else None
        
    def get_database_statistics(self) -> Optional[Dict[str, Any]]:
        """Get current database statistics"""
        if not self.engine:
            return None
            
        try:
            inspector = inspect(self.engine)
            tables = inspector.get_table_names()
            
            # Find orchid table (could be 'orchid_record', 'orchid_records', etc.)
            orchid_table = None
            for table in tables:
                if 'orchid' in table.lower() and 'record' in table.lower():
                    orchid_table = table
                    break
            
            if not orchid_table:
                return {'error': 'No orchid table found', 'tables': tables}
            
            with self.engine.connect() as conn:
                total = conn.execute(text(f'SELECT COUNT(*) FROM {orchid_table}')).scalar()
                
                # Check for common coordinate fields
                coord_count = 0
                coord_field = None
                for field in ['decimal_latitude', 'latitude', 'lat']:
                    try:
                        coord_count = conn.execute(text(f'SELECT COUNT(*) FROM {orchid_table} WHERE {field} IS NOT NULL')).scalar()
                        coord_field = field
                        break
                    except:
                        continue
                
                # Check for images
                image_count = 0
                for field in ['image_url', 'photo_url', 'media_url']:
                    try:
                        image_count = conn.execute(text(f'SELECT COUNT(*) FROM {orchid_table} WHERE {field} IS NOT NULL')).scalar()
                        break
                    except:
                        continue
                
                return {
                    'table_name': orchid_table,
                    'total_records': total,
                    'with_coordinates': coord_count,
                    'coordinate_field': coord_field,
                    'with_images': image_count,
                    'coordinate_percentage': round(coord_count/total*100, 1) if total > 0 else 0,
                    'image_percentage': round(image_count/total*100, 1) if total > 0 else 0
                }
                
        except Exception as e:
            return {'error': str(e)}
    
    def collect_comprehensive_orchid_data(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Collect comprehensive orchid data with full metadata"""
        
        # Priority genera known for good documentation
        priority_genera = [
            'Cypripedium',    # Lady's slippers - well documented
            'Paphiopedilum',  # Slipper orchids - cultivated, good data
            'Platanthera',    # Bog orchids - ecological data available
            'Spiranthes',     # Ladies' tresses - common, studied
            'Dendrobium',     # Tree orchids - many species, photos
            'Orchis',         # European orchids - historical records
            'Habenaria',      # Rein orchids - widespread
            'Cattleya',       # Showy orchids - horticultural data
            'Phalaenopsis',   # Moth orchids - commercial importance
            'Vanilla'         # Vanilla orchids - economic importance
        ]
        
        all_orchids = []
        
        for genus in priority_genera:
            try:
                print(f"🔍 Collecting {genus} species...")
                
                url = 'https://api.gbif.org/v1/occurrence/search'
                params = {
                    'genus': genus,
                    'family': 'Orchidaceae',
                    'kingdom': 'Plantae',
                    'hasCoordinate': 'true',
                    'mediaType': 'StillImage',
                    'limit': max(2, limit // len(priority_genera))
                }
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                for occurrence in data.get('results', []):
                    if occurrence.get('family') != 'Orchidaceae':
                        continue
                    
                    # Extract comprehensive metadata
                    orchid_record = {
                        # Core identification
                        'scientific_name': occurrence.get('scientificName', ''),
                        'genus': occurrence.get('genus', ''),
                        'species': occurrence.get('specificEpithet', ''),
                        'infraspecific_epithet': occurrence.get('infraspecificEpithet', ''),
                        'scientific_name_authorship': occurrence.get('scientificNameAuthorship', ''),
                        'vernacular_name': occurrence.get('vernacularName', ''),
                        
                        # Taxonomy
                        'kingdom': occurrence.get('kingdom', ''),
                        'phylum': occurrence.get('phylum', ''),
                        'class_name': occurrence.get('class', ''),
                        'order': occurrence.get('order', ''),
                        'family': occurrence.get('family', ''),
                        'taxon_rank': occurrence.get('taxonRank', ''),
                        'taxonomic_status': occurrence.get('taxonomicStatus', ''),
                        
                        # Geographic information
                        'decimal_latitude': occurrence.get('decimalLatitude'),
                        'decimal_longitude': occurrence.get('decimalLongitude'),
                        'coordinate_uncertainty_meters': occurrence.get('coordinateUncertaintyInMeters'),
                        'elevation': occurrence.get('elevation'),
                        'depth': occurrence.get('depth'),
                        'country': occurrence.get('country', ''),
                        'country_code': occurrence.get('countryCode', ''),
                        'state_province': occurrence.get('stateProvince', ''),
                        'county': occurrence.get('county', ''),
                        'locality': occurrence.get('locality', ''),
                        'verbatim_locality': occurrence.get('verbatimLocality', ''),
                        'water_body': occurrence.get('waterBody', ''),
                        
                        # Temporal data
                        'event_date': occurrence.get('eventDate'),
                        'year': occurrence.get('year'),
                        'month': occurrence.get('month'),
                        'day': occurrence.get('day'),
                        'start_day_of_year': occurrence.get('startDayOfYear'),
                        'end_day_of_year': occurrence.get('endDayOfYear'),
                        
                        # Collection information
                        'basis_of_record': occurrence.get('basisOfRecord', ''),
                        'occurrence_status': occurrence.get('occurrenceStatus', ''),
                        'individual_count': occurrence.get('individualCount'),
                        'organism_quantity': occurrence.get('organismQuantity'),
                        'organism_quantity_type': occurrence.get('organismQuantityType', ''),
                        'sex': occurrence.get('sex', ''),
                        'life_stage': occurrence.get('lifeStage', ''),
                        'reproductive_condition': occurrence.get('reproductiveCondition', ''),
                        'behavior': occurrence.get('behavior', ''),
                        'establishment_means': occurrence.get('establishmentMeans', ''),
                        'degree_of_establishment': occurrence.get('degreeOfEstablishment', ''),
                        'pathway': occurrence.get('pathway', ''),
                        
                        # Identification and collection
                        'recorded_by': occurrence.get('recordedBy', ''),
                        'identified_by': occurrence.get('identifiedBy', ''),
                        'date_identified': occurrence.get('dateIdentified'),
                        'identification_verification_status': occurrence.get('identificationVerificationStatus', ''),
                        'identification_remarks': occurrence.get('identificationRemarks', ''),
                        'type_status': occurrence.get('typeStatus', ''),
                        
                        # Specimen data
                        'catalog_number': occurrence.get('catalogNumber', ''),
                        'other_catalog_numbers': occurrence.get('otherCatalogNumbers', ''),
                        'record_number': occurrence.get('recordNumber', ''),
                        'collection_id': occurrence.get('collectionID', ''),
                        'collection_code': occurrence.get('collectionCode', ''),
                        'institution_id': occurrence.get('institutionID', ''),
                        'institution_code': occurrence.get('institutionCode', ''),
                        'owner_institution_code': occurrence.get('ownerInstitutionCode', ''),
                        
                        # Environmental data
                        'habitat': occurrence.get('habitat', ''),
                        'substrate': occurrence.get('substrate', ''),
                        'associated_taxa': occurrence.get('associatedTaxa', ''),
                        'associated_sequences': occurrence.get('associatedSequences', ''),
                        'occurrence_remarks': occurrence.get('occurrenceRemarks', ''),
                        'field_notes': occurrence.get('fieldNotes', ''),
                        'field_number': occurrence.get('fieldNumber', ''),
                        'event_remarks': occurrence.get('eventRemarks', ''),
                        'sampling_protocol': occurrence.get('samplingProtocol', ''),
                        'sampling_effort': occurrence.get('samplingEffort', ''),
                        'sample_size_value': occurrence.get('sampleSizeValue'),
                        'sample_size_unit': occurrence.get('sampleSizeUnit', ''),
                        
                        # Data quality and issues
                        'coordinate_precision': occurrence.get('coordinatePrecision'),
                        'georeferenced_by': occurrence.get('georeferencedBy', ''),
                        'georeferenced_date': occurrence.get('georeferencedDate'),
                        'georeference_protocol': occurrence.get('georeferenceProtocol', ''),
                        'georeference_sources': occurrence.get('georeferenceSources', ''),
                        'georeference_verification_status': occurrence.get('georeferenceVerificationStatus', ''),
                        'georeference_remarks': occurrence.get('georeferenceRemarks', ''),
                        'issues': occurrence.get('issues', []),
                        'flags': occurrence.get('flags', []),
                        
                        # References and sources
                        'references': occurrence.get('references', ''),
                        'bibliographic_citation': occurrence.get('bibliographicCitation', ''),
                        'source': occurrence.get('source', ''),
                        'information_withheld': occurrence.get('informationWithheld', ''),
                        'data_generalizations': occurrence.get('dataGeneralizations', ''),
                        'dynamic_properties': occurrence.get('dynamicProperties', ''),
                        
                        # GBIF specific
                        'gbif_id': occurrence.get('gbifID', ''),
                        'occurrence_id': occurrence.get('occurrenceID', ''),
                        'key': occurrence.get('key'),
                        'dataset_key': occurrence.get('datasetKey', ''),
                        'dataset_name': occurrence.get('datasetName', ''),
                        'publisher': occurrence.get('publisher', ''),
                        'publishing_organization': occurrence.get('publishingOrganization', ''),
                        'publishing_country': occurrence.get('publishingCountry', ''),
                        'installation_key': occurrence.get('installationKey', ''),
                        'hosting_organization': occurrence.get('hostingOrganization', ''),
                        'protocol': occurrence.get('protocol', ''),
                        'last_crawled': occurrence.get('lastCrawled'),
                        'last_parsed': occurrence.get('lastParsed'),
                        'crawl_id': occurrence.get('crawlId'),
                        'license': occurrence.get('license', ''),
                        'rights_holder': occurrence.get('rightsHolder', ''),
                        'access_rights': occurrence.get('accessRights', ''),
                        
                        # Media
                        'media': occurrence.get('media', []),
                        'extensions': occurrence.get('extensions', {}),
                        'facts': occurrence.get('facts', []),
                        'relations': occurrence.get('relations', []),
                        
                        # Additional metadata
                        'data_source': 'GBIF Enhanced Collection',
                        'collection_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'collection_method': 'Optimized Transfer',
                        'quality_score': self._calculate_quality_score(occurrence)
                    }
                    
                    all_orchids.append(orchid_record)
                    print(f"  ✓ {orchid_record['scientific_name']} - Quality: {orchid_record['quality_score']}/10")
                
                time.sleep(1)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error collecting {genus}: {e}")
                continue
        
        return all_orchids
    
    def collect_orchid_pollinators(self, limit: int = 30) -> List[Dict[str, Any]]:
        """Collect orchid pollinator data from GBIF"""
        
        pollinators = []
        
        # Specific orchid pollinator searches
        pollinator_queries = [
            # Direct orchid pollination searches
            {'q': 'orchid pollination', 'class': 'Insecta'},
            {'q': 'orchid pollinator', 'class': 'Insecta'},
            {'q': 'orchid nectar', 'order': 'Lepidoptera'},
            {'q': 'orchid visit', 'order': 'Hymenoptera'},
            
            # Known orchid-specialized pollinators
            {'genus': 'Euglossa', 'family': 'Apidae'},  # Orchid bees
            {'genus': 'Eulaema', 'family': 'Apidae'},   # Orchid bees
            {'genus': 'Bombus', 'associatedTaxa': 'Orchidaceae'},  # Bumblebees
            {'genus': 'Xylocopa', 'habitat': 'orchid'},  # Carpenter bees
        ]
        
        for query_params in pollinator_queries:
            try:
                print(f"🐝 Searching pollinators: {query_params}")
                
                url = 'https://api.gbif.org/v1/occurrence/search'
                params = {
                    **query_params,
                    'hasCoordinate': 'true',
                    'limit': max(3, limit // len(pollinator_queries))
                }
                
                response = self.session.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                for occurrence in data.get('results', []):
                    # Verify pollinator relevance
                    text_fields = f"{occurrence.get('habitat', '')} {occurrence.get('locality', '')} {occurrence.get('occurrenceRemarks', '')} {occurrence.get('associatedTaxa', '')}".lower()
                    
                    orchid_relevance = any(keyword in text_fields for keyword in [
                        'orchid', 'orchidaceae', 'pollination', 'nectar', 'flower visit', 'pollen'
                    ])
                    
                    if orchid_relevance or 'orchid' in query_params.get('q', ''):
                        pollinator_record = {
                            'scientific_name': occurrence.get('scientificName', ''),
                            'genus': occurrence.get('genus', ''),
                            'family': occurrence.get('family', ''),
                            'order': occurrence.get('order', ''),
                            'class_name': occurrence.get('class', ''),
                            'decimal_latitude': occurrence.get('decimalLatitude'),
                            'decimal_longitude': occurrence.get('decimalLongitude'),
                            'country': occurrence.get('country', ''),
                            'locality': occurrence.get('locality', ''),
                            'habitat': occurrence.get('habitat', ''),
                            'associated_taxa': occurrence.get('associatedTaxa', ''),
                            'occurrence_remarks': occurrence.get('occurrenceRemarks', ''),
                            'event_date': occurrence.get('eventDate'),
                            'recorded_by': occurrence.get('recordedBy', ''),
                            'gbif_id': occurrence.get('gbifID', ''),
                            'data_source': 'GBIF Pollinator Collection',
                            'orchid_relevance_score': self._calculate_orchid_relevance(occurrence),
                            'collection_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                        }
                        
                        pollinators.append(pollinator_record)
                        print(f"  ✓ {pollinator_record['scientific_name']} - Relevance: {pollinator_record['orchid_relevance_score']}/5")
                
                time.sleep(0.8)  # Rate limiting
                
            except Exception as e:
                print(f"  ❌ Error searching pollinators: {e}")
                continue
        
        return pollinators
    
    def collect_companion_plants(self, limit: int = 25) -> List[Dict[str, Any]]:
        """Collect companion plant data - species commonly found with orchids"""
        
        companions = []
        
        # Plant groups commonly associated with orchids in different habitats
        companion_searches = [
            # Epiphytic companions (tropical/subtropical orchids)
            {'family': 'Bromeliaceae', 'habitat': 'epiphytic'},  # Bromeliads
            {'genus': 'Tillandsia', 'habitat': 'epiphytic'},     # Air plants
            {'family': 'Araceae', 'habitat': 'epiphytic'},       # Aroids
            
            # Terrestrial forest companions
            {'family': 'Polypodiaceae', 'habitat': 'forest'},    # Ferns
            {'genus': 'Pteridium', 'habitat': 'forest'},         # Bracken fern
            {'family': 'Bryaceae', 'habitat': 'moss'},           # Mosses
            {'genus': 'Sphagnum', 'habitat': 'bog'},             # Sphagnum moss
            
            # Grassland/meadow companions
            {'family': 'Cyperaceae', 'habitat': 'grassland'},    # Sedges
            {'genus': 'Carex', 'habitat': 'meadow'},             # Sedges
            {'family': 'Poaceae', 'habitat': 'grassland'},       # Grasses
            
            # Understory companions
            {'family': 'Ericaceae', 'habitat': 'understory'},    # Heathers
            {'genus': 'Vaccinium', 'habitat': 'understory'},     # Blueberries
            {'family': 'Rosaceae', 'habitat': 'forest'},         # Rose family
        ]
        
        for search_params in companion_searches:
            try:
                print(f"🌿 Searching companions: {search_params}")
                
                url = 'https://api.gbif.org/v1/occurrence/search'
                params = {
                    **search_params,
                    'kingdom': 'Plantae',
                    'hasCoordinate': 'true',
                    'limit': max(2, limit // len(companion_searches))
                }
                
                response = self.session.get(url, params=params, timeout=20)
                response.raise_for_status()
                data = response.json()
                
                for occurrence in data.get('results', []):
                    companion_record = {
                        'scientific_name': occurrence.get('scientificName', ''),
                        'genus': occurrence.get('genus', ''),
                        'family': occurrence.get('family', ''),
                        'order': occurrence.get('order', ''),
                        'decimal_latitude': occurrence.get('decimalLatitude'),
                        'decimal_longitude': occurrence.get('decimalLongitude'),
                        'country': occurrence.get('country', ''),
                        'locality': occurrence.get('locality', ''),
                        'habitat': occurrence.get('habitat', ''),
                        'elevation': occurrence.get('elevation'),
                        'event_date': occurrence.get('eventDate'),
                        'recorded_by': occurrence.get('recordedBy', ''),
                        'gbif_id': occurrence.get('gbifID', ''),
                        'companion_type': self._determine_companion_type(search_params),
                        'data_source': 'GBIF Companion Plants',
                        'collection_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
                    }
                    
                    companions.append(companion_record)
                    print(f"  ✓ {companion_record['scientific_name']} ({companion_record['companion_type']})")
                
                time.sleep(0.5)
                
            except Exception as e:
                print(f"  ❌ Error searching companions: {e}")
                continue
        
        return companions
    
    def _calculate_quality_score(self, occurrence: Dict[str, Any]) -> int:
        """Calculate data quality score (0-10) based on available metadata"""
        score = 0
        
        # Basic identification (2 points)
        if occurrence.get('scientificName'): score += 1
        if occurrence.get('scientificNameAuthorship'): score += 1
        
        # Geographic data (3 points)
        if occurrence.get('decimalLatitude') and occurrence.get('decimalLongitude'): score += 2
        if occurrence.get('country'): score += 1
        
        # Temporal data (2 points)
        if occurrence.get('eventDate'): score += 1
        if occurrence.get('year'): score += 1
        
        # Collection data (2 points)
        if occurrence.get('recordedBy'): score += 1
        if occurrence.get('institutionCode'): score += 1
        
        # Environmental data (1 point)
        if occurrence.get('habitat') or occurrence.get('locality'): score += 1
        
        return score
    
    def _calculate_orchid_relevance(self, occurrence: Dict[str, Any]) -> int:
        """Calculate orchid relevance score (0-5) for pollinator records"""
        score = 0
        
        text_fields = f"{occurrence.get('habitat', '')} {occurrence.get('locality', '')} {occurrence.get('occurrenceRemarks', '')} {occurrence.get('associatedTaxa', '')}".lower()
        
        # Direct orchid mentions
        if 'orchid' in text_fields: score += 2
        if 'orchidaceae' in text_fields: score += 2
        
        # Pollination terms
        if any(term in text_fields for term in ['pollination', 'pollinator', 'nectar', 'pollen']): score += 1
        
        # Flower interaction terms
        if any(term in text_fields for term in ['flower', 'visit', 'feeding', 'foraging']): score += 1
        
        # Known orchid pollinator genera
        genus = occurrence.get('genus', '').lower()
        if genus in ['euglossa', 'eulaema', 'bombus', 'xylocopa', 'manduca']: score += 1
        
        return min(score, 5)  # Cap at 5
    
    def _determine_companion_type(self, search_params: Dict[str, Any]) -> str:
        """Determine companion plant type based on search parameters"""
        if 'Bromeliaceae' in str(search_params) or 'epiphytic' in str(search_params):
            return 'Epiphytic'
        elif 'Bryaceae' in str(search_params) or 'moss' in str(search_params):
            return 'Moss'
        elif 'Polypodiaceae' in str(search_params) or 'Pteridium' in str(search_params):
            return 'Fern'
        elif 'Cyperaceae' in str(search_params) or 'Poaceae' in str(search_params):
            return 'Grass/Sedge'
        elif 'Ericaceae' in str(search_params) or 'understory' in str(search_params):
            return 'Understory Shrub'
        else:
            return 'Other'


def main():
    """Main collection function"""
    collector = EnhancedOrchidEcosystemCollector()
    
    print("🚀 ENHANCED ORCHID ECOSYSTEM DATA COLLECTION")
    print("=" * 60)
    
    # Database analysis
    print("\n📊 Database Analysis:")
    db_stats = collector.get_database_statistics()
    if db_stats and 'error' not in db_stats:
        print(f"Current database: {db_stats['total_records']:,} records in '{db_stats['table_name']}'")
        print(f"Coordinate coverage: {db_stats['coordinate_percentage']}%")
        print(f"Image coverage: {db_stats['image_percentage']}%")
    else:
        print(f"Database analysis: {db_stats}")
    
    # Collect enhanced data
    print("\n🌺 Collecting enhanced orchid data...")
    orchids = collector.collect_comprehensive_orchid_data(limit=30)
    
    print("\n🐝 Collecting pollinator data...")
    pollinators = collector.collect_orchid_pollinators(limit=20)
    
    print("\n🌿 Collecting companion plant data...")
    companions = collector.collect_companion_plants(limit=20)
    
    # Summary
    print(f"\n📈 COLLECTION SUMMARY")
    print("=" * 30)
    print(f"Enhanced Orchids: {len(orchids)}")
    print(f"Pollinators: {len(pollinators)}")
    print(f"Companion Plants: {len(companions)}")
    print(f"Total New Records: {len(orchids) + len(pollinators) + len(companions)}")
    
    # Quality analysis
    if orchids:
        avg_quality = sum(o.get('quality_score', 0) for o in orchids) / len(orchids)
        print(f"Average orchid quality score: {avg_quality:.1f}/10")
    
    if pollinators:
        avg_relevance = sum(p.get('orchid_relevance_score', 0) for p in pollinators) / len(pollinators)
        print(f"Average pollinator relevance: {avg_relevance:.1f}/5")
    
    print("\n✅ Enhanced collection complete!")
    return orchids, pollinators, companions


if __name__ == "__main__":
    main()