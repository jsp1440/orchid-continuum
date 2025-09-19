#!/usr/bin/env python3
"""
Instant Bug Reporter System
Adds debug buttons to every UI element for instant feedback via Google Forms
"""

import os
import json
import requests
from datetime import datetime
from urllib.parse import urlencode

class InstantBugReporter:
    def __init__(self):
        # Google Form configuration for bug reports
        self.google_form_id = "1FAIpQLSe_PLACEHOLDER_FORM_ID"  # Replace with actual form ID
        self.google_sheet_id = "1PLACEHOLDER_SHEET_ID"  # Replace with actual sheet ID
        
        # Debug modes
        self.debug_modes = {
            'image': 'Image Loading Issue',
            'widget': 'Widget Malfunction', 
            'action': 'Button/Action Problem',
            'layout': 'Layout/Display Issue',
            'performance': 'Performance Problem',
            'data': 'Data Loading Error',
            'mobile': 'Mobile Responsiveness',
            'general': 'General Bug Report'
        }
        
    def generate_bug_button_html(self, element_type, element_id, context_info=None):
        """Generate HTML for bug report button attached to any element"""
        
        # Create unique identifier for this element
        report_data = {
            'element_type': element_type,
            'element_id': element_id,
            'page_url': '{{request.url}}',  # Will be filled by template
            'timestamp': '{{timestamp}}',   # Will be filled by template
            'user_agent': '{{user_agent}}', # Will be filled by template
            'context': context_info or {}
        }
        
        # Encode data for URL
        encoded_data = json.dumps(report_data)
        
        return f"""
        <div class="bug-report-container" data-element-type="{element_type}" data-element-id="{element_id}">
            <button class="btn-bug-report" 
                    onclick="reportBug('{element_type}', '{element_id}', {encoded_data})"
                    title="Report a problem with this {element_type}">
                <i class="bug-icon">🐛</i>
            </button>
        </div>
        """
    
    def get_debug_css(self):
        """CSS for bug report buttons and overlay"""
        return """
        <style>
        .bug-report-container {
            position: relative;
            display: inline-block;
        }
        
        .btn-bug-report {
            position: absolute;
            top: -5px;
            right: -5px;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: linear-gradient(135deg, #e74c3c, #c0392b);
            border: 2px solid white;
            color: white;
            font-size: 12px;
            cursor: pointer;
            z-index: 1000;
            opacity: 0.7;
            transition: all 0.3s ease;
            padding: 0;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 2px 8px rgba(231, 76, 60, 0.4);
        }
        
        .btn-bug-report:hover {
            opacity: 1;
            transform: scale(1.1);
            box-shadow: 0 4px 12px rgba(231, 76, 60, 0.6);
        }
        
        .bug-icon {
            font-size: 10px;
            line-height: 1;
        }
        
        /* Debug mode - show all bug buttons */
        .debug-mode .btn-bug-report {
            opacity: 1;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { transform: scale(1); }
            50% { transform: scale(1.1); }
            100% { transform: scale(1); }
        }
        
        /* Bug report modal */
        .bug-modal {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.8);
            z-index: 10000;
            display: none;
            align-items: center;
            justify-content: center;
        }
        
        .bug-modal-content {
            background: #2c3e50;
            color: white;
            padding: 30px;
            border-radius: 15px;
            max-width: 500px;
            width: 90%;
            max-height: 80vh;
            overflow-y: auto;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        
        .bug-modal h3 {
            color: #e74c3c;
            margin-bottom: 20px;
            font-size: 1.4rem;
        }
        
        .bug-form-group {
            margin-bottom: 20px;
        }
        
        .bug-form-group label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #ecf0f1;
        }
        
        .bug-form-group select,
        .bug-form-group textarea,
        .bug-form-group input {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            background: #34495e;
            color: white;
            font-size: 14px;
        }
        
        .bug-form-group textarea {
            min-height: 100px;
            resize: vertical;
        }
        
        .bug-modal-buttons {
            display: flex;
            gap: 15px;
            margin-top: 25px;
        }
        
        .btn-bug-submit {
            flex: 1;
            padding: 12px;
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-bug-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(39, 174, 96, 0.4);
        }
        
        .btn-bug-cancel {
            flex: 1;
            padding: 12px;
            background: #7f8c8d;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-bug-cancel:hover {
            background: #95a5a6;
        }
        
        /* Success message */
        .bug-success {
            position: fixed;
            top: 20px;
            right: 20px;
            background: linear-gradient(135deg, #27ae60, #2ecc71);
            color: white;
            padding: 15px 25px;
            border-radius: 10px;
            z-index: 10001;
            box-shadow: 0 4px 15px rgba(39, 174, 96, 0.3);
            animation: slideIn 0.5s ease;
        }
        
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        /* Debug toggle button */
        .debug-toggle {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: linear-gradient(135deg, #9b59b6, #8e44ad);
            color: white;
            border: none;
            padding: 12px 16px;
            border-radius: 50px;
            cursor: pointer;
            font-weight: bold;
            z-index: 9999;
            box-shadow: 0 4px 15px rgba(155, 89, 182, 0.4);
            transition: all 0.3s ease;
        }
        
        .debug-toggle:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(155, 89, 182, 0.6);
        }
        </style>
        """
    
    def get_debug_javascript(self):
        """JavaScript for bug reporting functionality"""
        return """
        <script>
        // Bug reporting system
        let bugReportData = {};
        let debugMode = false;
        
        function toggleDebugMode() {
            debugMode = !debugMode;
            document.body.classList.toggle('debug-mode', debugMode);
            
            const toggle = document.querySelector('.debug-toggle');
            toggle.textContent = debugMode ? '🐛 Debug: ON' : '🐛 Debug: OFF';
            
            // Show notification
            showNotification(debugMode ? 'Debug mode enabled - bug buttons are now visible!' : 'Debug mode disabled', 
                           debugMode ? '#e74c3c' : '#27ae60');
        }
        
        function reportBug(elementType, elementId, contextData) {
            bugReportData = {
                elementType,
                elementId,
                contextData,
                pageUrl: window.location.href,
                timestamp: new Date().toISOString(),
                userAgent: navigator.userAgent,
                screenResolution: `${screen.width}x${screen.height}`,
                viewportSize: `${window.innerWidth}x${window.innerHeight}`,
                scrollPosition: `${window.scrollX},${window.scrollY}`
            };
            
            showBugModal();
        }
        
        function showBugModal() {
            const modal = document.getElementById('bugModal');
            modal.style.display = 'flex';
            
            // Pre-fill form data
            document.getElementById('bugElementInfo').textContent = 
                `${bugReportData.elementType}: ${bugReportData.elementId}`;
            document.getElementById('bugPageUrl').value = bugReportData.pageUrl;
        }
        
        function closeBugModal() {
            document.getElementById('bugModal').style.display = 'none';
        }
        
        async function submitBugReport() {
            const form = document.getElementById('bugReportForm');
            const formData = new FormData(form);
            
            // Add technical details
            formData.append('element_type', bugReportData.elementType);
            formData.append('element_id', bugReportData.elementId);
            formData.append('page_url', bugReportData.pageUrl);
            formData.append('timestamp', bugReportData.timestamp);
            formData.append('user_agent', bugReportData.userAgent);
            formData.append('screen_resolution', bugReportData.screenResolution);
            formData.append('viewport_size', bugReportData.viewportSize);
            formData.append('scroll_position', bugReportData.scrollPosition);
            
            try {
                // Submit to Google Form
                const response = await fetch('/api/submit-bug-report', {
                    method: 'POST',
                    body: formData
                });
                
                if (response.ok) {
                    closeBugModal();
                    showNotification('🎉 Bug report submitted! Thank you for helping improve the site!', '#27ae60');
                    form.reset();
                } else {
                    throw new Error('Failed to submit report');
                }
            } catch (error) {
                console.error('Error submitting bug report:', error);
                showNotification('❌ Error submitting report. Please try again.', '#e74c3c');
            }
        }
        
        function showNotification(message, color = '#27ae60') {
            const notification = document.createElement('div');
            notification.className = 'bug-success';
            notification.style.background = color;
            notification.textContent = message;
            document.body.appendChild(notification);
            
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
        
        // Keyboard shortcuts
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + Shift + D = Toggle debug mode
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'D') {
                e.preventDefault();
                toggleDebugMode();
            }
            
            // Escape = Close modal
            if (e.key === 'Escape') {
                closeBugModal();
            }
        });
        
        // Auto-capture JavaScript errors
        window.addEventListener('error', function(e) {
            console.log('JavaScript error captured:', e);
            // Could auto-submit critical errors
        });
        
        // Initialize debug system
        document.addEventListener('DOMContentLoaded', function() {
            console.log('🐛 Bug reporting system initialized');
            console.log('Press Ctrl+Shift+D to toggle debug mode');
        });
        </script>
        """
    
    def get_bug_modal_html(self):
        """HTML for the bug report modal"""
        return """
        <!-- Bug Report Modal -->
        <div id="bugModal" class="bug-modal">
            <div class="bug-modal-content">
                <h3>🐛 Report a Bug</h3>
                <p>Help us improve the site by reporting this issue:</p>
                
                <div class="bug-form-group">
                    <label>Element:</label>
                    <div id="bugElementInfo" style="background: #34495e; padding: 8px; border-radius: 4px; font-family: monospace;"></div>
                </div>
                
                <form id="bugReportForm">
                    <div class="bug-form-group">
                        <label for="bugType">Problem Type:</label>
                        <select id="bugType" name="bug_type" required>
                            <option value="">Select problem type...</option>
                            <option value="image">Image not loading</option>
                            <option value="widget">Widget not working</option>
                            <option value="action">Button/link broken</option>
                            <option value="layout">Layout/display issue</option>
                            <option value="performance">Page loading slowly</option>
                            <option value="data">Data not showing</option>
                            <option value="mobile">Mobile display problem</option>
                            <option value="general">Other issue</option>
                        </select>
                    </div>
                    
                    <div class="bug-form-group">
                        <label for="bugDescription">Describe the problem:</label>
                        <textarea id="bugDescription" name="description" 
                                  placeholder="What happened? What did you expect to happen instead?" required></textarea>
                    </div>
                    
                    <div class="bug-form-group">
                        <label for="bugSteps">Steps to reproduce (if applicable):</label>
                        <textarea id="bugSteps" name="steps_to_reproduce" 
                                  placeholder="1. Click on... 2. Then... 3. Error appears..."></textarea>
                    </div>
                    
                    <div class="bug-form-group">
                        <label for="bugSeverity">How urgent is this?</label>
                        <select id="bugSeverity" name="severity">
                            <option value="low">Low - Minor annoyance</option>
                            <option value="medium" selected>Medium - Affects functionality</option>
                            <option value="high">High - Prevents use of feature</option>
                            <option value="critical">Critical - Site is broken</option>
                        </select>
                    </div>
                    
                    <input type="hidden" id="bugPageUrl" name="page_url">
                </form>
                
                <div class="bug-modal-buttons">
                    <button type="button" class="btn-bug-cancel" onclick="closeBugModal()">Cancel</button>
                    <button type="button" class="btn-bug-submit" onclick="submitBugReport()">
                        🚀 Submit Report
                    </button>
                </div>
                
                <p style="font-size: 12px; color: #95a5a6; margin-top: 20px;">
                    📋 This report will be sent instantly to our debug team with technical details to help fix the issue quickly.
                </p>
            </div>
        </div>
        
        <!-- Debug Toggle Button -->
        <button class="debug-toggle" onclick="toggleDebugMode()">🐛 Debug: OFF</button>
        """

# Flask integration functions
def add_bug_button_to_template(template_content, element_type, element_id):
    """Add bug report button to any template element"""
    reporter = InstantBugReporter()
    bug_button = reporter.generate_bug_button_html(element_type, element_id)
    
    # This would be integrated into template rendering
    return template_content.replace(
        f'id="{element_id}"',
        f'id="{element_id}" data-bug-enabled="true"'
    ) + bug_button

def inject_debug_system_to_template(template_content):
    """Inject the complete debug system into any template"""
    reporter = InstantBugReporter()
    
    debug_css = reporter.get_debug_css()
    debug_js = reporter.get_debug_javascript()
    debug_modal = reporter.get_bug_modal_html()
    
    # Inject before closing </head>
    if '</head>' in template_content:
        template_content = template_content.replace('</head>', f'{debug_css}</head>')
    
    # Inject before closing </body>
    if '</body>' in template_content:
        template_content = template_content.replace('</body>', f'{debug_js}{debug_modal}</body>')
    
    return template_content

if __name__ == "__main__":
    reporter = InstantBugReporter()
    print("🐛 Instant Bug Reporter System Created!")
    print(f"🎯 Debug modes: {list(reporter.debug_modes.keys())}")
    print("🚀 Ready to add debug buttons to any UI element!")
    print("📝 Integration: Use inject_debug_system_to_template() in your templates")