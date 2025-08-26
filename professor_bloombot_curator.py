from flask import Blueprint, render_template, request, jsonify, session, flash
from app import db
from models import OrchidRecord, UserActivity, User
from datetime import datetime, timedelta
import json
import logging
import random

logger = logging.getLogger(__name__)

bloombot_curator_bp = Blueprint('bloombot_curator', __name__)

class ProfessorBloomBot:
    """Professor BloomBot AI curator for orchid engagement"""
    
    def __init__(self):
        self.personality_traits = [
            "enthusiastic botanical expert",
            "encouraging mentor", 
            "curious researcher",
            "patient teacher"
        ]
        
        self.greeting_phrases = [
            "Welcome to our botanical wonderland!",
            "Greetings, fellow orchid enthusiast!",
            "Hello there, nature lover!",
            "Welcome to the fascinating world of orchids!"
        ]
        
        self.engagement_prompts = [
            "I'd love to hear your thoughts on these specimens!",
            "What catches your eye in this beautiful collection?",
            "Which of these orchids speaks to you?",
            "I'm curious about your observations!",
            "Help me understand what you find most interesting!"
        ]
    
    def get_curated_selection(self, theme='random'):
        """Get a curated selection of 10 orchids with Professor BloomBot commentary"""
        
        themes = {
            'beginner_friendly': {
                'criteria': "growth_habit IN ('epiphytic', 'terrestrial') AND climate_preference IN ('intermediate', 'warm')",
                'description': "Perfect orchids for those starting their journey!"
            },
            'exotic_beauties': {
                'criteria': "region NOT LIKE '%North America%' OR genus IN ('Vanda', 'Dendrobium', 'Oncidium')",
                'description': "Stunning orchids from around the world!"
            },
            'native_treasures': {
                'criteria': "region LIKE '%North America%' OR country LIKE '%United States%'",
                'description': "Beautiful native orchids from our region!"
            },
            'seasonal_highlights': {
                'criteria': f"bloom_time LIKE '%{self._current_season()}%' OR bloom_time IS NULL",
                'description': f"Orchids that bloom during {self._current_season()}!"
            },
            'rare_specimens': {
                'criteria': "ai_confidence > 0.8 AND view_count < 50",
                'description': "Hidden gems waiting to be discovered!"
            }
        }
        
        # Default to random if theme not found
        if theme not in themes:
            theme = 'random'
        
        try:
            if theme == 'random':
                # Random selection from well-documented orchids
                orchids = (OrchidRecord.query
                          .filter(OrchidRecord.image_url.isnot(None))
                          .filter(OrchidRecord.google_drive_id.isnot(None))
                          .filter(OrchidRecord.display_name.isnot(None))
                          .order_by(db.func.random())
                          .limit(10)
                          .all())
                description = "A delightful mix of orchids I've personally selected!"
            else:
                theme_info = themes[theme]
                # Note: Using raw SQL for complex queries - in production, use proper ORM methods
                orchids = (OrchidRecord.query
                          .filter(OrchidRecord.image_url.isnot(None))
                          .filter(OrchidRecord.google_drive_id.isnot(None))
                          .order_by(db.func.random())
                          .limit(10)
                          .all())
                description = theme_info['description']
            
            if not orchids:
                # Fallback to any available orchids
                orchids = (OrchidRecord.query
                          .filter(OrchidRecord.google_drive_id.isnot(None))
                          .limit(10)
                          .all())
                description = "A wonderful selection from our collection!"
            
            # Generate Professor BloomBot commentary for each orchid
            curated_orchids = []
            for orchid in orchids:
                commentary = self._generate_commentary(orchid)
                curated_orchids.append({
                    'id': orchid.id,
                    'display_name': orchid.display_name or orchid.scientific_name,
                    'scientific_name': orchid.scientific_name,
                    'genus': orchid.genus,
                    'image_url': f"/api/drive-photo/{orchid.google_drive_id}" if orchid.google_drive_id else orchid.image_url,
                    'region': orchid.region,
                    'growth_habit': orchid.growth_habit,
                    'bloom_time': orchid.bloom_time,
                    'climate_preference': orchid.climate_preference,
                    'bloombot_commentary': commentary,
                    'ai_description': orchid.ai_description
                })
            
            return {
                'theme': theme,
                'title': self._get_theme_title(theme),
                'description': description,
                'orchids': curated_orchids,
                'greeting': random.choice(self.greeting_phrases),
                'prompt': random.choice(self.engagement_prompts),
                'curator_note': self._get_curator_note(theme, len(curated_orchids))
            }
            
        except Exception as e:
            logger.error(f"Error creating curated selection: {e}")
            return self._get_fallback_selection()
    
    def _generate_commentary(self, orchid):
        """Generate Professor BloomBot commentary for an orchid"""
        
        comments = []
        
        # Growth habit commentary
        if orchid.growth_habit:
            if orchid.growth_habit == 'epiphytic':
                comments.append("This magnificent epiphyte grows naturally on trees in the wild!")
            elif orchid.growth_habit == 'terrestrial':
                comments.append("This ground-dwelling beauty thrives in rich forest soils.")
            elif orchid.growth_habit == 'lithophytic':
                comments.append("Remarkably, this orchid grows on rocks in nature!")
        
        # Geographic commentary
        if orchid.region:
            comments.append(f"Originally from {orchid.region}, showcasing nature's global artistry.")
        
        # Bloom time commentary
        if orchid.bloom_time:
            comments.append(f"Look for those stunning blooms during {orchid.bloom_time}!")
        
        # Climate commentary  
        if orchid.climate_preference:
            if orchid.climate_preference == 'cool':
                comments.append("Prefers cooler temperatures - perfect for temperate climates!")
            elif orchid.climate_preference == 'warm':
                comments.append("Loves warm conditions - imagine tropical paradise!")
            elif orchid.climate_preference == 'intermediate':
                comments.append("Adaptable to moderate temperatures - very accommodating!")
        
        # Genus-specific commentary
        genus_comments = {
            'Cattleya': "The 'Queen of Orchids' - truly spectacular!",
            'Phalaenopsis': "The beloved 'Moth Orchid' - perfect for beginners!",
            'Dendrobium': "Incredibly diverse genus with amazing forms!",
            'Oncidium': "Dancing ladies with cheerful yellow blooms!",
            'Cypripedium': "The elegant 'Lady Slipper' - nature's perfection!",
            'Paphiopedilum': "Tropical slipper orchids with unique pouches!",
            'Vanda': "Spectacular epiphytes with vibrant colors!",
            'Epidendrum': "Hardy and reliable - great garden orchids!"
        }
        
        if orchid.genus in genus_comments:
            comments.append(genus_comments[orchid.genus])
        
        # Default commentary if no specific traits
        if not comments:
            comments.append("A fascinating specimen with its own unique charm!")
        
        # Combine with enthusiasm
        return " ".join(comments[:2])  # Limit to 2 comments to keep it concise
    
    def _current_season(self):
        """Get current season"""
        month = datetime.now().month
        if month in [12, 1, 2]:
            return "winter"
        elif month in [3, 4, 5]:
            return "spring"
        elif month in [6, 7, 8]:
            return "summer"
        else:
            return "fall"
    
    def _get_theme_title(self, theme):
        """Get display title for theme"""
        titles = {
            'random': "My Personal Favorites",
            'beginner_friendly': "Perfect for Beginners", 
            'exotic_beauties': "Exotic Beauties",
            'native_treasures': "Native Treasures",
            'seasonal_highlights': f"{self._current_season().title()} Highlights",
            'rare_specimens': "Rare Specimens"
        }
        return titles.get(theme, "Orchid Selection")
    
    def _get_curator_note(self, theme, count):
        """Get Professor BloomBot's curator note"""
        notes = [
            f"I've carefully selected these {count} orchids just for you!",
            f"Each of these {count} specimens has something special to offer.",
            f"I'm excited to share these {count} remarkable orchids with you!",
            f"These {count} orchids represent some of nature's finest artistry.",
            f"I hope you find these {count} orchids as fascinating as I do!"
        ]
        return random.choice(notes)
    
    def _get_fallback_selection(self):
        """Fallback selection if database query fails"""
        return {
            'theme': 'fallback',
            'title': 'Coming Soon',
            'description': 'I\'m preparing a wonderful selection for you!',
            'orchids': [],
            'greeting': random.choice(self.greeting_phrases),
            'prompt': "Please check back soon for curated selections!",
            'curator_note': "I'm working on something special for you!"
        }

# Initialize Professor BloomBot
professor_bloombot = ProfessorBloomBot()

@bloombot_curator_bp.route('/bloombot/curator')
def curator_page():
    """Professor BloomBot curator page"""
    theme = request.args.get('theme', 'random')
    
    # Track visit for analytics
    user_id = session.get('user_id', 'visitor')
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type='bloombot_curator_visit',
            points_earned=2,
            details=json.dumps({'theme': theme, 'visit_time': datetime.now().isoformat()})
        )
        db.session.add(activity)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error tracking curator visit: {e}")
    
    # Get curated selection
    selection = professor_bloombot.get_curated_selection(theme)
    
    return render_template('bloombot/curator.html', 
                         selection=selection,
                         available_themes=['random', 'beginner_friendly', 'exotic_beauties', 
                                         'native_treasures', 'seasonal_highlights', 'rare_specimens'])

@bloombot_curator_bp.route('/api/bloombot/feedback', methods=['POST'])
def submit_feedback():
    """Submit feedback on curated orchids"""
    try:
        data = request.get_json()
        orchid_id = data.get('orchid_id')
        feedback_type = data.get('feedback_type')  # 'love', 'like', 'interesting', 'suggestion'
        feedback_text = data.get('feedback_text', '').strip()
        suggestion = data.get('suggestion', '').strip()
        
        user_id = session.get('user_id', 'visitor')
        
        # Validate inputs
        if not orchid_id or not feedback_type:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Check if orchid exists
        orchid = OrchidRecord.query.get(orchid_id)
        if not orchid:
            return jsonify({'success': False, 'error': 'Orchid not found'}), 404
        
        # Determine points based on feedback type
        points = 1  # Base point for any valid feedback
        if feedback_text and len(feedback_text) > 10:
            points += 1  # Bonus for detailed feedback
        if suggestion and len(suggestion) > 20:
            points += 2  # Extra bonus for improvement suggestions
        
        # Save feedback activity
        feedback_data = {
            'orchid_id': orchid_id,
            'orchid_name': orchid.display_name,
            'feedback_type': feedback_type,
            'feedback_text': feedback_text,
            'suggestion': suggestion,
            'submission_time': datetime.now().isoformat()
        }
        
        activity = UserActivity(
            user_id=user_id,
            activity_type='orchid_feedback',
            points_earned=points,
            details=json.dumps(feedback_data)
        )
        db.session.add(activity)
        db.session.commit()
        
        # Update orchid view count
        orchid.view_count = (orchid.view_count or 0) + 1
        db.session.commit()
        
        # Generate response message
        response_messages = {
            'love': f"Wonderful! I'm delighted you love {orchid.display_name}!",
            'like': f"Great to hear you like {orchid.display_name}!",
            'interesting': f"I'm pleased you find {orchid.display_name} interesting!",
            'suggestion': f"Thank you for your thoughtful suggestions about {orchid.display_name}!"
        }
        
        message = response_messages.get(feedback_type, "Thank you for your feedback!")
        if points > 1:
            message += f" You've earned {points} points for your detailed input!"
        
        return jsonify({
            'success': True,
            'message': message,
            'points_earned': points,
            'orchid_name': orchid.display_name
        })
        
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        return jsonify({'success': False, 'error': 'Unable to submit feedback'}), 500

@bloombot_curator_bp.route('/api/bloombot/selection/<theme>')
def get_themed_selection(theme):
    """API endpoint to get themed orchid selection"""
    try:
        selection = professor_bloombot.get_curated_selection(theme)
        return jsonify({'success': True, 'selection': selection})
    except Exception as e:
        logger.error(f"Error getting themed selection: {e}")
        return jsonify({'success': False, 'error': 'Unable to load selection'}), 500

@bloombot_curator_bp.route('/bloombot/feedback-summary')
def feedback_summary():
    """Show feedback summary for admins"""
    # Check if user is admin
    if not session.get('is_admin', False):
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('index'))
    
    try:
        # Get recent feedback
        cutoff_date = datetime.now() - timedelta(days=30)
        feedback_activities = (UserActivity.query
                             .filter(UserActivity.activity_type == 'orchid_feedback')
                             .filter(UserActivity.timestamp >= cutoff_date)
                             .order_by(UserActivity.timestamp.desc())
                             .limit(100)
                             .all())
        
        # Process feedback data
        feedback_summary_data = {
            'total_feedback': len(feedback_activities),
            'total_points_awarded': sum(a.points_earned for a in feedback_activities),
            'feedback_by_type': {},
            'recent_suggestions': [],
            'most_popular_orchids': {},
            'user_engagement': {}
        }
        
        for activity in feedback_activities:
            try:
                details = json.loads(activity.details) if activity.details else {}
                
                # Count by feedback type
                feedback_type = details.get('feedback_type', 'unknown')
                if feedback_type not in feedback_summary_data['feedback_by_type']:
                    feedback_summary_data['feedback_by_type'][feedback_type] = 0
                feedback_summary_data['feedback_by_type'][feedback_type] += 1
                
                # Collect suggestions
                if details.get('suggestion'):
                    feedback_summary_data['recent_suggestions'].append({
                        'orchid_name': details.get('orchid_name', 'Unknown'),
                        'suggestion': details.get('suggestion'),
                        'date': activity.timestamp.strftime('%Y-%m-%d'),
                        'user_id': activity.user_id
                    })
                
                # Track popular orchids
                orchid_name = details.get('orchid_name', 'Unknown')
                if orchid_name not in feedback_summary_data['most_popular_orchids']:
                    feedback_summary_data['most_popular_orchids'][orchid_name] = 0
                feedback_summary_data['most_popular_orchids'][orchid_name] += 1
                
                # Track user engagement
                user_id = activity.user_id
                if user_id not in feedback_summary_data['user_engagement']:
                    feedback_summary_data['user_engagement'][user_id] = 0
                feedback_summary_data['user_engagement'][user_id] += activity.points_earned
                
            except Exception as e:
                logger.error(f"Error processing feedback activity: {e}")
        
        # Sort data
        feedback_summary_data['recent_suggestions'] = feedback_summary_data['recent_suggestions'][:20]
        feedback_summary_data['most_popular_orchids'] = dict(sorted(
            feedback_summary_data['most_popular_orchids'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:10])
        
        return render_template('admin/feedback_summary.html', 
                             summary=feedback_summary_data,
                             activities=feedback_activities[:50])
        
    except Exception as e:
        logger.error(f"Error loading feedback summary: {e}")
        flash('Error loading feedback summary', 'error')
        return redirect(url_for('index'))

logger.info("Professor BloomBot Curator System initialized successfully")