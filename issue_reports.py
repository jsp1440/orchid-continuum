"""
Issue Reporting System for Orchid Continuum
Handles user-reported problems with orchid identifications and data
"""

from flask import request, jsonify
from app import app, db
from datetime import datetime
import random
import string
import logging

logger = logging.getLogger(__name__)

def generate_reference_number():
    """Generate a unique reference number like IR-2025-A7B9"""
    year = datetime.now().year
    random_suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"IR-{year}-{random_suffix}"

@app.route('/report-issue', methods=['POST'])
def report_issue():
    """Handle issue reports from users"""
    try:
        data = request.get_json()
        
        if not data or not data.get('orchid_id') or not data.get('issue_description'):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Generate unique reference number
        max_attempts = 5
        reference_number = None
        
        for _ in range(max_attempts):
            ref_num = generate_reference_number()
            # Check if reference number already exists
            from sqlalchemy import text
            
            with db.engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM issue_reports WHERE reference_number = :ref"), 
                    {"ref": ref_num}
                ).scalar()
                
                if result == 0:
                    reference_number = ref_num
                    break
        
        if not reference_number:
            return jsonify({'success': False, 'error': 'Could not generate reference number'}), 500
        
        # Insert issue report
        with db.engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO issue_reports (orchid_id, issue_description, page_url, reference_number)
                    VALUES (:orchid_id, :description, :url, :ref_num)
                """),
                {
                    "orchid_id": data['orchid_id'],
                    "description": data['issue_description'],
                    "url": data.get('page_url', ''),
                    "ref_num": reference_number
                }
            )
            conn.commit()
        
        logger.info(f"Issue reported: {reference_number} for orchid {data['orchid_id']}")
        
        return jsonify({
            'success': True, 
            'reference_number': reference_number,
            'message': 'Issue reported successfully'
        })
        
    except Exception as e:
        logger.error(f"Error reporting issue: {e}")
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/admin/issues')
def admin_issues():
    """Admin view of all reported issues"""
    try:
        from sqlalchemy import text
        
        with db.engine.connect() as conn:
            result = conn.execute(text("""
                SELECT ir.id, ir.orchid_id, ir.issue_description, ir.reference_number, 
                       ir.status, ir.reported_at, ir.page_url,
                       orch.display_name, orch.genus, orch.species
                FROM issue_reports ir
                LEFT JOIN orchid_record orch ON ir.orchid_id = orch.id
                ORDER BY ir.reported_at DESC
                LIMIT 50
            """))
            
            issues = [dict(row._mapping) for row in result]
        
        # Simple HTML response for now
        html = """
        <!DOCTYPE html>
        <html>
        <head><title>Issue Reports - Orchid Continuum Admin</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            .open { background-color: #fff3cd; }
            .resolved { background-color: #d4edda; }
        </style>
        </head>
        <body>
        <h1>🚨 Issue Reports Dashboard</h1>
        <p>Total reports: """ + str(len(issues)) + """</p>
        <table>
        <tr>
            <th>Reference</th>
            <th>Orchid</th>
            <th>Issue Description</th>
            <th>Status</th>
            <th>Reported</th>
        </tr>"""
        
        for issue in issues:
            status_class = 'open' if issue['status'] == 'open' else 'resolved'
            html += f"""
        <tr class="{status_class}">
            <td>{issue['reference_number']}</td>
            <td>OC-{issue['orchid_id']:04d}: {issue['display_name'] or 'Unknown'}</td>
            <td>{issue['issue_description'][:100]}...</td>
            <td>{issue['status'].title()}</td>
            <td>{issue['reported_at'].strftime('%Y-%m-%d %H:%M') if issue['reported_at'] else 'Unknown'}</td>
        </tr>"""
        
        html += """
        </table>
        </body>
        </html>"""
        
        return html
        
    except Exception as e:
        logger.error(f"Error fetching issues: {e}")
        return f"Error: {e}", 500