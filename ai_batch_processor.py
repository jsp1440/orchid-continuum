"""
AI Batch Processing System for Orchid Image Analysis
Processes all orchid images with AI analysis and provides progress tracking
"""

import logging
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from flask import current_app
from app import app, db
from models import OrchidRecord
from orchid_ai import analyze_orchid_image
from sqlalchemy import or_
import os

logger = logging.getLogger(__name__)

class AIBatchProcessor:
    def __init__(self):
        self.is_running = False
        self.progress = {
            'total_orchids': 0,
            'processed': 0,
            'success': 0,
            'errors': 0,
            'skipped': 0,
            'current_orchid': None,
            'start_time': None,
            'estimated_completion': None,
            'processing_rate': 0.0,
            'status': 'idle'
        }
        self.processing_thread = None
        self.stop_requested = False
        
    def start_batch_analysis(self, limit: Optional[int] = None) -> Dict[str, Any]:
        """Start batch AI analysis of orchid images"""
        if self.is_running:
            return {'error': 'Batch processing already running', 'success': False}
            
        self.is_running = True
        self.stop_requested = False
        self.progress['status'] = 'starting'
        self.progress['start_time'] = datetime.now()
        
        # Get orchids that need AI analysis
        with app.app_context():
            try:
                # Count total orchids with images first
                total_with_images = OrchidRecord.query.filter(
                    or_(
                        OrchidRecord.google_drive_id.isnot(None),
                        OrchidRecord.image_url.isnot(None),
                        OrchidRecord.image_filename.isnot(None)
                    )
                ).count()
                logger.info(f"Found {total_with_images} orchids with images")
                
                # Get orchids that need AI analysis
                query = OrchidRecord.query.filter(
                    or_(
                        OrchidRecord.google_drive_id.isnot(None),
                        OrchidRecord.image_url.isnot(None),
                        OrchidRecord.image_filename.isnot(None)
                    )
                ).filter(OrchidRecord.ai_description.is_(None))
                
                if limit:
                    query = query.limit(limit)
                    
                orchids_to_process = query.all()
                self.progress['total_orchids'] = len(orchids_to_process)
                
                logger.info(f"Found {len(orchids_to_process)} orchids needing AI analysis")
                
            except Exception as e:
                logger.error(f"Error querying orchids: {e}")
                orchids_to_process = []
                self.progress['total_orchids'] = 0
            
        logger.info(f"🤖 Starting AI batch analysis of {self.progress['total_orchids']} orchids")
        
        # Start processing in background thread
        self.processing_thread = threading.Thread(
            target=self._process_orchids_batch,
            args=(orchids_to_process,)
        )
        self.processing_thread.daemon = True
        self.processing_thread.start()
        
        return {
            'success': True,
            'message': f'Started AI analysis of {self.progress["total_orchids"]} orchids',
            'total_orchids': self.progress['total_orchids']
        }
    
    def _process_orchids_batch(self, orchids: List[OrchidRecord]):
        """Process batch of orchids with AI analysis"""
        self.progress['status'] = 'processing'
        
        for i, orchid in enumerate(orchids):
            if self.stop_requested:
                self.progress['status'] = 'stopped'
                break
                
            try:
                self.progress['current_orchid'] = {
                    'id': orchid.id,
                    'name': orchid.display_name or orchid.scientific_name or 'Unknown',
                    'genus': orchid.genus
                }
                
                # Skip if no image available
                if not orchid.google_drive_id and not orchid.image_url:
                    logger.info(f"⏭️ Skipping orchid {orchid.id}: No image available")
                    self.progress['skipped'] += 1
                    continue
                
                # Perform AI analysis
                success = self._analyze_single_orchid(orchid)
                
                if success:
                    self.progress['success'] += 1
                    logger.info(f"✅ AI analysis completed for orchid {orchid.id}: {orchid.display_name}")
                else:
                    self.progress['errors'] += 1
                    logger.error(f"❌ AI analysis failed for orchid {orchid.id}")
                    
            except Exception as e:
                logger.error(f"❌ Error processing orchid {orchid.id}: {e}")
                self.progress['errors'] += 1
                
            finally:
                self.progress['processed'] += 1
                
                # Update processing rate and estimated completion
                self._update_progress_estimates()
                
                # Small delay to prevent overwhelming the API
                time.sleep(0.5)
        
        # Mark completion
        self.progress['status'] = 'completed' if not self.stop_requested else 'stopped'
        self.is_running = False
        
        logger.info(f"🎉 AI batch analysis completed! Success: {self.progress['success']}, Errors: {self.progress['errors']}, Skipped: {self.progress['skipped']}")
    
    def _analyze_single_orchid(self, orchid: OrchidRecord) -> bool:
        """Analyze a single orchid with AI"""
        try:
            with app.app_context():
                # Check if we have an OpenAI API key
                api_key = os.environ.get("OPENAI_API_KEY", "")
                if not api_key or api_key == "your-api-key-here" or "export" in api_key:
                    logger.warning(f"⚠️ No valid OpenAI API key - skipping AI analysis for orchid {orchid.id}")
                    return False
                
                # Create image path for analysis
                if orchid.google_drive_id:
                    image_path = f"drive:{orchid.google_drive_id}"
                elif orchid.image_url:
                    image_path = orchid.image_url
                else:
                    return False
                
                # Perform AI analysis
                ai_results = analyze_orchid_image(image_path)
                
                if ai_results and 'description' in ai_results:
                    # Update orchid record with AI results
                    if ai_results.get('suggested_name'):
                        if not orchid.display_name or 'Unknown' in orchid.display_name:
                            orchid.display_name = ai_results['suggested_name']
                    
                    if ai_results.get('description'):
                        orchid.ai_description = ai_results['description']
                    
                    if ai_results.get('confidence'):
                        orchid.ai_confidence = float(ai_results['confidence'])
                    
                    # Update genus/species if AI provides better information
                    metadata = ai_results.get('metadata', {})
                    if metadata.get('genus') and not orchid.genus:
                        orchid.genus = metadata['genus']
                    
                    if metadata.get('species') and not orchid.species:
                        orchid.species = metadata['species']
                    
                    if metadata.get('scientific_name') and not orchid.scientific_name:
                        orchid.scientific_name = metadata['scientific_name']
                    
                    # Update cultural information
                    if metadata.get('climate_preference'):
                        orchid.climate_type = metadata['climate_preference']
                    
                    if metadata.get('growth_habit'):
                        orchid.growth_habit = metadata['growth_habit']
                    
                    if metadata.get('native_habitat'):
                        orchid.native_habitat = metadata['native_habitat']
                    
                    # Save changes
                    db.session.commit()
                    return True
                else:
                    logger.warning(f"⚠️ AI analysis returned no results for orchid {orchid.id}")
                    return False
                    
        except Exception as e:
            logger.error(f"❌ AI analysis error for orchid {orchid.id}: {e}")
            db.session.rollback()
            return False
    
    def _update_progress_estimates(self):
        """Update processing rate and time estimates"""
        if self.progress['start_time'] and self.progress['processed'] > 0:
            elapsed_time = (datetime.now() - self.progress['start_time']).total_seconds()
            self.progress['processing_rate'] = self.progress['processed'] / elapsed_time * 60  # per minute
            
            remaining = self.progress['total_orchids'] - self.progress['processed']
            if self.progress['processing_rate'] > 0:
                estimated_minutes = remaining / (self.progress['processing_rate'] / 60)
                self.progress['estimated_completion'] = datetime.now().timestamp() + (estimated_minutes * 60)
    
    def get_progress(self) -> Dict[str, Any]:
        """Get current processing progress"""
        progress = self.progress.copy()
        
        # Calculate percentage
        if progress['total_orchids'] > 0:
            progress['percentage'] = (progress['processed'] / progress['total_orchids']) * 100
        else:
            progress['percentage'] = 0
            
        # Format start time
        if progress['start_time']:
            progress['start_time'] = progress['start_time'].isoformat()
            
        return progress
    
    def stop_processing(self) -> Dict[str, Any]:
        """Stop the current batch processing"""
        if not self.is_running:
            return {'error': 'No processing currently running', 'success': False}
            
        self.stop_requested = True
        logger.info("🛑 AI batch processing stop requested")
        
        return {'success': True, 'message': 'Stop request sent'}

# Global processor instance
ai_batch_processor = AIBatchProcessor()