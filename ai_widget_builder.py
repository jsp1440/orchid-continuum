"""
AI-Powered Widget Builder and Modifier
Creates and modifies widgets using OpenAI GPT-4o
"""

import json
import os
import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from orchid_ai import openai_client
from admin_system import admin_required
from models import db

logger = logging.getLogger(__name__)

# Create blueprint for AI widget builder
ai_widget_bp = Blueprint('ai_widgets', __name__, url_prefix='/admin/ai-widgets')

class AIWidgetBuilder:
    """AI-powered widget creation and modification system"""
    
    def __init__(self):
        self.widget_templates = {
            'gallery': {
                'name': 'Gallery Widget',
                'description': 'Displays orchid images in a grid layout',
                'customizable_fields': ['limit', 'genus', 'layout', 'image_size', 'show_names', 'show_descriptions']
            },
            'search': {
                'name': 'Search Widget', 
                'description': 'Interactive orchid search interface',
                'customizable_fields': ['placeholder', 'results_limit', 'show_filters', 'search_fields']
            },
            'featured': {
                'name': 'Featured Orchid Widget',
                'description': 'Highlights a single featured orchid',
                'customizable_fields': ['update_frequency', 'show_description', 'show_care_tips']
            },
            'weather': {
                'name': 'Weather Comparison Widget',
                'description': 'Compares local weather with orchid preferences',
                'customizable_fields': ['location', 'orchid_count', 'show_forecast', 'show_care_advice']
            },
            'comparison': {
                'name': 'Orchid Comparison Widget',
                'description': 'Side-by-side comparison of orchids',
                'customizable_fields': ['comparison_count', 'comparison_fields', 'layout']
            },
            'mission': {
                'name': 'Mission & Stats Widget',
                'description': 'Shows organization mission and statistics',
                'customizable_fields': ['stats_displayed', 'mission_text', 'call_to_action']
            },
            'map': {
                'name': 'Interactive Map Widget',
                'description': 'Shows orchid locations on a world map',
                'customizable_fields': ['default_zoom', 'clustering', 'marker_style']
            },
            'citation': {
                'name': 'Citation Generator Widget',
                'description': 'Generates academic citations for orchid data',
                'customizable_fields': ['citation_format', 'auto_date', 'fields_included']
            },
            'identifier': {
                'name': 'AI Orchid Identifier Widget',
                'description': 'AI-powered orchid identification from photos',
                'customizable_fields': ['confidence_threshold', 'show_suggestions', 'upload_limit']
            }
        }
    
    def generate_widget_code(self, widget_request: str, widget_type: str = None):
        """Use AI to generate custom widget code based on user request"""
        try:
            system_prompt = f"""You are an expert web developer specializing in orchid database widgets. 

AVAILABLE WIDGET TYPES:
{json.dumps(self.widget_templates, indent=2)}

CURRENT DATABASE STRUCTURE:
- OrchidRecord: id, display_name, scientific_name, genus, species, image_url, google_drive_id, ai_description, climate_preference, growth_habit, etc.
- OrchidTaxonomy: taxonomic classification data
- UserUpload: user-submitted orchid photos
- ScrapingLog: automated data collection logs

WIDGET SYSTEM:
- Each widget has HTML template, CSS, and JavaScript
- Widgets can be embedded via /widgets/embed/<widget_type>
- Data is provided via OrchidWidgetSystem._get_<type>_data() method
- Widgets are responsive and use Bootstrap 5

USER REQUEST: {widget_request}

Please provide:
1. widget_type: Choose existing type or suggest "custom_<name>" for new types
2. configuration: JSON object with widget parameters
3. html_template: Complete HTML template for the widget
4. css_styles: Custom CSS for the widget
5. javascript: JavaScript functionality if needed
6. data_method: Python method to fetch data for this widget
7. implementation_notes: How to integrate this widget

Return as valid JSON format."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": widget_request}
                ],
                max_tokens=2000,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Try to parse AI response as JSON
            try:
                widget_config = json.loads(ai_response)
                return {
                    'success': True,
                    'widget_config': widget_config,
                    'raw_response': ai_response
                }
            except json.JSONDecodeError:
                # If not JSON, return as text with structure
                return {
                    'success': True,
                    'widget_config': {
                        'widget_type': widget_type or 'custom',
                        'description': 'AI-generated widget',
                        'raw_ai_response': ai_response
                    },
                    'raw_response': ai_response
                }
                
        except Exception as e:
            logger.error(f"Error generating widget code: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def modify_existing_widget(self, widget_type: str, modifications: str):
        """Use AI to modify existing widget based on user request"""
        try:
            # Get current widget info
            current_widget = self.widget_templates.get(widget_type, {})
            
            system_prompt = f"""You are modifying an existing orchid widget.

CURRENT WIDGET: {widget_type}
CURRENT CONFIG: {json.dumps(current_widget, indent=2)}

MODIFICATION REQUEST: {modifications}

Provide the modifications needed:
1. updated_config: Modified configuration object
2. code_changes: Specific code changes needed
3. template_updates: HTML template modifications
4. css_updates: CSS changes if needed
5. js_updates: JavaScript modifications if needed
6. implementation_steps: Step-by-step implementation guide

Return as valid JSON."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": modifications}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return {
                'success': True,
                'modifications': response.choices[0].message.content,
                'widget_type': widget_type
            }
            
        except Exception as e:
            logger.error(f"Error modifying widget: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def suggest_widget_improvements(self, widget_type: str):
        """AI suggestions for widget improvements"""
        try:
            current_widget = self.widget_templates.get(widget_type, {})
            
            system_prompt = f"""Suggest improvements for this orchid widget:

WIDGET: {widget_type}
CURRENT CONFIG: {json.dumps(current_widget, indent=2)}

Analyze the widget and suggest:
1. performance_improvements: Technical optimizations
2. ux_improvements: User experience enhancements  
3. feature_additions: New functionality that would be valuable
4. accessibility_improvements: Better accessibility features
5. mobile_optimizations: Mobile-specific improvements
6. integration_suggestions: Better integration with the orchid database

Provide practical, implementable suggestions."""

            response = openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Suggest improvements for {widget_type} widget"}
                ],
                max_tokens=1000,
                temperature=0.8
            )
            
            return {
                'success': True,
                'suggestions': response.choices[0].message.content,
                'widget_type': widget_type
            }
            
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Initialize AI widget builder
ai_widget_builder = AIWidgetBuilder()

@ai_widget_bp.route('/')
@admin_required
def ai_widget_dashboard():
    """AI Widget Builder Dashboard"""
    return render_template('admin/ai_widget_dashboard.html',
                         widget_templates=ai_widget_builder.widget_templates)

@ai_widget_bp.route('/create', methods=['GET', 'POST'])
@admin_required
def create_widget():
    """Create new widget using AI"""
    if request.method == 'POST':
        widget_request = request.form.get('widget_request', '').strip()
        widget_type = request.form.get('widget_type', '')
        
        if widget_request:
            result = ai_widget_builder.generate_widget_code(widget_request, widget_type)
            
            if result['success']:
                return render_template('admin/ai_widget_result.html',
                                     result=result,
                                     action='create',
                                     request_text=widget_request)
            else:
                flash(f'Error creating widget: {result["error"]}', 'error')
    
    return render_template('admin/ai_widget_create.html',
                         widget_templates=ai_widget_builder.widget_templates)

@ai_widget_bp.route('/modify/<widget_type>', methods=['GET', 'POST'])
@admin_required
def modify_widget(widget_type):
    """Modify existing widget using AI"""
    if widget_type not in ai_widget_builder.widget_templates:
        flash('Widget type not found', 'error')
        return redirect(url_for('ai_widgets.ai_widget_dashboard'))
    
    if request.method == 'POST':
        modifications = request.form.get('modifications', '').strip()
        
        if modifications:
            result = ai_widget_builder.modify_existing_widget(widget_type, modifications)
            
            if result['success']:
                return render_template('admin/ai_widget_result.html',
                                     result=result,
                                     action='modify',
                                     widget_type=widget_type,
                                     request_text=modifications)
            else:
                flash(f'Error modifying widget: {result["error"]}', 'error')
    
    widget_info = ai_widget_builder.widget_templates[widget_type]
    return render_template('admin/ai_widget_modify.html',
                         widget_type=widget_type,
                         widget_info=widget_info)

@ai_widget_bp.route('/suggestions/<widget_type>')
@admin_required
def widget_suggestions(widget_type):
    """Get AI suggestions for widget improvements"""
    if widget_type not in ai_widget_builder.widget_templates:
        return jsonify({'success': False, 'error': 'Widget type not found'}), 404
    
    result = ai_widget_builder.suggest_widget_improvements(widget_type)
    return jsonify(result)

@ai_widget_bp.route('/preview', methods=['POST'])
@admin_required
def preview_widget():
    """Preview AI-generated widget"""
    widget_config = request.json.get('widget_config', {})
    
    # Generate preview HTML
    preview_html = f"""
    <div class="widget-preview p-4 border rounded">
        <h5>Widget Preview: {widget_config.get('widget_type', 'Custom')}</h5>
        <p><strong>Description:</strong> {widget_config.get('description', 'AI-generated widget')}</p>
        
        {widget_config.get('html_template', '<div class="alert alert-info">Widget HTML will appear here</div>')}
        
        <style>
        {widget_config.get('css_styles', '')}
        </style>
        
        <script>
        {widget_config.get('javascript', '')}
        </script>
    </div>
    """
    
    return jsonify({
        'success': True,
        'preview_html': preview_html
    })

@ai_widget_bp.route('/implement', methods=['POST'])
@admin_required
def implement_widget():
    """Implement AI-generated widget into the system"""
    try:
        widget_config = request.json.get('widget_config', {})
        widget_type = widget_config.get('widget_type', 'custom')
        
        # This would implement the widget by:
        # 1. Creating template files
        # 2. Adding to widget_system.py
        # 3. Creating necessary routes
        
        # For now, return implementation instructions
        implementation_steps = [
            f"Create template: templates/widgets/{widget_type}_widget.html",
            f"Add CSS to: templates/widgets/widgets.css", 
            f"Add JavaScript: templates/widgets/{widget_type}_widget.js",
            f"Update widget_system.py to include new widget type",
            f"Add data method: _get_{widget_type}_data()",
            f"Test widget at: /widgets/embed/{widget_type}"
        ]
        
        return jsonify({
            'success': True,
            'message': 'Widget ready for implementation',
            'implementation_steps': implementation_steps,
            'widget_config': widget_config
        })
        
    except Exception as e:
        logger.error(f"Error implementing widget: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500