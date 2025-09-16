#!/usr/bin/env python3
"""
Unified Orchid Continuum Data Flow System
Orchestrates the complete integration between SVO Scraper, Google Cloud, and AI Breeder Pro
Implements the unified data flow: SVO Scraper → Database + Google Sheets → Google Drive → AI Analysis
"""

import os
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedOrchidContinuum:
    """
    Unified orchestration system for the complete orchid breeding data pipeline
    """
    
    def __init__(self):
        """Initialize all integrated components"""
        self.google_integration = None
        self.svo_scraper = None
        self.ai_breeder = None
        self.enhanced_ai = None
        
        # Initialize components with graceful fallbacks
        self._initialize_components()
        
        # Track data flow status
        self.data_flow_status = {
            'svo_scraping': 'idle',
            'database_sync': 'idle',
            'google_sheets_sync': 'idle',
            'google_drive_sync': 'idle',
            'ai_analysis': 'idle',
            'last_sync': None
        }
        
        logger.info("🌺 Unified Orchid Continuum initialized successfully")
    
    def _initialize_components(self):
        """Initialize all system components with fallback handling"""
        try:
            # Initialize Google Cloud integration
            from google_cloud_integration import get_google_integration
            self.google_integration = get_google_integration()
            if self.google_integration and self.google_integration.is_available():
                logger.info("✅ Google Cloud integration active")
            else:
                logger.warning("⚠️ Google Cloud integration not available")
        except ImportError:
            logger.warning("⚠️ Google Cloud integration module not found")
        
        try:
            # Initialize SVO Enhanced Scraper
            from svo_enhanced_scraper import SunsetValleyOrchidsEnhancedScraper
            self.svo_scraper = SunsetValleyOrchidsEnhancedScraper()
            logger.info("✅ SVO Enhanced Scraper initialized")
        except ImportError:
            logger.warning("⚠️ SVO Enhanced Scraper not available")
        
        try:
            # Initialize AI Breeder Pro
            from ai_breeder_assistant_pro import UnifiedBreederAssistant
            self.ai_breeder = UnifiedBreederAssistant()
            logger.info("✅ AI Breeder Pro initialized")
        except ImportError:
            logger.warning("⚠️ AI Breeder Pro not available")
        
        try:
            # Initialize Enhanced AI Analysis
            from enhanced_ai_analysis import (
                enhanced_image_analysis_with_drive_upload,
                save_breeding_analysis_with_cloud_integration
            )
            self.enhanced_ai = {
                'image_analysis': enhanced_image_analysis_with_drive_upload,
                'save_analysis': save_breeding_analysis_with_cloud_integration
            }
            logger.info("✅ Enhanced AI Analysis initialized")
        except ImportError:
            logger.warning("⚠️ Enhanced AI Analysis not available")
    
    def execute_unified_data_flow(self, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Execute the complete unified data flow pipeline
        """
        if not config:
            config = self._get_default_config()
        
        logger.info("🚀 Starting unified orchid breeding data flow pipeline")
        
        results = {
            'pipeline_id': f"unified_flow_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'start_time': datetime.now().isoformat(),
            'stages': {},
            'summary': {},
            'errors': []
        }
        
        try:
            # Stage 1: SVO Data Harvesting
            if config.get('enable_svo_scraping', True):
                svo_results = self._execute_svo_harvesting(config.get('svo_config', {}))
                results['stages']['svo_harvesting'] = svo_results
                self.data_flow_status['svo_scraping'] = 'completed'
            
            # Stage 2: Database + Google Sheets Synchronization
            if config.get('enable_data_sync', True):
                sync_results = self._execute_data_synchronization(results['stages'].get('svo_harvesting', {}))
                results['stages']['data_sync'] = sync_results
                self.data_flow_status['database_sync'] = 'completed'
                self.data_flow_status['google_sheets_sync'] = 'completed'
            
            # Stage 3: Image Processing + Google Drive Upload
            if config.get('enable_image_processing', True):
                image_results = self._execute_image_processing(results['stages'].get('svo_harvesting', {}))
                results['stages']['image_processing'] = image_results
                self.data_flow_status['google_drive_sync'] = 'completed'
            
            # Stage 4: Enhanced AI Analysis
            if config.get('enable_ai_analysis', True):
                ai_results = self._execute_ai_analysis_pipeline(results['stages'])
                results['stages']['ai_analysis'] = ai_results
                self.data_flow_status['ai_analysis'] = 'completed'
            
            # Stage 5: Generate Final Summary
            results['summary'] = self._generate_pipeline_summary(results['stages'])
            results['end_time'] = datetime.now().isoformat()
            results['success'] = True
            
            # Update status
            self.data_flow_status['last_sync'] = datetime.now().isoformat()
            
            logger.info("✅ Unified data flow pipeline completed successfully")
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {e}")
            results['error'] = str(e)
            results['success'] = False
            results['end_time'] = datetime.now().isoformat()
        
        return results
    
    def _execute_svo_harvesting(self, svo_config: Dict[str, Any]) -> Dict[str, Any]:
        """Execute SVO data harvesting with enhanced Google Drive integration"""
        logger.info("📡 Stage 1: SVO Data Harvesting")
        
        if not self.svo_scraper:
            return {'error': 'SVO Scraper not available', 'data_count': 0}
        
        try:
            # Configure scraper with Google integration
            if self.google_integration:
                self.svo_scraper.google_integration = self.google_integration
            
            # Run enhanced scraping
            scraped_data = self.svo_scraper.scrape_svo_complete(
                genera=[svo_config.get('genus', 'Sarcochilus')],
                years=list(range(svo_config.get('year_range', (2020, 2024))[0], svo_config.get('year_range', (2020, 2024))[1] + 1)),
                max_pages=svo_config.get('max_pages', 5)
            )
            
            return {
                'status': 'success',
                'data_count': len(scraped_data) if scraped_data else 0,
                'scraped_data': scraped_data,
                'google_drive_enabled': self.google_integration is not None,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ SVO harvesting failed: {e}")
            return {'error': str(e), 'status': 'failed', 'data_count': 0}
    
    def _execute_data_synchronization(self, svo_results: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize data to database and Google Sheets"""
        logger.info("📊 Stage 2: Database + Google Sheets Synchronization")
        
        sync_results = {
            'database_sync': {'status': 'skipped', 'records': 0},
            'google_sheets_sync': {'status': 'skipped', 'records': 0}
        }
        
        scraped_data = svo_results.get('scraped_data', [])
        if not scraped_data:
            return sync_results
        
        try:
            # Database synchronization (existing database models)
            if hasattr(self, '_sync_to_database'):
                db_result = self._sync_to_database(scraped_data)
                sync_results['database_sync'] = db_result
            
            # Google Sheets synchronization
            if self.google_integration and self.google_integration.is_available():
                sheets_result = self._sync_to_google_sheets(scraped_data)
                sync_results['google_sheets_sync'] = sheets_result
            
        except Exception as e:
            logger.error(f"❌ Data synchronization failed: {e}")
            sync_results['database_sync']['error'] = str(e)
            sync_results['google_sheets_sync']['error'] = str(e)
        
        return sync_results
    
    def _sync_to_database(self, scraped_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronize scraped data to database"""
        try:
            if self.svo_scraper and hasattr(self.svo_scraper, 'store_hybrids_in_database'):
                # Use the SVO scraper's database storage method
                self.svo_scraper.store_hybrids_in_database(scraped_data)
                return {
                    'status': 'success',
                    'records': len(scraped_data),
                    'timestamp': datetime.now().isoformat()
                }
            else:
                return {
                    'status': 'skipped',
                    'reason': 'SVO scraper database method not available',
                    'records': 0
                }
        except Exception as e:
            logger.error(f"❌ Database synchronization failed: {e}")
            return {
                'status': 'failed',
                'error': str(e),
                'records': 0
            }
    
    def _execute_image_processing(self, svo_results: Dict[str, Any]) -> Dict[str, Any]:
        """Process images and upload to Google Drive"""
        logger.info("📸 Stage 3: Image Processing + Google Drive Upload")
        
        if not self.google_integration:
            return {'status': 'skipped', 'reason': 'Google Drive not available'}
        
        image_results = {
            'processed_images': 0,
            'uploaded_to_drive': 0,
            'drive_urls': [],
            'errors': []
        }
        
        try:
            scraped_data = svo_results.get('scraped_data', [])
            
            for item in scraped_data:
                # Process images from scraped data
                image_paths = item.get('image_paths', '').split(', ')
                
                for image_path in image_paths:
                    if image_path.strip() and os.path.exists(image_path.strip()):
                        try:
                            # Upload to Google Drive
                            with open(image_path.strip(), 'rb') as f:
                                image_data = f.read()
                            
                            filename = f"{item.get('name', 'unknown')}_{os.path.basename(image_path)}"
                            drive_url = self.google_integration.upload_image_to_drive(image_data, filename)
                            
                            if drive_url:
                                image_results['uploaded_to_drive'] += 1
                                image_results['drive_urls'].append(drive_url)
                            
                            image_results['processed_images'] += 1
                            
                        except Exception as e:
                            image_results['errors'].append(f"Failed to process {image_path}: {str(e)}")
            
            image_results['status'] = 'success'
            
        except Exception as e:
            logger.error(f"❌ Image processing failed: {e}")
            image_results['error'] = str(e)
            image_results['status'] = 'failed'
        
        return image_results
    
    def _execute_ai_analysis_pipeline(self, pipeline_stages: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comprehensive AI analysis on processed data"""
        logger.info("🤖 Stage 4: Enhanced AI Analysis Pipeline")
        
        if not self.enhanced_ai:
            return {'status': 'skipped', 'reason': 'Enhanced AI not available'}
        
        ai_results = {
            'analyzed_items': 0,
            'breeding_predictions': [],
            'trait_analyses': [],
            'success_ratings': [],
            'recommendations': []
        }
        
        try:
            # Get data from previous stages
            svo_data = pipeline_stages.get('svo_harvesting', {}).get('scraped_data', [])
            image_data = pipeline_stages.get('image_processing', {})
            
            for item in svo_data:
                try:
                    # Prepare breeding analysis data
                    breeding_analysis = {
                        'hybrid_name': item.get('name', 'Unknown'),
                        'parent1': item.get('parent1', ''),
                        'parent2': item.get('parent2', ''),
                        'genus': item.get('genus', 'Sarcochilus'),
                        'notes': item.get('notes', ''),
                        'drive_urls': item.get('image_urls', ''),
                        'analysis_timestamp': datetime.now().isoformat()
                    }
                    
                    # Enhanced AI analysis if available
                    if self.ai_breeder:
                        # Use AI Breeder Pro for comprehensive analysis
                        parent1_data = {'name': item.get('parent1', ''), 'genus': item.get('genus', '')}
                        parent2_data = {'name': item.get('parent2', ''), 'genus': item.get('genus', '')}
                        breeding_goals = ['Enhanced flower quality', 'Improved vigor', 'Color development']
                        
                        analysis_result = self.ai_breeder.analyze_proposed_cross(
                            parent1_data, parent2_data, breeding_goals
                        )
                        
                        breeding_analysis['ai_analysis'] = analysis_result
                        ai_results['breeding_predictions'].append(analysis_result)
                    
                    # Save analysis to Google Sheets if available
                    if self.google_integration:
                        save_success = self.enhanced_ai['save_analysis'](
                            breeding_analysis, self.google_integration
                        )
                        breeding_analysis['saved_to_sheets'] = save_success
                    
                    ai_results['analyzed_items'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ Failed to analyze {item.get('name', 'unknown')}: {e}")
            
            ai_results['status'] = 'success'
            
        except Exception as e:
            logger.error(f"❌ AI analysis pipeline failed: {e}")
            ai_results['error'] = str(e)
            ai_results['status'] = 'failed'
        
        return ai_results
    
    def _sync_to_google_sheets(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Synchronize data to Google Sheets"""
        if not self.google_integration:
            return {'status': 'failed', 'reason': 'Google integration not available'}
        
        try:
            synced_count = 0
            for item in data:
                success = self.google_integration.save_svo_data(item)
                if success:
                    synced_count += 1
            
            return {
                'status': 'success',
                'records': synced_count,
                'total_attempted': len(data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {'status': 'failed', 'error': str(e), 'records': 0}
    
    def _generate_pipeline_summary(self, stages: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive pipeline summary"""
        summary = {
            'total_stages': len(stages),
            'successful_stages': 0,
            'failed_stages': 0,
            'data_processed': {
                'svo_records': 0,
                'images_processed': 0,
                'ai_analyses': 0
            },
            'cloud_integration': {
                'google_sheets_active': self.google_integration is not None,
                'google_drive_active': self.google_integration is not None,
                'records_in_sheets': 0,
                'images_in_drive': 0
            },
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Count successful vs failed stages
        for stage_name, stage_data in stages.items():
            if stage_data.get('status') == 'success' or stage_data.get('success', False):
                summary['successful_stages'] += 1
            else:
                summary['failed_stages'] += 1
        
        # Aggregate data counts
        if 'svo_harvesting' in stages:
            summary['data_processed']['svo_records'] = stages['svo_harvesting'].get('data_count', 0)
        
        if 'image_processing' in stages:
            summary['data_processed']['images_processed'] = stages['image_processing'].get('processed_images', 0)
            summary['cloud_integration']['images_in_drive'] = stages['image_processing'].get('uploaded_to_drive', 0)
        
        if 'ai_analysis' in stages:
            summary['data_processed']['ai_analyses'] = stages['ai_analysis'].get('analyzed_items', 0)
        
        if 'data_sync' in stages:
            summary['cloud_integration']['records_in_sheets'] = stages['data_sync'].get('google_sheets_sync', {}).get('records', 0)
        
        # Generate recommendations
        if summary['failed_stages'] > 0:
            summary['recommendations'].append("🔧 Review failed stages and check component availability")
        
        if not self.google_integration:
            summary['recommendations'].append("🌩️ Consider enabling Google Cloud integration for enhanced data persistence")
        
        if summary['data_processed']['svo_records'] > 0:
            summary['recommendations'].append("📊 Successfully integrated SVO breeding data - consider expanding to other genera")
        
        return summary
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the unified pipeline"""
        return {
            'enable_svo_scraping': True,
            'enable_data_sync': True,
            'enable_image_processing': True,
            'enable_ai_analysis': True,
            'svo_config': {
                'genus': 'Sarcochilus',
                'year_range': (2020, 2024),
                'max_pages': 3
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        return {
            'components': {
                'google_integration': self.google_integration is not None,
                'svo_scraper': self.svo_scraper is not None,
                'ai_breeder': self.ai_breeder is not None,
                'enhanced_ai': self.enhanced_ai is not None
            },
            'data_flow_status': self.data_flow_status,
            'google_cloud_available': self.google_integration.is_available() if self.google_integration else False,
            'system_health': 'operational' if all([
                self.google_integration,
                self.svo_scraper,
                self.ai_breeder,
                self.enhanced_ai
            ]) else 'partial',
            'timestamp': datetime.now().isoformat()
        }

def create_unified_system() -> UnifiedOrchidContinuum:
    """
    Factory function to create and initialize the unified system
    """
    return UnifiedOrchidContinuum()

def execute_demonstration_pipeline() -> Dict[str, Any]:
    """
    Execute a demonstration of the complete unified pipeline
    """
    logger.info("🌺 Starting Unified Orchid Continuum Demonstration")
    
    # Create unified system
    system = create_unified_system()
    
    # Get system status
    status = system.get_system_status()
    logger.info(f"📊 System Status: {status['system_health']}")
    
    # Execute demonstration pipeline
    demo_config = {
        'enable_svo_scraping': True,
        'enable_data_sync': True,
        'enable_image_processing': True,
        'enable_ai_analysis': True,
        'svo_config': {
            'genus': 'Sarcochilus',
            'year_range': (2022, 2024),
            'max_pages': 2  # Limited for demo
        }
    }
    
    results = system.execute_unified_data_flow(demo_config)
    
    return {
        'system_status': status,
        'pipeline_results': results,
        'demonstration_complete': True,
        'timestamp': datetime.now().isoformat()
    }

if __name__ == "__main__":
    # Run demonstration when executed directly
    demo_results = execute_demonstration_pipeline()
    print(json.dumps(demo_results, indent=2))