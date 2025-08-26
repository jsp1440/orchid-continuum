#!/usr/bin/env python3
"""
Game Leaderboard System
Tracks scores and achievements across all orchid games
"""

from datetime import datetime, timedelta
from app import app, db
from sqlalchemy import func, desc
import json

class GameScore(db.Model):
    __tablename__ = 'game_scores'
    
    id = db.Column(db.Integer, primary_key=True)
    player_name = db.Column(db.String(100), nullable=False)
    game_type = db.Column(db.String(50), nullable=False)  # quiz, memory, trivia, guess, crossword
    score = db.Column(db.Integer, nullable=False)
    max_score = db.Column(db.Integer, nullable=False)
    completion_time = db.Column(db.Integer)  # Time in seconds
    difficulty = db.Column(db.String(20), default='medium')
    game_data = db.Column(db.Text)  # JSON data about the specific game
    created_at = db.Column(db.DateTime, default=datetime.now)
    ip_address = db.Column(db.String(45))  # For basic uniqueness tracking

class GameLeaderboard:
    
    @staticmethod
    def submit_score(player_name, game_type, score, max_score, completion_time=None, 
                    difficulty='medium', game_data=None, ip_address=None):
        """Submit a new score to the leaderboard"""
        
        # Calculate percentage score
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        # Create new score record
        new_score = GameScore(
            player_name=player_name[:100],  # Limit length
            game_type=game_type,
            score=score,
            max_score=max_score,
            completion_time=completion_time,
            difficulty=difficulty,
            game_data=json.dumps(game_data) if game_data else None,
            ip_address=ip_address
        )
        
        db.session.add(new_score)
        db.session.commit()
        
        return {
            'success': True,
            'score_id': new_score.id,
            'percentage': round(percentage, 1),
            'rank': GameLeaderboard.get_player_rank(game_type, score, max_score)
        }
    
    @staticmethod
    def get_leaderboard(game_type=None, limit=10, time_period='all'):
        """Get leaderboard data"""
        
        query = GameScore.query
        
        # Filter by game type
        if game_type:
            query = query.filter(GameScore.game_type == game_type)
        
        # Filter by time period
        if time_period == 'daily':
            since = datetime.now() - timedelta(days=1)
            query = query.filter(GameScore.created_at >= since)
        elif time_period == 'weekly':
            since = datetime.now() - timedelta(weeks=1)
            query = query.filter(GameScore.created_at >= since)
        elif time_period == 'monthly':
            since = datetime.now() - timedelta(days=30)
            query = query.filter(GameScore.created_at >= since)
        
        # Order by percentage score, then by completion time
        scores = query.order_by(
            desc(GameScore.score * 100.0 / GameScore.max_score),
            GameScore.completion_time.asc()
        ).limit(limit).all()
        
        leaderboard = []
        for i, score in enumerate(scores, 1):
            percentage = (score.score / score.max_score * 100) if score.max_score > 0 else 0
            leaderboard.append({
                'rank': i,
                'player_name': score.player_name,
                'game_type': score.game_type,
                'score': score.score,
                'max_score': score.max_score,
                'percentage': round(percentage, 1),
                'completion_time': score.completion_time,
                'difficulty': score.difficulty,
                'date': score.created_at.strftime('%Y-%m-%d'),
                'time_ago': GameLeaderboard._time_ago(score.created_at)
            })
        
        return leaderboard
    
    @staticmethod
    def get_player_rank(game_type, score, max_score):
        """Get the rank of a specific score"""
        percentage = (score / max_score * 100) if max_score > 0 else 0
        
        better_scores = GameScore.query.filter(
            GameScore.game_type == game_type,
            GameScore.score * 100.0 / GameScore.max_score > percentage
        ).count()
        
        return better_scores + 1
    
    @staticmethod
    def get_game_stats():
        """Get overall game statistics"""
        
        # Total games played
        total_games = GameScore.query.count()
        
        # Games by type
        games_by_type = db.session.query(
            GameScore.game_type,
            func.count(GameScore.id).label('count'),
            func.avg(GameScore.score * 100.0 / GameScore.max_score).label('avg_percentage')
        ).group_by(GameScore.game_type).all()
        
        # Recent activity (last 7 days)
        week_ago = datetime.now() - timedelta(days=7)
        recent_games = GameScore.query.filter(
            GameScore.created_at >= week_ago
        ).count()
        
        # Top players (by average score)
        top_players = db.session.query(
            GameScore.player_name,
            func.count(GameScore.id).label('games_played'),
            func.avg(GameScore.score * 100.0 / GameScore.max_score).label('avg_percentage')
        ).group_by(GameScore.player_name).having(
            func.count(GameScore.id) >= 3  # At least 3 games
        ).order_by(
            desc(func.avg(GameScore.score * 100.0 / GameScore.max_score))
        ).limit(5).all()
        
        return {
            'total_games': total_games,
            'recent_games': recent_games,
            'games_by_type': [
                {
                    'game_type': game.game_type,
                    'count': game.count,
                    'avg_percentage': round(game.avg_percentage, 1)
                }
                for game in games_by_type
            ],
            'top_players': [
                {
                    'player_name': player.player_name,
                    'games_played': player.games_played,
                    'avg_percentage': round(player.avg_percentage, 1)
                }
                for player in top_players
            ]
        }
    
    @staticmethod
    def _time_ago(date):
        """Calculate human-readable time difference"""
        now = datetime.now()
        diff = now - date
        
        if diff.days > 0:
            return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        else:
            return "Just now"

# Create tables
with app.app_context():
    db.create_all()