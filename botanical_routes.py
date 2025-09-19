"""
Routes for botanical database integration and enhanced metadata analysis
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import app, db
from models import OrchidRecord
from botanical_databases import search_botanical_databases, get_cultivation_recommendations, verify_botanical_accuracy
from enhanced_metadata_analyzer import analyze_orchid_with_botanical_databases
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@app.route('/botanical-search/<int:orchid_id>')
def botanical_search_route(orchid_id):
    """Search all botanical databases for orchid information"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        orchid_name = orchid.scientific_name or orchid.display_name
        search_results = search_botanical_databases(orchid_name)
        
        return render_template('botanical_search.html', 
                             orchid=orchid, 
                             search_results=search_results)
        
    except Exception as e:
        logger.error(f"Botanical search failed: {str(e)}")
        flash(f'Botanical search failed: {str(e)}', 'error')
        return redirect(url_for('orchid_detail', id=orchid_id))

@app.route('/api/botanical-search/<int:orchid_id>')
def api_botanical_search(orchid_id):
    """API endpoint for botanical database search"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        orchid_name = orchid.scientific_name or orchid.display_name
        search_results = search_botanical_databases(orchid_name)
        
        return jsonify({
            'success': True,
            'orchid_id': orchid_id,
            'orchid_name': orchid_name,
            'results': search_results
        })
        
    except Exception as e:
        logger.error(f"API botanical search failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/cultivation-guide/<int:orchid_id>')
def cultivation_guide_route(orchid_id):
    """Get comprehensive cultivation guide from multiple sources"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        orchid_name = orchid.scientific_name or orchid.display_name
        cultivation_recommendations = get_cultivation_recommendations(orchid_name)
        
        return render_template('cultivation_guide.html',
                             orchid=orchid,
                             recommendations=cultivation_recommendations)
        
    except Exception as e:
        logger.error(f"Cultivation guide failed: {str(e)}")
        flash(f'Failed to generate cultivation guide: {str(e)}', 'error')
        return redirect(url_for('orchid_detail', id=orchid_id))

@app.route('/botanical-verification/<int:orchid_id>')
def botanical_verification_route(orchid_id):
    """Verify botanical accuracy across multiple databases"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        orchid_name = orchid.scientific_name or orchid.display_name
        verification_results = verify_botanical_accuracy(orchid_name)
        
        return render_template('botanical_verification.html',
                             orchid=orchid,
                             verification=verification_results)
        
    except Exception as e:
        logger.error(f"Botanical verification failed: {str(e)}")
        flash(f'Botanical verification failed: {str(e)}', 'error')
        return redirect(url_for('orchid_detail', id=orchid_id))

@app.route('/enhanced-analysis/<int:orchid_id>', methods=['GET', 'POST'])
def enhanced_analysis_route(orchid_id):
    """Comprehensive orchid analysis using all botanical databases"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    if request.method == 'POST':
        try:
            # Perform comprehensive analysis
            analysis_results = analyze_orchid_with_botanical_databases(orchid_id)
            
            flash('Enhanced analysis completed successfully!', 'success')
            return render_template('enhanced_analysis.html',
                                 orchid=orchid,
                                 analysis=analysis_results)
        
        except Exception as e:
            logger.error(f"Enhanced analysis failed: {str(e)}")
            flash(f'Enhanced analysis failed: {str(e)}', 'error')
    
    return render_template('enhanced_analysis.html', orchid=orchid, analysis=None)

@app.route('/api/enhanced-analysis/<int:orchid_id>')
@login_required
def api_enhanced_analysis(orchid_id):
    """API endpoint for comprehensive orchid analysis"""
    try:
        analysis_results = analyze_orchid_with_botanical_databases(orchid_id)
        
        return jsonify({
            'success': True,
            'analysis': analysis_results
        })
        
    except Exception as e:
        logger.error(f"API enhanced analysis failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@app.route('/metadata-comparison/<int:orchid_id>')
def metadata_comparison_route(orchid_id):
    """Compare metadata across multiple botanical sources"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        orchid_name = orchid.scientific_name or orchid.display_name
        
        # Get data from all sources
        botanical_results = search_botanical_databases(orchid_name)
        
        # Organize for comparison view
        comparison_data = {
            'orchid': orchid,
            'orchid_name': orchid_name,
            'sources': {},
            'field_comparison': {}
        }
        
        # Extract data for each source
        for source, data in botanical_results.get('data_found', {}).items():
            if data.get('found'):
                comparison_data['sources'][source] = data
        
        # Compare common fields across sources
        common_fields = ['scientific_name', 'cultivation', 'distribution', 'characteristics']
        
        for field in common_fields:
            comparison_data['field_comparison'][field] = {}
            for source, data in comparison_data['sources'].items():
                if field in data:
                    comparison_data['field_comparison'][field][source] = data[field]
        
        return render_template('metadata_comparison.html', 
                             comparison=comparison_data)
        
    except Exception as e:
        logger.error(f"Metadata comparison failed: {str(e)}")
        flash(f'Metadata comparison failed: {str(e)}', 'error')
        return redirect(url_for('orchid_detail', id=orchid_id))

@app.route('/batch-botanical-analysis', methods=['GET', 'POST'])
@login_required  
def batch_botanical_analysis_route():
    """Perform botanical analysis on multiple orchids"""
    if request.method == 'POST':
        try:
            orchid_ids = request.form.getlist('orchid_ids')
            
            if not orchid_ids:
                flash('No orchids selected for analysis', 'error')
                return redirect(request.url)
            
            results = []
            for orchid_id in orchid_ids:
                try:
                    orchid_id = int(orchid_id)
                    analysis_result = analyze_orchid_with_botanical_databases(orchid_id)
                    results.append({
                        'orchid_id': orchid_id,
                        'success': True,
                        'analysis': analysis_result
                    })
                except Exception as e:
                    results.append({
                        'orchid_id': orchid_id,
                        'success': False,
                        'error': str(e)
                    })
            
            return render_template('batch_analysis_results.html', results=results)
            
        except Exception as e:
            logger.error(f"Batch botanical analysis failed: {str(e)}")
            flash(f'Batch analysis failed: {str(e)}', 'error')
    
    # GET request - show selection form
    orchids = OrchidRecord.query.filter(
        OrchidRecord.scientific_name.isnot(None)
    ).limit(50).all()
    
    return render_template('batch_botanical_analysis.html', orchids=orchids)

@app.route('/database-coverage')
def database_coverage_route():
    """Show coverage statistics across botanical databases"""
    try:
        # Get sample of orchids to test coverage
        sample_orchids = OrchidRecord.query.filter(
            OrchidRecord.scientific_name.isnot(None)
        ).limit(20).all()
        
        coverage_stats = {
            'total_orchids_tested': len(sample_orchids),
            'database_coverage': {
                'worldplants': 0,
                'ecuagenera': 0,
                'aos': 0,
                'andys_orchids': 0,
                'jays_encyclopedia': 0
            },
            'overall_coverage': 0.0
        }
        
        # Test coverage for each database
        for orchid in sample_orchids:
            orchid_name = orchid.scientific_name
            search_results = search_botanical_databases(orchid_name)
            
            for source, data in search_results.get('data_found', {}).items():
                if data.get('found'):
                    coverage_stats['database_coverage'][source] += 1
        
        # Calculate percentages
        total = coverage_stats['total_orchids_tested']
        if total > 0:
            for source in coverage_stats['database_coverage']:
                coverage_stats['database_coverage'][source] = (
                    coverage_stats['database_coverage'][source] / total * 100
                )
        
        # Calculate overall coverage
        coverage_values = list(coverage_stats['database_coverage'].values())
        coverage_stats['overall_coverage'] = sum(coverage_values) / len(coverage_values)
        
        return render_template('database_coverage.html', stats=coverage_stats)
        
    except Exception as e:
        logger.error(f"Database coverage analysis failed: {str(e)}")
        flash(f'Coverage analysis failed: {str(e)}', 'error')
        return render_template('database_coverage.html', stats=None)

@app.route('/export-botanical-analysis/<int:orchid_id>')
@login_required
def export_botanical_analysis(orchid_id):
    """Export comprehensive botanical analysis results"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    
    try:
        analysis_results = analyze_orchid_with_botanical_databases(orchid_id)
        
        # Create exportable data
        export_data = {
            'orchid_info': {
                'id': orchid.id,
                'name': orchid.get_full_name(),
                'scientific_name': orchid.scientific_name,
                'display_name': orchid.display_name
            },
            'analysis_timestamp': datetime.utcnow().isoformat(),
            'comprehensive_analysis': analysis_results,
            'export_metadata': {
                'exported_by': current_user.id if current_user.is_authenticated else 'anonymous',
                'export_date': datetime.utcnow().isoformat(),
                'version': '1.0'
            }
        }
        
        # Create JSON response
        from flask import Response
        json_data = json.dumps(export_data, indent=2, default=str)
        
        filename = f"botanical_analysis_{orchid.display_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json"
        
        return Response(
            json_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename={filename}'
            }
        )
        
    except Exception as e:
        logger.error(f"Export failed: {str(e)}")
        flash('Export failed', 'error')
        return redirect(url_for('enhanced_analysis_route', orchid_id=orchid_id))