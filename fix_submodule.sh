#!/bin/bash
# Script to convert frontend_source from nested git repo to regular directory

set -e

echo "🔧 Converting frontend_source from nested git repo to regular directory..."
echo ""

# Step 1: Remove the nested .git directory
if [ -d "frontend_source/.git" ]; then
    echo "📁 Removing nested .git directory..."
    rm -rf frontend_source/.git
    echo "✅ Removed nested .git"
else
    echo "ℹ️  No nested .git found (might already be removed)"
fi

# Step 2: Remove .gitignore if it exists (to avoid issues)
if [ -f "frontend_source/.gitignore" ]; then
    echo "📄 Removing frontend_source/.gitignore..."
    rm frontend_source/.gitignore
    echo "✅ Removed .gitignore"
fi

# Step 3: Remove from git cache
echo "🗑️  Removing from git cache..."
git rm --cached frontend_source 2>/dev/null || true

# Step 4: Add as regular files
echo "➕ Adding frontend_source as regular files..."
git add frontend_source/

# Step 5: Show status
echo ""
echo "📊 Git status:"
git status --short frontend_source/ | head -10

echo ""
echo "✅ Done! Now commit and push:"
echo "   git commit -m 'Convert frontend_source from nested repo to regular directory'"
echo "   git push"
