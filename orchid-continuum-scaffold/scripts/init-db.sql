-- Initialize PostgreSQL database with required extensions
-- This script is automatically run when using docker-compose

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create database user if not exists (in case running manually)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'orchid_user') THEN
        CREATE USER orchid_user WITH PASSWORD 'orchid_dev_password';
    END IF;
END
$$;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE orchid_dev TO orchid_user;
GRANT ALL ON SCHEMA public TO orchid_user;

-- Log successful initialization
SELECT 'Database initialized with PostGIS and pgvector extensions' AS status;