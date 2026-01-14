#!/bin/bash

# Interactive deployment script
# Run this AFTER you SSH into the server

echo "🚀 Starting deployment..."
echo ""

# Navigate to app directory
cd /var/www/mingus-app || { echo "❌ Failed to cd to /var/www/mingus-app"; exit 1; }

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main || { echo "❌ Git pull failed"; exit 1; }

# Build frontend
echo "🔨 Building frontend..."
cd frontend || { echo "❌ Failed to cd to frontend"; exit 1; }
npm install || { echo "❌ npm install failed"; exit 1; }
npm run build || { echo "❌ npm build failed"; exit 1; }
cd .. || { echo "❌ Failed to cd back"; exit 1; }

# Restart services (these require sudo, so you'll be prompted for password)
echo "🔄 Restarting services (you may be prompted for password)..."
sudo systemctl restart mingus-backend || { echo "❌ Failed to restart backend"; exit 1; }
sudo systemctl restart nginx || { echo "❌ Failed to restart nginx"; exit 1; }

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Changes deployed:"
echo "  - CSRF token fix for assessment submissions"
echo "  - Next Steps buttons navigation fix"
echo "  - Assessment flow improvements"
echo ""
