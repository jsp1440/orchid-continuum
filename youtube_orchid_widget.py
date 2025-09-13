"""
YouTube Orchid Widget for Five Cities Orchid Society
Embeddable video player with channel search and broader orchid video discovery
"""

import os
import requests
import logging
from flask import Blueprint, render_template, jsonify, request, url_for
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import json

# Initialize blueprint
youtube_widget = Blueprint('youtube_widget', __name__, url_prefix='/youtube')

logger = logging.getLogger(__name__)

class YouTubeOrchidWidget:
    """YouTube widget specifically designed for Five Cities Orchid Society"""
    
    def __init__(self):
        self.api_key = os.environ.get('YOUTUBE_API_KEY')
        self.fcos_channel_id = "UCfivecitiesorchidsociety1290"  # Five Cities Orchid Society
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
        if not self.api_key:
            logger.warning("YouTube API key not found. Widget will show demo content.")
    
    def search_channel_videos(self, query: str = "", max_results: int = 12) -> List[Dict]:
        """Search videos specifically in Five Cities Orchid Society channel"""
        if not self.api_key:
            return self._get_demo_videos()
        
        try:
            # Search in specific channel
            search_url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'channelId': self.fcos_channel_id,
                'type': 'video',
                'order': 'relevance' if query else 'date',
                'maxResults': max_results,
                'key': self.api_key
            }
            
            if query:
                params['q'] = f"{query} orchid"
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                video = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:200] + "..." if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'is_fcos': True
                }
                videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return self._get_demo_videos()
    
    def search_orchid_videos_general(self, query: str, max_results: int = 12) -> List[Dict]:
        """Search for orchid videos across all of YouTube"""
        if not self.api_key:
            return self._get_demo_videos()
        
        try:
            search_url = f"{self.base_url}/search"
            params = {
                'part': 'snippet',
                'q': f"{query} orchid care growing",
                'type': 'video',
                'order': 'relevance',
                'maxResults': max_results,
                'key': self.api_key
            }
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            videos = []
            for item in data.get('items', []):
                video = {
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'][:200] + "..." if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['medium']['url'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'is_fcos': False
                }
                videos.append(video)
            
            return videos
            
        except Exception as e:
            logger.error(f"Error searching YouTube: {e}")
            return self._get_demo_videos()
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed information about a specific video"""
        if not self.api_key:
            return self._get_demo_video_details(video_id)
        
        try:
            details_url = f"{self.base_url}/videos"
            params = {
                'part': 'snippet,statistics,contentDetails',
                'id': video_id,
                'key': self.api_key
            }
            
            response = requests.get(details_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                item = data['items'][0]
                return {
                    'video_id': video_id,
                    'title': item['snippet']['title'],
                    'description': item['snippet']['description'],
                    'thumbnail': item['snippet']['thumbnails']['high']['url'],
                    'published_at': item['snippet']['publishedAt'],
                    'channel_title': item['snippet']['channelTitle'],
                    'view_count': item['statistics'].get('viewCount', 0),
                    'like_count': item['statistics'].get('likeCount', 0),
                    'duration': item['contentDetails']['duration']
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting video details: {e}")
            return self._get_demo_video_details(video_id)
    
    def get_channel_stats(self) -> Dict:
        """Get Five Cities Orchid Society channel statistics"""
        if not self.api_key:
            return {
                'subscriber_count': '2.3K',
                'video_count': 150,
                'view_count': '69,000+',
                'channel_title': 'Five Cities Orchid Society'
            }
        
        try:
            channel_url = f"{self.base_url}/channels"
            params = {
                'part': 'snippet,statistics',
                'id': self.fcos_channel_id,
                'key': self.api_key
            }
            
            response = requests.get(channel_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('items'):
                item = data['items'][0]
                stats = item['statistics']
                return {
                    'subscriber_count': self._format_number(int(stats.get('subscriberCount', 0))),
                    'video_count': int(stats.get('videoCount', 0)),
                    'view_count': self._format_number(int(stats.get('viewCount', 0))),
                    'channel_title': item['snippet']['title']
                }
            
            return {}
            
        except Exception as e:
            logger.error(f"Error getting channel stats: {e}")
            return {
                'subscriber_count': '2.3K',
                'video_count': 150,
                'view_count': '69,000+',
                'channel_title': 'Five Cities Orchid Society'
            }
    
    def _format_number(self, num: int) -> str:
        """Format large numbers for display"""
        if num >= 1000000:
            return f"{num/1000000:.1f}M"
        elif num >= 1000:
            return f"{num/1000:.1f}K"
        else:
            return str(num)
    
    def _get_demo_videos(self) -> List[Dict]:
        """Demo videos for development/testing"""
        return [
            {
                'video_id': 'demo1',
                'title': 'Orchid Care Basics - Five Cities Orchid Society',
                'description': 'Learn the fundamentals of orchid care with expert tips from our society members.',
                'thumbnail': 'https://img.youtube.com/vi/demo1/mqdefault.jpg',
                'published_at': '2024-01-15T10:00:00Z',
                'channel_title': 'Five Cities Orchid Society',
                'is_fcos': True
            },
            {
                'video_id': 'demo2',
                'title': 'Repotting Phalaenopsis Orchids',
                'description': 'Step-by-step guide to repotting your Phalaenopsis orchids for optimal health.',
                'thumbnail': 'https://img.youtube.com/vi/demo2/mqdefault.jpg',
                'published_at': '2024-02-10T14:30:00Z',
                'channel_title': 'Five Cities Orchid Society',
                'is_fcos': True
            }
        ]
    
    def _get_demo_video_details(self, video_id: str) -> Dict:
        """Demo video details for development"""
        return {
            'video_id': video_id,
            'title': 'Demo Orchid Video',
            'description': 'This is a demonstration video for the YouTube widget.',
            'thumbnail': f'https://img.youtube.com/vi/{video_id}/maxresdefault.jpg',
            'published_at': '2024-01-01T00:00:00Z',
            'channel_title': 'Five Cities Orchid Society',
            'view_count': 1250,
            'like_count': 45,
            'duration': 'PT10M30S'
        }

# Initialize the widget
youtube_widget_manager = YouTubeOrchidWidget()

# Routes
@youtube_widget.route('/')
def youtube_home():
    """Main YouTube widget page"""
    channel_stats = youtube_widget_manager.get_channel_stats()
    recent_videos = youtube_widget_manager.search_channel_videos(max_results=8)
    
    return render_template('youtube_widget/main.html',
                         channel_stats=channel_stats,
                         recent_videos=recent_videos)

@youtube_widget.route('/api/search')
def api_search_videos():
    """API endpoint for video search"""
    query = request.args.get('q', '')
    search_type = request.args.get('type', 'channel')  # 'channel' or 'general'
    max_results = min(int(request.args.get('limit', 12)), 50)
    
    if search_type == 'general':
        videos = youtube_widget_manager.search_orchid_videos_general(query, max_results)
    else:
        videos = youtube_widget_manager.search_channel_videos(query, max_results)
    
    return jsonify({
        'videos': videos,
        'search_query': query,
        'search_type': search_type,
        'total_results': len(videos)
    })

@youtube_widget.route('/api/video/<video_id>')
def api_video_details(video_id):
    """API endpoint for video details"""
    details = youtube_widget_manager.get_video_details(video_id)
    
    if details:
        return jsonify(details)
    else:
        return jsonify({'error': 'Video not found'}), 404

@youtube_widget.route('/api/channel-stats')
def api_channel_stats():
    """API endpoint for channel statistics"""
    stats = youtube_widget_manager.get_channel_stats()
    return jsonify(stats)

@youtube_widget.route('/embed')
def embed_widget():
    """Embeddable widget for Neon One integration"""
    width = request.args.get('width', '100%')
    height = request.args.get('height', '600px')
    theme = request.args.get('theme', 'light')
    show_search = request.args.get('search', 'true').lower() == 'true'
    
    channel_stats = youtube_widget_manager.get_channel_stats()
    recent_videos = youtube_widget_manager.search_channel_videos(max_results=6)
    
    return render_template('youtube_widget/embed.html',
                         width=width,
                         height=height,
                         theme=theme,
                         show_search=show_search,
                         channel_stats=channel_stats,
                         recent_videos=recent_videos)

@youtube_widget.route('/player/<video_id>')
def video_player(video_id):
    """Dedicated video player page"""
    video_details = youtube_widget_manager.get_video_details(video_id)
    related_videos = youtube_widget_manager.search_channel_videos(max_results=6)
    
    return render_template('youtube_widget/player.html',
                         video=video_details,
                         related_videos=related_videos)