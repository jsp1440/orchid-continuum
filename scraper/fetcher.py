#!/usr/bin/env python3
"""
SVO Data Fetcher Module

This module provides robust web scraping capabilities with rate limiting,
error handling, and retry mechanisms for orchid data collection.

Features:
- Configurable rate limiting and request delays
- Automatic retry with exponential backoff
- Session management with proper headers
- Progress tracking and logging
- Multiple URL source support
- Robust error handling and recovery
"""

import requests
import time
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union
from urllib.parse import urljoin, urlparse, quote
from bs4 import BeautifulSoup
from dataclasses import dataclass, asdict, field
import hashlib
import random
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class FetchResult:
    """Result of a fetch operation"""
    url: str
    status_code: int = 0
    content: str = ""
    raw_html: str = ""
    headers: Dict[str, str] = field(default_factory=dict)
    error: Optional[str] = None
    fetch_time: datetime = field(default_factory=datetime.now)
    processing_time: float = 0.0
    retry_count: int = 0
    source_category: str = ""
    
    @property
    def success(self) -> bool:
        """Check if fetch was successful"""
        return self.status_code == 200 and not self.error and self.content
    
    @property
    def domain(self) -> str:
        """Extract domain from URL"""
        return urlparse(self.url).netloc
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        result = asdict(self)
        result['fetch_time'] = self.fetch_time.isoformat()
        return result

@dataclass 
class ScrapingProgress:
    """Progress tracking for scraping operations"""
    total_urls: int = 0
    processed_urls: int = 0
    successful_fetches: int = 0
    failed_fetches: int = 0
    total_content_size: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    current_source: str = ""
    errors: List[str] = field(default_factory=list)
    
    @property
    def progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_urls == 0:
            return 0.0
        return (self.processed_urls / self.total_urls) * 100
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate"""
        if self.processed_urls == 0:
            return 0.0
        return (self.successful_fetches / self.processed_urls) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed time in seconds"""
        return (datetime.now() - self.start_time).total_seconds()
    
    def log_progress(self):
        """Log current progress"""
        logger.info(f"📊 Progress: {self.processed_urls}/{self.total_urls} URLs "
                   f"({self.progress_percentage:.1f}%) | "
                   f"Success: {self.success_rate:.1f}% | "
                   f"Elapsed: {self.elapsed_time:.1f}s")

class ScrapingSession:
    """HTTP session manager with rate limiting and error handling"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize scraping session
        
        Args:
            config: Configuration dictionary from config.py
        """
        self.config = config
        self.session = requests.Session()
        self.last_request_time = {}  # Per-domain rate limiting
        self._setup_session()
        
        # Thread safety for rate limiting
        self._lock = threading.Lock()
        
    def _setup_session(self):
        """Configure HTTP session"""
        self.session.headers.update({
            'User-Agent': self.config.get('user_agent', 'OrchidContinuum-SVO-Processor/1.0'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'DNT': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none'
        })
        
        # Configure retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=self.config.get('max_retries', 3),
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
    
    def _enforce_rate_limit(self, url: str):
        """Enforce per-domain rate limiting"""
        domain = urlparse(url).netloc
        current_time = time.time()
        
        with self._lock:
            last_request = self.last_request_time.get(domain, 0)
            time_since_last = current_time - last_request
            min_delay = self.config.get('request_delay', 1.0)
            
            if time_since_last < min_delay:
                sleep_time = min_delay - time_since_last
                # Add small random jitter to avoid thundering herd
                sleep_time += random.uniform(0, 0.5)
                logger.debug(f"⏳ Rate limiting: sleeping {sleep_time:.2f}s for {domain}")
                time.sleep(sleep_time)
            
            self.last_request_time[domain] = time.time()
    
    def fetch_url(self, url: str, source_category: str = "") -> FetchResult:
        """
        Fetch a single URL with error handling and rate limiting
        
        Args:
            url: URL to fetch
            source_category: Category of the source (e.g., 'svo_primary')
            
        Returns:
            FetchResult object with fetch results
        """
        result = FetchResult(url=url, source_category=source_category)
        start_time = time.time()
        
        try:
            # Enforce rate limiting
            self._enforce_rate_limit(url)
            
            logger.debug(f"🌐 Fetching: {url}")
            
            # Make request with timeout
            response = self.session.get(
                url,
                timeout=self.config.get('timeout', 30),
                allow_redirects=True
            )
            
            result.status_code = response.status_code
            result.headers = dict(response.headers)
            
            if response.status_code == 200:
                result.raw_html = response.text
                result.content = response.text
                logger.debug(f"✅ Successfully fetched {len(result.content)} chars from {url}")
            else:
                result.error = f"HTTP {response.status_code}: {response.reason}"
                logger.warning(f"⚠️  HTTP {response.status_code} for {url}")
                
        except requests.exceptions.Timeout:
            result.error = "Request timeout"
            logger.error(f"⏰ Timeout fetching {url}")
            
        except requests.exceptions.ConnectionError:
            result.error = "Connection error"
            logger.error(f"🔌 Connection error for {url}")
            
        except requests.exceptions.RequestException as e:
            result.error = f"Request exception: {str(e)}"
            logger.error(f"❌ Request exception for {url}: {e}")
            
        except Exception as e:
            result.error = f"Unexpected error: {str(e)}"
            logger.error(f"💥 Unexpected error for {url}: {e}")
        
        result.processing_time = time.time() - start_time
        return result

def fetch_all(urls_config: Dict[str, List[str]], config: Dict[str, Any]) -> List[FetchResult]:
    """
    Main function to fetch all URLs from configuration with robust error handling
    
    Args:
        urls_config: Dictionary of URL categories and their URLs (from config.URLS)
        config: Configuration dictionary (from config.CONFIG)
        
    Returns:
        List of FetchResult objects containing all fetched data
    """
    logger.info("🚀 Starting SVO data fetching pipeline")
    
    # Flatten URLs with categories
    all_urls = []
    for category, urls in urls_config.items():
        for url in urls:
            all_urls.append((url, category))
    
    # Initialize progress tracking
    progress = ScrapingProgress(total_urls=len(all_urls))
    
    # Initialize scraping session
    session = ScrapingSession(config)
    
    # Results storage
    results = []
    
    logger.info(f"📋 Processing {progress.total_urls} URLs across {len(urls_config)} categories")
    
    # Process URLs with optional parallel processing
    max_workers = config.get('max_workers', 1)  # Default to sequential
    
    if max_workers > 1:
        # Parallel processing
        logger.info(f"🔄 Using {max_workers} parallel workers")
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all fetch tasks
            future_to_url = {
                executor.submit(session.fetch_url, url, category): (url, category)
                for url, category in all_urls
            }
            
            # Collect results as they complete
            for future in as_completed(future_to_url):
                url, category = future_to_url[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Update progress
                    progress.processed_urls += 1
                    if result.success:
                        progress.successful_fetches += 1
                        progress.total_content_size += len(result.content)
                    else:
                        progress.failed_fetches += 1
                        if result.error:
                            progress.errors.append(f"{url}: {result.error}")
                    
                    # Log progress periodically
                    if progress.processed_urls % 10 == 0 or progress.processed_urls == progress.total_urls:
                        progress.log_progress()
                        
                except Exception as e:
                    logger.error(f"💥 Error processing {url}: {e}")
                    progress.failed_fetches += 1
                    progress.processed_urls += 1
                    progress.errors.append(f"{url}: {str(e)}")
    else:
        # Sequential processing
        logger.info("🔄 Using sequential processing")
        
        for i, (url, category) in enumerate(all_urls):
            progress.current_source = category
            result = session.fetch_url(url, category)
            results.append(result)
            
            # Update progress
            progress.processed_urls += 1
            if result.success:
                progress.successful_fetches += 1
                progress.total_content_size += len(result.content)
            else:
                progress.failed_fetches += 1
                if result.error:
                    progress.errors.append(f"{url}: {result.error}")
            
            # Log progress
            if (i + 1) % 5 == 0 or (i + 1) == len(all_urls):
                progress.log_progress()
    
    # Final summary
    logger.info("=" * 60)
    logger.info("📊 FETCHING SUMMARY")
    logger.info(f"✅ Successful: {progress.successful_fetches}/{progress.total_urls}")
    logger.info(f"❌ Failed: {progress.failed_fetches}/{progress.total_urls}")
    logger.info(f"📈 Success rate: {progress.success_rate:.1f}%")
    logger.info(f"💾 Total content: {progress.total_content_size / 1024:.1f} KB")
    logger.info(f"⏱️  Total time: {progress.elapsed_time:.1f}s")
    
    if progress.errors:
        logger.warning(f"⚠️  {len(progress.errors)} errors occurred:")
        for error in progress.errors[:5]:  # Show first 5 errors
            logger.warning(f"   - {error}")
        if len(progress.errors) > 5:
            logger.warning(f"   ... and {len(progress.errors) - 5} more errors")
    
    logger.info("=" * 60)
    
    return results

if __name__ == "__main__":
    # Test the fetcher module
    from config import URLS, CONFIG
    
    logger.info("🧪 Testing SVO fetcher module")
    results = fetch_all(URLS, CONFIG)
    
    successful = [r for r in results if r.success]
    logger.info(f"✅ Test complete: {len(successful)}/{len(results)} successful fetches")