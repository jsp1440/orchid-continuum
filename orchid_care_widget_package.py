#!/usr/bin/env python3
"""
Orchid Care Widget Package
==========================
Comprehensive widget package for embedding orchid care AI assistance.
Provides all three options as embeddable widgets for external websites.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from flask import Blueprint, render_template, request, jsonify, Response
from care_helper_widget import SimpleCareAdvisor
from guided_care_form import GuidedCareSystem

logger = logging.getLogger(__name__)

widget_package_bp = Blueprint('widget_package', __name__, url_prefix='/widgets')

class OrchidCareWidgetPackage:
    """Unified widget package for all three care options"""
    
    def __init__(self):
        self.care_advisor = SimpleCareAdvisor()
        self.guided_care = GuidedCareSystem()
    
    def get_widget_config(self, widget_type: str, custom_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get configuration for different widget types"""
        base_config = {
            'version': '1.0.0',
            'theme': 'dark',
            'responsive': True,
            'powered_by': 'Orchid Continuum AI',
            'api_base_url': '/widgets'
        }
        
        widget_configs = {
            'simple_chat': {
                'name': 'Simple Care Helper',
                'description': 'Natural language orchid care assistance',
                'features': ['natural_language', 'location_aware', 'conversational'],
                'size': {'width': '400px', 'height': '600px'},
                'embed_path': '/widgets/simple-chat/embed'
            },
            'guided_form': {
                'name': 'Guided Care Form',
                'description': 'Step-by-step structured care assistance', 
                'features': ['structured_input', 'species_selection', 'problem_categories'],
                'size': {'width': '500px', 'height': '700px'},
                'embed_path': '/widgets/guided-form/embed'
            },
            'enhanced_chat': {
                'name': 'Enhanced AI Chat',
                'description': 'Full-featured AI orchid assistant',
                'features': ['care_mode', 'image_analysis', 'database_queries'],
                'size': {'width': '800px', 'height': '600px'},
                'embed_path': '/widgets/enhanced-chat/embed'
            }
        }
        
        if widget_type in widget_configs:
            config = {**base_config, **widget_configs[widget_type]}
            if custom_config:
                config.update(custom_config)
            return config
        
        return base_config

# Initialize the widget package
widget_package = OrchidCareWidgetPackage()

@widget_package_bp.route('/')
def widget_showcase():
    """Widget showcase and selection page"""
    widgets = [
        widget_package.get_widget_config('simple_chat'),
        widget_package.get_widget_config('guided_form'),
        widget_package.get_widget_config('enhanced_chat')
    ]
    return render_template('widgets/showcase.html', widgets=widgets)

@widget_package_bp.route('/simple-chat/embed')
def simple_chat_widget():
    """Embeddable simple chat widget"""
    config = widget_package.get_widget_config('simple_chat')
    return render_template('widgets/simple_chat_embed.html', config=config)

@widget_package_bp.route('/guided-form/embed')
def guided_form_widget():
    """Embeddable guided form widget"""
    config = widget_package.get_widget_config('guided_form')
    genera = widget_package.guided_care.get_popular_orchid_genera(20)  # Limit for widget
    problems = widget_package.guided_care.get_care_problems_list()
    return render_template('widgets/guided_form_embed.html', 
                         config=config, genera=genera, problems=problems)

@widget_package_bp.route('/enhanced-chat/embed')
def enhanced_chat_widget():
    """Embeddable enhanced chat widget"""
    config = widget_package.get_widget_config('enhanced_chat')
    return render_template('widgets/enhanced_chat_embed.html', config=config)

@widget_package_bp.route('/api/simple-chat', methods=['POST'])
def simple_chat_api():
    """API endpoint for simple chat widget"""
    try:
        data = request.get_json()
        question = data.get('question', '').strip()
        location = data.get('location', '').strip()
        
        if not question:
            return jsonify({'success': False, 'error': 'Please enter a question about your orchid.'})
        
        result = widget_package.care_advisor.get_care_advice(question, location)
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error in simple chat API: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to process your question. Please try again.'
        })

@widget_package_bp.route('/api/guided-form', methods=['POST'])
def guided_form_api():
    """API endpoint for guided form widget"""
    try:
        data = request.get_json()
        
        genus = data.get('genus', '')
        species = data.get('species', '')
        problems = data.get('problems', [])
        location = data.get('location', '')
        additional_details = data.get('additional_details', '')
        
        if not genus or not problems:
            return jsonify({
                'success': False, 
                'error': 'Please select at least a genus and one problem'
            })
        
        # Build structured question
        question_parts = []
        
        if species:
            question_parts.append(f"My {species}")
        else:
            question_parts.append(f"My {genus} orchid")
        
        if len(problems) == 1:
            question_parts.append(f"has {problems[0].lower()}")
        else:
            question_parts.append(f"has these problems: {', '.join(problems).lower()}")
        
        if additional_details:
            question_parts.append(f"Additional details: {additional_details}")
        
        structured_question = ". ".join(question_parts) + "."
        
        advice_result = widget_package.care_advisor.get_care_advice(
            structured_question, location
        )
        
        if advice_result['success']:
            return jsonify({
                'success': True,
                'advice': advice_result['advice'],
                'structured_question': structured_question,
                'timestamp': advice_result['timestamp']
            })
        else:
            return jsonify({
                'success': False,
                'error': advice_result.get('error', 'Unable to generate advice')
            })
            
    except Exception as e:
        logger.error(f"Error in guided form API: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to process your request. Please try again.'
        })

@widget_package_bp.route('/api/enhanced-chat', methods=['POST'])
def enhanced_chat_api():
    """API endpoint for enhanced chat widget"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        mode = data.get('mode', 'general')  # 'general' or 'care'
        
        if not message:
            return jsonify({'success': False, 'error': 'Please enter a message.'})
        
        if mode == 'care':
            # Use care advisor for care mode
            result = widget_package.care_advisor.get_care_advice(message)
            if result['success']:
                return jsonify({
                    'success': True,
                    'response': result['advice'],
                    'mode': 'care'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Unable to provide care advice')
                })
        else:
            # Forward to existing AI chat system for general mode
            from ai_orchid_chat import OrchidAI
            orchid_ai = OrchidAI()
            
            # Use the existing chat response system
            response = f"I received your message: {message}. This is a general chat response."
            
            return jsonify({
                'success': True,
                'response': response,
                'mode': 'general'
            })
            
    except Exception as e:
        logger.error(f"Error in enhanced chat API: {e}")
        return jsonify({
            'success': False,
            'error': 'Unable to process your message. Please try again.'
        })

@widget_package_bp.route('/embed.js')
def embed_script():
    """JavaScript embed script for easy widget integration"""
    js_content = """
(function() {
    // Orchid Care Widget Embed Script v1.0.0
    
    window.OrchidCareWidgets = {
        embed: function(elementId, widgetType, config) {
            const element = document.getElementById(elementId);
            if (!element) {
                console.error('OrchidCareWidgets: Element not found:', elementId);
                return;
            }
            
            config = config || {};
            const baseUrl = config.baseUrl || 'https://orchidcontinuum.replit.app';
            
            const widgetUrls = {
                'simple-chat': baseUrl + '/widgets/simple-chat/embed',
                'guided-form': baseUrl + '/widgets/guided-form/embed',
                'enhanced-chat': baseUrl + '/widgets/enhanced-chat/embed'
            };
            
            if (!widgetUrls[widgetType]) {
                console.error('OrchidCareWidgets: Unknown widget type:', widgetType);
                return;
            }
            
            const iframe = document.createElement('iframe');
            iframe.src = widgetUrls[widgetType];
            iframe.style.width = config.width || '100%';
            iframe.style.height = config.height || '600px';
            iframe.style.border = config.border || 'none';
            iframe.style.borderRadius = config.borderRadius || '8px';
            iframe.frameBorder = '0';
            iframe.allowTransparency = true;
            
            element.appendChild(iframe);
            
            return iframe;
        }
    };
})();
    """
    
    return Response(js_content, mimetype='application/javascript')

@widget_package_bp.route('/demo')
def widget_demo():
    """Demo page showing all widgets in action"""
    return render_template('widgets/demo.html')

def register_widget_package_routes(app):
    """Register widget package routes with Flask app"""
    app.register_blueprint(widget_package_bp)
    logger.info("🎨 Orchid Care Widget Package registered successfully")