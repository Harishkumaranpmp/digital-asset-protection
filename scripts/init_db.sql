-- ============================================================
-- SportShield — PostgreSQL Initialization Script
-- Run automatically on first `docker-compose up` via entrypoint
-- ============================================================

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For fuzzy text search

-- Create initial admin placeholder (populated by seed script)
-- Tables are created by SQLAlchemy on startup (create_tables())

-- Set timezone
SET timezone = 'UTC';
