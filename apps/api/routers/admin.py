from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import List, Dict, Any
from pydantic import BaseModel
from datetime import datetime, timedelta

from database import get_db
from models.orchid_models import Orchid, Photo, User, AuditLog, Source, UserRole
from routers.auth import require_role

router = APIRouter()

class HealthStatus(BaseModel):
    database: str
    total_orchids: int
    total_photos: int
    verified_photos: int
    active_users: int
    recent_activity: int
    storage_health: Dict[str, Any]

class SyncStatus(BaseModel):
    source_name: str
    source_type: str
    last_sync: datetime = None
    status: str
    records_processed: int = 0
    errors: List[str] = []

@router.get("/health", response_model=HealthStatus)
async def get_system_health(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get comprehensive system health status"""
    
    # Database counts
    total_orchids = db.query(func.count(Orchid.id)).scalar()
    total_photos = db.query(func.count(Photo.id)).scalar()
    verified_photos = db.query(func.count(Photo.id)).filter(Photo.is_verified == True).scalar()
    active_users = db.query(func.count(User.id)).filter(User.is_active == True).scalar()
    
    # Recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_activity = db.query(func.count(AuditLog.id)).filter(
        AuditLog.created_at >= yesterday
    ).scalar()
    
    # Photo storage health check
    photo_sources = db.query(
        Photo.source, func.count(Photo.id)
    ).group_by(Photo.source).all()
    
    storage_health = {
        "sources": {source: count for source, count in photo_sources},
        "failsafe_active": True,  # TODO: Implement actual failsafe check
        "broken_links": 0  # TODO: Implement broken link detection
    }
    
    return HealthStatus(
        database="connected",
        total_orchids=total_orchids or 0,
        total_photos=total_photos or 0,
        verified_photos=verified_photos or 0,
        active_users=active_users or 0,
        recent_activity=recent_activity or 0,
        storage_health=storage_health
    )

@router.get("/sync-status", response_model=List[SyncStatus])
async def get_sync_status(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get data source synchronization status"""
    
    sources = db.query(Source).all()
    
    status_list = []
    for source in sources:
        status_list.append(SyncStatus(
            source_name=source.name,
            source_type=source.type.value,
            last_sync=source.last_sync_at,
            status=source.status,
            records_processed=0,  # TODO: Add this to Source model
            errors=[]  # TODO: Add error tracking
        ))
    
    return status_list

@router.post("/sync/{source_name}")
async def trigger_sync(
    source_name: str,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Trigger manual data source synchronization"""
    
    source = db.query(Source).filter(Source.name == source_name).first()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found")
    
    # TODO: Implement actual sync trigger
    # This would call the appropriate ingest function
    
    # Update last sync time
    source.last_sync_at = datetime.utcnow()
    source.status = "syncing"
    db.commit()
    
    return {
        "message": f"Synchronization started for {source_name}",
        "source_id": str(source.id),
        "started_at": source.last_sync_at
    }

@router.get("/audit-log")
async def get_audit_log(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Get recent audit log entries"""
    
    logs = db.query(AuditLog).order_by(
        AuditLog.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    return {
        "logs": [
            {
                "id": str(log.id),
                "user_id": str(log.user_id) if log.user_id else None,
                "action": log.action,
                "entity": log.entity,
                "entity_id": log.entity_id,
                "changes": log.diff,
                "created_at": log.created_at
            }
            for log in logs
        ],
        "total": db.query(func.count(AuditLog.id)).scalar()
    }

@router.get("/data-quality")
async def get_data_quality_report(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Generate data quality report"""
    
    # Orchids without photos
    orphan_orchids = db.query(func.count(Orchid.id)).outerjoin(Photo).filter(
        Photo.orchid_id.is_(None)
    ).scalar()
    
    # Photos without verification
    unverified_photos = db.query(func.count(Photo.id)).filter(
        Photo.is_verified == False
    ).scalar()
    
    # Orchids without culture sheets
    no_culture_data = db.query(func.count(Orchid.id)).outerjoin(
        'culture_sheets'
    ).filter(
        text("culture_sheets.orchid_id IS NULL")
    ).scalar()
    
    # Duplicate scientific names
    duplicates = db.query(
        Orchid.scientific_name, func.count(Orchid.id)
    ).group_by(Orchid.scientific_name).having(
        func.count(Orchid.id) > 1
    ).all()
    
    return {
        "summary": {
            "orphan_orchids": orphan_orchids or 0,
            "unverified_photos": unverified_photos or 0,
            "missing_culture_data": no_culture_data or 0,
            "duplicate_names": len(duplicates)
        },
        "duplicates": [
            {"scientific_name": name, "count": count}
            for name, count in duplicates
        ]
    }

@router.post("/reindex")
async def reindex_search(
    current_user: User = Depends(require_role(UserRole.ADMIN)),
    db: Session = Depends(get_db)
):
    """Rebuild search indexes"""
    
    try:
        # TODO: Implement search index rebuilding
        # This would recreate any full-text search indexes
        
        db.execute(text("REFRESH MATERIALIZED VIEW IF EXISTS orchid_search_mv"))
        db.commit()
        
        return {"message": "Search indexes rebuilt successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to rebuild indexes: {str(e)}"
        )

@router.get("/export/orchids")
async def export_orchids(
    format: str = "json",
    current_user: User = Depends(require_role(UserRole.EDITOR)),
    db: Session = Depends(get_db)
):
    """Export orchid data in various formats"""
    
    orchids = db.query(Orchid).all()
    
    if format == "json":
        return {
            "orchids": [
                {
                    "id": str(orchid.id),
                    "scientific_name": orchid.scientific_name,
                    "genus": orchid.genus,
                    "species": orchid.species,
                    "growth_habit": orchid.growth_habit,
                    "description": orchid.description,
                    "created_at": orchid.created_at.isoformat()
                }
                for orchid in orchids
            ],
            "exported_at": datetime.utcnow().isoformat(),
            "total_records": len(orchids)
        }
    
    # TODO: Implement CSV and other format exports
    raise HTTPException(status_code=400, detail="Unsupported export format")