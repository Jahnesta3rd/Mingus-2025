# Quick Deploy Commands - Copy & Paste

## Commands to Run on DigitalOcean Server

Copy and paste these commands into your terminal after SSH'ing into your server:

```bash
ssh mingus-app@test.mingusapp.com

cd /var/www/mingus-app
git pull origin main
cd frontend && npm install && npm run build && cd ..
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

---

## What Each Command Does

1. **`ssh mingus-app@test.mingusapp.com`**
   - Connects to your DigitalOcean droplet

2. **`cd /var/www/mingus-app`**
   - Navigates to your application directory

3. **`git pull origin main`**
   - Downloads the latest code changes from GitHub
   - Includes the optimized user flows we just pushed

4. **`cd frontend && npm install && npm run build && cd ..`**
   - Goes to frontend directory
   - Installs/updates npm packages
   - Builds the React app for production
   - Returns to root directory

5. **`sudo systemctl restart mingus-backend`**
   - Restarts the Flask/Python backend service
   - Loads the new code changes

6. **`sudo systemctl restart nginx`**
   - Restarts the web server
   - Serves the newly built frontend files

---

## Expected Output

### Git Pull:
```
Updating abc1234..caae1a8b
Fast-forward
 frontend/src/components/LandingPage.tsx      |  5 +-
 frontend/src/pages/SignUpPage.tsx           | 25 +-
 frontend/src/components/QuickSetup.tsx       | 45 +-
 ...
 11 files changed, 653 insertions(+), 24 deletions(-)
```

### Frontend Build:
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

### Service Restart:
```
✅ Both services should restart successfully
```

---

## Troubleshooting

### If git pull fails:
```bash
# Check git status
git status

# Check remote
git remote -v

# Try pulling again
git pull origin main --no-edit
```

### If npm build fails:
```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### If service won't restart:
```bash
# Check service status
sudo systemctl status mingus-backend

# Check logs
sudo journalctl -u mingus-backend -n 50

# Try alternative service name
sudo systemctl restart gunicorn
```

### If nginx fails:
```bash
# Check nginx config
sudo nginx -t

# Check error log
sudo tail -20 /var/log/nginx/error.log

# Restart again
sudo systemctl restart nginx
```

---

## Verification

After deployment, test both flows:

### Assessment Flow:
1. Visit https://test.mingusapp.com
2. Complete an assessment
3. Check URL: Should have `?from=assessment&type=ai-risk`
4. Check signup: Email/name pre-filled
5. Check Quick Setup: Assessment badge visible

### Get Started Flow:
1. Click "Get Started" button
2. Check URL: Should have `?source=cta`
3. Check signup: No pre-fill
4. Check Quick Setup: No assessment badge

---

**Ready to deploy!** Copy the commands above and run them on your server.
