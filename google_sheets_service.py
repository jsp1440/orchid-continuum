"""
Google Sheets Service for Orchid Continuum
Manages integration with Google Forms submissions and data processing
"""

import os
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import gspread
from google.auth import default
from google.oauth2.service_account import Credentials
import requests

logger = logging.getLogger(__name__)

class GoogleSheetsService:
    def __init__(self):
        self.client = None
        self.worksheet = None
        self.form_responses_sheet = None
        self.processed_submissions_sheet = None
        self.initialize_connection()
    
    def initialize_connection(self):
        """Initialize connection to Google Sheets"""
        try:
            # Try to get credentials from environment or service account
            if os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'):
                # Use service account credentials
                credentials_info = json.loads(os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'))
                credentials = Credentials.from_service_account_info(credentials_info)
                scoped_credentials = credentials.with_scopes([
                    'https://spreadsheets.google.com/feeds',
                    'https://www.googleapis.com/auth/drive'
                ])
                self.client = gspread.authorize(scoped_credentials)
            else:
                # For development, we'll use a mock connection
                logger.warning("No Google service account credentials found. Using mock connection for development.")
                self.client = None
                return
            
            logger.info("Google Sheets connection established successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets connection: {e}")
            self.client = None
    
    def get_form_submissions(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """Retrieve form submissions from Google Sheets"""
        if not self.client:
            return self._get_mock_submissions()
        
        try:
            # Open the spreadsheet by ID
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1  # Assuming first sheet contains form responses
            
            # Get all records
            records = worksheet.get_all_records()
            logger.info(f"Retrieved {len(records)} form submissions")
            
            return records
            
        except Exception as e:
            logger.error(f"Error retrieving form submissions: {e}")
            return []
    
    def _get_mock_submissions(self) -> List[Dict[str, Any]]:
        """Mock submissions for development/testing"""
        return [
            {
                'timestamp': '2025-08-22 22:00:00',
                'submitter_name': 'Development User',
                'submitter_email': 'dev@example.com',
                'orchid_name': 'Phalaenopsis amabilis',
                'genus': 'Phalaenopsis',
                'species': 'amabilis',
                'hybrid_name': '',
                'photo_url': 'https://example.com/photo1.jpg',
                'notes': 'Beautiful white orchid in bloom',
                'location_found': 'Home greenhouse',
                'bloom_season': 'Spring',
                'processed': 'No'
            }
        ]
    
    def mark_submission_processed(self, spreadsheet_id: str, row_number: int):
        """Mark a submission as processed in the Google Sheet"""
        if not self.client:
            logger.info(f"Mock: Marked row {row_number} as processed")
            return
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            worksheet = spreadsheet.sheet1
            
            # Update the 'processed' column (assuming it's the last column)
            worksheet.update_cell(row_number, worksheet.col_count, 'Yes')
            logger.info(f"Marked row {row_number} as processed")
            
        except Exception as e:
            logger.error(f"Error marking submission as processed: {e}")
    
    def save_enhanced_data(self, spreadsheet_id: str, enhanced_data: Dict[str, Any]):
        """Save enhanced/processed data back to Google Sheets"""
        if not self.client:
            logger.info(f"Mock: Saved enhanced data for {enhanced_data.get('orchid_name', 'Unknown')}")
            return
        
        try:
            spreadsheet = self.client.open_by_key(spreadsheet_id)
            
            # Try to get or create 'Enhanced Data' worksheet
            try:
                enhanced_sheet = spreadsheet.worksheet('Enhanced Data')
            except:
                enhanced_sheet = spreadsheet.add_worksheet('Enhanced Data', 1000, 20)
                # Add headers
                headers = [
                    'Original Submission ID', 'Timestamp', 'Submitter', 
                    'Validated Genus', 'Validated Species', 'Hybrid Name',
                    'Scientific Name', 'Common Names', 'Family',
                    'AI Confidence', 'Enhanced Metadata', 'Care Instructions',
                    'Cultural Requirements', 'Judging Score', 'Photo Analysis',
                    'Morphological Tags', 'Ecological Data', 'Processing Notes'
                ]
                enhanced_sheet.append_row(headers)
            
            # Prepare row data
            row_data = [
                enhanced_data.get('original_id', ''),
                datetime.now().isoformat(),
                enhanced_data.get('submitter', ''),
                enhanced_data.get('validated_genus', ''),
                enhanced_data.get('validated_species', ''),
                enhanced_data.get('hybrid_name', ''),
                enhanced_data.get('scientific_name', ''),
                enhanced_data.get('common_names', ''),
                enhanced_data.get('family', ''),
                enhanced_data.get('ai_confidence', ''),
                json.dumps(enhanced_data.get('metadata', {})),
                enhanced_data.get('care_instructions', ''),
                enhanced_data.get('cultural_requirements', ''),
                enhanced_data.get('judging_score', ''),
                enhanced_data.get('photo_analysis', ''),
                enhanced_data.get('morphological_tags', ''),
                enhanced_data.get('ecological_data', ''),
                enhanced_data.get('processing_notes', '')
            ]
            
            enhanced_sheet.append_row(row_data)
            logger.info(f"Saved enhanced data for {enhanced_data.get('orchid_name', 'Unknown')}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced data: {e}")
    
    def get_processing_queue(self, spreadsheet_id: str) -> List[Dict[str, Any]]:
        """Get submissions that need processing (marked as not processed)"""
        submissions = self.get_form_submissions(spreadsheet_id)
        unprocessed = [
            submission for submission in submissions 
            if submission.get('processed', '').lower() not in ['yes', 'true', '1']
        ]
        
        logger.info(f"Found {len(unprocessed)} unprocessed submissions")
        return unprocessed