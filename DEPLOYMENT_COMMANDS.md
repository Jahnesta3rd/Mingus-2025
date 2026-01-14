# Deployment Commands for DigitalOcean

## Quick Deploy (Copy & Paste)

Run these commands on your DigitalOcean server:

```bash
# Connect to your droplet
ssh mingus-app@test.mingusapp.com

# Navigate to app directory
cd /var/www/mingus-app

# Pull latest changes
git pull origin main

# Build frontend
cd frontend
npm install
npm run build
cd ..

# Restart services
sudo systemctl restart mingus-backend
sudo systemctl restart nginx

# Verify services are running
sudo systemctl status mingus-backend
sudo systemctl status nginx
```

---

## Alternative: Use Deployment Script

1. **Upload the script to your server:**
   ```bash
   scp deploy_to_production.sh mingus-app@test.mingusapp.com:/var/www/mingus-app/
   ```

2. **SSH into server and run:**
   ```bash
   ssh mingus-app@test.mingusapp.com
   cd /var/www/mingus-app
   chmod +x deploy_to_production.sh
   ./deploy_to_production.sh
   ```

---

## Step-by-Step with Explanations

### 1. Connect to Server
```bash
ssh mingus-app@test.mingusapp.com
```
**What this does:** Establishes SSH connection to your DigitalOcean droplet

### 2. Navigate to Application
```bash
cd /var/www/mingus-app
```
**What this does:** Changes to your application directory (adjust path if different)

### 3. Pull Latest Code
```bash
git pull origin main
```
**What this does:** Downloads the latest code changes from GitHub

**Expected output:**
```
Updating abc1234..def5678
Fast-forward
 app.py                                    |   2 +
 frontend/src/App.tsx                      |   3 +
 frontend/src/components/LandingPage.tsx   |  15 +-
 frontend/src/pages/SignUpPage.tsx        |  45 +-
 frontend/src/components/QuickSetup.tsx   | 259 ++++++++++++++++++++++
 backend/api/quick_setup_endpoints.py     | 140 +++++++++++++
 6 files changed, 463 insertions(+), 10 deletions(-)
```

### 4. Build Frontend
```bash
cd frontend
npm install
npm run build
cd ..
```
**What this does:**
- `npm install`: Installs/updates Node.js dependencies
- `npm run build`: Compiles React/TypeScript code into production-ready files
- `cd ..`: Returns to root directory

**Expected output:**
```
> mingus-landing-page@1.0.0 build
> tsc && vite build

vite v5.x.x building for production...
✓ 1234 modules transformed.
dist/index.html                   0.45 kB
dist/assets/index-abc123.js       245.67 kB
...
✓ built in 12.34s
```

### 5. Restart Backend Service
```bash
sudo systemctl restart mingus-backend
```
**What this does:** Restarts the Flask/Python backend to load new code

**Alternative if service name is different:**
```bash
sudo systemctl restart gunicorn
# OR
sudo systemctl restart flask-app
```

### 6. Restart Nginx
```bash
sudo systemctl restart nginx
```
**What this does:** Restarts web server to serve updated frontend files

---

## Verification Steps

### Check Service Status
```bash
# Backend
sudo systemctl status mingus-backend

# Nginx
sudo systemctl status nginx
```

**Expected output:** Both should show `active (running)`

### Test API Endpoint
```bash
curl http://localhost:5000/api/auth/verify
```

### Check Frontend Files
```bash
ls -lh frontend/dist/
```
Should show recently built files with current timestamp

### View Logs
```bash
# Backend logs
sudo journalctl -u mingus-backend -f

# Nginx error logs
sudo tail -f /var/log/nginx/error.log

# Nginx access logs
sudo tail -f /var/log/nginx/access.log
```

---

## Troubleshooting

### Issue: Git pull fails
```bash
# Check git remote
git remote -v

# Check branch
git branch

# Try pulling specific branch
git pull origin main --no-edit
```

### Issue: npm install fails
```bash
# Clear npm cache
npm cache clean --force

# Remove node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

### Issue: Build fails
```bash
# Check Node version
node --version  # Should be 16+ or 18+

# Check for TypeScript errors
cd frontend
npx tsc --noEmit
```

### Issue: Service won't restart
```bash
# Check service status
sudo systemctl status mingus-backend

# Check service logs
sudo journalctl -u mingus-backend -n 50

# Check if port is in use
sudo netstat -tulpn | grep 5000

# Try starting manually
cd /var/www/mingus-app
source venv/bin/activate
python app.py  # Check for errors
```

### Issue: 502 Bad Gateway
```bash
# Check if backend is running
sudo systemctl status mingus-backend

# Check nginx config
sudo nginx -t

# Check nginx error log
sudo tail -20 /var/log/nginx/error.log

# Restart both
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

---

## Post-Deployment Testing

1. **Visit the site:**
   ```
   https://test.mingusapp.com
   ```

2. **Test Assessment Flow:**
   - Click any assessment button
   - Complete the assessment
   - Verify it navigates to `/signup?from=assessment`

3. **Test Signup Pre-fill:**
   - Check if email and first name are pre-filled
   - Verify welcome message appears

4. **Test Registration:**
   - Complete registration form
   - Verify redirect to `/quick-setup`

5. **Test Quick Setup:**
   - Fill out the 3 questions
   - Submit and verify redirect to dashboard

6. **Check Browser Console:**
   - Open DevTools (F12)
   - Check for any JavaScript errors
   - Verify API calls are successful

---

## Rollback (if needed)

If something goes wrong, you can rollback:

```bash
# Find the previous commit
git log --oneline -10

# Reset to previous commit (replace COMMIT_HASH)
git reset --hard COMMIT_HASH

# Rebuild and restart
cd frontend && npm run build && cd ..
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

---

**Ready to deploy!** Copy and paste the commands from the "Quick Deploy" section above.
