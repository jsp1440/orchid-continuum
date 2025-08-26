#!/usr/bin/env python3
"""
Bug Report API Routes
Handles instant bug reporting with Google Forms integration
"""

from flask import Blueprint, request, jsonify, render_template_string
import requests
import json
from datetime import datetime
import os

bug_report_bp = Blueprint('bug_report', __name__)

# Google Forms configuration
GOOGLE_FORM_ACTION_URL = "https://docs.google.com/forms/d/e/1FAIpQLSe_PLACEHOLDER/formResponse"

@bug_report_bp.route('/api/submit-bug-report', methods=['POST'])
def submit_bug_report():
    """Submit bug report to Google Form"""
    try:
        # Get form data
        bug_type = request.form.get('bug_type')
        description = request.form.get('description') 
        steps = request.form.get('steps_to_reproduce', '')
        severity = request.form.get('severity', 'medium')
        page_url = request.form.get('page_url')
        element_type = request.form.get('element_type')
        element_id = request.form.get('element_id')
        
        # Technical details
        user_agent = request.form.get('user_agent')
        screen_resolution = request.form.get('screen_resolution')
        viewport_size = request.form.get('viewport_size')
        timestamp = request.form.get('timestamp')
        
        # Create comprehensive bug report
        full_report = f"""
🐛 BUG REPORT - {severity.upper()} PRIORITY

📍 Location: {page_url}
🎯 Element: {element_type} - {element_id}
⏰ Time: {timestamp}

📝 Problem Type: {bug_type}
📖 Description: {description}

🔄 Steps to Reproduce:
{steps}

🖥️ Technical Details:
- Screen: {screen_resolution}
- Viewport: {viewport_size}
- Browser: {user_agent}

🚨 Severity: {severity}
        """.strip()
        
        # Prepare data for Google Form
        form_data = {
            'entry.PLACEHOLDER1': bug_type,  # Replace with actual entry IDs
            'entry.PLACEHOLDER2': description,
            'entry.PLACEHOLDER3': full_report,
            'entry.PLACEHOLDER4': page_url,
            'entry.PLACEHOLDER5': severity,
            'entry.PLACEHOLDER6': f"{element_type}:{element_id}"
        }
        
        # Submit to Google Form (in a real implementation)
        # response = requests.post(GOOGLE_FORM_ACTION_URL, data=form_data)
        
        # For now, log the bug report locally
        log_bug_report_locally(full_report, bug_type, severity)
        
        return jsonify({
            'success': True,
            'message': 'Bug report submitted successfully!'
        })
        
    except Exception as e:
        print(f"Error submitting bug report: {e}")
        return jsonify({
            'success': False,
            'error': 'Failed to submit bug report'
        }), 500

def log_bug_report_locally(report, bug_type, severity):
    """Log bug report to local file for debugging"""
    try:
        log_dir = 'logs'
        os.makedirs(log_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{log_dir}/bug_report_{severity}_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write(report)
        
        print(f"🐛 Bug report logged: {filename}")
        
    except Exception as e:
        print(f"Error logging bug report: {e}")

@bug_report_bp.route('/debug-system')
def debug_system_demo():
    """Demo page showing the debug system in action"""
    return render_template_string("""
<!DOCTYPE html>
<html lang="en" data-bs-theme="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Debug System Demo - Five Cities Orchid Society</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
    {{ debug_css|safe }}
</head>
<body>
    <div class="container mt-4">
        <h1>🐛 Debug System Demo</h1>
        <p class="lead">Press <kbd>Ctrl+Shift+D</kbd> or click the debug button to enable bug reporting on all elements.</p>
        
        <div class="row">
            <div class="col-md-6">
                <div class="card bg-dark border-light mb-4" id="demo-card-1">
                    <div class="card-header">
                        <h5>Sample Widget</h5>
                    </div>
                    <div class="card-body">
                        <p>This is a demo widget with a bug button.</p>
                        <button class="btn btn-primary" id="demo-button-1">Test Button</button>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card bg-dark border-light mb-4" id="demo-card-2">
                    <div class="card-body">
                        <img src="/static/images/orchid_continuum_transparent_logo.png" 
                             alt="Demo Image" class="img-fluid" id="demo-image-1">
                    </div>
                </div>
            </div>
        </div>
        
        <div class="alert alert-info">
            <h6>How it works:</h6>
            <ol>
                <li>Enable debug mode (Ctrl+Shift+D or debug button)</li>
                <li>Click any 🐛 button that appears on elements</li>
                <li>Fill out the bug report form</li>
                <li>Reports are instantly logged and can be sent to Google Forms</li>
            </ol>
        </div>
    </div>
    
    {{ debug_js|safe }}
    {{ debug_modal|safe }}
    
    <script>
        // Add bug buttons to demo elements
        document.addEventListener('DOMContentLoaded', function() {
            // This would normally be done server-side during template rendering
            addBugButtonToElement('demo-card-1', 'widget');
            addBugButtonToElement('demo-button-1', 'action');
            addBugButtonToElement('demo-image-1', 'image');
        });
        
        function addBugButtonToElement(elementId, elementType) {
            const element = document.getElementById(elementId);
            if (element) {
                const container = document.createElement('div');
                container.className = 'bug-report-container';
                container.style.position = 'relative';
                container.style.display = 'inline-block';
                
                // Wrap the element
                element.parentNode.insertBefore(container, element);
                container.appendChild(element);
                
                // Add bug button
                const bugButton = document.createElement('button');
                bugButton.className = 'btn-bug-report';
                bugButton.title = `Report a problem with this ${elementType}`;
                bugButton.innerHTML = '<i class="bug-icon">🐛</i>';
                bugButton.onclick = () => reportBug(elementType, elementId, {});
                
                container.appendChild(bugButton);
            }
        }
    </script>
</body>
</html>
    """, 
    debug_css=get_debug_css(),
    debug_js=get_debug_js(),
    debug_modal=get_debug_modal()
    )

def get_debug_css():
    """Get debug system CSS"""
    from instant_bug_reporter import InstantBugReporter
    reporter = InstantBugReporter()
    return reporter.get_debug_css()

def get_debug_js():
    """Get debug system JavaScript"""
    from instant_bug_reporter import InstantBugReporter
    reporter = InstantBugReporter()
    return reporter.get_debug_javascript()

def get_debug_modal():
    """Get debug system modal HTML"""
    from instant_bug_reporter import InstantBugReporter
    reporter = InstantBugReporter()
    return reporter.get_bug_modal_html()

# Template filter to inject debug system
def inject_debug_system(template_content):
    """Template filter to inject debug system into any page"""
    from instant_bug_reporter import inject_debug_system_to_template
    return inject_debug_system_to_template(template_content)

if __name__ == "__main__":
    print("🐛 Bug Report Routes Created!")
    print("📝 API endpoint: /api/submit-bug-report")
    print("🎯 Demo page: /debug-system")
    print("🚀 Ready for instant bug reporting!")