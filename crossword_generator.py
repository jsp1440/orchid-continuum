#!/usr/bin/env python3
"""
Crossword Puzzle Generator for Orchid Terms
Creates interactive crossword puzzles using orchid glossary
"""

import random
import json
from orchid_glossary import ORCHID_GLOSSARY, get_terms_by_length, get_random_terms

class CrosswordGenerator:
    def __init__(self, grid_size=15):
        self.grid_size = grid_size
        self.grid = [['' for _ in range(grid_size)] for _ in range(grid_size)]
        self.words = []
        self.clues = {}
        
    def generate_puzzle(self, word_count=8, difficulty='mixed'):
        """Generate a crossword puzzle"""
        # Select words based on difficulty
        if difficulty == 'easy':
            terms = {k: v for k, v in ORCHID_GLOSSARY.items() if v['difficulty'] == 'easy'}
        elif difficulty == 'medium':
            terms = {k: v for k, v in ORCHID_GLOSSARY.items() if v['difficulty'] == 'medium'}
        elif difficulty == 'hard':
            terms = {k: v for k, v in ORCHID_GLOSSARY.items() if v['difficulty'] == 'hard'}
        else:
            terms = ORCHID_GLOSSARY
        
        # Filter by length (3-12 characters work best)
        suitable_terms = {k: v for k, v in terms.items() if 3 <= v['length'] <= 12}
        
        # Select random terms
        selected = dict(random.sample(list(suitable_terms.items()), 
                                    min(word_count, len(suitable_terms))))
        
        # Create simple crossword layout
        puzzle_data = self._create_simple_layout(selected)
        
        return puzzle_data
    
    def _create_simple_layout(self, terms):
        """Create a simple crossword layout"""
        words = list(terms.keys())
        
        # Simple grid layout - place words in cross pattern
        puzzle = {
            'grid_size': 15,
            'words': [],
            'clues': {
                'across': {},
                'down': {}
            }
        }
        
        # Place first word horizontally in center
        if len(words) > 0:
            word1 = words[0].upper()
            start_row = 7
            start_col = 7 - len(word1) // 2
            puzzle['words'].append({
                'word': word1,
                'row': start_row,
                'col': start_col,
                'direction': 'across',
                'number': 1
            })
            puzzle['clues']['across'][1] = terms[words[0]]['definition']
        
        # Place second word vertically intersecting
        if len(words) > 1:
            word2 = words[1].upper()
            intersect_pos = len(word1) // 2
            start_row = 7 - len(word2) // 2
            start_col = start_col + intersect_pos
            puzzle['words'].append({
                'word': word2,
                'row': start_row,
                'col': start_col,
                'direction': 'down',
                'number': 2
            })
            puzzle['clues']['down'][2] = terms[words[1]]['definition']
        
        # Add remaining words in simple pattern
        clue_number = 3
        for i, word in enumerate(words[2:], 2):
            if i >= 8:  # Limit to 8 words for simplicity
                break
                
            word_upper = word.upper()
            
            # Alternate between across and down
            if i % 2 == 0:
                # Place horizontally
                row = 3 + (i - 2) * 2
                col = 2
                direction = 'across'
                puzzle['clues']['across'][clue_number] = terms[word]['definition']
            else:
                # Place vertically  
                row = 2
                col = 3 + (i - 3) * 2
                direction = 'down'
                puzzle['clues']['down'][clue_number] = terms[word]['definition']
            
            puzzle['words'].append({
                'word': word_upper,
                'row': row,
                'col': col,
                'direction': direction,
                'number': clue_number
            })
            
            clue_number += 1
        
        return puzzle

def generate_crossword_api(difficulty='mixed', size='medium'):
    """API function to generate crossword data"""
    word_count = {'small': 5, 'medium': 8, 'large': 12}.get(size, 8)
    
    generator = CrosswordGenerator()
    puzzle = generator.generate_puzzle(word_count, difficulty)
    
    return {
        'puzzle': puzzle,
        'success': True,
        'difficulty': difficulty,
        'word_count': len(puzzle['words'])
    }