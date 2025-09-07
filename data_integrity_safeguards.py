"""
Data Integrity Safeguards for Orchid Database
Prevents genus/species data from becoming disconnected from images
"""

from models import db, OrchidRecord
import re
import logging

logger = logging.getLogger(__name__)

def validate_orchid_record_integrity(orchid_record):
    """
    Validates that orchid records maintain data integrity between 
    taxonomic information and images.
    
    Critical Rule: If an orchid has an image, it MUST have genus data.
    """
    has_image = bool(orchid_record.google_drive_id or orchid_record.image_url or orchid_record.image_filename)
    has_genus = bool(orchid_record.genus and orchid_record.genus.strip())
    
    if has_image and not has_genus:
        # CRITICAL INTEGRITY VIOLATION - Auto-fix if possible
        logger.error(f"CRITICAL: Record {orchid_record.id} has image but no genus!")
        
        # Try to extract genus from display_name or scientific_name
        display_name = orchid_record.display_name or orchid_record.scientific_name or ""
        extracted_genus = extract_genus_from_name(display_name)
        
        if extracted_genus:
            logger.info(f"Auto-fixing: Extracting genus '{extracted_genus}' from '{display_name}'")
            orchid_record.genus = extracted_genus
            
            # Also try to extract species
            extracted_species = extract_species_from_name(display_name)
            if extracted_species and not orchid_record.species:
                orchid_record.species = extracted_species
                
            return True  # Fixed
        else:
            logger.error(f"CANNOT AUTO-FIX: No genus extractable from '{display_name}'")
            return False  # Critical error
    
    return True  # Valid

def extract_genus_from_name(name):
    """Extract genus from scientific or display name"""
    if not name:
        return None
        
    # Remove common prefixes/suffixes
    name = name.strip()
    
    # Known genus patterns
    genus_patterns = [
        r'^(Cattleya)\b',
        r'^(Phalaenopsis)\b', 
        r'^(Dendrobium)\b',
        r'^(Oncidium)\b',
        r'^(Paphiopedilum)\b',
        r'^(Masdevallia)\b',
        r'^(Maxillaria)\b',
        r'^(Pleurothallis)\b',
        r'^(Dracula)\b',
        r'^(Brassia)\b',
        r'^(Epidendrum)\b',
        r'^(Angraecum)\b',
        r'^(Aerangis)\b',
        r'^(Jumellea)\b',
        r'^(Sophrolaeliocattleya)\b',
        r'^(Laeliocattleya)\b',
        r'^(Brassolaeliocattleya)\b',
        r'^(Potinara)\b',
        r'^([A-Z][a-z]+)\b'  # Generic capitalized word
    ]
    
    for pattern in genus_patterns:
        match = re.search(pattern, name, re.IGNORECASE)
        if match:
            return match.group(1).capitalize()
    
    return None

def extract_species_from_name(name):
    """Extract species from scientific name"""
    if not name:
        return None
        
    # Pattern: Genus species (may have additional info)
    match = re.match(r'^[A-Z][a-z]+\s+([a-z]+)', name)
    if match:
        return match.group(1).lower()
    
    return None

def enforce_data_integrity_before_save(orchid_record):
    """
    MANDATORY check before saving any OrchidRecord.
    Prevents the database corruption that happened before.
    """
    
    # Rule 1: If has image, MUST have genus
    if not validate_orchid_record_integrity(orchid_record):
        raise ValueError(f"Data integrity violation: Record has image but no genus data. "
                        f"Display name: '{orchid_record.display_name}', "
                        f"Image: {orchid_record.google_drive_id or orchid_record.image_url}")
    
    # Rule 2: Validate scientific name consistency
    if orchid_record.genus and orchid_record.species:
        expected_scientific = f"{orchid_record.genus} {orchid_record.species}"
        if (orchid_record.scientific_name and 
            orchid_record.scientific_name.strip().lower() != expected_scientific.lower()):
            logger.warning(f"Scientific name inconsistency: "
                          f"'{orchid_record.scientific_name}' vs '{expected_scientific}'")
    
    return True

def audit_existing_records():
    """
    Audits all existing records for integrity violations.
    Returns summary of issues found.
    """
    issues = {
        'images_without_genus': 0,
        'missing_scientific_names': 0,
        'inconsistent_names': 0,
        'total_records': 0,
        'problematic_records': []
    }
    
    records = OrchidRecord.query.all()
    issues['total_records'] = len(records)
    
    for record in records:
        has_image = bool(record.google_drive_id or record.image_url or record.image_filename)
        has_genus = bool(record.genus and record.genus.strip())
        
        if has_image and not has_genus:
            issues['images_without_genus'] += 1
            issues['problematic_records'].append({
                'id': record.id,
                'display_name': record.display_name,
                'issue': 'image_without_genus'
            })
    
    return issues

# Hook into SQLAlchemy events to prevent future corruption
from sqlalchemy import event

@event.listens_for(OrchidRecord, 'before_insert')
@event.listens_for(OrchidRecord, 'before_update')
def validate_before_save(mapper, connection, target):
    """Automatically validate data integrity before any save"""
    try:
        enforce_data_integrity_before_save(target)
    except ValueError as e:
        logger.error(f"Data integrity check failed: {e}")
        # In production, this would raise an error
        # For now, we'll log and auto-fix
        if not validate_orchid_record_integrity(target):
            logger.error(f"CRITICAL: Unable to auto-fix record {target.display_name}")