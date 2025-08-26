#!/usr/bin/env python3
"""
Emergency Gallery Protection System
Ensures gallery pages NEVER show empty results due to database failures
"""

import logging
from flask import render_template, jsonify
from photo_failsafe_system import get_photos_guaranteed

def protect_gallery_route(original_route_function):
    """
    Decorator to wrap gallery routes with emergency protection
    """
    def protected_gallery(*args, **kwargs):
        try:
            # Try the original route
            return original_route_function(*args, **kwargs)
        except Exception as e:
            logging.error(f"🚨 GALLERY FAILURE: {e}")
            
            # Emergency fallback - get guaranteed photos
            photos, recovery_info = get_photos_guaranteed(12)
            
            # Return emergency gallery with clear messaging
            return render_template('gallery.html', 
                orchids=photos,
                page=1,
                pages=1,
                total=len(photos),
                per_page=12,
                search_query='',
                genus_filter='',
                emergency_mode=True,
                recovery_info=recovery_info
            )
    
    return protected_gallery

def protect_api_route(original_api_function):
    """
    Decorator to wrap API routes with emergency protection
    """
    def protected_api(*args, **kwargs):
        try:
            # Try the original API
            return original_api_function(*args, **kwargs)
        except Exception as e:
            logging.error(f"🚨 API FAILURE: {e}")
            
            # Emergency fallback - get guaranteed photos
            photos, recovery_info = get_photos_guaranteed(12)
            
            # Return emergency API response
            return jsonify({
                'status': 'emergency_mode',
                'message': 'Database temporarily unavailable - showing backup collection',
                'orchids': photos,
                'recovery_info': recovery_info,
                'count': len(photos)
            })
    
    return protected_api

class EmergencyGalleryManager:
    """
    Central manager for emergency gallery operations
    """
    
    def __init__(self):
        self.emergency_stats = {
            'activations': 0,
            'last_activation': None,
            'routes_protected': []
        }
    
    def activate_emergency_mode(self, route_name: str, error: Exception):
        """Log emergency activation"""
        from datetime import datetime
        
        self.emergency_stats['activations'] += 1
        self.emergency_stats['last_activation'] = datetime.now().isoformat()
        
        if route_name not in self.emergency_stats['routes_protected']:
            self.emergency_stats['routes_protected'].append(route_name)
        
        logging.critical(f"🆘 EMERGENCY MODE: {route_name} failed with {type(error).__name__}: {error}")
    
    def get_emergency_status(self):
        """Get current emergency system status"""
        return self.emergency_stats.copy()

# Global emergency manager
emergency_manager = EmergencyGalleryManager()

def ensure_photos_always_load():
    """
    Universal function to ensure photos always load
    Returns guaranteed photos with recovery information
    """
    try:
        # Try database first
        from models import OrchidRecord
        from app import db
        
        orchids = OrchidRecord.query.filter(
            OrchidRecord.google_drive_id.isnot(None)
        ).limit(12).all()
        
        if orchids and len(orchids) >= 3:
            photo_list = []
            for orchid in orchids:
                photo_list.append({
                    'id': orchid.id,
                    'scientific_name': orchid.scientific_name,
                    'common_name': orchid.display_name,
                    'description': orchid.ai_description or 'Beautiful orchid specimen',
                    'image_url': f'/api/image/{orchid.google_drive_id}',
                    'source': 'database'
                })
            
            return photo_list, {'source': 'database', 'fallback_level': 1}
    
    except Exception as e:
        logging.error(f"Database photo fetch failed: {e}")
    
    # Emergency fallback
    photos, recovery_info = get_photos_guaranteed(12)
    emergency_manager.activate_emergency_mode('universal_photo_fetch', Exception("Database unavailable"))
    
    return photos, recovery_info