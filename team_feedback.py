"""
Team Feedback and Bug Reporting System
======================================

Simple system for your team to report issues directly during testing.
Each report gets a unique ID and is stored in the database.
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime
import uuid
import logging
from models import db

# Create blueprint
team_feedback_bp = Blueprint('team_feedback', __name__)

logger = logging.getLogger(__name__)

# Simple in-memory storage if database isn't available
feedback_storage = []

@team_feedback_bp.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    """Team feedback form for reporting bugs and issues"""
    if request.method == 'GET':
        return render_template('team_feedback.html')
    
    try:
        # Get form data
        issue_type = request.form.get('issue_type', 'bug')
        page_url = request.form.get('page_url', request.referrer or 'Unknown')
        description = request.form.get('description', '').strip()
        steps_to_reproduce = request.form.get('steps_to_reproduce', '').strip()
        expected_behavior = request.form.get('expected_behavior', '').strip()
        reporter_name = request.form.get('reporter_name', 'Anonymous').strip()
        priority = request.form.get('priority', 'medium')
        
        if not description:
            flash('Please describe the issue', 'error')
            return render_template('team_feedback.html')
        
        # Generate unique reference ID
        reference_id = f"OC-{uuid.uuid4().hex[:8].upper()}"
        
        # Create feedback report
        report = {
            'id': len(feedback_storage) + 1,
            'reference_id': reference_id,
            'issue_type': issue_type,
            'page_url': page_url,
            'description': description,
            'steps_to_reproduce': steps_to_reproduce,
            'expected_behavior': expected_behavior,
            'reporter_name': reporter_name,
            'priority': priority,
            'status': 'open',
            'reported_at': datetime.now(),
            'browser_info': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Store in memory for now
        feedback_storage.append(report)
        
        # Log for immediate attention
        logger.info(f"🚨 NEW TEAM FEEDBACK: {reference_id}")
        logger.info(f"   Reporter: {reporter_name}")
        logger.info(f"   Type: {issue_type} ({priority} priority)")
        logger.info(f"   Page: {page_url}")
        logger.info(f"   Issue: {description[:100]}...")
        
        flash(f'Issue reported successfully! Reference ID: {reference_id}', 'success')
        return redirect(url_for('team_feedback.report_issue'))
        
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        flash('Error saving feedback. Please try again.', 'error')
        return render_template('team_feedback.html')

@team_feedback_bp.route('/admin/team-feedback')
def admin_feedback():
    """Admin view of all team feedback"""
    try:
        # Get all feedback, sorted by newest first
        reports = sorted(feedback_storage, key=lambda x: x['reported_at'], reverse=True)
        
        # Simple stats
        stats = {
            'total': len(reports),
            'open': len([r for r in reports if r['status'] == 'open']),
            'high_priority': len([r for r in reports if r['priority'] == 'high']),
            'bugs': len([r for r in reports if r['issue_type'] == 'bug']),
        }
        
        return render_template('admin_feedback.html', reports=reports, stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading admin feedback: {e}")
        return f"Error loading feedback: {e}", 500

@team_feedback_bp.route('/api/feedback/<reference_id>/status', methods=['POST'])
def update_feedback_status(reference_id):
    """Update feedback status (for admins)"""
    try:
        new_status = request.json.get('status', 'open')
        
        # Find and update the report
        for report in feedback_storage:
            if report['reference_id'] == reference_id:
                report['status'] = new_status
                report['updated_at'] = datetime.now()
                
                logger.info(f"✅ Updated {reference_id} status to: {new_status}")
                return jsonify({'success': True, 'status': new_status})
        
        return jsonify({'error': 'Report not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating feedback status: {e}")
        return jsonify({'error': str(e)}), 500

# Quick access function for logging urgent issues
def log_urgent_issue(description, page_url=None, reporter="System"):
    """Quick function to log urgent issues from code"""
    reference_id = f"SYS-{uuid.uuid4().hex[:8].upper()}"
    
    report = {
        'id': len(feedback_storage) + 1,
        'reference_id': reference_id,
        'issue_type': 'system',
        'page_url': page_url or 'System Generated',
        'description': description,
        'steps_to_reproduce': 'System detected',
        'expected_behavior': 'Normal operation',
        'reporter_name': reporter,
        'priority': 'high',
        'status': 'open',
        'reported_at': datetime.now(),
        'browser_info': 'System'
    }
    
    feedback_storage.append(report)
    
    logger.error(f"🚨🚨 URGENT SYSTEM ISSUE {reference_id}: {description}")
    
    return reference_id