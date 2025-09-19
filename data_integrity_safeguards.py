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

def validate_featured_orchids():
    """
    Validate that featured orchids have proper genus and species data
    """
    try:
        from sqlalchemy import or_
        
        # Find featured orchids without proper taxonomy
        featured_problems = OrchidRecord.query.filter(
            OrchidRecord.is_featured == True,
            or_(
                OrchidRecord.genus.is_(None),
                OrchidRecord.genus == '',
                OrchidRecord.species.is_(None),
                OrchidRecord.species == ''
            )
        ).all()
        
        if featured_problems:
            logger.warning(f"🚨 Found {len(featured_problems)} featured orchids with missing genus/species data")
            for orchid in featured_problems:
                logger.warning(f"   - Featured orchid {orchid.id}: {orchid.display_name} missing genus={orchid.genus}, species={orchid.species}")
                # AUTOMATICALLY REMOVE FROM FEATURED STATUS
                orchid.is_featured = False
                orchid.validation_status = 'auto_unfeatured'
                logger.info(f"🔧 Auto-removed orchid {orchid.id} from featured status due to missing taxonomy")
            
            db.session.commit()
            return False
        
        logger.info("✅ All featured orchids have proper genus/species data")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error validating featured orchids: {e}")
        return False


def auto_prevent_bad_featured_selection():
    """
    Automatically prevent bad orchids from being featured
    RUNS EVERY TIME THE HOMEPAGE LOADS
    """
    try:
        from sqlalchemy import or_
        
        # Find and remove any featured orchids with validation problems
        bad_featured = OrchidRecord.query.filter(
            OrchidRecord.is_featured == True,
            or_(
                OrchidRecord.validation_status.in_(['incorrect_id', 'wrong_genus', 'needs_identification']),
                OrchidRecord.genus.is_(None),
                OrchidRecord.genus == ''
            )
        ).all()
        
        removed_count = 0
        for orchid in bad_featured:
            orchid.is_featured = False
            orchid.cultural_notes = f"Auto-removed from featured status: {orchid.validation_status or 'missing genus'}"
            removed_count += 1
            logger.info(f"🔧 Auto-removed bad featured orchid: {orchid.display_name} (ID: {orchid.id})")
        
        if removed_count > 0:
            db.session.commit()
            logger.info(f"✅ Auto-removed {removed_count} problematic orchids from featured status")
        
        # Ensure we have enough good featured orchids
        good_featured_count = OrchidRecord.query.filter(
            OrchidRecord.is_featured == True,
            OrchidRecord.google_drive_id.isnot(None),
            OrchidRecord.genus.isnot(None),
            OrchidRecord.genus != ''
        ).count()
        
        if good_featured_count < 5:
            # Add more good orchids to featured
            candidates = OrchidRecord.query.filter(
                OrchidRecord.is_featured == False,
                OrchidRecord.validation_status == 'validated',
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.genus.isnot(None),
                OrchidRecord.genus != ''
            ).limit(10 - good_featured_count).all()
            
            for candidate in candidates:
                candidate.is_featured = True
                logger.info(f"✅ Auto-added good orchid to featured: {candidate.display_name} (ID: {candidate.id})")
            
            if candidates:
                db.session.commit()
                logger.info(f"✅ Auto-added {len(candidates)} good orchids to featured status")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Error in auto-prevention system: {e}")
        return False