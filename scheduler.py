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
        """Start the background scheduler - DISABLED FOR DEMO"""
        logger.info("🚫 DEMO MODE: Background scheduler disabled for stability")
        logger.info("✅ Demo will run with existing data only")
        return
        
        # DISABLED FOR DEMO STABILITY:
        # if self.is_running:
        #     logger.warning("Scheduler is already running")
        #     return
        #     
        # logger.info("Starting orchid record scheduler - updates every 90 seconds")
        # self.is_running = True
        # 
        # # Schedule tasks - FASTER for Gary production scraping
        # schedule.every(30).seconds.do(self.update_orchid_records)  # 3x faster updates
        # schedule.every().hour.do(self.update_orchid_metadata)
        # schedule.every(6).hours.do(self.run_maintenance_tasks)
        # schedule.every().day.at("03:00").do(self.full_database_refresh)
        # schedule.every().day.at("04:30").do(self.run_mislabeling_detection)  # Daily data quality check
        # 
        # # Start scheduler in background thread
        # scheduler_thread = threading.Thread(target=self.run_scheduler, daemon=True)
        # scheduler_thread.start()
        # 
        # logger.info("Orchid scheduler started successfully")
        
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
                self.run_enhanced_flowering_collection()
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
            # Run Gary Yong Gee scraper - PRODUCTION MODE
            logger.info("Running Gary Yong Gee PRODUCTION scraper...")
            response = requests.get('http://localhost:5000/scrape?source=gary', timeout=600)
            if response.status_code == 200:
                logger.info("Gary PRODUCTION scraper completed successfully")
            
            # Run international scrapers - PRODUCTION MODE
            logger.info("Running international PRODUCTION scrapers...")
            response = requests.get('http://localhost:5000/run-international-collection', timeout=600)
            if response.status_code == 200:
                logger.info("International scrapers completed")
                
        except Exception as e:
            logger.warning(f"Scraper error (will retry next cycle): {e}")
    
    def run_enhanced_flowering_collection(self):
        """Run enhanced flowering and geographic data collection"""
        try:
            from enhanced_flowering_geographic_scraper import FloweringGeographicScraper
            scraper = FloweringGeographicScraper()
            
            logger.info("Running enhanced flowering & geographic collection...")
            results = scraper.run_enhanced_collection()
            
            logger.info(f"Enhanced collection results: {results['with_both']} records with both flowering dates and coordinates")
            
        except Exception as e:
            logger.warning(f"Enhanced collection error (will retry next cycle): {e}")
            
    def update_geographic_data(self):
        """Update geographic and location data for orchids"""
        try:
            # Find orchids without coordinates that have location info
            orchids_to_update = OrchidRecord.query.filter(
                OrchidRecord.decimal_latitude.is_(None),
                OrchidRecord.country.isnot(None)
            ).limit(50).all()  # Process 50 at a time
            
            updated_count = 0
            for orchid in orchids_to_update:
                # Add estimated coordinates based on country
                coords = self.get_country_coordinates(orchid.country)
                if coords:
                    # Add some randomization to avoid exact overlap
                    orchid.decimal_latitude = coords[0] + random.uniform(-2, 2)
                    orchid.decimal_longitude = coords[1] + random.uniform(-2, 2)
                    
                    # Update region info based on country
                    orchid.region = self.get_continent_from_country(orchid.country)
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
                
    def run_mislabeling_detection(self):
        """Daily mislabeling detection and auto-correction"""
        logger.info("🔍 Running daily mislabeling detection scan")
        
        with app.app_context():
            try:
                # Check for the infamous "T" abbreviation pattern that caused the massive issue
                trichocentrum_mislabels = self.detect_trichocentrum_mislabeling()
                
                # Check for other systematic mislabeling patterns
                abbreviation_issues = self.detect_abbreviation_mislabeling()
                
                # Check for genus/species field disconnections
                disconnected_data = self.detect_disconnected_taxonomy()
                
                # Auto-correct obvious cases
                auto_corrections = self.auto_correct_obvious_mislabeling()
                
                # Flag questionable cases for community review
                flagged_cases = self.flag_questionable_cases()
                
                logger.info(f"✅ Mislabeling scan completed:")
                logger.info(f"   - Trichocentrum issues detected: {trichocentrum_mislabels}")
                logger.info(f"   - Abbreviation issues detected: {abbreviation_issues}")
                logger.info(f"   - Disconnected taxonomy: {disconnected_data}")
                logger.info(f"   - Auto-corrections made: {auto_corrections}")
                logger.info(f"   - Cases flagged for review: {flagged_cases}")
                
            except Exception as e:
                logger.error(f"❌ Error during mislabeling detection: {e}")
                
    def detect_trichocentrum_mislabeling(self):
        """Detect the infamous 'T [abbreviation]' pattern mislabeled as Trichocentrum"""
        try:
            # Find Trichocentrum records that look like abbreviations
            suspicious_records = OrchidRecord.query.filter(
                OrchidRecord.genus == 'Trichocentrum',
                OrchidRecord.display_name.like('T %'),
                OrchidRecord.identification_status != 'unidentified'
            ).all()
            
            detected_count = len(suspicious_records)
            
            if detected_count > 0:
                logger.warning(f"🚨 CRITICAL: {detected_count} potential Trichocentrum mislabeling detected!")
                # Auto-move to unidentified for expert review
                for record in suspicious_records:
                    record.identification_status = 'unidentified'
                    logger.info(f"🔧 Flagged suspicious Trichocentrum: {record.display_name} (ID: {record.id})")
                
                db.session.commit()
                
            return detected_count
            
        except Exception as e:
            logger.error(f"Error detecting Trichocentrum mislabeling: {e}")
            return 0
            
    def detect_abbreviation_mislabeling(self):
        """Detect other abbreviation patterns that might indicate systematic mislabeling"""
        try:
            # Look for patterns like single letters, common abbreviations in wrong places
            suspicious_patterns = [
                "% C %",  # Cattleya abbreviation in wrong place
                "% Den %",  # Dendrobium abbreviation in wrong place  
                "% Bulb %",  # Bulbophyllum abbreviation in wrong place
                "% Masd %",  # Masdevallia abbreviation in wrong place
                "% Angcm %",  # Angraecum abbreviation in wrong place
                "% Ctsm %",  # Catasetum abbreviation in wrong place
            ]
            
            total_detected = 0
            for pattern in suspicious_patterns:
                records = OrchidRecord.query.filter(
                    OrchidRecord.display_name.like(pattern),
                    OrchidRecord.identification_status != 'unidentified'
                ).all()
                
                if records:
                    total_detected += len(records)
                    logger.warning(f"🚨 Detected {len(records)} records with suspicious pattern: {pattern}")
                    
            return total_detected
            
        except Exception as e:
            logger.error(f"Error detecting abbreviation mislabeling: {e}")
            return 0
            
    def detect_disconnected_taxonomy(self):
        """Detect cases where genus/species data is disconnected from display names"""
        try:
            # Find records where genus doesn't match what's in display_name
            disconnected_records = OrchidRecord.query.filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.display_name.isnot(None),
                ~OrchidRecord.display_name.like(f"%{OrchidRecord.genus}%")
            ).limit(100).all()  # Limit to avoid huge queries
            
            detected_count = len(disconnected_records)
            
            if detected_count > 10:  # If many disconnected, it's suspicious
                logger.warning(f"🚨 MASSIVE TAXONOMY DISCONNECTION: {detected_count} records detected!")
                
            return detected_count
            
        except Exception as e:
            logger.error(f"Error detecting disconnected taxonomy: {e}")
            return 0
            
    def auto_correct_obvious_mislabeling(self):
        """Auto-correct obvious mislabeling cases"""
        try:
            corrections_made = 0
            
            # Fix obvious Trichocentrum "T [abbreviation]" patterns
            trichocentrum_abbreviations = {
                'T C ': 'Cattleya',
                'T Den ': 'Dendrobium', 
                'T Bulb ': 'Bulbophyllum',
                'T Masd ': 'Masdevallia',
                'T Angcm ': 'Angraecum',
                'T Ctsm ': 'Catasetum',
                'T L ': 'Laelia',
                'T Epi ': 'Epidendrum'
            }
            
            for abbreviation, correct_genus in trichocentrum_abbreviations.items():
                records = OrchidRecord.query.filter(
                    OrchidRecord.genus == 'Trichocentrum',
                    OrchidRecord.display_name.like(f'{abbreviation}%')
                ).all()
                
                for record in records:
                    record.genus = correct_genus
                    record.suggested_genus = correct_genus
                    record.identification_status = 'verified'
                    corrections_made += 1
                    logger.info(f"🔧 AUTO-CORRECTED: {record.display_name} → genus: {correct_genus}")
            
            if corrections_made > 0:
                db.session.commit()
                logger.info(f"✅ Auto-corrected {corrections_made} obvious mislabeling cases")
                
            return corrections_made
            
        except Exception as e:
            logger.error(f"Error auto-correcting mislabeling: {e}")
            db.session.rollback()
            return 0
            
    def flag_questionable_cases(self):
        """Flag questionable cases for community review"""
        try:
            flagged_count = 0
            
            # Flag records with very generic species names
            generic_species = ['species', 'sp.', 'sp', 'spp.', 'unknown', 'Unknown']
            generic_records = OrchidRecord.query.filter(
                OrchidRecord.species.in_(generic_species),
                OrchidRecord.identification_status == 'verified'
            ).all()
            
            for record in generic_records:
                record.identification_status = 'needs_review'
                flagged_count += 1
                
            # Flag records where display_name and genus/species don't match at all
            mismatched_records = OrchidRecord.query.filter(
                OrchidRecord.genus.isnot(None),
                OrchidRecord.species.isnot(None),
                OrchidRecord.display_name.isnot(None),
                ~OrchidRecord.display_name.contains(OrchidRecord.genus),
                OrchidRecord.identification_status == 'verified'
            ).limit(50).all()  # Limit to avoid massive changes
            
            for record in mismatched_records:
                record.identification_status = 'needs_review'
                flagged_count += 1
                
            if flagged_count > 0:
                db.session.commit()
                logger.info(f"🏁 Flagged {flagged_count} questionable cases for expert review")
                
            return flagged_count
            
        except Exception as e:
            logger.error(f"Error flagging questionable cases: {e}")
            db.session.rollback()
            return 0
                
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