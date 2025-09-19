from flask import Blueprint, render_template, request, jsonify, session
from datetime import datetime
import random
import json

# Create blueprint for Orchid Bingo
orchid_bingo = Blueprint('orchid_bingo', __name__, url_prefix='/widgets/orchid-bingo')

# Comprehensive orchid word bank for bingo
ORCHID_WORDS = [
    "Cattleya", "Paphiopedilum", "Phalaenopsis", "Dendrobium", "Oncidium",
    "Vanda", "Cymbidium", "Laelia", "Phragmipedium", "Dracula",
    "Masdevallia", "Bulbophyllum", "Miltonia", "Gongora", "Stanhopea",
    "Catasetum", "Pleurothallis", "Encyclia", "Brassia", "Epidendrum",
    "Keiki", "Pseudobulb", "Aerial roots", "Spike", "Sepal",
    "Labellum", "Column", "Pollinia", "Mycorrhizae", "Velamen",
    "Epiphyte", "Monopodial", "Sympodial", "Inflorescence", "Raceme",
    "Resupinate", "Clonal", "Mericlone", "Backbulb", "Sheath",
    "Species", "Hybrid", "Intergeneric", "Fragrance", "Humidity",
    "Mounted", "Medium", "Bark mix", "Sphagnum", "LECA",
    "Terrestrial", "Lithophyte", "Protocorm", "Rhizome", "Tuber"
]

BADGE_REWARDS = {
    'first_bingo': {'name': 'First Bingo!', 'points': 50, 'icon': '🎯'},
    'speed_demon': {'name': 'Speed Demon', 'points': 100, 'icon': '⚡'},
    'bingo_master': {'name': 'Bingo Master', 'points': 200, 'icon': '👑'},
    'word_expert': {'name': 'Orchid Vocabulary Expert', 'points': 75, 'icon': '📚'},
    'pattern_finder': {'name': 'Pattern Finder', 'points': 125, 'icon': '🔍'}
}

@orchid_bingo.route('/')
def bingo_home():
    """Main bingo game interface"""
    return render_template('widgets/orchid_bingo.html')

@orchid_bingo.route('/generate-board', methods=['POST'])
def generate_board():
    """Generate a new bingo board with random orchid words"""
    try:
        data = request.get_json()
        size = int(data.get('size', 5))
        seed = data.get('seed', '')
        
        # Set random seed for reproducible boards
        if seed:
            random.seed(hash(seed) % (2**31))
        else:
            random.seed()
        
        # Generate board words
        needed_words = size * size
        board_words = random.sample(ORCHID_WORDS, min(needed_words, len(ORCHID_WORDS)))
        
        # If we need more words than available, allow repeats
        while len(board_words) < needed_words:
            board_words.extend(random.sample(ORCHID_WORDS, min(needed_words - len(board_words), len(ORCHID_WORDS))))
        
        # Create board grid
        board = []
        word_index = 0
        
        for row in range(size):
            board_row = []
            for col in range(size):
                # Free space in center for 5x5 boards
                if size == 5 and row == 2 and col == 2:
                    board_row.append({
                        'word': 'FREE',
                        'is_free': True,
                        'marked': True
                    })
                else:
                    board_row.append({
                        'word': board_words[word_index],
                        'is_free': False,
                        'marked': False
                    })
                    word_index += 1
            board.append(board_row)
        
        # Store board in session for validation
        session['current_bingo_board'] = board
        session['bingo_start_time'] = datetime.now().isoformat()
        session['bingo_size'] = size
        
        return jsonify({
            'success': True,
            'board': board,
            'game_id': f"bingo_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_bingo.route('/check-bingo', methods=['POST'])
def check_bingo():
    """Check if current board state has a winning bingo pattern"""
    try:
        data = request.get_json()
        marked_positions = data.get('marked_positions', [])
        size = session.get('bingo_size', 5)
        
        # Convert positions to grid for easier checking
        marked_grid = [[False for _ in range(size)] for _ in range(size)]
        for pos in marked_positions:
            row, col = pos['row'], pos['col']
            if 0 <= row < size and 0 <= col < size:
                marked_grid[row][col] = True
        
        # Check for winning patterns
        winning_patterns = []
        
        # Check rows
        for row in range(size):
            if all(marked_grid[row][col] for col in range(size)):
                winning_patterns.append({'type': 'row', 'index': row})
        
        # Check columns
        for col in range(size):
            if all(marked_grid[row][col] for row in range(size)):
                winning_patterns.append({'type': 'column', 'index': col})
        
        # Check diagonals
        if all(marked_grid[i][i] for i in range(size)):
            winning_patterns.append({'type': 'diagonal', 'index': 0})
        
        if all(marked_grid[i][size-1-i] for i in range(size)):
            winning_patterns.append({'type': 'diagonal', 'index': 1})
        
        # Calculate points and badges
        points_earned = 0
        badges_earned = []
        
        if winning_patterns:
            # Base points for bingo
            points_earned = 100
            
            # Bonus points for multiple patterns
            if len(winning_patterns) > 1:
                points_earned += 50 * (len(winning_patterns) - 1)
            
            # Speed bonus
            start_time = datetime.fromisoformat(session.get('bingo_start_time', datetime.now().isoformat()))
            time_taken = (datetime.now() - start_time).total_seconds()
            
            if time_taken < 60:  # Under 1 minute
                points_earned += 50
                badges_earned.append(BADGE_REWARDS['speed_demon'])
            
            # Check for first bingo badge
            if not session.get('has_completed_bingo', False):
                badges_earned.append(BADGE_REWARDS['first_bingo'])
                session['has_completed_bingo'] = True
        
        return jsonify({
            'success': True,
            'has_bingo': len(winning_patterns) > 0,
            'winning_patterns': winning_patterns,
            'points_earned': points_earned,
            'badges_earned': badges_earned,
            'total_patterns': len(winning_patterns)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_bingo.route('/submit-score', methods=['POST'])
def submit_score():
    """Submit final score to leaderboard system"""
    try:
        data = request.get_json()
        
        score_data = {
            'game_type': 'orchid_bingo',
            'points': data.get('points', 0),
            'badges': data.get('badges', []),
            'completion_time': data.get('completion_time'),
            'board_size': session.get('bingo_size', 5),
            'patterns_found': data.get('patterns_found', 0),
            'timestamp': datetime.now().isoformat()
        }
        
        # TODO: Integrate with main scoring system
        # For now, store in session
        if 'game_scores' not in session:
            session['game_scores'] = []
        
        session['game_scores'].append(score_data)
        
        return jsonify({
            'success': True,
            'message': 'Score submitted successfully!',
            'rank': len(session['game_scores'])  # Temporary ranking
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_bingo.route('/leaderboard')
def get_leaderboard():
    """Get current leaderboard for bingo games"""
    try:
        # TODO: Get from real database
        # For now, return session data
        scores = session.get('game_scores', [])
        bingo_scores = [s for s in scores if s['game_type'] == 'orchid_bingo']
        
        # Sort by points descending
        bingo_scores.sort(key=lambda x: x['points'], reverse=True)
        
        return jsonify({
            'success': True,
            'leaderboard': bingo_scores[:10],  # Top 10
            'player_count': len(bingo_scores)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_bingo.route('/daily-challenge')
def daily_challenge():
    """Generate daily challenge bingo board with special scoring"""
    try:
        # Use date as seed for consistent daily boards
        today = datetime.now().strftime('%Y-%m-%d')
        random.seed(hash(today) % (2**31))
        
        # Create challenging 5x5 board with advanced terms
        advanced_words = [
            "Angraecum", "Bulbophyllum", "Paphiopedilum", "Phragmipedium", 
            "Dracula", "Masdevallia", "Restrepia", "Stelis", "Lepanthes",
            "Pleurothallis", "Teagueia", "Trisetella", "Barbosella", "Octomeria",
            "Protocorm", "Mycorrhizae", "Velamen", "Resupinate", "Gynostemium",
            "Clinandrium", "Rostellum", "Viscidium", "Caudicle", "Tegula"
        ]
        
        challenge_words = random.sample(advanced_words, 24)  # 24 + 1 FREE = 25
        
        # Create board
        board = []
        word_index = 0
        
        for row in range(5):
            board_row = []
            for col in range(5):
                if row == 2 and col == 2:
                    board_row.append({
                        'word': 'FREE',
                        'is_free': True,
                        'marked': True
                    })
                else:
                    board_row.append({
                        'word': challenge_words[word_index],
                        'is_free': False,
                        'marked': False
                    })
                    word_index += 1
            board.append(board_row)
        
        return jsonify({
            'success': True,
            'board': board,
            'challenge_date': today,
            'bonus_multiplier': 2.0,
            'description': 'Daily Challenge: Advanced Orchid Terminology'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500