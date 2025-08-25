#!/usr/bin/env python3
"""
Enhanced Orchid Database Models
==============================
Expanded models to handle EOL, GBIF, and pollinator data integration
"""

from app import db
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON

# Add to existing OrchidRecord model - new fields needed:
class EnhancedOrchidRecord(db.Model):
    """
    Enhanced orchid record supporting multiple data sources
    """
    __tablename__ = 'orchid_record'
    
    # Existing fields from current model...
    id = db.Column(Integer, primary_key=True)
    
    # NEW: External database integration fields
    eol_page_id = db.Column(String(50), nullable=True)  # Encyclopedia of Life
    gbif_id = db.Column(String(50), nullable=True)      # GBIF occurrence ID
    gbif_key = db.Column(String(50), nullable=True)     # GBIF key
    gbif_dataset_key = db.Column(String(100), nullable=True)
    
    # NEW: Enhanced geographic data from GBIF
    country = db.Column(String(100), nullable=True)
    state_province = db.Column(String(100), nullable=True)
    locality = db.Column(String(200), nullable=True)
    decimal_latitude = db.Column(Float, nullable=True)
    decimal_longitude = db.Column(Float, nullable=True)
    coordinate_precision = db.Column(Float, nullable=True)
    elevation = db.Column(Float, nullable=True)
    
    # NEW: Collection and observation data
    collector = db.Column(String(200), nullable=True)
    institution_code = db.Column(String(100), nullable=True)
    catalog_number = db.Column(String(100), nullable=True)
    collection_code = db.Column(String(100), nullable=True)
    basis_of_record = db.Column(String(50), nullable=True)  # HUMAN_OBSERVATION, PRESERVED_SPECIMEN
    
    # NEW: Enhanced temporal data
    event_date = db.Column(String(50), nullable=True)
    year = db.Column(Integer, nullable=True)
    month = db.Column(Integer, nullable=True)
    day = db.Column(Integer, nullable=True)
    
    # NEW: Enhanced image metadata
    image_creator = db.Column(String(200), nullable=True)
    image_license = db.Column(String(200), nullable=True)
    image_publisher = db.Column(String(200), nullable=True)
    image_format = db.Column(String(50), nullable=True)
    image_title = db.Column(String(200), nullable=True)
    
    # NEW: Biological and ecological data
    life_stage = db.Column(String(50), nullable=True)
    reproductive_condition = db.Column(String(100), nullable=True)
    establishment_means = db.Column(String(50), nullable=True)
    habitat_description = db.Column(Text, nullable=True)
    
    # NEW: Data source tracking
    data_source = db.Column(String(50), nullable=True)  # 'GBIF Working', 'EOL', 'Manual Upload'
    source_url = db.Column(String(500), nullable=True)
    
    # Enhanced metadata JSON fields
    gbif_metadata = db.Column(JSON, nullable=True)      # Full GBIF response
    eol_traits = db.Column(JSON, nullable=True)         # EOL trait data
    pollinator_data = db.Column(JSON, nullable=True)    # Associated pollinator info

class PollinatorRecord(db.Model):
    """
    New model for pollinator data and orchid-pollinator relationships
    """
    id = db.Column(Integer, primary_key=True)
    
    # Pollinator identification
    scientific_name = db.Column(String(200), nullable=False)
    common_name = db.Column(String(200), nullable=True)
    family = db.Column(String(100), nullable=True)
    genus = db.Column(String(100), nullable=True)
    species = db.Column(String(100), nullable=True)
    
    # Pollinator characteristics
    pollinator_type = db.Column(String(50), nullable=True)  # bee, wasp, butterfly, etc.
    foraging_behavior = db.Column(String(100), nullable=True)
    body_size = db.Column(String(50), nullable=True)
    tongue_length = db.Column(Float, nullable=True)
    
    # Geographic range
    native_range = db.Column(Text, nullable=True)
    introduced_range = db.Column(Text, nullable=True)
    
    # Database source info
    source_database = db.Column(String(100), nullable=True)  # 'EU Pollinator Hub', 'DoPI', etc.
    external_id = db.Column(String(100), nullable=True)
    source_url = db.Column(String(500), nullable=True)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class OrchidPollinatorRelationship(db.Model):
    """
    Junction table for orchid-pollinator relationships
    """
    id = db.Column(Integer, primary_key=True)
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinator_record.id'), nullable=False)
    
    # Relationship characteristics
    relationship_type = db.Column(String(50), nullable=True)  # 'primary', 'occasional', 'deceptive'
    pollination_effectiveness = db.Column(String(50), nullable=True)  # 'high', 'medium', 'low'
    interaction_frequency = db.Column(String(50), nullable=True)
    seasonal_timing = db.Column(String(100), nullable=True)
    
    # Evidence and sources
    evidence_type = db.Column(String(50), nullable=True)  # 'observed', 'literature', 'experimental'
    reference_citation = db.Column(Text, nullable=True)
    observation_location = db.Column(String(200), nullable=True)
    observation_date = db.Column(DateTime, nullable=True)
    
    # Additional metadata
    notes = db.Column(Text, nullable=True)
    confidence_level = db.Column(String(20), nullable=True)  # 'high', 'medium', 'low'
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ExternalDataSource(db.Model):
    """
    Track external data sources and sync status
    """
    id = db.Column(Integer, primary_key=True)
    
    # Source identification
    source_name = db.Column(String(100), nullable=False)  # 'EOL', 'GBIF', 'EU Pollinator Hub'
    source_type = db.Column(String(50), nullable=False)   # 'API', 'scraper', 'manual'
    base_url = db.Column(String(500), nullable=True)
    api_key_required = db.Column(Boolean, default=False)
    
    # Sync status
    last_sync = db.Column(DateTime, nullable=True)
    next_sync = db.Column(DateTime, nullable=True)
    sync_frequency = db.Column(String(50), nullable=True)  # 'daily', 'weekly', 'monthly'
    records_synced = db.Column(Integer, default=0)
    sync_status = db.Column(String(20), default='pending')  # 'active', 'pending', 'error', 'disabled'
    
    # Rate limiting
    requests_per_minute = db.Column(Integer, default=60)
    requests_today = db.Column(Integer, default=0)
    rate_limit_reset = db.Column(DateTime, nullable=True)
    
    # Metadata
    description = db.Column(Text, nullable=True)
    data_types = db.Column(JSON, nullable=True)  # List of data types provided
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# Database migration helper
def get_enhanced_schema_additions():
    """
    Returns SQL commands to add new fields to existing tables
    """
    additions = [
        # Add new fields to existing orchid_record table
        "ALTER TABLE orchid_record ADD COLUMN eol_page_id VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN gbif_id VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN gbif_key VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN gbif_dataset_key VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN country VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN state_province VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN locality VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN decimal_latitude FLOAT;",
        "ALTER TABLE orchid_record ADD COLUMN decimal_longitude FLOAT;",
        "ALTER TABLE orchid_record ADD COLUMN coordinate_precision FLOAT;",
        "ALTER TABLE orchid_record ADD COLUMN elevation FLOAT;",
        "ALTER TABLE orchid_record ADD COLUMN collector VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN institution_code VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN catalog_number VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN collection_code VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN basis_of_record VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN event_date VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN year INTEGER;",
        "ALTER TABLE orchid_record ADD COLUMN month INTEGER;",
        "ALTER TABLE orchid_record ADD COLUMN day INTEGER;",
        "ALTER TABLE orchid_record ADD COLUMN image_creator VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN image_license VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN image_publisher VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN image_format VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN image_title VARCHAR(200);",
        "ALTER TABLE orchid_record ADD COLUMN life_stage VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN reproductive_condition VARCHAR(100);",
        "ALTER TABLE orchid_record ADD COLUMN establishment_means VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN habitat_description TEXT;",
        "ALTER TABLE orchid_record ADD COLUMN data_source VARCHAR(50);",
        "ALTER TABLE orchid_record ADD COLUMN source_url VARCHAR(500);",
        "ALTER TABLE orchid_record ADD COLUMN gbif_metadata JSON;",
        "ALTER TABLE orchid_record ADD COLUMN eol_traits JSON;",
        "ALTER TABLE orchid_record ADD COLUMN pollinator_data JSON;"
    ]
    
    return additions

print("Enhanced database models ready for integration!")
print("Key additions:")
print("- GBIF integration fields (geographic, temporal, collection data)")
print("- EOL trait and morphological data support") 
print("- Pollinator database with relationship tracking")
print("- External data source management")
print("- Enhanced image metadata and licensing")