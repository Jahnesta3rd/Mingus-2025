# Production Deployment Checklist

Complete checklist for deploying the Mingus Application to production.

## Pre-Deployment

### Environment Setup
- [ ] Server provisioned (Ubuntu 20.04+ recommended)
- [ ] Domain name configured and DNS pointing to server
- [ ] SSH access configured with key-based authentication
- [ ] Firewall configured (ports 80, 443, 22)
- [ ] SSL certificate obtained (Let's Encrypt recommended)

### Server Requirements
- [ ] Python 3.8+ installed
- [ ] Node.js 16+ and npm installed
- [ ] Nginx installed and configured
- [ ] PostgreSQL or SQLite available
- [ ] Redis installed (optional, for caching)
- [ ] Git installed

### Security
- [ ] Firewall rules configured
- [ ] SSH key-based authentication only
- [ ] Root login disabled
- [ ] Fail2ban configured (optional)
- [ ] Security updates applied

## Initial Setup

### 1. Run Production Setup Script
```bash
sudo ./scripts/setup_production.sh
```

- [ ] Application user created (`mingus-app`)
- [ ] Directories created (`/var/www/mingus-app`)
- [ ] Systemd service files installed
- [ ] Nginx configuration installed
- [ ] SSL certificate configured

### 2. Deploy Application Code
```bash
# Clone or copy application
sudo cp -r . /var/www/mingus-app/
sudo chown -R mingus-app:mingus-app /var/www/mingus-app
```

- [ ] Application code copied to production directory
- [ ] File permissions set correctly

### 3. Configure Environment
```bash
sudo -u mingus-app cp .env.example /var/www/mingus-app/.env.production
sudo -u mingus-app nano /var/www/mingus-app/.env.production
```

- [ ] `.env.production` file created
- [ ] `SECRET_KEY` set (strong random value)
- [ ] `CSRF_SECRET_KEY` set
- [ ] `DATABASE_URL` configured
- [ ] `REDIS_URL` configured (if using)
- [ ] `BACKEND_URL` set
- [ ] `FRONTEND_URL` set
- [ ] All API keys configured
- [ ] Production flags set (`FLASK_ENV=production`)

## Deployment

### 1. Deploy Backend
```bash
cd /var/www/mingus-app
sudo -u mingus-app ./scripts/deploy_backend.sh
```

- [ ] Python virtual environment created
- [ ] Dependencies installed
- [ ] Tests passed (or skipped with `SKIP_TESTS=true`)
- [ ] Gunicorn configured
- [ ] Database initialized

### 2. Deploy Frontend
```bash
sudo -u mingus-app ./scripts/deploy_frontend.sh
```

- [ ] Node.js dependencies installed
- [ ] Frontend built successfully
- [ ] Build artifacts in `frontend/dist/`

### 3. Run Database Migrations
```bash
sudo -u mingus-app ./scripts/migrate_database.sh
```

- [ ] Database backup created
- [ ] Migrations run successfully
- [ ] Database verified

### 4. Full Deployment
```bash
sudo -u mingus-app ./scripts/deploy.sh
```

- [ ] Prerequisites checked
- [ ] Environment loaded
- [ ] Backup created
- [ ] Backend deployed
- [ ] Frontend deployed
- [ ] Migrations run
- [ ] Services restarted
- [ ] Health checks passed

## Service Configuration

### Enable and Start Services
```bash
sudo systemctl enable mingus-backend
sudo systemctl enable mingus-frontend
sudo systemctl start mingus-backend
sudo systemctl start mingus-frontend
```

- [ ] Backend service enabled
- [ ] Frontend service enabled
- [ ] Services started successfully
- [ ] Services set to start on boot

### Verify Services
```bash
sudo systemctl status mingus-backend
sudo systemctl status mingus-frontend
```

- [ ] Backend service running
- [ ] Frontend service running
- [ ] No errors in service status

## Nginx Configuration

### Install and Configure
```bash
sudo cp scripts/nginx/mingus-app.conf /etc/nginx/sites-available/mingus-app
sudo ln -s /etc/nginx/sites-available/mingus-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

- [ ] Nginx configuration copied
- [ ] Site enabled
- [ ] Configuration test passed
- [ ] Nginx reloaded

### SSL Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

- [ ] SSL certificate obtained
- [ ] Certificate auto-renewal configured
- [ ] HTTPS redirect working

## Verification

### Health Checks
```bash
./scripts/health_check.sh
```

- [ ] Backend API responding
- [ ] Frontend accessible
- [ ] Database connection working
- [ ] Processes running
- [ ] Disk space adequate

### Manual Testing
- [ ] Homepage loads
- [ ] API endpoints respond
- [ ] Authentication works
- [ ] Forms submit correctly
- [ ] Static assets load
- [ ] HTTPS working
- [ ] Security headers present

### Performance
- [ ] Page load times acceptable
- [ ] API response times acceptable
- [ ] No memory leaks
- [ ] Database queries optimized

## Monitoring

### Logs
- [ ] Backend logs accessible (`/var/log/mingus-app/`)
- [ ] Frontend logs accessible
- [ ] Nginx logs accessible
- [ ] Systemd logs accessible (`journalctl`)

### Monitoring Setup
- [ ] Health check script scheduled (cron)
- [ ] Error monitoring configured (Sentry, etc.)
- [ ] Uptime monitoring configured
- [ ] Performance monitoring configured

### Alerts
- [ ] Email alerts configured
- [ ] Slack/Discord notifications configured
- [ ] Critical error alerts working

## Backup Configuration

### Automated Backups
- [ ] Backup script scheduled (cron)
- [ ] Database backups automated
- [ ] Backup retention policy set
- [ ] Backup restoration tested

### Backup Verification
```bash
./scripts/rollback.sh --list
```

- [ ] Backups being created
- [ ] Backup restoration tested

## Security Hardening

### Application Security
- [ ] Security headers configured
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] CSRF protection enabled
- [ ] Input validation working
- [ ] SQL injection prevention verified
- [ ] XSS prevention verified

### Server Security
- [ ] Firewall configured
- [ ] SSH hardened
- [ ] Unnecessary services disabled
- [ ] Security updates automated
- [ ] Log rotation configured

## Documentation

- [ ] Deployment documentation updated
- [ ] Environment variables documented
- [ ] API endpoints documented
- [ ] Troubleshooting guide created
- [ ] Runbook created

## Post-Deployment

### Immediate Checks (First 24 Hours)
- [ ] Monitor error logs
- [ ] Check application performance
- [ ] Verify all features working
- [ ] Monitor resource usage
- [ ] Check for any alerts

### Ongoing Maintenance
- [ ] Regular security updates
- [ ] Database backups verified
- [ ] Log rotation working
- [ ] Performance monitoring
- [ ] User feedback monitoring

## Rollback Plan

### If Issues Occur
1. [ ] Identify the issue
2. [ ] Check logs for errors
3. [ ] Run health check
4. [ ] If critical, execute rollback:
   ```bash
   ./scripts/rollback.sh /path/to/backup
   ```
5. [ ] Verify rollback successful
6. [ ] Document issue and resolution

## Deployment Sign-off

- [ ] All checklist items completed
- [ ] Application tested and verified
- [ ] Monitoring configured
- [ ] Team notified of deployment
- [ ] Documentation updated
- [ ] Deployment logged

**Deployed by:** _________________  
**Date:** _________________  
**Version:** _________________  
**Notes:** _________________

---

## Quick Reference Commands

```bash
# Full deployment
cd /var/www/mingus-app && sudo -u mingus-app ./scripts/deploy.sh

# Health check
./scripts/health_check.sh

# View logs
sudo journalctl -u mingus-backend -f
sudo journalctl -u mingus-frontend -f

# Restart services
sudo systemctl restart mingus-backend
sudo systemctl restart mingus-frontend

# Rollback
./scripts/rollback.sh --list
./scripts/rollback.sh /path/to/backup
```
