#!/bin/bash

# PostgreSQL Setup Script for KMRL Knowledge Hub
# This script sets up PostgreSQL with proper permissions for ENUM types

echo "🐘 Setting up PostgreSQL for KMRL Knowledge Hub..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    echo "   On Ubuntu/Debian: sudo systemctl start postgresql"
    echo "   On Windows: Start PostgreSQL service"
    exit 1
fi

# Set PostgreSQL password for postgres user
export PGPASSWORD=${POSTGRES_PASSWORD:-postgres}

echo "📝 Creating database and user..."

# Create database and user with proper permissions
psql -h localhost -U postgres -c "
-- Create database
CREATE DATABASE kmrl_db;

-- Create user with necessary privileges
CREATE USER kmrl_user WITH PASSWORD 'kmrl_password';

-- Grant database privileges
GRANT ALL PRIVILEGES ON DATABASE kmrl_db TO kmrl_user;

-- Connect to kmrl_db and set up schema permissions
\c kmrl_db;

-- Grant schema privileges (required for ENUM creation)
GRANT USAGE ON SCHEMA public TO kmrl_user;
GRANT CREATE ON SCHEMA public TO kmrl_user;

-- Grant table privileges
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO kmrl_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO kmrl_user;

-- Grant privileges on future objects
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO kmrl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO kmrl_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TYPES TO kmrl_user;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";

-- Make kmrl_user owner of the database (gives full control)
ALTER DATABASE kmrl_db OWNER TO kmrl_user;

-- Grant additional privileges for development
ALTER USER kmrl_user CREATEDB CREATEROLE;
"

if [ $? -eq 0 ]; then
    echo "✅ PostgreSQL setup completed successfully!"
    echo "🔍 Verifying permissions..."
    
    # Test the connection with kmrl_user
    psql -h localhost -U kmrl_user -d kmrl_db -c "SELECT current_user, current_database();"
    
    if [ $? -eq 0 ]; then
        echo "✅ Database connection test successful!"
        echo "🎉 PostgreSQL is ready for KMRL Gateway!"
    else
        echo "❌ Database connection test failed!"
        exit 1
    fi
else
    echo "❌ PostgreSQL setup failed!"
    exit 1
fi

