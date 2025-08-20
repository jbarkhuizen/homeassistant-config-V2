#!/bin/bash
cd /config

# Check if git is configured
if ! git config user.name > /dev/null; then
    git config user.name "jbarkhuizen@gmail.com"
    git config user.email "jbarkhuizen@gmail.com"
fi

# Add all changes
git add .

# Check if there are changes to commit
if git diff --staged --quiet; then
    echo "No changes to commit"
    exit 0
fi

# Create more descriptive commit message
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
CHANGED_FILES=$(git diff --staged --name-only | wc -l)
git commit -m "Auto-commit: $CHANGED_FILES file(s) updated - $TIMESTAMP"

# Push with error handling
if git push origin main; then
    echo "Configuration successfully committed and pushed to GitHub"
else
    echo "Failed to push to GitHub - check network/credentials"
    exit 1
fi