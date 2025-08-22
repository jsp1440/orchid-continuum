"""
Advanced Photo Editor for Orchid Continuum
Comprehensive photo editing, plant analysis, and export system
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from PIL import Image, ImageEnhance, ImageFilter, ImageOps, ImageDraw
import numpy as np
import cv2
from flask import Blueprint, render_template, request, jsonify, send_file, session
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
import zipfile
import tempfile

from models import OrchidRecord, db
from google_drive_service import upload_to_drive, get_drive_file_url
from admin_system import admin_required
import openai

logger = logging.getLogger(__name__)

# Create photo editor blueprint
photo_editor_bp = Blueprint('photo_editor', __name__, url_prefix='/photo-editor')

class AdvancedPhotoEditor:
    def __init__(self):
        self.temp_dir = 'temp/photo_editor'
        self.editing_sessions = {}  # In-memory session storage
        os.makedirs(self.temp_dir, exist_ok=True)
        
        # Initialize OpenAI for plant analysis
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
        
    def create_editing_session(self, orchid_id: int, user_id: str = None) -> Dict[str, Any]:
        """Create a new photo editing session"""
        try:
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid or not orchid.image_url:
                return {'error': 'Orchid or image not found'}
            
            session_id = str(uuid.uuid4())
            
            # Download and prepare image for editing
            original_image = self._load_image_from_url(orchid.image_url)
            if not original_image:
                return {'error': 'Could not load image'}
            
            # Save original to temp directory
            temp_filename = f"original_{session_id}.jpg"
            temp_path = os.path.join(self.temp_dir, temp_filename)
            original_image.save(temp_path, 'JPEG', quality=95)
            
            # Create editing session
            session_data = {
                'session_id': session_id,
                'orchid_id': orchid_id,
                'user_id': user_id,
                'orchid_name': orchid.scientific_name or orchid.display_name or 'Unknown Orchid',
                'original_path': temp_path,
                'current_path': temp_path,
                'original_size': original_image.size,
                'edit_history': [],
                'created_at': datetime.now().isoformat(),
                'analysis_data': {},
                'filters_applied': [],
                'transformations': []
            }
            
            self.editing_sessions[session_id] = session_data
            
            return {
                'success': True,
                'session_id': session_id,
                'orchid_name': session_data['orchid_name'],
                'original_size': session_data['original_size'],
                'editor_url': f'/photo-editor/edit/{session_id}'
            }
            
        except Exception as e:
            logger.error(f"Error creating editing session: {e}")
            return {'error': str(e)}
    
    def apply_basic_adjustments(self, session_id: str, brightness: float = 1.0, 
                               contrast: float = 1.0, saturation: float = 1.0, 
                               sharpness: float = 1.0) -> Dict[str, Any]:
        """Apply basic image adjustments"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            # Load current image
            image = Image.open(session['current_path'])
            
            # Apply adjustments
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(image)
                image = enhancer.enhance(brightness)
            
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(contrast)
            
            if saturation != 1.0:
                enhancer = ImageEnhance.Color(image)
                image = enhancer.enhance(saturation)
            
            if sharpness != 1.0:
                enhancer = ImageEnhance.Sharpness(image)
                image = enhancer.enhance(sharpness)
            
            # Save adjusted image
            new_filename = f"adjusted_{session_id}_{len(session['edit_history'])}.jpg"
            new_path = os.path.join(self.temp_dir, new_filename)
            image.save(new_path, 'JPEG', quality=95)
            
            # Update session
            session['current_path'] = new_path
            session['edit_history'].append({
                'operation': 'basic_adjustments',
                'parameters': {
                    'brightness': brightness,
                    'contrast': contrast,
                    'saturation': saturation,
                    'sharpness': sharpness
                },
                'timestamp': datetime.now().isoformat(),
                'file_path': new_path
            })
            
            return {
                'success': True,
                'image_data': self._image_to_base64(image),
                'operation_id': len(session['edit_history']) - 1
            }
            
        except Exception as e:
            logger.error(f"Error applying basic adjustments: {e}")
            return {'error': str(e)}
    
    def apply_crop(self, session_id: str, x: int, y: int, width: int, height: int) -> Dict[str, Any]:
        """Apply crop to image"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            image = Image.open(session['current_path'])
            
            # Validate crop boundaries
            img_width, img_height = image.size
            x = max(0, min(x, img_width))
            y = max(0, min(y, img_height))
            width = min(width, img_width - x)
            height = min(height, img_height - y)
            
            # Apply crop
            cropped_image = image.crop((x, y, x + width, y + height))
            
            # Save cropped image
            new_filename = f"cropped_{session_id}_{len(session['edit_history'])}.jpg"
            new_path = os.path.join(self.temp_dir, new_filename)
            cropped_image.save(new_path, 'JPEG', quality=95)
            
            # Update session
            session['current_path'] = new_path
            session['edit_history'].append({
                'operation': 'crop',
                'parameters': {'x': x, 'y': y, 'width': width, 'height': height},
                'timestamp': datetime.now().isoformat(),
                'file_path': new_path
            })
            
            return {
                'success': True,
                'image_data': self._image_to_base64(cropped_image),
                'new_size': cropped_image.size,
                'operation_id': len(session['edit_history']) - 1
            }
            
        except Exception as e:
            logger.error(f"Error applying crop: {e}")
            return {'error': str(e)}
    
    def apply_resize(self, session_id: str, new_width: int, new_height: int, 
                    maintain_aspect: bool = True) -> Dict[str, Any]:
        """Apply resize to image"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            image = Image.open(session['current_path'])
            
            if maintain_aspect:
                image.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
                resized_image = image
            else:
                resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save resized image
            new_filename = f"resized_{session_id}_{len(session['edit_history'])}.jpg"
            new_path = os.path.join(self.temp_dir, new_filename)
            resized_image.save(new_path, 'JPEG', quality=95)
            
            # Update session
            session['current_path'] = new_path
            session['edit_history'].append({
                'operation': 'resize',
                'parameters': {
                    'new_width': new_width,
                    'new_height': new_height,
                    'maintain_aspect': maintain_aspect,
                    'actual_size': resized_image.size
                },
                'timestamp': datetime.now().isoformat(),
                'file_path': new_path
            })
            
            return {
                'success': True,
                'image_data': self._image_to_base64(resized_image),
                'new_size': resized_image.size,
                'operation_id': len(session['edit_history']) - 1
            }
            
        except Exception as e:
            logger.error(f"Error applying resize: {e}")
            return {'error': str(e)}
    
    def apply_filters(self, session_id: str, filter_type: str, intensity: float = 1.0) -> Dict[str, Any]:
        """Apply various filters to image"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            image = Image.open(session['current_path'])
            filtered_image = image.copy()
            
            # Apply different filters based on type
            if filter_type == 'blur':
                filtered_image = filtered_image.filter(ImageFilter.GaussianBlur(radius=intensity))
            elif filter_type == 'sharpen':
                filtered_image = filtered_image.filter(ImageFilter.UnsharpMask(radius=2, percent=int(intensity * 150), threshold=3))
            elif filter_type == 'emboss':
                filtered_image = filtered_image.filter(ImageFilter.EMBOSS)
            elif filter_type == 'edge_enhance':
                filtered_image = filtered_image.filter(ImageFilter.EDGE_ENHANCE)
            elif filter_type == 'smooth':
                filtered_image = filtered_image.filter(ImageFilter.SMOOTH)
            elif filter_type == 'grayscale':
                filtered_image = ImageOps.grayscale(filtered_image).convert('RGB')
            elif filter_type == 'sepia':
                filtered_image = self._apply_sepia(filtered_image)
            elif filter_type == 'vintage':
                filtered_image = self._apply_vintage(filtered_image)
            elif filter_type == 'botanical_enhance':
                filtered_image = self._apply_botanical_enhancement(filtered_image)
            else:
                return {'error': f'Unknown filter type: {filter_type}'}
            
            # Save filtered image
            new_filename = f"filtered_{filter_type}_{session_id}_{len(session['edit_history'])}.jpg"
            new_path = os.path.join(self.temp_dir, new_filename)
            filtered_image.save(new_path, 'JPEG', quality=95)
            
            # Update session
            session['current_path'] = new_path
            session['filters_applied'].append(filter_type)
            session['edit_history'].append({
                'operation': 'filter',
                'parameters': {'filter_type': filter_type, 'intensity': intensity},
                'timestamp': datetime.now().isoformat(),
                'file_path': new_path
            })
            
            return {
                'success': True,
                'image_data': self._image_to_base64(filtered_image),
                'filter_applied': filter_type,
                'operation_id': len(session['edit_history']) - 1
            }
            
        except Exception as e:
            logger.error(f"Error applying filter: {e}")
            return {'error': str(e)}
    
    def analyze_plant_features(self, session_id: str) -> Dict[str, Any]:
        """Advanced AI plant analysis"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session or not self.openai_client:
                return {'error': 'Invalid session or AI not available'}
            
            image = Image.open(session['current_path'])
            
            # Convert image to base64 for AI analysis
            image_b64 = self._image_to_base64(image)
            
            # Comprehensive plant analysis prompt
            analysis_prompt = """
            Perform comprehensive botanical analysis on this orchid image:

            1. MORPHOLOGICAL ANALYSIS:
            - Flower structure and symmetry
            - Petal/sepal shape, size, and patterns
            - Lip structure and markings
            - Column characteristics
            - Spur presence and length
            - Color distribution and intensity

            2. PLANT STRUCTURE:
            - Growth habit (monopodial/sympodial)
            - Leaf characteristics (shape, texture, arrangement)
            - Pseudobulb presence and characteristics
            - Root visibility and condition

            3. IDENTIFICATION MARKERS:
            - Species-specific features
            - Hybrid characteristics
            - Distinguishing marks from similar species
            - Size estimation relative to typical for species

            4. CONDITION ASSESSMENT:
            - Overall plant health
            - Flowering stage and quality
            - Environmental stress indicators
            - Cultural care assessment

            5. PHOTOGRAPHY QUALITY:
            - Image sharpness and clarity
            - Lighting quality
            - Background suitability
            - Composition for identification

            6. 3D SPATIAL ANALYSIS:
            - Depth perception of flower structure
            - Dimensional characteristics
            - Spatial relationships between plant parts

            Provide detailed analysis in JSON format with confidence scores.
            """
            
            # Call OpenAI Vision API
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": analysis_prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}
                            }
                        ]
                    }
                ],
                max_tokens=2000,
                temperature=0.1
            )
            
            ai_analysis = response.choices[0].message.content
            
            # Try to parse as JSON, fallback to text
            try:
                analysis_data = json.loads(ai_analysis)
            except:
                analysis_data = {'analysis_text': ai_analysis, 'format': 'text'}
            
            # Store analysis in session
            session['analysis_data'] = {
                'analysis': analysis_data,
                'analyzed_at': datetime.now().isoformat(),
                'image_analyzed': session['current_path']
            }
            
            return {
                'success': True,
                'analysis': analysis_data,
                'features_detected': self._extract_plant_features(analysis_data),
                'quality_score': self._calculate_quality_score(analysis_data),
                'recommendations': self._generate_photo_recommendations(analysis_data)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing plant features: {e}")
            return {'error': str(e)}
    
    def save_edited_image(self, session_id: str, save_options: Dict[str, Any]) -> Dict[str, Any]:
        """Save edited image with various options"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            image = Image.open(session['current_path'])
            orchid = OrchidRecord.query.get(session['orchid_id'])
            
            # Generate filename
            base_name = orchid.image_filename or f"orchid_{session['orchid_id']}"
            name_without_ext = os.path.splitext(base_name)[0]
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # Save options
            save_format = save_options.get('format', 'JPEG')
            quality = save_options.get('quality', 95)
            save_original = save_options.get('save_original', True)
            upload_to_drive_flag = save_options.get('upload_to_drive', True)
            
            results = []
            
            # Save edited version
            edited_filename = f"{name_without_ext}_edited_{timestamp}.{save_format.lower()}"
            edited_path = os.path.join(self.temp_dir, edited_filename)
            
            if save_format.upper() == 'PNG':
                image.save(edited_path, 'PNG', optimize=True)
            else:
                image.save(edited_path, 'JPEG', quality=quality, optimize=True)
            
            # Upload to Google Drive if requested
            drive_id = None
            drive_url = None
            if upload_to_drive_flag:
                drive_id = upload_to_drive(edited_path, edited_filename, 'Orchid_Edited_Photos')
                drive_url = get_drive_file_url(drive_id) if drive_id else None
            
            results.append({
                'type': 'edited',
                'filename': edited_filename,
                'local_path': edited_path,
                'drive_id': drive_id,
                'drive_url': drive_url,
                'format': save_format,
                'size': os.path.getsize(edited_path)
            })
            
            # Update orchid record with edited version info
            enhancement_data = json.loads(orchid.enhancement_data or '{}')
            if 'edited_versions' not in enhancement_data:
                enhancement_data['edited_versions'] = []
            
            edited_version = {
                'version_id': str(uuid.uuid4()),
                'session_id': session_id,
                'filename': edited_filename,
                'drive_id': drive_id,
                'url': drive_url,
                'edit_history': session['edit_history'],
                'filters_applied': session['filters_applied'],
                'analysis_data': session.get('analysis_data', {}),
                'created_at': datetime.now().isoformat()
            }
            
            enhancement_data['edited_versions'].append(edited_version)
            orchid.enhancement_data = json.dumps(enhancement_data)
            
            # Create export package if requested
            if save_options.get('create_package', False):
                package_result = self._create_export_package(session, save_options)
                if package_result.get('success'):
                    results.append(package_result)
            
            db.session.commit()
            
            return {
                'success': True,
                'saved_files': results,
                'session_summary': {
                    'operations_performed': len(session['edit_history']),
                    'filters_applied': session['filters_applied'],
                    'analysis_completed': 'analysis_data' in session
                }
            }
            
        except Exception as e:
            logger.error(f"Error saving edited image: {e}")
            return {'error': str(e)}
    
    def _load_image_from_url(self, image_url: str) -> Optional[Image.Image]:
        """Load image from URL (placeholder - in production would download from URL)"""
        try:
            # For development, return a placeholder
            # In production, this would download from the actual URL
            placeholder = Image.new('RGB', (800, 600), color='lightgreen')
            draw = ImageDraw.Draw(placeholder)
            draw.text((300, 250), "Orchid Image", fill='darkgreen')
            draw.text((350, 300), "Placeholder", fill='darkgreen')
            return placeholder
        except Exception as e:
            logger.error(f"Error loading image from URL: {e}")
            return None
    
    def _image_to_base64(self, image: Image.Image) -> str:
        """Convert PIL Image to base64 string"""
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
    
    def _apply_sepia(self, image: Image.Image) -> Image.Image:
        """Apply sepia tone effect"""
        sepia_image = ImageOps.colorize(ImageOps.grayscale(image), '#704214', '#C0A882')
        return sepia_image
    
    def _apply_vintage(self, image: Image.Image) -> Image.Image:
        """Apply vintage effect"""
        # Reduce saturation and add warm tone
        enhancer = ImageEnhance.Color(image)
        vintage = enhancer.enhance(0.7)
        enhancer = ImageEnhance.Contrast(vintage)
        vintage = enhancer.enhance(1.2)
        return vintage
    
    def _apply_botanical_enhancement(self, image: Image.Image) -> Image.Image:
        """Apply botanical photography enhancement"""
        # Enhance colors typical in plant photography
        enhancer = ImageEnhance.Color(image)
        enhanced = enhancer.enhance(1.3)  # Boost saturation
        enhancer = ImageEnhance.Sharpness(enhanced)
        enhanced = enhancer.enhance(1.2)  # Sharpen details
        return enhanced
    
    def _extract_plant_features(self, analysis_data: Dict) -> List[str]:
        """Extract key plant features from analysis"""
        features = []
        if isinstance(analysis_data, dict):
            # Extract features based on analysis structure
            if 'morphological_analysis' in analysis_data:
                morph = analysis_data['morphological_analysis']
                if isinstance(morph, dict):
                    features.extend(morph.keys())
        return features
    
    def _calculate_quality_score(self, analysis_data: Dict) -> float:
        """Calculate overall image quality score"""
        # Basic quality assessment
        return 0.85  # Placeholder
    
    def _generate_photo_recommendations(self, analysis_data: Dict) -> List[str]:
        """Generate photography improvement recommendations"""
        recommendations = [
            "Consider increasing sharpness for better detail",
            "Adjust lighting to reduce shadows",
            "Crop closer to flower for better composition"
        ]
        return recommendations
    
    def _create_export_package(self, session: Dict, options: Dict) -> Dict[str, Any]:
        """Create export package with all versions and metadata"""
        try:
            package_name = f"orchid_edit_package_{session['session_id'][:8]}.zip"
            package_path = os.path.join(self.temp_dir, package_name)
            
            with zipfile.ZipFile(package_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Add original image
                if os.path.exists(session['original_path']):
                    zipf.write(session['original_path'], 'original.jpg')
                
                # Add final edited image
                if os.path.exists(session['current_path']):
                    zipf.write(session['current_path'], 'final_edited.jpg')
                
                # Add metadata JSON
                metadata = {
                    'session_info': {
                        'session_id': session['session_id'],
                        'orchid_name': session['orchid_name'],
                        'created_at': session['created_at']
                    },
                    'edit_history': session['edit_history'],
                    'filters_applied': session['filters_applied'],
                    'analysis_data': session.get('analysis_data', {})
                }
                
                metadata_json = json.dumps(metadata, indent=2)
                zipf.writestr('metadata.json', metadata_json)
            
            return {
                'success': True,
                'type': 'package',
                'filename': package_name,
                'local_path': package_path,
                'size': os.path.getsize(package_path)
            }
            
        except Exception as e:
            logger.error(f"Error creating export package: {e}")
            return {'error': str(e)}

# Initialize the photo editor
photo_editor = AdvancedPhotoEditor()