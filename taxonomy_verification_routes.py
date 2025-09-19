"""
Flask routes for the Taxonomy Verification System
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, session
from taxonomy_verification_system import TaxonomyVerificationSystem
from models import OrchidRecord, db
from functools import wraps
import logging

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return jsonify({'success': False, 'error': 'Admin authentication required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Create blueprint
taxonomy_bp = Blueprint('taxonomy_verification', __name__, url_prefix='/admin/taxonomy')

@taxonomy_bp.route('/')
@admin_required
def verification_panel():
    """Main taxonomy verification panel"""
    return render_template('admin/taxonomy_verification.html')

@taxonomy_bp.route('/scan-potinara', methods=['POST'])
@admin_required
def scan_potinara():
    """Scan all Potinara records for misclassifications"""
    try:
        verifier = TaxonomyVerificationSystem()
        issues = verifier.scan_potinara_issues()
        
        # Get statistics
        potinara_count = OrchidRecord.query.filter_by(genus='Potinara').count()
        
        return jsonify({
            'success': True,
            'issues': issues,
            'total_scanned': potinara_count,
            'issues_found': len(issues),
            'message': f'Scanned {potinara_count} Potinara records, found {len(issues)} potential issues'
        })
        
    except Exception as e:
        logger.error(f"Error scanning Potinara records: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@taxonomy_bp.route('/scan-all', methods=['POST'])
@admin_required
def scan_all():
    """Scan all records for taxonomy issues"""
    try:
        verifier = TaxonomyVerificationSystem()
        issues = verifier.scan_all_records()
        
        # Get total count
        total_count = OrchidRecord.query.count()
        
        return jsonify({
            'success': True,
            'issues': issues,
            'total_scanned': total_count,
            'issues_found': len(issues),
            'message': f'Scanned {total_count} records, found {len(issues)} potential issues'
        })
        
    except Exception as e:
        logger.error(f"Error scanning all records: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@taxonomy_bp.route('/apply-single', methods=['POST'])
@admin_required
def apply_single_correction():
    """Apply a single taxonomy correction"""
    try:
        data = request.get_json()
        record_id = data.get('record_id')
        
        if not record_id:
            return jsonify({'success': False, 'error': 'No record ID provided'}), 400
        
        # Get the record
        record = OrchidRecord.query.get(record_id)
        if not record:
            return jsonify({'success': False, 'error': 'Record not found'}), 404
        
        # Analyze and get correction
        verifier = TaxonomyVerificationSystem()
        analysis = verifier.analyze_filename_vs_classification(record)
        
        if not analysis['suggested_corrections']:
            return jsonify({'success': False, 'error': 'No corrections available'}), 400
        
        correction = analysis['suggested_corrections'][0]
        if correction['confidence'] < 0.5:
            return jsonify({'success': False, 'error': 'Confidence too low for automatic correction'}), 400
        
        # Apply the correction
        old_genus = record.genus
        record.genus = correction['to_genus']
        
        # Update scientific name if it exists
        if record.scientific_name:
            record.scientific_name = record.scientific_name.replace(old_genus, correction['to_genus'], 1)
        
        db.session.commit()
        
        logger.info(f"Applied taxonomy correction for record {record_id}: {old_genus} → {correction['to_genus']}")
        
        return jsonify({
            'success': True,
            'message': f'Updated record {record_id}: {old_genus} → {correction["to_genus"]}',
            'old_genus': old_genus,
            'new_genus': correction['to_genus']
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying single correction: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@taxonomy_bp.route('/apply-batch', methods=['POST'])
@admin_required
def apply_batch_corrections():
    """Apply multiple taxonomy corrections in batch"""
    try:
        data = request.get_json()
        record_ids = data.get('record_ids', [])
        
        if not record_ids:
            return jsonify({'success': False, 'error': 'No record IDs provided'}), 400
        
        verifier = TaxonomyVerificationSystem()
        corrections_applied = 0
        errors = []
        
        for record_id in record_ids:
            try:
                record = OrchidRecord.query.get(record_id)
                if not record:
                    errors.append(f"Record {record_id} not found")
                    continue
                
                analysis = verifier.analyze_filename_vs_classification(record)
                if not analysis['suggested_corrections']:
                    errors.append(f"No corrections for record {record_id}")
                    continue
                
                correction = analysis['suggested_corrections'][0]
                if correction['confidence'] < 0.7:  # Higher threshold for batch operations
                    errors.append(f"Low confidence for record {record_id}")
                    continue
                
                # Apply correction
                old_genus = record.genus
                record.genus = correction['to_genus']
                
                if record.scientific_name:
                    record.scientific_name = record.scientific_name.replace(old_genus, correction['to_genus'], 1)
                
                corrections_applied += 1
                logger.info(f"Batch correction applied for record {record_id}: {old_genus} → {correction['to_genus']}")
                
            except Exception as e:
                errors.append(f"Error with record {record_id}: {str(e)}")
                continue
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'corrections_applied': corrections_applied,
            'errors': errors,
            'message': f'Applied {corrections_applied} corrections with {len(errors)} errors'
        })
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error applying batch corrections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@taxonomy_bp.route('/statistics')
@admin_required
def get_statistics():
    """Get taxonomy statistics"""
    try:
        verifier = TaxonomyVerificationSystem()
        stats = verifier.get_taxonomy_statistics()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        logger.error(f"Error getting taxonomy statistics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@taxonomy_bp.route('/export-corrections/<genus>')
@admin_required
def export_corrections(genus):
    """Export corrections for a specific genus"""
    try:
        verifier = TaxonomyVerificationSystem()
        issues = verifier.scan_all_records(genus)
        
        # Generate CSV content
        csv_lines = ['ID,Current Genus,Current Species,Suggested Genus,Confidence,Issue Type,Filename Analysis']
        
        for issue in issues:
            correction = issue['suggested_corrections'][0] if issue['suggested_corrections'] else {}
            filename_analysis = '; '.join([f"{fa['source']} → {fa['suggested_genus']}" 
                                         for fa in issue['filename_analysis']])
            
            csv_lines.append(f"{issue['record_id']},{issue['current_genus']},{issue['current_species'] or ''},"
                           f"{correction.get('to_genus', '')},{correction.get('confidence', 0):.3f},"
                           f"{issue['issue_type']},{filename_analysis}")
        
        csv_content = '\n'.join(csv_lines)
        
        return jsonify({
            'success': True,
            'csv_content': csv_content,
            'filename': f'taxonomy_corrections_{genus}.csv'
        })
        
    except Exception as e:
        logger.error(f"Error exporting corrections: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

def register_taxonomy_routes(app):
    """Register taxonomy verification routes with Flask app"""
    app.register_blueprint(taxonomy_bp)
    logger.info("🔍 Taxonomy Verification routes registered successfully")