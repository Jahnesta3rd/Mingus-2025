#!/bin/bash

# Deployment script for user flow fixes
# Run this on your DigitalOcean server

set -e  # Exit on error

echo "🚀 Deploying user flow fixes to test.mingusapp.com..."
echo ""

# Navigate to app directory
cd /var/www/mingus-app

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
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

echo ""
echo "✅ Deployment complete!"
echo ""
echo "📋 Changes deployed:"
echo "  - Fixed AssessmentResults Sign Up button navigation"
echo "  - Added redirect for authenticated users on SignUpPage"
echo "  - Removed auto-navigation from LandingPage after assessment"
echo ""
echo "🧪 Test the following:"
echo "  1. Complete an assessment → Should see results → Click Sign Up"
echo "  2. Click Get Started (logged in) → Should go to dashboard"
echo "  3. Click Get Started (not logged in) → Should go to signup"
echo ""
