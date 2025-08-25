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

@games_bp.route('/orchid-quiz')
def orchid_quiz():
    """Orchid identification quiz game"""
    return render_template('games/orchid_quiz.html')

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
    
    # Create multiple choice options
    options = [orchid.display_name]
    for wrong in wrong_answers:
        if wrong.display_name:
            options.append(wrong.display_name)
    
    # Shuffle options
    random.shuffle(options)
    
    return jsonify({
        'image_url': orchid.image_url,
        'correct_answer': orchid.display_name,
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
        card_data = {
            'id': i,
            'image_url': orchid.image_url,
            'name': orchid.display_name,
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
        # Get other genera as wrong answers
        other_genera = db.session.query(OrchidRecord.genus).filter(
            OrchidRecord.genus != orchid.genus,
            OrchidRecord.genus.isnot(None)
        ).distinct().limit(3).all()
        
        options = [orchid.genus]
        for genus_tuple in other_genera:
            options.append(genus_tuple[0])
        
        random.shuffle(options)
        
        return jsonify({
            'question': f"What genus does '{orchid.display_name}' belong to?",
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
        
        return jsonify({
            'question': f"Where is '{orchid.display_name}' originally from?",
            'correct_answer': orchid.region,
            'options': options,
            'image_url': orchid.image_url
        })
    
    else:  # photographer
        return jsonify({
            'question': f"Who photographed this '{orchid.display_name}'?",
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