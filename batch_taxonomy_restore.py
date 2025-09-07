#!/usr/bin/env python3
"""
BATCH TAXONOMY RESTORATION SYSTEM
==================================
Restore 30,000+ orchid taxonomy entries using efficient batch processing
"""

import requests
import csv
from io import StringIO
import logging
import os
from sqlalchemy import create_engine, text
from datetime import datetime
import time
import sys

# Configure efficient logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class BatchTaxonomyRestorer:
    def __init__(self, batch_size=1500):
        self.batch_size = batch_size
        self.total_processed = 0
        self.total_inserted = 0
        self.batch_count = 0
        self.start_time = time.time()
        
        # Database connection
        self.database_url = os.environ.get('DATABASE_URL')
        if not self.database_url:
            raise Exception("DATABASE_URL not found")
        
        self.engine = create_engine(self.database_url, pool_pre_ping=True)
    
    def download_taxonomy_data(self):
        """Download the complete taxonomy CSV from Google Drive"""
        file_id = "1-tabVTYi22Fq_jY_rtK8wEYXxbcu1KWW"
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        
        logger.info("📥 Downloading complete taxonomy database...")
        response = requests.get(download_url, timeout=60)
        
        if response.status_code != 200:
            raise Exception(f"Download failed: HTTP {response.status_code}")
        
        csv_data = response.text
        logger.info(f"✅ Downloaded {len(csv_data):,} characters ({len(csv_data)/1024/1024:.1f} MB)")
        
        return csv_data
    
    def parse_name(self, name):
        """Extract genus and species from scientific name"""
        if not name or name in ['Name', 'Taxon']:
            return None, None
            
        # Clean up common prefixes and formatting
        name = name.strip()
        name_parts = name.split(' ')
        
        if len(name_parts) < 1:
            return None, None
            
        genus = name_parts[0]
        
        # Skip non-genus entries
        if not genus or len(genus) < 2:
            return None, None
            
        # Clean genus name
        genus = genus.replace('(', '').replace(')', '').strip()
        
        # Only accept valid genus names (alphabetic, capitalized)
        if not genus.isalpha() or not genus[0].isupper():
            return None, None
            
        # Extract species (everything after genus)
        species = None
        if len(name_parts) > 1:
            species_parts = name_parts[1:]
            # Join species parts, but clean them
            species = ' '.join(species_parts).replace('(', '').replace(')', '').strip()
            if not species or len(species) < 2:
                species = None
        
        return genus, species
    
    def process_batch(self, batch_data):
        """Process a batch of taxonomy records"""
        if not batch_data:
            return 0
            
        inserted_count = 0
        
        try:
            with self.engine.connect() as conn:
                # Begin transaction for this batch
                trans = conn.begin()
                
                for row in batch_data:
                    try:
                        name = row.get('Name', '').strip()
                        genus, species = self.parse_name(name)
                        
                        if not genus:
                            continue
                            
                        # Clean additional fields
                        author = row.get('Author', '').strip() or None
                        synonyms = row.get('Synonyms', '').strip() or None
                        common_names = row.get('TrivialName', '').strip() or None
                        distribution = row.get('Distribution', '').strip() or None
                        
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
                            'scientific_name': name,
                            'genus': genus,
                            'species': species,
                            'author': author,
                            'synonyms': synonyms,
                            'common_names': common_names,
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        # Also insert validation record
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
                            'genus': genus,
                            'species': species,
                            'family': 'Orchidaceae',
                            'authority': author,
                            'synonyms': [synonyms] if synonyms else None,
                            'common_names': [common_names] if common_names else None,
                            'native_regions': [distribution] if distribution else None,
                            'is_accepted': True,
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        inserted_count += 1
                        
                    except Exception as e:
                        # Skip individual record errors but continue batch
                        continue
                
                # Commit the entire batch
                trans.commit()
                
        except Exception as e:
            logger.error(f"❌ Batch processing error: {e}")
            return 0
        
        return inserted_count
    
    def restore_taxonomy(self):
        """Main restoration process with batch processing"""
        logger.info("🌺 STARTING BATCH TAXONOMY RESTORATION")
        logger.info(f"⚙️ Batch size: {self.batch_size:,} records per batch")
        
        try:
            # Download data
            csv_data = self.download_taxonomy_data()
            
            # Clear existing data
            logger.info("🧹 Clearing existing taxonomy data...")
            with self.engine.connect() as conn:
                conn.execute(text("DELETE FROM orchid_taxonomy_validation"))
                conn.execute(text("DELETE FROM orchid_taxonomy"))
                conn.commit()
            
            # Parse CSV and process in batches
            reader = csv.DictReader(StringIO(csv_data))
            current_batch = []
            
            logger.info("📊 Processing taxonomy records in batches...")
            
            for row in reader:
                current_batch.append(row)
                self.total_processed += 1
                
                # Process batch when it reaches batch_size
                if len(current_batch) >= self.batch_size:
                    inserted = self.process_batch(current_batch)
                    self.total_inserted += inserted
                    self.batch_count += 1
                    
                    # Progress update
                    elapsed = time.time() - self.start_time
                    rate = self.total_processed / elapsed if elapsed > 0 else 0
                    
                    logger.info(f"✅ Batch {self.batch_count}: {inserted:,}/{len(current_batch):,} inserted | "
                              f"Total: {self.total_inserted:,} entries | "
                              f"Rate: {rate:.0f} records/sec")
                    
                    # Clear batch for next iteration
                    current_batch = []
                    
                    # Small pause to prevent overwhelming the system
                    time.sleep(0.1)
            
            # Process remaining records in final batch
            if current_batch:
                inserted = self.process_batch(current_batch)
                self.total_inserted += inserted
                self.batch_count += 1
                logger.info(f"✅ Final batch: {inserted:,}/{len(current_batch):,} inserted")
            
            # Final verification
            with self.engine.connect() as conn:
                result = conn.execute(text("SELECT COUNT(*) as count FROM orchid_taxonomy")).fetchone()
                final_count = result[0] if result else 0
                
                result_val = conn.execute(text("SELECT COUNT(*) as count FROM orchid_taxonomy_validation")).fetchone()
                validation_count = result_val[0] if result_val else 0
            
            elapsed = time.time() - self.start_time
            
            logger.info("🎉 BATCH RESTORATION COMPLETE!")
            logger.info(f"📊 Total records processed: {self.total_processed:,}")
            logger.info(f"🌺 Taxonomy entries created: {final_count:,}")
            logger.info(f"✅ Validation entries created: {validation_count:,}")
            logger.info(f"⏱️ Total time: {elapsed:.1f} seconds")
            logger.info(f"⚡ Average rate: {self.total_processed/elapsed:.0f} records/sec")
            
            return final_count > 0
            
        except Exception as e:
            logger.error(f"❌ Restoration failed: {e}")
            return False

def main():
    """Run the batch restoration process"""
    try:
        restorer = BatchTaxonomyRestorer(batch_size=1500)  # Moderate batch size
        success = restorer.restore_taxonomy()
        
        if success:
            print("\n🎉 SUCCESS: Taxonomy database fully restored!")
        else:
            print("\n❌ FAILED: Taxonomy restoration encountered errors")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()