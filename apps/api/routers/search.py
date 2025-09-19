from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_, and_, func
from typing import List, Optional
from pydantic import BaseModel

from database import get_db
from models.orchid_models import Orchid, CultureSheet, Photo

router = APIRouter()

class GrowingConditions(BaseModel):
    light: Optional[str] = None  # very_low, low, medium, high, very_high
    temperature: Optional[str] = None  # cool, cool_intermediate, intermediate, cool_warm, warm
    humidity: Optional[str] = None  # low, moderate, high, very_high

class ConditionMatch(BaseModel):
    id: str
    scientific_name: str
    genus: str
    species: Optional[str]
    growth_habit: Optional[str]
    description: Optional[str]
    match_score: float
    care_summary: dict
    primary_photo_url: Optional[str]

@router.get("/conditions", response_model=List[ConditionMatch])
async def search_by_conditions(
    light: Optional[str] = Query(None, description="Light requirement level"),
    temperature: Optional[str] = Query(None, description="Temperature range preference"),
    humidity: Optional[str] = Query(None, description="Humidity range preference"),
    limit: int = Query(12, ge=1, le=50, description="Maximum results to return"),
    db: Session = Depends(get_db)
):
    """Search orchids by growing conditions"""
    
    # Define condition mappings
    light_ranges = {
        "very_low": (0, 800),
        "low": (800, 1200),
        "medium": (1200, 2000),
        "high": (2000, 3000),
        "very_high": (3000, 5000)
    }
    
    temp_ranges = {
        "cool": (10, 20),
        "cool_intermediate": (15, 22),
        "intermediate": (18, 25),
        "cool_warm": (20, 28),
        "warm": (25, 35)
    }
    
    humidity_ranges = {
        "low": (30, 50),
        "moderate": (50, 70),
        "high": (70, 85),
        "very_high": (85, 95)
    }
    
    # Start with base query
    query = db.query(Orchid).options(
        joinedload(Orchid.culture_sheets),
        joinedload(Orchid.photos)
    )
    
    # Build filter conditions
    conditions = []
    
    if light and light in light_ranges:
        light_min, light_max = light_ranges[light]
        conditions.append(
            and_(
                CultureSheet.light_low >= light_min * 0.8,  # Allow 20% tolerance
                CultureSheet.light_high <= light_max * 1.2
            )
        )
    
    if temperature and temperature in temp_ranges:
        temp_min, temp_max = temp_ranges[temperature]
        conditions.append(
            and_(
                CultureSheet.temp_min >= temp_min - 3,  # Allow 3°C tolerance
                CultureSheet.temp_max <= temp_max + 3
            )
        )
    
    if humidity and humidity in humidity_ranges:
        humid_min, humid_max = humidity_ranges[humidity]
        conditions.append(
            and_(
                CultureSheet.humidity_min >= humid_min - 10,  # Allow 10% tolerance
                CultureSheet.humidity_max <= humid_max + 10
            )
        )
    
    # Apply conditions if any filters specified
    if conditions:
        query = query.join(CultureSheet).filter(and_(*conditions))
    
    # Get results
    orchids = query.limit(limit * 2).all()  # Get extra to allow for scoring
    
    # Calculate match scores and format results
    results = []
    for orchid in orchids:
        match_score = calculate_match_score(orchid, light, temperature, humidity)
        
        # Get primary photo
        primary_photo_url = None
        if orchid.photos:
            verified_photos = [p for p in orchid.photos if p.is_verified]
            primary_photo = verified_photos[0] if verified_photos else orchid.photos[0]
            primary_photo_url = primary_photo.url
        
        # Get care summary from culture sheets
        care_summary = {}
        if orchid.culture_sheets:
            cs = orchid.culture_sheets[0]
            care_summary = {
                "light_range": f"{cs.light_low}-{cs.light_high} FC" if cs.light_low and cs.light_high else None,
                "temp_range": f"{cs.temp_min}-{cs.temp_max}°C" if cs.temp_min and cs.temp_max else None,
                "humidity_range": f"{cs.humidity_min}-{cs.humidity_max}%" if cs.humidity_min and cs.humidity_max else None,
                "source": cs.source.value
            }
        
        results.append(ConditionMatch(
            id=str(orchid.id),
            scientific_name=orchid.scientific_name,
            genus=orchid.genus,
            species=orchid.species,
            growth_habit=orchid.growth_habit,
            description=orchid.description,
            match_score=match_score,
            care_summary=care_summary,
            primary_photo_url=primary_photo_url
        ))
    
    # Sort by match score and limit results
    results.sort(key=lambda x: x.match_score, reverse=True)
    return results[:limit]

def calculate_match_score(orchid: Orchid, light: str, temperature: str, humidity: str) -> float:
    """Calculate how well an orchid matches the specified conditions"""
    score = 0.0
    factors = 0
    
    if not orchid.culture_sheets:
        return 0.5  # Default score for orchids without culture data
    
    culture_sheet = orchid.culture_sheets[0]
    
    # Light matching
    if light and culture_sheet.light_low and culture_sheet.light_high:
        light_ranges = {
            "very_low": (0, 800),
            "low": (800, 1200),
            "medium": (1200, 2000),
            "high": (2000, 3000),
            "very_high": (3000, 5000)
        }
        
        if light in light_ranges:
            target_min, target_max = light_ranges[light]
            orchid_min = culture_sheet.light_low
            orchid_max = culture_sheet.light_high
            
            # Calculate overlap
            overlap_min = max(target_min, orchid_min)
            overlap_max = min(target_max, orchid_max)
            
            if overlap_max > overlap_min:
                overlap = overlap_max - overlap_min
                target_range = target_max - target_min
                score += (overlap / target_range)
            
            factors += 1
    
    # Temperature matching
    if temperature and culture_sheet.temp_min and culture_sheet.temp_max:
        temp_ranges = {
            "cool": (10, 20),
            "cool_intermediate": (15, 22),
            "intermediate": (18, 25),
            "cool_warm": (20, 28),
            "warm": (25, 35)
        }
        
        if temperature in temp_ranges:
            target_min, target_max = temp_ranges[temperature]
            orchid_min = culture_sheet.temp_min
            orchid_max = culture_sheet.temp_max
            
            # Calculate overlap
            overlap_min = max(target_min, orchid_min)
            overlap_max = min(target_max, orchid_max)
            
            if overlap_max > overlap_min:
                overlap = overlap_max - overlap_min
                target_range = target_max - target_min
                score += (overlap / target_range)
            
            factors += 1
    
    # Humidity matching
    if humidity and culture_sheet.humidity_min and culture_sheet.humidity_max:
        humidity_ranges = {
            "low": (30, 50),
            "moderate": (50, 70),
            "high": (70, 85),
            "very_high": (85, 95)
        }
        
        if humidity in humidity_ranges:
            target_min, target_max = humidity_ranges[humidity]
            orchid_min = culture_sheet.humidity_min
            orchid_max = culture_sheet.humidity_max
            
            # Calculate overlap
            overlap_min = max(target_min, orchid_min)
            overlap_max = min(target_max, orchid_max)
            
            if overlap_max > overlap_min:
                overlap = overlap_max - overlap_min
                target_range = target_max - target_min
                score += (overlap / target_range)
            
            factors += 1
    
    # Return average score across all factors
    return score / factors if factors > 0 else 0.5

@router.get("/autocomplete")
async def autocomplete_search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(10, ge=1, le=20),
    db: Session = Depends(get_db)
):
    """Get autocomplete suggestions for orchid search"""
    
    # Search scientific names and common names
    suggestions = db.query(Orchid.scientific_name, Orchid.genus).filter(
        or_(
            Orchid.scientific_name.ilike(f"%{q}%"),
            Orchid.genus.ilike(f"%{q}%")
        )
    ).limit(limit).all()
    
    # Format results
    results = []
    for name, genus in suggestions:
        results.append({
            "text": name,
            "type": "species",
            "genus": genus
        })
    
    # Add genus suggestions
    genus_suggestions = db.query(Orchid.genus).filter(
        Orchid.genus.ilike(f"%{q}%")
    ).distinct().limit(5).all()
    
    for (genus,) in genus_suggestions:
        if not any(r["text"] == genus for r in results):
            results.append({
                "text": genus,
                "type": "genus"
            })
    
    return {"suggestions": results}