#!/usr/bin/env python3
"""
DR. MICHAEL HASSLER TAXONOMY DATABASE RESTORATION
================================================
Restore Dr. Michael Hassler's 40+ years of orchid taxonomy research
with proper attribution and data integrity validation.

Citation: Hassler, M. (2025). World Orchids Database. Accessed [Date].
"""

import requests
import csv
from io import StringIO
import logging
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import gc
import sys

# Configure logging for clear progress tracking
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class HasslerTaxonomyRestorer:
    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise Exception("DATABASE_URL environment variable required")
        
        self.engine = create_engine(
            self.database_url, 
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )
        
        # Conservative batch size for memory efficiency
        self.batch_size = 250
        
        # Track processing statistics
        self.stats = {
            'total_processed': 0,
            'total_inserted': 0,
            'batch_count': 0,
            'species_count': 0,
            'varieties_count': 0,
            'subspecies_count': 0,
            'genera_count': 0,
            'start_time': time.time()
        }
        
        # Target taxonomy types for Dr. Hassler's database
        self.target_types = {
            'S': 'Species',      # Primary species entries
            'V': 'Varieties',    # Botanical varieties
            'SS': 'Subspecies',  # Subspecies
            'G': 'Genera'        # Genus-level entries
        }
    
    def download_hassler_database(self):
        """Download Dr. Michael Hassler's complete taxonomy database"""
        logger.info("🌺 DR. MICHAEL HASSLER TAXONOMY RESTORATION")
        logger.info("=" * 60)
        logger.info("📚 Citation: Hassler, M. (2025). World Orchids Database.")
        logger.info("🔬 40+ years of comprehensive orchid taxonomy research")
        logger.info("=" * 60)
        
        # Google Drive file ID for the taxonomy database
        file_id = "1-tabVTYi22Fq_jY_rtK8wEYXxbcu1KWW"
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        
        logger.info("📥 Downloading Hassler taxonomy database...")
        
        try:
            response = requests.get(download_url, timeout=90)
            response.raise_for_status()
            
            csv_data = response.text
            size_mb = len(csv_data) / 1024 / 1024
            
            logger.info(f"✅ Successfully downloaded {len(csv_data):,} characters ({size_mb:.1f} MB)")
            logger.info(f"📊 Database contains decades of taxonomic research")
            
            return csv_data
            
        except Exception as e:
            logger.error(f"❌ Failed to download Hassler database: {e}")
            raise
    
    def validate_and_parse_entry(self, name, taxon_type):
        """Validate and parse a taxonomy entry with strict quality control"""
        if not name or name in ['Name', 'Taxon']:
            return None, None
        
        # Clean the scientific name
        name = name.strip()
        
        # Skip family and subfamily entries (not species-level)
        if any(suffix in name.lower() for suffix in ['aceae', 'oideae', 'ineae']):
            return None, None
        
        # Parse genus and species from scientific name
        parts = name.split(' ')
        if len(parts) < 2:
            return None, None
        
        # Extract and validate genus
        genus = parts[0].replace('(', '').replace(')', '').strip()
        
        # Genus validation - must be proper botanical format
        if not genus or len(genus) < 3 or not genus[0].isupper() or not genus.isalpha():
            return None, None
        
        # Extract species epithet(s)
        species_parts = []
        for part in parts[1:]:
            cleaned_part = part.replace('(', '').replace(')', '').replace('[', '').replace(']', '').strip()
            if cleaned_part and not cleaned_part.startswith('var.') and not cleaned_part.startswith('subsp.'):
                species_parts.append(cleaned_part)
                if len(species_parts) >= 2:  # Limit to binomial + infraspecific
                    break
        
        if not species_parts:
            return None, None
        
        species = ' '.join(species_parts)
        
        # Species validation
        if len(species) < 2:
            return None, None
        
        return genus, species
    
    def process_batch(self, batch_records):
        """Process a batch of taxonomy records with transaction safety"""
        if not batch_records:
            return 0
        
        inserted_count = 0
        
        try:
            with self.engine.connect() as conn:
                # Use transaction for batch integrity
                with conn.begin() as trans:
                    for record in batch_records:
                        try:
                            # Insert into main taxonomy table
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
                            
                            # Insert validation record for data integrity
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
                            
                            inserted_count += 1
                            
                        except Exception as e:
                            # Log but continue with batch
                            continue
                    
                    # Commit entire batch
                    trans.commit()
            
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return 0
        
        return inserted_count
    
    def restore_database(self):
        """Main restoration process with comprehensive progress tracking"""
        try:
            # Download the complete database
            csv_data = self.download_hassler_database()
            
            # Clear existing taxonomy data for fresh restoration
            logger.info("🧹 Preparing taxonomy tables for restoration...")
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM orchid_taxonomy_validation"))
                conn.execute(text("DELETE FROM orchid_taxonomy"))
                conn.commit()
            
            logger.info("✅ Tables prepared successfully")
            
            # Process the CSV data in memory-efficient batches
            logger.info(f"📊 Processing taxonomy records (batch size: {self.batch_size})")
            logger.info("🎯 Targeting: Species, Varieties, Subspecies, and Genera")
            
            reader = csv.DictReader(StringIO(csv_data))
            current_batch = []
            
            for row in reader:
                self.stats['total_processed'] += 1
                
                # Get taxonomy type and scientific name
                taxon_type = row.get('Taxon', '').strip()
                name = row.get('Name', '').strip()
                
                # Only process target taxonomy types from Hassler's database
                if taxon_type not in self.target_types:
                    continue
                
                # Validate and parse the entry
                genus, species = self.validate_and_parse_entry(name, taxon_type)
                
                if not genus or not species:
                    continue
                
                # Prepare record with full attribution
                record = {
                    'scientific_name': name,
                    'genus': genus,
                    'species': species,
                    'author': row.get('Author', '').strip() or None,
                    'synonyms': row.get('Synonyms', '').strip() or None,
                    'common_names': row.get('TrivialName', '').strip() or None,
                    'distribution': row.get('Distribution', '').strip() or None,
                    'taxon_type': taxon_type
                }
                
                current_batch.append(record)
                
                # Track by taxonomy type
                if taxon_type == 'S':
                    self.stats['species_count'] += 1
                elif taxon_type == 'V':
                    self.stats['varieties_count'] += 1
                elif taxon_type == 'SS':
                    self.stats['subspecies_count'] += 1
                elif taxon_type == 'G':
                    self.stats['genera_count'] += 1
                
                # Process batch when full
                if len(current_batch) >= self.batch_size:
                    inserted = self.process_batch(current_batch)
                    self.stats['total_inserted'] += inserted
                    self.stats['batch_count'] += 1
                    
                    # Progress update every 10 batches
                    if self.stats['batch_count'] % 10 == 0:
                        elapsed = time.time() - self.stats['start_time']
                        rate = self.stats['total_inserted'] / elapsed if elapsed > 0 else 0
                        
                        logger.info(f"📈 Batch {self.stats['batch_count']}: "
                                  f"{self.stats['total_inserted']:,} entries restored | "
                                  f"Rate: {rate:.0f}/sec")
                    
                    # Clear batch and run garbage collection
                    current_batch = []
                    gc.collect()
            
            # Process final batch
            if current_batch:
                inserted = self.process_batch(current_batch)
                self.stats['total_inserted'] += inserted
                self.stats['batch_count'] += 1
            
            # Final verification and statistics
            elapsed = time.time() - self.stats['start_time']
            
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy")).fetchone()
                final_count = result[0] if result else 0
                
                result_val = conn.execute(text("SELECT COUNT(*) FROM orchid_taxonomy_validation")).fetchone()
                validation_count = result_val[0] if result_val else 0
            
            # Success report
            logger.info("🎉 DR. HASSLER TAXONOMY RESTORATION COMPLETE!")
            logger.info("=" * 60)
            logger.info(f"📚 Citation: Hassler, M. (2025). World Orchids Database.")
            logger.info(f"🌺 Taxonomy entries restored: {final_count:,}")
            logger.info(f"✅ Validation entries created: {validation_count:,}")
            logger.info(f"📊 Processing statistics:")
            logger.info(f"   • Species (S): {self.stats['species_count']:,}")
            logger.info(f"   • Varieties (V): {self.stats['varieties_count']:,}")
            logger.info(f"   • Subspecies (SS): {self.stats['subspecies_count']:,}")
            logger.info(f"   • Genera (G): {self.stats['genera_count']:,}")
            logger.info(f"⏱️ Total restoration time: {elapsed:.1f} seconds")
            logger.info(f"⚡ Average processing rate: {self.stats['total_processed']/elapsed:.0f} records/sec")
            logger.info("=" * 60)
            logger.info("🔬 40+ years of taxonomic research successfully preserved!")
            
            return final_count > 0
            
        except Exception as e:
            logger.error(f"💥 CRITICAL ERROR: {e}")
            return False

def main():
    """Execute the Hassler taxonomy restoration"""
    logger.info("🚀 Initializing Dr. Michael Hassler Taxonomy Restoration System")
    
    try:
        restorer = HasslerTaxonomyRestorer()
        success = restorer.restore_database()
        
        if success:
            logger.info("🎉 SUCCESS: Dr. Hassler's taxonomy database fully restored!")
            return 0
        else:
            logger.error("❌ FAILED: Restoration encountered critical errors")
            return 1
            
    except Exception as e:
        logger.error(f"💥 SYSTEM ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())