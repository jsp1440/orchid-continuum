"""
Storage package for data persistence and database operations.

This package provides database handlers for storing and retrieving
SVO (Subject-Verb-Object) extracted data and analysis results.
"""

from .db_handler import (
    SVODatabaseHandler,
    save_results,
    get_svo_data,
    validate_svo_data,
    batch_insert_svo_data,
    create_svo_tables,
    get_svo_statistics,
    svo_handler
)

__all__ = [
    'SVODatabaseHandler',
    'save_results',
    'get_svo_data',
    'validate_svo_data',
    'batch_insert_svo_data',
    'create_svo_tables',
    'get_svo_statistics',
    'svo_handler'
]

__version__ = '1.0.0'