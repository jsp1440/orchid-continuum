"""
Botany Lab - Stats & Imports System
Integrated Flask version of the Node.js POC functionality
"""

import pandas as pd
import numpy as np
import json
import requests
import io
from flask import Blueprint, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from scipy import stats
from scipy.stats import spearmanr, ttest_ind, chi2_contingency
import re
from PIL import Image, ExifTags
from collections import Counter
import uuid
from datetime import datetime
import logging

from app import db
from models import OrchidRecord

logger = logging.getLogger(__name__)

botany_lab_bp = Blueprint('botany_lab', __name__, url_prefix='/botany-lab')

class BotanyLabStats:
    """Statistical analysis tools for orchid research"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_csv_data(self, csv_text):
        """Parse CSV text into structured data"""
        try:
            # Detect delimiter
            delimiter = '\t' if '\t' in csv_text.split('\n')[0] else ','
            
            # Use pandas for robust CSV parsing
            df = pd.read_csv(io.StringIO(csv_text), delimiter=delimiter)
            
            # Clean column names
            df.columns = df.columns.str.strip()
            
            # Convert to records format
            records = df.to_dict('records')
            columns = list(df.columns)
            
            return {
                'success': True,
                'records': records,
                'columns': columns,
                'row_count': len(records),
                'preview': records[:20]  # First 20 rows for preview
            }
            
        except Exception as e:
            self.logger.error(f"CSV parsing error: {e}")
            return {'success': False, 'error': str(e)}
    
    def fetch_external_data(self, url):
        """Fetch data from external URL (Google Drive, Dropbox, etc.)"""
        try:
            # Convert Google Drive share links to direct download
            if 'drive.google.com' in url and '/file/d/' in url:
                file_id = re.search(r'/file/d/([a-zA-Z0-9-_]+)', url)
                if file_id:
                    url = f"https://drive.google.com/uc?export=download&id={file_id.group(1)}"
            
            # Convert Dropbox share links
            if 'dropbox.com' in url and '?dl=0' in url:
                url = url.replace('?dl=0', '?dl=1')
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            return self.parse_csv_data(response.text)
            
        except Exception as e:
            self.logger.error(f"External data fetch error: {e}")
            return {'success': False, 'error': str(e)}
    
    def calculate_summary_stats(self, data, column):
        """Calculate summary statistics for a numerical column"""
        try:
            # Extract numerical values
            values = []
            for record in data:
                val = record.get(column)
                if val is not None:
                    # Clean and convert to float
                    clean_val = re.sub(r'[^0-9eE.\-+]', '', str(val))
                    try:
                        values.append(float(clean_val))
                    except ValueError:
                        continue
            
            if not values:
                return {'error': 'No valid numerical values found'}
            
            values = np.array(values)
            
            return {
                'count': len(values),
                'mean': float(np.mean(values)),
                'median': float(np.median(values)),
                'std': float(np.std(values)),
                'min': float(np.min(values)),
                'max': float(np.max(values)),
                'q25': float(np.percentile(values, 25)),
                'q75': float(np.percentile(values, 75))
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def calculate_spearman_correlation(self, data, col_x, col_y):
        """Calculate Spearman correlation between two numerical columns"""
        try:
            x_vals, y_vals = [], []
            
            for record in data:
                x_val = record.get(col_x)
                y_val = record.get(col_y)
                
                if x_val is not None and y_val is not None:
                    try:
                        x_clean = float(re.sub(r'[^0-9eE.\-+]', '', str(x_val)))
                        y_clean = float(re.sub(r'[^0-9eE.\-+]', '', str(y_val)))
                        x_vals.append(x_clean)
                        y_vals.append(y_clean)
                    except ValueError:
                        continue
            
            if len(x_vals) < 3:
                return {'error': 'Need at least 3 paired values for correlation'}
            
            correlation, p_value = spearmanr(x_vals, y_vals)
            
            return {
                'correlation': float(correlation),
                'p_value': float(p_value),
                'sample_size': len(x_vals),
                'interpretation': self._interpret_correlation(correlation, p_value)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def perform_welch_t_test(self, data, numeric_col, group_col):
        """Perform Welch's t-test comparing numeric values between two groups"""
        try:
            groups = {}
            
            # Group data by categorical column
            for record in data:
                group_val = str(record.get(group_col, 'unknown'))
                numeric_val = record.get(numeric_col)
                
                if numeric_val is not None:
                    try:
                        clean_val = float(re.sub(r'[^0-9eE.\-+]', '', str(numeric_val)))
                        if group_val not in groups:
                            groups[group_val] = []
                        groups[group_val].append(clean_val)
                    except ValueError:
                        continue
            
            group_names = list(groups.keys())
            if len(group_names) != 2:
                return {'error': f'Expected 2 groups, found {len(group_names)}: {group_names}'}
            
            group1_vals = groups[group_names[0]]
            group2_vals = groups[group_names[1]]
            
            if len(group1_vals) < 2 or len(group2_vals) < 2:
                return {'error': 'Each group needs at least 2 values'}
            
            t_stat, p_value = ttest_ind(group1_vals, group2_vals, equal_var=False)
            
            return {
                'groups': {
                    group_names[0]: {
                        'count': len(group1_vals),
                        'mean': float(np.mean(group1_vals)),
                        'std': float(np.std(group1_vals))
                    },
                    group_names[1]: {
                        'count': len(group2_vals),
                        'mean': float(np.mean(group2_vals)),
                        'std': float(np.std(group2_vals))
                    }
                },
                't_statistic': float(t_stat),
                'p_value': float(p_value),
                'interpretation': self._interpret_t_test(p_value)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def perform_chi_square_test(self, data, col_x, col_y):
        """Perform chi-square test of independence"""
        try:
            # Create contingency table
            contingency_data = {}
            
            for record in data:
                x_val = str(record.get(col_x, 'unknown'))
                y_val = str(record.get(col_y, 'unknown'))
                
                if x_val not in contingency_data:
                    contingency_data[x_val] = {}
                if y_val not in contingency_data[x_val]:
                    contingency_data[x_val][y_val] = 0
                contingency_data[x_val][y_val] += 1
            
            # Convert to matrix format
            y_categories = sorted(set(y_val for row in contingency_data.values() for y_val in row.keys()))
            x_categories = sorted(contingency_data.keys())
            
            matrix = []
            for x_cat in x_categories:
                row = []
                for y_cat in y_categories:
                    row.append(contingency_data[x_cat].get(y_cat, 0))
                matrix.append(row)
            
            chi2_stat, p_value, dof, expected = chi2_contingency(matrix)
            
            return {
                'chi2_statistic': float(chi2_stat),
                'p_value': float(p_value),
                'degrees_of_freedom': int(dof),
                'x_categories': x_categories,
                'y_categories': y_categories,
                'observed_matrix': matrix,
                'interpretation': self._interpret_chi_square(p_value)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def perform_linear_regression(self, data, col_x, col_y):
        """Simple linear regression Y ~ X"""
        try:
            x_vals, y_vals = [], []
            
            for record in data:
                x_val = record.get(col_x)
                y_val = record.get(col_y)
                
                if x_val is not None and y_val is not None:
                    try:
                        x_clean = float(re.sub(r'[^0-9eE.\-+]', '', str(x_val)))
                        y_clean = float(re.sub(r'[^0-9eE.\-+]', '', str(y_val)))
                        x_vals.append(x_clean)
                        y_vals.append(y_clean)
                    except ValueError:
                        continue
            
            if len(x_vals) < 3:
                return {'error': 'Need at least 3 data points for regression'}
            
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_vals, y_vals)
            
            return {
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_value ** 2),
                'p_value': float(p_value),
                'standard_error': float(std_err),
                'sample_size': len(x_vals),
                'equation': f"Y = {slope:.4f} * X + {intercept:.4f}",
                'interpretation': self._interpret_regression(r_value ** 2, p_value)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_image(self, image_url):
        """Analyze image for color histogram and EXIF data"""
        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()
            
            image = Image.open(io.BytesIO(response.content))
            
            # Extract EXIF data
            exif_data = {}
            try:
                if hasattr(image, 'getexif'):
                    exif = image.getexif()
                    if exif:
                        for tag_id, value in exif.items():
                            tag = ExifTags.TAGS.get(tag_id, tag_id)
                            exif_data[tag] = str(value)
            except Exception as e:
                logger.warning(f"Could not extract EXIF data: {e}")
            
            # Color histogram analysis
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Resize for processing
            image.thumbnail((400, 400))
            pixels = list(image.getdata())
            
            # Calculate dominant colors
            color_counts = Counter(pixels)
            most_common = color_counts.most_common(5)
            
            dominant_colors = []
            for color, count in most_common:
                r, g, b = color
                hex_color = f"#{r:02x}{g:02x}{b:02x}"
                dominant_colors.append({
                    'rgb': color,
                    'hex': hex_color,
                    'count': count,
                    'percentage': round(count / len(pixels) * 100, 2)
                })
            
            return {
                'success': True,
                'exif_data': exif_data,
                'dominant_colors': dominant_colors,
                'image_size': image.size,
                'total_pixels': len(pixels)
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _interpret_correlation(self, correlation, p_value):
        """Provide interpretation of correlation results"""
        strength = abs(correlation)
        if strength < 0.3:
            strength_desc = "weak"
        elif strength < 0.7:
            strength_desc = "moderate"
        else:
            strength_desc = "strong"
        
        direction = "positive" if correlation > 0 else "negative"
        significance = "significant" if p_value < 0.05 else "not significant"
        
        return f"{strength_desc} {direction} correlation, {significance} (p={p_value:.4f})"
    
    def _interpret_t_test(self, p_value):
        """Provide interpretation of t-test results"""
        if p_value < 0.001:
            return "Highly significant difference (p<0.001)"
        elif p_value < 0.01:
            return "Very significant difference (p<0.01)"
        elif p_value < 0.05:
            return "Significant difference (p<0.05)"
        else:
            return f"No significant difference (p={p_value:.4f})"
    
    def _interpret_chi_square(self, p_value):
        """Provide interpretation of chi-square results"""
        if p_value < 0.05:
            return f"Significant association between variables (p={p_value:.4f})"
        else:
            return f"No significant association (p={p_value:.4f})"
    
    def _interpret_regression(self, r_squared, p_value):
        """Provide interpretation of regression results"""
        variance_explained = round(r_squared * 100, 1)
        significance = "significant" if p_value < 0.05 else "not significant"
        
        return f"Model explains {variance_explained}% of variance, {significance} (p={p_value:.4f})"


# Initialize the stats analyzer
botany_stats = BotanyLabStats()

@botany_lab_bp.route('/')
def index():
    """Main Botany Lab Stats & Imports interface"""
    return render_template('botany_lab/stats_imports.html')

@botany_lab_bp.route('/api/parse-csv', methods=['POST'])
def parse_csv():
    """Parse CSV data from text input"""
    data = request.get_json()
    csv_text = data.get('csv_text', '')
    
    result = botany_stats.parse_csv_data(csv_text)
    
    if result.get('success'):
        # Store in session for later use
        session['botany_lab_data'] = {
            'records': result['records'],
            'columns': result['columns']
        }
    
    return jsonify(result)

@botany_lab_bp.route('/api/fetch-url', methods=['POST'])
def fetch_external_url():
    """Fetch data from external URL"""
    data = request.get_json()
    url = data.get('url', '')
    
    result = botany_stats.fetch_external_data(url)
    
    if result.get('success'):
        # Store in session for later use
        session['botany_lab_data'] = {
            'records': result['records'],
            'columns': result['columns']
        }
    
    return jsonify(result)

@botany_lab_bp.route('/api/summary-stats', methods=['POST'])
def summary_stats():
    """Calculate summary statistics"""
    data = request.get_json()
    column = data.get('column')
    
    lab_data = session.get('botany_lab_data')
    if not lab_data:
        return jsonify({'error': 'No data loaded'})
    
    result = botany_stats.calculate_summary_stats(lab_data['records'], column)
    return jsonify(result)

@botany_lab_bp.route('/api/correlation', methods=['POST'])
def correlation_analysis():
    """Calculate Spearman correlation"""
    data = request.get_json()
    col_x = data.get('col_x')
    col_y = data.get('col_y')
    
    lab_data = session.get('botany_lab_data')
    if not lab_data:
        return jsonify({'error': 'No data loaded'})
    
    result = botany_stats.calculate_spearman_correlation(lab_data['records'], col_x, col_y)
    return jsonify(result)

@botany_lab_bp.route('/api/t-test', methods=['POST'])
def t_test_analysis():
    """Perform Welch's t-test"""
    data = request.get_json()
    numeric_col = data.get('numeric_col')
    group_col = data.get('group_col')
    
    lab_data = session.get('botany_lab_data')
    if not lab_data:
        return jsonify({'error': 'No data loaded'})
    
    result = botany_stats.perform_welch_t_test(lab_data['records'], numeric_col, group_col)
    return jsonify(result)

@botany_lab_bp.route('/api/chi-square', methods=['POST'])
def chi_square_analysis():
    """Perform chi-square test"""
    data = request.get_json()
    col_x = data.get('col_x')
    col_y = data.get('col_y')
    
    lab_data = session.get('botany_lab_data')
    if not lab_data:
        return jsonify({'error': 'No data loaded'})
    
    result = botany_stats.perform_chi_square_test(lab_data['records'], col_x, col_y)
    return jsonify(result)

@botany_lab_bp.route('/api/regression', methods=['POST'])
def regression_analysis():
    """Perform linear regression"""
    data = request.get_json()
    col_x = data.get('col_x')
    col_y = data.get('col_y')
    
    lab_data = session.get('botany_lab_data')
    if not lab_data:
        return jsonify({'error': 'No data loaded'})
    
    result = botany_stats.perform_linear_regression(lab_data['records'], col_x, col_y)
    return jsonify(result)

@botany_lab_bp.route('/api/analyze-image', methods=['POST'])
def analyze_image():
    """Analyze image for colors and EXIF"""
    data = request.get_json()
    image_url = data.get('image_url', '')
    
    result = botany_stats.analyze_image(image_url)
    return jsonify(result)

@botany_lab_bp.route('/api/save-dataset-pointer', methods=['POST'])
def save_dataset_pointer():
    """Save a pointer to an external dataset"""
    data = request.get_json()
    dataset_url = data.get('dataset_url', '')
    title = data.get('title', 'Imported Dataset')
    description = data.get('description', '')
    
    # Create a new orchid record as a dataset pointer
    try:
        experiment_id = str(uuid.uuid4())
        
        # Store dataset pointer info
        pointer_record = {
            'experiment_id': experiment_id,
            'title': title,
            'dataset_url': dataset_url,
            'description': description,
            'created_at': datetime.utcnow().isoformat(),
            'type': 'external_dataset_pointer'
        }
        
        # For now, store in session (in production, you'd save to database)
        if 'dataset_pointers' not in session:
            session['dataset_pointers'] = []
        session['dataset_pointers'].append(pointer_record)
        
        return jsonify({
            'success': True,
            'experiment_id': experiment_id,
            'message': f'Dataset pointer saved successfully'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# Register the blueprint
def register_botany_lab_routes(app):
    """Register botany lab routes with the main app"""
    app.register_blueprint(botany_lab_bp)
    logger.info("🧪 Botany Lab Stats & Imports system registered successfully")