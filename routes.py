from flask import render_template, request, jsonify, flash, redirect, url_for, send_file, session, Response
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import app, db
from models import (OrchidRecord, OrchidTaxonomy, UserUpload, ScrapingLog, WidgetConfig, 
                   User, JudgingAnalysis, Certificate, BatchUpload, UserFeedback, WeatherData, UserLocation, WeatherAlert)
from orchid_ai import analyze_orchid_image, get_weather_based_care_advice, extract_metadata_from_text
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
from weather_service import WeatherService, get_coordinates_from_location
from orchid_atlas import atlas_bp
from darwin_core_exporter import DarwinCoreExporter
from weather_habitat_routes import register_weather_habitat_routes
from scraping_dashboard import scraping_dashboard
from vigilant_monitor import vigilant_monitor
import os
import json
import logging
import requests
from datetime import datetime, timedelta
from sqlalchemy import or_, func, and_
from io import BytesIO
from googleapiclient.http import MediaIoBaseDownload

logger = logging.getLogger(__name__)

# Register the Atlas blueprint
app.register_blueprint(atlas_bp)

# Register weather habitat comparison routes
register_weather_habitat_routes(app)

@app.route('/test_gary_scraper')
def test_gary_scraper():
    """Test Gary Yong Gee scraper with limited scope"""
    try:
        from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
        
        scraper = ComprehensiveOrchidScraper()
        
        # Test with just one genus for verification
        print("🧪 Testing Gary Yong Gee scraper with single genus...")
        test_url = "https://orchids.yonggee.name/genera/aa"
        
        genus_results = scraper.scrape_gary_genus_page(test_url, "aa")
        
        db.session.commit()
        
        return f"""
        <h2>Gary Yong Gee Scraper Test Results</h2>
        <p><strong>Test URL:</strong> {test_url}</p>
        <p><strong>Processed:</strong> {genus_results['processed']}</p>
        <p><strong>Errors:</strong> {genus_results['errors']}</p>
        <p><strong>Skipped:</strong> {genus_results['skipped']}</p>
        <p><a href="/admin">Back to Admin</a></p>
        """
        
    except Exception as e:
        return f"<h2>Test Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/analyze_all_photos')
def analyze_all_photos():
    """Analyze all orchid photos for names and metadata"""
    try:
        from photo_analysis_system import PhotoAnalysisSystem
        
        analyzer = PhotoAnalysisSystem()
        
        print("🔍 Starting comprehensive photo analysis...")
        results = analyzer.run_comprehensive_analysis()
        
        db.session.commit()
        
        return f"""
        <h2>🔍 Photo Analysis Results</h2>
        <p><strong>Photos Analyzed:</strong> {results['analyzed']}</p>
        <p><strong>Names Improved:</strong> {results['improved_names']}</p>
        <p><strong>Metadata Extracted:</strong> {results['extracted_metadata']}</p>
        <p><strong>AI Analyzed:</strong> {results['ai_analyzed']}</p>
        <p><strong>Errors:</strong> {results['errors']}</p>
        <p><strong>Analysis:</strong> Filename parsing, AI vision, EXIF extraction</p>
        <p><a href="/admin">Back to Admin</a></p>
        """
        
    except Exception as e:
        return f"<h2>Analysis Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/test_international_scrapers')
def test_international_scrapers():
    """Test comprehensive international orchid scrapers"""
    try:
        from international_orchid_scraper import InternationalOrchidScraper
        
        scraper = InternationalOrchidScraper()
        
        print("🌍 Testing international orchid scrapers...")
        results = scraper.run_comprehensive_international_collection()
        
        db.session.commit()
        
        return f"""
        <h2>🌍 International Orchid Collection Results</h2>
        <p><strong>Total Processed:</strong> {results['total_processed']}</p>
        <p><strong>New Countries:</strong> {len(results['new_countries'])}</p>
        <p><strong>New Genera:</strong> {len(results['new_genera'])}</p>
        <p><strong>Errors:</strong> {results['errors']}</p>
        <p><strong>Sources:</strong> Internet Orchid Species, Singapore Botanic, Australian, European, South American</p>
        <p><a href="/admin">Back to Admin</a></p>
        """
        
    except Exception as e:
        return f"<h2>International Test Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/test_ron_parsons')
def test_ron_parsons():
    """Test Ron Parsons Flickr scraper"""
    try:
        from ron_parsons_scraper import RonParsonsOrchidScraper
        
        scraper = RonParsonsOrchidScraper()
        
        print("🌸 Testing Ron Parsons scraper...")
        results = scraper.scrape_flickr_photostream()
        
        db.session.commit()
        
        return f"""
        <h2>🌸 Ron Parsons Scraper Test Results</h2>
        <p><strong>Target:</strong> 118,952+ photos from world's leading orchid photographer</p>
        <p><strong>Processed:</strong> {results['processed']}</p>
        <p><strong>Errors:</strong> {results['errors']}</p>
        <p><strong>Skipped:</strong> {results['skipped']}</p>
        <p><strong>Source:</strong> Flickr photostream</p>
        <p><a href="/admin">Back to Admin</a></p>
        """
        
    except Exception as e:
        return f"<h2>Test Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/test_iospe')
def test_iospe():
    """Test IOSPE scraper"""
    try:
        from comprehensive_orchid_scraper import ComprehensiveOrchidScraper
        
        scraper = ComprehensiveOrchidScraper()
        
        print("🌍 Testing IOSPE scraper...")
        results = scraper.scrape_iospe_comprehensive()
        
        db.session.commit()
        
        return f"""
        <h2>🌍 IOSPE Scraper Test Results</h2>
        <p><strong>Target:</strong> 25,996+ species from world's largest orchid database</p>
        <p><strong>Processed:</strong> {results['processed']}</p>
        <p><strong>Errors:</strong> {results['errors']}</p>
        <p><strong>Skipped:</strong> {results['skipped']}</p>
        <p><strong>Source:</strong> orchidspecies.com</p>
        <p><a href="/admin">Back to Admin</a></p>
        """
        
    except Exception as e:
        return f"<h2>Test Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/test_filename_parser')
def test_filename_parser():
    """Test enhanced filename parser"""
    try:
        from filename_parser import parse_orchid_filename, analyze_filename_for_orchid_name
        
        # Test filenames
        test_files = [
            "Cattleya_warscewiczii_alba.jpg",
            "phal_amabilis_var_rosenstromii.jpg", 
            "Dendrobium-nobile-cooksonii.JPG",
            "Ron_Parsons_Masdevallia_veitchiana_2024.jpg",
            "DSC_Oncidium_sphacelatum_Ecuador.jpg"
        ]
        
        results = []
        for filename in test_files:
            parsed = parse_orchid_filename(filename)
            analysis = analyze_filename_for_orchid_name(filename)
            
            results.append({
                'filename': filename,
                'parsed': parsed,
                'analysis': analysis
            })
        
        html = "<h2>🧠 Filename Parser Test Results</h2>"
        for result in results:
            html += f"""
            <div style="border: 1px solid #ccc; margin: 10px; padding: 10px;">
                <h3>{result['filename']}</h3>
                <p><strong>Genus:</strong> {result['parsed'].get('genus', 'None')}</p>
                <p><strong>Species:</strong> {result['parsed'].get('species', 'None')}</p>
                <p><strong>Full Name:</strong> {result['analysis'].get('full_parsed_name', 'None')}</p>
                <p><strong>Confidence:</strong> {result['analysis'].get('confidence', 0.0):.2f}</p>
                <p><strong>Method:</strong> {result['analysis'].get('parsing_method', 'None')}</p>
            </div>
            """
        
        html += '<p><a href="/admin">Back to Admin</a></p>'
        return html
        
    except Exception as e:
        return f"<h2>Test Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

# Register blueprints
app.register_blueprint(processing_bp)
app.register_blueprint(photo_editor_bp)

# Register advanced gallery system
from advanced_gallery_routes import advanced_gallery_bp
app.register_blueprint(advanced_gallery_bp, url_prefix='/advanced_gallery')

# Start the orchid record scheduler
from scheduler import start_orchid_scheduler, get_scheduler_status
start_orchid_scheduler()

@app.route('/admin/scheduler-status')
def scheduler_status():
    """Display scheduler status and controls"""
    try:
        status = get_scheduler_status()
        return render_template('admin/scheduler_status.html', status=status)
    except Exception as e:
        return f"<h2>Scheduler Status Error</h2><p>{str(e)}</p><p><a href='/admin'>Back to Admin</a></p>"

@app.route('/stats')
def detailed_statistics():
    """Detailed statistics page showing comprehensive orchid collection data"""
    try:
        from orchid_statistics import get_homepage_statistics, get_genus_statistics
        
        # Get comprehensive statistics
        stats = get_homepage_statistics()
        genus_stats = get_genus_statistics()
        
        return render_template('detailed_statistics.html', stats=stats, genus_stats=genus_stats)
        
    except Exception as e:
        logger.error(f"Error loading detailed statistics: {e}")
        return render_template('error.html', error="Could not load statistics system"), 500

@app.route('/stats/genus/<genus>')
def genus_detail_stats(genus):
    """Show detailed statistics for a specific genus"""
    try:
        from orchid_statistics import orchid_stats
        
        # Get genus-specific details
        genus_details = orchid_stats.get_genus_details(genus)
        
        # Get orchids in this genus for display
        orchids = OrchidRecord.query.filter(
            func.lower(OrchidRecord.genus) == genus.lower()
        ).limit(50).all()
        
        return render_template('genus_statistics.html', 
                             genus_details=genus_details, 
                             orchids=orchids)
        
    except Exception as e:
        logger.error(f"Error loading genus statistics for {genus}: {e}")
        return render_template('error.html', error=f"Could not load statistics for genus {genus}"), 500

@app.route('/phenotype-analysis')
def phenotype_analysis():
    """Phenotypic variation analysis page"""
    try:
        from phenotype_analyzer import get_analyzable_species
        
        # Get species with multiple specimens for analysis
        species_list = get_analyzable_species(min_specimens=3)
        
        return render_template('phenotype_analysis.html', species_list=species_list)
        
    except Exception as e:
        logger.error(f"Error loading phenotype analysis page: {e}")
        return render_template('error.html', error="Could not load phenotypic analysis system"), 500

@app.route('/api/analyze-phenotype', methods=['POST'])
def api_analyze_phenotype():
    """API endpoint for phenotypic variation analysis"""
    try:
        data = request.get_json()
        genus = data.get('genus')
        species = data.get('species')
        
        if not genus or not species:
            return jsonify({'error': 'Genus and species are required'}), 400
        
        # Import and run analysis
        from phenotype_analyzer import analyze_species_variations
        
        logger.info(f"Starting phenotypic analysis for {genus} {species}")
        analysis = analyze_species_variations(genus, species)
        
        if not analysis:
            return jsonify({'error': 'Analysis failed or insufficient data'}), 400
        
        # Get specimens for display
        specimens = OrchidRecord.query.filter(
            func.lower(OrchidRecord.genus) == genus.lower(),
            func.lower(OrchidRecord.species) == species.lower(),
            OrchidRecord.google_drive_id.isnot(None)
        ).limit(20).all()
        
        # Format response
        response = {
            'genus': analysis.genus,
            'species': analysis.species,
            'total_specimens': analysis.total_specimens,
            'research_notes': analysis.research_notes,
            'specimens': [
                {
                    'id': s.id,
                    'display_name': s.display_name,
                    'google_drive_id': s.google_drive_id,
                    'country': s.country,
                    'region': s.region
                } for s in specimens
            ],
            'variations': [
                {
                    'trait_name': v.trait_name,
                    'variation_type': v.variation_type,
                    'description': v.description,
                    'confidence': v.confidence,
                    'specimens_affected': v.specimens_affected
                } for v in analysis.variations
            ],
            'morphological_summary': analysis.morphological_summary,
            'mutation_indicators': analysis.mutation_indicators,
            'adaptation_patterns': analysis.adaptation_patterns
        }
        
        logger.info(f"Phenotypic analysis completed: {len(analysis.variations)} variations found")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in phenotypic analysis API: {e}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/')
def index():
    """Homepage with enhanced orchid of the day and advanced features"""
    try:
        # Get enhanced orchid of the day
        from enhanced_orchid_of_day import EnhancedOrchidOfDay
        enhanced_system = EnhancedOrchidOfDay()
        orchid_of_day_enhanced = enhanced_system.get_enhanced_orchid_of_day()
        
        # Fallback to basic orchid of day if enhanced fails
        orchid_of_day = orchid_of_day_enhanced['orchid'] if orchid_of_day_enhanced else get_orchid_of_the_day()
        
        # Get recent uploads with error handling
        recent_orchids = []
        try:
            recent_orchids = OrchidRecord.query.filter(
                or_(
                    OrchidRecord.google_drive_id.isnot(None),
                    and_(
                        OrchidRecord.image_url.isnot(None),
                        OrchidRecord.image_url != '/static/images/orchid_placeholder.svg'
                    )
                )
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
        
        # Get comprehensive statistics
        stats = {}
        try:
            from orchid_statistics import get_homepage_statistics
            stats = get_homepage_statistics()
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            # Get live counts as fallback
            try:
                total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar()
                total_genera = db.session.query(func.count(func.distinct(OrchidRecord.genus))).filter(OrchidRecord.genus.isnot(None)).scalar()
                photos_count = db.session.query(func.count(OrchidRecord.id)).filter(
                    OrchidRecord.image_url.isnot(None),
                    OrchidRecord.image_url != '',
                    ~OrchidRecord.image_url.like('%placeholder%')
                ).scalar()
                stats = {
                    'total_orchids': total_orchids or 4164,
                    'total_genera': total_genera or 396, 
                    'total_species': 2053,
                    'photos_available': photos_count or 1337,
                    'genus_breakdown': []
                }
            except:
                stats = {
                    'total_orchids': 4164,
                    'total_genera': 396,
                    'total_species': 2053,
                    'photos_available': 1337,
                    'genus_breakdown': []
                }
        
        return render_template('index.html',
                             orchid_of_day=orchid_of_day,
                             orchid_of_day_enhanced=orchid_of_day_enhanced,
                             recent_orchids=recent_orchids,
                             featured_orchids=featured_orchids,
                             stats=stats)
    
    except Exception as e:
        logger.error(f"Homepage error: {str(e)}")
        db.session.rollback()
        # Return minimal homepage on error with live counts if possible
        try:
            total_orchids = db.session.query(func.count(OrchidRecord.id)).scalar()
            photos_count = db.session.query(func.count(OrchidRecord.id)).filter(
                OrchidRecord.image_url.isnot(None),
                OrchidRecord.image_url != '',
                ~OrchidRecord.image_url.like('%placeholder%')
            ).scalar()
            fallback_stats = {
                'total_orchids': total_orchids or 4164,
                'total_genera': 396,
                'total_species': 2053,
                'photos_available': photos_count or 1337,
                'genus_breakdown': []
            }
        except:
            fallback_stats = {
                'total_orchids': 4164,
                'total_genera': 396,
                'total_species': 2053,
                'photos_available': 1337,
                'genus_breakdown': []
            }
        return render_template('index.html',
                             orchid_of_day=None,
                             orchid_of_day_enhanced=None,
                             recent_orchids=[],
                             featured_orchids=[],
                             stats=fallback_stats)

@app.route('/api/baker-extrapolation/analyze')
def analyze_baker_extrapolation():
    """API endpoint to analyze Baker culture extrapolation opportunities"""
    try:
        from baker_extrapolation_system import baker_extrapolation
        
        report = baker_extrapolation.generate_extrapolation_report()
        return jsonify({
            'success': True,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in Baker extrapolation analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/baker-extrapolation/batch-genus/<genus_name>')
def batch_extrapolate_genus(genus_name):
    """API endpoint to batch extrapolate culture data for a genus"""
    try:
        from baker_extrapolation_system import baker_extrapolation
        
        limit = request.args.get('limit', 50, type=int)
        results = baker_extrapolation.batch_extrapolate_genus(genus_name, limit)
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in batch genus extrapolation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/baker-extrapolation/by-climate/<climate>')
def extrapolate_by_climate(climate):
    """API endpoint to extrapolate by climate preference"""
    try:
        from baker_extrapolation_system import baker_extrapolation
        
        limit = request.args.get('limit', 100, type=int)
        results = baker_extrapolation.extrapolate_by_climate(climate, limit)
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in climate extrapolation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/baker-extrapolation/regional-analysis')
def regional_extrapolation_analysis():
    """API endpoint for endemic region extrapolation analysis"""
    try:
        from endemic_region_extrapolator import endemic_extrapolator
        
        report = endemic_extrapolator.generate_regional_extrapolation_report()
        return jsonify({
            'success': True,
            'report': report,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in regional analysis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/baker-extrapolation/by-region/<region>')
def extrapolate_by_region(region):
    """API endpoint to extrapolate by endemic region"""
    try:
        from endemic_region_extrapolator import endemic_extrapolator
        
        limit = request.args.get('limit', 50, type=int)
        results = endemic_extrapolator.batch_extrapolate_region(region, limit)
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in regional extrapolation: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/baker-weather-advice', methods=['POST'])
def baker_weather_advice():
    """API endpoint for AI-powered Baker culture weather advice"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        weather_data = data.get('weather', {})
        forecast_data = data.get('forecast', [])
        
        if not orchid_id:
            return jsonify({'success': False, 'error': 'Orchid ID required'})
        
        # Get orchid record
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return jsonify({'success': False, 'error': 'Orchid not found'})
        
        # Generate AI advice using Baker culture data (including extrapolated)
        from orchid_ai import extrapolate_baker_culture_data
        
        # Try direct Baker advice first, then extrapolated
        advice = get_weather_based_care_advice(orchid, weather_data, forecast_data)
        
        # If no direct advice, try extrapolation
        if not advice:
            extrapolated_data = extrapolate_baker_culture_data(orchid)
            if extrapolated_data:
                # Generate weather advice based on extrapolated data
                temp_orchid = orchid
                temp_orchid.cultural_notes = f"EXTRAPOLATED BAKER DATA: {json.dumps(extrapolated_data)}"
                advice = get_weather_based_care_advice(temp_orchid, weather_data, forecast_data)
        
        if advice:
            return jsonify({
                'success': True,
                'advice': advice,
                'has_baker_data': bool(orchid.cultural_notes and 'BAKER' in orchid.cultural_notes)
            })
        else:
            return jsonify({
                'success': True,
                'advice': 'Monitor temperature and humidity. Adjust watering based on conditions.',
                'has_baker_data': False
            })
        
    except Exception as e:
        logger.error(f"Error generating Baker weather advice: {str(e)}")
        return jsonify({'success': False, 'error': 'Unable to generate advice'})

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

@app.route('/api/live-stats')
def api_live_statistics():
    """API endpoint for real-time live statistics with auto-update support"""
    try:
        from orchid_statistics import get_homepage_statistics
        from datetime import datetime
        
        stats = get_homepage_statistics()
        
        # Add auto-update metadata
        stats['last_updated'] = datetime.now().strftime('%H:%M:%S')
        stats['timestamp'] = datetime.now().isoformat()
        
        # Force refresh from database for most current counts
        current_count = db.session.query(func.count(OrchidRecord.id)).scalar()
        photos_count = db.session.query(func.count(OrchidRecord.id)).filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).scalar()
        
        # Override with live counts
        stats['total_orchids'] = current_count or stats.get('total_orchids', 4164)
        stats['photos_available'] = photos_count or stats.get('photos_available', 1337)
        
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Error loading live statistics: {e}")
        return jsonify({
            'total_orchids': 4164,
            'total_genera': 396,
            'total_species': 2053,
            'photos_available': 1337,
            'last_updated': 'Error',
            'error': 'Statistics temporarily unavailable'
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

@app.route('/admin/baker-extrapolation')
def admin_baker_extrapolation():
    """Admin interface for Baker culture extrapolation system"""
    return render_template('admin/baker_extrapolation.html')

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

@app.route('/weather')
def weather_dashboard():
    """Weather dashboard for orchid growing conditions"""
    try:
        # Get user locations
        locations = UserLocation.query.filter_by(track_weather=True).all()
        
        # Get recent weather data
        recent_weather = WeatherData.query.filter(
            WeatherData.recorded_at >= datetime.utcnow() - timedelta(days=7),
            WeatherData.is_forecast == False
        ).order_by(WeatherData.recorded_at.desc()).limit(50).all()
        
        # Get active weather alerts
        active_alerts = WeatherAlert.query.filter(
            WeatherAlert.is_active == True,
            WeatherAlert.expires_at > datetime.utcnow()
        ).order_by(WeatherAlert.triggered_at.desc()).all()
        
        # Get forecast data
        forecast_data = WeatherData.query.filter(
            WeatherData.is_forecast == True,
            WeatherData.recorded_at >= datetime.utcnow()
        ).order_by(WeatherData.recorded_at.asc()).limit(14).all()
        
        return render_template('weather/dashboard.html',
                             locations=locations,
                             recent_weather=recent_weather,
                             active_alerts=active_alerts,
                             forecast_data=forecast_data)
        
    except Exception as e:
        logger.error(f"Error loading weather dashboard: {str(e)}")
        flash('Error loading weather dashboard', 'error')
        return redirect(url_for('index'))

@app.route('/weather/location/add', methods=['GET', 'POST'])
def add_weather_location():
    """Add a new weather tracking location"""
    if request.method == 'POST':
        try:
            data = request.get_json() if request.is_json else request.form
            
            location_name = data.get('name')
            city = data.get('city')
            state_province = data.get('state_province', '')
            country = data.get('country', '')
            growing_type = data.get('growing_type', 'outdoor')
            
            # Try to get coordinates
            full_location = f"{city}, {state_province}, {country}".strip(', ')
            coordinates = get_coordinates_from_location(full_location)
            
            if not coordinates:
                return jsonify({'error': 'Could not find coordinates for this location'}), 400
            
            latitude, longitude = coordinates
            
            # Create new location
            location = UserLocation(
                name=location_name,
                city=city,
                state_province=state_province,
                country=country,
                latitude=latitude,
                longitude=longitude,
                growing_type=growing_type,
                track_weather=True
            )
            
            db.session.add(location)
            db.session.commit()
            
            # Fetch initial weather data
            WeatherService.get_current_weather(latitude, longitude, location_name)
            
            if request.is_json:
                return jsonify({'success': True, 'location_id': location.id})
            else:
                flash(f'Added weather tracking for {location_name}', 'success')
                return redirect(url_for('weather_dashboard'))
                
        except Exception as e:
            logger.error(f"Error adding weather location: {str(e)}")
            if request.is_json:
                return jsonify({'error': str(e)}), 500
            else:
                flash('Error adding location', 'error')
                return redirect(url_for('weather_dashboard'))
    
    return render_template('weather/add_location.html')

@app.route('/weather/current/<int:location_id>')
def get_current_weather(location_id):
    """Get current weather for a specific location"""
    try:
        location = UserLocation.query.get_or_404(location_id)
        
        # Fetch fresh weather data
        weather = WeatherService.get_current_weather(
            location.latitude, 
            location.longitude, 
            location.name
        )
        
        if not weather:
            return jsonify({'error': 'Could not fetch weather data'}), 500
        
        # Check for alerts
        alerts = WeatherService.check_orchid_weather_alerts(location)
        
        # Get growing conditions summary
        conditions = WeatherService.get_growing_conditions_summary(location, 7)
        
        return jsonify({
            'weather': {
                'temperature': weather.temperature,
                'humidity': weather.humidity,
                'pressure': weather.pressure,
                'wind_speed': weather.wind_speed,
                'description': weather.description,
                'vpd': weather.vpd,
                'orchid_friendly': weather.is_orchid_friendly(),
                'recorded_at': weather.recorded_at.isoformat()
            },
            'alerts': [
                {
                    'type': alert.alert_type,
                    'severity': alert.severity,
                    'title': alert.title,
                    'message': alert.message,
                    'advice': alert.orchid_care_advice
                } for alert in alerts
            ],
            'conditions': conditions
        })
        
    except Exception as e:
        logger.error(f"Error fetching current weather: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather/historical/<int:location_id>')
def get_historical_weather(location_id):
    """Get historical weather data for analysis"""
    try:
        location = UserLocation.query.get_or_404(location_id)
        days = request.args.get('days', 30, type=int)
        
        # Get existing historical data
        existing_data = WeatherData.query.filter(
            WeatherData.latitude == location.latitude,
            WeatherData.longitude == location.longitude,
            WeatherData.recorded_at >= datetime.utcnow() - timedelta(days=days),
            WeatherData.is_forecast == False
        ).order_by(WeatherData.recorded_at.desc()).all()
        
        # If we have less than expected, fetch more
        if len(existing_data) < days * 0.8:  # Allow for some missing days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            new_data = WeatherService.get_historical_weather(
                location.latitude,
                location.longitude,
                start_date,
                end_date,
                location.name
            )
            
            # Refresh query after fetching new data
            existing_data = WeatherData.query.filter(
                WeatherData.latitude == location.latitude,
                WeatherData.longitude == location.longitude,
                WeatherData.recorded_at >= start_date,
                WeatherData.is_forecast == False
            ).order_by(WeatherData.recorded_at.desc()).all()
        
        # Format data for charts
        chart_data = []
        for weather in existing_data:
            chart_data.append({
                'date': weather.recorded_at.strftime('%Y-%m-%d'),
                'temperature': weather.temperature,
                'temperature_min': weather.temperature_min,
                'temperature_max': weather.temperature_max,
                'humidity': weather.humidity,
                'precipitation': weather.precipitation,
                'vpd': weather.vpd,
                'orchid_friendly': weather.is_orchid_friendly()
            })
        
        return jsonify({
            'data': chart_data,
            'summary': WeatherService.get_growing_conditions_summary(location, days)
        })
        
    except Exception as e:
        logger.error(f"Error fetching historical weather: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather/forecast/<int:location_id>')
def get_weather_forecast(location_id):
    """Get weather forecast for planning"""
    try:
        location = UserLocation.query.get_or_404(location_id)
        days = request.args.get('days', 7, type=int)
        
        # Fetch fresh forecast
        forecast = WeatherService.get_weather_forecast(
            location.latitude,
            location.longitude,
            days,
            location.name
        )
        
        forecast_data = []
        for weather in forecast:
            forecast_data.append({
                'date': weather.recorded_at.strftime('%Y-%m-%d'),
                'temperature_min': weather.temperature_min,
                'temperature_max': weather.temperature_max,
                'humidity': weather.humidity,
                'precipitation': weather.precipitation,
                'description': weather.description,
                'weather_code': weather.weather_code,
                'orchid_friendly': weather.is_orchid_friendly()
            })
        
        return jsonify({'forecast': forecast_data})
        
    except Exception as e:
        logger.error(f"Error fetching weather forecast: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/weather/alerts')
def weather_alerts():
    """Display weather alerts for orchid care"""
    try:
        # Get all active alerts
        alerts = WeatherAlert.query.filter(
            WeatherAlert.is_active == True,
            WeatherAlert.expires_at > datetime.utcnow()
        ).order_by(WeatherAlert.severity.desc(), WeatherAlert.triggered_at.desc()).all()
        
        return render_template('weather/alerts.html', alerts=alerts)
        
    except Exception as e:
        logger.error(f"Error loading weather alerts: {str(e)}")
        flash('Error loading weather alerts', 'error')
        return redirect(url_for('weather_dashboard'))

@app.route('/weather/alert/<int:alert_id>/acknowledge', methods=['POST'])
def acknowledge_alert(alert_id):
    """Acknowledge a weather alert"""
    try:
        alert = WeatherAlert.query.get_or_404(alert_id)
        alert.is_acknowledged = True
        alert.acknowledged_at = datetime.utcnow()
        
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True})
        else:
            flash('Alert acknowledged', 'success')
            return redirect(url_for('weather_alerts'))
            
    except Exception as e:
        logger.error(f"Error acknowledging alert: {str(e)}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash('Error acknowledging alert', 'error')
            return redirect(url_for('weather_alerts'))

@app.route('/weather/orchid-correlation')
def weather_orchid_correlation():
    """Analyze correlation between weather and orchid performance"""
    try:
        # Get orchids with recent activity or photos
        recent_orchids = OrchidRecord.query.filter(
            OrchidRecord.created_at >= datetime.utcnow() - timedelta(days=90)
        ).all()
        
        # Get weather data for the same period
        recent_weather = WeatherData.query.filter(
            WeatherData.recorded_at >= datetime.utcnow() - timedelta(days=90),
            WeatherData.is_forecast == False
        ).all()
        
        # Group weather by location
        weather_by_location = {}
        for weather in recent_weather:
            key = f"{weather.latitude},{weather.longitude}"
            if key not in weather_by_location:
                weather_by_location[key] = []
            weather_by_location[key].append(weather)
        
        # Analyze correlations
        correlations = {
            'temperature_trends': [],
            'humidity_patterns': [],
            'vpd_analysis': [],
            'orchid_friendly_days': 0,
            'recommendations': []
        }
        
        # Calculate orchid-friendly days
        orchid_friendly_count = sum(1 for w in recent_weather if w.is_orchid_friendly())
        correlations['orchid_friendly_days'] = orchid_friendly_count
        
        # Add basic recommendations
        if recent_weather:
            avg_temp = sum(w.temperature for w in recent_weather if w.temperature) / len([w for w in recent_weather if w.temperature])
            avg_humidity = sum(w.humidity for w in recent_weather if w.humidity) / len([w for w in recent_weather if w.humidity])
            
            if avg_temp < 18:
                correlations['recommendations'].append("Temperatures below optimal range - consider supplemental heating")
            if avg_humidity < 50:
                correlations['recommendations'].append("Humidity below optimal range - increase humidity for better orchid health")
        
        return render_template('weather/correlation.html',
                             recent_orchids=recent_orchids,
                             weather_data=recent_weather,
                             correlations=correlations)
        
    except Exception as e:
        logger.error(f"Error analyzing weather-orchid correlation: {str(e)}")
        flash('Error analyzing correlations', 'error')
        return redirect(url_for('weather_dashboard'))

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

@app.route('/admin/data-import')
def admin_data_import():
    """Data import management interface"""
    # Get database statistics
    stats = {}
    try:
        stats['total_orchids'] = db.session.query(func.count(OrchidRecord.id)).scalar() or 0
        stats['validated_orchids'] = db.session.query(func.count(OrchidRecord.id)).filter_by(validation_status='validated').scalar() or 0
        
        # Data source breakdown
        stats['by_source'] = {}
        sources = ['upload', 'scrape_gary', 'scrape_roberta', 'legacy', 'drive_import']
        for source in sources:
            count = db.session.query(func.count(OrchidRecord.id)).filter_by(ingestion_source=source).scalar() or 0
            stats['by_source'][source] = count
            
    except Exception as e:
        logger.error(f"Error fetching data import stats: {str(e)}")
        db.session.rollback()
        stats = {
            'total_orchids': 0,
            'validated_orchids': 0,
            'by_source': {}
        }
    
    return render_template('admin_data_import.html', stats=stats)

@app.route('/admin/run-scraping', methods=['POST'])
def admin_run_scraping():
    """Trigger web scraping to collect orchid data"""
    try:
        data = request.get_json()
        source = data.get('source', 'all')
        
        results = {'success': True, 'new_records': 0, 'errors': 0}
        
        # Import and run scrapers
        try:
            from web_scraper import scrape_gary_yong_gee, scrape_roberta_fox
            
            if source in ['all', 'gary']:
                gary_results = scrape_gary_yong_gee()
                results['new_records'] += gary_results.get('processed', 0)
                results['errors'] += gary_results.get('errors', 0)
                
            if source in ['all', 'roberta']:
                roberta_results = scrape_roberta_fox()
                results['new_records'] += roberta_results.get('processed', 0)
                results['errors'] += roberta_results.get('errors', 0)
                
        except ImportError as e:
            return jsonify({'success': False, 'error': f'Scraping modules not available: {e}'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': f'Scraping failed: {e}'}), 500
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Error running scraping: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/drive-photo/<file_id>')
def get_drive_photo(file_id):
    """Proxy Google Drive photos for display - PRODUCTION READY"""
    try:
        # Construct Google Drive image URL
        drive_url = f'https://drive.google.com/uc?export=view&id={file_id}'
        
        # Get the image with optimized settings
        response = requests.get(drive_url, timeout=15, stream=True)
        if response.status_code == 200:
            # Add caching headers for better performance
            headers = {
                'Content-Type': response.headers.get('Content-Type', 'image/jpeg'),
                'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                'ETag': f'drive-{file_id}',
                'X-Image-Source': 'Google Drive'
            }
            return response.content, 200, headers
        else:
            # Return placeholder if image not accessible
            logger.warning(f"Drive photo {file_id} returned {response.status_code}")
            return redirect('/static/images/orchid_placeholder.svg')
            
    except requests.Timeout:
        logger.warning(f"Drive photo {file_id} timed out - serving placeholder")
        return redirect('/static/images/orchid_placeholder.svg')
    except Exception as e:
        logger.error(f"Error loading Drive photo {file_id}: {e}")
        return redirect('/static/images/orchid_placeholder.svg')

@app.route('/admin/import-sheets-data', methods=['POST'])
def admin_import_sheets_data():
    """Import data from Five Cities Orchid Society Google Sheets"""
    try:
        from google_sheets_importer import GoogleSheetsImporter
        
        sheet_id = '1103vQ_D00Qio5W7PllFeRaFoFAzr7jd8ivOo79sdfgs'
        importer = GoogleSheetsImporter(sheet_id)
        
        # Import limited records for testing
        result = importer.import_all_records(max_records=100)
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error importing sheets data: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Register AI widget builder blueprint  
try:
    from ai_widget_builder import ai_widget_bp
    app.register_blueprint(ai_widget_bp)
    logger.info("AI Widget Builder registered successfully")
except ImportError as e:
    logger.warning(f"AI Widget Builder not available: {e}")

# Register media migration system
try:
    from media_migration_system import migration_bp
    app.register_blueprint(migration_bp)
    logger.info("Media Migration System registered successfully")
except ImportError as e:
    logger.warning(f"Media Migration System not available: {e}")

# ============================================================================
# FCOS PAGES ROUTES - Structured content from Five Cities Orchid Society
# ============================================================================

@app.route('/fcos/top-10-orchid-tips')
def fcos_top_10_tips():
    """Top 10 orchid growing tips from FCOS experts"""
    return render_template('fcos_pages/top_10_orchid_tips.html')

@app.route('/fcos/guest-information')
def fcos_guest_info():
    """Information for visitors and newcomers to FCOS"""
    return render_template('fcos_pages/guest_information.html')

@app.route('/fcos/orchid-fest-2025')
def fcos_orchid_fest():
    """Complete OrchidFest 2025 event information"""
    return render_template('fcos_pages/orchid_fest_2025.html')

@app.route('/fcos/member-benefits')
def fcos_member_benefits():
    """Benefits of FCOS membership"""
    return render_template('fcos_pages/member_benefits.html')

@app.route('/fcos/how-to-join')
def fcos_how_to_join():
    """How to join Five Cities Orchid Society"""
    return render_template('fcos_pages/how_to_join.html')

@app.route('/orchid-maps')
def orchid_maps():
    """Interactive orchid mapping system with topological data"""
    return render_template('orchid_maps.html')

@app.route('/api/orchid-map-data')
def api_orchid_map_data():
    """API endpoint for orchid mapping data"""
    try:
        from orchid_mapping_system import get_orchid_map_html
        map_html = get_orchid_map_html()
        return jsonify({'map_html': map_html, 'success': True})
    except Exception as e:
        logger.error(f"Error generating orchid map: {e}")
        return jsonify({'error': str(e), 'success': False}), 500

@app.route('/thematic-maps')
def thematic_maps():
    """Thematic orchid distribution maps"""
    return render_template('thematic_maps.html')

@app.route('/fcos/additional-information')
def fcos_additional_info():
    """Additional comprehensive FCOS information"""
    return render_template('fcos_pages/additional_fcos_information.html')

@app.route('/fcos/merchandise')
def fcos_merchandise():
    """FCOS merchandise store and products"""
    return render_template('fcos_pages/fcos_merchandise.html')

# FCOS main redirect for convenience
@app.route('/fcos')
def fcos_main():
    """Main FCOS page redirects to additional information"""
    return redirect(url_for('fcos_additional_info'))

# ============================================================================
# DARWIN CORE EXPORT ROUTES - GBIF Integration
# ============================================================================

@app.route('/export/darwin_core')
def export_darwin_core():
    """Export orchid data as Darwin Core Archive for GBIF publishing"""
    try:
        logger.info("Starting Darwin Core Archive export...")
        
        exporter = DarwinCoreExporter()
        archive_file = exporter.export_to_dwc_archive()
        
        # Generate download filename with timestamp
        download_name = f'orchid_atlas_dwc_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip'
        
        logger.info(f"Darwin Core Archive ready for download: {download_name}")
        
        return send_file(
            archive_file,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/zip'
        )
        
    except Exception as e:
        logger.error(f"Error creating Darwin Core Archive: {e}")
        flash('Error creating Darwin Core export. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/export/darwin_core/preview')
def preview_darwin_core():
    """Preview Darwin Core mapping without downloading"""
    try:
        exporter = DarwinCoreExporter()
        
        # Get sample records for preview
        sample_records = OrchidRecord.query.limit(5).all()
        mapped_samples = []
        
        for record in sample_records:
            mapped_record = exporter.map_orchid_to_dwc(record)
            mapped_samples.append({
                'original': {
                    'id': record.id,
                    'display_name': record.display_name,
                    'scientific_name': record.scientific_name,
                    'genus': record.genus,
                    'species': record.species,
                    'region': record.region,
                    'photographer': record.photographer
                },
                'darwin_core': mapped_record
            })
        
        # Get total counts
        total_records = OrchidRecord.query.count()
        records_with_coords = OrchidRecord.query.filter(
            OrchidRecord.region.like('%Lat:%')
        ).count()
        records_with_images = OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None)
        ).count()
        
        export_stats = {
            'total_records': total_records,
            'records_with_coordinates': records_with_coords,
            'records_with_images': records_with_images,
            'coordinate_percentage': round((records_with_coords / total_records * 100) if total_records > 0 else 0, 1),
            'image_percentage': round((records_with_images / total_records * 100) if total_records > 0 else 0, 1)
        }
        
        return render_template('admin/darwin_core_preview.html',
                             mapped_samples=mapped_samples,
                             export_stats=export_stats,
                             dwc_fields=exporter.dwc_fields)
        
    except Exception as e:
        logger.error(f"Error generating Darwin Core preview: {e}")
        flash('Error generating preview. Please try again.', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route("/compare/<species_name>")
def compare_orchid_specimens(species_name):
    """Compare multiple specimens of the same orchid species"""
    from collections import defaultdict
    
    # Get all specimens of this species
    records = OrchidRecord.query.filter(
        func.lower(OrchidRecord.display_name) == species_name.lower()
    ).all()
    
    if not records:
        flash("No specimens found for this species", "error")
        return redirect(url_for("gallery"))
    
    # Group specimens by different characteristics for comparison
    comparison_data = {
        "species_name": species_name,
        "specimen_count": len(records),
        "specimens": records,
        "photographers": list(set(r.photographer for r in records if r.photographer)),
        "sources": list(set(r.ingestion_source for r in records if r.ingestion_source)),
        "with_photos": [r for r in records if r.google_drive_id],
        "climate_conditions": list(set(r.climate_preference for r in records if r.climate_preference)),
        "growth_habits": list(set(r.growth_habit for r in records if r.growth_habit))
    }
    
    return render_template("comparison.html", data=comparison_data)

@app.route("/research_dashboard") 
def research_dashboard():
    """Dashboard for orchid growth research and comparison analysis"""
    # Get species with multiple specimens
    from collections import defaultdict
    
    species_groups = defaultdict(list)
    all_records = OrchidRecord.query.all()
    
    for record in all_records:
        if record.display_name:
            species_key = record.display_name.strip().lower()
            species_groups[species_key].append(record)
    
    # Filter to research candidates (multiple specimens)
    research_candidates = []
    for species, records in species_groups.items():
        if len(records) >= 2:  # Multiple specimens for comparison
            photos = sum(1 for r in records if r.google_drive_id)
            photographers = len(set(r.photographer for r in records if r.photographer))
            
            research_candidates.append({
                "species": species,
                "specimens": len(records),
                "photos": photos,
                "photographers": photographers,
                "photo_percentage": (photos/len(records)*100) if len(records) > 0 else 0
            })
    
    # Sort by research value (specimens with photos)
    research_candidates.sort(key=lambda x: (x["photos"], x["specimens"]), reverse=True)
    
    return render_template("research_dashboard.html", candidates=research_candidates[:50])


@app.route("/discovery_alerts")
def discovery_alerts():
    """Show Professor BloomBot discovery alerts dashboard"""
    from professor_bloombot import ProfessorBloomBot
    from models import DiscoveryAlert
    
    # Generate new discoveries
    bot = ProfessorBloomBot()
    discoveries = bot.discover_patterns()
    
    # Save important discoveries to database
    for discovery in discoveries:
        if discovery['importance'] >= 0.7:  # Only save important ones
            # Check if similar alert already exists
            existing = DiscoveryAlert.query.filter(
                DiscoveryAlert.alert_type == discovery['type'],
                DiscoveryAlert.title == discovery['title']
            ).first()
            
            if not existing:
                alert = DiscoveryAlert(
                    alert_type=discovery['type'],
                    title=discovery['title'],
                    message=discovery['message'],
                    importance=discovery['importance'],
                    action_url=discovery.get('action_url'),
                    action_text=discovery.get('action_text'),
                    icon=discovery.get('icon'),
                    category=discovery.get('category')
                )
                db.session.add(alert)
    
    db.session.commit()
    
    # Get all active alerts
    active_alerts = DiscoveryAlert.query.filter(
        DiscoveryAlert.is_active == True,
        DiscoveryAlert.dismissed_by_admin == False
    ).order_by(DiscoveryAlert.importance.desc()).all()
    
    # Generate daily report
    daily_report = bot.generate_daily_discovery_report()
    
    return render_template("discovery_alerts.html", 
                         alerts=active_alerts, 
                         daily_report=daily_report,
                         live_discoveries=discoveries)

@app.route("/dismiss_alert/<int:alert_id>", methods=['POST'])
def dismiss_alert(alert_id):
    """Dismiss a discovery alert"""
    alert = DiscoveryAlert.query.get_or_404(alert_id)
    alert.dismissed_by_admin = True
    db.session.commit()
    
    flash(f"Dismissed alert: {alert.title}", "success")
    return redirect(url_for('discovery_alerts'))

@app.route("/featured_discovery")
def featured_discovery():
    """Get featured discovery for homepage widget"""
    from professor_bloombot import ProfessorBloomBot
    
    # Try to get a featured alert from database first
    featured = DiscoveryAlert.query.filter(
        DiscoveryAlert.is_featured == True,
        DiscoveryAlert.is_active == True
    ).first()
    
    if featured:
        discovery = {
            'title': featured.title,
            'message': featured.message,
            'action_url': featured.action_url,
            'action_text': featured.action_text,
            'icon': featured.icon,
            'category': featured.category
        }
    else:
        # Generate a fresh discovery
        bot = ProfessorBloomBot()
        discoveries = bot.discover_patterns()
        discovery = discoveries[0] if discoveries else {
            'title': '🔬 Professor BloomBot is monitoring...',
            'message': 'Analyzing orchid patterns and correlations for new discoveries!',
            'icon': 'activity',
            'category': 'monitoring'
        }
    
    return jsonify(discovery)

@app.route("/api/discovery_widget")
def discovery_widget():
    """API endpoint for discovery widget data"""
    from professor_bloombot import ProfessorBloomBot
    
    bot = ProfessorBloomBot()
    report = bot.generate_daily_discovery_report()
    
    # Get the most important discovery for widget
    if report['discoveries']:
        top_discovery = report['discoveries'][0]
        return jsonify({
            'status': 'active',
            'discovery': top_discovery,
            'total_discoveries': len(report['discoveries'])
        })
    
    return jsonify({
        'status': 'monitoring',
        'message': 'Professor BloomBot is analyzing orchid patterns...',
        'icon': 'search'
    })

# Register AOS-Baker Culture Sheet System
try:
    from aos_baker_culture_routes import register_culture_routes
    register_culture_routes(app)
    logger.info("AOS-Baker Culture Sheet system registered successfully")
except Exception as e:
    logger.error(f"Failed to register culture sheet system: {str(e)}")

# ==============================================================================
# ADMIN SCRAPING DASHBOARD ROUTES - Real-time monitoring and control
# ==============================================================================

@app.route('/admin/scraping/dashboard-stats')
def scraping_dashboard_stats():
    """Get real-time scraping dashboard statistics"""
    try:
        stats = scraping_dashboard.get_dashboard_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Dashboard stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/scraping/start', methods=['POST'])
def start_methodical_scraping():
    """Start methodical one-plant-at-a-time scraping"""
    try:
        success = scraping_dashboard.start_methodical_scraping()
        if success:
            return jsonify({'success': True, 'message': 'Methodical scraping started'})
        else:
            return jsonify({'success': False, 'error': 'Scraping already running'})
    except Exception as e:
        logger.error(f"Start scraping error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/scraping/stop', methods=['POST'])
def stop_scraping():
    """Stop all scraping operations"""
    try:
        scraping_dashboard.stop_scraping()
        return jsonify({'success': True, 'message': 'Scraping stopped'})
    except Exception as e:
        logger.error(f"Stop scraping error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/scraping/manual-trigger', methods=['POST'])
def manual_trigger_scraper():
    """Manually trigger a specific scraper"""
    try:
        data = request.get_json()
        scraper_name = data.get('scraper')
        
        if not scraper_name:
            return jsonify({'success': False, 'error': 'Scraper name required'}), 400
        
        result = scraping_dashboard.manual_trigger_scraper(scraper_name)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Manual trigger error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ==============================================================================
# VIGILANT MONITORING ROUTES - 30-second checks and auto-recovery
# ==============================================================================

@app.route('/admin/vigilant/start', methods=['POST'])
def start_vigilant_monitoring():
    """Start vigilant 30-second monitoring"""
    try:
        success = vigilant_monitor.start_vigilant_monitoring()
        if success:
            return jsonify({'success': True, 'message': 'Vigilant monitoring started'})
        else:
            return jsonify({'success': False, 'error': 'Monitoring already running'})
    except Exception as e:
        logger.error(f"Start monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/vigilant/stop', methods=['POST'])
def stop_vigilant_monitoring():
    """Stop vigilant monitoring"""
    try:
        vigilant_monitor.stop_monitoring()
        return jsonify({'success': True, 'message': 'Vigilant monitoring stopped'})
    except Exception as e:
        logger.error(f"Stop monitoring error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/vigilant/stats')
def vigilant_monitor_stats():
    """Get vigilant monitoring statistics"""
    try:
        stats = vigilant_monitor.get_monitor_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Monitor stats error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/admin/vigilant/force-backup', methods=['POST'])
def force_database_backup():
    """Force immediate database backup"""
    try:
        result = vigilant_monitor.force_backup()
        backup_url = vigilant_monitor.get_backup_download_url()
        
        return jsonify({
            'success': True, 
            'message': result,
            'backup_url': backup_url
        })
    except Exception as e:
        logger.error(f"Force backup error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/download-backup/<filename>')
def download_backup(filename):
    """Download database backup file"""
    try:
        from pathlib import Path
        backup_path = Path('database_backups') / filename
        
        if backup_path.exists() and backup_path.name.startswith('orchid_db_backup_'):
            return send_file(backup_path, as_attachment=True)
        else:
            return "Backup file not found", 404
            
    except Exception as e:
        logger.error(f"Download backup error: {e}")
        return f"Error downloading backup: {e}", 500

# ==============================================================================
# VIGILANT MONITOR AUTO-START - Start vigilant monitoring on app startup
# ==============================================================================

# Auto-start vigilant monitoring
try:
    vigilant_monitor.start_vigilant_monitoring()
    logger.info("🚨 VIGILANT MONITOR: Auto-started 30-second checks")
except Exception as e:
    logger.error(f"Failed to auto-start vigilant monitor: {e}")
