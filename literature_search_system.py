"""
Integrated Scientific Literature Search System
Searches multiple academic databases for orchid and climate research
"""

import os
import json
import logging
import requests
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import Blueprint, render_template, request, jsonify
import xml.etree.ElementTree as ET
from urllib.parse import quote

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

literature_bp = Blueprint('literature', __name__, url_prefix='/literature')

@dataclass
class ResearchPaper:
    """Scientific research paper"""
    title: str
    authors: List[str]
    journal: str
    publication_date: str
    doi: Optional[str]
    abstract: str
    citation_count: int
    source: str  # 'crossref', 'pubmed', 'semantic_scholar'
    url: Optional[str]
    keywords: List[str]
    relevance_score: float

@dataclass
class LiteratureSearchResult:
    """Literature search results"""
    query: str
    total_results: int
    papers: List[ResearchPaper]
    search_sources: List[str]
    timestamp: datetime

class LiteratureSearchEngine:
    """
    Multi-database literature search engine for scientific research
    """
    
    def __init__(self):
        # API endpoints
        self.crossref_base = "https://api.crossref.org/works"
        self.pubmed_base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.semantic_scholar_base = "https://api.semanticscholar.org/graph/v1"
        
        # Rate limiting
        self.last_request_times = {}
        
        logger.info("📚 Literature Search Engine initialized")

    def search_all_databases(self, query: str, max_results: int = 50) -> LiteratureSearchResult:
        """
        Search all available databases for literature
        """
        try:
            all_papers = []
            search_sources = []
            
            # Search CrossRef
            try:
                crossref_papers = self.search_crossref(query, max_results // 3)
                all_papers.extend(crossref_papers)
                search_sources.append('CrossRef')
                logger.info(f"📖 Found {len(crossref_papers)} papers from CrossRef")
            except Exception as e:
                logger.warning(f"CrossRef search failed: {str(e)}")
            
            # Search PubMed
            try:
                pubmed_papers = self.search_pubmed(query, max_results // 3)
                all_papers.extend(pubmed_papers)
                search_sources.append('PubMed')
                logger.info(f"🔬 Found {len(pubmed_papers)} papers from PubMed")
            except Exception as e:
                logger.warning(f"PubMed search failed: {str(e)}")
            
            # Search Semantic Scholar
            try:
                semantic_papers = self.search_semantic_scholar(query, max_results // 3)
                all_papers.extend(semantic_papers)
                search_sources.append('Semantic Scholar')
                logger.info(f"🧠 Found {len(semantic_papers)} papers from Semantic Scholar")
            except Exception as e:
                logger.warning(f"Semantic Scholar search failed: {str(e)}")
            
            # Remove duplicates based on DOI and title similarity
            unique_papers = self.deduplicate_papers(all_papers)
            
            # Sort by relevance and recency
            unique_papers.sort(key=lambda p: (p.relevance_score, p.publication_date), reverse=True)
            
            # Limit results
            unique_papers = unique_papers[:max_results]
            
            result = LiteratureSearchResult(
                query=query,
                total_results=len(unique_papers),
                papers=unique_papers,
                search_sources=search_sources,
                timestamp=datetime.now()
            )
            
            logger.info(f"📚 Literature search completed: {len(unique_papers)} unique papers found")
            return result
            
        except Exception as e:
            logger.error(f"Literature search failed: {str(e)}")
            return LiteratureSearchResult(
                query=query,
                total_results=0,
                papers=[],
                search_sources=[],
                timestamp=datetime.now()
            )

    def search_crossref(self, query: str, limit: int = 20) -> List[ResearchPaper]:
        """
        Search CrossRef database
        """
        try:
            # Rate limiting
            self._rate_limit('crossref', 0.1)  # 10 requests per second max
            
            params = {
                'query': query,
                'rows': limit,
                'mailto': 'research@orchidcontinuum.org',  # Polite pool
                'sort': 'relevance',
                'filter': 'type:journal-article'
            }
            
            response = requests.get(self.crossref_base, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('message', {}).get('items', []):
                try:
                    # Extract paper information
                    title = item.get('title', ['Unknown Title'])[0] if item.get('title') else 'Unknown Title'
                    
                    # Authors
                    authors = []
                    for author in item.get('author', []):
                        given = author.get('given', '') or ''
                        family = author.get('family', '') or ''
                        if given and family:
                            authors.append(f"{given} {family}")
                        elif family:
                            authors.append(family)
                    
                    # Journal
                    journal = item.get('container-title', ['Unknown Journal'])[0] if item.get('container-title') else 'Unknown Journal'
                    
                    # Publication date
                    pub_date = 'Unknown'
                    if 'published-print' in item:
                        date_parts = item['published-print'].get('date-parts', [[]])[0]
                        if date_parts:
                            pub_date = f"{date_parts[0]}" + (f"-{date_parts[1]:02d}" if len(date_parts) > 1 else "")
                    
                    # DOI and URL
                    doi = item.get('DOI', '')
                    url = f"https://doi.org/{doi}" if doi else None
                    
                    # Citation count (if available)
                    citation_count = item.get('is-referenced-by-count', 0)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(title, query, citation_count)
                    
                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        abstract='',  # CrossRef doesn't provide abstracts
                        citation_count=citation_count,
                        source='CrossRef',
                        url=url,
                        keywords=[],
                        relevance_score=relevance_score
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing CrossRef paper: {str(e)}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"CrossRef search error: {str(e)}")
            return []

    def search_pubmed(self, query: str, limit: int = 20) -> List[ResearchPaper]:
        """
        Search PubMed database
        """
        try:
            # Rate limiting
            self._rate_limit('pubmed', 0.5)  # 2 requests per second max
            
            # Step 1: Search for PMIDs
            search_params = {
                'db': 'pubmed',
                'term': query,
                'retmax': limit,
                'retmode': 'xml',
                'usehistory': 'y'
            }
            
            search_response = requests.get(f"{self.pubmed_base}/esearch.fcgi", params=search_params, timeout=10)
            search_response.raise_for_status()
            
            # Parse search results
            search_root = ET.fromstring(search_response.content)
            pmids = [id_elem.text for id_elem in search_root.findall('.//Id')]
            
            if not pmids:
                return []
            
            # Step 2: Fetch detailed information
            self._rate_limit('pubmed', 0.5)
            
            fetch_params = {
                'db': 'pubmed',
                'id': ','.join(pmids),
                'retmode': 'xml'
            }
            
            fetch_response = requests.get(f"{self.pubmed_base}/efetch.fcgi", params=fetch_params, timeout=15)
            fetch_response.raise_for_status()
            
            # Parse detailed results
            fetch_root = ET.fromstring(fetch_response.content)
            papers = []
            
            for article in fetch_root.findall('.//PubmedArticle'):
                try:
                    # Title
                    title_elem = article.find('.//ArticleTitle')
                    title = title_elem.text if title_elem is not None else 'Unknown Title'
                    
                    # Authors
                    authors = []
                    for author in article.findall('.//Author'):
                        given = author.find('ForeName')
                        family = author.find('LastName')
                        if given is not None and family is not None:
                            authors.append(f"{given.text} {family.text}")
                        elif family is not None:
                            authors.append(family.text)
                    
                    # Journal
                    journal_elem = article.find('.//Journal/Title')
                    journal = journal_elem.text if journal_elem is not None else 'Unknown Journal'
                    
                    # Publication date
                    pub_date = 'Unknown'
                    pub_date_elem = article.find('.//PubDate')
                    if pub_date_elem is not None:
                        year = pub_date_elem.find('Year')
                        month = pub_date_elem.find('Month')
                        if year is not None:
                            pub_date = year.text
                            if month is not None:
                                try:
                                    month_num = datetime.strptime(month.text, '%b').month
                                    pub_date += f"-{month_num:02d}"
                                except:
                                    pass
                    
                    # DOI
                    doi = ''
                    for article_id in article.findall('.//ArticleId'):
                        if article_id.get('IdType') == 'doi':
                            doi = article_id.text
                            break
                    
                    # Abstract
                    abstract_elem = article.find('.//Abstract/AbstractText')
                    abstract = abstract_elem.text if abstract_elem is not None else ''
                    
                    # PMID for URL
                    pmid_elem = article.find('.//PMID')
                    pmid = pmid_elem.text if pmid_elem is not None else ''
                    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
                    
                    # Keywords
                    keywords = []
                    for keyword in article.findall('.//Keyword'):
                        if keyword.text:
                            keywords.append(keyword.text)
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(title + ' ' + abstract, query, 0)
                    
                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        abstract=abstract,
                        citation_count=0,  # PubMed doesn't provide citation counts
                        source='PubMed',
                        url=url,
                        keywords=keywords,
                        relevance_score=relevance_score
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing PubMed paper: {str(e)}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"PubMed search error: {str(e)}")
            return []

    def search_semantic_scholar(self, query: str, limit: int = 20) -> List[ResearchPaper]:
        """
        Search Semantic Scholar database
        """
        try:
            # Rate limiting
            self._rate_limit('semantic_scholar', 0.5)  # Be conservative
            
            params = {
                'query': query,
                'limit': limit,
                'fields': 'title,authors,abstract,venue,year,citationCount,externalIds,url'
            }
            
            response = requests.get(f"{self.semantic_scholar_base}/paper/search", params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            papers = []
            
            for item in data.get('data', []):
                try:
                    # Extract paper information
                    title = item.get('title', 'Unknown Title')
                    
                    # Authors
                    authors = []
                    for author in item.get('authors', []):
                        author_name = author.get('name', '')
                        if author_name:
                            authors.append(author_name)
                    
                    # Journal/Venue
                    journal = item.get('venue', 'Unknown Venue')
                    
                    # Publication year
                    pub_date = str(item.get('year', 'Unknown'))
                    
                    # DOI
                    doi = ''
                    external_ids = item.get('externalIds', {})
                    if external_ids and 'DOI' in external_ids:
                        doi = external_ids['DOI']
                    
                    # Abstract
                    abstract = item.get('abstract', '')
                    
                    # Citation count
                    citation_count = item.get('citationCount', 0)
                    
                    # URL
                    url = item.get('url', '')
                    
                    # Calculate relevance score
                    relevance_score = self._calculate_relevance_score(title + ' ' + abstract, query, citation_count)
                    
                    paper = ResearchPaper(
                        title=title,
                        authors=authors,
                        journal=journal,
                        publication_date=pub_date,
                        doi=doi,
                        abstract=abstract,
                        citation_count=citation_count,
                        source='Semantic Scholar',
                        url=url,
                        keywords=[],
                        relevance_score=relevance_score
                    )
                    
                    papers.append(paper)
                    
                except Exception as e:
                    logger.warning(f"Error parsing Semantic Scholar paper: {str(e)}")
                    continue
            
            return papers
            
        except Exception as e:
            logger.error(f"Semantic Scholar search error: {str(e)}")
            return []

    def _rate_limit(self, source: str, min_interval: float):
        """Simple rate limiting"""
        current_time = datetime.now().timestamp()
        last_time = self.last_request_times.get(source, 0)
        
        if current_time - last_time < min_interval:
            sleep_time = min_interval - (current_time - last_time)
            import time
            time.sleep(sleep_time)
        
        self.last_request_times[source] = datetime.now().timestamp()

    def _calculate_relevance_score(self, text: str, query: str, citation_count: int) -> float:
        """Calculate relevance score for a paper"""
        try:
            text_lower = text.lower()
            query_lower = query.lower()
            query_terms = query_lower.split()
            
            # Base score from term matching
            score = 0.0
            for term in query_terms:
                if term in text_lower:
                    score += 1.0
            
            # Normalize by number of query terms
            if query_terms:
                score = score / len(query_terms)
            
            # Boost based on citation count (logarithmic)
            if citation_count > 0:
                import math
                citation_boost = math.log10(citation_count + 1) * 0.1
                score += citation_boost
            
            return min(score, 1.0)  # Cap at 1.0
            
        except Exception as e:
            return 0.0

    def deduplicate_papers(self, papers: List[ResearchPaper]) -> List[ResearchPaper]:
        """Remove duplicate papers based on DOI and title similarity"""
        unique_papers = []
        seen_dois = set()
        seen_titles = set()
        
        for paper in papers:
            # Check DOI duplicates
            if paper.doi and paper.doi in seen_dois:
                continue
            
            # Check title similarity (simple approach)
            title_normalized = paper.title.lower().strip()
            if title_normalized in seen_titles:
                continue
            
            # Add to unique list
            unique_papers.append(paper)
            
            if paper.doi:
                seen_dois.add(paper.doi)
            seen_titles.add(title_normalized)
        
        return unique_papers

    def search_orchid_research(self, genus: str = '', species: str = '') -> LiteratureSearchResult:
        """Search for orchid-specific research"""
        query_parts = []
        
        if genus:
            query_parts.append(f'"{genus}"')
        if species:
            query_parts.append(f'"{species}"')
        
        query_parts.extend(['orchid', 'orchidaceae'])
        
        query = ' '.join(query_parts)
        return self.search_all_databases(query, max_results=30)

    def search_mycorrhizal_research(self) -> LiteratureSearchResult:
        """Search for mycorrhizal research"""
        query = 'mycorrhizal fungi orchid symbiosis carbon sequestration'
        return self.search_all_databases(query, max_results=40)

    def search_climate_research(self) -> LiteratureSearchResult:
        """Search for climate-related orchid research"""
        query = 'orchid climate change adaptation CAM photosynthesis carbon capture'
        return self.search_all_databases(query, max_results=40)

# Global literature search engine
literature_engine = LiteratureSearchEngine()

# Routes
@literature_bp.route('/')
def literature_home():
    """Literature search interface - redirect to research wizard"""
    from flask import redirect, url_for
    return redirect('/research/research-wizard?stage=hypothesis')

@literature_bp.route('/search', methods=['POST'])
def search_literature():
    """Search scientific literature"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        max_results = data.get('max_results', 50)
        
        if not query:
            return jsonify({'success': False, 'error': 'Query is required'}), 400
        
        # Perform search
        results = literature_engine.search_all_databases(query, max_results)
        
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
                'timestamp': results.timestamp.isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Literature search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@literature_bp.route('/search/orchid', methods=['POST'])
def search_orchid_literature():
    """Search orchid-specific literature"""
    try:
        data = request.get_json()
        genus = data.get('genus', '')
        species = data.get('species', '')
        
        results = literature_engine.search_orchid_research(genus, species)
        
        # Convert to JSON format (same as above)
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
        logger.error(f"Orchid literature search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@literature_bp.route('/search/mycorrhizal')
def search_mycorrhizal_literature():
    """Search mycorrhizal research"""
    try:
        results = literature_engine.search_mycorrhizal_research()
        
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
        logger.error(f"Mycorrhizal literature search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@literature_bp.route('/search/climate')
def search_climate_literature():
    """Search climate research"""
    try:
        results = literature_engine.search_climate_research()
        
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
        logger.error(f"Climate literature search error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("📚 Literature Search System standalone mode")
    print("Capabilities:")
    print("  - Multi-database search (CrossRef, PubMed, Semantic Scholar)")
    print("  - Orchid-specific research search")
    print("  - Mycorrhizal and climate research")
    print("  - Citation analysis and relevance scoring")