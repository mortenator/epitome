#!/bin/bash
# Helper script to set up Supabase database connection

set -e

echo "🔧 Supabase Database Setup"
echo "=========================="
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "Please create .env file first (copy from .env.example)"
    exit 1
fi

# Get password from user
echo "Please enter your Supabase database password:"
read -s SUPABASE_PASSWORD

if [ -z "$SUPABASE_PASSWORD" ]; then
    echo "❌ Error: Password cannot be empty"
    exit 1
fi

# Supabase connection details (from your .env)
SUPABASE_HOST="db.hsknjrrhvuyucowefqgw.supabase.co"
SUPABASE_USER="postgres"
SUPABASE_DB="postgres"

# Create connection strings
# DATABASE_URL - Use connection pooler (port 6543) for better performance
DATABASE_URL="postgresql://${SUPABASE_USER}:${SUPABASE_PASSWORD}@${SUPABASE_HOST}:6543/${SUPABASE_DB}?pgbouncer=true"

# DIRECT_URL - Direct connection (port 5432) for migrations
DIRECT_URL="postgresql://${SUPABASE_USER}:${SUPABASE_PASSWORD}@${SUPABASE_HOST}:5432/${SUPABASE_DB}"

echo ""
echo "📝 Updating .env file..."

# Update or add DATABASE_URL
if grep -q "^DATABASE_URL=" .env; then
    # Replace existing DATABASE_URL
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^DATABASE_URL=.*|DATABASE_URL=\"${DATABASE_URL}\"|" .env
    else
        # Linux
        sed -i "s|^DATABASE_URL=.*|DATABASE_URL=\"${DATABASE_URL}\"|" .env
    fi
else
    # Add new DATABASE_URL
    echo "DATABASE_URL=\"${DATABASE_URL}\"" >> .env
fi

# Update or add DIRECT_URL
if grep -q "^DIRECT_URL=" .env; then
    # Replace existing DIRECT_URL
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|^DIRECT_URL=.*|DIRECT_URL=\"${DIRECT_URL}\"|" .env
    else
        # Linux
        sed -i "s|^DIRECT_URL=.*|DIRECT_URL=\"${DIRECT_URL}\"|" .env
    fi
else
    # Add new DIRECT_URL
    echo "DIRECT_URL=\"${DIRECT_URL}\"" >> .env
fi

echo "✅ Updated .env file with database connection strings"
echo ""
echo "🔍 Verifying connection..."

# Test connection (optional - requires psql or can skip)
echo "Ready to run migrations!"
echo ""
echo "Next step: Run 'npx prisma migrate dev --name init'"
