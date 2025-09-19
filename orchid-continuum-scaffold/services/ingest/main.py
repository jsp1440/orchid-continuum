"""
Ingest service stubs for The Orchid Continuum.
Contains placeholder interfaces for external data source integration.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Protocol
from dataclasses import dataclass
from abc import ABC, abstractmethod
from celery import Celery
from celery.schedules import crontab
import httpx

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery configuration
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
celery_app = Celery("ingest-worker", broker=redis_url, backend=redis_url)

# Configuration
INGEST_ENABLED = os.getenv("INGEST_SCHEDULE_ENABLED", "false").lower() == "true"
BATCH_SIZE = int(os.getenv("INGEST_BATCH_SIZE", "100"))
MAX_RETRIES = 3
RETRY_BACKOFF = 300  # 5 minutes

@dataclass
class IngestionRecord:
    """Standardized record format for ingestion."""
    external_id: str
    source_name: str
    title: str
    scientific_name: Optional[str]
    description: Optional[str]
    image_urls: List[str]
    metadata: Dict[str, Any]
    location_data: Optional[Dict[str, Any]]
    timestamp: datetime

@dataclass
class IngestionResult:
    """Result of an ingestion operation."""
    success_count: int
    error_count: int
    skipped_count: int
    errors: List[str]
    processed_ids: List[str]

class DataSourceInterface(ABC):
    """Abstract interface for external data sources."""
    
    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass
    
    @abstractmethod
    async def test_connection(self) -> bool:
        """Test connection to the data source."""
        pass
    
    @abstractmethod
    async def fetch_records(self, since: Optional[datetime] = None, limit: int = 100) -> List[IngestionRecord]:
        """Fetch records from the data source."""
        pass
    
    @abstractmethod
    async def get_record_count(self) -> int:
        """Get total number of available records."""
        pass

class GBIFDataSource(DataSourceInterface):
    """GBIF (Global Biodiversity Information Facility) data source stub."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.gbif.org/v1"
        self._source_name = "gbif"
    
    @property
    def source_name(self) -> str:
        return self._source_name
    
    async def test_connection(self) -> bool:
        """Test GBIF API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/occurrence/search", params={"limit": 1})
                return response.status_code == 200
        except Exception as e:
            logger.error(f"GBIF connection test failed: {e}")
            return False
    
    async def fetch_records(self, since: Optional[datetime] = None, limit: int = 100) -> List[IngestionRecord]:
        """Fetch orchid records from GBIF."""
        # Placeholder implementation - in production this would:
        # 1. Query GBIF API with proper filters for Orchidaceae
        # 2. Handle pagination
        # 3. Parse response into IngestionRecord format
        # 4. Include proper attribution and rights information
        
        logger.info(f"Fetching {limit} records from GBIF (placeholder)")
        
        # Return empty list - actual implementation would be proprietary
        return []
    
    async def get_record_count(self) -> int:
        """Get total orchid records available in GBIF."""
        # Placeholder - would query GBIF for actual count
        return 0

class InatDataSource(DataSourceInterface):
    """iNaturalist data source stub."""
    
    def __init__(self):
        self.base_url = "https://api.inaturalist.org/v1"
        self._source_name = "inaturalist"
    
    @property
    def source_name(self) -> str:
        return self._source_name
    
    async def test_connection(self) -> bool:
        """Test iNaturalist API connection."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/observations", params={"per_page": 1})
                return response.status_code == 200
        except Exception as e:
            logger.error(f"iNaturalist connection test failed: {e}")
            return False
    
    async def fetch_records(self, since: Optional[datetime] = None, limit: int = 100) -> List[IngestionRecord]:
        """Fetch orchid observations from iNaturalist."""
        # Placeholder implementation
        logger.info(f"Fetching {limit} records from iNaturalist (placeholder)")
        return []
    
    async def get_record_count(self) -> int:
        """Get total orchid observations available."""
        return 0

class FlickrDataSource(DataSourceInterface):
    """Flickr photo data source stub."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.flickr.com/services/rest"
        self._source_name = "flickr"
    
    @property
    def source_name(self) -> str:
        return self._source_name
    
    async def test_connection(self) -> bool:
        """Test Flickr API connection."""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.base_url,
                    params={
                        "method": "flickr.test.echo",
                        "api_key": self.api_key,
                        "format": "json",
                        "nojsoncallback": 1
                    }
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Flickr connection test failed: {e}")
            return False
    
    async def fetch_records(self, since: Optional[datetime] = None, limit: int = 100) -> List[IngestionRecord]:
        """Fetch orchid photos from Flickr."""
        # Placeholder implementation
        logger.info(f"Fetching {limit} records from Flickr (placeholder)")
        return []
    
    async def get_record_count(self) -> int:
        """Get total orchid photos available."""
        return 0

class IngestionManager:
    """Manages data ingestion from multiple sources."""
    
    def __init__(self):
        self.sources: Dict[str, DataSourceInterface] = {}
        self._register_sources()
    
    def _register_sources(self):
        """Register available data sources."""
        # Only register sources with available credentials/config
        gbif_key = os.getenv("GBIF_API_KEY")
        if gbif_key:
            self.sources["gbif"] = GBIFDataSource(gbif_key)
        
        # iNaturalist doesn't require API key for basic access
        self.sources["inaturalist"] = InatDataSource()
        
        flickr_key = os.getenv("FLICKR_API_KEY")
        if flickr_key:
            self.sources["flickr"] = FlickrDataSource(flickr_key)
        
        logger.info(f"Registered {len(self.sources)} data sources: {list(self.sources.keys())}")
    
    async def test_all_connections(self) -> Dict[str, bool]:
        """Test connections to all registered sources."""
        results = {}
        for name, source in self.sources.items():
            try:
                results[name] = await source.test_connection()
            except Exception as e:
                logger.error(f"Connection test failed for {name}: {e}")
                results[name] = False
        return results
    
    async def ingest_from_source(self, source_name: str, limit: int = BATCH_SIZE) -> IngestionResult:
        """Ingest records from a specific source."""
        if source_name not in self.sources:
            raise ValueError(f"Unknown source: {source_name}")
        
        source = self.sources[source_name]
        logger.info(f"Starting ingestion from {source_name}")
        
        try:
            # Fetch records
            records = await source.fetch_records(limit=limit)
            
            # Process records (placeholder)
            success_count = 0
            error_count = 0
            skipped_count = 0
            errors = []
            processed_ids = []
            
            for record in records:
                try:
                    # In production, this would:
                    # 1. Check for duplicates
                    # 2. Validate record data
                    # 3. Transform to internal format
                    # 4. Save to database
                    # 5. Queue for AI processing
                    
                    logger.debug(f"Processing record {record.external_id} from {source_name}")
                    success_count += 1
                    processed_ids.append(record.external_id)
                    
                except Exception as e:
                    error_count += 1
                    errors.append(f"Record {record.external_id}: {str(e)}")
                    logger.error(f"Failed to process record {record.external_id}: {e}")
            
            result = IngestionResult(
                success_count=success_count,
                error_count=error_count,
                skipped_count=skipped_count,
                errors=errors,
                processed_ids=processed_ids
            )
            
            logger.info(f"Ingestion from {source_name} completed: {success_count} success, {error_count} errors")
            return result
            
        except Exception as e:
            logger.error(f"Ingestion from {source_name} failed: {e}")
            raise

# Celery tasks
@celery_app.task(bind=True, max_retries=MAX_RETRIES)
def run_scheduled_ingestion(self, source_name: str):
    """Run scheduled ingestion for a data source."""
    try:
        logger.info(f"Running scheduled ingestion for {source_name}")
        
        manager = IngestionManager()
        result = asyncio.run(manager.ingest_from_source(source_name))
        
        # Log metrics
        logger.info(f"Scheduled ingestion completed for {source_name}: {result}")
        
        return {
            "source": source_name,
            "result": result.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Scheduled ingestion failed for {source_name}: {e}")
        if self.request.retries < MAX_RETRIES:
            raise self.retry(countdown=RETRY_BACKOFF * (2 ** self.request.retries))
        raise

@celery_app.task
def test_source_connections():
    """Test connections to all data sources."""
    try:
        manager = IngestionManager()
        results = asyncio.run(manager.test_all_connections())
        
        logger.info(f"Connection test results: {results}")
        
        # Alert on failed connections
        failed_sources = [name for name, status in results.items() if not status]
        if failed_sources:
            logger.warning(f"Failed connections: {failed_sources}")
        
        return {
            "results": results,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Connection testing failed: {e}")
        raise

@celery_app.task
def manual_ingestion(source_name: str, limit: int = BATCH_SIZE):
    """Manually trigger ingestion from a specific source."""
    try:
        logger.info(f"Manual ingestion triggered for {source_name}")
        
        manager = IngestionManager()
        result = asyncio.run(manager.ingest_from_source(source_name, limit))
        
        return {
            "source": source_name,
            "result": result.__dict__,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Manual ingestion failed for {source_name}: {e}")
        raise

# Celery beat schedule (disabled by default)
if INGEST_ENABLED:
    celery_app.conf.beat_schedule = {
        'test-connections-hourly': {
            'task': 'main.test_source_connections',
            'schedule': crontab(minute=0),  # Every hour
        },
        'ingest-gbif-daily': {
            'task': 'main.run_scheduled_ingestion',
            'schedule': crontab(hour=2, minute=0),  # Daily at 2 AM
            'args': ('gbif',)
        },
        'ingest-inaturalist-daily': {
            'task': 'main.run_scheduled_ingestion',
            'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
            'args': ('inaturalist',)
        },
        'ingest-flickr-weekly': {
            'task': 'main.run_scheduled_ingestion',
            'schedule': crontab(hour=4, minute=0, day_of_week=1),  # Weekly on Monday at 4 AM
            'args': ('flickr',)
        },
    }

celery_app.conf.timezone = 'UTC'

if __name__ == "__main__":
    # Start Celery worker
    celery_app.start()