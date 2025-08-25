"""
Weather/Habitat Comparison Widget
Compares local growing conditions with orchid native habitat using biologically meaningful alignment methods
"""

import os
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ComparisonMode(Enum):
    """Available comparison modes for weather/habitat analysis"""
    CALENDAR = "calendar"      # Raw comparison - today vs today
    SEASONAL = "seasonal"      # Seasonal phase alignment with hemisphere offset
    PHOTOPERIOD = "photoperiod"  # Daylength and solar time alignment

class ConfidenceLevel(Enum):
    """Confidence levels for habitat comparisons"""
    HIGH = "High"
    MEDIUM = "Medium" 
    LOW = "Low"

@dataclass
class LocationData:
    """Location information with climate data"""
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    city: Optional[str] = None
    country: Optional[str] = None
    timezone: Optional[str] = None

@dataclass
class WeatherConditions:
    """Current weather conditions"""
    temperature: float  # Celsius
    humidity: float     # Percentage
    pressure: Optional[float] = None  # hPa
    wind_speed: Optional[float] = None  # m/s
    solar_hour: Optional[float] = None  # Solar time hour
    timestamp: Optional[datetime] = None

@dataclass
class ClimateNormals:
    """30-year climate normals for habitat comparison"""
    temp_min: float
    temp_max: float
    temp_avg: float
    humidity_avg: float
    precipitation: float
    month: int
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM

@dataclass
class ComparisonBadge:
    """Transparency badge for comparison methods"""
    type: str  # "hemisphere", "solar", "elevation", "confidence"
    value: str
    description: str
    color: str = "secondary"

class WeatherHabitatComparison:
    """Main widget class for weather/habitat comparison analysis"""
    
    def __init__(self):
        self.openai_client = None
        try:
            import openai
            api_key = os.environ.get('OPENAI_API_KEY')
            if api_key:
                self.openai_client = openai.OpenAI(api_key=api_key)
        except ImportError:
            logger.warning("OpenAI not available for weather insights")
    
    def compare_conditions(self, 
                         local_location: LocationData,
                         habitat_location: LocationData,
                         local_weather: WeatherConditions,
                         mode: ComparisonMode = ComparisonMode.SEASONAL,
                         environment_type: str = "greenhouse") -> Dict[str, Any]:
        """
        Compare local growing conditions with orchid habitat
        
        Args:
            local_location: User's growing location
            habitat_location: Orchid's native habitat location
            local_weather: Current local weather conditions
            mode: Comparison alignment mode
            environment_type: indoor, outdoor, greenhouse, lights
        
        Returns:
            Complete comparison analysis with charts, badges, and insights
        """
        try:
            # Calculate alignment and adjustments
            alignment_data = self._calculate_alignment(local_location, habitat_location, mode)
            
            # Get habitat climate data
            habitat_climate = self._get_habitat_climate_normals(habitat_location, alignment_data)
            
            # Generate comparison badges
            badges = self._generate_transparency_badges(alignment_data, habitat_climate)
            
            # Create chart data
            charts = self._generate_comparison_charts(
                local_location, habitat_location, local_weather, 
                habitat_climate, alignment_data, mode
            )
            
            # Generate plain English insights
            insights = self._generate_plain_english_insights(
                local_weather, habitat_climate, alignment_data, environment_type
            )
            
            return {
                'mode': mode.value,
                'local_location': local_location.__dict__,
                'habitat_location': habitat_location.__dict__,
                'alignment': alignment_data,
                'badges': [badge.__dict__ for badge in badges],
                'charts': charts,
                'insights': insights,
                'confidence': self._calculate_overall_confidence(habitat_climate, alignment_data),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in weather habitat comparison: {str(e)}")
            return {'error': str(e)}
    
    def _calculate_alignment(self, local_loc: LocationData, habitat_loc: LocationData, 
                           mode: ComparisonMode) -> Dict[str, Any]:
        """Calculate alignment based on comparison mode"""
        
        # Determine hemisphere offset
        local_hemisphere = "North" if local_loc.latitude >= 0 else "South"
        habitat_hemisphere = "North" if habitat_loc.latitude >= 0 else "South"
        hemisphere_offset_months = 6 if local_hemisphere != habitat_hemisphere else 0
        
        alignment = {
            'mode': mode.value,
            'hemisphere_offset_months': hemisphere_offset_months,
            'local_hemisphere': local_hemisphere,
            'habitat_hemisphere': habitat_hemisphere,
            'elevation_difference': None,
            'solar_alignment': False,
            'seasonal_phase_match': None
        }
        
        # Calculate elevation difference if available
        if local_loc.elevation and habitat_loc.elevation:
            alignment['elevation_difference'] = local_loc.elevation - habitat_loc.elevation
        
        if mode == ComparisonMode.CALENDAR:
            # Raw comparison - no adjustments
            alignment['description'] = "Direct calendar comparison"
            
        elif mode == ComparisonMode.SEASONAL:
            # Seasonal phase alignment
            current_month = datetime.now().month
            adjusted_month = (current_month + hemisphere_offset_months - 1) % 12 + 1
            alignment['habitat_equivalent_month'] = adjusted_month
            alignment['seasonal_phase_match'] = self._get_seasonal_phase(current_month, local_hemisphere)
            alignment['description'] = f"Seasonal alignment: {hemisphere_offset_months} month offset"
            
        elif mode == ComparisonMode.PHOTOPERIOD:
            # Photoperiod and solar time alignment
            current_daylength = self._calculate_daylength(local_loc.latitude, datetime.now())
            habitat_equivalent_date = self._find_matching_daylength_date(habitat_loc.latitude, current_daylength)
            alignment['solar_alignment'] = True
            alignment['habitat_equivalent_date'] = habitat_equivalent_date.isoformat() if habitat_equivalent_date else None
            alignment['daylength_hours'] = current_daylength
            alignment['description'] = f"Photoperiod alignment: {current_daylength:.1f}h daylength match"
        
        return alignment
    
    def _get_habitat_climate_normals(self, habitat_loc: LocationData, 
                                   alignment: Dict[str, Any]) -> ClimateNormals:
        """Get climate normals for habitat location based on alignment"""
        
        # For demo purposes, generate realistic climate data
        # In production, this would query actual climate databases
        current_month = datetime.now().month
        
        if alignment['mode'] == 'seasonal' and 'habitat_equivalent_month' in alignment:
            target_month = alignment['habitat_equivalent_month']
        else:
            target_month = current_month
        
        # Generate realistic tropical/subtropical climate data based on latitude
        abs_lat = abs(habitat_loc.latitude)
        
        if abs_lat <= 10:  # Tropical
            temp_base = 26
            temp_variation = 3
            humidity_base = 80
        elif abs_lat <= 23:  # Subtropical
            temp_base = 24
            temp_variation = 8
            humidity_base = 70
        else:  # Temperate
            temp_base = 18
            temp_variation = 15
            humidity_base = 65
        
        # Seasonal adjustment
        seasonal_factor = math.cos((target_month - 1) * math.pi / 6)
        temp_avg = temp_base + (seasonal_factor * temp_variation)
        temp_min = temp_avg - 4
        temp_max = temp_avg + 6
        humidity = humidity_base + (seasonal_factor * -10)
        
        confidence = ConfidenceLevel.MEDIUM
        if hasattr(habitat_loc, 'data_source') and habitat_loc.data_source == 'measured':
            confidence = ConfidenceLevel.HIGH
        elif abs_lat > 30:
            confidence = ConfidenceLevel.LOW
        
        return ClimateNormals(
            temp_min=temp_min,
            temp_max=temp_max,
            temp_avg=temp_avg,
            humidity_avg=humidity,
            precipitation=50.0,  # mm
            month=target_month,
            confidence=confidence
        )
    
    def _generate_transparency_badges(self, alignment: Dict[str, Any], 
                                    habitat_climate: ClimateNormals) -> List[ComparisonBadge]:
        """Generate transparency badges showing alignment methods"""
        badges = []
        
        # Hemisphere offset badge
        if alignment['hemisphere_offset_months'] > 0:
            badges.append(ComparisonBadge(
                type="hemisphere",
                value=f"+{alignment['hemisphere_offset_months']} months",
                description=f"Southern hemisphere offset: {alignment['hemisphere_offset_months']} months",
                color="info"
            ))
        
        # Solar alignment badge
        if alignment.get('solar_alignment'):
            badges.append(ComparisonBadge(
                type="solar",
                value="Solar Aligned",
                description="Aligned by daylength and solar time",
                color="warning"
            ))
        
        # Elevation adjustment badge
        if alignment.get('elevation_difference'):
            elev_diff = alignment['elevation_difference']
            badges.append(ComparisonBadge(
                type="elevation",
                value=f"{abs(elev_diff):.0f}m {'higher' if elev_diff > 0 else 'lower'}",
                description=f"Elevation difference: {elev_diff:.0f}m",
                color="secondary"
            ))
        
        # Confidence badge
        badges.append(ComparisonBadge(
            type="confidence",
            value=habitat_climate.confidence.value,
            description=f"Data confidence: {habitat_climate.confidence.value}",
            color=self._get_confidence_color(habitat_climate.confidence)
        ))
        
        return badges
    
    def _generate_comparison_charts(self, local_loc: LocationData, habitat_loc: LocationData,
                                  local_weather: WeatherConditions, habitat_climate: ClimateNormals,
                                  alignment: Dict[str, Any], mode: ComparisonMode) -> Dict[str, Any]:
        """Generate chart data for hourly and seasonal comparisons"""
        
        charts = {
            'hourly': self._generate_hourly_chart(local_weather, habitat_climate, alignment),
            'seasonal': self._generate_seasonal_chart(local_loc, habitat_loc, habitat_climate, alignment)
        }
        
        return charts
    
    def _generate_hourly_chart(self, local_weather: WeatherConditions, 
                             habitat_climate: ClimateNormals, alignment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate hourly comparison chart data"""
        
        # Generate 24-hour data
        hours = list(range(24))
        
        # Local temperature curve (simulated daily variation)
        local_temps = []
        local_humidity = []
        current_hour = datetime.now().hour
        
        for hour in hours:
            # Temperature variation throughout day
            hour_offset = (hour - 14) * math.pi / 12  # Peak at 2 PM
            temp_variation = 8 * math.cos(hour_offset)
            temp = local_weather.temperature + temp_variation
            local_temps.append(temp)
            
            # Humidity inverse relationship with temperature
            humidity_variation = -15 * math.cos(hour_offset)
            humidity = local_weather.humidity + humidity_variation
            local_humidity.append(max(20, min(100, humidity)))
        
        # Habitat comparison (from climate normals)
        habitat_temps = [habitat_climate.temp_avg + 6 * math.cos((h - 14) * math.pi / 12) for h in hours]
        habitat_humidity = [habitat_climate.humidity_avg - 10 * math.cos((h - 14) * math.pi / 12) for h in hours]
        
        return {
            'type': 'hourly',
            'hours': hours,
            'local': {
                'temperature': local_temps,
                'humidity': local_humidity,
                'current_hour': current_hour
            },
            'habitat': {
                'temperature': habitat_temps,
                'humidity': habitat_humidity
            },
            'units': {
                'temperature': '°C',
                'humidity': '%'
            }
        }
    
    def _generate_seasonal_chart(self, local_loc: LocationData, habitat_loc: LocationData,
                               habitat_climate: ClimateNormals, alignment: Dict[str, Any]) -> Dict[str, Any]:
        """Generate seasonal comparison chart data"""
        
        months = list(range(1, 13))
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Generate seasonal patterns
        local_seasonal = self._generate_seasonal_pattern(local_loc.latitude, months)
        habitat_seasonal = self._generate_seasonal_pattern(habitat_loc.latitude, months)
        
        return {
            'type': 'seasonal',
            'months': months,
            'month_names': month_names,
            'local': local_seasonal,
            'habitat': habitat_seasonal,
            'current_month': datetime.now().month,
            'alignment_offset': alignment.get('hemisphere_offset_months', 0)
        }
    
    def _generate_seasonal_pattern(self, latitude: float, months: List[int]) -> Dict[str, List[float]]:
        """Generate seasonal temperature and humidity patterns for a location"""
        
        abs_lat = abs(latitude)
        hemisphere_factor = 1 if latitude >= 0 else -1
        
        # Base climate based on latitude
        if abs_lat <= 10:  # Tropical
            base_temp = 26
            seasonal_variation = 3
            base_humidity = 80
        elif abs_lat <= 23:  # Subtropical  
            base_temp = 24
            seasonal_variation = 8
            base_humidity = 70
        else:  # Temperate
            base_temp = 18
            seasonal_variation = 15
            base_humidity = 65
        
        temps = []
        humidity = []
        
        for month in months:
            # Seasonal temperature variation (peak in summer)
            seasonal_factor = hemisphere_factor * math.cos((month - 7) * math.pi / 6)
            temp = base_temp + (seasonal_factor * seasonal_variation)
            temps.append(temp)
            
            # Humidity tends to be inverse to temperature in many climates
            humid = base_humidity - (seasonal_factor * 15)
            humidity.append(max(30, min(95, humid)))
        
        return {
            'temperature': temps,
            'humidity': humidity
        }
    
    def _generate_plain_english_insights(self, local_weather: WeatherConditions, 
                                       habitat_climate: ClimateNormals, alignment: Dict[str, Any],
                                       environment_type: str) -> List[Dict[str, str]]:
        """Generate plain English insights with specific recommendations"""
        
        insights = []
        
        # Temperature comparison
        temp_diff = local_weather.temperature - habitat_climate.temp_avg
        if abs(temp_diff) > 2:
            direction = "warmer" if temp_diff > 0 else "cooler"
            insights.append({
                'type': 'temperature',
                'severity': 'medium' if abs(temp_diff) < 5 else 'high',
                'message': f"Your {environment_type} today ({local_weather.temperature:.1f}°C) vs habitat average "
                          f"({habitat_climate.temp_avg:.1f}°C). You are {abs(temp_diff):.1f}°C {direction}.",
                'recommendation': self._get_temperature_recommendation(temp_diff, environment_type)
            })
        
        # Humidity comparison
        humidity_diff = local_weather.humidity - habitat_climate.humidity_avg
        humidity_percent_diff = (humidity_diff / habitat_climate.humidity_avg) * 100
        
        if abs(humidity_percent_diff) > 10:
            direction = "higher" if humidity_diff > 0 else "lower"
            insights.append({
                'type': 'humidity',
                'severity': 'medium' if abs(humidity_percent_diff) < 25 else 'high',
                'message': f"Your humidity is {local_weather.humidity:.0f}%. Habitat average: "
                          f"{habitat_climate.humidity_avg:.0f}% ({humidity_percent_diff:+.0f}%).",
                'recommendation': self._get_humidity_recommendation(humidity_diff, environment_type)
            })
        
        # Seasonal alignment insight
        if alignment.get('hemisphere_offset_months'):
            season_local = self._get_seasonal_phase(datetime.now().month, alignment['local_hemisphere'])
            season_habitat = self._get_seasonal_phase(
                (datetime.now().month + alignment['hemisphere_offset_months'] - 1) % 12 + 1,
                alignment['habitat_hemisphere']
            )
            insights.append({
                'type': 'seasonal',
                'severity': 'info',
                'message': f"Your {season_local} conditions compared to habitat {season_habitat} phase.",
                'recommendation': f"Adjust care routine to match habitat's {season_habitat} requirements."
            })
        
        return insights
    
    def _get_temperature_recommendation(self, temp_diff: float, environment_type: str) -> str:
        """Get specific temperature adjustment recommendations"""
        
        if temp_diff > 3:  # Too warm
            if environment_type == "greenhouse":
                return "Increase ventilation, add shade cloth, or use cooling fans."
            elif environment_type == "indoor":
                return "Move to cooler location or use air conditioning."
            elif environment_type == "lights":
                return "Reduce light intensity or increase distance from lights."
            else:
                return "Provide shade during hottest part of day."
        
        elif temp_diff < -3:  # Too cool
            if environment_type == "greenhouse":
                return "Add heating or close vents during cool periods."
            elif environment_type == "indoor":
                return "Move to warmer location or use heating mat."
            elif environment_type == "lights":
                return "Increase light intensity or move closer to lights."
            else:
                return "Provide protection from cold or move indoors."
        
        return "Temperature conditions are suitable."
    
    def _get_humidity_recommendation(self, humidity_diff: float, environment_type: str) -> str:
        """Get specific humidity adjustment recommendations"""
        
        if humidity_diff < -15:  # Too dry
            if environment_type == "greenhouse":
                return "Add humidifiers, misting systems, or water trays."
            elif environment_type == "indoor":
                return "Use humidity trays, group plants together, or add humidifier."
            else:
                return "Increase misting frequency or add humidity trays."
        
        elif humidity_diff > 15:  # Too humid
            if environment_type == "greenhouse":
                return "Improve ventilation and air circulation."
            elif environment_type == "indoor":
                return "Increase air circulation and reduce watering frequency."
            else:
                return "Improve air movement and avoid overwatering."
        
        return "Humidity levels are appropriate."
    
    def _calculate_daylength(self, latitude: float, date: datetime) -> float:
        """Calculate daylength in hours for given latitude and date"""
        
        # Solar declination
        day_of_year = date.timetuple().tm_yday
        declination = 23.45 * math.sin(math.radians(360 * (284 + day_of_year) / 365))
        
        # Hour angle
        lat_rad = math.radians(latitude)
        decl_rad = math.radians(declination)
        
        try:
            hour_angle = math.acos(-math.tan(lat_rad) * math.tan(decl_rad))
            daylength = 2 * hour_angle * 12 / math.pi
            return max(0, min(24, daylength))
        except ValueError:
            # Polar day or polar night
            if latitude * declination > 0:
                return 24.0  # Polar day
            else:
                return 0.0   # Polar night
    
    def _find_matching_daylength_date(self, latitude: float, target_daylength: float) -> Optional[datetime]:
        """Find the date with matching daylength at given latitude"""
        
        current_year = datetime.now().year
        best_date = None
        best_diff = float('inf')
        
        # Check each day of the year
        for day in range(1, 366):
            try:
                date = datetime(current_year, 1, 1) + timedelta(days=day-1)
                daylength = self._calculate_daylength(latitude, date)
                diff = abs(daylength - target_daylength)
                
                if diff < best_diff:
                    best_diff = diff
                    best_date = date
                    
                # If we find an exact match, return it
                if diff < 0.1:
                    return date
                    
            except ValueError:
                continue
        
        return best_date
    
    def _get_seasonal_phase(self, month: int, hemisphere: str) -> str:
        """Get seasonal phase for given month and hemisphere"""
        
        if hemisphere == "North":
            if month in [12, 1, 2]:
                return "winter"
            elif month in [3, 4, 5]:
                return "spring"
            elif month in [6, 7, 8]:
                return "summer"
            else:
                return "autumn"
        else:  # Southern hemisphere
            if month in [12, 1, 2]:
                return "summer"
            elif month in [3, 4, 5]:
                return "autumn"
            elif month in [6, 7, 8]:
                return "winter"
            else:
                return "spring"
    
    def _get_confidence_color(self, confidence: ConfidenceLevel) -> str:
        """Get bootstrap color class for confidence level"""
        if confidence == ConfidenceLevel.HIGH:
            return "success"
        elif confidence == ConfidenceLevel.MEDIUM:
            return "warning"
        else:
            return "danger"
    
    def _calculate_overall_confidence(self, habitat_climate: ClimateNormals, 
                                    alignment: Dict[str, Any]) -> ConfidenceLevel:
        """Calculate overall confidence in the comparison"""
        
        base_confidence = habitat_climate.confidence
        
        # Reduce confidence for large elevation differences
        if alignment.get('elevation_difference') and abs(alignment['elevation_difference']) > 1000:
            if base_confidence == ConfidenceLevel.HIGH:
                base_confidence = ConfidenceLevel.MEDIUM
            elif base_confidence == ConfidenceLevel.MEDIUM:
                base_confidence = ConfidenceLevel.LOW
        
        return base_confidence


def get_user_location_from_ip() -> Optional[LocationData]:
    """Get user location from IP address (fallback method)"""
    try:
        # This would use an IP geolocation service in production
        # For now, return a default location
        return LocationData(
            latitude=37.7749,
            longitude=-122.4194,
            city="San Francisco, CA",
            country="United States"
        )
    except Exception as e:
        logger.error(f"Error getting location from IP: {str(e)}")
        return None


def get_orchid_habitat_location(orchid_id: int) -> Optional[LocationData]:
    """Get habitat location for a specific orchid"""
    try:
        from models import OrchidRecord
        from app import db
        
        orchid = db.session.get(OrchidRecord, orchid_id)
        if not orchid:
            return None
        
        # Extract location from orchid data
        if hasattr(orchid, 'native_latitude') and hasattr(orchid, 'native_longitude'):
            return LocationData(
                latitude=orchid.native_latitude,
                longitude=orchid.native_longitude,
                city=getattr(orchid, 'native_region', None)
            )
        
        # Fallback: estimate from region/genus
        if orchid.region:
            return estimate_habitat_from_region(orchid.region, orchid.genus)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting orchid habitat location: {str(e)}")
        return None


def estimate_habitat_from_region(region: str, genus: str = None) -> Optional[LocationData]:
    """Estimate habitat coordinates from region name and genus"""
    
    # Common orchid habitat regions
    region_coordinates = {
        'southeast asia': LocationData(10.0, 105.0, city="Southeast Asia"),
        'central america': LocationData(15.0, -90.0, city="Central America"),
        'south america': LocationData(-10.0, -60.0, city="South America"),
        'madagascar': LocationData(-20.0, 47.0, city="Madagascar"),
        'africa': LocationData(0.0, 20.0, city="Africa"),
        'australia': LocationData(-25.0, 135.0, city="Australia"),
        'new guinea': LocationData(-6.0, 147.0, city="New Guinea"),
        'borneo': LocationData(1.0, 114.0, city="Borneo"),
        'philippines': LocationData(12.0, 122.0, city="Philippines"),
        'india': LocationData(20.0, 77.0, city="India"),
        'china': LocationData(35.0, 105.0, city="China"),
        'colombia': LocationData(4.0, -72.0, city="Colombia"),
        'ecuador': LocationData(-1.0, -78.0, city="Ecuador"),
        'peru': LocationData(-10.0, -76.0, city="Peru"),
        'brazil': LocationData(-14.0, -51.0, city="Brazil")
    }
    
    region_lower = region.lower()
    for key, location in region_coordinates.items():
        if key in region_lower:
            return location
    
    # Default to tropical region if unknown
    return LocationData(0.0, 0.0, city="Tropical Region")