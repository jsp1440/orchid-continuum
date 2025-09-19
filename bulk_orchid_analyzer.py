"""
Bulk Orchid Image Analysis System
Advanced ZIP upload and AI metadata extraction for Gary Yong Gee demonstration
"""

import os
import json
import zipfile
import shutil
from datetime import datetime
from PIL import Image, ExifTags
from PIL.ExifTags import TAGS
import pandas as pd
from flask import Blueprint, render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import db
from models import OrchidRecord
from orchid_ai import analyze_orchid_image
import tempfile
import uuid

bulk_analyzer = Blueprint('bulk_analyzer', __name__)

class BulkOrchidProcessor:
    """Advanced bulk processing for orchid image collections"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.bmp']
        self.temp_dir = None
        self.processing_stats = {
            'total_files': 0,
            'processed_files': 0,
            'successful_extractions': 0,
            'errors': 0,
            'start_time': None,
            'end_time': None
        }
    
    def extract_exif_metadata(self, image_path):
        """Extract comprehensive EXIF data from images"""
        try:
            image = Image.open(image_path)
            exifdata = image.getexif()
            
            metadata = {
                'camera_make': None,
                'camera_model': None,
                'datetime_taken': None,
                'gps_coordinates': None,
                'focal_length': None,
                'aperture': None,
                'iso_speed': None,
                'exposure_time': None,
                'flash_used': None,
                'image_width': image.width,
                'image_height': image.height,
                'color_space': None,
                'lens_info': None
            }
            
            if exifdata is not None:
                for tag_id in exifdata:
                    tag = TAGS.get(tag_id, tag_id)
                    data = exifdata.get(tag_id)
                    
                    if tag == "Make":
                        metadata['camera_make'] = str(data)
                    elif tag == "Model":
                        metadata['camera_model'] = str(data)
                    elif tag == "DateTime":
                        try:
                            metadata['datetime_taken'] = datetime.strptime(str(data), "%Y:%m:%d %H:%M:%S")
                        except:
                            metadata['datetime_taken'] = str(data)
                    elif tag == "FocalLength":
                        metadata['focal_length'] = float(data) if data else None
                    elif tag == "FNumber":
                        metadata['aperture'] = f"f/{float(data)}" if data else None
                    elif tag == "ISOSpeedRatings":
                        metadata['iso_speed'] = int(data) if data else None
                    elif tag == "ExposureTime":
                        metadata['exposure_time'] = f"1/{int(1/float(data))}" if data and float(data) > 0 else str(data)
                    elif tag == "Flash":
                        metadata['flash_used'] = "Yes" if data and int(data) > 0 else "No"
                    elif tag == "ColorSpace":
                        metadata['color_space'] = "sRGB" if data == 1 else "Adobe RGB" if data == 2 else str(data)
                    elif tag == "LensModel":
                        metadata['lens_info'] = str(data)
                    elif tag == "GPSInfo":
                        # Extract GPS coordinates if available
                        gps_data = self.extract_gps_coordinates(data)
                        if gps_data:
                            metadata['gps_coordinates'] = gps_data
            
            return metadata
            
        except Exception as e:
            print(f"EXIF extraction error for {image_path}: {e}")
            return {'error': str(e)}
    
    def extract_gps_coordinates(self, gps_info):
        """Extract GPS coordinates from EXIF GPS data"""
        try:
            if not gps_info:
                return None
                
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            lat = gps_info.get(2)  # GPSLatitude
            lat_ref = gps_info.get(1)  # GPSLatitudeRef
            lon = gps_info.get(4)  # GPSLongitude
            lon_ref = gps_info.get(3)  # GPSLongitudeRef
            
            if lat and lon and lat_ref and lon_ref:
                latitude = convert_to_degrees(lat)
                longitude = convert_to_degrees(lon)
                
                if lat_ref == 'S':
                    latitude = -latitude
                if lon_ref == 'W':
                    longitude = -longitude
                    
                return f"{latitude:.6f}, {longitude:.6f}"
            
        except Exception as e:
            print(f"GPS extraction error: {e}")
            return None
    
    def analyze_flowering_stage(self, ai_analysis):
        """Determine flowering stage from AI analysis"""
        description = ai_analysis.get('description', '').lower()
        
        stages = {
            'bud': ['bud', 'buds', 'unopened', 'closed flower', 'developing'],
            'early_bloom': ['just opening', 'beginning to open', 'starting to bloom', 'early flower'],
            'full_bloom': ['full bloom', 'fully open', 'peak flowering', 'open flower', 'in flower'],
            'late_bloom': ['fading', 'wilting', 'past peak', 'aging flower'],
            'seed_pod': ['seed pod', 'fruit', 'capsule', 'mature fruit']
        }
        
        for stage, keywords in stages.items():
            if any(keyword in description for keyword in keywords):
                return stage.replace('_', ' ').title()
        
        # Check if any flowers are visible
        if any(word in description for word in ['flower', 'bloom', 'petal', 'lip', 'column']):
            return 'Full Bloom'  # Default if flowers are present
        
        return 'Vegetative'  # No flowers detected
    
    def extract_botanical_features(self, ai_analysis):
        """Extract detailed botanical features from AI analysis"""
        description = ai_analysis.get('description', '').lower()
        
        features = {
            'growth_habit': self.determine_growth_habit(description),
            'leaf_type': self.determine_leaf_type(description),
            'flower_color': self.extract_color_info(description),
            'flower_size': self.extract_size_info(description),
            'flower_count': self.extract_flower_count(description),
            'special_features': self.extract_special_features(description),
            'pseudobulb_present': self.detect_pseudobulbs(description),
            'root_type': self.determine_root_type(description)
        }
        
        return features
    
    def determine_growth_habit(self, description):
        """Determine orchid growth habit"""
        if any(word in description for word in ['epiphyte', 'tree', 'bark', 'mounted', 'aerial']):
            return 'Epiphytic'
        elif any(word in description for word in ['ground', 'terrestrial', 'soil', 'earth']):
            return 'Terrestrial'
        elif any(word in description for word in ['rock', 'stone', 'cliff', 'lithophyte']):
            return 'Lithophytic'
        return 'Unknown'
    
    def determine_leaf_type(self, description):
        """Determine leaf characteristics"""
        if any(word in description for word in ['thick', 'succulent', 'fleshy']):
            return 'Succulent'
        elif any(word in description for word in ['thin', 'papery', 'delicate']):
            return 'Membranous'
        elif any(word in description for word in ['strap', 'long', 'linear']):
            return 'Linear'
        return 'Standard'
    
    def extract_color_info(self, description):
        """Extract flower color information"""
        colors = ['white', 'yellow', 'pink', 'purple', 'red', 'orange', 'green', 'blue', 'brown', 'cream']
        found_colors = [color for color in colors if color in description]
        return ', '.join(found_colors) if found_colors else 'Not specified'
    
    def extract_size_info(self, description):
        """Extract size information"""
        if any(word in description for word in ['large', 'big', 'huge']):
            return 'Large'
        elif any(word in description for word in ['small', 'tiny', 'miniature']):
            return 'Small'
        elif any(word in description for word in ['medium', 'moderate']):
            return 'Medium'
        return 'Not specified'
    
    def extract_flower_count(self, description):
        """Extract approximate flower count"""
        import re
        numbers = re.findall(r'\b(\d+)\b', description)
        if numbers:
            return int(numbers[0])
        elif any(word in description for word in ['single', 'one']):
            return 1
        elif any(word in description for word in ['multiple', 'many', 'several']):
            return 'Multiple'
        return 'Not specified'
    
    def extract_special_features(self, description):
        """Extract special botanical features"""
        features = []
        special_terms = [
            'fragrant', 'waxy', 'spotted', 'striped', 'variegated', 
            'hairy', 'glossy', 'matte', 'translucent', 'veined'
        ]
        
        for term in special_terms:
            if term in description:
                features.append(term.title())
        
        return ', '.join(features) if features else 'None noted'
    
    def detect_pseudobulbs(self, description):
        """Detect presence of pseudobulbs"""
        pseudobulb_terms = ['pseudobulb', 'bulb', 'swollen stem', 'storage organ']
        return any(term in description for term in pseudobulb_terms)
    
    def determine_root_type(self, description):
        """Determine root type"""
        if any(word in description for word in ['aerial', 'hanging', 'exposed']):
            return 'Aerial'
        elif any(word in description for word in ['thick', 'fleshy', 'storage']):
            return 'Storage'
        return 'Standard'
    
    def process_zip_file(self, zip_path, progress_callback=None):
        """Process entire ZIP file of orchid images"""
        self.processing_stats['start_time'] = datetime.now()
        results = []
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Create temporary directory
                self.temp_dir = tempfile.mkdtemp()
                zip_ref.extractall(self.temp_dir)
                
                # Get all image files
                image_files = []
                for root, dirs, files in os.walk(self.temp_dir):
                    for file in files:
                        if any(file.lower().endswith(ext) for ext in self.supported_formats):
                            image_files.append(os.path.join(root, file))
                
                self.processing_stats['total_files'] = len(image_files)
                
                # Process each image
                for i, image_path in enumerate(image_files):
                    try:
                        if progress_callback:
                            progress_callback(i, len(image_files))
                        
                        # Extract EXIF metadata
                        exif_data = self.extract_exif_metadata(image_path)
                        
                        # AI analysis
                        ai_analysis = analyze_orchid_image(image_path)
                        
                        # Extract botanical features
                        botanical_features = self.extract_botanical_features(ai_analysis)
                        
                        # Determine flowering stage
                        flowering_stage = self.analyze_flowering_stage(ai_analysis)
                        
                        # Compile comprehensive result
                        result = {
                            'filename': os.path.basename(image_path),
                            'file_path': image_path,
                            'file_size': os.path.getsize(image_path),
                            'processed_at': datetime.now().isoformat(),
                            
                            # EXIF Metadata
                            'camera_info': exif_data,
                            'photo_datetime': exif_data.get('datetime_taken'),
                            'gps_location': exif_data.get('gps_coordinates'),
                            
                            # AI Analysis Results
                            'ai_description': ai_analysis.get('description'),
                            'ai_confidence': ai_analysis.get('confidence'),
                            'identified_species': ai_analysis.get('species'),
                            'identified_genus': ai_analysis.get('genus'),
                            
                            # Botanical Analysis
                            'flowering_stage': flowering_stage,
                            'growth_habit': botanical_features['growth_habit'],
                            'leaf_type': botanical_features['leaf_type'],
                            'flower_color': botanical_features['flower_color'],
                            'flower_size': botanical_features['flower_size'],
                            'flower_count': botanical_features['flower_count'],
                            'special_features': botanical_features['special_features'],
                            'pseudobulb_present': botanical_features['pseudobulb_present'],
                            'root_type': botanical_features['root_type'],
                            
                            # Processing Status
                            'processing_success': True,
                            'extraction_time': (datetime.now() - self.processing_stats['start_time']).total_seconds()
                        }
                        
                        results.append(result)
                        self.processing_stats['successful_extractions'] += 1
                        
                    except Exception as e:
                        error_result = {
                            'filename': os.path.basename(image_path),
                            'processing_success': False,
                            'error': str(e),
                            'processed_at': datetime.now().isoformat()
                        }
                        results.append(error_result)
                        self.processing_stats['errors'] += 1
                    
                    self.processing_stats['processed_files'] += 1
                
        except Exception as e:
            print(f"ZIP processing error: {e}")
            return {'error': str(e)}
        
        finally:
            # Cleanup
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
            
            self.processing_stats['end_time'] = datetime.now()
        
        return {
            'results': results,
            'statistics': self.processing_stats,
            'summary': self.generate_analysis_summary(results)
        }
    
    def generate_analysis_summary(self, results):
        """Generate comprehensive analysis summary"""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.get('processing_success', False)]
        
        summary = {
            'total_images': len(results),
            'successful_analyses': len(successful_results),
            'success_rate': (len(successful_results) / len(results)) * 100 if results else 0,
            
            'flowering_stages': {},
            'growth_habits': {},
            'flower_colors': {},
            'genera_identified': {},
            'photos_with_gps': 0,
            'photos_with_datetime': 0,
            'date_range': {'earliest': None, 'latest': None},
            'camera_models': {},
            'average_confidence': 0
        }
        
        confidences = []
        dates = []
        
        for result in successful_results:
            # Flowering stages
            stage = result.get('flowering_stage', 'Unknown')
            summary['flowering_stages'][stage] = summary['flowering_stages'].get(stage, 0) + 1
            
            # Growth habits
            habit = result.get('growth_habit', 'Unknown')
            summary['growth_habits'][habit] = summary['growth_habits'].get(habit, 0) + 1
            
            # Flower colors
            color = result.get('flower_color', 'Unknown')
            summary['flower_colors'][color] = summary['flower_colors'].get(color, 0) + 1
            
            # Genera
            genus = result.get('identified_genus', 'Unknown')
            summary['genera_identified'][genus] = summary['genera_identified'].get(genus, 0) + 1
            
            # Location data
            if result.get('gps_location'):
                summary['photos_with_gps'] += 1
            
            # DateTime data
            if result.get('photo_datetime'):
                summary['photos_with_datetime'] += 1
                dates.append(result['photo_datetime'])
            
            # Camera models
            camera_info = result.get('camera_info', {})
            camera_model = camera_info.get('camera_model', 'Unknown')
            summary['camera_models'][camera_model] = summary['camera_models'].get(camera_model, 0) + 1
            
            # Confidence scores
            confidence = result.get('ai_confidence')
            if confidence:
                confidences.append(confidence)
        
        # Calculate averages and ranges
        if confidences:
            summary['average_confidence'] = sum(confidences) / len(confidences)
        
        if dates:
            summary['date_range']['earliest'] = min(dates)
            summary['date_range']['latest'] = max(dates)
        
        return summary

# Initialize processor
bulk_processor = BulkOrchidProcessor()

@bulk_analyzer.route('/bulk-upload')
def bulk_upload_interface():
    """Bulk orchid image analysis interface"""
    return render_template('bulk_analysis/upload_interface.html')

@bulk_analyzer.route('/api/process-zip', methods=['POST'])
def process_zip_upload():
    """Process uploaded ZIP file"""
    try:
        print(f"DEBUG: Processing ZIP upload request")
        print(f"DEBUG: Request files: {request.files}")
        print(f"DEBUG: Request form: {request.form}")
        
        if 'zip_file' not in request.files:
            print("DEBUG: No zip_file in request.files")
            return jsonify({'error': 'No ZIP file provided'}), 400
        
        zip_file = request.files['zip_file']
        print(f"DEBUG: ZIP file: {zip_file}, filename: {zip_file.filename}")
        
        if zip_file.filename == '':
            print("DEBUG: Empty filename")
            return jsonify({'error': 'No file selected'}), 400
        
        if not zip_file.filename.lower().endswith('.zip'):
            print(f"DEBUG: Invalid file extension: {zip_file.filename}")
            return jsonify({'error': 'File must be a ZIP archive'}), 400
        
        # Create temp directory if it doesn't exist
        temp_dir = tempfile.gettempdir()
        os.makedirs(temp_dir, exist_ok=True)
        
        # Save uploaded file
        temp_zip_path = os.path.join(temp_dir, f"orchid_bulk_{uuid.uuid4().hex}.zip")
        print(f"DEBUG: Saving ZIP to: {temp_zip_path}")
        zip_file.save(temp_zip_path)
        
        print(f"DEBUG: ZIP file saved, size: {os.path.getsize(temp_zip_path)} bytes")
        
        # Process the ZIP file
        print("DEBUG: Starting ZIP processing...")
        results = bulk_processor.process_zip_file(temp_zip_path)
        
        # Cleanup
        if os.path.exists(temp_zip_path):
            os.remove(temp_zip_path)
            print("DEBUG: Temporary ZIP file cleaned up")
        
        print(f"DEBUG: Processing completed successfully")
        return jsonify({
            'success': True,
            'data': results,
            'message': f"Successfully processed {results.get('statistics', {}).get('successful_extractions', 0)} images"
        })
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"DEBUG: Error processing ZIP: {str(e)}")
        print(f"DEBUG: Full traceback: {error_details}")
        return jsonify({'error': str(e), 'details': error_details}), 500

@bulk_analyzer.route('/api/export-results', methods=['POST'])
def export_results():
    """Export analysis results to various formats"""
    try:
        data = request.json.get('results', [])
        format_type = request.json.get('format', 'csv')
        
        if format_type == 'csv':
            # Convert to pandas DataFrame
            df = pd.DataFrame(data)
            
            # Create CSV file
            temp_csv_path = os.path.join(tempfile.gettempdir(), f"orchid_analysis_{uuid.uuid4().hex}.csv")
            df.to_csv(temp_csv_path, index=False)
            
            return send_file(temp_csv_path, as_attachment=True, download_name='orchid_analysis_results.csv')
        
        elif format_type == 'json':
            # Create JSON file
            temp_json_path = os.path.join(tempfile.gettempdir(), f"orchid_analysis_{uuid.uuid4().hex}.json")
            with open(temp_json_path, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            return send_file(temp_json_path, as_attachment=True, download_name='orchid_analysis_results.json')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500