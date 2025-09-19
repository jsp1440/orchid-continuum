#!/usr/bin/env python3
"""
Photo Failsafe System - Comprehensive Image Recovery & Backup
Ensures photos ALWAYS display with multiple fallback mechanisms
"""

import logging
import requests
import json
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import time
from sqlalchemy import text

class PhotoFailsafeSystem:
    """
    Multi-layered photo recovery system that NEVER allows empty galleries
    """
    
    def __init__(self):
        self.backup_images = self._initialize_backup_collection()
        self.recovery_stats = {
            'total_requests': 0,
            'database_failures': 0,
            'google_drive_failures': 0,
            'backup_uses': 0,
            'last_failure': None
        }
        
    def _initialize_backup_collection(self) -> List[Dict]:
        """Emergency backup collection - ALWAYS available offline"""
        return [
            {
                'id': 1001,
                'scientific_name': 'Phalaenopsis amabilis',
                'common_name': 'Moth Orchid',
                'description': 'Classic white moth orchid - symbol of elegance',
                'image_url': '/static/images/backup/phalaenopsis_white.jpg',
                'backup_emoji': '🌺',
                'region': 'Southeast Asia',
                'care_level': 'Beginner-friendly',
                'fun_fact': 'One of the most popular houseplant orchids worldwide'
            },
            {
                'id': 'backup_002', 
                'scientific_name': 'Dendrobium nobile',
                'common_name': 'Noble Dendrobium',
                'description': 'Stunning purple and white clusters',
                'image_url': '/static/images/backup/dendrobium_purple.jpg',
                'backup_emoji': '💜',
                'region': 'Himalayas',
                'care_level': 'Intermediate',
                'fun_fact': 'Requires winter rest period to bloom'
            },
            {
                'id': 'backup_003',
                'scientific_name': 'Cattleya labiata',
                'common_name': 'Corsage Orchid',
                'description': 'Large lavender blooms with ruffled lips',
                'image_url': '/static/images/backup/cattleya_lavender.jpg',
                'backup_emoji': '🌸',
                'region': 'Brazil',
                'care_level': 'Intermediate',
                'fun_fact': 'Traditional choice for wedding corsages'
            },
            {
                'id': 'backup_004',
                'scientific_name': 'Vanda coerulea',
                'common_name': 'Blue Orchid',
                'description': 'Rare blue flowers with intricate patterns',
                'image_url': '/static/images/backup/vanda_blue.jpg',
                'backup_emoji': '💙',
                'region': 'Thailand',
                'care_level': 'Advanced',
                'fun_fact': 'National flower of Singapore'
            },
            {
                'id': 'backup_005',
                'scientific_name': 'Oncidium sphacelatum',
                'common_name': 'Dancing Lady Orchid',
                'description': 'Bright yellow flowers resembling dancing figures',
                'image_url': '/static/images/backup/oncidium_yellow.jpg',
                'backup_emoji': '💃',
                'region': 'Central America',
                'care_level': 'Beginner-friendly',
                'fun_fact': 'Flowers dance in the breeze'
            },
            {
                'id': 'backup_006',
                'scientific_name': 'Cymbidium ensifolium',
                'common_name': 'Four Seasons Orchid',
                'description': 'Fragrant green and burgundy flowers',
                'image_url': '/static/images/backup/cymbidium_green.jpg',
                'backup_emoji': '🍃',
                'region': 'China',
                'care_level': 'Intermediate',
                'fun_fact': 'Symbolizes virtue in Chinese culture'
            }
        ]
    
    def get_photos_with_failsafe(self, requested_count: int = 12) -> Tuple[List[Dict], Dict]:
        """
        GUARANTEED photo retrieval with comprehensive fallback system
        
        Returns: (photos_list, recovery_info)
        """
        self.recovery_stats['total_requests'] += 1
        recovery_info = {
            'source': 'unknown',
            'fallback_level': 0,
            'errors': [],
            'timestamp': datetime.now().isoformat()
        }
        
        # Level 1: Try database (primary source)
        try:
            photos = self._get_database_photos(requested_count)
            if photos and len(photos) >= 3:  # Minimum viable gallery
                recovery_info['source'] = 'database'
                recovery_info['fallback_level'] = 1
                return photos, recovery_info
        except Exception as e:
            self.recovery_stats['database_failures'] += 1
            recovery_info['errors'].append(f"Database: {str(e)}")
            logging.error(f"❌ Database photo retrieval failed: {e}")
        
        # Level 2: Try Google Drive API (secondary source)
        try:
            photos = self._get_google_drive_photos(requested_count)
            if photos and len(photos) >= 3:
                recovery_info['source'] = 'google_drive'
                recovery_info['fallback_level'] = 2
                return photos, recovery_info
        except Exception as e:
            self.recovery_stats['google_drive_failures'] += 1
            recovery_info['errors'].append(f"Google Drive: {str(e)}")
            logging.error(f"❌ Google Drive photo retrieval failed: {e}")
        
        # Level 3: Emergency backup collection (ALWAYS works)
        self.recovery_stats['backup_uses'] += 1
        self.recovery_stats['last_failure'] = datetime.now().isoformat()
        
        backup_photos = self._get_backup_photos(requested_count)
        recovery_info['source'] = 'emergency_backup'
        recovery_info['fallback_level'] = 3
        recovery_info['backup_count'] = len(backup_photos)
        
        logging.warning(f"🆘 Using emergency backup photos: {len(backup_photos)} items")
        return backup_photos, recovery_info
    
    def _get_database_photos(self, count: int) -> List[Dict]:
        """Attempt database photo retrieval with error isolation"""
        try:
            from models import OrchidRecord
            from app import db
            
            # Test database connection first
            db.session.execute(text('SELECT 1'))
            
            # Query with safety limits
            query = OrchidRecord.query.filter(
                OrchidRecord.google_drive_id.isnot(None)
            ).limit(count * 2)  # Get extra for filtering
            
            records = query.all()
            
            photos = []
            for record in records[:count]:
                if record.google_drive_id and record.scientific_name:
                    photos.append({
                        'id': record.id,
                        'scientific_name': record.scientific_name,
                        'common_name': record.display_name or 'Beautiful Orchid',
                        'description': record.ai_description or 'Stunning orchid specimen',
                        'image_url': f'/api/image/{record.google_drive_id}',
                        'source': 'database'
                    })
            
            return photos
            
        except Exception as e:
            logging.error(f"Database photo retrieval error: {e}")
            raise
    
    def _get_google_drive_photos(self, count: int) -> List[Dict]:
        """Fallback to direct Google Drive API calls"""
        try:
            # This would connect directly to Google Drive
            # For now, return empty to trigger backup
            return []
        except Exception as e:
            logging.error(f"Google Drive photo retrieval error: {e}")
            raise
    
    def _get_backup_photos(self, count: int) -> List[Dict]:
        """Emergency backup photos - NEVER fails"""
        # Cycle through backup collection to fill requested count
        photos = []
        backup_count = len(self.backup_images)
        
        for i in range(count):
            backup_item = self.backup_images[i % backup_count].copy()
            # Use a large base number to avoid conflicts with real orchid IDs
            backup_item['id'] = 9000 + i + 1
            backup_item['emergency_mode'] = True
            backup_item['emergency_id'] = f"emergency_{i+1}"
            photos.append(backup_item)
        
        return photos
    
    def get_recovery_status(self) -> Dict:
        """Get current system status for monitoring"""
        return {
            'stats': self.recovery_stats.copy(),
            'backup_available': len(self.backup_images),
            'system_health': self._calculate_health_score(),
            'last_check': datetime.now().isoformat()
        }
    
    def _calculate_health_score(self) -> str:
        """Calculate system health based on failure rates"""
        total = self.recovery_stats['total_requests']
        if total == 0:
            return 'unknown'
        
        failure_rate = (self.recovery_stats['database_failures'] + 
                       self.recovery_stats['google_drive_failures']) / total
        
        if failure_rate < 0.1:
            return 'excellent'
        elif failure_rate < 0.3:
            return 'good'
        elif failure_rate < 0.6:
            return 'warning'
        else:
            return 'critical'

class ImageRecoveryService:
    """Service for individual image recovery with multiple fallbacks"""
    
    def __init__(self):
        self.cdn_fallbacks = [
            'https://via.placeholder.com/400x300/9b59b6/ffffff?text=Orchid+Image',
            'https://via.placeholder.com/400x300/27ae60/ffffff?text=Beautiful+Orchid',
            'https://via.placeholder.com/400x300/3498db/ffffff?text=Orchid+Gallery'
        ]
    
    def get_image_with_recovery(self, orchid_id: str, google_drive_id: str = None) -> Dict:
        """
        GUARANTEED image retrieval for individual orchids
        
        Returns: {
            'url': str,
            'source': str,
            'fallback_level': int,
            'available': bool
        }
        """
        
        # Level 1: Try Google Drive image
        if google_drive_id:
            try:
                drive_url = f'/api/image/{google_drive_id}'
                # Test if accessible
                response = requests.head(f'http://localhost:5000{drive_url}', timeout=2)
                if response.status_code == 200:
                    return {
                        'url': drive_url,
                        'source': 'google_drive',
                        'fallback_level': 1,
                        'available': True
                    }
            except Exception as e:
                logging.warning(f"Google Drive image {google_drive_id} unavailable: {e}")
        
        # Level 2: Static placeholder with orchid emoji
        return {
            'url': self._generate_emoji_placeholder(orchid_id),
            'source': 'emoji_placeholder',
            'fallback_level': 2,
            'available': True
        }
    
    def _generate_emoji_placeholder(self, orchid_id: str) -> str:
        """Generate data URL with orchid emoji as placeholder"""
        # Create SVG with orchid emoji
        svg_content = f'''
        <svg width="400" height="300" xmlns="http://www.w3.org/2000/svg">
            <rect width="400" height="300" fill="#f8f9fa"/>
            <text x="200" y="120" font-family="Arial" font-size="48" text-anchor="middle" fill="#9b59b6">🌺</text>
            <text x="200" y="160" font-family="Arial" font-size="14" text-anchor="middle" fill="#666">Orchid Image</text>
            <text x="200" y="180" font-family="Arial" font-size="12" text-anchor="middle" fill="#999">ID: {orchid_id}</text>
        </svg>
        '''
        
        import base64
        svg_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        return f"data:image/svg+xml;base64,{svg_base64}"

# Global instances
photo_failsafe = PhotoFailsafeSystem()
image_recovery = ImageRecoveryService()

def get_photos_guaranteed(count: int = 12) -> Tuple[List[Dict], Dict]:
    """Global function for guaranteed photo retrieval"""
    return photo_failsafe.get_photos_with_failsafe(count)

def get_image_guaranteed(orchid_id: str, google_drive_id: str = None) -> Dict:
    """Global function for guaranteed individual image retrieval"""
    return image_recovery.get_image_with_recovery(orchid_id, google_drive_id)

if __name__ == "__main__":
    # Test the failsafe system
    print("🔧 Testing Photo Failsafe System...")
    
    photos, info = get_photos_guaranteed(6)
    print(f"✅ Retrieved {len(photos)} photos from {info['source']}")
    
    status = photo_failsafe.get_recovery_status()
    print(f"📊 System health: {status['system_health']}")
    print(f"🆘 Backup collection: {status['backup_available']} items ready")