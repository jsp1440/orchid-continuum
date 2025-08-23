"""
Google Sheets Importer for Five Cities Orchid Society
Imports orchid records from the society's master spreadsheet
"""

import requests
import csv
import io
import logging
from datetime import datetime
from typing import Dict, List, Optional
from app import app, db
from models import OrchidRecord

logger = logging.getLogger(__name__)

class GoogleSheetsImporter:
    """Import orchid data from Google Sheets"""
    
    def __init__(self, sheet_id: str):
        self.sheet_id = sheet_id
        self.csv_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid=0'
        self.imported_count = 0
        self.skipped_count = 0
        self.error_count = 0
        
    def fetch_sheet_data(self) -> List[Dict]:
        """Fetch data from Google Sheets as CSV"""
        try:
            response = requests.get(self.csv_url, timeout=30)
            response.raise_for_status()
            
            csv_content = response.text
            reader = csv.DictReader(io.StringIO(csv_content))
            rows = list(reader)
            
            logger.info(f"Fetched {len(rows)} rows from Google Sheets")
            return rows
            
        except Exception as e:
            logger.error(f"Failed to fetch Google Sheets data: {e}")
            return []
    
    def create_orchid_record(self, row: Dict) -> Optional[OrchidRecord]:
        """Create an OrchidRecord from a spreadsheet row"""
        try:
            # Skip if already exists
            file_id = row.get('File ID', '').strip()
            if file_id:
                existing = OrchidRecord.query.filter_by(google_drive_id=file_id).first()
                if existing:
                    self.skipped_count += 1
                    return None
            
            # Create new orchid record
            orchid = OrchidRecord()
            
            # Basic identification
            orchid.display_name = row.get('Display Name', '').strip() or row.get('Name', '').strip()
            orchid.genus = row.get('Genus', '').strip()
            orchid.species = row.get('Species', '').strip()
            orchid.hybrid_name = row.get('Hybrid', '').strip()
            orchid.cultivar_name = row.get('Cultivar', '').strip()
            
            # Build scientific name
            if orchid.genus:
                parts = [orchid.genus]
                if orchid.species:
                    parts.append(orchid.species)
                if orchid.hybrid_name:
                    parts.append(f'({orchid.hybrid_name})')
                if orchid.cultivar_name:
                    parts.append(f'"{orchid.cultivar_name}"')
                orchid.scientific_name = ' '.join(parts)
            
            # Geographic and habitat data
            orchid.region = row.get('Region', '').strip()
            orchid.continent = row.get('Continent', '').strip()
            orchid.native_habitat = row.get('Habitat', '').strip()
            
            # Growing conditions
            orchid.light_requirements = row.get('Light_Requirement', '').strip()
            orchid.temperature_range = row.get('Temperature_Range', '').strip()
            orchid.growth_habit = row.get('Growth_Habit', '').strip()
            
            # Set climate preference based on temperature
            temp_range = orchid.temperature_range.lower()
            if 'cool' in temp_range or 'cold' in temp_range:
                orchid.climate_preference = 'cool'
            elif 'warm' in temp_range or 'hot' in temp_range:
                orchid.climate_preference = 'warm'
            else:
                orchid.climate_preference = 'intermediate'
            
            # Flower characteristics
            orchid.fragrance = row.get('Fragrance', '').strip()
            orchid.flower_count = row.get('Flower_Count', '').strip()
            orchid.flower_size = row.get('Flower_Size', '').strip()
            orchid.color_palette = row.get('Color_Palette', '').strip()
            
            # Conservation and taxonomy
            orchid.rarity_status = row.get('Rarity_Status', '').strip()
            orchid.conservation_status = row.get('Conservation_Status', '').strip()
            orchid.author = row.get('Authority', '').strip()
            orchid.synonyms = row.get('Synonyms', '').strip()
            orchid.parentage = row.get('Parentage', '').strip()
            
            # Photo and source data
            orchid.google_drive_id = file_id
            if file_id:
                orchid.image_url = f'/static/drive_photos/{file_id}.jpg'
            orchid.photographer = row.get('Photographer', '').strip()
            orchid.image_license = row.get('License', '').strip()
            
            # External links
            orchid.iospe_link = row.get('IOSPE_Link', '').strip()
            orchid.gbif_link = row.get('GBIF_Link', '').strip()
            orchid.inaturalist_link = row.get('iNaturalist_Link', '').strip()
            orchid.aos_link = row.get('AOS_Link', '').strip()
            
            # Metadata
            orchid.ingestion_source = 'google_sheets_import'
            orchid.validation_status = 'validated'  # Pre-validated society data
            orchid.notes = row.get('Notes', '').strip()
            orchid.created_at = datetime.utcnow()
            orchid.updated_at = datetime.utcnow()
            
            return orchid
            
        except Exception as e:
            logger.error(f"Error creating orchid record: {e}")
            self.error_count += 1
            return None
    
    def import_all_records(self, max_records: Optional[int] = None) -> Dict:
        """Import all records from the Google Sheet"""
        with app.app_context():
            rows = self.fetch_sheet_data()
            if not rows:
                return {'success': False, 'error': 'Failed to fetch data'}
            
            logger.info(f"Starting import of {len(rows)} orchid records")
            
            # Limit records if specified
            if max_records:
                rows = rows[:max_records]
                logger.info(f"Limited to first {max_records} records")
            
            batch_size = 50
            for i in range(0, len(rows), batch_size):
                batch = rows[i:i + batch_size]
                
                for row in batch:
                    orchid = self.create_orchid_record(row)
                    if orchid:
                        db.session.add(orchid)
                        self.imported_count += 1
                
                # Commit batch
                try:
                    db.session.commit()
                    logger.info(f"Imported batch {i//batch_size + 1}: {self.imported_count} total records")
                except Exception as e:
                    logger.error(f"Error committing batch: {e}")
                    db.session.rollback()
            
            # Final summary
            total_orchids = OrchidRecord.query.count()
            
            return {
                'success': True,
                'imported': self.imported_count,
                'skipped': self.skipped_count,
                'errors': self.error_count,
                'total_in_database': total_orchids
            }

def run_full_import():
    """Run the full import from Five Cities Orchid Society spreadsheet"""
    sheet_id = '1103vQ_D00Qio5W7PllFeRaFoFAzr7jd8ivOo79sdfgs'
    importer = GoogleSheetsImporter(sheet_id)
    
    logger.info("Starting Five Cities Orchid Society data import")
    result = importer.import_all_records()
    
    if result['success']:
        logger.info(f"Import completed: {result['imported']} imported, {result['skipped']} skipped, {result['errors']} errors")
        logger.info(f"Total orchids in database: {result['total_in_database']}")
    else:
        logger.error(f"Import failed: {result.get('error', 'Unknown error')}")
    
    return result

if __name__ == '__main__':
    run_full_import()