-- Database initialization for Chaptr
-- This file is executed when the PostgreSQL container starts for the first time

-- Create database (if not exists)
SELECT 'CREATE DATABASE chaptr'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'chaptr')\gexec

-- Connect to the database
\c chaptr;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create indexes for text search (will be used by SQLAlchemy models)
-- Note: Tables will be created by SQLAlchemy, but we can prepare some initial setup

-- Set timezone
SET timezone = 'UTC';

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Print success message
SELECT 'Chaptr database initialized successfully!' as message; 