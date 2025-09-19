#!/usr/bin/env python3
"""
Widget Integration Hub - Central coordination for all widgets
Implements cross-widget data sharing, unified sessions, and enhanced user experience
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import session, request
from app import db
from models import OrchidRecord
from sqlalchemy import func, or_

logger = logging.getLogger(__name__)

class WidgetIntegrationHub:
    """
    Central hub for widget integration and cross-widget functionality
    """
    
    def __init__(self):
        self.session_key = 'widget_hub_session'
        self.user_preferences_key = 'user_widget_preferences'
        self.favorites_key = 'user_favorites'
        self.exploration_key = 'exploration_progress'
        
    def get_user_session(self) -> Dict:
        """Get or create unified user session across all widgets"""
        if self.session_key not in session:
            session[self.session_key] = {
                'session_id': f"user_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'created_at': datetime.now().isoformat(),
                'widget_history': [],
                'current_context': {},
                'preferences': {
                    'preferred_view': 'gallery',
                    'favorite_genus': None,
                    'last_search': None,
                    'map_region': 'global',
                    'weather_location': None
                }
            }
        return session[self.session_key]
    
    def update_widget_context(self, widget_name: str, context_data: Dict):
        """Update current context when user interacts with a widget"""
        user_session = self.get_user_session()
        
        # Add to widget history
        user_session['widget_history'].append({
            'widget': widget_name,
            'timestamp': datetime.now().isoformat(),
            'action': context_data.get('action', 'view'),
            'data': context_data
        })
        
        # Keep only last 10 interactions
        user_session['widget_history'] = user_session['widget_history'][-10:]
        
        # Update current context
        user_session['current_context'][widget_name] = context_data
        
        # Update preferences based on usage
        self._update_preferences_from_context(widget_name, context_data)
        
        session[self.session_key] = user_session
        
    def _update_preferences_from_context(self, widget_name: str, context_data: Dict):
        """Intelligently update user preferences based on widget interactions"""
        user_session = self.get_user_session()
        preferences = user_session['preferences']
        
        # Update based on widget type
        if widget_name == 'search' and context_data.get('query'):
            preferences['last_search'] = context_data['query']
            # Extract genus if search looks like scientific name
            query = context_data['query'].strip()
            if ' ' in query:
                potential_genus = query.split()[0].capitalize()
                preferences['favorite_genus'] = potential_genus
                
        elif widget_name == 'map' and context_data.get('region'):
            preferences['map_region'] = context_data['region']
            
        elif widget_name == 'weather' and context_data.get('location'):
            preferences['weather_location'] = context_data['location']
            
        elif widget_name == 'gallery' and context_data.get('genus'):
            preferences['favorite_genus'] = context_data['genus']
            
    def get_smart_recommendations(self, current_widget: str) -> Dict:
        """Provide intelligent widget recommendations based on user context"""
        user_session = self.get_user_session()
        context = user_session['current_context']
        preferences = user_session['preferences']
        
        recommendations = {
            'next_widgets': [],
            'suggested_actions': [],
            'related_content': []
        }
        
        # Smart recommendations based on current widget
        if current_widget == 'search':
            last_search = preferences.get('last_search')
            if last_search:
                recommendations['next_widgets'].extend([
                    {
                        'widget': 'map',
                        'reason': f'Explore where {last_search} grows naturally',
                        'action_url': f'/widgets/map?genus={last_search.split()[0]}'
                    },
                    {
                        'widget': 'weather',
                        'reason': f'Compare growing conditions for {last_search}',
                        'action_url': f'/widgets/weather?species={last_search}'
                    }
                ])
                
        elif current_widget == 'gallery':
            recommendations['next_widgets'].extend([
                {
                    'widget': 'comparison',
                    'reason': 'Compare selected orchids side-by-side',
                    'action_url': '/compare'
                },
                {
                    'widget': 'search',
                    'reason': 'Find more orchids like these',
                    'action_url': '/search'
                }
            ])
            
        elif current_widget == 'map':
            map_region = context.get('map', {}).get('region')
            if map_region:
                recommendations['next_widgets'].extend([
                    {
                        'widget': 'weather',
                        'reason': f'Check climate conditions in {map_region}',
                        'action_url': f'/widgets/weather?region={map_region}'
                    },
                    {
                        'widget': 'gallery',
                        'reason': f'Browse orchids from {map_region}',
                        'action_url': f'/gallery?region={map_region}'
                    }
                ])
                
        return recommendations
    
    def manage_favorites(self, action: str, orchid_id: int = None, orchid_data: Dict = None) -> Dict:
        """Manage user favorites across all widgets"""
        if self.favorites_key not in session:
            session[self.favorites_key] = []
            
        favorites = session[self.favorites_key]
        
        if action == 'add' and orchid_id:
            # Add to favorites if not already there
            if orchid_id not in [fav.get('id') for fav in favorites]:
                favorite_item = {
                    'id': orchid_id,
                    'added_at': datetime.now().isoformat(),
                    'added_from_widget': request.endpoint or 'unknown'
                }
                
                # Add orchid data if provided
                if orchid_data:
                    favorite_item.update(orchid_data)
                else:
                    # Fetch from database
                    orchid = OrchidRecord.query.get(orchid_id)
                    if orchid:
                        favorite_item.update({
                            'display_name': orchid.display_name,
                            'scientific_name': orchid.scientific_name,
                            'genus': orchid.genus,
                            'image_url': orchid.image_url
                        })
                
                favorites.append(favorite_item)
                session[self.favorites_key] = favorites[-20:]  # Keep last 20
                
        elif action == 'remove' and orchid_id:
            favorites = [fav for fav in favorites if fav.get('id') != orchid_id]
            session[self.favorites_key] = favorites
            
        elif action == 'get':
            return {'favorites': favorites, 'count': len(favorites)}
            
        return {'favorites': favorites, 'count': len(favorites)}
    
    def track_exploration_progress(self, achievement_data: Dict) -> Dict:
        """Track user's exploration progress across widgets"""
        if self.exploration_key not in session:
            session[self.exploration_key] = {
                'genera_discovered': set(),
                'regions_explored': set(),
                'widgets_used': set(),
                'total_interactions': 0,
                'achievements': [],
                'started_at': datetime.now().isoformat()
            }
            
        progress = session[self.exploration_key]
        
        # Convert sets back from list (session serialization)
        for key in ['genera_discovered', 'regions_explored', 'widgets_used']:
            if isinstance(progress[key], list):
                progress[key] = set(progress[key])
        
        # Update progress
        if achievement_data.get('genus'):
            progress['genera_discovered'].add(achievement_data['genus'])
            
        if achievement_data.get('region'):
            progress['regions_explored'].add(achievement_data['region'])
            
        if achievement_data.get('widget'):
            progress['widgets_used'].add(achievement_data['widget'])
            
        progress['total_interactions'] += 1
        
        # Check for new achievements
        new_achievements = self._check_achievements(progress)
        progress['achievements'].extend(new_achievements)
        
        # Convert sets to lists for session storage
        for key in ['genera_discovered', 'regions_explored', 'widgets_used']:
            progress[key] = list(progress[key])
            
        session[self.exploration_key] = progress
        
        return {
            'progress': progress,
            'new_achievements': new_achievements
        }
    
    def _check_achievements(self, progress: Dict) -> List[Dict]:
        """Check for new achievements based on user progress"""
        achievements = []
        existing_achievement_types = [ach.get('type') for ach in progress.get('achievements', [])]
        
        # Genera discovery achievements
        genera_count = len(progress['genera_discovered'])
        if genera_count >= 5 and 'genus_explorer' not in existing_achievement_types:
            achievements.append({
                'type': 'genus_explorer',
                'title': 'Genus Explorer',
                'description': f'Discovered {genera_count} different orchid genera',
                'earned_at': datetime.now().isoformat(),
                'icon': '🌺'
            })
            
        # Widget usage achievements
        widget_count = len(progress['widgets_used'])
        if widget_count >= 3 and 'widget_master' not in existing_achievement_types:
            achievements.append({
                'type': 'widget_master',
                'title': 'Widget Master',
                'description': f'Used {widget_count} different widgets',
                'earned_at': datetime.now().isoformat(),
                'icon': '🎯'
            })
            
        # Interaction achievements
        interaction_count = progress['total_interactions']
        if interaction_count >= 25 and 'active_explorer' not in existing_achievement_types:
            achievements.append({
                'type': 'active_explorer',
                'title': 'Active Explorer',
                'description': f'Made {interaction_count} interactions',
                'earned_at': datetime.now().isoformat(),
                'icon': '⭐'
            })
            
        return achievements
    
    def get_cross_widget_data(self, widget_type: str, **kwargs) -> Dict:
        """Get data for widgets enhanced with cross-widget context"""
        user_session = self.get_user_session()
        preferences = user_session['preferences']
        
        # Base widget data
        base_data = self._get_base_widget_data(widget_type, **kwargs)
        
        # Enhance with cross-widget context
        enhancement = {
            'user_preferences': preferences,
            'favorites': self.manage_favorites('get')['favorites'],
            'recommendations': self.get_smart_recommendations(widget_type),
            'session_context': user_session['current_context']
        }
        
        # Widget-specific enhancements
        if widget_type == 'search':
            enhancement['suggested_searches'] = self._get_suggested_searches()
            
        elif widget_type == 'gallery':
            enhancement['personalized_filter'] = self._get_personalized_gallery_filter()
            
        elif widget_type == 'map':
            enhancement['preferred_regions'] = self._get_preferred_regions()
            
        base_data['integration'] = enhancement
        return base_data
    
    def _get_base_widget_data(self, widget_type: str, **kwargs) -> Dict:
        """Get base data for widget (placeholder - would call existing widget system)"""
        # This would integrate with your existing widget_system.py
        return {'widget_type': widget_type, 'data': 'base_data'}
    
    def _get_suggested_searches(self) -> List[str]:
        """Get personalized search suggestions"""
        user_session = self.get_user_session()
        suggestions = []
        
        # Based on favorite genus
        if user_session['preferences'].get('favorite_genus'):
            genus = user_session['preferences']['favorite_genus']
            suggestions.append(f"{genus} species")
            suggestions.append(f"{genus} hybrids")
            
        # Based on recent searches
        recent_searches = [item['data'].get('query') for item in user_session['widget_history'] 
                          if item['widget'] == 'search' and item['data'].get('query')]
        suggestions.extend(recent_searches[-3:])  # Last 3 searches
        
        return list(set(suggestions))  # Remove duplicates
    
    def _get_personalized_gallery_filter(self) -> Dict:
        """Get personalized gallery filtering preferences"""
        user_session = self.get_user_session()
        preferences = user_session['preferences']
        
        return {
            'preferred_genus': preferences.get('favorite_genus'),
            'last_viewed_region': preferences.get('map_region'),
            'show_favorites_first': True
        }
    
    def _get_preferred_regions(self) -> List[str]:
        """Get user's preferred geographic regions"""
        user_session = self.get_user_session()
        
        # Extract regions from widget history
        regions = []
        for item in user_session['widget_history']:
            if item['widget'] == 'map' and item['data'].get('region'):
                regions.append(item['data']['region'])
                
        return list(set(regions))
    
    def get_unified_dashboard_data(self) -> Dict:
        """Get comprehensive data for unified user dashboard"""
        user_session = self.get_user_session()
        progress = session.get(self.exploration_key, {})
        favorites = self.manage_favorites('get')
        
        # Recent activity summary
        recent_activity = user_session['widget_history'][-5:]  # Last 5 actions
        
        # Usage statistics
        widget_usage = {}
        for item in user_session['widget_history']:
            widget = item['widget']
            widget_usage[widget] = widget_usage.get(widget, 0) + 1
            
        return {
            'session_info': {
                'session_id': user_session['session_id'],
                'created_at': user_session['created_at'],
                'total_interactions': len(user_session['widget_history'])
            },
            'preferences': user_session['preferences'],
            'favorites': favorites,
            'progress': progress,
            'recent_activity': recent_activity,
            'widget_usage': widget_usage,
            'recommendations': self.get_smart_recommendations('dashboard')
        }


# Global instance for use across the application
widget_hub = WidgetIntegrationHub()


def track_widget_interaction(widget_name: str, action: str, **context_data):
    """Convenience function to track widget interactions"""
    try:
        context = {'action': action, **context_data}
        widget_hub.update_widget_context(widget_name, context)
        
        # Track exploration progress
        widget_hub.track_exploration_progress({
            'widget': widget_name,
            'genus': context_data.get('genus'),
            'region': context_data.get('region')
        })
        
    except Exception as e:
        logger.error(f"Error tracking widget interaction: {str(e)}")


def get_enhanced_widget_data(widget_type: str, **kwargs):
    """Get widget data enhanced with cross-widget integration"""
    try:
        return widget_hub.get_cross_widget_data(widget_type, **kwargs)
    except Exception as e:
        logger.error(f"Error getting enhanced widget data: {str(e)}")
        return {'error': str(e)}