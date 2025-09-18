"""
GBIF Ecosystem Batch Enrichment Service for Orchid Ecosystem Data
Processes existing orchid records in batches to enrich them with GBIF ecosystem data
"""

import json
import time
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from difflib import SequenceMatcher
from sqlalchemy import and_, or_, func
from app import db
from models import OrchidRecord, TrefleEnrichmentTracker
from gbif_botanical_service import GBIFBotanicalService

logger = logging.getLogger(__name__)

class TrefleBatchEnrichmentService:
    """Service for batch enrichment of orchid records with GBIF ecosystem data"""
    
    def __init__(self):
        self.trefle_service = GBIFBotanicalService()
        self.current_session = None
        self.logger = logging.getLogger(__name__)
        
        # Matching configuration
        self.fuzzy_match_threshold = 0.8  # Minimum similarity for fuzzy matching
        self.genus_fallback_enabled = True
        self.skip_already_enriched = True
        
        # Processing configuration
        self.default_batch_size = 25  # Reduced for better rate limiting
        self.max_retries_per_record = 3
        self.delay_between_batches = 5  # seconds
        self.request_timeout = 30  # seconds
        self.batch_timeout = 300  # 5 minutes max per batch
        
        # Background processing
        self.background_threads = {}  # Track active background threads
        self.thread_lock = threading.Lock()  # Thread safety
        
    def create_enrichment_session(self, session_name: str, priority_fcos_only: bool = False, 
                                  force_update_existing: bool = False, batch_size: int = None) -> str:
        """Create a new enrichment session and return session ID"""
        
        session_id = f"trefle_enrichment_{int(time.time())}"
        
        # Count total records to process
        query = db.session.query(OrchidRecord)
        
        if priority_fcos_only:
            # Priority: FCOS Google Drive records (1,591 records)
            query = query.filter(OrchidRecord.google_drive_id.isnot(None))
            self.logger.info("🎯 FCOS Priority Mode: Processing Google Drive orchid records first")
        
        if not force_update_existing and self.skip_already_enriched:
            # Skip records that already have Trefle data
            query = query.filter(
                or_(
                    OrchidRecord.habitat_research.is_(None),
                    ~OrchidRecord.habitat_research.contains('"source": "trefle"')
                )
            )
        
        # Only process records with scientific names
        query = query.filter(OrchidRecord.scientific_name.isnot(None))
        query = query.filter(OrchidRecord.scientific_name != '')
        
        total_records = query.count()
        
        # Create tracking record
        tracker = TrefleEnrichmentTracker(
            session_id=session_id,
            session_name=session_name,
            total_records=total_records,
            current_batch_size=batch_size or self.default_batch_size,
            priority_fcos_only=priority_fcos_only,
            force_update_existing=force_update_existing,
            status='pending'
        )
        
        db.session.add(tracker)
        db.session.commit()
        
        self.logger.info(f"✅ Created enrichment session '{session_name}' with {total_records} records to process")
        
        return session_id
    
    def get_session_status(self, session_id: str) -> Optional[Dict]:
        """Get current status of an enrichment session"""
        tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
        if not tracker:
            return None
        return tracker.to_dict()
    
    def list_enrichment_sessions(self, limit: int = 20) -> List[Dict]:
        """List recent enrichment sessions"""
        sessions = db.session.query(TrefleEnrichmentTracker)\
            .order_by(TrefleEnrichmentTracker.created_at.desc())\
            .limit(limit).all()
        return [session.to_dict() for session in sessions]
    
    def smart_name_matching(self, orchid_name: str, trefle_results: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        Smart matching algorithm for orchid names against Trefle results
        Returns (best_match, confidence_score)
        """
        if not orchid_name or not trefle_results:
            return None, 0.0
        
        orchid_name_clean = orchid_name.lower().strip()
        best_match = None
        best_score = 0.0
        
        for plant in trefle_results:
            if not plant.get('scientific_name'):
                continue
                
            trefle_name = plant['scientific_name'].lower().strip()
            
            # Exact match (highest priority)
            if orchid_name_clean == trefle_name:
                return plant, 1.0
            
            # Fuzzy string matching
            similarity = SequenceMatcher(None, orchid_name_clean, trefle_name).ratio()
            
            # Boost score for genus + species matches
            orchid_parts = orchid_name_clean.split()
            trefle_parts = trefle_name.split()
            
            if len(orchid_parts) >= 2 and len(trefle_parts) >= 2:
                if orchid_parts[0] == trefle_parts[0]:  # Same genus
                    similarity += 0.2  # Bonus for matching genus
                    if orchid_parts[1] == trefle_parts[1]:  # Same species
                        similarity += 0.3  # Additional bonus for matching species
            
            # Check for partial matches in scientific names
            if orchid_name_clean in trefle_name or trefle_name in orchid_name_clean:
                similarity = max(similarity, 0.85)
            
            if similarity > best_score:
                best_score = similarity
                best_match = plant
        
        return best_match, best_score
    
    def genus_fallback_search(self, orchid_name: str) -> Optional[Dict]:
        """Fallback to genus-level search if species not found"""
        if not orchid_name or not self.genus_fallback_enabled:
            return None
        
        # Extract genus from scientific name
        genus = orchid_name.split()[0] if ' ' in orchid_name else orchid_name
        
        self.logger.info(f"🔄 Attempting genus fallback search for: {genus}")
        
        # Search Trefle for genus-level information
        genus_data = self.trefle_service.search_plant_by_scientific_name(genus)
        
        if genus_data and not genus_data.get('rate_limit_exceeded'):
            self.logger.info(f"✅ Found genus-level data for: {genus}")
            # Mark as genus-level match
            genus_data['_match_level'] = 'genus'
            genus_data['_original_query'] = orchid_name
            return genus_data
        
        return None
    
    def enrich_orchid_with_trefle_data(self, orchid: OrchidRecord) -> Dict[str, Any]:
        """
        Enrich a single orchid record with Trefle ecosystem data
        Returns enrichment result with status and data
        """
        result = {
            'orchid_id': orchid.id,
            'scientific_name': orchid.scientific_name,
            'status': 'failed',
            'trefle_data': None,
            'confidence': 0.0,
            'match_level': None,
            'error': None,
            'api_calls_made': 0
        }
        
        try:
            # Check if already enriched (unless force update)
            if (self.skip_already_enriched and 
                orchid.habitat_research and 
                isinstance(orchid.habitat_research, dict) and 
                orchid.habitat_research.get('source') == 'trefle'):
                result['status'] = 'skipped'
                result['error'] = 'Already enriched with Trefle data'
                return result
            
            if not orchid.scientific_name:
                result['error'] = 'No scientific name available'
                return result
            
            # Search Trefle API
            self.logger.info(f"🔍 Searching Trefle for: {orchid.scientific_name}")
            trefle_data = self.trefle_service.search_plant_by_scientific_name(orchid.scientific_name)
            result['api_calls_made'] += 1
            
            # Handle rate limiting with structured response
            if trefle_data and trefle_data.get('rate_limit_exceeded'):
                result['status'] = 'rate_limited'
                result['error'] = f"Rate limit exceeded: {trefle_data.get('error')}"
                result['retry_after'] = trefle_data.get('retry_after', 60)
                self.logger.warning(f"⏳ Rate limited for orchid {orchid.id}: retry after {result['retry_after']}s")
                return result
            
            # Try smart matching if we got multiple results
            if trefle_data and trefle_data.get('data'):
                match, confidence = self.smart_name_matching(orchid.scientific_name, trefle_data['data'])
                if match and confidence >= self.fuzzy_match_threshold:
                    result['trefle_data'] = match
                    result['confidence'] = confidence
                    result['match_level'] = 'species'
                    result['status'] = 'success'
                else:
                    # Try genus fallback
                    genus_data = self.genus_fallback_search(orchid.scientific_name)
                    if genus_data:
                        result['trefle_data'] = genus_data
                        result['confidence'] = 0.7  # Lower confidence for genus matches
                        result['match_level'] = 'genus'
                        result['status'] = 'success'
                        result['api_calls_made'] += 1
            
            # If we have data, enrich the orchid record
            if result['status'] == 'success' and result['trefle_data']:
                self._update_orchid_with_trefle_data(orchid, result['trefle_data'], result)
                self.logger.info(f"✅ Enriched orchid {orchid.id} ({orchid.scientific_name}) with Trefle data")
            else:
                result['error'] = 'No matching data found in Trefle'
                
        except Exception as e:
            self.logger.error(f"❌ Error enriching orchid {orchid.id}: {str(e)}")
            result['error'] = str(e)
        
        return result
    
    def _update_orchid_with_trefle_data(self, orchid: OrchidRecord, trefle_data: Dict, enrichment_result: Dict):
        """Update orchid record with Trefle ecosystem data"""
        
        # Prepare structured habitat research data
        habitat_research = {
            'source': 'trefle',
            'enrichment_date': datetime.utcnow().isoformat(),
            'confidence_level': enrichment_result['confidence'],
            'match_level': enrichment_result['match_level'],
            'trefle_id': trefle_data.get('id'),
            'scientific_name_matched': trefle_data.get('scientific_name'),
            'raw_data': trefle_data
        }
        
        # Extract ecosystem and habitat information
        ecosystem_data = {}
        
        # Extract specifications (climate, habitat, etc.)
        if 'specifications' in trefle_data:
            specs = trefle_data['specifications']
            ecosystem_data.update({
                'growth_months': specs.get('growth_months'),
                'bloom_months': specs.get('bloom_months'),
                'drought_tolerance': specs.get('drought_tolerance'),
                'salt_tolerance': specs.get('salt_tolerance'),
                'ph_maximum': specs.get('ph_maximum'),
                'ph_minimum': specs.get('ph_minimum'),
                'light': specs.get('light'),
                'atmospheric_humidity': specs.get('atmospheric_humidity'),
                'ground_humidity': specs.get('ground_humidity'),
                'temperature_minimum': specs.get('temperature_minimum'),
                'temperature_maximum': specs.get('temperature_maximum')
            })
        
        # Extract growth information
        if 'growth' in trefle_data:
            growth = trefle_data['growth']
            ecosystem_data.update({
                'soil_nutriments': growth.get('soil_nutriments'),
                'soil_salinity': growth.get('soil_salinity'),
                'soil_texture': growth.get('soil_texture'),
                'soil_humidity': growth.get('soil_humidity'),
                'growth_form': growth.get('growth_form'),
                'growth_habit': growth.get('growth_habit'),
                'growth_rate': growth.get('growth_rate')
            })
        
        habitat_research['ecosystem_data'] = ecosystem_data
        
        # Update habitat_research field with structured data
        orchid.habitat_research = habitat_research
        
        # Update native_habitat with readable summary
        habitat_summary = self._generate_habitat_summary(trefle_data, ecosystem_data)
        if habitat_summary:
            orchid.native_habitat = habitat_summary
        
        # Update climate_preference based on temperature data
        climate_pref = self._determine_climate_preference(ecosystem_data)
        if climate_pref:
            orchid.climate_preference = climate_pref
        
        # Mark external data sources
        if not orchid.external_data_sources:
            orchid.external_data_sources = {}
        orchid.external_data_sources['trefle'] = {
            'enriched_at': datetime.utcnow().isoformat(),
            'confidence': enrichment_result['confidence'],
            'match_level': enrichment_result['match_level']
        }
        
        db.session.commit()
    
    def _generate_habitat_summary(self, trefle_data: Dict, ecosystem_data: Dict) -> str:
        """Generate human-readable habitat summary from Trefle data"""
        summary_parts = []
        
        # Add basic habitat info
        if ecosystem_data.get('growth_habit'):
            summary_parts.append(f"Growth habit: {ecosystem_data['growth_habit']}")
        
        # Add climate info
        temp_min = ecosystem_data.get('temperature_minimum')
        temp_max = ecosystem_data.get('temperature_maximum')
        if temp_min and temp_max:
            summary_parts.append(f"Temperature range: {temp_min}°C - {temp_max}°C")
        
        # Add light requirements
        if ecosystem_data.get('light'):
            summary_parts.append(f"Light: {ecosystem_data['light']}")
        
        # Add humidity info
        if ecosystem_data.get('atmospheric_humidity'):
            summary_parts.append(f"Humidity: {ecosystem_data['atmospheric_humidity']}")
        
        # Add soil/growing medium info
        if ecosystem_data.get('soil_texture'):
            summary_parts.append(f"Growing medium: {ecosystem_data['soil_texture']}")
        
        summary = ". ".join(summary_parts)
        if summary:
            summary = f"Trefle botanical data: {summary}."
        
        return summary
    
    def _determine_climate_preference(self, ecosystem_data: Dict) -> Optional[str]:
        """Determine climate preference based on temperature data"""
        temp_min = ecosystem_data.get('temperature_minimum')
        temp_max = ecosystem_data.get('temperature_maximum')
        
        if not temp_min and not temp_max:
            return None
        
        # Use average temperature to determine preference
        if temp_min and temp_max:
            avg_temp = (temp_min + temp_max) / 2
        elif temp_min:
            avg_temp = temp_min + 5  # Estimate
        else:
            avg_temp = temp_max - 5  # Estimate
        
        # Classify based on typical orchid temperature preferences
        if avg_temp < 18:
            return 'cool'
        elif avg_temp > 25:
            return 'warm'
        else:
            return 'intermediate'
    
    def process_batch_enrichment(self, session_id: str, max_records: int = None) -> Dict[str, Any]:
        """
        Process a batch of orchid records for Trefle enrichment
        Non-blocking with timeout protection
        Returns processing summary with structured status
        """
        tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
        if not tracker:
            return {'error': 'Session not found'}
        
        # Update session status
        if tracker.status == 'pending':
            tracker.status = 'running'
            tracker.started_at = datetime.utcnow()
        
        batch_size = min(tracker.current_batch_size, max_records or tracker.current_batch_size)
        
        # Build query for records to process
        query = db.session.query(OrchidRecord)
        
        if tracker.priority_fcos_only:
            query = query.filter(OrchidRecord.google_drive_id.isnot(None))
        
        if not tracker.force_update_existing:
            query = query.filter(
                or_(
                    OrchidRecord.habitat_research.is_(None),
                    ~OrchidRecord.habitat_research.contains('"source": "trefle"')
                )
            )
        
        query = query.filter(OrchidRecord.scientific_name.isnot(None))
        query = query.filter(OrchidRecord.scientific_name != '')
        
        # Skip already processed records in this session
        if tracker.last_processed_id:
            query = query.filter(OrchidRecord.id > tracker.last_processed_id)
        
        # Get batch of records
        orchids = query.order_by(OrchidRecord.id).limit(batch_size).all()
        
        processing_summary = {
            'session_id': session_id,
            'batch_size': len(orchids),
            'enriched': 0,
            'failed': 0,
            'skipped': 0,
            'rate_limited': 0,
            'api_calls_made': 0,
            'records_processed': []
        }
        
        # Process each orchid in the batch
        for orchid in orchids:
            result = self.enrich_orchid_with_trefle_data(orchid)
            processing_summary['api_calls_made'] += result.get('api_calls_made', 0)
            processing_summary['records_processed'].append(result)
            
            if result['status'] == 'success':
                processing_summary['enriched'] += 1
                tracker.enriched_records += 1
            elif result['status'] == 'skipped':
                processing_summary['skipped'] += 1
                tracker.skipped_records += 1
            elif result['status'] == 'rate_limited' and result.get('retry_after'):
                processing_summary['rate_limited'] += 1
                tracker.rate_limit_hits += 1
                # Store the retry_after time for proper resumption
                retry_after_seconds = result.get('retry_after', 60)
                tracker.estimated_completion = datetime.utcnow() + timedelta(seconds=retry_after_seconds)
                self.logger.info(f"⏸️ Pausing batch processing due to rate limit. Resume in {retry_after_seconds}s")
                # Stop processing if rate limited
                break
            else:
                processing_summary['failed'] += 1
                tracker.failed_records += 1
                
                # Track failed orchid IDs
                if not tracker.failed_orchid_ids:
                    tracker.failed_orchid_ids = []
                tracker.failed_orchid_ids.append(orchid.id)
            
            tracker.processed_records += 1
            tracker.last_processed_id = orchid.id
            tracker.api_calls_made += result.get('api_calls_made', 0)
            tracker.last_api_call = datetime.utcnow()
        
        # Update completion status
        if tracker.processed_records >= tracker.total_records:
            tracker.status = 'completed'
            tracker.completed_at = datetime.utcnow()
        elif processing_summary['rate_limited'] > 0:
            tracker.status = 'paused'
            # Estimate when we can continue (based on rate limit)
            retry_after = max([r.get('retry_after', 60) for r in processing_summary['records_processed'] if r.get('retry_after')])
            tracker.estimated_completion = datetime.utcnow() + timedelta(seconds=retry_after)
        
        tracker.updated_at = datetime.utcnow()
        db.session.commit()
        
        self.logger.info(f"📊 Batch processing complete: {processing_summary['enriched']} enriched, {processing_summary['failed']} failed, {processing_summary['skipped']} skipped")
        
        return processing_summary
    
    def start_background_processing(self, session_id: str, continuous: bool = False) -> Dict[str, Any]:
        """
        Start background enrichment processing for a session
        Non-blocking - runs in a separate thread
        """
        with self.thread_lock:
            # Check if already running
            if session_id in self.background_threads:
                thread = self.background_threads[session_id]
                if thread.is_alive():
                    return {
                        'success': False,
                        'error': 'Background processing already running for this session',
                        'status': 'already_running'
                    }
                else:
                    # Clean up dead thread
                    del self.background_threads[session_id]
            
            # Validate session exists
            tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
            if not tracker:
                return {
                    'success': False,
                    'error': 'Session not found',
                    'status': 'session_not_found'
                }
            
            if tracker.status not in ['pending', 'paused']:
                return {
                    'success': False,
                    'error': f'Cannot start processing - session status is: {tracker.status}',
                    'status': 'invalid_status'
                }
            
            # Start background thread
            thread = threading.Thread(
                target=self._background_enrichment_worker,
                args=(session_id, continuous),
                name=f"TrefleEnrichment-{session_id}",
                daemon=True
            )
            
            self.background_threads[session_id] = thread
            thread.start()
            
            self.logger.info(f"🚀 Started background enrichment for session {session_id} (continuous: {continuous})")
            
            return {
                'success': True,
                'message': f'Background processing started for session {session_id}',
                'status': 'started',
                'continuous': continuous
            }
    
    def stop_background_processing(self, session_id: str) -> Dict[str, Any]:
        """Stop background enrichment processing for a session"""
        with self.thread_lock:
            if session_id not in self.background_threads:
                return {
                    'success': False,
                    'error': 'No background processing found for this session',
                    'status': 'not_running'
                }
            
            thread = self.background_threads[session_id]
            if not thread.is_alive():
                del self.background_threads[session_id]
                return {
                    'success': False,
                    'error': 'Background processing not active',
                    'status': 'not_active'
                }
            
            # Update session status to signal stop
            tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
            if tracker:
                tracker.status = 'stopping'
                db.session.commit()
            
            self.logger.info(f"🛑 Stopping background enrichment for session {session_id}")
            
            return {
                'success': True,
                'message': f'Background processing stopped for session {session_id}',
                'status': 'stopped'
            }
    
    def get_background_status(self, session_id: str) -> Dict[str, Any]:
        """Get status of background processing for a session"""
        with self.thread_lock:
            thread_active = session_id in self.background_threads and self.background_threads[session_id].is_alive()
            
            # Get session status from database
            session_status = self.get_session_status(session_id)
            if not session_status:
                return {
                    'success': False,
                    'error': 'Session not found',
                    'thread_active': False
                }
            
            return {
                'success': True,
                'session_id': session_id,
                'thread_active': thread_active,
                'session_status': session_status,
                'processing_mode': 'background' if thread_active else 'manual'
            }
    
    def _background_enrichment_worker(self, session_id: str, continuous: bool = False):
        """Background worker function that processes enrichment batches"""
        try:
            self.logger.info(f"🔄 Background enrichment worker started for session {session_id}")
            
            while True:
                # Check if we should stop
                tracker = db.session.query(TrefleEnrichmentTracker).filter_by(session_id=session_id).first()
                if not tracker or tracker.status in ['completed', 'stopping', 'failed']:
                    break
                
                # Process a batch
                try:
                    result = self.process_batch_enrichment(session_id, max_records=tracker.current_batch_size)
                    
                    # Handle different result statuses
                    if result.get('error'):
                        self.logger.error(f"❌ Background batch error: {result['error']}")
                        if not continuous:
                            break
                        # Wait before retrying
                        time.sleep(self.delay_between_batches * 2)
                        continue
                    
                    # If rate limited, wait and continue
                    if result.get('rate_limited', 0) > 0:
                        retry_after = max([r.get('retry_after', 60) for r in result.get('records_processed', []) if r.get('retry_after')])
                        self.logger.info(f"⏳ Background worker pausing for {retry_after}s due to rate limit")
                        time.sleep(retry_after)
                        continue
                    
                    # Check if session is complete
                    if tracker.processed_records >= tracker.total_records:
                        self.logger.info(f"✅ Background enrichment completed for session {session_id}")
                        break
                    
                    # If not continuous and we processed successfully, break
                    if not continuous:
                        self.logger.info(f"📊 Background batch completed: {result.get('enriched', 0)} enriched")
                        break
                    
                    # Wait between batches for continuous processing
                    if continuous:
                        time.sleep(self.delay_between_batches)
                    
                except Exception as batch_error:
                    self.logger.error(f"❌ Background batch processing error: {str(batch_error)}")
                    if not continuous:
                        break
                    time.sleep(self.delay_between_batches * 2)
                    
        except Exception as e:
            self.logger.error(f"❌ Background enrichment worker error: {str(e)}")
        finally:
            # Clean up thread reference
            with self.thread_lock:
                if session_id in self.background_threads:
                    del self.background_threads[session_id]
            
            self.logger.info(f"🔚 Background enrichment worker finished for session {session_id}")

# Global service instance
trefle_batch_service = TrefleBatchEnrichmentService()

def create_enrichment_session(session_name: str, priority_fcos_only: bool = False, 
                             force_update_existing: bool = False, batch_size: int = None) -> str:
    """Create a new Trefle enrichment session"""
    return trefle_batch_service.create_enrichment_session(
        session_name, priority_fcos_only, force_update_existing, batch_size
    )

def get_enrichment_session_status(session_id: str) -> Optional[Dict]:
    """Get status of enrichment session"""
    return trefle_batch_service.get_session_status(session_id)

def list_enrichment_sessions(limit: int = 20) -> List[Dict]:
    """List recent enrichment sessions"""
    return trefle_batch_service.list_enrichment_sessions(limit)

def process_enrichment_batch(session_id: str, max_records: int = None) -> Dict:
    """Process a batch of records for enrichment"""
    return trefle_batch_service.process_batch_enrichment(session_id, max_records)

def start_background_enrichment(session_id: str, continuous: bool = False) -> Dict:
    """Start background enrichment processing for a session"""
    return trefle_batch_service.start_background_processing(session_id, continuous)

def stop_background_enrichment(session_id: str) -> Dict:
    """Stop background enrichment processing for a session"""
    return trefle_batch_service.stop_background_processing(session_id)

def get_background_status(session_id: str) -> Dict:
    """Get status of background processing for a session"""
    return trefle_batch_service.get_background_status(session_id)

def get_enrichment_statistics() -> Dict[str, Any]:
    """Get overall enrichment statistics"""
    
    # Count enriched records
    enriched_count = db.session.query(OrchidRecord).filter(
        OrchidRecord.habitat_research.contains('"source": "trefle"')
    ).count()
    
    # Count FCOS records
    fcos_total = db.session.query(OrchidRecord).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).count()
    
    fcos_enriched = db.session.query(OrchidRecord).filter(
        and_(
            OrchidRecord.google_drive_id.isnot(None),
            OrchidRecord.habitat_research.contains('"source": "trefle"')
        )
    ).count()
    
    # Total records with scientific names
    total_processable = db.session.query(OrchidRecord).filter(
        and_(
            OrchidRecord.scientific_name.isnot(None),
            OrchidRecord.scientific_name != ''
        )
    ).count()
    
    # Recent session summary
    recent_sessions = db.session.query(TrefleEnrichmentTracker)\
        .order_by(TrefleEnrichmentTracker.created_at.desc())\
        .limit(5).all()
    
    return {
        'total_orchid_records': db.session.query(OrchidRecord).count(),
        'total_processable_records': total_processable,
        'enriched_records': enriched_count,
        'enrichment_percentage': round((enriched_count / total_processable * 100) if total_processable > 0 else 0, 2),
        'fcos_total_records': fcos_total,
        'fcos_enriched_records': fcos_enriched,
        'fcos_enrichment_percentage': round((fcos_enriched / fcos_total * 100) if fcos_total > 0 else 0, 2),
        'recent_sessions': [session.to_dict() for session in recent_sessions]
    }