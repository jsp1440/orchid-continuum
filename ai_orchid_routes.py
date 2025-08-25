#!/usr/bin/env python3
"""
AI Orchid Identification Routes
===============================
Flask routes for the revolutionary AI orchid identification system
Part of The Orchid Continuum - Five Cities Orchid Society
"""

import os
import tempfile
from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
from werkzeug.utils import secure_filename
from ai_orchid_identification import identify_orchid_photo, AIOrchidIdentifier
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
ai_orchid_bp = Blueprint('ai', __name__, url_prefix='/ai')

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@ai_orchid_bp.route('/')
def ai_home():
    """AI orchid identification homepage"""
    return render_template('orchid_identify.html')

@ai_orchid_bp.route('/identify')
def identify_page():
    """Show orchid identification interface"""
    return render_template('orchid_identify.html')

@ai_orchid_bp.route('/identify-orchid', methods=['POST'])
def identify_orchid_api():
    """
    API endpoint for AI orchid identification from uploaded photo
    """
    try:
        logger.info("🤖 AI orchid identification request received")
        
        # Check if file was uploaded
        if 'orchid_image' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image file provided'
            }), 400
        
        file = request.files['orchid_image']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Please upload JPG, PNG, WebP, or GIF images.'
            }), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(file.filename)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
            file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        logger.info(f"📷 Analyzing uploaded orchid image: {filename}")
        
        # Run AI identification
        identification_result = identify_orchid_photo(temp_path)
        
        # Clean up temporary file
        os.unlink(temp_path)
        
        # Check if identification was successful
        if 'error' in identification_result:
            logger.error(f"❌ AI identification failed: {identification_result['error']}")
            return jsonify({
                'success': False,
                'error': identification_result['error']
            }), 500
        
        # Success response
        logger.info(f"✅ AI identification complete - Confidence: {identification_result.get('confidence_score', 0)}%")
        
        return jsonify({
            'success': True,
            'ai_identification': identification_result.get('ai_identification', {}),
            'database_matches': identification_result.get('database_matches', []),
            'confidence_score': identification_result.get('confidence_score', 0),
            'analysis_timestamp': identification_result.get('analysis_timestamp'),
            'message': 'Orchid identification completed successfully'
        })
        
    except Exception as e:
        logger.error(f"❌ API error during orchid identification: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@ai_orchid_bp.route('/batch-identify', methods=['POST'])
def batch_identify_api():
    """
    API endpoint for batch orchid identification from multiple photos
    """
    try:
        logger.info("🔄 Batch orchid identification request received")
        
        # Check if files were uploaded
        if 'orchid_images' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No image files provided'
            }), 400
        
        files = request.files.getlist('orchid_images')
        
        if not files or all(f.filename == '' for f in files):
            return jsonify({
                'success': False,
                'error': 'No files selected'
            }), 400
        
        # Limit batch size
        if len(files) > 10:
            return jsonify({
                'success': False,
                'error': 'Maximum 10 images per batch'
            }), 400
        
        # Process each file
        temp_paths = []
        valid_files = []
        
        for file in files:
            if file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                
                # Create temporary file
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(filename)[1]) as tmp_file:
                    file.save(tmp_file.name)
                    temp_paths.append(tmp_file.name)
                    valid_files.append(filename)
        
        if not temp_paths:
            return jsonify({
                'success': False,
                'error': 'No valid image files found'
            }), 400
        
        logger.info(f"📷 Processing {len(temp_paths)} orchid images in batch")
        
        # Run batch AI identification
        identifier = AIOrchidIdentifier()
        batch_results = identifier.batch_identify_orchids(temp_paths)
        
        # Clean up temporary files
        for temp_path in temp_paths:
            try:
                os.unlink(temp_path)
            except:
                pass
        
        # Success response
        logger.info(f"✅ Batch identification complete - Success: {batch_results['successful_identifications']}")
        
        return jsonify({
            'success': True,
            'batch_results': batch_results,
            'total_processed': len(temp_paths),
            'filenames': valid_files,
            'message': f'Batch identification completed - {batch_results["successful_identifications"]} successful'
        })
        
    except Exception as e:
        logger.error(f"❌ Batch API error: {e}")
        return jsonify({
            'success': False,
            'error': f'Server error: {str(e)}'
        }), 500

@ai_orchid_bp.route('/api/capabilities')
def api_capabilities():
    """
    Get AI identification system capabilities and status
    """
    try:
        # Check OpenAI API key availability
        openai_available = bool(os.environ.get('OPENAI_API_KEY'))
        
        capabilities = {
            'ai_available': openai_available,
            'supported_formats': list(ALLOWED_EXTENSIONS),
            'max_file_size': '10MB',
            'batch_limit': 10,
            'features': [
                'Species and genus identification',
                'Confidence scoring',
                'Botanical characteristic analysis', 
                'Growth habit assessment',
                'Care requirement recommendations',
                'Database cross-referencing',
                'Alternative possibility suggestions'
            ],
            'expertise_areas': [
                'Flower morphology analysis',
                'Pseudobulb identification',
                'Growth pattern recognition',
                'Leaf structure analysis',
                'Taxonomic classification',
                'Native habitat assessment'
            ]
        }
        
        return jsonify({
            'success': True,
            'capabilities': capabilities
        })
        
    except Exception as e:
        logger.error(f"❌ Capabilities API error: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@ai_orchid_bp.route('/demo')
def demo_page():
    """
    Show AI orchid identification demo with sample images
    """
    # Sample orchid images for demonstration
    demo_orchids = [
        {
            'name': 'Cattleya labiata',
            'description': 'Classic large-flowered orchid from Brazil',
            'image': '/static/demo/cattleya_sample.jpg'
        },
        {
            'name': 'Phalaenopsis amabilis',
            'description': 'Popular moth orchid from Southeast Asia',
            'image': '/static/demo/phal_sample.jpg'  
        },
        {
            'name': 'Dendrobium nobile',
            'description': 'Deciduous orchid with cane-like pseudobulbs',
            'image': '/static/demo/dendrobium_sample.jpg'
        }
    ]
    
    return render_template('ai_orchid_demo.html', demo_orchids=demo_orchids)

@ai_orchid_bp.route('/help')
def help_page():
    """
    Show help and tips for optimal orchid identification
    """
    photography_tips = [
        "📷 Take clear, well-lit photos of the entire flower",
        "🌸 Include multiple flowers if available for better analysis",
        "🍃 Capture both flowers and leaves in the same shot when possible",
        "📐 Show the plant's growth habit and pseudobulbs if visible",
        "💡 Use natural lighting or bright indoor lighting",
        "📱 Avoid blurry or heavily filtered images",
        "🔍 Close-up shots of flower details are very helpful",
        "🌿 Include the plant label if you have one for verification"
    ]
    
    return render_template('ai_orchid_help.html', tips=photography_tips)

# Register routes
logger.info("🤖 AI Orchid Identification routes registered successfully")