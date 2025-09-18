from app import db
from datetime import datetime, timedelta
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON, Enum, and_, or_
from sqlalchemy.sql import operators
from flask_login import UserMixin
from typing import List, Optional, Any
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import enum
import json
import uuid

# Enums for pollinator standardized vocabularies
class PollinatorTypeEnum(enum.Enum):
    BEE = "bee"
    BUTTERFLY = "butterfly"
    MOTH = "moth"
    BEETLE = "beetle"
    FLY = "fly"
    WASP = "wasp"
    BIRD = "bird"
    BAT = "bat"
    BEETLE_WEEVIL = "beetle_weevil"
    ANT = "ant"
    THRIPS = "thrips"
    OTHER = "other"

class RelationshipTypeEnum(enum.Enum):
    MUTUALISTIC = "mutualistic"
    DECEPTIVE = "deceptive"
    OCCASIONAL = "occasional"
    PRIMARY = "primary"
    SPECIALIST = "specialist"
    GENERALIST = "generalist"
    PREDATORY = "predatory"
    COMPETITIVE = "competitive"

class LifecycleStageEnum(enum.Enum):
    EGG = "egg"
    LARVA = "larva"
    PUPA = "pupa"
    ADULT = "adult"
    JUVENILE = "juvenile"
    NYMPH = "nymph"

class MigrationTypeEnum(enum.Enum):
    SEASONAL = "seasonal"
    ALTITUDINAL = "altitudinal"
    LOCAL = "local"
    LONG_DISTANCE = "long_distance"
    NOMADIC = "nomadic"
    NONE = "none"

# Bug Report System for Beta Testing
class BugReport(db.Model):
    """Bug reports from beta testers for AI agent immediate fixing"""
    __tablename__ = 'bug_reports'
    
    id = db.Column(Integer, primary_key=True)
    item_type = db.Column(String(50), nullable=False)  # 'movie', 'widget', 'photo', 'general'
    item_id = db.Column(String(100), nullable=False)   # specific ID of the broken item
    item_name = db.Column(String(200), nullable=False) # human-readable name
    issue_type = db.Column(String(50), nullable=False) # 'broken_link', 'image_not_loading', 'widget_crash', 'other'
    description = db.Column(Text, nullable=False)     # detailed description from user
    user_email = db.Column(String(120), nullable=True) # optional email for follow-up
    status = db.Column(String(20), default='open')    # 'open', 'in_progress', 'fixed', 'closed'
    created_at = db.Column(DateTime, default=datetime.utcnow)
    fixed_at = db.Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'item_type': self.item_type,
            'item_id': self.item_id,
            'item_name': self.item_name,
            'issue_type': self.issue_type,
            'description': self.description,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'fixed_at': self.fixed_at.isoformat() if self.fixed_at else None
        }

# SVO Analysis Models for Web Interface
class SvoAnalysisSession(db.Model):
    """SVO analysis sessions tracking multi-website analysis"""
    __tablename__ = 'svo_analysis_sessions'
    
    id = db.Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_name = db.Column(String(200), nullable=False)
    urls = db.Column(JSON, nullable=False)  # List of URLs to analyze
    status = db.Column(String(20), default='pending')  # pending, running, completed, failed
    progress_percent = db.Column(Integer, default=0)
    current_url_index = db.Column(Integer, default=0)
    total_svo_found = db.Column(Integer, default=0)
    
    # Analysis configuration
    max_retries = db.Column(Integer, default=3)
    timeout_seconds = db.Column(Integer, default=10)
    extraction_patterns = db.Column(String(50), default='all')  # all, growth_patterns, etc.
    min_context_length = db.Column(Integer, default=10)
    max_results_per_url = db.Column(Integer, default=500)
    include_scientific_terms = db.Column(Boolean, default=True)
    filter_noise = db.Column(Boolean, default=True)
    collection_type = db.Column(String(50), default='custom')  # custom, orchid_care_sites, etc.
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    started_at = db.Column(DateTime, nullable=True)
    completed_at = db.Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = db.Column(Text, nullable=True)
    failed_urls = db.Column(JSON, nullable=True)  # URLs that failed to analyze
    
    # Research metadata
    research_notes = db.Column(Text, nullable=True)
    tags = db.Column(JSON, nullable=True)  # Research tags for categorization
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_name': self.session_name,
            'urls': self.urls,
            'status': self.status,
            'progress_percent': self.progress_percent,
            'current_url_index': self.current_url_index,
            'total_svo_found': self.total_svo_found,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'error_message': self.error_message,
            'failed_urls': self.failed_urls
        }

class SvoResult(db.Model):
    """Individual SVO tuples extracted from analysis"""
    __tablename__ = 'svo_results'
    
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(String, db.ForeignKey('svo_analysis_sessions.id'), nullable=False)
    source_url = db.Column(String(500), nullable=False)
    
    # Raw SVO data
    subject = db.Column(String(200), nullable=False)
    verb = db.Column(String(200), nullable=False)
    object = db.Column(String(200), nullable=False)
    
    # Cleaned SVO data
    subject_clean = db.Column(String(200), nullable=False)
    verb_clean = db.Column(String(200), nullable=False)
    object_clean = db.Column(String(200), nullable=False)
    
    # Context information
    context_text = db.Column(Text, nullable=True)  # Surrounding text for context
    confidence_score = db.Column(Float, default=1.0)  # Confidence in extraction
    
    # Botanical categorization
    botanical_category = db.Column(String(50), nullable=True)  # growth_patterns, flowering_behavior, etc.
    is_scientific_term = db.Column(Boolean, default=False)
    relevance_score = db.Column(Float, default=0.5)  # How relevant to botanical research
    
    # Enhanced metadata
    extraction_method = db.Column(String(50), default='pattern_matching')
    language_detected = db.Column(String(10), default='en')
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    session = db.relationship('SvoAnalysisSession', backref='results')
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'source_url': self.source_url,
            'subject': self.subject,
            'verb': self.verb,
            'object': self.object,
            'subject_clean': self.subject_clean,
            'verb_clean': self.verb_clean,
            'object_clean': self.object_clean,
            'context_text': self.context_text,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class SvoAnalysisSummary(db.Model):
    """Analysis summary and frequency data for sessions"""
    __tablename__ = 'svo_analysis_summaries'
    
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(String, db.ForeignKey('svo_analysis_sessions.id'), nullable=False)
    
    # Frequency data (stored as JSON)
    subject_frequencies = db.Column(JSON, nullable=False)  # Counter data as dict
    verb_frequencies = db.Column(JSON, nullable=False)
    object_frequencies = db.Column(JSON, nullable=False)
    
    # Summary statistics
    total_tuples = db.Column(Integer, nullable=False)
    unique_subjects = db.Column(Integer, nullable=False)
    unique_verbs = db.Column(Integer, nullable=False)
    unique_objects = db.Column(Integer, nullable=False)
    
    # Chart file paths
    subject_chart_path = db.Column(String(500), nullable=True)
    verb_chart_path = db.Column(String(500), nullable=True)
    object_chart_path = db.Column(String(500), nullable=True)
    
    # CSV export path
    csv_export_path = db.Column(String(500), nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    session = db.relationship('SvoAnalysisSession', backref='summary', uselist=False)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'subject_frequencies': self.subject_frequencies,
            'verb_frequencies': self.verb_frequencies,
            'object_frequencies': self.object_frequencies,
            'total_tuples': self.total_tuples,
            'unique_subjects': self.unique_subjects,
            'unique_verbs': self.unique_verbs,
            'unique_objects': self.unique_objects,
            'subject_chart_path': self.subject_chart_path,
            'verb_chart_path': self.verb_chart_path,
            'object_chart_path': self.object_chart_path,
            'csv_export_path': self.csv_export_path,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

# Gaming and User Management Models - Using unified User model below

class MahjongGame(db.Model):
    """Mahjong game sessions"""
    __tablename__ = 'mahjong_games'
    
    id = db.Column(Integer, primary_key=True)
    room_code = db.Column(String(6), unique=True, nullable=False)
    host_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    max_players = db.Column(Integer, default=4)
    current_players = db.Column(Integer, default=1)
    game_state = db.Column(String, default='waiting')  # waiting, playing, finished
    winner_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    game_duration = db.Column(Integer, default=0)  # seconds
    created_at = db.Column(DateTime, default=datetime.now)
    finished_at = db.Column(DateTime, nullable=True)
    
    # Game configuration
    tile_set = db.Column(Text, default='{"layout": "classic", "theme": "orchid"}')
    
    # Use direct foreign key references since User.id is String
    # host = db.relationship('User', foreign_keys=[host_user_id], backref='hosted_games')
    # winner = db.relationship('User', foreign_keys=[winner_user_id], backref='won_games')

class MahjongPlayer(db.Model):
    """Players in Mahjong games"""
    __tablename__ = 'mahjong_players'
    
    id = db.Column(Integer, primary_key=True)
    game_id = db.Column(Integer, db.ForeignKey('mahjong_games.id'), nullable=False)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    player_position = db.Column(Integer, nullable=False)  # 1-4
    score = db.Column(Integer, default=0)
    tiles_matched = db.Column(Integer, default=0)
    joined_at = db.Column(DateTime, default=datetime.now)
    is_active = db.Column(Boolean, default=True)

# Contest Entry Model for Monthly Contests
class ContestEntry(db.Model):
    """Contest entries for monthly orchid contests"""
    __tablename__ = 'contest_entries'
    
    id = db.Column(Integer, primary_key=True)
    member_id = db.Column(String(100), nullable=False)  # Neon One member ID
    member_name = db.Column(String(200), nullable=True)  # Member display name
    contest_month = db.Column(String(7), nullable=False)  # Format: 2025-01
    category = db.Column(String(50), nullable=False)  # 'species', 'hybrids', 'miniature', etc.
    
    # Photo details
    photo_url = db.Column(String(500), nullable=False)  # URL to uploaded photo
    google_drive_id = db.Column(String(200), nullable=True)  # Google Drive file ID
    orchid_name = db.Column(String(200), nullable=False)  # Scientific or common name
    description = db.Column(Text, nullable=True)  # Optional description
    care_notes = db.Column(Text, nullable=True)  # Care information
    
    # Contest metadata
    status = db.Column(String(20), default='pending')  # 'pending', 'approved', 'rejected', 'winner'
    vote_count = db.Column(Integer, default=0)
    admin_notes = db.Column(Text, nullable=True)
    winner_position = db.Column(Integer, nullable=True)  # 1st, 2nd, 3rd place
    
    # Timestamps
    submitted_at = db.Column(DateTime, default=datetime.utcnow)
    moderated_at = db.Column(DateTime, nullable=True)
    winner_announced_at = db.Column(DateTime, nullable=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'member_id': self.member_id,
            'member_name': self.member_name,
            'contest_month': self.contest_month,
            'category': self.category,
            'orchid_name': self.orchid_name,
            'description': self.description,
            'photo_url': self.photo_url,
            'status': self.status,
            'vote_count': self.vote_count,
            'winner_position': self.winner_position,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None
        }

class TrefleEnrichmentTracker(db.Model):
    """Track Trefle enrichment progress and status"""
    __tablename__ = 'trefle_enrichment_tracker'
    
    id = db.Column(Integer, primary_key=True)
    session_id = db.Column(String(50), nullable=False, index=True)
    session_name = db.Column(String(200), nullable=False)
    
    # Progress tracking
    total_records = db.Column(Integer, default=0)
    processed_records = db.Column(Integer, default=0)
    enriched_records = db.Column(Integer, default=0)
    failed_records = db.Column(Integer, default=0)
    skipped_records = db.Column(Integer, default=0)
    
    # Processing details
    current_batch_size = db.Column(Integer, default=50)
    priority_fcos_only = db.Column(Boolean, default=False)
    force_update_existing = db.Column(Boolean, default=False)
    
    # Status and timing
    status = db.Column(String(20), default='pending')  # pending, running, paused, completed, failed
    started_at = db.Column(DateTime, nullable=True)
    completed_at = db.Column(DateTime, nullable=True)
    last_api_call = db.Column(DateTime, nullable=True)
    
    # Rate limiting info
    api_calls_made = db.Column(Integer, default=0)
    rate_limit_hits = db.Column(Integer, default=0)
    estimated_completion = db.Column(DateTime, nullable=True)
    
    # Error tracking
    error_message = db.Column(Text, nullable=True)
    last_processed_id = db.Column(Integer, nullable=True)
    failed_orchid_ids = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'session_name': self.session_name,
            'total_records': self.total_records,
            'processed_records': self.processed_records,
            'enriched_records': self.enriched_records,
            'failed_records': self.failed_records,
            'skipped_records': self.skipped_records,
            'progress_percent': round((self.processed_records / self.total_records * 100) if self.total_records > 0 else 0, 2),
            'status': self.status,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'api_calls_made': self.api_calls_made,
            'rate_limit_hits': self.rate_limit_hits,
            'estimated_completion': self.estimated_completion.isoformat() if self.estimated_completion else None,
            'error_message': self.error_message
        }
    
    @staticmethod
    def get_current_contest_period():
        """Get current contest month in YYYY-MM format"""
        return datetime.now().strftime('%Y-%m')
    
    @classmethod
    def get_contest_entries(cls, contest_month=None, category=None, status=None):
        """Get contest entries with optional filters"""
        query = cls.query
        
        if contest_month:
            query = query.filter(cls.contest_month == contest_month)
        if category:
            query = query.filter(cls.category == category)
        if status:
            query = query.filter(cls.status == status)
            
        return query.order_by(cls.vote_count.desc(), cls.submitted_at.asc()).all()

class GameChatMessage(db.Model):
    """Chat messages in game rooms"""
    __tablename__ = 'game_chat_messages'
    
    id = db.Column(Integer, primary_key=True)
    game_id = db.Column(Integer, db.ForeignKey('mahjong_games.id'), nullable=False)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(Text, nullable=False)
    message_type = db.Column(String, default='chat')  # chat, system, emote
    timestamp = db.Column(DateTime, default=datetime.now)
    
    game = db.relationship('MahjongGame', backref='chat_messages')
    user = db.relationship('User', backref='chat_messages')

class Badge(db.Model):
    """Achievement badges for gamification"""
    __tablename__ = 'badges'
    
    id = db.Column(String, primary_key=True)
    name = db.Column(String, nullable=False)
    description = db.Column(Text, nullable=False)
    icon = db.Column(String, nullable=False)  # emoji or icon class
    tier = db.Column(String, nullable=False)  # bronze, silver, gold, platinum
    points_required = db.Column(Integer, default=0)
    category = db.Column(String, nullable=False)  # gaming, exploration, social, learning
    rarity = db.Column(String, default='common')  # common, rare, epic, legendary
    created_at = db.Column(DateTime, default=datetime.now)

class UserActivity(db.Model):
    """Track user activities for gamification"""
    __tablename__ = 'user_activities'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    activity_type = db.Column(String, nullable=False)  # page_visit, game_play, search, etc.
    points_earned = db.Column(Integer, default=0)
    details = db.Column(Text, nullable=True)  # JSON string with activity details
    timestamp = db.Column(DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='activities')

class GameScore(db.Model):
    """Game scores and completion records"""
    __tablename__ = 'game_scores'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    game_type = db.Column(String, nullable=False)  # memory, rebus, etc.
    difficulty = db.Column(String, nullable=True)  # easy, medium, hard
    score = db.Column(Integer, nullable=False)
    time_taken = db.Column(Integer, nullable=False)  # seconds
    moves_made = db.Column(Integer, nullable=False)
    game_metadata = db.Column(JSON, nullable=True)  # Additional game-specific data
    created_at = db.Column(DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='game_scores')

class UserBadge(db.Model):
    """User badge achievements"""
    __tablename__ = 'user_badges'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    badge_type = db.Column(String, nullable=False)  # memory_game, exploration, etc.
    badge_key = db.Column(String, nullable=False)  # specific badge identifier
    badge_data = db.Column(JSON, nullable=False)  # Badge name, description, icon, etc.
    earned_at = db.Column(DateTime, default=datetime.now)
    
    user = db.relationship('User', backref='badges')
    
    # Ensure unique badge per user
    __table_args__ = (db.UniqueConstraint('user_id', 'badge_type', 'badge_key'),)

class MovieReview(db.Model):
    """User reviews for Hollywood Orchids movies"""
    __tablename__ = 'movie_reviews'
    
    id = db.Column(Integer, primary_key=True)
    movie_key = db.Column(String(100), nullable=False)  # Key from HOLLYWOOD_ORCHIDS_MOVIES
    reviewer_name = db.Column(String(100), nullable=False)
    reviewer_email = db.Column(String(255), nullable=True)
    rating = db.Column(Integer, nullable=False)  # 1-5 stars
    orchid_symbolism_rating = db.Column(Integer, nullable=False)  # 1-5 stars for orchid usage
    review_text = db.Column(Text, nullable=False)
    favorite_orchid_scene = db.Column(Text, nullable=True)
    would_recommend = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.now)
    is_approved = db.Column(Boolean, default=True)  # For moderation
    
    def to_dict(self):
        return {
            'id': self.id,
            'movie_key': self.movie_key,
            'reviewer_name': self.reviewer_name,
            'rating': self.rating,
            'orchid_symbolism_rating': self.orchid_symbolism_rating,
            'review_text': self.review_text,
            'favorite_orchid_scene': self.favorite_orchid_scene,
            'would_recommend': self.would_recommend,
            'created_at': self.created_at.strftime('%B %d, %Y'),
            'is_approved': self.is_approved
        }

class MovieVote(db.Model):
    """Quick Phalaenopsis voting for Hollywood Orchids movies"""
    __tablename__ = 'movie_votes'
    
    id = db.Column(Integer, primary_key=True)
    movie_key = db.Column(String(100), nullable=False)
    phalaenopsis_rating = db.Column(Integer, nullable=False)  # 1-5 Phalaenopsis flowers
    voter_ip = db.Column(String(45), nullable=True)  # For basic duplicate prevention
    voted_at = db.Column(DateTime, default=datetime.now)
    
    # Simple index for faster queries
    __table_args__ = (db.Index('idx_movie_votes', 'movie_key', 'phalaenopsis_rating'),)

class OAuth(db.Model):
    """OAuth tokens for authentication - Compatible with Replit Auth"""
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'))
    browser_session_key = db.Column(String, nullable=False)
    provider = db.Column(String, nullable=False)
    token = db.Column(Text, nullable=True)
    user = db.relationship('User')
    
    # Unique constraint for Replit Auth compatibility
    __table_args__ = (db.UniqueConstraint(
        'user_id',
        'browser_session_key', 
        'provider',
        name='uq_user_browser_session_key_provider',
    ),)

# Orchid Database Models
class OrchidTaxonomy(db.Model):
    """Master taxonomy table for orchid classification"""
    id = db.Column(Integer, primary_key=True)
    scientific_name = db.Column(String(200), unique=True, nullable=False, index=True)
    genus = db.Column(String(100), nullable=False, index=True)
    species = db.Column(String(100), nullable=False)
    author = db.Column(String(200))
    synonyms = db.Column(Text)  # JSON string of alternative names
    common_names = db.Column(Text)  # JSON string of common names
    
    # External database references
    gbif_key = db.Column(Integer, nullable=True, index=True)  # GBIF taxonomic key
    gbif_canonical_name = db.Column(String(200), nullable=True)  # GBIF canonical name
    gbif_taxonomic_status = db.Column(String(50), nullable=True)  # GBIF taxonomic status
    gbif_last_updated = db.Column(DateTime, nullable=True)  # Last GBIF sync
    
    inaturalist_taxon_id = db.Column(Integer, nullable=True, index=True)  # iNaturalist taxon ID
    inaturalist_common_name = db.Column(String(200), nullable=True)  # iNaturalist preferred common name
    inaturalist_observations_count = db.Column(Integer, default=0)  # Number of iNaturalist observations
    inaturalist_last_updated = db.Column(DateTime, nullable=True)  # Last iNaturalist sync
    
    # External verification status
    external_verification_status = db.Column(String(50), default='pending')  # pending, verified, conflict, not_found
    external_data_sources = db.Column(JSON, nullable=True)  # Track which external sources have data
    external_synonyms = db.Column(JSON, nullable=True)  # External synonyms from GBIF/iNaturalist
    external_vernacular_names = db.Column(JSON, nullable=True)  # External common names
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to orchid records
    orchids = db.relationship('OrchidRecord', backref='taxonomy', lazy=True)

    def __repr__(self):
        return f'<OrchidTaxonomy {self.scientific_name}>'

class OrchidRecord(db.Model):
    """Main orchid record with metadata"""
    id = db.Column(Integer, primary_key=True)
    
    # User and source tracking
    user_id = db.Column(Integer, nullable=True)  # Fixed: Should be Integer, not String
    
    # Taxonomy relationship
    taxonomy_id = db.Column(Integer, db.ForeignKey('orchid_taxonomy.id'), nullable=True)
    
    # RHS and parentage information
    rhs_registration_id = db.Column(String(100), nullable=True)
    is_hybrid = db.Column(Boolean, default=False)
    is_species = db.Column(Boolean, default=False)
    grex_name = db.Column(String(200), nullable=True)
    clone_name = db.Column(String(200), nullable=True)
    pod_parent = db.Column(String(200), nullable=True)
    pollen_parent = db.Column(String(200), nullable=True)
    parentage_formula = db.Column(String(500), nullable=True)
    generation = db.Column(Integer, nullable=True)
    registration_date = db.Column(DateTime, nullable=True)
    registrant = db.Column(String(200), nullable=True)
    rhs_verification_status = db.Column(String(50), default='pending')  # verified, pending, not_found
    
    # Basic information
    display_name = db.Column(String(200), nullable=False)
    scientific_name = db.Column(String(200), index=True)
    common_names = db.Column(Text, nullable=True)  # Fixed: Use plural form that exists in DB
    genus = db.Column(String(100), index=True)
    species = db.Column(String(100))
    author = db.Column(String(200))
    # REMOVED: description, notes - don't exist in actual database
    
    # Geographic and habitat data
    region = db.Column(String(100))
    native_habitat = db.Column(Text)
    # REMOVED: location, discovery_date - don't exist in actual database
    decimal_latitude = db.Column(Float, nullable=True)
    decimal_longitude = db.Column(Float, nullable=True)
    country = db.Column(String(100), nullable=True)
    state_province = db.Column(String(100), nullable=True)
    locality = db.Column(String(200), nullable=True)
    collector = db.Column(String(200), nullable=True)
    collection_number = db.Column(String(100), nullable=True)
    event_date = db.Column(String(50), nullable=True)
    data_source = db.Column(String(100), nullable=True)
    
    # Growing characteristics
    bloom_time = db.Column(String(100))
    growth_habit = db.Column(String(50))  # epiphytic, terrestrial, lithophytic
    climate_preference = db.Column(String(20))  # cool, intermediate, warm
    leaf_form = db.Column(String(100))
    pseudobulb_presence = db.Column(Boolean)
    # REMOVED pollinator_types here - it exists as ARRAY type elsewhere in DB, not Text
    
    # Cultural information
    light_requirements = db.Column(String(50))
    temperature_range = db.Column(String(100))
    water_requirements = db.Column(Text)
    fertilizer_needs = db.Column(Text)
    cultural_notes = db.Column(Text)
    
    # Image and source metadata
    image_filename = db.Column(String(300))
    image_url = db.Column(String(500))
    # REMOVED: image_path - doesn't exist in actual database
    google_drive_id = db.Column(String(100))
    photographer = db.Column(String(200))
    image_source = db.Column(String(200))
    
    # AI and OCR data
    ocr_text = db.Column(Text)
    ai_description = db.Column(Text)
    ai_confidence = db.Column(Float)
    ai_extracted_metadata = db.Column(Text)  # JSON string
    
    # Enhanced flowering and observation metadata (from AI analysis)
    is_flowering = db.Column(Boolean, default=False)
    flowering_stage = db.Column(String(50))  # bud, early_bloom, peak_bloom, late_bloom, spent, not_flowering
    flower_count = db.Column(Integer, default=0)
    inflorescence_count = db.Column(Integer, default=0)
    flower_size_mm = db.Column(Float)
    flower_measurements = db.Column(JSON)  # {"length_mm": X, "width_mm": Y, "depth_mm": Z}
    bloom_season_indicator = db.Column(String(50))
    
    # Photo metadata (from EXIF)
    flowering_photo_date = db.Column(DateTime)  # Date photo was taken if flowering
    flowering_photo_datetime = db.Column(DateTime)  # Full datetime if available
    photo_gps_coordinates = db.Column(JSON)  # {"latitude": X, "longitude": Y, "altitude": Z}
    camera_info = db.Column(JSON)  # Camera make, model, software
    exif_data = db.Column(JSON)  # Full EXIF metadata
    
    # Enhanced habitat and environment analysis
    growing_environment = db.Column(String(100))  # wild_native, naturalized, cultivated_outdoor, etc.
    substrate_type = db.Column(String(50))  # tree_bark, rock, soil, moss, artificial_medium
    mounting_evidence = db.Column(Text)  # Evidence of growing on trees, rocks, or ground
    natural_vs_cultivated = db.Column(String(50))  # native_wild, naturalized_wild, cultivated
    
    # Environmental conditions observed
    light_conditions = db.Column(String(50))  # deep_shade, filtered_light, bright_indirect, direct_sun
    humidity_indicators = db.Column(String(50))  # Visual clues about humidity (high/medium/low)
    temperature_indicators = db.Column(String(50))  # Visual clues about temperature preference
    
    # Plant morphology details
    root_visibility = db.Column(Text)  # Description of visible roots (aerial, terrestrial)
    plant_maturity = db.Column(String(50))  # juvenile, mature, specimen_size
    
    # Location and context
    setting_type = db.Column(String(100))  # natural_forest, botanical_garden, home_collection, etc.
    companion_plants = db.Column(Text)  # Other plants visible that indicate habitat
    elevation_indicators = db.Column(Text)  # Visual clues about elevation
    conservation_status_clues = db.Column(Text)  # Any indicators of rarity or conservation concern
    
    # External database occurrence references
    gbif_occurrence_key = db.Column(String(50), nullable=True, index=True)  # GBIF occurrence key
    gbif_species_key = db.Column(Integer, nullable=True)  # GBIF species key
    gbif_dataset_key = db.Column(String(50), nullable=True)  # GBIF dataset key
    gbif_basis_of_record = db.Column(String(50), nullable=True)  # GBIF basis of record
    gbif_license = db.Column(String(100), nullable=True)  # GBIF data license
    gbif_occurrence_status = db.Column(String(50), nullable=True)  # GBIF occurrence status
    gbif_establishment_means = db.Column(String(50), nullable=True)  # GBIF establishment means
    gbif_last_updated = db.Column(DateTime, nullable=True)  # Last GBIF sync
    
    inaturalist_observation_id = db.Column(Integer, nullable=True, index=True)  # iNaturalist observation ID
    inaturalist_quality_grade = db.Column(String(20), nullable=True)  # research, needs_id, casual
    inaturalist_identifications_count = db.Column(Integer, default=0)  # Number of identifications
    inaturalist_license_code = db.Column(String(20), nullable=True)  # iNaturalist license code
    inaturalist_positional_accuracy = db.Column(Integer, nullable=True)  # GPS accuracy in meters
    inaturalist_last_updated = db.Column(DateTime, nullable=True)  # Last iNaturalist sync
    
    # Encyclopedia of Life (EOL) integration
    eol_page_id = db.Column(String(50), nullable=True, index=True)  # EOL page identifier
    eol_traits = db.Column(JSON, nullable=True)  # EOL trait data and descriptions
    eol_common_names = db.Column(JSON, nullable=True)  # EOL common names in various languages
    eol_synonyms = db.Column(JSON, nullable=True)  # EOL taxonomic synonyms
    eol_descriptions = db.Column(JSON, nullable=True)  # EOL species descriptions
    eol_images = db.Column(JSON, nullable=True)  # EOL image URLs and metadata
    eol_last_updated = db.Column(DateTime, nullable=True)  # Last EOL sync
    
    # External media references
    external_images = db.Column(JSON, nullable=True)  # External image URLs and metadata
    external_media_count = db.Column(Integer, default=0)  # Total external media count
    external_image_licenses = db.Column(JSON, nullable=True)  # License info for external images
    external_image_credits = db.Column(JSON, nullable=True)  # Attribution info for external images
    
    # Literature References and Scientific Citations
    literature_references = db.Column(JSON, nullable=True)  # Scientific publications, books, research papers
    cultivation_sources = db.Column(JSON, nullable=True)  # Growing guides, cultural information sources
    reference_citations = db.Column(JSON, nullable=True)  # Formal citations for academic references
    conservation_papers = db.Column(JSON, nullable=True)  # Research papers related to conservation
    taxonomic_publications = db.Column(JSON, nullable=True)  # Publications describing or revising taxonomy
    horticultural_articles = db.Column(JSON, nullable=True)  # Articles on cultivation and horticulture
    
    # Purchase and Nursery Integration
    nursery_recommendations = db.Column(JSON, nullable=True)  # Recommended nurseries that carry this orchid
    current_availability = db.Column(JSON, nullable=True)  # Current availability from various sources
    price_range = db.Column(String(100), nullable=True)  # Typical price range for this orchid
    purchase_links = db.Column(JSON, nullable=True)  # Direct purchase links from nurseries
    seed_suppliers = db.Column(JSON, nullable=True)  # Sources for seeds if available
    tissue_culture_sources = db.Column(JSON, nullable=True)  # Tissue culture/flask sources
    specialty_vendors = db.Column(JSON, nullable=True)  # Vendors specializing in this genus/type
    
    # Growing Resource Links
    care_guides = db.Column(JSON, nullable=True)  # Links to growing guides and care sheets
    video_resources = db.Column(JSON, nullable=True)  # Educational videos about this orchid
    forum_discussions = db.Column(JSON, nullable=True)  # Links to relevant forum discussions
    expert_advice = db.Column(JSON, nullable=True)  # Links to expert growing advice
    
    # Research and Academic Integration
    research_significance = db.Column(Text, nullable=True)  # Why this orchid is scientifically important
    conservation_status_details = db.Column(JSON, nullable=True)  # Detailed conservation information
    habitat_research = db.Column(JSON, nullable=True)  # Research on natural habitat and ecology
    pollination_studies = db.Column(JSON, nullable=True)  # Studies on pollination biology
    breeding_research = db.Column(JSON, nullable=True)  # Research on breeding and genetics
    
    # Commercial and Availability Metadata
    commercial_importance = db.Column(String(50), nullable=True)  # high, medium, low, rare, unavailable
    propagation_difficulty = db.Column(String(50), nullable=True)  # easy, moderate, difficult, expert_only
    market_demand = db.Column(String(50), nullable=True)  # high, medium, low, niche, collector_only
    seasonal_availability = db.Column(JSON, nullable=True)  # When this orchid is typically available
    import_restrictions = db.Column(JSON, nullable=True)  # CITES or other import/export restrictions
    
    # Society and Community Integration
    society_highlights = db.Column(JSON, nullable=True)  # Orchid societies that feature this orchid
    show_awards = db.Column(JSON, nullable=True)  # Awards this orchid has won at shows
    notable_growers = db.Column(JSON, nullable=True)  # Famous growers known for this orchid
    community_notes = db.Column(JSON, nullable=True)  # Community observations and notes
    
    # System metadata
    ingestion_source = db.Column(String(50))  # 'upload', 'scrape_gary', 'scrape_roberta', 'legacy', 'gbif', 'inaturalist'
    validation_status = db.Column(String(20), default='pending')  # pending, validated, rejected
    is_featured = db.Column(Boolean, default=False)
    view_count = db.Column(Integer, default=0)
    external_data_sources = db.Column(JSON, nullable=True)  # Track which external sources have data
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Community identification system
    identification_status = db.Column(String(20), default='verified', nullable=True)  # verified, unidentified, pending
    identification_votes = db.Column(Integer, default=0, nullable=True)  # Number of community votes
    suggested_genus = db.Column(String(100), nullable=True)  # Community suggested genus
    suggested_species = db.Column(String(100), nullable=True)  # Community suggested species

    def get_parentage_display(self):
        """Get formatted parentage display"""
        if self.pod_parent and self.pollen_parent:
            return f"{self.pod_parent} × {self.pollen_parent}"
        elif self.parentage_formula:
            return self.parentage_formula
        return None
    
    def get_full_name(self):
        """Get full orchid name including clone if present"""
        base_name = self.scientific_name or self.display_name
        if self.clone_name:
            return f"{base_name} '{self.clone_name}'"
        return base_name
    
    def is_registered_hybrid(self):
        """Check if this is a registered hybrid"""
        return bool(self.rhs_registration_id or (self.pod_parent and self.pollen_parent))
    
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
    plant_id = db.Column(String(20), unique=True, nullable=False)  # Plant ID number
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    user_id = db.Column(String, nullable=True)  # Temporarily remove FK constraint
    batch_id = db.Column(Integer, db.ForeignKey('batch_upload.id'), nullable=True)
    
    # File information
    original_filename = db.Column(String(300), nullable=False)
    uploaded_filename = db.Column(String(300), nullable=False)
    file_size = db.Column(Integer)
    mime_type = db.Column(String(100))
    
    # Parsed information from filename
    parsed_genus = db.Column(String(100))
    parsed_species = db.Column(String(100))
    parsed_variety = db.Column(String(100))
    filename_confidence = db.Column(Float)  # Confidence in filename parsing
    
    # User data
    user_notes = db.Column(Text)
    location = db.Column(String(200))
    growing_conditions = db.Column(Text)
    
    # Processing status
    processing_status = db.Column(String(20), default='pending')  # pending, processing, completed, failed
    error_message = db.Column(Text)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    processed_at = db.Column(DateTime)
    
    def __init__(self, **kwargs):
        super(UserUpload, self).__init__(**kwargs)
        if not self.plant_id:
            self.plant_id = self.generate_plant_id()
    
    def generate_plant_id(self):
        """Generate unique plant ID"""
        while True:
            plant_id = 'P' + secrets.token_hex(4).upper()  # P + 8 chars
            if not UserUpload.query.filter_by(plant_id=plant_id).first():
                return plant_id
    
    def __repr__(self):
        return f'<UserUpload {self.plant_id}: {self.original_filename}>'

class WidgetConfig(db.Model):
    """Configuration for various widgets"""
    id = db.Column(Integer, primary_key=True)
    widget_name = db.Column(String(50), unique=True, nullable=False)
    config_data = db.Column(Text)  # JSON string with widget configuration
    is_active = db.Column(Boolean, default=True)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(UserMixin, db.Model):
    """Enhanced user management system with gamification and breeding labs"""
    __tablename__ = 'users'
    id = db.Column(String, primary_key=True)  # String ID for compatibility
    user_id = db.Column(String(20), unique=True, nullable=True)  # Distinctive user ID
    email = db.Column(String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(String(256))
    is_admin = db.Column(Boolean, default=False)
    
    # OrchidStein Lab settings
    lab_name = db.Column(String(200), default='My OrchidStein Lab')
    lab_established_date = db.Column(DateTime, default=datetime.utcnow)
    breeding_specialization = db.Column(String(100))  # e.g., 'Phalaenopsis', 'Cattleya'
    research_interests = db.Column(Text)  # JSON string of research areas
    
    # User profile
    first_name = db.Column(String(100))
    last_name = db.Column(String(100))
    profile_image_url = db.Column(String(500), nullable=True)
    organization = db.Column(String(200))
    country = db.Column(String(100))
    orchid_interests = db.Column(Text, nullable=True)  # User's orchid interests/specialties
    experience_level = db.Column(String(50), default='beginner')  # beginner, intermediate, expert
    bio = db.Column(Text, nullable=True)  # User bio
    
    # Statistics
    upload_count = db.Column(Integer, default=0)
    last_login = db.Column(DateTime)
    
    # Account status
    account_active = db.Column(Boolean, default=True)
    email_verified = db.Column(Boolean, default=False)
    
    # Gamification fields
    total_points = db.Column(Integer, default=0)
    website_visits = db.Column(Integer, default=0)
    last_visit = db.Column(DateTime, default=datetime.utcnow)
    current_badge_tier = db.Column(String, default='Seedling')
    badges_earned = db.Column(Text, default='[]')  # JSON string of badge IDs
    
    # Mahjong game stats
    mahjong_games_played = db.Column(Integer, default=0)
    mahjong_games_won = db.Column(Integer, default=0)
    mahjong_best_time = db.Column(Integer, default=0)  # seconds
    mahjong_total_score = db.Column(Integer, default=0)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Note: Relationships temporarily removed to fix foreign key conflicts
    
    def get_display_name(self):
        """Return first name + last initial for leaderboards"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name[0]}."
        elif self.first_name:
            return self.first_name
        else:
            return "Anonymous Player"
    
    def get_badges(self):
        """Get list of earned badges"""
        try:
            return json.loads(self.badges_earned or '[]')
        except:
            return []
    
    def add_badge(self, badge_id):
        """Add a new badge to user's collection"""
        badges = self.get_badges()
        if badge_id not in badges:
            badges.append(badge_id)
            self.badges_earned = json.dumps(badges)
            db.session.commit()
    
    def add_points(self, points, activity_type='general'):
        """Add points and check for badge upgrades"""
        self.total_points += points
        
        # Update badge tier based on total points
        new_tier = self._calculate_badge_tier(self.total_points)
        if new_tier != self.current_badge_tier:
            self.current_badge_tier = new_tier
            self.add_badge(f"tier_{new_tier.lower().replace(' ', '_')}")
        
        # Activity-specific badges
        if activity_type == 'mahjong_win':
            self.mahjong_games_won += 1
            if self.mahjong_games_won == 1:
                self.add_badge('first_mahjong_win')
            elif self.mahjong_games_won == 10:
                self.add_badge('mahjong_apprentice')
            elif self.mahjong_games_won == 50:
                self.add_badge('mahjong_master')
        
        db.session.commit()
    
    def _calculate_badge_tier(self, points):
        """Calculate badge tier based on total points"""
        if points >= 10000:
            return 'Orchid Master'
        elif points >= 5000:
            return 'Expert Grower'
        elif points >= 2000:
            return 'Experienced Cultivator'
        elif points >= 1000:
            return 'Orchid Enthusiast'
        elif points >= 500:
            return 'Growing Hobbyist'
        elif points >= 100:
            return 'Budding Gardener'
        else:
            return 'Seedling'
    # Relationships restored with correct foreign keys
    judgings = db.relationship('JudgingAnalysis', backref='user', lazy=True)
    certificates = db.relationship('Certificate', backref='user', lazy=True)
    locations = db.relationship('UserLocation', backref='user', lazy=True)
    collections = db.relationship('UserOrchidCollection', backref='user', lazy=True)
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.user_id:
            self.user_id = self.generate_user_id()
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def generate_user_id(self):
        """Generate a unique user ID"""
        while True:
            user_id = 'OU' + secrets.token_hex(4).upper()  # Orchid User + 8 chars
            if not User.query.filter_by(user_id=user_id).first():
                return user_id
    
    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.email
    
    def __repr__(self):
        return f'<User {self.user_id}: {self.email}>'


class PasswordResetToken(db.Model):
    """Password reset tokens for secure account recovery"""
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(String(100), unique=True, nullable=False)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    expires_at = db.Column(DateTime, nullable=False)
    used = db.Column(Boolean, default=False)
    
    # Relationship
    user = db.relationship('User', backref=db.backref('password_reset_tokens', lazy=True))
    
    def __init__(self, user_id, expires_in_hours=24):
        self.user_id = user_id
        self.token = secrets.token_urlsafe(32)
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
    
    def is_expired(self):
        return datetime.utcnow() > self.expires_at
    
    def is_valid(self):
        return not self.used and not self.is_expired()
    
    def mark_as_used(self):
        self.used = True
    
    @staticmethod
    def cleanup_expired_tokens():
        """Remove expired tokens from database"""
        now = datetime.utcnow()
        expired = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < now
        ).all()
        
        for token in expired:
            db.session.delete(token)
        
        return len(expired)
    
    def __repr__(self):
        return f'<PasswordResetToken for User {self.user_id}>'

# OrchidStein Lab Breeding Models
class BreedingProject(db.Model):
    """Individual breeding projects within user's OrchidStein lab"""
    __tablename__ = 'breeding_projects'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    project_name = db.Column(String(200), nullable=False)
    project_code = db.Column(String(20), unique=True, nullable=False)  # e.g., "PH-2025-001"
    
    # Project goals and traits
    target_traits = db.Column(Text)  # JSON string of desired traits
    success_criteria = db.Column(Text)  # JSON string of success metrics
    expected_generations = db.Column(Integer, default=3)
    
    # Status
    status = db.Column(String(50), default='planning')  # planning, active, paused, completed, abandoned
    progress_percentage = db.Column(Integer, default=0)
    
    # Statistics
    total_crosses_made = db.Column(Integer, default=0)
    total_seedlings_produced = db.Column(Integer, default=0)
    successful_traits_achieved = db.Column(Integer, default=0)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='breeding_projects')

class LabCollection(db.Model):
    """User's personal orchid collection in their OrchidStein lab"""
    __tablename__ = 'lab_collections'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    
    # Lab-specific data
    lab_accession_number = db.Column(String(50), unique=True)  # User's internal tracking number
    acquisition_date = db.Column(DateTime)
    acquisition_source = db.Column(String(200))  # vendor, trade, division, etc.
    location_in_collection = db.Column(String(100))  # bench position, greenhouse section
    
    # Breeding status
    is_breeding_stock = db.Column(Boolean, default=False)
    breeding_value_score = db.Column(Float)  # calculated breeding value
    proven_traits = db.Column(Text)  # JSON string of confirmed traits
    
    # Health and performance tracking
    health_status = db.Column(String(50), default='healthy')
    flowering_frequency = db.Column(String(50))  # annual, biannual, irregular
    last_flowering_date = db.Column(DateTime)
    award_potential = db.Column(String(50))  # high, medium, low, unknown
    
    notes = db.Column(Text)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='lab_collection')
    orchid = db.relationship('OrchidRecord', backref='in_lab_collections')

class BreedingCross(db.Model):
    """Individual breeding crosses with detailed tracking"""
    __tablename__ = 'breeding_crosses'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(Integer, db.ForeignKey('breeding_projects.id'), nullable=True)
    
    # Cross identification
    cross_code = db.Column(String(50), unique=True, nullable=False)  # e.g., "PH001 x PH002"
    cross_name = db.Column(String(200))  # Optional grex name
    
    # Parents
    pod_parent_id = db.Column(Integer, db.ForeignKey('lab_collections.id'), nullable=False)
    pollen_parent_id = db.Column(Integer, db.ForeignKey('lab_collections.id'), nullable=False)
    
    # Pollination details
    pollination_date = db.Column(DateTime, nullable=False)
    pollination_method = db.Column(String(100))  # hand pollination, assisted, etc.
    
    # Predicted outcomes using AI
    predicted_traits = db.Column(Text)  # JSON string of predicted offspring traits
    success_probability = db.Column(Float)  # 0.0 to 1.0 success likelihood
    ai_analysis = db.Column(Text)  # Detailed AI analysis and recommendations
    
    # Actual results
    pod_set_date = db.Column(DateTime)
    pod_harvest_date = db.Column(DateTime)
    seeds_count = db.Column(Integer)
    germination_percentage = db.Column(Float)
    
    # Progress tracking
    current_stage = db.Column(String(50), default='pollinated')  # pollinated, pod_set, harvested, flasked, deflasked, first_bloom
    stage_progression = db.Column(Text)  # JSON array of stage dates
    
    notes = db.Column(Text)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='breeding_crosses')

class OffspringPlant(db.Model):
    """Individual offspring plants from breeding crosses"""
    __tablename__ = 'offspring_plants'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    cross_id = db.Column(Integer, db.ForeignKey('breeding_crosses.id'), nullable=False)
    
    # Plant identification
    plant_code = db.Column(String(50), nullable=False)  # e.g., "PH001xPH002-001"
    
    # Development tracking
    germination_date = db.Column(DateTime)
    deflasking_date = db.Column(DateTime)
    first_flowering_date = db.Column(DateTime)
    
    # Trait analysis
    observed_traits = db.Column(Text)  # JSON string of measured/observed traits
    trait_scores = db.Column(Text)  # JSON string of quantified trait measurements
    breeding_value = db.Column(Float)  # calculated breeding value
    
    # Performance metrics
    survival_stage = db.Column(String(50), default='germinated')  # germinated, juvenile, mature, flowering, deceased
    health_score = db.Column(Float)  # 0.0 to 10.0 health rating
    award_potential = db.Column(String(50))  # exceptional, high, medium, low
    
    # Selection decisions
    selected_for_breeding = db.Column(Boolean, default=False)
    selection_reasons = db.Column(Text)
    
    notes = db.Column(Text)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='offspring_plants')
    cross = db.relationship('BreedingCross', backref='offspring_plants')

class TraitAnalysis(db.Model):
    """Statistical analysis of trait inheritance patterns"""
    __tablename__ = 'trait_analyses'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    cross_id = db.Column(Integer, db.ForeignKey('breeding_crosses.id'), nullable=False)
    
    # Analysis metadata
    analysis_date = db.Column(DateTime, default=datetime.utcnow)
    sample_size = db.Column(Integer, nullable=False)  # number of offspring analyzed
    
    # Statistical results
    trait_segregation_ratios = db.Column(Text)  # JSON string of observed ratios
    expected_vs_observed = db.Column(Text)  # JSON comparison of expected vs actual
    statistical_significance = db.Column(Text)  # JSON of chi-square or other tests
    heritability_estimates = db.Column(Text)  # JSON of calculated heritability values
    
    # Success metrics
    breeding_success_rate = db.Column(Float)  # percentage of goals achieved
    unexpected_outcomes = db.Column(Text)  # JSON of surprising results
    
    # AI insights
    ai_interpretation = db.Column(Text)  # AI analysis of the statistical patterns
    breeding_recommendations = db.Column(Text)  # AI suggestions for future crosses
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='trait_analyses')
    cross = db.relationship('BreedingCross', backref='analyses')

class JudgingStandard(db.Model):
    """Orchid judging standards from different organizations"""
    id = db.Column(Integer, primary_key=True)
    organization = db.Column(String(50), nullable=False)  # AOS, EU, AU, NZ, JP, TH
    standard_name = db.Column(String(100), nullable=False)
    category = db.Column(String(50), nullable=False)  # flower, plant, cultural
    criteria_name = db.Column(String(100), nullable=False)
    description = db.Column(Text)
    max_points = db.Column(Integer, nullable=False)
    weight_factor = db.Column(Float, default=1.0)
    
    # Detailed scoring guidance
    scoring_guide = db.Column(Text)  # JSON with detailed scoring criteria
    examples = db.Column(Text)  # JSON with example descriptions
    
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<JudgingStandard {self.organization}: {self.criteria_name}>'

class JudgingAnalysis(db.Model):
    """AI analysis of orchids against judging standards"""
    id = db.Column(Integer, primary_key=True)
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    judging_standard_id = db.Column(Integer, db.ForeignKey('judging_standard.id'), nullable=False)
    
    # Analysis results
    score = db.Column(Float)  # Score out of max_points
    percentage = db.Column(Float)  # Percentage score
    ai_comments = db.Column(Text)  # AI analysis comments
    detailed_analysis = db.Column(Text)  # JSON with detailed breakdown
    
    # Awards and recognition
    is_award_worthy = db.Column(Boolean, default=False)
    suggested_award_level = db.Column(String(50))  # HCC, AM, FCC, etc.
    award_justification = db.Column(Text)
    
    # Analysis metadata
    analysis_date = db.Column(DateTime, default=datetime.utcnow)
    created_at = db.Column(DateTime, default=datetime.utcnow)  # Added for routes.py compatibility
    ai_model_used = db.Column(String(50))
    confidence_level = db.Column(Float)
    
    # Relationships
    orchid = db.relationship('OrchidRecord', backref='judging_analyses')
    judging_standard = db.relationship('JudgingStandard')
    
    def __repr__(self):
        return f'<JudgingAnalysis {self.orchid_id}: {self.score}>'

class Certificate(db.Model):
    """Award certificates for orchids"""
    id = db.Column(Integer, primary_key=True)
    certificate_number = db.Column(String(50), unique=True, nullable=False)
    
    # Relationships
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    judging_analysis_id = db.Column(Integer, db.ForeignKey('judging_analysis.id'), nullable=True)
    
    # Certificate details
    award_level = db.Column(String(50), nullable=False)  # HCC, AM, FCC, etc.
    award_title = db.Column(String(200), nullable=False)
    total_score = db.Column(Float)
    judging_organization = db.Column(String(50))  # AOS, EU, etc.
    
    # Certificate content
    citation_text = db.Column(Text)
    technical_notes = db.Column(Text)
    judge_comments = db.Column(Text)
    
    # File information
    pdf_filename = db.Column(String(300))
    is_generated = db.Column(Boolean, default=False)
    
    # Timestamps
    issued_date = db.Column(DateTime, default=datetime.utcnow)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    orchid = db.relationship('OrchidRecord', backref='certificates')
    judging_analysis = db.relationship('JudgingAnalysis')
    
    def __init__(self, **kwargs):
        super(Certificate, self).__init__(**kwargs)
        if not self.certificate_number:
            self.certificate_number = self.generate_certificate_number()
    
    def generate_certificate_number(self):
        """Generate unique certificate number"""
        while True:
            # Format: OC-YYYY-XXXXX (Orchid Continuum - Year - 5 digit number)
            year = datetime.utcnow().year
            number = secrets.randbelow(99999) + 1
            cert_num = f"OC-{year}-{number:05d}"
            if not Certificate.query.filter_by(certificate_number=cert_num).first():
                return cert_num
    
    def __repr__(self):
        return f'<Certificate {self.certificate_number}>'

class BatchUpload(db.Model):
    """Track batch upload sessions"""
    id = db.Column(Integer, primary_key=True)
    batch_id = db.Column(String(50), unique=True, nullable=False)
    
    # User and session info
    user_id = db.Column(String, nullable=True)  # Remove FK constraint
    session_id = db.Column(String(100))
    
    # Batch statistics
    total_files = db.Column(Integer, default=0)
    processed_files = db.Column(Integer, default=0)
    successful_files = db.Column(Integer, default=0)
    failed_files = db.Column(Integer, default=0)
    
    # Processing status
    status = db.Column(String(20), default='pending')  # pending, processing, completed, failed
    processing_log = db.Column(Text)  # JSON log of processing steps
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    completed_at = db.Column(DateTime)
    
    # Relationships
    uploads = db.relationship('UserUpload', backref='batch', lazy=True)
    
    def __init__(self, **kwargs):
        super(BatchUpload, self).__init__(**kwargs)
        if not self.batch_id:
            self.batch_id = self.generate_batch_id()
    
    def generate_batch_id(self):
        """Generate unique batch ID"""
        while True:
            batch_id = 'B' + secrets.token_hex(6).upper()
            if not BatchUpload.query.filter_by(batch_id=batch_id).first():
                return batch_id
    
    def __repr__(self):
        return f'<BatchUpload {self.batch_id}: {self.total_files} files>'

class WeatherData(db.Model):
    """Weather data for orchid growing correlation analysis"""
    __tablename__ = 'weather_data'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Location information
    location_name = db.Column(db.String(200))  # City, State/Province, Country
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    
    # Weather measurements
    temperature = db.Column(db.Float)  # Celsius
    temperature_min = db.Column(db.Float)  # Daily minimum
    temperature_max = db.Column(db.Float)  # Daily maximum
    humidity = db.Column(db.Float)  # Percentage
    precipitation = db.Column(db.Float)  # mm
    wind_speed = db.Column(db.Float)  # km/h
    wind_direction = db.Column(db.Float)  # degrees
    pressure = db.Column(db.Float)  # hPa
    cloud_cover = db.Column(db.Float)  # Percentage
    uv_index = db.Column(db.Float)
    
    # Calculated metrics for orchids
    vpd = db.Column(db.Float)  # Vapor Pressure Deficit
    heat_index = db.Column(db.Float)
    growing_degree_days = db.Column(db.Float)
    
    # Weather description
    weather_code = db.Column(db.Integer)  # WMO weather code
    description = db.Column(db.String(100))
    
    # Data metadata
    recorded_at = db.Column(db.DateTime, nullable=False)  # When weather occurred
    data_source = db.Column(db.String(50), default='open-meteo')
    is_forecast = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def get_weather_description(self):
        """Convert WMO weather code to description"""
        weather_codes = {
            0: 'Clear sky',
            1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast',
            45: 'Fog', 48: 'Depositing rime fog',
            51: 'Light drizzle', 53: 'Moderate drizzle', 55: 'Dense drizzle',
            56: 'Light freezing drizzle', 57: 'Dense freezing drizzle',
            61: 'Slight rain', 63: 'Moderate rain', 65: 'Heavy rain',
            66: 'Light freezing rain', 67: 'Heavy freezing rain',
            71: 'Slight snow', 73: 'Moderate snow', 75: 'Heavy snow',
            77: 'Snow grains',
            80: 'Slight rain showers', 81: 'Moderate rain showers', 82: 'Violent rain showers',
            85: 'Slight snow showers', 86: 'Heavy snow showers',
            95: 'Thunderstorm', 96: 'Thunderstorm with slight hail', 99: 'Thunderstorm with heavy hail'
        }
        return weather_codes.get(self.weather_code, 'Unknown')
    
    def calculate_vpd(self):
        """Calculate Vapor Pressure Deficit - important for orchid health"""
        if self.temperature is not None and self.humidity is not None:
            # Saturated vapor pressure (kPa)
            svp = 0.6108 * (2.71828 ** (17.27 * self.temperature / (self.temperature + 237.3)))
            # Actual vapor pressure
            avp = svp * (self.humidity / 100)
            # VPD
            self.vpd = svp - avp
            return self.vpd
        return None
    
    def is_orchid_friendly(self):
        """Assess if conditions are good for orchids"""
        conditions = {
            'temperature_ok': 15 <= (self.temperature or 0) <= 30,
            'humidity_ok': (self.humidity or 0) >= 50,
            'low_wind': (self.wind_speed or 0) < 30,
            'no_extreme_weather': self.weather_code not in [61, 63, 65, 95, 96, 99] if self.weather_code else True
        }
        return all(conditions.values())
    
    def __repr__(self):
        return f'<WeatherData {self.location_name} at {self.recorded_at}>'

class UserLocation(db.Model):
    """User locations for weather tracking"""
    __tablename__ = 'user_locations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    
    # Location details
    name = db.Column(db.String(200), nullable=False)  # User-friendly name
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    city = db.Column(db.String(100))
    state_province = db.Column(db.String(100))
    country = db.Column(db.String(100))
    zip_code = db.Column(db.String(20))  # ZIP/postal code for location
    timezone = db.Column(db.String(50))
    
    # Growing environment details
    growing_type = db.Column(db.String(50))  # greenhouse, indoor, outdoor, shade_house
    microclimate_notes = db.Column(db.Text)
    
    # Settings
    is_primary = db.Column(db.Boolean, default=False)
    track_weather = db.Column(db.Boolean, default=True)
    alert_preferences = db.Column(db.Text)  # JSON with alert settings
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserLocation {self.name}>'

class WeatherAlert(db.Model):
    """Weather alerts for orchid care"""
    __tablename__ = 'weather_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    location_id = db.Column(db.Integer, db.ForeignKey('user_locations.id'), nullable=False)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # temperature, humidity, frost, storm, etc.
    severity = db.Column(db.String(20))  # low, medium, high, critical
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Alert triggers
    trigger_conditions = db.Column(db.Text)  # JSON with trigger conditions
    orchid_care_advice = db.Column(db.Text)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_acknowledged = db.Column(db.Boolean, default=False)
    acknowledged_at = db.Column(db.DateTime)
    
    # Timestamps
    triggered_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    # Relationships
    location = db.relationship('UserLocation', backref='weather_alerts')
    
    def __repr__(self):
        return f'<WeatherAlert {self.alert_type}: {self.title}>'

class UserFeedback(db.Model):
    __tablename__ = 'user_feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    feedback_type = db.Column(db.String(50), nullable=False)  # 'bug_report', 'feature_request', 'general_feedback'
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    page_url = db.Column(db.String(500))  # URL where feedback was submitted from
    browser_info = db.Column(db.String(500))  # User agent string
    status = db.Column(db.String(20), default='new')  # 'new', 'reviewed', 'resolved', 'closed'
    admin_notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<UserFeedback {self.id}: {self.feedback_type} - {self.subject}>'

class UserOrchidCollection(db.Model):
    """User's personal orchid collection for weather widget"""
    __tablename__ = 'user_orchid_collections'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=False)
    orchid_id = db.Column(db.Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    
    # Collection details
    collection_name = db.Column(db.String(100))  # User's name for this orchid
    acquisition_date = db.Column(db.Date)
    source = db.Column(db.String(200))  # Where they got it
    notes = db.Column(db.Text)  # User's growing notes
    
    # Growing status
    is_active = db.Column(db.Boolean, default=True)  # Still growing it
    is_primary = db.Column(db.Boolean, default=False)  # Featured in widget
    flowering_history = db.Column(db.Text)  # JSON of flowering dates
    
    # Widget preferences
    show_in_widget = db.Column(db.Boolean, default=True)
    widget_priority = db.Column(db.Integer, default=1)  # 1=highest priority
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orchid = db.relationship('OrchidRecord', backref='user_collections')
    
    def __repr__(self):
        return f'<UserOrchidCollection {self.user_id}: {self.orchid_id}>'

class DiscoveryAlert(db.Model):
    """AI discovery alerts and notifications (legacy from Professor BloomBot)"""
    __tablename__ = 'discovery_alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Alert details
    alert_type = db.Column(db.String(50), nullable=False)  # research_breakthrough, geographic_insight, etc.
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    importance = db.Column(db.Float, nullable=False)  # 0.0 to 1.0
    
    # Action details
    action_url = db.Column(db.String(500))
    action_text = db.Column(db.String(100))
    
    # Display details
    icon = db.Column(db.String(50))  # Feather icon name
    category = db.Column(db.String(50))  # research, geography, genetics, etc.
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    is_featured = db.Column(db.Boolean, default=False)
    dismissed_by_admin = db.Column(db.Boolean, default=False)
    
    # Metadata
    discovery_data = db.Column(db.Text)  # JSON with additional data
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_discovery_data(self):
        """Get parsed discovery data"""
        if self.discovery_data:
            try:
                import json
                return json.loads(self.discovery_data)
            except:
                return {}
        return {}
    
    def set_discovery_data(self, data):
        """Set discovery data as JSON"""
        import json
        self.discovery_data = json.dumps(data)
    
    def __repr__(self):
        return f'<DiscoveryAlert {self.alert_type}: {self.title}>'


# Admin Approval System for Orchid Validation
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
    
    id = db.Column(Integer, primary_key=True)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    special_display_id = db.Column(String(20), unique=True, nullable=False)  # FCOS-001, FCOS-002, etc.
    
    # Gallery assignments
    gallery_type = db.Column(Enum(GalleryType), nullable=False)
    status = db.Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    
    # Orchid of the Day scheduling
    scheduled_date = db.Column(db.Date, nullable=True)  # When this orchid should be featured
    priority_order = db.Column(Integer, default=1)  # Display priority within gallery
    
    # Admin metadata approval
    approved_genus = db.Column(String(100), nullable=False)
    approved_species = db.Column(String(100), nullable=False)
    approved_common_name = db.Column(String(200), nullable=True)
    approved_country = db.Column(String(100), nullable=True)
    approved_description = db.Column(Text, nullable=True)
    
    # Validation flags
    taxonomy_verified = db.Column(Boolean, default=False)
    image_quality_approved = db.Column(Boolean, default=False)
    metadata_complete = db.Column(Boolean, default=False)
    
    # Admin info
    approved_by = db.Column(String(200), nullable=True)
    approved_at = db.Column(DateTime, nullable=True)
    rejection_reason = db.Column(Text, nullable=True)
    
    # Display customization
    custom_title = db.Column(String(300), nullable=True)
    custom_description = db.Column(Text, nullable=True)
    featured_highlights = db.Column(JSON, nullable=True)  # Special features to highlight
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    orchid = db.relationship('OrchidRecord', backref='approvals')
    
    def __repr__(self):
        return f'<OrchidApproval {self.special_display_id}: {self.approved_genus} {self.approved_species}>'


class OrchidTaxonomyValidation(db.Model):
    """Validated orchid taxonomy for admin reference"""
    __tablename__ = 'orchid_taxonomy_validation'
    
    id = db.Column(Integer, primary_key=True)
    genus = db.Column(String(100), nullable=False, index=True)
    species = db.Column(String(100), nullable=True, index=True)
    family = db.Column(String(100), default="Orchidaceae")
    subfamily = db.Column(String(100), nullable=True)
    tribe = db.Column(String(100), nullable=True)
    
    # Validation info
    is_accepted = db.Column(Boolean, default=True)
    authority = db.Column(String(300), nullable=True)
    synonyms = db.Column(JSON, nullable=True)
    common_names = db.Column(JSON, nullable=True)
    
    # Distribution
    native_regions = db.Column(JSON, nullable=True)
    cultivation_notes = db.Column(Text, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('genus', 'species', name='unique_genus_species'),)
    
    def __repr__(self):
        return f'<ValidTaxonomy {self.genus} {self.species or "sp."}>'


class GalleryConfiguration(db.Model):
    """Configuration for different gallery displays"""
    __tablename__ = 'gallery_configurations'
    
    id = db.Column(Integer, primary_key=True)
    gallery_name = db.Column(String(100), unique=True, nullable=False)
    gallery_type = db.Column(Enum(GalleryType), nullable=False)
    display_title = db.Column(String(200), nullable=False)
    description = db.Column(Text, nullable=True)
    
    # Display settings
    max_items = db.Column(Integer, default=12)
    auto_refresh_hours = db.Column(Integer, default=24)  # How often to refresh content
    show_metadata_fields = db.Column(JSON, nullable=True)  # Which fields to show
    
    # Approval requirements
    require_admin_approval = db.Column(Boolean, default=True)
    require_taxonomy_verification = db.Column(Boolean, default=True)
    require_image_quality_check = db.Column(Boolean, default=True)
    
    is_active = db.Column(Boolean, default=True)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Gallery {self.gallery_name}>'

# ==============================================================================
# MEMBER FEEDBACK AND BETA TESTING SYSTEM
# ==============================================================================

class MemberFeedback(db.Model):
    """Member feedback for beta testing and data accuracy verification"""
    __tablename__ = 'member_feedback'
    
    id = db.Column(Integer, primary_key=True)
    member_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    
    # Feedback details
    feedback_type = db.Column(String, nullable=False)  # 'photo_mismatch', 'data_error', 'widget_bug', 'general'
    severity = db.Column(String, default='medium')  # 'low', 'medium', 'high', 'critical'
    description = db.Column(Text, nullable=False)
    suggested_correction = db.Column(Text, nullable=True)
    
    # System context
    page_url = db.Column(String, nullable=True)
    widget_type = db.Column(String, nullable=True)  # 'featured', 'gallery', 'discovery', 'orchid_of_day'
    browser_info = db.Column(Text, nullable=True)
    screenshot_url = db.Column(String, nullable=True)
    
    # Resolution tracking
    status = db.Column(String, default='open')  # 'open', 'in_progress', 'resolved', 'closed'
    assigned_to = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    resolution_notes = db.Column(Text, nullable=True)
    ai_attempted_fix = db.Column(Boolean, default=False)
    ai_fix_details = db.Column(Text, nullable=True)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.now)
    resolved_at = db.Column(DateTime, nullable=True)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)

class PhotoFlag(db.Model):
    """Photo flagging system for immediate issue reporting"""
    __tablename__ = 'photo_flags'
    
    id = db.Column(Integer, primary_key=True)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    flagger_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    
    # Flag details
    flag_reason = db.Column(String, nullable=False)  # 'wrong_species', 'mislabeled', 'poor_quality', 'duplicate', 'inappropriate'
    confidence_level = db.Column(String, default='medium')  # 'low', 'medium', 'high'
    expert_notes = db.Column(Text, nullable=True)
    
    # Auto-resolution tracking
    ai_reviewed = db.Column(Boolean, default=False)
    ai_confidence = db.Column(Float, nullable=True)  # 0.0 to 1.0
    ai_suggested_species = db.Column(String, nullable=True)
    ai_analysis_notes = db.Column(Text, nullable=True)
    
    # Status
    status = db.Column(String, default='pending')  # 'pending', 'validated', 'rejected', 'fixed'
    verified_by = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    verification_notes = db.Column(Text, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.now)
    resolved_at = db.Column(DateTime, nullable=True)

class WidgetStatus(db.Model):
    """Real-time widget performance monitoring"""
    __tablename__ = 'widget_status'
    
    id = db.Column(Integer, primary_key=True)
    widget_name = db.Column(String, nullable=False)  # 'featured', 'gallery', 'discovery', 'orchid_of_day'
    
    # Performance metrics
    status = db.Column(String, default='healthy')  # 'healthy', 'degraded', 'down'
    response_time_ms = db.Column(Integer, nullable=True)
    success_rate = db.Column(Float, default=100.0)  # 0.0 to 100.0
    error_count = db.Column(Integer, default=0)
    last_error = db.Column(Text, nullable=True)
    
    # Content metrics
    images_loaded = db.Column(Integer, default=0)
    images_failed = db.Column(Integer, default=0)
    data_freshness = db.Column(DateTime, nullable=True)
    
    # System info
    server_load = db.Column(Float, nullable=True)
    memory_usage = db.Column(Float, nullable=True)
    
    last_checked = db.Column(DateTime, default=datetime.now)
    created_at = db.Column(DateTime, default=datetime.now)

class ExpertVerification(db.Model):
    """Expert member verification of orchid data accuracy"""
    __tablename__ = 'expert_verifications'
    
    id = db.Column(Integer, primary_key=True)
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    expert_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    
    # Verification details
    verification_status = db.Column(String, nullable=False)  # 'verified', 'needs_correction', 'disputed'
    expertise_areas = db.Column(JSON, nullable=True)  # ['taxonomy', 'habitat', 'morphology', 'cultivation']
    confidence_score = db.Column(Float, nullable=True)  # 0.0 to 1.0
    
    # Field-specific verifications
    scientific_name_verified = db.Column(Boolean, default=None, nullable=True)
    common_name_verified = db.Column(Boolean, default=None, nullable=True)
    habitat_verified = db.Column(Boolean, default=None, nullable=True)
    geographic_range_verified = db.Column(Boolean, default=None, nullable=True)
    morphology_verified = db.Column(Boolean, default=None, nullable=True)
    
    # Notes and corrections
    expert_notes = db.Column(Text, nullable=True)
    suggested_corrections = db.Column(JSON, nullable=True)
    references_cited = db.Column(Text, nullable=True)
    
    verified_at = db.Column(DateTime, default=datetime.now)
    updated_at = db.Column(DateTime, default=datetime.now, onupdate=datetime.now)

class WorkshopRegistration(db.Model):
    __tablename__ = 'workshop_registrations'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    experience_level = db.Column(db.String(50))  # 'beginner', 'intermediate', 'experienced'
    member_status = db.Column(db.String(50), nullable=False)  # 'current', 'former', 'non-member'
    bringing_orchid = db.Column(db.Boolean, default=False)
    orchid_type = db.Column(db.String(100))
    primary_interest = db.Column(db.String(100))  # 'traditional', 'semi-hydro', 'both', 'learning'
    special_needs = db.Column(db.Text)
    workshop_date = db.Column(db.Date, nullable=False)
    amount_paid = db.Column(db.Float, default=10.00)
    payment_status = db.Column(db.String(50), default='pending')  # 'pending', 'paid', 'refunded'
    payment_method = db.Column(db.String(50))  # 'cash', 'venmo', 'check', 'online'
    registration_status = db.Column(db.String(50), default='confirmed')  # 'confirmed', 'waitlist', 'cancelled'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    notes = db.Column(db.Text)  # Admin notes
    
    def __repr__(self):
        return f'<WorkshopRegistration {self.first_name} {self.last_name} - {self.workshop_date}>'

class FieldObservation(db.Model):
    """Field observation records from mobile researchers"""
    __tablename__ = 'field_observations'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User and session info
    user_id = db.Column(db.String, db.ForeignKey('users.id'), nullable=True)
    session_id = db.Column(db.String(50), nullable=False)  # For anonymous users
    researcher_name = db.Column(db.String(200), nullable=True)
    researcher_email = db.Column(db.String(120), nullable=True)
    
    # Observation data
    observation_id = db.Column(db.String(20), unique=True, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Location data
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    altitude = db.Column(db.Float, nullable=True)
    location_accuracy = db.Column(db.Float, nullable=True)  # GPS accuracy in meters
    location_description = db.Column(db.String(500), nullable=True)
    
    # Environmental conditions
    habitat_notes = db.Column(db.Text, nullable=True)
    weather_conditions = db.Column(db.String(200), nullable=True)
    light_conditions = db.Column(db.String(100), nullable=True)
    substrate_type = db.Column(db.String(100), nullable=True)  # tree_trunk, rock, soil, etc.
    companion_species = db.Column(db.Text, nullable=True)
    
    # Orchid observation data
    tentative_genus = db.Column(db.String(100), nullable=True)
    tentative_species = db.Column(db.String(100), nullable=True)
    growth_stage = db.Column(db.String(50), nullable=True)  # seedling, juvenile, flowering, fruiting
    flower_color = db.Column(db.String(100), nullable=True)
    estimated_size = db.Column(db.String(100), nullable=True)
    population_count = db.Column(db.Integer, nullable=True)
    
    # Photo data
    photo_drive_id = db.Column(db.String(200), nullable=True)
    photo_url = db.Column(db.String(500), nullable=True)
    photo_filename = db.Column(db.String(300), nullable=True)
    
    # AI Analysis results
    ai_identification = db.Column(db.JSON, nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)
    
    # Processing status
    sync_status = db.Column(db.String(20), default='pending')  # pending, synced, processed, error
    processing_status = db.Column(db.String(20), default='queue')  # queue, processing, completed, failed
    admin_status = db.Column(db.String(20), default='pending')  # pending, approved, needs_review
    
    # Privacy and conservation
    sensitivity_flag = db.Column(db.Boolean, default=False)  # For rare/endangered species
    location_privacy = db.Column(db.String(20), default='precise')  # precise, approximate, hidden
    research_consent = db.Column(db.Boolean, default=True)  # User consent for research use
    
    # Field notes
    field_notes = db.Column(db.Text, nullable=True)
    research_questions = db.Column(db.Text, nullable=True)
    conservation_concerns = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, **kwargs):
        super(FieldObservation, self).__init__(**kwargs)
        if not self.observation_id:
            self.observation_id = self.generate_observation_id()
        if not self.session_id:
            self.session_id = str(uuid.uuid4())[:8]
    
    def generate_observation_id(self):
        """Generate unique observation ID"""
        timestamp = datetime.now().strftime('%Y%m%d')
        random_suffix = str(uuid.uuid4())[:6].upper()
        return f"OBS{timestamp}{random_suffix}"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'observation_id': self.observation_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'location_description': self.location_description,
            'tentative_genus': self.tentative_genus,
            'tentative_species': self.tentative_species,
            'habitat_notes': self.habitat_notes,
            'field_notes': self.field_notes,
            'photo_url': self.photo_url,
            'sync_status': self.sync_status,
            'processing_status': self.processing_status,
            'ai_identification': self.ai_identification,
            'ai_confidence': self.ai_confidence
        }


# ==========================================
# Breeder Pro+ Pipeline Models
# ==========================================

class PipelineRun(db.Model):
    """Master record for each Breeder Pro+ pipeline execution"""
    __tablename__ = 'pipeline_runs'
    
    id = db.Column(Integer, primary_key=True)
    pipeline_id = db.Column(String(100), unique=True, nullable=False)  # UUID for tracking
    name = db.Column(String(200), nullable=False)  # User-friendly name
    
    # User and configuration
    started_by_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    config = db.Column(JSON, nullable=True)  # Pipeline configuration JSON
    
    # Status tracking
    status = db.Column(String(20), default='queued')  # queued, running, completed, failed, cancelled
    stage = db.Column(String(50), default='initializing')  # Current stage
    progress_percentage = db.Column(Float, default=0.0)
    
    # Timing
    started_at = db.Column(DateTime, default=datetime.utcnow)
    completed_at = db.Column(DateTime, nullable=True)
    duration_seconds = db.Column(Integer, nullable=True)
    
    # Results
    success_count = db.Column(Integer, default=0)  # Number of successful operations
    error_count = db.Column(Integer, default=0)   # Number of errors
    total_operations = db.Column(Integer, default=0)  # Total operations planned
    
    # Output files and reports
    report_files = db.Column(JSON, nullable=True)  # JSON array of generated report file paths
    data_files = db.Column(JSON, nullable=True)   # JSON array of data file paths
    log_file_path = db.Column(String(500), nullable=True)  # Path to detailed log file
    
    # Email notification
    notification_emails = db.Column(JSON, nullable=True)  # JSON array of email addresses
    email_sent = db.Column(Boolean, default=False)
    
    # Error information
    error_message = db.Column(Text, nullable=True)
    error_details = db.Column(JSON, nullable=True)  # Detailed error information
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    started_by = db.relationship('User', backref='pipeline_runs')
    steps = db.relationship('PipelineStep', backref='pipeline_run', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(PipelineRun, self).__init__(**kwargs)
        if not self.pipeline_id:
            self.pipeline_id = str(uuid.uuid4())
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'name': self.name,
            'status': self.status,
            'stage': self.stage,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'total_operations': self.total_operations,
            'report_files': self.report_files,
            'data_files': self.data_files,
            'email_sent': self.email_sent,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def update_progress(self, stage, progress_percentage, success_count=None, error_count=None):
        """Update pipeline progress"""
        self.stage = stage
        self.progress_percentage = progress_percentage
        if success_count is not None:
            self.success_count = success_count
        if error_count is not None:
            self.error_count = error_count
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def mark_completed(self, success=True, error_message=None):
        """Mark pipeline as completed"""
        self.status = 'completed' if success else 'failed'
        self.completed_at = datetime.utcnow()
        self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    @classmethod
    def get_recent_runs(cls, limit=20):
        """Get recent pipeline runs"""
        return cls.query.order_by(cls.started_at.desc()).limit(limit).all()
    
    @classmethod
    def get_active_runs(cls):
        """Get currently active pipeline runs"""
        return cls.query.filter(cls.status.in_(['queued', 'running'])).all()


class PipelineStep(db.Model):
    """Individual steps within a pipeline run"""
    __tablename__ = 'pipeline_steps'
    
    id = db.Column(Integer, primary_key=True)
    pipeline_run_id = db.Column(Integer, db.ForeignKey('pipeline_runs.id'), nullable=False)
    
    # Step identification
    step_name = db.Column(String(100), nullable=False)  # scraping, upload, analysis, reporting, email
    step_order = db.Column(Integer, nullable=False)     # Order in pipeline
    
    # Status tracking
    status = db.Column(String(20), default='pending')  # pending, running, completed, failed, skipped
    progress_percentage = db.Column(Float, default=0.0)
    
    # Timing
    started_at = db.Column(DateTime, nullable=True)
    completed_at = db.Column(DateTime, nullable=True)
    duration_seconds = db.Column(Integer, nullable=True)
    
    # Results
    items_processed = db.Column(Integer, default=0)
    items_successful = db.Column(Integer, default=0)
    items_failed = db.Column(Integer, default=0)
    
    # Step-specific data
    step_data = db.Column(JSON, nullable=True)  # Step-specific information
    output_files = db.Column(JSON, nullable=True)  # Files generated by this step
    
    # Error information
    error_message = db.Column(Text, nullable=True)
    error_details = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'step_name': self.step_name,
            'step_order': self.step_order,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'duration_seconds': self.duration_seconds,
            'items_processed': self.items_processed,
            'items_successful': self.items_successful,
            'items_failed': self.items_failed,
            'step_data': self.step_data,
            'output_files': self.output_files,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def start_step(self):
        """Mark step as started"""
        self.status = 'running'
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def update_progress(self, progress_percentage, items_processed=None, items_successful=None, items_failed=None):
        """Update step progress"""
        self.progress_percentage = progress_percentage
        if items_processed is not None:
            self.items_processed = items_processed
        if items_successful is not None:
            self.items_successful = items_successful
        if items_failed is not None:
            self.items_failed = items_failed
        self.updated_at = datetime.utcnow()
        db.session.commit()
    
    def complete_step(self, success=True, error_message=None):
        """Mark step as completed"""
        self.status = 'completed' if success else 'failed'
        self.completed_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = int((self.completed_at - self.started_at).total_seconds())
        if error_message:
            self.error_message = error_message
        self.updated_at = datetime.utcnow()
        db.session.commit()


class PipelineTemplate(db.Model):
    """Saved pipeline templates for reuse"""
    __tablename__ = 'pipeline_templates'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    description = db.Column(Text, nullable=True)
    
    # Template configuration
    config = db.Column(JSON, nullable=False)  # Template configuration
    steps = db.Column(JSON, nullable=False)   # Ordered list of steps
    
    # Usage tracking
    created_by_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    usage_count = db.Column(Integer, default=0)
    is_default = db.Column(Boolean, default=False)
    is_active = db.Column(Boolean, default=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    created_by = db.relationship('User', backref='pipeline_templates')
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'config': self.config,
            'steps': self.steps,
            'usage_count': self.usage_count,
            'is_default': self.is_default,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_active_templates(cls):
        """Get all active templates"""
        return cls.query.filter_by(is_active=True).order_by(cls.name).all()
    
    @classmethod
    def get_default_template(cls):
        """Get the default pipeline template"""
        return cls.query.filter_by(is_default=True, is_active=True).first()


class PipelineSchedule(db.Model):
    """Scheduled pipeline runs"""
    __tablename__ = 'pipeline_schedules'
    
    id = db.Column(Integer, primary_key=True)
    name = db.Column(String(200), nullable=False)
    description = db.Column(Text, nullable=True)
    
    # Schedule configuration
    template_id = db.Column(Integer, db.ForeignKey('pipeline_templates.id'), nullable=False)
    schedule_type = db.Column(String(20), nullable=False)  # daily, weekly, monthly, custom
    schedule_config = db.Column(JSON, nullable=False)  # Cron-like schedule configuration
    
    # Status
    is_active = db.Column(Boolean, default=True)
    next_run_at = db.Column(DateTime, nullable=True)
    last_run_at = db.Column(DateTime, nullable=True)
    last_run_status = db.Column(String(20), nullable=True)  # completed, failed
    
    # User and notification
    created_by_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    notification_emails = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('PipelineTemplate', backref='schedules')
    created_by = db.relationship('User', backref='pipeline_schedules')
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'schedule_type': self.schedule_type,
            'schedule_config': self.schedule_config,
            'is_active': self.is_active,
            'next_run_at': self.next_run_at.isoformat() if self.next_run_at else None,
            'last_run_at': self.last_run_at.isoformat() if self.last_run_at else None,
            'last_run_status': self.last_run_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class SVOExtractedData(db.Model):
    """Store SVO (Subject-Verb-Object) extracted data and analysis results"""
    __tablename__ = 'svo_extracted_data'
    
    id = db.Column(Integer, primary_key=True)
    
    # Source information
    source_url = db.Column(String(500), nullable=False, index=True)
    source_type = db.Column(String(50), nullable=False)  # 'svo_primary', 'gary_yong_gee', 'aos_resources'
    page_title = db.Column(String(200), nullable=True)
    
    # SVO Triple data
    subject = db.Column(String(200), nullable=False, index=True)  # orchid species/hybrid name
    verb = db.Column(String(100), nullable=False)  # action/relationship verb
    object = db.Column(Text, nullable=False)  # object/description
    
    # Extracted context and metadata
    original_text = db.Column(Text, nullable=False)  # Original sentence/paragraph
    context_before = db.Column(Text, nullable=True)  # Text before the SVO
    context_after = db.Column(Text, nullable=True)  # Text after the SVO
    
    # Confidence and quality scores
    extraction_confidence = db.Column(Float, nullable=False, default=0.0)  # 0.0-1.0
    svo_confidence = db.Column(Float, nullable=False, default=0.0)  # 0.0-1.0
    text_quality_score = db.Column(Float, nullable=True)  # Overall text quality
    
    # Classification and taxonomy
    genus = db.Column(String(100), nullable=True, index=True)  # Extracted genus
    species = db.Column(String(100), nullable=True, index=True)  # Extracted species
    orchid_type = db.Column(String(50), nullable=True)  # 'species', 'hybrid', 'variety', 'cultivar'
    
    # Care information categories
    care_category = db.Column(String(50), nullable=True)  # 'light', 'water', 'temperature', 'humidity', etc.
    care_subcategory = db.Column(String(50), nullable=True)  # More specific categorization
    seasonal_relevance = db.Column(String(20), nullable=True)  # 'spring', 'summer', 'fall', 'winter', 'year-round'
    
    # Processing metadata
    processing_status = db.Column(String(20), default='pending')  # pending, validated, rejected, archived
    validation_notes = db.Column(Text, nullable=True)
    batch_id = db.Column(String(50), nullable=True)  # For batch processing tracking
    
    # Analysis results (stored as JSON)
    nlp_metadata = db.Column(JSON, nullable=True)  # NLP processing results
    extraction_metadata = db.Column(JSON, nullable=True)  # Additional extraction data
    quality_metrics = db.Column(JSON, nullable=True)  # Quality assessment results
    
    # Relationships to other data
    orchid_record_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    related_svo_ids = db.Column(JSON, nullable=True)  # Array of related SVO record IDs
    
    # System tracking
    ingestion_source = db.Column(String(50), default='svo_processor')
    is_featured = db.Column(Boolean, default=False)
    view_count = db.Column(Integer, default=0)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    extracted_at = db.Column(DateTime, nullable=True)  # When the data was originally extracted
    validated_at = db.Column(DateTime, nullable=True)  # When it was validated
    
    def to_dict(self):
        """Convert to dictionary for API responses and serialization"""
        return {
            'id': self.id,
            'source_url': self.source_url,
            'source_type': self.source_type,
            'page_title': self.page_title,
            'subject': self.subject,
            'verb': self.verb,
            'object': self.object,
            'original_text': self.original_text,
            'extraction_confidence': self.extraction_confidence,
            'svo_confidence': self.svo_confidence,
            'genus': self.genus,
            'species': self.species,
            'orchid_type': self.orchid_type,
            'care_category': self.care_category,
            'care_subcategory': self.care_subcategory,
            'seasonal_relevance': self.seasonal_relevance,
            'processing_status': self.processing_status,
            'batch_id': self.batch_id,
            'nlp_metadata': self.nlp_metadata,
            'extraction_metadata': self.extraction_metadata,
            'quality_metrics': self.quality_metrics,
            'orchid_record_id': self.orchid_record_id,
            'related_svo_ids': self.related_svo_ids,
            'ingestion_source': self.ingestion_source,
            'is_featured': self.is_featured,
            'view_count': self.view_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'extracted_at': self.extracted_at.isoformat() if self.extracted_at else None,
            'validated_at': self.validated_at.isoformat() if self.validated_at else None
        }
    
    def get_full_svo_text(self):
        """Get formatted SVO triple as readable text"""
        return f"{self.subject} {self.verb} {self.object}"
    
    def get_orchid_name(self):
        """Extract orchid name from subject"""
        if self.genus and self.species:
            return f"{self.genus} {self.species}"
        return self.subject
    
    def is_high_confidence(self, threshold=0.7):
        """Check if extraction meets high confidence threshold"""
        return (self.extraction_confidence >= threshold and 
                self.svo_confidence >= threshold)
    
    def validate_svo_quality(self):
        """Validate SVO data quality based on defined thresholds"""
        issues = []
        
        if not self.subject or len(self.subject.strip()) < 3:
            issues.append("Subject too short or empty")
            
        if not self.verb or len(self.verb.strip()) < 2:
            issues.append("Verb too short or empty")
            
        if not self.object or len(self.object.strip()) < 5:
            issues.append("Object too short or empty")
            
        if self.extraction_confidence < 0.3:
            issues.append("Extraction confidence too low")
            
        if len(self.original_text) > 1000:
            issues.append("Original text too long")
            
        if len(self.original_text) < 20:
            issues.append("Original text too short")
            
        return len(issues) == 0, issues
    
    @classmethod
    def get_by_source_type(cls, source_type, limit=100):
        """Get SVO records by source type"""
        return cls.query.filter(cls.source_type == source_type).limit(limit).all()
    
    @classmethod
    def get_by_genus(cls, genus, limit=100):
        """Get SVO records by genus"""
        return cls.query.filter(cls.genus == genus).limit(limit).all()
    
    @classmethod
    def get_high_confidence_records(cls, threshold=0.7, limit=100):
        """Get high confidence SVO records"""
        return cls.query.filter(
            cls.extraction_confidence >= threshold,
            cls.svo_confidence >= threshold
        ).limit(limit).all()
    
    def __repr__(self):
        return f'<SVOExtractedData {self.id}: {self.subject} {self.verb} {self.object[:30]}...>'


# =============================================================================
# COMPREHENSIVE POLLINATOR ECOSYSTEM MODELS
# =============================================================================

class Pollinator(db.Model):
    """
    Comprehensive pollinator species database with ecological data
    """
    __tablename__ = 'pollinators'
    
    id = db.Column(Integer, primary_key=True)
    
    # Taxonomic Information
    scientific_name = db.Column(String(200), nullable=False, index=True)
    common_name = db.Column(String(200), nullable=True)
    family = db.Column(String(100), nullable=False, index=True)
    genus = db.Column(String(100), nullable=False, index=True)
    species = db.Column(String(100), nullable=False)
    subspecies = db.Column(String(100), nullable=True)
    author = db.Column(String(200), nullable=True)
    year_described = db.Column(Integer, nullable=True)
    
    # Classification and Type
    pollinator_type = db.Column(Enum(PollinatorTypeEnum), nullable=False, index=True)
    taxonomic_order = db.Column(String(100), nullable=True)
    taxonomic_class = db.Column(String(100), nullable=True)
    
    # Physical Characteristics
    body_length_mm = db.Column(Float, nullable=True)
    wingspan_mm = db.Column(Float, nullable=True)
    body_mass_mg = db.Column(Float, nullable=True)
    tongue_length_mm = db.Column(Float, nullable=True)
    color_pattern = db.Column(Text, nullable=True)
    
    # Foraging and Behavior
    foraging_behavior = db.Column(String(100), nullable=True)
    social_structure = db.Column(String(50), nullable=True)  # solitary, social, eusocial
    activity_pattern = db.Column(String(50), nullable=True)  # diurnal, nocturnal, crepuscular
    nesting_behavior = db.Column(Text, nullable=True)
    foraging_range_km = db.Column(Float, nullable=True)
    flower_specialization = db.Column(String(100), nullable=True)
    
    # Geographic and Habitat Data
    native_range = db.Column(Text, nullable=True)
    introduced_range = db.Column(Text, nullable=True)
    altitude_min_m = db.Column(Integer, nullable=True)
    altitude_max_m = db.Column(Integer, nullable=True)
    habitat_types = db.Column(JSON, nullable=True)  # List of habitat types
    climate_preferences = db.Column(JSON, nullable=True)  # Temperature, humidity ranges
    
    # Phenology and Timing
    flight_period_start = db.Column(Integer, nullable=True)  # Day of year
    flight_period_end = db.Column(Integer, nullable=True)
    generations_per_year = db.Column(Integer, nullable=True)
    overwintering_stage = db.Column(String(50), nullable=True)
    
    # Conservation Status
    iucn_status = db.Column(String(20), nullable=True)
    population_trend = db.Column(String(20), nullable=True)  # increasing, stable, declining
    threat_level = db.Column(String(20), nullable=True)
    conservation_notes = db.Column(Text, nullable=True)
    
    # External Database Links
    gbif_key = db.Column(String(50), nullable=True, index=True)
    eol_page_id = db.Column(String(50), nullable=True)
    bold_systems_id = db.Column(String(50), nullable=True)
    
    # Data Source and Quality
    data_source = db.Column(String(100), nullable=True)
    source_url = db.Column(String(500), nullable=True)
    data_quality_score = db.Column(Float, default=0.5)
    verification_status = db.Column(String(20), default='unverified')
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'scientific_name': self.scientific_name,
            'common_name': self.common_name,
            'family': self.family,
            'genus': self.genus,
            'species': self.species,
            'pollinator_type': self.pollinator_type.value if self.pollinator_type else None,
            'body_length_mm': self.body_length_mm,
            'foraging_behavior': self.foraging_behavior,
            'native_range': self.native_range,
            'conservation_status': self.iucn_status,
            'flight_period': f"{self.flight_period_start}-{self.flight_period_end}" if self.flight_period_start else None
        }
    
    def __repr__(self):
        return f'<Pollinator {self.scientific_name} ({self.pollinator_type.value if self.pollinator_type else "unknown"})>'

class PollinatorLifecycle(db.Model):
    """
    Detailed lifecycle stages and timing for pollinators
    """
    __tablename__ = 'pollinator_lifecycles'
    
    id = db.Column(Integer, primary_key=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Lifecycle Stage Information
    stage = db.Column(Enum(LifecycleStageEnum), nullable=False)
    duration_days = db.Column(Integer, nullable=True)
    temperature_requirements = db.Column(JSON, nullable=True)  # {min: X, max: Y, optimal: Z}
    humidity_requirements = db.Column(JSON, nullable=True)
    host_plant_requirements = db.Column(Text, nullable=True)
    
    # Timing and Seasonality
    start_day_of_year = db.Column(Integer, nullable=True)
    end_day_of_year = db.Column(Integer, nullable=True)
    peak_activity_day = db.Column(Integer, nullable=True)
    
    # Environmental Triggers
    photoperiod_trigger = db.Column(Float, nullable=True)  # Hours of daylight
    temperature_trigger = db.Column(Float, nullable=True)  # Celsius
    diapause_stage = db.Column(Boolean, default=False)
    
    # Habitat Requirements
    microhabitat = db.Column(Text, nullable=True)
    substrate_requirements = db.Column(Text, nullable=True)
    shelter_requirements = db.Column(Text, nullable=True)
    
    # Mortality and Survival
    survival_rate = db.Column(Float, nullable=True)  # 0.0 to 1.0
    mortality_causes = db.Column(JSON, nullable=True)  # List of mortality factors
    
    # Research Data
    study_references = db.Column(JSON, nullable=True)
    observation_notes = db.Column(Text, nullable=True)
    data_confidence = db.Column(String(20), default='medium')
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = db.relationship('Pollinator', backref='lifecycle_stages')
    
    def __repr__(self):
        return f'<PollinatorLifecycle {self.pollinator_id} - {self.stage.value if self.stage else "unknown"}>'

class MigrationPattern(db.Model):
    """
    Migration routes, timing, and triggers for mobile pollinators
    """
    __tablename__ = 'migration_patterns'
    
    id = db.Column(Integer, primary_key=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Migration Classification
    migration_type = db.Column(Enum(MigrationTypeEnum), nullable=False)
    pattern_name = db.Column(String(200), nullable=True)
    
    # Geographic Information
    origin_latitude = db.Column(Float, nullable=True)
    origin_longitude = db.Column(Float, nullable=True)
    destination_latitude = db.Column(Float, nullable=True)
    destination_longitude = db.Column(Float, nullable=True)
    waypoint_coordinates = db.Column(JSON, nullable=True)  # List of lat/lng pairs
    total_distance_km = db.Column(Float, nullable=True)
    
    # Timing and Duration
    departure_day_of_year = db.Column(Integer, nullable=True)
    arrival_day_of_year = db.Column(Integer, nullable=True)
    migration_duration_days = db.Column(Integer, nullable=True)
    return_migration = db.Column(Boolean, default=False)
    
    # Triggers and Conditions
    temperature_trigger = db.Column(Float, nullable=True)
    photoperiod_trigger = db.Column(Float, nullable=True)
    weather_conditions = db.Column(JSON, nullable=True)
    resource_availability_trigger = db.Column(Text, nullable=True)
    
    # Population Data
    percentage_population_migrating = db.Column(Float, nullable=True)
    survival_rate_migration = db.Column(Float, nullable=True)
    breeding_migration = db.Column(Boolean, default=False)
    
    # Corridor Information
    habitat_corridor_requirements = db.Column(Text, nullable=True)
    stopover_sites = db.Column(JSON, nullable=True)  # Key stopover locations
    threats_along_route = db.Column(JSON, nullable=True)
    
    # Research and Tracking
    tracking_method = db.Column(String(100), nullable=True)  # radar, tagging, citizen science
    study_years = db.Column(JSON, nullable=True)  # Years of study data
    data_source = db.Column(String(200), nullable=True)
    reliability_score = db.Column(Float, default=0.5)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = db.relationship('Pollinator', backref='migration_patterns')
    
    def __repr__(self):
        return f'<MigrationPattern {self.pollinator_id} - {self.migration_type.value if self.migration_type else "unknown"}>'

class AdvancedOrchidPollinatorRelationship(db.Model):
    """
    Enhanced orchid-pollinator relationships with detailed ecological data
    """
    __tablename__ = 'advanced_orchid_pollinator_relationships'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Relationship Characteristics
    relationship_type = db.Column(Enum(RelationshipTypeEnum), nullable=False)
    pollination_effectiveness = db.Column(Float, nullable=True)  # 0.0 to 1.0
    specificity_level = db.Column(String(50), nullable=True)  # specialist, generalist
    interaction_frequency = db.Column(String(50), nullable=True)
    
    # Temporal Patterns
    seasonal_timing = db.Column(JSON, nullable=True)  # {start_day: X, end_day: Y, peak_day: Z}
    time_of_day_pattern = db.Column(JSON, nullable=True)  # Hourly activity pattern
    weather_dependency = db.Column(JSON, nullable=True)  # Weather conditions required
    
    # Pollination Mechanics
    pollinia_attachment_rate = db.Column(Float, nullable=True)
    pollen_transfer_efficiency = db.Column(Float, nullable=True)
    visit_duration_seconds = db.Column(Integer, nullable=True)
    visits_per_flower = db.Column(Float, nullable=True)
    
    # Floral Rewards and Attraction
    nectar_reward = db.Column(Boolean, default=False)
    pollen_reward = db.Column(Boolean, default=False)
    fragrance_attraction = db.Column(Boolean, default=False)
    visual_attraction = db.Column(Boolean, default=False)
    deceptive_mechanism = db.Column(Text, nullable=True)
    
    # Geographic and Habitat Overlap
    geographic_overlap_percentage = db.Column(Float, nullable=True)
    habitat_overlap_score = db.Column(Float, nullable=True)
    altitude_overlap_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    
    # Research Evidence
    evidence_type = db.Column(String(50), nullable=True)  # observed, experimental, literature
    observation_method = db.Column(String(100), nullable=True)
    study_location = db.Column(String(200), nullable=True)
    observation_date = db.Column(DateTime, nullable=True)
    researcher_name = db.Column(String(200), nullable=True)
    reference_citation = db.Column(Text, nullable=True)
    confidence_level = db.Column(String(20), nullable=True)
    
    # Ecosystem Context
    mycorrhizal_connection = db.Column(Text, nullable=True)  # Connection to fungal networks
    plant_community_context = db.Column(Text, nullable=True)
    competition_notes = db.Column(Text, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    pollinator = db.relationship('Pollinator', backref='orchid_relationships')
    orchid = db.relationship('OrchidRecord', backref='pollinator_relationships')
    
    def __repr__(self):
        return f'<AdvancedOrchidPollinatorRelationship {self.orchid_id}-{self.pollinator_id}>'

class PreyPredatorRelationship(db.Model):
    """
    Predator-prey relationships affecting pollinator populations
    """
    __tablename__ = 'prey_predator_relationships'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    predator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    prey_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Relationship Strength
    relationship_strength = db.Column(Float, nullable=True)  # 0.0 to 1.0
    predation_rate = db.Column(Float, nullable=True)  # prey consumed per predator per time
    prey_preference = db.Column(String(50), nullable=True)  # preferred, occasional, rare
    
    # Temporal Patterns
    seasonal_variation = db.Column(JSON, nullable=True)  # Monthly predation rates
    life_stage_specificity = db.Column(JSON, nullable=True)  # Which stages are targeted
    
    # Hunting and Feeding Behavior
    hunting_method = db.Column(String(100), nullable=True)
    attack_success_rate = db.Column(Float, nullable=True)
    feeding_behavior = db.Column(Text, nullable=True)
    
    # Environmental Context
    habitat_specificity = db.Column(Text, nullable=True)
    microhabitat_overlap = db.Column(Float, nullable=True)
    environmental_triggers = db.Column(JSON, nullable=True)
    
    # Population Impact
    population_impact_level = db.Column(String(50), nullable=True)  # low, medium, high
    ecosystem_role = db.Column(Text, nullable=True)
    
    # Research Data
    study_location = db.Column(String(200), nullable=True)
    observation_method = db.Column(String(100), nullable=True)
    data_source = db.Column(String(200), nullable=True)
    reliability_score = db.Column(Float, default=0.5)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    predator = db.relationship('Pollinator', foreign_keys=[predator_id], backref='prey_relationships')
    prey = db.relationship('Pollinator', foreign_keys=[prey_id], backref='predator_relationships')
    
    def __repr__(self):
        return f'<PreyPredatorRelationship {self.predator_id}->{self.prey_id}>'

class EcosystemNetwork(db.Model):
    """
    Network connections between orchids, pollinators, and mycorrhizal fungi
    """
    __tablename__ = 'ecosystem_networks'
    
    id = db.Column(Integer, primary_key=True)
    
    # Network Identification
    network_name = db.Column(String(200), nullable=False)
    network_type = db.Column(String(50), nullable=False)  # pollination, mycorrhizal, tri-partite
    
    # Geographic Scope
    location_name = db.Column(String(200), nullable=True)
    latitude = db.Column(Float, nullable=True)
    longitude = db.Column(Float, nullable=True)
    area_km2 = db.Column(Float, nullable=True)
    habitat_type = db.Column(String(100), nullable=True)
    
    # Network Components (JSON arrays of IDs)
    orchid_species = db.Column(JSON, nullable=True)  # List of orchid_record IDs
    pollinator_species = db.Column(JSON, nullable=True)  # List of pollinator IDs
    mycorrhizal_fungi = db.Column(JSON, nullable=True)  # List of fungal species names
    
    # Network Metrics
    species_richness = db.Column(Integer, nullable=True)
    interaction_count = db.Column(Integer, nullable=True)
    network_density = db.Column(Float, nullable=True)
    modularity_score = db.Column(Float, nullable=True)
    nestedness_score = db.Column(Float, nullable=True)
    
    # Temporal Dynamics
    seasonal_stability = db.Column(Float, nullable=True)
    annual_variation = db.Column(Float, nullable=True)
    phenological_mismatch_risk = db.Column(Float, nullable=True)
    
    # Conservation Status
    threat_level = db.Column(String(20), nullable=True)
    conservation_priority = db.Column(String(20), nullable=True)
    keystone_species = db.Column(JSON, nullable=True)  # Critical species for network stability
    
    # Research Context
    study_duration_years = db.Column(Integer, nullable=True)
    sampling_method = db.Column(String(200), nullable=True)
    research_institution = db.Column(String(200), nullable=True)
    principal_investigator = db.Column(String(200), nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<EcosystemNetwork {self.network_name} ({self.network_type})>'

class HabitatOverlap(db.Model):
    """
    Spatial and temporal habitat overlap between species
    """
    __tablename__ = 'habitat_overlaps'
    
    id = db.Column(Integer, primary_key=True)
    
    # Species Involved
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=True)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=True)
    
    # Spatial Overlap
    geographic_overlap_percentage = db.Column(Float, nullable=True)
    habitat_similarity_score = db.Column(Float, nullable=True)
    microhabitat_overlap = db.Column(Float, nullable=True)
    
    # Elevation and Climate
    elevation_overlap_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    temperature_overlap = db.Column(JSON, nullable=True)
    precipitation_overlap = db.Column(JSON, nullable=True)
    humidity_overlap = db.Column(JSON, nullable=True)
    
    # Temporal Overlap
    phenological_overlap_days = db.Column(Integer, nullable=True)
    peak_activity_synchrony = db.Column(Float, nullable=True)  # 0.0 to 1.0
    seasonal_mismatch_risk = db.Column(Float, nullable=True)
    
    # Quality Metrics
    habitat_quality_score = db.Column(Float, nullable=True)
    fragmentation_impact = db.Column(Float, nullable=True)
    connectivity_index = db.Column(Float, nullable=True)
    
    # Analysis Method
    analysis_method = db.Column(String(100), nullable=True)  # GIS, field_survey, remote_sensing
    resolution_scale = db.Column(String(50), nullable=True)  # fine, medium, coarse
    data_sources = db.Column(JSON, nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<HabitatOverlap orchid:{self.orchid_id} pollinator:{self.pollinator_id}>'

class SeasonalInteraction(db.Model):
    """
    Detailed seasonal timing and interaction patterns
    """
    __tablename__ = 'seasonal_interactions'
    
    id = db.Column(Integer, primary_key=True)
    
    # Core Relationship
    orchid_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    pollinator_id = db.Column(Integer, db.ForeignKey('pollinators.id'), nullable=False)
    
    # Temporal Specificity
    interaction_month = db.Column(Integer, nullable=False)  # 1-12
    interaction_week = db.Column(Integer, nullable=True)  # 1-52
    peak_interaction_day = db.Column(Integer, nullable=True)  # Day of year
    
    # Activity Patterns
    morning_activity = db.Column(Float, nullable=True)  # 0.0 to 1.0
    midday_activity = db.Column(Float, nullable=True)
    afternoon_activity = db.Column(Float, nullable=True)
    evening_activity = db.Column(Float, nullable=True)
    
    # Weather Dependencies
    temperature_optimum = db.Column(Float, nullable=True)
    temperature_range = db.Column(JSON, nullable=True)  # {min: X, max: Y}
    humidity_preference = db.Column(JSON, nullable=True)
    wind_tolerance = db.Column(Float, nullable=True)
    rain_impact = db.Column(String(50), nullable=True)  # stops, reduces, no_effect
    
    # Interaction Quality
    pollination_success_rate = db.Column(Float, nullable=True)
    resource_availability = db.Column(Float, nullable=True)
    competition_level = db.Column(Float, nullable=True)
    
    # Phenological Context
    orchid_flowering_stage = db.Column(String(50), nullable=True)
    pollinator_activity_stage = db.Column(String(50), nullable=True)
    synchrony_score = db.Column(Float, nullable=True)
    
    # Observation Data
    observation_count = db.Column(Integer, nullable=True)
    study_years = db.Column(JSON, nullable=True)
    location_specificity = db.Column(String(200), nullable=True)
    
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<SeasonalInteraction {self.orchid_id}-{self.pollinator_id} month:{self.interaction_month}>'


# =============================================================================
# COMPREHENSIVE MEMBER COLLECTION MODELS
# =============================================================================

class MemberCollection(db.Model):
    """
    Enhanced member collection management with external database integration
    """
    __tablename__ = 'member_collections'
    
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    orchid_record_id = db.Column(Integer, db.ForeignKey('orchid_record.id'), nullable=False)
    
    # Collection metadata
    acquisition_date = db.Column(DateTime, nullable=True)
    acquisition_source = db.Column(String(200), nullable=True)  # nursery, trade, wild collection, etc.
    acquisition_cost = db.Column(Float, nullable=True)
    current_location = db.Column(String(100), nullable=True)  # greenhouse, windowsill, etc.
    
    # Growing conditions and care
    growing_medium = db.Column(String(100), nullable=True)
    pot_size = db.Column(String(50), nullable=True)
    light_conditions = db.Column(String(100), nullable=True)
    watering_schedule = db.Column(String(100), nullable=True)
    fertilizer_routine = db.Column(Text, nullable=True)
    
    # Collection status
    collection_status = db.Column(String(50), default='active')  # active, dormant, flowering, problematic, deceased
    health_status = db.Column(String(50), default='healthy')  # healthy, stressed, diseased, recovering
    flowering_status = db.Column(Boolean, default=False)
    last_repotted = db.Column(DateTime, nullable=True)
    
    # Personal notes and observations
    personal_notes = db.Column(Text, nullable=True)
    care_observations = db.Column(Text, nullable=True)
    breeding_notes = db.Column(Text, nullable=True)
    research_interests = db.Column(JSON, nullable=True)  # List of research topics
    
    # External database integration status
    eol_data_updated = db.Column(DateTime, nullable=True)
    gbif_data_updated = db.Column(DateTime, nullable=True)
    ecological_data_complete = db.Column(Boolean, default=False)
    literature_citations_count = db.Column(Integer, default=0)
    
    # Research and collaboration
    available_for_research = db.Column(Boolean, default=False)
    sharing_permissions = db.Column(String(50), default='private')  # private, members, public
    collaboration_interests = db.Column(JSON, nullable=True)  # List of collaboration types
    
    # Analytics and tracking
    photo_count = db.Column(Integer, default=0)
    measurement_records = db.Column(Integer, default=0)
    care_log_entries = db.Column(Integer, default=0)
    research_publications = db.Column(Integer, default=0)
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='member_collections')
    orchid_record = db.relationship('OrchidRecord', backref='member_collections')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'orchid_record_id': self.orchid_record_id,
            'acquisition_date': self.acquisition_date.isoformat() if self.acquisition_date else None,
            'acquisition_source': self.acquisition_source,
            'current_location': self.current_location,
            'collection_status': self.collection_status,
            'health_status': self.health_status,
            'flowering_status': self.flowering_status,
            'personal_notes': self.personal_notes,
            'available_for_research': self.available_for_research,
            'photo_count': self.photo_count,
            'created_at': self.created_at.isoformat(),
            'orchid': self.orchid_record.to_dict() if self.orchid_record else None
        }
    
    def get_research_opportunities(self):
        """Identify research opportunities for this collection item"""
        opportunities = []
        
        # Check for missing external database data
        if not self.eol_data_updated:
            opportunities.append({
                'type': 'external_database',
                'source': 'EOL',
                'description': 'Enrich with Encyclopedia of Life data',
                'priority': 'medium'
            })
        
        if not self.gbif_data_updated:
            opportunities.append({
                'type': 'external_database', 
                'source': 'GBIF',
                'description': 'Add global occurrence records',
                'priority': 'medium'
            })
        
        # Check for missing ecological data
        if not self.ecological_data_complete:
            opportunities.append({
                'type': 'ecological',
                'description': 'Map pollinator relationships',
                'priority': 'high'
            })
        
        # Check for documentation opportunities
        if self.photo_count < 3:
            opportunities.append({
                'type': 'documentation',
                'description': 'Add more photos (flowers, habit, details)',
                'priority': 'high'
            })
        
        if not self.care_observations:
            opportunities.append({
                'type': 'documentation',
                'description': 'Document care observations and growth patterns',
                'priority': 'medium'
            })
        
        return opportunities


class ExternalDatabaseCache(db.Model):
    """
    Cache for external database queries to improve performance
    """
    __tablename__ = 'external_database_cache'
    
    id = db.Column(Integer, primary_key=True)
    
    # Query identification
    database_source = db.Column(String(50), nullable=False, index=True)  # 'eol', 'gbif', 'bold'
    query_type = db.Column(String(50), nullable=False)  # 'species_search', 'occurrence', 'traits'
    query_key = db.Column(String(200), nullable=False, index=True)  # scientific name or identifier
    
    # Cache data
    response_data = db.Column(JSON, nullable=False)
    response_status = db.Column(String(20), default='success')  # success, error, partial
    query_metadata = db.Column(JSON, nullable=True)  # query parameters, result count, etc.
    
    # Cache management
    cache_created = db.Column(DateTime, default=datetime.utcnow)
    cache_expires = db.Column(DateTime, nullable=False)
    access_count = db.Column(Integer, default=0)
    last_accessed = db.Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_cached_result(cls, database_source, query_type, query_key):
        """Get cached result if available and not expired"""
        cache_entry = cls.query.filter(
            cls.database_source == database_source,
            cls.query_type == query_type,
            cls.query_key == query_key,
            cls.cache_expires > datetime.utcnow()
        ).first()
        
        if cache_entry:
            cache_entry.access_count += 1
            cache_entry.last_accessed = datetime.utcnow()
            db.session.commit()
            return cache_entry.response_data
        
        return None
    
    @classmethod
    def cache_result(cls, database_source, query_type, query_key, response_data, expires_hours=24):
        """Cache a database query result"""
        # Remove existing cache entry
        cls.query.filter(
            cls.database_source == database_source,
            cls.query_type == query_type,
            cls.query_key == query_key
        ).delete()
        
        # Create new cache entry
        cache_entry = cls(
            database_source=database_source,
            query_type=query_type,
            query_key=query_key,
            response_data=response_data,
            cache_expires=datetime.utcnow() + timedelta(hours=expires_hours)
        )
        
        db.session.add(cache_entry)
        db.session.commit()
        
        return cache_entry


class ResearchCollaboration(db.Model):
    """
    Track research collaborations and data sharing between members
    """
    __tablename__ = 'research_collaborations'
    
    id = db.Column(Integer, primary_key=True)
    
    # Collaboration participants
    initiator_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    collaborator_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=False)
    
    # Collaboration details
    collaboration_type = db.Column(String(50), nullable=False)  # 'data_sharing', 'joint_research', 'breeding_program'
    research_focus = db.Column(String(200), nullable=False)
    shared_orchids = db.Column(JSON, nullable=True)  # List of orchid IDs being shared
    
    # Status and permissions
    status = db.Column(String(20), default='proposed')  # proposed, active, completed, cancelled
    data_sharing_level = db.Column(String(50), default='basic')  # basic, detailed, full_access
    can_publish = db.Column(Boolean, default=False)
    attribution_requirements = db.Column(Text, nullable=True)
    
    # Research outputs
    shared_publications = db.Column(JSON, nullable=True)  # List of publication DOIs
    shared_datasets = db.Column(JSON, nullable=True)  # List of dataset identifiers
    collaboration_notes = db.Column(Text, nullable=True)
    
    # Timestamps
    proposed_at = db.Column(DateTime, default=datetime.utcnow)
    accepted_at = db.Column(DateTime, nullable=True)
    completed_at = db.Column(DateTime, nullable=True)
    
    # Relationships
    initiator = db.relationship('User', foreign_keys=[initiator_user_id], backref='initiated_collaborations')
    collaborator = db.relationship('User', foreign_keys=[collaborator_user_id], backref='received_collaborations')
    
    def to_dict(self):
        return {
            'id': self.id,
            'collaboration_type': self.collaboration_type,
            'research_focus': self.research_focus,
            'status': self.status,
            'data_sharing_level': self.data_sharing_level,
            'proposed_at': self.proposed_at.isoformat(),
            'initiator': {
                'id': self.initiator.id,
                'username': self.initiator.username
            } if self.initiator else None,
            'collaborator': {
                'id': self.collaborator.id,
                'username': self.collaborator.username
            } if self.collaborator else None
        }


class LiteratureCitation(db.Model):
    """
    Academic literature citations for orchid research
    """
    __tablename__ = 'literature_citations'
    
    id = db.Column(Integer, primary_key=True)
    
    # Citation metadata
    title = db.Column(String(500), nullable=False)
    authors = db.Column(Text, nullable=False)  # JSON string of author list
    journal = db.Column(String(200), nullable=True)
    publication_year = db.Column(Integer, nullable=True)
    volume = db.Column(String(50), nullable=True)
    issue = db.Column(String(50), nullable=True)
    pages = db.Column(String(100), nullable=True)
    
    # Digital identifiers
    doi = db.Column(String(200), nullable=True, index=True)
    pmid = db.Column(String(20), nullable=True)
    isbn = db.Column(String(20), nullable=True)
    url = db.Column(String(500), nullable=True)
    
    # Orchid relevance
    relevant_genera = db.Column(JSON, nullable=True)  # List of genus names
    relevant_species = db.Column(JSON, nullable=True)  # List of species names
    research_topics = db.Column(JSON, nullable=True)  # List of research keywords
    conservation_relevance = db.Column(Boolean, default=False)
    
    # Access and availability
    open_access = db.Column(Boolean, default=False)
    pdf_available = db.Column(Boolean, default=False)
    local_pdf_path = db.Column(String(500), nullable=True)
    
    # User interactions
    added_by_user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    member_collections_cited = db.Column(JSON, nullable=True)  # List of member collection IDs
    citation_count = db.Column(Integer, default=0)
    
    # Quality and verification
    peer_reviewed = db.Column(Boolean, default=True)
    quality_score = db.Column(Float, nullable=True)  # 0-1 relevance score
    verification_status = db.Column(String(20), default='unverified')
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    added_by = db.relationship('User', backref='added_literature')
    
    def generate_bibtex(self):
        """Generate BibTeX citation format"""
        # Clean title and create citation key
        clean_title = ''.join(c for c in self.title if c.isalnum() or c.isspace())
        citation_key = f"{self.authors.split(',')[0].split()[-1].lower()}{self.publication_year or 'nd'}{clean_title.split()[0].lower()}"
        
        # Parse authors
        try:
            authors_list = json.loads(self.authors) if isinstance(self.authors, str) else self.authors
            authors_str = ' and '.join(authors_list) if isinstance(authors_list, list) else str(self.authors)
        except:
            authors_str = str(self.authors)
        
        # Generate BibTeX entry
        bibtex = f"@article{{{citation_key},\n"
        bibtex += f"  title={{{self.title}}},\n"
        bibtex += f"  author={{{authors_str}}},\n"
        
        if self.journal:
            bibtex += f"  journal={{{self.journal}}},\n"
        if self.publication_year:
            bibtex += f"  year={{{self.publication_year}}},\n"
        if self.volume:
            bibtex += f"  volume={{{self.volume}}},\n"
        if self.issue:
            bibtex += f"  number={{{self.issue}}},\n"
        if self.pages:
            bibtex += f"  pages={{{self.pages}}},\n"
        if self.doi:
            bibtex += f"  doi={{{self.doi}}},\n"
        if self.url:
            bibtex += f"  url={{{self.url}}},\n"
        
        bibtex += "}\n"
        return bibtex
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'journal': self.journal,
            'publication_year': self.publication_year,
            'doi': self.doi,
            'relevant_genera': self.relevant_genera,
            'relevant_species': self.relevant_species,
            'research_topics': self.research_topics,
            'open_access': self.open_access,
            'citation_count': self.citation_count,
            'created_at': self.created_at.isoformat()
        }


# Knowledge Base System for Educational Content
class KnowledgeBase(db.Model):
    """Educational knowledge base entries for orchid research and learning"""
    __tablename__ = 'knowledge_base'
    
    id = db.Column(Integer, primary_key=True)
    title = db.Column(String(200), nullable=False, index=True)
    question = db.Column(Text, nullable=True)
    answer = db.Column(Text, nullable=True)
    category = db.Column(String(100), nullable=False, index=True)
    article = db.Column(Text, nullable=True)
    
    # Search and organization
    keywords = db.Column(JSON, nullable=True)  # For enhanced search
    related_genera = db.Column(JSON, nullable=True)  # Related orchid genera
    difficulty_level = db.Column(String(20), default='intermediate')  # beginner, intermediate, advanced
    content_type = db.Column(String(20), default='qa')  # qa, article, tutorial
    
    # Metadata
    view_count = db.Column(Integer, default=0)
    helpful_votes = db.Column(Integer, default=0)
    last_updated = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = db.Column(DateTime, default=datetime.utcnow)
    
    # Optional attribution
    author = db.Column(String(100), nullable=True)
    source_url = db.Column(String(500), nullable=True)
    
    def increment_view(self):
        """Increment view count for analytics"""
        self.view_count += 1
        db.session.commit()
    
    def add_helpful_vote(self):
        """Add helpful vote for content quality tracking"""
        self.helpful_votes += 1
        db.session.commit()
    
    @staticmethod
    def search_entries(query, category=None, limit=20):
        """Search knowledge base entries by query and optionally by category"""
        search_query = KnowledgeBase.query
        
        if query:
            # Search in title, question, answer, and article
            search_terms = f"%{query.lower()}%"
            search_query = search_query.filter(
                db.or_(
                    KnowledgeBase.title.ilike(search_terms),
                    KnowledgeBase.question.ilike(search_terms),
                    KnowledgeBase.answer.ilike(search_terms),
                    KnowledgeBase.article.ilike(search_terms)
                )
            )
        
        if category:
            search_query = search_query.filter(KnowledgeBase.category == category)
        
        return search_query.order_by(KnowledgeBase.helpful_votes.desc(), KnowledgeBase.view_count.desc()).limit(limit).all()
    
    @staticmethod
    def get_categories():
        """Get all unique categories from knowledge base"""
        categories = db.session.query(KnowledgeBase.category).distinct().all()
        return [cat[0] for cat in categories]
    
    @staticmethod
    def get_popular_entries(limit=10):
        """Get most popular entries by views and votes"""
        return KnowledgeBase.query.order_by(
            (KnowledgeBase.helpful_votes * 2 + KnowledgeBase.view_count).desc()
        ).limit(limit).all()
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'question': self.question,
            'answer': self.answer,
            'category': self.category,
            'article': self.article,
            'difficulty_level': self.difficulty_level,
            'content_type': self.content_type,
            'view_count': self.view_count,
            'helpful_votes': self.helpful_votes,
            'author': self.author,
            'source_url': self.source_url,
            'created_at': self.created_at.isoformat(),
            'last_updated': self.last_updated.isoformat()
        }
