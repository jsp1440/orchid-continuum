import os
import logging
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "orchid-continuum-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database - Use PostgreSQL from environment
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///orchid_continuum.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Configure upload settings
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size for ZIP uploads
app.config['UPLOAD_EXTENSIONS'] = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.zip']
app.config['UPLOAD_FOLDER'] = 'temp'

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models to ensure tables are created - lazy import to avoid circular import
    try:
        import models
        import parentage_models  # Import additional models
    except ImportError as e:
        logging.warning(f"Model import issue (will retry): {e}")
    
    # Initialize database
    try:
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database creation error: {e}")
    
    # Import and register auth blueprint after db initialization
    try:
        from auth_routes import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/auth')
    except ImportError as e:
        logging.warning(f"Auth routes not available: {e}")
    
    # Initialize judging standards
    try:
        from judging_standards import initialize_judging_standards
        initialize_judging_standards()
        print("Judging standards initialized")
    except Exception as e:
        print(f"Judging standards initialization error: {e}")

# Auth blueprint is now registered inside app context above

# Register user weather blueprint
from user_weather_routes import user_weather_bp
app.register_blueprint(user_weather_bp)

# Import routes after app initialization
import routes  # Full featured routes with complete homepage
# import simple_routes  # DISABLED - using full routes instead
import botanical_routes  # Import botanical database routes
import botanical_analysis_route  # Additional botanical analysis integration
import admin_system  # Administrative system with ultimate database control
import user_registration  # User registration and profile system

# Register additional blueprints
try:
    from drive_importer import drive_import_bp
    app.register_blueprint(drive_import_bp)
    print("Google Drive import system initialized")
except Exception as e:
    print(f"Drive import initialization error: {e}")

try:
    from orchid_comparison_system import comparison_bp
    app.register_blueprint(comparison_bp)
    print("Orchid comparison system initialized")
except Exception as e:
    print(f"Comparison system initialization error: {e}")

try:
    from citation_system import citation_bp
    app.register_blueprint(citation_bp)
    print("Citation and attribution system initialized")
except Exception as e:
    print(f"Citation system initialization error: {e}")

try:
    from widget_system import widget_bp
    app.register_blueprint(widget_bp)
    print("Widget system for external integration initialized")
except Exception as e:
    print(f"Widget system initialization error: {e}")

try:
    from orchid_interaction_routes import orchid_interaction_bp
    app.register_blueprint(orchid_interaction_bp)
    print("Orchid Interaction Explorer system initialized")
except Exception as e:
    print(f"Orchid Interaction Explorer initialization error: {e}")

try:
    from system_monitor_dashboard import monitor_bp, initialize_monitoring
    app.register_blueprint(monitor_bp)
    initialize_monitoring()
    print("System Monitor Dashboard initialized")
except Exception as e:
    print(f"System Monitor Dashboard initialization error: {e}")

try:
    from orchid_games import games_bp
    app.register_blueprint(games_bp)
    print("Orchid Games system initialized")
except Exception as e:
    print(f"Orchid Games initialization error: {e}")

# Temporarily disable discovery game due to import conflicts
# try:
#     from interactive_species_discovery import discovery_bp
#     app.register_blueprint(discovery_bp)
#     print("Interactive Species Discovery game initialized")
# except Exception as e:
#     print(f"Species Discovery game initialization error: {e}")

try:
    from api_v2_routes import api_v2
    app.register_blueprint(api_v2)
    print("API v2 routes initialized - FastAPI-compatible endpoints available")
except Exception as e:
    print(f"API v2 routes initialization error: {e}")

try:
    from taxonomy_verification_routes import taxonomy_bp
    app.register_blueprint(taxonomy_bp)
    print("Taxonomy Verification system initialized")
except Exception as e:
    print(f"Taxonomy Verification initialization error: {e}")
