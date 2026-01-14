#!/bin/bash
# Quick deployment script for DigitalOcean
# Run this on your DigitalOcean server

echo "🚀 Deploying Optimized User Flows to DigitalOcean..."
echo ""

# Navigate to app directory
cd /var/www/mingus-app || {
    echo "❌ Error: /var/www/mingus-app not found"
    exit 1
}

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

# Check status
echo ""
echo "✅ Checking service status..."
sudo systemctl status mingus-backend --no-pager -l | head -10
echo ""
sudo systemctl status nginx --no-pager -l | head -10

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Test the flows at: https://test.mingusapp.com"
echo ""
echo "Assessment Flow: Complete an assessment → Check pre-fill"
echo "CTA Flow: Click Get Started → Check no pre-fill"
