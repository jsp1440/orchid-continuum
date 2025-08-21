import os
import logging
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.service_account import Credentials
import json

logger = logging.getLogger(__name__)

# Google Drive API configuration
SCOPES = ['https://www.googleapis.com/auth/drive.file']
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
