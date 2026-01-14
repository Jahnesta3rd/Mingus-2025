#!/bin/bash
# Deployment script for DigitalOcean - Optimized User Flows
# Run this script on your DigitalOcean server

set -e  # Exit on error

echo "🚀 Deploying Optimized User Flows to DigitalOcean..."
echo "=================================================="
echo ""

# Connect to server (you'll need to run this manually)
echo "📋 Step 1: SSH into server"
echo "Run: ssh mingus-app@test.mingusapp.com"
echo ""

# Navigate to app directory
echo "📁 Step 2: Navigating to app directory..."
cd /var/www/mingus-app || {
    echo "❌ Error: /var/www/mingus-app not found"
    echo "Please update the path in this script to match your deployment directory"
    exit 1
}

echo "✅ Current directory: $(pwd)"
echo ""

# Pull latest changes
echo "📥 Step 3: Pulling latest changes from GitHub..."
git pull origin main || {
    echo "❌ Error: Git pull failed"
    echo "Make sure you're connected to the internet and have access to the repository"
    exit 1
}

echo "✅ Git pull completed"
echo ""

# Show recent commits
echo "📋 Recent commits:"
git log --oneline -3
echo ""

# Build frontend
echo "🔨 Step 4: Building frontend..."
cd frontend || {
    echo "❌ Error: frontend directory not found"
    exit 1
}

echo "📦 Installing npm dependencies..."
npm install || {
    echo "⚠️  Warning: npm install had some issues, but continuing..."
}

echo "🏗️  Building frontend (this may take a few minutes)..."
npm run build || {
    echo "❌ Error: Frontend build failed"
    echo "Check the error messages above"
    exit 1
}

echo "✅ Frontend build completed"
cd ..
echo ""

# Check if backend needs updates
echo "🔍 Step 5: Checking backend..."
if [ -f "requirements.txt" ]; then
    echo "📦 Backend requirements.txt found"
    if [ -d "venv" ]; then
        echo "🐍 Activating virtual environment..."
        source venv/bin/activate
        echo "📦 Installing/updating Python dependencies..."
        pip install -r requirements.txt --quiet || {
            echo "⚠️  Warning: pip install had some issues"
        }
    else
        echo "⚠️  Warning: Virtual environment not found, skipping pip install"
    fi
else
    echo "ℹ️  No requirements.txt found, skipping backend dependency update"
fi
echo ""

# Restart services
echo "🔄 Step 6: Restarting services..."

echo "  → Restarting mingus-backend..."
sudo systemctl restart mingus-backend || {
    echo "⚠️  Warning: mingus-backend restart failed or service not found"
    echo "Trying alternative: gunicorn..."
    sudo systemctl restart gunicorn || {
        echo "⚠️  Warning: gunicorn restart also failed"
    }
}

echo "  → Restarting nginx..."
sudo systemctl restart nginx || {
    echo "❌ Error: nginx restart failed"
    exit 1
}

echo "✅ Services restarted"
echo ""

# Check service status
echo "📊 Step 7: Checking service status..."
echo ""
echo "Backend service status:"
sudo systemctl status mingus-backend --no-pager -l | head -15 || sudo systemctl status gunicorn --no-pager -l | head -15 || echo "⚠️  Could not check backend status"

echo ""
echo "Nginx service status:"
sudo systemctl status nginx --no-pager -l | head -15

echo ""
echo "=================================================="
echo "🎉 Deployment Complete!"
echo "=================================================="
echo ""
echo "📝 Next Steps:"
echo "1. Visit https://test.mingusapp.com to verify the changes"
echo "2. Test the Assessment Flow:"
echo "   - Complete an assessment"
echo "   - Verify pre-fill on signup"
echo "   - Check assessment badge in Quick Setup"
echo ""
echo "3. Test the Get Started Flow:"
echo "   - Click any 'Get Started' button"
echo "   - Verify no pre-fill"
echo "   - Check standard messaging"
echo ""
echo "4. Check logs if issues occur:"
echo "   sudo journalctl -u mingus-backend -f"
echo "   sudo tail -f /var/log/nginx/error.log"
echo ""
