# Check Dependencies on DigitalOcean Server

## Quick Start

SSH into your DigitalOcean server and run the comprehensive dependency check:

```bash
# Connect to server
ssh mingus-test

# Navigate to application directory
cd /var/www/mingus-app

# Run the dependency check script
./scripts/check_all_dependencies.sh
```

---

## What the Script Checks

### ✅ System Dependencies
- Node.js (v18+)
- npm
- Python 3
- pip
- Nginx
- PostgreSQL (client)
- Redis (client)
- Git

### ✅ Frontend Dependencies
- `package.json` and `package-lock.json`
- `node_modules/` directory
- Critical packages: React, React-DOM, Vite, React Router
- Build output (`dist/` directory)

### ✅ Backend Dependencies
- `requirements.txt`
- Python virtual environment (`venv/`)
- Critical packages: Flask, Gunicorn, psycopg2, Redis, Stripe
- Application structure

### ✅ Service Status
- mingus-backend service
- nginx service
- PostgreSQL service
- Redis service

### ✅ System Resources
- Disk space usage
- Memory availability

---

## Manual Checks (Alternative)

If you prefer to check manually, here are the key commands:

### System Dependencies
```bash
# Check Node.js
node --version    # Should be v18.x or higher
npm --version

# Check Python
python3 --version
pip3 --version

# Check services
systemctl status nginx
systemctl status mingus-backend
systemctl status postgresql
```

### Frontend Dependencies
```bash
cd /var/www/mingus-app/frontend

# Check if dependencies are installed
ls -la node_modules | head -20

# Check critical packages
ls node_modules/react
ls node_modules/vite

# Check build
ls -la dist/

# Verify all packages
npm list --depth=0
```

### Backend Dependencies
```bash
cd /var/www/mingus-app

# Check virtual environment
ls -la venv/

# Activate and check packages
source venv/bin/activate
pip list | grep -E "(flask|gunicorn|psycopg2|redis|stripe)"

# Check requirements
cat requirements.txt | head -20
```

---

## Fixing Missing Dependencies

### Frontend Dependencies Missing

```bash
cd /var/www/mingus-app/frontend

# Remove and reinstall
rm -rf node_modules package-lock.json
npm install

# Build frontend
npm run build
```

### Backend Dependencies Missing

```bash
cd /var/www/mingus-app

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
pip install -r requirements.txt

# Or if venv doesn't exist, create it
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Services Not Running

```bash
# Start services
sudo systemctl start mingus-backend
sudo systemctl start nginx
sudo systemctl start postgresql  # If using local database
sudo systemctl start redis       # If using local Redis

# Enable services to start on boot
sudo systemctl enable mingus-backend
sudo systemctl enable nginx
```

---

## Expected Output

When the script runs successfully, you should see:

```
✅ Node.js installed: v20.x.x (compatible)
✅ npm installed: 10.x.x
✅ Python installed: Python 3.12.x
✅ pip installed
✅ Nginx installed: 1.24.x (running)
✅ Git installed: 2.x.x
✅ package.json found
✅ node_modules directory exists
✅ Build directory exists
✅ requirements.txt found
✅ Virtual environment (venv) found
✅ mingus-backend service is running
✅ nginx service is running

✅ Passed: 15
❌ Failed: 0
⚠️  Warnings: 2
```

---

## Troubleshooting

### Script Permission Denied

```bash
chmod +x /var/www/mingus-app/scripts/check_all_dependencies.sh
```

### Cannot Find Script

```bash
# Make sure you're in the right directory
cd /var/www/mingus-app
pwd  # Should show /var/www/mingus-app

# Check if script exists
ls -la scripts/check_all_dependencies.sh
```

### Connection Issues

If you can't SSH into the server:

1. **Check SSH key:**
   ```bash
   ls -la ~/.ssh/mingus_test
   chmod 600 ~/.ssh/mingus_test
   ```

2. **Test connection:**
   ```bash
   ssh -v mingus-test
   ```

3. **Verify server is accessible:**
   ```bash
   ping 64.225.16.241
   ```

---

## Quick Reference

**Server:** `64.225.16.241`  
**User:** `mingus-app`  
**SSH:** `ssh mingus-test`  
**App Directory:** `/var/www/mingus-app`  
**Frontend:** `/var/www/mingus-app/frontend`  
**Backend:** `/var/www/mingus-app/backend`

---

**Status:** Ready to check dependencies
