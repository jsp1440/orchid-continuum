"""
Database configuration and models for The Orchid Continuum.
Uses neutral field names to protect proprietary schema.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Float, Boolean, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from geoalchemy2 import Geometry
from pgvector.sqlalchemy import Vector
import uuid
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="viewer")  # viewer, member, contributor, curator, admin
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)

class Record(Base):
    """Generic record model with neutral field names."""
    __tablename__ = "records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False, index=True)
    scientific_name = Column(String(255), index=True)
    common_name = Column(String(255), index=True)
    taxonomy_family = Column(String(100), index=True)
    taxonomy_genus = Column(String(100), index=True)
    taxonomy_species = Column(String(100), index=True)
    description = Column(Text)
    ai_description = Column(Text)
    ai_confidence = Column(Float)
    ai_embeddings = Column(Vector(1536))  # OpenAI embeddings dimension
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_status = Column(String(50), default="pending")  # pending, approved, flagged, merged
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="records")
    media_items = relationship("Media", back_populates="record")
    locations = relationship("Location", back_populates="record")
    tags = relationship("RecordTag", back_populates="record")
    curation_events = relationship("CurationEvent", back_populates="record")

class Media(Base):
    """Media files associated with records."""
    __tablename__ = "media"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False)
    media_type = Column(String(50), nullable=False)  # image, video, audio
    file_path = Column(String(1000), nullable=False)
    file_url = Column(String(1000))
    mime_type = Column(String(100))
    file_size = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    exif_data = Column(JSONB)
    rights_info = Column(JSONB)  # photographer, license, restrictions
    is_featured = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    record = relationship("Record", back_populates="media_items")

class Location(Base):
    """Geographic location data."""
    __tablename__ = "locations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False)
    location_name = Column(String(255))
    country = Column(String(100), index=True)
    region = Column(String(100), index=True)
    latitude = Column(Float, index=True)
    longitude = Column(Float, index=True)
    elevation = Column(Float)
    geometry = Column(Geometry('POINT', srid=4326))
    habitat_type = Column(String(100))
    climate_zone = Column(String(100))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    record = relationship("Record", back_populates="locations")
    
    # Spatial index
    __table_args__ = (
        Index('ix_locations_geometry', geometry, postgresql_using='gist'),
    )

class Tag(Base):
    """Tags for categorizing records."""
    __tablename__ = "tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(50), index=True)  # trait, habitat, phenology, etc.
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)

class RecordTag(Base):
    """Many-to-many relationship between records and tags."""
    __tablename__ = "record_tags"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False)
    tag_id = Column(UUID(as_uuid=True), ForeignKey("tags.id"), nullable=False)
    confidence = Column(Float)  # AI confidence if auto-tagged
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    record = relationship("Record", back_populates="tags")
    tag = relationship("Tag")
    creator = relationship("User")

class CurationEvent(Base):
    """Track curation actions on records."""
    __tablename__ = "curation_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    record_id = Column(UUID(as_uuid=True), ForeignKey("records.id"), nullable=False)
    action_type = Column(String(50), nullable=False)  # approve, flag, merge, reject
    curator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    notes = Column(Text)
    metadata = Column(JSONB)  # Additional action-specific data
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Relationships
    record = relationship("Record", back_populates="curation_events")
    curator = relationship("User")

# Add back_populates to User
User.records = relationship("Record", back_populates="creator")

class DatabaseManager:
    """Database session and connection management."""
    
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
    
    def get_session(self):
        """Get database session."""
        db = self.SessionLocal()
        try:
            yield db
        finally:
            db.close()
    
    def create_tables(self):
        """Create all tables."""
        Base.metadata.create_all(bind=self.engine)
    
    def enable_extensions(self):
        """Enable required PostgreSQL extensions."""
        with self.engine.connect() as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()