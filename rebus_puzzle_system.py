from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import OrchidRecord, GameScore
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

rebus_puzzle_bp = Blueprint('rebus_puzzle', __name__)

class OrchidRebusPuzzle:
    def __init__(self):
        self.puzzle_templates = [
            {
                'id': 1,
                'visual_clues': ['🌸', '+', '🏔️'],
                'text_clues': ['FLOWER', '+', 'MOUNTAIN'],
                'solution_pattern': 'GENUS + HABITAT',
                'difficulty': 'easy',
                'hint': 'Think about where this orchid grows'
            },
            {
                'id': 2,
                'visual_clues': ['👑', '+', '🦋'],
                'text_clues': ['CROWN', '+', 'BUTTERFLY'],
                'solution_pattern': 'ROYAL + POLLINATOR',
                'difficulty': 'medium',
                'hint': 'Royal orchid with butterfly-like flowers'
            },
            {
                'id': 3,
                'visual_clues': ['🕷️', '+', '👦'],
                'text_clues': ['SPIDER', '+', 'BOY'],
                'solution_pattern': 'ARACHNID + YOUNG',
                'difficulty': 'medium',
                'hint': 'Web-like pattern with youthful appearance'
            },
            {
                'id': 4,
                'visual_clues': ['🌙', '+', '🎵'],
                'text_clues': ['MOON', '+', 'MUSIC'],
                'solution_pattern': 'NIGHT + SOUND',
                'difficulty': 'hard',
                'hint': 'Nocturnal bloomer with musical connection'
            },
            {
                'id': 5,
                'visual_clues': ['👞', '+', '👑'],
                'text_clues': ['SHOE', '+', 'CROWN'],
                'solution_pattern': 'FOOTWEAR + ROYALTY',
                'difficulty': 'easy',
                'hint': 'Famous slipper-shaped orchid'
            }
        ]
        
        # Real orchid solutions mapped to puzzles
        self.puzzle_solutions = {
            1: {'genus': 'Pleione', 'common': 'Mountain Orchid', 'explanation': 'Pleione grows in mountainous regions'},
            2: {'genus': 'Psychopsis', 'common': 'Butterfly Orchid', 'explanation': 'Psychopsis has butterfly-like flowers'},
            3: {'genus': 'Brassia', 'common': 'Spider Orchid', 'explanation': 'Brassia flowers resemble spiders'},
            4: {'genus': 'Brassavola', 'common': 'Night-blooming Orchid', 'explanation': 'Brassavola blooms at night with fragrance'},
            5: {'genus': 'Cypripedium', 'common': 'Lady Slipper', 'explanation': 'Cypripedium has a slipper-shaped pouch'}
        }
    
    def generate_daily_puzzle(self):
        """Generate today's rebus puzzle"""
        # Use date to ensure same puzzle for all users on same day
        today = datetime.now().date()
        puzzle_index = (today.day + today.month + today.year) % len(self.puzzle_templates)
        
        template = self.puzzle_templates[puzzle_index]
        solution = self.puzzle_solutions[template['id']]
        
        # Get real orchid photo for this genus if available
        orchid_example = OrchidRecord.query.filter(
            OrchidRecord.genus.ilike(f'%{solution["genus"]}%')
        ).filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).first()
        
        return {
            'puzzle_id': template['id'],
            'visual_clues': template['visual_clues'],
            'text_clues': template['text_clues'],
            'solution_pattern': template['solution_pattern'],
            'difficulty': template['difficulty'],
            'hint': template['hint'],
            'solution': solution,
            'orchid_photo': f'/api/drive-photo/{orchid_example.google_drive_id}' if orchid_example else None,
            'date': today.isoformat()
        }
    
    def check_solution(self, puzzle_id, user_answer):
        """Check if user's answer is correct"""
        if puzzle_id not in self.puzzle_solutions:
            return False, "Invalid puzzle"
        
        solution = self.puzzle_solutions[puzzle_id]
        user_answer_clean = user_answer.lower().strip()
        
        # Accept multiple correct answers
        correct_answers = [
            solution['genus'].lower(),
            solution['common'].lower(),
            f"{solution['genus'].lower()} orchid",
            f"{solution['common'].lower()} orchid"
        ]
        
        is_correct = user_answer_clean in correct_answers
        
        return is_correct, solution if is_correct else "Not correct"

# Initialize rebus system
rebus_system = OrchidRebusPuzzle()

# Routes
@rebus_puzzle_bp.route('/api/rebus/daily')
def get_daily_rebus():
    """Get today's rebus puzzle"""
    try:
        puzzle_data = rebus_system.generate_daily_puzzle()
        
        # Remove solution from response (except for admin testing)
        if not session.get('is_admin'):
            puzzle_data.pop('solution', None)
        
        return jsonify({
            'success': True,
            'puzzle': puzzle_data
        })
        
    except Exception as e:
        logger.error(f"Error generating daily rebus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@rebus_puzzle_bp.route('/api/rebus/solve', methods=['POST'])
def solve_rebus():
    """Submit solution to rebus puzzle"""
    try:
        data = request.get_json()
        puzzle_id = data.get('puzzle_id')
        user_answer = data.get('answer', '').strip()
        
        if not user_answer:
            return jsonify({'success': False, 'error': 'Answer required'}), 400
        
        is_correct, solution = rebus_system.check_solution(puzzle_id, user_answer)
        
        result = {
            'success': True,
            'correct': is_correct,
            'user_answer': user_answer
        }
        
        if is_correct:
            result.update({
                'solution': solution,
                'points_earned': 50,  # Base points for solving rebus
                'message': f'Correct! The answer is {solution["genus"]} - {solution["common"]}'
            })
            
            # Award points to user if logged in
            if session.get('user_id'):
                try:
                    rebus_score = GameScore(
                        user_id=session['user_id'],
                        game_type='rebus',
                        difficulty='daily',
                        score=50,
                        time_taken=0,  # Rebus doesn't track time
                        moves_made=1,  # One submission
                        game_metadata={
                            'puzzle_id': puzzle_id,
                            'user_answer': user_answer,
                            'correct_answer': solution['genus']
                        }
                    )
                    db.session.add(rebus_score)
                    db.session.commit()
                    
                except Exception as e:
                    logger.error(f"Error saving rebus score: {e}")
        else:
            result.update({
                'message': 'Not quite right. Try again!',
                'hint_available': True
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error solving rebus: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@rebus_puzzle_bp.route('/api/rebus/hint/<int:puzzle_id>')
def get_rebus_hint(puzzle_id):
    """Get hint for rebus puzzle"""
    try:
        puzzle_template = next((p for p in rebus_system.puzzle_templates if p['id'] == puzzle_id), None)
        
        if not puzzle_template:
            return jsonify({'success': False, 'error': 'Puzzle not found'}), 404
        
        return jsonify({
            'success': True,
            'hint': puzzle_template['hint'],
            'difficulty': puzzle_template['difficulty']
        })
        
    except Exception as e:
        logger.error(f"Error getting rebus hint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

logger.info("Rebus Puzzle System initialized successfully")