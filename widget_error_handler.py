#!/usr/bin/env python3
"""
Comprehensive Widget Error Handler
Provides robust error handling, timeouts, and fallbacks for all widget endpoints
"""

import logging
import time
import json
from functools import wraps
from flask import jsonify, request, g
from typing import Dict, Any, Optional, Callable
import threading

logger = logging.getLogger(__name__)

class WidgetErrorHandler:
    """Centralized error handling for all widgets"""
    
    def __init__(self):
        self.error_counts = {}
        self.circuit_breakers = {}
        self.cache = {}
        self.cache_ttl = {}
        
    def with_error_handling(self, 
                          timeout: int = 30,
                          fallback_data: Optional[Dict] = None,
                          cache_ttl: int = 300,
                          circuit_breaker: bool = False):
        """Decorator that adds comprehensive error handling to widget endpoints"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                endpoint_name = func.__name__
                
                # Check circuit breaker
                if circuit_breaker and self._is_circuit_open(endpoint_name):
                    logger.warning(f"🔌 Circuit breaker OPEN for {endpoint_name}")
                    return self._get_fallback_response(endpoint_name, fallback_data)
                
                # Check cache first
                cache_key = f"{endpoint_name}_{hash(str(request.args))}"
                cached_response = self._get_cached_response(cache_key)
                if cached_response:
                    logger.debug(f"📦 Cache HIT for {endpoint_name}")
                    return cached_response
                
                # Set timeout
                original_timeout = getattr(g, 'request_timeout', None)
                g.request_timeout = timeout
                
                start_time = time.time()
                try:
                    # Execute the function
                    result = func(*args, **kwargs)
                    
                    # Cache successful results
                    if cache_ttl > 0:
                        self._cache_response(cache_key, result, cache_ttl)
                    
                    # Reset error count on success
                    self.error_counts[endpoint_name] = 0
                    
                    execution_time = time.time() - start_time
                    logger.debug(f"✅ {endpoint_name} completed in {execution_time:.2f}s")
                    
                    return result
                    
                except Exception as e:
                    execution_time = time.time() - start_time
                    
                    # Increment error count
                    self.error_counts[endpoint_name] = self.error_counts.get(endpoint_name, 0) + 1
                    
                    # Log the error with context
                    logger.error(f"❌ {endpoint_name} failed after {execution_time:.2f}s: {str(e)}")
                    
                    # Check if circuit breaker should open
                    if circuit_breaker and self.error_counts[endpoint_name] >= 3:
                        self._open_circuit(endpoint_name)
                    
                    # Return fallback response
                    return self._get_fallback_response(endpoint_name, fallback_data, error=str(e))
                    
                finally:
                    # Restore original timeout
                    if original_timeout is not None:
                        g.request_timeout = original_timeout
                    
            return wrapper
        return decorator
    
    def _is_circuit_open(self, endpoint_name: str) -> bool:
        """Check if circuit breaker is open for endpoint"""
        if endpoint_name not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[endpoint_name]
        if time.time() - breaker['opened_at'] > breaker['timeout']:
            # Reset circuit breaker after timeout
            del self.circuit_breakers[endpoint_name]
            self.error_counts[endpoint_name] = 0
            logger.info(f"🔌 Circuit breaker RESET for {endpoint_name}")
            return False
        
        return True
    
    def _open_circuit(self, endpoint_name: str):
        """Open circuit breaker for endpoint"""
        self.circuit_breakers[endpoint_name] = {
            'opened_at': time.time(),
            'timeout': 60  # 1 minute timeout
        }
        logger.warning(f"🔌 Circuit breaker OPENED for {endpoint_name}")
    
    def _get_cached_response(self, cache_key: str):
        """Get cached response if still valid"""
        if cache_key not in self.cache:
            return None
        
        if time.time() > self.cache_ttl[cache_key]:
            # Cache expired
            del self.cache[cache_key]
            del self.cache_ttl[cache_key]
            return None
        
        return self.cache[cache_key]
    
    def _cache_response(self, cache_key: str, response, ttl: int):
        """Cache a response"""
        self.cache[cache_key] = response
        self.cache_ttl[cache_key] = time.time() + ttl
        
        # Clean up old cache entries (basic cleanup)
        if len(self.cache) > 1000:
            self._cleanup_cache()
    
    def _cleanup_cache(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [key for key, ttl in self.cache_ttl.items() if current_time > ttl]
        
        for key in expired_keys:
            del self.cache[key]
            del self.cache_ttl[key]
        
        logger.debug(f"🧹 Cleaned up {len(expired_keys)} expired cache entries")
    
    def _get_fallback_response(self, endpoint_name: str, fallback_data: Optional[Dict] = None, error: str = None):
        """Generate fallback response"""
        
        default_fallbacks = {
            'api_recent_orchids': {'orchids': [], 'count': 0, 'message': 'Recent orchids temporarily unavailable'},
            'api_featured_orchids': {'featured': [], 'count': 0, 'message': 'Featured orchids temporarily unavailable'},
            'api_orchid_genera': {'genera': [], 'count': 0, 'message': 'Genera list temporarily unavailable'},
            'api_weather_patterns': {'weather_points': [], 'message': 'Weather data temporarily unavailable'},
            'gallery': {'error': 'Gallery temporarily unavailable', 'retry_in': 60},
            'search': {'results': [], 'message': 'Search temporarily unavailable'},
        }
        
        # Use provided fallback or default
        response_data = fallback_data or default_fallbacks.get(endpoint_name, {
            'error': 'Service temporarily unavailable',
            'endpoint': endpoint_name,
            'retry_in': 60
        })
        
        if error:
            response_data['error_details'] = error
        
        response_data['fallback'] = True
        response_data['timestamp'] = time.time()
        
        # Return JSON response with appropriate status code
        if 'error' in response_data:
            return jsonify(response_data), 503  # Service Unavailable
        else:
            return jsonify(response_data), 200

# Global instance
widget_error_handler = WidgetErrorHandler()

def safe_json_parse(json_string: str, default=None):
    """Safely parse JSON with fallback"""
    try:
        if not json_string or json_string.strip() == '':
            return default or {}
        return json.loads(json_string)
    except (json.JSONDecodeError, ValueError, TypeError) as e:
        logger.warning(f"⚠️ JSON parse error: {e}")
        return default or {}

def safe_get_user_favorites(user_id: Optional[int] = None) -> list:
    """Safely get user favorites with fallback"""
    try:
        if not user_id:
            return []
        
        # Simulate getting user favorites (replace with actual implementation)
        from flask_login import current_user
        if hasattr(current_user, 'favorites'):
            favorites_json = getattr(current_user, 'favorites', '[]')
            return safe_json_parse(favorites_json, [])
        
        return []
    except Exception as e:
        logger.warning(f"⚠️ Error getting user favorites: {e}")
        return []

def validate_feather_icon(icon_name: str) -> str:
    """Validate and fix Feather icon names"""
    
    # Common valid Feather icons
    valid_icons = {
        'alert-triangle', 'award', 'search', 'upload', 'upload-cloud', 'info', 
        'check-circle', 'check', 'x-circle', 'x', 'home', 'user', 'settings',
        'menu', 'star', 'heart', 'eye', 'edit', 'delete', 'trash-2', 'plus',
        'minus', 'arrow-right', 'arrow-left', 'arrow-up', 'arrow-down',
        'external-link', 'link', 'mail', 'phone', 'map-pin', 'calendar',
        'clock', 'download', 'refresh-cw', 'save', 'file', 'folder',
        'image', 'camera', 'video', 'music', 'play', 'pause', 'stop',
        'volume-2', 'wifi', 'bluetooth', 'battery', 'zap', 'sun', 'moon'
    }
    
    # Icon name mappings for common issues
    icon_mappings = {
        'upload-cloud-2': 'upload-cloud',
        'check-square': 'check-circle',
        'alert-circle': 'alert-triangle',
        'info-circle': 'info',
        'warning': 'alert-triangle',
        'error': 'x-circle',
        'success': 'check-circle'
    }
    
    # Clean the icon name
    clean_name = icon_name.strip().lower()
    
    # Check mappings first
    if clean_name in icon_mappings:
        return icon_mappings[clean_name]
    
    # Check if it's a valid icon
    if clean_name in valid_icons:
        return clean_name
    
    # Return a safe default
    logger.warning(f"⚠️ Invalid Feather icon '{icon_name}', using 'info' as fallback")
    return 'info'