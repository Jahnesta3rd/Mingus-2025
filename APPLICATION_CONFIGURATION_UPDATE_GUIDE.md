# Application Configuration Update Guide

## Recommended Steps for Updating Application Configuration

**Date:** January 8, 2026  
**Server:** mingus-test (64.225.16.241)  
**Status:** 📋 **CONFIGURATION UPDATE RECOMMENDATIONS**

---

## Quick Start - Critical Updates

### ⚠️ IMMEDIATE ACTION REQUIRED:

**1. Update Database URL in `.env` file:**
```bash
# CHANGE THIS LINE in your .env file:
# FROM: DATABASE_URL=sqlite:///app.db
# TO:   DATABASE_URL=postgresql://mingus_user:MingusApp2026!@localhost:5432/mingus_db
```

**2. Update CORS Origins for Production:**
```bash
# ADD production domains to CORS_ORIGINS:
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,https://mingusapp.com,https://www.mingusapp.com
```

**3. Enable Secure Cookies for Production:**
```bash
# CHANGE for production:
SESSION_COOKIE_SECURE=true  # Was: false
```

**4. Update API URLs:**
```bash
# For production, update frontend API calls to use:
API_URL=https://mingusapp.com/api
# Instead of: http://localhost:5000/api
```

---

## Overview

This guide provides step-by-step recommendations for updating your Mingus application configuration to work with the newly configured server infrastructure:

- ✅ PostgreSQL database (mingus_db)
- ✅ Nginx reverse proxy
- ✅ SSL certificates
- ✅ Security headers

---

## Step 1: Database Configuration

### 1.1 Update Database Connection Settings

**For Python/Flask Applications:**

**Option A: Environment Variables (Recommended)**

Based on your existing `env.example` file, update your `.env` file:

**Current Configuration (env.example):**
```bash
DATABASE_URL=sqlite:///app.db
```

**Update to PostgreSQL:**
```bash
# Database Configuration - UPDATE THIS
DATABASE_URL=postgresql://mingus_user:MingusApp2026!@localhost:5432/mingus_db

# OR use individual variables:
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mingus_db
DB_USER=mingus_user
DB_PASSWORD=MingusApp2026!
```

**Option B: Configuration File**

Update `config.py` or `settings.py`:
```python
import os
from urllib.parse import quote_plus

class Config:
    # Database Configuration
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
    DB_NAME = os.getenv('DB_NAME', 'mingus_db')
    DB_USER = os.getenv('DB_USER', 'mingus_user')
    DB_PASSWORD = os.getenv('DB_PASSWORD', 'MingusApp2026!')
    
    # SQLAlchemy Configuration
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql+psycopg2://{DB_USER}:{quote_plus(DB_PASSWORD)}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }
```

**For Node.js/Express Applications:**

Create or update `.env` file:
```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mingus_db
DB_USER=mingus_user
DB_PASSWORD=MingusApp2026!

# Database Connection String
DATABASE_URL=postgresql://mingus_user:MingusApp2026!@localhost:5432/mingus_db
```

Update database connection file:
```javascript
// config/database.js
require('dotenv').config();
const { Pool } = require('pg');

const pool = new Pool({
  host: process.env.DB_HOST || 'localhost',
  port: process.env.DB_PORT || 5432,
  database: process.env.DB_NAME || 'mingus_db',
  user: process.env.DB_USER || 'mingus_user',
  password: process.env.DB_PASSWORD || 'MingusApp2026!',
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});

module.exports = pool;
```

---

### 1.2 Test Database Connection

**Python/Flask:**
```python
# test_db_connection.py
from app import db
from app import create_app

app = create_app()
with app.app_context():
    try:
        db.engine.execute('SELECT 1')
        print("✅ Database connection successful!")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
```

**Node.js:**
```javascript
// test_db_connection.js
const pool = require('./config/database');

pool.query('SELECT NOW()', (err, res) => {
  if (err) {
    console.error('❌ Database connection failed:', err);
  } else {
    console.log('✅ Database connection successful!', res.rows[0]);
  }
  pool.end();
});
```

---

## Step 2: Environment Configuration

### 2.1 Create Environment Files

**Development Environment (`.env` or `.env.development`):**

Update your existing `.env` file based on `env.example`:

```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=development
SECRET_KEY=your-super-secret-key-change-in-production

# Database Configuration - UPDATE THIS LINE
DATABASE_URL=postgresql://mingus_user:MingusApp2026!@localhost:5432/mingus_db
# OLD: DATABASE_URL=sqlite:///app.db

# Database Connection Settings
DB_CONNECTION_TIMEOUT=30
DB_MAX_CONNECTIONS=20

# CORS Configuration - UPDATE FOR PRODUCTION
CORS_ORIGINS=http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,https://mingusapp.com,https://www.mingusapp.com

# Session Security - UPDATE FOR PRODUCTION
SESSION_COOKIE_SECURE=false  # Set to true in production
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Strict
PERMANENT_SESSION_LIFETIME=86400

# Application Ports
APP_HOST=0.0.0.0  # Development
APP_PORT=5000
FRONTEND_PORT=3000

# API URLs
API_URL=http://localhost:5000/api  # Development
FRONTEND_URL=http://localhost:3000  # Development
```

**Production Environment (`.env.production`):**

Create or update `.env.production` file:

```bash
# Flask Configuration
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=your-production-secret-key-change-this

# Database Configuration
DATABASE_URL=postgresql://mingus_user:MingusApp2026!@localhost:5432/mingus_db
DB_CONNECTION_TIMEOUT=30
DB_MAX_CONNECTIONS=20

# CORS Configuration - PRODUCTION
CORS_ORIGINS=https://mingusapp.com,https://www.mingusapp.com

# Session Security - PRODUCTION
SESSION_COOKIE_SECURE=true  # HTTPS only
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=86400

# Application
APP_HOST=127.0.0.1  # Localhost only (Nginx reverse proxy)
APP_PORT=5000
FRONTEND_PORT=3000

# API URLs - PRODUCTION
API_URL=https://mingusapp.com/api
FRONTEND_URL=https://mingusapp.com

# Security
CSRF_SECRET_KEY=your-production-csrf-secret
ENCRYPTION_KEY=your-production-encryption-key
RATE_LIMIT_PER_MINUTE=100

# SSL/TLS
FORCE_HTTPS=true
```

---

### 2.2 Update .gitignore

Ensure sensitive files are not committed:
```gitignore
# Environment files
.env
.env.local
.env.development
.env.production
.env.*.local

# Secrets
secrets/
*.key
*.pem

# Database
*.db
*.sqlite
```

---

## Step 3: Application Server Configuration

### 3.1 Backend Server (Python/Flask)

**Update application to listen on correct host/port:**

```python
# app.py or main.py
import os
from flask import Flask

app = Flask(__name__)

# ... your app configuration ...

if __name__ == '__main__':
    host = os.getenv('APP_HOST', '127.0.0.1')
    port = int(os.getenv('APP_PORT', 5000))
    app.run(host=host, port=port, debug=False)
```

**For production with Gunicorn:**
```bash
# gunicorn_config.py
bind = "127.0.0.1:5000"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
```

---

### 3.2 Frontend Server (React/Node.js)

**Update API endpoint configuration:**

```javascript
// src/config/api.js
const API_URL = process.env.REACT_APP_API_URL || 
  (process.env.NODE_ENV === 'production' 
    ? 'https://api.mingusapp.com' 
    : 'http://localhost:5000');

export default API_URL;
```

**Update Vite/Webpack configuration:**

```javascript
// vite.config.js or webpack.config.js
export default {
  server: {
    host: '127.0.0.1',
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:5000',
        changeOrigin: true,
      }
    }
  }
}
```

---

## Step 4: Nginx Integration

### 4.1 Verify Reverse Proxy Configuration

The Nginx reverse proxy is already configured:
- **Backend API:** `/api/` → `http://127.0.0.1:5000`
- **Frontend:** `/` → `http://127.0.0.1:3000`

**No changes needed** - your application should work with the existing Nginx configuration.

---

### 4.2 Update API Endpoints

**Frontend API calls should use relative paths:**

```javascript
// Instead of: http://localhost:5000/api/users
// Use: /api/users

// Example:
const response = await fetch('/api/users', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  }
});
```

---

## Step 5: Security Configuration

### 5.1 Update CORS Settings

**Backend (Flask):**
```python
from flask_cors import CORS

# For production
CORS(app, 
     resources={r"/api/*": {
         "origins": ["https://mingusapp.com", "https://www.mingusapp.com"],
         "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
         "allow_headers": ["Content-Type", "Authorization"]
     }},
     supports_credentials=True)
```

**Backend (Express):**
```javascript
const cors = require('cors');

app.use(cors({
  origin: process.env.NODE_ENV === 'production' 
    ? ['https://mingusapp.com', 'https://www.mingusapp.com']
    : 'http://localhost:3000',
  credentials: true,
  methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'Authorization']
}));
```

---

### 5.2 Update Session Configuration

**Flask:**
```python
app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
```

**Express:**
```javascript
app.use(session({
  cookie: {
    secure: process.env.NODE_ENV === 'production', // HTTPS only
    httpOnly: true,
    sameSite: 'lax',
    maxAge: 24 * 60 * 60 * 1000 // 24 hours
  }
}));
```

---

## Step 6: Testing Configuration

### 6.1 Local Testing Checklist

- [ ] Database connection works
- [ ] API endpoints accessible
- [ ] Frontend can connect to API
- [ ] Environment variables loaded correctly
- [ ] No hardcoded credentials in code

### 6.2 Server Testing Checklist

- [ ] Application starts on correct ports (5000, 3000)
- [ ] Nginx reverse proxy routes correctly
- [ ] HTTPS works (SSL certificate)
- [ ] Security headers present
- [ ] Database connection from server works
- [ ] API endpoints accessible via domain

---

## Step 7: Deployment Configuration

### 7.1 Create Deployment Script

**deploy.sh:**
```bash
#!/bin/bash
set -e

echo "=== Deploying Mingus Application ==="

# Load environment variables
source .env.production

# Install dependencies
echo "Installing dependencies..."
npm install  # or pip install -r requirements.txt

# Run database migrations
echo "Running database migrations..."
npm run migrate  # or python manage.py migrate

# Build frontend (if needed)
echo "Building frontend..."
npm run build

# Restart services
echo "Restarting services..."
sudo systemctl restart mingus-backend
sudo systemctl restart mingus-frontend
sudo systemctl reload nginx

echo "✅ Deployment complete!"
```

---

### 7.2 Create Systemd Service Files

**Backend Service (`/etc/systemd/system/mingus-backend.service`):**
```ini
[Unit]
Description=Mingus Backend API
After=network.target postgresql.service

[Service]
Type=simple
User=mingus-app
WorkingDirectory=/var/www/mingus-app/backend
Environment="PATH=/var/www/mingus-app/backend/venv/bin"
ExecStart=/var/www/mingus-app/backend/venv/bin/gunicorn -c gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Frontend Service (`/etc/systemd/system/mingus-frontend.service`):**
```ini
[Unit]
Description=Mingus Frontend
After=network.target

[Service]
Type=simple
User=mingus-app
WorkingDirectory=/var/www/mingus-app/frontend
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## Step 8: Database Migrations

### 8.1 Run Initial Migrations

**Flask-Migrate:**
```bash
# Initialize migrations (if not done)
flask db init

# Create migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

**Node.js (Sequelize/Knex):**
```bash
# Run migrations
npm run migrate
# or
npx sequelize-cli db:migrate
```

---

### 8.2 Verify Database Schema

```sql
-- Connect to database
PGPASSWORD='MingusApp2026!' psql -h localhost -U mingus_user -d mingus_db

-- List tables
\dt

-- Describe table
\d table_name
```

---

## Step 9: Monitoring and Logging

### 9.1 Configure Logging

**Flask:**
```python
import logging
from logging.handlers import RotatingFileHandler

if not app.debug:
    file_handler = RotatingFileHandler(
        '/var/log/mingus-app/backend.log',
        maxBytes=10240000,
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s'
    ))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
```

**Node.js:**
```javascript
const winston = require('winston');

const logger = winston.createLogger({
  level: 'info',
  format: winston.format.json(),
  transports: [
    new winston.transports.File({ 
      filename: '/var/log/mingus-app/backend-error.log', 
      level: 'error' 
    }),
    new winston.transports.File({ 
      filename: '/var/log/mingus-app/backend.log' 
    })
  ]
});
```

---

## Step 10: Security Hardening

### 10.1 Secure Environment Variables

**Use secrets management:**
- Store secrets in environment variables
- Never commit secrets to git
- Use different secrets for dev/prod
- Rotate secrets regularly

### 10.2 Update Application Security

- Enable HTTPS only in production
- Use secure session cookies
- Implement CSRF protection
- Validate all inputs
- Use parameterized queries (prevent SQL injection)

---

## Configuration Checklist

### Pre-Deployment:
- [ ] Database connection configured
- [ ] Environment variables set
- [ ] API endpoints updated
- [ ] CORS configured correctly
- [ ] Session security enabled
- [ ] Secrets secured (not in code)
- [ ] Logging configured
- [ ] Error handling implemented

### Deployment:
- [ ] Application builds successfully
- [ ] Database migrations run
- [ ] Services configured (systemd)
- [ ] Nginx configuration verified
- [ ] SSL certificates valid
- [ ] Security headers present

### Post-Deployment:
- [ ] Database connection works
- [ ] API endpoints accessible
- [ ] Frontend loads correctly
- [ ] HTTPS redirects work
- [ ] Monitoring configured
- [ ] Logs accessible

---

## Quick Reference

### Database Connection:
```
Host: localhost
Port: 5432
Database: mingus_db
User: mingus_user
Password: MingusApp2026!
```

### Application Ports:
```
Backend: 127.0.0.1:5000
Frontend: 127.0.0.1:3000
```

### URLs:
```
Production: https://mingusapp.com
API: https://mingusapp.com/api/
```

---

## Troubleshooting

### Database Connection Issues:
1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Test connection: `PGPASSWORD='MingusApp2026!' psql -h localhost -U mingus_user -d mingus_db`
3. Check firewall: `sudo ufw status`
4. Verify credentials in application config

### API Connection Issues:
1. Verify backend is running: `sudo systemctl status mingus-backend`
2. Check Nginx configuration: `sudo nginx -t`
3. Test API endpoint: `curl http://localhost:5000/api/health`
4. Check Nginx logs: `sudo tail -f /var/log/nginx/mingusapp.com.error.log`

### Frontend Issues:
1. Verify frontend is running: `sudo systemctl status mingus-frontend`
2. Check API URL in frontend config
3. Verify CORS settings
4. Check browser console for errors

---

**Guide Date:** January 8, 2026  
**Status:** 📋 **READY FOR IMPLEMENTATION**  
**Next Step:** Follow steps in order, testing after each major change

