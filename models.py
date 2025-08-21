from app import db
from datetime import datetime
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime

class OrchidTaxonomy(db.Model):
    """Master taxonomy table for orchid classification"""
    id = db.Column(Integer, primary_key=True)
    scientific_name = db.Column(String(200), unique=True, nullable=False, index=True)
    genus = db.Column(String(100), nullable=False, index=True)
    species = db.Column(String(100), nullable=False)
    author = db.Column(String(200))
    synonyms = db.Column(Text)  # JSON string of alternative names
    common_names = db.Column(Text)  # JSON string of common names
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to orchid records
    orchids = db.relationship('OrchidRecord', backref='taxonomy', lazy=True)

    def __repr__(self):
        return f'<OrchidTaxonomy {self.scientific_name}>'

class OrchidRecord(db.Model):
    """Main orchid record with metadata"""
    id = db.Column(Integer, primary_key=True)
    
    # Taxonomy relationship
    taxonomy_id = db.Column(Integer, db.ForeignKey('orchid_taxonomy.id'), nullable=True)
    
    # Basic information
    display_name = db.Column(String(200), nullable=False)
    scientific_name = db.Column(String(200), index=True)
    genus = db.Column(String(100), index=True)
    species = db.Column(String(100))
    author = db.Column(String(200))
    
    # Geographic and habitat data
    region = db.Column(String(100))
    native_habitat = db.Column(Text)
    
    # Growing characteristics
    bloom_time = db.Column(String(100))
    growth_habit = db.Column(String(50))  # epiphytic, terrestrial, lithophytic
    climate_preference = db.Column(String(20))  # cool, intermediate, warm
    leaf_form = db.Column(String(100))
    pseudobulb_presence = db.Column(Boolean)
    
    # Cultural information
    light_requirements = db.Column(String(50))
    temperature_range = db.Column(String(100))
    water_requirements = db.Column(Text)
    fertilizer_needs = db.Column(Text)
    cultural_notes = db.Column(Text)
    
    # Image and source metadata
    image_filename = db.Column(String(300))
    image_url = db.Column(String(500))
    google_drive_id = db.Column(String(100))
    photographer = db.Column(String(200))
    image_source = db.Column(String(200))
    
    # AI and OCR data
    ocr_text = db.Column(Text)
    ai_description = db.Column(Text)
    ai_confidence = db.Column(Float)
    ai_extracted_metadata = db.Column(Text)  # JSON string
    
    # System metadata
    ingestion_source = db.Column(String(50))  # 'upload', 'scrape_gary', 'scrape_roberta', 'legacy'
    validation_status = db.Column(String(20), default='pending')  # pending, validated, rejected
    is_featured = db.Column(Boolean, default=False)
    view_count = db.Column(Integer, default=0)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<OrchidRecord {self.display_name}>'

class ScrapingLog(db.Model):
    """Log of scraping activities"""
    id = db.Column(Integer, primary_key=True)
    source = db.Column(String(50), nullable=False)  # 'gary_yong_gee', 'roberta_fox'
    url = db.Column(String(500), nullable=False)
    status = db.Column(String(20), nullable=False)  # 'success', 'error', 'skipped'
    error_message = db.Column(Text)
    items_found = db.Column(Integer, default=0)
    items_processed = db.Column(Integer, default=0)
    created_at = db.Column(DateTime, default=datetime.utcnow)

class UserUpload(db.Model):
    """Track user uploads and submissions"""
    id = db.Column(Integer, primary_key=True)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    original_filename = db.Column(String(300), nullable=False)
    uploaded_filename = db.Column(String(300), nullable=False)
    file_size = db.Column(Integer)
    mime_type = db.Column(String(100))
    user_notes = db.Column(Text)
    processing_status = db.Column(String(20), default='pending')  # pending, processing, completed, failed
    created_at = db.Column(DateTime, default=datetime.utcnow)

class WidgetConfig(db.Model):
    """Configuration for various widgets"""
    id = db.Column(Integer, primary_key=True)
    widget_name = db.Column(String(50), unique=True, nullable=False)
    config_data = db.Column(Text)  # JSON string with widget configuration
    is_active = db.Column(Boolean, default=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
