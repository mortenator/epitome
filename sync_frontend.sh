#!/bin/bash
# Sync script to pull frontend from Lovable repo and build it

set -e

FRONTEND_REPO="https://github.com/mortenator/blueprint-dash-render.git"
FRONTEND_DIR="frontend_source"
BUILD_OUTPUT="static"

echo "🔄 Syncing frontend from Lovable repo..."

# Clone or update the frontend repo
if [ -d "$FRONTEND_DIR" ]; then
    echo "📥 Updating existing frontend repo..."
    cd "$FRONTEND_DIR"
    git pull origin main
    cd ..
else
    echo "📥 Cloning frontend repo..."
    git clone "$FRONTEND_REPO" "$FRONTEND_DIR"
fi

# Build the frontend
echo "🔨 Building frontend..."
cd "$FRONTEND_DIR"

# Check if node_modules exists, if not install
if [ ! -d "node_modules" ]; then
    echo "📦 Installing dependencies..."
    if command -v bun &> /dev/null; then
        bun install
    elif command -v npm &> /dev/null; then
        npm install
    else
        echo "❌ Error: Neither bun nor npm found. Please install Node.js."
        exit 1
    fi
fi

# Build the frontend
echo "🏗️  Building production bundle..."
if command -v bun &> /dev/null; then
    bun run build
else
    npm run build
fi

# Copy built files to static directory
echo "📋 Copying built files to static/ directory..."
cd ..
rm -rf "$BUILD_OUTPUT"/*
cp -r "$FRONTEND_DIR/dist"/* "$BUILD_OUTPUT/"

echo "✅ Frontend sync complete!"
echo "📁 Built files are in: $BUILD_OUTPUT/"
