# Production Deployment Scripts

This directory contains comprehensive production deployment scripts for the Mingus Application.

## Scripts Overview

### Main Deployment Scripts

1. **`deploy.sh`** - Main deployment script
   - Orchestrates the entire deployment process
   - Creates backups
   - Deploys backend and frontend
   - Runs migrations
   - Restarts services
   - Performs health checks

2. **`deploy_backend.sh`** - Backend deployment
   - Sets up Python virtual environment
   - Installs dependencies
   - Runs tests
   - Configures Gunicorn

3. **`deploy_frontend.sh`** - Frontend deployment
   - Installs Node.js dependencies
   - Builds production bundle
   - Verifies build

4. **`migrate_database.sh`** - Database migrations
   - Creates database backup
   - Runs migration scripts
   - Verifies database integrity

5. **`rollback.sh`** - Rollback to previous version
   - Lists available backups
   - Restores from backup
   - Restarts services

6. **`health_check.sh`** - Health monitoring
   - Checks backend API
   - Checks frontend
   - Verifies database
   - Monitors disk space
   - Checks running processes

7. **`setup_production.sh`** - Initial production setup
   - Creates application user
   - Sets up directories
   - Installs systemd services
   - Configures nginx
   - Sets up SSL certificates

## Quick Start

### Initial Setup

```bash
# 1. Run production setup (as root)
sudo ./scripts/setup_production.sh

# 2. Copy application to production directory
sudo cp -r . /var/www/mingus-app/
sudo chown -R mingus-app:mingus-app /var/www/mingus-app

# 3. Create production environment file
sudo -u mingus-app cp .env.example /var/www/mingus-app/.env.production
sudo -u mingus-app nano /var/www/mingus-app/.env.production
```

### Deploy Application

```bash
# Full deployment
cd /var/www/mingus-app
sudo -u mingus-app ./scripts/deploy.sh

# Or deploy components separately
sudo -u mingus-app ./scripts/deploy_backend.sh
sudo -u mingus-app ./scripts/deploy_frontend.sh
sudo -u mingus-app ./scripts/migrate_database.sh
```

### Monitor Health

```bash
# Run health check
./scripts/health_check.sh

# Check service status
sudo systemctl status mingus-backend
sudo systemctl status mingus-frontend
```

### Rollback

```bash
# List available backups
./scripts/rollback.sh --list

# Rollback to specific backup
./scripts/rollback.sh /var/www/mingus-app/backups/backup_20240101_120000
```

## Systemd Services

The deployment includes systemd service files:

- **`mingus-backend.service`** - Backend API service
- **`mingus-frontend.service`** - Frontend service

### Service Management

```bash
# Enable services
sudo systemctl enable mingus-backend
sudo systemctl enable mingus-frontend

# Start services
sudo systemctl start mingus-backend
sudo systemctl start mingus-frontend

# Stop services
sudo systemctl stop mingus-backend
sudo systemctl stop mingus-frontend

# Restart services
sudo systemctl restart mingus-backend
sudo systemctl restart mingus-frontend

# View logs
sudo journalctl -u mingus-backend -f
sudo journalctl -u mingus-frontend -f
```

## Nginx Configuration

The nginx configuration file is located at:
- **`nginx/mingus-app.conf`**

### Installation

```bash
# Copy configuration
sudo cp scripts/nginx/mingus-app.conf /etc/nginx/sites-available/mingus-app

# Enable site
sudo ln -s /etc/nginx/sites-available/mingus-app /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Environment Variables

Create `.env.production` with the following variables:

```bash
# Application
FLASK_ENV=production
SECRET_KEY=your-secret-key-here
CSRF_SECRET_KEY=your-csrf-secret-key-here

# Database
DATABASE_URL=sqlite:///assessments.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost/mingus_db

# Redis
REDIS_URL=redis://localhost:6379/0

# API URLs
BACKEND_URL=https://api.mingusapp.com
FRONTEND_URL=https://mingusapp.com

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_BIND=0.0.0.0:5001

# Security
RATE_LIMIT_PER_MINUTE=100
DB_ENCRYPTION_ENABLED=true
```

## Backup and Recovery

### Automatic Backups

The deployment script automatically creates backups before deployment:
- Database backup
- Environment file backup
- Code backup (tar.gz)

Backups are stored in: `/var/www/mingus-app/backups/`

### Manual Backup

```bash
# Create manual backup
./scripts/deploy.sh --backup-only
```

### Restore from Backup

```bash
# List backups
./scripts/rollback.sh --list

# Restore
./scripts/rollback.sh /path/to/backup
```

## Monitoring

### Health Checks

```bash
# Run health check
./scripts/health_check.sh

# Schedule regular health checks (cron)
*/5 * * * * /var/www/mingus-app/scripts/health_check.sh >> /var/log/mingus-app/health.log 2>&1
```

### Logs

- Backend logs: `/var/log/mingus-app/backend-*.log`
- Frontend logs: `/var/log/mingus-app/frontend-*.log`
- Nginx logs: `/var/log/nginx/mingus-app-*.log`
- Systemd logs: `journalctl -u mingus-backend` or `journalctl -u mingus-frontend`

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status mingus-backend

# Check logs
sudo journalctl -u mingus-backend -n 50

# Check configuration
sudo -u mingus-app /var/www/mingus-app/venv/bin/gunicorn --check-config app:app
```

### Database Issues

```bash
# Check database connection
python3 -c "from backend.models.database import db; print('OK')"

# Run migrations manually
./scripts/migrate_database.sh
```

### Nginx Issues

```bash
# Test configuration
sudo nginx -t

# Check error logs
sudo tail -f /var/log/nginx/error.log

# Reload configuration
sudo systemctl reload nginx
```

## Security Considerations

1. **Firewall**: Ensure only necessary ports are open
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **SSL/TLS**: Always use HTTPS in production
   - Use Let's Encrypt for free SSL certificates
   - Configure automatic renewal

3. **Secrets**: Never commit `.env.production` to version control
   - Use environment variables or secret management services
   - Rotate secrets regularly

4. **Updates**: Keep system and dependencies updated
   ```bash
   sudo apt update && sudo apt upgrade
   pip install --upgrade -r requirements.txt
   ```

## Deployment Checklist

- [ ] Production environment setup completed
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Backend deployed and tested
- [ ] Frontend built and deployed
- [ ] Services enabled and started
- [ ] Nginx configured and reloaded
- [ ] SSL certificate installed
- [ ] Health checks passing
- [ ] Monitoring configured
- [ ] Backups configured
- [ ] Documentation updated

## Support

For issues or questions:
1. Check logs: `/var/log/mingus-app/`
2. Run health check: `./scripts/health_check.sh`
3. Review deployment logs: `./logs/deployment_*.log`
