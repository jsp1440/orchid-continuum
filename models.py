from app import db
from datetime import datetime, timedelta
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON, Enum
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets
import enum
import json
import uuid

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
    """OAuth tokens for authentication"""
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String, db.ForeignKey('users.id'))
    browser_session_key = db.Column(String, nullable=False)
    provider = db.Column(String, nullable=False)
    token = db.Column(Text, nullable=True)
    user = db.relationship('User')

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
    user_id = db.Column(String, db.ForeignKey('users.id'), nullable=True)
    
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
    genus = db.Column(String(100), index=True)
    species = db.Column(String(100))
    author = db.Column(String(200))
    
    # Geographic and habitat data
    region = db.Column(String(100))
    native_habitat = db.Column(Text)
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
    
    # System metadata
    ingestion_source = db.Column(String(50))  # 'upload', 'scrape_gary', 'scrape_roberta', 'legacy'
    validation_status = db.Column(String(20), default='pending')  # pending, validated, rejected
    is_featured = db.Column(Boolean, default=False)
    view_count = db.Column(Integer, default=0)
    
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
        expired = PasswordResetToken.query.filter(
            PasswordResetToken.expires_at < datetime.utcnow()
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
