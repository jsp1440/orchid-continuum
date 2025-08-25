#!/usr/bin/env python3
"""
GBIF Integration Routes
======================
Web interface and API endpoints for GBIF orchid data collection
Part of The Orchid Continuum - Five Cities Orchid Society
"""

from flask import Blueprint, request, jsonify, render_template, redirect, url_for, flash
from gbif_orchid_scraper import GBIFOrchidIntegrator, run_gbif_collection
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
gbif_bp = Blueprint('gbif', __name__, url_prefix='/gbif')

@gbif_bp.route('/')
def gbif_dashboard():
    """GBIF integration dashboard"""
    return render_template('gbif_dashboard.html')

@gbif_bp.route('/collect', methods=['GET', 'POST'])
def collect_orchids():
    """Start GBIF orchid collection process"""
    if request.method == 'POST':
        try:
            # Get parameters from form
            max_records = int(request.form.get('max_records', 1000))
            country = request.form.get('country', '').strip() or None
            
            # Validate max_records (reasonable limits)
            if max_records > 10000:
                flash('Maximum 10,000 records per collection run', 'warning')
                max_records = 10000
            elif max_records < 1:
                flash('Must collect at least 1 record', 'error')
                return redirect(url_for('gbif.collect_orchids'))
            
            # Start collection process
            logger.info(f"🚀 Starting GBIF collection: {max_records} records, country: {country or 'All'}")
            
            stats = run_gbif_collection(max_records=max_records, country=country)
            
            # Show results
            flash(f"✅ Collection Complete! Processed: {stats['processed']}, Saved: {stats['saved']} new records", 'success')
            
            return render_template('gbif_results.html', stats=stats)
            
        except ValueError as e:
            flash('Invalid number format for max records', 'error')
            return redirect(url_for('gbif.collect_orchids'))
        except Exception as e:
            logger.error(f"❌ Collection error: {e}")
            flash(f'Collection error: {str(e)}', 'error')
            return redirect(url_for('gbif.collect_orchids'))
    
    # GET request - show collection form
    return render_template('gbif_collect.html')

@gbif_bp.route('/api/status')
def api_status():
    """Get GBIF API connection status"""
    try:
        integrator = GBIFOrchidIntegrator()
        
        # Test API connectivity
        test_response = integrator.session.get(
            f"{integrator.base_url}/occurrence/count",
            params={'familyKey': 7711},  # Orchidaceae
            timeout=10
        )
        
        status = {
            'api_connected': test_response.status_code == 200,
            'api_key_configured': False,  # GBIF uses public API
            'total_orchid_occurrences': test_response.json() if test_response.status_code == 200 else 0
        }
        
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"❌ API status error: {e}")
        return jsonify({
            'api_connected': False,
            'api_key_configured': False,
            'error': str(e)
        })

@gbif_bp.route('/api/search')
def api_search():
    """Search GBIF for orchid occurrences (preview)"""
    try:
        # Get search parameters
        limit = min(int(request.args.get('limit', 20)), 100)
        country = request.args.get('country', '').strip() or None
        genus = request.args.get('genus', '').strip() or None
        
        integrator = GBIFOrchidIntegrator()
        
        # Build search parameters
        params = {
            'familyKey': 7711,  # Orchidaceae
            'hasCoordinate': True,
            'limit': limit
        }
        
        if country:
            params['country'] = country
        if genus:
            params['scientificName'] = f"{genus}*"
        
        # Search GBIF
        response = integrator.session.get(
            f"{integrator.base_url}/occurrence/search",
            params=params,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Format results for display
            results = []
            for occurrence in data.get('results', []):
                results.append({
                    'scientific_name': occurrence.get('scientificName', ''),
                    'country': occurrence.get('country', ''),
                    'locality': occurrence.get('locality', ''),
                    'date': occurrence.get('eventDate', ''),
                    'collector': occurrence.get('recordedBy', ''),
                    'institution': occurrence.get('institutionCode', ''),
                    'gbif_url': f"https://www.gbif.org/occurrence/{occurrence.get('key')}"
                })
            
            return jsonify({
                'success': True,
                'count': data.get('count', 0),
                'results': results
            })
        else:
            return jsonify({
                'success': False,
                'error': f'GBIF API error: {response.status_code}'
            })
        
    except Exception as e:
        logger.error(f"❌ Search error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

@gbif_bp.route('/test')
def test_gbif():
    """Test GBIF integration with small sample"""
    try:
        logger.info("🧪 Testing GBIF integration...")
        
        # Run small test collection
        stats = run_gbif_collection(max_records=10)
        
        return jsonify({
            'success': True,
            'message': 'GBIF test completed successfully',
            'stats': stats
        })
        
    except Exception as e:
        logger.error(f"❌ GBIF test error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        })

# Country codes for the collection form
COUNTRY_CODES = {
    'US': 'United States',
    'BR': 'Brazil',
    'AU': 'Australia', 
    'CO': 'Colombia',
    'PE': 'Peru',
    'EC': 'Ecuador',
    'VE': 'Venezuela',
    'MX': 'Mexico',
    'CR': 'Costa Rica',
    'PA': 'Panama',
    'GT': 'Guatemala',
    'MY': 'Malaysia',
    'ID': 'Indonesia',
    'TH': 'Thailand',
    'PH': 'Philippines',
    'IN': 'India',
    'CN': 'China',
    'JP': 'Japan',
    'ZA': 'South Africa',
    'KE': 'Kenya',
    'TZ': 'Tanzania',
    'MG': 'Madagascar'
}

@gbif_bp.context_processor
def inject_countries():
    """Inject country codes into all GBIF templates"""
    return {'countries': COUNTRY_CODES}

logger.info("🌍 GBIF Integration routes registered successfully")