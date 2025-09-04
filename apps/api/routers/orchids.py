from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import List, Optional
from pydantic import BaseModel, UUID4
from datetime import datetime

from database import get_db
from models.orchid_models import Orchid, Photo, CultureSheet, Trait, Occurrence, User, UserRole
from routers.auth import get_user_from_token, require_role

router = APIRouter()

# Pydantic response models
class PhotoResponse(BaseModel):
    id: UUID4
    source: str
    url: Optional[str]
    credited_to: Optional[str]
    is_verified: bool

    class Config:
        from_attributes = True

class CultureSheetResponse(BaseModel):
    id: UUID4
    source: str
    light_low: Optional[int]
    light_high: Optional[int]
    temp_min: Optional[float]
    temp_max: Optional[float]
    humidity_min: Optional[float]
    humidity_max: Optional[float]
    water_notes: Optional[str]
    seasonal_notes: Optional[str]

    class Config:
        from_attributes = True

class OrchidSummary(BaseModel):
    id: UUID4
    scientific_name: str
    genus: str
    species: Optional[str]
    growth_habit: Optional[str]
    description: Optional[str]
    photo_count: int
    primary_photo: Optional[PhotoResponse]

    class Config:
        from_attributes = True

class OrchidDetail(BaseModel):
    id: UUID4
    scientific_name: str
    genus: str
    species: Optional[str]
    hybrid_status: bool
    synonyms: Optional[dict]
    description: Optional[str]
    growth_habit: Optional[str]
    iucn_status: Optional[str]
    notes: Optional[str]
    created_at: datetime
    photos: List[PhotoResponse]
    culture_sheets: List[CultureSheetResponse]

    class Config:
        from_attributes = True

class OrchidCreate(BaseModel):
    scientific_name: str
    genus: str
    species: Optional[str] = None
    hybrid_status: bool = False
    description: Optional[str] = None
    growth_habit: Optional[str] = None
    notes: Optional[str] = None

# Routes
@router.get("/", response_model=List[OrchidSummary])
async def get_orchids(
    query: Optional[str] = Query(None, description="Search query for scientific name or description"),
    genus: Optional[str] = Query(None, description="Filter by genus"),
    growth_habit: Optional[str] = Query(None, description="Filter by growth habit"),
    light_min: Optional[int] = Query(None, description="Minimum light requirement (foot-candles)"),
    light_max: Optional[int] = Query(None, description="Maximum light requirement (foot-candles)"),
    temp_min: Optional[float] = Query(None, description="Minimum temperature (Celsius)"),
    temp_max: Optional[float] = Query(None, description="Maximum temperature (Celsius)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db)
):
    """Get orchids with optional filtering and pagination"""
    
    # Base query
    query_builder = db.query(Orchid).options(
        joinedload(Orchid.photos)
    )
    
    # Apply filters
    if query:
        query_builder = query_builder.filter(
            or_(
                Orchid.scientific_name.ilike(f"%{query}%"),
                Orchid.description.ilike(f"%{query}%"),
                Orchid.notes.ilike(f"%{query}%")
            )
        )
    
    if genus:
        query_builder = query_builder.filter(Orchid.genus.ilike(f"%{genus}%"))
    
    if growth_habit:
        query_builder = query_builder.filter(Orchid.growth_habit.ilike(f"%{growth_habit}%"))
    
    # Culture sheet filters (requires join)
    if any([light_min, light_max, temp_min, temp_max]):
        query_builder = query_builder.join(CultureSheet, Orchid.id == CultureSheet.orchid_id)
        
        if light_min:
            query_builder = query_builder.filter(CultureSheet.light_high >= light_min)
        if light_max:
            query_builder = query_builder.filter(CultureSheet.light_low <= light_max)
        if temp_min:
            query_builder = query_builder.filter(CultureSheet.temp_max >= temp_min)
        if temp_max:
            query_builder = query_builder.filter(CultureSheet.temp_min <= temp_max)
    
    # Pagination
    offset = (page - 1) * limit
    orchids = query_builder.offset(offset).limit(limit).all()
    
    # Format response
    result = []
    for orchid in orchids:
        primary_photo = None
        if orchid.photos:
            # Prefer verified photos
            verified_photos = [p for p in orchid.photos if p.is_verified]
            if verified_photos:
                primary_photo = verified_photos[0]
            else:
                primary_photo = orchid.photos[0]
        
        result.append(OrchidSummary(
            id=orchid.id,
            scientific_name=orchid.scientific_name,
            genus=orchid.genus,
            species=orchid.species,
            growth_habit=orchid.growth_habit,
            description=orchid.description,
            photo_count=len(orchid.photos),
            primary_photo=primary_photo
        ))
    
    return result

@router.get("/{orchid_id}", response_model=OrchidDetail)
async def get_orchid(orchid_id: UUID4, db: Session = Depends(get_db)):
    """Get detailed orchid information"""
    
    orchid = db.query(Orchid).options(
        joinedload(Orchid.photos),
        joinedload(Orchid.culture_sheets),
        joinedload(Orchid.traits),
        joinedload(Orchid.occurrences),
        joinedload(Orchid.citations)
    ).filter(Orchid.id == orchid_id).first()
    
    if not orchid:
        raise HTTPException(status_code=404, detail="Orchid not found")
    
    return orchid

@router.post("/", response_model=OrchidDetail)
async def create_orchid(
    orchid_data: OrchidCreate,
    current_user: User = Depends(require_role(UserRole.EDITOR)),
    db: Session = Depends(get_db)
):
    """Create a new orchid record (Editor+ only)"""
    
    # Check for duplicate scientific name
    existing = db.query(Orchid).filter(
        Orchid.scientific_name == orchid_data.scientific_name
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Orchid with this scientific name already exists"
        )
    
    # Create new orchid
    new_orchid = Orchid(**orchid_data.dict())
    db.add(new_orchid)
    db.commit()
    db.refresh(new_orchid)
    
    return new_orchid

@router.get("/{orchid_id}/care-wheel")
async def get_care_wheel(orchid_id: UUID4, db: Session = Depends(get_db)):
    """Generate care wheel data for an orchid"""
    
    orchid = db.query(Orchid).options(
        joinedload(Orchid.culture_sheets)
    ).filter(Orchid.id == orchid_id).first()
    
    if not orchid:
        raise HTTPException(status_code=404, detail="Orchid not found")
    
    # Default care wheel values
    care_wheel = {
        "light": 50,
        "temperature": 50,
        "humidity": 50,
        "water": 50,
        "fertilizer": 50,
        "airflow": 50
    }
    
    # Calculate from culture sheets
    if orchid.culture_sheets:
        culture_data = orchid.culture_sheets[0]  # Use primary culture sheet
        
        # Light (convert foot-candles to 0-100 scale)
        if culture_data.light_low and culture_data.light_high:
            avg_light = (culture_data.light_low + culture_data.light_high) / 2
            care_wheel["light"] = min(100, max(0, (avg_light / 3000) * 100))
        
        # Temperature (convert Celsius to 0-100 scale)
        if culture_data.temp_min and culture_data.temp_max:
            avg_temp = (culture_data.temp_min + culture_data.temp_max) / 2
            care_wheel["temperature"] = min(100, max(0, ((avg_temp - 10) / 25) * 100))
        
        # Humidity (direct percentage to 0-100 scale)
        if culture_data.humidity_min and culture_data.humidity_max:
            avg_humidity = (culture_data.humidity_min + culture_data.humidity_max) / 2
            care_wheel["humidity"] = min(100, max(0, avg_humidity))
    
    return {
        "orchid_id": str(orchid_id),
        "scientific_name": orchid.scientific_name,
        "care_wheel": care_wheel,
        "culture_sources": [cs.source.value for cs in orchid.culture_sheets]
    }