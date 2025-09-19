"""
Batch upload processing utilities
"""
import os
import zipfile
import shutil
import tempfile
from typing import List, Dict, Tuple
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from PIL import Image
import logging

from models import db, BatchUpload, UserUpload, OrchidRecord
from filename_parser import parse_orchid_filename
from orchid_ai import analyze_orchid_image
from google_drive_service import upload_to_drive

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'webp'}
ALLOWED_ARCHIVE_EXTENSIONS = {'zip', 'rar', '7z', 'tar', 'tar.gz'}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB per file
MAX_BATCH_SIZE = 500 * 1024 * 1024  # 500MB per batch
MAX_FILES_PER_BATCH = 100

def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def allowed_archive(filename: str) -> bool:
    """Check if archive file is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_ARCHIVE_EXTENSIONS

class BatchUploadProcessor:
    """Process batch uploads with filename parsing and AI analysis"""
    
    def __init__(self, user_id: int = None, session_id: str = None):
        self.user_id = user_id
        self.session_id = session_id
        self.batch_upload = None
        self.temp_dir = None
        self.processing_log = []
        
    def process_batch(self, files: List[FileStorage], user_notes: str = None) -> Dict:
        """
        Process a batch of uploaded files
        
        Args:
            files: List of FileStorage objects
            user_notes: Optional notes from user
            
        Returns:
            Dict with processing results
        """
        try:
            # Create batch record
            self.batch_upload = BatchUpload(
                user_id=self.user_id,
                session_id=self.session_id,
                total_files=len(files)
            )
            db.session.add(self.batch_upload)
            db.session.commit()
            
            self.log_message(f"Started batch upload {self.batch_upload.batch_id} with {len(files)} files")
            
            # Create temporary directory
            self.temp_dir = tempfile.mkdtemp(prefix=f"batch_{self.batch_upload.batch_id}_")
            
            # Process files
            results = self._process_files(files, user_notes)
            
            # Update batch status
            self.batch_upload.status = 'completed' if results['successful_files'] > 0 else 'failed'
            self.batch_upload.processed_files = results['processed_files']
            self.batch_upload.successful_files = results['successful_files']
            self.batch_upload.failed_files = results['failed_files']
            self.batch_upload.processing_log = str(self.processing_log)
            self.batch_upload.completed_at = db.func.now()
            
            db.session.commit()
            
            return results
            
        except Exception as e:
            logger.error(f"Batch upload failed: {str(e)}")
            if self.batch_upload:
                self.batch_upload.status = 'failed'
                self.batch_upload.processing_log = str(self.processing_log + [f"Fatal error: {str(e)}"])
                db.session.commit()
            
            return {
                'success': False,
                'error': str(e),
                'batch_id': self.batch_upload.batch_id if self.batch_upload else None
            }
        
        finally:
            # Clean up temporary directory
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _process_files(self, files: List[FileStorage], user_notes: str) -> Dict:
        """Process individual files in the batch"""
        results = {
            'success': True,
            'batch_id': self.batch_upload.batch_id,
            'processed_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'uploads': [],
            'errors': []
        }
        
        for file in files:
            if not file or not file.filename:
                continue
            
            try:
                upload_result = self._process_single_file(file, user_notes)
                results['uploads'].append(upload_result)
                results['processed_files'] += 1
                
                if upload_result.get('success'):
                    results['successful_files'] += 1
                else:
                    results['failed_files'] += 1
                    if upload_result.get('error'):
                        results['errors'].append({
                            'filename': file.filename,
                            'error': upload_result['error']
                        })
                        
            except Exception as e:
                error_msg = f"Error processing {file.filename}: {str(e)}"
                logger.error(error_msg)
                results['errors'].append({
                    'filename': file.filename,
                    'error': str(e)
                })
                results['failed_files'] += 1
                results['processed_files'] += 1
        
        return results
    
    def _process_single_file(self, file: FileStorage, user_notes: str) -> Dict:
        """Process a single uploaded file"""
        original_filename = file.filename
        
        # Validate file
        if not allowed_file(original_filename):
            return {
                'success': False,
                'filename': original_filename,
                'error': 'File type not allowed'
            }
        
        # Check file size
        file.seek(0, 2)  # Seek to end
        file_size = file.tell()
        file.seek(0)  # Reset
        
        if file_size > MAX_FILE_SIZE:
            return {
                'success': False,
                'filename': original_filename,
                'error': f'File too large ({file_size/1024/1024:.1f}MB > {MAX_FILE_SIZE/1024/1024}MB)'
            }
        
        # Create upload record
        user_upload = UserUpload(
            user_id=self.user_id,
            batch_id=self.batch_upload.id,
            original_filename=original_filename,
            uploaded_filename='',  # Will be set later
            file_size=file_size,
            mime_type=file.mimetype,
            user_notes=user_notes,
            processing_status='processing'
        )
        
        try:
            # Parse filename for orchid information
            parsed_info = parse_orchid_filename(original_filename)
            user_upload.parsed_genus = parsed_info.get('genus')
            user_upload.parsed_species = parsed_info.get('species')
            user_upload.parsed_variety = parsed_info.get('variety')
            user_upload.filename_confidence = parsed_info.get('confidence', 0.0)
            
            self.log_message(f"Parsed {original_filename}: {parsed_info}")
            
            # Save file temporarily
            temp_path = os.path.join(self.temp_dir, secure_filename(original_filename))
            file.save(temp_path)
            
            # Validate image
            try:
                with Image.open(temp_path) as img:
                    img.verify()
            except Exception:
                return {
                    'success': False,
                    'filename': original_filename,
                    'error': 'Invalid image file'
                }
            
            # Generate new filename
            file_ext = original_filename.rsplit('.', 1)[1].lower()
            new_filename = f"batch_{self.batch_upload.batch_id}_{user_upload.plant_id}.{file_ext}"
            user_upload.uploaded_filename = new_filename
            
            # Upload to Google Drive
            try:
                drive_folder = 'Batch_Uploads'
                drive_file_id = upload_to_drive(temp_path, new_filename, drive_folder)
                
                if not drive_file_id:
                    return {
                        'success': False,
                        'filename': original_filename,
                        'error': 'Failed to upload to Google Drive'
                    }
            except Exception as e:
                logger.warning(f"Google Drive upload failed for {original_filename}: {str(e)}")
                drive_file_id = None
            
            # Create orchid record
            orchid_record = OrchidRecord(
                user_id=self.user_id,
                display_name=parsed_info.get('genus', 'Unknown') + ' ' + (parsed_info.get('species', '') or parsed_info.get('hybrid_name', 'sp.')),
                scientific_name=self._format_scientific_name(parsed_info),
                genus=parsed_info.get('genus'),
                species=parsed_info.get('species'),
                image_filename=new_filename,
                google_drive_id=drive_file_id,
                ingestion_source='batch_upload',
                validation_status='pending'
            )
            
            # AI analysis (if OpenAI key is available)
            try:
                ai_result = analyze_orchid_image(temp_path)
                if ai_result and ai_result.get('success'):
                    ai_data = ai_result.get('data', {})
                    orchid_record.ai_description = ai_data.get('description')
                    orchid_record.ai_confidence = ai_data.get('confidence')
                    orchid_record.ai_extracted_metadata = str(ai_data)
                    
                    # Update with AI findings if filename parsing was weak
                    if parsed_info.get('confidence', 0) < 0.5 and ai_data.get('scientific_name'):
                        orchid_record.scientific_name = ai_data.get('scientific_name')
                        orchid_record.genus = ai_data.get('genus')
                        orchid_record.species = ai_data.get('species')
                        
            except Exception as e:
                logger.warning(f"AI analysis failed for {original_filename}: {str(e)}")
            
            # Save to database
            db.session.add(orchid_record)
            db.session.flush()  # Get the ID
            
            user_upload.orchid_id = orchid_record.id
            user_upload.processing_status = 'completed'
            user_upload.processed_at = db.func.now()
            
            db.session.add(user_upload)
            db.session.commit()
            
            return {
                'success': True,
                'filename': original_filename,
                'plant_id': user_upload.plant_id,
                'orchid_id': orchid_record.id,
                'parsed_name': self._format_scientific_name(parsed_info),
                'confidence': parsed_info.get('confidence', 0.0),
                'drive_id': drive_file_id
            }
            
        except Exception as e:
            user_upload.processing_status = 'failed'
            user_upload.error_message = str(e)
            db.session.add(user_upload)
            db.session.commit()
            
            return {
                'success': False,
                'filename': original_filename,
                'plant_id': user_upload.plant_id,
                'error': str(e)
            }
    
    def _format_scientific_name(self, parsed_info: Dict) -> str:
        """Format parsed info into scientific name"""
        if not parsed_info.get('genus'):
            return 'Unknown sp.'
        
        if parsed_info.get('is_hybrid'):
            hybrid_name = parsed_info.get('hybrid_name', 'Hybrid')
            return f"{parsed_info['genus']} {hybrid_name}"
        
        parts = [parsed_info['genus']]
        if parsed_info.get('species'):
            parts.append(parsed_info['species'])
        else:
            parts.append('sp.')
            
        if parsed_info.get('variety'):
            var_type = parsed_info.get('variety_type', 'var.')
            parts.extend([var_type, parsed_info['variety']])
            
        return ' '.join(parts)
    
    def log_message(self, message: str):
        """Add message to processing log"""
        log_entry = {
            'timestamp': str(db.func.now()),
            'message': message
        }
        self.processing_log.append(log_entry)
        logger.info(f"Batch {self.batch_upload.batch_id if self.batch_upload else 'unknown'}: {message}")

def extract_archive(archive_file: FileStorage, extract_to: str) -> List[str]:
    """
    Extract archive file and return list of extracted image files
    
    Args:
        archive_file: Archive file to extract
        extract_to: Directory to extract to
        
    Returns:
        List of extracted image file paths
    """
    extracted_files = []
    
    if not allowed_archive(archive_file.filename):
        raise ValueError("Archive type not supported")
    
    # Save archive temporarily
    temp_archive_path = os.path.join(extract_to, secure_filename(archive_file.filename))
    archive_file.save(temp_archive_path)
    
    try:
        # Extract based on file type
        if archive_file.filename.lower().endswith('.zip'):
            with zipfile.ZipFile(temp_archive_path, 'r') as zip_ref:
                for file_info in zip_ref.infolist():
                    if not file_info.is_dir() and allowed_file(file_info.filename):
                        # Extract file
                        extracted_path = zip_ref.extract(file_info, extract_to)
                        extracted_files.append(extracted_path)
        
        # Add support for other archive formats as needed
        else:
            raise ValueError(f"Archive format not yet supported: {archive_file.filename}")
        
    finally:
        # Clean up archive file
        if os.path.exists(temp_archive_path):
            os.remove(temp_archive_path)
    
    return extracted_files

def validate_batch_limits(files: List[FileStorage]) -> Tuple[bool, str]:
    """
    Validate batch upload limits
    
    Args:
        files: List of files to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(files) > MAX_FILES_PER_BATCH:
        return False, f"Too many files ({len(files)} > {MAX_FILES_PER_BATCH})"
    
    total_size = 0
    for file in files:
        if file:
            file.seek(0, 2)
            total_size += file.tell()
            file.seek(0)
    
    if total_size > MAX_BATCH_SIZE:
        return False, f"Batch too large ({total_size/1024/1024:.1f}MB > {MAX_BATCH_SIZE/1024/1024}MB)"
    
    return True, ""