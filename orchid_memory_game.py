from flask import Blueprint, render_template, request, jsonify, session
from app import db
from models import OrchidRecord, User, GameScore, UserBadge
import random
import logging
from datetime import datetime, timedelta
from sqlalchemy import func, desc

logger = logging.getLogger(__name__)

orchid_memory_bp = Blueprint('orchid_memory', __name__)

class OrchidMemoryGame:
    def __init__(self):
        self.difficulty_levels = {
            'easy': {
                'name': 'Picture Matching',
                'description': 'Match identical orchid photos',
                'grid_size': 4,  # 4x4 = 16 cards (8 pairs)
                'time_limit': 120,  # 2 minutes
                'points_base': 100
            },
            'medium': {
                'name': 'Genus Matching', 
                'description': 'Match orchid photos with their genus names',
                'grid_size': 4,  # 4x4 = 16 cards (8 pairs)
                'time_limit': 180,  # 3 minutes
                'points_base': 200
            },
            'hard': {
                'name': 'Species Matching',
                'description': 'Match orchid photos with full scientific names',
                'grid_size': 5,  # 5x4 = 20 cards (10 pairs) 
                'time_limit': 240,  # 4 minutes
                'points_base': 300
            }
        }
        
    def generate_game_data(self, difficulty='easy', game_id=None):
        """Generate game cards based on difficulty level"""
        if game_id is None:
            game_id = f"game_{datetime.now().timestamp()}"
            
        level_config = self.difficulty_levels[difficulty]
        grid_size = level_config['grid_size']
        pairs_needed = (grid_size * grid_size) // 2
        
        # Get random orchids with photos from database
        orchids = (OrchidRecord.query
                  .filter(OrchidRecord.google_drive_id.isnot(None))
                  .filter(OrchidRecord.genus.isnot(None))
                  .order_by(func.random())
                  .limit(pairs_needed)
                  .all())
        
        if len(orchids) < pairs_needed:
            # Fallback: repeat orchids if not enough unique ones
            while len(orchids) < pairs_needed:
                orchids.extend(orchids[:pairs_needed - len(orchids)])
        
        cards = []
        card_id = 1
        
        for orchid in orchids[:pairs_needed]:
            if difficulty == 'easy':
                # Picture matching - two identical cards
                card_data = {
                    'type': 'image',
                    'image_url': f'/api/drive-photo/{orchid.google_drive_id}',
                    'match_value': orchid.id,
                    'display_text': '',
                    'orchid_data': {
                        'genus': orchid.genus,
                        'species': orchid.species or '',
                        'scientific_name': f"{orchid.genus} {orchid.species or ''}".strip(),
                        'common_name': orchid.common_name or ''
                    }
                }
                
                # Add two identical cards
                cards.append({**card_data, 'id': card_id, 'pair_id': orchid.id})
                card_id += 1
                cards.append({**card_data, 'id': card_id, 'pair_id': orchid.id})
                card_id += 1
                
            elif difficulty == 'medium':
                # Genus matching - photo + genus text
                cards.append({
                    'id': card_id,
                    'type': 'image',
                    'image_url': f'/api/drive-photo/{orchid.google_drive_id}',
                    'match_value': orchid.genus,
                    'pair_id': orchid.genus,
                    'display_text': '',
                    'orchid_data': {
                        'genus': orchid.genus,
                        'species': orchid.species or '',
                        'scientific_name': f"{orchid.genus} {orchid.species or ''}".strip()
                    }
                })
                card_id += 1
                
                cards.append({
                    'id': card_id,
                    'type': 'text',
                    'image_url': '',
                    'match_value': orchid.genus,
                    'pair_id': orchid.genus,
                    'display_text': orchid.genus,
                    'orchid_data': {
                        'genus': orchid.genus,
                        'species': orchid.species or '',
                        'scientific_name': f"{orchid.genus} {orchid.species or ''}".strip()
                    }
                })
                card_id += 1
                
            elif difficulty == 'hard':
                # Species matching - photo + full scientific name
                scientific_name = f"{orchid.genus} {orchid.species or ''}".strip()
                cards.append({
                    'id': card_id,
                    'type': 'image',
                    'image_url': f'/api/drive-photo/{orchid.google_drive_id}',
                    'match_value': scientific_name,
                    'pair_id': scientific_name,
                    'display_text': '',
                    'orchid_data': {
                        'genus': orchid.genus,
                        'species': orchid.species or '',
                        'scientific_name': scientific_name,
                        'common_name': orchid.common_name or ''
                    }
                })
                card_id += 1
                
                cards.append({
                    'id': card_id,
                    'type': 'text',
                    'image_url': '',
                    'match_value': scientific_name,
                    'pair_id': scientific_name,
                    'display_text': scientific_name,
                    'orchid_data': {
                        'genus': orchid.genus,
                        'species': orchid.species or '',
                        'scientific_name': scientific_name,
                        'common_name': orchid.common_name or ''
                    }
                })
                card_id += 1
        
        # Shuffle cards
        random.shuffle(cards)
        
        return {
            'game_id': game_id,
            'difficulty': difficulty,
            'level_config': level_config,
            'cards': cards,
            'total_pairs': pairs_needed,
            'grid_size': grid_size
        }

    def calculate_score(self, difficulty, time_taken, moves_made, pairs_found):
        """Calculate game score with bonuses"""
        level_config = self.difficulty_levels[difficulty]
        base_points = level_config['points_base']
        time_limit = level_config['time_limit']
        
        # Base score
        score = base_points * pairs_found
        
        # Time bonus (faster = more points)
        time_remaining = max(0, time_limit - time_taken)
        time_bonus = int(time_remaining * 2)  # 2 points per second remaining
        
        # Efficiency bonus (fewer moves = more points)
        perfect_moves = pairs_found * 2  # Minimum possible moves
        if moves_made <= perfect_moves * 1.5:  # Within 50% of perfect
            efficiency_bonus = int((perfect_moves * 2 - moves_made) * 5)
        else:
            efficiency_bonus = 0
            
        efficiency_bonus = max(0, efficiency_bonus)  # Don't allow negative bonus
        
        total_score = score + time_bonus + efficiency_bonus
        
        return {
            'total_score': max(0, total_score),
            'base_score': score,
            'time_bonus': time_bonus,
            'efficiency_bonus': efficiency_bonus,
            'time_taken': time_taken,
            'moves_made': moves_made
        }

# Initialize game system
memory_game = OrchidMemoryGame()

# Routes
@orchid_memory_bp.route('/games/memory')
def memory_game_home():
    """Memory game home page with level selection"""
    return render_template('games/memory_game.html', 
                         difficulty_levels=memory_game.difficulty_levels)

@orchid_memory_bp.route('/games/memory/<difficulty>')
def play_memory_game(difficulty):
    """Start a new memory game at specified difficulty"""
    if difficulty not in memory_game.difficulty_levels:
        difficulty = 'easy'
    
    # Generate new game
    game_data = memory_game.generate_game_data(difficulty)
    
    # Store game session
    session[f'memory_game_{game_data["game_id"]}'] = {
        'difficulty': difficulty,
        'start_time': datetime.now().timestamp(),
        'moves_made': 0,
        'pairs_found': 0,
        'total_pairs': game_data['total_pairs']
    }
    
    return render_template('games/memory_game_play.html', 
                         game_data=game_data,
                         difficulty=difficulty)

@orchid_memory_bp.route('/api/games/memory/move', methods=['POST'])
def record_game_move():
    """Record a game move and check for matches"""
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        card1_id = data.get('card1_id')
        card2_id = data.get('card2_id')
        card1_value = data.get('card1_value')
        card2_value = data.get('card2_value')
        
        game_session_key = f'memory_game_{game_id}'
        if game_session_key not in session:
            return jsonify({'success': False, 'error': 'Game session not found'}), 400
        
        # Update game state
        game_session = session[game_session_key]
        game_session['moves_made'] += 1
        
        # Check if cards match
        is_match = card1_value == card2_value
        if is_match:
            game_session['pairs_found'] += 1
        
        # Check if game is complete
        is_complete = game_session['pairs_found'] >= game_session['total_pairs']
        
        result = {
            'success': True,
            'is_match': is_match,
            'is_complete': is_complete,
            'pairs_found': game_session['pairs_found'],
            'moves_made': game_session['moves_made']
        }
        
        if is_complete:
            # Calculate final score
            time_taken = datetime.now().timestamp() - game_session['start_time']
            score_data = memory_game.calculate_score(
                game_session['difficulty'],
                int(time_taken),
                game_session['moves_made'],
                game_session['pairs_found']
            )
            
            result.update(score_data)
            
            # Save high score (if user is logged in)
            if session.get('user_id'):
                try:
                    new_score = GameScore(
                        user_id=session['user_id'],
                        game_type='memory',
                        difficulty=game_session['difficulty'],
                        score=score_data['total_score'],
                        time_taken=int(time_taken),
                        moves_made=game_session['moves_made'],
                        game_metadata={
                            'pairs_found': game_session['pairs_found'],
                            'base_score': score_data['base_score'],
                            'time_bonus': score_data['time_bonus'],
                            'efficiency_bonus': score_data['efficiency_bonus']
                        }
                    )
                    db.session.add(new_score)
                    db.session.commit()
                    
                    # Check for new badges
                    badges_earned = check_badge_achievements(session['user_id'], score_data, game_session)
                    result['badges_earned'] = badges_earned
                    
                except Exception as e:
                    logger.error(f"Error saving game score: {e}")
        
        # Update session
        session[game_session_key] = game_session
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error recording game move: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@orchid_memory_bp.route('/api/games/memory/leaderboard/<difficulty>')
def get_memory_leaderboard(difficulty):
    """Get leaderboard for memory game"""
    try:
        # Get top 10 scores for this difficulty
        leaderboard = (db.session.query(GameScore, User)
                      .join(User, GameScore.user_id == User.id)
                      .filter(GameScore.game_type == 'memory')
                      .filter(GameScore.difficulty == difficulty)
                      .order_by(desc(GameScore.score))
                      .limit(10)
                      .all())
        
        results = []
        for score, user in leaderboard:
            results.append({
                'rank': len(results) + 1,
                'username': user.username if hasattr(user, 'username') else f"Player {user.id}",
                'score': score.score,
                'time_taken': score.time_taken,
                'moves_made': score.moves_made,
                'date': score.created_at.strftime('%Y-%m-%d'),
                'efficiency': f"{score.game_metadata.get('efficiency_bonus', 0):,}" if score.game_metadata else "0"
            })
        
        return jsonify({
            'success': True,
            'leaderboard': results,
            'difficulty': difficulty
        })
        
    except Exception as e:
        logger.error(f"Error getting leaderboard: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def check_badge_achievements(user_id, score_data, game_session):
    """Check and award badges for game achievements"""
    badges_earned = []
    
    try:
        # Define badge criteria
        badge_criteria = {
            'memory_rookie': {
                'name': 'Memory Rookie',
                'description': 'Complete your first memory game',
                'icon': 'brain',
                'check': lambda: GameScore.query.filter_by(user_id=user_id, game_type='memory').count() == 1
            },
            'speed_demon': {
                'name': 'Speed Demon',
                'description': 'Complete a hard game in under 2 minutes',
                'icon': 'zap',
                'check': lambda: game_session['difficulty'] == 'hard' and score_data['time_taken'] < 120
            },
            'perfect_memory': {
                'name': 'Perfect Memory',
                'description': 'Complete a game with perfect efficiency',
                'icon': 'star',
                'check': lambda: game_session['moves_made'] <= game_session['total_pairs'] * 2
            },
            'genus_master': {
                'name': 'Genus Master',
                'description': 'Score over 400 points in genus matching',
                'icon': 'award',
                'check': lambda: game_session['difficulty'] == 'medium' and score_data['total_score'] >= 400
            },
            'species_expert': {
                'name': 'Species Expert',
                'description': 'Score over 600 points in species matching',
                'icon': 'target',
                'check': lambda: game_session['difficulty'] == 'hard' and score_data['total_score'] >= 600
            }
        }
        
        for badge_key, badge_info in badge_criteria.items():
            # Check if user already has this badge
            existing_badge = UserBadge.query.filter_by(
                user_id=user_id, 
                badge_type='memory_game',
                badge_key=badge_key
            ).first()
            
            if not existing_badge and badge_info['check']():
                # Award new badge
                new_badge = UserBadge(
                    user_id=user_id,
                    badge_type='memory_game',
                    badge_key=badge_key,
                    badge_data={
                        'name': badge_info['name'],
                        'description': badge_info['description'],
                        'icon': badge_info['icon'],
                        'earned_date': datetime.now().isoformat(),
                        'game_score': score_data['total_score'],
                        'difficulty': game_session['difficulty']
                    }
                )
                
                db.session.add(new_badge)
                badges_earned.append(badge_info)
        
        db.session.commit()
        
    except Exception as e:
        logger.error(f"Error checking badge achievements: {e}")
        
    return badges_earned

logger.info("Orchid Memory Game System initialized successfully")