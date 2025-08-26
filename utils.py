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
    """Get the orchid of the day based on date and available orchids with real images"""
    try:
        # Use current date as seed for consistent daily selection
        today = date.today()
        seed = int(today.strftime("%Y%m%d"))
        random.seed(seed)
        
        # Get orchids with STRICT quality criteria (same as enhanced system)
        orchids = OrchidRecord.query.filter(
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

def validate_orchid_data(data):
    """Validate orchid data before saving"""
    errors = []
    
    # Required fields
    if not data.get('display_name'):
        errors.append("Display name is required")
    
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
