#!/usr/bin/env python3
"""
Adaptive Care Calendar Generator - The Orchid Continuum
==================================================

A sophisticated orchid care scheduling system that generates dynamic, personalized care
calendars based on local weather patterns, seasonal changes, and species-specific needs.
This system represents a breakthrough in automated horticultural planning.

Features:
- Weather-adaptive scheduling that modifies care based on real conditions
- Species-specific care protocols for different orchid genera
- Growth stage awareness (seedling, juvenile, mature, dormant)
- Seasonal cycle integration with natural dormancy periods
- Multi-modal care recommendations (watering, fertilizing, environmental)
- Calendar integration with reminder systems
- Performance tracking and schedule optimization

Author: The Orchid Continuum Platform
Created: 2025-09-27
"""

import logging
import json
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Any, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
from calendar import monthrange
from collections import defaultdict
import math

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CareAction(Enum):
    """Types of care actions"""
    WATERING = "watering"
    FERTILIZING = "fertilizing" 
    REPOTTING = "repotting"
    HUMIDITY_ADJUSTMENT = "humidity_adjustment"
    TEMPERATURE_MONITORING = "temperature_monitoring"
    AIR_CIRCULATION = "air_circulation"
    PEST_INSPECTION = "pest_inspection"
    PRUNING = "pruning"
    LIGHT_ADJUSTMENT = "light_adjustment"
    MISTING = "misting"

class Priority(Enum):
    """Priority levels for care tasks"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"

class GrowthStage(Enum):
    """Orchid growth stages"""
    SEEDLING = "seedling"
    JUVENILE = "juvenile"
    MATURE_VEGETATIVE = "mature_vegetative"
    MATURE_BLOOMING = "mature_blooming"
    POST_BLOOM = "post_bloom"
    DORMANT = "dormant"
    STRESSED = "stressed"

class Season(Enum):
    """Seasonal periods"""
    SPRING = "spring"
    SUMMER = "summer"
    AUTUMN = "autumn"
    WINTER = "winter"

@dataclass
class WeatherPattern:
    """Weather pattern data structure"""
    temperature_avg: float
    humidity_avg: float
    rainfall_mm: float
    sunlight_hours: float
    wind_speed: float
    pressure: float
    season: Season
    date_range: Tuple[date, date]

@dataclass
class CareTask:
    """Individual care task"""
    action: CareAction
    priority: Priority
    scheduled_date: date
    description: str
    weather_dependent: bool
    duration_minutes: int
    notes: Optional[str] = None
    completed: bool = False
    weather_conditions: Optional[Dict[str, Any]] = None

@dataclass
class OrchidProfile:
    """Orchid profile for care planning"""
    orchid_id: int
    genus: str
    species: Optional[str]
    hybrid_name: Optional[str]
    growth_stage: GrowthStage
    location: str
    pot_size: str
    medium_type: str
    last_repotted: Optional[date]
    health_status: str
    special_needs: List[str]

@dataclass
class CareCalendar:
    """Generated care calendar"""
    orchid_profile: OrchidProfile
    start_date: date
    end_date: date
    tasks: List[CareTask]
    weather_integration: bool
    auto_adaptation_enabled: bool
    created_timestamp: datetime
    last_updated: Optional[datetime] = None

class AdaptiveCareCalendarGenerator:
    """
    Advanced orchid care calendar generator that adapts to weather patterns
    and provides personalized scheduling based on species requirements
    """
    
    def __init__(self):
        """Initialize the adaptive care calendar generator"""
        self.care_protocols = self._load_care_protocols()
        self.seasonal_adjustments = self._load_seasonal_adjustments()
        self.weather_thresholds = self._load_weather_thresholds()
        self.genus_specific_care = self._load_genus_specific_care()
        
        logger.info("🗓️ Adaptive Care Calendar Generator initialized")
    
    def generate_adaptive_calendar(self, orchid_profile: OrchidProfile, 
                                 duration_days: int = 90,
                                 weather_data: Optional[List[WeatherPattern]] = None,
                                 user_preferences: Optional[Dict[str, Any]] = None) -> CareCalendar:
        """
        Generate adaptive care calendar for an orchid
        
        Args:
            orchid_profile: Orchid information and current status
            duration_days: Calendar duration in days
            weather_data: Historical and forecasted weather patterns
            user_preferences: User-specific preferences and constraints
            
        Returns:
            Generated care calendar with adaptive scheduling
        """
        try:
            start_date = date.today()
            end_date = start_date + timedelta(days=duration_days)
            
            # Generate base care schedule
            base_tasks = self._generate_base_schedule(orchid_profile, start_date, end_date)
            
            # Apply weather adaptations
            if weather_data:
                adapted_tasks = self._apply_weather_adaptations(base_tasks, weather_data)
            else:
                adapted_tasks = base_tasks
            
            # Apply seasonal adjustments
            seasonal_tasks = self._apply_seasonal_adjustments(adapted_tasks, start_date, end_date)
            
            # Apply genus-specific modifications
            genus_tasks = self._apply_genus_specific_care(seasonal_tasks, orchid_profile.genus)
            
            # Apply growth stage considerations
            growth_tasks = self._apply_growth_stage_adjustments(genus_tasks, orchid_profile.growth_stage)
            
            # Apply user preferences
            if user_preferences:
                final_tasks = self._apply_user_preferences(growth_tasks, user_preferences)
            else:
                final_tasks = growth_tasks
            
            # Sort tasks by date and priority
            sorted_tasks = sorted(final_tasks, key=lambda t: (t.scheduled_date, t.priority.value))
            
            calendar = CareCalendar(
                orchid_profile=orchid_profile,
                start_date=start_date,
                end_date=end_date,
                tasks=sorted_tasks,
                weather_integration=weather_data is not None,
                auto_adaptation_enabled=True,
                created_timestamp=datetime.now()
            )
            
            logger.info(f"🗓️ Generated adaptive calendar for {orchid_profile.genus} with {len(sorted_tasks)} tasks")
            return calendar
            
        except Exception as e:
            logger.error(f"Error generating adaptive calendar: {e}")
            raise
    
    def _generate_base_schedule(self, profile: OrchidProfile, 
                              start_date: date, end_date: date) -> List[CareTask]:
        """Generate base care schedule without adaptations"""
        tasks = []
        current_date = start_date
        
        # Get care protocol for this genus
        protocol = self.care_protocols.get(profile.genus, self.care_protocols.get('default'))
        
        while current_date <= end_date:
            # Daily tasks
            if self._should_schedule_task(CareAction.TEMPERATURE_MONITORING, current_date, protocol):
                tasks.append(CareTask(
                    action=CareAction.TEMPERATURE_MONITORING,
                    priority=Priority.MEDIUM,
                    scheduled_date=current_date,
                    description="Monitor temperature and humidity levels",
                    weather_dependent=True,
                    duration_minutes=5
                ))
            
            # Weekly tasks
            if current_date.weekday() == 0:  # Monday
                if self._should_schedule_task(CareAction.PEST_INSPECTION, current_date, protocol):
                    tasks.append(CareTask(
                        action=CareAction.PEST_INSPECTION,
                        priority=Priority.HIGH,
                        scheduled_date=current_date,
                        description="Inspect for pests, diseases, and overall health",
                        weather_dependent=False,
                        duration_minutes=10
                    ))
            
            # Watering schedule (adaptive)
            watering_days = self._calculate_watering_schedule(profile, current_date)
            if current_date in watering_days:
                tasks.append(CareTask(
                    action=CareAction.WATERING,
                    priority=Priority.HIGH,
                    scheduled_date=current_date,
                    description=f"Water {profile.genus} - check soil moisture first",
                    weather_dependent=True,
                    duration_minutes=10
                ))
            
            # Fertilizing schedule
            if self._should_fertilize(profile, current_date):
                tasks.append(CareTask(
                    action=CareAction.FERTILIZING,
                    priority=Priority.MEDIUM,
                    scheduled_date=current_date,
                    description="Apply appropriate fertilizer based on growth stage",
                    weather_dependent=False,
                    duration_minutes=15
                ))
            
            # Monthly tasks
            if current_date.day == 1:
                tasks.append(CareTask(
                    action=CareAction.AIR_CIRCULATION,
                    priority=Priority.MEDIUM,
                    scheduled_date=current_date,
                    description="Check and adjust air circulation systems",
                    weather_dependent=True,
                    duration_minutes=10
                ))
            
            # Seasonal repotting check
            if self._should_check_repotting(profile, current_date):
                tasks.append(CareTask(
                    action=CareAction.REPOTTING,
                    priority=Priority.HIGH,
                    scheduled_date=current_date,
                    description=f"Evaluate repotting needs - last repotted: {profile.last_repotted}",
                    weather_dependent=False,
                    duration_minutes=60,
                    notes="Check root health and growing medium condition"
                ))
            
            current_date += timedelta(days=1)
        
        return tasks
    
    def _apply_weather_adaptations(self, tasks: List[CareTask], 
                                 weather_data: List[WeatherPattern]) -> List[CareTask]:
        """Apply weather-based adaptations to care schedule"""
        adapted_tasks = []
        
        for task in tasks:
            if not task.weather_dependent:
                adapted_tasks.append(task)
                continue
            
            # Find weather pattern for this date
            weather_pattern = self._get_weather_for_date(task.scheduled_date, weather_data)
            if not weather_pattern:
                adapted_tasks.append(task)
                continue
            
            # Adapt watering based on rainfall
            if task.action == CareAction.WATERING:
                if weather_pattern.rainfall_mm > 10:  # Significant rainfall
                    # Skip watering or reduce frequency
                    task.priority = Priority.LOW
                    task.notes = f"Reduced priority due to rainfall: {weather_pattern.rainfall_mm}mm"
                elif weather_pattern.humidity_avg < 40:  # Low humidity
                    task.priority = Priority.CRITICAL
                    task.notes = f"Increased priority due to low humidity: {weather_pattern.humidity_avg}%"
            
            # Adapt misting based on humidity
            elif task.action == CareAction.MISTING:
                if weather_pattern.humidity_avg > 70:
                    task.priority = Priority.LOW
                elif weather_pattern.humidity_avg < 50:
                    task.priority = Priority.HIGH
            
            # Adapt temperature monitoring
            elif task.action == CareAction.TEMPERATURE_MONITORING:
                if abs(weather_pattern.temperature_avg - 22) > 5:  # Outside optimal range
                    task.priority = Priority.HIGH
                    task.notes = f"Temperature monitoring critical: {weather_pattern.temperature_avg}°C"
            
            # Store weather conditions with task
            task.weather_conditions = {
                'temperature': weather_pattern.temperature_avg,
                'humidity': weather_pattern.humidity_avg,
                'rainfall': weather_pattern.rainfall_mm,
                'season': weather_pattern.season.value
            }
            
            adapted_tasks.append(task)
        
        return adapted_tasks
    
    def _apply_seasonal_adjustments(self, tasks: List[CareTask], 
                                  start_date: date, end_date: date) -> List[CareTask]:
        """Apply seasonal care adjustments"""
        adjusted_tasks = []
        
        for task in tasks:
            season = self._get_season_for_date(task.scheduled_date)
            adjustments = self.seasonal_adjustments.get(season.value, {})
            
            # Apply seasonal frequency modifications
            if task.action.value in adjustments:
                adjustment = adjustments[task.action.value]
                
                # Modify watering frequency in winter
                if task.action == CareAction.WATERING and season == Season.WINTER:
                    if adjustment.get('reduce_frequency', False):
                        # Skip some watering days in winter
                        if task.scheduled_date.weekday() in [1, 3, 5]:  # Tue, Thu, Sat
                            continue
                
                # Increase fertilizing in growing season
                elif task.action == CareAction.FERTILIZING and season in [Season.SPRING, Season.SUMMER]:
                    if adjustment.get('increase_frequency', False):
                        task.priority = Priority.HIGH
            
            # Add seasonal-specific tasks
            self._add_seasonal_tasks(adjusted_tasks, task.scheduled_date, season)
            
            adjusted_tasks.append(task)
        
        return adjusted_tasks
    
    def _apply_genus_specific_care(self, tasks: List[CareTask], genus: str) -> List[CareTask]:
        """Apply genus-specific care modifications"""
        genus_care = self.genus_specific_care.get(genus, {})
        if not genus_care:
            return tasks
        
        modified_tasks = []
        
        for task in tasks:
            # Apply genus-specific modifications
            if task.action.value in genus_care:
                modifications = genus_care[task.action.value]
                
                # Modify watering for different genera
                if task.action == CareAction.WATERING:
                    if 'frequency_modifier' in modifications:
                        modifier = modifications['frequency_modifier']
                        if modifier < 1.0 and task.scheduled_date.weekday() % 2 == 0:
                            # Reduce frequency for drought-tolerant genera
                            continue
                    
                    if 'special_notes' in modifications:
                        task.notes = modifications['special_notes']
                
                # Modify fertilizing for epiphytes vs terrestrials
                elif task.action == CareAction.FERTILIZING:
                    if 'concentration' in modifications:
                        conc = modifications['concentration']
                        task.description = f"{task.description} - Use {conc} concentration"
            
            modified_tasks.append(task)
        
        return modified_tasks
    
    def _apply_growth_stage_adjustments(self, tasks: List[CareTask], 
                                      growth_stage: GrowthStage) -> List[CareTask]:
        """Apply growth stage-specific adjustments"""
        adjusted_tasks = []
        
        for task in tasks:
            # Seedling care adjustments
            if growth_stage == GrowthStage.SEEDLING:
                if task.action == CareAction.WATERING:
                    task.description = "Gentle misting rather than direct watering"
                    task.duration_minutes = 5
                elif task.action == CareAction.FERTILIZING:
                    task.description = "Very dilute fertilizer (1/4 strength)"
            
            # Mature blooming adjustments
            elif growth_stage == GrowthStage.MATURE_BLOOMING:
                if task.action == CareAction.WATERING:
                    task.priority = Priority.HIGH
                    task.notes = "Maintain consistent moisture during blooming"
                elif task.action == CareAction.TEMPERATURE_MONITORING:
                    task.priority = Priority.HIGH
                    task.notes = "Stable temperatures critical during blooming"
            
            # Dormant period adjustments
            elif growth_stage == GrowthStage.DORMANT:
                if task.action == CareAction.WATERING:
                    task.priority = Priority.LOW
                    task.description = "Minimal watering during dormancy"
                elif task.action == CareAction.FERTILIZING:
                    continue  # Skip fertilizing during dormancy
            
            adjusted_tasks.append(task)
        
        return adjusted_tasks
    
    def _apply_user_preferences(self, tasks: List[CareTask], 
                              preferences: Dict[str, Any]) -> List[CareTask]:
        """Apply user preferences and constraints"""
        filtered_tasks = []
        
        # Get user constraints
        unavailable_days = preferences.get('unavailable_days', [])
        preferred_times = preferences.get('preferred_care_times', {})
        skill_level = preferences.get('skill_level', 'intermediate')
        time_constraints = preferences.get('max_daily_minutes', 60)
        
        for task in tasks:
            # Skip tasks on unavailable days
            if task.scheduled_date.strftime('%A').lower() in unavailable_days:
                # Reschedule to next available day
                next_date = task.scheduled_date + timedelta(days=1)
                while next_date.strftime('%A').lower() in unavailable_days:
                    next_date += timedelta(days=1)
                task.scheduled_date = next_date
            
            # Adjust task complexity based on skill level
            if skill_level == 'beginner':
                if task.action == CareAction.REPOTTING:
                    task.notes = "Consider seeking guidance for first repotting"
                    task.duration_minutes += 30  # Extra time for beginners
            
            filtered_tasks.append(task)
        
        # Ensure daily time constraints
        daily_tasks = defaultdict(list)
        for task in filtered_tasks:
            daily_tasks[task.scheduled_date].append(task)
        
        # Redistribute if over time limit
        final_tasks = []
        for date_tasks in daily_tasks.values():
            total_time = sum(task.duration_minutes for task in date_tasks)
            if total_time > time_constraints:
                # Keep high priority tasks, reschedule others
                high_priority = [t for t in date_tasks if t.priority in [Priority.CRITICAL, Priority.HIGH]]
                low_priority = [t for t in date_tasks if t.priority not in [Priority.CRITICAL, Priority.HIGH]]
                
                final_tasks.extend(high_priority)
                
                # Reschedule low priority tasks
                for i, task in enumerate(low_priority):
                    task.scheduled_date += timedelta(days=i+1)
                    final_tasks.append(task)
            else:
                final_tasks.extend(date_tasks)
        
        return final_tasks
    
    def get_calendar_summary(self, calendar: CareCalendar) -> Dict[str, Any]:
        """Generate calendar summary and statistics"""
        total_tasks = len(calendar.tasks)
        tasks_by_priority = defaultdict(int)
        tasks_by_action = defaultdict(int)
        weather_dependent_count = 0
        
        for task in calendar.tasks:
            tasks_by_priority[task.priority.value] += 1
            tasks_by_action[task.action.value] += 1
            if task.weather_dependent:
                weather_dependent_count += 1
        
        # Calculate weekly patterns
        weekly_distribution = defaultdict(int)
        for task in calendar.tasks:
            week_start = task.scheduled_date - timedelta(days=task.scheduled_date.weekday())
            weekly_distribution[week_start.isoformat()] += 1
        
        return {
            'orchid_info': {
                'genus': calendar.orchid_profile.genus,
                'species': calendar.orchid_profile.species,
                'growth_stage': calendar.orchid_profile.growth_stage.value,
                'health_status': calendar.orchid_profile.health_status
            },
            'schedule_overview': {
                'total_tasks': total_tasks,
                'duration_days': (calendar.end_date - calendar.start_date).days,
                'weather_integration': calendar.weather_integration,
                'tasks_per_week': round(total_tasks / ((calendar.end_date - calendar.start_date).days / 7), 1)
            },
            'task_breakdown': {
                'by_priority': dict(tasks_by_priority),
                'by_action': dict(tasks_by_action),
                'weather_dependent': weather_dependent_count
            },
            'weekly_distribution': dict(weekly_distribution),
            'estimated_weekly_time': sum(task.duration_minutes for task in calendar.tasks[:7]),
            'care_intensity': self._calculate_care_intensity(calendar)
        }
    
    def get_upcoming_tasks(self, calendar: CareCalendar, days_ahead: int = 7) -> List[CareTask]:
        """Get upcoming tasks for the next specified days"""
        cutoff_date = date.today() + timedelta(days=days_ahead)
        upcoming = [task for task in calendar.tasks 
                   if task.scheduled_date >= date.today() and task.scheduled_date <= cutoff_date]
        return sorted(upcoming, key=lambda t: (t.scheduled_date, t.priority.value))
    
    def adjust_calendar_for_weather(self, calendar: CareCalendar, 
                                  weather_update: WeatherPattern) -> CareCalendar:
        """Dynamically adjust calendar based on new weather data"""
        adjusted_tasks = []
        
        for task in calendar.tasks:
            if (task.weather_dependent and 
                task.scheduled_date >= date.today() and 
                not task.completed):
                
                # Apply weather-based adjustments
                if task.action == CareAction.WATERING:
                    if weather_update.rainfall_mm > 15:
                        task.scheduled_date += timedelta(days=1)
                        task.notes = f"Postponed due to heavy rain: {weather_update.rainfall_mm}mm"
                
                elif task.action == CareAction.MISTING:
                    if weather_update.humidity_avg > 75:
                        task.priority = Priority.OPTIONAL
                        task.notes = f"Reduced priority due to high humidity: {weather_update.humidity_avg}%"
            
            adjusted_tasks.append(task)
        
        calendar.tasks = adjusted_tasks
        calendar.last_updated = datetime.now()
        
        return calendar
    
    def export_calendar_formats(self, calendar: CareCalendar) -> Dict[str, str]:
        """Export calendar in multiple formats"""
        formats = {}
        
        # iCal format for calendar apps
        formats['ical'] = self._generate_ical_format(calendar)
        
        # JSON format for API integration
        formats['json'] = json.dumps({
            'calendar_id': f"orchid_{calendar.orchid_profile.orchid_id}",
            'orchid': calendar.orchid_profile.genus,
            'start_date': calendar.start_date.isoformat(),
            'end_date': calendar.end_date.isoformat(),
            'tasks': [
                {
                    'date': task.scheduled_date.isoformat(),
                    'action': task.action.value,
                    'priority': task.priority.value,
                    'description': task.description,
                    'duration_minutes': task.duration_minutes,
                    'weather_dependent': task.weather_dependent,
                    'notes': task.notes
                }
                for task in calendar.tasks
            ]
        }, indent=2)
        
        # CSV format for spreadsheets
        formats['csv'] = self._generate_csv_format(calendar)
        
        return formats
    
    # Helper methods
    def _should_schedule_task(self, action: CareAction, date: date, protocol: Dict) -> bool:
        """Determine if a task should be scheduled on a given date"""
        action_config = protocol.get(action.value, {})
        frequency = action_config.get('frequency', 'weekly')
        
        if frequency == 'daily':
            return True
        elif frequency == 'weekly':
            return date.weekday() == action_config.get('preferred_day', 0)
        elif frequency == 'monthly':
            return date.day == action_config.get('preferred_day', 1)
        
        return False
    
    def _calculate_watering_schedule(self, profile: OrchidProfile, current_date: date) -> List[date]:
        """Calculate watering schedule dates"""
        genus_schedule = self.genus_specific_care.get(profile.genus, {}).get('watering', {})
        base_frequency = genus_schedule.get('base_frequency', 3)  # Every 3 days default
        
        watering_dates = []
        start_date = current_date - timedelta(days=current_date.weekday())  # Week start
        
        for i in range(0, 7, base_frequency):
            watering_date = start_date + timedelta(days=i)
            if watering_date >= current_date:
                watering_dates.append(watering_date)
        
        return watering_dates
    
    def _should_fertilize(self, profile: OrchidProfile, current_date: date) -> bool:
        """Determine if fertilizing is needed on this date"""
        # Typically every 2 weeks during growing season
        growing_season = current_date.month in [3, 4, 5, 6, 7, 8, 9]
        if not growing_season:
            return False
        
        # Check if it's been 14 days since start of month
        return current_date.day % 14 == 0
    
    def _should_check_repotting(self, profile: OrchidProfile, current_date: date) -> bool:
        """Check if repotting evaluation is needed"""
        if not profile.last_repotted:
            return True  # Need to evaluate if never recorded
        
        years_since_repotting = (current_date - profile.last_repotted).days / 365.25
        
        # Check repotting needs annually in spring
        if current_date.month == 3 and current_date.day == 1:
            if years_since_repotting >= 1.5:  # Needs repotting
                return True
        
        return False
    
    def _get_weather_for_date(self, target_date: date, 
                            weather_data: List[WeatherPattern]) -> Optional[WeatherPattern]:
        """Find weather pattern for a specific date"""
        for pattern in weather_data:
            start_date, end_date = pattern.date_range
            if start_date <= target_date <= end_date:
                return pattern
        return None
    
    def _get_season_for_date(self, target_date: date) -> Season:
        """Determine season for a given date"""
        month = target_date.month
        if month in [3, 4, 5]:
            return Season.SPRING
        elif month in [6, 7, 8]:
            return Season.SUMMER
        elif month in [9, 10, 11]:
            return Season.AUTUMN
        else:
            return Season.WINTER
    
    def _add_seasonal_tasks(self, tasks: List[CareTask], target_date: date, season: Season):
        """Add seasonal-specific care tasks"""
        if season == Season.SPRING and target_date.day == 1:
            tasks.append(CareTask(
                action=CareAction.LIGHT_ADJUSTMENT,
                priority=Priority.MEDIUM,
                scheduled_date=target_date,
                description="Adjust lighting for increased spring daylight",
                weather_dependent=True,
                duration_minutes=15
            ))
        
        elif season == Season.WINTER and target_date.day == 1:
            tasks.append(CareTask(
                action=CareAction.HUMIDITY_ADJUSTMENT,
                priority=Priority.HIGH,
                scheduled_date=target_date,
                description="Increase humidity for winter heating season",
                weather_dependent=True,
                duration_minutes=10
            ))
    
    def _calculate_care_intensity(self, calendar: CareCalendar) -> str:
        """Calculate care intensity level"""
        total_time = sum(task.duration_minutes for task in calendar.tasks)
        avg_daily_time = total_time / (calendar.end_date - calendar.start_date).days
        
        if avg_daily_time > 30:
            return "high"
        elif avg_daily_time > 15:
            return "medium"
        else:
            return "low"
    
    def _generate_ical_format(self, calendar: CareCalendar) -> str:
        """Generate iCal format for calendar integration"""
        ical_lines = [
            "BEGIN:VCALENDAR",
            "VERSION:2.0",
            "PRODID:-//The Orchid Continuum//Adaptive Care Calendar//EN",
            "CALSCALE:GREGORIAN"
        ]
        
        for task in calendar.tasks:
            ical_lines.extend([
                "BEGIN:VEVENT",
                f"DTSTART;VALUE=DATE:{task.scheduled_date.strftime('%Y%m%d')}",
                f"SUMMARY:{task.action.value.title()}: {task.description}",
                f"DESCRIPTION:Priority: {task.priority.value}\\nDuration: {task.duration_minutes} minutes",
                f"UID:task-{task.scheduled_date.isoformat()}-{task.action.value}@orchidcontinuum.com",
                "END:VEVENT"
            ])
        
        ical_lines.append("END:VCALENDAR")
        return "\n".join(ical_lines)
    
    def _generate_csv_format(self, calendar: CareCalendar) -> str:
        """Generate CSV format for spreadsheet import"""
        csv_lines = ["Date,Action,Priority,Description,Duration (minutes),Weather Dependent,Notes"]
        
        for task in calendar.tasks:
            csv_lines.append(
                f"{task.scheduled_date.isoformat()},"
                f"{task.action.value},"
                f"{task.priority.value},"
                f"\"{task.description}\","
                f"{task.duration_minutes},"
                f"{task.weather_dependent},"
                f"\"{task.notes or ''}\""
            )
        
        return "\n".join(csv_lines)
    
    def _load_care_protocols(self) -> Dict[str, Any]:
        """Load genus-specific care protocols"""
        return {
            'Phalaenopsis': {
                'watering': {'frequency': 'every_3_days', 'preferred_day': 1},
                'fertilizing': {'frequency': 'bi_weekly', 'concentration': 'quarter_strength'},
                'temperature_monitoring': {'frequency': 'daily', 'optimal_range': [18, 28]},
                'pest_inspection': {'frequency': 'weekly', 'preferred_day': 0}
            },
            'Cattleya': {
                'watering': {'frequency': 'every_4_days', 'preferred_day': 3},
                'fertilizing': {'frequency': 'weekly', 'concentration': 'half_strength'},
                'temperature_monitoring': {'frequency': 'daily', 'optimal_range': [16, 30]},
                'pest_inspection': {'frequency': 'weekly', 'preferred_day': 0}
            },
            'Dendrobium': {
                'watering': {'frequency': 'every_5_days', 'preferred_day': 5},
                'fertilizing': {'frequency': 'weekly', 'concentration': 'quarter_strength'},
                'temperature_monitoring': {'frequency': 'daily', 'optimal_range': [15, 25]},
                'pest_inspection': {'frequency': 'weekly', 'preferred_day': 0}
            },
            'default': {
                'watering': {'frequency': 'every_4_days', 'preferred_day': 2},
                'fertilizing': {'frequency': 'bi_weekly', 'concentration': 'quarter_strength'},
                'temperature_monitoring': {'frequency': 'daily', 'optimal_range': [18, 26]},
                'pest_inspection': {'frequency': 'weekly', 'preferred_day': 0}
            }
        }
    
    def _load_seasonal_adjustments(self) -> Dict[str, Any]:
        """Load seasonal care adjustments"""
        return {
            'spring': {
                'watering': {'increase_frequency': True},
                'fertilizing': {'increase_frequency': True},
                'repotting': {'optimal_season': True}
            },
            'summer': {
                'watering': {'increase_frequency': True},
                'misting': {'increase_frequency': True},
                'air_circulation': {'priority': 'high'}
            },
            'autumn': {
                'watering': {'normal_frequency': True},
                'fertilizing': {'reduce_frequency': True}
            },
            'winter': {
                'watering': {'reduce_frequency': True},
                'fertilizing': {'skip_most': True},
                'humidity_adjustment': {'increase_priority': True}
            }
        }
    
    def _load_weather_thresholds(self) -> Dict[str, Any]:
        """Load weather adaptation thresholds"""
        return {
            'rainfall_heavy': 10.0,  # mm
            'humidity_low': 40.0,    # %
            'humidity_high': 70.0,   # %
            'temperature_optimal_min': 18.0,  # °C
            'temperature_optimal_max': 28.0,  # °C
        }
    
    def _load_genus_specific_care(self) -> Dict[str, Any]:
        """Load genus-specific care modifications"""
        return {
            'Phalaenopsis': {
                'watering': {
                    'frequency_modifier': 1.0,
                    'special_notes': 'Water when bark is almost dry'
                },
                'fertilizing': {
                    'concentration': 'quarter_strength',
                    'type': 'balanced'
                }
            },
            'Cattleya': {
                'watering': {
                    'frequency_modifier': 0.8,
                    'special_notes': 'Allow to dry between waterings'
                },
                'fertilizing': {
                    'concentration': 'half_strength',
                    'type': 'high_potassium_when_budding'
                }
            },
            'Dendrobium': {
                'watering': {
                    'frequency_modifier': 0.7,
                    'special_notes': 'Reduce significantly in winter'
                },
                'fertilizing': {
                    'concentration': 'quarter_strength',
                    'type': 'nitrogen_rich_in_spring'
                }
            },
            'Oncidium': {
                'watering': {
                    'frequency_modifier': 1.1,
                    'special_notes': 'Keep consistently moist but not soggy'
                },
                'fertilizing': {
                    'concentration': 'quarter_strength',
                    'type': 'balanced'
                }
            }
        }

def generate_adaptive_care_calendar(orchid_id: int, duration_days: int = 90, 
                                   location: Optional[str] = None,
                                   user_preferences: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main function to generate adaptive care calendar for an orchid
    
    Args:
        orchid_id: ID of the orchid in the database
        duration_days: Calendar duration in days (default 90)
        location: User location for weather data
        user_preferences: User-specific preferences and constraints
        
    Returns:
        Generated care calendar with tasks and metadata
    """
    try:
        from app import app
        from models import OrchidRecord
        
        with app.app_context():
            # Get orchid information
            orchid = OrchidRecord.query.get(orchid_id)
            if not orchid:
                return {
                    'success': False,
                    'error': f'Orchid with ID {orchid_id} not found'
                }
            
            # Create orchid profile
            profile = OrchidProfile(
                orchid_id=orchid.id,
                genus=orchid.genus,
                species=orchid.species,
                hybrid_name=orchid.display_name,
                growth_stage=GrowthStage.MATURE_VEGETATIVE,  # Default, could be inferred
                location=location or 'Unknown',
                pot_size='Medium',  # Could be stored in database
                medium_type='Bark mix',  # Could be stored in database
                last_repotted=None,  # Could be tracked in database
                health_status='Healthy',  # Could be assessed
                special_needs=[]
            )
            
            # Generate weather data if location provided
            weather_data = None
            if location:
                try:
                    from weather_service import WeatherService
                    weather_service = WeatherService()
                    current_weather = weather_service.get_current_weather(location)
                    if current_weather:
                        # Create weather pattern from current data
                        weather_data = [WeatherPattern(
                            temperature_avg=current_weather.get('temperature', 22),
                            humidity_avg=current_weather.get('humidity', 60),
                            rainfall_mm=current_weather.get('precipitation', 0),
                            sunlight_hours=8.0,
                            wind_speed=current_weather.get('wind_speed', 5),
                            pressure=current_weather.get('pressure', 1013),
                            season=Season.SPRING,  # Could be calculated
                            date_range=(date.today(), date.today() + timedelta(days=duration_days))
                        )]
                except Exception as e:
                    logger.warning(f"Weather data unavailable: {e}")
            
            # Generate calendar
            generator = AdaptiveCareCalendarGenerator()
            calendar = generator.generate_adaptive_calendar(
                profile, duration_days, weather_data, user_preferences
            )
            
            # Get summary and upcoming tasks
            summary = generator.get_calendar_summary(calendar)
            upcoming_tasks = generator.get_upcoming_tasks(calendar, days_ahead=14)
            
            # Export formats
            export_formats = generator.export_calendar_formats(calendar)
            
            return {
                'success': True,
                'calendar': {
                    'orchid_info': {
                        'id': orchid.id,
                        'name': orchid.display_name or f"{orchid.genus} {orchid.species}",
                        'genus': orchid.genus,
                        'species': orchid.species,
                        'scientific_name': orchid.scientific_name
                    },
                    'schedule_period': {
                        'start_date': calendar.start_date.isoformat(),
                        'end_date': calendar.end_date.isoformat(),
                        'duration_days': duration_days
                    },
                    'tasks': [
                        {
                            'date': task.scheduled_date.isoformat(),
                            'action': task.action.value,
                            'priority': task.priority.value,
                            'description': task.description,
                            'duration_minutes': task.duration_minutes,
                            'weather_dependent': task.weather_dependent,
                            'notes': task.notes,
                            'weather_conditions': task.weather_conditions
                        }
                        for task in calendar.tasks
                    ],
                    'upcoming_tasks': [
                        {
                            'date': task.scheduled_date.isoformat(),
                            'action': task.action.value,
                            'priority': task.priority.value,
                            'description': task.description,
                            'duration_minutes': task.duration_minutes,
                            'days_from_now': (task.scheduled_date - date.today()).days
                        }
                        for task in upcoming_tasks
                    ],
                    'summary': summary,
                    'export_formats': export_formats,
                    'weather_integration': calendar.weather_integration,
                    'created_timestamp': calendar.created_timestamp.isoformat()
                }
            }
            
    except Exception as e:
        logger.error(f"Error generating adaptive care calendar: {e}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def get_care_calendar_templates() -> Dict[str, Any]:
    """
    Get available care calendar templates and options
    
    Returns:
        Available templates, preferences, and configuration options
    """
    try:
        return {
            'success': True,
            'templates': {
                'beginner_friendly': {
                    'name': 'Beginner Friendly',
                    'description': 'Simplified schedule with detailed guidance',
                    'features': ['Extended task durations', 'Detailed instructions', 'Low-risk activities'],
                    'duration_options': [30, 60, 90],
                    'skill_level': 'beginner'
                },
                'standard_care': {
                    'name': 'Standard Care',
                    'description': 'Balanced care schedule for most orchids',
                    'features': ['Weather adaptation', 'Seasonal adjustments', 'All care activities'],
                    'duration_options': [60, 90, 120],
                    'skill_level': 'intermediate'
                },
                'intensive_care': {
                    'name': 'Intensive Care',
                    'description': 'Comprehensive schedule for optimal results',
                    'features': ['Daily monitoring', 'Advanced techniques', 'Performance optimization'],
                    'duration_options': [90, 120, 180],
                    'skill_level': 'advanced'
                },
                'seasonal_focus': {
                    'name': 'Seasonal Focus',
                    'description': 'Schedule optimized for current season',
                    'features': ['Season-specific tasks', 'Climate adaptation', 'Growth cycle alignment'],
                    'duration_options': [30, 90, 365],
                    'skill_level': 'intermediate'
                }
            },
            'preference_options': {
                'skill_levels': ['beginner', 'intermediate', 'advanced'],
                'time_constraints': [15, 30, 45, 60, 90],  # minutes per day
                'care_intensity': ['low', 'medium', 'high'],
                'available_days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                'reminder_methods': ['none', 'daily', 'weekly', 'before_task'],
                'weather_integration': [True, False]
            },
            'supported_genera': [
                'Phalaenopsis', 'Cattleya', 'Dendrobium', 'Oncidium',
                'Cymbidium', 'Paphiopedilum', 'Vanda', 'Masdevallia',
                'Epidendrum', 'Brassia', 'Miltonia', 'Zygopetalum'
            ],
            'care_actions': [action.value for action in CareAction],
            'growth_stages': [stage.value for stage in GrowthStage],
            'seasons': [season.value for season in Season]
        }
        
    except Exception as e:
        logger.error(f"Error getting care calendar templates: {e}")
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == "__main__":
    # Test the adaptive care calendar generator
    test_profile = OrchidProfile(
        orchid_id=1,
        genus="Phalaenopsis",
        species="amabilis",
        hybrid_name="Test Orchid",
        growth_stage=GrowthStage.MATURE_VEGETATIVE,
        location="San Francisco, CA",
        pot_size="4 inch",
        medium_type="Bark mix",
        last_repotted=date(2024, 3, 15),
        health_status="Healthy",
        special_needs=[]
    )
    
    generator = AdaptiveCareCalendarGenerator()
    calendar = generator.generate_adaptive_calendar(test_profile, 30)
    
    print(f"Generated calendar with {len(calendar.tasks)} tasks")
    print("\nUpcoming tasks:")
    for task in generator.get_upcoming_tasks(calendar, 7):
        print(f"  {task.scheduled_date}: {task.action.value} - {task.description}")
    
    print("\nCalendar summary:")
    summary = generator.get_calendar_summary(calendar)
    print(json.dumps(summary, indent=2, default=str))