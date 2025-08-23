from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import (OrchidRecord, OrchidTaxonomy, UserUpload, ScrapingLog, WidgetConfig, 
                   User, JudgingAnalysis, Certificate, BatchUpload, UserFeedback)
from orchid_ai import analyze_orchid_image, extract_metadata_from_text
from web_scraper import scrape_gary_yong_gee, scrape_roberta_fox
from google_drive_service import upload_to_drive, get_drive_file_url
from utils import allowed_file, generate_filename, get_orchid_of_the_day
from batch_upload import BatchUploadProcessor, validate_batch_limits
from judging_standards import analyze_orchid_by_organization, get_available_organizations
from enhanced_judging import analyze_orchid_with_genetics
# from genetic_analysis import analyze_orchid_genetics, compare_hybrid_to_parents  # Temporarily disabled
from enhanced_metadata_analyzer import analyze_orchid_with_botanical_databases
from rhs_integration import get_rhs_orchid_data, analyze_hybrid_parentage
from export_utils import export_orchid_data, get_export_filename
from certificate_generator import generate_award_certificate, get_certificate_pdf
from filename_parser import parse_orchid_filename
from processing_routes import processing_bp
from photo_editor_routes import photo_editor_bp
import os
import json
import logging
from datetime import datetime
from sqlalchemy import or_, func, and_
from io import BytesIO

logger = logging.getLogger(__name__)

# Register blueprints
app.register_blueprint(processing_bp)
app.register_blueprint(photo_editor_bp)

@app.route('/')
def index():
    """Homepage with featured orchids and widgets"""
    try:
        # Get orchid of the day
        orchid_of_day = get_orchid_of_the_day()
        
        # Get recent uploads with error handling
        recent_orchids = []
        try:
            recent_orchids = OrchidRecord.query.filter(
                OrchidRecord.image_url.isnot(None)
            ).order_by(OrchidRecord.created_at.desc()).limit(6).all()
        except Exception as e:
            logger.error(f"Error fetching recent orchids: {str(e)}")
            db.session.rollback()
        
        # Get featured orchids with error handling
        featured_orchids = []
        try:
            featured_orchids = OrchidRecord.query.filter_by(is_featured=True).limit(4).all()
        except Exception as e:
            logger.error(f"Error fetching featured orchids: {str(e)}")
            db.session.rollback()
        
        # Stats with error handling
        total_orchids = 0
        total_genera = 0
        try:
            total_orchids = OrchidRecord.query.count()
            total_genera = db.session.query(func.count(func.distinct(OrchidRecord.genus))).scalar() or 0
        except Exception as e:
            logger.error(f"Error fetching stats: {str(e)}")
            db.session.rollback()
        
        return render_template('index.html',
                             orchid_of_day=orchid_of_day,
                             recent_orchids=recent_orchids,
                             featured_orchids=featured_orchids,
                             total_orchids=total_orchids,
                             total_genera=total_genera)
    
    except Exception as e:
        logger.error(f"Homepage error: {str(e)}")
        db.session.rollback()
        # Return minimal homepage on error
        return render_template('index.html',
                             orchid_of_day=None,
                             recent_orchids=[],
                             featured_orchids=[],
                             total_orchids=0,
                             total_genera=0)

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """Handle orchid photo uploads"""
    if request.method == 'POST':
        try:
            if 'file' not in request.files:
                flash('No file selected', 'error')
                return redirect(request.url)
            
            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'error')
                return redirect(request.url)
            
            if file and allowed_file(file.filename):
                # Generate secure filename
                original_filename = secure_filename(file.filename)
                new_filename = generate_filename(original_filename)
                
                # Save temporarily
                temp_path = os.path.join('temp', new_filename)
                os.makedirs('temp', exist_ok=True)
                file.save(temp_path)
                
                # Parse filename for orchid info
                parsed_info = parse_orchid_filename(original_filename)
                
                # Create upload record
                upload_record = UserUpload(
                    user_id=current_user.id if current_user.is_authenticated else None,
                    original_filename=original_filename,
                    uploaded_filename=new_filename,
                    file_size=os.path.getsize(temp_path),
                    mime_type=file.content_type,
                    user_notes=request.form.get('notes', ''),
                    processing_status='processing',
                    parsed_genus=parsed_info.get('genus'),
                    parsed_species=parsed_info.get('species'),
                    filename_confidence=parsed_info.get('confidence', 0.0)
                )
                db.session.add(upload_record)
                db.session.commit()
                
                # Process the image
                try:
                    # Upload to Google Drive
                    drive_file_id = upload_to_drive(temp_path, new_filename, 'Orchid_Quick_Images')
                    image_url = get_drive_file_url(drive_file_id) if drive_file_id else None
                    
                    # Analyze with AI
                    ai_result = analyze_orchid_image(temp_path)
                    
                    # Create orchid record
                    orchid = OrchidRecord(
                        display_name=ai_result.get('suggested_name', f'Unknown Orchid {upload_record.id}'),
                        scientific_name=ai_result.get('scientific_name'),
                        genus=ai_result.get('genus'),
                        species=ai_result.get('species'),
                        image_filename=new_filename,
                        image_url=image_url,
                        google_drive_id=drive_file_id,
                        ai_description=ai_result.get('description'),
                        ai_confidence=ai_result.get('confidence', 0.0),
                        ai_extracted_metadata=json.dumps(ai_result.get('metadata', {})),
                        ingestion_source='upload',
                        cultural_notes=request.form.get('notes', '')
                    )
                    
                    # Try to match with taxonomy
                    if orchid.scientific_name:
                        taxonomy = OrchidTaxonomy.query.filter_by(
                            scientific_name=orchid.scientific_name
                        ).first()
                        if taxonomy:
                            orchid.taxonomy_id = taxonomy.id
                    
                    db.session.add(orchid)
                    upload_record.processing_status = 'completed'
                    upload_record.orchid_id = orchid.id
                    db.session.commit()
                    
                    # Clean up temp file
                    os.remove(temp_path)
                    
                    flash('Orchid uploaded and processed successfully!', 'success')
                    return redirect(url_for('orchid_detail', id=orchid.id))
                    
                except Exception as e:
                    logger.error(f"Error processing upload: {str(e)}")
                    upload_record.processing_status = 'failed'
                    db.session.commit()
                    flash(f'Error processing image: {str(e)}', 'error')
            else:
                flash('Invalid file type. Please upload JPG, PNG, or GIF files.', 'error')
                
        except Exception as e:
            logger.error(f"Upload error: {str(e)}")
            flash(f'Upload failed: {str(e)}', 'error')
    
    return render_template('upload.html')

@app.route('/gallery')
def gallery():
    """Display orchid gallery with filtering"""
    page = request.args.get('page', 1, type=int)
    genus = request.args.get('genus', '')
    climate = request.args.get('climate', '')
    growth_habit = request.args.get('growth_habit', '')
    
    query = OrchidRecord.query.filter(OrchidRecord.image_url.isnot(None))
    
    if genus:
        query = query.filter(OrchidRecord.genus.ilike(f'%{genus}%'))
    if climate:
        query = query.filter_by(climate_preference=climate)
    if growth_habit:
        query = query.filter_by(growth_habit=growth_habit)
    
    orchids = query.order_by(OrchidRecord.created_at.desc()).paginate(
        page=page, per_page=12, error_out=False
    )
    
    # Get filter options
    genera = db.session.query(OrchidRecord.genus).distinct().filter(
        OrchidRecord.genus.isnot(None)
    ).all()
    genera = [g[0] for g in genera if g[0]]
    
    climates = ['cool', 'intermediate', 'warm']
    growth_habits = ['epiphytic', 'terrestrial', 'lithophytic']
    
    return render_template('gallery.html',
                         orchids=orchids,
                         genera=genera,
                         climates=climates,
                         growth_habits=growth_habits,
                         current_genus=genus,
                         current_climate=climate,
                         current_growth_habit=growth_habit)

@app.route('/search')
def search():
    """Search orchids by various criteria"""
    query_text = request.args.get('q', '').strip()
    
    if not query_text:
        orchids = []
    else:
        # Search across multiple fields
        orchids = OrchidRecord.query.filter(
            or_(
                OrchidRecord.display_name.ilike(f'%{query_text}%'),
                OrchidRecord.scientific_name.ilike(f'%{query_text}%'),
                OrchidRecord.genus.ilike(f'%{query_text}%'),
                OrchidRecord.species.ilike(f'%{query_text}%'),
                OrchidRecord.cultural_notes.ilike(f'%{query_text}%'),
                OrchidRecord.ai_description.ilike(f'%{query_text}%')
            )
        ).order_by(OrchidRecord.view_count.desc()).limit(50).all()
    
    return render_template('search.html', orchids=orchids, query=query_text)

@app.route('/map')
def world_map():
    """Interactive world map showing orchid locations"""
    return render_template('map.html')

def get_database_statistics():
    """Calculate comprehensive database statistics"""
    try:
        # Basic counts
        total_orchids = OrchidRecord.query.count()
        total_genera = db.session.query(func.count(func.distinct(OrchidRecord.genus))).scalar() or 0
        
        # Species count
        species_count = OrchidRecord.query.filter(
            OrchidRecord.is_species == True
        ).count()
        
        # Hybrid count
        hybrid_count = OrchidRecord.query.filter(
            OrchidRecord.is_hybrid == True
        ).count()
        
        # Intergeneric count (hybrids with different genera in parentage)
        intergeneric_count = 0
        try:
            # Check for records with different genera in parentage
            intergenerics = OrchidRecord.query.filter(
                and_(
                    OrchidRecord.is_hybrid == True,
                    or_(
                        OrchidRecord.pod_parent.isnot(None),
                        OrchidRecord.pollen_parent.isnot(None),
                        OrchidRecord.parentage_formula.isnot(None)
                    )
                )
            ).all()
            
            for orchid in intergenerics:
                if is_intergeneric_hybrid(orchid):
                    intergeneric_count += 1
                    
        except Exception as e:
            logger.error(f"Error calculating intergeneric count: {str(e)}")
        
        return {
            'total_orchids': total_orchids,
            'genera': total_genera,
            'species': species_count,
            'hybrids': hybrid_count,
            'intergenerics': intergeneric_count
        }
    except Exception as e:
        logger.error(f"Error calculating database statistics: {str(e)}")
        return {
            'total_orchids': 0,
            'genera': 0,
            'species': 0,
            'hybrids': 0,
            'intergenerics': 0
        }

def is_intergeneric_hybrid(orchid):
    """Check if an orchid is an intergeneric hybrid"""
    try:
        # Check if parents have different genera
        if orchid.pod_parent and orchid.pollen_parent:
            pod_genus = extract_genus_from_name(orchid.pod_parent)
            pollen_genus = extract_genus_from_name(orchid.pollen_parent)
            
            if pod_genus and pollen_genus and pod_genus != pollen_genus:
                return True
        
        # Check parentage formula for genus crosses (e.g., "Cattleya × Laelia")
        if orchid.parentage_formula:
            formula = orchid.parentage_formula.lower()
            # Look for genus names separated by × or x
            if '×' in formula or ' x ' in formula:
                # Extract genera from the formula
                genera_in_formula = extract_genera_from_formula(formula)
                if len(set(genera_in_formula)) > 1:
                    return True
        
        # Check scientific name for intergeneric notation (usually starts with ×)
        if orchid.scientific_name and orchid.scientific_name.startswith('×'):
            return True
            
        return False
    except Exception:
        return False

def extract_genus_from_name(name):
    """Extract genus from a plant name"""
    if not name:
        return None
    
    # Take the first word as genus
    parts = name.strip().split()
    if parts:
        genus = parts[0].replace('×', '').strip()
        return genus.capitalize()
    return None

def extract_genera_from_formula(formula):
    """Extract all genus names from a parentage formula"""
    import re
    # Find genus names (capitalized words at the start of names)
    genera = []
    words = re.findall(r'\b[A-Z][a-z]+', formula)
    for word in words:
        if len(word) > 2 and word not in ['var', 'Ver', 'Var']:  # Skip common abbreviations
            genera.append(word)
    return genera

@app.route('/api/database-statistics')
def api_database_statistics():
    """API endpoint for database statistics"""
    try:
        stats = get_database_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error fetching database statistics: {str(e)}")
        return jsonify({
            'total_orchids': 0,
            'genera': 0,
            'species': 0,
            'hybrids': 0,
            'intergenerics': 0
        }), 500

@app.route('/api/orchid-locations')
def orchid_locations_api():
    """API endpoint to get orchid location data for the map"""
    try:
        # Get all orchids with geographic data
        orchids = OrchidRecord.query.filter(
            or_(
                OrchidRecord.region.isnot(None),
                OrchidRecord.native_habitat.isnot(None)
            )
        ).all()
        
        locations = []
        for orchid in orchids:
            location_data = {}
            
            # Try to extract coordinates from AI extracted metadata if available
            if orchid.ai_extracted_metadata:
                try:
                    metadata = json.loads(orchid.ai_extracted_metadata) if isinstance(orchid.ai_extracted_metadata, str) else orchid.ai_extracted_metadata
                    if metadata and 'location' in metadata:
                        location_info = metadata['location']
                        if 'latitude' in location_info and 'longitude' in location_info:
                            location_data['lat'] = float(location_info['latitude'])
                            location_data['lng'] = float(location_info['longitude'])
                except (json.JSONDecodeError, KeyError, ValueError, TypeError):
                    pass
            
            # If no coordinates from metadata, try to derive approximate location from region/habitat
            if 'lat' not in location_data:
                location_data.update(_get_approximate_location(orchid.region, orchid.native_habitat))
            
            # Only include orchids with valid location data
            if 'lat' in location_data and 'lng' in location_data:
                location_data.update({
                    'id': orchid.id,
                    'name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'region': orchid.region,
                    'habitat': orchid.native_habitat,
                    'image_url': orchid.image_url,
                    'climate': orchid.climate_preference,
                    'growth_habit': orchid.growth_habit,
                    'bloom_time': orchid.bloom_time
                })
                locations.append(location_data)
        
        return jsonify({
            'success': True,
            'locations': locations,
            'total_count': len(locations)
        })
    
    except Exception as e:
        logger.error(f"Error fetching orchid locations: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to fetch orchid locations',
            'locations': [],
            'total_count': 0
        })

def _get_approximate_location(region, habitat):
    """Get approximate coordinates based on region/habitat text"""
    # Simple mapping of common regions to approximate coordinates
    region_coordinates = {
        # Asia
        'thailand': {'lat': 15.87, 'lng': 100.99},
        'malaysia': {'lat': 4.21, 'lng': 101.97},
        'singapore': {'lat': 1.35, 'lng': 103.82},
        'indonesia': {'lat': -0.79, 'lng': 113.92},
        'philippines': {'lat': 12.88, 'lng': 121.77},
        'vietnam': {'lat': 14.06, 'lng': 108.28},
        'laos': {'lat': 19.85, 'lng': 102.50},
        'cambodia': {'lat': 12.57, 'lng': 104.99},
        'myanmar': {'lat': 21.92, 'lng': 95.96},
        'china': {'lat': 35.86, 'lng': 104.20},
        'india': {'lat': 20.59, 'lng': 78.96},
        'japan': {'lat': 36.20, 'lng': 138.25},
        'south korea': {'lat': 35.91, 'lng': 127.77},
        
        # Americas
        'ecuador': {'lat': -1.83, 'lng': -78.18},
        'colombia': {'lat': 4.57, 'lng': -74.30},
        'peru': {'lat': -9.19, 'lng': -75.02},
        'brazil': {'lat': -14.24, 'lng': -51.93},
        'costa rica': {'lat': 9.75, 'lng': -83.75},
        'guatemala': {'lat': 15.78, 'lng': -90.23},
        'mexico': {'lat': 23.63, 'lng': -102.55},
        'panama': {'lat': 8.54, 'lng': -80.78},
        'venezuela': {'lat': 6.42, 'lng': -66.58},
        'bolivia': {'lat': -16.29, 'lng': -63.59},
        
        # Africa  
        'madagascar': {'lat': -18.77, 'lng': 46.87},
        'south africa': {'lat': -30.56, 'lng': 22.94},
        'kenya': {'lat': -0.02, 'lng': 37.91},
        'tanzania': {'lat': -6.37, 'lng': 34.89},
        'cameroon': {'lat': 7.37, 'lng': 12.35},
        
        # Oceania
        'australia': {'lat': -25.27, 'lng': 133.78},
        'new zealand': {'lat': -40.90, 'lng': 174.89},
        'new guinea': {'lat': -5.32, 'lng': 141.00},
        'papua new guinea': {'lat': -6.31, 'lng': 143.96},
        
        # Europe
        'mediterranean': {'lat': 40.00, 'lng': 18.00}
    }
    
    # Check region first
    if region:
        region_lower = region.lower()
        for key, coords in region_coordinates.items():
            if key in region_lower:
                return coords
    
    # Check habitat text
    if habitat:
        habitat_lower = habitat.lower()
        for key, coords in region_coordinates.items():
            if key in habitat_lower:
                return coords
    
    return {}

@app.route('/orchid/<int:id>')
def orchid_detail(id):
    """Display detailed orchid information"""
    orchid = OrchidRecord.query.get_or_404(id)
    
    # Increment view count
    orchid.view_count += 1
    db.session.commit()
    
    # Get related orchids (same genus)
    related_orchids = OrchidRecord.query.filter(
        OrchidRecord.genus == orchid.genus,
        OrchidRecord.id != orchid.id,
        OrchidRecord.image_url.isnot(None)
    ).limit(4).all()
    
    return render_template('orchid_detail.html', orchid=orchid, related_orchids=related_orchids)

@app.route('/mission')
def mission():
    """Display mission statement and support information"""
    return render_template('mission.html')

@app.route('/admin')
def admin():
    """Admin interface for batch operations"""
    # Get recent uploads
    recent_uploads = UserUpload.query.order_by(UserUpload.created_at.desc()).limit(10).all()
    
    # Get scraping logs
    recent_scrapes = ScrapingLog.query.order_by(ScrapingLog.created_at.desc()).limit(10).all()
    
    # Get statistics
    stats = {
        'total_orchids': OrchidRecord.query.count(),
        'pending_uploads': UserUpload.query.filter_by(processing_status='pending').count(),
        'validated_orchids': OrchidRecord.query.filter_by(validation_status='validated').count(),
        'featured_orchids': OrchidRecord.query.filter_by(is_featured=True).count()
    }
    
    return render_template('admin.html',
                         recent_uploads=recent_uploads,
                         recent_scrapes=recent_scrapes,
                         stats=stats)

@app.route('/api/scrape/<source>')
def trigger_scrape(source):
    """Trigger scraping for a specific source"""
    try:
        if source == 'gary':
            results = scrape_gary_yong_gee()
        elif source == 'roberta':
            results = scrape_roberta_fox()
        else:
            return jsonify({'error': 'Unknown source'}), 400
        
        return jsonify(results)
    except Exception as e:
        logger.error(f"Scraping error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/validate/<int:orchid_id>', methods=['POST'])
def validate_orchid(orchid_id):
    """Validate an orchid record"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    action = request.json.get('action', 'validate')
    
    if action == 'validate':
        orchid.validation_status = 'validated'
    elif action == 'reject':
        orchid.validation_status = 'rejected'
    elif action == 'feature':
        orchid.is_featured = not orchid.is_featured
    
    db.session.commit()
    return jsonify({'status': 'success'})

@app.route('/api/orchid-of-day')
def api_orchid_of_day():
    """API endpoint for orchid of the day widget"""
    orchid = get_orchid_of_the_day()
    if orchid:
        return jsonify({
            'id': orchid.id,
            'name': orchid.display_name,
            'scientific_name': orchid.scientific_name,
            'description': orchid.ai_description,
            'image_url': orchid.image_url,
            'cultural_notes': orchid.cultural_notes
        })
    return jsonify({'error': 'No orchid found'}), 404

@app.route('/api/orchids-map-data')
def api_orchids_map_data():
    """API endpoint for orchid map data with filtering"""
    try:
        # Get filter parameters
        genus_filter = request.args.get('genus', '').strip()
        climate_filter = request.args.get('climate', '').strip()
        
        # Build query
        query = OrchidRecord.query.filter(
            OrchidRecord.validation_status == 'validated'
        )
        
        # Apply filters
        if genus_filter:
            query = query.filter(OrchidRecord.genus == genus_filter)
        
        if climate_filter:
            query = query.filter(OrchidRecord.climate_preference == climate_filter)
        
        orchids = query.all()
        
        # Convert to map data format
        map_data = []
        for orchid in orchids:
            # Get location data using existing function
            location_data = _get_approximate_location(orchid.region, orchid.native_habitat)
            
            if location_data and 'lat' in location_data and 'lng' in location_data:  # Only include orchids with location data
                map_data.append({
                    'id': orchid.id,
                    'name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'region': orchid.region,
                    'climate': orchid.climate_preference,
                    'growth_habit': orchid.growth_habit,
                    'image_url': orchid.image_url,
                    'lat': location_data.get('lat'),
                    'lng': location_data.get('lng'),
                    'description': orchid.ai_description[:200] + '...' if orchid.ai_description and len(orchid.ai_description) > 200 else orchid.ai_description
                })
        
        return jsonify({
            'orchids': map_data,
            'total': len(map_data)
        })
        
    except Exception as e:
        logger.error(f"Error fetching map data: {str(e)}")
        return jsonify({'error': 'Failed to fetch map data'}), 500

@app.route('/api/orchids-filters')
def api_orchids_filters():
    """API endpoint for available filter options"""
    try:
        # Get unique genera
        genera_query = db.session.query(OrchidRecord.genus).filter(
            OrchidRecord.genus.isnot(None),
            OrchidRecord.validation_status == 'validated'
        ).distinct()
        genera = [g[0] for g in genera_query if g[0]]
        
        # Get unique climate preferences
        climate_query = db.session.query(OrchidRecord.climate_preference).filter(
            OrchidRecord.climate_preference.isnot(None),
            OrchidRecord.validation_status == 'validated'
        ).distinct()
        climates = [c[0] for c in climate_query if c[0]]
        
        # Get unique growth habits
        habit_query = db.session.query(OrchidRecord.growth_habit).filter(
            OrchidRecord.growth_habit.isnot(None),
            OrchidRecord.validation_status == 'validated'
        ).distinct()
        growth_habits = [h[0] for h in habit_query if h[0]]
        
        return jsonify({
            'genera': sorted(genera),
            'climates': sorted(climates),
            'growth_habits': sorted(growth_habits)
        })
        
    except Exception as e:
        logger.error(f"Error fetching filter options: {str(e)}")
        return jsonify({'error': 'Failed to fetch filter options'}), 500

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    """User feedback submission form"""
    if request.method == 'POST':
        try:
            # Get form data
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            feedback_type = request.form.get('feedback_type', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()
            
            # Basic validation
            if not all([name, email, feedback_type, subject, message]):
                flash('Please fill in all required fields.', 'error')
                return render_template('feedback.html')
            
            # Create feedback record
            feedback_record = UserFeedback(
                name=name,
                email=email,
                feedback_type=feedback_type,
                subject=subject,
                message=message,
                page_url=request.referrer or request.url,
                browser_info=request.headers.get('User-Agent', '')
            )
            
            db.session.add(feedback_record)
            db.session.commit()
            
            flash(f'Thank you for your {feedback_type.replace("_", " ")}! We\'ll review it and get back to you if needed.', 'success')
            return redirect(url_for('feedback'))
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            flash('There was an error submitting your feedback. Please try again.', 'error')
            db.session.rollback()
    
    return render_template('feedback.html')

@app.route('/admin/feedback')
def admin_feedback():
    """Admin view for managing feedback"""
    if not current_user.is_authenticated or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    # Get feedback with pagination
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    type_filter = request.args.get('type', 'all')
    
    query = UserFeedback.query
    
    if status_filter != 'all':
        query = query.filter(UserFeedback.status == status_filter)
    
    if type_filter != 'all':
        query = query.filter(UserFeedback.feedback_type == type_filter)
    
    feedback_items = query.order_by(UserFeedback.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get summary statistics
    total_feedback = UserFeedback.query.count()
    new_feedback = UserFeedback.query.filter(UserFeedback.status == 'new').count()
    bug_reports = UserFeedback.query.filter(UserFeedback.feedback_type == 'bug_report').count()
    feature_requests = UserFeedback.query.filter(UserFeedback.feedback_type == 'feature_request').count()
    
    return render_template('admin/feedback.html', 
                         feedback_items=feedback_items,
                         total_feedback=total_feedback,
                         new_feedback=new_feedback,
                         bug_reports=bug_reports,
                         feature_requests=feature_requests,
                         status_filter=status_filter,
                         type_filter=type_filter)

@app.route('/admin/feedback/<int:feedback_id>/update', methods=['POST'])
def update_feedback_status(feedback_id):
    """Update feedback status and admin notes"""
    if not current_user.is_authenticated or not hasattr(current_user, 'is_admin') or not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    feedback_item = UserFeedback.query.get_or_404(feedback_id)
    
    try:
        new_status = request.json.get('status')
        admin_notes = request.json.get('admin_notes', '')
        
        if new_status:
            feedback_item.status = new_status
        
        if admin_notes:
            feedback_item.admin_notes = admin_notes
        
        feedback_item.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Feedback updated successfully'})
        
    except Exception as e:
        logger.error(f"Error updating feedback: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Failed to update feedback'}), 500

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
