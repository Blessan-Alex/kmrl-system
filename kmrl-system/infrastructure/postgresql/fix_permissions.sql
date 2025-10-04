-- Fix PostgreSQL permissions for KMRL database
-- Run this as postgres superuser

-- Connect to kmrl_db
\c kmrl_db;

-- Grant schema privileges to kmrl_user
GRANT USAGE ON SCHEMA public TO kmrl_user;
GRANT CREATE ON SCHEMA public TO kmrl_user;

-- Grant table privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kmrl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kmrl_user;

-- Grant privileges on future tables
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kmrl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kmrl_user;

-- Make kmrl_user owner of the database
ALTER DATABASE kmrl_db OWNER TO kmrl_user;

-- Grant superuser privileges (for development only)
ALTER USER kmrl_user CREATEDB CREATEROLE;

-- Verify permissions
\du kmrl_user


