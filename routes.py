from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import (OrchidRecord, OrchidTaxonomy, UserUpload, ScrapingLog, WidgetConfig, 
                   User, JudgingAnalysis, Certificate, BatchUpload)
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
import os
import json
import logging
from datetime import datetime
from sqlalchemy import or_, func
from io import BytesIO

logger = logging.getLogger(__name__)

# Register processing blueprint
app.register_blueprint(processing_bp)

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

@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
