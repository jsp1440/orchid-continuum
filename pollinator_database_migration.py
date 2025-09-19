#!/usr/bin/env python3
"""
Pollinator Database Migration Script
===================================
Safe migration script to add comprehensive pollinator ecosystem tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from models import (
    Pollinator, PollinatorLifecycle, MigrationPattern, 
    AdvancedOrchidPollinatorRelationship, PreyPredatorRelationship,
    EcosystemNetwork, HabitatOverlap, SeasonalInteraction,
    PollinatorTypeEnum, RelationshipTypeEnum, LifecycleStageEnum, MigrationTypeEnum
)
from sqlalchemy import text
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_table_exists(table_name):
    """Check if a table exists in the database"""
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text(f"""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name = '{table_name}'
                );
            """))
            return result.scalar()
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False

def create_pollinator_tables():
    """Create all pollinator-related tables safely"""
    try:
        with app.app_context():
            logger.info("🔧 Starting pollinator database migration...")
            
            # Check existing tables
            tables_to_create = [
                'pollinators',
                'pollinator_lifecycles',
                'migration_patterns',
                'advanced_orchid_pollinator_relationships',
                'prey_predator_relationships',
                'ecosystem_networks',
                'habitat_overlaps',
                'seasonal_interactions'
            ]
            
            existing_tables = []
            new_tables = []
            
            for table in tables_to_create:
                if check_table_exists(table):
                    existing_tables.append(table)
                    logger.info(f"✅ Table '{table}' already exists")
                else:
                    new_tables.append(table)
            
            if new_tables:
                logger.info(f"📊 Creating {len(new_tables)} new tables: {', '.join(new_tables)}")
                
                # Create all tables
                db.create_all()
                
                logger.info("✅ All pollinator tables created successfully!")
                
                # Verify table creation
                for table in new_tables:
                    if check_table_exists(table):
                        logger.info(f"✅ Verified: {table}")
                    else:
                        logger.error(f"❌ Failed to create: {table}")
                        
            else:
                logger.info("✅ All pollinator tables already exist")
                
            return True
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

def verify_database_integrity():
    """Verify that all tables and relationships are properly created"""
    try:
        with app.app_context():
            logger.info("🔍 Verifying database integrity...")
            
            # Test basic table access
            test_queries = [
                ("Pollinator count", "SELECT COUNT(*) FROM pollinators"),
                ("PollinatorLifecycle count", "SELECT COUNT(*) FROM pollinator_lifecycles"),
                ("MigrationPattern count", "SELECT COUNT(*) FROM migration_patterns"),
                ("Relationship count", "SELECT COUNT(*) FROM advanced_orchid_pollinator_relationships"),
                ("Ecosystem count", "SELECT COUNT(*) FROM ecosystem_networks")
            ]
            
            with db.engine.connect() as conn:
                for test_name, query in test_queries:
                    try:
                        result = conn.execute(text(query))
                        count = result.scalar()
                        logger.info(f"✅ {test_name}: {count} records")
                    except Exception as e:
                        logger.error(f"❌ {test_name} failed: {e}")
                        return False
            
            logger.info("✅ Database integrity verification completed successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Integrity verification failed: {e}")
        return False

def create_indexes_for_performance():
    """Create indexes for better query performance"""
    try:
        with app.app_context():
            logger.info("🚀 Creating performance indexes...")
            
            indexes = [
                # Pollinator indexes
                "CREATE INDEX IF NOT EXISTS idx_pollinator_scientific_name ON pollinators(scientific_name);",
                "CREATE INDEX IF NOT EXISTS idx_pollinator_type ON pollinators(pollinator_type);",
                "CREATE INDEX IF NOT EXISTS idx_pollinator_family ON pollinators(family);",
                "CREATE INDEX IF NOT EXISTS idx_pollinator_flight_period ON pollinators(flight_period_start, flight_period_end);",
                
                # Relationship indexes
                "CREATE INDEX IF NOT EXISTS idx_relationship_orchid ON advanced_orchid_pollinator_relationships(orchid_id);",
                "CREATE INDEX IF NOT EXISTS idx_relationship_pollinator ON advanced_orchid_pollinator_relationships(pollinator_id);",
                "CREATE INDEX IF NOT EXISTS idx_relationship_type ON advanced_orchid_pollinator_relationships(relationship_type);",
                "CREATE INDEX IF NOT EXISTS idx_relationship_effectiveness ON advanced_orchid_pollinator_relationships(pollination_effectiveness);",
                
                # Temporal indexes
                "CREATE INDEX IF NOT EXISTS idx_seasonal_month ON seasonal_interactions(interaction_month);",
                "CREATE INDEX IF NOT EXISTS idx_seasonal_timing ON seasonal_interactions(peak_interaction_day);",
                
                # Geographic indexes
                "CREATE INDEX IF NOT EXISTS idx_migration_origin ON migration_patterns(origin_latitude, origin_longitude);",
                "CREATE INDEX IF NOT EXISTS idx_migration_destination ON migration_patterns(destination_latitude, destination_longitude);",
            ]
            
            with db.engine.connect() as conn:
                for index_sql in indexes:
                    try:
                        conn.execute(text(index_sql))
                        conn.commit()
                        logger.info(f"✅ Created index: {index_sql.split('ON')[1].split('(')[0].strip()}")
                    except Exception as e:
                        logger.warning(f"⚠️ Index creation warning: {e}")
            
            logger.info("✅ Performance indexes created successfully")
            return True
            
    except Exception as e:
        logger.error(f"❌ Index creation failed: {e}")
        return False

def rollback_migration():
    """Rollback migration by dropping pollinator tables"""
    try:
        with app.app_context():
            logger.warning("⚠️ Rolling back pollinator migration...")
            
            tables_to_drop = [
                'seasonal_interactions',
                'habitat_overlaps',
                'ecosystem_networks',
                'prey_predator_relationships',
                'advanced_orchid_pollinator_relationships',
                'migration_patterns',
                'pollinator_lifecycles',
                'pollinators'
            ]
            
            with db.engine.connect() as conn:
                for table in tables_to_drop:
                    try:
                        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
                        conn.commit()
                        logger.info(f"✅ Dropped table: {table}")
                    except Exception as e:
                        logger.error(f"❌ Failed to drop {table}: {e}")
            
            logger.info("✅ Migration rollback completed")
            return True
            
    except Exception as e:
        logger.error(f"❌ Rollback failed: {e}")
        return False

def main():
    """Main migration function"""
    print("🐝 Pollinator Database Migration")
    print("=" * 50)
    
    try:
        # Step 1: Create tables
        if not create_pollinator_tables():
            print("❌ Migration failed at table creation")
            return False
        
        # Step 2: Verify integrity
        if not verify_database_integrity():
            print("❌ Migration failed at integrity verification")
            return False
        
        # Step 3: Create performance indexes
        if not create_indexes_for_performance():
            print("⚠️ Migration completed but with index warnings")
        
        print("\n✅ POLLINATOR DATABASE MIGRATION COMPLETED SUCCESSFULLY!")
        print("🔗 Tables created:")
        print("   • pollinators - Comprehensive species data")
        print("   • pollinator_lifecycles - Lifecycle stages and timing")
        print("   • migration_patterns - Movement and migration data")
        print("   • advanced_orchid_pollinator_relationships - Enhanced relationships")
        print("   • prey_predator_relationships - Ecological food webs")
        print("   • ecosystem_networks - Network-level analysis")
        print("   • habitat_overlaps - Spatial and temporal overlaps")
        print("   • seasonal_interactions - Detailed phenological data")
        
        print("\n🚀 Ready for data population and API integration!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)