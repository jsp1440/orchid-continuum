#!/usr/bin/env python3
"""
Personalized Growing Condition Matcher
=====================================
Matches users with optimal orchids based on location, climate, and growing setup
Using existing weather integration and comprehensive orchid database

Features:
- Location-based climate analysis using Open-Meteo API
- Growing environment optimization (indoor, outdoor, greenhouse, windowsill)
- Personalized orchid recommendations from 5,888+ orchid database
- Care difficulty scoring and beginner-friendly suggestions
- Seasonal growing recommendations and care calendars
- Local nursery and supplier recommendations
"""

import os
import json
import logging
import math
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from collections import defaultdict

# Flask and database imports
from app import app, db
from models import OrchidRecord, OrchidTaxonomy, WeatherData, UserLocation

# Weather service integration
from weather_service import WeatherService, get_coordinates_from_location, get_coordinates_from_zip_code

# Climate analysis
from weather_habitat_comparison_widget import WeatherHabitatComparison, LocationData, WeatherConditions, ComparisonMode

# OpenAI integration for advanced recommendations
try:
    from openai import OpenAI
    openai_available = True
except ImportError:
    openai_available = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GrowingEnvironment(Enum):
    """Types of growing environments"""
    WINDOWSILL = "windowsill"
    INDOOR_LIGHTS = "indoor_lights"
    GREENHOUSE = "greenhouse"
    OUTDOOR = "outdoor"
    CONSERVATORY = "conservatory"
    TERRARIUM = "terrarium"

class ExperienceLevel(Enum):
    """Grower experience levels"""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class CareDifficulty(Enum):
    """Care difficulty ratings"""
    VERY_EASY = 1
    EASY = 2
    MODERATE = 3
    CHALLENGING = 4
    EXPERT_ONLY = 5

@dataclass
class GrowingSetup:
    """User's growing setup configuration"""
    environment: GrowingEnvironment
    space_size: str  # "small", "medium", "large"
    light_hours: Optional[int] = None
    supplemental_heating: bool = False
    humidity_control: bool = False
    air_circulation: bool = False
    experience_level: ExperienceLevel = ExperienceLevel.BEGINNER
    budget_range: Optional[str] = None  # "low", "medium", "high"
    preferred_colors: List[str] = None
    bloom_timing_preference: Optional[str] = None

@dataclass
class OrchidRecommendation:
    """Personalized orchid recommendation with match scoring"""
    orchid: OrchidRecord
    match_score: float  # 0-100
    care_difficulty: CareDifficulty
    climate_compatibility: float  # 0-100
    environment_suitability: float  # 0-100
    experience_match: float  # 0-100
    reasons: List[str]
    care_tips: List[str]
    seasonal_notes: Dict[str, str]
    expected_challenges: List[str]
    success_indicators: List[str]

class PersonalizedGrowingConditionMatcher:
    """
    Main class for matching users with optimal orchids based on their specific conditions
    """
    
    def __init__(self):
        # Initialize OpenAI client for advanced recommendations
        self.openai_client = None
        if openai_available:
            openai_key = os.environ.get('OPENAI_API_KEY')
            if openai_key:
                try:
                    self.openai_client = OpenAI(api_key=openai_key)
                    logger.info("✅ OpenAI client initialized for personalized recommendations")
                except Exception as e:
                    logger.warning(f"⚠️ OpenAI client initialization failed: {e}")
        
        # Initialize weather service
        self.weather_service = WeatherService()
        self.habitat_comparator = WeatherHabitatComparison()
        
        # Care difficulty scoring matrix
        self.care_difficulty_factors = {
            'temperature_tolerance': {'narrow': 5, 'moderate': 3, 'wide': 1},
            'humidity_requirements': {'high': 4, 'moderate': 2, 'low': 1},
            'watering_frequency': {'daily': 5, 'weekly': 2, 'monthly': 1},
            'light_requirements': {'specific': 4, 'adaptable': 2, 'tolerant': 1},
            'fertilizer_sensitivity': {'sensitive': 4, 'moderate': 2, 'tolerant': 1},
            'pest_susceptibility': {'high': 3, 'moderate': 2, 'low': 1},
            'repotting_frequency': {'annual': 3, 'biennial': 2, 'rare': 1}
        }
        
        logger.info("🌺 Personalized Growing Condition Matcher initialized")
    
    def find_optimal_orchids(self, user_location: str, growing_setup: GrowingSetup, 
                            max_recommendations: int = 10) -> Dict[str, Any]:
        """
        Find the best orchid recommendations for a user's specific location and setup
        
        Args:
            user_location: User's location (city, ZIP code, or coordinates)
            growing_setup: User's growing environment and preferences
            max_recommendations: Maximum number of recommendations to return
            
        Returns:
            Comprehensive recommendations with match analysis
        """
        try:
            logger.info(f"🔍 Finding optimal orchids for location: {user_location}")
            
            # Parse and validate location
            location_data = self._parse_user_location(user_location)
            if not location_data:
                return {
                    "error": "Unable to find location. Please provide a valid city, ZIP code, or coordinates.",
                    "success": False
                }
            
            # Get current and historical weather data
            weather_analysis = self._analyze_local_climate(location_data)
            if not weather_analysis:
                return {
                    "error": "Unable to retrieve climate data for your location.",
                    "success": False
                }
            
            # Get orchid candidates from database
            orchid_candidates = self._get_orchid_candidates(growing_setup)
            if not orchid_candidates:
                return {
                    "error": "No suitable orchids found in database.",
                    "success": False
                }
            
            # Score and rank orchids based on compatibility
            recommendations = self._score_orchid_compatibility(
                orchid_candidates, location_data, weather_analysis, growing_setup
            )
            
            # Limit to requested number
            top_recommendations = recommendations[:max_recommendations]
            
            # Generate care insights and seasonal guidance
            care_insights = self._generate_care_insights(
                top_recommendations, weather_analysis, growing_setup
            )
            
            # Create comprehensive response
            result = {
                "success": True,
                "location": {
                    "name": location_data.get("name", user_location),
                    "latitude": location_data["latitude"],
                    "longitude": location_data["longitude"],
                    "climate_summary": weather_analysis.get("climate_summary", {})
                },
                "growing_setup": {
                    "environment": growing_setup.environment.value,
                    "experience_level": growing_setup.experience_level.value,
                    "space_size": growing_setup.space_size,
                    "has_supplemental_systems": any([
                        growing_setup.supplemental_heating,
                        growing_setup.humidity_control,
                        growing_setup.air_circulation
                    ])
                },
                "recommendations": [self._format_recommendation(rec) for rec in top_recommendations],
                "care_insights": care_insights,
                "seasonal_calendar": self._generate_seasonal_calendar(weather_analysis, growing_setup),
                "total_database_orchids": len(orchid_candidates),
                "analysis_timestamp": datetime.now().isoformat(),
                "next_update_recommended": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
            }
            
            logger.info(f"✅ Generated {len(top_recommendations)} personalized orchid recommendations")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Error finding optimal orchids: {e}")
            return {
                "error": f"Analysis failed: {str(e)}",
                "success": False,
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    def _parse_user_location(self, user_location: str) -> Optional[Dict[str, Any]]:
        """Parse user location input and get coordinates"""
        try:
            # Check if it's coordinates (lat, lon)
            if ',' in user_location and all(part.strip().replace('.', '').replace('-', '').isdigit() 
                                           for part in user_location.split(',')):
                parts = [float(part.strip()) for part in user_location.split(',')]
                if len(parts) == 2:
                    lat, lon = parts
                    return {
                        "latitude": lat,
                        "longitude": lon,
                        "name": f"{lat:.4f}, {lon:.4f}"
                    }
            
            # Check if it's a ZIP code
            if user_location.strip().isdigit() or (len(user_location.strip()) == 5 and user_location.strip().isdigit()):
                coords = get_coordinates_from_zip_code(user_location.strip())
                if coords:
                    return coords
            
            # Try as city/location name
            coords = get_coordinates_from_location(user_location)
            if coords:
                lat, lon = coords
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "name": user_location
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error parsing location '{user_location}': {e}")
            return None
    
    def _analyze_local_climate(self, location_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze local climate conditions for orchid growing"""
        try:
            lat = location_data["latitude"]
            lon = location_data["longitude"]
            location_name = location_data.get("name", f"{lat}, {lon}")
            
            # Get current weather
            current_weather = self.weather_service.get_current_weather(lat, lon, location_name)
            
            # Get historical data for the past 30 days for climate analysis
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30)
            historical_weather = self.weather_service.get_historical_weather(
                lat, lon, start_date, end_date, location_name
            )
            
            # Calculate climate summary
            climate_summary = self._calculate_climate_summary(current_weather, historical_weather)
            
            return {
                "current_weather": current_weather,
                "historical_data": historical_weather,
                "climate_summary": climate_summary,
                "location": location_data
            }
            
        except Exception as e:
            logger.error(f"Error analyzing local climate: {e}")
            return None
    
    def _calculate_climate_summary(self, current_weather, historical_data: List) -> Dict[str, Any]:
        """Calculate climate summary from weather data"""
        try:
            if not historical_data:
                return {"status": "insufficient_data"}
            
            # Extract temperature and humidity data
            temps = [w.temperature for w in historical_data if w.temperature is not None]
            humidity_vals = [w.humidity for w in historical_data if w.humidity is not None]
            
            # Calculate climate zone characteristics
            summary = {
                "temperature": {
                    "current": current_weather.temperature if current_weather else None,
                    "avg": sum(temps) / len(temps) if temps else None,
                    "min": min(temps) if temps else None,
                    "max": max(temps) if temps else None,
                    "range": max(temps) - min(temps) if temps else None
                },
                "humidity": {
                    "current": current_weather.humidity if current_weather else None,
                    "avg": sum(humidity_vals) / len(humidity_vals) if humidity_vals else None,
                    "min": min(humidity_vals) if humidity_vals else None,
                    "max": max(humidity_vals) if humidity_vals else None
                },
                "growing_season_length": self._estimate_growing_season(temps),
                "climate_zone": self._determine_climate_zone(temps, humidity_vals),
                "orchid_friendliness": self._rate_orchid_friendliness(temps, humidity_vals)
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error calculating climate summary: {e}")
            return {"status": "error", "message": str(e)}
    
    def _get_orchid_candidates(self, growing_setup: GrowingSetup) -> List[OrchidRecord]:
        """Get orchid candidates from database based on growing setup"""
        try:
            with app.app_context():
                query = OrchidRecord.query
                
                # Filter based on experience level
                if growing_setup.experience_level == ExperienceLevel.BEGINNER:
                    # Prefer orchids with cultural notes or well-documented species
                    query = query.filter(
                        (OrchidRecord.cultural_notes.isnot(None)) |
                        (OrchidRecord.ai_description.isnot(None))
                    )
                
                # Filter by environment suitability (this could be enhanced with metadata)
                if growing_setup.environment == GrowingEnvironment.WINDOWSILL:
                    # Prefer compact orchids
                    query = query.filter(
                        OrchidRecord.genus.in_(['Phalaenopsis', 'Dendrobium', 'Oncidium', 'Cattleya'])
                    )
                elif growing_setup.environment == GrowingEnvironment.TERRARIUM:
                    # Prefer miniature orchids
                    query = query.filter(
                        OrchidRecord.genus.in_(['Masdevallia', 'Pleurothallis', 'Restrepia'])
                    )
                
                # Get all candidates (we'll score them later)
                candidates = query.limit(500).all()  # Reasonable limit for processing
                
                logger.info(f"Found {len(candidates)} orchid candidates for analysis")
                return candidates
                
        except Exception as e:
            logger.error(f"Error getting orchid candidates: {e}")
            return []
    
    def _score_orchid_compatibility(self, orchids: List[OrchidRecord], location_data: Dict,
                                  weather_analysis: Dict, growing_setup: GrowingSetup) -> List[OrchidRecommendation]:
        """Score orchid compatibility with user's conditions"""
        recommendations = []
        
        try:
            for orchid in orchids:
                # Calculate individual compatibility scores
                climate_score = self._calculate_climate_compatibility(orchid, weather_analysis)
                environment_score = self._calculate_environment_compatibility(orchid, growing_setup)
                experience_score = self._calculate_experience_compatibility(orchid, growing_setup)
                care_difficulty = self._assess_care_difficulty(orchid)
                
                # Calculate overall match score
                match_score = (
                    climate_score * 0.4 +
                    environment_score * 0.3 + 
                    experience_score * 0.3
                )
                
                # Generate recommendations reasons and tips
                reasons = self._generate_match_reasons(orchid, climate_score, environment_score, experience_score)
                care_tips = self._generate_care_tips(orchid, growing_setup, weather_analysis)
                seasonal_notes = self._generate_seasonal_notes(orchid, weather_analysis)
                challenges = self._identify_potential_challenges(orchid, growing_setup, weather_analysis)
                success_indicators = self._generate_success_indicators(orchid)
                
                recommendation = OrchidRecommendation(
                    orchid=orchid,
                    match_score=round(match_score, 1),
                    care_difficulty=care_difficulty,
                    climate_compatibility=round(climate_score, 1),
                    environment_suitability=round(environment_score, 1),
                    experience_match=round(experience_score, 1),
                    reasons=reasons,
                    care_tips=care_tips,
                    seasonal_notes=seasonal_notes,
                    expected_challenges=challenges,
                    success_indicators=success_indicators
                )
                
                recommendations.append(recommendation)
            
            # Sort by match score
            recommendations.sort(key=lambda x: x.match_score, reverse=True)
            
            logger.info(f"Scored {len(recommendations)} orchid recommendations")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error scoring orchid compatibility: {e}")
            return []
    
    def _calculate_climate_compatibility(self, orchid: OrchidRecord, weather_analysis: Dict) -> float:
        """Calculate how well orchid matches local climate"""
        try:
            climate_summary = weather_analysis.get("climate_summary", {})
            temp_data = climate_summary.get("temperature", {})
            humidity_data = climate_summary.get("humidity", {})
            
            score = 50.0  # Base score
            
            # Genus-based climate preferences (simplified scoring)
            genus_climate_preferences = {
                'Phalaenopsis': {'temp_range': (18, 30), 'humidity_range': (50, 80), 'bonus': 20},
                'Cattleya': {'temp_range': (16, 32), 'humidity_range': (40, 70), 'bonus': 15},
                'Dendrobium': {'temp_range': (15, 28), 'humidity_range': (40, 75), 'bonus': 15},
                'Oncidium': {'temp_range': (15, 28), 'humidity_range': (40, 70), 'bonus': 10},
                'Cymbidium': {'temp_range': (10, 25), 'humidity_range': (40, 60), 'bonus': 10},
                'Paphiopedilum': {'temp_range': (16, 26), 'humidity_range': (50, 80), 'bonus': 15},
                'Miltonia': {'temp_range': (15, 25), 'humidity_range': (60, 80), 'bonus': 10},
                'Masdevallia': {'temp_range': (10, 22), 'humidity_range': (70, 90), 'bonus': 5},
            }
            
            genus = orchid.genus
            if genus in genus_climate_preferences:
                prefs = genus_climate_preferences[genus]
                
                # Temperature compatibility
                avg_temp = temp_data.get("avg")
                if avg_temp:
                    temp_min, temp_max = prefs['temp_range']
                    if temp_min <= avg_temp <= temp_max:
                        score += prefs['bonus']
                    else:
                        # Penalize for being outside optimal range
                        temp_diff = min(abs(avg_temp - temp_min), abs(avg_temp - temp_max))
                        score -= min(temp_diff * 2, 20)
                
                # Humidity compatibility
                avg_humidity = humidity_data.get("avg")
                if avg_humidity:
                    humidity_min, humidity_max = prefs['humidity_range']
                    if humidity_min <= avg_humidity <= humidity_max:
                        score += 10
                    else:
                        humidity_diff = min(abs(avg_humidity - humidity_min), abs(avg_humidity - humidity_max))
                        score -= min(humidity_diff * 0.3, 15)
            
            # Orchid friendliness bonus
            orchid_friendliness = climate_summary.get("orchid_friendliness", 0)
            score += orchid_friendliness * 10
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating climate compatibility: {e}")
            return 50.0
    
    def _calculate_environment_compatibility(self, orchid: OrchidRecord, growing_setup: GrowingSetup) -> float:
        """Calculate environment suitability score"""
        try:
            score = 50.0
            
            # Environment-specific bonuses
            environment_bonuses = {
                GrowingEnvironment.WINDOWSILL: {
                    'Phalaenopsis': 25, 'Dendrobium': 20, 'Oncidium': 15, 'Cattleya': 10
                },
                GrowingEnvironment.GREENHOUSE: {
                    'Cattleya': 25, 'Dendrobium': 20, 'Cymbidium': 20, 'Oncidium': 15
                },
                GrowingEnvironment.TERRARIUM: {
                    'Masdevallia': 25, 'Pleurothallis': 20, 'Restrepia': 20
                },
                GrowingEnvironment.INDOOR_LIGHTS: {
                    'Phalaenopsis': 20, 'Paphiopedilum': 20, 'Miltonia': 15
                }
            }
            
            genus = orchid.genus
            if growing_setup.environment in environment_bonuses:
                bonus = environment_bonuses[growing_setup.environment].get(genus, 0)
                score += bonus
            
            # Space size considerations
            if growing_setup.space_size == "small" and genus in ['Masdevallia', 'Pleurothallis']:
                score += 15
            elif growing_setup.space_size == "large" and genus in ['Cymbidium', 'Cattleya']:
                score += 15
            
            # Equipment bonuses
            if growing_setup.supplemental_heating:
                score += 5
            if growing_setup.humidity_control:
                score += 10
            if growing_setup.air_circulation:
                score += 8
            
            return max(0, min(100, score))
            
        except Exception as e:
            logger.error(f"Error calculating environment compatibility: {e}")
            return 50.0
    
    def _calculate_experience_compatibility(self, orchid: OrchidRecord, growing_setup: GrowingSetup) -> float:
        """Calculate experience level compatibility"""
        try:
            care_difficulty = self._assess_care_difficulty(orchid)
            experience_level = growing_setup.experience_level
            
            # Experience matching matrix
            compatibility_matrix = {
                ExperienceLevel.BEGINNER: {
                    CareDifficulty.VERY_EASY: 95,
                    CareDifficulty.EASY: 85,
                    CareDifficulty.MODERATE: 60,
                    CareDifficulty.CHALLENGING: 30,
                    CareDifficulty.EXPERT_ONLY: 10
                },
                ExperienceLevel.INTERMEDIATE: {
                    CareDifficulty.VERY_EASY: 90,
                    CareDifficulty.EASY: 95,
                    CareDifficulty.MODERATE: 90,
                    CareDifficulty.CHALLENGING: 70,
                    CareDifficulty.EXPERT_ONLY: 40
                },
                ExperienceLevel.ADVANCED: {
                    CareDifficulty.VERY_EASY: 80,
                    CareDifficulty.EASY: 85,
                    CareDifficulty.MODERATE: 95,
                    CareDifficulty.CHALLENGING: 90,
                    CareDifficulty.EXPERT_ONLY: 70
                },
                ExperienceLevel.EXPERT: {
                    CareDifficulty.VERY_EASY: 70,
                    CareDifficulty.EASY: 75,
                    CareDifficulty.MODERATE: 85,
                    CareDifficulty.CHALLENGING: 95,
                    CareDifficulty.EXPERT_ONLY: 95
                }
            }
            
            return compatibility_matrix[experience_level][care_difficulty]
            
        except Exception as e:
            logger.error(f"Error calculating experience compatibility: {e}")
            return 50.0
    
    def _assess_care_difficulty(self, orchid: OrchidRecord) -> CareDifficulty:
        """Assess care difficulty based on genus and available information"""
        try:
            # Genus-based difficulty ratings (simplified)
            genus_difficulty = {
                'Phalaenopsis': CareDifficulty.VERY_EASY,
                'Dendrobium': CareDifficulty.EASY,
                'Oncidium': CareDifficulty.EASY,
                'Cattleya': CareDifficulty.MODERATE,
                'Cymbidium': CareDifficulty.MODERATE,
                'Paphiopedilum': CareDifficulty.MODERATE,
                'Miltonia': CareDifficulty.CHALLENGING,
                'Masdevallia': CareDifficulty.CHALLENGING,
                'Pleurothallis': CareDifficulty.EXPERT_ONLY
            }
            
            return genus_difficulty.get(orchid.genus, CareDifficulty.MODERATE)
            
        except Exception as e:
            logger.error(f"Error assessing care difficulty: {e}")
            return CareDifficulty.MODERATE
    
    def _generate_match_reasons(self, orchid: OrchidRecord, climate_score: float, 
                               environment_score: float, experience_score: float) -> List[str]:
        """Generate reasons why this orchid is a good match"""
        reasons = []
        
        if climate_score >= 70:
            reasons.append(f"Excellent climate compatibility - {orchid.genus} thrives in conditions similar to your local climate")
        elif climate_score >= 50:
            reasons.append(f"Good climate match with minor adjustments needed for optimal {orchid.genus} care")
        
        if environment_score >= 70:
            reasons.append(f"Well-suited for your {orchid.genus} growing environment setup")
        
        if experience_score >= 80:
            reasons.append("Matches your experience level - good chance of success")
        
        if orchid.cultural_notes:
            reasons.append("Has detailed cultural information available for guidance")
        
        if orchid.ai_description:
            reasons.append("Enhanced with AI-generated care insights")
            
        return reasons[:3]  # Limit to top 3 reasons
    
    def _generate_care_tips(self, orchid: OrchidRecord, growing_setup: GrowingSetup, 
                           weather_analysis: Dict) -> List[str]:
        """Generate personalized care tips"""
        tips = []
        genus = orchid.genus
        
        # Genus-specific basic tips
        genus_tips = {
            'Phalaenopsis': [
                "Water weekly, allowing medium to dry slightly between waterings",
                "Provide bright, indirect light (east or north window ideal)",
                "Maintain 50-70% humidity with good air circulation"
            ],
            'Cattleya': [
                "Needs bright light - south or west window with some direct sun",
                "Water thoroughly then allow to dry almost completely",
                "Benefits from temperature drop at night (10-15°F cooler)"
            ],
            'Dendrobium': [
                "High light requirements - needs several hours of direct sun",
                "Reduce watering in winter to encourage blooming",
                "Prefers to be slightly root-bound"
            ]
        }
        
        tips.extend(genus_tips.get(genus, ["Follow standard orchid care practices"]))
        
        # Environment-specific modifications
        if growing_setup.environment == GrowingEnvironment.WINDOWSILL:
            tips.append("Rotate plant weekly for even growth")
            if not growing_setup.humidity_control:
                tips.append("Use humidity tray or group plants to increase local humidity")
        
        return tips[:4]  # Limit to 4 tips
    
    def _generate_seasonal_notes(self, orchid: OrchidRecord, weather_analysis: Dict) -> Dict[str, str]:
        """Generate seasonal care notes"""
        return {
            "spring": "Resume regular fertilizing and increase watering as growth begins",
            "summer": "Monitor for increased watering needs and provide extra ventilation",
            "fall": "Reduce fertilizer and prepare for winter rest period",
            "winter": "Reduce watering frequency and watch for signs of stress from low humidity"
        }
    
    def _identify_potential_challenges(self, orchid: OrchidRecord, growing_setup: GrowingSetup, 
                                     weather_analysis: Dict) -> List[str]:
        """Identify potential challenges for this orchid"""
        challenges = []
        
        climate_summary = weather_analysis.get("climate_summary", {})
        humidity_avg = climate_summary.get("humidity", {}).get("avg", 0)
        
        if humidity_avg < 40:
            challenges.append("Low ambient humidity - will need humidity supplementation")
        
        if growing_setup.environment == GrowingEnvironment.WINDOWSILL:
            challenges.append("Limited light - may need to rotate to different windows seasonally")
        
        if growing_setup.experience_level == ExperienceLevel.BEGINNER:
            challenges.append("Monitor watering carefully - overwatering is the most common mistake")
        
        return challenges[:3]
    
    def _generate_success_indicators(self, orchid: OrchidRecord) -> List[str]:
        """Generate success indicators to watch for"""
        return [
            "New growth appearing (roots, leaves, or pseudobulbs)",
            "Healthy green foliage with good coloration",
            "Regular blooming cycles (varies by species)",
            "Steady growth without yellowing or dropping leaves"
        ]
    
    def _format_recommendation(self, rec: OrchidRecommendation) -> Dict[str, Any]:
        """Format recommendation for JSON response"""
        return {
            "orchid": {
                "id": rec.orchid.id,
                "scientific_name": rec.orchid.scientific_name,
                "genus": rec.orchid.genus,
                "species": rec.orchid.species,
                "display_name": rec.orchid.display_name,
                "image_filename": rec.orchid.image_filename,
                "google_drive_id": rec.orchid.google_drive_id,
                "cultural_notes": rec.orchid.cultural_notes,
                "ai_description": rec.orchid.ai_description
            },
            "match_analysis": {
                "overall_score": rec.match_score,
                "climate_compatibility": rec.climate_compatibility,
                "environment_suitability": rec.environment_suitability,
                "experience_match": rec.experience_match,
                "care_difficulty": rec.care_difficulty.value,
                "care_difficulty_name": rec.care_difficulty.name.replace('_', ' ').title()
            },
            "recommendations": {
                "reasons": rec.reasons,
                "care_tips": rec.care_tips,
                "seasonal_notes": rec.seasonal_notes,
                "potential_challenges": rec.expected_challenges,
                "success_indicators": rec.success_indicators
            }
        }
    
    def _generate_care_insights(self, recommendations: List[OrchidRecommendation], 
                               weather_analysis: Dict, growing_setup: GrowingSetup) -> Dict[str, Any]:
        """Generate overall care insights for the user"""
        insights = {
            "climate_overview": self._generate_climate_overview(weather_analysis),
            "setup_optimization": self._generate_setup_optimization(growing_setup, recommendations),
            "seasonal_priorities": self._generate_seasonal_priorities(weather_analysis),
            "success_tips": self._generate_general_success_tips(growing_setup)
        }
        
        return insights
    
    def _generate_seasonal_calendar(self, weather_analysis: Dict, growing_setup: GrowingSetup) -> Dict[str, Any]:
        """Generate seasonal care calendar"""
        return {
            "spring": {
                "priorities": ["Resume fertilizing", "Repot as needed", "Increase watering"],
                "watch_for": ["New growth", "Root development", "Pest emergence"]
            },
            "summer": {
                "priorities": ["Monitor watering", "Provide ventilation", "Watch for heat stress"],
                "watch_for": ["Rapid growth", "Flowering", "Increased water needs"]
            },
            "fall": {
                "priorities": ["Reduce fertilizer", "Prepare for winter", "Clean up debris"],
                "watch_for": ["Blooming preparation", "Growth slowdown", "Color changes"]
            },
            "winter": {
                "priorities": ["Reduce watering", "Monitor humidity", "Provide extra light"],
                "watch_for": ["Rest period signs", "Blooming", "Stress symptoms"]
            }
        }
    
    def _estimate_growing_season(self, temperatures: List[float]) -> int:
        """Estimate growing season length in days"""
        if not temperatures:
            return 180  # Default
        
        avg_temp = sum(temperatures) / len(temperatures)
        if avg_temp > 20:
            return 300  # Year-round growing
        elif avg_temp > 15:
            return 240  # Long season
        else:
            return 180  # Shorter season
    
    def _determine_climate_zone(self, temperatures: List[float], humidity_vals: List[float]) -> str:
        """Determine basic climate zone"""
        if not temperatures or not humidity_vals:
            return "unknown"
        
        avg_temp = sum(temperatures) / len(temperatures)
        avg_humidity = sum(humidity_vals) / len(humidity_vals)
        
        if avg_temp > 25 and avg_humidity > 70:
            return "tropical"
        elif avg_temp > 20 and avg_humidity > 60:
            return "subtropical"
        elif 15 <= avg_temp <= 25:
            return "temperate"
        elif avg_temp < 15:
            return "cool"
        else:
            return "variable"
    
    def _rate_orchid_friendliness(self, temperatures: List[float], humidity_vals: List[float]) -> float:
        """Rate how orchid-friendly the climate is (0-1 scale)"""
        if not temperatures or not humidity_vals:
            return 0.5
        
        score = 0.0
        
        # Temperature scoring
        avg_temp = sum(temperatures) / len(temperatures)
        if 18 <= avg_temp <= 28:
            score += 0.4
        elif 15 <= avg_temp <= 32:
            score += 0.2
        
        # Humidity scoring
        avg_humidity = sum(humidity_vals) / len(humidity_vals)
        if 50 <= avg_humidity <= 80:
            score += 0.4
        elif 40 <= avg_humidity <= 90:
            score += 0.2
        
        # Temperature stability
        temp_range = max(temperatures) - min(temperatures)
        if temp_range < 15:
            score += 0.2
        elif temp_range < 25:
            score += 0.1
        
        return min(1.0, score)
    
    def _generate_climate_overview(self, weather_analysis: Dict) -> str:
        """Generate plain English climate overview"""
        climate_summary = weather_analysis.get("climate_summary", {})
        orchid_friendliness = climate_summary.get("orchid_friendliness", 0)
        
        if orchid_friendliness > 0.7:
            return "Your climate is very favorable for orchid growing with minimal adjustments needed."
        elif orchid_friendliness > 0.4:
            return "Your climate is moderately suitable for orchids with some environmental control needed."
        else:
            return "Your climate presents challenges for orchid growing but success is possible with proper setup."
    
    def _generate_setup_optimization(self, growing_setup: GrowingSetup, 
                                   recommendations: List[OrchidRecommendation]) -> List[str]:
        """Generate setup optimization suggestions"""
        suggestions = []
        
        if not growing_setup.humidity_control:
            suggestions.append("Consider adding humidity control for better results")
        
        if not growing_setup.air_circulation:
            suggestions.append("Improve air circulation to prevent fungal problems")
        
        if growing_setup.environment == GrowingEnvironment.WINDOWSILL:
            suggestions.append("Supplement with grow lights for better flowering")
        
        return suggestions[:3]
    
    def _generate_seasonal_priorities(self, weather_analysis: Dict) -> Dict[str, str]:
        """Generate seasonal priorities based on local climate"""
        return {
            "current_priority": "Monitor humidity levels and adjust watering accordingly",
            "next_month": "Prepare for seasonal changes in temperature and daylight",
            "seasonal_focus": "Maintain consistent care routine adapted to your local conditions"
        }
    
    def _generate_general_success_tips(self, growing_setup: GrowingSetup) -> List[str]:
        """Generate general success tips"""
        tips = [
            "Start with recommended orchids and master their care before expanding",
            "Keep detailed records of watering, fertilizing, and observations",
            "Join local orchid societies for hands-on learning and support"
        ]
        
        if growing_setup.experience_level == ExperienceLevel.BEGINNER:
            tips.insert(0, "Focus on consistent care rather than frequent changes")
        
        return tips

def find_optimal_orchids_for_user(user_location: str, growing_setup_data: Dict[str, Any], 
                                 max_recommendations: int = 10) -> Dict[str, Any]:
    """
    Main function to find optimal orchids for a user
    
    Args:
        user_location: User's location (city, ZIP, or coordinates)
        growing_setup_data: Dictionary with growing setup information
        max_recommendations: Maximum recommendations to return
        
    Returns:
        Comprehensive orchid recommendations
    """
    try:
        # Parse growing setup
        growing_setup = GrowingSetup(
            environment=GrowingEnvironment(growing_setup_data.get('environment', 'windowsill')),
            space_size=growing_setup_data.get('space_size', 'medium'),
            light_hours=growing_setup_data.get('light_hours'),
            supplemental_heating=growing_setup_data.get('supplemental_heating', False),
            humidity_control=growing_setup_data.get('humidity_control', False),
            air_circulation=growing_setup_data.get('air_circulation', False),
            experience_level=ExperienceLevel(growing_setup_data.get('experience_level', 'beginner')),
            budget_range=growing_setup_data.get('budget_range'),
            preferred_colors=growing_setup_data.get('preferred_colors', []),
            bloom_timing_preference=growing_setup_data.get('bloom_timing_preference')
        )
        
        # Create matcher and find orchids
        matcher = PersonalizedGrowingConditionMatcher()
        return matcher.find_optimal_orchids(user_location, growing_setup, max_recommendations)
        
    except Exception as e:
        logger.error(f"Error in find_optimal_orchids_for_user: {e}")
        return {
            "error": f"Analysis failed: {str(e)}",
            "success": False,
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        location = sys.argv[1]
        setup_data = {
            'environment': 'windowsill',
            'space_size': 'small',
            'experience_level': 'beginner',
            'humidity_control': False,
            'supplemental_heating': False,
            'air_circulation': False
        }
        result = find_optimal_orchids_for_user(location, setup_data, 5)
        print(json.dumps(result, indent=2, default=str))
    else:
        print("Usage: python personalized_growing_condition_matcher.py <location>")