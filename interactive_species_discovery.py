#!/usr/bin/env python3
"""
Interactive Orchid Species Discovery Gamification System
========================================================
The Orchid Continuum - Five Cities Orchid Society

Features:
- Progressive discovery challenges with real orchid data
- Species unlock system with achievement rewards
- Interactive photo identification challenges
- Streak tracking and bonus multipliers
- Discovery missions and seasonal challenges
- Real-time scoring with leaderboards
- Educational hints and learning progression
"""

import os
import json
import random
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from flask import Blueprint, render_template, jsonify, request, session
from models import OrchidRecord, GameScore, UserBadge, db
from leaderboard import GameLeaderboard
import uuid

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

discovery_bp = Blueprint('discovery', __name__, url_prefix='/discovery')

class OrchidSpeciesDiscoveryEngine:
    """
    Core engine for interactive orchid species discovery gamification
    """
    
    def __init__(self):
        self.discovery_categories = {
            'beginner': {
                'name': 'Orchid Explorer',
                'description': 'Start your orchid discovery journey',
                'unlock_threshold': 0,
                'species_pool': ['Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium'],
                'points_base': 100,
                'hint_level': 'detailed'
            },
            'intermediate': {
                'name': 'Species Detective',
                'description': 'Discover intermediate orchid varieties',
                'unlock_threshold': 10,
                'species_pool': ['Masdevallia', 'Bulbophyllum', 'Angraecum', 'Pleurothallis'],
                'points_base': 200,
                'hint_level': 'moderate'
            },
            'advanced': {
                'name': 'Orchid Master',
                'description': 'Challenge yourself with rare species',
                'unlock_threshold': 25,
                'species_pool': ['Disa', 'Cypripedium', 'Paphiopedilum', 'Coelogyne'],
                'points_base': 400,
                'hint_level': 'minimal'
            },
            'expert': {
                'name': 'Taxonomist',
                'description': 'Master the most challenging species',
                'unlock_threshold': 50,
                'species_pool': ['Pterostylis', 'Spiranthes', 'Goodyera', 'Habenaria'],
                'points_base': 800,
                'hint_level': 'expert'
            }
        }
        
        self.challenge_types = {
            'photo_id': {
                'name': 'Photo Identification',
                'description': 'Identify orchid species from photos',
                'points_multiplier': 1.0
            },
            'genus_match': {
                'name': 'Genus Matching',
                'description': 'Match orchids to their genus',
                'points_multiplier': 0.8
            },
            'habitat_guess': {
                'name': 'Habitat Detective',
                'description': 'Guess the native habitat',
                'points_multiplier': 1.2
            },
            'bloom_time': {
                'name': 'Flowering Calendar',
                'description': 'Predict when orchids bloom',
                'points_multiplier': 1.1
            },
            'rapid_fire': {
                'name': 'Rapid Fire Round',
                'description': 'Quick identification challenges',
                'points_multiplier': 1.5
            }
        }
        
        self.achievements = {
            'first_discovery': {'name': 'First Discovery', 'points': 50, 'icon': '🌱'},
            'genus_expert': {'name': 'Genus Expert', 'points': 200, 'icon': '🔬'},
            'streak_master': {'name': 'Streak Master', 'points': 300, 'icon': '🔥'},
            'photo_detective': {'name': 'Photo Detective', 'points': 150, 'icon': '📸'},
            'speed_demon': {'name': 'Speed Demon', 'points': 250, 'icon': '⚡'},
            'diversity_champion': {'name': 'Diversity Champion', 'points': 400, 'icon': '🌈'},
            'perfect_score': {'name': 'Perfect Score', 'points': 500, 'icon': '💎'},
            'weekend_warrior': {'name': 'Weekend Warrior', 'points': 100, 'icon': '⭐'},
            'daily_discoverer': {'name': 'Daily Discoverer', 'points': 75, 'icon': '📅'},
            'orchid_scholar': {'name': 'Orchid Scholar', 'points': 350, 'icon': '🎓'}
        }
        
    def get_user_discovery_session(self, player_name: str = None) -> Dict:
        """Get or create user discovery session"""
        session_key = 'orchid_discovery_session'
        
        if session_key not in session:
            session[session_key] = {
                'session_id': f"discovery_{uuid.uuid4().hex[:8]}",
                'player_name': player_name or 'Anonymous Explorer',
                'level': 'beginner',
                'total_discoveries': 0,
                'current_streak': 0,
                'longest_streak': 0,
                'total_points': 0,
                'discovered_species': set(),
                'unlocked_achievements': set(),
                'daily_progress': {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'discoveries': 0,
                    'points': 0
                },
                'current_challenge': None,
                'challenge_history': []
            }
        
        # Reset daily progress if new day
        user_session = session[session_key]
        today = datetime.now().strftime('%Y-%m-%d')
        if user_session['daily_progress']['date'] != today:
            user_session['daily_progress'] = {
                'date': today,
                'discoveries': 0,
                'points': 0
            }
        
        # Convert sets to lists for JSON compatibility
        if isinstance(user_session['discovered_species'], list):
            user_session['discovered_species'] = set(user_session['discovered_species'])
        if isinstance(user_session['unlocked_achievements'], list):
            user_session['unlocked_achievements'] = set(user_session['unlocked_achievements'])
            
        return user_session
    
    def generate_discovery_challenge(self, level: str = 'beginner', challenge_type: str = 'photo_id') -> Dict:
        """Generate a new discovery challenge based on level and type"""
        
        level_config = self.discovery_categories.get(level, self.discovery_categories['beginner'])
        challenge_config = self.challenge_types.get(challenge_type, self.challenge_types['photo_id'])
        
        # Get orchids from the specified genera for this level
        target_genera = level_config['species_pool']
        
        # Query database for orchids with photos in target genera
        orchids = (OrchidRecord.query
                  .filter(OrchidRecord.google_drive_id.isnot(None))
                  .filter(OrchidRecord.genus.in_(target_genera))
                  .order_by(db.func.random())
                  .limit(20)
                  .all())
        
        if not orchids:
            # Fallback to any orchids with photos
            orchids = (OrchidRecord.query
                      .filter(OrchidRecord.google_drive_id.isnot(None))
                      .order_by(db.func.random())
                      .limit(20)
                      .all())
        
        if len(orchids) < 4:
            return {'error': 'Not enough orchid data available'}
        
        # Select target orchid and create distractors
        target_orchid = random.choice(orchids)
        distractors = [o for o in orchids if o.id != target_orchid.id][:3]
        
        challenge_id = f"challenge_{uuid.uuid4().hex[:8]}"
        
        if challenge_type == 'photo_id':
            return self._create_photo_identification_challenge(target_orchid, distractors, level_config, challenge_config, challenge_id)
        elif challenge_type == 'genus_match':
            return self._create_genus_matching_challenge(target_orchid, distractors, level_config, challenge_config, challenge_id)
        elif challenge_type == 'habitat_guess':
            return self._create_habitat_challenge(target_orchid, distractors, level_config, challenge_config, challenge_id)
        elif challenge_type == 'bloom_time':
            return self._create_bloom_time_challenge(target_orchid, distractors, level_config, challenge_config, challenge_id)
        else:
            return self._create_rapid_fire_challenge(orchids, level_config, challenge_config, challenge_id)
    
    def _create_photo_identification_challenge(self, target: OrchidRecord, distractors: List[OrchidRecord], 
                                             level_config: Dict, challenge_config: Dict, challenge_id: str) -> Dict:
        """Create photo identification challenge"""
        
        # Create answer options
        options = [target] + distractors
        random.shuffle(options)
        
        correct_answer = next(i for i, opt in enumerate(options) if opt.id == target.id)
        
        # Generate hints based on level
        hints = self._generate_hints(target, level_config['hint_level'])
        
        return {
            'challenge_id': challenge_id,
            'type': 'photo_id',
            'level': level_config['name'],
            'title': 'Identify This Orchid Species',
            'description': challenge_config['description'],
            'image_url': f'/api/drive-photo/{target.google_drive_id}',
            'question': 'What species is shown in this photo?',
            'options': [
                {
                    'id': i,
                    'text': f"{opt.genus} {opt.species or 'sp.'}" if opt.species else f"{opt.genus} species",
                    'scientific_name': f"{opt.genus} {opt.species or ''}".strip()
                }
                for i, opt in enumerate(options)
            ],
            'correct_answer': correct_answer,
            'hints': hints,
            'points_possible': int(level_config['points_base'] * challenge_config['points_multiplier']),
            'time_limit': 60,
            'target_data': {
                'id': target.id,
                'genus': target.genus,
                'species': target.species,
                'common_name': target.common_name,
                'description': target.ai_description,
                'habitat': target.region,
                'cultural_notes': target.cultural_notes
            }
        }
    
    def _create_genus_matching_challenge(self, target: OrchidRecord, distractors: List[OrchidRecord],
                                       level_config: Dict, challenge_config: Dict, challenge_id: str) -> Dict:
        """Create genus matching challenge"""
        
        # Get unique genera from distractors
        genera_options = [target.genus]
        for d in distractors:
            if d.genus and d.genus not in genera_options:
                genera_options.append(d.genus)
        
        # Add more random genera if needed
        if len(genera_options) < 4:
            more_genera = (db.session.query(OrchidRecord.genus.distinct())
                          .filter(OrchidRecord.genus.isnot(None))
                          .filter(~OrchidRecord.genus.in_(genera_options))
                          .order_by(db.func.random())
                          .limit(4 - len(genera_options))
                          .all())
            genera_options.extend([g[0] for g in more_genera])
        
        random.shuffle(genera_options)
        correct_answer = genera_options.index(target.genus)
        
        hints = self._generate_genus_hints(target, level_config['hint_level'])
        
        return {
            'challenge_id': challenge_id,
            'type': 'genus_match',
            'level': level_config['name'],
            'title': 'Match the Genus',
            'description': challenge_config['description'],
            'image_url': f'/api/drive-photo/{target.google_drive_id}',
            'question': 'What genus does this orchid belong to?',
            'options': [
                {
                    'id': i,
                    'text': genus,
                    'scientific_name': genus
                }
                for i, genus in enumerate(genera_options)
            ],
            'correct_answer': correct_answer,
            'hints': hints,
            'points_possible': int(level_config['points_base'] * challenge_config['points_multiplier']),
            'time_limit': 45,
            'target_data': {
                'id': target.id,
                'genus': target.genus,
                'species': target.species,
                'description': target.ai_description
            }
        }
    
    def _create_habitat_challenge(self, target: OrchidRecord, distractors: List[OrchidRecord],
                                level_config: Dict, challenge_config: Dict, challenge_id: str) -> Dict:
        """Create habitat guessing challenge"""
        
        # Predefined habitat options for variety
        habitat_options = [
            'Tropical rainforest',
            'Temperate woodland',
            'Mountain meadow',
            'Desert oasis',
            'Cloud forest',
            'Mangrove swamp',
            'Alpine tundra',
            'Coastal dunes'
        ]
        
        # Try to use target's actual habitat if available
        target_habitat = target.region or 'Tropical rainforest'
        if target_habitat not in habitat_options:
            habitat_options[0] = target_habitat
        
        random.shuffle(habitat_options)
        habitat_options = habitat_options[:4]
        
        # Ensure target habitat is in options
        if target_habitat not in habitat_options:
            habitat_options[0] = target_habitat
        
        correct_answer = habitat_options.index(target_habitat)
        
        hints = self._generate_habitat_hints(target, level_config['hint_level'])
        
        return {
            'challenge_id': challenge_id,
            'type': 'habitat_guess',
            'level': level_config['name'],
            'title': 'Habitat Detective',
            'description': challenge_config['description'],
            'image_url': f'/api/drive-photo/{target.google_drive_id}',
            'question': 'Where would you typically find this orchid in nature?',
            'options': [
                {
                    'id': i,
                    'text': habitat,
                    'scientific_name': habitat
                }
                for i, habitat in enumerate(habitat_options)
            ],
            'correct_answer': correct_answer,
            'hints': hints,
            'points_possible': int(level_config['points_base'] * challenge_config['points_multiplier']),
            'time_limit': 50,
            'target_data': {
                'id': target.id,
                'genus': target.genus,
                'species': target.species,
                'habitat': target.region,
                'description': target.ai_description
            }
        }
    
    def _create_bloom_time_challenge(self, target: OrchidRecord, distractors: List[OrchidRecord],
                                   level_config: Dict, challenge_config: Dict, challenge_id: str) -> Dict:
        """Create bloom time prediction challenge"""
        
        season_options = [
            'Spring (March-May)',
            'Summer (June-August)', 
            'Fall (September-November)',
            'Winter (December-February)',
            'Year-round bloomer',
            'Multiple seasons'
        ]
        
        # Try to extract bloom time from cultural notes or description
        bloom_season = 'Spring (March-May)'  # Default
        if target.cultural_notes:
            notes = target.cultural_notes.lower()
            if 'summer' in notes or 'june' in notes or 'july' in notes or 'august' in notes:
                bloom_season = 'Summer (June-August)'
            elif 'fall' in notes or 'autumn' in notes or 'september' in notes or 'october' in notes or 'november' in notes:
                bloom_season = 'Fall (September-November)'
            elif 'winter' in notes or 'december' in notes or 'january' in notes or 'february' in notes:
                bloom_season = 'Winter (December-February)'
            elif 'year' in notes and 'round' in notes:
                bloom_season = 'Year-round bloomer'
        
        correct_answer = season_options.index(bloom_season)
        
        hints = self._generate_bloom_hints(target, level_config['hint_level'])
        
        return {
            'challenge_id': challenge_id,
            'type': 'bloom_time',
            'level': level_config['name'],
            'title': 'Flowering Calendar',
            'description': challenge_config['description'],
            'image_url': f'/api/drive-photo/{target.google_drive_id}',
            'question': 'When does this orchid typically bloom?',
            'options': [
                {
                    'id': i,
                    'text': season,
                    'scientific_name': season
                }
                for i, season in enumerate(season_options)
            ],
            'correct_answer': correct_answer,
            'hints': hints,
            'points_possible': int(level_config['points_base'] * challenge_config['points_multiplier']),
            'time_limit': 40,
            'target_data': {
                'id': target.id,
                'genus': target.genus,
                'species': target.species,
                'bloom_season': bloom_season,
                'cultural_notes': target.cultural_notes
            }
        }
    
    def _create_rapid_fire_challenge(self, orchids: List[OrchidRecord], level_config: Dict, 
                                   challenge_config: Dict, challenge_id: str) -> Dict:
        """Create rapid fire round with multiple quick questions"""
        
        questions = []
        for i, orchid in enumerate(orchids[:5]):  # 5 quick questions
            questions.append({
                'id': i,
                'image_url': f'/api/drive-photo/{orchid.google_drive_id}',
                'question': 'Quick ID: What genus?',
                'correct_answer': orchid.genus,
                'options': self._get_rapid_fire_options(orchid.genus),
                'time_limit': 10  # 10 seconds per question
            })
        
        return {
            'challenge_id': challenge_id,
            'type': 'rapid_fire',
            'level': level_config['name'],
            'title': 'Rapid Fire Round',
            'description': 'Quick identification challenges - 10 seconds each!',
            'questions': questions,
            'total_questions': len(questions),
            'points_possible': int(level_config['points_base'] * challenge_config['points_multiplier']),
            'time_limit': len(questions) * 10,
            'hints': ['Trust your instincts!', 'Look for distinctive features', 'Focus on flower shape']
        }
    
    def _get_rapid_fire_options(self, correct_genus: str) -> List[str]:
        """Get genus options for rapid fire"""
        common_genera = ['Cattleya', 'Phalaenopsis', 'Dendrobium', 'Oncidium', 'Masdevallia', 'Bulbophyllum']
        options = [correct_genus]
        
        for genus in common_genera:
            if genus != correct_genus and genus not in options:
                options.append(genus)
            if len(options) >= 4:
                break
                
        random.shuffle(options)
        return options
    
    def _generate_hints(self, orchid: OrchidRecord, hint_level: str) -> List[str]:
        """Generate contextual hints based on orchid characteristics"""
        hints = []
        
        if hint_level == 'detailed':
            hints.extend([
                f"This orchid belongs to the {orchid.genus} genus",
                "Look at the flower shape and petal arrangement",
                "Consider the growth habit (sympodial vs monopodial)"
            ])
            if orchid.cultural_notes:
                hints.append("Check the growing conditions mentioned")
        
        elif hint_level == 'moderate':
            hints.extend([
                "Focus on the distinctive flower characteristics",
                "Consider the overall plant structure"
            ])
            if orchid.region:
                hints.append(f"Native to {orchid.region}")
        
        elif hint_level == 'minimal':
            hints.extend([
                "Look carefully at the flower details",
                "Trust your botanical knowledge"
            ])
        
        else:  # expert
            hints.extend([
                "No hints - you're an expert!",
                "Rely on your taxonomic expertise"
            ])
        
        return hints
    
    def _generate_genus_hints(self, orchid: OrchidRecord, hint_level: str) -> List[str]:
        """Generate genus-specific hints"""
        hints = []
        
        genus_characteristics = {
            'Cattleya': 'Large, showy flowers with prominent labellum',
            'Phalaenopsis': 'Moth-like flowers, monopodial growth',
            'Dendrobium': 'Cane-like pseudobulbs, diverse flower forms',
            'Oncidium': 'Dancing lady flowers, often yellow',
            'Masdevallia': 'Triangular sepals, no visible petals',
            'Bulbophyllum': 'Diverse family, often unusual fragrances'
        }
        
        if hint_level in ['detailed', 'moderate'] and orchid.genus in genus_characteristics:
            hints.append(genus_characteristics[orchid.genus])
        
        if hint_level == 'detailed':
            hints.extend([
                "Look at the flower structure",
                "Consider the growth pattern",
                "Note any distinctive features"
            ])
        
        return hints
    
    def _generate_habitat_hints(self, orchid: OrchidRecord, hint_level: str) -> List[str]:
        """Generate habitat-specific hints"""
        hints = []
        
        if hint_level == 'detailed':
            hints.extend([
                "Consider the flower adaptations",
                "Think about pollinator relationships",
                "Look for environmental clues in the plant structure"
            ])
        
        if orchid.cultural_notes and hint_level in ['detailed', 'moderate']:
            if 'cool' in orchid.cultural_notes.lower():
                hints.append("Prefers cooler temperatures")
            elif 'warm' in orchid.cultural_notes.lower():
                hints.append("Thrives in warmer conditions")
        
        return hints
    
    def _generate_bloom_hints(self, orchid: OrchidRecord, hint_level: str) -> List[str]:
        """Generate bloom time hints"""
        hints = []
        
        if hint_level == 'detailed':
            hints.extend([
                "Consider the natural habitat's climate",
                "Think about seasonal temperature changes",
                "Some orchids respond to day length"
            ])
        
        if orchid.cultural_notes and hint_level in ['detailed', 'moderate']:
            notes = orchid.cultural_notes.lower()
            if 'light' in notes:
                hints.append("Light levels affect blooming")
            if 'temperature' in notes:
                hints.append("Temperature changes trigger blooms")
        
        return hints
    
    def evaluate_challenge_answer(self, challenge_id: str, user_answer: int, time_taken: int = None) -> Dict:
        """Evaluate user's answer and update scoring"""
        
        user_session = self.get_user_discovery_session()
        
        # Find the challenge in history or current challenge
        challenge_data = user_session.get('current_challenge')
        if not challenge_data or challenge_data.get('challenge_id') != challenge_id:
            return {'error': 'Challenge not found or expired'}
        
        correct_answer = challenge_data['correct_answer']
        is_correct = user_answer == correct_answer
        
        # Calculate points
        base_points = challenge_data['points_possible']
        points_earned = 0
        
        if is_correct:
            points_earned = base_points
            
            # Time bonus (faster = more points)
            if time_taken and time_taken < challenge_data['time_limit']:
                time_bonus = int((challenge_data['time_limit'] - time_taken) / challenge_data['time_limit'] * base_points * 0.2)
                points_earned += time_bonus
            
            # Streak bonus
            if user_session['current_streak'] >= 5:
                streak_bonus = int(base_points * 0.1 * (user_session['current_streak'] - 4))
                points_earned = min(points_earned + streak_bonus, base_points * 2)  # Cap at 2x
        
        # Update user session
        user_session['total_discoveries'] += 1
        user_session['total_points'] += points_earned
        user_session['daily_progress']['discoveries'] += 1
        user_session['daily_progress']['points'] += points_earned
        
        if is_correct:
            user_session['current_streak'] += 1
            user_session['longest_streak'] = max(user_session['longest_streak'], user_session['current_streak'])
            
            # Add to discovered species
            target_data = challenge_data.get('target_data', {})
            species_key = f"{target_data.get('genus', 'Unknown')}_{target_data.get('species', 'sp')}"
            user_session['discovered_species'].add(species_key)
        else:
            user_session['current_streak'] = 0
        
        # Check for achievements
        new_achievements = self._check_achievements(user_session, is_correct, challenge_data)
        
        # Save updated session
        session['orchid_discovery_session'] = user_session
        
        # Submit score to leaderboard
        try:
            GameLeaderboard.submit_score(
                player_name=user_session['player_name'],
                game_type='species_discovery',
                score=points_earned,
                max_score=base_points * 2,  # Max possible with bonuses
                completion_time=time_taken,
                difficulty=user_session['level'],
                game_data={
                    'challenge_type': challenge_data['type'],
                    'correct': is_correct,
                    'streak': user_session['current_streak']
                }
            )
        except Exception as e:
            logger.error(f"Failed to submit score: {e}")
        
        return {
            'success': True,
            'correct': is_correct,
            'correct_answer': correct_answer,
            'points_earned': points_earned,
            'total_points': user_session['total_points'],
            'current_streak': user_session['current_streak'],
            'new_achievements': new_achievements,
            'explanation': self._generate_explanation(challenge_data, is_correct),
            'level_progress': self._calculate_level_progress(user_session)
        }
    
    def _check_achievements(self, user_session: Dict, is_correct: bool, challenge_data: Dict) -> List[Dict]:
        """Check for newly unlocked achievements"""
        new_achievements = []
        
        # First discovery
        if user_session['total_discoveries'] == 1 and 'first_discovery' not in user_session['unlocked_achievements']:
            new_achievements.append(self.achievements['first_discovery'])
            user_session['unlocked_achievements'].add('first_discovery')
        
        # Streak achievements
        if user_session['current_streak'] >= 10 and 'streak_master' not in user_session['unlocked_achievements']:
            new_achievements.append(self.achievements['streak_master'])
            user_session['unlocked_achievements'].add('streak_master')
        
        # Perfect score (full points)
        if is_correct and challenge_data.get('points_possible') > 0:
            if 'perfect_score' not in user_session['unlocked_achievements']:
                new_achievements.append(self.achievements['perfect_score'])
                user_session['unlocked_achievements'].add('perfect_score')
        
        # Photo detection expert
        if challenge_data.get('type') == 'photo_id' and user_session['total_discoveries'] >= 20:
            if 'photo_detective' not in user_session['unlocked_achievements']:
                new_achievements.append(self.achievements['photo_detective'])
                user_session['unlocked_achievements'].add('photo_detective')
        
        # Daily discoveries
        if user_session['daily_progress']['discoveries'] >= 5:
            if 'daily_discoverer' not in user_session['unlocked_achievements']:
                new_achievements.append(self.achievements['daily_discoverer'])
                user_session['unlocked_achievements'].add('daily_discoverer')
        
        return new_achievements
    
    def _generate_explanation(self, challenge_data: Dict, is_correct: bool) -> str:
        """Generate educational explanation"""
        target_data = challenge_data.get('target_data', {})
        
        explanation = f"The correct answer is {target_data.get('genus', 'Unknown')} {target_data.get('species', 'sp.')}. "
        
        if target_data.get('description'):
            explanation += f" {target_data['description'][:200]}..."
        
        if not is_correct:
            explanation += " Better luck next time! Keep studying those orchid characteristics."
        else:
            explanation += " Great job identifying this species correctly!"
        
        return explanation
    
    def _calculate_level_progress(self, user_session: Dict) -> Dict:
        """Calculate progress toward next level"""
        current_level = user_session['level']
        discoveries = user_session['total_discoveries']
        
        # Level thresholds
        level_order = ['beginner', 'intermediate', 'advanced', 'expert']
        current_index = level_order.index(current_level) if current_level in level_order else 0
        
        if current_index < len(level_order) - 1:
            next_level = level_order[current_index + 1]
            next_threshold = self.discovery_categories[next_level]['unlock_threshold']
            
            if discoveries >= next_threshold:
                user_session['level'] = next_level
                return {
                    'level_up': True,
                    'new_level': next_level,
                    'unlocked_challenges': list(self.challenge_types.keys())
                }
        
        # Calculate progress to next level
        next_level = level_order[min(current_index + 1, len(level_order) - 1)]
        next_threshold = self.discovery_categories[next_level]['unlock_threshold']
        
        return {
            'level_up': False,
            'current_level': current_level,
            'next_level': next_level if current_index < len(level_order) - 1 else None,
            'progress': min(discoveries / next_threshold * 100, 100) if next_threshold > 0 else 100,
            'discoveries_needed': max(0, next_threshold - discoveries)
        }

# Initialize the discovery engine
discovery_engine = OrchidSpeciesDiscoveryEngine()

@discovery_bp.route('/')
def discovery_home():
    """Discovery game homepage"""
    user_session = discovery_engine.get_user_discovery_session()
    
    return render_template('discovery/discovery_home.html', 
                         user_session=user_session,
                         discovery_categories=discovery_engine.discovery_categories,
                         challenge_types=discovery_engine.challenge_types,
                         achievements=discovery_engine.achievements)

@discovery_bp.route('/api/start-challenge', methods=['POST'])
def api_start_challenge():
    """Start a new discovery challenge"""
    data = request.get_json()
    level = data.get('level', 'beginner')
    challenge_type = data.get('challenge_type', 'photo_id')
    player_name = data.get('player_name', 'Anonymous Explorer')
    
    try:
        # Update user session with player name
        user_session = discovery_engine.get_user_discovery_session(player_name)
        user_session['player_name'] = player_name
        
        # Generate new challenge
        challenge = discovery_engine.generate_discovery_challenge(level, challenge_type)
        
        if 'error' in challenge:
            return jsonify({'success': False, 'error': challenge['error']}), 400
        
        # Store current challenge in session
        user_session['current_challenge'] = challenge
        session['orchid_discovery_session'] = user_session
        
        return jsonify({
            'success': True,
            'challenge': challenge,
            'user_progress': {
                'level': user_session['level'],
                'total_points': user_session['total_points'],
                'current_streak': user_session['current_streak'],
                'discoveries_today': user_session['daily_progress']['discoveries']
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting challenge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@discovery_bp.route('/api/submit-answer', methods=['POST'])
def api_submit_answer():
    """Submit answer for current challenge"""
    data = request.get_json()
    challenge_id = data.get('challenge_id')
    user_answer = data.get('answer')
    time_taken = data.get('time_taken')
    
    try:
        result = discovery_engine.evaluate_challenge_answer(challenge_id, user_answer, time_taken)
        
        if 'error' in result:
            return jsonify({'success': False, 'error': result['error']}), 400
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error submitting answer: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@discovery_bp.route('/api/user-stats')
def api_user_stats():
    """Get current user statistics"""
    try:
        user_session = discovery_engine.get_user_discovery_session()
        
        # Get leaderboard position
        try:
            leaderboard_data = GameLeaderboard.get_leaderboard('species_discovery', limit=100)
            user_rank = None
            for entry in leaderboard_data:
                if entry['player_name'] == user_session['player_name']:
                    user_rank = entry['rank']
                    break
        except:
            user_rank = None
        
        return jsonify({
            'success': True,
            'stats': {
                'player_name': user_session['player_name'],
                'level': user_session['level'],
                'total_discoveries': user_session['total_discoveries'],
                'total_points': user_session['total_points'],
                'current_streak': user_session['current_streak'],
                'longest_streak': user_session['longest_streak'],
                'species_discovered': len(user_session['discovered_species']),
                'achievements_unlocked': len(user_session['unlocked_achievements']),
                'daily_progress': user_session['daily_progress'],
                'leaderboard_rank': user_rank
            },
            'achievements': [
                {**discovery_engine.achievements[achievement], 'id': achievement}
                for achievement in user_session['unlocked_achievements']
            ]
        })
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@discovery_bp.route('/api/daily-challenge')
def api_daily_challenge():
    """Get today's special daily challenge"""
    try:
        # Create a special daily challenge with higher rewards
        today = datetime.now().strftime('%Y-%m-%d')
        random.seed(today)  # Consistent daily challenge
        
        challenge_types = list(discovery_engine.challenge_types.keys())
        daily_challenge_type = random.choice(challenge_types)
        
        challenge = discovery_engine.generate_discovery_challenge('intermediate', daily_challenge_type)
        
        if 'error' not in challenge:
            # Boost rewards for daily challenge
            challenge['points_possible'] = int(challenge['points_possible'] * 1.5)
            challenge['title'] = f"🌟 Daily Challenge: {challenge['title']}"
            challenge['is_daily'] = True
        
        return jsonify({
            'success': True,
            'daily_challenge': challenge,
            'date': today
        })
        
    except Exception as e:
        logger.error(f"Error generating daily challenge: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@discovery_bp.route('/leaderboard')
def discovery_leaderboard():
    """Discovery game leaderboard"""
    return render_template('discovery/leaderboard.html')

@discovery_bp.route('/api/leaderboard')
def api_discovery_leaderboard():
    """Get discovery game leaderboard"""
    try:
        time_period = request.args.get('time_period', 'all')
        limit = int(request.args.get('limit', 20))
        
        leaderboard_data = GameLeaderboard.get_leaderboard('species_discovery', limit, time_period)
        
        return jsonify({
            'success': True,
            'leaderboard': leaderboard_data,
            'time_period': time_period
        })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500