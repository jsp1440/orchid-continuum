#!/usr/bin/env python3
"""
🌤️ Google Cloud Integration for Orchid Continuum
Provides unified Google Sheets and Google Drive integration for AI Breeder Pro and SVO systems
Enhanced from orchid_continuum.py script functionality
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from io import BytesIO
from PIL import Image
import requests

try:
    import gspread
    from google.oauth2.service_account import Credentials
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseUpload
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError as e:
    GOOGLE_LIBRARIES_AVAILABLE = False
    logging.warning(f"⚠️ Google libraries not available: {e}")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleCloudIntegration:
    """Unified Google Sheets and Drive integration for Orchid Continuum systems"""
    
    def __init__(self):
        self.sheets_client = None
        self.drive_service = None
        self.credentials = None
        self.sheets_cache = {}
        self.drive_folder_id = None
        
        # Google Cloud configuration from environment
        self.scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Initialize services
        self.initialize_services()
        
        logger.info("🌤️ Google Cloud Integration initialized")
    
    def initialize_services(self):
        """Initialize Google Sheets and Drive services from environment variables"""
        if not GOOGLE_LIBRARIES_AVAILABLE:
            logger.warning("⚠️ Google libraries not available - cloud integration disabled")
            return False
            
        try:
            # Get service account credentials from environment
            service_account_json = os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_json:
                credentials_info = json.loads(service_account_json)
                self.credentials = Credentials.from_service_account_info(
                    credentials_info, 
                    scopes=self.scopes
                )
                
                # Initialize Google Sheets client
                self.sheets_client = gspread.authorize(self.credentials)
                
                # Initialize Google Drive service
                self.drive_service = build('drive', 'v3', credentials=self.credentials)
                
                # Get Drive folder ID from environment
                self.drive_folder_id = os.getenv('GOOGLE_DRIVE_FOLDER_ID')
                
                logger.info("✅ Google Cloud services initialized successfully")
                return True
            else:
                logger.warning("⚠️ GOOGLE_SERVICE_ACCOUNT_JSON not found - using local storage only")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Cloud services: {e}")
            return False
    
    def get_or_create_sheet(self, sheet_name: str, headers: List[str] = None) -> Optional[Any]:
        """Get existing sheet or create new one with headers"""
        if not self.sheets_client:
            logger.warning("⚠️ Google Sheets not available - skipping sheet operations")
            return None
            
        try:
            # Check cache first
            if sheet_name in self.sheets_cache:
                return self.sheets_cache[sheet_name]
            
            # Try to open existing sheet
            try:
                spreadsheet = self.sheets_client.open(sheet_name)
                worksheet = spreadsheet.sheet1
                logger.info(f"📊 Opened existing sheet: {sheet_name}")
            except gspread.SpreadsheetNotFound:
                # Create new sheet
                spreadsheet = self.sheets_client.create(sheet_name)
                worksheet = spreadsheet.sheet1
                
                # Add headers if provided
                if headers:
                    worksheet.append_row(headers)
                    logger.info(f"📊 Created new sheet: {sheet_name} with headers")
                else:
                    logger.info(f"📊 Created new sheet: {sheet_name}")
            
            # Cache the worksheet
            self.sheets_cache[sheet_name] = worksheet
            return worksheet
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create sheet {sheet_name}: {e}")
            return None
    
    def append_to_sheet(self, sheet_name: str, data: List[Any], headers: List[str] = None) -> bool:
        """Append data to Google Sheet"""
        worksheet = self.get_or_create_sheet(sheet_name, headers)
        if not worksheet:
            return False
            
        try:
            worksheet.append_row(data)
            logger.info(f"📝 Appended data to sheet: {sheet_name}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to append to sheet {sheet_name}: {e}")
            return False
    
    def upload_image_to_drive(self, image_data: bytes, filename: str, mime_type: str = 'image/jpeg') -> Optional[str]:
        """Upload image to Google Drive and return public URL"""
        if not self.drive_service or not self.drive_folder_id:
            logger.warning("⚠️ Google Drive not available - skipping image upload")
            return None
            
        try:
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [self.drive_folder_id]
            }
            
            # Create media upload
            media = MediaIoBaseUpload(
                BytesIO(image_data),
                mimetype=mime_type,
                resumable=True
            )
            
            # Upload file
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Set secure file permissions - Restricted access with link sharing
            self.drive_service.permissions().create(
                fileId=file_id,
                body={
                    'role': 'reader', 
                    'type': 'anyone',
                    'allowFileDiscovery': False  # Prevent discovery through search
                }
            ).execute()
            
            # Add additional security metadata
            self.drive_service.files().update(
                fileId=file_id,
                body={
                    'description': f'Orchid Continuum image - Uploaded: {datetime.now().isoformat()}'
                }
            ).execute()
            
            # Return public URL
            public_url = f"https://drive.google.com/uc?id={file_id}"
            logger.info(f"📸 Uploaded image to Drive: {filename} -> {public_url}")
            return public_url
            
        except Exception as e:
            logger.error(f"❌ Failed to upload image to Drive: {e}")
            return None
    
    def upload_local_image_to_drive(self, local_path: str, drive_filename: str = None) -> Optional[str]:
        """Upload local image file to Google Drive"""
        if not os.path.exists(local_path):
            logger.error(f"❌ Local image file not found: {local_path}")
            return None
            
        try:
            with open(local_path, 'rb') as f:
                image_data = f.read()
            
            if not drive_filename:
                drive_filename = os.path.basename(local_path)
            
            # Determine MIME type
            mime_type = 'image/jpeg'
            if local_path.lower().endswith('.png'):
                mime_type = 'image/png'
            elif local_path.lower().endswith('.gif'):
                mime_type = 'image/gif'
            
            return self.upload_image_to_drive(image_data, drive_filename, mime_type)
            
        except Exception as e:
            logger.error(f"❌ Failed to upload local image: {e}")
            return None
    
    def download_and_upload_image(self, image_url: str, filename: str) -> Optional[str]:
        """Download image from URL and upload to Google Drive"""
        try:
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            return self.upload_image_to_drive(response.content, filename)
            
        except Exception as e:
            logger.error(f"❌ Failed to download and upload image from {image_url}: {e}")
            return None
    
    def save_breeding_data(self, breeding_data: Dict[str, Any]) -> bool:
        """Save breeding data to Google Sheets with standardized format"""
        sheet_name = "OrchidBreedingData"
        headers = [
            "Date", "Hybrid Name", "Parent1", "Parent2", "Genus", 
            "Breeder Notes", "AI Analysis", "Image URLs", "Source", 
            "Success Rating", "Vigor Notes", "Color Notes", "Size Notes"
        ]
        
        # Prepare data row
        data_row = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            breeding_data.get('hybrid_name', ''),
            breeding_data.get('parent1', ''),
            breeding_data.get('parent2', ''),
            breeding_data.get('genus', 'Sarcochilus'),
            breeding_data.get('breeder_notes', ''),
            breeding_data.get('ai_analysis', ''),
            breeding_data.get('image_urls', ''),
            breeding_data.get('source', 'AI Breeder Pro'),
            breeding_data.get('success_rating', ''),
            breeding_data.get('vigor_notes', ''),
            breeding_data.get('color_notes', ''),
            breeding_data.get('size_notes', '')
        ]
        
        return self.append_to_sheet(sheet_name, data_row, headers)
    
    def save_svo_data(self, svo_data: Dict[str, Any]) -> bool:
        """Save SVO scraper data to Google Sheets"""
        sheet_name = "SVO_Hybrid_Data"
        headers = [
            "Genus", "Hybrid Name", "Parent1", "Parent2", "Year", 
            "Breeder Notes", "Image URLs", "Price", "Availability", 
            "Source URL", "Scraped At"
        ]
        
        # Prepare data row
        data_row = [
            svo_data.get('genus', 'Sarcochilus'),
            svo_data.get('name', ''),
            svo_data.get('parent1', ''),
            svo_data.get('parent2', ''),
            svo_data.get('year', ''),
            svo_data.get('notes', ''),
            svo_data.get('image_urls', ''),
            svo_data.get('price', ''),
            svo_data.get('availability', ''),
            svo_data.get('source_url', ''),
            datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ]
        
        return self.append_to_sheet(sheet_name, data_row, headers)
    
    def get_breeding_history(self, hybrid_name: str = None) -> List[Dict[str, Any]]:
        """Get breeding history from Google Sheets"""
        if not self.sheets_client:
            return []
            
        try:
            worksheet = self.get_or_create_sheet("OrchidBreedingData")
            if not worksheet:
                return []
            
            records = worksheet.get_all_records()
            
            if hybrid_name:
                # Filter by hybrid name
                records = [r for r in records if hybrid_name.lower() in r.get('Hybrid Name', '').lower()]
            
            logger.info(f"📊 Retrieved {len(records)} breeding records from Google Sheets")
            return records
            
        except Exception as e:
            logger.error(f"❌ Failed to get breeding history: {e}")
            return []
    
    def is_available(self) -> bool:
        """Check if Google Cloud integration is available"""
        return self.sheets_client is not None and self.drive_service is not None
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of Google Cloud integration"""
        return {
            'available': self.is_available(),
            'sheets_client': self.sheets_client is not None,
            'drive_service': self.drive_service is not None,
            'drive_folder_id': self.drive_folder_id,
            'cached_sheets': list(self.sheets_cache.keys())
        }

# Global instance for use across the application
google_integration = GoogleCloudIntegration()

def get_google_integration() -> GoogleCloudIntegration:
    """Get the global Google integration instance"""
    return google_integration

# Convenience functions for direct usage
def upload_image_to_google_drive(image_data: bytes, filename: str) -> Optional[str]:
    """Convenience function to upload image to Google Drive"""
    return google_integration.upload_image_to_drive(image_data, filename)

def save_breeding_analysis_to_sheets(breeding_data: Dict[str, Any]) -> bool:
    """Convenience function to save breeding analysis to Google Sheets"""
    return google_integration.save_breeding_data(breeding_data)

def save_svo_data_to_sheets(svo_data: Dict[str, Any]) -> bool:
    """Convenience function to save SVO data to Google Sheets"""
    return google_integration.save_svo_data(svo_data)