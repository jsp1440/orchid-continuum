#!/usr/bin/env python3
"""
Orchid Games System - Fun interactive games for orchid enthusiasts
"""

from flask import Blueprint, render_template, request, jsonify, session
from models import OrchidRecord, db
import random
import json
from datetime import datetime

games_bp = Blueprint('games', __name__, url_prefix='/games')

@games_bp.route('/')
def games_home():
    """Games homepage with all available games"""
    return render_template('games/index.html')

@games_bp.route('/puzzle')
def puzzle_game():
    """Orchid puzzle game"""
    return render_template('games/puzzle_game.html')

@games_bp.route('/quiz')
def quiz_game():
    """Orchid quiz game"""  
    return render_template('games/quiz_game.html')

# Widget endpoints for embedding games in other pages
@games_bp.route('/widget/quiz')
def quiz_widget():
    """Embeddable orchid quiz widget"""
    return render_template('games/widgets/quiz_widget.html')

@games_bp.route('/widget/memory')
def memory_widget():
    """Embeddable memory match widget"""
    return render_template('games/widgets/memory_widget.html')

@games_bp.route('/widget/trivia')
def trivia_widget():
    """Embeddable trivia widget"""
    return render_template('games/widgets/trivia_widget.html')

@games_bp.route('/widget/guess')
def guess_widget():
    """Embeddable guess-the-orchid widget"""
    return render_template('games/widgets/guess_widget.html')

@games_bp.route('/widget/crossword')
def crossword_widget():
    """Embeddable crossword puzzle widget"""
    return render_template('games/widgets/crossword_widget.html')

# Leaderboard routes
@games_bp.route('/leaderboard')
def leaderboard():
    """Game leaderboard page"""
    return render_template('games/leaderboard.html')

@games_bp.route('/api/leaderboard')
def api_leaderboard():
    """API endpoint for leaderboard data"""
    from leaderboard import GameLeaderboard
    
    game_type = request.args.get('game_type')
    time_period = request.args.get('time_period', 'all')
    limit = int(request.args.get('limit', 10))
    
    try:
        leaderboard_data = GameLeaderboard.get_leaderboard(game_type, limit, time_period)
        stats = GameLeaderboard.get_game_stats()
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data,
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@games_bp.route('/api/submit-score', methods=['POST'])
def api_submit_score():
    """API endpoint to submit game scores"""
    from leaderboard import GameLeaderboard
    
    data = request.get_json()
    
    try:
        result = GameLeaderboard.submit_score(
            player_name=data.get('player_name', 'Anonymous'),
            game_type=data['game_type'],
            score=data['score'],
            max_score=data['max_score'],
            completion_time=data.get('completion_time'),
            difficulty=data.get('difficulty', 'medium'),
            game_data=data.get('game_data'),
            ip_address=request.remote_addr
        )
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Crossword puzzle routes
@games_bp.route('/crossword-puzzle')
def crossword_puzzle():
    """Crossword puzzle game page"""
    return render_template('games/crossword.html')

@games_bp.route('/api/crossword-puzzle')
def api_crossword_puzzle():
    """API endpoint for crossword puzzle data"""
    from crossword_generator import generate_crossword_api
    
    difficulty = request.args.get('difficulty', 'mixed')
    size = request.args.get('size', 'medium')
    
    try:
        puzzle_data = generate_crossword_api(difficulty, size)
        return jsonify(puzzle_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@games_bp.route('/orchid-quiz')
def orchid_quiz():
    """Orchid identification quiz game"""
    return render_template('games/orchid_quiz.html')

def expand_orchid_name(name):
    """Expand abbreviated orchid names to full names"""
    if not name:
        return name
        
    # Common orchid abbreviations to full names
    abbreviations = {
        'Bc ': 'Brassocattleya ',
        'Blc ': 'Brassolaeliocattleya ',
        'Lc ': 'Laeliocattleya ',
        'Den ': 'Dendrobium ',
        'Bulb ': 'Bulbophyllum ',
        'Pos ': 'Posthia ',
        'CT ': '',  # Remove "CT" prefix completely
        'Onc ': 'Oncidium ',
        'Paph ': 'Paphiopedilum ',
        'Phrag ': 'Phragmipedium ',
        'Cym ': 'Cymbidium ',
        'Van ': 'Vanda ',
        'Phal ': 'Phalaenopsis ',
        'Coel ': 'Coelogyne ',
        'Masd ': 'Masdevallia ',
        'Max ': 'Maxillaria ',
        'Epi ': 'Epidendrum ',
        'Enc ': 'Encyclia ',
        'Pot ': 'Potinara ',
        'Slc ': 'Sophrolaeliocattleya ',
        'Rlc ': 'Rhyncholaeliocattleya '
    }
    
    expanded_name = name
    for abbrev, full in abbreviations.items():
        if expanded_name.startswith(abbrev):
            expanded_name = full + expanded_name[len(abbrev):]
            break
    
    return expanded_name.strip()

@games_bp.route('/api/quiz-question')
def get_quiz_question():
    """Get a random orchid for the quiz"""
    # Get random orchid with image
    orchid = OrchidRecord.query.filter(
        OrchidRecord.image_url.isnot(None),
        OrchidRecord.image_url != '',
        OrchidRecord.display_name.isnot(None)
    ).order_by(db.func.random()).first()
    
    if not orchid:
        return jsonify({'error': 'No orchids available'}), 404
    
    # Get 3 other random orchid names as wrong answers
    wrong_answers = OrchidRecord.query.filter(
        OrchidRecord.id != orchid.id,
        OrchidRecord.display_name.isnot(None)
    ).order_by(db.func.random()).limit(3).all()
    
    # Create multiple choice options with expanded names
    correct_name = expand_orchid_name(orchid.display_name)
    options = [correct_name]
    for wrong in wrong_answers:
        if wrong.display_name:
            expanded_wrong = expand_orchid_name(wrong.display_name)
            options.append(expanded_wrong)
    
    # Shuffle options
    random.shuffle(options)
    
    return jsonify({
        'image_url': orchid.image_url,
        'correct_answer': correct_name,
        'options': options,
        'hint': f"This orchid is from the {orchid.genus} genus" if orchid.genus else "No hint available",
        'orchid_id': orchid.id
    })

@games_bp.route('/memory-match')
def memory_match():
    """Orchid memory matching game"""
    return render_template('games/memory_match.html')

@games_bp.route('/api/memory-cards')
def get_memory_cards():
    """Get orchid images for memory game"""
    # Get 8 random orchids with images for 16-card memory game
    orchids = OrchidRecord.query.filter(
        OrchidRecord.image_url.isnot(None),
        OrchidRecord.image_url != '',
        OrchidRecord.display_name.isnot(None)
    ).order_by(db.func.random()).limit(8).all()
    
    cards = []
    for i, orchid in enumerate(orchids):
        expanded_name = expand_orchid_name(orchid.display_name)
        card_data = {
            'id': i,
            'image_url': orchid.image_url,
            'name': expanded_name,
            'pair_id': i  # Each orchid appears twice
        }
        # Add each card twice for matching pairs
        cards.append(card_data)
        cards.append({**card_data, 'id': i + 8})
    
    # Shuffle the cards
    random.shuffle(cards)
    
    return jsonify({'cards': cards})

@games_bp.route('/orchid-trivia')
def orchid_trivia():
    """Orchid trivia game"""
    return render_template('games/orchid_trivia.html')

@games_bp.route('/api/trivia-question')
def get_trivia_question():
    """Get random orchid trivia question"""
    
    # Get random orchid with interesting info
    orchid = OrchidRecord.query.filter(
        db.or_(
            OrchidRecord.cultural_notes.isnot(None),
            OrchidRecord.ai_description.isnot(None),
            OrchidRecord.region.isnot(None)
        )
    ).order_by(db.func.random()).first()
    
    if not orchid:
        return jsonify({'error': 'No trivia available'}), 404
    
    # Generate different types of questions
    question_types = []
    
    if orchid.genus:
        question_types.append('genus')
    if orchid.region:
        question_types.append('region')
    if orchid.photographer:
        question_types.append('photographer')
    
    if not question_types:
        question_types = ['genus']
    
    question_type = random.choice(question_types)
    
    if question_type == 'genus':
        # Get other genera as wrong answers (exclude invalid genus names)
        other_genera = db.session.query(OrchidRecord.genus).filter(
            OrchidRecord.genus != orchid.genus,
            OrchidRecord.genus.isnot(None),
            ~OrchidRecord.genus.like('BOLD%'),  # Exclude BOLD identifiers
            ~OrchidRecord.genus.like('%:%'),    # Exclude any with colons
            ~OrchidRecord.genus.like('%[0-9]%'),# Exclude any with numbers
            OrchidRecord.genus.op('~')('^[A-Z][a-z]+$')  # Must be proper genus format
        ).distinct().limit(10).all()
        
        # Filter to get only valid genus names
        valid_genera = []
        for genus_tuple in other_genera:
            genus_name = genus_tuple[0]
            # Additional validation: proper genus format (Capitalized, letters only)
            if (genus_name and 
                len(genus_name) > 2 and 
                genus_name[0].isupper() and 
                genus_name[1:].islower() and 
                genus_name.isalpha() and
                'BOLD' not in genus_name and
                ':' not in genus_name):
                valid_genera.append(genus_name)
        
        # Take first 3 valid genera
        options = [orchid.genus] + valid_genera[:3]
        
        # If we don't have enough valid genera, add some common ones
        if len(options) < 4:
            common_genera = ['Cattleya', 'Dendrobium', 'Phalaenopsis', 'Oncidium', 'Cymbidium', 'Paphiopedilum']
            for genus in common_genera:
                if genus not in options and len(options) < 4:
                    options.append(genus)
        
        random.shuffle(options)
        
        expanded_display_name = expand_orchid_name(orchid.display_name)
        return jsonify({
            'question': f"What genus does '{expanded_display_name}' belong to?",
            'correct_answer': orchid.genus,
            'options': options,
            'image_url': orchid.image_url
        })
    
    elif question_type == 'region':
        # Get other regions as wrong answers
        other_regions = db.session.query(OrchidRecord.region).filter(
            OrchidRecord.region != orchid.region,
            OrchidRecord.region.isnot(None)
        ).distinct().limit(3).all()
        
        options = [orchid.region]
        for region_tuple in other_regions:
            options.append(region_tuple[0])
        
        random.shuffle(options)
        
        expanded_display_name = expand_orchid_name(orchid.display_name)
        return jsonify({
            'question': f"Where is '{expanded_display_name}' originally from?",
            'correct_answer': orchid.region,
            'options': options,
            'image_url': orchid.image_url
        })
    
    else:  # photographer
        expanded_display_name = expand_orchid_name(orchid.display_name)
        return jsonify({
            'question': f"Who photographed this '{expanded_display_name}'?",
            'correct_answer': orchid.photographer,
            'options': [orchid.photographer, "Ron Parsons", "Gary Yong Gee", "Roberta Fox"],
            'image_url': orchid.image_url
        })

@games_bp.route('/guess-the-orchid')
def guess_the_orchid():
    """Progressive reveal orchid guessing game"""
    return render_template('games/guess_orchid.html')

@games_bp.route('/api/guess-orchid')
def get_guess_orchid():
    """Get orchid for progressive guessing game"""
    orchid = OrchidRecord.query.filter(
        OrchidRecord.image_url.isnot(None),
        OrchidRecord.image_url != '',
        OrchidRecord.display_name.isnot(None)
    ).order_by(db.func.random()).first()
    
    if not orchid:
        return jsonify({'error': 'No orchids available'}), 404
    
    # Create progressive hints
    hints = []
    
    if orchid.genus:
        hints.append(f"Genus: {orchid.genus}")
    
    if orchid.region:
        hints.append(f"Native to: {orchid.region}")
    
    if orchid.cultural_notes:
        # Extract first sentence as hint
        first_sentence = orchid.cultural_notes.split('.')[0]
        if len(first_sentence) < 100:
            hints.append(f"Growing info: {first_sentence}")
    
    if orchid.ai_description:
        # Extract color or size info if available
        description_words = orchid.ai_description.lower()
        if any(color in description_words for color in ['purple', 'yellow', 'white', 'pink', 'red', 'orange']):
            hints.append("Color hint available in description")
    
    if not hints:
        hints = ["This is a beautiful orchid species", "It requires specific growing conditions"]
    
    return jsonify({
        'orchid_id': orchid.id,
        'image_url': orchid.image_url,
        'correct_answer': orchid.display_name,
        'hints': hints,
        'max_score': len(hints) * 10  # More points for guessing with fewer hints
    })

@games_bp.route('/api/submit-score', methods=['POST'])
def submit_score():
    """Submit game score (can be enhanced with leaderboards later)"""
    data = request.get_json()
    game_type = data.get('game_type')
    score = data.get('score', 0)
    
    # Store in session for now (could be database later)
    if 'game_scores' not in session:
        session['game_scores'] = {}
    
    session['game_scores'][game_type] = max(
        session['game_scores'].get(game_type, 0), 
        score
    )
    
    return jsonify({
        'success': True,
        'high_score': session['game_scores'][game_type],
        'message': f'Score saved! Your best {game_type} score is {session["game_scores"][game_type]}'
    })

@games_bp.route('/leaderboard')
def leaderboard():
    """Simple leaderboard showing session high scores"""
    scores = session.get('game_scores', {})
    return render_template('games/leaderboard.html', scores=scores)