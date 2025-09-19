"""
Educational Games Integration System
Transforms analyzed orchid photos into interactive learning experiences
"""

import os
import json
import random
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from app import db
from models import OrchidRecord

educational_games = Blueprint('educational_games', __name__)

class OrchidLearningSystem:
    """Convert analyzed orchid data into educational games and activities"""
    
    def __init__(self):
        self.game_types = {
            'match_picture': 'Match Picture to Picture',
            'match_name': 'Match Picture to Name',
            'crossword': 'Orchid Crossword Puzzle',
            'trivia_cards': 'Interactive Trivia Cards',
            'gallery_display': 'Educational Gallery with Captions'
        }
    
    def generate_matching_game_data(self, analyzed_results, game_type='match_picture'):
        """Generate data for picture matching games"""
        try:
            # Filter successful analyses with good identification
            good_results = [r for r in analyzed_results if 
                          r.get('processing_success', False) and 
                          r.get('identified_genus') and 
                          r.get('identified_species')]
            
            if len(good_results) < 4:
                return {'error': 'Need at least 4 successfully analyzed images for matching game'}
            
            # Select random subset for game
            game_items = random.sample(good_results, min(len(good_results), 12))
            
            if game_type == 'match_picture':
                # Picture to picture matching
                pairs = []
                for i in range(0, len(game_items), 2):
                    if i + 1 < len(game_items):
                        pairs.append({
                            'id': f'pair_{i//2}',
                            'image1': {
                                'filename': game_items[i]['filename'],
                                'genus': game_items[i]['identified_genus'],
                                'species': game_items[i]['identified_species']
                            },
                            'image2': {
                                'filename': game_items[i+1]['filename'],
                                'genus': game_items[i+1]['identified_genus'],
                                'species': game_items[i+1]['identified_species']
                            }
                        })
                
                return {
                    'game_type': 'Picture to Picture Matching',
                    'pairs': pairs,
                    'instructions': 'Match orchid pictures from the same genus or with similar characteristics'
                }
            
            elif game_type == 'match_name':
                # Picture to name matching
                cards = []
                for item in game_items:
                    cards.append({
                        'id': f'card_{len(cards)}',
                        'type': 'image',
                        'filename': item['filename'],
                        'match_id': f"name_{item['identified_genus']}_{item['identified_species']}"
                    })
                    cards.append({
                        'id': f'card_{len(cards)}',
                        'type': 'name',
                        'text': f"{item['identified_genus']} {item['identified_species']}",
                        'match_id': f"name_{item['identified_genus']}_{item['identified_species']}"
                    })
                
                # Shuffle cards
                random.shuffle(cards)
                
                return {
                    'game_type': 'Picture to Name Matching',
                    'cards': cards,
                    'instructions': 'Match orchid pictures with their scientific names'
                }
        
        except Exception as e:
            return {'error': f'Game generation failed: {str(e)}'}
    
    def generate_trivia_cards(self, analyzed_results):
        """Generate interactive trivia cards with comprehensive orchid information"""
        try:
            trivia_cards = []
            
            for result in analyzed_results:
                if not result.get('processing_success', False):
                    continue
                
                # Create comprehensive trivia card
                card = {
                    'id': f"trivia_{len(trivia_cards)}",
                    'image': result['filename'],
                    'title': f"{result.get('identified_genus', 'Unknown')} {result.get('identified_species', '')}",
                    'taxonomy': {
                        'genus': result.get('identified_genus', 'Unknown'),
                        'species': result.get('identified_species', ''),
                        'family': 'Orchidaceae',
                        'common_name': self.generate_common_name(result.get('identified_genus', ''))
                    },
                    'characteristics': {
                        'flowering_stage': result.get('flowering_stage', 'Unknown'),
                        'growth_habit': result.get('growth_habit', 'Unknown'),
                        'flower_color': result.get('flower_color', 'Not specified'),
                        'flower_size': result.get('flower_size', 'Not specified'),
                        'special_features': result.get('special_features', 'None noted')
                    },
                    'habitat': {
                        'origin': self.determine_origin(result.get('identified_genus', '')),
                        'climate': self.determine_climate(result.get('growth_habit', '')),
                        'habitat_type': result.get('growth_habit', 'Unknown')
                    },
                    'care_info': self.generate_care_info(result.get('growth_habit', '')),
                    'interesting_facts': self.generate_interesting_facts(result.get('identified_genus', '')),
                    'ai_analysis': result.get('ai_description', 'No analysis available'),
                    'photo_data': {
                        'date_taken': result.get('photo_datetime', 'Unknown'),
                        'location': result.get('gps_location', 'Unknown'),
                        'camera_info': result.get('camera_info', {})
                    }
                }
                
                trivia_cards.append(card)
            
            return {
                'cards': trivia_cards,
                'total_count': len(trivia_cards),
                'game_type': 'Interactive Trivia Cards'
            }
        
        except Exception as e:
            return {'error': f'Trivia card generation failed: {str(e)}'}
    
    def generate_crossword_data(self, analyzed_results):
        """Generate crossword puzzle from orchid data"""
        try:
            clues = []
            
            # Collect unique genera and characteristics
            genera = set()
            characteristics = set()
            
            for result in analyzed_results:
                if result.get('processing_success', False):
                    if result.get('identified_genus'):
                        genera.add(result['identified_genus'])
                    if result.get('growth_habit'):
                        characteristics.add(result['growth_habit'])
                    if result.get('flowering_stage'):
                        characteristics.add(result['flowering_stage'])
            
            # Generate across clues (genera)
            across_clues = []
            for i, genus in enumerate(list(genera)[:10]):  # Limit to 10
                across_clues.append({
                    'number': i + 1,
                    'clue': f"Orchid genus known for {self.generate_genus_hint(genus)}",
                    'answer': genus.upper(),
                    'length': len(genus)
                })
            
            # Generate down clues (characteristics)
            down_clues = []
            char_hints = {
                'Epiphytic': 'Growing on trees or other plants',
                'Terrestrial': 'Growing in soil or ground',
                'Full Bloom': 'Peak flowering stage',
                'Vegetative': 'Non-flowering growth phase'
            }
            
            for i, char in enumerate(list(characteristics)[:8]):  # Limit to 8
                hint = char_hints.get(char, f"Orchid characteristic: {char.lower()}")
                down_clues.append({
                    'number': i + 1,
                    'clue': hint,
                    'answer': char.upper().replace(' ', ''),
                    'length': len(char.replace(' ', ''))
                })
            
            return {
                'across': across_clues,
                'down': down_clues,
                'title': 'Gary Yong Gee Orchid Collection Crossword',
                'difficulty': 'Intermediate'
            }
        
        except Exception as e:
            return {'error': f'Crossword generation failed: {str(e)}'}
    
    def generate_gallery_captions(self, analyzed_results):
        """Generate detailed captions for gallery display"""
        try:
            gallery_items = []
            
            for result in analyzed_results:
                if not result.get('processing_success', False):
                    continue
                
                # Create comprehensive caption
                caption = {
                    'image': result['filename'],
                    'title': f"{result.get('identified_genus', 'Unknown')} {result.get('identified_species', '')}",
                    'scientific_name': f"<em>{result.get('identified_genus', 'Unknown')} {result.get('identified_species', '')}</em>",
                    'description': result.get('ai_description', 'A beautiful orchid specimen'),
                    'details': {
                        'Flowering Stage': result.get('flowering_stage', 'Unknown'),
                        'Growth Habit': result.get('growth_habit', 'Unknown'),
                        'Flower Characteristics': f"{result.get('flower_color', 'Various colors')}, {result.get('flower_size', 'medium')} size",
                        'Special Features': result.get('special_features', 'Standard orchid features'),
                        'Photography Date': result.get('photo_datetime', 'Date not available'),
                        'Location': result.get('gps_location', 'Location not recorded')
                    },
                    'attribution': 'Photo courtesy of Gary Yong Gee Orchid Collection',
                    'learn_more': 'Visit orchids.yonggee.name for more orchid information'
                }
                
                gallery_items.append(caption)
            
            return {
                'items': gallery_items,
                'total_count': len(gallery_items),
                'attribution': {
                    'photographer': 'Gary Yong Gee',
                    'website': 'https://orchids.yonggee.name',
                    'partner': 'Ralph Sawkins',
                    'collection': 'Gary Yong Gee Orchid Database'
                }
            }
        
        except Exception as e:
            return {'error': f'Gallery caption generation failed: {str(e)}'}
    
    def generate_common_name(self, genus):
        """Generate common names for orchid genera"""
        common_names = {
            'Phalaenopsis': 'Moth Orchid',
            'Cattleya': 'Corsage Orchid',
            'Dendrobium': 'Tree Orchid',
            'Oncidium': 'Dancing Lady Orchid',
            'Paphiopedilum': 'Lady Slipper Orchid',
            'Cymbidium': 'Boat Orchid',
            'Vanda': 'Vanda Orchid',
            'Epidendrum': 'Reed Orchid'
        }
        return common_names.get(genus, f'{genus} Orchid')
    
    def determine_origin(self, genus):
        """Determine likely geographic origin"""
        origins = {
            'Phalaenopsis': 'Southeast Asia',
            'Cattleya': 'Central and South America',
            'Dendrobium': 'Asia and Pacific Islands',
            'Oncidium': 'Central and South America',
            'Paphiopedilum': 'Southeast Asia',
            'Cymbidium': 'Asia',
            'Vanda': 'Southeast Asia',
            'Epidendrum': 'Americas'
        }
        return origins.get(genus, 'Tropical regions worldwide')
    
    def determine_climate(self, growth_habit):
        """Determine climate preferences"""
        if growth_habit == 'Epiphytic':
            return 'Warm, humid tropical climates'
        elif growth_habit == 'Terrestrial':
            return 'Temperate to tropical climates'
        else:
            return 'Varied climate preferences'
    
    def generate_care_info(self, growth_habit):
        """Generate basic care information"""
        if growth_habit == 'Epiphytic':
            return {
                'light': 'Bright, indirect light',
                'water': 'Water when dry, good drainage essential',
                'humidity': 'High humidity (50-70%)',
                'temperature': 'Warm temperatures (65-85°F)'
            }
        elif growth_habit == 'Terrestrial':
            return {
                'light': 'Bright to moderate light',
                'water': 'Regular watering, well-draining soil',
                'humidity': 'Moderate humidity (40-60%)',
                'temperature': 'Cool to warm temperatures (55-80°F)'
            }
        else:
            return {
                'light': 'Varies by species',
                'water': 'Varies by species',
                'humidity': 'Moderate to high humidity',
                'temperature': 'Species-dependent'
            }
    
    def generate_interesting_facts(self, genus):
        """Generate interesting facts about orchid genera"""
        facts = {
            'Phalaenopsis': [
                'Known as moth orchids because their flowers resemble flying moths',
                'One of the most popular houseplant orchids',
                'Can bloom for 2-6 months with proper care'
            ],
            'Cattleya': [
                'The classic corsage orchid used in formal wear',
                'National flower of several countries including Colombia',
                'Known for their large, showy, fragrant flowers'
            ],
            'Dendrobium': [
                'One of the largest orchid genera with over 1,800 species',
                'Name means "tree life" referring to their epiphytic nature',
                'Some species lose their leaves seasonally'
            ]
        }
        return facts.get(genus, [f'{genus} orchids are fascinating members of the orchid family'])
    
    def generate_genus_hint(self, genus):
        """Generate hints for crossword clues"""
        hints = {
            'Phalaenopsis': 'moth-like flowers',
            'Cattleya': 'large, showy blooms',
            'Dendrobium': 'tree-dwelling habits',
            'Oncidium': 'dancing lady appearance',
            'Paphiopedilum': 'slipper-shaped flowers'
        }
        return hints.get(genus, 'beautiful flowers')

# Initialize learning system
learning_system = OrchidLearningSystem()

@educational_games.route('/learning-activities')
def learning_activities_dashboard():
    """Dashboard for educational activities"""
    return render_template('educational_games/activities_dashboard.html')

@educational_games.route('/api/generate-activities', methods=['POST'])
def generate_educational_activities():
    """Generate educational activities from analyzed data"""
    try:
        data = request.json
        analyzed_results = data.get('analyzed_results', [])
        selected_activities = data.get('activities', [])
        
        activities = {}
        
        # Generate selected activities
        for activity in selected_activities:
            if activity == 'match_picture':
                activities['match_picture'] = learning_system.generate_matching_game_data(
                    analyzed_results, 'match_picture')
            elif activity == 'match_name':
                activities['match_name'] = learning_system.generate_matching_game_data(
                    analyzed_results, 'match_name')
            elif activity == 'trivia_cards':
                activities['trivia_cards'] = learning_system.generate_trivia_cards(analyzed_results)
            elif activity == 'crossword':
                activities['crossword'] = learning_system.generate_crossword_data(analyzed_results)
            elif activity == 'gallery_display':
                activities['gallery_display'] = learning_system.generate_gallery_captions(analyzed_results)
        
        return jsonify({
            'success': True,
            'activities': activities,
            'message': f'Generated {len(activities)} educational activities'
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@educational_games.route('/matching-game/<game_type>')
def matching_game(game_type):
    """Display matching game interface"""
    return render_template('educational_games/matching_game.html', game_type=game_type)

@educational_games.route('/trivia-cards')
def trivia_cards():
    """Display trivia cards interface"""
    return render_template('educational_games/trivia_cards.html')

@educational_games.route('/crossword-puzzle')
def crossword_puzzle():
    """Display crossword puzzle interface"""
    return render_template('educational_games/crossword_puzzle.html')

@educational_games.route('/educational-gallery')
def educational_gallery():
    """Display educational gallery with detailed captions"""
    return render_template('educational_games/educational_gallery.html')

@educational_games.route('/attributions')
def attributions_page():
    """Display acknowledgments and attributions"""
    return render_template('educational_games/attributions.html')