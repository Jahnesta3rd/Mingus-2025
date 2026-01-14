# Deployment Instructions for User Flow Fixes

## Quick Deploy (Recommended)

Run these commands **on your local machine** (in your terminal):

```bash
# 1. Navigate to your project directory
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# 2. Copy the deployment script to your server
scp deploy_fixes.sh mingus-app@test.mingusapp.com:/tmp/

# 3. SSH into your server and run the script
ssh mingus-app@test.mingusapp.com "chmod +x /tmp/deploy_fixes.sh && /tmp/deploy_fixes.sh"
```

This will:
- Copy the script to your server
- Make it executable
- Run the deployment automatically

---

## Manual Deploy (Alternative)

If you prefer to run commands step-by-step:

```bash
# 1. SSH into your server
ssh mingus-app@test.mingusapp.com

# 2. Navigate to app directory
cd /var/www/mingus-app

# 3. Pull latest changes
git pull origin main

# 4. Build frontend
cd frontend
npm install
npm run build
cd ..

# 5. Restart services
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

---

## What Gets Deployed

✅ **Assessment Flow Fix:**
- Users see results after completing assessment
- "Sign Up to Access Full Features" button properly navigates to signup with assessment type

✅ **Get Started Button Fix:**
- Authenticated users → Dashboard (correct behavior)
- Non-authenticated users → Signup flow

---

## Verification After Deployment

1. **Test Assessment Flow:**
   - Complete an assessment
   - Verify results screen appears
   - Click "Sign Up to Access Full Features"
   - Should navigate to signup with pre-filled email/name

2. **Test Get Started (Logged In):**
   - Click "Get Started"
   - Should redirect to `/career-dashboard`

3. **Test Get Started (Not Logged In):**
   - Logout or clear session
   - Click "Get Started"
   - Should navigate to `/signup?source=cta`

---

## Troubleshooting

If you encounter issues:

1. **Check Git Status:**
   ```bash
   ssh mingus-app@test.mingusapp.com
   cd /var/www/mingus-app
   git status
   git log --oneline -5
   ```

2. **Check Service Status:**
   ```bash
   sudo systemctl status mingus-backend
   sudo systemctl status nginx
   ```

3. **View Logs:**
   ```bash
   sudo journalctl -u mingus-backend -n 50
   sudo tail -f /var/log/nginx/error.log
   ```

---

**Status:** Ready to deploy ✅
