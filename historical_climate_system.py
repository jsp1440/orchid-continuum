"""
Historical Climate Data Analysis System
Provides long-term climate trend analysis and comparison tools
"""

import os
import json
import logging
import requests
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from flask import Blueprint, render_template, request, jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

historical_climate_bp = Blueprint('historical_climate', __name__, url_prefix='/historical-climate')

@dataclass
class ClimateDataPoint:
    """Single climate data point"""
    timestamp: datetime
    temperature: float
    precipitation: float
    humidity: float
    wind_speed: float
    pressure: float
    location: str

@dataclass
class ClimateTrend:
    """Climate trend analysis"""
    parameter: str  # 'temperature', 'precipitation', etc.
    start_date: datetime
    end_date: datetime
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    rate_of_change: float  # per year
    statistical_significance: float  # p-value
    confidence_interval: Tuple[float, float]
    description: str

@dataclass
class ClimateComparison:
    """Comparison between historical and current climate"""
    location: str
    parameter: str
    historical_average: float
    current_average: float
    change_percentage: float
    change_significance: str
    historical_period: str
    current_period: str

class HistoricalClimateAnalyzer:
    """
    Analyzes historical climate data and trends for research applications
    """
    
    def __init__(self):
        # API endpoints
        self.open_meteo_historical = "https://archive-api.open-meteo.com/v1/archive"
        self.open_meteo_current = "https://api.open-meteo.com/v1/forecast"
        
        # Cache for data
        self.data_cache = {}
        self.cache_duration = timedelta(hours=6)  # Cache for 6 hours
        
        logger.info("🌡️ Historical Climate Analyzer initialized")

    def get_historical_data(self, latitude: float, longitude: float, 
                          start_date: str, end_date: str, 
                          parameters: List[str] = None) -> List[ClimateDataPoint]:
        """
        Fetch historical climate data for a location
        """
        try:
            if parameters is None:
                parameters = ['temperature_2m', 'precipitation', 'relative_humidity_2m', 
                            'wind_speed_10m', 'pressure_msl']
            
            # Create cache key
            cache_key = f"hist_{latitude}_{longitude}_{start_date}_{end_date}_{'-'.join(parameters)}"
            
            # Check cache
            if cache_key in self.data_cache:
                cache_time, cached_data = self.data_cache[cache_key]
                if datetime.now() - cache_time < self.cache_duration:
                    logger.info(f"📋 Using cached historical data for {latitude}, {longitude}")
                    return cached_data
            
            # API parameters
            params = {
                'latitude': latitude,
                'longitude': longitude,
                'start_date': start_date,
                'end_date': end_date,
                'hourly': parameters,
                'timezone': 'auto'
            }
            
            response = requests.get(self.open_meteo_historical, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if 'hourly' not in data:
                raise ValueError("No hourly data in response")
            
            # Convert to ClimateDataPoint objects
            hourly = data['hourly']
            data_points = []
            
            for i, timestamp_str in enumerate(hourly['time']):
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    
                    data_point = ClimateDataPoint(
                        timestamp=timestamp,
                        temperature=hourly.get('temperature_2m', [None])[i] or 0.0,
                        precipitation=hourly.get('precipitation', [None])[i] or 0.0,
                        humidity=hourly.get('relative_humidity_2m', [None])[i] or 0.0,
                        wind_speed=hourly.get('wind_speed_10m', [None])[i] or 0.0,
                        pressure=hourly.get('pressure_msl', [None])[i] or 0.0,
                        location=f"{latitude},{longitude}"
                    )
                    
                    data_points.append(data_point)
                    
                except Exception as e:
                    logger.warning(f"Error parsing data point {i}: {str(e)}")
                    continue
            
            # Cache the data
            self.data_cache[cache_key] = (datetime.now(), data_points)
            
            logger.info(f"📊 Retrieved {len(data_points)} historical data points for {latitude}, {longitude}")
            return data_points
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {str(e)}")
            return []

    def analyze_climate_trends(self, data_points: List[ClimateDataPoint], 
                             parameter: str, years_window: int = 5) -> List[ClimateTrend]:
        """
        Analyze climate trends in the data
        """
        try:
            if not data_points:
                return []
            
            # Convert to pandas DataFrame for easier analysis
            df_data = []
            for point in data_points:
                df_data.append({
                    'timestamp': point.timestamp,
                    'temperature': point.temperature,
                    'precipitation': point.precipitation,
                    'humidity': point.humidity,
                    'wind_speed': point.wind_speed,
                    'pressure': point.pressure
                })
            
            df = pd.DataFrame(df_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            df.set_index('timestamp', inplace=True)
            
            # Resample to annual averages for trend analysis
            annual_data = df.resample('Y').mean()
            
            if len(annual_data) < 3:  # Need at least 3 years for trend analysis
                return []
            
            # Extract the parameter values
            if parameter not in annual_data.columns:
                return []
            
            y_values = annual_data[parameter].dropna()
            x_values = np.arange(len(y_values))
            
            if len(y_values) < 3:
                return []
            
            # Linear regression for trend
            from scipy import stats
            slope, intercept, r_value, p_value, std_err = stats.linregress(x_values, y_values)
            
            # Determine trend direction
            if abs(slope) < 0.01:  # Threshold for "stable"
                trend_direction = 'stable'
            elif slope > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # Calculate confidence interval for slope
            confidence_interval = (slope - 1.96 * std_err, slope + 1.96 * std_err)
            
            # Generate description
            parameter_name = parameter.replace('_', ' ').title()
            if trend_direction == 'stable':
                description = f"{parameter_name} has remained relatively stable over the analyzed period."
            else:
                direction_verb = "increased" if slope > 0 else "decreased"
                description = f"{parameter_name} has {direction_verb} at a rate of {abs(slope):.3f} units per year."
            
            trend = ClimateTrend(
                parameter=parameter,
                start_date=annual_data.index[0].to_pydatetime(),
                end_date=annual_data.index[-1].to_pydatetime(),
                trend_direction=trend_direction,
                rate_of_change=slope,
                statistical_significance=p_value,
                confidence_interval=confidence_interval,
                description=description
            )
            
            return [trend]
            
        except Exception as e:
            logger.error(f"Error analyzing climate trends: {str(e)}")
            return []

    def compare_climate_periods(self, latitude: float, longitude: float,
                              historical_start: str, historical_end: str,
                              current_start: str, current_end: str) -> List[ClimateComparison]:
        """
        Compare climate between historical and current periods
        """
        try:
            # Get historical data
            historical_data = self.get_historical_data(
                latitude, longitude, historical_start, historical_end
            )
            
            # Get current/recent data
            current_data = self.get_historical_data(
                latitude, longitude, current_start, current_end
            )
            
            if not historical_data or not current_data:
                return []
            
            # Convert to DataFrames
            hist_df = pd.DataFrame([{
                'temperature': p.temperature,
                'precipitation': p.precipitation,
                'humidity': p.humidity,
                'wind_speed': p.wind_speed,
                'pressure': p.pressure
            } for p in historical_data])
            
            curr_df = pd.DataFrame([{
                'temperature': p.temperature,
                'precipitation': p.precipitation,
                'humidity': p.humidity,
                'wind_speed': p.wind_speed,
                'pressure': p.pressure
            } for p in current_data])
            
            # Calculate averages
            hist_means = hist_df.mean()
            curr_means = curr_df.mean()
            
            # Create comparisons
            comparisons = []
            location_str = f"{latitude}, {longitude}"
            
            for parameter in hist_means.index:
                hist_avg = hist_means[parameter]
                curr_avg = curr_means[parameter]
                
                if hist_avg == 0:  # Avoid division by zero
                    change_pct = 0
                else:
                    change_pct = ((curr_avg - hist_avg) / hist_avg) * 100
                
                # Determine significance (simplified)
                if abs(change_pct) > 10:
                    significance = 'highly significant'
                elif abs(change_pct) > 5:
                    significance = 'significant'
                elif abs(change_pct) > 2:
                    significance = 'moderate'
                else:
                    significance = 'minimal'
                
                comparison = ClimateComparison(
                    location=location_str,
                    parameter=parameter,
                    historical_average=hist_avg,
                    current_average=curr_avg,
                    change_percentage=change_pct,
                    change_significance=significance,
                    historical_period=f"{historical_start} to {historical_end}",
                    current_period=f"{current_start} to {current_end}"
                )
                
                comparisons.append(comparison)
            
            logger.info(f"🔬 Generated {len(comparisons)} climate comparisons")
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing climate periods: {str(e)}")
            return []

    def analyze_orchid_habitat_trends(self, latitude: float, longitude: float,
                                    years_back: int = 30) -> Dict[str, Any]:
        """
        Analyze climate trends specifically relevant to orchid habitats
        """
        try:
            # Calculate date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=years_back * 365)
            
            # Get historical data
            data_points = self.get_historical_data(
                latitude, longitude, 
                start_date.isoformat(), 
                end_date.isoformat()
            )
            
            if not data_points:
                return {}
            
            # Analyze key parameters for orchids
            orchid_parameters = ['temperature', 'humidity', 'precipitation']
            trends = {}
            
            for param in orchid_parameters:
                trend_analysis = self.analyze_climate_trends(data_points, param)
                if trend_analysis:
                    trends[param] = trend_analysis[0]
            
            # Calculate orchid-specific metrics
            df_data = [{
                'temperature': p.temperature,
                'humidity': p.humidity,
                'precipitation': p.precipitation,
                'timestamp': p.timestamp
            } for p in data_points]
            
            df = pd.DataFrame(df_data)
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Growing season analysis (April-October in Northern Hemisphere)
            df['month'] = df['timestamp'].dt.month
            growing_season = df[df['month'].isin([4, 5, 6, 7, 8, 9, 10])]
            
            # Calculate key orchid habitat metrics
            analysis = {
                'location': f"{latitude}, {longitude}",
                'analysis_period': f"{start_date} to {end_date}",
                'trends': {param: {
                    'direction': trends[param].trend_direction,
                    'rate_per_year': trends[param].rate_of_change,
                    'significance_p_value': trends[param].statistical_significance,
                    'description': trends[param].description
                } for param in trends},
                'growing_season_averages': {
                    'temperature': growing_season['temperature'].mean(),
                    'humidity': growing_season['humidity'].mean(),
                    'precipitation': growing_season['precipitation'].mean()
                },
                'annual_averages': {
                    'temperature': df['temperature'].mean(),
                    'humidity': df['humidity'].mean(),
                    'precipitation': df['precipitation'].mean()
                },
                'extreme_events': {
                    'hot_days_over_35c': len(df[df['temperature'] > 35]),
                    'cold_days_below_0c': len(df[df['temperature'] < 0]),
                    'very_dry_days': len(df[df['humidity'] < 30]),
                    'very_wet_days': len(df[df['precipitation'] > 20])
                }
            }
            
            logger.info(f"🌺 Completed orchid habitat trend analysis for {latitude}, {longitude}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing orchid habitat trends: {str(e)}")
            return {}

    def get_climate_summary_for_location(self, latitude: float, longitude: float) -> Dict[str, Any]:
        """
        Get comprehensive climate summary for research purposes
        """
        try:
            # Get recent 5-year period
            recent_end = datetime.now().date()
            recent_start = recent_end - timedelta(days=5 * 365)
            
            # Get historical 30-year average (1990-2020)
            hist_start = "1990-01-01"
            hist_end = "2020-12-31"
            
            # Compare periods
            comparisons = self.compare_climate_periods(
                latitude, longitude,
                hist_start, hist_end,
                recent_start.isoformat(), recent_end.isoformat()
            )
            
            # Get orchid habitat analysis
            habitat_analysis = self.analyze_orchid_habitat_trends(latitude, longitude)
            
            # Combine into summary
            summary = {
                'location': f"{latitude}, {longitude}",
                'analysis_date': datetime.now().isoformat(),
                'period_comparison': {comp.parameter: {
                    'historical_average': comp.historical_average,
                    'recent_average': comp.current_average,
                    'change_percentage': comp.change_percentage,
                    'significance': comp.change_significance
                } for comp in comparisons},
                'orchid_habitat_suitability': habitat_analysis,
                'research_recommendations': self._generate_research_recommendations(comparisons, habitat_analysis)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating climate summary: {str(e)}")
            return {}

    def _generate_research_recommendations(self, comparisons: List[ClimateComparison], 
                                         habitat_analysis: Dict[str, Any]) -> List[str]:
        """
        Generate research recommendations based on climate analysis
        """
        recommendations = []
        
        try:
            # Temperature recommendations
            temp_comparison = next((c for c in comparisons if c.parameter == 'temperature'), None)
            if temp_comparison and abs(temp_comparison.change_percentage) > 5:
                if temp_comparison.change_percentage > 0:
                    recommendations.append(
                        f"Rising temperatures ({temp_comparison.change_percentage:.1f}% increase) may affect orchid flowering timing and mycorrhizal activity. "
                        "Consider research into heat stress adaptation mechanisms."
                    )
                else:
                    recommendations.append(
                        f"Cooling temperatures ({abs(temp_comparison.change_percentage):.1f}% decrease) may extend growing seasons but affect tropical orchid species. "
                        "Research cold tolerance and adaptation strategies."
                    )
            
            # Humidity recommendations
            humidity_comparison = next((c for c in comparisons if c.parameter == 'humidity'), None)
            if humidity_comparison and abs(humidity_comparison.change_percentage) > 10:
                if humidity_comparison.change_percentage > 0:
                    recommendations.append(
                        "Increasing humidity levels may enhance mycorrhizal fungal activity and orchid survival rates. "
                        "Study optimal humidity ranges for carbon transfer efficiency."
                    )
                else:
                    recommendations.append(
                        "Decreasing humidity could stress orchid populations and reduce fungal partnerships. "
                        "Research drought adaptation and water conservation strategies."
                    )
            
            # Precipitation recommendations
            precip_comparison = next((c for c in comparisons if c.parameter == 'precipitation'), None)
            if precip_comparison and abs(precip_comparison.change_percentage) > 15:
                recommendations.append(
                    f"Precipitation patterns have changed significantly ({precip_comparison.change_percentage:.1f}%). "
                    "Research impact on soil mycorrhizal networks and orchid-fungal partnerships."
                )
            
            # General recommendations
            if habitat_analysis and 'trends' in habitat_analysis:
                trends = habitat_analysis['trends']
                changing_params = [param for param, trend in trends.items() 
                                 if trend['direction'] != 'stable']
                
                if len(changing_params) >= 2:
                    recommendations.append(
                        f"Multiple climate parameters are changing ({', '.join(changing_params)}). "
                        "Comprehensive adaptation research needed for orchid-fungal climate solutions."
                    )
            
            if not recommendations:
                recommendations.append(
                    "Climate conditions appear relatively stable. "
                    "Focus research on optimizing current orchid-fungal partnerships for maximum carbon capture efficiency."
                )
            
        except Exception as e:
            logger.warning(f"Error generating recommendations: {str(e)}")
            recommendations.append("Climate analysis incomplete. Recommend collecting additional data for comprehensive assessment.")
        
        return recommendations

# Global climate analyzer
climate_analyzer = HistoricalClimateAnalyzer()

# Routes
@historical_climate_bp.route('/')
def climate_home():
    """Historical climate analysis interface"""
    return render_template('climate/historical_analysis.html')

@historical_climate_bp.route('/analyze', methods=['POST'])
def analyze_location():
    """Analyze climate for a specific location"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        
        if not latitude or not longitude:
            return jsonify({'success': False, 'error': 'Valid latitude and longitude required'}), 400
        
        # Get comprehensive climate summary
        summary = climate_analyzer.get_climate_summary_for_location(latitude, longitude)
        
        return jsonify({
            'success': True,
            'analysis': summary
        })
        
    except Exception as e:
        logger.error(f"Climate analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@historical_climate_bp.route('/trends', methods=['POST'])
def analyze_trends():
    """Analyze climate trends for research"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        years_back = int(data.get('years_back', 30))
        
        # Get orchid habitat trend analysis
        analysis = climate_analyzer.analyze_orchid_habitat_trends(latitude, longitude, years_back)
        
        return jsonify({
            'success': True,
            'trends': analysis
        })
        
    except Exception as e:
        logger.error(f"Trend analysis error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@historical_climate_bp.route('/compare', methods=['POST'])
def compare_periods():
    """Compare climate between different time periods"""
    try:
        data = request.get_json()
        latitude = float(data.get('latitude', 0))
        longitude = float(data.get('longitude', 0))
        historical_start = data.get('historical_start', '1990-01-01')
        historical_end = data.get('historical_end', '2000-12-31')
        current_start = data.get('current_start', '2015-01-01')
        current_end = data.get('current_end', '2024-12-31')
        
        # Perform comparison
        comparisons = climate_analyzer.compare_climate_periods(
            latitude, longitude,
            historical_start, historical_end,
            current_start, current_end
        )
        
        # Convert to JSON format
        comparison_data = []
        for comp in comparisons:
            comparison_data.append({
                'location': comp.location,
                'parameter': comp.parameter,
                'historical_average': comp.historical_average,
                'current_average': comp.current_average,
                'change_percentage': comp.change_percentage,
                'change_significance': comp.change_significance,
                'historical_period': comp.historical_period,
                'current_period': comp.current_period
            })
        
        return jsonify({
            'success': True,
            'comparisons': comparison_data
        })
        
    except Exception as e:
        logger.error(f"Period comparison error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == "__main__":
    print("🌡️ Historical Climate System standalone mode")
    print("Capabilities:")
    print("  - Historical weather data analysis (1940-present)")
    print("  - Climate trend analysis and significance testing")
    print("  - Period comparisons for research")
    print("  - Orchid habitat suitability analysis")