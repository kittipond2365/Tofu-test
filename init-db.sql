-- init-db.sql - Initialize database
-- Create user and database

-- Create user (if not exists)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'badminton') THEN
        CREATE USER badminton WITH PASSWORD 'badminton123';
    END IF;
END
$$;

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE badminton_db TO badminton;

-- Connect to badminton_db and grant schema privileges
\c badminton_db;

GRANT ALL ON SCHEMA public TO badminton;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO badminton;
