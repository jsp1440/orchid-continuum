#!/usr/bin/env python3
"""
Orchid Mahjong Game System
Multiplayer Mahjong with beautiful orchid tiles, chat, and leaderboards
"""

from flask import Blueprint, render_template, request, jsonify, session
from flask_login import login_required, current_user
from app import db, app
import random
import string
import json
from datetime import datetime
from models import MahjongGame, MahjongPlayer, GameChatMessage, User

mahjong_bp = Blueprint('orchid_mahjong_widget', __name__)

class OrchidMahjongEngine:
    def __init__(self):
        self.tile_layouts = {
            'classic': self._generate_classic_layout(),
            'pyramid': self._generate_pyramid_layout(),
            'butterfly': self._generate_butterfly_layout()
        }
        
        self.orchid_tiles = {
            # Cattleya suit (purple theme)
            'cattleya': [
                {'id': f'cattleya_{i}', 'suit': 'cattleya', 'number': i, 'symbol': '🌺', 'color': '#9B59B6'}
                for i in range(1, 10)
            ],
            # Dendrobium suit (blue theme)
            'dendrobium': [
                {'id': f'dendrobium_{i}', 'suit': 'dendrobium', 'number': i, 'symbol': '💐', 'color': '#3498DB'}
                for i in range(1, 10)
            ],
            # Phalaenopsis suit (pink theme)
            'phalaenopsis': [
                {'id': f'phalaenopsis_{i}', 'suit': 'phalaenopsis', 'number': i, 'symbol': '🦋', 'color': '#E91E63'}
                for i in range(1, 10)
            ],
            # Honor tiles (AOS Awards)
            'honors': [
                {'id': 'am_aos', 'suit': 'honors', 'type': 'AM/AOS', 'symbol': '🏆', 'color': '#F39C12'},
                {'id': 'fcc_aos', 'suit': 'honors', 'type': 'FCC/AOS', 'symbol': '🥇', 'color': '#E74C3C'},
                {'id': 'hcc_aos', 'suit': 'honors', 'type': 'HCC/AOS', 'symbol': '🎖️', 'color': '#27AE60'},
                {'id': 'cbr_aos', 'suit': 'honors', 'type': 'CBR/AOS', 'symbol': '📜', 'color': '#8E44AD'}
            ],
            # Dragon tiles (Growing Conditions)
            'dragons': [
                {'id': 'temp_dragon', 'suit': 'dragons', 'type': 'Temperature', 'symbol': '🌡️', 'color': '#E67E22'},
                {'id': 'light_dragon', 'suit': 'dragons', 'type': 'Light', 'symbol': '☀️', 'color': '#F1C40F'},
                {'id': 'water_dragon', 'suit': 'dragons', 'type': 'Water', 'symbol': '💧', 'color': '#3498DB'}
            ]
        }
    
    def _generate_classic_layout(self):
        """Generate classic Mahjong solitaire layout"""
        return {
            'name': 'Classic Turtle',
            'description': 'Traditional Mahjong solitaire layout',
            'layers': 5,
            'total_tiles': 144,
            'positions': self._create_turtle_positions()
        }
    
    def _generate_pyramid_layout(self):
        """Generate pyramid layout"""
        return {
            'name': 'Orchid Pyramid',
            'description': 'Beautiful pyramid arrangement',
            'layers': 6,
            'total_tiles': 140,
            'positions': self._create_pyramid_positions()
        }
    
    def _generate_butterfly_layout(self):
        """Generate butterfly layout"""
        return {
            'name': 'Butterfly Garden',
            'description': 'Elegant butterfly-shaped layout',
            'layers': 4,
            'total_tiles': 132,
            'positions': self._create_butterfly_positions()
        }
    
    def _create_turtle_positions(self):
        """Create classic turtle shape positions"""
        positions = []
        # This would contain the actual tile positions for the turtle layout
        # For now, creating a simplified grid
        for layer in range(5):
            for row in range(8):
                for col in range(16):
                    if self._is_valid_turtle_position(layer, row, col):
                        positions.append({
                            'layer': layer,
                            'row': row,
                            'col': col,
                            'x': col * 40 + layer * 2,
                            'y': row * 50 + layer * 2,
                            'z': layer
                        })
        return positions
    
    def _is_valid_turtle_position(self, layer, row, col):
        """Check if position is valid for turtle layout"""
        # Simplified turtle shape logic
        if layer == 0:  # Base layer
            return True
        elif layer == 1:
            return 1 <= row <= 6 and 1 <= col <= 14
        elif layer == 2:
            return 2 <= row <= 5 and 2 <= col <= 13
        elif layer == 3:
            return 3 <= row <= 4 and 6 <= col <= 9
        elif layer == 4:
            return row == 3 and col == 7
        return False
    
    def _create_pyramid_positions(self):
        """Create pyramid layout positions"""
        positions = []
        for layer in range(6):
            size = 12 - layer * 2
            start = layer
            for row in range(size):
                for col in range(size):
                    positions.append({
                        'layer': layer,
                        'row': start + row,
                        'col': start + col,
                        'x': (start + col) * 40 + layer * 2,
                        'y': (start + row) * 50 + layer * 2,
                        'z': layer
                    })
        return positions
    
    def _create_butterfly_positions(self):
        """Create butterfly layout positions"""
        positions = []
        # Simplified butterfly shape
        butterfly_pattern = [
            "  XX    XX  ",
            " XXXX  XXXX ",
            "XXXXXXXXXXXX",
            " XXXX  XXXX ",
            "  XX    XX  "
        ]
        
        for layer in range(4):
            for row, pattern_row in enumerate(butterfly_pattern):
                for col, char in enumerate(pattern_row):
                    if char == 'X':
                        positions.append({
                            'layer': layer,
                            'row': row,
                            'col': col,
                            'x': col * 40 + layer * 2,
                            'y': row * 50 + layer * 2,
                            'z': layer
                        })
        return positions
    
    def create_game_tiles(self, layout='classic'):
        """Create shuffled tiles for a new game"""
        layout_info = self.tile_layouts[layout]
        tiles_needed = layout_info['total_tiles']
        
        # Create tile pairs (each tile appears twice for matching)
        game_tiles = []
        tile_id = 0
        
        # Add numbered tiles (multiple copies to fill layout)
        all_tiles = []
        for suit in ['cattleya', 'dendrobium', 'phalaenopsis']:
            all_tiles.extend(self.orchid_tiles[suit])
        all_tiles.extend(self.orchid_tiles['honors'])
        all_tiles.extend(self.orchid_tiles['dragons'])
        
        # Generate enough tiles for the layout (each tile appears in pairs)
        while len(game_tiles) < tiles_needed:
            for tile in all_tiles:
                if len(game_tiles) >= tiles_needed:
                    break
                # Add 4 copies of each tile (standard Mahjong)
                for _ in range(4):
                    if len(game_tiles) >= tiles_needed:
                        break
                    game_tile = tile.copy()
                    game_tile['game_tile_id'] = tile_id
                    game_tile['matched'] = False
                    game_tile['position'] = None
                    game_tiles.append(game_tile)
                    tile_id += 1
        
        # Shuffle tiles
        random.shuffle(game_tiles)
        
        # Assign positions
        positions = layout_info['positions']
        for i, tile in enumerate(game_tiles):
            if i < len(positions):
                tile['position'] = positions[i]
        
        return game_tiles[:len(positions)]
    
    def can_match_tiles(self, tile1, tile2):
        """Check if two tiles can be matched"""
        # Same tile type can match
        if tile1['suit'] == tile2['suit']:
            if tile1['suit'] in ['cattleya', 'dendrobium', 'phalaenopsis']:
                return tile1['number'] == tile2['number']
            else:
                return tile1['id'] == tile2['id']
        return False
    
    def is_tile_playable(self, tile, all_tiles):
        """Check if a tile can be selected (not blocked)"""
        tile_pos = tile['position']
        if not tile_pos:
            return False
        
        # Check if tile is blocked by other tiles
        for other_tile in all_tiles:
            if other_tile['matched'] or other_tile['game_tile_id'] == tile['game_tile_id']:
                continue
            
            other_pos = other_tile['position']
            if not other_pos:
                continue
            
            # Check if other tile is on top
            if (other_pos['layer'] == tile_pos['layer'] + 1 and
                abs(other_pos['row'] - tile_pos['row']) <= 1 and
                abs(other_pos['col'] - tile_pos['col']) <= 1):
                return False
            
            # Check if other tile blocks from side
            if (other_pos['layer'] == tile_pos['layer'] and
                other_pos['row'] == tile_pos['row'] and
                abs(other_pos['col'] - tile_pos['col']) == 1):
                # Check if both sides are blocked
                left_blocked = any(
                    t['position'] and t['position']['layer'] == tile_pos['layer'] and
                    t['position']['row'] == tile_pos['row'] and
                    t['position']['col'] == tile_pos['col'] - 1 and not t['matched']
                    for t in all_tiles if t['game_tile_id'] != tile['game_tile_id']
                )
                right_blocked = any(
                    t['position'] and t['position']['layer'] == tile_pos['layer'] and
                    t['position']['row'] == tile_pos['row'] and
                    t['position']['col'] == tile_pos['col'] + 1 and not t['matched']
                    for t in all_tiles if t['game_tile_id'] != tile['game_tile_id']
                )
                if left_blocked and right_blocked:
                    return False
        
        return True

# Game management functions
def generate_room_code():
    """Generate unique 6-character room code"""
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not MahjongGame.query.filter_by(room_code=code).first():
            return code

# Flask routes
@mahjong_bp.route('/mahjong')
@login_required
def mahjong_lobby():
    """Display Mahjong game lobby"""
    return render_template('mahjong_lobby.html')

@mahjong_bp.route('/mahjong/game/<room_code>')
@login_required
def mahjong_game(room_code):
    """Display Mahjong game room"""
    game = MahjongGame.query.filter_by(room_code=room_code).first_or_404()
    return render_template('mahjong_game.html', game=game, room_code=room_code)

@mahjong_bp.route('/api/mahjong/create-room', methods=['POST'])
@login_required
def create_room():
    """Create new Mahjong game room"""
    data = request.get_json()
    max_players = data.get('max_players', 4)
    layout = data.get('layout', 'classic')
    
    room_code = generate_room_code()
    
    # Create new game
    game = MahjongGame(
        room_code=room_code,
        host_user_id=current_user.id,
        max_players=max_players,
        tile_set=json.dumps({'layout': layout, 'theme': 'orchid'})
    )
    
    db.session.add(game)
    db.session.commit()
    
    # Add host as first player
    player = MahjongPlayer(
        game_id=game.id,
        user_id=current_user.id,
        player_position=1
    )
    
    db.session.add(player)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'room_code': room_code,
        'game_id': game.id
    })

@mahjong_bp.route('/api/mahjong/join-room', methods=['POST'])
@login_required
def join_room():
    """Join existing Mahjong game room"""
    data = request.get_json()
    room_code = data.get('room_code', '').upper()
    
    game = MahjongGame.query.filter_by(room_code=room_code).first()
    
    if not game:
        return jsonify({'success': False, 'error': 'Room not found'})
    
    if game.current_players >= game.max_players:
        return jsonify({'success': False, 'error': 'Room is full'})
    
    # Check if player already in game
    existing_player = MahjongPlayer.query.filter_by(
        game_id=game.id, user_id=current_user.id
    ).first()
    
    if existing_player:
        return jsonify({'success': True, 'room_code': room_code, 'rejoined': True})
    
    # Add player to game
    player = MahjongPlayer(
        game_id=game.id,
        user_id=current_user.id,
        player_position=game.current_players + 1
    )
    
    game.current_players += 1
    
    db.session.add(player)
    db.session.commit()
    
    return jsonify({'success': True, 'room_code': room_code})

@mahjong_bp.route('/api/mahjong/game-state/<room_code>')
@login_required
def get_game_state(room_code):
    """Get current game state"""
    game = MahjongGame.query.filter_by(room_code=room_code).first_or_404()
    
    players = []
    for player in game.players:
        players.append({
            'user_id': player.user_id,
            'display_name': player.user.get_display_name(),
            'position': player.player_position,
            'score': player.score,
            'tiles_matched': player.tiles_matched,
            'is_active': player.is_active
        })
    
    # Generate game tiles if game is starting
    game_tiles = []
    if game.game_state == 'playing':
        engine = OrchidMahjongEngine()
        tile_config = json.loads(game.tile_set)
        game_tiles = engine.create_game_tiles(tile_config['layout'])
    
    return jsonify({
        'room_code': room_code,
        'game_state': game.game_state,
        'current_players': game.current_players,
        'max_players': game.max_players,
        'host_user_id': game.host_user_id,
        'players': players,
        'tiles': game_tiles,
        'created_at': game.created_at.isoformat()
    })

@mahjong_bp.route('/api/mahjong/leaderboard')
def get_leaderboard():
    """Get Mahjong leaderboard"""
    # Top players by total score
    top_players = db.session.query(User).order_by(User.mahjong_total_score.desc()).limit(10).all()
    
    leaderboard = []
    for i, player in enumerate(top_players, 1):
        leaderboard.append({
            'rank': i,
            'display_name': player.get_display_name(),
            'total_score': player.mahjong_total_score,
            'games_played': player.mahjong_games_played,
            'games_won': player.mahjong_games_won,
            'win_rate': round((player.mahjong_games_won / max(player.mahjong_games_played, 1)) * 100, 1),
            'best_time': player.mahjong_best_time,
            'badge_tier': player.current_badge_tier
        })
    
    return jsonify(leaderboard)

# Register blueprint
app.register_blueprint(mahjong_bp)

if __name__ == "__main__":
    with app.app_context():
        print("🎴 Orchid Mahjong Game System Initialized!")
        engine = OrchidMahjongEngine()
        print(f"🎯 Available layouts: {list(engine.tile_layouts.keys())}")
        print(f"🌺 Tile suits: {list(engine.orchid_tiles.keys())}")
        print("🏆 Ready for multiplayer gaming!")