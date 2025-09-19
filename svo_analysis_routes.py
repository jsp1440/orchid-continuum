from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash
from werkzeug.utils import secure_filename
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from collections import Counter
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import csv
import logging
import os
import json
import uuid
from datetime import datetime
from models import SvoAnalysisSession, SvoResult, SvoAnalysisSummary, db
import threading
import time

# Create blueprint for SVO analysis routes
svo_bp = Blueprint('svo_analysis', __name__, url_prefix='/svo')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
STATIC_DIR = 'static'
SVO_CHARTS_DIR = os.path.join(STATIC_DIR, 'svo_charts')
SVO_EXPORTS_DIR = os.path.join(STATIC_DIR, 'svo_exports')
MAX_RETRIES = 3
TIMEOUT = 10

# Ensure directories exist
os.makedirs(SVO_CHARTS_DIR, exist_ok=True)
os.makedirs(SVO_EXPORTS_DIR, exist_ok=True)

# ========================================
# CORE SVO ANALYSIS ENGINE (WEB-ADAPTED)
# ========================================

async def fetch_url_content(session, url):
    """Fetch content from a single URL with retries"""
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as response:
                response.raise_for_status()
                text = await response.text()
                logger.info(f"Successfully fetched {url}")
                return text, None
        except Exception as e:
            logger.warning(f"Attempt {attempt} failed for {url}: {str(e)}")
            if attempt == MAX_RETRIES:
                error_msg = f"Failed to fetch {url} after {MAX_RETRIES} attempts: {str(e)}"
                logger.error(error_msg)
                return None, error_msg
    return None, "Unknown error"

def parse_svo_from_html(raw_html, source_url):
    """Extract SVO tuples from HTML content"""
    svo_list = []
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Enhanced SVO extraction from multiple elements
        content_elements = soup.find_all(['p', 'div', 'article', 'section', 'span', 'li'])
        
        for element in content_elements:
            text = element.get_text(strip=True)
            if len(text) < 10:  # Skip very short text
                continue
                
            # More sophisticated SVO pattern matching
            patterns = [
                r'(\b\w+\b)\s+(grows?|blooms?|flowers?|requires?|needs?|thrives?|prefers?|likes?|lives?|produces?|displays?|shows?|exhibits?)\s+(\b\w+(?:\s+\w+){0,2}\b)',
                r'(\b\w+\b)\s+(is|are|was|were|becomes?|appears?|seems?|looks?|remains?)\s+(\b\w+(?:\s+\w+){0,2}\b)',
                r'(\b\w+\b)\s+(has|have|had|contains?|includes?|features?|possesses?)\s+(\b\w+(?:\s+\w+){0,2}\b)',
                r'(\b\w+\b)\s+(creates?|makes?|forms?|develops?|builds?)\s+(\b\w+(?:\s+\w+){0,2}\b)',
                r'(\b[A-Z]\w+\b)\s+(\w+s?)\s+(\b\w+(?:\s+\w+){0,2}\b)'  # Proper nouns as subjects
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                for match in matches:
                    if len(match) == 3:
                        subject, verb, obj = match
                        # Filter out common non-meaningful matches
                        if len(subject) > 1 and len(verb) > 1 and len(obj) > 1:
                            # Get surrounding context (up to 100 chars)
                            start_pos = text.lower().find(subject.lower())
                            if start_pos != -1:
                                context_start = max(0, start_pos - 50)
                                context_end = min(len(text), start_pos + len(subject) + len(verb) + len(obj) + 50)
                                context = text[context_start:context_end].strip()
                            else:
                                context = text[:100].strip()
                            
                            svo_list.append((subject, verb, obj, context))
        
        logger.info(f"Extracted {len(svo_list)} SVO tuples from {source_url}")
        return svo_list
        
    except Exception as e:
        logger.error(f"Error parsing HTML from {source_url}: {str(e)}")
        return []

def clean_svo_text(text):
    """Clean and normalize text"""
    # Remove extra whitespace and special characters
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s-]', '', text)
    return text.strip().lower()

def analyze_svo_results(cleaned_svo_list):
    """Analyze SVO results and generate frequency data"""
    subjects = [s for s, v, o in cleaned_svo_list]
    verbs = [v for s, v, o in cleaned_svo_list]
    objects = [o for s, v, o in cleaned_svo_list]
    
    analysis = {
        'subject_freq': Counter(subjects),
        'verb_freq': Counter(verbs),
        'object_freq': Counter(objects),
        'total_svo': len(cleaned_svo_list),
        'unique_subjects': len(set(subjects)),
        'unique_verbs': len(set(verbs)),
        'unique_objects': len(set(objects))
    }
    
    return analysis

def create_frequency_charts(analysis, session_id):
    """Create and save frequency charts"""
    chart_paths = {}
    
    try:
        for component, counter in [('subject', analysis['subject_freq']), 
                                 ('verb', analysis['verb_freq']), 
                                 ('object', analysis['object_freq'])]:
            
            top_items = counter.most_common(15)  # Show top 15
            if not top_items:
                continue
                
            labels, counts = zip(*top_items)
            
            plt.figure(figsize=(12, 8))
            bars = plt.bar(labels, counts, color='#3aa681', alpha=0.8)
            
            # Customize the chart
            plt.title(f'Top {len(top_items)} {component.title()}s in SVO Analysis', 
                     fontsize=16, fontweight='bold', color='#2c3e50')
            plt.xlabel(f'{component.title()}s', fontsize=12, fontweight='bold')
            plt.ylabel('Frequency', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                        str(count), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.grid(axis='y', alpha=0.3)
            
            # Save chart
            chart_filename = f'{session_id}_{component}_freq.png'
            chart_path = os.path.join(SVO_CHARTS_DIR, chart_filename)
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            # Store relative path for web serving
            chart_paths[f'{component}_chart_path'] = f'/static/svo_charts/{chart_filename}'
            logger.info(f"Created {component} frequency chart: {chart_path}")
    
    except Exception as e:
        logger.error(f"Error creating charts: {str(e)}")
    
    return chart_paths

def export_results_to_csv(svo_results, session_id):
    """Export SVO results to CSV file"""
    try:
        csv_filename = f'{session_id}_svo_results.csv'
        csv_path = os.path.join(SVO_EXPORTS_DIR, csv_filename)
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write header
            writer.writerow(['Source URL', 'Subject', 'Verb', 'Object', 
                           'Subject (Clean)', 'Verb (Clean)', 'Object (Clean)', 
                           'Context', 'Confidence Score'])
            
            # Write data
            for result in svo_results:
                writer.writerow([
                    result.source_url,
                    result.subject,
                    result.verb,
                    result.object,
                    result.subject_clean,
                    result.verb_clean,
                    result.object_clean,
                    result.context_text or '',
                    result.confidence_score
                ])
        
        logger.info(f"Exported results to CSV: {csv_path}")
        return f'/static/svo_exports/{csv_filename}'
        
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        return None

def background_svo_analysis(session_id, urls):
    """Run SVO analysis in background thread"""
    
    async def run_analysis():
        session = SvoAnalysisSession.query.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        try:
            # Update session status
            session.status = 'running'
            session.started_at = datetime.utcnow()
            db.session.commit()
            
            total_urls = len(urls)
            all_svo_results = []
            failed_urls = []
            
            async with aiohttp.ClientSession() as http_session:
                for i, url in enumerate(urls):
                    try:
                        # Update progress
                        session.current_url_index = i
                        session.progress_percent = int((i / total_urls) * 100)
                        db.session.commit()
                        
                        # Fetch and analyze URL
                        content, error = await fetch_url_content(http_session, url)
                        
                        if content:
                            svo_tuples = parse_svo_from_html(content, url)
                            
                            # Store results in database
                            for subject, verb, obj, context in svo_tuples:
                                svo_result = SvoResult()
                                svo_result.session_id = session_id
                                svo_result.source_url = url
                                svo_result.subject = subject
                                svo_result.verb = verb
                                svo_result.object = obj
                                svo_result.subject_clean = clean_svo_text(subject)
                                svo_result.verb_clean = clean_svo_text(verb)
                                svo_result.object_clean = clean_svo_text(obj)
                                svo_result.context_text = context
                                svo_result.confidence_score = 1.0  # Basic confidence for now
                                db.session.add(svo_result)
                                all_svo_results.append(svo_result)
                        else:
                            failed_urls.append({'url': url, 'error': error})
                        
                        db.session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {str(e)}")
                        failed_urls.append({'url': url, 'error': str(e)})
            
            # Create analysis summary
            if all_svo_results:
                cleaned_svo_list = [(r.subject_clean, r.verb_clean, r.object_clean) 
                                  for r in all_svo_results]
                analysis = analyze_svo_results(cleaned_svo_list)
                
                # Create charts
                chart_paths = create_frequency_charts(analysis, session_id)
                
                # Export CSV
                csv_path = export_results_to_csv(all_svo_results, session_id)
                
                # Save summary to database
                summary = SvoAnalysisSummary()
                summary.session_id = session_id
                summary.subject_frequencies = dict(analysis['subject_freq'])
                summary.verb_frequencies = dict(analysis['verb_freq'])
                summary.object_frequencies = dict(analysis['object_freq'])
                summary.total_tuples = analysis['total_svo']
                summary.unique_subjects = analysis['unique_subjects']
                summary.unique_verbs = analysis['unique_verbs']
                summary.unique_objects = analysis['unique_objects']
                summary.subject_chart_path = chart_paths.get('subject_chart_path')
                summary.verb_chart_path = chart_paths.get('verb_chart_path')
                summary.object_chart_path = chart_paths.get('object_chart_path')
                summary.csv_export_path = csv_path
                db.session.add(summary)
            
            # Update session completion
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            session.progress_percent = 100
            session.total_svo_found = len(all_svo_results)
            session.failed_urls = failed_urls if failed_urls else None
            
            db.session.commit()
            logger.info(f"Analysis completed for session {session_id}")
            
        except Exception as e:
            # Handle errors
            logger.error(f"Analysis failed for session {session_id}: {str(e)}")
            session.status = 'failed'
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.session.commit()
    
    # Run async function in thread
    def run_in_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_analysis())
        except Exception as e:
            logger.error(f"Thread execution failed: {str(e)}")
        finally:
            if 'loop' in locals():
                loop.close()
    
    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True
    thread.start()

# ========================================
# FLASK ROUTES
# ========================================

@svo_bp.route('/')
def index():
    """Main SVO analysis page"""
    # Get recent sessions for the user (you may want to add user authentication)
    recent_sessions = SvoAnalysisSession.query.order_by(
        SvoAnalysisSession.created_at.desc()
    ).limit(10).all()
    
    return render_template('svo_analysis/index.html', recent_sessions=recent_sessions)

@svo_bp.route('/start', methods=['POST'])
def start_analysis():
    """Start a new SVO analysis session"""
    try:
        data = request.get_json()
        session_name = data.get('session_name', '').strip()
        urls = data.get('urls', [])
        
        # Validation
        if not session_name:
            return jsonify({'error': 'Session name is required'}), 400
        
        if not urls or len(urls) == 0:
            return jsonify({'error': 'At least one URL is required'}), 400
        
        # Clean and validate URLs
        cleaned_urls = []
        for url in urls:
            url = url.strip()
            if url:
                if not url.startswith(('http://', 'https://')):
                    url = 'https://' + url
                cleaned_urls.append(url)
        
        if not cleaned_urls:
            return jsonify({'error': 'No valid URLs provided'}), 400
        
        # Create new session
        session = SvoAnalysisSession()
        session.session_name = session_name
        session.urls = cleaned_urls
        session.max_retries = MAX_RETRIES
        session.timeout_seconds = TIMEOUT
        
        db.session.add(session)
        db.session.commit()
        
        # Start background analysis
        background_svo_analysis(session.id, cleaned_urls)
        
        return jsonify({
            'success': True,
            'session_id': session.id,
            'message': 'Analysis started successfully'
        })
        
    except Exception as e:
        logger.error(f"Error starting analysis: {str(e)}")
        return jsonify({'error': 'Failed to start analysis'}), 500

@svo_bp.route('/status/<session_id>')
def get_status(session_id):
    """Get analysis status for a session"""
    try:
        session = SvoAnalysisSession.query.get_or_404(session_id)
        return jsonify(session.to_dict())
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        return jsonify({'error': 'Failed to get status'}), 500

@svo_bp.route('/results/<session_id>')
def view_results(session_id):
    """View analysis results"""
    try:
        session = SvoAnalysisSession.query.get_or_404(session_id)
        
        if session.status != 'completed':
            flash(f'Analysis is {session.status}. Results not available yet.', 'warning')
            return redirect(url_for('svo_analysis.index'))
        
        # Get results and summary
        results = SvoResult.query.filter_by(session_id=session_id).all()
        summary = SvoAnalysisSummary.query.filter_by(session_id=session_id).first()
        
        return render_template('svo_analysis/results.html', 
                             session=session, 
                             results=results, 
                             summary=summary)
        
    except Exception as e:
        logger.error(f"Error viewing results: {str(e)}")
        flash('Error loading results', 'error')
        return redirect(url_for('svo_analysis.index'))

@svo_bp.route('/download/<session_id>')
def download_csv(session_id):
    """Download CSV export of results"""
    try:
        summary = SvoAnalysisSummary.query.filter_by(session_id=session_id).first_or_404()
        
        if not summary.csv_export_path:
            flash('CSV export not available', 'error')
            return redirect(url_for('svo_analysis.view_results', session_id=session_id))
        
        # Convert relative path to absolute
        csv_path = summary.csv_export_path.replace('/static/svo_exports/', '')
        full_path = os.path.join(SVO_EXPORTS_DIR, csv_path)
        
        if not os.path.exists(full_path):
            flash('CSV file not found', 'error')
            return redirect(url_for('svo_analysis.view_results', session_id=session_id))
        
        return send_file(full_path, as_attachment=True, 
                        download_name=f'svo_analysis_{session_id}.csv')
        
    except Exception as e:
        logger.error(f"Error downloading CSV: {str(e)}")
        flash('Error downloading file', 'error')
        return redirect(url_for('svo_analysis.index'))

@svo_bp.route('/delete/<session_id>', methods=['POST'])
def delete_session(session_id):
    """Delete an analysis session and its data"""
    try:
        session = SvoAnalysisSession.query.get_or_404(session_id)
        
        # Delete associated files
        summary = SvoAnalysisSummary.query.filter_by(session_id=session_id).first()
        if summary:
            # Delete chart files
            for chart_path in [summary.subject_chart_path, summary.verb_chart_path, summary.object_chart_path]:
                if chart_path:
                    full_path = chart_path.replace('/static/', '')
                    full_path = os.path.join(STATIC_DIR, full_path.replace('/static/', ''))
                    if os.path.exists(full_path):
                        os.remove(full_path)
            
            # Delete CSV file
            if summary.csv_export_path:
                csv_path = summary.csv_export_path.replace('/static/svo_exports/', '')
                full_path = os.path.join(SVO_EXPORTS_DIR, csv_path)
                if os.path.exists(full_path):
                    os.remove(full_path)
        
        # Delete database records
        SvoResult.query.filter_by(session_id=session_id).delete()
        if summary:
            db.session.delete(summary)
        db.session.delete(session)
        db.session.commit()
        
        flash('Analysis session deleted successfully', 'success')
        
    except Exception as e:
        logger.error(f"Error deleting session: {str(e)}")
        flash('Error deleting session', 'error')
    
    return redirect(url_for('svo_analysis.index'))

# ========================================
# API ROUTES FOR AJAX CALLS
# ========================================

@svo_bp.route('/api/sessions')
def api_list_sessions():
    """API endpoint to list all sessions"""
    try:
        sessions = SvoAnalysisSession.query.order_by(
            SvoAnalysisSession.created_at.desc()
        ).limit(50).all()
        
        return jsonify([session.to_dict() for session in sessions])
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        return jsonify({'error': 'Failed to list sessions'}), 500

@svo_bp.route('/api/results/<session_id>')
def api_get_results(session_id):
    """API endpoint to get results for a session"""
    try:
        results = SvoResult.query.filter_by(session_id=session_id).all()
        summary = SvoAnalysisSummary.query.filter_by(session_id=session_id).first()
        
        return jsonify({
            'results': [result.to_dict() for result in results],
            'summary': summary.to_dict() if summary else None
        })
        
    except Exception as e:
        logger.error(f"Error getting results: {str(e)}")
        return jsonify({'error': 'Failed to get results'}), 500