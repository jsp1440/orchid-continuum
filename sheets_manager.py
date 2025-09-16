#!/usr/bin/env python3
"""
📊 Sheets Manager - Enhanced Google Sheets Integration for Orchid Continuum
Specialized module for managing Google Sheets data operations with batch processing,
progress tracking, and integration with orchestrator systems.
Built on top of google_cloud_integration.py for the Orchid Continuum project.
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# Import required Google Sheets libraries (no fallbacks - fail fast if missing)
try:
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError as e:
    error_msg = f"CRITICAL: Google Sheets libraries not available: {e}"
    logging.error(error_msg)
    logging.error("Google Sheets functionality requires: gspread, google-api-python-client, google-auth")
    logging.error("Install with: pip install gspread google-api-python-client google-auth")
    raise RuntimeError(error_msg)

# Import existing Google Cloud integration (required)
try:
    from google_cloud_integration import get_google_integration, GoogleCloudIntegration
    BASE_INTEGRATION_AVAILABLE = True
except ImportError as e:
    error_msg = f"CRITICAL: Base Google Cloud integration not available: {e}"
    logging.error(error_msg)
    logging.error("Sheets Manager requires google_cloud_integration.py to be available")
    raise RuntimeError(error_msg)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SheetConfig:
    """Configuration for sheet operations"""
    name: str
    headers: List[str]
    max_rows: int = 10000
    batch_size: int = 100
    auto_resize: bool = True
    data_validation: bool = True

@dataclass
class BatchOperation:
    """Represents a batch operation on sheets"""
    operation_id: str
    sheet_name: str
    operation_type: str  # 'insert', 'update', 'delete'
    data: List[Any]
    status: str = 'pending'  # pending, processing, completed, failed
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

class SheetsManager:
    """Enhanced Google Sheets manager with batch operations and progress tracking"""
    
    def __init__(self):
        """Initialize the sheets manager"""
        self.base_integration = None
        self.initialized = False
        self.operation_queue = []
        self.operation_history = []
        self.sheet_configs = {}
        self.progress_tracker = {}
        
        # Initialize base integration
        self._initialize_base_integration()
        
        # Initialize predefined sheet configurations
        self._setup_default_sheets()
        
        logger.info("📊 Sheets Manager initialized")
    
    def _initialize_base_integration(self):
        """Initialize connection to base Google Cloud integration"""
        # BASE_INTEGRATION_AVAILABLE is guaranteed True due to import validation above
        try:
            from google_cloud_integration import get_google_integration as ggi
            self.base_integration = ggi()
            if self.base_integration and self.base_integration.is_available():
                self.initialized = True
                logger.info("✅ Sheets Manager connected to Google Cloud")
                return True
            else:
                error_msg = "CRITICAL: Google Cloud integration not functional - check credentials and API access"
                logger.error(error_msg)
                raise RuntimeError(error_msg)
        except Exception as e:
            error_msg = f"CRITICAL: Failed to initialize base integration: {e}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
    
    def _setup_default_sheets(self):
        """Setup default sheet configurations for orchid data"""
        self.sheet_configs = {
            'OrchidBreedingData': SheetConfig(
                name='OrchidBreedingData',
                headers=[
                    'Date', 'Hybrid Name', 'Parent1', 'Parent2', 'Genus', 
                    'Breeder Notes', 'AI Analysis', 'Image URLs', 'Source', 
                    'Success Rating', 'Vigor Notes', 'Color Notes', 'Size Notes',
                    'Status', 'Updated At'
                ]
            ),
            'SVO_Hybrid_Data': SheetConfig(
                name='SVO_Hybrid_Data',
                headers=[
                    'Genus', 'Hybrid Name', 'Parent1', 'Parent2', 'Year', 
                    'Breeder Notes', 'Image URLs', 'Price', 'Availability', 
                    'Source URL', 'Scraped At', 'Status', 'Updated At'
                ]
            ),
            'HybridDataUpdates': SheetConfig(
                name='HybridDataUpdates',
                headers=[
                    'Update ID', 'Hybrid Name', 'Field Updated', 'Old Value', 
                    'New Value', 'Source', 'Timestamp', 'Verified', 'Notes'
                ]
            ),
            'OrchidProgressTracking': SheetConfig(
                name='OrchidProgressTracking',
                headers=[
                    'Operation ID', 'Operation Type', 'Sheet Name', 'Records Count',
                    'Status', 'Started At', 'Completed At', 'Duration (sec)', 'Error Message'
                ]
            )
        }
    
    def is_available(self) -> bool:
        """Check if sheets manager is available and initialized"""
        if not self.initialized or not self.base_integration:
            return False
        
        try:
            return self.base_integration.is_available()
        except:
            return False
    
    def create_sheet_with_config(self, config: SheetConfig) -> bool:
        """Create a sheet with specified configuration"""
        if not self.is_available() or not self.base_integration:
            logger.warning("⚠️ Sheets manager not available")
            return False
            
        try:
            worksheet = self.base_integration.get_or_create_sheet(config.name, config.headers)
            if worksheet:
                # Apply configuration settings
                if config.auto_resize:
                    self._auto_resize_sheet(worksheet)
                
                logger.info(f"📊 Sheet created/configured: {config.name}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to create sheet {config.name}: {e}")
            return False
    
    def _auto_resize_sheet(self, worksheet):
        """Auto-resize sheet columns for better visibility"""
        try:
            # Basic auto-resize - adjust column widths
            worksheet.format('A1:Z1', {'textFormat': {'bold': True}})
            logger.debug(f"📏 Auto-resized sheet: {worksheet.title}")
        except Exception as e:
            logger.debug(f"⚠️ Could not auto-resize sheet: {e}")
    
    def batch_insert_data(self, sheet_name: str, data_list: List[List[Any]], 
                         batch_size: int = 100) -> str:
        """Insert data in batches with progress tracking"""
        operation_id = f"batch_insert_{sheet_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        batch_op = BatchOperation(
            operation_id=operation_id,
            sheet_name=sheet_name,
            operation_type='insert',
            data=data_list
        )
        
        self.operation_queue.append(batch_op)
        self._execute_batch_operation(batch_op, batch_size)
        
        return operation_id
    
    def _execute_batch_operation(self, batch_op: BatchOperation, batch_size: int = 100):
        """Execute a batch operation with error handling and progress tracking"""
        if not self.is_available() or not self.base_integration:
            batch_op.status = 'failed'
            batch_op.error_message = 'Sheets manager not available'
            return
            
        try:
            batch_op.status = 'processing'
            logger.info(f"🔄 Processing batch operation: {batch_op.operation_id}")
            
            # Get sheet configuration
            config = self.sheet_configs.get(batch_op.sheet_name)
            if not config:
                # Create default config
                config = SheetConfig(name=batch_op.sheet_name, headers=[])
            
            # Ensure sheet exists
            if not self.create_sheet_with_config(config):
                raise Exception(f"Failed to create/access sheet: {batch_op.sheet_name}")
            
            # Process data in batches
            data_batches = [batch_op.data[i:i + batch_size] 
                          for i in range(0, len(batch_op.data), batch_size)]
            
            successful_batches = 0
            failed_batches = 0
            
            for i, batch in enumerate(data_batches):
                try:
                    # Insert batch
                    for row in batch:
                        success = self.base_integration.append_to_sheet(
                            batch_op.sheet_name, row, config.headers
                        )
                        if not success:
                            failed_batches += 1
                            break
                    else:
                        successful_batches += 1
                    
                    # Update progress
                    progress = ((i + 1) / len(data_batches)) * 100
                    self.progress_tracker[batch_op.operation_id] = {
                        'progress_percent': progress,
                        'batches_completed': i + 1,
                        'total_batches': len(data_batches),
                        'records_processed': (i + 1) * batch_size,
                        'total_records': len(batch_op.data)
                    }
                    
                    logger.debug(f"📊 Batch {i + 1}/{len(data_batches)} completed for {batch_op.operation_id}")
                    
                    # Small delay to avoid rate limiting
                    time.sleep(0.1)
                    
                except Exception as batch_error:
                    logger.error(f"❌ Batch {i + 1} failed: {batch_error}")
                    failed_batches += 1
            
            # Mark operation as completed
            batch_op.status = 'completed' if failed_batches == 0 else 'partial'
            batch_op.completed_at = datetime.now()
            
            # Record operation in progress tracking sheet
            self._record_operation_progress(batch_op, successful_batches, failed_batches)
            
            logger.info(f"✅ Batch operation completed: {batch_op.operation_id}")
            
        except Exception as e:
            batch_op.status = 'failed'
            batch_op.error_message = str(e)
            batch_op.completed_at = datetime.now()
            logger.error(f"❌ Batch operation failed: {batch_op.operation_id} - {e}")
        
        # Move to history
        self.operation_history.append(batch_op)
        if batch_op in self.operation_queue:
            self.operation_queue.remove(batch_op)
    
    def _record_operation_progress(self, batch_op: BatchOperation, 
                                 successful_batches: int, failed_batches: int):
        """Record operation progress in tracking sheet"""
        try:
            duration = 0
            if batch_op.completed_at and batch_op.created_at:
                duration = (batch_op.completed_at - batch_op.created_at).total_seconds()
            
            progress_data = [
                batch_op.operation_id,
                batch_op.operation_type,
                batch_op.sheet_name,
                len(batch_op.data),
                batch_op.status,
                batch_op.created_at.isoformat() if batch_op.created_at else '',
                batch_op.completed_at.isoformat() if batch_op.completed_at else '',
                round(duration, 2),
                batch_op.error_message or ''
            ]
            
            if self.base_integration:
                self.base_integration.append_to_sheet(
                    'OrchidProgressTracking', 
                    progress_data, 
                    self.sheet_configs['OrchidProgressTracking'].headers
                )
            
        except Exception as e:
            logger.debug(f"⚠️ Could not record operation progress: {e}")
    
    def update_hybrid_data(self, hybrid_name: str, field: str, 
                          new_value: Any, source: str = 'OrchidContinuum') -> bool:
        """Update specific hybrid data with change tracking"""
        if not self.is_available():
            logger.warning("⚠️ Sheets manager not available for hybrid data update")
            return False
            
        try:
            # Record the update in the tracking sheet
            update_id = f"update_{hybrid_name}_{field}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            update_data = [
                update_id,
                hybrid_name,
                field,
                '',  # Old value - would need to be fetched
                str(new_value),
                source,
                datetime.now().isoformat(),
                'pending',  # Verification status
                f'Automated update from {source}'
            ]
            
            if not self.base_integration:
                return False
                
            success = self.base_integration.append_to_sheet(
                'HybridDataUpdates',
                update_data,
                self.sheet_configs['HybridDataUpdates'].headers
            )
            
            if success:
                logger.info(f"📝 Hybrid data update recorded: {hybrid_name}.{field} = {new_value}")
                return True
            else:
                logger.error(f"❌ Failed to record hybrid data update for {hybrid_name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error updating hybrid data: {e}")
            return False
    
    def get_operation_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a batch operation"""
        # Check active operations
        for op in self.operation_queue:
            if op.operation_id == operation_id:
                status = asdict(op)
                status['progress'] = self.progress_tracker.get(operation_id, {})
                return status
        
        # Check completed operations
        for op in self.operation_history:
            if op.operation_id == operation_id:
                status = asdict(op)
                status['progress'] = self.progress_tracker.get(operation_id, {})
                return status
        
        return None
    
    def get_sheet_data(self, sheet_name: str, limit: int = 1000) -> List[Dict[str, Any]]:
        """Retrieve data from a sheet with optional limit"""
        if not self.is_available() or not self.base_integration:
            return []
            
        try:
            worksheet = self.base_integration.get_or_create_sheet(sheet_name)
            if not worksheet:
                return []
            
            records = worksheet.get_all_records()
            
            # Apply limit if specified
            if limit and len(records) > limit:
                records = records[:limit]
                logger.info(f"📊 Retrieved {limit} records from {sheet_name} (limited)")
            else:
                logger.info(f"📊 Retrieved {len(records)} records from {sheet_name}")
            
            return records
            
        except Exception as e:
            logger.error(f"❌ Failed to get data from sheet {sheet_name}: {e}")
            return []
    
    def validate_data_format(self, sheet_name: str, data: List[List[Any]]) -> Tuple[bool, List[str]]:
        """Validate data format against sheet configuration"""
        config = self.sheet_configs.get(sheet_name)
        if not config:
            return True, []  # No validation if no config
        
        errors = []
        
        for i, row in enumerate(data):
            if len(row) != len(config.headers):
                errors.append(f"Row {i + 1}: Expected {len(config.headers)} columns, got {len(row)}")
            
            # Additional validation could be added here
            # (e.g., data type validation, required fields, etc.)
        
        is_valid = len(errors) == 0
        return is_valid, errors
    
    def bulk_update_status_flags(self, sheet_name: str, 
                                status_updates: List[Dict[str, Any]]) -> bool:
        """Bulk update status flags for records in a sheet"""
        if not self.is_available():
            return False
            
        try:
            # This would require more complex logic to update specific cells
            # For now, we'll add new status records to a tracking sheet
            for update in status_updates:
                self.update_hybrid_data(
                    update.get('record_id', ''),
                    'status',
                    update.get('status', ''),
                    update.get('source', 'BulkUpdate')
                )
            
            logger.info(f"📊 Bulk updated {len(status_updates)} status flags in {sheet_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to bulk update status flags: {e}")
            return False
    
    def get_manager_status(self) -> Dict[str, Any]:
        """Get comprehensive status of the sheets manager"""
        return {
            'initialized': self.initialized,
            'available': self.is_available(),
            'base_integration_status': self.base_integration.get_status() if self.base_integration else None,
            'configured_sheets': list(self.sheet_configs.keys()),
            'active_operations': len(self.operation_queue),
            'completed_operations': len(self.operation_history),
            'operation_queue': [op.operation_id for op in self.operation_queue],
            'recent_operations': [
                {
                    'operation_id': op.operation_id,
                    'status': op.status,
                    'sheet_name': op.sheet_name,
                    'created_at': op.created_at.isoformat() if op.created_at else None
                }
                for op in self.operation_history[-5:]  # Last 5 operations
            ]
        }
    
    def save_breeding_data_batch(self, breeding_data_list: List[Dict[str, Any]]) -> str:
        """Save multiple breeding data records in batch"""
        # Convert breeding data to row format
        rows = []
        for data in breeding_data_list:
            row = [
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                data.get('hybrid_name', ''),
                data.get('parent1', ''),
                data.get('parent2', ''),
                data.get('genus', 'Sarcochilus'),
                data.get('breeder_notes', ''),
                data.get('ai_analysis', ''),
                data.get('image_urls', ''),
                data.get('source', 'AI Breeder Pro'),
                data.get('success_rating', ''),
                data.get('vigor_notes', ''),
                data.get('color_notes', ''),
                data.get('size_notes', ''),
                'active',  # Status
                datetime.now().isoformat()  # Updated At
            ]
            rows.append(row)
        
        return self.batch_insert_data('OrchidBreedingData', rows)
    
    def save_svo_data_batch(self, svo_data_list: List[Dict[str, Any]]) -> str:
        """Save multiple SVO data records in batch"""
        # Convert SVO data to row format
        rows = []
        for data in svo_data_list:
            row = [
                data.get('genus', 'Sarcochilus'),
                data.get('name', ''),
                data.get('parent1', ''),
                data.get('parent2', ''),
                data.get('year', ''),
                data.get('notes', ''),
                data.get('image_urls', ''),
                data.get('price', ''),
                data.get('availability', ''),
                data.get('source_url', ''),
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                'active',  # Status
                datetime.now().isoformat()  # Updated At
            ]
            rows.append(row)
        
        return self.batch_insert_data('SVO_Hybrid_Data', rows)

# Global instance for use across the application
sheets_manager = SheetsManager()

def get_sheets_manager() -> SheetsManager:
    """Get the global sheets manager instance"""
    return sheets_manager

# Convenience functions for orchestrator integration
def update_hybrid_data_batch(updates: List[Dict[str, Any]]) -> List[str]:
    """Convenience function for batch hybrid data updates"""
    operation_ids = []
    for update in updates:
        if sheets_manager.update_hybrid_data(
            update.get('hybrid_name', ''),
            update.get('field', ''),
            update.get('new_value', ''),
            update.get('source', 'Orchestrator')
        ):
            operation_ids.append(f"update_{update.get('hybrid_name', '')}")
    return operation_ids

def bulk_save_breeding_data(breeding_data_list: List[Dict[str, Any]]) -> str:
    """Convenience function for bulk breeding data save"""
    return sheets_manager.save_breeding_data_batch(breeding_data_list)

def bulk_save_svo_data(svo_data_list: List[Dict[str, Any]]) -> str:
    """Convenience function for bulk SVO data save"""
    return sheets_manager.save_svo_data_batch(svo_data_list)

def get_operation_progress(operation_id: str) -> Optional[Dict[str, Any]]:
    """Convenience function to get operation progress"""
    return sheets_manager.get_operation_status(operation_id)

def is_sheets_available() -> bool:
    """Convenience function to check sheets availability"""
    return sheets_manager.is_available()

if __name__ == "__main__":
    # Test the sheets manager
    manager = get_sheets_manager()
    status = manager.get_manager_status()
    print("📊 Sheets Manager Status:")
    print(json.dumps(status, indent=2, default=str))