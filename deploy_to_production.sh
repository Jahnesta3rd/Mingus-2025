#!/bin/bash
# Deployment script for DigitalOcean production server
# Run this script on your DigitalOcean droplet

set -e  # Exit on error

echo "🚀 Starting deployment to DigitalOcean..."
echo ""

# Navigate to app directory
echo "📁 Navigating to app directory..."
cd /var/www/mingus-app || {
    echo "❌ Error: /var/www/mingus-app not found"
    echo "Please update the path in this script to match your deployment directory"
    exit 1
}

# Pull latest changes
echo "📥 Pulling latest changes from GitHub..."
git pull origin main || {
    echo "❌ Error: Git pull failed"
    echo "Make sure you're connected to the internet and have access to the repository"
    exit 1
}

# Show what changed
echo ""
echo "📋 Recent commits:"
git log --oneline -5

# Build frontend
echo ""
echo "🔨 Building frontend..."
cd frontend || {
    echo "❌ Error: frontend directory not found"
    exit 1
}

echo "📦 Installing npm dependencies..."
npm install || {
    echo "⚠️  Warning: npm install had some issues, but continuing..."
}

echo "🏗️  Building frontend..."
npm run build || {
    echo "❌ Error: Frontend build failed"
    echo "Check the error messages above"
    exit 1
}

cd ..

# Check if backend needs updates
echo ""
echo "🔍 Checking backend dependencies..."
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

# Restart services
echo ""
echo "🔄 Restarting services..."

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

# Check service status
echo ""
echo "✅ Checking service status..."
echo ""
echo "Backend service:"
sudo systemctl status mingus-backend --no-pager -l || sudo systemctl status gunicorn --no-pager -l || echo "⚠️  Could not check backend status"

echo ""
echo "Nginx service:"
sudo systemctl status nginx --no-pager -l | head -10

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "📝 Next steps:"
echo "1. Visit https://test.mingusapp.com to verify the changes"
echo "2. Test the new user workflow:"
echo "   - Complete an assessment"
echo "   - Verify signup pre-fill"
echo "   - Test quick-setup page"
echo "3. Check logs if issues occur:"
echo "   sudo journalctl -u mingus-backend -f"
echo "   sudo tail -f /var/log/nginx/error.log"
