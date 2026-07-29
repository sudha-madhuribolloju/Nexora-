-- ==========================================================
-- NEXORA AI Classroom Portal - PostgreSQL Initialization Script
-- ==========================================================
-- This script runs automatically when the PostgreSQL container initializes.

-- 1. Ensure required extensions exist
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- 2. Log status of installed extensions
DO $$
BEGIN
    RAISE NOTICE 'NEXORA PostgreSQL setup: Extensions vector, uuid-ossp, pg_trgm initialized successfully.';
END $$;

-- 3. Set default time zone to UTC
SET timezone TO 'UTC';
