"""
Administrative System for Ultimate Database Control
Secure administrative access with environment-based authentication
"""
import os
import json
import csv
import logging
from datetime import datetime
from functools import wraps
from flask import render_template, request, jsonify, flash, redirect, url_for, session, Response
from werkzeug.security import check_password_hash, generate_password_hash
from app import app, db
from models import OrchidRecord, OrchidTaxonomy, UserUpload, ScrapingLog, JudgingAnalysis, Certificate, BatchUpload
from sqlalchemy import text, func
import zipfile
import io
import tempfile

logger = logging.getLogger(__name__)

# Admin password hash from environment variable - fail closed if not set
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
if not ADMIN_PASSWORD:
    logger.critical("🚨 ADMIN_PASSWORD environment variable not set. Admin access disabled for security.")
    ADMIN_PASSWORD_HASH = None
else:
    ADMIN_PASSWORD_HASH = generate_password_hash(ADMIN_PASSWORD)
    logger.info("✅ Admin authentication properly configured")

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    # Check if admin access is disabled due to missing environment variable
    if ADMIN_PASSWORD_HASH is None:
        flash('Administrative access is disabled. Contact system administrator.', 'error')
        return render_template('admin_login.html', admin_disabled=True)
    
    if request.method == 'POST':
        password = request.form.get('password')
        
        if password and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_authenticated'] = True
            session['admin_login_time'] = datetime.utcnow().isoformat()
            flash('Admin access granted - Ultimate database control activated', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid administrative password', 'error')
    
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    """Admin logout"""
    session.pop('admin_authenticated', None)
    session.pop('admin_login_time', None)
    flash('Administrative session ended', 'info')
    return redirect(url_for('index'))

@app.route('/admin/ai-assistant', methods=['GET', 'POST'])
@admin_required
def admin_ai_assistant():
    """AI Assistant for making platform changes"""
    if request.method == 'POST':
        user_request = request.form.get('request')
        
        # Use existing OpenAI integration
        try:
            from orchid_ai import openai_client
            
            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system", 
                        "content": """You are an AI assistant for The Orchid Continuum - Five Cities Orchid Society's digital platform. You have access to:

CURRENT PLATFORM CAPABILITIES:
- 1,459 orchid records with 92% image coverage (1,342 images)
- 9 widget types: gallery, search, comparison, identifier, citation, featured, mission, map, weather
- Google Drive integration with 200+ orchid photos
- AI-powered orchid identification using GPT-4o Vision
- Advanced admin system with database control
- Web scraping from Gary Yong Gee and Roberta Fox sites
- Google Sheets integration (1,337 Five Cities Orchid Society records)
- Widget system for external integration
- Citation and research attribution system

AI WIDGET BUILDER:
- Create new widgets with natural language descriptions
- Modify existing widgets with AI assistance
- Generate implementation code automatically
- Preview widgets before deployment
- Access at /admin/ai-widgets/

AVAILABLE ACTIONS:
1. Create new widgets: "Create a widget that shows orchids by climate preference"
2. Modify widgets: "Add search functionality to the gallery widget"
3. Database operations: "Show me orchids without images" 
4. Platform improvements: "Add mobile responsiveness to the comparison widget"
5. Integration help: "How do I embed the weather widget on our main site?"

Provide specific, actionable guidance for orchid platform management."""
                    },
                    {"role": "user", "content": str(user_request or "")}
                ],
                max_tokens=800
            )
            
            ai_response = response.choices[0].message.content
            return render_template('admin_ai_assistant.html', 
                                 user_request=user_request, 
                                 ai_response=ai_response)
        except Exception as e:
            flash(f'AI Assistant error: {e}', 'error')
    
    return render_template('admin_ai_assistant.html')

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Administrative dashboard with ultimate database control"""
    try:
        # Database statistics with safe fallbacks
        stats = {}
        
        # Safe count queries with error handling
        try:
            stats['orchid_records'] = OrchidRecord.query.count()
        except Exception as e:
            logger.warning(f"Could not count orchid_records: {e}")
            stats['orchid_records'] = 0
            
        try:
            stats['taxonomy_entries'] = OrchidTaxonomy.query.count()
        except Exception as e:
            logger.warning(f"Could not count taxonomy_entries: {e}")
            stats['taxonomy_entries'] = 0
            
        # Safe queries for potentially missing tables
        for table_name, model_class in [
            ('user_uploads', UserUpload),
            ('scraping_logs', ScrapingLog),
            ('judging_analyses', JudgingAnalysis),
            ('certificates', Certificate),
            ('batch_uploads', BatchUpload)
        ]:
            try:
                stats[table_name] = model_class.query.count()
            except Exception as e:
                logger.warning(f"Table {table_name} not available: {e}")
                stats[table_name] = 0
        
        # Recent activities with safe queries
        recent_orchids = []
        recent_uploads = []
        recent_logs = []
        
        try:
            recent_orchids = OrchidRecord.query.order_by(OrchidRecord.created_at.desc()).limit(10).all()
        except Exception as e:
            logger.warning(f"Could not fetch recent orchids: {e}")
            
        try:
            recent_uploads = UserUpload.query.order_by(UserUpload.created_at.desc()).limit(5).all()
        except Exception as e:
            logger.warning(f"Could not fetch recent uploads: {e}")
            
        try:
            recent_logs = ScrapingLog.query.order_by(ScrapingLog.created_at.desc()).limit(5).all()
        except Exception as e:
            logger.warning(f"Could not fetch recent logs: {e}")
        
        # System health with safe queries
        health_info = {}
        
        try:
            health_info['database_size'] = get_database_size()
        except Exception as e:
            logger.warning(f"Could not get database size: {e}")
            health_info['database_size'] = "Unknown"
            
        try:
            health_info['total_images'] = len([r for r in recent_orchids if r.image_url])
        except Exception:
            health_info['total_images'] = 0
            
        try:
            health_info['ai_analyzed'] = OrchidRecord.query.filter(OrchidRecord.ai_description.isnot(None)).count()
        except Exception:
            health_info['ai_analyzed'] = 0
            
        try:
            health_info['rhs_verified'] = OrchidRecord.query.filter(OrchidRecord.rhs_verification_status == 'verified').count()
        except Exception:
            health_info['rhs_verified'] = 0
        
        return render_template('admin_dashboard.html',
                             stats=stats,
                             recent_orchids=recent_orchids,
                             recent_uploads=recent_uploads,
                             recent_logs=recent_logs,
                             health=health_info)
    
    except Exception as e:
        logger.error(f"Admin dashboard error: {str(e)}")
        flash(f'Dashboard partially loaded - some database tables may not be available', 'warning')
        
        # Provide minimal safe data
        minimal_stats = {
            'orchid_records': 0,
            'taxonomy_entries': 0,
            'user_uploads': 0,
            'scraping_logs': 0,
            'judging_analyses': 0,
            'certificates': 0,
            'batch_uploads': 0
        }
        minimal_health = {
            'database_size': "Unknown",
            'total_images': 0,
            'ai_analyzed': 0,
            'rhs_verified': 0
        }
        
        return render_template('admin_dashboard.html', 
                             stats=minimal_stats, 
                             recent_orchids=[], 
                             recent_uploads=[], 
                             recent_logs=[], 
                             health=minimal_health)

@app.route('/admin/database/query', methods=['GET', 'POST'])
@admin_required
def admin_database_query():
    """Execute raw database queries with full control"""
    results = None
    query = ""
    error = None
    
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        
        if query:
            try:
                # Execute raw SQL query
                result = db.session.execute(text(query))
                
                if query.lower().strip().startswith(('select', 'show', 'describe', 'explain')):
                    # For SELECT queries, fetch results
                    rows = result.fetchall()
                    columns = result.keys() if rows else []
                    results = {
                        'columns': list(columns),
                        'rows': [list(row) for row in rows],
                        'count': len(rows)
                    }
                else:
                    # For other queries (INSERT, UPDATE, DELETE), commit changes
                    db.session.commit()
                    rows_affected = getattr(result, 'rowcount', 0)
                    results = {
                        'message': f'Query executed successfully. Rows affected: {rows_affected}',
                        'rows_affected': rows_affected
                    }
                
            except Exception as e:
                error = str(e)
                db.session.rollback()
                logger.error(f"Database query error: {error}")
    
    return render_template('admin_database_query.html', 
                         query=query, 
                         results=results, 
                         error=error)

@app.route('/admin/export/complete-database')
@admin_required
def export_complete_database():
    """Export complete database as comprehensive archive"""
    try:
        # Create temporary file for the zip
        temp_buffer = io.BytesIO()
        
        with zipfile.ZipFile(temp_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            
            # Export all orchid records
            orchids = OrchidRecord.query.all()
            orchid_data = []
            for orchid in orchids:
                orchid_dict = {
                    'id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'author': orchid.author,
                    'native_habitat': orchid.native_habitat,
                    'temperature_range': orchid.temperature_range,
                    'light_requirements': orchid.light_requirements,
                    'image_url': orchid.image_url,
                    'ai_description': orchid.ai_description,
                    'ai_confidence': orchid.ai_confidence,
                    'created_at': orchid.created_at.isoformat() if orchid.created_at else None,
                    'updated_at': orchid.updated_at.isoformat() if orchid.updated_at else None,
                    'rhs_registration_id': orchid.rhs_registration_id,
                    'is_hybrid': orchid.is_hybrid,
                    'pod_parent': orchid.pod_parent,
                    'pollen_parent': orchid.pollen_parent,
                    'parentage_formula': orchid.parentage_formula,
                    'is_featured': orchid.is_featured,
                    'view_count': orchid.view_count
                }
                orchid_data.append(orchid_dict)
            
            # Add orchid records as JSON
            zip_file.writestr('orchid_records.json', json.dumps(orchid_data, indent=2, default=str))
            
            # Add orchid records as CSV
            csv_buffer = io.StringIO()
            if orchid_data:
                fieldnames = orchid_data[0].keys()
                writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(orchid_data)
                zip_file.writestr('orchid_records.csv', csv_buffer.getvalue())
            
            # Export taxonomy data
            taxonomy = OrchidTaxonomy.query.all()
            taxonomy_data = []
            for tax in taxonomy:
                taxonomy_data.append({
                    'id': tax.id,
                    'genus': tax.genus,
                    'species': tax.species,
                    'subspecies': tax.subspecies,
                    'author': tax.author,
                    'family': tax.family,
                    'subfamily': tax.subfamily,
                    'tribe': tax.tribe,
                    'subtribe': tax.subtribe,
                    'created_at': tax.created_at.isoformat() if tax.created_at else None
                })
            zip_file.writestr('taxonomy.json', json.dumps(taxonomy_data, indent=2, default=str))
            
            # Export user uploads
            uploads = UserUpload.query.all()
            upload_data = []
            for upload in uploads:
                upload_data.append({
                    'id': upload.id,
                    'filename': upload.filename,
                    'original_filename': upload.original_filename,
                    'file_path': upload.file_path,
                    'file_size': upload.file_size,
                    'upload_date': upload.upload_date.isoformat() if upload.upload_date else None,
                    'processed': upload.processed,
                    'processing_notes': upload.processing_notes
                })
            zip_file.writestr('user_uploads.json', json.dumps(upload_data, indent=2, default=str))
            
            # Export scraping logs
            logs = ScrapingLog.query.all()
            log_data = []
            for log in logs:
                log_data.append({
                    'id': log.id,
                    'source': log.source,
                    'url': log.url,
                    'status': log.status,
                    'items_found': log.items_found,
                    'items_processed': log.items_processed,
                    'scraped_at': log.scraped_at.isoformat() if log.scraped_at else None,
                    'error_message': log.error_message
                })
            zip_file.writestr('scraping_logs.json', json.dumps(log_data, indent=2, default=str))
            
            # Export judging analyses
            analyses = JudgingAnalysis.query.all()
            analysis_data = []
            for analysis in analyses:
                analysis_data.append({
                    'id': analysis.id,
                    'orchid_id': analysis.orchid_id,
                    'organization': analysis.organization,
                    'total_score': analysis.total_score,
                    'form_score': analysis.form_score,
                    'color_score': analysis.color_score,
                    'substance_score': analysis.substance_score,
                    'size_score': analysis.size_score,
                    'created_at': analysis.created_at.isoformat() if analysis.created_at else None
                })
            zip_file.writestr('judging_analyses.json', json.dumps(analysis_data, indent=2, default=str))
            
            # Add export metadata
            export_metadata = {
                'export_date': datetime.utcnow().isoformat(),
                'exported_by': 'Admin System',
                'total_orchid_records': len(orchid_data),
                'total_taxonomy_entries': len(taxonomy_data),
                'total_user_uploads': len(upload_data),
                'total_scraping_logs': len(log_data),
                'total_judging_analyses': len(analysis_data),
                'database_version': '1.0',
                'export_format': 'Complete Database Archive'
            }
            zip_file.writestr('export_metadata.json', json.dumps(export_metadata, indent=2))
        
        temp_buffer.seek(0)
        
        # Create response
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'orchid_continuum_complete_database_{timestamp}.zip'
        
        return Response(
            temp_buffer.getvalue(),
            mimetype='application/zip',
            headers={
                'Content-Disposition': f'attachment; filename={filename}',
                'Content-Length': str(len(temp_buffer.getvalue()))
            }
        )
    
    except Exception as e:
        logger.error(f"Database export error: {str(e)}")
        flash(f'Export failed: {str(e)}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/export/custom', methods=['GET', 'POST'])
@admin_required  
def export_custom_data():
    """Custom data export with flexible options"""
    if request.method == 'POST':
        try:
            export_options = request.form.getlist('export_tables')
            export_format = request.form.get('format', 'json')
            
            if not export_options:
                flash('No tables selected for export', 'error')
                return redirect(request.url)
            
            # Prepare data based on selections
            export_data = {}
            
            if 'orchid_records' in export_options:
                orchids = OrchidRecord.query.all()
                export_data['orchid_records'] = [
                    {
                        'id': o.id, 'display_name': o.display_name, 'scientific_name': o.scientific_name,
                        'genus': o.genus, 'species': o.species, 'native_habitat': o.native_habitat,
                        'temperature_range': o.temperature_range, 'light_requirements': o.light_requirements,
                        'ai_description': o.ai_description, 'ai_confidence': o.ai_confidence,
                        'created_at': o.created_at.isoformat() if o.created_at else None
                    } for o in orchids
                ]
            
            if 'taxonomy' in export_options:
                taxonomy = OrchidTaxonomy.query.all()
                export_data['taxonomy'] = [
                    {
                        'id': t.id, 'genus': t.genus, 'species': t.species, 
                        'author': t.author, 'family': t.family
                    } for t in taxonomy
                ]
            
            if 'user_uploads' in export_options:
                uploads = UserUpload.query.all()
                export_data['user_uploads'] = [
                    {
                        'id': u.id, 'filename': u.filename, 'file_size': u.file_size,
                        'upload_date': u.upload_date.isoformat() if u.upload_date else None,
                        'processed': u.processed
                    } for u in uploads
                ]
            
            # Create response based on format
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            if export_format == 'json':
                data_str = json.dumps(export_data, indent=2, default=str)
                filename = f'orchid_custom_export_{timestamp}.json'
                mimetype = 'application/json'
            else:  # CSV format
                # For CSV, export first selected table only
                if export_data:
                    first_table = list(export_data.values())[0]
                    csv_buffer = io.StringIO()
                    if first_table:
                        writer = csv.DictWriter(csv_buffer, fieldnames=first_table[0].keys())
                        writer.writeheader()
                        writer.writerows(first_table)
                    data_str = csv_buffer.getvalue()
                    filename = f'orchid_custom_export_{timestamp}.csv'
                    mimetype = 'text/csv'
                else:
                    data_str = ""
                    filename = f'orchid_custom_export_{timestamp}.csv'
                    mimetype = 'text/csv'
            
            return Response(
                data_str,
                mimetype=mimetype,
                headers={'Content-Disposition': f'attachment; filename={filename}'}
            )
            
        except Exception as e:
            logger.error(f"Custom export error: {str(e)}")
            flash(f'Export failed: {str(e)}', 'error')
    
    return render_template('admin_export_custom.html')

@app.route('/admin/database/maintenance')
@admin_required
def database_maintenance():
    """Database maintenance and cleanup operations"""
    try:
        maintenance_info = {
            'orphaned_images': get_orphaned_images_count(),
            'duplicate_records': get_duplicate_records_count(), 
            'empty_descriptions': OrchidRecord.query.filter(
                OrchidRecord.ai_description.is_(None)
            ).count(),
            'unprocessed_uploads': UserUpload.query.filter_by(processed=False).count(),
            'old_scraping_logs': ScrapingLog.query.filter(
                ScrapingLog.created_at < datetime.utcnow().replace(month=datetime.utcnow().month-1)
            ).count() if datetime.utcnow().month > 1 else 0
        }
        
        return render_template('admin_maintenance.html', info=maintenance_info)
    
    except Exception as e:
        logger.error(f"Maintenance page error: {str(e)}")
        flash(f'Maintenance info error: {str(e)}', 'error')
        return render_template('admin_maintenance.html', info={})

def get_database_size():
    """Get database size information (SQLite compatible)"""
    try:
        # Query to get table sizes safely
        result = db.session.execute(text("""
            SELECT name 
            FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
        """))
        
        tables = {}
        total_rows = 0
        
        for row in result:
            table_name = row[0]
            try:
                count_result = db.session.execute(text(f"SELECT COUNT(*) FROM `{table_name}`"))
                row_count = count_result.scalar()
                tables[table_name] = row_count if row_count is not None else 0
                total_rows += tables[table_name]
            except Exception as table_error:
                logger.warning(f"Could not count rows in table {table_name}: {table_error}")
                tables[table_name] = 0
        
        return {
            'total_tables': len(tables),
            'total_rows': total_rows,
            'tables': tables
        }
    except Exception as e:
        logger.error(f"Database size error: {e}")
        return {
            'total_tables': 0,
            'total_rows': 0,
            'tables': {}
        }

def get_orphaned_images_count():
    """Count images without corresponding records"""
    try:
        return OrchidRecord.query.filter(
            OrchidRecord.image_url.isnot(None),
            OrchidRecord.ai_description.is_(None)
        ).count()
    except Exception:
        return 0

def get_duplicate_records_count():
    """Count potential duplicate records"""
    try:
        duplicates = db.session.execute(text("""
            SELECT COUNT(*) FROM (
                SELECT scientific_name, COUNT(*) as cnt 
                FROM orchid_record 
                WHERE scientific_name IS NOT NULL 
                GROUP BY scientific_name 
                HAVING COUNT(*) > 1
            ) as dups
        """))
        return duplicates.scalar() or 0
    except Exception:
        return 0