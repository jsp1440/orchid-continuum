from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import random
import json

# Create blueprint for Orchid Trivia
orchid_trivia = Blueprint('orchid_trivia', __name__, url_prefix='/widgets/orchid-trivia')

# Comprehensive trivia database with difficulty levels
TRIVIA_DATABASE = [
    # Easy Level (10-15 points)
    {
        "category": "Basic Knowledge",
        "difficulty": "easy",
        "question": "What is the most common orchid found in grocery stores?",
        "options": ["Phalaenopsis", "Cattleya", "Dendrobium", "Oncidium"],
        "correct": 0,
        "explanation": "Phalaenopsis, also called 'Moth Orchids', are the most popular orchids sold commercially.",
        "points": 10,
        "image": "images/phalaenopsis_moth_orchid.jpg"
    },
    {
        "category": "Colors",
        "difficulty": "easy", 
        "question": "Which color do orchids NOT naturally produce?",
        "options": ["Blue", "Purple", "White", "Yellow"],
        "correct": 0,
        "explanation": "True blue orchids don't exist naturally - blue orchids are typically dyed.",
        "points": 10,
        "image": "images/blue_orchid_dyed.jpg"
    },
    {
        "category": "Growing",
        "difficulty": "easy",
        "question": "What do most orchids grow on in nature?",
        "options": ["Soil", "Trees", "Rocks", "Water"],
        "correct": 1,
        "explanation": "Most orchids are epiphytes, meaning they grow on trees and get nutrients from the air and rain.",
        "points": 10,
        "image": "images/epiphyte_orchid_tree.jpg"
    },
    
    # Medium Level (20-25 points)
    {
        "category": "Anatomy",
        "difficulty": "medium",
        "question": "What is the specialized lip petal of an orchid called?",
        "options": ["Labellum", "Column", "Pollinia", "Sepals"],
        "correct": 0,
        "explanation": "The labellum is the modified lip petal that often serves as a landing platform for pollinators.",
        "points": 20,
        "image": "images/orchid_labellum_anatomy.jpg"
    },
    {
        "category": "Biology",
        "difficulty": "medium",
        "question": "What are keikis in orchid growing?",
        "options": ["Diseases", "Baby plants", "Fertilizers", "Pot types"],
        "correct": 1,
        "explanation": "Keiki is Hawaiian for 'baby' - these are small plantlets that grow on the mother plant.",
        "points": 20,
        "image": "images/orchid_keiki_baby.jpg"
    },
    {
        "category": "History",
        "difficulty": "medium",
        "question": "Which scientist wrote a famous book about orchid pollination?",
        "options": ["Darwin", "Mendel", "Linnaeus", "Watson"],
        "correct": 0,
        "explanation": "Charles Darwin wrote 'On the Various Contrivances by which British and Foreign Orchids are Fertilised by Insects' in 1862.",
        "points": 25,
        "image": "images/darwin_orchid_book.jpg"
    },
    
    # Hard Level (30-40 points)
    {
        "category": "Advanced Botany",
        "difficulty": "hard",
        "question": "What is the column in an orchid flower?",
        "options": ["A support structure", "Fused stamens and pistils", "The stem", "A type of root"],
        "correct": 1,
        "explanation": "The column is the unique reproductive structure where the male and female parts are fused together.",
        "points": 30,
        "image": "images/orchid_column_anatomy.jpg"
    },
    {
        "category": "Rare Species",
        "difficulty": "hard",
        "question": "Which orchid is known as the 'Ghost Orchid'?",
        "options": ["Dendrophylax lindenii", "Dracula vampira", "Catasetum pileatum", "Stanhopea tigrina"],
        "correct": 0,
        "explanation": "Dendrophylax lindenii is the true Ghost Orchid, found in Florida swamps and extremely rare.",
        "points": 35,
        "image": "images/ghost_orchid_dendrophylax.jpg"
    },
    {
        "category": "Conservation",
        "difficulty": "hard",
        "question": "Which international agreement protects endangered orchids?",
        "options": ["IUCN", "CITES", "CBD", "UNFCCC"],
        "correct": 1,
        "explanation": "CITES (Convention on International Trade in Endangered Species) regulates orchid trade to prevent extinction.",
        "points": 40,
        "image": "images/cites_orchid_protection.jpg"
    },
    
    # Expert Level (45-50 points)
    {
        "category": "Taxonomy",
        "difficulty": "expert",
        "question": "What does 'mycorrhizal' mean in orchid biology?",
        "options": ["Flower color", "Symbiotic fungal relationship", "Seed type", "Pollination method"],
        "correct": 1,
        "explanation": "Orchids have symbiotic relationships with fungi that help them absorb nutrients - essential for survival.",
        "points": 45,
        "image": "images/mycorrhizal_fungi_roots.jpg"
    },
    {
        "category": "Advanced Genetics",
        "difficulty": "expert",
        "question": "What was the first artificial orchid hybrid?",
        "options": ["Cattleya × elegans", "Calanthe × dominyi", "Paphiopedilum × harrisianum", "Dendrobium × ainsworthii"],
        "correct": 1,
        "explanation": "Calanthe × dominyi was created by John Dominy in 1856, starting the modern era of orchid hybridization.",
        "points": 50,
        "image": "images/calanthe_dominyi_first_hybrid.jpg"
    }
]

# Streak and achievement tracking
ACHIEVEMENT_SYSTEM = {
    'first_answer': {'name': 'First Answer', 'points': 25, 'icon': '🌱'},
    'perfect_easy': {'name': 'Easy Expert', 'points': 50, 'icon': '🎯'},
    'perfect_medium': {'name': 'Medium Master', 'points': 100, 'icon': '⭐'},
    'perfect_hard': {'name': 'Hard Hero', 'points': 150, 'icon': '🏆'},
    'expert_scholar': {'name': 'Expert Scholar', 'points': 200, 'icon': '👑'},
    'streak_5': {'name': '5-Question Streak', 'points': 75, 'icon': '🔥'},
    'streak_10': {'name': '10-Question Streak', 'points': 150, 'icon': '⚡'},
    'speed_demon': {'name': 'Speed Answer (<5s)', 'points': 25, 'icon': '💨'},
    'knowledge_seeker': {'name': 'Read 10 Explanations', 'points': 50, 'icon': '📚'}
}

@orchid_trivia.route('/')
def trivia_home():
    """Main trivia game interface"""
    return render_template('widgets/orchid_trivia.html')

@orchid_trivia.route('/get-question', methods=['POST'])
def get_question():
    """Get a random question based on difficulty preference"""
    try:
        data = request.get_json()
        difficulty = data.get('difficulty', 'mixed')
        
        # Filter questions by difficulty
        if difficulty == 'mixed':
            available_questions = TRIVIA_DATABASE
        else:
            available_questions = [q for q in TRIVIA_DATABASE if q['difficulty'] == difficulty]
        
        if not available_questions:
            return jsonify({'success': False, 'error': 'No questions available for this difficulty'})
        
        # Avoid recently asked questions
        recent_questions = session.get('recent_trivia_questions', [])
        unused_questions = [q for q in available_questions if q.get('question') not in recent_questions]
        
        if not unused_questions:
            # Reset if we've used all questions
            session['recent_trivia_questions'] = []
            unused_questions = available_questions
        
        question = random.choice(unused_questions)
        
        # Track recent questions
        if 'recent_trivia_questions' not in session:
            session['recent_trivia_questions'] = []
        session['recent_trivia_questions'].append(question['question'])
        
        # Keep only last 5 questions in memory
        if len(session['recent_trivia_questions']) > 5:
            session['recent_trivia_questions'] = session['recent_trivia_questions'][-5:]
        
        # Store current question for answer validation
        session['current_trivia_question'] = question
        session['question_start_time'] = datetime.now().isoformat()
        
        # Don't send the correct answer to client
        question_data = {
            'category': question['category'],
            'difficulty': question['difficulty'],
            'question': question['question'],
            'options': question['options'],
            'points': question['points'],
            'image': question.get('image', ''),
            'question_id': hash(question['question']) % 10000
        }
        
        return jsonify({'success': True, 'question': question_data})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_trivia.route('/submit-answer', methods=['POST'])
def submit_answer():
    """Submit answer and get results with scoring"""
    try:
        data = request.get_json()
        selected_option = data.get('selected_option')
        time_taken = data.get('time_taken', 10)
        
        # Get stored question
        current_question = session.get('current_trivia_question')
        if not current_question:
            return jsonify({'success': False, 'error': 'No active question found'})
        
        # Check answer
        is_correct = selected_option == current_question['correct']
        
        # Calculate points
        base_points = current_question['points'] if is_correct else 0
        time_bonus = 0
        
        # Speed bonus for answers under 5 seconds
        if is_correct and time_taken < 5:
            time_bonus = 10
        
        total_points = base_points + time_bonus
        
        # Update session stats
        if 'trivia_stats' not in session:
            session['trivia_stats'] = {
                'total_questions': 0,
                'correct_answers': 0,
                'total_points': 0,
                'current_streak': 0,
                'best_streak': 0,
                'achievements': []
            }
        
        stats = session['trivia_stats']
        stats['total_questions'] += 1
        stats['total_points'] += total_points
        
        if is_correct:
            stats['correct_answers'] += 1
            stats['current_streak'] += 1
            stats['best_streak'] = max(stats['best_streak'], stats['current_streak'])
        else:
            stats['current_streak'] = 0
        
        # Check for achievements
        new_achievements = []
        
        # First answer achievement
        if stats['total_questions'] == 1 and 'first_answer' not in stats['achievements']:
            new_achievements.append(ACHIEVEMENT_SYSTEM['first_answer'])
            stats['achievements'].append('first_answer')
        
        # Streak achievements
        if stats['current_streak'] == 5 and 'streak_5' not in stats['achievements']:
            new_achievements.append(ACHIEVEMENT_SYSTEM['streak_5'])
            stats['achievements'].append('streak_5')
        
        if stats['current_streak'] == 10 and 'streak_10' not in stats['achievements']:
            new_achievements.append(ACHIEVEMENT_SYSTEM['streak_10'])
            stats['achievements'].append('streak_10')
        
        # Speed achievement
        if time_taken < 5 and is_correct and 'speed_demon' not in stats['achievements']:
            new_achievements.append(ACHIEVEMENT_SYSTEM['speed_demon'])
            stats['achievements'].append('speed_demon')
        
        # Difficulty mastery (perfect answers in category)
        difficulty_key = f"perfect_{current_question['difficulty']}"
        if is_correct and difficulty_key not in stats['achievements']:
            # Check if this completes a perfect run (simplified)
            difficulty_questions = [q for q in TRIVIA_DATABASE if q['difficulty'] == current_question['difficulty']]
            if len(difficulty_questions) <= 3:  # For demo purposes
                achievement = ACHIEVEMENT_SYSTEM.get(difficulty_key)
                if achievement:
                    new_achievements.append(achievement)
                    stats['achievements'].append(difficulty_key)
        
        # Add achievement points
        achievement_points = sum(a['points'] for a in new_achievements)
        stats['total_points'] += achievement_points
        
        # Response data
        response_data = {
            'success': True,
            'is_correct': is_correct,
            'correct_answer': current_question['options'][current_question['correct']],
            'explanation': current_question['explanation'],
            'points_earned': total_points,
            'achievement_points': achievement_points,
            'new_achievements': new_achievements,
            'stats': {
                'total_questions': stats['total_questions'],
                'correct_answers': stats['correct_answers'],
                'accuracy': round((stats['correct_answers'] / stats['total_questions']) * 100, 1),
                'total_points': stats['total_points'],
                'current_streak': stats['current_streak'],
                'best_streak': stats['best_streak']
            },
            'time_bonus': time_bonus
        }
        
        session['trivia_stats'] = stats
        
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_trivia.route('/get-stats')
def get_stats():
    """Get current player statistics"""
    stats = session.get('trivia_stats', {
        'total_questions': 0,
        'correct_answers': 0,
        'total_points': 0,
        'current_streak': 0,
        'best_streak': 0,
        'achievements': []
    })
    
    # Calculate accuracy
    accuracy = 0
    total_q = stats.get('total_questions', 0)
    correct_a = stats.get('correct_answers', 0)
    if isinstance(total_q, int) and total_q > 0 and isinstance(correct_a, int):
        accuracy = round((correct_a / total_q) * 100, 1)
    
    return jsonify({
        'success': True,
        'stats': {
            **stats,
            'accuracy': accuracy,
            'achievement_count': len(stats.get('achievements', []))
        }
    })

@orchid_trivia.route('/reset-stats', methods=['POST'])
def reset_stats():
    """Reset player statistics"""
    session['trivia_stats'] = {
        'total_questions': 0,
        'correct_answers': 0,
        'total_points': 0,
        'current_streak': 0,
        'best_streak': 0,
        'achievements': []
    }
    session['recent_trivia_questions'] = []
    
    return jsonify({'success': True, 'message': 'Statistics reset successfully'})

@orchid_trivia.route('/leaderboard')
def get_leaderboard():
    """Get trivia leaderboard (placeholder for now)"""
    # TODO: Implement with database
    mock_leaderboard = [
        {'name': 'Orchid Expert', 'points': 1250, 'accuracy': 94.5, 'streak': 15},
        {'name': 'Flower Power', 'points': 980, 'accuracy': 87.2, 'streak': 8},
        {'name': 'Garden Master', 'points': 765, 'accuracy': 91.1, 'streak': 12},
        {'name': 'Botanical Scholar', 'points': 650, 'accuracy': 83.7, 'streak': 6},
        {'name': 'Plant Lover', 'points': 545, 'accuracy': 79.4, 'streak': 4}
    ]
    
    return jsonify({
        'success': True,
        'leaderboard': mock_leaderboard
    })

@orchid_trivia.route('/daily-challenge')
def daily_challenge():
    """Get daily challenge questions with bonus scoring"""
    try:
        # Use date as seed for consistent daily challenges
        today = datetime.now().strftime('%Y-%m-%d')
        random.seed(hash(today) % (2**31))
        
        # Select 5 questions of increasing difficulty
        easy_q = random.choice([q for q in TRIVIA_DATABASE if q['difficulty'] == 'easy'])
        medium_q = random.choice([q for q in TRIVIA_DATABASE if q['difficulty'] == 'medium'])
        hard_q = random.choice([q for q in TRIVIA_DATABASE if q['difficulty'] == 'hard'])
        
        try:
            expert_q = random.choice([q for q in TRIVIA_DATABASE if q['difficulty'] == 'expert'])
            expert_available = True
        except:
            expert_q = hard_q  # Fallback if no expert questions
            expert_available = False
        
        challenge_questions = [easy_q, medium_q, hard_q, expert_q]
        
        # Increase point values for daily challenge
        for q in challenge_questions:
            q['points'] = int(q['points'] * 1.5)  # 50% bonus
        
        session['daily_challenge_questions'] = challenge_questions
        session['daily_challenge_date'] = today
        
        return jsonify({
            'success': True,
            'challenge_date': today,
            'questions': len(challenge_questions),
            'bonus_multiplier': 1.5,
            'total_possible_points': sum(q['points'] for q in challenge_questions)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500