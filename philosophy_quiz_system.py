"""
Philosophy Quiz System for Five Cities Orchid Society
Integrates with existing badge and leaderboard systems
"""

import logging
from datetime import datetime
from flask import render_template, request, jsonify, session, redirect, url_for, flash
from app import app, db
from models import User, UserBadge, UserActivity, GameScore
from widget_integration_hub import widget_hub
import json

logger = logging.getLogger(__name__)

class PhilosophyQuizEngine:
    """Core engine for the orchid philosophy quiz"""
    
    def __init__(self):
        # Complete 29-question philosophy quiz based on your Google Form structure
        self.questions = [
            {
                'id': 1,
                'question': "You walk into a greenhouse. What draws your eye first?",
                'options': {
                    'A': "The wild, unkempt corner where orchids grow free",
                    'B': "The perfectly arranged display with artistic lighting", 
                    'C': "The empty spaces where beauty once bloomed",
                    'D': "The classic setup, time-tested and reliable"
                }
            },
            {
                'id': 2,
                'question': "When your orchid finally blooms, you...",
                'options': {
                    'A': "Feel proud—this success belongs to you",
                    'B': "Share photos with everyone you know",
                    'C': "Follow the community guidelines for proper care",
                    'D': "Appreciate the fleeting moment without attachment"
                }
            },
            {
                'id': 3,
                'question': "What's your approach to choosing new orchids?",
                'options': {
                    'A': "Hunt for the rarest, most perfect specimen",
                    'B': "Pick what works reliably in your conditions",
                    'C': "Research thoroughly, organize by classification",
                    'D': "Choose what brings you immediate joy and fragrance"
                }
            },
            {
                'id': 4,
                'question': "Your orchid gets a bacterial infection. You...",
                'options': {
                    'A': "Research the best treatment for your collection",
                    'B': "Ask the community for help and advice",
                    'C': "Follow established wisdom from experienced growers",
                    'D': "Accept that some flowers are meant to fade"
                }
            },
            {
                'id': 5,
                'question': "How do you feel about following orchid care rules?",
                'options': {
                    'A': "Old wisdom exists for good reasons",
                    'B': "Rules are meant to be creatively bent",
                    'C': "Test everything—even expert advice",
                    'D': "Focus on what serves your goals"
                }
            },
            {
                'id': 6,
                'question': "What motivates your orchid growing?",
                'options': {
                    'A': "Creating harmony between tradition and innovation",
                    'B': "Solving problems and learning what works",
                    'C': "Finding peace through patient cultivation",
                    'D': "Questioning assumptions and discovering truth"
                }
            },
            {
                'id': 7,
                'question': "Your ideal orchid space would be...",
                'options': {
                    'A': "An artistic gallery showcasing form and beauty",
                    'B': "A sensory paradise of color and fragrance",
                    'C': "A quiet space accepting both bloom and decay",
                    'D': "A natural sanctuary connecting you to something greater"
                }
            },
            {
                'id': 8,
                'question': "When someone asks for orchid advice, you...",
                'options': {
                    'A': "Question their assumptions and dig deeper",
                    'B': "Offer enthusiastic help and encouragement",
                    'C': "Share what has worked best for you",
                    'D': "Suggest they find their own patient path"
                }
            },
            {
                'id': 9,
                'question': "What's your relationship with orchid failures?",
                'options': {
                    'A': "Test different approaches until you succeed",
                    'B': "Honor the lineage of growers who came before",
                    'C': "See them as part of a larger spiritual journey",
                    'D': "Accept them with calm understanding"
                }
            },
            {
                'id': 10,
                'question': "Why do orchids matter to you?",
                'options': {
                    'A': "They reflect your personal achievement and taste",
                    'B': "They connect you to a community of fellow enthusiasts",
                    'C': "They challenge you to think and question",
                    'D': "They teach balance, respect, and proper order"
                }
            },
            {
                'id': 11,
                'question': "When you see a rare orchid you can't afford, you...",
                'options': {
                    'A': "Accept that some beauty is beyond reach",
                    'B': "Find creative ways to experience it anyway",
                    'C': "Research everything about it to understand its perfection",
                    'D': "Ask experienced growers for their wisdom"
                }
            },
            {
                'id': 12,
                'question': "Your ideal orchid mentor would be...",
                'options': {
                    'A': "Someone who questions every conventional method",
                    'B': "A generous soul who shares freely with others",
                    'C': "A master who embodies traditional wisdom",
                    'D': "Someone focused on achieving personal excellence"
                }
            },
            {
                'id': 13,
                'question': "If you discovered a new orchid species, you would...",
                'options': {
                    'A': "Document it precisely and scientifically",
                    'B': "Share the discovery with the whole community",
                    'C': "Contemplate its place in the greater mystery of nature",
                    'D': "Focus on how to successfully cultivate it"
                }
            },
            {
                'id': 14,
                'question': "When orchid trends change, you...",
                'options': {
                    'A': "Stick with what has worked for generations",
                    'B': "Ignore trends and grow what brings you joy",
                    'C': "Question whether the trend has real merit",
                    'D': "Adapt if the new approach serves your goals"
                }
            },
            {
                'id': 15,
                'question': "Your greenhouse organization reflects...",
                'options': {
                    'A': "Systematic classification and clear labeling",
                    'B': "Harmonious balance between all elements",
                    'C': "A living artwork of form and beauty",
                    'D': "Practical efficiency and what works best"
                }
            },
            {
                'id': 16,
                'question': "When facing a difficult orchid rescue, you...",
                'options': {
                    'A': "Channel all your energy into saving it",
                    'B': "Accept whatever outcome comes with peace",
                    'C': "Try every method until something works",
                    'D': "Research the traditional rescue techniques"
                }
            },
            {
                'id': 17,
                'question': "The most rewarding part of orchid growing is...",
                'options': {
                    'A': "The sensory pleasure of blooms and fragrance",
                    'B': "The inner peace it brings to your life",
                    'C': "The knowledge you gain about nature",
                    'D': "The joy of sharing with others"
                }
            },
            {
                'id': 18,
                'question': "When you see 'perfect' orchids at shows, you feel...",
                'options': {
                    'A': "Inspired to achieve that same perfection",
                    'B': "Grateful for the fleeting beauty",
                    'C': "Curious about the growing techniques used",
                    'D': "Appreciation for the artistic presentation"
                }
            },
            {
                'id': 19,
                'question': "Your approach to orchid photography is...",
                'options': {
                    'A': "Document every bloom as a precious moment",
                    'B': "Capture the artistic beauty and composition",
                    'C': "Record scientific details and characteristics",
                    'D': "Share the joy with others through images"
                }
            },
            {
                'id': 20,
                'question': "When an orchid blooms out of season, you...",
                'options': {
                    'A': "Marvel at nature's mysterious ways",
                    'B': "Research what environmental factors caused it",
                    'C': "Enjoy the unexpected gift without overthinking",
                    'D': "Make notes to replicate the conditions"
                }
            },
            {
                'id': 21,
                'question': "Your biggest orchid growing fear is...",
                'options': {
                    'A': "Never achieving the perfection you seek",
                    'B': "Losing the peace orchids bring to your life",
                    'C': "Running out of space for your growing collection",
                    'D': "Making mistakes that harm your plants"
                }
            },
            {
                'id': 22,
                'question': "When teaching someone about orchids, you emphasize...",
                'options': {
                    'A': "Questioning assumptions and testing everything",
                    'B': "Sharing knowledge generously and building community",
                    'C': "Respecting traditional methods and mentors",
                    'D': "Finding what works for their unique situation"
                }
            },
            {
                'id': 23,
                'question': "The orchid that means most to you is...",
                'options': {
                    'A': "The rarest one you've managed to acquire",
                    'B': "One given to you by a dear friend",
                    'C': "The first one that ever bloomed for you",
                    'D': "One you rescued and brought back to health"
                }
            },
            {
                'id': 24,
                'question': "When you see orchids in nature, you feel...",
                'options': {
                    'A': "Deep spiritual connection to something greater",
                    'B': "Curiosity about their natural growing conditions",
                    'C': "Awe at their perfect adaptation and form",
                    'D': "Peaceful acceptance of nature's rhythm"
                }
            },
            {
                'id': 25,
                'question': "Your orchid budget reflects...",
                'options': {
                    'A': "Investment in your personal collection goals",
                    'B': "Practical spending on what you need most",
                    'C': "Resources for sharing and helping others",
                    'D': "Careful research before every purchase"
                }
            },
            {
                'id': 26,
                'question': "When orchid experts disagree on care methods, you...",
                'options': {
                    'A': "Test different approaches to find what works",
                    'B': "Follow the wisdom of established authorities",
                    'C': "Question the underlying assumptions of both",
                    'D': "Seek harmony between the different viewpoints"
                }
            },
            {
                'id': 27,
                'question': "The greatest orchid lesson you've learned is...",
                'options': {
                    'A': "Patience—everything happens in its own time",
                    'B': "Beauty is fleeting and should be treasured",
                    'C': "Knowledge grows through careful observation",
                    'D': "Joy multiplies when shared with others"
                }
            },
            {
                'id': 28,
                'question': "Your dream orchid experience would be...",
                'options': {
                    'A': "Finding the perfect specimen you've always sought",
                    'B': "Sharing a magical bloom moment with loved ones",
                    'C': "Discovering something entirely new about orchids",
                    'D': "Achieving perfect harmony in your growing space"
                }
            },
            {
                'id': 29,
                'question': "When people ask why you grow orchids, you say...",
                'options': {
                    'A': "They connect me to the mystery of life itself",
                    'B': "They satisfy my need to understand and learn",
                    'C': "They bring beauty and joy into every day",
                    'D': "They help me create something meaningful to share"
                }
            }
        ]
        
        # Complete 29-question scoring key mapping to all 14 philosophies
        self.scoring_key = {
            1: {'A': 'Cynicism', 'B': 'Renaissance Humanism', 'C': 'Nihilism', 'D': 'Traditionalism'},
            2: {'A': 'Egoism', 'B': 'Altruism', 'C': 'Confucianism', 'D': 'Nihilism'},
            3: {'A': 'Idealism', 'B': 'Pragmatism', 'C': 'Aristotelian', 'D': 'Epicureanism'},
            4: {'A': 'Egoism', 'B': 'Altruism', 'C': 'Confucianism', 'D': 'Nihilism'},
            5: {'A': 'Traditionalism', 'B': 'Cynicism', 'C': 'Skepticism', 'D': 'Egoism'},
            6: {'A': 'Confucianism', 'B': 'Pragmatism', 'C': 'Stoicism', 'D': 'Skepticism'},
            7: {'A': 'Renaissance Humanism', 'B': 'Epicureanism', 'C': 'Nihilism', 'D': 'Transcendentalism'},
            8: {'A': 'Skepticism', 'B': 'Altruism', 'C': 'Egoism', 'D': 'Stoicism'},
            9: {'A': 'Pragmatism', 'B': 'Traditionalism', 'C': 'Transcendentalism', 'D': 'Stoicism'},
            10: {'A': 'Egoism', 'B': 'Altruism', 'C': 'Skepticism', 'D': 'Confucianism'},
            # Additional questions 11-29 for balanced philosophy representation
            11: {'A': 'Nihilism', 'B': 'Cynicism', 'C': 'Idealism', 'D': 'Traditionalism'},
            12: {'A': 'Skepticism', 'B': 'Altruism', 'C': 'Traditionalism', 'D': 'Egoism'},
            13: {'A': 'Aristotelian', 'B': 'Altruism', 'C': 'Transcendentalism', 'D': 'Pragmatism'},
            14: {'A': 'Traditionalism', 'B': 'Epicureanism', 'C': 'Skepticism', 'D': 'Pragmatism'},
            15: {'A': 'Aristotelian', 'B': 'Confucianism', 'C': 'Renaissance Humanism', 'D': 'Pragmatism'},
            16: {'A': 'Egoism', 'B': 'Stoicism', 'C': 'Pragmatism', 'D': 'Traditionalism'},
            17: {'A': 'Epicureanism', 'B': 'Stoicism', 'C': 'Aristotelian', 'D': 'Altruism'},
            18: {'A': 'Idealism', 'B': 'Nihilism', 'C': 'Skepticism', 'D': 'Renaissance Humanism'},
            19: {'A': 'Nihilism', 'B': 'Renaissance Humanism', 'C': 'Aristotelian', 'D': 'Altruism'},
            20: {'A': 'Transcendentalism', 'B': 'Skepticism', 'C': 'Epicureanism', 'D': 'Pragmatism'},
            21: {'A': 'Idealism', 'B': 'Stoicism', 'C': 'Egoism', 'D': 'Confucianism'},
            22: {'A': 'Skepticism', 'B': 'Altruism', 'C': 'Traditionalism', 'D': 'Pragmatism'},
            23: {'A': 'Egoism', 'B': 'Altruism', 'C': 'Stoicism', 'D': 'Pragmatism'},
            24: {'A': 'Transcendentalism', 'B': 'Aristotelian', 'C': 'Idealism', 'D': 'Stoicism'},
            25: {'A': 'Egoism', 'B': 'Pragmatism', 'C': 'Altruism', 'D': 'Skepticism'},
            26: {'A': 'Pragmatism', 'B': 'Traditionalism', 'C': 'Skepticism', 'D': 'Confucianism'},
            27: {'A': 'Stoicism', 'B': 'Nihilism', 'C': 'Aristotelian', 'D': 'Altruism'},
            28: {'A': 'Idealism', 'B': 'Altruism', 'C': 'Skepticism', 'D': 'Confucianism'},
            29: {'A': 'Transcendentalism', 'B': 'Aristotelian', 'C': 'Epicureanism', 'D': 'Altruism'}
        }
        
        # Philosophy descriptions and badges
        self.philosophies = {
            'Epicureanism': {
                'badge_name': 'Being in Bloom',
                'badge_emoji': '🌺',
                'description': 'Your orchids are a garden of joy. Each bloom is a reminder that life\'s greatest pleasures are often the simplest: fragrance, color, the quiet moment of opening a new flower. You savor orchids with mindful delight.',
                'growing_style': 'Delight in sensory joy',
                'badge_image': 'being_in_bloom.png',
                'drive_id': '109qscgJSKo0M1FlRGsZzn81F5_0ge9BX'
            },
            'Stoicism': {
                'badge_name': 'Enduring Bloom', 
                'badge_emoji': '🪷',
                'description': 'You let orchids follow their own rhythm. You embrace what comes: the withered leaf, the late spike, the sudden gift of blossoms. Peace in tending, not controlling.',
                'growing_style': 'Strength through cycles',
                'badge_image': 'enduring_bloom.png',
                'drive_id': '1QUBaM3AJfvhvfTS9qkDIxnIaCFY8AE4a'
            },
            'Transcendentalism': {
                'badge_name': 'Moonlight Reverie',
                'badge_emoji': '🌙', 
                'description': 'You sense the spirit in nature. Orchids are messengers of connection — roots in mystery, blossoms in wonder.',
                'growing_style': 'Spiritual harmony with nature',
                'badge_image': 'moonlight_reverie.png',
                'drive_id': '16vKYdUk8JnBcKEx27sH5TkynPsqLiwXN'
            },
            'Idealism': {
                'badge_name': 'Vision Vine',
                'badge_emoji': '🌿',
                'description': 'You chase the perfect bloom — rare, exquisite, inspiring. Orchids give you a vision of perfection worth striving for.',
                'growing_style': 'Chasing perfection and ideals',
                'badge_image': 'vision_vine.png',
                'drive_id': '11T52NzspBhfu8IU_Ulw-ApG-fXKnIh_S'
            },
            'Confucianism': {
                'badge_name': 'Harmony Orchid',
                'badge_emoji': '⚖️',
                'description': 'You cultivate harmony: light and shade, water and rest, discipline and care. Orchids reflect your respect for tradition, mentors, and community.',
                'growing_style': 'Responsibility, respect, and order',
                'badge_image': 'harmony_orchid.png'
            },
            'Egoism': {
                'badge_name': 'Radiant Flame Orchid',
                'badge_emoji': '🔥', 
                'description': 'Your collection is a mirror of your taste and triumphs. You grow for the joy it brings you — and your orchids glow in that certainty.',
                'growing_style': 'Self-driven brilliance',
                'badge_image': 'radiant_flame.png'
            },
            'Nihilism': {
                'badge_name': 'Vanishing Bloom',
                'badge_emoji': '🖤',
                'description': 'You see the beauty in impermanence. Blooms fade; that is their truth. You do not cling — and yet you marvel every time one returns.',
                'growing_style': 'Beauty in impermanence',
                'badge_image': 'vanishing_bloom.png'
            },
            'Renaissance Humanism': {
                'badge_name': 'Orchid Muse',
                'badge_emoji': '🎨',
                'description': 'Your orchids are art. You admire symmetry, form, and grace — every flower a masterpiece, devotion worthy of beauty.',
                'growing_style': 'Art, form and symmetry',
                'badge_image': 'orchid_muse.png'
            },
            'Pragmatism': {
                'badge_name': 'Grounded Root',
                'badge_emoji': '🌱',
                'description': 'You test, adapt, and do what works. Your orchids thrive on curiosity as much as water and light.',
                'growing_style': 'Practical wisdom',
                'badge_image': 'grounded_root.png'
            },
            'Skepticism': {
                'badge_name': 'Veil Orchid',
                'badge_emoji': '🕵️',
                'description': 'You question, test, and refine. Your orchids thrive on curiosity as much as water and light.',
                'growing_style': 'Questioning pursuit of truth',
                'badge_image': 'veil_orchid.png'
            },
            'Traditionalism': {
                'badge_name': 'Legacy Bloom',
                'badge_emoji': '📜',
                'description': 'Your orchids carry stories — divisions handed down, journals kept, lessons preserved. You honor the lineage of growers.',
                'growing_style': 'Honor and lineage',
                'badge_image': 'legacy_bloom.png'
            },
            'Cynicism': {
                'badge_name': 'Wild Sprout',
                'badge_emoji': '🌵',
                'description': 'You refuse to be boxed by rules. If it grows in a bottle, a log, or a teacup — you smile and let it bloom outside the lines.',
                'growing_style': 'Breaking convention',
                'badge_image': 'wild_sprout.png'
            },
            'Aristotelian': {
                'badge_name': 'Ordered Bloom',
                'badge_emoji': '🔢',
                'description': 'You delight in names, order, and clarity. Each tag, a piece of a larger pattern. Wisdom begins with seeing what a thing is.',
                'growing_style': 'Knowledge through order',
                'badge_image': 'ordered_bloom.png'
            },
            'Altruism': {
                'badge_name': 'Gifted Orchid',
                'badge_emoji': '🎁',
                'description': 'You share joy through orchids. Your plants are gifts of spirit, spreading beauty and wisdom to others.',
                'growing_style': 'Sharing joy and wisdom',
                'badge_image': 'gifted_orchid.png'
            }
        }
        
        # Tie-breaker priority
        self.tie_priority = [
            'Epicureanism', 'Stoicism', 'Confucianism', 'Egoism', 'Nihilism',
            'Renaissance Humanism', 'Pragmatism', 'Transcendentalism', 'Skepticism',
            'Traditionalism', 'Cynicism', 'Idealism', 'Aristotelian', 'Altruism'
        ]
    
    def calculate_philosophy_result(self, answers):
        """Calculate philosophy result from quiz answers"""
        philosophy_scores = {}
        
        for question_id, answer in answers.items():
            if question_id in self.scoring_key and answer in self.scoring_key[question_id]:
                philosophy = self.scoring_key[question_id][answer]
                philosophy_scores[philosophy] = philosophy_scores.get(philosophy, 0) + 1
        
        # Find winner (handle ties with priority system)
        if not philosophy_scores:
            return 'Epicureanism'  # Default fallback
            
        max_score = max(philosophy_scores.values())
        tied_philosophies = [p for p, score in philosophy_scores.items() if score == max_score]
        
        # Use tie-breaker priority
        for philosophy in self.tie_priority:
            if philosophy in tied_philosophies:
                return philosophy
                
        return tied_philosophies[0]  # Final fallback
    
    def award_philosophy_badge(self, user_id, philosophy):
        """Award philosophy badge to user and update leaderboard"""
        try:
            philosophy_data = self.philosophies.get(philosophy, {})
            
            # Create badge data
            badge_data = {
                'philosophy': philosophy,
                'badge_name': philosophy_data.get('badge_name', f'{philosophy} Grower'),
                'badge_emoji': philosophy_data.get('badge_emoji', '🌺'),
                'description': philosophy_data.get('description', 'A unique orchid philosophy'),
                'growing_style': philosophy_data.get('growing_style', 'Individual approach'),
                'earned_date': datetime.now().isoformat(),
                'quiz_version': '1.0'
            }
            
            # Check if user already has this badge type
            existing_badge = UserBadge.query.filter_by(
                user_id=user_id,
                badge_type='philosophy_quiz',
                badge_key=philosophy
            ).first()
            
            if not existing_badge:
                # Award new badge
                new_badge = UserBadge()
                new_badge.user_id = user_id
                new_badge.badge_type = 'philosophy_quiz'
                new_badge.badge_key = philosophy
                new_badge.badge_data = badge_data
                db.session.add(new_badge)
                
                # Record activity for leaderboard
                activity = UserActivity()
                activity.user_id = user_id
                activity.activity_type = 'philosophy_quiz_completed'
                activity.points_earned = 50  # Philosophy quiz completion points
                activity.details = json.dumps({
                    'philosophy': philosophy,
                    'badge_name': badge_data['badge_name'],
                    'quiz_version': '1.0'
                })
                db.session.add(activity)
                
                # Record game score
                game_score = GameScore()
                game_score.user_id = user_id
                game_score.game_type = 'philosophy_quiz'
                game_score.difficulty = 'standard'
                game_score.score = 100  # Perfect completion score
                game_score.time_taken = 0  # We'll track this separately if needed
                game_score.moves_made = 29  # 29 questions answered
                game_score.game_metadata = badge_data
                db.session.add(game_score)
                
                db.session.commit()
                
                logger.info(f"✅ Philosophy badge '{philosophy}' awarded to user {user_id}")
                return True
            else:
                logger.info(f"User {user_id} already has {philosophy} philosophy badge")
                return False
                
        except Exception as e:
            logger.error(f"Error awarding philosophy badge: {e}")
            db.session.rollback()
            return False

# Initialize quiz engine
quiz_engine = PhilosophyQuizEngine()

@app.route('/philosophy-quiz')
def philosophy_quiz():
    """Main philosophy quiz widget page"""
    try:
        # Track widget usage
        widget_hub.update_widget_context('philosophy_quiz', {
            'action': 'view',
            'timestamp': datetime.now().isoformat()
        })
        
        # Get user's existing philosophy if they're logged in
        existing_philosophy = None
        if 'user_id' in session:  # Basic session check
            try:
                existing_badge = UserBadge.query.filter_by(
                    user_id=session['user_id'],
                    badge_type='philosophy_quiz'
                ).first()
                if existing_badge:
                    existing_philosophy = existing_badge.badge_data
            except:
                pass
        
        return render_template('widgets/philosophy_quiz.html',
                             questions=quiz_engine.questions,
                             existing_philosophy=existing_philosophy)
                             
    except Exception as e:
        logger.error(f"Philosophy quiz error: {e}")
        return render_template('widgets/philosophy_quiz.html',
                             questions=quiz_engine.questions,
                             existing_philosophy=None)

@app.route('/philosophy-quiz/submit', methods=['POST'])
def submit_philosophy_quiz():
    """Process quiz submission and award badge"""
    try:
        # Get answers from form
        answers = {}
        for i in range(1, 30):  # Changed from 11 to 30 for 29 questions
            answer = request.form.get(f'question_{i}')
            if answer:
                answers[i] = answer
        
        if len(answers) < 29:  # Changed from 10 to 29
            flash('Please answer all questions to get your philosophy result', 'error')
            return redirect(url_for('philosophy_quiz'))
        
        # Calculate philosophy result
        philosophy = quiz_engine.calculate_philosophy_result(answers)
        philosophy_data = quiz_engine.philosophies.get(philosophy, {})
        
        # Store result in session for immediate display
        session['quiz_result'] = {
            'philosophy': philosophy,
            'philosophy_data': philosophy_data,
            'answers': answers,
            'completed_at': datetime.now().isoformat()
        }
        
        # Award badge if user is logged in
        badge_awarded = False
        if 'user_id' in session:
            badge_awarded = quiz_engine.award_philosophy_badge(session['user_id'], philosophy)
        
        # Track completion activity
        widget_hub.update_widget_context('philosophy_quiz', {
            'action': 'complete',
            'philosophy': philosophy,
            'badge_awarded': badge_awarded
        })
        
        return redirect(url_for('philosophy_quiz_result'))
        
    except Exception as e:
        logger.error(f"Quiz submission error: {e}")
        flash('There was an error processing your quiz. Please try again.', 'error')
        return redirect(url_for('philosophy_quiz'))

@app.route('/philosophy-quiz/result')
def philosophy_quiz_result():
    """Display quiz results with badge"""
    quiz_result = session.get('quiz_result')
    
    if not quiz_result:
        flash('No quiz result found. Please take the quiz first.', 'info')
        return redirect(url_for('philosophy_quiz'))
    
    return render_template('widgets/philosophy_quiz_result.html',
                         result=quiz_result)

@app.route('/api/philosophy-leaderboard')
def philosophy_leaderboard_api():
    """API endpoint for philosophy quiz leaderboard data"""
    try:
        # Get philosophy distribution
        philosophy_counts = {}
        philosophy_badges = UserBadge.query.filter_by(badge_type='philosophy_quiz').all()
        
        for badge in philosophy_badges:
            philosophy = badge.badge_data.get('philosophy', 'Unknown')
            philosophy_counts[philosophy] = philosophy_counts.get(philosophy, 0) + 1
        
        # Format for display
        leaderboard_data = []
        for philosophy, count in sorted(philosophy_counts.items(), key=lambda x: x[1], reverse=True):
            philosophy_info = quiz_engine.philosophies.get(philosophy, {})
            leaderboard_data.append({
                'philosophy': philosophy,
                'badge_name': philosophy_info.get('badge_name', philosophy),
                'badge_emoji': philosophy_info.get('badge_emoji', '🌺'),
                'member_count': count,
                'growing_style': philosophy_info.get('growing_style', 'Unique approach')
            })
        
        return jsonify({
            'success': True,
            'total_participants': sum(philosophy_counts.values()),
            'philosophy_distribution': leaderboard_data,
            'most_popular': leaderboard_data[0] if leaderboard_data else None
        })
        
    except Exception as e:
        logger.error(f"Philosophy leaderboard API error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/widgets/philosophy-quiz-mini')
def philosophy_quiz_mini_widget():
    """Mini widget version for embedding"""
    try:
        # Get philosophy distribution for display
        philosophy_counts = {}
        philosophy_badges = UserBadge.query.filter_by(badge_type='philosophy_quiz').all()
        
        for badge in philosophy_badges:
            philosophy = badge.badge_data.get('philosophy', 'Unknown')
            philosophy_counts[philosophy] = philosophy_counts.get(philosophy, 0) + 1
        
        total_participants = sum(philosophy_counts.values())
        
        # Get top 3 philosophies
        top_philosophies = []
        for philosophy, count in sorted(philosophy_counts.items(), key=lambda x: x[1], reverse=True)[:3]:
            philosophy_info = quiz_engine.philosophies.get(philosophy, {})
            top_philosophies.append({
                'philosophy': philosophy,
                'badge_name': philosophy_info.get('badge_name', philosophy),
                'badge_emoji': philosophy_info.get('badge_emoji', '🌺'),
                'count': count,
                'percentage': round((count / total_participants * 100), 1) if total_participants > 0 else 0
            })
        
        return render_template('widgets/philosophy_quiz_mini.html',
                             total_participants=total_participants,
                             top_philosophies=top_philosophies)
                             
    except Exception as e:
        logger.error(f"Philosophy mini widget error: {e}")
        return render_template('widgets/philosophy_quiz_mini.html',
                             total_participants=0,
                             top_philosophies=[])

# Initialize widget integration
try:
    # Track widget registration for integration
    widget_hub.update_widget_context('philosophy_quiz', {
        'action': 'system_init',
        'widget_type': 'philosophy_quiz',
        'routes': ['/philosophy-quiz', '/widgets/philosophy-quiz-mini', '/api/philosophy-leaderboard']
    })
    logger.info("✅ Philosophy Quiz widget registered successfully")
except Exception as e:
    logger.warning(f"Widget integration not available: {e}")