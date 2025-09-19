import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from google.oauth2.service_account import Credentials
import json
import tempfile
import requests
from PIL import Image
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive.readonly', 'https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_FILE = os.environ.get('GOOGLE_SERVICE_ACCOUNT_FILE')
DRIVE_FOLDER_ID = os.environ.get('GOOGLE_DRIVE_FOLDER_ID')

def get_drive_service():
    """Initialize Google Drive service"""
    try:
        if SERVICE_ACCOUNT_FILE:
            credentials = Credentials.from_service_account_file(
                SERVICE_ACCOUNT_FILE, scopes=SCOPES
            )
        else:
            # Try to get credentials from environment variable
            service_account_info = os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON')
            if service_account_info:
                credentials = Credentials.from_service_account_info(
                    json.loads(service_account_info), scopes=SCOPES
                )
            else:
                logger.warning("No Google Drive credentials found")
                return None
        
        service = build('drive', 'v3', credentials=credentials)
        return service
    except Exception as e:
        logger.error(f"Failed to initialize Google Drive service: {str(e)}")
        return None

def create_folder(service, folder_name, parent_folder_id=None):
    """Create a folder in Google Drive"""
    try:
        folder_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }
        
        if parent_folder_id:
            folder_metadata['parents'] = [parent_folder_id]
        
        folder = service.files().create(body=folder_metadata).execute()
        return folder.get('id')
    except Exception as e:
        logger.error(f"Failed to create folder {folder_name}: {str(e)}")
        return None

def upload_to_drive(file_path, filename, folder_name='Orchid_Quick_Images'):
    """Upload a file to Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            logger.warning("Google Drive service not available, skipping upload")
            return None
        
        # Check if folder exists or create it
        folder_id = get_or_create_folder(service, folder_name)
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id] if folder_id else []
        }
        
        media = MediaFileUpload(file_path)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        file_id = file.get('id')
        
        # Make file publicly viewable
        service.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        logger.info(f"Uploaded {filename} to Google Drive with ID: {file_id}")
        return file_id
        
    except Exception as e:
        logger.error(f"Failed to upload {filename} to Google Drive: {str(e)}")
        return None

def get_or_create_folder(service, folder_name, parent_id=None):
    """Get existing folder or create new one"""
    try:
        # Search for existing folder
        query = f"name='{folder_name}' and mimeType='application/vnd.google-apps.folder'"
        if parent_id:
            query += f" and '{parent_id}' in parents"
        
        results = service.files().list(q=query).execute()
        folders = results.get('files', [])
        
        if folders:
            return folders[0]['id']
        else:
            # Create new folder
            return create_folder(service, folder_name, parent_id)
    except Exception as e:
        logger.error(f"Failed to get or create folder {folder_name}: {str(e)}")
        return parent_id or DRIVE_FOLDER_ID

def get_drive_file_url(file_id):
    """Get public URL for a Google Drive file"""
    if file_id:
        return f"https://drive.google.com/uc?id={file_id}"
    return None

def setup_drive_folders():
    """Setup the required folder structure in Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return False
        
        # Create main OrchidContinuum folder
        main_folder_id = get_or_create_folder(service, 'OrchidContinuum_Central')
        
        # Create subfolders
        subfolders = [
            'TAXONOMY_MASTER',
            'Orchid_Quick_Images',
            'Legacy_Submissions',
            'Scraped_Content_Gary_Yong_Gee',
            'Scraped_Content_Roberta_Fox',
            'Processed_Metadata',
            'Widget_Outputs'
        ]
        
        for folder_name in subfolders:
            get_or_create_folder(service, folder_name, main_folder_id)
        
        logger.info("Google Drive folder structure created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to setup Google Drive folders: {str(e)}")
        return False

def get_folder_contents(folder_id: str) -> List[Dict[str, Any]]:
    """Get all files from a specific Google Drive folder"""
    try:
        service = get_drive_service()
        if not service:
            logger.warning("Google Drive service not available")
            return []
        
        # Search for files in the specified folder
        query = f"'{folder_id}' in parents and trashed=false"
        logger.info(f"🔍 Searching folder {folder_id} with query: {query}")
        
        results = service.files().list(
            q=query,
            fields="files(id, name, mimeType, size, createdTime, modifiedTime, webViewLink, thumbnailLink)",
            pageSize=1000
        ).execute()
        
        files = results.get('files', [])
        logger.info(f"Found {len(files)} files in Google Drive folder")
        
        # Filter for image files and organize data
        orchid_files = []
        for file in files:
            mime_type = file.get('mimeType', '')
            if mime_type.startswith('image/'):
                orchid_files.append({
                    'id': file.get('id'),
                    'name': file.get('name'),
                    'mime_type': mime_type,
                    'size': file.get('size'),
                    'created_time': file.get('createdTime'),
                    'modified_time': file.get('modifiedTime'),
                    'web_view_link': file.get('webViewLink'),
                    'thumbnail_link': file.get('thumbnailLink'),
                    'download_url': f"https://drive.google.com/uc?id={file.get('id')}&export=download"
                })
        
        logger.info(f"Found {len(orchid_files)} image files for import")
        return orchid_files
        
    except Exception as e:
        logger.error(f"Error getting folder contents: {str(e)}")
        return []

def import_orchid_from_drive_file(file_info: Dict[str, Any], target_folder_id: str = None) -> Dict[str, Any]:
    """Import a single orchid image from Google Drive file into the system"""
    try:
        service = get_drive_service()
        if not service:
            return {'success': False, 'error': 'Google Drive service not available'}
        
        file_id = file_info.get('id')
        filename = file_info.get('name', f'orchid_{file_id}.jpg')
        
        # Download the file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
            request = service.files().get_media(fileId=file_id)
            downloader = MediaIoBaseDownload(temp_file, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            temp_path = temp_file.name
        
        # Process the image
        try:
            with Image.open(temp_path) as img:
                # Convert to RGB if necessary
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Generate new filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"imported_drive_{timestamp}_{uuid.uuid4().hex[:8]}.jpg"
                
                # Save processed image
                processed_path = os.path.join('static', 'uploads', new_filename)
                os.makedirs(os.path.dirname(processed_path), exist_ok=True)
                img.save(processed_path, 'JPEG', quality=90)
                
                # Upload back to our organized Drive structure
                upload_result = None
                if target_folder_id:
                    upload_result = upload_to_drive(processed_path, new_filename, 'Imported_Orchids')
                
                # Extract potential orchid name from filename
                orchid_name = extract_orchid_name_from_filename(filename)
                
                return {
                    'success': True,
                    'original_file_id': file_id,
                    'original_filename': filename,
                    'processed_filename': new_filename,
                    'processed_path': processed_path,
                    'upload_file_id': upload_result,
                    'suggested_name': orchid_name,
                    'file_info': file_info
                }
                
        except Exception as img_error:
            logger.error(f"Error processing image {filename}: {str(img_error)}")
            return {'success': False, 'error': f'Image processing failed: {str(img_error)}'}
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
                
    except Exception as e:
        logger.error(f"Error importing file {file_info.get('name', 'unknown')}: {str(e)}")
        return {'success': False, 'error': str(e)}

def extract_orchid_name_from_filename(filename: str) -> str:
    """Extract potential orchid name from filename"""
    # Remove file extension
    name = os.path.splitext(filename)[0]
    
    # Remove common prefixes/suffixes
    name = name.replace('IMG_', '').replace('DSC_', '').replace('Photo_', '')
    
    # Replace underscores and hyphens with spaces
    name = name.replace('_', ' ').replace('-', ' ')
    
    # Remove numbers at the end (likely timestamps or sequence numbers)
    import re
    name = re.sub(r'\d+$', '', name).strip()
    
    # Capitalize words that look like genus/species names
    words = name.split()
    if len(words) >= 2:
        # Capitalize first two words (likely genus and species)
        words[0] = words[0].capitalize()
        words[1] = words[1].lower()
        name = ' '.join(words)
    
    return name.strip() if name.strip() else 'Unknown Orchid'

def batch_import_from_drive_folder(folder_id: str, limit: int = 50) -> Dict[str, Any]:
    """Import multiple orchid images from a Google Drive folder"""
    try:
        # Get folder contents
        files = get_folder_contents(folder_id)
        
        if not files:
            return {
                'success': False,
                'error': 'No image files found in the specified folder',
                'imported_count': 0,
                'results': []
            }
        
        # Limit the number of files to process
        files = files[:limit]
        
        results = []
        success_count = 0
        
        logger.info(f"Starting batch import of {len(files)} files from Drive folder {folder_id}")
        
        for i, file_info in enumerate(files):
            logger.info(f"Processing file {i+1}/{len(files)}: {file_info.get('name')}")
            
            try:
                import_result = import_orchid_from_drive_file(file_info)
                results.append(import_result)
                
                if import_result.get('success'):
                    success_count += 1
                    
            except Exception as e:
                logger.error(f"Error importing file {file_info.get('name')}: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'original_filename': file_info.get('name')
                })
        
        return {
            'success': True,
            'imported_count': success_count,
            'total_processed': len(files),
            'results': results
        }
        
    except Exception as e:
        logger.error(f"Error in batch import: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'imported_count': 0,
            'results': []
        }

def download_file(file_id, destination_path):
    """Download a file from Google Drive"""
    try:
        service = get_drive_service()
        if not service:
            return False
        
        request = service.files().get_media(fileId=file_id)
        with open(destination_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to download file {file_id}: {str(e)}")
        return False
