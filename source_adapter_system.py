#!/usr/bin/env python3
"""
Modular International Orchid Scraping System
Created for Orchid Continuum - Respectful, compliant, extensible architecture
"""

import requests
import time
import logging
import hashlib
import json
from abc import ABC, abstractmethod
from urllib.parse import urljoin, urlparse
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from bs4 import BeautifulSoup
import trafilatura
from PIL import Image
import io

from models import OrchidRecord, ScrapingLog, db
from google_drive_service import upload_to_drive
from orchid_ai import extract_metadata_from_text

logger = logging.getLogger(__name__)

@dataclass
class SourceMetadata:
    """Metadata for a scraped orchid source"""
    source_id: str
    source_name: str
    url: str
    license: str
    rights_holder: str
    country: str
    locality: Optional[str] = None
    collection_date: Optional[datetime] = None
    collector: Optional[str] = None

@dataclass
class OrchidAsset:
    """Represents an orchid image or data asset"""
    image_url: str
    description: str
    scientific_name: Optional[str] = None
    genus: Optional[str] = None
    species: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    license: Optional[str] = None
    
class RespectfulCrawler:
    """Handles respectful crawling with robots.txt compliance and rate limiting"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'OrchidContinuum-Research-Bot/1.0 (+https://orchidcontinuum.replit.app/about)',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive'
        })
        self.robots_cache = {}
        self.rate_limits = {}  # domain -> last_request_time
        self.default_delay = 2  # seconds between requests
        
    def can_fetch(self, url: str) -> bool:
        """Check if we can fetch this URL according to robots.txt (simplified version)"""
        try:
            domain = urlparse(url).netloc
            if domain not in self.robots_cache:
                robots_url = f"https://{domain}/robots.txt"
                robots_response = self.session.get(robots_url, timeout=10)
                if robots_response.status_code == 200:
                    # Simple robots.txt parsing - check for User-agent: * Disallow: /
                    robots_text = robots_response.text.lower()
                    if 'user-agent: *' in robots_text and 'disallow: /' in robots_text:
                        self.robots_cache[domain] = False
                        logger.info(f"📜 Robots.txt disallows crawling for {domain}")
                    else:
                        self.robots_cache[domain] = True
                        logger.info(f"📜 Robots.txt allows crawling for {domain}")
                else:
                    # If no robots.txt, assume we can crawl
                    self.robots_cache[domain] = True
                    logger.info(f"📜 No robots.txt found for {domain}, proceeding")
            
            return self.robots_cache[domain]
            
        except Exception as e:
            logger.warning(f"Could not check robots.txt for {url}: {e}")
            return True  # If we can't check, assume it's OK
    
    def respectful_get(self, url: str, **kwargs) -> Optional[requests.Response]:
        """Make a respectful GET request with rate limiting"""
        domain = urlparse(url).netloc
        
        # Check robots.txt compliance
        if not self.can_fetch(url):
            logger.warning(f"🚫 robots.txt disallows fetching {url}")
            return None
        
        # Apply rate limiting
        if domain in self.rate_limits:
            time_since_last = time.time() - self.rate_limits[domain]
            if time_since_last < self.default_delay:
                sleep_time = self.default_delay - time_since_last
                logger.debug(f"⏱️ Rate limiting: sleeping {sleep_time:.1f}s for {domain}")
                time.sleep(sleep_time)
        
        try:
            response = self.session.get(url, timeout=30, **kwargs)
            self.rate_limits[domain] = time.time()
            
            if response.status_code == 200:
                logger.debug(f"✅ Successfully fetched {url}")
                return response
            else:
                logger.warning(f"⚠️ HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.error(f"❌ Failed to fetch {url}: {e}")
            return None

class SourceAdapter(ABC):
    """Abstract base class for orchid data source adapters"""
    
    def __init__(self, crawler: RespectfulCrawler):
        self.crawler = crawler
        self.stats = {'processed': 0, 'errors': 0, 'skipped': 0}
    
    @abstractmethod
    def get_source_info(self) -> SourceMetadata:
        """Return metadata about this source"""
        pass
    
    @abstractmethod
    def discover_taxa(self, limit: int = 100) -> List[str]:
        """Discover available taxa (genus/species) from the source"""
        pass
    
    @abstractmethod
    def list_assets(self, taxon: str) -> List[OrchidAsset]:
        """List available assets (images, data) for a given taxon"""
        pass
    
    @abstractmethod
    def fetch_record(self, asset: OrchidAsset) -> Optional[Dict[str, Any]]:
        """Fetch detailed record data for an orchid asset"""
        pass
    
    def normalize_to_dwca(self, record: Dict[str, Any], source: SourceMetadata) -> Dict[str, Any]:
        """Normalize record data to Darwin Core Archive format"""
        return {
            'source_id': source.source_id,
            'source_name': source.source_name,
            'source_url': record.get('url', ''),
            'license': source.license,
            'rights_holder': source.rights_holder,
            'country': source.country,
            'locality': source.locality,
            'scientific_name': record.get('scientific_name', ''),
            'genus': record.get('genus', ''),
            'species': record.get('species', ''),
            'image_url': record.get('image_url', ''),
            'description': record.get('description', ''),
            'collection_date': source.collection_date,
            'collector': source.collector,
            'ingestion_date': datetime.utcnow()
        }
    
    def compute_image_hash(self, image_data: bytes) -> str:
        """Compute perceptual hash for image deduplication"""
        try:
            image = Image.open(io.BytesIO(image_data))
            # Simple hash based on resized image
            image = image.resize((8, 8)).convert('L')
            pixels = list(image.getdata())
            avg = sum(pixels) / len(pixels)
            hash_bits = ''.join('1' if p > avg else '0' for p in pixels)
            return hash_bits
        except Exception as e:
            logger.error(f"Failed to compute image hash: {e}")
            return hashlib.md5(image_data).hexdigest()

class IOSPEAdapter(SourceAdapter):
    """Internet Orchid Species Photo Encyclopedia adapter"""
    
    def get_source_info(self) -> SourceMetadata:
        return SourceMetadata(
            source_id="iospe",
            source_name="Internet Orchid Species Photo Encyclopedia",
            url="https://orchidspecies.com/",
            license="Educational Use - Attribution Required",
            rights_holder="Internet Orchid Species Photo Encyclopedia",
            country="Global",
            locality="Various"
        )
    
    def discover_taxa(self, limit: int = 100) -> List[str]:
        """Discover orchid genera from IOSPE alphabetical index"""
        genera = []
        try:
            url = "https://orchidspecies.com/indexalpha.htm"
            response = self.crawler.respectful_get(url)
            if not response:
                return genera
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find genus links
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                text = link.get_text().strip()
                
                # Look for genus pages - handle None values
                if href and isinstance(href, str) and href.endswith('.htm') and text and len(text) > 2:
                    if text.istitle() and not any(char.isdigit() for char in text):
                        genera.append(text)
                        if len(genera) >= limit:
                            break
            
            logger.info(f"🌱 Discovered {len(genera)} genera from IOSPE")
            return genera[:limit]
            
        except Exception as e:
            logger.error(f"Failed to discover taxa from IOSPE: {e}")
            return genera
    
    def list_assets(self, genus: str) -> List[OrchidAsset]:
        """List orchid images for a genus from IOSPE"""
        assets = []
        try:
            # Construct genus page URL (this is a simplified approach)
            genus_url = f"https://orchidspecies.com/{genus.lower()}gen.htm"
            response = self.crawler.respectful_get(genus_url)
            if not response:
                return assets
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find image and species links
            for img in soup.find_all('img'):
                src = img.get('src')
                alt = img.get('alt', '') or ''
                
                if src and isinstance(src, str) and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    # Extract species name from alt text or nearby elements
                    scientific_name = self._extract_scientific_name(alt, soup)
                    
                    asset = OrchidAsset(
                        image_url=urljoin(genus_url, str(src)),
                        description=str(alt),
                        scientific_name=scientific_name,
                        genus=genus,
                        species=scientific_name.split()[-1] if scientific_name and ' ' in scientific_name else None
                    )
                    assets.append(asset)
            
            logger.info(f"🖼️ Found {len(assets)} assets for {genus} from IOSPE")
            return assets
            
        except Exception as e:
            logger.error(f"Failed to list assets for {genus} from IOSPE: {e}")
            return assets
    
    def fetch_record(self, asset: OrchidAsset) -> Optional[Dict[str, Any]]:
        """Fetch detailed orchid record from IOSPE"""
        try:
            # Get the image page URL (usually linked from the thumbnail)
            response = self.crawler.respectful_get(asset.image_url)
            if not response:
                return None
            
            # Extract text content for AI analysis
            text_content = trafilatura.extract(response.text) or ""
            
            # Use AI to extract metadata
            ai_metadata = extract_metadata_from_text(text_content) if text_content else {}
            
            return {
                'url': asset.image_url,
                'scientific_name': asset.scientific_name or ai_metadata.get('scientific_name', ''),
                'genus': asset.genus or ai_metadata.get('genus', ''),
                'species': asset.species or ai_metadata.get('species', ''),
                'description': asset.description,
                'image_url': asset.image_url,
                'text_content': text_content,
                'ai_metadata': ai_metadata
            }
            
        except Exception as e:
            logger.error(f"Failed to fetch record for {asset.image_url}: {e}")
            return None
    
    def _extract_scientific_name(self, alt_text: str, soup: BeautifulSoup) -> Optional[str]:
        """Extract scientific name from alt text or surrounding context"""
        # Simple extraction - can be enhanced
        if alt_text and isinstance(alt_text, str) and len(alt_text.split()) >= 2:
            words = alt_text.split()
            if words[0].istitle() and words[1].islower():
                return f"{words[0]} {words[1]}"
        return None

class SingaporeAdapter(SourceAdapter):
    """Singapore Botanic Gardens adapter"""
    
    def get_source_info(self) -> SourceMetadata:
        return SourceMetadata(
            source_id="singapore_botanic",
            source_name="Singapore Botanic Gardens",
            url="https://www.nparks.gov.sg/sbg/",
            license="Educational Use - Attribution Required",
            rights_holder="National Parks Singapore",
            country="Singapore",
            locality="Singapore Botanic Gardens"
        )
    
    def discover_taxa(self, limit: int = 100) -> List[str]:
        """Discover taxa from Singapore Botanic Gardens"""
        # Implementation would depend on their specific site structure
        return []
    
    def list_assets(self, taxon: str) -> List[OrchidAsset]:
        """List assets from Singapore Botanic Gardens"""
        # Implementation would depend on their specific site structure
        return []
    
    def fetch_record(self, asset: OrchidAsset) -> Optional[Dict[str, Any]]:
        """Fetch record from Singapore Botanic Gardens"""
        # Implementation would depend on their specific site structure
        return None

class IngestionOrchestrator:
    """Orchestrates the ingestion process across multiple sources"""
    
    def __init__(self):
        self.crawler = RespectfulCrawler()
        self.adapters = {}
        self.register_adapters()
    
    def register_adapters(self):
        """Register all available source adapters"""
        self.adapters['iospe'] = IOSPEAdapter(self.crawler)
        self.adapters['singapore'] = SingaporeAdapter(self.crawler)
        logger.info(f"📋 Registered {len(self.adapters)} source adapters")
    
    def run_collection(self, source_ids: List[str], max_records_per_source: int = 100) -> Dict[str, Any]:
        """Run collection process for specified sources"""
        results = {}
        
        for source_id in source_ids:
            if source_id not in self.adapters:
                logger.warning(f"Unknown source: {source_id}")
                continue
            
            logger.info(f"🌍 Starting collection from {source_id}")
            adapter = self.adapters[source_id]
            
            try:
                # Log collection start
                log_entry = ScrapingLog()
                log_entry.source = source_id
                log_entry.url = adapter.get_source_info().url
                log_entry.status = 'processing'
                log_entry.items_found = 0
                log_entry.items_processed = 0
                db.session.add(log_entry)
                db.session.commit()
                
                # Discover taxa
                taxa = adapter.discover_taxa(limit=20)  # Start with 20 genera
                total_processed = 0
                
                for taxon in taxa:
                    if total_processed >= max_records_per_source:
                        break
                    
                    logger.info(f"🔍 Processing {taxon} from {source_id}")
                    
                    # List assets for this taxon
                    assets = adapter.list_assets(taxon)
                    
                    for asset in assets:
                        if total_processed >= max_records_per_source:
                            break
                        
                        # Fetch detailed record
                        record = adapter.fetch_record(asset)
                        if record:
                            # Normalize to Darwin Core
                            normalized = adapter.normalize_to_dwca(record, adapter.get_source_info())
                            
                            # Check for duplicates
                            if not self._is_duplicate(normalized):
                                # Save to database
                                if self._save_orchid_record(normalized):
                                    total_processed += 1
                                    adapter.stats['processed'] += 1
                                    logger.info(f"✅ Saved: {normalized.get('scientific_name', 'Unknown')}")
                                else:
                                    adapter.stats['errors'] += 1
                            else:
                                adapter.stats['skipped'] += 1
                                logger.debug(f"⏭️ Skipped duplicate: {normalized.get('scientific_name', 'Unknown')}")
                        
                        # Respectful delay between records
                        time.sleep(1)
                
                # Update log entry
                log_entry.status = 'completed'
                log_entry.items_found = len(taxa)
                log_entry.items_processed = total_processed
                db.session.commit()
                
                results[source_id] = {
                    'processed': adapter.stats['processed'],
                    'errors': adapter.stats['errors'],
                    'skipped': adapter.stats['skipped'],
                    'taxa_discovered': len(taxa)
                }
                
                logger.info(f"✅ Completed {source_id}: {total_processed} records processed")
                
            except Exception as e:
                logger.error(f"❌ Error processing {source_id}: {e}")
                log_entry.status = 'error'
                log_entry.error_message = str(e)
                db.session.commit()
                results[source_id] = {'error': str(e)}
        
        return results
    
    def _is_duplicate(self, record: Dict[str, Any]) -> bool:
        """Check if record already exists in database"""
        scientific_name = record.get('scientific_name', '')
        source_url = record.get('source_url', '')
        
        if scientific_name:
            existing = OrchidRecord.query.filter_by(
                scientific_name=scientific_name,
                ingestion_source=record.get('source_id')
            ).first()
            return existing is not None
        
        return False
    
    def _save_orchid_record(self, record: Dict[str, Any]) -> bool:
        """Save normalized record to OrchidRecord table"""
        try:
            orchid_record = OrchidRecord()
            orchid_record.display_name = record.get('scientific_name', 'Unknown')
            orchid_record.scientific_name = record.get('scientific_name')
            orchid_record.genus = record.get('genus')
            orchid_record.species = record.get('species')
            orchid_record.country = record.get('country')
            orchid_record.locality = record.get('locality')
            orchid_record.photo_url = record.get('image_url')
            orchid_record.description = record.get('description')
            orchid_record.ingestion_source = f"international_{record.get('source_id')}"
            orchid_record.photographer_credit = record.get('rights_holder')
            orchid_record.photo_date_taken = record.get('collection_date')
            orchid_record.license_attribution = record.get('license')
            orchid_record.created_at = datetime.utcnow()
            
            db.session.add(orchid_record)
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save orchid record: {e}")
            db.session.rollback()
            return False

# Usage example and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    orchestrator = IngestionOrchestrator()
    results = orchestrator.run_collection(['iospe'], max_records_per_source=50)
    
    print("\n🎯 Collection Results:")
    for source_id, result in results.items():
        print(f"  {source_id}: {result}")