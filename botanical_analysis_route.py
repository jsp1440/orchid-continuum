"""
Additional route for enhanced botanical analysis integration into main orchid detail page
"""
from flask import render_template, request, jsonify, flash, redirect, url_for
from app import app, db
from models import OrchidRecord
from enhanced_metadata_analyzer import analyze_orchid_with_botanical_databases
import json
import logging

logger = logging.getLogger(__name__)

@app.route('/orchid/<int:id>/botanical-analysis')
def orchid_botanical_analysis(id):
    """Enhanced orchid detail page with botanical database analysis"""
    orchid = OrchidRecord.query.get_or_404(id)
    
    try:
        # Perform comprehensive botanical analysis
        botanical_analysis = analyze_orchid_with_botanical_databases(id)
        
        # Update view count
        orchid.view_count = (orchid.view_count or 0) + 1
        try:
            db.session.commit()
        except:
            db.session.rollback()
        
        return render_template('orchid_detail_enhanced.html', 
                             orchid=orchid,
                             botanical_analysis=botanical_analysis)
        
    except Exception as e:
        logger.error(f"Botanical analysis failed for orchid {id}: {str(e)}")
        flash(f'Enhanced analysis failed: {str(e)}', 'error')
        return redirect(url_for('orchid_detail', id=id))

@app.route('/api/orchid/<int:id>/quick-botanical-check')  
def quick_botanical_check(id):
    """Quick API endpoint to check botanical database coverage for an orchid"""
    orchid = OrchidRecord.query.get_or_404(id)
    
    try:
        from botanical_databases import botanical_db
        orchid_name = orchid.scientific_name or orchid.display_name
        
        # Quick search across databases
        quick_results = {}
        for db_name, db_instance in botanical_db.databases.items():
            try:
                result = db_instance.search_orchid(orchid_name)
                quick_results[db_name] = {
                    'found': result.get('found', False),
                    'source': result.get('source', db_name),
                    'has_cultivation': 'cultivation' in result,
                    'has_distribution': 'distribution' in result
                }
            except:
                quick_results[db_name] = {'found': False, 'error': True}
        
        return jsonify({
            'success': True,
            'orchid_id': id,
            'orchid_name': orchid_name,
            'database_coverage': quick_results,
            'total_sources': len(quick_results),
            'sources_found': sum(1 for r in quick_results.values() if r.get('found'))
        })
        
    except Exception as e:
        logger.error(f"Quick botanical check failed: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        })