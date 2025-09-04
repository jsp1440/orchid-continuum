from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
import json

from database import get_db
from models.existing_models import OrchidRecord

router = APIRouter()

# Response models for existing data
class OrchidResponse(BaseModel):
    id: int
    scientific_name: str = ""
    genus: str = ""
    species: str = ""
    description: str = ""
    photo_url: Optional[str] = None
    drive_id: Optional[str] = None

    class Config:
        from_attributes = True

@router.get("/orchids", response_model=List[OrchidResponse])
async def get_legacy_orchids(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    genus: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Get orchids from existing database"""
    
    query = db.query(OrchidRecord)
    
    if genus:
        query = query.filter(OrchidRecord.genus.ilike(f"%{genus}%"))
    
    orchids = query.offset(offset).limit(limit).all()
    
    results = []
    for orchid in orchids:
        photo_url = None
        if orchid.google_drive_id:
            photo_url = f"https://drive.google.com/uc?id={orchid.google_drive_id}"
        
        # Extract species from scientific name if not provided
        species = orchid.species or ""
        if not species and orchid.scientific_name:
            parts = orchid.scientific_name.split()
            if len(parts) >= 2:
                species = parts[1]
        
        results.append(OrchidResponse(
            id=orchid.id,
            scientific_name=orchid.scientific_name or "",
            genus=orchid.genus or "",
            species=species,
            description=orchid.ai_description or "",
            photo_url=photo_url,
            drive_id=orchid.google_drive_id
        ))
    
    return results

@router.get("/orchids/{orchid_id}", response_model=OrchidResponse)
async def get_legacy_orchid(orchid_id: int, db: Session = Depends(get_db)):
    """Get single orchid from existing database"""
    
    orchid = db.query(OrchidRecord).filter(OrchidRecord.id == orchid_id).first()
    
    if not orchid:
        raise HTTPException(status_code=404, detail="Orchid not found")
    
    photo_url = None
    if orchid.google_drive_id:
        photo_url = f"https://drive.google.com/uc?id={orchid.google_drive_id}"
    
    species = orchid.species or ""
    if not species and orchid.scientific_name:
        parts = orchid.scientific_name.split()
        if len(parts) >= 2:
            species = parts[1]
    
    return OrchidResponse(
        id=orchid.id,
        scientific_name=orchid.scientific_name or "",
        genus=orchid.genus or "",
        species=species,
        description=orchid.ai_description or "",
        photo_url=photo_url,
        drive_id=orchid.google_drive_id
    )

@router.get("/stats")
async def get_database_stats(db: Session = Depends(get_db)):
    """Get database statistics"""
    
    total_orchids = db.query(OrchidRecord).count()
    with_photos = db.query(OrchidRecord).filter(
        OrchidRecord.google_drive_id.isnot(None)
    ).count()
    
    return {
        "total_orchids": total_orchids,
        "with_photos": with_photos,
        "photo_percentage": round((with_photos / total_orchids * 100) if total_orchids > 0 else 0, 1)
    }