#!/bin/bash
# Deployment script for new user workflow changes

set -e

echo "🚀 Starting deployment process..."

# Navigate to project root
cd "$(dirname "$0")"

# Check git status
echo "📋 Checking git status..."
git status

# Stage all changes
echo "📦 Staging changes..."
git add app.py
git add frontend/src/App.tsx
git add frontend/src/components/LandingPage.tsx
git add frontend/src/pages/SignUpPage.tsx
git add frontend/src/components/QuickSetup.tsx
git add backend/api/quick_setup_endpoints.py
git add test_new_user_workflow.md
git add TEST_RESULTS_SUMMARY.md

# Commit changes
echo "💾 Committing changes..."
git commit -m "feat: Implement new user workflow optimization

- Add localStorage save after assessment completion
- Navigate to signup with assessment data pre-fill
- Create QuickSetup component for simplified profile setup
- Add backend quick-setup endpoint with JWT authentication
- Update registration flow to redirect to quick-setup
- Add comprehensive test documentation"

# Push to remote
echo "📤 Pushing to remote repository..."
git push origin main

echo "✅ Changes pushed successfully!"
echo ""
echo "📝 Next steps:"
echo "1. SSH into DigitalOcean droplet: ssh mingus-app@test.mingusapp.com"
echo "2. Navigate to app directory: cd /var/www/mingus-app"
echo "3. Pull latest changes: git pull origin main"
echo "4. Install dependencies: cd frontend && npm install"
echo "5. Build frontend: npm run build"
echo "6. Restart services: sudo systemctl restart mingus-backend && sudo systemctl restart nginx"
