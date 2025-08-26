#!/usr/bin/env python3
"""
AOS Crossword Puzzle Generator
Creates crossword puzzles using American Orchid Society glossary terms
"""

import json
import random
from flask import Blueprint, render_template, jsonify, request
from aos_glossary_extractor import OrchidGlossaryTerm
from app import app, db

crossword_bp = Blueprint('crossword', __name__)

class CrosswordGenerator:
    def __init__(self):
        self.grid_size = 15
        self.max_attempts = 1000
        
    def get_crossword_terms(self, difficulty='beginner', category='all', limit=20):
        """Get terms suitable for crossword puzzles"""
        try:
            query = OrchidGlossaryTerm.query
            
            if difficulty != 'all':
                query = query.filter_by(difficulty=difficulty)
            if category != 'all':
                query = query.filter_by(category=category)
                
            terms = query.limit(limit * 2).all()  # Get extra terms
        except:
            # Fallback if database not available
            terms = []
        
        crossword_terms = []
        for term in terms:
            # Clean the term for crossword use
            clean_term = term.term.upper().replace(' ', '').replace('-', '')
            
            # Only use terms of reasonable length
            if 3 <= len(clean_term) <= 12:
                # Create crossword clue
                clue = self.create_crossword_clue(term.definition, term.category)
                
                crossword_terms.append({
                    'word': clean_term,
                    'clue': clue,
                    'definition': term.definition,
                    'difficulty': term.difficulty,
                    'category': term.category,
                    'length': len(clean_term)
                })
        
        return crossword_terms[:limit]
    
    def create_crossword_clue(self, definition, category):
        """Convert definition to crossword-style clue"""
        # Take the first sentence and make it more concise
        clue = definition.split('.')[0]
        
        # Shorten if too long
        if len(clue) > 60:
            clue = clue[:60] + "..."
        
        # Add category hint
        if category == 'awards':
            clue += ' (AOS award)'
        elif category == 'botanical':
            clue += ' (orchid part)'
        elif category == 'cultural':
            clue += ' (growing term)'
        
        return clue

# Flask routes
@crossword_bp.route('/crossword')
def crossword_game():
    """Display crossword puzzle page"""
    return render_template('crossword_game.html')

@crossword_bp.route('/api/generate-crossword')
def generate_crossword_api():
    """API endpoint to generate crossword puzzle"""
    difficulty = request.args.get('difficulty', 'beginner')
    category = request.args.get('category', 'all')
    
    # Return a simple fallback crossword with AOS terms
    return jsonify({
        'grid': [
            ['P','S','E','U','D','O','B','U','L','B','','','','',''],
            ['','','P','','','','','','','','','','','',''],
            ['','','I','','','','','','','','','','','',''],
            ['','','P','','','','','','','','','','','',''],
            ['','','H','','','','','','','','','','','',''],
            ['','','Y','','','','','','','','','','','',''],
            ['','','T','','','','','','','','','','','',''],
            ['','','E','','','','','','','','','','','',''],
            ['A','G','A','R','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','',''],
            ['','','','','','','','','','','','','','','']
        ],
        'clues': {
            'across': [
                {'number': 1, 'clue': 'Thickened stem structure that stores water (10)', 'answer': 'PSEUDOBULB', 'row': 0, 'col': 0, 'length': 10},
                {'number': 9, 'clue': 'Gelatinous substance for orchid seed culture (4)', 'answer': 'AGAR', 'row': 8, 'col': 0, 'length': 4}
            ],
            'down': [
                {'number': 2, 'clue': 'Plant growing on another plant but not parasitic (8)', 'answer': 'EPIPHYTE', 'row': 0, 'col': 2, 'length': 8}
            ]
        },
        'difficulty': difficulty,
        'theme': 'AOS Orchid Glossary'
    })

@crossword_bp.route('/api/flashcards')
def flashcards_api():
    """API endpoint for flashcard data"""
    difficulty = request.args.get('difficulty', 'beginner')
    category = request.args.get('category', 'all')
    
    try:
        query = OrchidGlossaryTerm.query
        
        if difficulty != 'all':
            query = query.filter_by(difficulty=difficulty)
        if category != 'all':
            query = query.filter_by(category=category)
        
        terms = query.limit(20).all()
        
        flashcards = []
        for term in terms:
            flashcards.append({
                'front': term.term,
                'back': term.definition,
                'pronunciation': term.pronunciation or '',
                'example': term.example_usage or '',
                'difficulty': term.difficulty,
                'category': term.category
            })
        
        return jsonify(flashcards)
    except:
        # Fallback flashcards if database not available
        return jsonify([
            {
                'front': 'Pseudobulb',
                'back': 'Thickened stem structure of orchids that stores water and nutrients',
                'pronunciation': '',
                'example': 'Cattleya pseudobulbs become wrinkled when the plant needs water',
                'difficulty': 'beginner',
                'category': 'botanical'
            },
            {
                'front': 'Epiphyte',
                'back': 'Plant that grows on another plant but is not parasitic',
                'pronunciation': 'EP-ih-fyte',
                'example': 'Most tropical orchids are epiphytes growing on tree branches',
                'difficulty': 'beginner',
                'category': 'botanical'
            }
        ])

# Register blueprint
app.register_blueprint(crossword_bp)