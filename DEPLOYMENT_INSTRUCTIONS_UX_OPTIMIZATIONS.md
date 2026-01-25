# Deployment Instructions - UX Optimizations

## ✅ Changes Committed and Pushed

All changes have been committed to `main` branch and pushed to GitHub:
- **Commit:** `40db4bb1`
- **Branch:** `main`
- **Files Changed:** 18 files (1503 insertions, 312 deletions)

## 🚀 Deploy to DigitalOcean

### Option 1: Quick Deploy (Recommended)

SSH into your DigitalOcean server and run:

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

### Option 2: Use Deployment Script

If you have the deployment script on the server:

```bash
ssh mingus-app@test.mingusapp.com
cd /var/www/mingus-app
./deploy_to_digitalocean.sh
```

## 📋 What Was Deployed

### Frontend Changes
- ✅ Anchor navigation in HeroSection (smooth scroll to assessments)
- ✅ Unified assessment section (removed duplicates)
- ✅ Password visibility toggle (removed confirmation field)
- ✅ QuickSetupOverlay component for dashboard onboarding
- ✅ Remember Me checkbox and Forgot Password link in login
- ✅ ForgotPasswordPage with proper routing
- ✅ Cookie-based authentication (httpOnly cookies)
- ✅ Login redirect to dashboard after authentication

### Backend Changes
- ✅ Cookie-based authentication endpoints
- ✅ Remember Me support (30-day vs 24-hour token expiry)
- ✅ Forgot password endpoint
- ✅ Updated CORS configuration for credentials
- ✅ Logout endpoint

## 🔍 Post-Deployment Verification

### 1. Test Landing Page
- [ ] Hero section buttons scroll smoothly to assessment section
- [ ] Only ONE assessment section exists
- [ ] All 4 assessment cards display correctly
- [ ] Assessment modal opens when clicking cards
- [ ] "Skip assessments" link works

### 2. Test Registration Flow
- [ ] Signup form has password show/hide toggle
- [ ] No password confirmation field
- [ ] Registration redirects to dashboard (not quick-setup page)
- [ ] QuickSetupOverlay appears on dashboard for new users

### 3. Test Login Flow
- [ ] Remember Me checkbox works
- [ ] Forgot Password link navigates correctly
- [ ] Login redirects to dashboard after success
- [ ] Cookies are set correctly (check browser DevTools)

### 4. Test Forgot Password
- [ ] Forgot password page loads
- [ ] Form submission works
- [ ] Success message displays

## 🐛 Troubleshooting

### If frontend doesn't update:
```bash
# Clear nginx cache
sudo rm -rf /var/cache/nginx/*
sudo systemctl restart nginx
```

### If backend has issues:
```bash
# Check backend logs
sudo journalctl -u mingus-backend -f

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### If CORS errors occur:
- Verify CORS configuration in `app.py` has `supports_credentials: True`
- Check that frontend requests include `credentials: 'include'`

## 📝 Important Notes

1. **Cookie Security**: Cookies are set with `secure=False` in development. For production, ensure `FLASK_ENV=production` is set so cookies use `secure=True`.

2. **Database Migration**: The User model now includes `password_reset_token` and `password_reset_expires` fields. If you're using migrations, run:
   ```bash
   # On server
   flask db upgrade
   ```

3. **Environment Variables**: Ensure these are set on the server:
   - `FLASK_ENV=production` (for secure cookies)
   - `JWT_SECRET_KEY` (for token generation)
   - `CORS_ORIGINS` (comma-separated list of allowed origins)

## ✅ Deployment Complete

After running the deployment commands, visit:
- **Test Site:** https://test.mingusapp.com
- Verify all features are working as expected
