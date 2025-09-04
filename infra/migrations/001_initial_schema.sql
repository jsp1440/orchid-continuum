-- Initial schema for Orchid Continuum v2.0
-- Production-grade PostgreSQL database structure

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create custom ENUM types
CREATE TYPE source_type AS ENUM ('google_drive', 'gbif', 'user', 'other');
CREATE TYPE culture_source AS ENUM ('baker', 'aos', 'custom');
CREATE TYPE iucn_status AS ENUM ('LC', 'NT', 'VU', 'EN', 'CR', 'EW', 'EX', 'DD', 'NE');
CREATE TYPE user_role AS ENUM ('admin', 'editor', 'member', 'viewer');
CREATE TYPE collection_status AS ENUM ('active', 'dormant', 'blooming', 'deceased');

-- Main orchids table
CREATE TABLE orchids (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    scientific_name VARCHAR(255) NOT NULL,
    genus VARCHAR(100) NOT NULL,
    species VARCHAR(100),
    hybrid_status BOOLEAN DEFAULT FALSE,
    synonyms JSONB,
    description TEXT,
    growth_habit VARCHAR(50),
    iucn_status iucn_status,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Photos table
CREATE TABLE photos (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchid_id UUID NOT NULL REFERENCES orchids(id) ON DELETE CASCADE,
    source source_type NOT NULL,
    source_ref TEXT,
    url TEXT,
    storage_key VARCHAR(255),
    exif JSONB,
    credited_to VARCHAR(255),
    license VARCHAR(100),
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Culture sheets (Baker, AOS, custom care data)
CREATE TABLE culture_sheets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchid_id UUID REFERENCES orchids(id) ON DELETE CASCADE,
    source culture_source NOT NULL,
    light_low INTEGER,
    light_high INTEGER,
    temp_min DECIMAL(5,2),
    temp_max DECIMAL(5,2),
    humidity_min DECIMAL(5,2),
    humidity_max DECIMAL(5,2),
    water_notes TEXT,
    media_notes TEXT,
    seasonal_notes TEXT,
    citations JSONB,
    version INTEGER DEFAULT 1,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Phenotypic traits
CREATE TABLE traits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchid_id UUID NOT NULL REFERENCES orchids(id) ON DELETE CASCADE,
    phenotypic JSONB NOT NULL
);

-- GBIF occurrences and geographic data
CREATE TABLE occurrences (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchid_id UUID NOT NULL REFERENCES orchids(id) ON DELETE CASCADE,
    gbif_occurrence_id VARCHAR(50),
    lat DECIMAL(10,8),
    lon DECIMAL(11,8),
    elev_m DECIMAL(8,2),
    country VARCHAR(100),
    date_observed TIMESTAMP WITH TIME ZONE,
    raw JSONB
);

-- Citations and references
CREATE TABLE citations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    orchid_id UUID NOT NULL REFERENCES orchids(id) ON DELETE CASCADE,
    doi VARCHAR(255),
    title TEXT NOT NULL,
    source VARCHAR(255),
    url TEXT,
    year INTEGER,
    notes TEXT
);

-- User management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    role user_role NOT NULL DEFAULT 'viewer',
    display_name VARCHAR(255),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Personal collections
CREATE TABLE collections (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    notes TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collection items
CREATE TABLE collection_items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    collection_id UUID NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    orchid_id UUID NOT NULL REFERENCES orchids(id) ON DELETE CASCADE,
    nick_name VARCHAR(255),
    acquired_at TIMESTAMP WITH TIME ZONE,
    last_repot TIMESTAMP WITH TIME ZONE,
    status collection_status DEFAULT 'active',
    care_prefs JSONB
);

-- Audit logging
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    entity VARCHAR(100) NOT NULL,
    entity_id VARCHAR(255) NOT NULL,
    diff JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Data sources configuration
CREATE TABLE sources (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    type source_type NOT NULL,
    auth JSONB,
    status VARCHAR(50) DEFAULT 'active',
    last_sync_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_orchids_scientific_name ON orchids USING GIN (scientific_name gin_trgm_ops);
CREATE INDEX idx_orchids_genus ON orchids (genus);
CREATE INDEX idx_orchids_species ON orchids (species);
CREATE INDEX idx_orchids_growth_habit ON orchids (growth_habit);

CREATE INDEX idx_photos_orchid_id ON photos (orchid_id);
CREATE INDEX idx_photos_source ON photos (source);
CREATE INDEX idx_photos_verified ON photos (is_verified);

CREATE INDEX idx_culture_orchid_id ON culture_sheets (orchid_id);
CREATE INDEX idx_culture_source ON culture_sheets (source);

CREATE INDEX idx_occurrences_orchid_id ON occurrences (orchid_id);
CREATE INDEX idx_occurrences_gbif_id ON occurrences (gbif_occurrence_id);
CREATE INDEX idx_occurrences_location ON occurrences USING GIST (ST_Point(lon, lat));

CREATE INDEX idx_users_email ON users (email);
CREATE INDEX idx_users_role ON users (role);

CREATE INDEX idx_audit_user_id ON audit_log (user_id);
CREATE INDEX idx_audit_created_at ON audit_log (created_at);
CREATE INDEX idx_audit_entity ON audit_log (entity, entity_id);

-- Enable trigram extension for fuzzy text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Create full-text search indexes
CREATE INDEX idx_orchids_fulltext ON orchids USING GIN (
    to_tsvector('english', 
        COALESCE(scientific_name, '') || ' ' || 
        COALESCE(description, '') || ' ' || 
        COALESCE(notes, '')
    )
);

-- Function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_orchids_updated_at BEFORE UPDATE ON orchids 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();