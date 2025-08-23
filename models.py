from app import db
from datetime import datetime, timedelta
from sqlalchemy import String, Text, Integer, Float, Boolean, DateTime, JSON
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=True)
    
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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=True)
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
    """User management system"""
    id = db.Column(Integer, primary_key=True)
    user_id = db.Column(String(20), unique=True, nullable=False)  # Distinctive user ID
    email = db.Column(String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(String(256))
    is_admin = db.Column(Boolean, default=False)
    
    # User profile
    first_name = db.Column(String(100))
    last_name = db.Column(String(100))
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
    
    # Timestamps
    created_at = db.Column(DateTime, default=datetime.utcnow)
    updated_at = db.Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    uploads = db.relationship('UserUpload', backref='user', lazy=True)
    orchid_records = db.relationship('OrchidRecord', backref='owner', lazy=True)
    judgings = db.relationship('JudgingAnalysis', backref='user', lazy=True)
    certificates = db.relationship('Certificate', backref='user', lazy=True)
    
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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=True)
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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=False)
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
    user_id = db.Column(Integer, db.ForeignKey('user.id'), nullable=True)
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
