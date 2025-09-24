import os
import uuid
from datetime import datetime, date
import random
from models import OrchidRecord
from sqlalchemy import or_, and_
import logging

logger = logging.getLogger(__name__)

def allowed_file(filename):
    """Check if file extension is allowed"""
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp'}
    return '.' in filename and \
           os.path.splitext(filename)[1].lower() in ALLOWED_EXTENSIONS

def generate_filename(original_filename):
    """Generate a unique filename with timestamp and UUID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_ext = os.path.splitext(original_filename)[1].lower()
    unique_id = str(uuid.uuid4())[:8]
    return f"orchid_{timestamp}_{unique_id}{file_ext}"

def get_orchid_of_the_day():
    """Get the orchid of the day based on date and available orchids with real images - FIXED to prevent mismatches"""
    try:
        # USER REQUIREMENT: Only select genus and species orchids, never hybrids
            
        # Fallback to random selection if Gary's orchid not available
        today = date.today()
        seed = int(today.strftime("%Y%m%d"))
        random.seed(seed)
        
        # Get EPIPHYTIC orchids only - GENUS + SPECIES ONLY (NO HYBRIDS)
        orchids = OrchidRecord.query.filter(
            # CRITICAL: Exclude all hybrids
            OrchidRecord.is_hybrid != True,
            ~OrchidRecord.display_name.ilike('%hybrid%'),
            ~OrchidRecord.display_name.ilike('%x %'),  # Exclude intergeneric crosses
            ~OrchidRecord.scientific_name.ilike('%x %'),
            OrchidRecord.display_name.notlike('%"%'), # Exclude cultivar names with quotes
            # PRIORITY: Epiphytic orchids only
            or_(
                OrchidRecord.growth_habit == 'epiphytic',
                OrchidRecord.growth_habit == 'Epiphytic',
                OrchidRecord.ai_description.ilike('%epiphytic%'),
                OrchidRecord.ai_description.ilike('%epiphyte%')
            ),
            # PRIORITY: Reliable images (Google Drive OR working external URLs)
            or_(
                OrchidRecord.google_drive_id.isnot(None),
                and_(
                    OrchidRecord.image_url.isnot(None),
                    OrchidRecord.image_url != '/static/images/orchid_placeholder.svg',
                    OrchidRecord.image_url.notlike('%placeholder%'),
                    OrchidRecord.image_url != ''
                )
            ),
            # Has BOTH genus AND species information (fully spelled out)
            OrchidRecord.genus.isnot(None),
            OrchidRecord.species.isnot(None),
            OrchidRecord.genus != '',
            OrchidRecord.species != '',
            # No single letter abbreviations
            ~OrchidRecord.genus.like('%.'),
            ~OrchidRecord.species.like('%.'),
            # Has country/region of origin
            or_(
                OrchidRecord.region.isnot(None),
                OrchidRecord.native_habitat.isnot(None)
            ),
            # Has metadata/description (relaxed requirement)
            OrchidRecord.ai_description.isnot(None),
            # Has proper name (not just "Unknown Orchid")
            OrchidRecord.display_name != 'Unknown Orchid',
            OrchidRecord.display_name.isnot(None),
            # Not rejected
            OrchidRecord.validation_status != 'rejected'
        ).all()
        
        candidate_orchids = orchids
        
        # If no orchids meet strict criteria, try relaxed criteria
        if not candidate_orchids:
            logger.info("No orchids found with strict criteria, trying relaxed search...")
            candidate_orchids = OrchidRecord.query.filter(
                # Must have Google Drive ID (real photos only!)
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.google_drive_id != '',
                OrchidRecord.google_drive_id != 'None',
                # Has display name
                OrchidRecord.display_name.isnot(None),
                OrchidRecord.display_name != '',
                # Not rejected
                OrchidRecord.validation_status != 'rejected'
            ).limit(50).all()
        
        # If still no results, get ANY orchid with an image (no validation status filter)
        if not candidate_orchids:
            logger.info("No orchids found with relaxed criteria, getting any orchid with image...")
            candidate_orchids = OrchidRecord.query.filter(
                OrchidRecord.google_drive_id.isnot(None),
                OrchidRecord.google_drive_id != '',
                OrchidRecord.google_drive_id != 'None'
            ).limit(50).all()
        
        # Final fallback - just get ANY orchid with display name
        if not candidate_orchids:
            logger.info("Still no results, getting any orchid from database...")
            candidate_orchids = OrchidRecord.query.filter(
                OrchidRecord.display_name.isnot(None),
                OrchidRecord.display_name != ''
            ).limit(20).all()
        
        if candidate_orchids:
            # Select orchid based on seeded random
            selected_orchid = random.choice(candidate_orchids)
            
            # Ensure the selected orchid has a working image URL
            if selected_orchid.google_drive_id:
                # Update image_url to use the drive API if it's not already set correctly
                expected_url = f"/api/drive-photo/{selected_orchid.google_drive_id}"
                if selected_orchid.image_url != expected_url:
                    selected_orchid.image_url = expected_url
            
            logger.info(f"Selected orchid of the day: {selected_orchid.display_name} (ID: {selected_orchid.id})")
            return selected_orchid
        else:
            logger.warning("No orchids with real images available for orchid of the day")
            return None
            
    except Exception as e:
        logger.error(f"Error getting orchid of the day: {str(e)}")
        return None

def parse_scientific_name(name):
    """Parse a scientific name into genus, species, and author"""
    try:
        parts = name.strip().split()
        if len(parts) >= 2:
            genus = parts[0]
            species = parts[1]
            author = ' '.join(parts[2:]) if len(parts) > 2 else None
            return genus, species, author
        else:
            return parts[0] if parts else None, None, None
    except Exception as e:
        logger.error(f"Error parsing scientific name '{name}': {str(e)}")
        return None, None, None

def format_scientific_name(genus, species, author=None):
    """Format genus, species, and author into proper scientific name"""
    if not genus:
        return None
    
    name = genus
    if species:
        name += f" {species}"
    if author:
        name += f" {author}"
    
    return name

def validate_google_drive_id_unique(google_drive_id, current_orchid_id=None):
    """
    Validate that a Google Drive ID is not already assigned to another orchid.
    Prevents duplicate image assignments that cause data quality issues.
    
    Args:
        google_drive_id: The Google Drive ID to check
        current_orchid_id: ID of current orchid (for updates, to exclude self)
    
    Returns:
        tuple: (is_valid, error_message, existing_orchid_info)
    """
    if not google_drive_id or google_drive_id in ['', 'None']:
        return True, None, None
    
    try:
        from models import OrchidRecord
        
        # Check if this Google Drive ID is already used by another orchid
        query = OrchidRecord.query.filter(
            OrchidRecord.google_drive_id == google_drive_id,
            OrchidRecord.google_drive_id.isnot(None),
            OrchidRecord.google_drive_id != '',
            OrchidRecord.google_drive_id != 'None'
        )
        
        # Exclude current orchid if this is an update
        if current_orchid_id:
            query = query.filter(OrchidRecord.id != current_orchid_id)
        
        existing_orchid = query.first()
        
        if existing_orchid:
            error_msg = f"Google Drive ID '{google_drive_id}' is already assigned to orchid '{existing_orchid.display_name}' (ID: {existing_orchid.id})"
            orchid_info = {
                'id': existing_orchid.id,
                'display_name': existing_orchid.display_name,
                'genus': existing_orchid.genus,
                'species': existing_orchid.species
            }
            return False, error_msg, orchid_info
        
        return True, None, None
        
    except Exception as e:
        logger.error(f"Error validating Google Drive ID uniqueness: {str(e)}")
        return False, f"Error validating Google Drive ID: {str(e)}", None

def validate_orchid_data(data):
    """Validate orchid data before saving"""
    errors = []
    
    # Required fields
    if not data.get('display_name'):
        errors.append("Display name is required")
    
    # Validate Google Drive ID uniqueness
    if data.get('google_drive_id'):
        is_valid, error_msg, existing_info = validate_google_drive_id_unique(
            data['google_drive_id'], 
            data.get('id')  # Pass current orchid ID for updates
        )
        if not is_valid:
            errors.append(error_msg)
    
    # Validate scientific name format if provided
    if data.get('scientific_name'):
        genus, species, author = parse_scientific_name(data['scientific_name'])
        if not genus:
            errors.append("Invalid scientific name format")
    
    # Validate climate preference
    if data.get('climate_preference'):
        valid_climates = ['cool', 'intermediate', 'warm']
        if data['climate_preference'] not in valid_climates:
            errors.append(f"Climate preference must be one of: {', '.join(valid_climates)}")
    
    # Validate growth habit
    if data.get('growth_habit'):
        valid_habits = ['epiphytic', 'terrestrial', 'lithophytic']
        if data['growth_habit'] not in valid_habits:
            errors.append(f"Growth habit must be one of: {', '.join(valid_habits)}")
    
    return errors

def get_popular_orchids(limit=10):
    """Get most viewed orchids"""
    try:
        return OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None)
        ).order_by(OrchidRecord.view_count.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting popular orchids: {str(e)}")
        return []

def get_recent_uploads(limit=10):
    """Get recently uploaded orchids"""
    try:
        return OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.ingestion_source == 'upload'
        ).order_by(OrchidRecord.created_at.desc()).limit(limit).all()
    except Exception as e:
        logger.error(f"Error getting recent uploads: {str(e)}")
        return []

def clean_filename(filename):
    """Clean filename for safe storage"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename.lower()

def get_file_size_mb(file_path):
    """Get file size in MB"""
    try:
        size_bytes = os.path.getsize(file_path)
        return round(size_bytes / (1024 * 1024), 2)
    except Exception as e:
        logger.error(f"Error getting file size for {file_path}: {str(e)}")
        return 0

def create_thumbnail(image_path, thumbnail_path, size=(300, 300)):
    """Create thumbnail of an image"""
    try:
        from PIL import Image
        with Image.open(image_path) as img:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(thumbnail_path, optimize=True, quality=85)
        return True
    except Exception as e:
        logger.error(f"Error creating thumbnail: {str(e)}")
        return False
