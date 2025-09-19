"""
Admin SVO Research Dashboard - Advanced Botanical Research Tool
=============================================================

Comprehensive admin interface for Subject-Verb-Object analysis with:
- Bulk URL management for multiple orchid websites
- Batch processing with advanced configuration
- Historical analysis and trend tracking
- Research-grade export options (JSON, Excel, citations)
- Sophisticated monitoring and analytics

Password: jsp191516 (same as main admin)
"""

from flask import Blueprint, render_template, request, jsonify, send_file, redirect, url_for, flash, session
from functools import wraps
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from collections import Counter, defaultdict
import pandas as pd
import json
import uuid
import logging
import os
import zipfile
import io
from datetime import datetime, timedelta
from models import SvoAnalysisSession, SvoResult, SvoAnalysisSummary, OrchidRecord, db
from svo_analysis_routes import (
    fetch_url_content, parse_svo_from_html, clean_svo_text, 
    analyze_svo_results, create_frequency_charts, export_results_to_csv
)
from admin_system import admin_required
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create admin SVO research blueprint  
admin_svo = Blueprint('admin_svo_research', __name__)

# Configuration directories
ADMIN_SVO_EXPORTS_DIR = os.path.join('static', 'admin_svo_exports')
ADMIN_SVO_CHARTS_DIR = os.path.join('static', 'admin_svo_charts')

# Ensure directories exist
os.makedirs(ADMIN_SVO_EXPORTS_DIR, exist_ok=True)
os.makedirs(ADMIN_SVO_CHARTS_DIR, exist_ok=True)

# Preset URL collections for quick botanical research
BOTANICAL_URL_COLLECTIONS = {
    'orchid_care_sites': [
        'https://www.aos.org/orchids.aspx',
        'https://www.orchidcareexpert.com/',
        'https://www.gardeningknowhow.com/ornamental/flowers/orchid',
        'https://www.repotme.com/orchid-care/',
        'https://orchidbliss.com/'
    ],
    'scientific_databases': [
        'https://www.gbif.org/species/search?q=orchidaceae',
        'https://wcsp.science.kew.org.uk/',
        'https://www.catalogueoflife.org/data/taxon/62WJZ',
        'https://plants.jstor.org/'
    ],
    'society_resources': [
        'https://www.aos.org/',
        'https://www.orchidsociety.org/',
        'https://www.britishorchids.org.uk/',
        'https://www.orchid.or.jp/orchid/english/'
    ],
    'cultivation_guides': [
        'https://mrfothergill.co.uk/growing-guides/growing-orchids',
        'https://www.rhs.org.uk/plants/orchids/growing-guide',
        'https://extension.oregonstate.edu/gardening/flowers-shrubs-trees/orchids-indoors'
    ]
}

# Advanced SVO patterns for botanical analysis
BOTANICAL_SVO_PATTERNS = {
    'growth_patterns': [
        r'(\b[A-Z]\w+\b)\s+(grows?|develops?|matures?|elongates?)\s+(in|during|under)\s+(\b\w+(?:\s+\w+){0,3}\b)',
        r'(\b\w+orchid\b|\b\w+aceae\b|\b[A-Z]\w+\b)\s+(requires?|needs?|prefers?)\s+(\b\w+(?:\s+\w+){0,2}\b)'
    ],
    'flowering_behavior': [
        r'(\b[A-Z]\w+\b)\s+(blooms?|flowers?|produces?\s+flowers?)\s+(in|during|from)\s+(\b\w+(?:\s+\w+){0,2}\b)',
        r'(\b\w+\b)\s+(triggers?|initiates?|stimulates?)\s+(flowering|blooming|budding)'
    ],
    'environmental_needs': [
        r'(\b[A-Z]\w+\b)\s+(thrives?|survives?|adapts?)\s+(in|under|with)\s+(\b\w+(?:\s+\w+){0,3}\b)',
        r'(\b\w+\b)\s+(tolerates?|withstands?|endures?)\s+(extreme|high|low|minimal)\s+(\b\w+(?:\s+\w+){0,2}\b)'
    ],
    'care_relationships': [
        r'(\bwater(?:ing)?\b|\bfertiliz(?:ing|er)\b|\blight(?:ing)?\b|\bhumidity\b)\s+(affects?|influences?|determines?)\s+(\b\w+(?:\s+\w+){0,2}\b)',
        r'(\b\w+\b)\s+(causes?|prevents?|reduces?)\s+(disease|pest|problem|issue)'
    ]
}

@admin_svo.route('/admin/svo-research')
@admin_required
def svo_research_dashboard():
    """Main admin SVO research dashboard"""
    # Get recent sessions for quick access
    recent_sessions = SvoAnalysisSession.query.order_by(
        SvoAnalysisSession.created_at.desc()
    ).limit(10).all()
    
    # Get analysis statistics
    stats = {
        'total_sessions': SvoAnalysisSession.query.count(),
        'completed_sessions': SvoAnalysisSession.query.filter_by(status='completed').count(),
        'total_svo_tuples': SvoResult.query.count(),
        'unique_subjects': db.session.query(SvoResult.subject_clean).distinct().count(),
        'unique_verbs': db.session.query(SvoResult.verb_clean).distinct().count(),
        'unique_objects': db.session.query(SvoResult.object_clean).distinct().count()
    }
    
    return render_template('admin/svo_research_dashboard.html', 
                         recent_sessions=recent_sessions,
                         stats=stats,
                         url_collections=BOTANICAL_URL_COLLECTIONS)

@admin_svo.route('/admin/svo-research/bulk-analyze', methods=['POST'])
@admin_required
def bulk_svo_analysis():
    """Start bulk SVO analysis with advanced configuration"""
    try:
        data = request.get_json()
        
        # Extract configuration
        session_name = data.get('session_name', f'Bulk Analysis {datetime.now().strftime("%Y-%m-%d %H:%M")}')
        urls = data.get('urls', [])
        collection_type = data.get('collection_type', 'custom')
        
        # Advanced configuration options
        config = {
            'max_retries': int(data.get('max_retries', 3)),
            'timeout_seconds': int(data.get('timeout_seconds', 15)),
            'extraction_patterns': data.get('extraction_patterns', 'all'),
            'min_context_length': int(data.get('min_context_length', 10)),
            'max_results_per_url': int(data.get('max_results_per_url', 500)),
            'include_scientific_terms': data.get('include_scientific_terms', True),
            'filter_noise': data.get('filter_noise', True)
        }
        
        # Use preset collection if specified
        if collection_type in BOTANICAL_URL_COLLECTIONS:
            urls = BOTANICAL_URL_COLLECTIONS[collection_type]
        
        if not urls:
            return jsonify({'error': 'No URLs provided for analysis'}), 400
        
        # Create analysis session
        session = SvoAnalysisSession(
            session_name=session_name,
            urls=urls,
            max_retries=config['max_retries'],
            timeout_seconds=config['timeout_seconds']
        )
        db.session.add(session)
        db.session.commit()
        
        # Start background analysis with enhanced configuration
        from threading import Thread
        thread = Thread(target=enhanced_background_analysis, 
                       args=(session.id, urls, config))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True, 
            'session_id': session.id,
            'message': f'Started bulk analysis of {len(urls)} URLs'
        })
        
    except Exception as e:
        logger.error(f"Error starting bulk analysis: {e}")
        return jsonify({'error': str(e)}), 500

def enhanced_background_analysis(session_id, urls, config):
    """Enhanced background SVO analysis with botanical focus"""
    
    async def run_enhanced_analysis():
        session = SvoAnalysisSession.query.get(session_id)
        if not session:
            logger.error(f"Session {session_id} not found")
            return
        
        try:
            session.status = 'running'
            session.started_at = datetime.utcnow()
            db.session.commit()
            
            total_urls = len(urls)
            all_svo_results = []
            failed_urls = []
            botanical_insights = defaultdict(list)
            
            # Enhanced extraction patterns based on configuration
            patterns_to_use = BOTANICAL_SVO_PATTERNS['growth_patterns'] + \
                            BOTANICAL_SVO_PATTERNS['flowering_behavior'] + \
                            BOTANICAL_SVO_PATTERNS['environmental_needs'] + \
                            BOTANICAL_SVO_PATTERNS['care_relationships']
            
            if config['extraction_patterns'] != 'all':
                patterns_to_use = BOTANICAL_SVO_PATTERNS.get(
                    config['extraction_patterns'], patterns_to_use
                )
            
            async with aiohttp.ClientSession() as http_session:
                for i, url in enumerate(urls):
                    try:
                        # Update progress
                        session.current_url_index = i
                        session.progress_percent = int((i / total_urls) * 100)
                        db.session.commit()
                        
                        # Fetch content with configured timeout
                        content, error = await fetch_url_content(http_session, url)
                        
                        if content:
                            # Enhanced SVO extraction with botanical focus
                            svo_tuples = enhanced_parse_svo(
                                content, url, patterns_to_use, config
                            )
                            
                            # Limit results per URL if configured
                            if config['max_results_per_url'] > 0:
                                svo_tuples = svo_tuples[:config['max_results_per_url']]
                            
                            # Store results and botanical insights
                            for subject, verb, obj, context, confidence, category in svo_tuples:
                                svo_result = SvoResult(
                                    session_id=session_id,
                                    source_url=url,
                                    subject=subject,
                                    verb=verb,
                                    object=obj,
                                    subject_clean=clean_svo_text(subject),
                                    verb_clean=clean_svo_text(verb),
                                    object_clean=clean_svo_text(obj),
                                    context_text=context,
                                    confidence_score=confidence
                                )
                                db.session.add(svo_result)
                                all_svo_results.append(svo_result)
                                botanical_insights[category].append(svo_result)
                        else:
                            failed_urls.append({'url': url, 'error': error})
                        
                        db.session.commit()
                        
                    except Exception as e:
                        logger.error(f"Error processing URL {url}: {e}")
                        failed_urls.append({'url': url, 'error': str(e)})
            
            # Generate enhanced analysis summary
            if all_svo_results:
                summary = create_enhanced_analysis_summary(
                    session_id, all_svo_results, botanical_insights, config
                )
                db.session.add(summary)
            
            # Update session completion
            session.status = 'completed'
            session.completed_at = datetime.utcnow()
            session.progress_percent = 100
            session.total_svo_found = len(all_svo_results)
            session.failed_urls = failed_urls if failed_urls else None
            
            db.session.commit()
            logger.info(f"Enhanced analysis completed for session {session_id}")
            
        except Exception as e:
            logger.error(f"Enhanced analysis failed for session {session_id}: {e}")
            session.status = 'failed'
            session.error_message = str(e)
            session.completed_at = datetime.utcnow()
            db.session.commit()
    
    # Run async function in thread
    def run_in_thread():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(run_enhanced_analysis())
        except Exception as e:
            logger.error(f"Thread execution failed: {e}")
        finally:
            loop.close()
    
    import threading
    thread = threading.Thread(target=run_in_thread)
    thread.daemon = True
    thread.start()

def enhanced_parse_svo(raw_html, source_url, patterns, config):
    """Enhanced SVO extraction with botanical focus and categorization"""
    svo_list = []
    
    try:
        soup = BeautifulSoup(raw_html, "html.parser")
        
        # Remove unwanted elements for cleaner extraction
        for tag in soup(['script', 'style', 'nav', 'header', 'footer']):
            tag.decompose()
        
        # Focus on content-rich elements
        content_elements = soup.find_all([
            'p', 'div', 'article', 'section', 'li', 'td', 'th', 'blockquote'
        ])
        
        for element in content_elements:
            text = element.get_text(strip=True)
            if len(text) < config['min_context_length']:
                continue
            
            # Apply all pattern categories
            for category, pattern_list in BOTANICAL_SVO_PATTERNS.items():
                if config['extraction_patterns'] != 'all' and category != config['extraction_patterns']:
                    continue
                    
                for pattern in pattern_list:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    for match in matches:
                        if len(match) >= 3:  # At least subject, verb, object
                            subject, verb = match[0], match[1]
                            obj = ' '.join(match[2:]) if len(match) > 3 else match[2]
                            
                            # Enhanced filtering for botanical relevance
                            if config['filter_noise'] and not is_botanically_relevant(subject, verb, obj):
                                continue
                            
                            # Calculate confidence score
                            confidence = calculate_confidence_score(subject, verb, obj, text, config)
                            
                            # Extract enhanced context
                            context = extract_enhanced_context(text, subject, verb, obj)
                            
                            svo_list.append((subject, verb, obj, context, confidence, category))
        
        logger.info(f"Enhanced extraction: {len(svo_list)} SVO tuples from {source_url}")
        return svo_list
        
    except Exception as e:
        logger.error(f"Error in enhanced parsing from {source_url}: {e}")
        return []

def is_botanically_relevant(subject, verb, obj):
    """Check if SVO tuple is relevant to botanical research"""
    botanical_keywords = {
        'subjects': ['orchid', 'plant', 'flower', 'root', 'leaf', 'stem', 'bulb', 'pseudobulb', 
                    'cattleya', 'phalaenopsis', 'dendrobium', 'oncidium', 'paphiopedilum'],
        'verbs': ['grow', 'bloom', 'flower', 'thrive', 'prefer', 'need', 'require', 
                 'produce', 'develop', 'adapt', 'tolerate', 'survive'],
        'objects': ['light', 'water', 'humidity', 'temperature', 'fertilizer', 'medium', 
                   'bark', 'moss', 'season', 'environment', 'condition']
    }
    
    subject_clean = subject.lower()
    verb_clean = verb.lower()
    obj_clean = obj.lower()
    
    # Check for botanical relevance
    subject_relevant = any(kw in subject_clean for kw in botanical_keywords['subjects'])
    verb_relevant = any(kw in verb_clean for kw in botanical_keywords['verbs'])
    obj_relevant = any(kw in obj_clean for kw in botanical_keywords['objects'])
    
    return subject_relevant or verb_relevant or obj_relevant

def calculate_confidence_score(subject, verb, obj, full_text, config):
    """Calculate confidence score for SVO extraction"""
    base_score = 0.5
    
    # Length and complexity factors
    if len(subject) > 3: base_score += 0.1
    if len(verb) > 2: base_score += 0.1
    if len(obj) > 3: base_score += 0.1
    
    # Botanical relevance factor
    if is_botanically_relevant(subject, verb, obj):
        base_score += 0.2
    
    # Scientific term factor
    if config['include_scientific_terms']:
        if any(char.isupper() for char in subject) or any(char.isupper() for char in obj):
            base_score += 0.1
    
    return min(1.0, base_score)

def extract_enhanced_context(text, subject, verb, obj):
    """Extract enhanced context around SVO tuple"""
    # Find the position of the SVO pattern in text
    pattern = f"{subject}.*{verb}.*{obj}"
    match = re.search(pattern, text, re.IGNORECASE)
    
    if match:
        start, end = match.span()
        # Extract 150 characters before and after
        context_start = max(0, start - 150)
        context_end = min(len(text), end + 150)
        context = text[context_start:context_end].strip()
        
        # Clean up context
        context = re.sub(r'\s+', ' ', context)
        return context
    
    # Fallback to simple context
    return text[:200].strip()

def create_enhanced_analysis_summary(session_id, results, botanical_insights, config):
    """Create enhanced analysis summary with botanical categorization"""
    # Basic frequency analysis
    cleaned_svo_list = [(r.subject_clean, r.verb_clean, r.object_clean) for r in results]
    analysis = analyze_svo_results(cleaned_svo_list)
    
    # Botanical category analysis
    category_stats = {}
    for category, category_results in botanical_insights.items():
        category_stats[category] = {
            'count': len(category_results),
            'top_subjects': Counter([r.subject_clean for r in category_results]).most_common(5),
            'top_verbs': Counter([r.verb_clean for r in category_results]).most_common(5),
            'top_objects': Counter([r.object_clean for r in category_results]).most_common(5)
        }
    
    # Create enhanced charts
    chart_paths = create_enhanced_charts(analysis, botanical_insights, session_id)
    
    # Export comprehensive data
    export_paths = create_comprehensive_exports(results, botanical_insights, session_id, config)
    
    # Create enhanced summary
    summary = SvoAnalysisSummary(
        session_id=session_id,
        subject_frequencies=dict(analysis['subject_freq']),
        verb_frequencies=dict(analysis['verb_freq']),
        object_frequencies=dict(analysis['object_freq']),
        total_tuples=analysis['total_svo'],
        unique_subjects=analysis['unique_subjects'],
        unique_verbs=analysis['unique_verbs'],
        unique_objects=analysis['unique_objects'],
        subject_chart_path=chart_paths.get('subject_chart_path'),
        verb_chart_path=chart_paths.get('verb_chart_path'),
        object_chart_path=chart_paths.get('object_chart_path'),
        csv_export_path=export_paths.get('csv_path')
    )
    
    return summary

def create_enhanced_charts(analysis, botanical_insights, session_id):
    """Create enhanced charts with botanical categorization"""
    chart_paths = {}
    
    try:
        # Set style for professional charts
        plt.style.use('seaborn-v0_8')
        colors = ['#3aa681', '#6a3fb5', '#ff6b6b', '#4ecdc4', '#45b7d1']
        
        # 1. Standard frequency charts
        for component, counter in [('subject', analysis['subject_freq']), 
                                 ('verb', analysis['verb_freq']), 
                                 ('object', analysis['object_freq'])]:
            
            top_items = counter.most_common(15)
            if not top_items:
                continue
                
            labels, counts = zip(*top_items)
            
            plt.figure(figsize=(14, 8))
            bars = plt.bar(labels, counts, color=colors[0], alpha=0.8, edgecolor='white')
            
            plt.title(f'Top {len(top_items)} {component.title()}s in Botanical SVO Analysis', 
                     fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
            plt.xlabel(f'{component.title()}s', fontsize=12, fontweight='bold')
            plt.ylabel('Frequency', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                        str(count), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.grid(axis='y', alpha=0.3)
            
            chart_filename = f'{session_id}_{component}_enhanced.png'
            chart_path = os.path.join(ADMIN_SVO_CHARTS_DIR, chart_filename)
            plt.savefig(chart_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            chart_paths[f'{component}_chart_path'] = f'/static/admin_svo_charts/{chart_filename}'
        
        # 2. Botanical category distribution chart
        if botanical_insights:
            categories = list(botanical_insights.keys())
            counts = [len(results) for results in botanical_insights.values()]
            
            plt.figure(figsize=(12, 8))
            bars = plt.bar(categories, counts, color=colors[:len(categories)], 
                          alpha=0.8, edgecolor='white')
            
            plt.title('SVO Distribution by Botanical Category', 
                     fontsize=16, fontweight='bold', color='#2c3e50', pad=20)
            plt.xlabel('Botanical Categories', fontsize=12, fontweight='bold')
            plt.ylabel('Number of SVO Tuples', fontsize=12, fontweight='bold')
            plt.xticks(rotation=45, ha='right')
            
            for bar, count in zip(bars, counts):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(counts)*0.01,
                        str(count), ha='center', va='bottom', fontweight='bold')
            
            plt.tight_layout()
            plt.grid(axis='y', alpha=0.3)
            
            category_chart = f'{session_id}_category_distribution.png'
            category_path = os.path.join(ADMIN_SVO_CHARTS_DIR, category_chart)
            plt.savefig(category_path, dpi=300, bbox_inches='tight', facecolor='white')
            plt.close()
            
            chart_paths['category_chart_path'] = f'/static/admin_svo_charts/{category_chart}'
        
        logger.info(f"Created enhanced charts for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error creating enhanced charts: {e}")
    
    return chart_paths

def create_comprehensive_exports(results, botanical_insights, session_id, config):
    """Create comprehensive export files for research"""
    export_paths = {}
    
    try:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 1. Enhanced CSV with botanical categories
        csv_filename = f'{session_id}_comprehensive_analysis_{timestamp}.csv'
        csv_path = os.path.join(ADMIN_SVO_EXPORTS_DIR, csv_filename)
        
        # Prepare data with categories
        export_data = []
        for result in results:
            # Find which category this result belongs to
            category = 'general'
            for cat, cat_results in botanical_insights.items():
                if result in cat_results:
                    category = cat
                    break
            
            export_data.append({
                'Source_URL': result.source_url,
                'Subject': result.subject,
                'Verb': result.verb,
                'Object': result.object,
                'Subject_Clean': result.subject_clean,
                'Verb_Clean': result.verb_clean,
                'Object_Clean': result.object_clean,
                'Context': result.context_text or '',
                'Confidence_Score': result.confidence_score,
                'Botanical_Category': category,
                'Created_At': result.created_at.isoformat() if result.created_at else ''
            })
        
        # Save as CSV
        df = pd.DataFrame(export_data)
        df.to_csv(csv_path, index=False, encoding='utf-8')
        export_paths['csv_path'] = f'/static/admin_svo_exports/{csv_filename}'
        
        # 2. Excel export with multiple sheets
        excel_filename = f'{session_id}_research_export_{timestamp}.xlsx'
        excel_path = os.path.join(ADMIN_SVO_EXPORTS_DIR, excel_filename)
        
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='SVO_Analysis', index=False)
            
            # Category summary sheet
            category_summary = []
            for category, cat_results in botanical_insights.items():
                subjects = [r.subject_clean for r in cat_results]
                verbs = [r.verb_clean for r in cat_results]
                objects = [r.object_clean for r in cat_results]
                
                category_summary.append({
                    'Category': category,
                    'Total_Tuples': len(cat_results),
                    'Unique_Subjects': len(set(subjects)),
                    'Unique_Verbs': len(set(verbs)),
                    'Unique_Objects': len(set(objects)),
                    'Top_Subject': Counter(subjects).most_common(1)[0][0] if subjects else '',
                    'Top_Verb': Counter(verbs).most_common(1)[0][0] if verbs else '',
                    'Top_Object': Counter(objects).most_common(1)[0][0] if objects else ''
                })
            
            category_df = pd.DataFrame(category_summary)
            category_df.to_excel(writer, sheet_name='Category_Summary', index=False)
            
            # Frequency analysis sheet
            freq_data = []
            all_subjects = [r.subject_clean for r in results]
            all_verbs = [r.verb_clean for r in results]
            all_objects = [r.object_clean for r in results]
            
            for item, count in Counter(all_subjects).most_common(50):
                freq_data.append({'Type': 'Subject', 'Term': item, 'Frequency': count})
            for item, count in Counter(all_verbs).most_common(50):
                freq_data.append({'Type': 'Verb', 'Term': item, 'Frequency': count})
            for item, count in Counter(all_objects).most_common(50):
                freq_data.append({'Type': 'Object', 'Term': item, 'Frequency': count})
            
            freq_df = pd.DataFrame(freq_data)
            freq_df.to_excel(writer, sheet_name='Frequency_Analysis', index=False)
        
        export_paths['excel_path'] = f'/static/admin_svo_exports/{excel_filename}'
        
        # 3. JSON export for API access
        json_filename = f'{session_id}_api_export_{timestamp}.json'
        json_path = os.path.join(ADMIN_SVO_EXPORTS_DIR, json_filename)
        
        json_data = {
            'session_id': session_id,
            'export_timestamp': timestamp,
            'configuration': config,
            'summary': {
                'total_tuples': len(results),
                'unique_subjects': len(set(r.subject_clean for r in results)),
                'unique_verbs': len(set(r.verb_clean for r in results)),
                'unique_objects': len(set(r.object_clean for r in results))
            },
            'botanical_insights': {
                cat: {
                    'count': len(cat_results),
                    'sample_tuples': [(r.subject, r.verb, r.object) for r in cat_results[:5]]
                } for cat, cat_results in botanical_insights.items()
            },
            'data': export_data
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        export_paths['json_path'] = f'/static/admin_svo_exports/{json_filename}'
        
        logger.info(f"Created comprehensive exports for session {session_id}")
        
    except Exception as e:
        logger.error(f"Error creating comprehensive exports: {e}")
    
    return export_paths

@admin_svo.route('/admin/svo-research/session/<session_id>')
@admin_required
def view_research_session(session_id):
    """View detailed results from a research session"""
    session = SvoAnalysisSession.query.get_or_404(session_id)
    summary = SvoAnalysisSummary.query.filter_by(session_id=session_id).first()
    
    # Get sample results for preview
    sample_results = SvoResult.query.filter_by(session_id=session_id).limit(100).all()
    
    # Calculate additional analytics
    analytics = calculate_session_analytics(session_id)
    
    return render_template('admin/svo_research_session.html',
                         session=session,
                         summary=summary,
                         sample_results=sample_results,
                         analytics=analytics)

def calculate_session_analytics(session_id):
    """Calculate advanced analytics for a session"""
    results = SvoResult.query.filter_by(session_id=session_id).all()
    
    if not results:
        return {}
    
    # URL-based analysis
    url_stats = defaultdict(int)
    for result in results:
        url_stats[result.source_url] += 1
    
    # Confidence score analysis
    confidence_scores = [r.confidence_score for r in results if r.confidence_score]
    avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
    
    # Context length analysis
    context_lengths = [len(r.context_text or '') for r in results]
    avg_context_length = sum(context_lengths) / len(context_lengths) if context_lengths else 0
    
    return {
        'url_distribution': dict(url_stats),
        'most_productive_url': max(url_stats.items(), key=lambda x: x[1]) if url_stats else None,
        'average_confidence': round(avg_confidence, 3),
        'average_context_length': round(avg_context_length, 1),
        'high_confidence_count': len([s for s in confidence_scores if s > 0.8]),
        'total_urls_processed': len(url_stats)
    }

@admin_svo.route('/admin/svo-research/historical-analysis')
@admin_required
def historical_analysis():
    """Historical analysis and trends across sessions"""
    # Get all completed sessions
    sessions = SvoAnalysisSession.query.filter_by(status='completed').order_by(
        SvoAnalysisSession.completed_at.desc()
    ).all()
    
    # Calculate trends over time
    trends = calculate_historical_trends(sessions)
    
    return render_template('admin/svo_historical_analysis.html',
                         sessions=sessions,
                         trends=trends)

def calculate_historical_trends(sessions):
    """Calculate historical trends across sessions"""
    if not sessions:
        return {}
    
    # Monthly aggregation
    monthly_stats = defaultdict(lambda: {
        'sessions': 0,
        'total_tuples': 0,
        'unique_subjects': set(),
        'unique_verbs': set(),
        'unique_objects': set()
    })
    
    for session in sessions:
        if session.completed_at:
            month_key = session.completed_at.strftime('%Y-%m')
            monthly_stats[month_key]['sessions'] += 1
            monthly_stats[month_key]['total_tuples'] += session.total_svo_found or 0
            
            # Get results for this session to calculate unique terms
            results = SvoResult.query.filter_by(session_id=session.id).all()
            for result in results:
                monthly_stats[month_key]['unique_subjects'].add(result.subject_clean)
                monthly_stats[month_key]['unique_verbs'].add(result.verb_clean)
                monthly_stats[month_key]['unique_objects'].add(result.object_clean)
    
    # Convert sets to counts for JSON serialization
    trends = {}
    for month, stats in monthly_stats.items():
        trends[month] = {
            'sessions': stats['sessions'],
            'total_tuples': stats['total_tuples'],
            'unique_subjects': len(stats['unique_subjects']),
            'unique_verbs': len(stats['unique_verbs']),
            'unique_objects': len(stats['unique_objects'])
        }
    
    return trends

@admin_svo.route('/admin/svo-research/export-all', methods=['POST'])
@admin_required
def export_all_data():
    """Export all SVO research data as comprehensive research package"""
    try:
        export_format = request.json.get('format', 'zip')
        date_range = request.json.get('date_range', 'all')
        
        # Get sessions based on date range
        query = SvoAnalysisSession.query.filter_by(status='completed')
        
        if date_range != 'all':
            if date_range == 'last_month':
                cutoff = datetime.now() - timedelta(days=30)
                query = query.filter(SvoAnalysisSession.completed_at >= cutoff)
            elif date_range == 'last_week':
                cutoff = datetime.now() - timedelta(days=7)
                query = query.filter(SvoAnalysisSession.completed_at >= cutoff)
        
        sessions = query.all()
        
        if export_format == 'zip':
            # Create comprehensive ZIP package
            zip_buffer = io.BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add session summaries
                sessions_data = []
                for session in sessions:
                    sessions_data.append({
                        'id': session.id,
                        'name': session.session_name,
                        'created_at': session.created_at.isoformat() if session.created_at else None,
                        'completed_at': session.completed_at.isoformat() if session.completed_at else None,
                        'total_svo_found': session.total_svo_found,
                        'urls_count': len(session.urls) if session.urls and isinstance(session.urls, list) else 0
                    })
                
                zip_file.writestr('sessions_summary.json', 
                                json.dumps(sessions_data, indent=2))
                
                # Add detailed results for each session
                for session in sessions[:10]:  # Limit to 10 most recent to prevent huge files
                    results = SvoResult.query.filter_by(session_id=session.id).all()
                    results_data = [result.to_dict() for result in results]
                    
                    zip_file.writestr(f'session_{session.id}_results.json',
                                    json.dumps(results_data, indent=2))
                
                # Add overall statistics
                overall_stats = {
                    'total_sessions': len(sessions),
                    'total_svo_tuples': sum(s.total_svo_found or 0 for s in sessions),
                    'date_range': date_range,
                    'export_timestamp': datetime.now().isoformat(),
                    'export_format': export_format
                }
                
                zip_file.writestr('export_metadata.json',
                                json.dumps(overall_stats, indent=2))
            
            zip_buffer.seek(0)
            
            # Save the ZIP file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            zip_filename = f'svo_research_export_{timestamp}.zip'
            zip_path = os.path.join(ADMIN_SVO_EXPORTS_DIR, zip_filename)
            
            with open(zip_path, 'wb') as f:
                f.write(zip_buffer.getvalue())
            
            return jsonify({
                'success': True,
                'download_url': f'/static/admin_svo_exports/{zip_filename}',
                'filename': zip_filename,
                'sessions_count': len(sessions)
            })
            
    except Exception as e:
        logger.error(f"Error exporting all data: {e}")
        return jsonify({'error': str(e)}), 500

@admin_svo.route('/admin/api/svo-session-status/<session_id>')
@admin_required
def get_session_status(session_id):
    """Get real-time status of analysis session"""
    session = SvoAnalysisSession.query.get_or_404(session_id)
    
    status_data = {
        'id': session.id,
        'status': session.status,
        'progress_percent': session.progress_percent,
        'current_url_index': session.current_url_index,
        'total_urls': len(session.urls) if session.urls and isinstance(session.urls, list) else 0,
        'total_svo_found': session.total_svo_found or 0,
        'started_at': session.started_at.isoformat() if session.started_at else None,
        'completed_at': session.completed_at.isoformat() if session.completed_at else None,
        'error_message': session.error_message,
        'failed_urls_count': len(session.failed_urls) if session.failed_urls and isinstance(session.failed_urls, list) else 0
    }
    
    return jsonify(status_data)

@admin_svo.route('/admin/svo-research/delete-session/<session_id>', methods=['DELETE'])
@admin_required
def delete_research_session(session_id):
    """Delete a research session and all associated data"""
    try:
        session = SvoAnalysisSession.query.get_or_404(session_id)
        
        # Delete associated results
        SvoResult.query.filter_by(session_id=session_id).delete()
        
        # Delete summary
        SvoAnalysisSummary.query.filter_by(session_id=session_id).delete()
        
        # Delete session
        db.session.delete(session)
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'Session {session_id} deleted'})
        
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({'error': str(e)}), 500

# Register the blueprint with the app
from app import app
app.register_blueprint(admin_svo, url_prefix='')