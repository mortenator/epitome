#!/bin/bash
# Build script for Vercel
# This builds the frontend and copies it to the static directory

set -e

echo "Building frontend..."
cd frontend_source
npm ci
npm run build

echo "Copying build output to static directory..."
mkdir -p ../static
cp -r dist/* ../static/

echo "Build complete!"
