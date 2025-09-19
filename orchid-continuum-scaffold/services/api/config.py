"""
Configuration management for The Orchid Continuum API.
"""

import os
from typing import List, Optional
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings."""
    
    # Database
    database_url: str = "postgresql://localhost/orchid_db"
    
    # Security
    secret_key: str = "dev-secret-key-change-in-production"
    access_token_expire_minutes: int = 30
    
    # CORS
    allowed_origins: List[str] = ["http://localhost:3000", "http://localhost:8080"]
    allowed_hosts: List[str] = ["localhost", "127.0.0.1"]
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # Observability
    sentry_dsn: Optional[str] = None
    otel_endpoint: Optional[str] = None
    
    # External services
    redis_url: str = "redis://localhost:6379"
    
    # File storage
    upload_dir: str = "./uploads"
    max_file_size: int = 50 * 1024 * 1024  # 50MB
    
    # AI services
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    
    # Ingestion
    ingest_schedule_enabled: bool = False
    ingest_batch_size: int = 100
    
    # Development
    debug: bool = False
    reload: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = False

def get_settings() -> Settings:
    """Get application settings."""
    return Settings()