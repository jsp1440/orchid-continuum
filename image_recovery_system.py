#!/usr/bin/env python3
"""
Advanced Image Recovery and Fallback System
Handles multiple image sources with automatic fallbacks and local caching
"""

import os
import logging
import requests
import hashlib
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import threading
import time
from urllib.parse import urlparse
import tempfile
import shutil

logger = logging.getLogger(__name__)

class ImageRecoverySystem:
    """Comprehensive image recovery with multiple fallback sources"""
    
    def __init__(self):
        self.cache_dir = Path('static/image_cache')
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Fallback image sources
        self.fallback_sources = [
            'google_drive',
            'local_cache', 
            'placeholder_generator',
            'backup_proxy'
        ]
        
        # Blocked domain handling
        self.blocked_domains = {
            'inaturalist-open-data.s3.amazonaws.com': 'inaturalist_proxy',
            'static.inaturalist.org': 'inaturalist_proxy',
            'gbif.org': 'gbif_proxy'
        }
        
        # Cache metadata
        self.cache_metadata = {}
        self._load_cache_metadata()
        
        # Recovery stats
        self.stats = {
            'cache_hits': 0,
            'fallback_used': 0,
            'recovery_success': 0,
            'blocked_bypassed': 0
        }
        
    def _load_cache_metadata(self):
        """Load cache metadata from disk"""
        metadata_file = self.cache_dir / 'cache_metadata.json'
        if metadata_file.exists():
            try:
                with open(metadata_file, 'r') as f:
                    self.cache_metadata = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load cache metadata: {e}")
                self.cache_metadata = {}
    
    def _save_cache_metadata(self):
        """Save cache metadata to disk"""
        metadata_file = self.cache_dir / 'cache_metadata.json'
        try:
            with open(metadata_file, 'w') as f:
                json.dump(self.cache_metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache metadata: {e}")
    
    def get_image_with_fallback(self, url: str, orchid_id: Optional[str] = None) -> Tuple[str, str]:
        """
        Get image with comprehensive fallback system
        Returns: (final_url, source_type)
        """
        if not url:
            return self._generate_placeholder_image(orchid_id or "default"), 'placeholder'
        
        # Check if domain is blocked
        domain = urlparse(url).netloc
        if domain in self.blocked_domains:
            logger.info(f"🚫 Blocked domain detected: {domain}")
            return self._handle_blocked_domain(url, domain, orchid_id)
        
        # Try original URL first
        if self._test_image_url(url):
            return url, 'original'
        
        # Try fallback sources
        for source in self.fallback_sources:
            try:
                fallback_url = self._try_fallback_source(url, source, orchid_id)
                if fallback_url:
                    self.stats['fallback_used'] += 1
                    return fallback_url, source
            except Exception as e:
                logger.warning(f"Fallback source {source} failed: {e}")
        
        # Ultimate fallback - generate placeholder
        placeholder_url = self._generate_placeholder_image(orchid_id)
        return placeholder_url, 'placeholder'
    
    def _handle_blocked_domain(self, url: str, domain: str, orchid_id: str = None) -> Tuple[str, str]:
        """Handle blocked domains with specialized proxies"""
        proxy_type = self.blocked_domains[domain]
        
        if proxy_type == 'inaturalist_proxy':
            # Try to extract image ID and use alternative URLs
            return self._handle_inaturalist_image(url, orchid_id)
        elif proxy_type == 'gbif_proxy':
            return self._handle_gbif_image(url, orchid_id)
        
        # If no specialized handler, try generic proxy
        return self._try_generic_proxy(url, orchid_id)
    
    def _handle_inaturalist_image(self, url: str, orchid_id: str = None) -> Tuple[str, str]:
        """Handle iNaturalist images with multiple fallback strategies"""
        
        # Extract photo ID from URL
        photo_id = None
        if 'photos/' in url:
            try:
                photo_id = url.split('photos/')[1].split('/')[0]
            except:
                pass
        
        if photo_id:
            # Try alternative iNaturalist URLs
            alt_urls = [
                f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photo_id}/medium.jpg",
                f"https://inaturalist-open-data.s3.amazonaws.com/photos/{photo_id}/small.jpg",
                f"https://static.inaturalist.org/photos/{photo_id}/medium.jpg",
                f"https://www.inaturalist.org/photos/{photo_id}",
            ]
            
            for alt_url in alt_urls:
                try:
                    if self._test_image_url(alt_url, timeout=3):
                        logger.info(f"✅ iNaturalist fallback successful: {alt_url}")
                        return alt_url, 'inaturalist_fallback'
                except:
                    continue
        
        # Try to cache and serve locally
        cache_path = self._attempt_local_cache(url, f"inaturalist_{photo_id or orchid_id}")
        if cache_path:
            return f"/static/image_cache/{cache_path.name}", 'local_cache'
        
        return self._generate_placeholder_image(orchid_id), 'placeholder'
    
    def _handle_gbif_image(self, url: str, orchid_id: str = None) -> Tuple[str, str]:
        """Handle GBIF images with fallback strategies"""
        
        # Try GBIF API alternatives
        if 'gbif.org' in url:
            # Extract occurrence key if possible
            try:
                # Try direct image download
                cache_path = self._attempt_local_cache(url, f"gbif_{orchid_id}")
                if cache_path:
                    return f"/static/image_cache/{cache_path.name}", 'local_cache'
            except:
                pass
        
        return self._generate_placeholder_image(orchid_id), 'placeholder'
    
    def _try_generic_proxy(self, url: str, orchid_id: str = None) -> Tuple[str, str]:
        """Try generic proxy methods"""
        
        # Method 1: Try web.archive.org
        archive_url = f"https://web.archive.org/web/{url}"
        if self._test_image_url(archive_url, timeout=5):
            return archive_url, 'archive_proxy'
        
        # Method 2: Try local caching
        cache_path = self._attempt_local_cache(url, f"proxy_{orchid_id}")
        if cache_path:
            return f"/static/image_cache/{cache_path.name}", 'local_cache'
        
        return self._generate_placeholder_image(orchid_id), 'placeholder'
    
    def _attempt_local_cache(self, url: str, cache_key: str) -> Optional[Path]:
        """Attempt to download and cache image locally"""
        try:
            # Generate cache filename
            url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
            cache_filename = f"{cache_key}_{url_hash}.jpg"
            cache_path = self.cache_dir / cache_filename
            
            # Check if already cached
            if cache_path.exists():
                # Verify cache is not expired (24 hours)
                if cache_path.stat().st_mtime > (time.time() - 86400):
                    self.stats['cache_hits'] += 1
                    return cache_path
            
            # Download with multiple attempts
            for attempt in range(3):
                try:
                    response = requests.get(
                        url, 
                        timeout=10, 
                        headers={
                            'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0)',
                            'Accept': 'image/*,*/*;q=0.8'
                        },
                        stream=True
                    )
                    
                    if response.status_code == 200:
                        with open(cache_path, 'wb') as f:
                            shutil.copyfileobj(response.raw, f)
                        
                        # Update cache metadata
                        self.cache_metadata[cache_filename] = {
                            'original_url': url,
                            'cached_at': datetime.now().isoformat(),
                            'size': cache_path.stat().st_size
                        }
                        self._save_cache_metadata()
                        
                        logger.info(f"✅ Cached image: {cache_filename}")
                        return cache_path
                        
                except Exception as e:
                    logger.warning(f"Cache attempt {attempt + 1} failed: {e}")
                    time.sleep(1)
            
        except Exception as e:
            logger.error(f"Local cache failed for {url}: {e}")
        
        return None
    
    def _try_fallback_source(self, url: str, source: str, orchid_id: str = None) -> Optional[str]:
        """Try specific fallback source"""
        
        if source == 'google_drive':
            return self._try_google_drive_fallback(orchid_id)
        elif source == 'local_cache':
            cache_path = self._attempt_local_cache(url, f"fallback_{orchid_id}")
            if cache_path:
                return f"/static/image_cache/{cache_path.name}"
        elif source == 'placeholder_generator':
            return self._generate_placeholder_image(orchid_id)
        elif source == 'backup_proxy':
            return self._try_generic_proxy(url, orchid_id)[0]
        
        return None
    
    def _try_google_drive_fallback(self, orchid_id: str = None) -> Optional[str]:
        """Try to find Google Drive alternative for orchid"""
        
        if not orchid_id:
            return None
        
        # Try to find Google Drive image for this orchid
        from models import OrchidRecord
        try:
            orchid = OrchidRecord.query.get(orchid_id)
            if orchid and orchid.google_drive_id:
                return f"/api/drive-photo/{orchid.google_drive_id}"
        except:
            pass
        
        return None
    
    def _generate_placeholder_image(self, orchid_id: str = None) -> str:
        """Generate beautiful placeholder image"""
        
        # Different placeholder types
        placeholders = [
            '/static/images/orchid_placeholder_1.svg',
            '/static/images/orchid_placeholder_2.svg', 
            '/static/images/orchid_placeholder_3.svg'
        ]
        
        # Select based on orchid_id or use default
        if orchid_id:
            try:
                idx = int(orchid_id) % len(placeholders)
                return placeholders[idx]
            except:
                pass
        
        return '/static/images/orchid_continuum_transparent_logo.png'
    
    def _test_image_url(self, url: str, timeout: int = 5) -> bool:
        """Test if image URL is accessible"""
        try:
            response = requests.head(
                url,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (compatible; OrchidBot/1.0)'},
                allow_redirects=True
            )
            return response.status_code == 200
        except:
            return False
    
    def cleanup_cache(self, max_age_days: int = 7):
        """Clean up old cache files"""
        cutoff_time = time.time() - (max_age_days * 86400)
        
        for cache_file in self.cache_dir.glob('*.jpg'):
            if cache_file.stat().st_mtime < cutoff_time:
                try:
                    cache_file.unlink()
                    # Remove from metadata
                    if cache_file.name in self.cache_metadata:
                        del self.cache_metadata[cache_file.name]
                    logger.info(f"🗑️ Cleaned cache file: {cache_file.name}")
                except Exception as e:
                    logger.error(f"Failed to clean cache file {cache_file.name}: {e}")
        
        self._save_cache_metadata()
    
    def get_recovery_stats(self) -> Dict:
        """Get recovery system statistics"""
        cache_size = sum(f.stat().st_size for f in self.cache_dir.glob('*.jpg'))
        cache_count = len(list(self.cache_dir.glob('*.jpg')))
        
        return {
            **self.stats,
            'cache_size_mb': round(cache_size / 1024 / 1024, 2),
            'cached_files': cache_count,
            'cache_metadata_entries': len(self.cache_metadata)
        }

# Global instance
image_recovery = ImageRecoverySystem()

def get_image_with_recovery(url: str, orchid_id: str = None) -> Tuple[str, str]:
    """Public interface for image recovery"""
    return image_recovery.get_image_with_fallback(url, orchid_id)

def cleanup_image_cache():
    """Public interface for cache cleanup"""
    image_recovery.cleanup_cache()

def get_image_recovery_stats():
    """Public interface for recovery stats"""
    return image_recovery.get_recovery_stats()