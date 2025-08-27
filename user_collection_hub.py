#!/usr/bin/env python3
"""
User Collection Hub - Personal orchid collection management and care system
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import session, request
from app import db
from models import OrchidRecord
from sqlalchemy import func, or_
from widget_integration_hub import widget_hub

logger = logging.getLogger(__name__)

class UserCollectionHub:
    """
    Manages personal orchid collections, care reminders, and personalized experiences
    """
    
    def __init__(self):
        self.collection_key = 'user_orchid_collection'
        self.care_schedule_key = 'care_schedule'
        self.growing_log_key = 'growing_log'
        
    def get_user_collection(self) -> Dict:
        """Get user's personal orchid collection"""
        if self.collection_key not in session:
            session[self.collection_key] = {
                'owned_orchids': [],
                'wishlist': [],
                'growing_notes': {},
                'care_preferences': {
                    'watering_schedule': 'weekly',
                    'fertilizer_schedule': 'biweekly',
                    'preferred_growing_medium': 'bark',
                    'light_preference': 'bright_indirect',
                    'humidity_target': 60,
                    'temperature_range': 'intermediate'
                },
                'created_at': datetime.now().isoformat()
            }
        return session[self.collection_key]
    
    def add_to_collection(self, orchid_id: int, collection_type: str = 'owned', care_data: Dict = None) -> Dict:
        """Add orchid to user's collection"""
        collection = self.get_user_collection()
        
        # Get orchid data
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return {'success': False, 'error': 'Orchid not found'}
        
        collection_item = {
            'orchid_id': orchid_id,
            'display_name': orchid.display_name,
            'scientific_name': orchid.scientific_name,
            'genus': orchid.genus,
            'species': orchid.species,
            'image_url': orchid.image_url,
            'added_at': datetime.now().isoformat(),
            'personal_notes': care_data.get('notes', '') if care_data else '',
            'acquisition_date': care_data.get('acquisition_date') if care_data else None,
            'source': care_data.get('source', 'unknown') if care_data else 'unknown',
            'current_stage': care_data.get('stage', 'healthy') if care_data else 'healthy',
            'care_difficulty': care_data.get('difficulty', 'medium') if care_data else 'medium'
        }
        
        # Add to appropriate collection
        if collection_type == 'owned':
            # Check if already in collection
            if not any(item['orchid_id'] == orchid_id for item in collection['owned_orchids']):
                collection['owned_orchids'].append(collection_item)
                
                # Set up default care schedule
                self._create_care_schedule(orchid_id, orchid, care_data or {})
                
        elif collection_type == 'wishlist':
            if not any(item['orchid_id'] == orchid_id for item in collection['wishlist']):
                collection['wishlist'].append(collection_item)
        
        session[self.collection_key] = collection
        
        # Track in widget hub
        widget_hub.update_widget_context('collection', {
            'action': 'add_orchid',
            'orchid_id': orchid_id,
            'collection_type': collection_type,
            'genus': orchid.genus
        })
        
        return {'success': True, 'collection_item': collection_item}
    
    def _create_care_schedule(self, orchid_id: int, orchid: OrchidRecord, care_data: Dict):
        """Create care schedule for newly added orchid"""
        if self.care_schedule_key not in session:
            session[self.care_schedule_key] = {}
            
        care_schedule = session[self.care_schedule_key]
        
        # Default care schedule based on orchid characteristics
        base_schedule = {
            'watering': {
                'frequency_days': 7,  # Weekly default
                'last_watered': None,
                'next_due': None,
                'notes': f'Adjust based on {orchid.genus} requirements'
            },
            'fertilizing': {
                'frequency_days': 14,  # Biweekly default
                'last_fertilized': None,
                'next_due': None,
                'fertilizer_type': 'balanced_orchid'
            },
            'repotting': {
                'frequency_days': 730,  # Every 2 years
                'last_repotted': care_data.get('last_repotted'),
                'next_due': None,
                'medium_type': orchid.growth_habit or 'bark_mix'
            },
            'monitoring': {
                'check_frequency_days': 3,
                'last_checked': datetime.now().isoformat(),
                'health_status': 'good',
                'growth_stage': care_data.get('stage', 'mature')
            }
        }
        
        # Customize based on genus-specific needs
        if orchid.genus:
            genus_specific = self._get_genus_care_requirements(orchid.genus)
            base_schedule.update(genus_specific)
        
        care_schedule[str(orchid_id)] = base_schedule
        session[self.care_schedule_key] = care_schedule
    
    def _get_genus_care_requirements(self, genus: str) -> Dict:
        """Get genus-specific care requirements"""
        genus_care = {
            'Phalaenopsis': {
                'watering': {'frequency_days': 10, 'notes': 'Allow slight drying between waterings'},
                'fertilizing': {'frequency_days': 14, 'fertilizer_type': 'weak_weekly'},
                'light_requirements': 'bright_indirect',
                'humidity_preference': 50
            },
            'Cattleya': {
                'watering': {'frequency_days': 7, 'notes': 'Dry out completely between waterings'},
                'fertilizing': {'frequency_days': 7, 'fertilizer_type': 'high_potassium'},
                'light_requirements': 'bright_direct',
                'humidity_preference': 60
            },
            'Dendrobium': {
                'watering': {'frequency_days': 5, 'notes': 'More frequent in growing season'},
                'fertilizing': {'frequency_days': 10, 'fertilizer_type': 'balanced'},
                'light_requirements': 'bright_indirect',
                'humidity_preference': 65
            },
            'Oncidium': {
                'watering': {'frequency_days': 6, 'notes': 'Keep slightly moist'},
                'fertilizing': {'frequency_days': 14, 'fertilizer_type': 'balanced'},
                'light_requirements': 'bright_indirect',
                'humidity_preference': 55
            },
            'Vanda': {
                'watering': {'frequency_days': 1, 'notes': 'Daily watering or misting'},
                'fertilizing': {'frequency_days': 7, 'fertilizer_type': 'weak_weekly'},
                'light_requirements': 'bright_direct',
                'humidity_preference': 70
            }
        }
        
        return genus_care.get(genus, {})
    
    def get_care_reminders(self) -> List[Dict]:
        """Get upcoming care reminders for user's collection"""
        if self.care_schedule_key not in session:
            return []
            
        care_schedule = session[self.care_schedule_key]
        collection = self.get_user_collection()
        reminders = []
        
        today = datetime.now()
        
        for orchid_item in collection['owned_orchids']:
            orchid_id = str(orchid_item['orchid_id'])
            if orchid_id not in care_schedule:
                continue
                
            schedule = care_schedule[orchid_id]
            
            # Check each care type
            for care_type, care_info in schedule.items():
                if 'frequency_days' not in care_info:
                    continue
                    
                last_date_str = care_info.get('last_watered') or care_info.get('last_fertilized') or care_info.get('last_repotted') or care_info.get('last_checked')
                
                if last_date_str:
                    last_date = datetime.fromisoformat(last_date_str)
                    next_due = last_date + timedelta(days=care_info['frequency_days'])
                    days_until = (next_due - today).days
                    
                    if days_until <= 3:  # Show reminders for next 3 days
                        urgency = 'overdue' if days_until < 0 else ('today' if days_until == 0 else 'soon')
                        
                        reminders.append({
                            'orchid_id': orchid_item['orchid_id'],
                            'orchid_name': orchid_item['display_name'],
                            'care_type': care_type,
                            'due_date': next_due.isoformat(),
                            'days_until': days_until,
                            'urgency': urgency,
                            'notes': care_info.get('notes', ''),
                            'image_url': orchid_item.get('image_url')
                        })
        
        # Sort by urgency
        urgency_order = {'overdue': 0, 'today': 1, 'soon': 2}
        reminders.sort(key=lambda x: (urgency_order[x['urgency']], x['days_until']))
        
        return reminders
    
    def log_care_activity(self, orchid_id: int, care_type: str, notes: str = '') -> Dict:
        """Log a care activity for an orchid"""
        if self.care_schedule_key not in session:
            session[self.care_schedule_key] = {}
            
        care_schedule = session[self.care_schedule_key]
        orchid_id_str = str(orchid_id)
        
        if orchid_id_str not in care_schedule:
            return {'success': False, 'error': 'Orchid not in care schedule'}
        
        # Update last activity date
        today = datetime.now().isoformat()
        
        if care_type == 'watering':
            care_schedule[orchid_id_str]['watering']['last_watered'] = today
        elif care_type == 'fertilizing':
            care_schedule[orchid_id_str]['fertilizing']['last_fertilized'] = today
        elif care_type == 'repotting':
            care_schedule[orchid_id_str]['repotting']['last_repotted'] = today
        elif care_type == 'monitoring':
            care_schedule[orchid_id_str]['monitoring']['last_checked'] = today
        
        # Log the activity
        if self.growing_log_key not in session:
            session[self.growing_log_key] = []
            
        growing_log = session[self.growing_log_key]
        
        log_entry = {
            'orchid_id': orchid_id,
            'care_type': care_type,
            'date': today,
            'notes': notes,
            'logged_at': today
        }
        
        growing_log.append(log_entry)
        
        # Keep only last 100 entries
        session[self.growing_log_key] = growing_log[-100:]
        session[self.care_schedule_key] = care_schedule
        
        # Track in widget hub
        widget_hub.update_widget_context('collection', {
            'action': 'log_care',
            'orchid_id': orchid_id,
            'care_type': care_type
        })
        
        return {'success': True, 'log_entry': log_entry}
    
    def get_collection_dashboard_data(self) -> Dict:
        """Get comprehensive dashboard data for user's collection"""
        collection = self.get_user_collection()
        reminders = self.get_care_reminders()
        
        # Collection statistics
        stats = {
            'total_owned': len(collection['owned_orchids']),
            'total_wishlist': len(collection['wishlist']),
            'genera_count': len(set(item['genus'] for item in collection['owned_orchids'] if item.get('genus'))),
            'overdue_care': len([r for r in reminders if r['urgency'] == 'overdue']),
            'care_due_today': len([r for r in reminders if r['urgency'] == 'today'])
        }
        
        # Recent activity
        growing_log = session.get(self.growing_log_key, [])
        recent_activity = growing_log[-5:]  # Last 5 activities
        
        # Genus distribution
        genus_distribution = {}
        for item in collection['owned_orchids']:
            genus = item.get('genus', 'Unknown')
            genus_distribution[genus] = genus_distribution.get(genus, 0) + 1
        
        return {
            'collection': collection,
            'statistics': stats,
            'care_reminders': reminders[:10],  # Next 10 reminders
            'recent_activity': recent_activity,
            'genus_distribution': genus_distribution,
            'care_preferences': collection['care_preferences']
        }
    
    def get_personalized_recommendations(self) -> Dict:
        """Get personalized orchid recommendations based on collection"""
        collection = self.get_user_collection()
        
        if not collection['owned_orchids']:
            # New user recommendations
            return self._get_beginner_recommendations()
        
        # Analyze user's collection
        user_genera = set(item['genus'] for item in collection['owned_orchids'] if item.get('genus'))
        care_preferences = collection['care_preferences']
        
        # Find similar orchids
        recommendations = []
        
        # Query database for orchids in user's preferred genera
        for genus in user_genera:
            similar_orchids = OrchidRecord.query.filter(
                OrchidRecord.genus == genus,
                OrchidRecord.id.notin_([item['orchid_id'] for item in collection['owned_orchids']])
            ).limit(3).all()
            
            for orchid in similar_orchids:
                recommendations.append({
                    'orchid_id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': orchid.image_url,
                    'reason': f'Similar to your {genus} collection',
                    'care_compatibility': self._calculate_care_compatibility(orchid, care_preferences)
                })
        
        # Also recommend orchids with compatible care requirements
        compatible_orchids = self._find_care_compatible_orchids(care_preferences, user_genera)
        recommendations.extend(compatible_orchids)
        
        # Remove duplicates and sort by compatibility
        seen_ids = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec['orchid_id'] not in seen_ids:
                seen_ids.add(rec['orchid_id'])
                unique_recommendations.append(rec)
        
        unique_recommendations.sort(key=lambda x: x['care_compatibility'], reverse=True)
        
        return {
            'recommendations': unique_recommendations[:10],
            'based_on': {
                'user_genera': list(user_genera),
                'care_preferences': care_preferences,
                'collection_size': len(collection['owned_orchids'])
            }
        }
    
    def _get_beginner_recommendations(self) -> Dict:
        """Get recommendations for new orchid growers"""
        beginner_friendly = ['Phalaenopsis', 'Dendrobium', 'Oncidium']
        
        recommendations = []
        for genus in beginner_friendly:
            orchids = OrchidRecord.query.filter(OrchidRecord.genus == genus).limit(2).all()
            
            for orchid in orchids:
                recommendations.append({
                    'orchid_id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': orchid.image_url,
                    'reason': f'{genus} orchids are beginner-friendly',
                    'care_compatibility': 0.9  # High compatibility for beginners
                })
        
        return {
            'recommendations': recommendations,
            'based_on': {
                'user_genera': [],
                'care_preferences': {},
                'collection_size': 0,
                'note': 'Beginner-friendly recommendations'
            }
        }
    
    def _calculate_care_compatibility(self, orchid: OrchidRecord, care_preferences: Dict) -> float:
        """Calculate how well an orchid matches user's care preferences"""
        compatibility_score = 0.5  # Base score
        
        # Check genus-specific requirements
        if orchid.genus:
            genus_care = self._get_genus_care_requirements(orchid.genus)
            
            # Compare light requirements
            if genus_care.get('light_requirements') == care_preferences.get('light_preference'):
                compatibility_score += 0.2
            
            # Compare humidity preferences
            genus_humidity = genus_care.get('humidity_preference', 60)
            user_humidity = care_preferences.get('humidity_target', 60)
            humidity_diff = abs(genus_humidity - user_humidity)
            if humidity_diff <= 10:
                compatibility_score += 0.2
            
            # Compare watering frequency
            genus_watering = genus_care.get('watering', {}).get('frequency_days', 7)
            user_watering_map = {'daily': 1, 'every_few_days': 3, 'weekly': 7, 'biweekly': 14}
            user_watering = user_watering_map.get(care_preferences.get('watering_schedule', 'weekly'), 7)
            
            watering_diff = abs(genus_watering - user_watering)
            if watering_diff <= 2:
                compatibility_score += 0.1
        
        return min(compatibility_score, 1.0)
    
    def _find_care_compatible_orchids(self, care_preferences: Dict, exclude_genera: set) -> List[Dict]:
        """Find orchids with compatible care requirements"""
        compatible_genera = []
        
        # Map care preferences to compatible genera
        light_pref = care_preferences.get('light_preference', 'bright_indirect')
        if light_pref == 'bright_indirect':
            compatible_genera.extend(['Phalaenopsis', 'Dendrobium', 'Oncidium'])
        elif light_pref == 'bright_direct':
            compatible_genera.extend(['Cattleya', 'Vanda'])
        
        # Remove genera user already has
        compatible_genera = [g for g in compatible_genera if g not in exclude_genera]
        
        recommendations = []
        for genus in compatible_genera[:3]:  # Limit to 3 genera
            orchids = OrchidRecord.query.filter(OrchidRecord.genus == genus).limit(2).all()
            
            for orchid in orchids:
                recommendations.append({
                    'orchid_id': orchid.id,
                    'display_name': orchid.display_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': orchid.image_url,
                    'reason': f'Compatible with your care preferences',
                    'care_compatibility': self._calculate_care_compatibility(orchid, care_preferences)
                })
        
        return recommendations


# Global instance
collection_hub = UserCollectionHub()