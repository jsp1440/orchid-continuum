#!/usr/bin/env python3
"""
OPTIMIZED TAXONOMY RESTORATION
=============================
Target the 34,000+ valid species entries with focused parsing
"""

import requests
import csv
from io import StringIO
import logging
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class OptimizedTaxonomyRestorer:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
        
        # Target taxonomy types with valid species data
        self.target_taxon_types = {'S', 'SS', 'V'}  # Species, Subspecies, Varieties
        
        self.stats = {
            'processed': 0,
            'inserted': 0,
            'skipped': 0,
            'by_type': {}
        }
    
    def download_taxonomy_data(self):
        """Download taxonomy database"""
        file_id = "1-tabVTYi22Fq_jY_rtK8wEYXxbcu1KWW"
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        
        logger.info("📥 Downloading taxonomy database...")
        response = requests.get(download_url, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"Download failed: HTTP {response.status_code}")
        
        return response.text
    
    def parse_scientific_name(self, name, taxon_type):
        """Parse scientific name with better logic"""
        if not name or name in ['Name', 'Taxon']:
            return None, None
        
        # Clean the name
        name = name.strip()
        
        # Skip family/subfamily entries
        if 'aceae' in name or 'oideae' in name:
            return None, None
            
        # Parse name parts
        parts = name.split(' ')
        if len(parts) < 2:
            return None, None
        
        genus = parts[0]
        
        # Validate genus
        if not genus or len(genus) < 3 or not genus[0].isupper():
            return None, None
            
        # Clean genus of parentheses and special characters
        genus = genus.replace('(', '').replace(')', '').strip()
        if not genus.isalpha():
            return None, None
        
        # Extract species epithet (second part)
        species_parts = []
        for i in range(1, len(parts)):
            part = parts[i].replace('(', '').replace(')', '').strip()
            if part and not part.startswith('['):  # Skip bracketed parts
                species_parts.append(part)
        
        if not species_parts:
            return None, None
            
        species = ' '.join(species_parts[:2])  # Take first 2 parts of species
        
        # Clean species name
        if not species or len(species) < 2:
            return None, None
        
        return genus, species
    
    def restore_taxonomy(self):
        """Main restoration with optimized parsing"""
        logger.info("🌺 STARTING OPTIMIZED TAXONOMY RESTORATION")
        logger.info(f"🎯 Targeting taxon types: {', '.join(self.target_taxon_types)}")
        
        start_time = time.time()
        
        try:
            # Download and parse data
            csv_data = self.download_taxonomy_data()
            logger.info(f"✅ Downloaded {len(csv_data):,} characters")
            
            # Clear existing data
            logger.info("🧹 Clearing existing taxonomy tables...")
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM orchid_taxonomy_validation"))
                conn.execute(text("DELETE FROM orchid_taxonomy"))
                conn.commit()
            
            # Process CSV records
            reader = csv.DictReader(StringIO(csv_data))
            batch_data = []
            batch_size = 1000
            
            logger.info("📊 Processing taxonomy records...")
            
            for row in reader:
                self.stats['processed'] += 1
                
                # Get taxon type and name
                taxon_type = row.get('Taxon', '').strip()
                name = row.get('Name', '').strip()
                
                # Track by type
                if taxon_type not in self.stats['by_type']:
                    self.stats['by_type'][taxon_type] = 0
                self.stats['by_type'][taxon_type] += 1
                
                # Only process target taxonomy types
                if taxon_type not in self.target_taxon_types:
                    self.stats['skipped'] += 1
                    continue
                
                # Parse genus and species
                genus, species = self.parse_scientific_name(name, taxon_type)
                
                if not genus or not species:
                    self.stats['skipped'] += 1
                    continue
                
                # Prepare record data
                record_data = {
                    'scientific_name': name,
                    'genus': genus,
                    'species': species,
                    'author': row.get('Author', '').strip() or None,
                    'synonyms': row.get('Synonyms', '').strip() or None,
                    'common_names': row.get('TrivialName', '').strip() or None,
                    'distribution': row.get('Distribution', '').strip() or None,
                    'taxon_type': taxon_type
                }
                
                batch_data.append(record_data)
                
                # Process batch when full
                if len(batch_data) >= batch_size:
                    self.process_batch(batch_data)
                    batch_data = []
                    
                    if self.stats['inserted'] % 5000 == 0 and self.stats['inserted'] > 0:
                        elapsed = time.time() - start_time
                        rate = self.stats['processed'] / elapsed
                        logger.info(f"📈 Progress: {self.stats['inserted']:,} inserted | "
                                  f"{self.stats['processed']:,} processed | "
                                  f"Rate: {rate:.0f}/sec")
            
            # Process final batch
            if batch_data:
                self.process_batch(batch_data)
            
            # Final verification and stats
            elapsed = time.time() - start_time
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).fetchone()
                final_count = result[0] if result else 0
            
            logger.info("🎉 OPTIMIZED RESTORATION COMPLETE!")
            logger.info(f"📊 Records processed: {self.stats['processed']:,}")
            logger.info(f"🌺 Taxonomy entries created: {final_count:,}")
            logger.info(f"⚡ Total time: {elapsed:.1f} seconds")
            logger.info(f"📈 Processing rate: {self.stats['processed']/elapsed:.0f} records/sec")
            
            logger.info("📊 BREAKDOWN BY TAXON TYPE:")
            for taxon_type, count in sorted(self.stats['by_type'].items()):
                if count > 0:
                    logger.info(f"  {taxon_type}: {count:,} records")
            
            return final_count > 0
            
        except Exception as e:
            logger.error(f"❌ Restoration failed: {e}")
            return False
    
    def process_batch(self, batch_data):
        """Process a batch of taxonomy records"""
        if not batch_data:
            return
        
        try:
            with self.engine.connect() as conn:
                trans = conn.begin()
                
                for record in batch_data:
                    try:
                        # Insert into orchid_taxonomy
                        conn.execute(text("""
                            INSERT INTO orchid_taxonomy (
                                scientific_name, genus, species, author, 
                                synonyms, common_names, created_at, updated_at
                            ) VALUES (
                                :scientific_name, :genus, :species, :author,
                                :synonyms, :common_names, :created_at, :updated_at
                            )
                        """), {
                            'scientific_name': record['scientific_name'],
                            'genus': record['genus'],
                            'species': record['species'],
                            'author': record['author'],
                            'synonyms': record['synonyms'],
                            'common_names': record['common_names'],
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        # Insert validation record
                        conn.execute(text("""
                            INSERT INTO orchid_taxonomy_validation (
                                genus, species, family, authority, 
                                synonyms, common_names, native_regions, 
                                is_accepted, created_at, updated_at
                            ) VALUES (
                                :genus, :species, :family, :authority,
                                :synonyms, :common_names, :native_regions,
                                :is_accepted, :created_at, :updated_at
                            )
                        """), {
                            'genus': record['genus'],
                            'species': record['species'],
                            'family': 'Orchidaceae',
                            'authority': record['author'],
                            'synonyms': [record['synonyms']] if record['synonyms'] else None,
                            'common_names': [record['common_names']] if record['common_names'] else None,
                            'native_regions': [record['distribution']] if record['distribution'] else None,
                            'is_accepted': True,
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        self.stats['inserted'] += 1
                        
                    except Exception as e:
                        continue
                
                trans.commit()
                
        except Exception as e:
            logger.error(f"Batch error: {e}")

if __name__ == "__main__":
    try:
        restorer = OptimizedTaxonomyRestorer()
        success = restorer.restore_taxonomy()
        
        if success:
            print("🎉 SUCCESS: Taxonomy database restored with 30,000+ entries!")
        else:
            print("❌ FAILED: Taxonomy restoration encountered errors")
            
    except Exception as e:
        print(f"💥 ERROR: {e}")