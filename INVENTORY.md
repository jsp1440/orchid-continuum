# ORCHID CONTINUUM - COMPLETE INVENTORY

## TOP-LEVEL DIRECTORY STRUCTURE

### widgets/ (Embeddable Components)
- **gallery/** - Gallery widget with responsive image display (`index.html`, `widget.js`)
- **weather_widget.js** - Standalone weather/habitat comparison widget

### apps/ (Standalone Applications)
- **admin/** - Admin management tools
- **api/** - FastAPI backend with models and routers
  - `models/` - Database models (orchid_models.py, existing_models.py)
  - `routers/` - API endpoints (admin.py, auth.py, ingest.py, orchids.py, search.py, widgets.py)
- **web/** - Next.js frontend (React/TypeScript)
- **widgets/** - Widget development area

### assets/ (Configuration Data)
- **data/** - JSON data files
  - `gallery.json` - Gallery image metadata and paths

### public/ (Static Web Assets)
- **images/** - Image collections
  - `badges/` - Philosophy quiz badges (~17 SVG files)
  - `gary_collection/` - Photography collection (~21 JPG files)
  - `mahjong_tiles/` - Game tile images (~36 PNG files)
  - Brand assets (logos, placeholders)
- **tools/** - Testing/QA pages
  - `gallery-sanity.html` - Gallery functionality test

### templates/ (HTML Pages - Flask/Jinja2)
- **admin/** - Administrative interfaces (~25 HTML files)
- **widgets/** - Widget templates (~30 HTML files)
- **games/** - Interactive games (~10 HTML files)
- **research/** - Scientific research tools (~10 HTML files)
- Root level templates (~80+ HTML files including main pages)

### Main Application Files
- **routes.py** - Primary Flask application routes (9,848 lines)
- **app.py** - Flask application configuration and initialization
- **models.py** - SQLAlchemy database models
- **main.py** - Application entry point

## ENVIRONMENT VARIABLES ACTUALLY REFERENCED

| Variable | Usage Location | Description |
|----------|----------------|-------------|
| `SESSION_SECRET` | app.py, routes.py | Flask session encryption key |
| `DATABASE_URL` | app.py, routes.py, multiple modules | PostgreSQL connection string |
| `OPENAI_API_KEY` | 15+ modules | AI image analysis and processing |
| `YOUTUBE_API_KEY` | youtube_orchid_widget.py | Five Cities Orchid Society channel |
| `SENDGRID_API_KEY` | sendgrid_email_automation.py, philosophy_quiz_system.py | Email notifications |
| `NEON_ONE_API_KEY` | fcos_integrations.py, neon_one_integration.py | Membership management |
| `NEON_ONE_CLIENT_SECRET` | fcos_integrations.py | Neon One authentication |
| `GOOGLE_SERVICE_ACCOUNT_JSON` | google_drive_service.py, google_sheets_service.py | Cloud storage integration |
| `GOOGLE_DRIVE_FOLDER_ID` | google_drive_service.py | Photo storage location |
| `GOOGLE_SPREADSHEET_ID` | processing_routes.py, orchid_processor.py | Data import source |
| `ADMIN_PASSWORD` | auth_routes.py | **SECURITY RISK: Hardcoded default 'admin123'** |
| `REPLIT_DEV_DOMAIN` | social_media_integration.py, neon_one_integration.py | Deployment URL |
| `EOL_API_KEY` | eol_integration.py | Encyclopedia of Life integration |
| `PLANTNET_API_KEY` | ai_verification_system.py | Plant identification service |

## EXTERNAL DEPENDENCIES/SERVICES

### Cloud Services
- **Neon PostgreSQL** - Primary database (multiple files)
- **Google Drive API** - Image storage (google_drive_service.py)
- **Google Sheets API** - Data import (google_sheets_service.py)
- **OpenAI GPT-4** - AI analysis (15+ modules)
- **SendGrid** - Email automation (sendgrid_email_automation.py)

### Third-Party APIs
- **YouTube Data API v3** - Video integration (youtube_orchid_widget.py)
- **Neon One CRM** - Membership management (fcos_integrations.py)
- **Encyclopedia of Life** - Species data (eol_integration.py)
- **PlantNet** - Plant identification (ai_verification_system.py)

### Python Dependencies
- Flask ecosystem (Flask, SQLAlchemy, Login, WTF)
- AI/ML libraries (OpenAI, scikit-learn, opencv-python)
- Data processing (pandas, numpy, pillow)
- Web scraping (beautifulsoup4, trafilatura, playwright)

## KNOWN ISSUES / TODO COMMENTS

### CRITICAL Security Issues
- **ADMIN_PASSWORD hardcoded default** in auth_routes.py (line 25)
- **SESSION_SECRET hardcoded fallback** in app.py (line 18)

### Development TODOs
- Bug report system needs debugging (test_scrapers_fixed.py line 161)
- Genetic analysis module temporarily disabled (routes.py line 16)
- Enhanced data collection disabled for demo (routes.py line 40)
- Discovery game disabled due to import conflicts (app.py lines 162-167)

### Data Quality
- Multiple Darwin Core export references need validation
- Scraper systems require further debugging
- Image health monitoring needs optimization

## IMAGE COLLECTIONS (Approximate Counts)

| Directory | Count | Content Type |
|-----------|-------|--------------|
| `public/images/badges/` | ~17 files | Philosophy quiz badge SVGs |
| `public/images/gary_collection/` | ~21 files | Photography collection JPGs |
| `public/images/mahjong_tiles/` | ~36 files | Game tile PNGs |
| `attached_assets/gary_photos/` | ~21 files | Test photography JPGs |
| `attached_assets/generated_images/` | ~8 files | AI-generated placeholder PNGs |
| Root image files | ~70+ files | Screenshots, assets, documents |

## CRITICAL SYSTEMS FOR CORE FEATURES

### Orchid-of-the-Day
- **Dependencies**: routes.py (get_orchid_of_the_day), models.py (OrchidRecord)
- **Status**: ✅ Operational
- **Files**: utils.py, templates/index.html

### Gallery System
- **Dependencies**: widgets/gallery/, assets/data/gallery.json, public/images/
- **Status**: ✅ Recently implemented
- **Files**: widgets/gallery/index.html, widgets/gallery/widget.js

### Judging System
- **Dependencies**: judging_standards.py, enhanced_judging.py, models.py (JudgingAnalysis)
- **Status**: ✅ Operational with genetics integration
- **Files**: templates/fcos_judge_index.html, routes_fcos_judge.py

### Climate Comparator
- **Dependencies**: weather_habitat_comparison_widget.py, WeatherService
- **Status**: ✅ Operational with AI advice
- **Files**: templates/weather_habitat/widget.html

### Search System
- **Dependencies**: routes.py search endpoints, models.py (OrchidRecord, OrchidTaxonomy)
- **Status**: ✅ Operational with taxonomy verification
- **Files**: templates/search.html, templates/widgets/search_widget.html

### Map System
- **Dependencies**: geographic_mapping_routes.py, enhanced_mapping_routes.py
- **Status**: ✅ Operational with satellite integration
- **Files**: templates/widgets/map_widget.html, templates/global_satellite_map.html

### AI Analysis
- **Dependencies**: orchid_ai.py, ai_orchid_identification.py, OPENAI_API_KEY
- **Status**: ✅ Operational with image recognition
- **Files**: ai_orchid_routes.py, multiple AI integration modules

## API ENDPOINTS (Sample from routers/)

### Core APIs
- `/api/orchids` - Orchid data CRUD operations
- `/api/search` - Search functionality
- `/api/widgets` - Widget configuration
- `/api/admin` - Administrative functions
- `/api/auth` - Authentication endpoints
- `/api/ingest` - Data import/scraping

### Widget APIs
- YouTube widget endpoints in youtube_orchid_widget.py
- Neon One widget endpoints in neon_one_widget_package.py
- Weather/habitat comparison APIs
- Philosophy quiz scoring endpoints

---

**Last Updated**: 2025-09-15  
**Total Files Scanned**: 500+ files across entire project structure  
**Database Models**: 15+ core models in models.py and parentage_models.py