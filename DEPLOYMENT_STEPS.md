# Deployment Steps for Recent Changes

## Changes Made

1. **Backend (`app.py`)**: Commented out `quick_setup_api` import and registration
2. **Frontend (`frontend/src/utils/sanitize.ts`)**: Removed trim() call to preserve spaces during input

## Step-by-Step Deployment Guide

### Step 1: Copy Changes to Correct Repository Files

The changes are already on the server, but we need to save them to the repository:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# The app.py in root is already modified and tracked - verify it has our changes
grep -n "quick_setup_api" app.py | head -2

# Copy sanitize.ts changes to the correct location
cp sanitize.ts frontend/src/utils/sanitize.ts

# Verify the sanitize.ts changes
grep -A 2 "Don't trim here" frontend/src/utils/sanitize.ts
```

### Step 2: Clean Up Temporary Files

```bash
# Remove temporary files we created during editing
rm -f sanitize.ts
# Note: Keep app.py as it's the actual tracked file
```

### Step 3: Review Changes Before Committing

```bash
# Check what files have changed
git status

# Review the changes in app.py
git diff app.py | head -30

# Review the changes in sanitize.ts
git diff frontend/src/utils/sanitize.ts
```

### Step 4: Stage and Commit Changes

```bash
# Stage the modified files
git add app.py frontend/src/utils/sanitize.ts

# Commit with a descriptive message
git commit -m "feat: Disable quick_setup_api and preserve input spaces in sanitizer

- Comment out quick_setup_api import and blueprint registration
- Remove trim() from sanitizeString to preserve spaces during input
- Trimming will now happen on final submission only"
```

### Step 5: Push to Repository

```bash
# Push to remote repository
git push origin main
```

If you encounter authentication issues, you may need to use a Personal Access Token (see `HTTPS_PUSH_INSTRUCTIONS.md`).

### Step 6: Deploy to Server

The changes are already on the server at `/var/www/mingus/`, but to ensure everything is in sync:

```bash
# SSH into the server
ssh mingus-test

# Navigate to application directory
cd /var/www/mingus

# Pull latest changes from repository
git pull origin main

# If frontend needs rebuilding (if sanitize.ts changes require it)
cd frontend
npm run build
cd ..

# Restart the application (if using systemd)
# Check what service manages the app
sudo systemctl status mingus-backend 2>/dev/null || echo "No systemd service found"

# Or restart manually if using a process manager
# pkill -f "python.*app.py"  # Only if needed
```

### Step 7: Verify Deployment

```bash
# On the server, verify the changes are in place
grep -n "quick_setup_api" /var/www/mingus/app.py | head -2
grep -A 2 "Don't trim here" /var/www/mingus/frontend/src/utils/sanitize.ts

# Check if the application is running
curl http://localhost:5000/health 2>/dev/null || echo "App may not be running on port 5000"
```

## Quick Command Summary

```bash
# All-in-one local commands
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
cp sanitize.ts frontend/src/utils/sanitize.ts
rm sanitize.ts
git add app.py frontend/src/utils/sanitize.ts
git commit -m "feat: Disable quick_setup_api and preserve input spaces in sanitizer"
git push origin main

# Server deployment
ssh mingus-test "cd /var/www/mingus && git pull origin main && cd frontend && npm run build && cd .."
```

## Troubleshooting

### If git push fails:
- Check your SSH key is set up: `ssh -T git@github.com`
- Or use HTTPS with Personal Access Token (see `HTTPS_PUSH_INSTRUCTIONS.md`)

### If server git pull fails:
- Check you have write permissions: `ls -la /var/www/mingus/.git`
- May need to use `sudo git pull` or fix permissions

### If frontend build fails:
- Check Node.js version: `node --version`
- Clear cache: `rm -rf frontend/node_modules frontend/.vite && npm install`

## Notes

- The changes are **already deployed** on the server (we edited them directly)
- This process ensures the repository matches the server state
- Future deployments can use `git pull` instead of direct file editing
