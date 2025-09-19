"""
Location-Based Culture Sheet System
Generates species-specific orchid culture sheets adapted to geographical location
Uses Baker culture data with local climate and photoperiod adjustments
"""

import logging
import json
import math
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import openai
import os
from models import OrchidRecord
from app import db

logger = logging.getLogger(__name__)

class LocationBasedCultureSystem:
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY')) if os.getenv('OPENAI_API_KEY') else None
    
    def generate_location_culture_sheet(self, orchid_species: str, user_location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete culture sheet for a specific orchid species
        adapted to the user's geographical location
        """
        try:
            # Get the orchid record
            orchid_record = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'%{orchid_species}%')
            ).first()
            
            if not orchid_record:
                return {'error': f'Orchid species {orchid_species} not found in database'}
            
            # Get Baker culture data if available
            baker_culture = self._get_baker_culture_data(orchid_species)
            
            # Get AOS culture data if available
            aos_culture = self._get_aos_culture_data(orchid_species)
            
            # Calculate location-specific data
            location_data = self._analyze_location_climate(user_location)
            
            # Calculate photoperiod for location
            photoperiod_calendar = self._calculate_location_photoperiods(user_location)
            
            # Generate adaptation recommendations with expert comparison
            adaptations = self._generate_location_adaptations(orchid_record, location_data, baker_culture, aos_culture)
            
            # Compare expert recommendations and flag differences
            expert_comparison = self._compare_expert_recommendations(baker_culture, aos_culture, adaptations)
            
            # Create cultivation calendar with expert data
            cultivation_calendar = self._create_location_cultivation_calendar(
                orchid_record, location_data, photoperiod_calendar, baker_culture, aos_culture
            )
            
            # Compile the complete culture sheet
            culture_sheet = {
                'orchid_info': {
                    'scientific_name': orchid_record.scientific_name,
                    'display_name': orchid_record.display_name,
                    'genus': orchid_record.genus,
                    'native_habitat': orchid_record.region,
                    'growth_habit': orchid_record.growth_habit,
                    'climate_preference': orchid_record.climate_preference
                },
                'location_info': location_data,
                'baker_foundation': baker_culture,
                'aos_foundation': aos_culture,
                'expert_comparison': expert_comparison,
                'photoperiod_calendar': photoperiod_calendar,
                'location_adaptations': adaptations,
                'cultivation_calendar': cultivation_calendar,
                'emergency_care': self._generate_emergency_care_guide(orchid_record, location_data),
                'seasonal_checklist': self._create_seasonal_checklist(orchid_record, location_data),
                'generated_date': datetime.now().isoformat(),
                'data_sources': ['Charles & Margaret Baker Culture Data', 'American Orchid Society Worksheets', 'Baker Daylength Database', 'Location Climate Analysis']
            }
            
            return culture_sheet
            
        except Exception as e:
            logger.error(f"Error generating location culture sheet: {str(e)}")
            return {'error': str(e)}
    
    def _get_baker_culture_data(self, orchid_species: str) -> Dict[str, Any]:
        """Get Baker culture data for the species"""
        try:
            # Look for direct Baker culture sheet
            baker_record = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'%{orchid_species}%'),
                OrchidRecord.photographer.like('%Baker%')
            ).first()
            
            if baker_record and baker_record.cultural_notes:
                return {
                    'available': True,
                    'source': 'Direct Baker Culture Sheet',
                    'data': baker_record.cultural_notes,
                    'confidence': 'High - Species-specific data'
                }
            
            # Look for genus-level Baker data
            genus = orchid_species.split(' ')[0] if ' ' in orchid_species else orchid_species
            genus_baker = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'{genus} %'),
                OrchidRecord.photographer.like('%Baker%')
            ).first()
            
            if genus_baker and genus_baker.cultural_notes:
                return {
                    'available': True,
                    'source': 'Genus-level Baker Data',
                    'data': genus_baker.cultural_notes,
                    'confidence': 'Medium - Genus extrapolation'
                }
            
            return {'available': False, 'note': 'No Baker culture data available for this species'}
            
        except Exception as e:
            logger.error(f"Error getting Baker culture data: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def _get_aos_culture_data(self, orchid_species: str) -> Dict[str, Any]:
        """Get AOS (American Orchid Society) culture data for the species"""
        try:
            # Look for direct AOS culture sheet
            aos_record = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'%{orchid_species}%'),
                OrchidRecord.photographer.like('%American Orchid Society%')
            ).first()
            
            if aos_record and aos_record.cultural_notes:
                return {
                    'available': True,
                    'source': 'AOS Culture Sheet',
                    'data': aos_record.cultural_notes,
                    'confidence': 'High - AOS Official Guidelines'
                }
            
            # Look for genus-level AOS data
            genus = orchid_species.split(' ')[0] if ' ' in orchid_species else orchid_species
            genus_aos = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like(f'{genus} sp.%'),
                OrchidRecord.photographer.like('%American Orchid Society%')
            ).first()
            
            if genus_aos and genus_aos.cultural_notes:
                return {
                    'available': True,
                    'source': 'AOS Genus Guidelines',
                    'data': genus_aos.cultural_notes,
                    'confidence': 'Medium - AOS Genus-level data'
                }
            
            return {'available': False, 'note': 'No AOS culture data available for this species'}
            
        except Exception as e:
            logger.error(f"Error getting AOS culture data: {str(e)}")
            return {'available': False, 'error': str(e)}
    
    def _compare_expert_recommendations(self, baker_culture: Dict[str, Any], aos_culture: Dict[str, Any], 
                                       location_adaptations: Dict[str, Any]) -> Dict[str, Any]:
        """Compare Baker, AOS, and location-adapted recommendations and flag differences"""
        try:
            if not self.openai_client:
                return {'error': 'AI analysis not available for comparison'}
            
            # Prepare comparison data
            comparison_data = {
                'baker_available': baker_culture.get('available', False),
                'aos_available': aos_culture.get('available', False),
                'baker_data': baker_culture.get('data', ''),
                'aos_data': aos_culture.get('data', ''),
                'location_adaptations': location_adaptations
            }
            
            if not (comparison_data['baker_available'] or comparison_data['aos_available']):
                return {'note': 'No expert data available for comparison'}
            
            system_prompt = """You are comparing orchid culture recommendations from different expert sources.
            
            CRITICAL: When recommendations differ, you MUST use this exact format:
            "The AOS says [AOS recommendation], however, [explanation of why our recommendation differs and what we recommend instead]."
            
            OR if Baker data differs:
            "The Baker culture sheets recommend [Baker recommendation], however, [our different recommendation and why]."
            
            Compare these cultivation approaches:
            1. Temperature requirements
            2. Light needs  
            3. Watering schedules
            4. Humidity requirements
            5. Fertilizing approaches
            6. Seasonal care differences
            7. Photoperiod sensitivity
            
            For EACH difference found, create a clear flag using the format above.
            Also note where experts AGREE to build confidence.
            
            Return as JSON with specific comparison categories and clear flags."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Compare expert recommendations: {comparison_data}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            comparison_result = json.loads(response.choices[0].message.content)
            comparison_result['comparison_performed'] = True
            comparison_result['sources_compared'] = []
            
            if comparison_data['baker_available']:
                comparison_result['sources_compared'].append('Baker Culture Data')
            if comparison_data['aos_available']:
                comparison_result['sources_compared'].append('AOS Guidelines')
            
            comparison_result['sources_compared'].append('Location-Specific Adaptations')
            
            return comparison_result
            
        except Exception as e:
            logger.error(f"Error comparing expert recommendations: {str(e)}")
            return {'error': str(e)}
    
    def _analyze_location_climate(self, user_location: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the user's location for climate characteristics"""
        try:
            lat = user_location.get('latitude')
            lng = user_location.get('longitude')
            city = user_location.get('city', 'Unknown')
            
            if not lat or not lng:
                return {'error': 'Latitude and longitude required for location analysis'}
            
            # Determine climate zone
            climate_zone = self._determine_climate_zone(lat)
            
            # Calculate seasonal temperature patterns (estimated)
            seasonal_temps = self._estimate_seasonal_temperatures(lat)
            
            # Calculate humidity patterns (estimated based on geography)
            humidity_patterns = self._estimate_humidity_patterns(lat, lng)
            
            # Determine frost risk and seasonal risks
            seasonal_risks = self._analyze_seasonal_risks(lat, climate_zone)
            
            return {
                'city': city,
                'latitude': lat,
                'longitude': lng,
                'climate_zone': climate_zone,
                'seasonal_temperatures': seasonal_temps,
                'humidity_patterns': humidity_patterns,
                'seasonal_risks': seasonal_risks,
                'growing_challenges': self._identify_growing_challenges(lat, climate_zone),
                'advantages': self._identify_location_advantages(lat, climate_zone)
            }
            
        except Exception as e:
            logger.error(f"Error analyzing location climate: {str(e)}")
            return {'error': str(e)}
    
    def _determine_climate_zone(self, latitude: float) -> Dict[str, Any]:
        """Determine climate zone based on latitude"""
        abs_lat = abs(latitude)
        
        if abs_lat <= 10:
            return {
                'zone': 'Tropical Equatorial',
                'characteristics': 'Minimal seasonal variation, high humidity, consistent temperatures',
                'orchid_suitability': 'Excellent for warm-growing epiphytes'
            }
        elif abs_lat <= 25:
            return {
                'zone': 'Tropical',
                'characteristics': 'Moderate seasonal variation, wet/dry seasons, warm temperatures',
                'orchid_suitability': 'Great for most tropical orchids'
            }
        elif abs_lat <= 35:
            return {
                'zone': 'Subtropical',
                'characteristics': 'Distinct seasons, mild winters, hot summers',
                'orchid_suitability': 'Good for intermediate orchids, some protection needed'
            }
        elif abs_lat <= 45:
            return {
                'zone': 'Temperate',
                'characteristics': 'Four distinct seasons, cold winters, moderate summers',
                'orchid_suitability': 'Indoor growing required, excellent seasonal variation'
            }
        else:
            return {
                'zone': 'Cool Temperate',
                'characteristics': 'Cold climate, short growing season, long winters',
                'orchid_suitability': 'Indoor growing essential, great for cool-growing species'
            }
    
    def _calculate_location_photoperiods(self, user_location: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate photoperiod calendar for user's location"""
        try:
            lat = user_location.get('latitude')
            if not lat:
                return {'error': 'Latitude required for photoperiod calculation'}
            
            # Get Baker Daylength Database for reference
            daylength_db = OrchidRecord.query.filter(
                OrchidRecord.scientific_name.like('%Daylength%')
            ).filter_by(photographer='Charles and Margaret Baker').first()
            
            monthly_photoperiods = {}
            
            for month in range(1, 13):
                # Calculate approximate daylight hours for each month
                daylight_hours = self._calculate_daylight_hours(lat, month)
                month_names = ['', 'January', 'February', 'March', 'April', 'May', 'June',
                              'July', 'August', 'September', 'October', 'November', 'December']
                
                monthly_photoperiods[month_names[month]] = {
                    'daylight_hours': round(daylight_hours, 1),
                    'sunrise_sunset': self._estimate_sunrise_sunset(lat, month),
                    'orchid_impact': self._assess_photoperiod_orchid_impact(daylight_hours),
                    'month_number': month
                }
            
            # Calculate seasonal patterns
            seasonal_analysis = self._analyze_seasonal_photoperiod_patterns(monthly_photoperiods)
            
            return {
                'monthly_photoperiods': monthly_photoperiods,
                'seasonal_analysis': seasonal_analysis,
                'baker_daylength_reference': daylength_db is not None,
                'precision_note': 'Calculated using astronomical formulas from Baker methodology'
            }
            
        except Exception as e:
            logger.error(f"Error calculating location photoperiods: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_daylight_hours(self, latitude: float, month: int) -> float:
        """Calculate approximate daylight hours for given latitude and month"""
        # Approximate day of year for middle of month
        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        day_of_year = sum(days_in_month[:month-1]) + 15  # Middle of month
        
        # Solar declination angle
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle
        lat_rad = math.radians(latitude)
        dec_rad = math.radians(declination)
        
        # Calculate sunrise hour angle
        try:
            hour_angle = math.acos(-math.tan(lat_rad) * math.tan(dec_rad))
            daylight_hours = 2 * hour_angle * 12 / math.pi
            return max(0, min(24, daylight_hours))
        except:
            # Handle extreme latitudes
            if abs(latitude) > 66.5:  # Polar regions
                if (latitude > 0 and month in [6, 7]) or (latitude < 0 and month in [12, 1]):
                    return 24  # Midnight sun
                elif (latitude > 0 and month in [12, 1]) or (latitude < 0 and month in [6, 7]):
                    return 0   # Polar night
            return 12  # Default fallback
    
    def _generate_location_adaptations(self, orchid_record: OrchidRecord, location_data: Dict[str, Any], 
                                     baker_culture: Dict[str, Any], aos_culture: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific adaptations needed for the user's location"""
        try:
            if not self.openai_client:
                return {'error': 'AI analysis not available'}
            
            # Prepare data for AI analysis
            orchid_info = {
                'name': orchid_record.scientific_name,
                'genus': orchid_record.genus,
                'native_region': orchid_record.region,
                'climate_preference': orchid_record.climate_preference,
                'growth_habit': orchid_record.growth_habit
            }
            
            system_prompt = """You are an expert orchid cultivation specialist creating location-specific growing adaptations.
            
            Analyze the orchid's native habitat requirements against the user's local climate conditions.
            Provide specific, practical adaptations for successful cultivation.
            
            Focus on:
            - Temperature management (heating/cooling needs)
            - Humidity adjustments for local climate
            - Light requirements and seasonal adjustments  
            - Watering modifications for local weather patterns
            - Seasonal care schedule adaptations
            - Protection from local weather extremes
            - Indoor vs outdoor growing recommendations
            - Equipment and setup modifications needed
            
            Be specific and practical. Consider the user's actual location and climate.
            
            IMPORTANT: When your recommendations differ from expert sources, use this format:
            - "The AOS says [AOS recommendation], however, for your location we recommend [your recommendation] because [reason]."
            - "The Baker culture sheets suggest [Baker recommendation], however, in your climate [your adaptation] works better because [reason]."
            
            Always acknowledge expert sources when making different recommendations."""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Orchid: {orchid_info}\n\nLocation Climate: {location_data}\n\nBaker Culture Foundation: {baker_culture}\n\nAOS Culture Data: {aos_culture}\n\nGenerate specific adaptations with expert comparison:"}
                ],
                response_format={"type": "json_object"},
                max_tokens=1500
            )
            
            adaptations = json.loads(response.choices[0].message.content)
            adaptations['ai_generated'] = True
            adaptations['confidence'] = 'High - Location-specific analysis'
            
            return adaptations
            
        except Exception as e:
            logger.error(f"Error generating location adaptations: {str(e)}")
            return {'error': str(e)}
    
    def _create_location_cultivation_calendar(self, orchid_record: OrchidRecord, location_data: Dict[str, Any], 
                                            photoperiod_calendar: Dict[str, Any], baker_culture: Dict[str, Any], 
                                            aos_culture: Dict[str, Any]) -> Dict[str, Any]:
        """Create a month-by-month cultivation calendar for the user's location"""
        try:
            if not self.openai_client:
                return {'error': 'AI analysis not available'}
            
            system_prompt = """You are an expert orchid grower creating a detailed monthly cultivation calendar.
            
            Create specific month-by-month care instructions adapted to the user's location.
            
            For each month include:
            - Watering schedule adjustments
            - Fertilizer recommendations  
            - Light/photoperiod management
            - Temperature control needs
            - Humidity management
            - Air circulation requirements
            - Pest/disease prevention
            - Repotting timing if applicable
            - Bloom expectation and care
            - Weather protection needs
            
            Base recommendations on Baker culture data and AOS guidelines but adapt for local climate patterns.
            Be specific about timing and practical actions.
            
            IMPORTANT: When recommendations differ from expert sources, clearly state:
            - "The AOS recommends [AOS approach], however, for your location [your recommendation] because [reason]."
            - "Baker culture data suggests [Baker approach], however, in your climate [adaptation] works better.\""""
            
            calendar_data = {
                'orchid': orchid_record.scientific_name,
                'location': location_data,
                'photoperiods': photoperiod_calendar,
                'baker_foundation': baker_culture,
                'aos_guidelines': aos_culture
            }
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Create detailed monthly cultivation calendar for: {calendar_data}"}
                ],
                response_format={"type": "json_object"},
                max_tokens=2000
            )
            
            calendar = json.loads(response.choices[0].message.content)
            calendar['baker_data_integrated'] = baker_culture.get('available', False)
            calendar['aos_data_integrated'] = aos_culture.get('available', False)
            calendar['location_customized'] = True
            
            return calendar
            
        except Exception as e:
            logger.error(f"Error creating cultivation calendar: {str(e)}")
            return {'error': str(e)}
    
    def _estimate_seasonal_temperatures(self, latitude: float) -> Dict[str, Any]:
        """Estimate seasonal temperature patterns based on latitude"""
        abs_lat = abs(latitude)
        
        if abs_lat <= 10:  # Tropical equatorial
            return {
                'winter': {'high': 85, 'low': 75},
                'spring': {'high': 88, 'low': 78},
                'summer': {'high': 90, 'low': 80},
                'fall': {'high': 87, 'low': 77},
                'variation': 'Minimal seasonal temperature variation'
            }
        elif abs_lat <= 25:  # Tropical
            return {
                'winter': {'high': 80, 'low': 65},
                'spring': {'high': 85, 'low': 70},
                'summer': {'high': 90, 'low': 75},
                'fall': {'high': 85, 'low': 70},
                'variation': 'Moderate seasonal temperature variation'
            }
        elif abs_lat <= 35:  # Subtropical
            return {
                'winter': {'high': 65, 'low': 45},
                'spring': {'high': 75, 'low': 55},
                'summer': {'high': 85, 'low': 70},
                'fall': {'high': 75, 'low': 55},
                'variation': 'Distinct seasonal temperature changes'
            }
        else:  # Temperate+
            return {
                'winter': {'high': 45, 'low': 25},
                'spring': {'high': 65, 'low': 45},
                'summer': {'high': 80, 'low': 60},
                'fall': {'high': 65, 'low': 45},
                'variation': 'Strong seasonal temperature variation'
            }
    
    def _estimate_humidity_patterns(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """Estimate humidity patterns based on geographic location"""
        abs_lat = abs(latitude)
        
        # Coastal vs inland estimation (very rough)
        coastal_indicator = abs(longitude) > 100  # Rough inland indicator for US
        
        base_humidity = 70 if abs_lat <= 25 else 60 if abs_lat <= 35 else 50
        
        if coastal_indicator:
            base_humidity += 10  # Higher humidity near coasts
        
        return {
            'annual_average': f'{base_humidity}%',
            'summer': f'{base_humidity + 10}%',
            'winter': f'{base_humidity - 10}%',
            'notes': 'Estimated based on latitude and general geographic patterns'
        }
    
    def _analyze_seasonal_risks(self, latitude: float, climate_zone: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze seasonal risks for orchid growing"""
        abs_lat = abs(latitude)
        
        risks = {
            'winter': [],
            'spring': [],
            'summer': [],
            'fall': []
        }
        
        if abs_lat > 35:  # Temperate climates
            risks['winter'].extend(['Frost damage', 'Low humidity from heating', 'Insufficient light'])
            risks['summer'].extend(['Heat stress', 'High humidity issues'])
        elif abs_lat > 25:  # Subtropical
            risks['winter'].extend(['Occasional cold snaps', 'Dry periods'])
            risks['summer'].extend(['Excessive heat', 'Storm damage'])
        else:  # Tropical
            risks['summer'].extend(['Heavy rains', 'High humidity fungal issues'])
            risks['winter'].extend(['Dry season stress'])
        
        # Common risks for all locations
        risks['spring'].extend(['Temperature fluctuations', 'Pest emergence'])
        risks['fall'].extend(['Preparation for dormancy', 'Pest prevention'])
        
        return risks
    
    def _identify_growing_challenges(self, latitude: float, climate_zone: Dict[str, Any]) -> List[str]:
        """Identify main growing challenges for the location"""
        abs_lat = abs(latitude)
        challenges = []
        
        if abs_lat > 40:
            challenges.extend([
                'Short growing season',
                'Winter light supplementation needed',
                'Heating costs and dry air',
                'Limited outdoor growing time'
            ])
        elif abs_lat > 25:
            challenges.extend([
                'Summer heat management',
                'Occasional frost protection',
                'Seasonal humidity control'
            ])
        else:
            challenges.extend([
                'Year-round humidity management',
                'Pest pressure',
                'Storm and rain protection'
            ])
        
        return challenges
    
    def _identify_location_advantages(self, latitude: float, climate_zone: Dict[str, Any]) -> List[str]:
        """Identify growing advantages for the location"""
        abs_lat = abs(latitude)
        advantages = []
        
        if abs_lat > 40:
            advantages.extend([
                'Excellent natural seasonal photoperiod variation',
                'Cool nights ideal for many orchids',
                'Low pest pressure in winter',
                'Natural dormancy triggers'
            ])
        elif abs_lat > 25:
            advantages.extend([
                'Good seasonal variation',
                'Natural temperature differentials',
                'Moderate growing season'
            ])
        else:
            advantages.extend([
                'Year-round growing possible',
                'Natural humidity',
                'Consistent temperatures'
            ])
        
        return advantages
    
    def _estimate_sunrise_sunset(self, latitude: float, month: int) -> Dict[str, str]:
        """Estimate approximate sunrise and sunset times"""
        daylight_hours = self._calculate_daylight_hours(latitude, month)
        
        # Rough estimation assuming sunrise/sunset symmetric around solar noon
        sunrise_hour = 12 - daylight_hours / 2
        sunset_hour = 12 + daylight_hours / 2
        
        def format_time(hour):
            h = int(hour)
            m = int((hour - h) * 60)
            return f"{h:02d}:{m:02d}"
        
        return {
            'sunrise': format_time(sunrise_hour),
            'sunset': format_time(sunset_hour)
        }
    
    def _assess_photoperiod_orchid_impact(self, daylight_hours: float) -> str:
        """Assess the impact of photoperiod on orchids"""
        if daylight_hours < 10:
            return "Short day period - triggers blooming in many orchids"
        elif daylight_hours > 14:
            return "Long day period - promotes vegetative growth"
        else:
            return "Moderate photoperiod - balanced growth and flowering"
    
    def _analyze_seasonal_photoperiod_patterns(self, monthly_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze seasonal photoperiod patterns for orchid cultivation"""
        daylight_values = [data['daylight_hours'] for data in monthly_data.values()]
        
        min_daylight = min(daylight_values)
        max_daylight = max(daylight_values)
        variation = max_daylight - min_daylight
        
        if variation < 2:
            pattern_type = "Minimal seasonal variation"
            orchid_impact = "Stable photoperiods - good for equatorial species"
        elif variation < 4:
            pattern_type = "Moderate seasonal variation"
            orchid_impact = "Good seasonal cues for most tropical orchids"
        elif variation < 6:
            pattern_type = "Strong seasonal variation"
            orchid_impact = "Excellent natural bloom triggers for temperate orchids"
        else:
            pattern_type = "Extreme seasonal variation"
            orchid_impact = "Intense seasonal signals - ideal for deciduous species"
        
        return {
            'pattern_type': pattern_type,
            'min_daylight': min_daylight,
            'max_daylight': max_daylight,
            'variation_hours': variation,
            'orchid_cultivation_impact': orchid_impact,
            'bloom_triggering_months': self._identify_bloom_trigger_months(monthly_data)
        }
    
    def _identify_bloom_trigger_months(self, monthly_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Identify months that typically trigger blooming"""
        daylight_changes = {}
        months = list(monthly_data.keys())
        
        for i, month in enumerate(months):
            prev_month = months[i-1]
            current_hours = monthly_data[month]['daylight_hours']
            prev_hours = monthly_data[prev_month]['daylight_hours']
            change = current_hours - prev_hours
            daylight_changes[month] = change
        
        decreasing_months = [month for month, change in daylight_changes.items() if change < -0.5]
        increasing_months = [month for month, change in daylight_changes.items() if change > 0.5]
        
        return {
            'shortening_days': decreasing_months,
            'lengthening_days': increasing_months,
            'short_day_bloomers_triggered': decreasing_months,
            'long_day_bloomers_triggered': increasing_months
        }
    
    def _generate_emergency_care_guide(self, orchid_record: OrchidRecord, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate emergency care guide for local weather events"""
        climate_zone = location_data.get('climate_zone', {})
        zone_name = climate_zone.get('zone', 'Unknown')
        
        emergency_guide = {
            'heat_wave': [
                'Increase watering frequency',
                'Provide extra shade/move away from windows',
                'Increase humidity with trays or humidifiers',
                'Improve air circulation with fans'
            ],
            'cold_snap': [
                'Move plants away from windows',
                'Reduce watering temporarily',
                'Provide supplemental heating if needed',
                'Watch for cold damage on leaves'
            ],
            'dry_period': [
                'Increase watering frequency',
                'Add humidity trays',
                'Group plants together',
                'Monitor for dehydration signs'
            ],
            'storm_preparation': [
                'Secure outdoor plants',
                'Provide wind protection',
                'Ensure good drainage',
                'Check for physical damage after storms'
            ]
        }
        
        # Add location-specific emergency items
        if 'Temperate' in zone_name:
            emergency_guide['winter_care'] = [
                'Provide grow lights for short days',
                'Monitor for dry air from heating',
                'Reduce fertilizing in winter',
                'Watch for spider mites in dry conditions'
            ]
        
        return emergency_guide
    
    def _create_seasonal_checklist(self, orchid_record: OrchidRecord, location_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Create seasonal checklist for orchid care"""
        return {
            'Spring': [
                'Begin increasing watering as growth resumes',
                'Start regular fertilizing program',
                'Check for new growth and root activity',
                'Repot if medium is broken down',
                'Increase light gradually',
                'Watch for pest emergence'
            ],
            'Summer': [
                'Monitor for heat stress',
                'Maintain consistent moisture',
                'Provide maximum light (with protection from direct sun)',
                'Increase air circulation',
                'Watch for fungal issues in high humidity'
            ],
            'Fall': [
                'Begin reducing watering frequency',
                'Reduce fertilizer concentration',
                'Prepare for temperature drops',
                'Check photoperiod needs for bloom induction',
                'Clean up dead leaves and debris'
            ],
            'Winter': [
                'Reduce watering significantly',
                'Provide supplemental lighting if needed',
                'Maintain humidity despite heating',
                'Watch for bloom spikes developing',
                'Avoid repotting unless absolutely necessary'
            ]
        }

# Location detection and culture sheet generation functions
def detect_user_location() -> Dict[str, Any]:
    """Attempt to detect user's location (placeholder for now)"""
    # In a full implementation, this could use IP geolocation, user input, or browser APIs
    return {
        'city': 'San Francisco',
        'latitude': 37.7749,
        'longitude': -122.4194,
        'detected': False,
        'note': 'Default location - user should specify their actual location'
    }

def get_available_orchid_species() -> List[str]:
    """Get list of available orchid species for culture sheet generation"""
    try:
        species = db.session.query(OrchidRecord.scientific_name).distinct().all()
        return [s[0] for s in species if s[0]]
    except Exception as e:
        logger.error(f"Error getting available species: {str(e)}")
        return []