"""
Weather service integration using Open-Meteo API
Provides current and historical weather data for orchid cultivation analysis
"""

import requests
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from app import db
from models import WeatherData, UserLocation, WeatherAlert

logger = logging.getLogger(__name__)

class WeatherService:
    """Service for fetching and managing weather data"""
    
    BASE_URL = "https://api.open-meteo.com/v1"
    FORECAST_URL = f"{BASE_URL}/forecast"
    HISTORICAL_URL = f"{BASE_URL}/historical"
    
    @staticmethod
    def get_growing_conditions_analysis(weather_data: WeatherData, orchid_records: List = None) -> Dict:
        """Analyze growing conditions based on weather and Baker culture data"""
        try:
            analysis = {
                'overall_rating': 'good',
                'temperature_status': 'optimal',
                'humidity_status': 'adequate', 
                'recommendations': [],
                'baker_insights': []
            }
            
            # Analyze temperature
            temp = weather_data.temperature
            if temp:
                if temp < 10:
                    analysis['temperature_status'] = 'too_cold'
                    analysis['recommendations'].append('Protect orchids from cold temperatures')
                elif temp > 35:
                    analysis['temperature_status'] = 'too_hot'
                    analysis['recommendations'].append('Increase ventilation and reduce light')
                elif 15 <= temp <= 30:
                    analysis['temperature_status'] = 'optimal'
            
            # Analyze humidity
            humidity = weather_data.humidity
            if humidity:
                if humidity < 40:
                    analysis['humidity_status'] = 'low'
                    analysis['recommendations'].append('Increase humidity around orchids')
                elif humidity > 90:
                    analysis['humidity_status'] = 'high'
                    analysis['recommendations'].append('Improve air circulation')
                elif 50 <= humidity <= 80:
                    analysis['humidity_status'] = 'optimal'
            
            # Add Baker culture insights for specific orchids
            if orchid_records:
                from orchid_ai import analyze_baker_culture_data
                for orchid in orchid_records:
                    if orchid.cultural_notes and 'BAKER' in orchid.cultural_notes:
                        baker_data = analyze_baker_culture_data(orchid.cultural_notes)
                        if baker_data:
                            analysis['baker_insights'].append({
                                'orchid': orchid.display_name,
                                'insights': baker_data
                            })
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing growing conditions: {str(e)}")
            return {'overall_rating': 'unknown', 'recommendations': []}
    
    @staticmethod
    def get_current_weather(latitude: float, longitude: float, location_name: str = None) -> Optional[WeatherData]:
        """Fetch current weather conditions"""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "current_weather": True,
                "hourly": [
                    "temperature_2m", "relative_humidity_2m", "precipitation",
                    "wind_speed_10m", "wind_direction_10m", "pressure_msl",
                    "cloud_cover", "uv_index"
                ],
                "daily": [
                    "temperature_2m_max", "temperature_2m_min", "precipitation_sum"
                ],
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Parse current weather
            current = data.get('current_weather', {})
            hourly = data.get('hourly', {})
            daily = data.get('daily', {})
            
            # Create weather record
            weather = WeatherData(
                location_name=location_name,
                latitude=latitude,
                longitude=longitude,
                temperature=current.get('temperature'),
                wind_speed=current.get('windspeed'),
                wind_direction=current.get('winddirection'),
                weather_code=current.get('weathercode'),
                recorded_at=datetime.utcnow(),
                data_source='open-meteo',
                is_forecast=False
            )
            
            # Add additional data from hourly if available
            if hourly and hourly.get('time'):
                current_hour_index = 0  # Most recent hour
                weather.humidity = hourly.get('relative_humidity_2m', [None])[current_hour_index]
                weather.precipitation = hourly.get('precipitation', [None])[current_hour_index]
                weather.pressure = hourly.get('pressure_msl', [None])[current_hour_index]
                weather.cloud_cover = hourly.get('cloud_cover', [None])[current_hour_index]
                weather.uv_index = hourly.get('uv_index', [None])[current_hour_index]
            
            # Add daily min/max temperatures
            if daily and daily.get('time'):
                weather.temperature_max = daily.get('temperature_2m_max', [None])[0]
                weather.temperature_min = daily.get('temperature_2m_min', [None])[0]
            
            # Calculate derived metrics
            weather.calculate_vpd()
            weather.description = weather.get_weather_description()
            
            # Save to database
            db.session.add(weather)
            db.session.commit()
            
            logger.info(f"Fetched current weather for {location_name or f'{latitude},{longitude}'}")
            return weather
            
        except Exception as e:
            logger.error(f"Error fetching current weather: {str(e)}")
            return None
    
    @staticmethod
    def get_historical_weather(latitude: float, longitude: float, 
                             start_date: datetime, end_date: datetime,
                             location_name: str = None) -> List[WeatherData]:
        """Fetch historical weather data"""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "daily": [
                    "temperature_2m_max", "temperature_2m_min", "temperature_2m_mean",
                    "relative_humidity_2m_max", "relative_humidity_2m_min", "relative_humidity_2m_mean",
                    "precipitation_sum", "wind_speed_10m_max", "wind_direction_10m_dominant",
                    "pressure_msl_mean", "cloud_cover_mean", "uv_index_max"
                ],
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.HISTORICAL_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily_data = data.get('daily', {})
            if not daily_data.get('time'):
                return []
            
            weather_records = []
            
            for i, date_str in enumerate(daily_data['time']):
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    weather = WeatherData(
                        location_name=location_name,
                        latitude=latitude,
                        longitude=longitude,
                        temperature=daily_data.get('temperature_2m_mean', [None])[i],
                        temperature_max=daily_data.get('temperature_2m_max', [None])[i],
                        temperature_min=daily_data.get('temperature_2m_min', [None])[i],
                        humidity=daily_data.get('relative_humidity_2m_mean', [None])[i],
                        precipitation=daily_data.get('precipitation_sum', [None])[i],
                        wind_speed=daily_data.get('wind_speed_10m_max', [None])[i],
                        wind_direction=daily_data.get('wind_direction_10m_dominant', [None])[i],
                        pressure=daily_data.get('pressure_msl_mean', [None])[i],
                        cloud_cover=daily_data.get('cloud_cover_mean', [None])[i],
                        uv_index=daily_data.get('uv_index_max', [None])[i],
                        recorded_at=date,
                        data_source='open-meteo',
                        is_forecast=False
                    )
                    
                    # Calculate derived metrics
                    weather.calculate_vpd()
                    weather.description = 'Historical data'
                    
                    weather_records.append(weather)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing historical weather data for {date_str}: {e}")
                    continue
            
            # Bulk save to database
            if weather_records:
                db.session.add_all(weather_records)
                db.session.commit()
                logger.info(f"Saved {len(weather_records)} historical weather records")
            
            return weather_records
            
        except Exception as e:
            logger.error(f"Error fetching historical weather: {str(e)}")
            return []
    
    @staticmethod
    def get_weather_forecast(latitude: float, longitude: float, 
                           days: int = 7, location_name: str = None) -> List[WeatherData]:
        """Fetch weather forecast"""
        try:
            params = {
                "latitude": latitude,
                "longitude": longitude,
                "daily": [
                    "temperature_2m_max", "temperature_2m_min",
                    "relative_humidity_2m_max", "relative_humidity_2m_min",
                    "precipitation_sum", "precipitation_probability_max",
                    "wind_speed_10m_max", "wind_direction_10m_dominant",
                    "uv_index_max", "weather_code"
                ],
                "forecast_days": min(days, 16),  # Max 16 days for free API
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.FORECAST_URL, params=params)
            response.raise_for_status()
            data = response.json()
            
            daily_data = data.get('daily', {})
            if not daily_data.get('time'):
                return []
            
            forecast_records = []
            
            for i, date_str in enumerate(daily_data['time']):
                try:
                    date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    weather = WeatherData(
                        location_name=location_name,
                        latitude=latitude,
                        longitude=longitude,
                        temperature_max=daily_data.get('temperature_2m_max', [None])[i],
                        temperature_min=daily_data.get('temperature_2m_min', [None])[i],
                        precipitation=daily_data.get('precipitation_sum', [None])[i],
                        wind_speed=daily_data.get('wind_speed_10m_max', [None])[i],
                        wind_direction=daily_data.get('wind_direction_10m_dominant', [None])[i],
                        uv_index=daily_data.get('uv_index_max', [None])[i],
                        weather_code=daily_data.get('weather_code', [None])[i],
                        recorded_at=date,
                        data_source='open-meteo',
                        is_forecast=True
                    )
                    
                    # Calculate average temperature and humidity
                    if weather.temperature_max and weather.temperature_min:
                        weather.temperature = (weather.temperature_max + weather.temperature_min) / 2
                    
                    humidity_max = daily_data.get('relative_humidity_2m_max', [None])[i]
                    humidity_min = daily_data.get('relative_humidity_2m_min', [None])[i]
                    if humidity_max and humidity_min:
                        weather.humidity = (humidity_max + humidity_min) / 2
                    
                    # Calculate derived metrics
                    weather.calculate_vpd()
                    weather.description = weather.get_weather_description()
                    
                    forecast_records.append(weather)
                    
                except (ValueError, IndexError) as e:
                    logger.warning(f"Error parsing forecast data for {date_str}: {e}")
                    continue
            
            # Save to database
            if forecast_records:
                db.session.add_all(forecast_records)
                db.session.commit()
                logger.info(f"Saved {len(forecast_records)} forecast records")
            
            return forecast_records
            
        except Exception as e:
            logger.error(f"Error fetching weather forecast: {str(e)}")
            return []
    
    @staticmethod
    def check_orchid_weather_alerts(location: UserLocation) -> List[WeatherAlert]:
        """Check for weather conditions that might affect orchids"""
        alerts = []
        
        try:
            # Get current weather
            current_weather = WeatherService.get_current_weather(
                location.latitude, location.longitude, location.name
            )
            
            if not current_weather:
                return alerts
            
            # Check for various alert conditions
            
            # Temperature alerts
            if current_weather.temperature and current_weather.temperature < 5:
                alerts.append(WeatherAlert(
                    location_id=location.id,
                    user_id=location.user_id,
                    alert_type='frost_warning',
                    severity='critical',
                    title='Frost Warning',
                    message=f'Temperature dropping to {current_weather.temperature:.1f}°C. Protect your orchids!',
                    orchid_care_advice='Move outdoor orchids inside or provide frost protection. Check greenhouse heating.',
                    expires_at=datetime.utcnow() + timedelta(hours=24)
                ))
            
            elif current_weather.temperature and current_weather.temperature > 35:
                alerts.append(WeatherAlert(
                    location_id=location.id,
                    user_id=location.user_id,
                    alert_type='heat_warning',
                    severity='high',
                    title='Extreme Heat Warning',
                    message=f'Temperature reaching {current_weather.temperature:.1f}°C. Provide shade and extra humidity.',
                    orchid_care_advice='Increase ventilation, provide shade cloth, mist frequently, check water levels.',
                    expires_at=datetime.utcnow() + timedelta(hours=12)
                ))
            
            # Humidity alerts
            if current_weather.humidity and current_weather.humidity < 30:
                alerts.append(WeatherAlert(
                    location_id=location.id,
                    user_id=location.user_id,
                    alert_type='low_humidity',
                    severity='medium',
                    title='Low Humidity Alert',
                    message=f'Humidity at {current_weather.humidity:.0f}%. Orchids prefer 50-70% humidity.',
                    orchid_care_advice='Increase humidity with trays, grouping plants, or humidifiers. Reduce watering frequency.',
                    expires_at=datetime.utcnow() + timedelta(hours=8)
                ))
            
            # Wind/storm alerts
            if current_weather.wind_speed and current_weather.wind_speed > 50:
                alerts.append(WeatherAlert(
                    location_id=location.id,
                    user_id=location.user_id,
                    alert_type='wind_warning',
                    severity='high',
                    title='High Wind Warning',
                    message=f'Winds reaching {current_weather.wind_speed:.0f} km/h. Secure your orchids.',
                    orchid_care_advice='Move orchids to protected areas, secure hanging baskets, check supports.',
                    expires_at=datetime.utcnow() + timedelta(hours=6)
                ))
            
            # Severe weather alerts
            if current_weather.weather_code in [95, 96, 99]:  # Thunderstorms
                alerts.append(WeatherAlert(
                    location_id=location.id,
                    user_id=location.user_id,
                    alert_type='storm_warning',
                    severity='critical',
                    title='Thunderstorm Warning',
                    message='Severe weather approaching. Protect your orchid collection.',
                    orchid_care_advice='Move orchids indoors, secure greenhouse structures, avoid watering during storms.',
                    expires_at=datetime.utcnow() + timedelta(hours=4)
                ))
            
            # Save alerts to database
            if alerts:
                db.session.add_all(alerts)
                db.session.commit()
                logger.info(f"Generated {len(alerts)} weather alerts for {location.name}")
            
            return alerts
            
        except Exception as e:
            logger.error(f"Error checking weather alerts: {str(e)}")
            return []
    
    @staticmethod
    def get_growing_conditions_summary(location: UserLocation, days: int = 7) -> Dict:
        """Get a summary of growing conditions for orchids"""
        try:
            # Get recent weather data
            recent_weather = db.session.query(WeatherData).filter(
                WeatherData.latitude == location.latitude,
                WeatherData.longitude == location.longitude,
                WeatherData.recorded_at >= datetime.utcnow() - timedelta(days=days),
                WeatherData.is_forecast == False
            ).order_by(WeatherData.recorded_at.desc()).all()
            
            if not recent_weather:
                return {"error": "No recent weather data available"}
            
            # Calculate averages and trends
            temps = [w.temperature for w in recent_weather if w.temperature]
            humidity_vals = [w.humidity for w in recent_weather if w.humidity]
            vpd_vals = [w.vpd for w in recent_weather if w.vpd]
            
            summary = {
                "period_days": days,
                "data_points": len(recent_weather),
                "temperature": {
                    "avg": sum(temps) / len(temps) if temps else None,
                    "min": min(temps) if temps else None,
                    "max": max(temps) if temps else None,
                    "trend": "stable"  # Could add trend calculation
                },
                "humidity": {
                    "avg": sum(humidity_vals) / len(humidity_vals) if humidity_vals else None,
                    "min": min(humidity_vals) if humidity_vals else None,
                    "max": max(humidity_vals) if humidity_vals else None
                },
                "vpd": {
                    "avg": sum(vpd_vals) / len(vpd_vals) if vpd_vals else None,
                    "optimal_range": "0.8-1.2 kPa"
                },
                "orchid_friendly_days": len([w for w in recent_weather if w.is_orchid_friendly()]),
                "recommendations": []
            }
            
            # Add recommendations based on conditions
            if summary["temperature"]["avg"] and summary["temperature"]["avg"] < 18:
                summary["recommendations"].append("Consider supplemental heating for optimal orchid growth")
            
            if summary["humidity"]["avg"] and summary["humidity"]["avg"] < 50:
                summary["recommendations"].append("Increase humidity for better orchid health")
            
            if summary["vpd"]["avg"] and summary["vpd"]["avg"] > 1.5:
                summary["recommendations"].append("High VPD - increase humidity or reduce temperature")
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating growing conditions summary: {str(e)}")
            return {"error": str(e)}

def get_coordinates_from_location(location_name: str) -> Optional[Tuple[float, float]]:
    """Get coordinates from location name using a geocoding service"""
    try:
        # Use Open-Meteo's geocoding API
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": location_name,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        response = requests.get(geocoding_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            return result['latitude'], result['longitude']
        
        return None
        
    except Exception as e:
        logger.error(f"Error geocoding location {location_name}: {str(e)}")
        return None

def get_coordinates_from_zip_code(zip_code: str, country: str = "US") -> Optional[dict]:
    """Get coordinates and location details from ZIP code"""
    try:
        # Format ZIP code search query
        search_query = f"{zip_code}"
        if country and country.upper() != "US":
            search_query = f"{zip_code}, {country}"
        
        # Use Open-Meteo's geocoding API
        geocoding_url = "https://geocoding-api.open-meteo.com/v1/search"
        params = {
            "name": search_query,
            "count": 1,
            "language": "en",
            "format": "json"
        }
        
        response = requests.get(geocoding_url, params=params)
        response.raise_for_status()
        data = response.json()
        
        if data.get('results') and len(data['results']) > 0:
            result = data['results'][0]
            return {
                'latitude': result['latitude'],
                'longitude': result['longitude'],
                'city': result.get('name', ''),
                'state_province': result.get('admin1', ''),
                'country': result.get('country', ''),
                'timezone': result.get('timezone', ''),
                'name': f"{result.get('name', '')}, {result.get('admin1', '')}"
            }
        
        return None
        
    except Exception as e:
        logger.error(f"Error geocoding ZIP code {zip_code}: {str(e)}")
        return None