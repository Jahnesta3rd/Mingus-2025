# Deploy New User Workflow Changes to DigitalOcean

## Step 1: Commit and Push Changes Locally

Run these commands in your terminal from the project root:

```bash
# Navigate to project root
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# Stage all changed files
git add app.py
git add frontend/src/App.tsx
git add frontend/src/components/LandingPage.tsx
git add frontend/src/pages/SignUpPage.tsx
git add frontend/src/components/QuickSetup.tsx
git add backend/api/quick_setup_endpoints.py
git add test_new_user_workflow.md
git add TEST_RESULTS_SUMMARY.md

# Commit changes
git commit -m "feat: Implement new user workflow optimization

- Add localStorage save after assessment completion
- Navigate to signup with assessment data pre-fill
- Create QuickSetup component for simplified profile setup
- Add backend quick-setup endpoint with JWT authentication
- Update registration flow to redirect to quick-setup
- Add comprehensive test documentation"

# Push to GitHub
git push origin main
```

---

## Step 2: Deploy to DigitalOcean Droplet

SSH into your DigitalOcean droplet and deploy:

```bash
# Connect to droplet
ssh mingus-app@test.mingusapp.com
# OR if you have SSH config:
ssh mingus-test

# Navigate to application directory
cd /var/www/mingus-app
# OR wherever your app is deployed

# Pull latest changes
git pull origin main

# Install/update frontend dependencies
cd frontend
npm install

# Build frontend
npm run build

# Go back to root
cd ..

# Install/update backend dependencies (if needed)
source venv/bin/activate  # If using virtual environment
pip install -r requirements.txt

# Restart backend service
sudo systemctl restart mingus-backend
# OR if using gunicorn directly:
sudo systemctl restart gunicorn

# Restart nginx (to serve updated frontend)
sudo systemctl restart nginx

# Check service status
sudo systemctl status mingus-backend
sudo systemctl status nginx
```

---

## Step 3: Verify Deployment

### Check Backend API
```bash
# Test the new endpoint (from server)
curl -X POST http://localhost:5000/api/profile/quick-setup \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"incomeRange":"50-75k","location":"Atlanta, GA","primaryGoal":"emergency-fund"}'
```

### Check Frontend
1. Visit https://test.mingusapp.com
2. Complete an assessment
3. Verify it navigates to signup with pre-filled data
4. Register a new account
5. Verify redirect to quick-setup page
6. Complete quick setup
7. Verify redirect to dashboard

---

## Step 4: Check Logs (if issues occur)

```bash
# Backend logs
sudo journalctl -u mingus-backend -f
# OR
sudo journalctl -u gunicorn -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# Application logs (if using file logging)
tail -f /var/www/mingus-app/logs/app.log
```

---

## Troubleshooting

### Issue: Frontend build fails
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Backend won't start
```bash
# Check Python dependencies
source venv/bin/activate
pip install -r requirements.txt

# Check if port is in use
sudo netstat -tulpn | grep 5000

# Check service configuration
sudo systemctl status mingus-backend
sudo journalctl -u mingus-backend -n 50
```

### Issue: 502 Bad Gateway
```bash
# Check if backend is running
sudo systemctl status mingus-backend

# Check nginx configuration
sudo nginx -t

# Restart both services
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

### Issue: Database errors
```bash
# Check database file permissions
ls -la user_profiles.db

# Fix permissions if needed
chmod 644 user_profiles.db
chown mingus-app:mingus-app user_profiles.db
```

---

## Quick Deployment Script (Alternative)

If you prefer a single script, create this on your server:

```bash
#!/bin/bash
# Quick deploy script - save as deploy.sh on server

cd /var/www/mingus-app
git pull origin main

# Frontend
cd frontend
npm install
npm run build
cd ..

# Backend
source venv/bin/activate
pip install -r requirements.txt

# Restart services
sudo systemctl restart mingus-backend
sudo systemctl restart nginx

echo "✅ Deployment complete!"
```

Make it executable and run:
```bash
chmod +x deploy.sh
./deploy.sh
```

---

## Files Changed

- ✅ `app.py` - Registered quick_setup_api blueprint
- ✅ `frontend/src/App.tsx` - Added QuickSetup route
- ✅ `frontend/src/components/LandingPage.tsx` - Assessment data save & navigation
- ✅ `frontend/src/pages/SignUpPage.tsx` - Pre-fill from assessment
- ✅ `frontend/src/components/QuickSetup.tsx` - New component
- ✅ `backend/api/quick_setup_endpoints.py` - New API endpoint

---

## Post-Deployment Checklist

- [ ] Git pull completed successfully
- [ ] Frontend build completed without errors
- [ ] Backend dependencies installed
- [ ] Services restarted successfully
- [ ] Assessment → Signup flow works
- [ ] Signup pre-fill works
- [ ] Quick-setup page loads
- [ ] Quick-setup submission works
- [ ] Database saves correctly
- [ ] No console errors in browser
- [ ] No server errors in logs

---

**Deployment Date:** [Current Date]  
**Deployed By:** [Your Name]  
**Status:** Ready for deployment
