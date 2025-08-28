#!/usr/bin/env python3
"""
Research Lab Upgrade - Core Implementation
Full Scientific Method Workflow with Statistical Analysis and Paper Generation

This implements the non-negotiable specifications for the Orchid Continuum Research Lab:
1. Complete scientific method pipeline (Observation → Hypothesis → Methods → Data → Analysis → Conclusions → Paper)
2. Statistical testing (Welch's t-test, Mann-Whitney U)
3. IMRaD paper generation
4. Reference management with DOI support
5. Educational guidance and examples
"""

import os
import json
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, send_file
from scipy import stats
from scipy.stats import ttest_ind, mannwhitneyu
import markdown
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import tempfile
from app import db
from models import OrchidRecord

# Create Research Lab blueprint
research_lab = Blueprint('research_lab', __name__, url_prefix='/research-lab')

class ResearchProject:
    """Complete research project management"""
    
    def __init__(self):
        self.stages = [
            'observation', 'hypothesis', 'methods', 'data_collection', 
            'analysis', 'conclusions', 'paper_draft'
        ]
        self.project_data = {}
    
    def save_stage_data(self, stage, data):
        """Save data for a specific research stage"""
        self.project_data[stage] = {
            'data': data,
            'completed_at': datetime.now().isoformat(),
            'stage_id': stage
        }
    
    def get_stage_data(self, stage):
        """Get data for a specific stage"""
        return self.project_data.get(stage, {})
    
    def get_completion_status(self):
        """Check which stages are completed"""
        return {stage: stage in self.project_data for stage in self.stages}

class StatisticalAnalyzer:
    """Statistical analysis tools for orchid research"""
    
    def __init__(self):
        self.supported_tests = {
            'welch_t_test': 'Welch\'s t-test (unequal variances)',
            'mann_whitney_u': 'Mann-Whitney U test (non-parametric)',
            'descriptive_stats': 'Descriptive statistics',
            'correlation': 'Correlation analysis'
        }
    
    def get_orchid_data(self, filters=None):
        """Get orchid data for analysis with comprehensive filtering"""
        try:
            query = db.session.query(OrchidRecord)
            
            # Apply filters
            if filters:
                if filters.get('genus'):
                    query = query.filter(OrchidRecord.genus.ilike(f"%{filters['genus']}%"))
                if filters.get('region'):
                    query = query.filter(OrchidRecord.region.ilike(f"%{filters['region']}%"))
                if filters.get('elevation_min'):
                    query = query.filter(OrchidRecord.elevation_indicators >= filters['elevation_min'])
                if filters.get('elevation_max'):
                    query = query.filter(OrchidRecord.elevation_indicators <= filters['elevation_max'])
                if filters.get('wild_cultivated'):
                    if filters['wild_cultivated'] == 'wild':
                        query = query.filter(OrchidRecord.natural_vs_cultivated.ilike('%wild%'))
                    elif filters['wild_cultivated'] == 'cultivated':
                        query = query.filter(OrchidRecord.natural_vs_cultivated.ilike('%cultivated%'))
                if filters.get('month'):
                    # Filter by bloom season
                    query = query.filter(OrchidRecord.bloom_season_indicator.ilike(f"%{filters['month']}%"))
            
            orchids = query.all()
            
            # Convert to analysis-ready DataFrame
            data = []
            for orchid in orchids:
                try:
                    # Extract numeric values where possible
                    flower_size = None
                    if orchid.flower_size_mm:
                        try:
                            flower_size = float(orchid.flower_size_mm)
                        except:
                            pass
                    
                    elevation = None
                    if orchid.elevation_indicators:
                        try:
                            elevation = float(orchid.elevation_indicators)
                        except:
                            pass
                    
                    data.append({
                        'id': orchid.id,
                        'genus': orchid.genus or 'Unknown',
                        'species': orchid.species or 'unknown',
                        'region': orchid.region or 'Unknown',
                        'latitude': orchid.decimal_latitude,
                        'longitude': orchid.decimal_longitude,
                        'flower_size_mm': flower_size,
                        'flower_count': orchid.flower_count or 0,
                        'elevation': elevation,
                        'growth_habit': orchid.growth_habit or 'Unknown',
                        'natural_vs_cultivated': orchid.natural_vs_cultivated or 'Unknown',
                        'bloom_season': orchid.bloom_season_indicator or 'Unknown',
                        'ai_confidence': orchid.ai_confidence or 0.0,
                        'created_at': orchid.created_at
                    })
                except Exception as e:
                    continue
            
            return pd.DataFrame(data) if data else pd.DataFrame()
            
        except Exception as e:
            print(f"Error in data retrieval: {e}")
            return pd.DataFrame()
    
    def run_welch_t_test(self, data, group_column, value_column, group1, group2):
        """Run Welch's t-test comparing two groups"""
        try:
            group1_data = data[data[group_column] == group1][value_column].dropna()
            group2_data = data[data[group_column] == group2][value_column].dropna()
            
            if len(group1_data) < 2 or len(group2_data) < 2:
                return {'error': 'Insufficient data for t-test (need at least 2 samples per group)'}
            
            # Welch's t-test (assumes unequal variances)
            statistic, p_value = ttest_ind(group1_data, group2_data, equal_var=False)
            
            result = {
                'test': 'Welch\'s t-test',
                'statistic': float(statistic),
                'p_value': float(p_value),
                'group1': {
                    'name': group1,
                    'count': len(group1_data),
                    'mean': float(group1_data.mean()),
                    'std': float(group1_data.std()),
                    'median': float(group1_data.median())
                },
                'group2': {
                    'name': group2,
                    'count': len(group2_data),
                    'mean': float(group2_data.mean()),
                    'std': float(group2_data.std()),
                    'median': float(group2_data.median())
                },
                'significant': p_value < 0.05,
                'effect_size': abs((group1_data.mean() - group2_data.mean()) / 
                                 np.sqrt((group1_data.var() + group2_data.var()) / 2))
            }
            
            # Interpretation
            if p_value < 0.001:
                result['interpretation'] = 'Highly significant difference (p < 0.001)'
            elif p_value < 0.01:
                result['interpretation'] = 'Very significant difference (p < 0.01)'
            elif p_value < 0.05:
                result['interpretation'] = 'Significant difference (p < 0.05)'
            else:
                result['interpretation'] = 'No significant difference (p ≥ 0.05)'
            
            return result
            
        except Exception as e:
            return {'error': f'Statistical analysis failed: {str(e)}'}
    
    def run_mann_whitney_u(self, data, group_column, value_column, group1, group2):
        """Run Mann-Whitney U test (non-parametric)"""
        try:
            group1_data = data[data[group_column] == group1][value_column].dropna()
            group2_data = data[data[group_column] == group2][value_column].dropna()
            
            if len(group1_data) < 2 or len(group2_data) < 2:
                return {'error': 'Insufficient data for Mann-Whitney U test'}
            
            statistic, p_value = mannwhitneyu(group1_data, group2_data, alternative='two-sided')
            
            result = {
                'test': 'Mann-Whitney U test',
                'statistic': float(statistic),
                'p_value': float(p_value),
                'group1': {
                    'name': group1,
                    'count': len(group1_data),
                    'median': float(group1_data.median()),
                    'q1': float(group1_data.quantile(0.25)),
                    'q3': float(group1_data.quantile(0.75))
                },
                'group2': {
                    'name': group2,
                    'count': len(group2_data),
                    'median': float(group2_data.median()),
                    'q1': float(group2_data.quantile(0.25)),
                    'q3': float(group2_data.quantile(0.75))
                },
                'significant': p_value < 0.05
            }
            
            # Interpretation
            if p_value < 0.001:
                result['interpretation'] = 'Highly significant difference (p < 0.001)'
            elif p_value < 0.01:
                result['interpretation'] = 'Very significant difference (p < 0.01)'
            elif p_value < 0.05:
                result['interpretation'] = 'Significant difference (p < 0.05)'
            else:
                result['interpretation'] = 'No significant difference (p ≥ 0.05)'
            
            return result
            
        except Exception as e:
            return {'error': f'Statistical analysis failed: {str(e)}'}

class PaperGenerator:
    """Generate scientific papers in IMRaD format"""
    
    def __init__(self):
        self.template = {
            'title': '',
            'authors': [],
            'affiliations': [],
            'abstract': '',
            'introduction': '',
            'methods': '',
            'results': '',
            'discussion': '',
            'conclusions': '',
            'references': []
        }
    
    def generate_paper(self, project_data, statistical_results, references):
        """Generate complete paper from research data"""
        try:
            paper = self.template.copy()
            
            # Extract data from project
            hypothesis_data = project_data.get('hypothesis', {}).get('data', {})
            methods_data = project_data.get('methods', {}).get('data', {})
            conclusions_data = project_data.get('conclusions', {}).get('data', {})
            
            # Generate each section
            paper['title'] = hypothesis_data.get('research_question', 'Orchid Research Study')
            paper['authors'] = ['Student Researcher']  # Could be customized
            paper['affiliations'] = ['Five Cities Orchid Society Research Lab']
            
            # Abstract (200-300 words)
            paper['abstract'] = self._generate_abstract(hypothesis_data, statistical_results, conclusions_data)
            
            # Introduction
            paper['introduction'] = self._generate_introduction(hypothesis_data)
            
            # Methods
            paper['methods'] = self._generate_methods(methods_data, statistical_results)
            
            # Results
            paper['results'] = self._generate_results(statistical_results)
            
            # Discussion
            paper['discussion'] = self._generate_discussion(statistical_results, conclusions_data)
            
            # Conclusions
            paper['conclusions'] = conclusions_data.get('conclusions', 'Further research is needed.')
            
            # References
            paper['references'] = references
            
            return paper
            
        except Exception as e:
            return {'error': f'Paper generation failed: {str(e)}'}
    
    def _generate_abstract(self, hypothesis_data, results, conclusions_data):
        """Generate abstract section"""
        h0 = hypothesis_data.get('null_hypothesis', 'No difference exists between groups')
        h1 = hypothesis_data.get('alternative_hypothesis', 'A significant difference exists between groups')
        
        if results and 'error' not in results:
            p_value = results.get('p_value', 0.0)
            significant = results.get('significant', False)
            
            return f"""**Objective:** This study tested the hypothesis that {h1.lower()}. 
**Methods:** We analyzed orchid specimens from the Five Cities Orchid Society database using statistical methods including {results.get('test', 'statistical analysis')}. 
**Results:** The analysis included {results.get('group1', {}).get('count', 0) + results.get('group2', {}).get('count', 0)} specimens. The p-value was {p_value:.4f}, {'indicating a significant difference' if significant else 'indicating no significant difference'} between groups. 
**Conclusions:** {'The alternative hypothesis was supported' if significant else 'The null hypothesis was not rejected'}. {conclusions_data.get('conclusions', 'These findings contribute to our understanding of orchid biology.')}"""
        
        return f"""**Objective:** This study investigated {hypothesis_data.get('research_question', 'orchid characteristics')}. **Methods:** Data analysis was performed using the Five Cities Orchid Society research database. **Results:** Statistical analysis was completed on the available specimens. **Conclusions:** Further research is recommended to validate these preliminary findings."""
    
    def _generate_introduction(self, hypothesis_data):
        """Generate introduction section"""
        return f"""Orchids (Orchidaceae) represent one of the largest families of flowering plants, with over 28,000 species distributed across diverse habitats worldwide. Understanding the patterns and relationships within this family is crucial for conservation efforts and botanical research.

**Research Question:** {hypothesis_data.get('research_question', 'What factors influence orchid characteristics?')}

**Background:** Previous studies have shown that orchid characteristics can vary significantly based on environmental factors, geographic location, and evolutionary pressures. This study aims to contribute to the existing body of knowledge by examining specific relationships within our regional orchid collection.

**Hypotheses:**
- **Null Hypothesis (H₀):** {hypothesis_data.get('null_hypothesis', 'No significant difference exists between the compared groups')}
- **Alternative Hypothesis (H₁):** {hypothesis_data.get('alternative_hypothesis', 'A significant difference exists between the compared groups')}"""
    
    def _generate_methods(self, methods_data, results):
        """Generate methods section"""
        return f"""**Data Source:** Orchid specimens were analyzed from the Five Cities Orchid Society database, which contains detailed morphological and ecological data collected from various sources including field observations, herbarium specimens, and cultivated collections.

**Sample Selection:** {methods_data.get('sample_selection', 'Specimens were selected based on data completeness and quality criteria.')}

**Variables Measured:** {', '.join(methods_data.get('variables', ['morphological characteristics', 'ecological factors']))}

**Statistical Analysis:** Data analysis was performed using {results.get('test', 'appropriate statistical methods')}. {'Welch\'s t-test was used for comparing means between groups, accounting for potential differences in variance' if results.get('test') == 'Welch\'s t-test' else ''}{'Mann-Whitney U test was used as a non-parametric alternative for comparing group distributions' if results.get('test') == 'Mann-Whitney U test' else ''}. Statistical significance was set at α = 0.05.

**Data Processing:** All statistical analyses were conducted using standardized procedures to ensure reproducibility and accuracy."""
    
    def _generate_results(self, results):
        """Generate results section"""
        if not results or 'error' in results:
            return "Statistical analysis was completed on the available data. Detailed results are presented in the following sections."
        
        test_name = results.get('test', 'Statistical test')
        group1 = results.get('group1', {})
        group2 = results.get('group2', {})
        
        results_text = f"""**{test_name} Results:**

The analysis included {group1.get('count', 0)} specimens in the {group1.get('name', 'first')} group and {group2.get('count', 0)} specimens in the {group2.get('name', 'second')} group.

**Group Statistics:**
- **{group1.get('name', 'Group 1')}:** Mean = {group1.get('mean', group1.get('median', 'N/A')):.3f}, SD = {group1.get('std', 'N/A')}
- **{group2.get('name', 'Group 2')}:** Mean = {group2.get('mean', group2.get('median', 'N/A')):.3f}, SD = {group2.get('std', 'N/A')}

**Test Statistics:**
- Test statistic = {results.get('statistic', 0.0):.4f}
- p-value = {results.get('p_value', 0.0):.6f}
- Effect size = {results.get('effect_size', 'N/A')}

**Statistical Significance:** {results.get('interpretation', 'Results require further interpretation.')}"""

        return results_text
    
    def _generate_discussion(self, results, conclusions_data):
        """Generate discussion section"""
        if not results or 'error' in results:
            return "The results of this study provide insights into orchid characteristics and their relationships. Further research with larger sample sizes would strengthen these findings."
        
        significant = results.get('significant', False)
        
        discussion = f"""**Interpretation of Results:** {results.get('interpretation', 'The statistical analysis provides insights into the research question.')}

**Biological Significance:** {'The significant difference observed between groups suggests that the measured characteristics are influenced by the grouping variable' if significant else 'The lack of significant difference may indicate that the grouping variable does not strongly influence the measured characteristics, or that additional factors need to be considered'}. This has implications for understanding orchid ecology and evolution.

**Limitations:** This study was conducted using available specimens from the Five Cities Orchid Society database. Sample sizes, geographic representation, and data collection methods may influence the generalizability of results. Future studies should consider: (1) larger sample sizes, (2) standardized measurement protocols, and (3) broader geographic sampling.

**Future Directions:** {conclusions_data.get('future_research', 'Additional research should explore related variables and expand the sample size to validate these findings.')}"""

        return discussion
    
    def export_to_markdown(self, paper):
        """Export paper to Markdown format"""
        try:
            md_content = f"""# {paper['title']}

**Authors:** {', '.join(paper['authors'])}  
**Affiliations:** {', '.join(paper['affiliations'])}  
**Date:** {datetime.now().strftime('%B %d, %Y')}

## Abstract

{paper['abstract']}

## Introduction

{paper['introduction']}

## Methods

{paper['methods']}

## Results

{paper['results']}

## Discussion

{paper['discussion']}

## Conclusions

{paper['conclusions']}

## References

{self._format_references(paper['references'])}

---

*Generated by Five Cities Orchid Society Research Lab*  
*Data sources: Orchid Continuum Database, Gary Yong Gee Collection, GBIF*
"""
            return md_content
            
        except Exception as e:
            return f"Error generating markdown: {str(e)}"
    
    def export_to_pdf(self, paper):
        """Export paper to PDF format using ReportLab"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(temp_file.name, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            # Title
            story.append(Paragraph(paper['title'], styles['Title']))
            story.append(Spacer(1, 12))
            
            # Authors and affiliations
            if paper['authors']:
                story.append(Paragraph(f"<b>Authors:</b> {', '.join(paper['authors'])}", styles['Normal']))
            if paper['affiliations']:
                story.append(Paragraph(f"<b>Affiliations:</b> {', '.join(paper['affiliations'])}", styles['Normal']))
            story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", styles['Normal']))
            story.append(Spacer(1, 12))
            
            # Sections
            sections = [
                ('Abstract', paper['abstract']),
                ('Introduction', paper['introduction']),
                ('Methods', paper['methods']),
                ('Results', paper['results']),
                ('Discussion', paper['discussion']),
                ('Conclusions', paper['conclusions'])
            ]
            
            for title, content in sections:
                if content:
                    story.append(Paragraph(title, styles['Heading2']))
                    story.append(Spacer(1, 6))
                    # Clean content of markdown
                    clean_content = content.replace('**', '').replace('*', '')
                    story.append(Paragraph(clean_content, styles['Normal']))
                    story.append(Spacer(1, 12))
            
            # References
            if paper['references']:
                story.append(Paragraph('References', styles['Heading2']))
                story.append(Spacer(1, 6))
                story.append(Paragraph(self._format_references(paper['references']), styles['Normal']))
            
            # Build PDF
            doc.build(story)
            
            return temp_file.name
            
        except Exception as e:
            return None
    
    def _format_references(self, references):
        """Format references in APA style"""
        if not references:
            return "No references added."
        
        formatted = []
        for i, ref in enumerate(references, 1):
            if isinstance(ref, dict):
                # Format based on reference type
                if ref.get('type') == 'journal':
                    formatted.append(f"{i}. {ref.get('authors', 'Unknown')} ({ref.get('year', 'n.d.')}). {ref.get('title', 'Untitled')}. *{ref.get('journal', 'Unknown Journal')}*, {ref.get('volume', '')}({ref.get('issue', '')}), {ref.get('pages', '')}. DOI: {ref.get('doi', 'Not available')}")
                else:
                    formatted.append(f"{i}. {ref.get('authors', 'Unknown')} ({ref.get('year', 'n.d.')}). {ref.get('title', 'Untitled')}.")
            else:
                formatted.append(f"{i}. {str(ref)}")
        
        return '\n'.join(formatted)

class ReferenceManager:
    """Manage research references with DOI support"""
    
    def __init__(self):
        self.references = []
        self.crossref_api = "https://api.crossref.org/works/"
    
    def add_doi_reference(self, doi):
        """Add reference by DOI using CrossRef API"""
        try:
            response = requests.get(f"{self.crossref_api}{doi}")
            if response.status_code == 200:
                data = response.json()
                work = data['message']
                
                # Extract key information
                reference = {
                    'doi': doi,
                    'type': 'journal',
                    'title': work.get('title', ['Unknown'])[0],
                    'authors': self._format_authors(work.get('author', [])),
                    'journal': work.get('container-title', ['Unknown'])[0] if work.get('container-title') else 'Unknown',
                    'year': str(work.get('published-print', work.get('published-online', {})).get('date-parts', [[None]])[0][0] or 'n.d.'),
                    'volume': work.get('volume', ''),
                    'issue': work.get('issue', ''),
                    'pages': work.get('page', ''),
                    'url': work.get('URL', ''),
                    'added_date': datetime.now().isoformat()
                }
                
                self.references.append(reference)
                return reference
            else:
                return {'error': f'DOI not found or API error: {response.status_code}'}
                
        except Exception as e:
            return {'error': f'Failed to fetch DOI: {str(e)}'}
    
    def add_manual_reference(self, reference_data):
        """Add reference manually"""
        reference = {
            'type': reference_data.get('type', 'misc'),
            'title': reference_data.get('title', ''),
            'authors': reference_data.get('authors', ''),
            'journal': reference_data.get('journal', ''),
            'year': reference_data.get('year', ''),
            'volume': reference_data.get('volume', ''),
            'issue': reference_data.get('issue', ''),
            'pages': reference_data.get('pages', ''),
            'publisher': reference_data.get('publisher', ''),
            'url': reference_data.get('url', ''),
            'added_date': datetime.now().isoformat()
        }
        
        self.references.append(reference)
        return reference
    
    def export_bibtex(self):
        """Export references as BibTeX"""
        bibtex_entries = []
        
        for i, ref in enumerate(self.references, 1):
            if ref.get('type') == 'journal':
                entry = f"""@article{{ref{i},
    author = {{{ref.get('authors', 'Unknown')}}},
    title = {{{ref.get('title', 'Untitled')}}},
    journal = {{{ref.get('journal', 'Unknown')}}},
    year = {{{ref.get('year', 'n.d.')}}},
    volume = {{{ref.get('volume', '')}}},
    number = {{{ref.get('issue', '')}}},
    pages = {{{ref.get('pages', '')}}},
    doi = {{{ref.get('doi', '')}}}
}}"""
            else:
                entry = f"""@misc{{ref{i},
    author = {{{ref.get('authors', 'Unknown')}}},
    title = {{{ref.get('title', 'Untitled')}}},
    year = {{{ref.get('year', 'n.d.')}}},
    note = {{{ref.get('note', '')}}}
}}"""
            
            bibtex_entries.append(entry)
        
        return '\n\n'.join(bibtex_entries)
    
    def _format_authors(self, authors_list):
        """Format authors from CrossRef data"""
        if not authors_list:
            return 'Unknown'
        
        formatted_authors = []
        for author in authors_list[:3]:  # Limit to first 3 authors
            given = author.get('given', '')
            family = author.get('family', '')
            if family:
                formatted_authors.append(f"{family}, {given}")
        
        if len(authors_list) > 3:
            formatted_authors.append('et al.')
        
        return '; '.join(formatted_authors)

# Initialize components
research_project = ResearchProject()
statistical_analyzer = StatisticalAnalyzer()
paper_generator = PaperGenerator()
reference_manager = ReferenceManager()

# Core routes
@research_lab.route('/')
def dashboard():
    """Research Lab main dashboard"""
    return render_template('research/research_lab_dashboard.html')

@research_lab.route('/stage/<stage_id>')
def research_stage(stage_id):
    """Individual research stage interface"""
    valid_stages = ['observation', 'hypothesis', 'methods', 'data_collection', 'analysis', 'conclusions', 'paper_draft']
    
    if stage_id not in valid_stages:
        return redirect(url_for('research_lab.dashboard'))
    
    return render_template(f'research/stages/{stage_id}.html', stage_id=stage_id)

@research_lab.route('/api/statistical-analysis', methods=['POST'])
def run_statistical_analysis():
    """API endpoint for running statistical tests"""
    try:
        data = request.json
        test_type = data.get('test_type')
        filters = data.get('filters', {})
        group_column = data.get('group_column')
        value_column = data.get('value_column')
        group1 = data.get('group1')
        group2 = data.get('group2')
        
        # Get filtered orchid data
        orchid_data = statistical_analyzer.get_orchid_data(filters)
        
        if orchid_data.empty:
            return jsonify({
                'success': False,
                'error': 'No data found with the specified filters'
            })
        
        # Run appropriate statistical test
        if test_type == 'welch_t_test':
            result = statistical_analyzer.run_welch_t_test(orchid_data, group_column, value_column, group1, group2)
        elif test_type == 'mann_whitney_u':
            result = statistical_analyzer.run_mann_whitney_u(orchid_data, group_column, value_column, group1, group2)
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported statistical test type'
            })
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            })
        
        return jsonify({
            'success': True,
            'result': result,
            'data_summary': {
                'total_records': len(orchid_data),
                'columns': list(orchid_data.columns)
            }
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Statistical analysis failed: {str(e)}'
        })

@research_lab.route('/api/generate-paper', methods=['POST'])
def generate_research_paper():
    """Generate scientific paper from research data"""
    try:
        data = request.json
        project_data = data.get('project_data', {})
        statistical_results = data.get('statistical_results', {})
        references = data.get('references', [])
        export_format = data.get('format', 'markdown')  # 'markdown' or 'pdf'
        
        # Generate paper
        paper = paper_generator.generate_paper(project_data, statistical_results, references)
        
        if 'error' in paper:
            return jsonify({
                'success': False,
                'error': paper['error']
            })
        
        if export_format == 'pdf':
            pdf_path = paper_generator.export_to_pdf(paper)
            if pdf_path:
                return send_file(pdf_path, as_attachment=True, download_name=f"research_paper_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            else:
                return jsonify({
                    'success': False,
                    'error': 'PDF generation failed'
                })
        else:
            # Return markdown
            markdown_content = paper_generator.export_to_markdown(paper)
            return jsonify({
                'success': True,
                'paper': paper,
                'markdown': markdown_content
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Paper generation failed: {str(e)}'
        })

@research_lab.route('/api/add-reference', methods=['POST'])
def add_reference():
    """Add reference via DOI or manual entry"""
    try:
        data = request.json
        reference_type = data.get('type')  # 'doi' or 'manual'
        
        if reference_type == 'doi':
            doi = data.get('doi')
            result = reference_manager.add_doi_reference(doi)
        elif reference_type == 'manual':
            result = reference_manager.add_manual_reference(data.get('reference_data', {}))
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid reference type'
            })
        
        if 'error' in result:
            return jsonify({
                'success': False,
                'error': result['error']
            })
        
        return jsonify({
            'success': True,
            'reference': result,
            'total_references': len(reference_manager.references)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Failed to add reference: {str(e)}'
        })

@research_lab.route('/api/export-references/<format>')
def export_references(format):
    """Export references in various formats"""
    try:
        if format == 'bibtex':
            bibtex_content = reference_manager.export_bibtex()
            
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.bib')
            temp_file.write(bibtex_content)
            temp_file.close()
            
            return send_file(temp_file.name, as_attachment=True, download_name=f"references_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bib")
        else:
            return jsonify({
                'success': False,
                'error': 'Unsupported export format'
            })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Export failed: {str(e)}'
        })

@research_lab.route('/api/example-projects')
def get_example_projects():
    """Get available example research projects"""
    return jsonify({
        'success': True,
        'projects': EXAMPLE_PROJECTS
    })

@research_lab.route('/api/orchid-data')
def get_orchid_data_api():
    """API endpoint to get orchid data with filters"""
    try:
        filters = request.args.to_dict()
        
        # Convert numeric filters
        for key in ['latitude_min', 'latitude_max', 'elevation_min', 'elevation_max']:
            if key in filters and filters[key]:
                try:
                    filters[key] = float(filters[key])
                except ValueError:
                    del filters[key]
        
        data = statistical_analyzer.get_orchid_data(filters)
        
        return jsonify({
            'success': True,
            'data_count': len(data),
            'columns': list(data.columns) if not data.empty else [],
            'sample_data': data.head().to_dict('records') if not data.empty else [],
            'filters_applied': filters
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Data retrieval failed: {str(e)}'
        })

# Flask imports are already at the top of the file

# Example research projects for educational guidance
EXAMPLE_PROJECTS = {
    'cymbidium_35n': {
        'title': 'Cymbidium Flowering Patterns at 35°N Latitude',
        'research_question': 'How does geographic location along the 35th parallel affect Cymbidium orchid flowering time?',
        'null_hypothesis': 'There is no significant difference in flowering time for Cymbidium orchids across different regions at 35°N latitude',
        'alternative_hypothesis': 'Cymbidium orchids show significantly different flowering times based on their geographic location along the 35th parallel',
        'variables': ['latitude', 'longitude', 'flowering_time', 'climate_zone', 'elevation'],
        'filters': {'genus': 'Cymbidium', 'latitude_min': 34.5, 'latitude_max': 35.5},
        'suggested_analysis': 'mann_whitney_u',
        'description': 'Compare Cymbidium flowering patterns across different regions at similar latitudes to test climate influence hypotheses.'
    },
    'epiphyte_terrestrial': {
        'title': 'Morphological Differences: Epiphytic vs Terrestrial Orchids',
        'research_question': 'Do epiphytic orchids have significantly different morphological characteristics compared to terrestrial orchids?',
        'null_hypothesis': 'There is no significant difference in flower size between epiphytic and terrestrial orchids',
        'alternative_hypothesis': 'Epiphytic orchids have significantly different flower sizes compared to terrestrial orchids',
        'variables': ['growth_habit', 'flower_size_mm', 'flower_count', 'root_type'],
        'filters': {},
        'suggested_analysis': 'welch_t_test',
        'description': 'Analyze morphological adaptations between different orchid growth strategies.'
    },
    'biodiversity_hotspots': {
        'title': 'Orchid Species Diversity Across Geographic Regions',
        'research_question': 'Which geographic regions exhibit the highest orchid species diversity?',
        'null_hypothesis': 'There is no significant difference in orchid species count between tropical and temperate regions',
        'alternative_hypothesis': 'Tropical regions contain significantly more orchid species than temperate regions',
        'variables': ['region', 'species_count', 'climate_type', 'latitude', 'elevation'],
        'filters': {},
        'suggested_analysis': 'mann_whitney_u',
        'description': 'Investigate global patterns of orchid biodiversity and conservation priorities.'
    }
}