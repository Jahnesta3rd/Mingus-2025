# Deployment Guide: Registration & Sign Up Changes

This guide will help you deploy the registration and sign-up functionality changes to the live site at https://test.mingusapp.com/

## Changes Summary

1. ✅ Created SignUp page component
2. ✅ Added registration function to auth hook
3. ✅ Created backend auth endpoints (`/api/auth/register`, `/api/auth/login`, `/api/auth/verify`)
4. ✅ Updated User model with `password_hash` field
5. ✅ Fixed all "Get Started" buttons to navigate to `/signup`
6. ✅ Added sign up button after assessment completion
7. ✅ Created database migration for `password_hash` field

## Pre-Deployment Checklist

- [ ] Backup current database
- [ ] Backup current codebase
- [ ] Test changes locally
- [ ] Verify SSH access to server

## Deployment Steps

### Step 1: Connect to Server

```bash
ssh mingus-test
# OR
ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com
```

### Step 2: Navigate to Application Directory

```bash
cd /var/www/mingus-app
# OR wherever your application is deployed
```

### Step 3: Pull Latest Changes (if using Git)

```bash
git pull origin main
# OR
git pull origin master
```

### Step 4: Run Database Migration

**IMPORTANT:** Run this migration to add the `password_hash` column to the users table.

```bash
# From the project root
python3 migrations/add_password_hash_to_users.py
```

This will:
- Check if `password_hash` column exists
- Add it if it doesn't exist
- Skip if already present (safe to run multiple times)

### Step 5: Deploy Backend

```bash
# Run backend deployment script
./scripts/deploy_backend.sh

# OR manually:
source venv/bin/activate
pip install -r requirements.txt
```

### Step 6: Deploy Frontend

```bash
# Run frontend deployment script
./scripts/deploy_frontend.sh

# OR manually:
cd frontend
npm install
npm run build
```

### Step 7: Restart Services

```bash
# Restart backend service
sudo systemctl restart mingus-backend
# OR
sudo systemctl restart gunicorn

# Restart frontend service (if applicable)
sudo systemctl restart mingus-frontend
# OR restart nginx if serving static files
sudo systemctl restart nginx
```

### Step 8: Verify Deployment

1. **Check Backend API:**
   ```bash
   curl https://test.mingusapp.com/api/auth/verify
   ```

2. **Check Frontend:**
   - Visit https://test.mingusapp.com/
   - Click "Get Started" button
   - Should navigate to `/signup` page

3. **Test Registration:**
   - Fill out signup form
   - Submit registration
   - Should create user and redirect to dashboard

## Quick Deployment Script

If you prefer a single command, you can use the main deployment script:

```bash
cd /var/www/mingus-app
./scripts/deploy.sh
```

This will:
- Create backups
- Deploy backend
- Deploy frontend
- Run migrations
- Restart services
- Perform health checks

## Database Migration Details

The migration script (`migrations/add_password_hash_to_users.py`) will:
- Add `password_hash TEXT` column to `users` table
- Check if column already exists (safe to run multiple times)
- Work with SQLite databases

**If using PostgreSQL or MySQL**, you may need to adjust the migration script or run:

```sql
ALTER TABLE users ADD COLUMN password_hash TEXT;
```

## Rollback Instructions

If something goes wrong:

1. **Restore from backup:**
   ```bash
   ./scripts/rollback.sh
   ```

2. **Or manually restore:**
   ```bash
   # Restore database
   cp backups/backup_YYYYMMDD_HHMMSS/assessments.db ./
   
   # Restore code
   tar -xzf backups/backup_YYYYMMDD_HHMMSS/backend.tar.gz
   tar -xzf backups/backup_YYYYMMDD_HHMMSS/frontend.tar.gz
   ```

## Troubleshooting

### Issue: Migration fails
- **Solution:** Check database permissions and ensure SQLite file is writable

### Issue: Backend won't start
- **Solution:** Check logs: `sudo journalctl -u mingus-backend -f`
- **Solution:** Verify Python dependencies: `pip install -r requirements.txt`

### Issue: Frontend build fails
- **Solution:** Check Node.js version: `node --version` (should be 16+)
- **Solution:** Clear node_modules: `rm -rf node_modules && npm install`

### Issue: "Get Started" still goes to login
- **Solution:** Clear browser cache
- **Solution:** Verify frontend build completed successfully
- **Solution:** Check that new files are in the build directory

## Files Changed

### Frontend Files:
- `frontend/src/pages/SignUpPage.tsx` (NEW)
- `frontend/src/hooks/useAuth.tsx` (UPDATED)
- `frontend/src/App.tsx` (UPDATED)
- `frontend/src/components/NavigationBar.tsx` (UPDATED)
- `frontend/src/components/AssessmentResults.tsx` (UPDATED)
- `frontend/src/components/LandingPage.tsx` (UPDATED)
- `frontend/src/components/sections/CTASection.tsx` (UPDATED)
- `frontend/src/components/sections/PricingSection.tsx` (UPDATED)
- `frontend/src/components/sections/HeroSection.tsx` (UPDATED)

### Backend Files:
- `backend/api/auth_endpoints.py` (NEW)
- `backend/models/user_models.py` (UPDATED)
- `app.py` (UPDATED - registered auth blueprint)

### Migration Files:
- `migrations/add_password_hash_to_users.py` (NEW)

## Post-Deployment Testing

After deployment, test:

1. ✅ Landing page loads
2. ✅ "Get Started" button navigates to `/signup`
3. ✅ Sign up form displays correctly
4. ✅ Registration creates user account
5. ✅ Login works with new accounts
6. ✅ Assessment completion shows sign up button
7. ✅ All "Get Started" buttons work throughout the site

## Support

If you encounter issues:
1. Check server logs
2. Check browser console for errors
3. Verify all files were deployed
4. Ensure database migration completed

---

**Deployment Date:** $(date)
**Deployed By:** Automated deployment script
**Status:** Ready for deployment
