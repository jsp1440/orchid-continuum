"""
Orchid Comparison and Analysis System
Advanced interface for viewing, comparing, and contrasting orchids
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from flask import Blueprint, render_template, request, jsonify, flash
from models import OrchidRecord, db
from sqlalchemy import or_, and_, func
from PIL import Image, ExifTags
import openai

logger = logging.getLogger(__name__)

# Create blueprint
comparison_bp = Blueprint('comparison', __name__, url_prefix='/comparison')

class OrchidComparisonSystem:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def extract_exif_metadata(self, image_path: str) -> Dict[str, Any]:
        """Extract EXIF metadata including date, location, time from image"""
        try:
            if not os.path.exists(image_path):
                return {'extracted': False, 'error': 'Image file not found'}
            
            with Image.open(image_path) as img:
                exif_data = img.getexif()
                
                if not exif_data:
                    return {'extracted': False, 'error': 'No EXIF data found'}
                
                metadata = {
                    'extracted': True,
                    'camera_info': {},
                    'datetime_info': {},
                    'location_info': {},
                    'technical_info': {}
                }
                
                # Extract relevant EXIF tags
                for tag_id, value in exif_data.items():
                    tag_name = ExifTags.TAGS.get(tag_id, tag_id)
                    
                    # Date and time information
                    if tag_name in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
                        try:
                            dt = datetime.strptime(str(value), '%Y:%m:%d %H:%M:%S')
                            metadata['datetime_info'][tag_name.lower()] = {
                                'raw': str(value),
                                'formatted': dt.strftime('%Y-%m-%d %H:%M:%S'),
                                'date': dt.date().isoformat(),
                                'time': dt.time().isoformat(),
                                'year': dt.year,
                                'month': dt.month,
                                'day': dt.day
                            }
                        except:
                            metadata['datetime_info'][tag_name.lower()] = str(value)
                    
                    # GPS/Location information
                    elif tag_name == 'GPSInfo':
                        gps_data = self._parse_gps_data(value)
                        if gps_data:
                            metadata['location_info'] = gps_data
                    
                    # Camera information
                    elif tag_name in ['Make', 'Model', 'Software']:
                        metadata['camera_info'][tag_name.lower()] = str(value)
                    
                    # Technical information
                    elif tag_name in ['ExposureTime', 'FNumber', 'ISO', 'FocalLength', 'Flash']:
                        metadata['technical_info'][tag_name.lower()] = str(value)
                
                return metadata
                
        except Exception as e:
            logger.error(f"EXIF extraction error: {e}")
            return {'extracted': False, 'error': str(e)}
    
    def _parse_gps_data(self, gps_info: Dict) -> Optional[Dict[str, Any]]:
        """Parse GPS coordinates from EXIF data"""
        try:
            def convert_to_degrees(value):
                d, m, s = value
                return d + (m / 60.0) + (s / 3600.0)
            
            location = {}
            
            if 1 in gps_info and 2 in gps_info:  # Latitude
                lat = convert_to_degrees(gps_info[2])
                if gps_info[1] == 'S':
                    lat = -lat
                location['latitude'] = lat
            
            if 3 in gps_info and 4 in gps_info:  # Longitude
                lon = convert_to_degrees(gps_info[4])
                if gps_info[3] == 'W':
                    lon = -lon
                location['longitude'] = lon
            
            if 5 in gps_info and 6 in gps_info:  # Altitude
                location['altitude'] = float(gps_info[6])
            
            # Reverse geocoding would go here in production
            if 'latitude' in location and 'longitude' in location:
                location['coordinates'] = f"{location['latitude']:.6f}, {location['longitude']:.6f}"
                location['estimated_country'] = self._estimate_country_from_coordinates(
                    location['latitude'], location['longitude']
                )
            
            return location if location else None
            
        except Exception as e:
            logger.error(f"GPS parsing error: {e}")
            return None
    
    def _estimate_country_from_coordinates(self, lat: float, lon: float) -> str:
        """Estimate country from coordinates (simplified version)"""
        # This is a simplified implementation - production would use a proper geocoding service
        country_estimates = {
            # Approximate ranges for major orchid-producing countries
            (0, 15, 95, 140): 'Philippines/Indonesia',
            (10, 30, 70, 140): 'Southeast Asia',
            (-10, 15, 95, 155): 'Indonesia/Malaysia',
            (20, 50, 70, 135): 'China/Japan',
            (8, 20, -90, -70): 'Central America',
            (-20, 15, -80, -35): 'South America',
            (-35, -10, 140, 175): 'Australia',
            (18, 28, -88, -60): 'Caribbean',
            (-25, 5, 10, 55): 'Africa'
        }
        
        for (min_lat, max_lat, min_lon, max_lon), region in country_estimates.items():
            if min_lat <= lat <= max_lat and min_lon <= lon <= max_lon:
                return region
        
        return 'Unknown region'
    
    def generate_biodiversity_tags(self, orchid: OrchidRecord) -> List[str]:
        """Generate comprehensive biodiversity and phenotypic tags"""
        tags = set()
        
        # Basic taxonomic tags
        if orchid.genus:
            tags.add(f"genus_{orchid.genus.lower()}")
        if orchid.species:
            tags.add(f"species_{orchid.species.lower()}")
        # Family info is stored in ai_extracted_metadata
        try:
            if orchid.ai_extracted_metadata:
                metadata = json.loads(orchid.ai_extracted_metadata)
                family = metadata.get('family', 'Orchidaceae')
                if family:
                    tags.add(f"family_{family.lower()}")
        except:
            pass
        
        # Growth habit tags
        if orchid.growth_habit:
            tags.add(f"growth_{orchid.growth_habit.lower()}")
        
        # Extract phenotypic traits from AI metadata
        if orchid.ai_extracted_metadata:
            try:
                metadata = json.loads(orchid.ai_extracted_metadata)
                
                # Morphological tags
                morpho_tags = metadata.get('morphological_tags', [])
                for tag in morpho_tags:
                    tags.add(f"phenotype_{tag.lower()}")
                
                # Cultural requirements as ecological tags
                cultural = metadata.get('cultural_requirements', {})
                if cultural.get('light'):
                    light_level = cultural['light'].lower()
                    if 'bright' in light_level:
                        tags.add('ecology_high_light')
                    elif 'low' in light_level:
                        tags.add('ecology_low_light')
                    else:
                        tags.add('ecology_medium_light')
                
                if cultural.get('temperature'):
                    temp = cultural['temperature'].lower()
                    if 'warm' in temp:
                        tags.add('climate_warm')
                    elif 'cool' in temp:
                        tags.add('climate_cool')
                    else:
                        tags.add('climate_intermediate')
                
                # Native habitat tags
                habitat = metadata.get('native_habitat', '').lower()
                if 'rainforest' in habitat or 'tropical' in habitat:
                    tags.add('habitat_tropical_rainforest')
                if 'cloud forest' in habitat or 'montane' in habitat:
                    tags.add('habitat_cloud_forest')
                if 'terrestrial' in habitat:
                    tags.add('habitat_ground_dwelling')
                if 'epiphytic' in habitat or 'tree' in habitat:
                    tags.add('habitat_tree_dwelling')
                
                # Geographic/biogeographic tags
                if 'asia' in habitat:
                    tags.add('biogeography_asian')
                elif 'america' in habitat:
                    tags.add('biogeography_neotropical')
                elif 'africa' in habitat:
                    tags.add('biogeography_african')
                
                # Conservation and rarity indicators
                care_difficulty = metadata.get('care_difficulty', '').lower()
                if 'advanced' in care_difficulty or 'difficult' in care_difficulty:
                    tags.add('conservation_specialist_care')
                elif 'beginner' in care_difficulty:
                    tags.add('cultivation_beginner_friendly')
                
            except Exception as e:
                logger.error(f"Error extracting biodiversity tags: {e}")
        
        # Hybrid vs species tags
        if orchid.is_hybrid:
            tags.add('classification_hybrid')
        else:
            tags.add('classification_species')
        
        return sorted(list(tags))
    
    def enhanced_photo_analysis(self, orchid: OrchidRecord) -> Dict[str, Any]:
        """Perform enhanced analysis including EXIF and biodiversity tagging"""
        analysis = {
            'orchid_id': orchid.id,
            'analysis_timestamp': datetime.now().isoformat(),
            'exif_metadata': {},
            'biodiversity_tags': [],
            'phenotypic_traits': {},
            'geographic_origin': {},
            'temporal_data': {}
        }
        
        # Extract EXIF data if image file exists
        if orchid.image_filename:
            image_path = os.path.join('static/uploads', orchid.image_filename)
            analysis['exif_metadata'] = self.extract_exif_metadata(image_path)
        
        # Generate biodiversity tags
        analysis['biodiversity_tags'] = self.generate_biodiversity_tags(orchid)
        
        # Extract phenotypic traits
        if orchid.ai_extracted_metadata:
            try:
                metadata = json.loads(orchid.ai_extracted_metadata)
                analysis['phenotypic_traits'] = {
                    'morphology': metadata.get('morphological_tags', []),
                    'physical_characteristics': metadata.get('physical_characteristics', ''),
                    'growth_pattern': metadata.get('growth_habits', {}),
                    'flowering_traits': metadata.get('flowering_info', {})
                }
                
                # Geographic origin analysis
                native_habitat = metadata.get('native_habitat', '')
                analysis['geographic_origin'] = {
                    'native_habitat': native_habitat,
                    'estimated_origin': self._extract_geographic_origin(native_habitat)
                }
                
            except Exception as e:
                logger.error(f"Phenotypic analysis error: {e}")
        
        # Temporal data from EXIF
        exif_data = analysis['exif_metadata']
        if exif_data.get('extracted') and 'datetime_info' in exif_data:
            datetime_info = exif_data['datetime_info']
            if datetime_info:
                analysis['temporal_data'] = {
                    'photo_date': datetime_info.get('datetimeoriginal', {}).get('date'),
                    'photo_time': datetime_info.get('datetimeoriginal', {}).get('time'),
                    'season_estimate': self._estimate_season(datetime_info),
                    'temporal_context': self._analyze_temporal_context(datetime_info)
                }
        
        return analysis
    
    def _extract_geographic_origin(self, habitat_text: str) -> Dict[str, str]:
        """Extract geographic origin from habitat description"""
        origins = {
            'continent': 'Unknown',
            'region': 'Unknown',
            'climate_zone': 'Unknown'
        }
        
        habitat_lower = habitat_text.lower()
        
        # Continent detection
        if any(term in habitat_lower for term in ['asia', 'asian', 'southeast asia', 'china', 'japan', 'philippines', 'thailand', 'malaysia']):
            origins['continent'] = 'Asia'
        elif any(term in habitat_lower for term in ['america', 'central america', 'south america', 'brazil', 'colombia', 'ecuador']):
            origins['continent'] = 'Americas'
        elif any(term in habitat_lower for term in ['africa', 'african', 'madagascar']):
            origins['continent'] = 'Africa'
        elif any(term in habitat_lower for term in ['australia', 'oceania', 'new guinea']):
            origins['continent'] = 'Oceania'
        
        # Climate zone detection
        if any(term in habitat_lower for term in ['tropical', 'rainforest', 'equatorial']):
            origins['climate_zone'] = 'Tropical'
        elif any(term in habitat_lower for term in ['temperate', 'subtropical']):
            origins['climate_zone'] = 'Subtropical'
        elif any(term in habitat_lower for term in ['montane', 'cloud forest', 'highland']):
            origins['climate_zone'] = 'Montane'
        elif any(term in habitat_lower for term in ['cool', 'alpine']):
            origins['climate_zone'] = 'Alpine'
        
        return origins
    
    def _estimate_season(self, datetime_info: Dict) -> str:
        """Estimate season when photo was taken"""
        try:
            if 'datetimeoriginal' in datetime_info and 'month' in datetime_info['datetimeoriginal']:
                month = datetime_info['datetimeoriginal']['month']
                if month in [12, 1, 2]:
                    return 'Winter'
                elif month in [3, 4, 5]:
                    return 'Spring'
                elif month in [6, 7, 8]:
                    return 'Summer'
                elif month in [9, 10, 11]:
                    return 'Fall'
        except:
            pass
        return 'Unknown'
    
    def _analyze_temporal_context(self, datetime_info: Dict) -> str:
        """Analyze temporal context of the photograph"""
        try:
            if 'datetimeoriginal' in datetime_info:
                dt_data = datetime_info['datetimeoriginal']
                if 'year' in dt_data:
                    year = dt_data['year']
                    if year >= 2020:
                        return 'Recent documentation'
                    elif year >= 2010:
                        return 'Modern digital photography'
                    elif year >= 2000:
                        return 'Early digital era'
                    else:
                        return 'Film photography era'
        except:
            pass
        return 'Unknown timeframe'

# Initialize the system
comparison_system = OrchidComparisonSystem()

@comparison_bp.route('/')
def comparison_interface():
    """Main comparison interface"""
    # Get basic statistics
    total_orchids = OrchidRecord.query.count()
    genera_count = db.session.query(func.count(func.distinct(OrchidRecord.genus))).scalar()
    
    # Get unique filter options
    genera = db.session.query(OrchidRecord.genus).distinct().filter(OrchidRecord.genus.isnot(None)).all()
    genera = [g[0] for g in genera if g[0]]
    
    growth_habits = db.session.query(OrchidRecord.growth_habit).distinct().filter(OrchidRecord.growth_habit.isnot(None)).all()
    growth_habits = [h[0] for h in growth_habits if h[0]]
    
    return render_template('comparison/interface.html',
                         total_orchids=total_orchids,
                         genera_count=genera_count,
                         genera=sorted(genera),
                         growth_habits=sorted(growth_habits))

@comparison_bp.route('/search')
def search_orchids():
    """Advanced search with multiple criteria"""
    # Get search parameters
    genus = request.args.get('genus')
    species = request.args.get('species')
    growth_habit = request.args.get('growth_habit')
    origin_filter = request.args.get('origin')
    biodiversity_tag = request.args.get('biodiversity_tag')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Build query
    query = OrchidRecord.query
    
    if genus:
        query = query.filter(OrchidRecord.genus.ilike(f'%{genus}%'))
    if species:
        query = query.filter(OrchidRecord.species.ilike(f'%{species}%'))
    if growth_habit:
        query = query.filter(OrchidRecord.growth_habit == growth_habit)
    
    orchids = query.all()
    
    # Enhanced analysis for each result
    results = []
    for orchid in orchids:
        analysis = comparison_system.enhanced_photo_analysis(orchid)
        
        # Apply additional filters based on enhanced analysis
        include_orchid = True
        
        if origin_filter and analysis['geographic_origin']:
            origin_text = str(analysis['geographic_origin']).lower()
            if origin_filter.lower() not in origin_text:
                include_orchid = False
        
        if biodiversity_tag and biodiversity_tag not in analysis['biodiversity_tags']:
            include_orchid = False
        
        if date_from or date_to:
            photo_date = analysis['temporal_data'].get('photo_date')
            if photo_date:
                try:
                    photo_dt = datetime.fromisoformat(photo_date)
                    if date_from and photo_dt < datetime.fromisoformat(date_from):
                        include_orchid = False
                    if date_to and photo_dt > datetime.fromisoformat(date_to):
                        include_orchid = False
                except:
                    pass
        
        if include_orchid:
            results.append({
                'orchid': orchid,
                'analysis': analysis
            })
    
    return jsonify({
        'success': True,
        'count': len(results),
        'results': [
            {
                'id': r['orchid'].id,
                'display_name': r['orchid'].display_name,
                'scientific_name': r['orchid'].scientific_name,
                'genus': r['orchid'].genus,
                'species': r['orchid'].species,
                'image_url': r['orchid'].image_url,
                'biodiversity_tags': r['analysis']['biodiversity_tags'],
                'geographic_origin': r['analysis']['geographic_origin'],
                'temporal_data': r['analysis']['temporal_data'],
                'phenotypic_traits': r['analysis']['phenotypic_traits']
            } for r in results
        ]
    })

@comparison_bp.route('/compare/<int:orchid1_id>/<int:orchid2_id>')
def compare_orchids(orchid1_id: int, orchid2_id: int):
    """Compare two orchids in detail"""
    orchid1 = OrchidRecord.query.get_or_404(orchid1_id)
    orchid2 = OrchidRecord.query.get_or_404(orchid2_id)
    
    # Get enhanced analysis for both
    analysis1 = comparison_system.enhanced_photo_analysis(orchid1)
    analysis2 = comparison_system.enhanced_photo_analysis(orchid2)
    
    # Generate comparison metrics
    comparison = {
        'taxonomic_similarity': calculate_taxonomic_similarity(orchid1, orchid2),
        'phenotypic_similarity': calculate_phenotypic_similarity(analysis1, analysis2),
        'geographic_relationship': analyze_geographic_relationship(analysis1, analysis2),
        'temporal_relationship': analyze_temporal_relationship(analysis1, analysis2),
        'shared_biodiversity_tags': list(set(analysis1['biodiversity_tags']) & set(analysis2['biodiversity_tags'])),
        'unique_tags_orchid1': list(set(analysis1['biodiversity_tags']) - set(analysis2['biodiversity_tags'])),
        'unique_tags_orchid2': list(set(analysis2['biodiversity_tags']) - set(analysis1['biodiversity_tags']))
    }
    
    return render_template('comparison/compare_detail.html',
                         orchid1=orchid1,
                         orchid2=orchid2,
                         analysis1=analysis1,
                         analysis2=analysis2,
                         comparison=comparison)

@comparison_bp.route('/analyze/<int:orchid_id>')
def analyze_orchid_metadata(orchid_id: int):
    """Get complete metadata analysis for an orchid"""
    orchid = OrchidRecord.query.get_or_404(orchid_id)
    analysis = comparison_system.enhanced_photo_analysis(orchid)
    
    return jsonify({
        'success': True,
        'orchid_id': orchid_id,
        'analysis': analysis
    })

@comparison_bp.route('/biodiversity-tags')
def get_biodiversity_tags():
    """Get all available biodiversity tags"""
    all_orchids = OrchidRecord.query.all()
    all_tags = set()
    
    for orchid in all_orchids:
        tags = comparison_system.generate_biodiversity_tags(orchid)
        all_tags.update(tags)
    
    # Categorize tags
    categorized_tags = {
        'taxonomic': [t for t in all_tags if t.startswith(('genus_', 'species_', 'family_'))],
        'phenotypic': [t for t in all_tags if t.startswith('phenotype_')],
        'ecological': [t for t in all_tags if t.startswith(('ecology_', 'habitat_', 'climate_'))],
        'geographic': [t for t in all_tags if t.startswith('biogeography_')],
        'conservation': [t for t in all_tags if t.startswith(('conservation_', 'cultivation_'))],
        'classification': [t for t in all_tags if t.startswith('classification_')]
    }
    
    return jsonify({
        'success': True,
        'total_tags': len(all_tags),
        'all_tags': sorted(list(all_tags)),
        'categorized_tags': categorized_tags
    })

# Helper functions for comparison analysis
def calculate_taxonomic_similarity(orchid1: OrchidRecord, orchid2: OrchidRecord) -> Dict[str, Any]:
    """Calculate taxonomic similarity between two orchids"""
    # Extract family from AI metadata for comparison
    family1 = None
    family2 = None
    
    try:
        if orchid1.ai_extracted_metadata:
            metadata1 = json.loads(orchid1.ai_extracted_metadata)
            family1 = metadata1.get('family')
    except:
        pass
    
    try:
        if orchid2.ai_extracted_metadata:
            metadata2 = json.loads(orchid2.ai_extracted_metadata)
            family2 = metadata2.get('family')
    except:
        pass
    
    similarity = {
        'same_genus': orchid1.genus == orchid2.genus,
        'same_species': orchid1.species == orchid2.species,
        'same_family': family1 == family2 if family1 and family2 else False,
        'relationship': 'Different'
    }
    
    if similarity['same_species'] and similarity['same_genus']:
        similarity['relationship'] = 'Same species'
    elif similarity['same_genus']:
        similarity['relationship'] = 'Same genus'
    elif similarity['same_family']:
        similarity['relationship'] = 'Same family'
    
    return similarity

def calculate_phenotypic_similarity(analysis1: Dict, analysis2: Dict) -> Dict[str, Any]:
    """Calculate phenotypic similarity based on traits"""
    traits1 = set(analysis1.get('biodiversity_tags', []))
    traits2 = set(analysis2.get('biodiversity_tags', []))
    
    if not traits1 or not traits2:
        return {'similarity_score': 0.0, 'shared_traits': 0, 'total_unique_traits': 0}
    
    shared_traits = len(traits1 & traits2)
    total_unique_traits = len(traits1 | traits2)
    similarity_score = shared_traits / total_unique_traits if total_unique_traits > 0 else 0.0
    
    return {
        'similarity_score': similarity_score,
        'shared_traits': shared_traits,
        'total_unique_traits': total_unique_traits,
        'similarity_percentage': similarity_score * 100
    }

def analyze_geographic_relationship(analysis1: Dict, analysis2: Dict) -> Dict[str, str]:
    """Analyze geographic relationship between orchids"""
    origin1 = analysis1.get('geographic_origin', {})
    origin2 = analysis2.get('geographic_origin', {})
    
    relationship = 'Unknown'
    if origin1.get('continent') == origin2.get('continent'):
        if origin1.get('climate_zone') == origin2.get('climate_zone'):
            relationship = 'Same continent and climate zone'
        else:
            relationship = 'Same continent, different climate zones'
    else:
        relationship = 'Different continents'
    
    return {
        'relationship': relationship,
        'origin1': origin1,
        'origin2': origin2
    }

def analyze_temporal_relationship(analysis1: Dict, analysis2: Dict) -> Dict[str, str]:
    """Analyze temporal relationship between photographs"""
    temporal1 = analysis1.get('temporal_data', {})
    temporal2 = analysis2.get('temporal_data', {})
    
    relationship = 'Unknown'
    if temporal1.get('photo_date') and temporal2.get('photo_date'):
        try:
            date1 = datetime.fromisoformat(temporal1['photo_date'])
            date2 = datetime.fromisoformat(temporal2['photo_date'])
            diff_days = abs((date1 - date2).days)
            
            if diff_days < 30:
                relationship = 'Photographed within a month'
            elif diff_days < 365:
                relationship = 'Photographed within a year'
            elif diff_days < 365 * 5:
                relationship = 'Photographed within 5 years'
            else:
                relationship = 'Photographed years apart'
        except:
            pass
    
    return {
        'relationship': relationship,
        'temporal1': temporal1,
        'temporal2': temporal2
    }