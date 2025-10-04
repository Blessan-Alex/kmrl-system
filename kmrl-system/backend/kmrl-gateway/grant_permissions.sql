-- Grant PostgreSQL permissions for KMRL database
-- Run this as postgres superuser: psql -h localhost -U postgres -d kmrl_db -f grant_permissions.sql

-- Grant all necessary privileges to kmrl_user
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO kmrl_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kmrl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kmrl_user;

-- Grant privileges on future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kmrl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kmrl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO kmrl_user;

-- Make kmrl_user owner of the database
ALTER DATABASE kmrl_db OWNER TO kmrl_user;

-- Grant additional privileges for development
ALTER USER kmrl_user CREATEDB CREATEROLE;

-- Verify permissions
\du kmrl_user

