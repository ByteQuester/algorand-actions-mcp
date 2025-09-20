#!/bin/bash
# PostgreSQL Setup Script for Lending Platform
# Sets up database, tables, and initial configuration

set -e

echo "🗄️ POSTGRESQL SETUP FOR LENDING PLATFORM"
echo "========================================"

# Configuration
DB_NAME="${DB_NAME:-lending_platform}"
DB_USER="${DB_USER:-lending_admin}"
DB_PASSWORD="${DB_PASSWORD:-secure_password_123}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

# Check if PostgreSQL is installed
if ! command -v psql &> /dev/null; then
    echo "❌ PostgreSQL is not installed. Please install PostgreSQL first."
    echo "   Ubuntu/Debian: sudo apt install postgresql postgresql-contrib"
    echo "   MacOS: brew install postgresql"
    exit 1
fi

echo "✅ PostgreSQL found"

# Create database and user (if not exists)
echo "📝 Creating database and user..."

sudo -u postgres psql <<EOF || true
-- Create user if not exists
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_user WHERE usename = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    END IF;
END
\$\$;

-- Create database if not exists
SELECT 'CREATE DATABASE $DB_NAME OWNER $DB_USER'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec

-- Grant all privileges
GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOF

echo "✅ Database and user created"

# Export connection string
export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"
echo "📌 DATABASE_URL=$DATABASE_URL"

# Save to .env file
echo "DATABASE_URL=$DATABASE_URL" > .env
echo "✅ Connection string saved to .env"

echo ""
echo "🎉 PostgreSQL setup complete!"
echo "   Database: $DB_NAME"
echo "   User: $DB_USER"
echo "   Host: $DB_HOST:$DB_PORT"
echo ""
echo "Next steps:"
echo "1. Run migration script: python scripts/deployment/create_audit_tables.py"
echo "2. Start the API server: python src/api/server.py"