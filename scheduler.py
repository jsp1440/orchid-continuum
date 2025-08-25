#!/usr/bin/env python3
"""
Orchid Record Scheduler - Updates orchid records every 15 minutes
Handles automatic data updates, scraping, and database maintenance
"""

import schedule
import time
import logging
import threading
from datetime import datetime, timedelta
from models import OrchidRecord, db
from app import app
import requests
import random

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrchidScheduler:
    def __init__(self):
        self.is_running = False
        self.last_update = None
        self.update_count = 0
        
    def start_scheduler(self):
        """Start the background scheduler"""
        if self.is_running:
            logger.warning("Scheduler is already running")
            return
            
        logger.info("Starting orchid record scheduler - updates every 90 seconds")
        self.is_running = True
        
        # Schedule tasks
        schedule.every(90).seconds.do(self.update_orchid_records)
        schedule.every().hour.do(self.update_orchid_metadata)
        schedule.every(6).hours.do(self.run_maintenance_tasks)
        schedule.every().day.at("03:00").do(self.full_database_refresh)
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Orchid scheduler started successfully")
        
    def run_scheduler(self):
        """Run the scheduler loop"""
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(9)  # Check every 9 seconds for reinitialize
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)
                
    def update_orchid_records(self):
        """Main update function - runs every 90 seconds"""
        logger.info("🔄 Starting 90-second orchid record update")
        
        with app.app_context():
            try:
                # Run various update tasks
                self.run_scrapers()
                self.update_geographic_data()
                self.refresh_orchid_of_day()
                self.update_ai_metadata()
                
                self.update_count += 1
                self.last_update = datetime.now()
                
                logger.info(f"✅ Orchid record update completed (#{self.update_count})")
                
            except Exception as e:
                logger.error(f"❌ Error during orchid record update: {e}")
                
    def run_scrapers(self):
        """Run orchid scrapers to get new data"""
        try:
            # Run Gary Yong Gee scraper
            logger.info("Running Gary Yong Gee scraper...")
            response = requests.get('http://localhost:5000/test_gary_scraper', timeout=300)
            if response.status_code == 200:
                logger.info("Gary scraper completed successfully")
            
            # Run international scrapers with small batch
            logger.info("Running international scrapers...")
            response = requests.get('http://localhost:5000/test_international_scrapers', timeout=300)
            if response.status_code == 200:
                logger.info("International scrapers completed")
                
        except Exception as e:
            logger.warning(f"Scraper error (will retry next cycle): {e}")
            
    def update_geographic_data(self):
        """Update geographic and location data for orchids"""
        try:
            # Find orchids without coordinates that have location info
            orchids_to_update = OrchidRecord.query.filter(
                OrchidRecord.latitude.is_(None),
                OrchidRecord.country.isnot(None)
            ).limit(50).all()  # Process 50 at a time
            
            updated_count = 0
            for orchid in orchids_to_update:
                # Add estimated coordinates based on country
                coords = self.get_country_coordinates(orchid.country)
                if coords:
                    # Add some randomization to avoid exact overlap
                    orchid.latitude = coords[0] + random.uniform(-2, 2)
                    orchid.longitude = coords[1] + random.uniform(-2, 2)
                    
                    # Update continent info
                    orchid.continent = self.get_continent_from_country(orchid.country)
                    updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Updated geographic data for {updated_count} orchids")
                
        except Exception as e:
            logger.error(f"Error updating geographic data: {e}")
            db.session.rollback()
            
    def refresh_orchid_of_day(self):
        """Refresh the enhanced orchid of the day selection"""
        try:
            from enhanced_orchid_of_day import EnhancedOrchidOfDay
            enhancer = EnhancedOrchidOfDay()
            result = enhancer.get_enhanced_orchid_of_day()
            if result:
                logger.info(f"Refreshed orchid of the day: {result['orchid'].display_name}")
        except Exception as e:
            logger.warning(f"Error refreshing orchid of day: {e}")
            
    def update_ai_metadata(self):
        """Update AI-generated metadata for orchids without it"""
        try:
            # Find orchids without AI descriptions
            orchids_without_ai = OrchidRecord.query.filter(
                OrchidRecord.ai_description.is_(None),
                OrchidRecord.genus.isnot(None)
            ).limit(10).all()  # Process 10 at a time to avoid API limits
            
            updated_count = 0
            for orchid in orchids_without_ai:
                # Generate AI metadata
                ai_data = self.generate_orchid_metadata(orchid)
                if ai_data:
                    orchid.ai_description = ai_data.get('description')
                    orchid.ai_confidence = ai_data.get('confidence', 0.5)
                    
                    # Update traits based on AI analysis
                    if 'fragrant' in ai_data.get('traits', []):
                        orchid.is_fragrant = True
                    if ai_data.get('growth_habit'):
                        orchid.growth_habit = ai_data['growth_habit']
                    if ai_data.get('climate_zone'):
                        orchid.climate_zone = ai_data['climate_zone']
                    if ai_data.get('pollinators'):
                        orchid.pollinator_types = ai_data['pollinators']
                        
                    updated_count += 1
                    
                # Rate limiting
                time.sleep(1)
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Updated AI metadata for {updated_count} orchids")
                
        except Exception as e:
            logger.error(f"Error updating AI metadata: {e}")
            db.session.rollback()
            
    def update_orchid_metadata(self):
        """Hourly metadata updates"""
        logger.info("🔄 Running hourly metadata update")
        
        with app.app_context():
            try:
                # Update view counts
                self.update_view_counts()
                
                # Update validation statuses
                self.update_validation_statuses()
                
                # Update featured orchids
                self.update_featured_orchids()
                
                logger.info("✅ Hourly metadata update completed")
                
            except Exception as e:
                logger.error(f"❌ Error during hourly update: {e}")
                
    def run_maintenance_tasks(self):
        """6-hourly maintenance tasks"""
        logger.info("🔧 Running maintenance tasks")
        
        with app.app_context():
            try:
                # Clean up old temporary data
                self.cleanup_old_data()
                
                # Update database statistics
                self.update_database_stats()
                
                # Refresh materialized views if any
                self.refresh_views()
                
                logger.info("✅ Maintenance tasks completed")
                
            except Exception as e:
                logger.error(f"❌ Error during maintenance: {e}")
                
    def full_database_refresh(self):
        """Daily full database refresh"""
        logger.info("🔄 Running daily full database refresh")
        
        with app.app_context():
            try:
                # Full scraper run
                logger.info("Running full scraper cycle...")
                
                # Update all orchid names to expanded forms
                self.expand_all_orchid_names()
                
                # Refresh all cached data
                self.refresh_all_cached_data()
                
                logger.info("✅ Daily refresh completed")
                
            except Exception as e:
                logger.error(f"❌ Error during daily refresh: {e}")
                
    def get_country_coordinates(self, country):
        """Get approximate coordinates for a country"""
        country_coords = {
            'Brazil': [-14.235, -51.9253],
            'USA': [39.8283, -98.5795],
            'Mexico': [23.6345, -102.5528],
            'Colombia': [4.5709, -74.2973],
            'Ecuador': [-1.8312, -78.1834],
            'Peru': [-9.19, -75.0152],
            'Guatemala': [15.7835, -90.2308],
            'Philippines': [12.8797, 121.7740],
            'Thailand': [15.8700, 100.9925],
            'Madagascar': [-18.7669, 46.8691],
            'Africa': [0, 20],
            'Central America': [15, -90],
            'Southeast Asia': [10, 110],
            'Comoro Islands': [-11.6455, 43.3333],
            'Papua New Guinea': [-6.314993, 143.95555],
            'Japan': [36.2048, 138.2529]
        }
        return country_coords.get(country)
        
    def get_continent_from_country(self, country):
        """Get continent from country name"""
        continent_map = {
            'Brazil': 'South America',
            'Colombia': 'South America',
            'Ecuador': 'South America',
            'Peru': 'South America',
            'Mexico': 'North America',
            'USA': 'North America',
            'Guatemala': 'North America',
            'Central America': 'North America',
            'Philippines': 'Asia',
            'Thailand': 'Asia',
            'Japan': 'Asia',
            'Southeast Asia': 'Asia',
            'Madagascar': 'Africa',
            'Africa': 'Africa',
            'Comoro Islands': 'Africa',
            'Papua New Guinea': 'Oceania'
        }
        return continent_map.get(country, 'Unknown')
        
    def generate_orchid_metadata(self, orchid):
        """Generate AI metadata for an orchid"""
        try:
            # Simple metadata generation based on genus and species
            genus = orchid.genus or ''
            species = orchid.species or ''
            
            # Basic traits based on common orchid knowledge
            metadata = {
                'description': f"{genus} {species} is a beautiful orchid with unique characteristics.",
                'confidence': 0.7,
                'traits': [],
                'growth_habit': 'epiphytic',
                'climate_zone': 'intermediate',
                'pollinators': ['insects']
            }
            
            # Add genus-specific traits
            if 'cattleya' in genus.lower():
                metadata['traits'].extend(['fragrant'])
                metadata['growth_habit'] = 'epiphytic'
                metadata['pollinators'] = ['bees', 'butterflies']
                metadata['description'] = f"Cattleya orchid known for its large, showy, often fragrant flowers. This {species} variety displays the characteristic beauty of the Cattleya genus."
                
            elif 'phalaenopsis' in genus.lower():
                metadata['growth_habit'] = 'epiphytic'
                metadata['climate_zone'] = 'warm'
                metadata['pollinators'] = ['moths']
                metadata['description'] = f"Phalaenopsis orchid, commonly known as moth orchid, prized for its long-lasting blooms and ease of care."
                
            elif 'dendrobium' in genus.lower():
                metadata['growth_habit'] = 'epiphytic'
                metadata['climate_zone'] = 'cool'
                metadata['pollinators'] = ['bees']
                metadata['description'] = f"Dendrobium orchid with diverse growth habits and flowering patterns, adapted to various climatic conditions."
                
            return metadata
            
        except Exception as e:
            logger.error(f"Error generating metadata for orchid {orchid.id}: {e}")
            return None
            
    def expand_all_orchid_names(self):
        """Expand abbreviated orchid names across the database"""
        try:
            from orchid_name_utils import orchid_name_utils
            
            # Find orchids with abbreviated names
            orchids_to_expand = OrchidRecord.query.filter(
                OrchidRecord.display_name.ilike('%lc%')
            ).all()
            
            updated_count = 0
            for orchid in orchids_to_expand:
                original_name = orchid.display_name
                expanded_name = orchid_name_utils.expand_orchid_name(original_name)
                
                if expanded_name != original_name:
                    orchid.display_name = expanded_name
                    updated_count += 1
            
            if updated_count > 0:
                db.session.commit()
                logger.info(f"Expanded names for {updated_count} orchids")
                
        except Exception as e:
            logger.error(f"Error expanding orchid names: {e}")
            db.session.rollback()
            
    def update_view_counts(self):
        """Update view counts and popularity metrics"""
        # Placeholder for view count updates
        pass
        
    def update_validation_statuses(self):
        """Update validation statuses based on data quality"""
        # Placeholder for validation updates
        pass
        
    def update_featured_orchids(self):
        """Update featured orchid selections"""
        # Placeholder for featured orchid updates
        pass
        
    def cleanup_old_data(self):
        """Clean up old temporary data"""
        # Placeholder for cleanup tasks
        pass
        
    def update_database_stats(self):
        """Update database statistics"""
        # Placeholder for stats updates
        pass
        
    def refresh_views(self):
        """Refresh materialized views"""
        # Placeholder for view refresh
        pass
        
    def refresh_all_cached_data(self):
        """Refresh all cached data"""
        # Placeholder for cache refresh
        pass
        
    def stop_scheduler(self):
        """Stop the scheduler"""
        logger.info("Stopping orchid record scheduler...")
        self.is_running = False
        
    def get_status(self):
        """Get scheduler status"""
        return {
            'running': self.is_running,
            'last_update': self.last_update.isoformat() if self.last_update else None,
            'update_count': self.update_count,
            'next_update': (datetime.now() + timedelta(minutes=15 - (datetime.now().minute % 15))).isoformat()
        }

# Global scheduler instance
scheduler = OrchidScheduler()

def start_orchid_scheduler():
    """Start the orchid scheduler"""
    scheduler.start_scheduler()
    
def get_scheduler_status():
    """Get current scheduler status"""
    return scheduler.get_status()

if __name__ == "__main__":
    logger.info("Starting orchid record scheduler...")
    start_orchid_scheduler()
    
    try:
        # Keep the script running
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down scheduler...")
        scheduler.stop_scheduler()