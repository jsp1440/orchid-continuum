"""
Orchid Continuum Partner Connect API
Minimal partner integration system with geoprivacy controls
"""

import os
import sqlite3
import hashlib
import hmac
import time
import json
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Literal
from dataclasses import dataclass
import csv
import io
import math

from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File, Query, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

# Database initialization
def init_db():
    """Initialize SQLite database with partner connect schema"""
    conn = sqlite3.connect('partner_connect.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    # Create tables
    conn.executescript('''
        CREATE TABLE IF NOT EXISTS partners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            api_key_hash TEXT NOT NULL,
            scopes TEXT NOT NULL, -- JSON array
            quota_per_day INTEGER DEFAULT 10000,
            active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            partner_id INTEGER NOT NULL,
            source_id TEXT NOT NULL, -- unique per partner
            scientific_name TEXT,
            image_url TEXT,
            credit TEXT,
            license TEXT,
            locality TEXT,
            event_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (partner_id) REFERENCES partners(id),
            UNIQUE(partner_id, source_id)
        );
        
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            lat REAL NOT NULL,
            lng REAL NOT NULL,
            elevation_m REAL,
            geo_visibility TEXT DEFAULT 'public', -- 'public', 'partner_private', 'internal_private'
            coordinate_uncertainty_m INTEGER,
            FOREIGN KEY (record_id) REFERENCES records(id)
        );
        
        CREATE TABLE IF NOT EXISTS phenology_months (
            record_id INTEGER NOT NULL,
            month INTEGER NOT NULL, -- 1-12
            PRIMARY KEY (record_id, month),
            FOREIGN KEY (record_id) REFERENCES records(id)
        );
        
        CREATE TABLE IF NOT EXISTS curation_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            record_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            actor TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (record_id) REFERENCES records(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_records_partner_source ON records(partner_id, source_id);
        CREATE INDEX IF NOT EXISTS idx_locations_visibility ON locations(geo_visibility);
        CREATE INDEX IF NOT EXISTS idx_records_scientific_name ON records(scientific_name);
    ''')
    
    conn.commit()
    conn.close()

# Initialize database on startup
init_db()

# FastAPI app
app = FastAPI(
    title="Orchid Continuum Partner Connect",
    description="Partner integration API with geoprivacy controls",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Rate limiting storage (in-memory for demo, use Redis in production)
rate_limit_storage = {}

# Pydantic models
class RecordUpload(BaseModel):
    source_id: str
    scientific_name: Optional[str] = None
    image_url: Optional[str] = None
    credit: Optional[str] = None
    license: Optional[str] = None
    locality: Optional[str] = None
    event_date: Optional[str] = None
    coords: Optional[Dict[str, float]] = None  # {lat, lng}
    geo_visibility: Literal['public', 'partner_private', 'internal_private'] = 'public'
    coordinateUncertaintyInMeters: Optional[int] = None

class BatchUpload(BaseModel):
    records: List[RecordUpload]

class SearchResponse(BaseModel):
    results: List[Dict[str, Any]]
    total: int
    page: int

class MapFeature(BaseModel):
    type: str = "Feature"
    geometry: Dict[str, Any]
    properties: Dict[str, Any]

class MapResponse(BaseModel):
    type: str = "FeatureCollection"
    features: List[MapFeature]

@dataclass
class Partner:
    id: int
    slug: str
    name: str
    email: str
    scopes: List[str]
    quota_per_day: int
    active: bool

# Utility functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('partner_connect.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def hash_api_key(api_key: str) -> str:
    """Hash API key for storage"""
    return hashlib.sha256(api_key.encode()).hexdigest()

def generalize_coords(lat: float, lng: float, cell_km: int = 25) -> tuple[float, float]:
    """
    Generalize coordinates to a grid for geoprivacy
    Snaps to nearest grid cell center
    """
    # Convert km to degrees (rough approximation)
    cell_deg = cell_km / 111.0  # 1 degree ≈ 111 km
    
    # Snap to grid
    lat_grid = round(lat / cell_deg) * cell_deg
    lng_grid = round(lng / cell_deg) * cell_deg
    
    return lat_grid, lng_grid

def check_rate_limit(api_key: str, quota_per_day: int) -> bool:
    """Check if API key is within rate limit"""
    now = time.time()
    day_start = now - (now % 86400)  # Start of current day
    
    if api_key not in rate_limit_storage:
        rate_limit_storage[api_key] = {}
    
    # Clean old entries
    rate_limit_storage[api_key] = {
        k: v for k, v in rate_limit_storage[api_key].items() 
        if k >= day_start
    }
    
    # Count requests today
    requests_today = sum(rate_limit_storage[api_key].values())
    
    if requests_today >= quota_per_day:
        return False
    
    # Increment counter
    hour_key = int(now // 3600)  # Hour bucket
    rate_limit_storage[api_key][hour_key] = rate_limit_storage[api_key].get(hour_key, 0) + 1
    
    return True

def get_partner_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Partner:
    """Authenticate partner from API key"""
    api_key = credentials.credentials
    api_key_hash = hash_api_key(api_key)
    
    conn = get_db_connection()
    try:
        result = conn.execute(
            "SELECT * FROM partners WHERE api_key_hash = ? AND active = 1",
            (api_key_hash,)
        ).fetchone()
        
        if not result:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        partner = Partner(
            id=result['id'],
            slug=result['slug'],
            name=result['name'],
            email=result['email'],
            scopes=json.loads(result['scopes']),
            quota_per_day=result['quota_per_day'],
            active=bool(result['active'])
        )
        
        # Check rate limit
        if not check_rate_limit(api_key, partner.quota_per_day):
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
                headers={"Retry-After": "3600"}
            )
        
        return partner
        
    finally:
        conn.close()

def require_scope(required_scope: str):
    """Decorator factory to require specific scope"""
    def scope_checker(partner: Partner = Depends(get_partner_from_token)) -> Partner:
        if required_scope not in partner.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Scope '{required_scope}' required"
            )
        return partner
    return scope_checker

# Routes
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}

@app.post("/partner/upload-json")
async def upload_json(
    batch: BatchUpload,
    partner: Partner = Depends(require_scope("write:records"))
):
    """Upload records via JSON batch"""
    conn = get_db_connection()
    try:
        created_count = 0
        updated_count = 0
        
        for record_data in batch.records:
            # Upsert record
            cursor = conn.execute('''
                INSERT INTO records (
                    partner_id, source_id, scientific_name, image_url, 
                    credit, license, locality, event_date, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(partner_id, source_id) DO UPDATE SET
                    scientific_name = excluded.scientific_name,
                    image_url = excluded.image_url,
                    credit = excluded.credit,
                    license = excluded.license,
                    locality = excluded.locality,
                    event_date = excluded.event_date,
                    updated_at = CURRENT_TIMESTAMP
            ''', (
                partner.id,
                record_data.source_id,
                record_data.scientific_name,
                record_data.image_url,
                record_data.credit,
                record_data.license,
                record_data.locality,
                record_data.event_date
            ))
            
            # Get record ID
            record_id = cursor.lastrowid
            if cursor.rowcount == 1:
                created_count += 1
            else:
                updated_count += 1
                # Get existing record ID for updates
                record_id = conn.execute(
                    "SELECT id FROM records WHERE partner_id = ? AND source_id = ?",
                    (partner.id, record_data.source_id)
                ).fetchone()[0]
            
            # Handle location data
            if record_data.coords:
                # Delete existing location
                conn.execute("DELETE FROM locations WHERE record_id = ?", (record_id,))
                
                # Insert new location
                conn.execute('''
                    INSERT INTO locations (
                        record_id, lat, lng, geo_visibility, coordinate_uncertainty_m
                    ) VALUES (?, ?, ?, ?, ?)
                ''', (
                    record_id,
                    record_data.coords['lat'],
                    record_data.coords['lng'],
                    record_data.geo_visibility,
                    record_data.coordinateUncertaintyInMeters
                ))
        
        conn.commit()
        
        return {
            "status": "success",
            "created": created_count,
            "updated": updated_count,
            "total": len(batch.records)
        }
        
    except Exception as e:
        conn.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Upload failed: {str(e)}"
        )
    finally:
        conn.close()

@app.post("/partner/upload-csv")
async def upload_csv(
    file: UploadFile = File(...),
    partner: Partner = Depends(require_scope("write:records"))
):
    """Upload records via CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV format"
        )
    
    try:
        content = await file.read()
        csv_data = content.decode('utf-8')
        reader = csv.DictReader(io.StringIO(csv_data))
        
        # Convert CSV to batch format
        records = []
        for row in reader:
            record = RecordUpload(
                source_id=row.get('source_id', ''),
                scientific_name=row.get('scientific_name'),
                image_url=row.get('image_url'),
                credit=row.get('credit'),
                license=row.get('license'),
                locality=row.get('locality'),
                event_date=row.get('event_date'),
                geo_visibility=row.get('geo_visibility', 'public')
            )
            
            # Handle coordinates
            if row.get('lat') and row.get('lng'):
                record.coords = {
                    'lat': float(row['lat']),
                    'lng': float(row['lng'])
                }
            
            if row.get('coordinate_uncertainty_m'):
                record.coordinateUncertaintyInMeters = int(row['coordinate_uncertainty_m'])
            
            records.append(record)
        
        # Use existing JSON upload logic
        batch = BatchUpload(records=records)
        return await upload_json(batch, partner)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV processing failed: {str(e)}"
        )

@app.get("/widgets/search")
async def widget_search(
    q: str = Query("", description="Search query"),
    page: int = Query(1, description="Page number"),
    partner: Partner = Depends(require_scope("read:widgets"))
) -> SearchResponse:
    """Search records for widget display"""
    conn = get_db_connection()
    try:
        offset = (page - 1) * 20
        
        # Build search query
        search_query = '''
            SELECT r.*, p.name as partner_name
            FROM records r
            JOIN partners p ON r.partner_id = p.id
            WHERE r.scientific_name LIKE ? OR r.locality LIKE ?
            ORDER BY r.created_at DESC
            LIMIT 20 OFFSET ?
        '''
        
        search_term = f"%{q}%"
        results = conn.execute(search_query, (search_term, search_term, offset)).fetchall()
        
        # Count total
        count_query = '''
            SELECT COUNT(*) as total
            FROM records r
            WHERE r.scientific_name LIKE ? OR r.locality LIKE ?
        '''
        total = conn.execute(count_query, (search_term, search_term)).fetchone()['total']
        
        # Format results
        formatted_results = []
        for row in results:
            formatted_results.append({
                'id': row['id'],
                'source_id': row['source_id'],
                'scientific_name': row['scientific_name'],
                'image_url': row['image_url'],
                'credit': row['credit'],
                'license': row['license'],
                'locality': row['locality'],
                'event_date': row['event_date'],
                'partner_name': row['partner_name']
            })
        
        return SearchResponse(
            results=formatted_results,
            total=total,
            page=page
        )
        
    finally:
        conn.close()

@app.get("/widgets/map")
async def widget_map(
    bbox: Optional[str] = Query(None, description="Bounding box: minLng,minLat,maxLng,maxLat"),
    mode: str = Query("public", description="Data mode: public or partner"),
    partner: Partner = Depends(require_scope("read:widgets"))
) -> MapResponse:
    """Get map data with geoprivacy controls"""
    conn = get_db_connection()
    try:
        # Determine if partner can see private data
        can_see_private = (
            mode == "partner" and 
            "read:partner_private_geo" in partner.scopes
        )
        
        # Build query with geoprivacy filter
        if can_see_private:
            visibility_filter = "l.geo_visibility IN ('public', 'partner_private')"
        else:
            visibility_filter = "l.geo_visibility = 'public'"
        
        query = f'''
            SELECT r.*, l.lat, l.lng, l.geo_visibility, l.coordinate_uncertainty_m, p.name as partner_name
            FROM records r
            JOIN locations l ON r.id = l.record_id
            JOIN partners p ON r.partner_id = p.id
            WHERE {visibility_filter}
        '''
        
        params = []
        
        # Add bounding box filter
        if bbox:
            try:
                min_lng, min_lat, max_lng, max_lat = map(float, bbox.split(','))
                query += " AND l.lat BETWEEN ? AND ? AND l.lng BETWEEN ? AND ?"
                params.extend([min_lat, max_lat, min_lng, max_lng])
            except ValueError:
                raise HTTPException(400, "Invalid bbox format")
        
        query += " LIMIT 1000"  # Prevent large responses
        
        results = conn.execute(query, params).fetchall()
        
        # Format as GeoJSON
        features = []
        for row in results:
            lat, lng = row['lat'], row['lng']
            
            # Apply geoprivacy generalization for public mode
            if not can_see_private and row['geo_visibility'] != 'public':
                lat, lng = generalize_coords(lat, lng)
            
            feature = MapFeature(
                geometry={
                    "type": "Point",
                    "coordinates": [lng, lat]
                },
                properties={
                    "id": row['id'],
                    "source_id": row['source_id'],
                    "scientific_name": row['scientific_name'],
                    "locality": row['locality'],
                    "credit": row['credit'],
                    "partner_name": row['partner_name'],
                    "coordinateUncertaintyInMeters": row['coordinate_uncertainty_m']
                }
            )
            features.append(feature)
        
        return MapResponse(features=features)
        
    finally:
        conn.close()

@app.get("/widgets/phenology")
async def widget_phenology(
    taxon: str = Query(..., description="Taxon name"),
    partner: Partner = Depends(require_scope("read:widgets"))
):
    """Get phenology data for taxon"""
    conn = get_db_connection()
    try:
        # Query phenology data
        query = '''
            SELECT pm.month, COUNT(*) as count
            FROM phenology_months pm
            JOIN records r ON pm.record_id = r.id
            WHERE r.scientific_name LIKE ?
            GROUP BY pm.month
            ORDER BY pm.month
        '''
        
        results = conn.execute(query, (f"%{taxon}%",)).fetchall()
        
        # Format as month data
        months = {}
        for row in results:
            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            month_name = month_names[row['month'] - 1]
            months[month_name] = row['count']
        
        return {
            "taxon": taxon,
            "months": months,
            "total_records": sum(months.values())
        }
        
    finally:
        conn.close()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)