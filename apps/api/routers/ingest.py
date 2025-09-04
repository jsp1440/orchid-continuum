from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
import httpx
import asyncio
from datetime import datetime

from database import get_db
from models.orchid_models import Orchid, Photo, Occurrence, Citation, Source, SourceType, User, UserRole
from routers.auth import require_role

router = APIRouter()

class GBIFIngestRequest(BaseModel):
    scientific_name: str
    limit: int = 100
    include_media: bool = True
    include_occurrences: bool = True

class IngestResult(BaseModel):
    source: str
    scientific_name: str
    orchids_processed: int
    photos_added: int
    occurrences_added: int
    citations_added: int
    errors: List[str]

# GBIF Integration
async def fetch_gbif_data(scientific_name: str, limit: int = 100) -> Dict[str, Any]:
    """Fetch data from GBIF API"""
    
    async with httpx.AsyncClient() as client:
        # First, get the species key
        species_response = await client.get(
            "https://api.gbif.org/v1/species/match",
            params={"name": scientific_name}
        )
        
        if species_response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to match species in GBIF")
        
        species_data = species_response.json()
        species_key = species_data.get("usageKey")
        
        if not species_key:
            raise HTTPException(status_code=404, detail="Species not found in GBIF")
        
        # Get occurrences
        occurrences_response = await client.get(
            "https://api.gbif.org/v1/occurrence/search",
            params={
                "taxonKey": species_key,
                "hasCoordinate": "true",
                "limit": limit
            }
        )
        
        # Get media
        media_response = await client.get(
            "https://api.gbif.org/v1/species/{}/media".format(species_key),
            params={"limit": 50}
        )
        
        return {
            "species": species_data,
            "occurrences": occurrences_response.json() if occurrences_response.status_code == 200 else {"results": []},
            "media": media_response.json() if media_response.status_code == 200 else {"results": []}
        }

@router.post("/gbif", response_model=IngestResult)
async def ingest_from_gbif(
    request: GBIFIngestRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(require_role(UserRole.EDITOR)),
    db: Session = Depends(get_db)
):
    """Ingest orchid data from GBIF"""
    
    try:
        # Fetch data from GBIF
        gbif_data = await fetch_gbif_data(request.scientific_name, request.limit)
        
        # Process in background
        background_tasks.add_task(
            process_gbif_data,
            gbif_data,
            request,
            str(current_user.id)
        )
        
        return IngestResult(
            source="GBIF",
            scientific_name=request.scientific_name,
            orchids_processed=1,
            photos_added=0,  # Will be updated by background task
            occurrences_added=0,
            citations_added=0,
            errors=[]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GBIF ingestion failed: {str(e)}")

async def process_gbif_data(gbif_data: Dict, request: GBIFIngestRequest, user_id: str):
    """Background task to process GBIF data"""
    
    # This would run in the background and process the GBIF data
    # For now, just a placeholder
    
    from database import SessionLocal
    db = SessionLocal()
    
    try:
        species_info = gbif_data["species"]
        
        # Find or create orchid
        orchid = db.query(Orchid).filter(
            Orchid.scientific_name == request.scientific_name
        ).first()
        
        if not orchid:
            orchid = Orchid(
                scientific_name=request.scientific_name,
                genus=species_info.get("genus", ""),
                species=species_info.get("species", ""),
                description=species_info.get("description", "")
            )
            db.add(orchid)
            db.commit()
            db.refresh(orchid)
        
        # Process media if requested
        if request.include_media:
            for media_item in gbif_data["media"]["results"]:
                if media_item.get("type") == "StillImage":
                    photo = Photo(
                        orchid_id=orchid.id,
                        source=SourceType.GBIF,
                        source_ref=str(media_item.get("key")),
                        url=media_item.get("identifier"),
                        credited_to=media_item.get("creator"),
                        license=media_item.get("license")
                    )
                    db.add(photo)
        
        # Process occurrences if requested
        if request.include_occurrences:
            for occurrence in gbif_data["occurrences"]["results"]:
                if occurrence.get("decimalLatitude") and occurrence.get("decimalLongitude"):
                    occ = Occurrence(
                        orchid_id=orchid.id,
                        gbif_occurrence_id=str(occurrence.get("key")),
                        lat=occurrence.get("decimalLatitude"),
                        lon=occurrence.get("decimalLongitude"),
                        country=occurrence.get("country"),
                        date_observed=occurrence.get("eventDate"),
                        raw=occurrence
                    )
                    db.add(occ)
        
        db.commit()
        
    finally:
        db.close()

# Google Drive Integration
@router.post("/google-drive")
async def ingest_from_google_drive(
    folder_id: str,
    current_user: User = Depends(require_role(UserRole.EDITOR)),
    db: Session = Depends(get_db)
):
    """Ingest photos from Google Drive folder"""
    
    # TODO: Implement Google Drive API integration
    # This would use the existing Google Drive integration from the current system
    
    return {
        "message": f"Google Drive ingestion started for folder {folder_id}",
        "status": "processing"
    }

# EOL Integration  
@router.post("/eol")
async def ingest_from_eol(
    scientific_name: str,
    current_user: User = Depends(require_role(UserRole.EDITOR)),
    db: Session = Depends(get_db)
):
    """Ingest trait data from Encyclopedia of Life"""
    
    # TODO: Implement EOL API integration
    # This would fetch trait and characteristic data
    
    return {
        "message": f"EOL ingestion started for {scientific_name}",
        "status": "processing"
    }

@router.get("/sources")
async def list_data_sources(
    current_user: User = Depends(require_role(UserRole.VIEWER)),
    db: Session = Depends(get_db)
):
    """List all configured data sources"""
    
    sources = db.query(Source).all()
    
    return {
        "sources": [
            {
                "id": str(source.id),
                "name": source.name,
                "type": source.type.value,
                "status": source.status,
                "last_sync": source.last_sync_at
            }
            for source in sources
        ]
    }

@router.post("/sources")
async def create_data_source(
    name: str,
    source_type: SourceType,
    auth_config: Optional[Dict] = None,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Create a new data source configuration"""
    
    source = Source(
        name=name,
        type=source_type,
        auth=auth_config or {},
        status="active"
    )
    
    db.add(source)
    db.commit()
    db.refresh(source)
    
    return {
        "id": str(source.id),
        "name": source.name,
        "type": source.type.value,
        "created_at": source.created_at
    }