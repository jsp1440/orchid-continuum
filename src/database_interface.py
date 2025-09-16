#!/usr/bin/env python3
"""
Database Interface for Orchid Terminology Management
====================================================

Provides CRUD operations and database integration for the orchid terminology system.
Seamlessly integrates with existing Flask/SQLAlchemy models while adding botanical
intelligence to SVO analysis and orchid taxonomy management.
"""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from datetime import datetime, timedelta
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy import and_, or_, func, text
import json

logger = logging.getLogger(__name__)

# Import database models and app context with proper typing guards
try:
    from models import (SvoResult, SvoAnalysisSession, OrchidTaxonomy, 
                       SvoAnalysisSummary, OrchidTaxonomyValidation, db)
    from app import app
    MODELS_AVAILABLE = True
except Exception:
    from typing import cast, Any
    SvoResult = cast(Any, None)
    SvoAnalysisSession = cast(Any, None) 
    OrchidTaxonomy = cast(Any, None)
    SvoAnalysisSummary = cast(Any, None)
    OrchidTaxonomyValidation = cast(Any, None)
    db = cast(Any, None)
    app = cast(Any, None)
    MODELS_AVAILABLE = False
    logger.warning("Database models not available - running in standalone mode")

# Import enhancement modules with factory functions
try:
    from load_glossary import get_glossary_loader
    from map_glossary_to_schema import get_schema_mapper
    from ai_trait_inference import get_inference_engine
except ImportError:
    logger.warning("Enhancement modules not available")
    get_glossary_loader = lambda: None
    get_schema_mapper = lambda: None
    get_inference_engine = lambda: None

class OrchidTerminologyDatabaseInterface:
    """
    Database interface for managing orchid terminology and enhanced SVO results.
    Integrates botanical knowledge with existing database schema.
    """
    
    def __init__(self, flask_app=None):
        self.flask_app = flask_app or app
        self.models_available = MODELS_AVAILABLE
        self.glossary_loader = get_glossary_loader()
        self.schema_mapper = get_schema_mapper()
        self.inference_engine = get_inference_engine()
        
        # Cache for frequently accessed data
        self._taxonomy_cache = {}
        self._term_cache = {}
        
        # Performance tracking
        self.operation_stats = {
            'queries_executed': 0,
            'cache_hits': 0,
            'enhancement_operations': 0
        }
    
    def _app_ctx(self):
        """Get Flask app context - helper for database operations"""
        if self.flask_app and hasattr(self.flask_app, 'app_context'):
            return self.flask_app.app_context()
        else:
            # Return a no-op context manager for standalone mode
            from contextlib import nullcontext
            return nullcontext()
    
    def create_enhanced_svo_result(self, svo_data: Dict, session_id: str) -> Optional[int]:
        """
        Create a new SvoResult with botanical enhancement.
        
        Args:
            svo_data: Dictionary with SVO data (subject, verb, object, context, etc.)
            session_id: SVO analysis session ID
            
        Returns:
            ID of created SvoResult or None if failed
        """
        if not self.models_available or not db or not SvoResult:
            logger.error("Database models not available")
            return None
        
        try:
            with self._app_ctx():
                # Enhance the SVO data with botanical knowledge
                enhanced_data = self.schema_mapper.enhance_svo_result(svo_data) if self.schema_mapper else {}
                
                # Create SvoResult object with proper model validation
                if not SvoResult:
                    logger.error("SvoResult model not available")
                    return None
                    
                svo_result = SvoResult()
                svo_result.session_id = session_id
                svo_result.source_url = svo_data.get('source_url', '')
                svo_result.subject = svo_data.get('subject', '')
                svo_result.verb = svo_data.get('verb', '')
                svo_result.object = svo_data.get('object', '')
                svo_result.subject_clean = svo_data.get('subject_clean', svo_data.get('subject', '').lower().strip())
                svo_result.verb_clean = svo_data.get('verb_clean', svo_data.get('verb', '').lower().strip())
                svo_result.object_clean = svo_data.get('object_clean', svo_data.get('object', '').lower().strip())
                svo_result.context_text = svo_data.get('context_text', '')
                svo_result.confidence_score = enhanced_data.get('confidence_score', 1.0)
                svo_result.botanical_category = enhanced_data.get('botanical_category')
                svo_result.is_scientific_term = enhanced_data.get('is_scientific_term', False)
                svo_result.relevance_score = enhanced_data.get('relevance_score', 0.5)
                
                db.session.add(svo_result)
                db.session.commit()
                
                self.operation_stats['enhancement_operations'] += 1
                logger.info(f"Created enhanced SVO result with ID: {svo_result.id}")
                
                return svo_result.id
                
        except Exception as e:
            logger.error(f"Error creating enhanced SVO result: {str(e)}")
            if db and db.session:
                db.session.rollback()
            return None
    
    def bulk_create_enhanced_svo_results(self, svo_data_list: List[Dict], 
                                       session_id: str) -> List[int]:
        """
        Bulk create enhanced SVO results for better performance.
        
        Args:
            svo_data_list: List of SVO data dictionaries
            session_id: SVO analysis session ID
            
        Returns:
            List of created SvoResult IDs
        """
        if not self.models_available or not db or not SvoResult:
            logger.error("Database models not available")
            return []
        
        created_ids = []
        
        try:
            with self._app_ctx():
                # Prepare batch insert data
                svo_objects = []
                
                for svo_data in svo_data_list:
                    # Enhance each SVO with botanical knowledge
                    enhanced_data = self.schema_mapper.enhance_svo_result(svo_data) if self.schema_mapper else {}
                    
                    if not SvoResult:
                        logger.error("SvoResult model not available")
                        continue
                        
                    svo_result = SvoResult()
                    svo_result.session_id = session_id
                    svo_result.source_url = svo_data.get('source_url', '')
                    svo_result.subject = svo_data.get('subject', '')
                    svo_result.verb = svo_data.get('verb', '')
                    svo_result.object = svo_data.get('object', '')
                    svo_result.subject_clean = svo_data.get('subject_clean', svo_data.get('subject', '').lower().strip())
                    svo_result.verb_clean = svo_data.get('verb_clean', svo_data.get('verb', '').lower().strip())
                    svo_result.object_clean = svo_data.get('object_clean', svo_data.get('object', '').lower().strip())
                    svo_result.context_text = svo_data.get('context_text', '')
                    svo_result.confidence_score = enhanced_data.get('confidence_score', 1.0)
                    svo_result.botanical_category = enhanced_data.get('botanical_category')
                    svo_result.is_scientific_term = enhanced_data.get('is_scientific_term', False)
                    svo_result.relevance_score = enhanced_data.get('relevance_score', 0.5)
                    svo_objects.append(svo_result)
                
                # Bulk insert
                db.session.add_all(svo_objects)
                db.session.commit()
                
                # Get the created IDs
                created_ids = [svo.id for svo in svo_objects]
                
                self.operation_stats['enhancement_operations'] += len(created_ids)
                logger.info(f"Bulk created {len(created_ids)} enhanced SVO results")
                
                return created_ids
                
        except Exception as e:
            logger.error(f"Error in bulk SVO creation: {str(e)}")
            if db and db.session:
                db.session.rollback()
            return []
    
    def get_enhanced_svo_results(self, session_id: str, 
                               categories: Optional[List[str]] = None,
                               min_relevance: float = 0.0) -> List[Dict]:
        """
        Retrieve enhanced SVO results with optional filtering.
        
        Args:
            session_id: SVO analysis session ID
            categories: Optional list of botanical categories to filter by
            min_relevance: Minimum relevance score threshold
            
        Returns:
            List of enhanced SVO result dictionaries
        """
        if not self.models_available or not db or not SvoResult:
            return []
        
        try:
            with self._app_ctx():
                query = SvoResult.query.filter(SvoResult.session_id == session_id)
                
                # Apply filters
                if categories:
                    query = query.filter(SvoResult.botanical_category.in_(categories))
                
                if min_relevance > 0:
                    query = query.filter(SvoResult.relevance_score >= min_relevance)
                
                # Execute query
                results = query.all()
                self.operation_stats['queries_executed'] += 1
                
                # Convert to dictionaries with additional enhancement info
                enhanced_results = []
                for result in results:
                    result_dict = result.to_dict()
                    
                    # Add botanical enhancement information
                    if result.is_scientific_term:
                        # Get additional term information from glossary
                        full_text = f"{result.subject} {result.verb} {result.object}"
                        botanical_terms = self.glossary_loader.find_terms_in_text(full_text) if self.glossary_loader else []
                        result_dict['detected_botanical_terms'] = [term[0] for term in botanical_terms]
                        result_dict['botanical_definitions'] = {
                            term[0]: (term[1] or {}).get('definition', '') 
                            for term in botanical_terms
                        }
                    
                    enhanced_results.append(result_dict)
                
                logger.info(f"Retrieved {len(enhanced_results)} enhanced SVO results")
                return enhanced_results
                
        except Exception as e:
            logger.error(f"Error retrieving enhanced SVO results: {str(e)}")
            return []
    
    def update_orchid_taxonomy(self, scientific_name: str, 
                             taxonomy_data: Dict) -> bool:
        """
        Update or create orchid taxonomy entry with enhanced data.
        
        Args:
            scientific_name: Scientific name of the orchid
            taxonomy_data: Dictionary with taxonomy information
            
        Returns:
            True if successful, False otherwise
        """
        if not self.models_available or not db or not OrchidTaxonomy:
            return False
        
        try:
            with self._app_ctx():
                # Check if taxonomy entry exists
                taxonomy = OrchidTaxonomy.query.filter_by(
                    scientific_name=scientific_name
                ).first()
                
                if taxonomy:
                    # Update existing entry
                    for key, value in taxonomy_data.items():
                        if hasattr(taxonomy, key):
                            setattr(taxonomy, key, value)
                    taxonomy.updated_at = datetime.utcnow()
                else:
                    # Create new entry with proper model validation
                    if not OrchidTaxonomy:
                        logger.error("OrchidTaxonomy model not available")
                        return False
                        
                    taxonomy = OrchidTaxonomy()
                    taxonomy.scientific_name = scientific_name
                    taxonomy.genus = taxonomy_data.get('genus', '')
                    taxonomy.species = taxonomy_data.get('species', '')
                    taxonomy.author = taxonomy_data.get('author', '')
                    taxonomy.synonyms = json.dumps(taxonomy_data.get('synonyms', []))
                    taxonomy.common_names = json.dumps(taxonomy_data.get('common_names', []))
                    db.session.add(taxonomy)
                
                db.session.commit()
                self.operation_stats['enhancement_operations'] += 1
                logger.info(f"Updated taxonomy for: {scientific_name}")
                
                return True
                
        except Exception as e:
            logger.error(f"Error updating orchid taxonomy: {str(e)}")
            if db and db.session:
                db.session.rollback()
            return False
    
    def search_orchid_taxonomy(self, search_term: str, 
                             search_type: str = 'all') -> List[Dict]:
        """
        Search orchid taxonomy with botanical term enhancement.
        
        Args:
            search_term: Term to search for
            search_type: Type of search ('genus', 'species', 'common', 'all')
            
        Returns:
            List of matching taxonomy entries
        """
        if not self.models_available or not db or not OrchidTaxonomy:
            return []
        
        # Check cache first
        cache_key = f"{search_term}_{search_type}"
        if cache_key in self._taxonomy_cache:
            self.operation_stats['cache_hits'] += 1
            return self._taxonomy_cache[cache_key]
        
        try:
            with self._app_ctx():
                query = OrchidTaxonomy.query
                
                search_term_lower = search_term.lower()
                
                if search_type == 'genus':
                    query = query.filter(
                        func.lower(OrchidTaxonomy.genus).contains(search_term_lower)
                    )
                elif search_type == 'species':
                    query = query.filter(
                        func.lower(OrchidTaxonomy.species).contains(search_term_lower)
                    )
                elif search_type == 'common':
                    query = query.filter(
                        func.lower(OrchidTaxonomy.common_names).contains(search_term_lower)
                    )
                else:  # search_type == 'all'
                    query = query.filter(
                        or_(
                            func.lower(OrchidTaxonomy.scientific_name).contains(search_term_lower),
                            func.lower(OrchidTaxonomy.genus).contains(search_term_lower),
                            func.lower(OrchidTaxonomy.species).contains(search_term_lower),
                            func.lower(OrchidTaxonomy.common_names).contains(search_term_lower),
                            func.lower(OrchidTaxonomy.synonyms).contains(search_term_lower)
                        )
                    )
                
                results = query.all()
                self.operation_stats['queries_executed'] += 1
                
                # Convert to dictionaries and enhance with botanical information
                taxonomy_results = []
                for result in results:
                    result_dict = {
                        'id': result.id,
                        'scientific_name': result.scientific_name,
                        'genus': result.genus,
                        'species': result.species,
                        'author': result.author,
                        'synonyms': json.loads(result.synonyms) if result.synonyms else [],
                        'common_names': json.loads(result.common_names) if result.common_names else [],
                        'created_at': result.created_at.isoformat() if result.created_at else None,
                        'updated_at': result.updated_at.isoformat() if result.updated_at else None
                    }
                    
                    # Add botanical term analysis
                    full_name_text = f"{result.scientific_name} {result.genus} {result.species}"
                    botanical_terms = self.glossary_loader.find_terms_in_text(full_name_text) if self.glossary_loader else []
                    if botanical_terms:
                        result_dict['related_botanical_terms'] = [term[0] for term in botanical_terms]
                    
                    taxonomy_results.append(result_dict)
                
                # Cache the results
                self._taxonomy_cache[cache_key] = taxonomy_results
                
                logger.info(f"Found {len(taxonomy_results)} taxonomy matches for: {search_term}")
                return taxonomy_results
                
        except Exception as e:
            logger.error(f"Error searching orchid taxonomy: {str(e)}")
            return []
    
    def get_botanical_analysis_summary(self, session_id: str) -> Dict[str, Any]:
        """
        Generate comprehensive botanical analysis summary for a session.
        
        Args:
            session_id: SVO analysis session ID
            
        Returns:
            Dictionary with botanical analysis summary
        """
        if not self.models_available or not db or not SvoResult or not SvoAnalysisSession:
            return {}
        
        try:
            with self._app_ctx():
                # Get all SVO results for the session
                svo_results = SvoResult.query.filter(
                    SvoResult.session_id == session_id
                ).all()
                
                if not svo_results:
                    return {}
                
                # Calculate botanical metrics
                total_results = len(svo_results)
                scientific_terms = sum(1 for r in svo_results if r.is_scientific_term)
                
                # Category distribution
                category_counts = {}
                relevance_scores = []
                confidence_scores = []
                
                for result in svo_results:
                    if result.botanical_category:
                        category_counts[result.botanical_category] = category_counts.get(result.botanical_category, 0) + 1
                    
                    if result.relevance_score:
                        relevance_scores.append(result.relevance_score)
                    
                    if result.confidence_score:
                        confidence_scores.append(result.confidence_score)
                
                # Calculate averages
                avg_relevance = sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0
                avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
                
                # Get session information
                session = SvoAnalysisSession.query.get(session_id)
                session_info = session.to_dict() if session else {}
                
                summary = {
                    'session_id': session_id,
                    'session_info': session_info,
                    'botanical_metrics': {
                        'total_svo_results': total_results,
                        'scientific_terms_detected': scientific_terms,
                        'scientific_term_rate': scientific_terms / total_results if total_results > 0 else 0,
                        'category_distribution': category_counts,
                        'average_relevance_score': round(avg_relevance, 3),
                        'average_confidence_score': round(avg_confidence, 3),
                        'high_relevance_results': len([s for s in relevance_scores if s > 0.7]),
                        'high_confidence_results': len([s for s in confidence_scores if s > 0.8])
                    },
                    'top_categories': sorted(category_counts.items(), key=lambda x: x[1], reverse=True)[:5],
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                
                self.operation_stats['queries_executed'] += 2
                logger.info(f"Generated botanical analysis summary for session: {session_id}")
                
                return summary
                
        except Exception as e:
            logger.error(f"Error generating botanical summary: {str(e)}")
            return {}
    
    def cleanup_old_data(self, days_old: int = 30) -> Dict[str, int]:
        """
        Clean up old SVO analysis data and taxonomy entries.
        
        Args:
            days_old: Number of days old to consider for cleanup
            
        Returns:
            Dictionary with cleanup statistics
        """
        if not self.models_available or not db or not SvoAnalysisSession or not SvoResult or not SvoAnalysisSummary:
            return {}
        
        cleanup_stats = {
            'old_svo_sessions_removed': 0,
            'old_svo_results_removed': 0,
            'orphaned_summaries_removed': 0
        }
        
        try:
            with self._app_ctx():
                cutoff_date = datetime.utcnow() - timedelta(days=days_old)
                
                # Find old sessions
                old_sessions = SvoAnalysisSession.query.filter(
                    SvoAnalysisSession.created_at < cutoff_date
                ).all()
                
                for session in old_sessions:
                    session_id = session.id
                    
                    # Remove associated SVO results
                    old_results = SvoResult.query.filter(
                        SvoResult.session_id == session_id
                    ).all()
                    
                    for result in old_results:
                        db.session.delete(result)
                    
                    cleanup_stats['old_svo_results_removed'] += len(old_results)
                    
                    # Remove associated summaries
                    old_summary = SvoAnalysisSummary.query.filter(
                        SvoAnalysisSummary.session_id == session_id
                    ).first()
                    
                    if old_summary:
                        db.session.delete(old_summary)
                        cleanup_stats['orphaned_summaries_removed'] += 1
                    
                    # Remove the session itself
                    db.session.delete(session)
                    cleanup_stats['old_svo_sessions_removed'] += 1
                
                db.session.commit()
                
                logger.info(f"Cleanup completed: {cleanup_stats}")
                return cleanup_stats
                
        except Exception as e:
            logger.error(f"Error during data cleanup: {str(e)}")
            if db and db.session:
                db.session.rollback()
            return cleanup_stats
    
    def get_operation_stats(self) -> Dict[str, Any]:
        """Get database operation statistics"""
        return {
            **self.operation_stats,
            'cache_size': len(self._taxonomy_cache),
            'glossary_terms_loaded': len(self.glossary_loader._glossary_data.get('terms', {})) if (self.glossary_loader and hasattr(self.glossary_loader, '_glossary_data') and self.glossary_loader._glossary_data) else 0,
            'schema_mappings_available': len(self.schema_mapper._mappings) if (self.schema_mapper and hasattr(self.schema_mapper, '_initialized') and hasattr(self.schema_mapper, '_mappings') and self.schema_mapper._initialized) else 0
        }
    
    def clear_caches(self):
        """Clear internal caches"""
        self._taxonomy_cache.clear()
        self._term_cache.clear()
        logger.info("Database interface caches cleared")


# Global database interface instance
_global_db_interface = None

def get_database_interface(flask_app=None) -> OrchidTerminologyDatabaseInterface:
    """Get global database interface instance with optional flask app"""
    global _global_db_interface
    if _global_db_interface is None:
        _global_db_interface = OrchidTerminologyDatabaseInterface(flask_app=flask_app)
    return _global_db_interface


# Convenience functions for common operations
def create_enhanced_svo(svo_data: Dict, session_id: str, flask_app=None) -> Optional[int]:
    """Create enhanced SVO result - convenience function"""
    interface = get_database_interface(flask_app)
    return interface.create_enhanced_svo_result(svo_data, session_id)

def search_orchid_by_name(name: str, flask_app=None) -> List[Dict]:
    """Search orchid taxonomy by name - convenience function"""
    interface = get_database_interface(flask_app)
    return interface.search_orchid_taxonomy(name)


if __name__ == "__main__":
    # Test database interface (requires Flask app context)
    if MODELS_AVAILABLE:
        interface = OrchidTerminologyDatabaseInterface()
        print("✅ Database interface initialized!")
        print(f"📊 Stats: {interface.get_operation_stats()}")
        
        # Test search functionality
        results = interface.search_orchid_taxonomy("Phalaenopsis", "genus")
        print(f"🔍 Found {len(results)} Phalaenopsis entries")
        
    else:
        print("⚠️ Database models not available - interface running in standalone mode")
        print("💡 Run from Flask app context to test database operations")