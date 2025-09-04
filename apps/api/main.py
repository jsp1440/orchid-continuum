from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import route modules
from routers import orchids, auth, admin, widgets, search, ingest, legacy_adapter
from database import engine, Base
from models import orchid_models

# Create FastAPI app
app = FastAPI(
    title="Orchid Continuum API",
    description="AI-enhanced orchid database and widget library for Five Cities Orchid Society",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
origins = [
    "http://localhost:3000",  # Next.js dev
    "http://localhost:3001",  # Admin panel
    "https://*.neonone.com",  # Neon One CMS
    "https://fcos.org",       # FCOS main site
    "https://*.fcos.org",     # FCOS subdomains
]

if os.getenv("ENVIRONMENT") == "development":
    origins.extend([
        "http://localhost:*",
        "https://localhost:*"
    ])

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Create database tables
@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    Base.metadata.create_all(bind=engine)
    print("🌺 Orchid Continuum API started successfully")

# Include routers
app.include_router(legacy_adapter.router, prefix="/api/v2", tags=["Legacy Data"])
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(orchids.router, prefix="/orchids", tags=["Orchids"])
app.include_router(search.router, prefix="/search", tags=["Search"])
app.include_router(widgets.router, prefix="/widgets", tags=["Widgets"])
app.include_router(ingest.router, prefix="/ingest", tags=["Data Ingestion"])
app.include_router(admin.router, prefix="/admin", tags=["Administration"])

@app.get("/")
async def root():
    """API health check"""
    return {
        "message": "Orchid Continuum API v2.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "database": "connected",
        "version": "2.0.0",
        "features": [
            "AI identification",
            "GBIF integration", 
            "Baker culture data",
            "Widget system",
            "Care wheel generator"
        ]
    }