"""
FastAPI main application with auth, rate limiting, and core endpoints.
"""

import os
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any
import uvicorn
from fastapi import FastAPI, Depends, HTTPException, status, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
import json

from database import DatabaseManager, Record, Media, Location, User, CurationEvent
from auth import AuthManager, get_current_user, require_role
from config import get_settings

# Configuration
settings = get_settings()

# Observability setup
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        integrations=[FastApiIntegration(auto_enabling_integrations=False)],
        traces_sample_rate=0.1,
    )

# OpenTelemetry setup
if settings.otel_endpoint:
    trace.set_tracer_provider(TracerProvider())
    otlp_exporter = OTLPSpanExporter(endpoint=settings.otel_endpoint)
    span_processor = BatchSpanProcessor(otlp_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)

# Prometheus metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Database
db_manager = DatabaseManager(settings.database_url)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    db_manager.enable_extensions()
    db_manager.create_tables()
    yield
    # Shutdown
    pass

# FastAPI app
app = FastAPI(
    title="The Orchid Continuum API",
    description="Research platform API with neutral field names",
    version="0.1.0",
    lifespan=lifespan
)

# Middleware
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=settings.allowed_hosts)

# Rate limit handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Auth setup
auth_manager = AuthManager(settings.secret_key)
security = HTTPBearer()

# OpenTelemetry instrumentation
FastAPIInstrumentor.instrument_app(app)

# Pydantic models
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str

class SearchRequest(BaseModel):
    q: Optional[str] = None
    filters: Optional[Dict[str, Any]] = None
    semantic: bool = False
    page: int = 1
    limit: int = 20

class SearchResult(BaseModel):
    id: UUID
    title: str
    scientific_name: Optional[str]
    description: Optional[str]
    thumbnail_url: Optional[str]
    created_at: datetime

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    page: int
    pages: int

class MapQuery(BaseModel):
    bbox: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    elevation_min: Optional[float] = None
    elevation_max: Optional[float] = None

class PhenologyResponse(BaseModel):
    taxon: str
    region: Optional[str]
    months: Dict[str, int]  # month -> count

class CurationItem(BaseModel):
    id: UUID
    title: str
    confidence: float
    suggested_tags: List[str]
    needs_review_reason: str

class CurationAction(BaseModel):
    action: str  # approve, flag, merge, reject
    notes: Optional[str] = None
    merge_target_id: Optional[UUID] = None

# Dependency injection
def get_db():
    return next(db_manager.get_session())

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    """Collect Prometheus metrics."""
    with REQUEST_DURATION.time():
        response = await call_next(request)
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path
        ).inc()
    return response

# Routes
@app.get("/health", response_model=HealthResponse)
@limiter.limit("10/minute")
async def health_check(request: Request):
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow(),
        version="0.1.0"
    )

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/search", response_model=SearchResponse)
@limiter.limit("30/minute")
async def search_records(
    request: Request,
    search_req: SearchRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Search records with text and semantic options."""
    query = db.query(Record)
    
    # Text search
    if search_req.q:
        query = query.filter(
            Record.title.ilike(f"%{search_req.q}%") |
            Record.scientific_name.ilike(f"%{search_req.q}%") |
            Record.description.ilike(f"%{search_req.q}%")
        )
    
    # Apply filters
    if search_req.filters:
        if "family" in search_req.filters:
            query = query.filter(Record.taxonomy_family == search_req.filters["family"])
        if "genus" in search_req.filters:
            query = query.filter(Record.taxonomy_genus == search_req.filters["genus"])
    
    # Pagination
    total = query.count()
    offset = (search_req.page - 1) * search_req.limit
    records = query.offset(offset).limit(search_req.limit).all()
    
    # Build response
    results = []
    for record in records:
        thumbnail_url = None
        if record.media_items:
            thumbnail_url = record.media_items[0].file_url
        
        results.append(SearchResult(
            id=record.id,
            title=record.title,
            scientific_name=record.scientific_name,
            description=record.description,
            thumbnail_url=thumbnail_url,
            created_at=record.created_at
        ))
    
    pages = (total + search_req.limit - 1) // search_req.limit
    
    return SearchResponse(
        results=results,
        total=total,
        page=search_req.page,
        pages=pages
    )

@app.get("/map/tiles")
@limiter.limit("100/minute")
async def get_map_tiles(
    request: Request,
    z: int = Query(..., ge=0, le=18),
    x: int = Query(...),
    y: int = Query(...),
    current_user: User = Depends(get_current_user)
):
    """Get map tiles for visualization."""
    # Return demo tile URL - in production this would serve actual tiles
    return {
        "tile_url": f"https://demo-tiles.example.com/{z}/{x}/{y}.png",
        "attribution": "Demo tiles for development"
    }

@app.post("/map/query")
@limiter.limit("60/minute")
async def query_map_data(
    request: Request,
    map_query: MapQuery,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Query geographic data for map display."""
    query = db.query(Location).join(Record)
    
    # Apply bounding box filter
    if map_query.bbox:
        min_lon, min_lat, max_lon, max_lat = map_query.bbox
        query = query.filter(
            Location.longitude >= min_lon,
            Location.longitude <= max_lon,
            Location.latitude >= min_lat,
            Location.latitude <= max_lat
        )
    
    # Apply elevation filter
    if map_query.elevation_min is not None:
        query = query.filter(Location.elevation >= map_query.elevation_min)
    if map_query.elevation_max is not None:
        query = query.filter(Location.elevation <= map_query.elevation_max)
    
    locations = query.limit(1000).all()  # Limit for performance
    
    # Build GeoJSON response
    features = []
    for location in locations:
        if location.latitude and location.longitude:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [location.longitude, location.latitude]
                },
                "properties": {
                    "record_id": str(location.record_id),
                    "title": location.record.title if location.record else "",
                    "elevation": location.elevation,
                    "habitat": location.habitat_type
                }
            })
    
    return {
        "type": "FeatureCollection",
        "features": features
    }

@app.get("/phenology", response_model=PhenologyResponse)
@limiter.limit("30/minute")
async def get_phenology_data(
    request: Request,
    taxon: str = Query(...),
    region: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user)
):
    """Get phenology data for a taxon and region."""
    # Demo data - in production this would query actual phenology records
    months = {
        "Jan": 5, "Feb": 8, "Mar": 15, "Apr": 25, "May": 35,
        "Jun": 45, "Jul": 38, "Aug": 30, "Sep": 20, "Oct": 12,
        "Nov": 8, "Dec": 6
    }
    
    return PhenologyResponse(
        taxon=taxon,
        region=region,
        months=months
    )

@app.get("/curation/queue", response_model=List[CurationItem])
@limiter.limit("20/minute")
async def get_curation_queue(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("curator"))
):
    """Get items needing curation review."""
    # Get low-confidence records needing review
    records = db.query(Record).filter(
        Record.verification_status == "pending",
        Record.ai_confidence < 0.8
    ).limit(50).all()
    
    items = []
    for record in records:
        items.append(CurationItem(
            id=record.id,
            title=record.title,
            confidence=record.ai_confidence or 0.0,
            suggested_tags=["needs_review"],
            needs_review_reason="Low AI confidence"
        ))
    
    return items

@app.post("/curation/queue/{record_id}/action")
@limiter.limit("100/minute")
async def perform_curation_action(
    request: Request,
    record_id: UUID,
    action: CurationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("curator"))
):
    """Perform curation action on a record."""
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record not found")
    
    # Update record status based on action
    if action.action == "approve":
        record.verification_status = "approved"
        record.is_verified = True
    elif action.action == "flag":
        record.verification_status = "flagged"
    elif action.action == "reject":
        record.verification_status = "rejected"
    
    # Create curation event
    event = CurationEvent(
        record_id=record_id,
        action_type=action.action,
        curator_id=current_user.id,
        notes=action.notes,
        metadata={"merge_target_id": str(action.merge_target_id)} if action.merge_target_id else None
    )
    
    db.add(event)
    db.commit()
    
    return {"status": "success", "action": action.action}

@app.get("/export/csv")
@limiter.limit("5/minute")
async def export_csv(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export records as CSV with rights filtering."""
    # This would implement CSV export with rights checking
    return {"download_url": "/exports/demo_export.csv", "expires_at": datetime.utcnow()}

@app.get("/export/bibtex")
@limiter.limit("5/minute")
async def export_bibtex(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Export records as BibTeX with rights filtering."""
    # This would implement BibTeX export with rights checking
    return {"download_url": "/exports/demo_export.bib", "expires_at": datetime.utcnow()}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        reload=True
    )