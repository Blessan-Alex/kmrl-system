#!/bin/bash

# Fix PostgreSQL permissions for KMRL database
echo "🔧 Fixing PostgreSQL permissions for KMRL database..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "❌ PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

echo "📝 Granting necessary privileges to kmrl_user..."

# Try to connect as postgres superuser and grant privileges
# Note: You may need to enter the postgres password
psql -h localhost -U postgres -d kmrl_db << 'EOF'
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

-- Grant superuser privileges for development (optional)
-- ALTER USER kmrl_user CREATEDB CREATEROLE;

-- Verify permissions
\du kmrl_user
EOF

if [ $? -eq 0 ]; then
    echo "✅ Permissions granted successfully!"
    echo "🧪 Testing database initialization..."
    
    # Test the database initialization
    python3 migrations/init_db.py init
    
    if [ $? -eq 0 ]; then
        echo "✅ Database initialization successful!"
        echo "🎉 PostgreSQL is ready for KMRL Gateway!"
    else
        echo "❌ Database initialization still failing."
        echo "💡 Try running as postgres superuser:"
        echo "   sudo -u postgres psql -d kmrl_db -c \"ALTER USER kmrl_user CREATEDB CREATEROLE;\""
    fi
else
    echo "❌ Failed to grant permissions."
    echo "💡 You may need to run this as postgres superuser or provide the postgres password."
fi

