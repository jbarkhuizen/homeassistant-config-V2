#!/bin/bash
cd /config

# Add all changes
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "No changes to commit"
    exit 0
fi

# Create commit with timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
git commit -m "Auto-commit: Configuration update - $TIMESTAMP"

# Push to GitHub
git push origin main

echo "Configuration successfully committed and pushed to GitHub"