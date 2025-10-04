#!/bin/bash

# Fix PostgreSQL permissions for KMRL database
echo "🔧 Fixing PostgreSQL permissions for KMRL database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Run the permission fix script
echo "📝 Applying permission fixes..."
psql -h localhost -U postgres -d kmrl_db -f ../infrastructure/postgresql/fix_permissions.sql

if [ $? -eq 0 ]; then
    echo "✅ Permissions fixed successfully!"
    echo "🧪 Testing database initialization..."
    
    # Test the database initialization
    python3 migrations/init_db.py init
    
    if [ $? -eq 0 ]; then
        echo "✅ Database initialization successful!"
    else
        echo "❌ Database initialization still failing. Trying alternative approach..."
        echo "🔄 Switching to SQLite fallback..."
        export DATABASE_URL="sqlite:///./kmrl_gateway.db"
        python3 migrations/init_db.py init
    fi
else
    echo "❌ Failed to fix permissions. Trying SQLite fallback..."
    echo "🔄 Switching to SQLite fallback..."
    export DATABASE_URL="sqlite:///./kmrl_gateway.db"
    python3 migrations/init_db.py init
fi

