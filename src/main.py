#!/usr/bin/env python3
"""
Orchid Terminology Integration System - Main Orchestrator
==========================================================

Integrates comprehensive botanical knowledge with the existing proven SVO extraction
system (user_svo_script.py). Maintains the 17x performance advantage while adding
botanical intelligence for enhanced orchid research and analysis.

This orchestrator seamlessly bridges:
- Existing high-performance SVO extraction (user_svo_script.py)
- Botanical terminology knowledge (Orchid_Floral_Glossary_Master.json)
- Database integration (models.py - SvoResult, OrchidTaxonomy)
- Web interface compatibility (svo_analysis_routes.py)
"""

import os
import sys
import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('orchid_terminology_system.log')
    ]
)
logger = logging.getLogger(__name__)

# Import the existing proven SVO extraction system
try:
    sys.path.append('..')  # Add parent directory for user_svo_script.py
    from user_svo_script import (
        fetch_all, parse_svo, clean_svo, analyze_svo,
        visualize_svo, save_results
    )
    SVO_SCRIPT_AVAILABLE = True
    logger.info("✅ Successfully imported proven SVO extraction system")
except ImportError as e:
    logger.warning(f"⚠️ Could not import user_svo_script.py: {str(e)}")
    # Create dummy functions for missing imports
    fetch_all = lambda urls: []
    parse_svo = lambda html: []
    clean_svo = lambda data: data or []
    analyze_svo = lambda data: {}
    visualize_svo = lambda data: None
    save_results = lambda data, name: None
    SVO_SCRIPT_AVAILABLE = False

# Import our botanical enhancement modules
try:
    from load_glossary import OrchidGlossaryLoader, get_glossary_loader
    from map_glossary_to_schema import GlossarySchemaMapper, get_schema_mapper
    from ai_trait_inference import BotanicalTraitInferenceEngine, get_inference_engine
    from database_interface import OrchidTerminologyDatabaseInterface, get_database_interface
    ENHANCEMENT_MODULES_AVAILABLE = True
    logger.info("✅ Successfully imported botanical enhancement modules")
except ImportError as e:
    logger.error(f"❌ Could not import enhancement modules: {str(e)}")
    # Create dummy functions for missing imports
    get_glossary_loader = lambda: None
    get_schema_mapper = lambda: None 
    get_inference_engine = lambda: None
    get_database_interface = lambda **kwargs: None
    ENHANCEMENT_MODULES_AVAILABLE = False

# Import Flask app and database models if available
try:
    from models import SvoResult, SvoAnalysisSession, OrchidTaxonomy, db
    from app import app
    FLASK_AVAILABLE = True
    logger.info("✅ Flask app and database models available")
except ImportError:
    logger.warning("⚠️ Flask app not available - running in standalone mode")
    from typing import cast, Any
    SvoResult = cast(Any, None)
    SvoAnalysisSession = cast(Any, None)
    OrchidTaxonomy = cast(Any, None)
    db = cast(Any, None)
    app = cast(Any, None)
    FLASK_AVAILABLE = False


class OrchidTerminologyOrchestrator:
    """
    Main orchestrator that integrates the proven SVO system with botanical intelligence.
    Designed to enhance, not replace, the existing 17x effective system.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or self._load_default_config()
        
        # Initialize components
        self.glossary_loader = None
        self.schema_mapper = None
        self.inference_engine = None
        self.database_interface = None
        
        # Performance tracking
        self.performance_stats = {
            'total_processed': 0,
            'enhancement_time': 0.0,
            'extraction_time': 0.0,
            'total_time': 0.0,
            'botanically_enhanced': 0,
            'high_confidence_results': 0
        }
        
        # Status flags
        self.initialized = False
        self.components_loaded = False
        
    def _load_default_config(self) -> Dict:
        """Load default configuration"""
        return {
            'glossary_path': 'data/glossary/Orchid_Floral_Glossary_Master.json',
            'output_dir': 'output',
            'enable_caching': True,
            'enable_database_integration': FLASK_AVAILABLE,
            'enable_web_integration': True,
            'max_retries': 3,
            'timeout': 10,
            'confidence_threshold': 0.7,
            'relevance_threshold': 0.5,
            'batch_size': 100,
            'preserve_original_performance': True
        }
    
    def initialize(self) -> bool:
        """Initialize all components of the terminology system"""
        if self.initialized:
            return True
            
        logger.info("🚀 Initializing Orchid Terminology Integration System...")
        
        try:
            # Initialize botanical components
            if ENHANCEMENT_MODULES_AVAILABLE:
                self.glossary_loader = get_glossary_loader()
                self.schema_mapper = get_schema_mapper()
                self.inference_engine = get_inference_engine()
                
                if self.config['enable_database_integration'] and FLASK_AVAILABLE:
                    self.database_interface = get_database_interface(flask_app=app)
                
                self.components_loaded = True
                logger.info("✅ Botanical enhancement components loaded")
            else:
                logger.warning("⚠️ Running without botanical enhancements")
            
            self.initialized = True
            logger.info("🎉 Orchid Terminology System initialized successfully!")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize system: {str(e)}")
            return False
    
    def analyze_urls_with_enhancement(self, urls: List[str], 
                                    session_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Main analysis method that combines proven SVO extraction with botanical enhancement.
        Maintains the performance advantage of user_svo_script.py while adding intelligence.
        
        Args:
            urls: List of URLs to analyze
            session_name: Optional session name for tracking
            
        Returns:
            Dictionary with comprehensive analysis results
        """
        if not self.initialized:
            self.initialize()
        
        start_time = time.time()
        session_name = session_name or f"Enhanced_Analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        logger.info(f"🔬 Starting enhanced SVO analysis for {len(urls)} URLs")
        
        # Initialize results structure
        analysis_results = {
            'session_name': session_name,
            'urls_processed': 0,
            'total_svo_extracted': 0,
            'botanically_enhanced': 0,
            'high_confidence_results': 0,
            'performance_metrics': {},
            'svo_results': [],
            'botanical_summary': {},
            'error_log': []
        }
        
        # Create database session if available
        session_id = None
        if self.config['enable_database_integration'] and FLASK_AVAILABLE:
            session_id = self._create_analysis_session(session_name, urls)
        
        try:
            # Process each URL using the proven extraction method
            for i, url in enumerate(urls):
                logger.info(f"📥 Processing URL {i+1}/{len(urls)}: {url}")
                
                try:
                    # Use the proven SVO extraction (maintains performance advantage)
                    extraction_start = time.time()
                    if SVO_SCRIPT_AVAILABLE:
                        try:
                            raw_html = asyncio.run(fetch_all([url]))
                            # Handle case where fetch_all returns a list
                            if isinstance(raw_html, list) and raw_html:
                                raw_html = raw_html[0]
                            elif isinstance(raw_html, list):
                                raw_html = None
                        except Exception as e:
                            logger.warning(f"SVO script failed for {url}: {e}")
                            raw_html = self._fallback_fetch(url)
                    else:
                        raw_html = self._fallback_fetch(url)
                    
                    if not raw_html:
                        analysis_results['error_log'].append(f"Failed to fetch: {url}")
                        continue
                    
                    # Extract SVO using proven method
                    svo_tuples = parse_svo([raw_html]) if SVO_SCRIPT_AVAILABLE else self._fallback_parse(raw_html)
                    cleaned_svo = clean_svo(svo_tuples) if SVO_SCRIPT_AVAILABLE else svo_tuples
                    
                    extraction_time = time.time() - extraction_start
                    self.performance_stats['extraction_time'] += extraction_time
                    
                    # Enhance with botanical knowledge (if available)
                    enhancement_start = time.time()
                    enhanced_results = []
                    
                    if self.components_loaded and self.inference_engine and cleaned_svo:
                        # Batch enhance for performance
                        enhanced_svo_list = self.inference_engine.batch_enhance_svo_results(
                            cleaned_svo, [raw_html[:500]] * len(cleaned_svo)  # Use first 500 chars as context
                        )
                        
                        for j, enhanced_svo in enumerate(enhanced_svo_list):
                            # Convert to database-compatible format
                            svo_data = {
                                'source_url': url,
                                'subject': enhanced_svo.subject,
                                'verb': enhanced_svo.verb,
                                'object': enhanced_svo.object,
                                'context_text': enhanced_svo.context_text,
                                'confidence_score': enhanced_svo.overall_confidence,
                                'relevance_score': enhanced_svo.botanical_relevance
                            }
                            
                            # Apply schema mapping enhancements
                            enhanced_data = self.schema_mapper.enhance_svo_result(svo_data) if self.schema_mapper else svo_data
                            
                            # Store in database if available
                            if session_id and self.database_interface and self.database_interface.models_available:
                                result_id = self.database_interface.create_enhanced_svo_result(
                                    enhanced_data, session_id
                                )
                                if result_id:
                                    enhanced_data['database_id'] = result_id
                            
                            enhanced_results.append(enhanced_data)
                            
                            # Track botanical enhancements
                            if enhanced_data.get('is_scientific_term'):
                                analysis_results['botanically_enhanced'] += 1
                            
                            if enhanced_data.get('confidence_score', 0) > self.config['confidence_threshold']:
                                analysis_results['high_confidence_results'] += 1
                    
                    else:
                        # Fallback to original format if enhancements not available
                        for subject, verb, obj in cleaned_svo:
                            svo_data = {
                                'source_url': url,
                                'subject': subject,
                                'verb': verb,
                                'object': obj,
                                'confidence_score': 1.0,
                                'relevance_score': 0.5
                            }
                            enhanced_results.append(svo_data)
                    
                    enhancement_time = time.time() - enhancement_start
                    self.performance_stats['enhancement_time'] += enhancement_time
                    
                    # Add to results
                    analysis_results['svo_results'].extend(enhanced_results)
                    analysis_results['urls_processed'] += 1
                    analysis_results['total_svo_extracted'] += len(enhanced_results)
                    
                    logger.info(f"✅ Processed {url}: {len(enhanced_results)} SVO tuples extracted")
                    
                except Exception as e:
                    error_msg = f"Error processing {url}: {str(e)}"
                    logger.error(error_msg)
                    analysis_results['error_log'].append(error_msg)
                    continue
            
            # Generate comprehensive analysis summary
            total_time = time.time() - start_time
            self.performance_stats['total_time'] = total_time
            self.performance_stats['total_processed'] = analysis_results['total_svo_extracted']
            
            analysis_results['performance_metrics'] = self._calculate_performance_metrics()
            
            # Generate botanical summary if enhancement available
            if self.components_loaded and analysis_results['svo_results']:
                analysis_results['botanical_summary'] = self._generate_botanical_summary(
                    analysis_results['svo_results']
                )
            
            # Save results using proven method (maintains compatibility)
            if SVO_SCRIPT_AVAILABLE:
                self._save_enhanced_results(analysis_results, session_name)
            
            # Update database session if available
            if session_id and self.database_interface and self.database_interface.models_available and FLASK_AVAILABLE:
                self._update_analysis_session(session_id, analysis_results)
            
            logger.info(f"🎉 Enhanced SVO analysis completed!")
            logger.info(f"📊 Results: {analysis_results['total_svo_extracted']} SVO tuples, "
                       f"{analysis_results['botanically_enhanced']} botanically enhanced, "
                       f"{analysis_results['high_confidence_results']} high confidence")
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"❌ Critical error in analysis: {str(e)}")
            analysis_results['error_log'].append(f"Critical error: {str(e)}")
            return analysis_results
    
    def _create_analysis_session(self, session_name: str, urls: List[str]) -> Optional[str]:
        """Create database session for tracking analysis"""
        if not FLASK_AVAILABLE or not app:
            return None
            
        try:
            with app.app_context():
                if not db or not SvoAnalysisSession:
                    return None
                    
                import uuid
                
                session = SvoAnalysisSession(
                    id=str(uuid.uuid4()),
                    session_name=session_name,
                    urls=urls,
                    status='running',
                    collection_type='enhanced_terminology_analysis'
                )
                
                db.session.add(session)
                db.session.commit()
                
                logger.info(f"📝 Created analysis session: {session.id}")
                return session.id
                
        except Exception as e:
            logger.error(f"Error creating analysis session: {str(e)}")
            return None
    
    def _update_analysis_session(self, session_id: str, results: Dict):
        """Update analysis session with results"""
        if not FLASK_AVAILABLE or not app:
            return
            
        try:
            with app.app_context():
                if not db or not SvoAnalysisSession:
                    return
                    
                session = SvoAnalysisSession.query.get(session_id)
                if session:
                    session.status = 'completed'
                    session.total_svo_found = results['total_svo_extracted']
                    session.completed_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"📊 Updated analysis session: {session_id}")
                    
        except Exception as e:
            logger.error(f"Error updating analysis session: {str(e)}")
    
    def _fallback_fetch(self, url: str) -> Optional[str]:
        """Fallback URL fetching if user_svo_script not available"""
        try:
            import requests
            response = requests.get(url, timeout=self.config['timeout'])
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Fallback fetch failed for {url}: {str(e)}")
            return None
    
    def _fallback_parse(self, html: str) -> List[Tuple[str, str, str]]:
        """Fallback SVO parsing if user_svo_script not available"""
        import re
        from bs4 import BeautifulSoup
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
            
            # Basic SVO pattern matching (simplified version)
            svo_pattern = r'(\w+)\s+(grows?|blooms?|shows?|displays?|has|produces?|requires?|needs?)\s+(\w+)'
            matches = re.findall(svo_pattern, text, re.IGNORECASE)
            
            return [(m[0].lower(), m[1].lower(), m[2].lower()) for m in matches]
            
        except Exception as e:
            logger.error(f"Fallback parsing failed: {str(e)}")
            return []
    
    def _calculate_performance_metrics(self) -> Dict[str, Any]:
        """Calculate performance metrics showing enhancement overhead"""
        total_time = self.performance_stats['total_time']
        extraction_time = self.performance_stats['extraction_time']
        enhancement_time = self.performance_stats['enhancement_time']
        total_processed = self.performance_stats['total_processed']
        
        metrics = {
            'total_processing_time': round(total_time, 2),
            'extraction_time': round(extraction_time, 2),
            'enhancement_time': round(enhancement_time, 2),
            'extraction_percentage': round((extraction_time / total_time) * 100, 1) if total_time > 0 else 0,
            'enhancement_overhead_percentage': round((enhancement_time / total_time) * 100, 1) if total_time > 0 else 0,
            'processing_rate': round(total_processed / total_time, 2) if total_time > 0 else 0,
            'items_per_second': round(total_processed / total_time, 2) if total_time > 0 else 0
        }
        
        # Check if we're maintaining performance advantage
        if metrics['enhancement_overhead_percentage'] < 20:
            metrics['performance_status'] = 'Excellent - Low overhead maintained'
        elif metrics['enhancement_overhead_percentage'] < 40:
            metrics['performance_status'] = 'Good - Acceptable overhead'
        else:
            metrics['performance_status'] = 'High overhead - Consider optimization'
        
        return metrics
    
    def _generate_botanical_summary(self, svo_results: List[Dict]) -> Dict[str, Any]:
        """Generate botanical analysis summary"""
        if not self.components_loaded:
            return {}
        
        try:
            # Calculate botanical metrics
            scientific_terms = [r for r in svo_results if r.get('is_scientific_term')]
            high_relevance = [r for r in svo_results if r.get('relevance_score', 0) > self.config['relevance_threshold']]
            
            # Category distribution
            categories = {}
            for result in svo_results:
                category = result.get('botanical_category')
                if category:
                    categories[category] = categories.get(category, 0) + 1
            
            # Confidence distribution
            confidence_ranges = {'high': 0, 'medium': 0, 'low': 0}
            for result in svo_results:
                confidence = result.get('confidence_score', 0)
                if confidence > 0.8:
                    confidence_ranges['high'] += 1
                elif confidence > 0.5:
                    confidence_ranges['medium'] += 1
                else:
                    confidence_ranges['low'] += 1
            
            summary = {
                'total_analyzed': len(svo_results),
                'scientific_terms_detected': len(scientific_terms),
                'scientific_term_rate': len(scientific_terms) / len(svo_results) if svo_results else 0,
                'high_relevance_results': len(high_relevance),
                'high_relevance_rate': len(high_relevance) / len(svo_results) if svo_results else 0,
                'category_distribution': categories,
                'confidence_distribution': confidence_ranges,
                'top_categories': sorted(categories.items(), key=lambda x: x[1], reverse=True)[:5]
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating botanical summary: {str(e)}")
            return {}
    
    def _save_enhanced_results(self, analysis_results: Dict, session_name: str):
        """Save enhanced results maintaining compatibility with original system"""
        try:
            output_dir = self.config['output_dir']
            os.makedirs(output_dir, exist_ok=True)
            
            # Save comprehensive results as JSON
            results_file = os.path.join(output_dir, f"{session_name}_enhanced_results.json")
            with open(results_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results, f, indent=2, ensure_ascii=False, default=str)
            
            # Save SVO results in original CSV format for compatibility
            csv_file = os.path.join(output_dir, f"{session_name}_svo_results.csv")
            import csv
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Subject', 'Verb', 'Object', 'Confidence', 'Relevance', 'Source_URL'])
                
                for result in analysis_results['svo_results']:
                    writer.writerow([
                        result.get('subject', ''),
                        result.get('verb', ''),
                        result.get('object', ''),
                        result.get('confidence_score', 1.0),
                        result.get('relevance_score', 0.5),
                        result.get('source_url', '')
                    ])
            
            # Save botanical summary
            summary_file = os.path.join(output_dir, f"{session_name}_botanical_summary.json")
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_results.get('botanical_summary', {}), f, indent=2)
            
            logger.info(f"💾 Enhanced results saved to {output_dir}")
            
        except Exception as e:
            logger.error(f"Error saving enhanced results: {str(e)}")
    
    def analyze_single_url(self, url: str) -> Dict[str, Any]:
        """Analyze a single URL (convenience method)"""
        return self.analyze_urls_with_enhancement([url])
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        status = {
            'system_initialized': self.initialized,
            'components_loaded': self.components_loaded,
            'svo_script_available': SVO_SCRIPT_AVAILABLE,
            'enhancement_modules_available': ENHANCEMENT_MODULES_AVAILABLE,
            'flask_integration_available': FLASK_AVAILABLE,
            'performance_stats': self.performance_stats,
            'config': self.config
        }
        
        if self.components_loaded:
            status['glossary_stats'] = self.glossary_loader.get_stats()
            status['schema_mapper_stats'] = self.schema_mapper.get_stats()
            status['inference_engine_stats'] = self.inference_engine.get_inference_stats()
            
            if self.database_interface:
                status['database_stats'] = self.database_interface.get_operation_stats()
        
        return status


def main():
    """Main entry point for the enhanced SVO analysis system"""
    
    print("🌺 Orchid Terminology Integration System")
    print("=" * 50)
    
    # Initialize the orchestrator
    orchestrator = OrchidTerminologyOrchestrator()
    
    if not orchestrator.initialize():
        print("❌ Failed to initialize system")
        return 1
    
    # Print system status
    status = orchestrator.get_system_status()
    print(f"✅ System Status:")
    print(f"  - SVO Script Available: {status['svo_script_available']}")
    print(f"  - Enhancement Modules: {status['enhancement_modules_available']}")
    print(f"  - Flask Integration: {status['flask_integration_available']}")
    
    if status['components_loaded']:
        glossary_stats = status.get('glossary_stats', {})
        print(f"  - Botanical Terms Loaded: {glossary_stats.get('total_terms', 0)}")
        print(f"  - Categories Available: {len(glossary_stats.get('categories', {}))}")
    
    # Example usage
    print("\n🔬 Running Example Analysis...")
    
    # Test URLs (replace with actual URLs for real analysis)
    test_urls = [
        "https://sunsetvalleyorchids.com/htm/archive.html"
        # Add more URLs as needed
    ]
    
    try:
        results = orchestrator.analyze_urls_with_enhancement(
            test_urls, 
            session_name="Demo_Enhanced_Analysis"
        )
        
        print(f"\n📊 Analysis Results:")
        print(f"  - URLs Processed: {results['urls_processed']}")
        print(f"  - SVO Tuples Extracted: {results['total_svo_extracted']}")
        print(f"  - Botanically Enhanced: {results['botanically_enhanced']}")
        print(f"  - High Confidence Results: {results['high_confidence_results']}")
        
        performance = results.get('performance_metrics', {})
        if performance:
            print(f"  - Processing Rate: {performance.get('items_per_second', 0)} items/sec")
            print(f"  - Enhancement Overhead: {performance.get('enhancement_overhead_percentage', 0)}%")
            print(f"  - Performance Status: {performance.get('performance_status', 'Unknown')}")
        
        print(f"\n🎉 Enhanced analysis completed successfully!")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Analysis failed: {str(e)}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)