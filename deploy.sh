#!/bin/bash
# Deployment script for DigitalOcean
# Run this on your server: ssh mingus-app@test.mingusapp.com

set -e  # Exit on error

echo "🚀 Starting deployment..."

# Navigate to app directory
cd /var/www/mingus-app

# Pull latest changes
echo "📥 Pulling latest changes..."
git pull origin main

# Build frontend
echo "🔨 Building frontend..."
cd frontend
npm install
npm run build
cd ..

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart mingus-backend
sudo systemctl restart nginx

echo "✅ Deployment complete!"
echo ""
echo "Test at: https://test.mingusapp.com"
