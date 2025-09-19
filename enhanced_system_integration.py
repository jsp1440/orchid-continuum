#!/usr/bin/env python3
"""
Enhanced System Integration for Orchid Continuum
Integrates international scraping and mobile field research systems
"""

from flask import current_app
import logging
from datetime import datetime

# Import the new systems
from international_scraping_routes import international_scraping_bp
from field_research_system import field_research_bp
from models import db

logger = logging.getLogger(__name__)

def register_enhanced_systems(app):
    """Register all enhanced systems with the Flask app"""
    try:
        # Register blueprints
        app.register_blueprint(international_scraping_bp)
        app.register_blueprint(field_research_bp)
        
        # Create database tables
        with app.app_context():
            # Add FieldObservation to models if not already there
            if not hasattr(db.Model.registry._class_registry, 'FieldObservation'):
                # The table will be created when db.create_all() is called
                db.create_all()
        
        logger.info("🚀 Enhanced systems registered successfully")
        logger.info("📱 Mobile field research system available at /field/")
        logger.info("🌍 International scraping admin at /admin/international/")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to register enhanced systems: {e}")
        return False

def get_system_status():
    """Get status of enhanced systems"""
    try:
        status = {
            'international_scraping': {
                'registered': True,
                'endpoint': '/admin/international/',
                'description': 'International orchid database scraping system'
            },
            'mobile_field_research': {
                'registered': True,
                'endpoint': '/field/',
                'description': 'Mobile Progressive Web App for field researchers'
            },
            'database_tables': {
                'field_observations': check_table_exists('field_observations')
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        return {'error': str(e)}

def check_table_exists(table_name: str) -> bool:
    """Check if database table exists"""
    try:
        from sqlalchemy import text
        # Try PostgreSQL first (since we're using PostgreSQL)
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT tablename FROM pg_catalog.pg_tables WHERE tablename = :table_name"), 
                                {"table_name": table_name})
            return bool(result.fetchone())
    except:
        try:
            # Fallback to SQLite check
            with db.engine.connect() as conn:
                result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name = :table_name"), 
                                    {"table_name": table_name})
                return bool(result.fetchone())
        except:
            return False

# Quick test functions for development
def test_international_scraping():
    """Test international scraping system"""
    try:
        from source_adapter_system import IngestionOrchestrator
        orchestrator = IngestionOrchestrator()
        
        # Test IOSPE adapter
        iospe_adapter = orchestrator.adapters.get('iospe')
        if iospe_adapter:
            # Test discovery (limit to 3 for quick test)
            taxa = iospe_adapter.discover_taxa(limit=3)
            return {
                'success': True,
                'adapter_available': True,
                'taxa_discovered': len(taxa),
                'sample_taxa': taxa
            }
        else:
            return {'success': False, 'error': 'IOSPE adapter not found'}
            
    except Exception as e:
        logger.error(f"Error testing international scraping: {e}")
        return {'success': False, 'error': str(e)}

def test_mobile_system():
    """Test mobile field research system"""
    try:
        # Check if FieldObservation model is accessible
        test_observation = FieldObservation()
        
        return {
            'success': True,
            'model_available': True,
            'observation_id_format': test_observation.observation_id,
            'session_id_format': test_observation.session_id
        }
        
    except Exception as e:
        logger.error(f"Error testing mobile system: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    # For testing purposes
    logging.basicConfig(level=logging.INFO)
    
    print("🧪 Testing Enhanced Systems...")
    
    print("\n📡 International Scraping Test:")
    int_result = test_international_scraping()
    print(f"  Result: {int_result}")
    
    print("\n📱 Mobile System Test:")
    mobile_result = test_mobile_system()
    print(f"  Result: {mobile_result}")
    
    print("\n✅ Testing completed!")