"""
Database handler for SVO (Subject-Verb-Object) data persistence.

This module provides comprehensive database operations for storing, retrieving,
and managing SVO extracted data and analysis results using SQLAlchemy patterns
from the existing codebase.
"""

import logging
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy import and_, or_, func
from sqlalchemy.exc import IntegrityError, DataError

# Import database and models from the existing codebase with error handling
try:
    from app import db, app
except ImportError as e:
    logger.error(f"❌ Failed to import Flask app components: {str(e)}")
    raise ImportError(f"Cannot import Flask app components: {str(e)}")

try:
    from models import SVOExtractedData, OrchidRecord
except ImportError as e:
    logger.error(f"❌ Failed to import database models: {str(e)}")
    raise ImportError(f"Cannot import database models: {str(e)}")

try:
    from config import CONFIG, DB_CONFIG
except ImportError as e:
    logger.warning(f"⚠️ Failed to import config, using defaults: {str(e)}")
    CONFIG = {
        'quality_thresholds': {
            'min_svo_confidence': 0.7,
            'min_text_length': 20,
            'max_text_length': 1000
        }
    }
    DB_CONFIG = {
        'batch_insert_size': 1000,
        'connection_timeout': 30
    }

# Set up logging
logger = logging.getLogger(__name__)


class SVODatabaseHandler:
    """
    Main database handler class for SVO data operations.
    
    Provides comprehensive methods for creating tables, inserting data,
    validating records, and retrieving SVO extracted data.
    """
    
    def __init__(self):
        """Initialize the SVO database handler with comprehensive error handling"""
        try:
            self.batch_size = DB_CONFIG.get('batch_insert_size', 1000) if DB_CONFIG else 1000
            self.connection_timeout = DB_CONFIG.get('connection_timeout', 30) if DB_CONFIG else 30
            self.quality_thresholds = CONFIG.get('quality_thresholds', {}) if CONFIG else {
                'min_svo_confidence': 0.7,
                'min_text_length': 20,
                'max_text_length': 1000
            }
            
            # Validate configuration values
            if not isinstance(self.batch_size, int) or self.batch_size <= 0:
                logger.warning("⚠️ Invalid batch_size, using default 1000")
                self.batch_size = 1000
            
            if not isinstance(self.connection_timeout, (int, float)) or self.connection_timeout <= 0:
                logger.warning("⚠️ Invalid connection_timeout, using default 30")
                self.connection_timeout = 30
            
            if not isinstance(self.quality_thresholds, dict):
                logger.warning("⚠️ Invalid quality_thresholds, using defaults")
                self.quality_thresholds = {
                    'min_svo_confidence': 0.7,
                    'min_text_length': 20,
                    'max_text_length': 1000
                }
            
            logger.info("✅ SVO Database Handler initialized with validated config")
            
        except Exception as e:
            logger.error(f"❌ Error initializing SVO Database Handler: {str(e)}")
            # Set safe defaults
            self.batch_size = 1000
            self.connection_timeout = 30
            self.quality_thresholds = {
                'min_svo_confidence': 0.7,
                'min_text_length': 20,
                'max_text_length': 1000
            }
            logger.info("✅ SVO Database Handler initialized with safe defaults")
    
    def create_tables(self) -> bool:
        """
        Create SVO database tables if they don't exist.
        
        Returns:
            bool: True if tables were created successfully, False otherwise
        """
        try:
            with app.app_context():
                # Create all tables (this will only create missing ones)
                db.create_all()
                logger.info("✅ SVO database tables created successfully")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error creating SVO database tables: {str(e)}")
            return False
    
    def validate_svo_data(self, svo_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate SVO data before insertion.
        
        Args:
            svo_data (dict): Dictionary containing SVO data to validate
            
        Returns:
            tuple: (is_valid, list_of_issues)
        """
        issues = []
        
        # Required fields validation
        required_fields = ['subject', 'verb', 'object', 'original_text', 'source_url']
        for field in required_fields:
            if field not in svo_data or not svo_data[field]:
                issues.append(f"Missing required field: {field}")
        
        if issues:  # Don't continue if required fields are missing
            return False, issues
        
        # Subject validation
        subject = svo_data['subject'].strip()
        if len(subject) < 3:
            issues.append("Subject too short (minimum 3 characters)")
        elif len(subject) > 200:
            issues.append("Subject too long (maximum 200 characters)")
        
        # Verb validation
        verb = svo_data['verb'].strip()
        if len(verb) < 2:
            issues.append("Verb too short (minimum 2 characters)")
        elif len(verb) > 100:
            issues.append("Verb too long (maximum 100 characters)")
        
        # Object validation
        obj = svo_data['object'].strip()
        if len(obj) < 5:
            issues.append("Object too short (minimum 5 characters)")
        
        # Original text validation
        original_text = svo_data['original_text'].strip()
        min_text_length = self.quality_thresholds.get('min_text_length', 20)
        max_text_length = self.quality_thresholds.get('max_text_length', 1000)
        
        if len(original_text) < min_text_length:
            issues.append(f"Original text too short (minimum {min_text_length} characters)")
        elif len(original_text) > max_text_length:
            issues.append(f"Original text too long (maximum {max_text_length} characters)")
        
        # Confidence scores validation
        min_confidence = self.quality_thresholds.get('min_svo_confidence', 0.0)
        extraction_confidence = svo_data.get('extraction_confidence', 0.0)
        svo_confidence = svo_data.get('svo_confidence', 0.0)
        
        if extraction_confidence < min_confidence:
            issues.append(f"Extraction confidence too low (minimum {min_confidence})")
        
        if svo_confidence < min_confidence:
            issues.append(f"SVO confidence too low (minimum {min_confidence})")
        
        # URL validation (basic)
        source_url = svo_data['source_url']
        if not source_url.startswith(('http://', 'https://')):
            issues.append("Invalid source URL format")
        
        return len(issues) == 0, issues
    
    def save_svo_record(self, svo_data: Dict[str, Any]) -> Optional[SVOExtractedData]:
        """
        Save a single SVO record to the database with comprehensive error handling.
        
        Args:
            svo_data (dict): Dictionary containing SVO data
            
        Returns:
            SVOExtractedData: The saved record, or None if failed
        """
        try:
            # Validate input data type
            if not isinstance(svo_data, dict):
                logger.error(f"❌ Invalid svo_data type: {type(svo_data)}")
                return None
            
            # Validate data first
            is_valid, issues = self.validate_svo_data(svo_data)
            if not is_valid:
                logger.warning(f"⚠️ SVO data validation failed: {', '.join(issues)}")
                return None
            
            # Ensure we're in app context
            def _create_record():
                try:
                    # Create new SVO record with safe value extraction
                    svo_record = SVOExtractedData(
                        source_url=str(svo_data['source_url']),
                        source_type=str(svo_data.get('source_type', 'unknown')),
                        page_title=str(svo_data.get('page_title')) if svo_data.get('page_title') else None,
                        subject=str(svo_data['subject']).strip(),
                        verb=str(svo_data['verb']).strip(),
                        object=str(svo_data['object']).strip(),
                        original_text=str(svo_data['original_text']).strip(),
                        context_before=str(svo_data.get('context_before')) if svo_data.get('context_before') else None,
                        context_after=str(svo_data.get('context_after')) if svo_data.get('context_after') else None,
                        extraction_confidence=float(svo_data.get('extraction_confidence', 0.0)),
                        svo_confidence=float(svo_data.get('svo_confidence', 0.0)),
                        text_quality_score=float(svo_data.get('text_quality_score')) if svo_data.get('text_quality_score') is not None else None,
                        genus=str(svo_data.get('genus')) if svo_data.get('genus') else None,
                        species=str(svo_data.get('species')) if svo_data.get('species') else None,
                        orchid_type=str(svo_data.get('orchid_type')) if svo_data.get('orchid_type') else None,
                        care_category=str(svo_data.get('care_category')) if svo_data.get('care_category') else None,
                        care_subcategory=str(svo_data.get('care_subcategory')) if svo_data.get('care_subcategory') else None,
                        seasonal_relevance=str(svo_data.get('seasonal_relevance')) if svo_data.get('seasonal_relevance') else None,
                        processing_status=str(svo_data.get('processing_status', 'pending')),
                        validation_notes=str(svo_data.get('validation_notes')) if svo_data.get('validation_notes') else None,
                        batch_id=str(svo_data.get('batch_id')) if svo_data.get('batch_id') else None,
                        nlp_metadata=svo_data.get('nlp_metadata'),
                        extraction_metadata=svo_data.get('extraction_metadata'),
                        quality_metrics=svo_data.get('quality_metrics'),
                        orchid_record_id=int(svo_data.get('orchid_record_id')) if svo_data.get('orchid_record_id') else None,
                        related_svo_ids=svo_data.get('related_svo_ids'),
                        ingestion_source=str(svo_data.get('ingestion_source', 'svo_processor')),
                        is_featured=bool(svo_data.get('is_featured', False)),
                        extracted_at=svo_data.get('extracted_at') or datetime.utcnow(),
                        validated_at=svo_data.get('validated_at')
                    )
                    
                    # Add to session and commit
                    db.session.add(svo_record)
                    db.session.commit()
                    
                    logger.info(f"✅ SVO record saved: ID {svo_record.id}")
                    return svo_record
                    
                except ValueError as e:
                    logger.error(f"❌ Data type conversion error: {str(e)}")
                    db.session.rollback()
                    return None
                except AttributeError as e:
                    logger.error(f"❌ Attribute error during record creation: {str(e)}")
                    db.session.rollback()
                    return None
            
            # Execute within app context if needed
            if hasattr(app, 'app_context') and app.app_context:
                return _create_record()
            else:
                with app.app_context():
                    return _create_record()
                
        except IntegrityError as e:
            logger.error(f"❌ Database integrity error: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return None
        except ImportError as e:
            logger.error(f"❌ Import error in save_svo_record: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected error saving SVO record: {str(e)}")
            try:
                db.session.rollback()
            except:
                pass
            return None
    
    def batch_insert_svo_data(self, svo_data_list: List[Dict[str, Any]], 
                             batch_id: Optional[str] = None) -> Tuple[int, int, List[str]]:
        """
        Batch insert multiple SVO records with validation.
        
        Args:
            svo_data_list (list): List of SVO data dictionaries
            batch_id (str, optional): Batch ID for tracking
            
        Returns:
            tuple: (successful_count, failed_count, error_messages)
        """
        successful_count = 0
        failed_count = 0
        error_messages = []
        
        if batch_id is None:
            batch_id = str(uuid.uuid4())[:8]
        
        logger.info(f"🔄 Starting batch insert: {len(svo_data_list)} records, batch_id: {batch_id}")
        
        try:
            with app.app_context():
                for i, svo_data in enumerate(svo_data_list):
                    try:
                        # Add batch_id to data
                        svo_data['batch_id'] = batch_id
                        
                        # Save individual record
                        record = self.save_svo_record(svo_data)
                        
                        if record:
                            successful_count += 1
                        else:
                            failed_count += 1
                            error_messages.append(f"Failed to save record {i+1}: validation failed")
                        
                        # Commit in batches to avoid memory issues
                        if (i + 1) % self.batch_size == 0:
                            db.session.commit()
                            logger.info(f"📦 Batch commit: {i+1} records processed")
                            
                    except Exception as e:
                        failed_count += 1
                        error_msg = f"Record {i+1} failed: {str(e)}"
                        error_messages.append(error_msg)
                        logger.warning(f"⚠️ {error_msg}")
                        
                        # Continue processing other records
                        try:
                            db.session.rollback()
                        except:
                            pass
                
                # Final commit for any remaining records
                try:
                    db.session.commit()
                except Exception as e:
                    logger.error(f"❌ Final commit failed: {str(e)}")
                    db.session.rollback()
                
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {str(e)}")
            error_messages.append(f"Batch insert error: {str(e)}")
            
        logger.info(f"✅ Batch insert completed: {successful_count} success, {failed_count} failed")
        return successful_count, failed_count, error_messages
    
    def get_svo_data(self, filters: Dict[str, Any] = None, 
                     limit: int = 100, offset: int = 0) -> List[SVOExtractedData]:
        """
        Retrieve SVO data with optional filters.
        
        Args:
            filters (dict): Optional filters for querying
            limit (int): Maximum number of records to return
            offset (int): Number of records to skip
            
        Returns:
            list: List of SVOExtractedData records
        """
        try:
            with app.app_context():
                query = SVOExtractedData.query
                
                if filters:
                    # Apply filters
                    if 'source_type' in filters:
                        query = query.filter(SVOExtractedData.source_type == filters['source_type'])
                    
                    if 'genus' in filters:
                        query = query.filter(SVOExtractedData.genus == filters['genus'])
                    
                    if 'species' in filters:
                        query = query.filter(SVOExtractedData.species == filters['species'])
                    
                    if 'care_category' in filters:
                        query = query.filter(SVOExtractedData.care_category == filters['care_category'])
                    
                    if 'processing_status' in filters:
                        query = query.filter(SVOExtractedData.processing_status == filters['processing_status'])
                    
                    if 'min_confidence' in filters:
                        min_conf = filters['min_confidence']
                        query = query.filter(
                            and_(
                                SVOExtractedData.extraction_confidence >= min_conf,
                                SVOExtractedData.svo_confidence >= min_conf
                            )
                        )
                    
                    if 'batch_id' in filters:
                        query = query.filter(SVOExtractedData.batch_id == filters['batch_id'])
                    
                    if 'is_featured' in filters:
                        query = query.filter(SVOExtractedData.is_featured == filters['is_featured'])
                
                # Apply ordering, limit, and offset
                records = query.order_by(SVOExtractedData.created_at.desc()).offset(offset).limit(limit).all()
                
                logger.info(f"📊 Retrieved {len(records)} SVO records")
                return records
                
        except Exception as e:
            logger.error(f"❌ Error retrieving SVO data: {str(e)}")
            return []
    
    def get_svo_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about SVO data in the database.
        
        Returns:
            dict: Statistics about SVO data
        """
        try:
            with app.app_context():
                stats = {
                    'total_records': SVOExtractedData.query.count(),
                    'by_source_type': {},
                    'by_processing_status': {},
                    'by_care_category': {},
                    'high_confidence_count': 0,
                    'featured_count': SVOExtractedData.query.filter(SVOExtractedData.is_featured == True).count(),
                    'recent_count': SVOExtractedData.query.filter(
                        SVOExtractedData.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
                    ).count()
                }
                
                # Source type distribution
                source_types = db.session.query(
                    SVOExtractedData.source_type, 
                    func.count(SVOExtractedData.id)
                ).group_by(SVOExtractedData.source_type).all()
                
                for source_type, count in source_types:
                    stats['by_source_type'][source_type] = count
                
                # Processing status distribution
                statuses = db.session.query(
                    SVOExtractedData.processing_status,
                    func.count(SVOExtractedData.id)
                ).group_by(SVOExtractedData.processing_status).all()
                
                for status, count in statuses:
                    stats['by_processing_status'][status] = count
                
                # Care category distribution
                categories = db.session.query(
                    SVOExtractedData.care_category,
                    func.count(SVOExtractedData.id)
                ).filter(SVOExtractedData.care_category.isnot(None)).group_by(SVOExtractedData.care_category).all()
                
                for category, count in categories:
                    stats['by_care_category'][category] = count
                
                # High confidence count
                min_confidence = self.quality_thresholds.get('min_svo_confidence', 0.7)
                stats['high_confidence_count'] = SVOExtractedData.query.filter(
                    and_(
                        SVOExtractedData.extraction_confidence >= min_confidence,
                        SVOExtractedData.svo_confidence >= min_confidence
                    )
                ).count()
                
                logger.info("📊 SVO statistics generated successfully")
                return stats
                
        except Exception as e:
            logger.error(f"❌ Error generating SVO statistics: {str(e)}")
            return {}
    
    def update_svo_record(self, record_id: int, updates: Dict[str, Any]) -> bool:
        """
        Update an existing SVO record.
        
        Args:
            record_id (int): ID of the record to update
            updates (dict): Dictionary of fields to update
            
        Returns:
            bool: True if update was successful, False otherwise
        """
        try:
            with app.app_context():
                record = SVOExtractedData.query.get(record_id)
                
                if not record:
                    logger.warning(f"⚠️ SVO record not found: ID {record_id}")
                    return False
                
                # Update allowed fields
                allowed_fields = [
                    'processing_status', 'validation_notes', 'care_category',
                    'care_subcategory', 'seasonal_relevance', 'genus', 'species',
                    'orchid_type', 'is_featured', 'orchid_record_id',
                    'nlp_metadata', 'extraction_metadata', 'quality_metrics'
                ]
                
                for field, value in updates.items():
                    if field in allowed_fields and hasattr(record, field):
                        setattr(record, field, value)
                
                record.updated_at = datetime.utcnow()
                db.session.commit()
                
                logger.info(f"✅ SVO record updated: ID {record_id}")
                return True
                
        except Exception as e:
            logger.error(f"❌ Error updating SVO record {record_id}: {str(e)}")
            db.session.rollback()
            return False
    
    def delete_svo_records(self, filters: Dict[str, Any]) -> int:
        """
        Delete SVO records based on filters (use with caution).
        
        Args:
            filters (dict): Filters to identify records to delete
            
        Returns:
            int: Number of records deleted
        """
        try:
            with app.app_context():
                query = SVOExtractedData.query
                
                # Apply filters
                if 'batch_id' in filters:
                    query = query.filter(SVOExtractedData.batch_id == filters['batch_id'])
                
                if 'processing_status' in filters:
                    query = query.filter(SVOExtractedData.processing_status == filters['processing_status'])
                
                if 'source_type' in filters:
                    query = query.filter(SVOExtractedData.source_type == filters['source_type'])
                
                records_to_delete = query.all()
                count = len(records_to_delete)
                
                if count > 0:
                    for record in records_to_delete:
                        db.session.delete(record)
                    
                    db.session.commit()
                    logger.info(f"🗑️ Deleted {count} SVO records")
                
                return count
                
        except Exception as e:
            logger.error(f"❌ Error deleting SVO records: {str(e)}")
            db.session.rollback()
            return 0


# Initialize global handler instance
svo_handler = SVODatabaseHandler()


def save_results(results: Union[Dict[str, Any], List[Dict[str, Any]]], 
                batch_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Main function to save SVO extraction results to the database.
    Ensures proper Flask app context and comprehensive error handling.
    
    Args:
        results (dict or list): SVO extraction results to save
        batch_id (str, optional): Batch ID for tracking
        
    Returns:
        tuple: (success, result_info)
    """
    try:
        # Validate input parameters
        if results is None:
            logger.warning("⚠️ No results provided to save")
            return False, {'error': 'No results provided'}
        
        # Handle single result or list of results
        if isinstance(results, dict):
            results = [results]
        elif not isinstance(results, list):
            logger.error(f"❌ Invalid results type: {type(results)}")
            return False, {'error': f'Invalid results type: {type(results)}'}
        
        if not results:
            logger.warning("⚠️ Empty results list provided")
            return False, {'error': 'Empty results list provided'}
        
        # Ensure we're in Flask app context
        if not app.app_context:
            logger.warning("⚠️ No Flask app context, creating one")
            with app.app_context():
                return _save_results_with_context(results, batch_id)
        else:
            # We're already in app context
            return _save_results_with_context(results, batch_id)
        
    except ImportError as e:
        logger.error(f"❌ Import error in save_results: {str(e)}")
        return False, {'error': f'Import error: {str(e)}'}
    except AttributeError as e:
        logger.error(f"❌ Attribute error in save_results: {str(e)}")
        return False, {'error': f'Attribute error: {str(e)}'}
    except Exception as e:
        logger.error(f"❌ Unexpected error in save_results: {str(e)}")
        return False, {'error': f'Unexpected error: {str(e)}'}

def _save_results_with_context(results: List[Dict[str, Any]], 
                              batch_id: Optional[str] = None) -> Tuple[bool, Dict[str, Any]]:
    """
    Internal function to save results within Flask app context.
    
    Args:
        results: List of SVO data dictionaries
        batch_id: Optional batch ID for tracking
        
    Returns:
        tuple: (success, result_info)
    """
    try:
        # Ensure database tables exist
        if not svo_handler.create_tables():
            logger.error("❌ Failed to create/verify database tables")
            return False, {'error': 'Database table creation failed'}
        
        # Validate each result before processing
        valid_results = []
        validation_errors = []
        
        for i, result in enumerate(results):
            try:
                if not isinstance(result, dict):
                    validation_errors.append(f"Result {i+1}: Not a dictionary")
                    continue
                
                # Check for required fields
                required_fields = ['subject', 'verb', 'object', 'original_text', 'source_url']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    validation_errors.append(f"Result {i+1}: Missing fields {missing_fields}")
                    continue
                
                # Basic data type validation
                if not isinstance(result.get('subject'), str) or not result['subject'].strip():
                    validation_errors.append(f"Result {i+1}: Invalid subject")
                    continue
                
                if not isinstance(result.get('verb'), str) or not result['verb'].strip():
                    validation_errors.append(f"Result {i+1}: Invalid verb")
                    continue
                
                if not isinstance(result.get('object'), str) or not result['object'].strip():
                    validation_errors.append(f"Result {i+1}: Invalid object")
                    continue
                
                valid_results.append(result)
                
            except Exception as e:
                validation_errors.append(f"Result {i+1}: Validation error - {str(e)}")
                continue
        
        if not valid_results:
            logger.error("❌ No valid results to save after validation")
            return False, {
                'error': 'No valid results after validation',
                'validation_errors': validation_errors[:10]  # Limit error messages
            }
        
        # Log validation results
        if validation_errors:
            logger.warning(f"⚠️ {len(validation_errors)} results failed validation")
        
        # Perform batch insert with error handling
        try:
            successful, failed, errors = svo_handler.batch_insert_svo_data(valid_results, batch_id)
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {str(e)}")
            return False, {'error': f'Batch insert failed: {str(e)}'}
        
        # Prepare result information
        result_info = {
            'total_processed': len(results),
            'valid_results': len(valid_results),
            'successful': successful,
            'failed': failed,
            'validation_failed': len(validation_errors),
            'batch_id': batch_id or 'auto-generated',
            'errors': (errors + validation_errors)[:15] if errors or validation_errors else [],  # Limit error messages
            'success_rate': (successful / len(valid_results)) if valid_results else 0.0
        }
        
        success = successful > 0
        logger.info(f"💾 Save results completed: {successful}/{len(valid_results)} successful (validation passed: {len(valid_results)}/{len(results)})")
        
        return success, result_info
        
    except Exception as e:
        logger.error(f"❌ Error in _save_results_with_context: {str(e)}")
        return False, {'error': f'Context execution error: {str(e)}'}


def get_svo_data(filters: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Retrieve SVO data with optional filters.
    
    Args:
        filters (dict): Optional filters for querying
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip
        
    Returns:
        list: List of SVO data dictionaries
    """
    records = svo_handler.get_svo_data(filters, limit, offset)
    return [record.to_dict() for record in records]


def validate_svo_data(svo_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate SVO data before processing.
    
    Args:
        svo_data (dict): SVO data to validate
        
    Returns:
        tuple: (is_valid, list_of_issues)
    """
    return svo_handler.validate_svo_data(svo_data)


def batch_insert_svo_data(svo_data_list: List[Dict[str, Any]], 
                         batch_id: Optional[str] = None) -> Tuple[int, int, List[str]]:
    """
    Batch insert SVO data records.
    
    Args:
        svo_data_list (list): List of SVO data dictionaries
        batch_id (str, optional): Batch ID for tracking
        
    Returns:
        tuple: (successful_count, failed_count, error_messages)
    """
    return svo_handler.batch_insert_svo_data(svo_data_list, batch_id)


def create_svo_tables() -> bool:
    """
    Create SVO database tables.
    
    Returns:
        bool: True if successful, False otherwise
    """
    return svo_handler.create_tables()


def get_svo_statistics() -> Dict[str, Any]:
    """
    Get comprehensive statistics about SVO data.
    
    Returns:
        dict: Statistics about SVO data
    """
    return svo_handler.get_svo_statistics()


# Export main functions for easy importing
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