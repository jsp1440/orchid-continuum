"""
Report generation routes for Orchid Continuum
Handles PDF and CSV report generation with progress tracking
"""
from flask import Blueprint, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_login import login_required, current_user
import threading
import time
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from report_generator import (
    OrchidReportGenerator, ReportConfig, ReportType, OutputFormat,
    generate_data_summary_report, generate_collection_analysis_report,
    generate_custom_report, get_report_progress, cleanup_old_reports
)
import logging

logger = logging.getLogger(__name__)

# Create blueprint
report_bp = Blueprint('reports', __name__, url_prefix='/reports')

# Global report generator instance
report_gen = OrchidReportGenerator()

@report_bp.route('/')
def report_dashboard():
    """Main reports dashboard"""
    return render_template('reports/dashboard.html')

@report_bp.route('/generate')
def generate_report_page():
    """Report generation form page"""
    return render_template('reports/generate.html')

@report_bp.route('/api/generate', methods=['POST'])
def api_generate_report():
    """API endpoint to generate reports"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data or 'report_type' not in data:
            return jsonify({'error': 'Report type is required'}), 400
        
        report_type_str = data['report_type']
        if report_type_str not in [rt.value for rt in ReportType]:
            return jsonify({'error': 'Invalid report type'}), 400
        
        # Parse configuration
        config = ReportConfig(
            report_type=ReportType(report_type_str),
            output_formats=[OutputFormat(fmt) for fmt in data.get('output_formats', ['pdf'])],
            title=data.get('title', ''),
            subtitle=data.get('subtitle', ''),
            author=data.get('author', 'Orchid Continuum User'),
            include_charts=data.get('include_charts', True),
            include_images=data.get('include_images', False),
            include_metadata=data.get('include_metadata', True),
            filters=data.get('filters', {}),
            custom_queries=data.get('custom_queries', []),
            template_name=data.get('template_name', 'standard'),
            color_scheme=data.get('color_scheme', 'orchid_purple'),
            chart_style=data.get('chart_style', 'seaborn')
        )
        
        # Parse date range if provided
        if data.get('date_range'):
            try:
                start_date = datetime.fromisoformat(data['date_range']['start'])
                end_date = datetime.fromisoformat(data['date_range']['end'])
                config.date_range = (start_date, end_date)
            except (ValueError, KeyError):
                logger.warning("Invalid date range format, ignoring")
        
        # Start report generation in background thread
        def generate_with_progress():
            try:
                result = report_gen.generate_report(config)
                # Store result for retrieval (in production, use Redis or database)
                report_gen._completed_reports = getattr(report_gen, '_completed_reports', {})
                report_gen._completed_reports[result['report_id']] = result
                logger.info(f"✅ Report generation completed: {result['report_id']}")
            except Exception as e:
                logger.error(f"❌ Report generation failed: {e}")
                # Store error result
                report_gen._completed_reports = getattr(report_gen, '_completed_reports', {})
                report_gen._completed_reports[f"error_{int(time.time())}"] = {
                    'status': 'failed',
                    'error': str(e)
                }
        
        # Start background thread
        thread = threading.Thread(target=generate_with_progress)
        thread.daemon = True
        thread.start()
        
        # Return report ID for progress tracking
        report_id = list(report_gen.progress_tracker.keys())[-1] if report_gen.progress_tracker else 'unknown'
        
        return jsonify({
            'status': 'started',
            'report_id': report_id,
            'message': 'Report generation started. Use the report_id to check progress.'
        })
        
    except Exception as e:
        logger.error(f"Error in report generation API: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/progress/<report_id>')
def api_report_progress(report_id: str):
    """Get progress of report generation"""
    try:
        progress_info = get_report_progress(report_id)
        
        if not progress_info:
            return jsonify({'error': 'Report not found'}), 404
        
        return jsonify(progress_info)
        
    except Exception as e:
        logger.error(f"Error getting report progress: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/download/<report_id>/<format>')
def api_download_report(report_id: str, format: str):
    """Download generated report file"""
    try:
        # Get completed report
        completed_reports = getattr(report_gen, '_completed_reports', {})
        result = completed_reports.get(report_id)
        
        if not result:
            return jsonify({'error': 'Report not found'}), 404
        
        if result['status'] != 'success':
            return jsonify({'error': 'Report generation failed or not completed'}), 400
        
        # Get file path for requested format
        files = result.get('files', {})
        if format not in files:
            return jsonify({'error': f'Format {format} not available'}), 404
        
        file_path = files[format]
        if not os.path.exists(file_path):
            return jsonify({'error': 'Report file not found'}), 404
        
        # Determine MIME type
        mime_types = {
            'pdf': 'application/pdf',
            'excel': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'csv': 'text/csv',
            'json': 'application/json'
        }
        
        # Generate download filename
        metadata = result.get('metadata', {})
        report_type = metadata.get('report_type', 'report')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        extensions = {'pdf': 'pdf', 'excel': 'xlsx', 'csv': 'csv', 'json': 'json'}
        filename = f"orchid_{report_type}_{timestamp}.{extensions.get(format, format)}"
        
        return send_file(
            file_path,
            mimetype=mime_types.get(format, 'application/octet-stream'),
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading report: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/quick-summary')
def api_quick_summary():
    """Generate quick data summary report"""
    try:
        # Use convenience function for quick summary
        result = generate_data_summary_report(
            output_formats=['json'],
            title="Quick Data Summary",
            include_charts=False
        )
        
        if result['status'] == 'success':
            # Return the JSON data directly for quick viewing
            json_file = result['files'].get('json')
            if json_file and os.path.exists(json_file):
                import json
                with open(json_file, 'r') as f:
                    report_data = json.load(f)
                return jsonify(report_data)
        
        return jsonify({'error': 'Failed to generate quick summary'}), 500
        
    except Exception as e:
        logger.error(f"Error generating quick summary: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/templates')
def report_templates():
    """Show available report templates"""
    templates = [
        {
            'name': 'data_summary',
            'title': 'Data Summary Report',
            'description': 'Comprehensive overview of all orchid data in the system',
            'charts': ['genus_distribution', 'monthly_growth', 'data_quality_dashboard'],
            'estimated_time': '2-3 minutes',
            'formats': ['PDF', 'Excel', 'CSV']
        },
        {
            'name': 'collection_analysis',
            'title': 'Collection Analysis Report',
            'description': 'Detailed analysis of specific collection subsets with filtering options',
            'charts': ['growth_habits', 'climate_preferences', 'flowering_analysis'],
            'estimated_time': '1-2 minutes',
            'formats': ['PDF', 'Excel']
        },
        {
            'name': 'geographic_distribution',
            'title': 'Geographic Distribution Report',
            'description': 'Geographic analysis and mapping of orchid locations',
            'charts': ['geographic_distribution', 'coordinate_clusters'],
            'estimated_time': '3-4 minutes',
            'formats': ['PDF', 'Excel']
        },
        {
            'name': 'flowering_analysis',
            'title': 'Flowering Analysis Report',
            'description': 'Seasonal and phenological analysis of flowering patterns',
            'charts': ['seasonal_flowering', 'flowering_stages'],
            'estimated_time': '2-3 minutes',
            'formats': ['PDF', 'Excel']
        },
        {
            'name': 'ai_analysis_report',
            'title': 'AI Analysis Performance Report',
            'description': 'Analysis of AI system performance and confidence metrics',
            'charts': ['confidence_distribution', 'accuracy_metrics'],
            'estimated_time': '1-2 minutes',
            'formats': ['PDF', 'Excel']
        },
        {
            'name': 'system_health_report',
            'title': 'System Health Report',
            'description': 'Overall system performance and data quality metrics',
            'charts': ['health_indicators', 'performance_metrics'],
            'estimated_time': '1 minute',
            'formats': ['PDF']
        }
    ]
    
    return render_template('reports/templates.html', templates=templates)

@report_bp.route('/history')
@login_required
def report_history():
    """Show user's report generation history"""
    # In production, this would query a database for user's reports
    history = [
        {
            'id': 'report_001',
            'type': 'Data Summary Report',
            'generated_at': datetime.now() - timedelta(hours=2),
            'status': 'completed',
            'formats': ['PDF', 'Excel'],
            'file_size': '2.3 MB'
        },
        {
            'id': 'report_002',
            'type': 'Collection Analysis Report',
            'generated_at': datetime.now() - timedelta(days=1),
            'status': 'completed',
            'formats': ['PDF'],
            'file_size': '1.8 MB'
        }
    ]
    
    return render_template('reports/history.html', history=history)

@report_bp.route('/api/cleanup')
def api_cleanup_reports():
    """Clean up old report files (admin endpoint)"""
    try:
        cleanup_old_reports()
        return jsonify({'status': 'success', 'message': 'Cleanup completed'})
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({'error': str(e)}), 500

# Background task to periodically clean up old files
def start_cleanup_scheduler():
    """Start background scheduler for cleanup tasks"""
    def cleanup_task():
        while True:
            try:
                time.sleep(3600)  # Run every hour
                cleanup_old_reports()
                logger.info("🧹 Automatic cleanup completed")
            except Exception as e:
                logger.error(f"Error in automatic cleanup: {e}")
    
    thread = threading.Thread(target=cleanup_task)
    thread.daemon = True
    thread.start()
    logger.info("🔄 Started automatic cleanup scheduler")

# Initialize cleanup scheduler when module is imported
start_cleanup_scheduler()

# Additional convenience endpoints for common report types

@report_bp.route('/api/genus-analysis/<genus>')
def api_genus_analysis(genus: str):
    """Generate quick genus-specific analysis"""
    try:
        result = generate_collection_analysis_report(
            genus=genus,
            output_formats=['json'],
            title=f"Analysis Report for {genus}",
            include_charts=False
        )
        
        if result['status'] == 'success':
            json_file = result['files'].get('json')
            if json_file and os.path.exists(json_file):
                import json
                with open(json_file, 'r') as f:
                    report_data = json.load(f)
                return jsonify(report_data)
        
        return jsonify({'error': 'Failed to generate genus analysis'}), 500
        
    except Exception as e:
        logger.error(f"Error generating genus analysis: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/country-analysis/<country>')
def api_country_analysis(country: str):
    """Generate quick country-specific analysis"""
    try:
        result = generate_collection_analysis_report(
            country=country,
            output_formats=['json'],
            title=f"Analysis Report for {country}",
            include_charts=False
        )
        
        if result['status'] == 'success':
            json_file = result['files'].get('json')
            if json_file and os.path.exists(json_file):
                import json
                with open(json_file, 'r') as f:
                    report_data = json.load(f)
                return jsonify(report_data)
        
        return jsonify({'error': 'Failed to generate country analysis'}), 500
        
    except Exception as e:
        logger.error(f"Error generating country analysis: {e}")
        return jsonify({'error': str(e)}), 500

@report_bp.route('/api/export-formats')
def api_export_formats():
    """Get available export formats"""
    formats = [
        {
            'id': 'pdf',
            'name': 'PDF Report',
            'description': 'Professional PDF with charts and analysis',
            'icon': 'file-pdf',
            'mime_type': 'application/pdf'
        },
        {
            'id': 'excel',
            'name': 'Excel Workbook',
            'description': 'Multi-sheet Excel file with data and charts',
            'icon': 'file-excel',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        {
            'id': 'csv',
            'name': 'CSV Data',
            'description': 'Comma-separated values for data analysis',
            'icon': 'file-csv',
            'mime_type': 'text/csv'
        },
        {
            'id': 'json',
            'name': 'JSON Data',
            'description': 'Structured JSON data for programmatic access',
            'icon': 'file-json',
            'mime_type': 'application/json'
        }
    ]
    
    return jsonify(formats)

@report_bp.route('/api/color-schemes')
def api_color_schemes():
    """Get available color schemes"""
    schemes = [
        {
            'id': 'orchid_purple',
            'name': 'Orchid Purple',
            'description': 'Purple and gold theme inspired by orchid colors',
            'primary_color': '#6B46C1',
            'secondary_color': '#A78BFA',
            'accent_color': '#FFD700'
        },
        {
            'id': 'professional_blue',
            'name': 'Professional Blue',
            'description': 'Clean blue theme for business reports',
            'primary_color': '#1E3A8A',
            'secondary_color': '#3B82F6',
            'accent_color': '#00BCD4'
        },
        {
            'id': 'nature_green',
            'name': 'Nature Green',
            'description': 'Green and earth tones for botanical reports',
            'primary_color': '#166534',
            'secondary_color': '#22C55E',
            'accent_color': '#F97316'
        }
    ]
    
    return jsonify(schemes)

# Register error handlers
@report_bp.errorhandler(404)
def report_not_found(error):
    return jsonify({'error': 'Report endpoint not found'}), 404

@report_bp.errorhandler(500)
def report_server_error(error):
    logger.error(f"Server error in reports: {error}")
    return jsonify({'error': 'Internal server error in report generation'}), 500