"""
Enhanced Scientific Research Platform
Follows the complete scientific method with AI guidance and research capabilities
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from app import db
from models import OrchidRecord

# Create blueprint
scientific_research = Blueprint('scientific_research', __name__)

class ScientificMethod:
    """Complete scientific method workflow with AI guidance"""
    
    def __init__(self):
        self.stages = [
            {
                'id': 'observation',
                'title': 'Make Observations',
                'description': 'Use your senses to gather information about the natural world',
                'icon': 'eye',
                'color': '#3498db'
            },
            {
                'id': 'question', 
                'title': 'Ask Questions',
                'description': 'Formulate specific, testable questions based on your observations',
                'icon': 'help-circle',
                'color': '#e74c3c'
            },
            {
                'id': 'hypothesis',
                'title': 'Form Hypothesis',
                'description': 'Create a testable prediction that answers your question',
                'icon': 'lightbulb',
                'color': '#f39c12'
            },
            {
                'id': 'experiment',
                'title': 'Design Experiment',
                'description': 'Plan how to test your hypothesis with controlled variables',
                'icon': 'flask',
                'color': '#9b59b6'
            },
            {
                'id': 'data',
                'title': 'Collect Data',
                'description': 'Gather quantitative and qualitative data from your database',
                'icon': 'database',
                'color': '#1abc9c'
            },
            {
                'id': 'analysis',
                'title': 'Analyze Results',
                'description': 'Use statistical methods to find patterns and significance',
                'icon': 'bar-chart-2',
                'color': '#34495e'
            },
            {
                'id': 'conclusion',
                'title': 'Draw Conclusions',
                'description': 'Interpret results and determine if hypothesis is supported',
                'icon': 'check-circle',
                'color': '#27ae60'
            },
            {
                'id': 'communicate',
                'title': 'Share Results',
                'description': 'Write and publish your findings with proper citations',
                'icon': 'share-2',
                'color': '#2c3e50'
            }
        ]

class DataAnalyzer:
    """Statistical analysis tools for orchid research"""
    
    def __init__(self):
        self.analysis_methods = {
            'descriptive': ['mean', 'median', 'mode', 'std', 'range'],
            'correlation': ['pearson', 'spearman', 'kendall'],
            'comparison': ['t-test', 'anova', 'chi-square'],
            'regression': ['linear', 'logistic', 'polynomial']
        }
    
    def get_orchid_data(self, filters=None):
        """Retrieve orchid data for analysis"""
        try:
            query = db.session.query(OrchidRecord)
            
            if filters:
                if 'latitude_min' in filters and filters['latitude_min']:
                    query = query.filter(OrchidRecord.decimal_latitude >= float(filters['latitude_min']))
                if 'latitude_max' in filters and filters['latitude_max']:
                    query = query.filter(OrchidRecord.decimal_latitude <= float(filters['latitude_max']))
                if 'genus' in filters and filters['genus']:
                    query = query.filter(OrchidRecord.genus.ilike(f"%{filters['genus']}%"))
                if 'region' in filters and filters['region']:
                    query = query.filter(OrchidRecord.region.ilike(f"%{filters['region']}%"))
            
            results = query.all()
            
            # Convert to analysis-friendly format
            data = []
            for orchid in results:
                data.append({
                    'id': orchid.id,
                    'genus': orchid.genus,
                    'species': orchid.species,
                    'latitude': orchid.decimal_latitude,
                    'longitude': orchid.decimal_longitude,
                    'region': orchid.region,
                    'bloom_time': orchid.bloom_time,
                    'growth_habit': orchid.growth_habit,
                    'climate_preference': orchid.climate_preference,
                    'temperature_range': orchid.temperature_range,
                    'created_at': orchid.created_at
                })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"Error retrieving data: {e}")
            return pd.DataFrame()

# Initialize components
scientific_method = ScientificMethod()
data_analyzer = DataAnalyzer()

@scientific_research.route('/scientific-method')
def scientific_method_interface():
    """Main scientific method learning interface"""
    return render_template('research/scientific_method_interface.html', 
                         stages=scientific_method.stages)

@scientific_research.route('/satellite-map')
def enhanced_satellite_map():
    """Enhanced satellite world map"""
    return render_template('mapping/enhanced_satellite_map.html')

@scientific_research.route('/api/analyze-data', methods=['POST'])
def analyze_data():
    """API endpoint for data analysis"""
    try:
        data = data_analyzer.get_orchid_data()
        return jsonify({
            'success': True,
            'data_count': len(data),
            'message': 'Data analysis ready'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})