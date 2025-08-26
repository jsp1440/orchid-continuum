from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from app import db
from models import OrchidRecord, User, UserActivity
from datetime import datetime, timedelta
import json
import logging

logger = logging.getLogger(__name__)

game_infrastructure_bp = Blueprint('game_infrastructure', __name__)

class GameSettings:
    """Manage game settings for users"""
    
    DEFAULT_SETTINGS = {
        'sound_effects': True,
        'background_music': False,
        'animations': True,
        'difficulty_level': 'medium',
        'auto_save': True,
        'show_hints': True,
        'timer_display': True,
        'card_back_style': 'orchid',
        'theme': 'dark'
    }
    
    @staticmethod
    def get_user_settings(user_id=None):
        """Get user's game settings or defaults"""
        if user_id and 'game_settings' in session:
            stored_settings = session.get('game_settings', {})
            # Merge with defaults
            settings = {**GameSettings.DEFAULT_SETTINGS, **stored_settings}
            return settings
        return GameSettings.DEFAULT_SETTINGS.copy()
    
    @staticmethod
    def save_user_settings(settings, user_id=None):
        """Save user's game settings"""
        session['game_settings'] = settings
        
        # Track settings change
        if user_id:
            activity = UserActivity(
                user_id=user_id,
                activity_type='game_settings_updated',
                points_earned=1,
                details=json.dumps({'settings': settings})
            )
            db.session.add(activity)
            db.session.commit()

class GameAnalytics:
    """Track game usage and user behavior for admin dashboard"""
    
    @staticmethod
    def log_game_start(user_id, game_type, difficulty=None):
        """Log when a user starts a game"""
        try:
            activity = UserActivity(
                user_id=user_id or 'anonymous',
                activity_type=f'game_start_{game_type}',
                points_earned=5,
                details=json.dumps({
                    'game_type': game_type,
                    'difficulty': difficulty,
                    'timestamp': datetime.now().isoformat(),
                    'session_id': session.get('session_id', 'unknown')
                })
            )
            db.session.add(activity)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging game start: {e}")
    
    @staticmethod
    def log_game_complete(user_id, game_type, score, time_taken, difficulty=None):
        """Log when a user completes a game"""
        try:
            activity = UserActivity(
                user_id=user_id or 'anonymous',
                activity_type=f'game_complete_{game_type}',
                points_earned=10,
                details=json.dumps({
                    'game_type': game_type,
                    'score': score,
                    'time_taken': time_taken,
                    'difficulty': difficulty,
                    'timestamp': datetime.now().isoformat()
                })
            )
            db.session.add(activity)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging game completion: {e}")
    
    @staticmethod
    def log_widget_usage(user_id, widget_name, action='view'):
        """Log widget usage"""
        try:
            # Use None for anonymous users instead of 'anonymous' string
            # to avoid foreign key constraint issues
            activity_user_id = user_id if user_id and user_id != 'anonymous' else None
            
            activity = UserActivity(
                user_id=activity_user_id,
                activity_type=f'widget_{action}',
                points_earned=2,
                details=json.dumps({
                    'widget_name': widget_name,
                    'action': action,
                    'timestamp': datetime.now().isoformat(),
                    'user_agent': request.headers.get('User-Agent', 'unknown'),
                    'is_anonymous': activity_user_id is None
                })
            )
            db.session.add(activity)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging widget usage: {e}")
    
    @staticmethod
    def get_admin_analytics(days=30):
        """Get analytics data for admin dashboard"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days)
            
            # Game analytics
            game_activities = UserActivity.query.filter(
                UserActivity.activity_type.like('game_%'),
                UserActivity.timestamp >= cutoff_date
            ).all()
            
            # Widget analytics
            widget_activities = UserActivity.query.filter(
                UserActivity.activity_type.like('widget_%'),
                UserActivity.timestamp >= cutoff_date
            ).all()
            
            # Process data
            analytics = {
                'games': {
                    'total_sessions': len([a for a in game_activities if 'start' in a.activity_type]),
                    'total_completions': len([a for a in game_activities if 'complete' in a.activity_type]),
                    'by_type': {},
                    'by_difficulty': {},
                    'daily_usage': {}
                },
                'widgets': {
                    'total_views': len(widget_activities),
                    'by_widget': {},
                    'daily_usage': {}
                },
                'users': {
                    'unique_players': len(set(a.user_id for a in game_activities + widget_activities if a.user_id)),
                    'anonymous_users': len([a for a in game_activities + widget_activities if a.user_id is None]),
                    'registered_users': len([a for a in game_activities + widget_activities if a.user_id is not None])
                }
            }
            
            # Process game data
            for activity in game_activities:
                try:
                    details = json.loads(activity.details) if activity.details else {}
                    game_type = details.get('game_type', 'unknown')
                    difficulty = details.get('difficulty', 'unknown')
                    
                    # Count by type
                    if game_type not in analytics['games']['by_type']:
                        analytics['games']['by_type'][game_type] = 0
                    analytics['games']['by_type'][game_type] += 1
                    
                    # Count by difficulty
                    if difficulty not in analytics['games']['by_difficulty']:
                        analytics['games']['by_difficulty'][difficulty] = 0
                    analytics['games']['by_difficulty'][difficulty] += 1
                    
                    # Daily usage
                    date_key = activity.timestamp.strftime('%Y-%m-%d')
                    if date_key not in analytics['games']['daily_usage']:
                        analytics['games']['daily_usage'][date_key] = 0
                    analytics['games']['daily_usage'][date_key] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing game activity: {e}")
            
            # Process widget data
            for activity in widget_activities:
                try:
                    details = json.loads(activity.details) if activity.details else {}
                    widget_name = details.get('widget_name', 'unknown')
                    
                    # Count by widget
                    if widget_name not in analytics['widgets']['by_widget']:
                        analytics['widgets']['by_widget'][widget_name] = 0
                    analytics['widgets']['by_widget'][widget_name] += 1
                    
                    # Daily usage
                    date_key = activity.timestamp.strftime('%Y-%m-%d')
                    if date_key not in analytics['widgets']['daily_usage']:
                        analytics['widgets']['daily_usage'][date_key] = 0
                    analytics['widgets']['daily_usage'][date_key] += 1
                    
                except Exception as e:
                    logger.error(f"Error processing widget activity: {e}")
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error getting admin analytics: {e}")
            return None

class BugReporting:
    """Handle bug reports from games and widgets"""
    
    @staticmethod
    def submit_bug_report(user_id, report_type, title, description, game_context=None):
        """Submit a bug report"""
        try:
            bug_data = {
                'type': report_type,
                'title': title,
                'description': description,
                'game_context': game_context,
                'user_agent': request.headers.get('User-Agent'),
                'timestamp': datetime.now().isoformat(),
                'status': 'open'
            }
            
            activity = UserActivity(
                user_id=user_id or 'anonymous',
                activity_type='bug_report',
                points_earned=5,  # Reward for helping improve the platform
                details=json.dumps(bug_data)
            )
            db.session.add(activity)
            db.session.commit()
            
            logger.info(f"Bug report submitted: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Error submitting bug report: {e}")
            return False

# Routes
@game_infrastructure_bp.route('/games/settings')
def game_settings():
    """Game settings page"""
    user_id = session.get('user_id')
    current_settings = GameSettings.get_user_settings(user_id)
    return render_template('games/settings.html', settings=current_settings)

@game_infrastructure_bp.route('/api/games/settings', methods=['POST'])
def save_game_settings():
    """Save game settings"""
    try:
        data = request.get_json()
        user_id = session.get('user_id')
        
        # Validate settings
        valid_settings = {}
        for key, default_value in GameSettings.DEFAULT_SETTINGS.items():
            if key in data:
                # Type validation
                if isinstance(default_value, bool):
                    valid_settings[key] = bool(data[key])
                elif isinstance(default_value, str):
                    valid_settings[key] = str(data[key])
                else:
                    valid_settings[key] = data[key]
        
        GameSettings.save_user_settings(valid_settings, user_id)
        
        return jsonify({
            'success': True,
            'message': 'Settings saved successfully',
            'settings': valid_settings
        })
        
    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@game_infrastructure_bp.route('/games/help')
def game_help():
    """Game help and how to play page"""
    return render_template('games/help.html')

@game_infrastructure_bp.route('/games/faq')
def game_faq():
    """Game FAQ page"""
    faqs = [
        {
            'category': 'Getting Started',
            'questions': [
                {
                    'question': 'How do I start playing the memory games?',
                    'answer': 'Go to the Games section and select "Memory Challenge". Choose your difficulty level (Easy, Medium, or Hard) and click "Start Game".'
                },
                {
                    'question': 'Do I need to create an account to play?',
                    'answer': 'No! You can play as a guest, but creating an account lets you save your scores, earn badges, and compete on leaderboards.'
                },
                {
                    'question': 'What are the different difficulty levels?',
                    'answer': 'Easy: Match identical orchid photos. Medium: Match photos with genus names. Hard: Match photos with full scientific names.'
                }
            ]
        },
        {
            'category': 'Scoring & Badges',
            'questions': [
                {
                    'question': 'How is my score calculated?',
                    'answer': 'Your score includes base points for matches found, time bonuses for speed, and efficiency bonuses for using fewer moves.'
                },
                {
                    'question': 'How do I earn badges?',
                    'answer': 'Badges are earned automatically for various achievements like completing games, achieving high scores, or demonstrating perfect efficiency.'
                },
                {
                    'question': 'What do the different badge tiers mean?',
                    'answer': 'Badges have different rarities: Common (easy to earn), Rare (moderate challenge), Epic (difficult), and Legendary (extremely challenging).'
                }
            ]
        },
        {
            'category': 'Technical Issues',
            'questions': [
                {
                    'question': 'The game is running slowly. What can I do?',
                    'answer': 'Try disabling animations and sound effects in Settings. Also ensure you have a stable internet connection.'
                },
                {
                    'question': 'My progress was not saved. Why?',
                    'answer': 'Make sure you have cookies enabled and complete the game fully. If playing as a guest, your progress may not be saved.'
                },
                {
                    'question': 'Cards are not flipping when I click them.',
                    'answer': 'This might be a browser issue. Try refreshing the page or clearing your browser cache. Report persistent issues using the bug report form.'
                }
            ]
        },
        {
            'category': 'Rebus Puzzles',
            'questions': [
                {
                    'question': 'What are rebus puzzles?',
                    'answer': 'Rebus puzzles use pictures and symbols to represent orchid names or concepts. Solve the visual clues to find the answer!'
                },
                {
                    'question': 'How often do rebus puzzles change?',
                    'answer': 'A new rebus puzzle is available every day. Each puzzle relates to a different orchid genus or species.'
                },
                {
                    'question': 'Can I get hints for rebus puzzles?',
                    'answer': 'Yes! Click the "Hint" button if you\'re stuck. Hints provide additional context about the orchid or clues about the answer.'
                }
            ]
        }
    ]
    
    return render_template('games/faq.html', faqs=faqs)

@game_infrastructure_bp.route('/games/bug-report', methods=['GET', 'POST'])
def bug_report():
    """Bug report page and submission"""
    if request.method == 'POST':
        data = request.get_json() or request.form
        
        user_id = session.get('user_id')
        report_type = data.get('report_type', 'bug')
        title = data.get('title', '').strip()
        description = data.get('description', '').strip()
        game_context = data.get('game_context', {})
        
        if not title or not description:
            return jsonify({'success': False, 'error': 'Title and description are required'}), 400
        
        success = BugReporting.submit_bug_report(user_id, report_type, title, description, game_context)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Bug report submitted successfully. Thank you for helping us improve!'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to submit bug report'}), 500
    
    return render_template('games/bug_report.html')

@game_infrastructure_bp.route('/admin/game-analytics')
def admin_game_analytics():
    """Admin analytics dashboard for games and widgets"""
    # Check if user is admin (implement your admin check here)
    if not session.get('is_admin', False):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    analytics = GameAnalytics.get_admin_analytics()
    
    if analytics is None:
        flash('Unable to load analytics data', 'error')
        analytics = {'games': {}, 'widgets': {}, 'users': {}}
    
    return render_template('admin/game_analytics.html', analytics=analytics)

@game_infrastructure_bp.route('/api/admin/game-analytics/<int:days>')
def admin_analytics_api(days):
    """API endpoint for admin analytics"""
    if not session.get('is_admin', False):
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    analytics = GameAnalytics.get_admin_analytics(days)
    
    if analytics:
        return jsonify({'success': True, 'analytics': analytics})
    else:
        return jsonify({'success': False, 'error': 'Unable to load analytics'}), 500

# Track widget usage middleware
@game_infrastructure_bp.before_app_request
def track_widget_usage():
    """Track widget usage automatically"""
    if request.endpoint and 'widget' in request.endpoint:
        user_id = session.get('user_id')
        widget_name = request.endpoint.replace('_', ' ').replace('widget', '').strip()
        GameAnalytics.log_widget_usage(user_id, widget_name)

logger.info("Game Infrastructure System initialized successfully")