"""
Main Orchid Processing Pipeline
Orchestrates the complete workflow from Google Forms to enhanced analysis
"""

import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
import os

from google_sheets_service import GoogleSheetsService
from taxonomy_validator import TaxonomyValidator
from metadata_enhancer import MetadataEnhancer
from models import OrchidRecord, db

logger = logging.getLogger(__name__)

class OrchidProcessor:
    def __init__(self):
        self.sheets_service = GoogleSheetsService()
        self.taxonomy_validator = TaxonomyValidator()
        self.metadata_enhancer = MetadataEnhancer()
        
        # Configuration
        self.spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID', 'mock-spreadsheet-id')
        self.processing_enabled = True
        
    def process_all_pending_submissions(self) -> Dict[str, Any]:
        """Process all pending submissions from Google Forms"""
        results = {
            'processed': 0,
            'errors': 0,
            'submissions': [],
            'processing_log': []
        }
        
        try:
            # Get unprocessed submissions
            pending_submissions = self.sheets_service.get_processing_queue(self.spreadsheet_id)
            results['processing_log'].append(f"Found {len(pending_submissions)} pending submissions")
            
            for idx, submission in enumerate(pending_submissions, 1):
                try:
                    # Process individual submission
                    processed_result = self.process_single_submission(submission)
                    
                    if processed_result['success']:
                        results['processed'] += 1
                        results['submissions'].append(processed_result)
                        
                        # Mark as processed in Google Sheets
                        self.sheets_service.mark_submission_processed(
                            self.spreadsheet_id, 
                            submission.get('row_number', idx + 1)  # Assuming row numbers start at 2
                        )
                        
                        results['processing_log'].append(
                            f"Successfully processed submission {idx}: {submission.get('orchid_name', 'Unknown')}"
                        )
                    else:
                        results['errors'] += 1
                        results['processing_log'].append(
                            f"Failed to process submission {idx}: {processed_result.get('error', 'Unknown error')}"
                        )
                        
                except Exception as e:
                    results['errors'] += 1
                    error_msg = f"Error processing submission {idx}: {str(e)}"
                    results['processing_log'].append(error_msg)
                    logger.error(error_msg)
            
            # Summary
            results['processing_log'].append(
                f"Processing complete: {results['processed']} successful, {results['errors']} errors"
            )
            
        except Exception as e:
            error_msg = f"Error in batch processing: {str(e)}"
            results['processing_log'].append(error_msg)
            logger.error(error_msg)
        
        return results
    
    def process_single_submission(self, submission: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single form submission through the complete pipeline"""
        result = {
            'success': False,
            'submission_id': submission.get('timestamp', datetime.now().isoformat()),
            'original_submission': submission,
            'processing_steps': [],
            'validation_result': {},
            'enhanced_data': {},
            'database_record': None,
            'error': None
        }
        
        try:
            # Step 1: Validate taxonomy
            result['processing_steps'].append("Starting taxonomy validation")
            
            validation_result = self.taxonomy_validator.validate_orchid_name(
                submitted_name=submission.get('orchid_name', ''),
                genus=submission.get('genus', ''),
                species=submission.get('species', '')
            )
            
            result['validation_result'] = validation_result
            result['processing_steps'].append(f"Taxonomy validation complete: {validation_result['validated_name']}")
            
            # Step 2: Enhance with additional metadata
            result['processing_steps'].append("Starting metadata enhancement")
            
            # Prepare data for enhancement
            enhancement_data = submission.copy()
            enhancement_data.update(validation_result)
            
            enhanced_data = self.metadata_enhancer.enhance_submission(enhancement_data)
            result['enhanced_data'] = enhanced_data
            result['processing_steps'].append("Metadata enhancement complete")
            
            # Step 3: Create database record
            result['processing_steps'].append("Creating database record")
            
            db_record = self.create_database_record(submission, validation_result, enhanced_data)
            result['database_record'] = db_record
            result['processing_steps'].append(f"Database record created with ID: {db_record.id}")
            
            # Step 4: Save enhanced data back to Google Sheets
            result['processing_steps'].append("Saving enhanced data to Google Sheets")
            
            enhanced_for_sheets = self.prepare_enhanced_data_for_sheets(
                submission, validation_result, enhanced_data, db_record
            )
            
            self.sheets_service.save_enhanced_data(self.spreadsheet_id, enhanced_for_sheets)
            result['processing_steps'].append("Enhanced data saved to Google Sheets")
            
            result['success'] = True
            result['processing_steps'].append("Processing completed successfully")
            
        except Exception as e:
            error_msg = str(e)
            result['error'] = error_msg
            result['processing_steps'].append(f"Processing failed: {error_msg}")
            logger.error(f"Error processing submission: {error_msg}")
        
        return result
    
    def create_database_record(self, submission: Dict[str, Any], validation: Dict[str, Any], enhanced: Dict[str, Any]) -> OrchidRecord:
        """Create a database record from processed submission"""
        
        try:
            # Extract enhanced botanical data
            botanical_data = enhanced.get('botanical_data', {})
            cultural_reqs = enhanced.get('cultural_requirements', {})
            judging_analysis = enhanced.get('judging_analysis', {})
            ai_analysis = enhanced.get('ai_analysis', {})
            
            # Create orchid record
            orchid = OrchidRecord(
                # Basic identification
                scientific_name=validation.get('validated_name', ''),
                genus=validation.get('validated_genus', ''),
                species=validation.get('validated_species', ''),
                hybrid_name=validation.get('hybrid_name', ''),
                common_names=', '.join(botanical_data.get('common_names', [])),
                
                # Taxonomy
                family=botanical_data.get('family', ''),
                subfamily=botanical_data.get('subfamily', ''),
                
                # Photo and submission info
                image_url=submission.get('photo_url', ''),
                original_filename=f"form_submission_{submission.get('timestamp', '')}.jpg",
                submitter_name=submission.get('submitter_name', ''),
                submitter_email=submission.get('submitter_email', ''),
                
                # Location and notes
                location_found=submission.get('location_found', ''),
                notes=submission.get('notes', ''),
                
                # Enhanced metadata
                ai_description=str(ai_analysis.get('photo_analysis', {})),
                ai_confidence=ai_analysis.get('ai_confidence', 0),
                
                # Cultural information
                light_requirements=cultural_reqs.get('light', {}).get('requirement', ''),
                temperature_min=self.extract_temperature_min(cultural_reqs.get('temperature', {})),
                temperature_max=self.extract_temperature_max(cultural_reqs.get('temperature', {})),
                humidity_min=self.extract_humidity_min(cultural_reqs.get('humidity', {})),
                humidity_max=self.extract_humidity_max(cultural_reqs.get('humidity', {})),
                
                # Care instructions
                watering_notes=cultural_reqs.get('watering', {}).get('method', ''),
                fertilizer_notes=cultural_reqs.get('fertilizing', {}).get('type', ''),
                repotting_notes=cultural_reqs.get('repotting', {}).get('medium', ''),
                
                # Judging information
                judging_score=judging_analysis.get('total_score', 0),
                judging_notes=judging_analysis.get('judging_notes', ''),
                
                # Distribution and habitat
                native_distribution=botanical_data.get('distribution', ''),
                natural_habitat=botanical_data.get('habitat', ''),
                
                # Processing metadata
                source='google_forms',
                processed=True,
                validation_notes=json.dumps(validation.get('validation_notes', [])),
                enhancement_data=json.dumps({
                    'morphological_tags': enhanced.get('morphological_tags', []),
                    'ecological_data': enhanced.get('ecological_data', {}),
                    'processing_timestamp': enhanced.get('enhancement_timestamp', ''),
                    'ai_analysis_summary': ai_analysis.get('quality_assessment', 0)
                }),
                
                # Status
                is_verified=False,  # Requires admin verification
                is_featured=False,
                view_count=0
            )
            
            # Save to database
            db.session.add(orchid)
            db.session.commit()
            
            logger.info(f"Created database record for {orchid.scientific_name} (ID: {orchid.id})")
            return orchid
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating database record: {e}")
            raise
    
    def extract_temperature_min(self, temp_data: Dict) -> Optional[int]:
        """Extract minimum temperature from temperature data"""
        temp_range = temp_data.get('range', '')
        if '-' in temp_range:
            try:
                min_temp = temp_range.split('-')[0].strip()
                return int(''.join(filter(str.isdigit, min_temp)))
            except:
                pass
        return None
    
    def extract_temperature_max(self, temp_data: Dict) -> Optional[int]:
        """Extract maximum temperature from temperature data"""
        temp_range = temp_data.get('range', '')
        if '-' in temp_range:
            try:
                max_temp = temp_range.split('-')[1].split('°')[0].strip()
                return int(''.join(filter(str.isdigit, max_temp)))
            except:
                pass
        return None
    
    def extract_humidity_min(self, humidity_data: Dict) -> Optional[int]:
        """Extract minimum humidity from humidity data"""
        humidity_range = humidity_data.get('preference', '')
        if '-' in humidity_range:
            try:
                min_humidity = humidity_range.split('-')[0].strip()
                return int(''.join(filter(str.isdigit, min_humidity)))
            except:
                pass
        return None
    
    def extract_humidity_max(self, humidity_data: Dict) -> Optional[int]:
        """Extract maximum humidity from humidity data"""
        humidity_range = humidity_data.get('preference', '')
        if '-' in humidity_range:
            try:
                max_humidity = humidity_range.split('-')[1].split('%')[0].strip()
                return int(''.join(filter(str.isdigit, max_humidity)))
            except:
                pass
        return None
    
    def prepare_enhanced_data_for_sheets(self, submission: Dict[str, Any], validation: Dict[str, Any], 
                                       enhanced: Dict[str, Any], db_record: OrchidRecord) -> Dict[str, Any]:
        """Prepare enhanced data for saving back to Google Sheets"""
        return {
            'original_id': submission.get('timestamp', ''),
            'submitter': submission.get('submitter_name', ''),
            'validated_genus': validation.get('validated_genus', ''),
            'validated_species': validation.get('validated_species', ''),
            'hybrid_name': validation.get('hybrid_name', ''),
            'scientific_name': validation.get('validated_name', ''),
            'common_names': ', '.join(enhanced.get('botanical_data', {}).get('common_names', [])),
            'family': enhanced.get('botanical_data', {}).get('family', ''),
            'ai_confidence': enhanced.get('ai_analysis', {}).get('ai_confidence', 0),
            'enhanced_metadata': json.dumps(enhanced.get('enhanced_fields', {})),
            'care_instructions': json.dumps(enhanced.get('cultural_requirements', {})),
            'cultural_requirements': enhanced.get('botanical_data', {}).get('habitat', ''),
            'judging_score': enhanced.get('judging_analysis', {}).get('total_score', 0),
            'photo_analysis': json.dumps(enhanced.get('ai_analysis', {}).get('photo_analysis', {})),
            'morphological_tags': ', '.join(enhanced.get('morphological_tags', [])),
            'ecological_data': json.dumps(enhanced.get('ecological_data', {})),
            'processing_notes': f'Processed successfully. Database ID: {db_record.id}',
            'database_id': db_record.id
        }
    
    def get_processing_status(self) -> Dict[str, Any]:
        """Get current processing status and statistics"""
        try:
            pending_count = len(self.sheets_service.get_processing_queue(self.spreadsheet_id))
            
            # Get database statistics
            total_records = OrchidRecord.query.count()
            processed_today = OrchidRecord.query.filter(
                OrchidRecord.created_at >= datetime.now().date()
            ).count()
            
            return {
                'processing_enabled': self.processing_enabled,
                'pending_submissions': pending_count,
                'total_database_records': total_records,
                'processed_today': processed_today,
                'last_check': datetime.now().isoformat(),
                'google_sheets_connected': self.sheets_service.client is not None
            }
            
        except Exception as e:
            logger.error(f"Error getting processing status: {e}")
            return {
                'error': str(e),
                'processing_enabled': False
            }