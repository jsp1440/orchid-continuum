# Orchid Continuum AI Project

## Overview

The Orchid Continuum is an AI-enhanced orchid database and management system that consolidates orchid photos and metadata from multiple sources. It provides automated data ingestion, AI-powered orchid identification, and real-time web widgets for orchid enthusiasts and researchers.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask web application with SQLAlchemy ORM
- **Database**: SQLite (default) with support for PostgreSQL via environment configuration
- **AI Integration**: OpenAI GPT-4o for image analysis and metadata extraction
- **File Storage**: Google Drive API integration for cloud storage
- **Web Scraping**: Automated content extraction from orchid websites using trafilatura and BeautifulSoup

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Bootstrap 5 dark theme
- **Styling**: Bootstrap CSS with custom orchid-themed styling
- **Icons**: Feather Icons for consistent UI elements
- **Interactive Features**: JavaScript for enhanced user experience, image previews, and lazy loading

### Database Schema
The system uses a dual-model approach:
- **OrchidTaxonomy**: Master taxonomy table for standardized orchid classification
- **OrchidRecord**: Main orchid records with extensive metadata including growing characteristics, cultural information, and AI analysis results

## Key Components

### 1. AI-Powered Image Analysis
- OpenAI Vision API integration for orchid identification
- Extracts detailed metadata including scientific names, characteristics, and growing conditions
- Confidence scoring for identification accuracy

### 2. Automated Web Scraping
- Configurable scrapers for orchid websites (Gary Yong Gee, Roberta Fox)
- Content extraction and metadata normalization
- Logging system for tracking scraping activities

### 3. File Upload and Management
- Secure file upload with validation and size limits
- Automatic filename generation with timestamps and UUIDs
- Google Drive integration for cloud storage

### 4. Search and Gallery Systems
- Advanced search functionality across multiple fields
- Filterable gallery with pagination
- Featured orchid system and "Orchid of the Day" widget

### 5. Admin Dashboard
- Upload validation and moderation
- Database statistics and management
- Scraping log monitoring

## Data Flow

1. **Input Sources**:
   - User photo uploads via web interface
   - Automated web scraping from orchid websites
   - Legacy form submissions and taxonomy files

2. **Processing Pipeline**:
   - File validation and secure storage
   - AI analysis for metadata extraction
   - Taxonomy matching and normalization
   - Database storage with logging

3. **Output Systems**:
   - Web gallery and search interfaces
   - Real-time widgets (Orchid of the Day)
   - Admin dashboard for management

## External Dependencies

### APIs and Services
- **OpenAI API**: GPT-4o model for image analysis and text processing
- **Google Drive API**: Cloud storage for orchid images
- **Web Scraping Targets**: Gary Yong Gee and Roberta Fox orchid websites

### Python Libraries
- **Flask**: Web framework and routing
- **SQLAlchemy**: Database ORM and migrations
- **Pillow**: Image processing and manipulation
- **BeautifulSoup/trafilatura**: Web content extraction
- **Werkzeug**: File upload security and utilities

### Frontend Libraries
- **Bootstrap 5**: UI framework with dark theme
- **Feather Icons**: Icon system
- **JavaScript**: Enhanced interactivity and AJAX functionality

## Deployment Strategy

### Environment Configuration
- **Development**: SQLite database with debug mode enabled
- **Production**: PostgreSQL database via DATABASE_URL environment variable
- **API Keys**: Environment variables for OpenAI and Google Drive credentials

### File Structure Organization
- Centralized folder structure for different data sources
- Automated categorization of scraped content, user uploads, and processed metadata
- Google Drive integration for scalable cloud storage

### Scaling Considerations
- Database connection pooling with automatic reconnection
- File size limits and upload validation
- Logging system for monitoring and debugging
- Modular scraper architecture for adding new data sources

The system is designed to be self-contained yet extensible, with clear separation between data ingestion, processing, and presentation layers. The AI integration provides intelligent metadata extraction while maintaining human oversight through the admin dashboard.