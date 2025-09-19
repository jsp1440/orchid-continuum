#!/usr/bin/env python3
"""
GBIF ORCHID INTEGRATOR
====================
Integrate with Global Biodiversity Information Facility (GBIF) to:
- Fetch additional orchid occurrence data
- Cross-reference with Dr. Hassler's taxonomy database
- Import validated geographic and temporal data
- Expand orchid collection with authoritative records
"""

import requests
import json
import logging
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class GBIFOrchidIntegrator:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        
        # GBIF API endpoints
        self.gbif_base_url = "https://api.gbif.org/v1"
        
        # Statistics tracking
        self.stats = {
            'gbif_queries': 0,
            'gbif_records_found': 0,
            'taxonomy_matches': 0,
            'new_occurrences': 0,
            'geographic_data_added': 0
        }
    
    def search_gbif_species(self, genus, species, limit=100):
        """Search GBIF for specific orchid species"""
        try:
            # Search for the species in GBIF
            search_url = f"{self.gbif_base_url}/species/match"
            params = {
                'genus': genus,
                'species': species,
                'family': 'Orchidaceae'
            }
            
            response = requests.get(search_url, params=params, timeout=30)
            response.raise_for_status()
            
            species_data = response.json()
            
            if 'usageKey' not in species_data:
                return None
            
            # Get occurrence data for this species
            occurrence_url = f"{self.gbif_base_url}/occurrence/search"
            params = {
                'taxonKey': species_data['usageKey'],
                'hasCoordinate': 'true',
                'hasGeospatialIssue': 'false',
                'limit': limit
            }
            
            response = requests.get(occurrence_url, params=params, timeout=30)
            response.raise_for_status()
            
            occurrence_data = response.json()
            
            self.stats['gbif_queries'] += 1
            self.stats['gbif_records_found'] += occurrence_data.get('count', 0)
            
            return {
                'species_info': species_data,
                'occurrences': occurrence_data.get('results', []),
                'total_count': occurrence_data.get('count', 0)
            }
            
        except Exception as e:
            logger.error(f"GBIF search error for {genus} {species}: {e}")
            return None
    
    def get_hassler_genera(self):
        """Get unique genera from Dr. Hassler's taxonomy database"""
        with self.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT DISTINCT genus, COUNT(*) as species_count
                FROM orchid_taxonomy 
                WHERE genus IS NOT NULL 
                ORDER BY species_count DESC
                LIMIT 50
            """)).fetchall()
            
            return result
    
    def cross_reference_with_gbif(self):
        """Cross-reference Dr. Hassler's taxonomy with GBIF data"""
        logger.info("🌍 Cross-referencing Dr. Hassler's taxonomy with GBIF...")
        
        # Get representative genera from Hassler's database
        genera = self.get_hassler_genera()
        
        logger.info(f"🔍 Searching GBIF for {len(genera)} genera from Dr. Hassler's database")
        
        gbif_matches = []
        
        for genus_row in genera[:10]:  # Start with top 10 genera
            genus = genus_row[0]
            species_count = genus_row[1]
            
            logger.info(f"🌺 Searching GBIF for genus {genus} ({species_count} species in Hassler DB)")
            
            # Get species for this genus from Hassler's database
            with self.engine.connect() as conn:
                species_result = conn.execute(text("""
                    SELECT genus, species, scientific_name 
                    FROM orchid_taxonomy 
                    WHERE genus = :genus 
                    AND species IS NOT NULL
                    LIMIT 5
                """), {'genus': genus}).fetchall()
                
                for species_row in species_result:
                    genus_name = species_row[0]
                    species_name = species_row[1]
                    scientific_name = species_row[2]
                    
                    # Search GBIF for this species
                    gbif_data = self.search_gbif_species(genus_name, species_name)
                    
                    if gbif_data and gbif_data['occurrences']:
                        gbif_matches.append({
                            'hassler_name': scientific_name,
                            'gbif_data': gbif_data,
                            'occurrence_count': len(gbif_data['occurrences'])
                        })
                        
                        logger.info(f"  ✅ {scientific_name}: {len(gbif_data['occurrences'])} GBIF occurrences")
                        
                        self.stats['taxonomy_matches'] += 1
                    else:
                        logger.info(f"  ⚠️ {scientific_name}: No GBIF data found")
                    
                    # Rate limiting
                    time.sleep(0.5)
        
        return gbif_matches
    
    def analyze_geographic_coverage(self, gbif_matches):
        """Analyze geographic distribution from GBIF data"""
        logger.info("🗺️ Analyzing geographic coverage from GBIF data...")
        
        countries = {}
        coordinates = []
        
        for match in gbif_matches:
            for occurrence in match['gbif_data']['occurrences']:
                # Track countries
                country = occurrence.get('country')
                if country:
                    countries[country] = countries.get(country, 0) + 1
                
                # Track coordinates
                lat = occurrence.get('decimalLatitude')
                lon = occurrence.get('decimalLongitude')
                if lat and lon:
                    coordinates.append({
                        'species': match['hassler_name'],
                        'latitude': lat,
                        'longitude': lon,
                        'country': country,
                        'date': occurrence.get('eventDate')
                    })
        
        logger.info(f"🌍 Geographic analysis:")
        logger.info(f"  • Countries represented: {len(countries)}")
        logger.info(f"  • Coordinate points: {len(coordinates)}")
        
        # Top countries
        top_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)[:10]
        logger.info("🏆 Top countries by occurrence:")
        for country, count in top_countries:
            logger.info(f"  • {country}: {count} occurrences")
        
        return {
            'countries': countries,
            'coordinates': coordinates,
            'top_countries': top_countries
        }
    
    def suggest_collection_priorities(self, gbif_matches, geographic_data):
        """Suggest priority species for collection based on GBIF data"""
        logger.info("🎯 Generating collection priorities based on GBIF analysis...")
        
        priorities = []
        
        for match in gbif_matches:
            species_name = match['hassler_name']
            occurrence_count = match['occurrence_count']
            
            # Check if we already have photos for this species
            with self.engine.connect() as conn:
                existing_photos = conn.execute(text("""
                    SELECT COUNT(*) 
                    FROM orchid_record 
                    WHERE scientific_name ILIKE :name 
                    OR display_name ILIKE :name
                """), {'name': f'%{species_name}%'}).fetchone()
                
                photo_count = existing_photos[0] if existing_photos else 0
            
            # Calculate priority score
            priority_score = occurrence_count
            if photo_count == 0:
                priority_score *= 2  # Boost for species without photos
            
            priorities.append({
                'species': species_name,
                'gbif_occurrences': occurrence_count,
                'existing_photos': photo_count,
                'priority_score': priority_score,
                'status': 'Missing photos' if photo_count == 0 else f'{photo_count} photos'
            })
        
        # Sort by priority score
        priorities.sort(key=lambda x: x['priority_score'], reverse=True)
        
        logger.info("🎯 Collection priorities (top 10):")
        for i, priority in enumerate(priorities[:10], 1):
            logger.info(f"  {i}. {priority['species']}")
            logger.info(f"     GBIF: {priority['gbif_occurrences']} occurrences | Status: {priority['status']}")
        
        return priorities
    
    def generate_gbif_integration_report(self):
        """Generate comprehensive GBIF integration report"""
        logger.info("🌍 GBIF ORCHID INTEGRATION REPORT")
        logger.info("=" * 60)
        logger.info("📊 Global Biodiversity Information Facility (GBIF) Analysis")
        logger.info("🤝 Cross-referenced with Dr. Hassler's Taxonomy Database")
        logger.info("=" * 60)
        
        # Cross-reference with GBIF
        gbif_matches = self.cross_reference_with_gbif()
        
        # Analyze geographic coverage
        geographic_data = self.analyze_geographic_coverage(gbif_matches)
        
        # Generate collection priorities
        priorities = self.suggest_collection_priorities(gbif_matches, geographic_data)
        
        logger.info("=" * 60)
        logger.info("📈 GBIF INTEGRATION SUMMARY:")
        logger.info(f"🔍 GBIF queries made: {self.stats['gbif_queries']:,}")
        logger.info(f"📊 GBIF records found: {self.stats['gbif_records_found']:,}")
        logger.info(f"✅ Taxonomy matches: {self.stats['taxonomy_matches']:,}")
        logger.info(f"🌍 Countries represented: {len(geographic_data['countries'])}")
        logger.info(f"📍 Coordinate points: {len(geographic_data['coordinates'])}")
        logger.info("=" * 60)
        
        logger.info("🎯 NEXT STEPS:")
        logger.info("1. Focus collection efforts on high-priority species")
        logger.info("2. Use GBIF geographic data for habitat analysis")
        logger.info("3. Cross-reference occurrence data with climate zones")
        logger.info("4. Validate identifications against GBIF specimens")
        logger.info("=" * 60)
        
        return {
            'gbif_matches': gbif_matches,
            'geographic_data': geographic_data,
            'priorities': priorities,
            'stats': self.stats
        }

def main():
    """Run GBIF integration analysis"""
    logger.info("🌍 GBIF ORCHID INTEGRATOR")
    logger.info("Connecting global biodiversity data with Dr. Hassler's taxonomy")
    
    try:
        integrator = GBIFOrchidIntegrator()
        report = integrator.generate_gbif_integration_report()
        
        logger.info("🎉 GBIF integration analysis complete!")
        logger.info("🌺 Use results to expand and validate orchid collection")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ GBIF integration failed: {e}")
        return False

if __name__ == "__main__":
    main()