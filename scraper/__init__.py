"""
SVO (Subject-Verb-Object) Scraper Package for Orchid Data Processing

This package provides modular components for web scraping and NLP-based 
data extraction focused on orchid-related content from various sources.

Modules:
- fetcher: URL fetching with rate limiting and error handling
- parser: SVO tuple extraction using NLP techniques

Usage:
    from scraper.fetcher import fetch_all
    from scraper.parser import parse_svo
    
    # Fetch data from URLs
    raw_data = fetch_all(urls, config)
    
    # Extract SVO tuples
    svo_tuples = parse_svo(raw_data, config)
"""

__version__ = "1.0.0"
__author__ = "Orchid Continuum Project"

# Package-level imports for convenience
from .fetcher import fetch_all, FetchResult, ScrapingSession
from .parser import parse_svo, SVOTuple, SVOParser

__all__ = [
    'fetch_all',
    'parse_svo', 
    'FetchResult',
    'ScrapingSession',
    'SVOTuple',
    'SVOParser'
]