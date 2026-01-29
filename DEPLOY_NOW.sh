#!/bin/bash
# Local wrapper script to deploy to Digital Ocean
# This script will SSH into the server and run the deployment

set -e

echo "🚀 Starting Digital Ocean Deployment..."
echo "=================================================="
echo ""

# Server details
SERVER="mingus-app@test.mingusapp.com"
APP_DIR="/var/www/mingus-app"

echo "📋 Connecting to server: $SERVER"
echo ""

# SSH into server and run deployment commands
ssh -t $SERVER << 'ENDSSH'
    set -e
    
    echo "✅ Connected to server"
    echo ""
    
    # Navigate to app directory
    echo "📁 Navigating to app directory..."
    cd /var/www/mingus-app || {
        echo "❌ Error: /var/www/mingus-app not found"
        exit 1
    }
    
    echo "✅ Current directory: $(pwd)"
    echo ""
    
    # Pull latest changes
    echo "📥 Pulling latest changes from GitHub..."
    git pull origin main || {
        echo "❌ Error: Git pull failed"
        exit 1
    }
    
    echo "✅ Git pull completed"
    echo ""
    
    # Show recent commits
    echo "📋 Recent commits:"
    git log --oneline -5
    echo ""
    
    # Build frontend
    echo "🔨 Building frontend..."
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
        exit 1
    }
    
    echo "✅ Frontend build completed"
    cd ..
    echo ""
    
    # Check if backend needs updates
    echo "🔍 Checking backend..."
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
    
    echo "✅ Services restarted"
    echo ""
    
    # Check service status
    echo "📊 Checking service status..."
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
    echo "2. Check logs if issues occur:"
    echo "   sudo journalctl -u mingus-backend -f"
    echo "   sudo tail -f /var/log/nginx/error.log"
    echo ""
ENDSSH

echo ""
echo "✅ Deployment script completed!"
echo ""
