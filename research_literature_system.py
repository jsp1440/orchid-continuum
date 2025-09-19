#!/usr/bin/env python3
"""
Literature Review and Citation Management System
Part of the Five Cities Orchid Society Research Lab
"""

import os
import json
import re
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
import requests
from typing import Dict, List, Any, Optional
import openai

research_literature = Blueprint('research_literature', __name__)

class LiteratureReviewSystem:
    """Comprehensive literature review and citation management"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        # Academic databases and resources
        self.databases = {
            'crossref': 'https://api.crossref.org/works',
            'arxiv': 'https://export.arxiv.org/api/query',
            'pubmed': 'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi',
            'google_scholar': 'https://scholar.google.com/scholar',  # For reference only
            'orchid_sources': {
                'aos': 'https://www.aos.org/',
                'orchidwiz': 'https://www.orchidwiz.com/',
                'kew': 'https://www.kew.org/',
                'missouri': 'https://www.missouribotanicalgarden.org/'
            }
        }
        
        # Citation formats
        self.citation_formats = {
            'apa': 'APA Style (7th Edition)',
            'mla': 'MLA Style (9th Edition)', 
            'chicago': 'Chicago Style (17th Edition)',
            'harvard': 'Harvard Style',
            'vancouver': 'Vancouver Style',
            'bibtex': 'BibTeX Format'
        }

    def search_literature(self, query: str, database: str = 'crossref', limit: int = 20) -> Dict:
        """Search academic literature across multiple databases"""
        try:
            if database == 'crossref':
                return self._search_crossref(query, limit)
            elif database == 'arxiv':
                return self._search_arxiv(query, limit)
            elif database == 'pubmed':
                return self._search_pubmed(query, limit)
            else:
                return {'error': f'Database {database} not supported'}
                
        except Exception as e:
            return {'error': f'Literature search failed: {str(e)}'}

    def _search_crossref(self, query: str, limit: int) -> Dict:
        """Search CrossRef database for academic papers"""
        try:
            params = {
                'query': f'{query} orchid',
                'rows': limit,
                'sort': 'relevance'
            }
            
            response = requests.get(self.databases['crossref'], params=params, timeout=10)
            data = response.json()
            
            papers = []
            if 'message' in data and 'items' in data['message']:
                for item in data['message']['items']:
                    paper = {
                        'title': item.get('title', ['Unknown Title'])[0] if item.get('title') else 'Unknown Title',
                        'authors': [f"{author.get('given', '')} {author.get('family', '')}" 
                                  for author in item.get('author', [])],
                        'journal': item.get('container-title', ['Unknown Journal'])[0] if item.get('container-title') else 'Unknown Journal',
                        'year': item.get('published-print', {}).get('date-parts', [[None]])[0][0] or 
                               item.get('published-online', {}).get('date-parts', [[None]])[0][0],
                        'doi': item.get('DOI', ''),
                        'url': item.get('URL', ''),
                        'abstract': item.get('abstract', 'No abstract available'),
                        'source': 'CrossRef',
                        'citation_count': item.get('is-referenced-by-count', 0),
                        'relevance_score': self._calculate_orchid_relevance(item.get('title', [''])[0], item.get('abstract', ''))
                    }
                    papers.append(paper)
            
            return {
                'papers': papers,
                'total_found': data.get('message', {}).get('total-results', 0),
                'database': 'CrossRef',
                'query': query
            }
            
        except Exception as e:
            return {'error': f'CrossRef search failed: {str(e)}'}

    def _search_arxiv(self, query: str, limit: int) -> Dict:
        """Search arXiv database for preprints"""
        try:
            params = {
                'search_query': f'all:{query} AND (bio OR plant OR orchid)',
                'start': 0,
                'max_results': limit,
                'sortBy': 'relevance'
            }
            
            response = requests.get(self.databases['arxiv'], params=params, timeout=10)
            
            papers = []
            if response.status_code == 200:
                # Parse XML response (simplified)
                content = response.text
                # Basic XML parsing for demonstration
                papers.append({
                    'title': 'arXiv Integration Coming Soon',
                    'authors': ['System'],
                    'journal': 'arXiv',
                    'year': 2025,
                    'abstract': 'Full arXiv integration will be available in the next update.',
                    'source': 'arXiv',
                    'url': 'https://arxiv.org'
                })
            
            return {
                'papers': papers,
                'total_found': len(papers),
                'database': 'arXiv',
                'query': query
            }
            
        except Exception as e:
            return {'error': f'arXiv search failed: {str(e)}'}

    def _search_pubmed(self, query: str, limit: int) -> Dict:
        """Search PubMed database for medical/biological papers"""
        try:
            # PubMed integration would require more complex implementation
            papers = [{
                'title': 'PubMed Integration Coming Soon',
                'authors': ['System'],
                'journal': 'PubMed',
                'year': 2025,
                'abstract': 'Full PubMed integration will be available in the next update.',
                'source': 'PubMed',
                'url': 'https://pubmed.ncbi.nlm.nih.gov'
            }]
            
            return {
                'papers': papers,
                'total_found': len(papers),
                'database': 'PubMed',
                'query': query
            }
            
        except Exception as e:
            return {'error': f'PubMed search failed: {str(e)}'}

    def _calculate_orchid_relevance(self, title: str, abstract: str) -> float:
        """Calculate relevance score for orchid research"""
        orchid_terms = [
            'orchid', 'orchidaceae', 'phalaenopsis', 'dendrobium', 'cattleya',
            'cymbidium', 'oncidium', 'paphiopedilum', 'vanda', 'epidendrum',
            'mycorrhiza', 'pollination', 'epiphyte', 'botanical', 'taxonomy',
            'biodiversity', 'conservation', 'horticulture', 'cultivation'
        ]
        
        text = f"{title} {abstract}".lower()
        matches = sum(1 for term in orchid_terms if term in text)
        return min(matches / len(orchid_terms), 1.0)

    def generate_citation(self, paper: Dict, format_type: str = 'apa') -> str:
        """Generate citation in specified format"""
        try:
            if format_type == 'apa':
                return self._generate_apa_citation(paper)
            elif format_type == 'mla':
                return self._generate_mla_citation(paper)
            elif format_type == 'chicago':
                return self._generate_chicago_citation(paper)
            elif format_type == 'bibtex':
                return self._generate_bibtex_citation(paper)
            else:
                return self._generate_apa_citation(paper)
                
        except Exception as e:
            return f"Citation generation error: {str(e)}"

    def _generate_apa_citation(self, paper: Dict) -> str:
        """Generate APA format citation"""
        authors = paper.get('authors', ['Unknown Author'])
        if len(authors) > 6:
            author_str = f"{authors[0]}, et al."
        elif len(authors) > 1:
            author_str = ", ".join(authors[:-1]) + f", & {authors[-1]}"
        else:
            author_str = authors[0]
            
        year = paper.get('year', 'n.d.')
        title = paper.get('title', 'Unknown title')
        journal = paper.get('journal', 'Unknown journal')
        doi = paper.get('doi', '')
        
        citation = f"{author_str} ({year}). {title}. *{journal}*"
        if doi:
            citation += f". https://doi.org/{doi}"
            
        return citation

    def _generate_mla_citation(self, paper: Dict) -> str:
        """Generate MLA format citation"""
        authors = paper.get('authors', ['Unknown Author'])
        author_str = authors[0] if authors else 'Unknown Author'
        if len(authors) > 1:
            author_str += ", et al."
            
        title = paper.get('title', 'Unknown title')
        journal = paper.get('journal', 'Unknown journal')
        year = paper.get('year', 'n.d.')
        
        return f'{author_str} "{title}." *{journal}*, {year}.'

    def _generate_chicago_citation(self, paper: Dict) -> str:
        """Generate Chicago format citation"""
        authors = paper.get('authors', ['Unknown Author'])
        author_str = authors[0] if authors else 'Unknown Author'
        
        title = paper.get('title', 'Unknown title')
        journal = paper.get('journal', 'Unknown journal')
        year = paper.get('year', 'n.d.')
        
        return f'{author_str}. "{title}." *{journal}* ({year}).'

    def _generate_bibtex_citation(self, paper: Dict) -> str:
        """Generate BibTeX format citation"""
        key = re.sub(r'[^a-zA-Z0-9]', '', paper.get('title', 'unknown'))[:20]
        authors = ' and '.join(paper.get('authors', ['Unknown Author']))
        
        return f"""@article{{{key},
    title={{{paper.get('title', 'Unknown title')}}},
    author={{{authors}}},
    journal={{{paper.get('journal', 'Unknown journal')}}},
    year={{{paper.get('year', 'n.d.')}}},
    doi={{{paper.get('doi', '')}}},
    url={{{paper.get('url', '')}}}
}}"""

    def analyze_paper_content(self, content: str, research_question: str = '') -> Dict:
        """Use AI to analyze paper content for research relevance"""
        try:
            prompt = f"""
            Analyze this academic paper content for orchid research relevance.
            Research Question: {research_question}
            
            Paper Content: {content[:3000]}...
            
            Provide analysis in JSON format:
            {{
                "relevance_score": 0-10,
                "key_findings": ["finding1", "finding2"],
                "methodology": "brief description",
                "orchid_species_mentioned": ["species1", "species2"],
                "research_implications": "how this relates to orchid research",
                "recommended_sections": ["section1", "section2"],
                "citation_importance": "why this paper should be cited"
            }}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert orchid researcher and academic analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return {'error': f'Paper analysis failed: {str(e)}'}

    def suggest_search_terms(self, research_topic: str) -> List[str]:
        """AI-powered search term suggestions"""
        try:
            prompt = f"""
            Generate comprehensive search terms for orchid research on: {research_topic}
            
            Include:
            1. Scientific terminology
            2. Common names
            3. Related concepts
            4. Methodology terms
            5. Geographic regions if relevant
            
            Return as JSON array of strings, max 15 terms.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert in orchid research and academic literature search."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=400,
                temperature=0.7
            )
            
            return json.loads(response.choices[0].message.content)
            
        except Exception as e:
            return [research_topic, "orchid", "orchidaceae"]

# Initialize the literature system
lit_system = LiteratureReviewSystem()

@research_literature.route('/literature-review')
def literature_review_dashboard():
    """Literature review dashboard"""
    return render_template('research/literature_review.html')

@research_literature.route('/api/literature/search', methods=['POST'])
def api_literature_search():
    """API endpoint for literature search"""
    data = request.get_json()
    query = data.get('query', '')
    database = data.get('database', 'crossref')
    limit = data.get('limit', 20)
    
    results = lit_system.search_literature(query, database, limit)
    return jsonify(results)

@research_literature.route('/api/literature/citation', methods=['POST'])
def api_generate_citation():
    """API endpoint for citation generation"""
    data = request.get_json()
    paper = data.get('paper', {})
    format_type = data.get('format', 'apa')
    
    citation = lit_system.generate_citation(paper, format_type)
    return jsonify({'citation': citation, 'format': format_type})

@research_literature.route('/api/literature/analyze', methods=['POST'])
def api_analyze_paper():
    """API endpoint for paper analysis"""
    data = request.get_json()
    content = data.get('content', '')
    research_question = data.get('research_question', '')
    
    analysis = lit_system.analyze_paper_content(content, research_question)
    return jsonify(analysis)

@research_literature.route('/api/literature/suggest-terms', methods=['POST'])
def api_suggest_search_terms():
    """API endpoint for search term suggestions"""
    data = request.get_json()
    topic = data.get('topic', '')
    
    terms = lit_system.suggest_search_terms(topic)
    return jsonify({'suggested_terms': terms})

@research_literature.route('/literature-tools')
def literature_tools():
    """Literature management tools page"""
    return render_template('research/literature_tools.html', 
                         citation_formats=lit_system.citation_formats)