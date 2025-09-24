#!/usr/bin/env python3
"""
Encyclopedia of Life (EOL) Integration
=====================================
Integrates with Encyclopedia of Life to complement the Orchid Continuum
Downloads orchid images, descriptions, and ecological data
"""

import requests
import time
import logging
import json
import os
from datetime import datetime
from app import app, db
from models import OrchidRecord
from validation_integration import ScraperValidationSystem, create_validated_orchid_record

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EncyclopediaOfLifeIntegration:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Orchid-Continuum/1.0 (Educational/Research; eol-integration)'
        })
        
        # EOL API base URL
        self.base_url = "https://eol.org/api"
        
        # Initialize validation system
        self.validator = ScraperValidationSystem()
        self.collected_count = 0
        self.enriched_count = 0
        self.rejected_count = 0
        
        logger.info("🔬 ENCYCLOPEDIA OF LIFE INTEGRATION INITIALIZED")
    
    def enrich_existing_orchids(self, limit=100):
        """Enrich existing orchid records with EOL data"""
        
        logger.info(f"🔍 Starting EOL enrichment for existing orchids (limit: {limit})...")
        
        with app.app_context():
            # Get orchids without detailed descriptions
            orchids = OrchidRecord.query.filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None),
                db.or_(
                    OrchidRecord.ai_description.is_(None),
                    OrchidRecord.ai_description.like('%GBIF%'),
                    OrchidRecord.ai_description.like('%gallery%')
                )
            ).limit(limit).all()
            
            logger.info(f"📋 Found {len(orchids)} orchids for EOL enrichment")
            
            for i, orchid in enumerate(orchids):
                logger.info(f"🔍 Processing {i+1}/{len(orchids)}: {orchid.scientific_name}")
                
                try:
                    eol_data = self.search_eol_species(orchid.scientific_name)
                    if eol_data:
                        self.enrich_orchid_with_eol_data(orchid, eol_data)
                        self.enriched_count += 1
                        logger.info(f"   ✅ Enriched with EOL data")
                    else:
                        logger.debug(f"   ❌ No EOL data found for {orchid.scientific_name}")
                    
                    # Commit every 10 records
                    if (i + 1) % 10 == 0:
                        db.session.commit()
                        logger.info(f"✅ Committed batch of 10 records")
                    
                    # Be respectful to EOL API
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"❌ Error enriching {orchid.scientific_name}: {e}")
            
            # Final commit
            db.session.commit()
            
        logger.info(f"🎉 EOL ENRICHMENT COMPLETE! Enriched {self.enriched_count} orchids")
    
    def search_eol_species(self, scientific_name):
        """Search for species in Encyclopedia of Life"""
        
        try:
            # Search for the species
            response = self.session.get(
                f"{self.base_url}/search/1.0.json",
                params={
                    'q': scientific_name,
                    'page': 1,
                    'exact': True,
                    'filter_by_taxon_concept_id': '',
                    'filter_by_hierarchy_entry_id': '',
                    'filter_by_string': '',
                    'cache_ttl': ''
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return None
                
            data = response.json()
            results = data.get('results', [])
            
            # Find exact match
            for result in results:
                if result.get('title', '').lower() == scientific_name.lower():
                    eol_id = result.get('id')
                    if eol_id:
                        return self.get_eol_species_details(eol_id)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error searching EOL for {scientific_name}: {e}")
            return None
    
    def get_eol_species_details(self, eol_id):
        """Get detailed species information from EOL"""
        
        try:
            # Get species page data
            response = self.session.get(
                f"{self.base_url}/pages/1.0/{eol_id}.json",
                params={
                    'images': 5,  # Get up to 5 images
                    'videos': 0,
                    'sounds': 0,
                    'maps': 1,
                    'text': 3,  # Get text descriptions
                    'iucn': True,  # Conservation status
                    'subjects': 'all',
                    'licenses': 'all',
                    'details': True,
                    'common_names': True,
                    'synonyms': True,
                    'references': True,
                    'taxonomy': True,
                    'vetted': 2,  # Trusted and unreviewed content
                    'cache_ttl': ''
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return None
                
            return response.json()
            
        except Exception as e:
            logger.error(f"❌ Error getting EOL details for ID {eol_id}: {e}")
            return None
    
    def enrich_orchid_with_eol_data(self, orchid, eol_data):
        """Enrich orchid record with EOL data"""
        
        try:
            # Extract descriptions
            descriptions = []
            text_objects = eol_data.get('dataObjects', [])
            
            for obj in text_objects:
                if obj.get('dataType') == 'http://purl.org/dc/dcmitype/Text':
                    description = obj.get('description', '').strip()
                    if description and len(description) > 50:
                        descriptions.append(description[:500])  # Limit length
            
            # Create enhanced description
            enhanced_description = f"Encyclopedia of Life data for {orchid.scientific_name}."
            
            if descriptions:
                # Use the first good description
                enhanced_description += f" {descriptions[0]}"
            
            # Add conservation status if available
            for obj in text_objects:
                if 'conservation' in obj.get('subject', '').lower():
                    status = obj.get('description', '').strip()
                    if status:
                        enhanced_description += f" Conservation: {status[:200]}"
                        break
            
            # Add habitat information
            for obj in text_objects:
                if any(keyword in obj.get('subject', '').lower() for keyword in ['habitat', 'ecology', 'distribution']):
                    habitat = obj.get('description', '').strip()
                    if habitat:
                        enhanced_description += f" Habitat: {habitat[:200]}"
                        break
            
            # Extract images
            images = []
            for obj in eol_data.get('dataObjects', []):
                if obj.get('dataType') == 'http://purl.org/dc/dcmitype/StillImage':
                    image_url = obj.get('eolMediaURL') or obj.get('mediaURL')
                    if image_url and not orchid.image_url:
                        orchid.image_url = image_url
                        orchid.image_source = f"Encyclopedia of Life - {obj.get('title', 'Image')}"
                        break
            
            # Update the orchid record
            if enhanced_description != orchid.ai_description:
                orchid.ai_description = enhanced_description[:1000]  # Limit length
                orchid.updated_at = datetime.utcnow()
                
                # Add EOL metadata
                if not orchid.data_source or 'EOL' not in orchid.data_source:
                    orchid.data_source = f"{orchid.data_source or ''} | EOL ID: {eol_data.get('identifier', 'Unknown')}"
            
        except Exception as e:
            logger.error(f"❌ Error enriching orchid with EOL data: {e}")
    
    def discover_new_orchids(self, search_terms=None):
        """Discover new orchid species from EOL"""
        
        if not search_terms:
            search_terms = [
                'Orchidaceae', 'Dendrobium', 'Phalaenopsis', 'Cattleya', 
                'Oncidium', 'Vanda', 'Paphiopedilum', 'Bulbophyllum'
            ]
        
        logger.info(f"🔍 Discovering new orchids from EOL using {len(search_terms)} search terms...")
        
        with app.app_context():
            for term in search_terms:
                logger.info(f"🔎 Searching EOL for: {term}")
                
                try:
                    # Search EOL
                    response = self.session.get(
                        f"{self.base_url}/search/1.0.json",
                        params={
                            'q': term,
                            'page': 1,
                            'exact': False,
                            'filter_by_taxon_concept_id': '',
                            'filter_by_hierarchy_entry_id': '',
                            'filter_by_string': '',
                            'cache_ttl': ''
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        results = data.get('results', [])
                        
                        logger.info(f"   📋 Found {len(results)} results for {term}")
                        
                        for result in results[:10]:  # Process first 10 results
                            title = result.get('title', '')
                            if title and len(title.split()) >= 2:  # Must have genus and species
                                self.create_orchid_from_eol_search(title, result)
                        
                        time.sleep(3)  # Be respectful
                    
                except Exception as e:
                    logger.error(f"❌ Error searching EOL for {term}: {e}")
        
        logger.info(f"🎉 EOL DISCOVERY COMPLETE! Collected {self.collected_count} new orchids")
    
    def create_orchid_from_eol_search(self, scientific_name, eol_result):
        """Create orchid record from EOL search result"""
        
        try:
            # Parse genus and species
            parts = scientific_name.split()
            genus = parts[0] if parts else ''
            species = parts[1] if len(parts) > 1 else ''
            
            if not genus or not species:
                return False
            
            # Check if we already have this orchid
            existing = OrchidRecord.query.filter_by(scientific_name=scientific_name).first()
            if existing:
                return False
            
            # Prepare record data for validation
            record_data = {
                'display_name': scientific_name,
                'scientific_name': scientific_name,
                'genus': genus,
                'species': species,
                'ai_description': f"Encyclopedia of Life species: {scientific_name}. EOL ID: {eol_result.get('id', 'Unknown')}",
                'ingestion_source': 'eol_validated',
                'data_source': f"Encyclopedia of Life - ID: {eol_result.get('id', 'Unknown')}"
            }
            
            # Validate before creating database record
            validated_data = create_validated_orchid_record(record_data, "eol_integrator")
            
            if validated_data:
                try:
                    orchid_record = OrchidRecord()
                    orchid_record.display_name = validated_data['display_name']
                    orchid_record.scientific_name = validated_data['scientific_name']
                    orchid_record.genus = validated_data['genus']
                    orchid_record.species = validated_data.get('species', '')
                    orchid_record.ai_description = validated_data['ai_description']
                    orchid_record.ingestion_source = validated_data['ingestion_source']
                    orchid_record.data_source = validated_data['data_source']
                    orchid_record.created_at = datetime.utcnow()
                    orchid_record.updated_at = datetime.utcnow()
                    
                    db.session.add(orchid_record)
                    
                    self.collected_count += 1
                    logger.debug(f"   ✅ Created EOL orchid: {scientific_name}")
                    return True
                    
                except Exception as e:
                    logger.error(f"❌ Database error for {scientific_name}: {e}")
                    db.session.rollback()
                    return False
            else:
                logger.debug(f"❌ Validation failed for {scientific_name} (genus: {genus})")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error creating EOL record: {e}")
            return False
    
    def get_integration_opportunities(self):
        """Analyze how Orchid Continuum can complement EOL"""
        
        return {
            'complementary_features': [
                'AI-powered orchid identification from photos',
                'Specialized orchid care and growing advice',
                'Orchid breeding and hybridization tracking',
                'Interactive orchid habitat mapping',
                'Real-time orchid bloom tracking and alerts',
                'Orchid society and nursery directory integration',
                'Orchid show and exhibition calendar',
                'Personalized orchid collection management'
            ],
            'data_integration': [
                'Cross-reference EOL species data with our taxonomy',
                'Enhance EOL entries with orchid-specific metadata',
                'Provide orchid care instructions for EOL species',
                'Link EOL conservation data with habitat requirements',
                'Contribute orchid photos and observations to EOL'
            ],
            'api_integration': [
                'Widget for EOL pages showing orchid care info',
                'Direct links from Orchid Continuum to EOL entries',
                'Shared taxonomic validation system',
                'Collaborative conservation status tracking'
            ]
        }

if __name__ == "__main__":
    integrator = EncyclopediaOfLifeIntegration()
    
    # Enrich existing orchids
    integrator.enrich_existing_orchids(limit=20)
    
    # Discover new orchids
    integrator.discover_new_orchids()
    
    # Show integration opportunities
    opportunities = integrator.get_integration_opportunities()
    
    print(f"\n🔬 ENCYCLOPEDIA OF LIFE INTEGRATION COMPLETE!")
    print(f"✅ Enriched records: {integrator.enriched_count}")
    print(f"📝 New orchids discovered: {integrator.collected_count}")
    print(f"\n🤝 INTEGRATION OPPORTUNITIES WITH EOL:")
    print(f"🌟 Complementary Features: {len(opportunities['complementary_features'])}")
    print(f"📊 Data Integration: {len(opportunities['data_integration'])}")
    print(f"🔗 API Integration: {len(opportunities['api_integration'])}")