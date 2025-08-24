# MINGUS Production Deployment Configuration

This directory contains comprehensive production deployment configurations for the MINGUS application, optimized for high-performance, scalable deployment with proper monitoring, security, and reliability.

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Nginx
- SSL certificates (for production)

### Environment Setup

1. **Create production environment file:**
   ```bash
   cp .env.example .env.production
   ```

2. **Configure environment variables:**
   ```bash
   # Database Configuration
   DATABASE_URL=postgresql://mingus_user:your_password@localhost:5432/mingus_production
   POSTGRES_PASSWORD=your_secure_password
   
   # Redis Configuration
   REDIS_URL=redis://localhost:6379/0
   REDIS_PASSWORD=your_redis_password
   
   # Celery Configuration
   CELERY_BROKER_URL=redis://localhost:6379/0
   CELERY_RESULT_BACKEND=redis://localhost:6379/0
   
   # Application Configuration
   SECRET_KEY=your_very_secure_secret_key
   FLASK_ENV=production
   
   # External Services
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
   
   # Email Configuration
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USE_TLS=true
   MAIL_USERNAME=your_email@gmail.com
   MAIL_PASSWORD=your_app_password
   MAIL_DEFAULT_SENDER=your_email@gmail.com
   
   # SMS Configuration
   TWILIO_ACCOUNT_SID=your_twilio_sid
   TWILIO_AUTH_TOKEN=your_twilio_token
   TWILIO_PHONE_NUMBER=your_twilio_number
   
   # Email Service
   RESEND_API_KEY=your_resend_api_key
   ```

3. **Run the production startup script:**
   ```bash
   ./deployment/start-production.sh
   ```

## 📁 Configuration Files

### Core Configuration Files

| File | Purpose | Description |
|------|---------|-------------|
| `gunicorn.conf.py` | Web Server | Gunicorn configuration for Flask app |
| `celery-worker.conf.py` | Task Queue | Celery worker configuration |
| `redis.conf` | Cache/Message Broker | Redis configuration |
| `database.conf.py` | Database | PostgreSQL connection optimization |
| `docker-compose.production.yml` | Orchestration | Complete service orchestration |
| `nginx/nginx.conf` | Reverse Proxy | Nginx configuration with SSL |

### Startup and Management

| File | Purpose | Description |
|------|---------|-------------|
| `start-production.sh` | Deployment | Complete production deployment script |
| `backup.sh` | Backup | Automated backup script |
| `README.md` | Documentation | This documentation file |

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Nginx (443)   │    │   Nginx (80)    │    │   Load Balancer │
│   (SSL/TLS)     │    │   (Redirect)    │    │   (Optional)    │
└─────────┬───────┘    └─────────────────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐
│   Web App       │    ┌─────────────────┐    ┌─────────────────┐
│   (Gunicorn)    │    │  Celery Worker  │    │  Celery Beat    │
│   Port: 5002    │    │  (SMS/Email)    │    │  (Scheduler)    │
└─────────┬───────┘    └─────────────────┘    └─────────────────┘
          │
          ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │     Redis       │    │   Monitoring    │
│   (Database)    │    │   (Cache/MQ)    │    │   (StatsD)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Service Configuration

### Gunicorn Configuration

**File:** `gunicorn.conf.py`

**Key Features:**
- Auto-scaling worker processes based on CPU cores
- Gevent worker class for async support
- Comprehensive logging and monitoring
- Health check endpoints
- Request tracking and metrics

**Environment Variables:**
```bash
GUNICORN_WORKERS=4                    # Number of worker processes
GUNICORN_WORKER_CLASS=gevent         # Worker class
GUNICORN_TIMEOUT=180                 # Request timeout
GUNICORN_MAX_REQUESTS=1000           # Max requests per worker
GUNICORN_BIND=0.0.0.0:5002          # Bind address
```

### Celery Worker Configuration

**File:** `celery-worker.conf.py`

**Key Features:**
- Specialized workers for different task types
- Priority-based queue routing
- Automatic task retry and error handling
- Performance monitoring and metrics
- Graceful shutdown handling

**Worker Types:**
- **SMS Worker:** High-priority SMS tasks
- **Email Worker:** Email delivery tasks
- **Analytics Worker:** Data analysis tasks
- **Monitoring Worker:** System monitoring tasks
- **Optimization Worker:** Performance optimization tasks

**Environment Variables:**
```bash
CELERY_WORKER_CONCURRENCY=4          # Worker concurrency
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000  # Max tasks per worker
CELERY_WORKER_PREFETCH_MULTIPLIER=1  # Task prefetch
CELERY_WORKER_TYPE=sms               # Worker specialization
```

### Redis Configuration

**File:** `redis.conf`

**Key Features:**
- Optimized for high-performance caching
- Persistent storage with AOF and RDB
- Memory management with LRU eviction
- Security with password authentication
- Monitoring and slow query logging

**Environment Variables:**
```bash
REDIS_PASSWORD=your_redis_password   # Redis authentication
REDIS_MAXMEMORY=2gb                  # Maximum memory usage
REDIS_MAXMEMORY_POLICY=allkeys-lru   # Memory eviction policy
```

### Database Configuration

**File:** `database.conf.py`

**Key Features:**
- Connection pooling optimization
- SSL/TLS encryption
- Query performance monitoring
- Automatic connection retry
- Health check integration

**Environment Variables:**
```bash
DB_POOL_SIZE=20                      # Connection pool size
DB_MAX_OVERFLOW=30                   # Max overflow connections
DB_POOL_RECYCLE=3600                 # Connection recycle time
DB_STATEMENT_TIMEOUT=30000           # Query timeout (ms)
DB_SSL_MODE=require                  # SSL requirement
```

### Nginx Configuration

**File:** `nginx/nginx.conf`

**Key Features:**
- SSL/TLS termination with modern ciphers
- Rate limiting and security headers
- Load balancing with health checks
- Gzip compression and caching
- CORS support for API endpoints

**Security Features:**
- HSTS headers
- Content Security Policy
- XSS protection
- CSRF protection
- Rate limiting by endpoint type

## 📊 Monitoring and Observability

### Metrics Collection

- **StatsD:** Application metrics collection
- **Graphite:** Metrics storage and visualization
- **Health Checks:** Service health monitoring
- **Log Aggregation:** Centralized logging

### Monitoring Endpoints

- **Application Health:** `https://your-domain/health`
- **Nginx Status:** `http://localhost:8080/nginx_status`
- **Graphite Dashboard:** `http://localhost:8080`

### Log Management

- **Log Rotation:** Automatic log rotation with compression
- **Log Levels:** Configurable logging levels per service
- **Error Tracking:** Comprehensive error logging and alerting

## 🔒 Security Configuration

### SSL/TLS Configuration

1. **Obtain SSL certificates:**
   ```bash
   # For Let's Encrypt
   certbot certonly --standalone -d your-domain.com
   ```

2. **Place certificates:**
   ```bash
   cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deployment/nginx/ssl/certificate.crt
   cp /etc/letsencrypt/live/your-domain.com/privkey.pem deployment/nginx/ssl/private.key
   ```

3. **Set permissions:**
   ```bash
   chmod 600 deployment/nginx/ssl/private.key
   chmod 644 deployment/nginx/ssl/certificate.crt
   ```

### Security Headers

- **HSTS:** Strict Transport Security
- **CSP:** Content Security Policy
- **X-Frame-Options:** Clickjacking protection
- **X-Content-Type-Options:** MIME type sniffing protection

### Rate Limiting

- **API Endpoints:** 10 requests/second
- **Authentication:** 5 requests/minute
- **General Traffic:** 30 requests/second

## 💾 Backup and Recovery

### Automated Backups

The deployment includes automated backup scripts that:

- **Database Backups:** Daily PostgreSQL dumps
- **Redis Backups:** Periodic Redis snapshots
- **File Backups:** Application data and logs
- **Retention Policy:** 30-day retention with compression

### Manual Backup

```bash
# Run backup manually
./deployment/backup.sh

# Restore database
gunzip -c backups/mingus_db_backup_YYYYMMDD_HHMMSS.sql.gz | \
  docker-compose -f deployment/docker-compose.production.yml exec -T postgres psql -U mingus_user -d mingus_production
```

## 🚀 Deployment Commands

### Start Production Deployment

```bash
# Complete production deployment
./deployment/start-production.sh
```

### Service Management

```bash
# Start all services
docker-compose -f deployment/docker-compose.production.yml up -d

# Stop all services
docker-compose -f deployment/docker-compose.production.yml down

# Restart specific service
docker-compose -f deployment/docker-compose.production.yml restart web

# View logs
docker-compose -f deployment/docker-compose.production.yml logs -f web

# Scale services
docker-compose -f deployment/docker-compose.production.yml up -d --scale web=3
```

### Health Checks

```bash
# Check application health
curl -f https://your-domain/health

# Check service status
docker-compose -f deployment/docker-compose.production.yml ps

# Check Celery workers
docker-compose -f deployment/docker-compose.production.yml exec celery-worker celery -A backend.tasks.mingus_celery_tasks inspect ping
```

## 🔧 Troubleshooting

### Common Issues

1. **Port Conflicts:**
   ```bash
   # Check port usage
   netstat -tulpn | grep :5002
   
   # Kill process using port
   sudo kill -9 $(lsof -t -i:5002)
   ```

2. **Database Connection Issues:**
   ```bash
   # Check database connectivity
   docker-compose -f deployment/docker-compose.production.yml exec postgres pg_isready -U mingus_user
   
   # View database logs
   docker-compose -f deployment/docker-compose.production.yml logs postgres
   ```

3. **Redis Connection Issues:**
   ```bash
   # Check Redis connectivity
   docker-compose -f deployment/docker-compose.production.yml exec redis redis-cli ping
   
   # View Redis logs
   docker-compose -f deployment/docker-compose.production.yml logs redis
   ```

4. **SSL Certificate Issues:**
   ```bash
   # Test SSL configuration
   openssl s_client -connect your-domain:443 -servername your-domain
   
   # Check certificate validity
   openssl x509 -in deployment/nginx/ssl/certificate.crt -text -noout
   ```

### Performance Tuning

1. **Database Performance:**
   ```bash
   # Monitor database performance
   docker-compose -f deployment/docker-compose.production.yml exec postgres psql -U mingus_user -d mingus_production -c "SELECT * FROM pg_stat_activity;"
   ```

2. **Redis Performance:**
   ```bash
   # Monitor Redis performance
   docker-compose -f deployment/docker-compose.production.yml exec redis redis-cli info memory
   ```

3. **Application Performance:**
   ```bash
   # Monitor application metrics
   curl http://localhost:8080/metrics
   ```

## 📈 Scaling Considerations

### Horizontal Scaling

1. **Web Application:**
   ```bash
   # Scale web workers
   docker-compose -f deployment/docker-compose.production.yml up -d --scale web=3
   ```

2. **Celery Workers:**
   ```bash
   # Scale specific worker types
   docker-compose -f deployment/docker-compose.production.yml up -d --scale celery-sms-worker=2
   ```

3. **Database Scaling:**
   - Consider read replicas for read-heavy workloads
   - Implement connection pooling at application level
   - Use database sharding for very large datasets

### Vertical Scaling

1. **Resource Limits:**
   - Adjust CPU and memory limits in `docker-compose.production.yml`
   - Monitor resource usage and adjust accordingly

2. **Performance Tuning:**
   - Optimize database queries and indexes
   - Implement caching strategies
   - Use CDN for static assets

## 🔄 Maintenance

### Regular Maintenance Tasks

1. **Log Rotation:** Automatic daily log rotation
2. **Database Maintenance:** Weekly VACUUM and ANALYZE
3. **SSL Certificate Renewal:** Monthly certificate checks
4. **Security Updates:** Regular dependency updates
5. **Backup Verification:** Weekly backup restoration tests

### Update Procedures

1. **Application Updates:**
   ```bash
   # Pull latest code
   git pull origin main
   
   # Rebuild and restart
   docker-compose -f deployment/docker-compose.production.yml build --no-cache
   docker-compose -f deployment/docker-compose.production.yml up -d
   ```

2. **Configuration Updates:**
   ```bash
   # Update configuration files
   # Restart affected services
   docker-compose -f deployment/docker-compose.production.yml restart web nginx
   ```

## 📞 Support

For deployment issues or questions:

1. Check the troubleshooting section above
2. Review application logs in `logs/` directory
3. Check service status with Docker Compose
4. Verify environment configuration
5. Test individual service connectivity

## 📝 License

This deployment configuration is part of the MINGUS application and follows the same licensing terms. 