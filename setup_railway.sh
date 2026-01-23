#!/bin/bash
# Railway Setup Helper Script
# This script helps you set up Railway environment variables

set -e

echo "🚂 Railway Setup Helper"
echo "======================"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  No .env file found. Please create one or provide your environment variables."
    echo ""
    read -p "Do you want to continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Function to set Railway variable
set_railway_var() {
    local var_name=$1
    local var_value=$2
    
    if [ -z "$var_value" ]; then
        echo "⚠️  Skipping $var_name (not set)"
        return
    fi
    
    echo "Setting $var_name..."
    npx @railway/cli variables set "$var_name"="$var_value" || {
        echo "❌ Failed to set $var_name"
        return 1
    }
    echo "✅ Set $var_name"
}

# Load .env file if it exists
if [ -f .env ]; then
    echo "📄 Loading variables from .env file..."
    export $(grep -v '^#' .env | xargs)
    echo ""
fi

echo "Setting Railway environment variables..."
echo ""

# Set variables (will prompt if not in .env)
set_railway_var "DATABASE_URL" "${DATABASE_URL:-}"
set_railway_var "DIRECT_URL" "${DIRECT_URL:-}"
set_railway_var "GOOGLE_MAPS_API_KEY" "${GOOGLE_MAPS_API_KEY:-}"
set_railway_var "GEMINI_API_KEY" "${GEMINI_API_KEY:-}"
set_railway_var "LOGO_DEV_API_KEY" "${LOGO_DEV_API_KEY:-}"
set_railway_var "EXA_API_KEY" "${EXA_API_KEY:-}"

echo ""
echo "✅ Environment variables setup complete!"
echo ""
echo "Next steps:"
echo "1. Run: npx @railway/cli up"
echo "2. Or deploy via Railway dashboard"
echo ""
