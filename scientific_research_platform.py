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
from literature_search_system import literature_engine

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

@scientific_research.route('/research-wizard')
def research_wizard():
    """Interactive research wizard with integrated literature search"""
    return render_template('research/research_wizard.html')

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

@scientific_research.route('/api/literature-search', methods=['POST'])
def literature_search():
    """Integrated literature search for research workflow"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        # Validate and cap max_results
        try:
            max_results = int(data.get('max_results', 20))
            max_results = max(1, min(max_results, 50))  # Cap between 1-50
        except (ValueError, TypeError):
            max_results = 20
            
        stage = data.get('stage', 'general')  # Stage of scientific method
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        # Enhance query based on stage
        if stage == 'hypothesis':
            enhanced_query = f'{query} research background literature review'
        elif stage == 'communicate':
            enhanced_query = f'{query} recent findings publications citations'
        else:
            enhanced_query = query
        
        # Perform search
        results = literature_engine.search_all_databases(enhanced_query, max_results)
        
        # Convert to JSON-serializable format
        papers_data = []
        for paper in results.papers:
            papers_data.append({
                'title': paper.title,
                'authors': paper.authors,
                'journal': paper.journal,
                'publication_date': paper.publication_date,
                'doi': paper.doi,
                'abstract': paper.abstract,
                'citation_count': paper.citation_count,
                'source': paper.source,
                'url': paper.url,
                'keywords': paper.keywords,
                'relevance_score': paper.relevance_score
            })
        
        return jsonify({
            'success': True,
            'results': {
                'query': results.query,
                'total_results': results.total_results,
                'papers': papers_data,
                'search_sources': results.search_sources,
                'timestamp': results.timestamp.isoformat(),
                'stage': stage
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@scientific_research.route('/api/orchid-literature-search', methods=['POST'])
def orchid_literature_search():
    """Search literature for specific orchid genus/species"""
    try:
        data = request.get_json()
        genus = data.get('genus', '').strip()
        species = data.get('species', '').strip()
        
        # Perform orchid-specific search
        results = literature_engine.search_orchid_research(genus, species)
        
        # Convert to JSON format
        papers_data = []
        for paper in results.papers:
            papers_data.append({
                'title': paper.title,
                'authors': paper.authors,
                'journal': paper.journal,
                'publication_date': paper.publication_date,
                'doi': paper.doi,
                'abstract': paper.abstract,
                'citation_count': paper.citation_count,
                'source': paper.source,
                'url': paper.url,
                'keywords': paper.keywords,
                'relevance_score': paper.relevance_score
            })
        
        return jsonify({
            'success': True,
            'results': {
                'query': results.query,
                'total_results': results.total_results,
                'papers': papers_data,
                'search_sources': results.search_sources,
                'timestamp': results.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@scientific_research.route('/api/generate-citation', methods=['POST'])
def generate_citation():
    """Generate citation for a paper"""
    try:
        data = request.get_json()
        paper = data.get('paper')
        format_style = data.get('format', 'apa')
        
        if not paper:
            return jsonify({'success': False, 'error': 'Paper data required'}), 400
        
        # Generate citation based on format
        if format_style == 'apa':
            citation = format_apa_citation(paper)
        elif format_style == 'mla':
            citation = format_mla_citation(paper)
        elif format_style == 'bibtex':
            citation = format_bibtex_citation(paper)
        else:
            citation = format_apa_citation(paper)  # Default to APA
        
        return jsonify({
            'success': True,
            'citation': citation,
            'format': format_style
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def format_apa_citation(paper):
    """Format citation in APA style"""
    try:
        authors = paper.get('authors', [])
        if isinstance(authors, list) and authors:
            author_text = authors[0]
            if len(authors) > 1:
                author_text += " et al."
        else:
            author_text = "Unknown Author"
        
        year = paper.get('publication_date', 'n.d.')[:4] if paper.get('publication_date') else 'n.d.'
        title = paper.get('title', 'Unknown Title')
        journal = paper.get('journal', 'Unknown Journal')
        doi = paper.get('doi', '')
        
        citation = f"{author_text} ({year}). {title}. *{journal}*."
        if doi:
            citation += f" https://doi.org/{doi}"
        
        return citation
    except:
        return "Citation formatting error"

def format_mla_citation(paper):
    """Format citation in MLA style"""
    try:
        authors = paper.get('authors', [])
        if isinstance(authors, list) and authors:
            author_text = authors[0]
        else:
            author_text = "Unknown Author"
        
        title = paper.get('title', 'Unknown Title')
        journal = paper.get('journal', 'Unknown Journal')
        year = paper.get('publication_date', 'n.d.')[:4] if paper.get('publication_date') else 'n.d.'
        
        citation = f'{author_text}. "{title}." *{journal}*, {year}.'
        return citation
    except:
        return "Citation formatting error"

def format_bibtex_citation(paper):
    """Format citation in BibTeX style"""
    try:
        authors = paper.get('authors', [])
        author_text = ' and '.join(authors) if isinstance(authors, list) else str(authors)
        
        title = paper.get('title', 'Unknown Title')
        journal = paper.get('journal', 'Unknown Journal')
        year = paper.get('publication_date', 'unknown')[:4] if paper.get('publication_date') else 'unknown'
        doi = paper.get('doi', '')
        
        # Create a simple key from first author and year
        key = f"{author_text.split()[0].lower()}{year}" if author_text != 'Unknown Author' else f"unknown{year}"
        
        bibtex = f"""@article{{{key},
    title={{{title}}},
    author={{{author_text}}},
    journal={{{journal}}},
    year={{{year}}}"""
        
        if doi:
            bibtex += f",\n    doi={{{doi}}}"
        
        bibtex += "\n}"
        return bibtex
    except:
        return "Citation formatting error"