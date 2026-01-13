# 🔧 Mingus Meme Splash Page - Troubleshooting Guide

This guide helps you diagnose and resolve common issues during deployment and operation of the Mingus Meme Splash Page.

## 🚨 Common Issues

### 1. Application Won't Start

#### Symptoms
- Container fails to start
- Application returns 500 errors
- Database connection errors

#### Solutions

**Check Environment Variables**
```bash
# Verify all required variables are set
docker-compose exec mingus-meme-app env | grep -E "(SECRET_KEY|DATABASE_URL|AWS_)"

# Check for missing variables
echo $SECRET_KEY
echo $DATABASE_URL
```

**Check Database Connection**
```bash
# Test database connectivity
docker-compose exec mingus-meme-app python -c "
import sqlite3
conn = sqlite3.connect('mingus_memes.db')
print('Database connected successfully')
conn.close()
"
```

**Check Logs**
```bash
# View application logs
docker-compose logs mingus-meme-app

# View specific error logs
docker-compose logs mingus-meme-app | grep ERROR
```

### 2. File Upload Issues

#### Symptoms
- Upload fails with 413 error
- Images not displaying
- S3 upload errors

#### Solutions

**Check File Size Limits**
```bash
# Verify nginx configuration
docker-compose exec nginx cat /etc/nginx/nginx.conf | grep client_max_body_size

# Check Flask configuration
docker-compose exec mingus-meme-app python -c "
import os
print('Max file size:', os.environ.get('MAX_FILE_SIZE', 'Not set'))
"
```

**Test S3 Configuration**
```bash
# Test AWS credentials
docker-compose exec mingus-meme-app python -c "
import boto3
s3 = boto3.client('s3')
print('S3 buckets:', [b['Name'] for b in s3.list_buckets()['Buckets']])
"
```

**Check File Permissions**
```bash
# Verify upload directory permissions
docker-compose exec mingus-meme-app ls -la /app/static/uploads/

# Fix permissions if needed
docker-compose exec mingus-meme-app chmod 755 /app/static/uploads/
```

### 3. Database Issues

#### Symptoms
- Migration failures
- Data not persisting
- SQL errors

#### Solutions

**Check Database File**
```bash
# Verify database exists and is accessible
docker-compose exec mingus-meme-app ls -la mingus_memes.db

# Check database integrity
docker-compose exec mingus-meme-app python migrations/migrate.py --check-health
```

**Run Migrations Manually**
```bash
# Run migrations with verbose output
docker-compose exec mingus-meme-app python migrations/migrate.py --db-path mingus_memes.db

# Check migration status
docker-compose exec mingus-meme-app sqlite3 mingus_memes.db "SELECT * FROM migrations;"
```

**Reset Database (Development Only)**
```bash
# WARNING: This will delete all data
docker-compose exec mingus-meme-app rm mingus_memes.db
docker-compose exec mingus-meme-app python migrations/migrate.py
```

### 4. Performance Issues

#### Symptoms
- Slow page loads
- High memory usage
- Timeout errors

#### Solutions

**Check Resource Usage**
```bash
# Monitor container resources
docker stats

# Check application logs for performance issues
docker-compose logs mingus-meme-app | grep -E "(slow|timeout|memory)"
```

**Optimize Database**
```bash
# Analyze database performance
docker-compose exec mingus-meme-app sqlite3 mingus_memes.db "ANALYZE;"

# Check for missing indexes
docker-compose exec mingus-meme-app sqlite3 mingus_memes.db ".indices"
```

**Scale Application**
```bash
# Increase worker processes
docker-compose up --scale mingus-meme-app=3

# Add more memory to containers
# Edit docker-compose.yml and add:
# deploy:
#   resources:
#     limits:
#       memory: 1G
```

### 5. SSL/HTTPS Issues

#### Symptoms
- SSL certificate errors
- Mixed content warnings
- HTTPS redirect loops

#### Solutions

**Check SSL Certificate**
```bash
# Verify certificate validity
openssl x509 -in /etc/nginx/ssl/cert.pem -text -noout

# Check certificate expiration
certbot certificates
```

**Test SSL Configuration**
```bash
# Test SSL with external tool
curl -I https://yourdomain.com

# Check SSL rating
# Visit: https://www.ssllabs.com/ssltest/
```

**Fix Mixed Content**
```bash
# Ensure all resources use HTTPS
grep -r "http://" /app/static/
grep -r "http://" /app/templates/
```

### 6. Monitoring Issues

#### Symptoms
- No error reports in Sentry
- Missing performance data
- Log files not rotating

#### Solutions

**Test Sentry Integration**
```bash
# Send test error
docker-compose exec mingus-meme-app python -c "
import sentry_sdk
sentry_sdk.capture_message('Test error from deployment')
"
```

**Check Log Rotation**
```bash
# Verify log files
docker-compose exec mingus-meme-app ls -la /app/logs/

# Check log rotation configuration
docker-compose exec mingus-meme-app cat /etc/logrotate.d/mingus
```

**Test New Relic**
```bash
# Check New Relic agent status
docker-compose exec mingus-meme-app python -c "
import newrelic.agent
print('New Relic agent status:', newrelic.agent.application())
"
```

## 🔍 Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
# health_check.sh

echo "=== System Health Check ==="

# Check containers
echo "Container Status:"
docker-compose ps

# Check disk space
echo "Disk Usage:"
df -h

# Check memory
echo "Memory Usage:"
free -h

# Check database
echo "Database Status:"
docker-compose exec mingus-meme-app python migrations/migrate.py --check-health

# Check application
echo "Application Health:"
curl -f http://localhost/health || echo "Health check failed"

# Check logs for errors
echo "Recent Errors:"
docker-compose logs --tail=50 mingus-meme-app | grep ERROR
```

### Performance Analysis
```bash
#!/bin/bash
# performance_check.sh

echo "=== Performance Analysis ==="

# Database performance
echo "Database Performance:"
docker-compose exec mingus-meme-app sqlite3 mingus_memes.db "
SELECT name, sql FROM sqlite_master WHERE type='index';
EXPLAIN QUERY PLAN SELECT * FROM memes WHERE category='faith' AND is_active=1;
"

# Application metrics
echo "Application Metrics:"
docker-compose exec mingus-meme-app python -c "
import psutil
import os
print(f'Memory usage: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB')
print(f'CPU usage: {psutil.cpu_percent()}%')
"

# Network connectivity
echo "Network Connectivity:"
curl -w "@curl-format.txt" -o /dev/null -s https://yourdomain.com
```

### Security Audit
```bash
#!/bin/bash
# security_audit.sh

echo "=== Security Audit ==="

# Check for exposed secrets
echo "Checking for exposed secrets:"
grep -r "password\|secret\|key" /app/ --exclude-dir=logs --exclude="*.pyc"

# Check file permissions
echo "File Permissions:"
find /app -type f -perm /o+w -ls

# Check SSL configuration
echo "SSL Configuration:"
openssl s_client -connect yourdomain.com:443 -servername yourdomain.com < /dev/null 2>/dev/null | openssl x509 -noout -text | grep -E "(Subject:|Issuer:|Not After)"
```

## 📊 Monitoring and Alerts

### Set Up Alerts

**Disk Space Alert**
```bash
# Add to crontab
echo "0 */6 * * * df -h | awk '\$5 > 80 {print \$0}' | mail -s 'Disk Space Alert' admin@yourdomain.com" | crontab -
```

**Application Health Alert**
```bash
# Health check script
#!/bin/bash
if ! curl -f http://localhost/health > /dev/null 2>&1; then
    echo "Application health check failed" | mail -s "App Down Alert" admin@yourdomain.com
fi
```

**Database Backup Alert**
```bash
# Backup verification
#!/bin/bash
if [ ! -f "/backups/mingus_memes_$(date +%Y%m%d).db" ]; then
    echo "Daily backup missing" | mail -s "Backup Alert" admin@yourdomain.com
fi
```

## 🆘 Emergency Procedures

### Application Down
1. Check container status: `docker-compose ps`
2. Restart services: `docker-compose restart`
3. Check logs: `docker-compose logs mingus-meme-app`
4. Scale up: `docker-compose up --scale mingus-meme-app=2`

### Database Corruption
1. Stop application: `docker-compose stop mingus-meme-app`
2. Restore from backup: `cp /backups/mingus_memes_backup.db mingus_memes.db`
3. Run integrity check: `sqlite3 mingus_memes.db "PRAGMA integrity_check;"`
4. Restart application: `docker-compose start mingus-meme-app`

### Security Breach
1. Immediately change all passwords and API keys
2. Review access logs: `docker-compose logs nginx | grep -E "(POST|PUT|DELETE)"`
3. Check for unauthorized files: `find /app -name "*.php" -o -name "*.sh"`
4. Update all dependencies: `pip install --upgrade -r requirements-production.txt`

## 📞 Getting Help

### Log Collection
```bash
# Collect all relevant logs
mkdir -p /tmp/mingus-logs
docker-compose logs > /tmp/mingus-logs/docker-compose.log
docker-compose exec mingus-meme-app cat /app/logs/mingus-meme-app.log > /tmp/mingus-logs/app.log
docker-compose exec nginx cat /var/log/nginx/error.log > /tmp/mingus-logs/nginx-error.log
tar -czf mingus-logs-$(date +%Y%m%d).tar.gz /tmp/mingus-logs/
```

### Support Information
When seeking help, provide:
- Application version
- Deployment method (Docker, Heroku, AWS)
- Error messages and logs
- Environment configuration (without secrets)
- Steps to reproduce the issue

### Useful Resources
- [Docker Documentation](https://docs.docker.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [AWS S3 Documentation](https://docs.aws.amazon.com/s3/)
- [Nginx Documentation](https://nginx.org/en/docs/)
