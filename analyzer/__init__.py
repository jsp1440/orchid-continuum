"""
Analyzer Package for SVO (Subject-Verb-Object) Data Analysis

This package provides comprehensive tools for analyzing orchid care information
using Subject-Verb-Object pattern extraction and analysis.

Modules:
- processor: Data cleaning and normalization functions
- analyzer: Pattern analysis and insight extraction
- visualizer: Professional visualization and charting

Author: Orchid Continuum Project
Version: 1.0.0
"""

from .processor import clean_svo
from .analyzer import analyze_svo
from .visualizer import visualize_svo

__all__ = ['clean_svo', 'analyze_svo', 'visualize_svo']
__version__ = '1.0.0'

# Package configuration
PACKAGE_CONFIG = {
    'name': 'analyzer',
    'description': 'SVO Data Analysis Package for Orchid Care Information',
    'supported_formats': ['json', 'csv', 'dict'],
    'visualization_formats': ['png', 'jpg', 'svg', 'pdf'],
    'analysis_methods': ['frequency', 'correlation', 'clustering', 'sentiment']
}