# Database Connectivity Troubleshooting Guide

## Overview
This guide provides comprehensive solutions for resolving PostgreSQL and SQLAlchemy connectivity issues in your Flask application.

## Quick Diagnosis

### 1. Run the Connectivity Test
```bash
python database_connectivity_test.py
```

### 2. Run the Auto-Fix Script
```bash
python fix_database_connectivity.py
```

## Common Issues and Solutions

### Issue 1: PostgreSQL Service Not Running

**Symptoms:**
- Connection refused errors
- "Could not connect to server" messages
- Flask app fails to start

**Solutions:**
```bash
# Check PostgreSQL service status
brew services list | grep postgresql

# Start PostgreSQL service
brew services start postgresql@14

# Restart if there are errors
brew services restart postgresql@14

# Check logs for errors
tail -f /usr/local/var/log/postgresql@14.log
```

### Issue 2: Missing Environment Variables

**Symptoms:**
- "DATABASE_URL not configured" errors
- Configuration validation failures
- Database initialization skipped

**Solutions:**
1. Create a `.env` file in your project root:
```bash
cp database_config.env.example .env
```

2. Update the `.env` file with your actual database credentials:
```env
DATABASE_URL=postgresql://username:password@localhost:5432/database_name
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_RECYCLE=3600
```

### Issue 3: Connection Pool Exhaustion

**Symptoms:**
- "Too many connections" errors
- Slow response times
- Connection timeouts

**Solutions:**
1. **Increase pool size** in your `.env` file:
```env
DB_POOL_SIZE=50
DB_MAX_OVERFLOW=100
```

2. **Enable connection recycling**:
```env
DB_POOL_RECYCLE=1800
DB_POOL_PRE_PING=true
```

3. **Monitor pool usage**:
```python
from backend.database import get_database_info
info = get_database_info()
print(f"Pool status: {info}")
```

### Issue 4: Authentication Failures

**Symptoms:**
- "Authentication failed" errors
- "Password authentication failed" messages
- Permission denied errors

**Solutions:**
1. **Reset PostgreSQL user password**:
```sql
ALTER USER your_username PASSWORD 'new_password';
```

2. **Check pg_hba.conf** for authentication method:
```bash
# Find PostgreSQL config directory
psql -U postgres -c "SHOW config_file"
```

3. **Create new database user**:
```sql
CREATE USER mingus_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE mingus_db TO mingus_user;
```

### Issue 5: Connection Timeouts

**Symptoms:**
- Slow connection establishment
- "Connection timed out" errors
- Hanging database operations

**Solutions:**
1. **Add connection timeouts** to your database configuration:
```python
engine = create_engine(
    database_url,
    connect_args={
        'connect_timeout': 10,
        'application_name': 'mingus_app'
    },
    pool_pre_ping=True,
    pool_recycle=300
)
```

2. **Check network connectivity**:
```bash
# Test PostgreSQL port
telnet localhost 5432

# Check firewall settings
sudo ufw status
```

### Issue 6: SQLAlchemy Version Compatibility

**Symptoms:**
- Import errors
- Deprecation warnings
- Unexpected behavior

**Solutions:**
1. **Update requirements.txt**:
```txt
SQLAlchemy>=2.0.0
Flask-SQLAlchemy>=3.0.5
psycopg2-binary>=2.9.7
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

## Configuration Optimization

### Optimal Connection Pool Settings

```python
# For development
DB_POOL_SIZE = 20
DB_MAX_OVERFLOW = 30
DB_POOL_RECYCLE = 3600

# For production
DB_POOL_SIZE = 50
DB_MAX_OVERFLOW = 100
DB_POOL_RECYCLE = 1800
```

### PostgreSQL Performance Tuning

```sql
-- Increase connection limits
ALTER SYSTEM SET max_connections = 200;

-- Optimize memory settings
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';

-- Reload configuration
SELECT pg_reload_conf();
```

### Redis Configuration

```env
# Redis connection with fallback
REDIS_URL=redis://localhost:6379/0
REDIS_POOL_SIZE=20
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5
```

## Monitoring and Debugging

### Enable SQLAlchemy Logging

```python
# In your Flask app configuration
app.config['SQLALCHEMY_ECHO'] = True
app.config['SQLALCHEMY_RECORD_QUERIES'] = True
```

### Monitor Connection Pool Status

```python
from backend.database import get_database_info

@app.route('/db-status')
def database_status():
    info = get_database_info()
    return jsonify(info)
```

### Check Database Health

```python
from backend.database import health_check

@app.route('/health')
def health():
    db_health = health_check()
    return jsonify(db_health)
```

## Production Deployment Checklist

- [ ] Set `FLASK_ENV=production`
- [ ] Disable debug mode (`DEBUG=false`)
- [ ] Use secure session cookies
- [ ] Configure proper connection pooling
- [ ] Set up database monitoring
- [ ] Configure connection timeouts
- [ ] Test failover scenarios
- [ ] Monitor connection pool usage
- [ ] Set up alerting for connection issues

## Troubleshooting Commands

### PostgreSQL Commands
```bash
# Connect to PostgreSQL
psql -U postgres -d postgres

# List databases
\l

# List users
\du

# Check active connections
SELECT * FROM pg_stat_activity;

# Check connection count
SELECT count(*) FROM pg_stat_activity;
```

### System Commands
```bash
# Check PostgreSQL process
ps aux | grep postgres

# Check port usage
lsof -i :5432

# Check system resources
top
htop
```

### Log Analysis
```bash
# PostgreSQL logs
tail -f /usr/local/var/log/postgresql@14.log

# Application logs
tail -f logs/mingus.log

# System logs
tail -f /var/log/system.log
```

## Emergency Recovery

### Reset Database Connection
```python
from backend.database import engine

# Dispose all connections
engine.dispose()

# Reinitialize
from backend.database import init_database_session_factory
init_database_session_factory(database_url)
```

### Restart PostgreSQL Service
```bash
brew services stop postgresql@14
brew services start postgresql@14
```

### Clear Connection Pool
```python
# Force close all connections
engine.pool.dispose()
```

## Support and Resources

- **PostgreSQL Documentation**: https://www.postgresql.org/docs/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Flask-SQLAlchemy**: https://flask-sqlalchemy.palletsprojects.com/
- **psycopg2 Documentation**: https://www.psycopg.org/docs/

## Contact Information

If you continue to experience issues after following this guide:

1. Run the diagnostic scripts provided
2. Check the logs for specific error messages
3. Review your environment configuration
4. Verify network and firewall settings
5. Consider upgrading PostgreSQL or SQLAlchemy versions

---

**Last Updated**: January 2025
**Version**: 1.0
**Maintainer**: MINGUS Development Team
