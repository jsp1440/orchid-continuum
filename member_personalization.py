from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app import db
from models import User, UserActivity
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

member_personalization_bp = Blueprint('member_personalization', __name__)

class PersonalizationManager:
    """Manage user personalization settings and preferences"""
    
    DEFAULT_SETTINGS = {
        'theme': 'dark_orchid',
        'color_scheme': 'green_gold',
        'layout_density': 'comfortable',
        'sidebar_collapsed': False,
        'dashboard_widgets': ['quick_notes', 'recent_orchids', 'care_reminders', 'points_tracker'],
        'notification_preferences': {
            'care_reminders': True,
            'new_orchids': True,
            'society_news': True,
            'game_achievements': True
        }
    }
    
    AVAILABLE_THEMES = {
        'dark_orchid': {
            'name': 'Dark Orchid',
            'description': 'Deep purple and green botanical theme',
            'preview_colors': ['#2d1b3d', '#4a3c5c', '#6b5b95', '#8b7ba8']
        },
        'light_botanical': {
            'name': 'Light Botanical', 
            'description': 'Clean whites and natural greens',
            'preview_colors': ['#ffffff', '#f8f9fa', '#e8f5e8', '#d4e6d4']
        },
        'classic_society': {
            'name': 'Classic Society',
            'description': 'Traditional orchid society colors',
            'preview_colors': ['#1a4d3a', '#2e7d5a', '#4caf50', '#81c784']
        },
        'sunset_bloom': {
            'name': 'Sunset Bloom',
            'description': 'Warm oranges and pinks like evening blooms',
            'preview_colors': ['#3a1f3d', '#7d4f7d', '#ff7043', '#ffab91']
        },
        'forest_canopy': {
            'name': 'Forest Canopy',
            'description': 'Deep forest greens and earth tones',
            'preview_colors': ['#1b3d1b', '#2e5a2e', '#4a7c59', '#7ba87b']
        }
    }
    
    COLOR_SCHEMES = {
        'green_gold': {
            'name': 'Emerald & Gold',
            'primary': '#198754',
            'secondary': '#ffc107',
            'accent': '#20c997',
            'text': '#ffffff'
        },
        'purple_silver': {
            'name': 'Orchid Purple & Silver',
            'primary': '#6f42c1',
            'secondary': '#6c757d', 
            'accent': '#e83e8c',
            'text': '#ffffff'
        },
        'blue_amber': {
            'name': 'Sky Blue & Amber',
            'primary': '#0d6efd',
            'secondary': '#fd7e14',
            'accent': '#17a2b8',
            'text': '#ffffff'
        },
        'rose_mint': {
            'name': 'Rose & Mint',
            'primary': '#d63384',
            'secondary': '#20c997',
            'accent': '#fd7e14',
            'text': '#ffffff'
        }
    }
    
    @staticmethod
    def get_user_settings(user_id):
        """Get user's personalization settings"""
        if not user_id or user_id == 'visitor':
            return PersonalizationManager.DEFAULT_SETTINGS.copy()
        
        try:
            # Get from session first, then database
            session_key = f'personalization_{user_id}'
            if session_key in session:
                stored_settings = session[session_key]
                # Merge with defaults to ensure all keys exist
                settings = {**PersonalizationManager.DEFAULT_SETTINGS}
                settings.update(stored_settings)
                return settings
            
            # TODO: Load from database user preferences table
            return PersonalizationManager.DEFAULT_SETTINGS.copy()
            
        except Exception as e:
            logger.error(f"Error loading user settings: {e}")
            return PersonalizationManager.DEFAULT_SETTINGS.copy()
    
    @staticmethod
    def save_user_settings(user_id, settings):
        """Save user's personalization settings"""
        if not user_id or user_id == 'visitor':
            return False
        
        try:
            # Save to session
            session_key = f'personalization_{user_id}'
            session[session_key] = settings
            
            # Track activity
            activity = UserActivity(
                user_id=user_id,
                activity_type='personalization_updated',
                points_earned=2,
                details=json.dumps({
                    'settings_updated': list(settings.keys()),
                    'theme': settings.get('theme'),
                    'color_scheme': settings.get('color_scheme')
                })
            )
            db.session.add(activity)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving user settings: {e}")
            return False

class NotebookManager:
    """Manage user notebooks and notes"""
    
    @staticmethod
    def get_user_notebooks(user_id):
        """Get user's notebooks"""
        try:
            # Get notebooks from user activities with type 'notebook_entry'
            notebook_activities = (UserActivity.query
                                 .filter(UserActivity.user_id == user_id)
                                 .filter(UserActivity.activity_type.like('notebook_%'))
                                 .order_by(UserActivity.timestamp.desc())
                                 .all())
            
            notebooks = {
                'personal_notes': [],
                'orchid_observations': [],
                'growing_tips': [],
                'care_reminders': []
            }
            
            for activity in notebook_activities:
                try:
                    details = json.loads(activity.details) if activity.details else {}
                    notebook_type = details.get('notebook_type', 'personal_notes')
                    
                    if notebook_type in notebooks:
                        notebooks[notebook_type].append({
                            'id': activity.id,
                            'title': details.get('title', 'Untitled'),
                            'content': details.get('content', ''),
                            'created_at': activity.timestamp,
                            'tags': details.get('tags', [])
                        })
                except Exception as e:
                    logger.error(f"Error processing notebook activity: {e}")
            
            return notebooks
            
        except Exception as e:
            logger.error(f"Error loading notebooks: {e}")
            return {'personal_notes': [], 'orchid_observations': [], 'growing_tips': [], 'care_reminders': []}
    
    @staticmethod
    def save_notebook_entry(user_id, notebook_type, title, content, tags=None):
        """Save a notebook entry"""
        try:
            entry_data = {
                'notebook_type': notebook_type,
                'title': title,
                'content': content,
                'tags': tags or [],
                'created_date': datetime.now().isoformat()
            }
            
            activity = UserActivity(
                user_id=user_id,
                activity_type=f'notebook_{notebook_type}',
                points_earned=5,  # Reward for documentation
                details=json.dumps(entry_data)
            )
            
            db.session.add(activity)
            db.session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving notebook entry: {e}")
            return False

# Routes
@member_personalization_bp.route('/member/dashboard')
def member_dashboard():
    """Enhanced member dashboard"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        flash('Please log in to access your member dashboard', 'info')
        return redirect(url_for('index'))
    
    try:
        # Get user settings
        settings = PersonalizationManager.get_user_settings(user_id)
        
        # Get user notebooks
        notebooks = NotebookManager.get_user_notebooks(user_id)
        
        # Get user statistics
        user_stats = {
            'total_points': 0,
            'notebook_entries': 0,
            'orchid_interactions': 0,
            'days_active': 0
        }
        
        # Calculate stats from activities
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_activities = (UserActivity.query
                           .filter(UserActivity.user_id == user_id)
                           .filter(UserActivity.timestamp >= cutoff_date)
                           .all())
        
        user_stats['total_points'] = sum(a.points_earned for a in recent_activities)
        user_stats['notebook_entries'] = len([a for a in recent_activities if 'notebook' in a.activity_type])
        user_stats['orchid_interactions'] = len([a for a in recent_activities if 'orchid' in a.activity_type])
        
        # Count active days
        active_dates = set(a.timestamp.date() for a in recent_activities)
        user_stats['days_active'] = len(active_dates)
        
        return render_template('member/dashboard.html',
                             settings=settings,
                             notebooks=notebooks,
                             user_stats=user_stats,
                             available_themes=PersonalizationManager.AVAILABLE_THEMES,
                             color_schemes=PersonalizationManager.COLOR_SCHEMES)
        
    except Exception as e:
        logger.error(f"Error loading member dashboard: {e}")
        flash('Error loading dashboard', 'error')
        return redirect(url_for('index'))

@member_personalization_bp.route('/member/personalization')
def personalization_settings():
    """Personalization settings page"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        flash('Please log in to access personalization settings', 'info')
        return redirect(url_for('index'))
    
    settings = PersonalizationManager.get_user_settings(user_id)
    
    return render_template('member/personalization.html',
                         settings=settings,
                         available_themes=PersonalizationManager.AVAILABLE_THEMES,
                         color_schemes=PersonalizationManager.COLOR_SCHEMES)

@member_personalization_bp.route('/api/member/settings', methods=['POST'])
def save_personalization_settings():
    """Save personalization settings"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        
        # Validate settings
        valid_settings = {}
        
        # Theme validation
        if data.get('theme') in PersonalizationManager.AVAILABLE_THEMES:
            valid_settings['theme'] = data['theme']
        
        # Color scheme validation
        if data.get('color_scheme') in PersonalizationManager.COLOR_SCHEMES:
            valid_settings['color_scheme'] = data['color_scheme']
        
        # Layout settings
        if data.get('layout_density') in ['compact', 'comfortable', 'spacious']:
            valid_settings['layout_density'] = data['layout_density']
        
        if 'sidebar_collapsed' in data:
            valid_settings['sidebar_collapsed'] = bool(data['sidebar_collapsed'])
        
        # Dashboard widgets
        if 'dashboard_widgets' in data and isinstance(data['dashboard_widgets'], list):
            valid_settings['dashboard_widgets'] = data['dashboard_widgets']
        
        # Notification preferences
        if 'notification_preferences' in data and isinstance(data['notification_preferences'], dict):
            valid_settings['notification_preferences'] = data['notification_preferences']
        
        # Save settings
        success = PersonalizationManager.save_user_settings(user_id, valid_settings)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Settings saved successfully',
                'settings': valid_settings
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to save settings'}), 500
        
    except Exception as e:
        logger.error(f"Error saving personalization settings: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@member_personalization_bp.route('/member/notebook')
def member_notebook():
    """Member notebook page"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        flash('Please log in to access your notebook', 'info')
        return redirect(url_for('index'))
    
    notebooks = NotebookManager.get_user_notebooks(user_id)
    settings = PersonalizationManager.get_user_settings(user_id)
    
    return render_template('member/notebook.html', 
                         notebooks=notebooks,
                         settings=settings)

@member_personalization_bp.route('/api/member/notebook', methods=['POST'])
def save_notebook_entry():
    """Save a notebook entry"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        
        notebook_type = data.get('notebook_type', 'personal_notes')
        title = data.get('title', '').strip()
        content = data.get('content', '').strip()
        tags = data.get('tags', [])
        
        if not title or not content:
            return jsonify({'success': False, 'error': 'Title and content are required'}), 400
        
        success = NotebookManager.save_notebook_entry(user_id, notebook_type, title, content, tags)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notebook entry saved successfully',
                'points_earned': 5
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to save entry'}), 500
        
    except Exception as e:
        logger.error(f"Error saving notebook entry: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

@member_personalization_bp.route('/api/member/quick-note', methods=['POST'])
def save_quick_note():
    """Save a quick notepad note"""
    user_id = session.get('user_id')
    if not user_id or user_id == 'visitor':
        return jsonify({'success': False, 'error': 'Login required'}), 401
    
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Save as a quick note
        success = NotebookManager.save_notebook_entry(
            user_id, 
            'personal_notes', 
            f"Quick Note - {datetime.now().strftime('%m/%d %H:%M')}", 
            content,
            ['quick-note']
        )
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Quick note saved',
                'points_earned': 2
            })
        else:
            return jsonify({'success': False, 'error': 'Unable to save note'}), 500
        
    except Exception as e:
        logger.error(f"Error saving quick note: {e}")
        return jsonify({'success': False, 'error': 'Server error'}), 500

logger.info("Member Personalization System initialized successfully")