#!/usr/bin/env python3
"""
EMERGENCY TAXONOMY RESTORATION SCRIPT
====================================
Restore the 30,000+ orchid taxonomy database entries
"""

import requests
import csv
from io import StringIO
import logging
import os
from sqlalchemy import create_engine, text
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def restore_taxonomy_database():
    """Restore the complete taxonomy database"""
    
    # Get database connection
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        logger.error("DATABASE_URL not found")
        return False
    
    engine = create_engine(database_url)
    
    logger.info("🌺 STARTING TAXONOMY RESTORATION...")
    
    try:
        # Download taxonomy CSV
        file_id = "1-tabVTYi22Fq_jY_rtK8wEYXxbcu1KWW"
        download_url = f"https://drive.usercontent.google.com/download?id={file_id}&export=download"
        
        logger.info("📥 Downloading taxonomy database...")
        response = requests.get(download_url, timeout=60)
        
        if response.status_code != 200:
            logger.error(f"Download failed: HTTP {response.status_code}")
            return False
            
        csv_data = response.text
        logger.info(f"✅ Downloaded {len(csv_data)} characters of taxonomy data")
        
        # Parse CSV
        reader = csv.DictReader(StringIO(csv_data))
        records_processed = 0
        taxonomy_entries = 0
        
        with engine.connect() as conn:
            # Clear existing taxonomy data
            logger.info("🧹 Clearing existing taxonomy tables...")
            conn.execute(text("DELETE FROM orchid_taxonomy"))
            conn.execute(text("DELETE FROM orchid_taxonomy_validation"))
            conn.commit()
            
            logger.info("📊 Processing taxonomy records...")
            
            for row in reader:
                try:
                    taxon = row.get('Taxon', '').strip()
                    name = row.get('Name', '').strip()
                    number = row.get('Number', '').strip()
                    
                    if not name or not taxon:
                        continue
                    
                    # Parse genus and species from name
                    name_parts = name.split(' ')
                    genus = name_parts[0] if len(name_parts) > 0 else ''
                    species = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''
                    
                    # Clean genus and species
                    genus = genus.replace('(', '').replace(')', '').strip()
                    if species:
                        species = species.replace('(', '').replace(')', '').strip()
                    
                    # Only insert if we have valid genus
                    if genus and len(genus) > 1 and genus.isalpha():
                        
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
                            'species': species if species else None,
                            'author': row.get('Author', '').strip() or None,
                            'synonyms': row.get('Synonyms', '').strip() or None,
                            'common_names': row.get('TrivialName', '').strip() or None,
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        # Also insert into validation table for admin reference
                        conn.execute(text("""
                            INSERT INTO orchid_taxonomy_validation (
                                genus, species, family, authority, synonyms,
                                common_names, native_regions, is_accepted,
                                created_at, updated_at
                            ) VALUES (
                                :genus, :species, :family, :authority, :synonyms,
                                :common_names, :native_regions, :is_accepted,
                                :created_at, :updated_at
                            )
                        """), {
                            'genus': genus,
                            'species': species if species else None,
                            'family': 'Orchidaceae',
                            'authority': row.get('Author', '').strip() or None,
                            'synonyms': [row.get('Synonyms', '').strip()] if row.get('Synonyms', '').strip() else None,
                            'common_names': [row.get('TrivialName', '').strip()] if row.get('TrivialName', '').strip() else None,
                            'native_regions': [row.get('Distribution', '').strip()] if row.get('Distribution', '').strip() else None,
                            'is_accepted': row.get('Status', '').lower() != 'synonym',
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        })
                        
                        taxonomy_entries += 1
                        
                        if taxonomy_entries % 1000 == 0:
                            logger.info(f"📊 Processed {taxonomy_entries} taxonomy entries...")
                            conn.commit()
                    
                    records_processed += 1
                    
                except Exception as e:
                    logger.error(f"Error processing record: {e}")
                    continue
            
            # Final commit
            conn.commit()
            
            logger.info(f"🎉 TAXONOMY RESTORATION COMPLETE!")
            logger.info(f"📊 Total CSV records processed: {records_processed}")
            logger.info(f"🌺 Taxonomy entries created: {taxonomy_entries}")
            
            # Verify the restoration
            result = conn.execute(text("SELECT COUNT(*) as count FROM orchid_taxonomy")).fetchone()
            taxonomy_count = result[0] if result else 0
            
            result_val = conn.execute(text("SELECT COUNT(*) as count FROM orchid_taxonomy_validation")).fetchone()
            validation_count = result_val[0] if result_val else 0
            
            logger.info(f"✅ Final taxonomy count: {taxonomy_count}")
            logger.info(f"✅ Final validation count: {validation_count}")
            
            return taxonomy_count > 0
            
    except Exception as e:
        logger.error(f"❌ Taxonomy restoration failed: {e}")
        return False

if __name__ == "__main__":
    success = restore_taxonomy_database()
    if success:
        print("🌺 Taxonomy database successfully restored!")
    else:
        print("❌ Taxonomy restoration failed!")