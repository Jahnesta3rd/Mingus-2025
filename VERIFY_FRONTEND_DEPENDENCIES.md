# Frontend Dependencies Verification Guide

## Overview

This guide helps you verify that all frontend dependencies are properly installed on your DigitalOcean server.

## Quick Verification

### Option 1: Run the Verification Script (Recommended)

SSH into your DigitalOcean server and run:

```bash
ssh mingus-app@test.mingusapp.com
cd /var/www/mingus-app
./scripts/verify_frontend_dependencies.sh
```

This script will:
- ✅ Check Node.js and npm versions
- ✅ Verify node_modules directory exists
- ✅ Check all production dependencies are installed
- ✅ Verify critical dependencies (React, Vite, etc.)
- ✅ Check if build directory exists
- ✅ Test build capability
- ✅ Report any missing or broken dependencies

### Option 2: Manual Verification

Run these commands on your DigitalOcean server:

```bash
# SSH into server
ssh mingus-app@test.mingusapp.com

# Navigate to frontend directory
cd /var/www/mingus-app/frontend

# Check Node.js and npm
node --version    # Should be v18.x or higher
npm --version     # Should be 8.x or higher

# Check if node_modules exists
ls -la node_modules | head -20

# Check if critical dependencies are installed
ls node_modules/react
ls node_modules/react-dom
ls node_modules/vite
ls node_modules/@vitejs/plugin-react

# Check if build exists
ls -la dist/

# Verify all dependencies from package.json
npm list --depth=0

# Test if dependencies are complete
npm install --dry-run
```

## Expected Dependencies

Based on `frontend/package.json`, the following dependencies should be installed:

### Production Dependencies (Required)
- `@heroicons/react` ^2.2.0
- `@mui/icons-material` ^7.3.7
- `@mui/material` ^7.3.7
- `@types/dompurify` ^3.0.5
- `@types/node` ^24.5.1
- `@types/react-router-dom` ^5.3.3
- `chart.js` ^4.5.1
- `dompurify` ^3.2.6
- `lucide-react` ^0.263.1
- `react` ^18.2.0
- `react-chartjs-2` ^5.3.1
- `react-dom` ^18.2.0
- `react-router-dom` ^7.9.1
- `recharts` ^3.2.1
- `zustand` ^5.0.8

### Development Dependencies (Required for Build)
- `@vitejs/plugin-react` ^4.0.3
- `typescript` ^5.0.2
- `vite` ^4.4.5
- `tailwindcss` ^3.4.0
- `postcss` ^8.4.27
- `autoprefixer` ^10.4.21

## Common Issues and Solutions

### Issue: node_modules directory is missing

**Solution:**
```bash
cd /var/www/mingus-app/frontend
npm install
```

### Issue: Dependencies are outdated

**Solution:**
```bash
cd /var/www/mingus-app/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Issue: Build fails due to missing dependencies

**Solution:**
```bash
cd /var/www/mingus-app/frontend
npm install --production=false  # Install dev dependencies too
npm run build
```

### Issue: Version mismatches

**Solution:**
```bash
cd /var/www/mingus-app/frontend
npm ci  # Uses package-lock.json for exact versions
```

## Verification Checklist

Use this checklist to verify dependencies on DigitalOcean:

- [ ] Node.js v18+ is installed
- [ ] npm is installed and working
- [ ] `frontend/package.json` exists
- [ ] `frontend/package-lock.json` exists
- [ ] `frontend/node_modules/` directory exists
- [ ] All production dependencies are in `node_modules/`
- [ ] Critical dependencies (React, Vite) are installed
- [ ] Build directory (`frontend/dist/`) exists and has files
- [ ] `npm list --depth=0` shows no missing dependencies
- [ ] `npm run build` completes successfully

## Automated Verification

The verification script (`scripts/verify_frontend_dependencies.sh`) performs all these checks automatically and provides a detailed report.

## Deployment Integration

To ensure dependencies are always up to date during deployment, your deployment scripts should:

1. Pull latest code: `git pull origin main`
2. Install dependencies: `cd frontend && npm install`
3. Build frontend: `npm run build`
4. Restart services: `sudo systemctl restart nginx`

Example deployment command:
```bash
cd /var/www/mingus-app && \
git pull origin main && \
cd frontend && \
npm install && \
npm run build && \
cd .. && \
sudo systemctl restart mingus-backend && \
sudo systemctl restart nginx
```

## Monitoring

To regularly check dependency status, you can:

1. **Set up a cron job** to run the verification script weekly:
   ```bash
   # Add to crontab (crontab -e)
   0 2 * * 0 /var/www/mingus-app/scripts/verify_frontend_dependencies.sh >> /var/log/mingus-deps-check.log 2>&1
   ```

2. **Check after each deployment** by running the verification script

3. **Monitor npm audit** for security issues:
   ```bash
   cd /var/www/mingus-app/frontend
   npm audit
   ```

## Troubleshooting

### If verification script fails:

1. Check file permissions:
   ```bash
   chmod +x /var/www/mingus-app/scripts/verify_frontend_dependencies.sh
   ```

2. Ensure you're in the correct directory:
   ```bash
   cd /var/www/mingus-app
   ```

3. Check Node.js version:
   ```bash
   node --version  # Should be v18+
   ```

4. Verify npm is working:
   ```bash
   npm --version
   ```

## Next Steps

After verifying dependencies:

1. ✅ If all checks pass: Your frontend dependencies are properly installed
2. ⚠️ If warnings appear: Review and address non-critical issues
3. ❌ If errors appear: Follow the solutions above to fix missing dependencies

For more information, see:
- `DEPLOYMENT_COMMANDS.md` - Deployment procedures
- `DIGITALOCEAN_PRODUCTION_DEPLOYMENT_CHECKLIST.md` - Full deployment checklist
- `scripts/deploy_frontend.sh` - Frontend deployment script
