"""
Enhanced Baker Culture Data Importer
Processes structured Baker culture data with FS numbers, confidence scores, and regional expertise
"""

import csv
import json
import logging
from typing import Dict, List, Optional
from app import app, db
from models import OrchidRecord
from datetime import datetime

logger = logging.getLogger(__name__)

class EnhancedBakerImporter:
    """Import and process enhanced Baker culture data with confidence scoring"""
    
    def __init__(self):
        self.imported_count = 0
        self.error_count = 0
        self.enhanced_records = []
    
    def process_csv_file(self, file_path: str) -> Dict:
        """Process the enhanced Baker culture CSV file"""
        try:
            results = {
                'processed': 0,
                'imported': 0,
                'updated': 0,
                'errors': [],
                'regional_coverage': {},
                'confidence_distribution': {}
            }
            
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for row in reader:
                    try:
                        processed_record = self._process_record(row)
                        if processed_record:
                            # Import to database
                            orchid_record = self._create_or_update_orchid_record(processed_record)
                            if orchid_record:
                                results['imported'] += 1
                                
                                # Track regional coverage
                                region = processed_record.get('region')
                                if region:
                                    results['regional_coverage'][region] = results['regional_coverage'].get(region, 0) + 1
                                
                                # Track confidence distribution
                                tier = processed_record.get('confidence_tier')
                                if tier:
                                    results['confidence_distribution'][tier] = results['confidence_distribution'].get(tier, 0) + 1
                        
                        results['processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing row {results['processed']}: {str(e)}"
                        results['errors'].append(error_msg)
                        logger.error(error_msg)
            
            # Commit all changes
            db.session.commit()
            logger.info(f"Enhanced Baker import completed: {results['imported']} records imported")
            
            return results
            
        except Exception as e:
            logger.error(f"Error processing CSV file: {str(e)}")
            return {'error': str(e)}
    
    def _process_record(self, row: Dict) -> Optional[Dict]:
        """Process a single CSV row into structured data"""
        try:
            # Extract and clean the data
            processed = {
                'fs_number': row.get('FS Number', '').strip(),
                'species': row.get('Species', '').strip(),
                'region': row.get('Region/Country', '').strip(),
                'elevation': row.get('Elevation', '').strip(),
                'growth_habit': row.get('Growth Habit', '').strip(),
                'avg_day_temp': row.get('Avg Day Temp', '').strip(),
                'avg_night_temp': row.get('Avg Night Temp', '').strip(),
                'diurnal_range': row.get('Diurnal Range', '').strip(),
                'rainfall_pattern': row.get('Rainfall Pattern', '').strip(),
                'dry_season': row.get('Dry Season', '').strip(),
                'humidity': row.get('Humidity', '').strip(),
                'light': row.get('Light', '').strip(),
                'rest_notes': row.get('Rest Notes', '').strip(),
                'extrapolation_confidence': float(row.get('Extrapolation Confidence', 0)),
                'confidence_tier': row.get('Confidence Tier', '').strip()
            }
            
            # Validate required fields
            if not processed['species'] or not processed['fs_number']:
                logger.warning(f"Missing required fields for record: {processed}")
                return None
            
            return processed
            
        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
            return None
    
    def _create_or_update_orchid_record(self, processed_data: Dict) -> Optional[OrchidRecord]:
        """Create or update an OrchidRecord with the enhanced Baker data"""
        try:
            # Check if record already exists by FS number or species name
            existing_record = OrchidRecord.query.filter(
                OrchidRecord.cultural_notes.like(f"%{processed_data['fs_number']}%")
            ).first()
            
            if not existing_record:
                # Create new record
                orchid = OrchidRecord()
                orchid.display_name = processed_data['species']
                orchid.scientific_name = processed_data['species']
                orchid.photographer = 'Charles & Margaret Baker (Enhanced)'
                orchid.created_at = datetime.now()
            else:
                orchid = existing_record
            
            # Generate comprehensive cultural notes
            cultural_data = {
                'fs_number': processed_data['fs_number'],
                'region': processed_data['region'],
                'elevation': processed_data['elevation'],
                'growth_habit': processed_data['growth_habit'],
                'temperatures': {
                    'day': processed_data['avg_day_temp'],
                    'night': processed_data['avg_night_temp'],
                    'range': processed_data['diurnal_range']
                },
                'rainfall_pattern': processed_data['rainfall_pattern'],
                'dry_season': processed_data['dry_season'],
                'humidity': processed_data['humidity'],
                'light': processed_data['light'],
                'rest_notes': processed_data['rest_notes'],
                'extrapolation_confidence': processed_data['extrapolation_confidence'],
                'confidence_tier': processed_data['confidence_tier']
            }
            
            # Store as JSON in cultural notes
            orchid.cultural_notes = f"ENHANCED BAKER CULTURE: {json.dumps(cultural_data)}"
            
            # Set other fields
            orchid.region = processed_data['region']
            orchid.growth_habit = self._normalize_growth_habit(processed_data['growth_habit'])
            orchid.climate_preference = self._determine_climate_preference(processed_data)
            orchid.metadata_source = f"Enhanced Baker Culture Sheet ({processed_data['fs_number']})"
            
            # Add to session
            if not existing_record:
                db.session.add(orchid)
            
            return orchid
            
        except Exception as e:
            logger.error(f"Error creating orchid record: {str(e)}")
            return None
    
    def _normalize_growth_habit(self, growth_habit: str) -> str:
        """Normalize growth habit for consistency"""
        if not growth_habit:
            return 'unknown'
        
        growth_lower = growth_habit.lower()
        
        if 'epiphyte' in growth_lower:
            return 'epiphytic'
        elif 'terrestrial' in growth_lower:
            return 'terrestrial'
        elif 'lithophyte' in growth_lower:
            return 'lithophytic'
        else:
            return growth_habit.lower()
    
    def _determine_climate_preference(self, data: Dict) -> str:
        """Determine climate preference from temperature and elevation data"""
        day_temp = data.get('avg_day_temp', '').lower()
        elevation = data.get('elevation', '')
        
        # Simple heuristic based on temperature descriptions
        if 'hot' in day_temp:
            return 'warm'
        elif 'warm' in day_temp and 'cool' not in data.get('avg_night_temp', '').lower():
            return 'intermediate'
        elif 'mild' in day_temp or 'cool' in data.get('avg_night_temp', '').lower():
            return 'cool'
        elif '1500' in elevation or '2000' in elevation:  # High elevation
            return 'cool'
        else:
            return 'intermediate'
    
    def analyze_enhanced_coverage(self) -> Dict:
        """Analyze the coverage provided by enhanced Baker data"""
        try:
            # Get all enhanced Baker records
            enhanced_records = OrchidRecord.query.filter(
                OrchidRecord.cultural_notes.like('%ENHANCED BAKER CULTURE%')
            ).all()
            
            regional_analysis = {}
            confidence_analysis = {'High': 0, 'Medium': 0, 'Low': 0}
            genus_coverage = {}
            
            for record in enhanced_records:
                # Extract data from cultural notes
                try:
                    notes = record.cultural_notes
                    json_start = notes.find('{')
                    if json_start > 0:
                        data = json.loads(notes[json_start:])
                        
                        # Regional analysis
                        region = data.get('region')
                        if region:
                            if region not in regional_analysis:
                                regional_analysis[region] = {
                                    'count': 0,
                                    'confidence_levels': [],
                                    'genera': set()
                                }
                            regional_analysis[region]['count'] += 1
                            regional_analysis[region]['confidence_levels'].append(
                                data.get('extrapolation_confidence', 0)
                            )
                            
                            # Genus tracking
                            if record.scientific_name:
                                genus = record.scientific_name.split(' ')[0]
                                regional_analysis[region]['genera'].add(genus)
                                genus_coverage[genus] = genus_coverage.get(genus, 0) + 1
                        
                        # Confidence tier analysis
                        tier = data.get('confidence_tier')
                        if tier in confidence_analysis:
                            confidence_analysis[tier] += 1
                
                except json.JSONDecodeError:
                    continue
            
            # Convert sets to lists for JSON serialization
            for region_data in regional_analysis.values():
                region_data['genera'] = list(region_data['genera'])
                if region_data['confidence_levels']:
                    region_data['avg_confidence'] = sum(region_data['confidence_levels']) / len(region_data['confidence_levels'])
                else:
                    region_data['avg_confidence'] = 0
            
            return {
                'total_enhanced_records': len(enhanced_records),
                'regional_analysis': regional_analysis,
                'confidence_distribution': confidence_analysis,
                'genus_coverage': genus_coverage
            }
            
        except Exception as e:
            logger.error(f"Error analyzing enhanced coverage: {str(e)}")
            return {'error': str(e)}

# Initialize the enhanced importer
enhanced_baker_importer = EnhancedBakerImporter()