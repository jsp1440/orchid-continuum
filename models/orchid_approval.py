from app import db
from datetime import datetime
from sqlalchemy import Enum
import enum


class GalleryType(enum.Enum):
    ORCHID_OF_THE_DAY = "orchid_of_the_day"
    FEATURED_GALLERY = "featured_gallery"
    MAIN_GALLERY = "main_gallery"
    RECENT_ADDITIONS = "recent_additions"
    PREMIUM_SHOWCASE = "premium_showcase"
    SPECIES_SPOTLIGHT = "species_spotlight"


class ApprovalStatus(enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class OrchidApproval(db.Model):
    """Admin approval system for orchid display in galleries"""
    __tablename__ = 'orchid_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    orchid_id = db.Column(db.Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    special_display_id = db.Column(db.String(20), unique=True, nullable=False)  # FCOS-001, FCOS-002, etc.
    
    # Gallery assignments
    gallery_type = db.Column(Enum(GalleryType), nullable=False)
    status = db.Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    
    # Orchid of the Day scheduling
    scheduled_date = db.Column(db.Date, nullable=True)  # When this orchid should be featured
    priority_order = db.Column(db.Integer, default=1)  # Display priority within gallery
    
    # Admin metadata approval
    approved_genus = db.Column(db.String(100), nullable=False)
    approved_species = db.Column(db.String(100), nullable=False)
    approved_common_name = db.Column(db.String(200), nullable=True)
    approved_country = db.Column(db.String(100), nullable=True)
    approved_description = db.Column(db.Text, nullable=True)
    
    # Validation flags
    taxonomy_verified = db.Column(db.Boolean, default=False)
    image_quality_approved = db.Column(db.Boolean, default=False)
    metadata_complete = db.Column(db.Boolean, default=False)
    
    # Admin info
    approved_by = db.Column(db.String(200), nullable=True)
    approved_at = db.Column(db.DateTime, nullable=True)
    rejection_reason = db.Column(db.Text, nullable=True)
    
    # Display customization
    custom_title = db.Column(db.String(300), nullable=True)
    custom_description = db.Column(db.Text, nullable=True)
    featured_highlights = db.Column(db.JSON, nullable=True)  # Special features to highlight
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orchid = db.relationship('OrchidRecord', backref='approvals')
    
    def __repr__(self):
        return f'<OrchidApproval {self.special_display_id}: {self.approved_genus} {self.approved_species}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'orchid_id': self.orchid_id,
            'special_display_id': self.special_display_id,
            'gallery_type': self.gallery_type.value if self.gallery_type else None,
            'status': self.status.value if self.status else None,
            'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
            'approved_genus': self.approved_genus,
            'approved_species': self.approved_species,
            'approved_common_name': self.approved_common_name,
            'approved_country': self.approved_country,
            'taxonomy_verified': self.taxonomy_verified,
            'image_quality_approved': self.image_quality_approved,
            'metadata_complete': self.metadata_complete,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None
        }


class OrchidTaxonomyValidation(db.Model):
    """Validated orchid taxonomy for admin reference"""
    __tablename__ = 'orchid_taxonomy_validation'
    
    id = db.Column(db.Integer, primary_key=True)
    genus = db.Column(db.String(100), nullable=False, index=True)
    species = db.Column(db.String(100), nullable=True, index=True)
    family = db.Column(db.String(100), default="Orchidaceae")
    subfamily = db.Column(db.String(100), nullable=True)
    tribe = db.Column(db.String(100), nullable=True)
    
    # Validation info
    is_accepted = db.Column(db.Boolean, default=True)
    authority = db.Column(db.String(300), nullable=True)
    synonyms = db.Column(db.JSON, nullable=True)
    common_names = db.Column(db.JSON, nullable=True)
    
    # Distribution
    native_regions = db.Column(db.JSON, nullable=True)
    cultivation_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('genus', 'species', name='unique_genus_species'),)
    
    def __repr__(self):
        return f'<ValidTaxonomy {self.genus} {self.species or "sp."}>'


class GalleryConfiguration(db.Model):
    """Configuration for different gallery displays"""
    __tablename__ = 'gallery_configurations'
    
    id = db.Column(db.Integer, primary_key=True)
    gallery_name = db.Column(db.String(100), unique=True, nullable=False)
    gallery_type = db.Column(Enum(GalleryType), nullable=False)
    display_title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Display settings
    max_items = db.Column(db.Integer, default=12)
    auto_refresh_hours = db.Column(db.Integer, default=24)  # How often to refresh content
    show_metadata_fields = db.Column(db.JSON, nullable=True)  # Which fields to show
    
    # Approval requirements
    require_admin_approval = db.Column(db.Boolean, default=True)
    require_taxonomy_verification = db.Column(db.Boolean, default=True)
    require_image_quality_check = db.Column(db.Boolean, default=True)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Gallery {self.gallery_name}>'