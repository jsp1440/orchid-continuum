from datetime import datetime
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from app import db
from models import BugReport
import logging

# Bug Report System for Beta Testing Phase
# This allows users to report issues directly to the AI agent for immediate fixes

bug_report_bp = Blueprint('bug_reports', __name__)

@bug_report_bp.route('/report-bug', methods=['GET', 'POST'])
def report_bug():
    """Bug reporting form for beta testers"""
    if request.method == 'POST':
        try:
            # Create new bug report
            bug_report = BugReport(
                item_type=request.form.get('item_type', 'general'),
                item_id=request.form.get('item_id', 'unknown'),
                item_name=request.form.get('item_name', 'Unknown Item'),
                issue_type=request.form.get('issue_type', 'other'),
                description=request.form.get('description', ''),
                user_email=request.form.get('user_email', None)
            )
            
            db.session.add(bug_report)
            db.session.commit()
            
            # Log for AI agent to see
            logging.info(f"🐛 NEW BUG REPORT: {bug_report.item_type} '{bug_report.item_name}' - {bug_report.issue_type}")
            logging.info(f"📝 Description: {bug_report.description}")
            logging.info(f"🆔 Item ID: {bug_report.item_id}")
            
            flash('Thank you! Your bug report has been sent directly to our AI agent for immediate fixing.', 'success')
            return redirect(url_for('bug_reports.report_bug'))
            
        except Exception as e:
            logging.error(f"Error saving bug report: {e}")
            flash('Sorry, there was an error submitting your report. Please try again.', 'error')
    
    return render_template('bug_report_form.html')

@bug_report_bp.route('/api/report-bug', methods=['POST'])
def api_report_bug():
    """API endpoint for AJAX bug reporting"""
    try:
        data = request.get_json()
        
        bug_report = BugReport(
            item_type=data.get('item_type', 'general'),
            item_id=data.get('item_id', 'unknown'),
            item_name=data.get('item_name', 'Unknown Item'),
            issue_type=data.get('issue_type', 'other'),
            description=data.get('description', ''),
            user_email=data.get('user_email', None)
        )
        
        db.session.add(bug_report)
        db.session.commit()
        
        # Log for AI agent immediate attention
        logging.warning(f"🚨 URGENT BUG REPORT #{bug_report.id}: {bug_report.item_type} '{bug_report.item_name}'")
        logging.warning(f"🔧 Issue: {bug_report.issue_type} - {bug_report.description}")
        logging.warning(f"🆔 Item ID: {bug_report.item_id}")
        
        return jsonify({
            'success': True,
            'message': 'Bug report submitted successfully! Our AI agent will fix this immediately.',
            'report_id': bug_report.id
        })
        
    except Exception as e:
        logging.error(f"API bug report error: {e}")
        return jsonify({
            'success': False,
            'message': 'Error submitting bug report. Please try again.'
        }), 500

@bug_report_bp.route('/admin/bug-reports')
def admin_bug_reports():
    """Admin view of all bug reports for AI agent"""
    reports = BugReport.query.order_by(BugReport.created_at.desc()).all()
    return render_template('admin_bug_reports.html', reports=reports)

@bug_report_bp.route('/api/bug-reports')
def api_bug_reports():
    """API to get all bug reports for AI agent monitoring"""
    reports = BugReport.query.order_by(BugReport.created_at.desc()).all()
    return jsonify([report.to_dict() for report in reports])

@bug_report_bp.route('/api/mark-fixed/<int:report_id>', methods=['POST'])
def mark_fixed(report_id):
    """Mark a bug report as fixed"""
    try:
        report = BugReport.query.get_or_404(report_id)
        report.status = 'fixed'
        report.fixed_at = datetime.utcnow()
        db.session.commit()
        
        logging.info(f"✅ Bug report #{report_id} marked as FIXED: {report.item_name}")
        
        return jsonify({
            'success': True,
            'message': f'Bug report #{report_id} marked as fixed!'
        })
        
    except Exception as e:
        logging.error(f"Error marking bug as fixed: {e}")
        return jsonify({
            'success': False,
            'message': 'Error updating bug report status'
        }), 500

# JavaScript helper function for easy bug reporting
BUG_REPORT_JS = """
function reportBug(itemType, itemId, itemName, issueType = 'other') {
    const description = prompt(`What's wrong with "${itemName}"?\\n\\nPlease describe the issue:`);
    if (!description) return;
    
    const email = prompt('Email (optional, for follow-up):');
    
    fetch('/api/report-bug', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            item_type: itemType,
            item_id: itemId,
            item_name: itemName,
            issue_type: issueType,
            description: description,
            user_email: email || null
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ Bug report submitted! Our AI agent will fix this immediately.');
        } else {
            alert('❌ Error submitting report. Please try again.');
        }
    })
    .catch(error => {
        console.error('Bug report error:', error);
        alert('❌ Network error. Please try again.');
    });
}

// Add bug report buttons to any element
function addBugReportButton(element, itemType, itemId, itemName) {
    const button = document.createElement('button');
    button.innerHTML = '🐛 Report Issue';
    button.className = 'btn btn-sm btn-outline-warning bug-report-btn';
    button.style.cssText = 'position: absolute; top: 5px; right: 5px; z-index: 1000; font-size: 10px; padding: 2px 6px;';
    button.onclick = () => reportBug(itemType, itemId, itemName);
    
    element.style.position = 'relative';
    element.appendChild(button);
}
"""