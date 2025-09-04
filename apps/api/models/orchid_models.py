from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Float, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from database import Base
from datetime import datetime
import uuid
import enum

class SourceType(enum.Enum):
    GOOGLE_DRIVE = "google_drive"
    GBIF = "gbif"
    USER = "user"
    OTHER = "other"

class CultureSource(enum.Enum):
    BAKER = "baker"
    AOS = "aos"
    CUSTOM = "custom"

class IUCNStatus(enum.Enum):
    LC = "LC"  # Least Concern
    NT = "NT"  # Near Threatened
    VU = "VU"  # Vulnerable
    EN = "EN"  # Endangered
    CR = "CR"  # Critically Endangered
    EW = "EW"  # Extinct in Wild
    EX = "EX"  # Extinct
    DD = "DD"  # Data Deficient
    NE = "NE"  # Not Evaluated

class UserRole(enum.Enum):
    ADMIN = "admin"
    EDITOR = "editor"
    MEMBER = "member"
    VIEWER = "viewer"

class CollectionStatus(enum.Enum):
    ACTIVE = "active"
    DORMANT = "dormant"
    BLOOMING = "blooming"
    DECEASED = "deceased"

# Main orchid table
class Orchid(Base):
    __tablename__ = "orchids"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    scientific_name = Column(String(255), nullable=False, index=True)
    genus = Column(String(100), nullable=False, index=True)
    species = Column(String(100), nullable=True)
    hybrid_status = Column(Boolean, default=False)
    synonyms = Column(JSONB, nullable=True)  # Array of alternative names
    description = Column(Text, nullable=True)
    growth_habit = Column(String(50), nullable=True)  # epiphytic, terrestrial, lithophytic
    iucn_status = Column(SQLEnum(IUCNStatus), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    photos = relationship("Photo", back_populates="orchid", cascade="all, delete-orphan")
    culture_sheets = relationship("CultureSheet", back_populates="orchid", cascade="all, delete-orphan")
    traits = relationship("Trait", back_populates="orchid", cascade="all, delete-orphan")
    occurrences = relationship("Occurrence", back_populates="orchid", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="orchid", cascade="all, delete-orphan")

# Photo management table
class Photo(Base):
    __tablename__ = "photos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=False)
    source = Column(SQLEnum(SourceType), nullable=False)
    source_ref = Column(Text, nullable=True)  # Drive file ID, GBIF media key, etc.
    url = Column(Text, nullable=True)
    storage_key = Column(String(255), nullable=True)  # For object storage
    exif = Column(JSONB, nullable=True)  # EXIF metadata
    credited_to = Column(String(255), nullable=True)
    license = Column(String(100), nullable=True)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    orchid = relationship("Orchid", back_populates="photos")

# Culture sheets (Baker, AOS, custom)
class CultureSheet(Base):
    __tablename__ = "culture_sheets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=True)
    source = Column(SQLEnum(CultureSource), nullable=False)
    
    # Care requirements
    light_low = Column(Integer, nullable=True)  # foot-candles
    light_high = Column(Integer, nullable=True)
    temp_min = Column(Float, nullable=True)  # Celsius
    temp_max = Column(Float, nullable=True)
    humidity_min = Column(Float, nullable=True)  # Percentage
    humidity_max = Column(Float, nullable=True)
    
    # Care notes
    water_notes = Column(Text, nullable=True)
    media_notes = Column(Text, nullable=True)
    seasonal_notes = Column(Text, nullable=True)
    
    # Metadata
    citations = Column(JSONB, nullable=True)
    version = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    orchid = relationship("Orchid", back_populates="culture_sheets")

# Phenotypic traits
class Trait(Base):
    __tablename__ = "traits"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=False)
    phenotypic = Column(JSONB, nullable=False)  # Flexible trait storage
    
    # Relationship
    orchid = relationship("Orchid", back_populates="traits")

# GBIF occurrences
class Occurrence(Base):
    __tablename__ = "occurrences"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=False)
    gbif_occurrence_id = Column(String(50), nullable=True, index=True)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    elev_m = Column(Float, nullable=True)
    country = Column(String(100), nullable=True)
    date_observed = Column(DateTime, nullable=True)
    raw = Column(JSONB, nullable=True)  # Original GBIF data
    
    # Relationship
    orchid = relationship("Orchid", back_populates="occurrences")

# Citations and references
class Citation(Base):
    __tablename__ = "citations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=False)
    doi = Column(String(255), nullable=True)
    title = Column(Text, nullable=False)
    source = Column(String(255), nullable=True)
    url = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)
    
    # Relationship
    orchid = relationship("Orchid", back_populates="citations")

# User management
class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.VIEWER)
    display_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    collections = relationship("Collection", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")

# Personal collections
class Collection(Base):
    __tablename__ = "collections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    notes = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="collections")
    items = relationship("CollectionItem", back_populates="collection", cascade="all, delete-orphan")

class CollectionItem(Base):
    __tablename__ = "collection_items"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collection_id = Column(UUID(as_uuid=True), ForeignKey("collections.id"), nullable=False)
    orchid_id = Column(UUID(as_uuid=True), ForeignKey("orchids.id"), nullable=False)
    nick_name = Column(String(255), nullable=True)  # User's personal name
    acquired_at = Column(DateTime, nullable=True)
    last_repot = Column(DateTime, nullable=True)
    status = Column(SQLEnum(CollectionStatus), default=CollectionStatus.ACTIVE)
    care_prefs = Column(JSONB, nullable=True)  # Personal care notes
    
    # Relationships
    collection = relationship("Collection", back_populates="items")
    orchid = relationship("Orchid")

# Audit logging
class AuditLog(Base):
    __tablename__ = "audit_log"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)  # CREATE, UPDATE, DELETE
    entity = Column(String(100), nullable=False)  # Table name
    entity_id = Column(String(255), nullable=False)  # Record ID
    diff = Column(JSONB, nullable=True)  # Changes made
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    user = relationship("User", back_populates="audit_logs")

# Data sources configuration
class Source(Base):
    __tablename__ = "sources"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    type = Column(SQLEnum(SourceType), nullable=False)
    auth = Column(JSONB, nullable=True)  # API keys, tokens, etc.
    status = Column(String(50), default="active")
    last_sync_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)