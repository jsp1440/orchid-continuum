#!/usr/bin/env python3
"""
🌤️ Google Drive Manager for Orchid Continuum
Enhanced Google Drive integration with orchestrator-compatible interface

This module provides comprehensive Google Drive functionality including:
- Authentication and service initialization
- File upload with folder organization
- Batch operations with progress tracking
- File management and URL generation
- Integration with existing Google Cloud credentials

Built on existing patterns from google_drive_service.py and google_cloud_integration.py
"""

import os
import json
import time
import logging
import tempfile
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Callable, Union
from io import BytesIO
from dataclasses import dataclass, asdict, field
from concurrent.futures import ThreadPoolExecutor, as_completed

# Import required Google libraries (no fallbacks - fail fast if missing)
try:
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload, MediaIoBaseUpload, MediaIoBaseDownload
    from google.oauth2.service_account import Credentials
    from PIL import Image
    import requests
    GOOGLE_LIBRARIES_AVAILABLE = True
except ImportError as e:
    error_msg = f"CRITICAL: Google libraries not available: {e}"
    logging.error(error_msg)
    logging.error("Google Drive functionality requires: google-api-python-client, google-auth, Pillow, requests")
    logging.error("Install with: pip install google-api-python-client google-auth Pillow requests")
    raise RuntimeError(error_msg)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class UploadProgress:
    """Progress tracking for uploads"""
    current: int = 0
    total: int = 0
    completed_files: List[str] = field(default_factory=list)
    failed_files: List[str] = field(default_factory=list)
    current_file: str = ""
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def progress_percent(self) -> float:
        return (self.current / self.total * 100) if self.total > 0 else 0
    
    @property
    def elapsed_time(self) -> float:
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def estimated_remaining(self) -> float:
        if self.current > 0:
            avg_time_per_file = self.elapsed_time / self.current
            return avg_time_per_file * (self.total - self.current)
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'current': self.current,
            'total': self.total,
            'progress_percent': self.progress_percent,
            'completed_files': self.completed_files,
            'failed_files': self.failed_files,
            'current_file': self.current_file,
            'elapsed_time': self.elapsed_time,
            'estimated_remaining': self.estimated_remaining
        }

@dataclass
class DriveFile:
    """Represents a file in Google Drive"""
    id: str
    name: str
    mime_type: str
    size: Optional[int] = None
    created_time: Optional[str] = None
    modified_time: Optional[str] = None
    web_view_link: Optional[str] = None
    download_url: Optional[str] = None
    thumbnail_link: Optional[str] = None
    parent_folders: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.download_url and self.id:
            self.download_url = f"https://drive.google.com/uc?id={self.id}"

class GDriveManager:
    """Enhanced Google Drive Manager with orchestrator-compatible interface"""
    
    def __init__(self):
        self.drive_service = None
        self.credentials = None
        self.folder_cache = {}
        self.upload_sessions = {}
        
        # Google Drive configuration with fallback to existing patterns
        self.scopes = [
            'https://www.googleapis.com/auth/drive',
            'https://www.googleapis.com/auth/drive.file'
        ]
        
        # Default folder structure for Orchid Continuum
        self.default_folders = {
            'main': 'OrchidContinuum_Central',
            'images': 'Orchid_Quick_Images',
            'taxonomy': 'TAXONOMY_MASTER',
            'legacy': 'Legacy_Submissions',
            'scraped_gary': 'Scraped_Content_Gary_Yong_Gee',
            'scraped_roberta': 'Scraped_Content_Roberta_Fox',
            'metadata': 'Processed_Metadata',
            'widgets': 'Widget_Outputs',
            'breeding': 'AI_Breeding_Data',
            'batch_uploads': 'Batch_Uploads',
            'edited_photos': 'Orchid_Edited_Photos',
            'imported': 'Imported_Orchids'
        }
        
        # Initialize the service
        self.initialize()
        
        logger.info("🌤️ GDrive Manager initialized")
    
    def initialize(self) -> bool:
        """Initialize Google Drive service using existing credential patterns"""
        # Google libraries are guaranteed available due to import validation above
        
        try:
            # Try multiple credential sources following existing patterns
            credentials = None
            
            # Method 1: Service account file (from google_drive_service.py pattern)
            service_account_file = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
            if service_account_file and os.path.exists(service_account_file):
                credentials = Credentials.from_service_account_file(
                    service_account_file, scopes=self.scopes
                )
                logger.info("🔑 Using service account file credentials")
            
            # Method 2: Service account JSON (from google_cloud_integration.py pattern)
            elif os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON'):
                service_account_json = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
                if service_account_json:
                    credentials_info = json.loads(service_account_json)
                    credentials = Credentials.from_service_account_info(
                        credentials_info, scopes=self.scopes
                    )
                logger.info("🔑 Using service account JSON credentials")
            
            if credentials:
                self.credentials = credentials
                self.drive_service = build('drive', 'v3', credentials=credentials)
                logger.info("✅ Google Drive service initialized successfully")
                
                # Setup default folder structure
                self.setup_folder_structure()
                return True
            else:
                logger.warning("⚠️ No Google Drive credentials found")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize Google Drive service: {e}")
            return False
    
    def is_available(self) -> bool:
        """Check if Google Drive service is available"""
        if self.drive_service is None:
            logger.error("❌ Google Drive service not initialized - check credentials and API access")
            return False
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of Google Drive manager"""
        return {
            'available': self.is_available(),
            'credentials_type': 'service_account' if self.credentials else None,
            'cached_folders': list(self.folder_cache.keys()),
            'active_upload_sessions': len(self.upload_sessions),
            'default_folders': self.default_folders
        }
    
    def setup_folder_structure(self) -> bool:
        """Setup the default folder structure in Google Drive"""
        if not self.is_available():
            logger.warning("⚠️ Drive service not available for folder setup")
            return False
        
        try:
            # Create or find main folder
            main_folder_id = self.get_or_create_folder(self.default_folders['main'])
            if not main_folder_id:
                logger.error("❌ Failed to create main folder")
                return False
            
            # Create subfolders
            for folder_key, folder_name in self.default_folders.items():
                if folder_key != 'main':  # Skip main folder
                    folder_id = self.get_or_create_folder(folder_name, main_folder_id)
                    if folder_id:
                        self.folder_cache[folder_key] = folder_id
                        logger.debug(f"📁 Setup folder: {folder_name} -> {folder_id}")
            
            logger.info("✅ Google Drive folder structure setup complete")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to setup folder structure: {e}")
            return False
    
    def get_or_create_folder(self, folder_name: str, parent_id: str = None) -> Optional[str]:
        """Get existing folder or create new one"""
        if not self.is_available():
            return None
        
        try:
            # Check cache first
            cache_key = f"{folder_name}_{parent_id or 'root'}"
            if cache_key in self.folder_cache:
                return self.folder_cache[cache_key]
            
            # Search for existing folder
            query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
            if parent_id:
                query += f" and '{parent_id}' in parents"
            
            results = self.drive_service.files().list(q=query).execute()
            folders = results.get('files', [])
            
            if folders:
                folder_id = folders[0]['id']
                self.folder_cache[cache_key] = folder_id
                return folder_id
            
            # Create new folder
            folder_metadata = {
                'name': folder_name,
                'mimeType': 'application/vnd.google-apps.folder'
            }
            
            if parent_id:
                folder_metadata['parents'] = [parent_id]
            
            folder = self.drive_service.files().create(body=folder_metadata).execute()
            folder_id = folder.get('id')
            
            # Cache the result
            self.folder_cache[cache_key] = folder_id
            
            logger.info(f"📁 Created folder: {folder_name} -> {folder_id}")
            return folder_id
            
        except Exception as e:
            logger.error(f"❌ Failed to get/create folder {folder_name}: {e}")
            return None
    
    def upload_file(self, file_path: str, filename: str = None, folder_key: str = 'images', 
                   make_public: bool = True, description: str = None) -> Optional[str]:
        """Upload a single file to Google Drive"""
        if not self.is_available():
            logger.warning("⚠️ Drive service not available for upload")
            return None
        
        try:
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return None
            
            # Use provided filename or extract from path
            if not filename:
                filename = os.path.basename(file_path)
            
            # Get folder ID
            folder_id = self.folder_cache.get(folder_key)
            if not folder_id:
                folder_name = self.default_folders.get(folder_key, 'Orchid_Quick_Images')
                folder_id = self.get_or_create_folder(folder_name)
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            if description:
                file_metadata['description'] = description
            
            # Upload file
            media = MediaFileUpload(file_path)
            file = self.drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            file_id = file.get('id')
            
            # Make file publicly viewable if requested
            if make_public:
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body={
                        'role': 'reader', 
                        'type': 'anyone',
                        'allowFileDiscovery': False
                    }
                ).execute()
            
            logger.info(f"📤 Uploaded: {filename} -> {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {filename}: {e}")
            return None
    
    def upload_bytes(self, data: bytes, filename: str, folder_key: str = 'images',
                    mime_type: str = 'image/jpeg', make_public: bool = True,
                    description: str = None) -> Optional[str]:
        """Upload bytes data to Google Drive"""
        if not self.is_available():
            return None
        
        try:
            # Get folder ID
            folder_id = self.folder_cache.get(folder_key)
            if not folder_id:
                folder_name = self.default_folders.get(folder_key, 'Orchid_Quick_Images')
                folder_id = self.get_or_create_folder(folder_name)
            
            # Prepare file metadata
            file_metadata = {
                'name': filename,
                'parents': [folder_id] if folder_id else []
            }
            
            if description:
                file_metadata['description'] = f"Orchid Continuum - {description} - Uploaded: {datetime.now().isoformat()}"
            
            # Create media upload from bytes
            media = MediaIoBaseUpload(
                BytesIO(data),
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
            
            # Make file publicly viewable
            if make_public:
                self.drive_service.permissions().create(
                    fileId=file_id,
                    body={
                        'role': 'reader',
                        'type': 'anyone',
                        'allowFileDiscovery': False
                    }
                ).execute()
            
            logger.info(f"📤 Uploaded bytes: {filename} -> {file_id}")
            return file_id
            
        except Exception as e:
            logger.error(f"❌ Failed to upload bytes {filename}: {e}")
            return None
    
    def download_and_upload(self, image_url: str, filename: str = None, 
                           folder_key: str = 'images') -> Optional[str]:
        """Download image from URL and upload to Google Drive"""
        try:
            response = requests.get(image_url, timeout=15)
            response.raise_for_status()
            
            if not filename:
                # Extract filename from URL or generate one
                filename = os.path.basename(image_url.split('?')[0])
                if not filename or '.' not in filename:
                    filename = f"downloaded_{uuid.uuid4().hex[:8]}.jpg"
            
            return self.upload_bytes(
                response.content, 
                filename, 
                folder_key,
                description=f"Downloaded from {image_url}"
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to download and upload from {image_url}: {e}")
            return None
    
    def batch_upload(self, file_paths: List[str], folder_key: str = 'batch_uploads',
                    progress_callback: Optional[Callable[[UploadProgress], None]] = None,
                    max_workers: int = 3) -> Dict[str, Any]:
        """Upload multiple files with progress tracking"""
        session_id = str(uuid.uuid4())
        progress = UploadProgress(total=len(file_paths))
        self.upload_sessions[session_id] = progress
        
        def update_progress():
            if progress_callback:
                progress_callback(progress)
        
        results = {
            'session_id': session_id,
            'success_count': 0,
            'failed_count': 0,
            'uploaded_files': {},
            'failed_files': {},
            'progress': progress.to_dict()
        }
        
        try:
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submit upload tasks
                future_to_path = {}
                for file_path in file_paths:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        future = executor.submit(self.upload_file, file_path, filename, folder_key)
                        future_to_path[future] = file_path
                    else:
                        progress.failed_files.append(file_path)
                        results['failed_files'][file_path] = "File not found"
                        results['failed_count'] += 1
                
                # Process completed uploads
                for future in as_completed(future_to_path):
                    file_path = future_to_path[future]
                    progress.current_file = os.path.basename(file_path)
                    
                    try:
                        file_id = future.result()
                        if file_id:
                            progress.completed_files.append(file_path)
                            results['uploaded_files'][file_path] = {
                                'file_id': file_id,
                                'url': self.get_file_url(file_id)
                            }
                            results['success_count'] += 1
                        else:
                            progress.failed_files.append(file_path)
                            results['failed_files'][file_path] = "Upload failed"
                            results['failed_count'] += 1
                    except Exception as e:
                        progress.failed_files.append(file_path)
                        results['failed_files'][file_path] = str(e)
                        results['failed_count'] += 1
                    
                    progress.current += 1
                    update_progress()
            
            progress.current_file = ""
            results['progress'] = progress.to_dict()
            
            logger.info(f"✅ Batch upload completed: {results['success_count']}/{len(file_paths)} successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Batch upload failed: {e}")
            results['error'] = str(e)
            return results
        finally:
            # Clean up session after some time
            if session_id in self.upload_sessions:
                del self.upload_sessions[session_id]
    
    def get_upload_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get progress of an ongoing upload session"""
        progress = self.upload_sessions.get(session_id)
        return progress.to_dict() if progress else None
    
    def get_file_url(self, file_id: str) -> Optional[str]:
        """Get public URL for a Google Drive file"""
        return f"https://drive.google.com/uc?id={file_id}" if file_id else None
    
    def get_file_info(self, file_id: str) -> Optional[DriveFile]:
        """Get detailed information about a file"""
        if not self.is_available():
            return None
        
        try:
            file_info = self.drive_service.files().get(
                fileId=file_id,
                fields='id,name,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink,parents'
            ).execute()
            
            return DriveFile(
                id=file_info.get('id'),
                name=file_info.get('name'),
                mime_type=file_info.get('mimeType'),
                size=int(file_info.get('size', 0)) if file_info.get('size') else None,
                created_time=file_info.get('createdTime'),
                modified_time=file_info.get('modifiedTime'),
                web_view_link=file_info.get('webViewLink'),
                thumbnail_link=file_info.get('thumbnailLink'),
                parent_folders=file_info.get('parents', [])
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get file info for {file_id}: {e}")
            return None
    
    def list_folder_contents(self, folder_key: str = 'images', 
                           file_type: str = 'image') -> List[DriveFile]:
        """List contents of a folder"""
        if not self.is_available():
            return []
        
        try:
            folder_id = self.folder_cache.get(folder_key)
            if not folder_id:
                folder_name = self.default_folders.get(folder_key, 'Orchid_Quick_Images')
                folder_id = self.get_or_create_folder(folder_name)
            
            if not folder_id:
                return []
            
            # Build query
            query = f"'{folder_id}' in parents and trashed=false"
            if file_type:
                query += f" and mimeType contains '{file_type}'"
            
            results = self.drive_service.files().list(
                q=query,
                fields="files(id,name,mimeType,size,createdTime,modifiedTime,webViewLink,thumbnailLink)",
                pageSize=1000
            ).execute()
            
            files = []
            for file_info in results.get('files', []):
                files.append(DriveFile(
                    id=file_info.get('id'),
                    name=file_info.get('name'),
                    mime_type=file_info.get('mimeType'),
                    size=int(file_info.get('size', 0)) if file_info.get('size') else None,
                    created_time=file_info.get('createdTime'),
                    modified_time=file_info.get('modifiedTime'),
                    web_view_link=file_info.get('webViewLink'),
                    thumbnail_link=file_info.get('thumbnailLink')
                ))
            
            logger.info(f"📁 Found {len(files)} files in folder {folder_key}")
            return files
            
        except Exception as e:
            logger.error(f"❌ Failed to list folder contents: {e}")
            return []
    
    def delete_file(self, file_id: str) -> bool:
        """Delete a file from Google Drive"""
        if not self.is_available():
            return False
        
        try:
            self.drive_service.files().delete(fileId=file_id).execute()
            logger.info(f"🗑️ Deleted file: {file_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to delete file {file_id}: {e}")
            return False
    
    def download_file(self, file_id: str, destination_path: str) -> bool:
        """Download a file from Google Drive"""
        if not self.is_available():
            return False
        
        try:
            request = self.drive_service.files().get_media(fileId=file_id)
            
            with open(destination_path, 'wb') as f:
                downloader = MediaIoBaseDownload(f, request)
                done = False
                while done is False:
                    status, done = downloader.next_chunk()
            
            logger.info(f"📥 Downloaded file {file_id} to {destination_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to download file {file_id}: {e}")
            return False
    
    def create_shared_folder(self, folder_name: str, parent_key: Optional[str] = None) -> Optional[str]:
        """Create a new shared folder"""
        parent_id = None
        if parent_key:
            parent_id = self.folder_cache.get(parent_key)
            if not parent_id:
                parent_folder_name = self.default_folders.get(parent_key)
                if parent_folder_name:
                    parent_id = self.get_or_create_folder(parent_folder_name)
        
        return self.get_or_create_folder(folder_name, parent_id)
    
    def get_folder_id(self, folder_key: str) -> Optional[str]:
        """Get folder ID by key"""
        return self.folder_cache.get(folder_key)

# Global instance for use across the application
drive_manager = GDriveManager()

def get_drive_manager() -> GDriveManager:
    """Get the global Drive manager instance"""
    return drive_manager

# Orchestrator-compatible convenience functions
def upload_file_to_drive(file_path: str, filename: Optional[str] = None, 
                        folder_key: str = 'images') -> Optional[str]:
    """Upload file to Google Drive - orchestrator compatible"""
    return drive_manager.upload_file(file_path, filename, folder_key)

def upload_image_bytes_to_drive(image_data: bytes, filename: str,
                              folder_key: str = 'images') -> Optional[str]:
    """Upload image bytes to Google Drive - orchestrator compatible"""
    return drive_manager.upload_bytes(image_data, filename, folder_key)

def download_and_upload_to_drive(image_url: str, filename: Optional[str] = None,
                               folder_key: str = 'images') -> Optional[str]:
    """Download and upload to Google Drive - orchestrator compatible"""
    return drive_manager.download_and_upload(image_url, filename, folder_key)

def batch_upload_to_drive(file_paths: List[str], folder_key: str = 'batch_uploads',
                         progress_callback: Optional[Callable[[UploadProgress], None]] = None) -> Dict[str, Any]:
    """Batch upload files to Google Drive - orchestrator compatible"""
    return drive_manager.batch_upload(file_paths, folder_key, progress_callback)

def get_drive_file_url(file_id: str) -> Optional[str]:
    """Get Google Drive file URL - orchestrator compatible"""
    return drive_manager.get_file_url(file_id)

def get_drive_status() -> Dict[str, Any]:
    """Get Google Drive manager status - orchestrator compatible"""
    return drive_manager.get_status()

def create_drive_folder(folder_name: str, parent_key: Optional[str] = None) -> Optional[str]:
    """Create folder in Google Drive - orchestrator compatible"""
    return drive_manager.create_shared_folder(folder_name, parent_key)

# Legacy compatibility functions for existing codebase
def upload_to_drive(file_path: str, filename: str, folder_name: str = 'Orchid_Quick_Images') -> Optional[str]:
    """Legacy compatibility function for existing codebase"""
    # Map folder names to keys for backward compatibility
    folder_mapping = {
        'Orchid_Quick_Images': 'images',
        'Batch_Uploads': 'batch_uploads',
        'Imported_Orchids': 'imported',
        'Orchid_Edited_Photos': 'edited_photos',
        'AI_Breeding_Data': 'breeding',
        'TAXONOMY_MASTER': 'taxonomy'
    }
    
    folder_key = folder_mapping.get(folder_name, 'images')
    return drive_manager.upload_file(file_path, filename, folder_key)

if __name__ == "__main__":
    # Test the drive manager
    manager = get_drive_manager()
    status = manager.get_status()
    print(f"🌤️ Google Drive Manager Status: {json.dumps(status, indent=2)}")