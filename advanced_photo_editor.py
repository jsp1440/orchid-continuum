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
    
    def generate_social_caption(self, orchid: 'OrchidRecord', include_analysis: bool = False) -> str:
        """Generate social media caption with botanical information"""
        try:
            caption_parts = []
            
            # Plant identification
            if orchid.scientific_name:
                caption_parts.append(f"🌺 {orchid.scientific_name}")
            elif orchid.display_name:
                caption_parts.append(f"🌺 {orchid.display_name}")
            else:
                caption_parts.append("🌺 Beautiful Orchid")
            
            # Botanical classification
            botanical_info = []
            if orchid.genus:
                botanical_info.append(f"Genus: {orchid.genus}")
            if orchid.species:
                botanical_info.append(f"Species: {orchid.species}")
            
            # Determine if hybrid or intergeneric
            if orchid.scientific_name:
                if 'x' in orchid.scientific_name.lower() or '×' in orchid.scientific_name:
                    if orchid.genus and len(orchid.scientific_name.split()) > 1:
                        # Check if it's intergeneric (multiple genus names)
                        genus_parts = orchid.scientific_name.split()
                        if any('x' in part.lower() or '×' in part for part in genus_parts[:2]):
                            botanical_info.append("Type: Intergeneric Hybrid")
                        else:
                            botanical_info.append("Type: Hybrid")
                    else:
                        botanical_info.append("Type: Hybrid")
                else:
                    botanical_info.append("Type: Species")
            
            if botanical_info:
                caption_parts.append(" | ".join(botanical_info))
            
            # Add analysis info if available and requested
            if include_analysis and orchid.ai_description:
                description = orchid.ai_description[:100] + "..." if len(orchid.ai_description) > 100 else orchid.ai_description
                caption_parts.append(f"\n📝 {description}")
            
            # Add hashtags
            hashtags = ["#Orchids", "#OrchidPhotography", "#Botanica", "#FlowerPhotography", "#PlantLovers"]
            if orchid.genus:
                hashtags.append(f"#{orchid.genus.replace(' ', '')}")
            
            caption_parts.append(" ".join(hashtags))
            
            # Add branding and copyright
            caption_parts.append("\n📸 Enhanced with AI photo editing")
            caption_parts.append("🔬 Orchid Continuum project, Copyright 2025")
            
            return "\n\n".join(caption_parts)
            
        except Exception as e:
            logger.error(f"Error generating social caption: {e}")
            return f"🌺 Beautiful orchid enhanced with professional photo editing\n\n#Orchids #OrchidPhotography #Botanica\n\n📸 Enhanced with AI photo editing\n🔬 Orchid Continuum project, Copyright 2025"
    
    def create_captioned_image(self, session_id: str, caption_options: Dict[str, Any]) -> Dict[str, Any]:
        """Create image with integrated caption overlay"""
        try:
            session = self.editing_sessions.get(session_id)
            if not session:
                return {'error': 'Invalid session'}
            
            orchid = OrchidRecord.query.get(session['orchid_id'])
            image = Image.open(session['current_path'])
            
            # Caption settings
            add_caption_overlay = caption_options.get('add_overlay', False)
            caption_position = caption_options.get('position', 'bottom')
            caption_style = caption_options.get('style', 'classic')
            
            if add_caption_overlay:
                # Create caption text
                caption_text = self._generate_image_caption(orchid, caption_style)
                
                # Add caption overlay to image
                captioned_image = self._add_caption_overlay(image, caption_text, caption_position, caption_style)
            else:
                captioned_image = image
            
            # Save captioned image
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            captioned_filename = f"captioned_{session_id}_{timestamp}.jpg"
            captioned_path = os.path.join(self.temp_dir, captioned_filename)
            captioned_image.save(captioned_path, 'JPEG', quality=95)
            
            # Generate social media caption
            social_caption = self.generate_social_caption(orchid, include_analysis=caption_options.get('include_analysis', False))
            
            return {
                'success': True,
                'captioned_image_path': captioned_path,
                'social_caption': social_caption,
                'image_data': self._image_to_base64(captioned_image)
            }
            
        except Exception as e:
            logger.error(f"Error creating captioned image: {e}")
            return {'error': str(e)}
    
    def _generate_image_caption(self, orchid: 'OrchidRecord', style: str = 'classic') -> str:
        """Generate caption text for image overlay"""
        if style == 'minimal':
            return f"{orchid.scientific_name or orchid.display_name or 'Orchid'}\nOrchid Continuum © 2025"
        elif style == 'detailed':
            caption = f"{orchid.scientific_name or orchid.display_name or 'Beautiful Orchid'}\n"
            if orchid.genus:
                caption += f"Genus: {orchid.genus}"
                if orchid.species:
                    caption += f" | Species: {orchid.species}"
                caption += "\n"
            caption += "Orchid Continuum project © 2025"
            return caption
        else:  # classic
            return f"{orchid.scientific_name or orchid.display_name or 'Orchid'}\nOrchid Continuum © 2025"
    
    def _add_caption_overlay(self, image: Image.Image, caption_text: str, position: str, style: str) -> Image.Image:
        """Add caption overlay to image"""
        try:
            # Create a copy of the image
            captioned_image = image.copy()
            draw = ImageDraw.Draw(captioned_image)
            
            # Calculate text size and position
            img_width, img_height = captioned_image.size
            
            try:
                # Try to use a better font if available
                font_size = max(24, img_width // 30)
                # For now, use default font
                font = None
            except:
                font = None
            
            # Calculate text dimensions
            text_lines = caption_text.split('\n')
            line_height = 30 if font is None else font.getsize('A')[1] + 5
            text_height = len(text_lines) * line_height
            max_line_width = max([len(line) * 12 for line in text_lines])  # Approximate width
            
            # Position the text
            if position == 'bottom':
                y = img_height - text_height - 20
            elif position == 'top':
                y = 20
            else:  # center
                y = (img_height - text_height) // 2
            
            x = 20
            
            # Draw background rectangle
            padding = 15
            bg_coords = [
                x - padding,
                y - padding,
                x + max_line_width + padding,
                y + text_height + padding
            ]
            
            # Semi-transparent black background
            overlay = Image.new('RGBA', captioned_image.size, (0, 0, 0, 0))
            overlay_draw = ImageDraw.Draw(overlay)
            overlay_draw.rectangle(bg_coords, fill=(0, 0, 0, 128))
            captioned_image = Image.alpha_composite(captioned_image.convert('RGBA'), overlay).convert('RGB')
            draw = ImageDraw.Draw(captioned_image)
            
            # Draw text lines
            for i, line in enumerate(text_lines):
                line_y = y + (i * line_height)
                draw.text((x, line_y), line, fill='white', font=font)
            
            return captioned_image
            
        except Exception as e:
            logger.error(f"Error adding caption overlay: {e}")
            return image

    def save_edited_image(self, session_id: str, save_options: Dict[str, Any]) -> Dict[str, Any]:
        """Save edited image with various options including captions and social sharing"""
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
            
            # Generate social media caption
            social_caption = self.generate_social_caption(orchid, include_analysis=save_options.get('include_analysis', False))
            
            # Process usage waivers
            usage_waivers = save_options.get('usage_waivers', {})
            if usage_waivers:
                # Add waiver information to social caption if permissions granted
                waiver_text = self._generate_waiver_text(usage_waivers)
                if waiver_text:
                    social_caption += f"\n\n{waiver_text}"
            
            # Create captioned version if requested
            captioned_results = {}
            if save_options.get('create_captioned', False):
                caption_result = self.create_captioned_image(session_id, save_options.get('caption_options', {}))
                if caption_result.get('success'):
                    captioned_results = caption_result
            
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
                'social_caption': social_caption,
                'captioned_version': captioned_results.get('captioned_image_path') is not None,
                'usage_waivers': usage_waivers,
                'waiver_granted_at': datetime.now().isoformat() if usage_waivers else None,
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
                'social_caption': social_caption,
                'captioned_image': captioned_results.get('captioned_image_path'),
                'usage_permissions': usage_waivers,
                'social_sharing_data': {
                    'caption': social_caption,
                    'hashtags': ['Orchids', 'OrchidPhotography', 'Botanica', 'FlowerPhotography', 'PlantLovers'],
                    'image_url': drive_url,
                    'project_credit': 'Orchid Continuum project, Copyright 2025',
                    'usage_permissions': usage_waivers
                },
                'session_summary': {
                    'operations_performed': len(session['edit_history']),
                    'filters_applied': session['filters_applied'],
                    'analysis_completed': 'analysis_data' in session,
                    'waivers_granted': bool(usage_waivers)
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
    
    def _generate_waiver_text(self, waivers: Dict[str, Any]) -> str:
        """Generate waiver text for social media sharing"""
        waiver_parts = []
        
        if waivers.get('educational_use'):
            waiver_parts.append("✅ Available for educational use")
        if waivers.get('research_use'):
            waiver_parts.append("✅ Available for research purposes")
        if waivers.get('database_use'):
            waiver_parts.append("✅ Contributing to orchid identification database")
        if waivers.get('attribution_required'):
            waiver_parts.append("📝 Attribution required for reuse")
        
        if waiver_parts:
            return "📋 Usage Permissions:\n" + "\n".join(waiver_parts)
        return ""
    
    def check_usage_permissions(self, orchid_id: int, requested_use: str) -> Dict[str, Any]:
        """Check if an orchid photo has permission for specific usage"""
        try:
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid or not orchid.enhancement_data:
                return {'error': 'No permissions data available'}
            
            enhancement_data = json.loads(orchid.enhancement_data)
            edited_versions = enhancement_data.get('edited_versions', [])
            
            # Check latest version with waivers
            for version in reversed(edited_versions):
                waivers = version.get('usage_waivers', {})
                if waivers:
                    permission_granted = False
                    if requested_use == 'educational' and waivers.get('educational_use'):
                        permission_granted = True
                    elif requested_use == 'research' and waivers.get('research_use'):
                        permission_granted = True
                    elif requested_use == 'database' and waivers.get('database_use'):
                        permission_granted = True
                    
                    return {
                        'success': True,
                        'permission_granted': permission_granted,
                        'attribution_required': waivers.get('attribution_required', False),
                        'waiver_date': version.get('waiver_granted_at'),
                        'all_permissions': waivers
                    }
            
            return {'error': 'No usage waivers found'}
            
        except Exception as e:
            logger.error(f"Error checking usage permissions: {e}")
            return {'error': str(e)}

# Initialize the photo editor
photo_editor = AdvancedPhotoEditor()