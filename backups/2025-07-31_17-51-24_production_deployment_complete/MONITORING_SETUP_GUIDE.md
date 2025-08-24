# 🔍 PostgreSQL Monitoring Setup Guide
## MINGUS Database Monitoring and Alerting Configuration

### **Date**: January 2025
### **Status**: 📋 **SETUP GUIDE**
### **Priority**: 🔴 **CRITICAL FOR PRODUCTION**

---

## **📋 Overview**

This guide provides step-by-step instructions for setting up the PostgreSQL monitoring and alerting system for the MINGUS application. The monitoring system tracks database performance, health metrics, and sends alerts for critical issues.

### **Key Features**
- ✅ **Real-time Monitoring**: 30-second monitoring intervals
- ✅ **Performance Metrics**: Query time, connection pool, cache hit ratio
- ✅ **Health Alerts**: Email, webhook, and Slack notifications
- ✅ **Trend Analysis**: Performance trend tracking
- ✅ **Health Scoring**: Overall database health assessment

---

## **🔧 Installation and Setup**

### **1. Prerequisites**

#### **Required Python Packages**
```bash
pip install psycopg2-binary schedule requests
```

#### **Required Environment Variables**
```bash
# Database Configuration
DATABASE_URL=postgresql://mingus_user:mingus_password@localhost:5432/mingus_production

# Alert Configuration
EMAIL_ALERTS_ENABLED=true
WEBHOOK_ALERTS_ENABLED=false
SLACK_ALERTS_ENABLED=false

# Email Configuration (if using email alerts)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=alerts@mingus.com
TO_EMAIL=admin@mingus.com

# Webhook Configuration (if using webhook alerts)
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts

# Slack Configuration (if using Slack alerts)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
```

### **2. File Structure**
```
mingus-app/
├── POSTGRESQL_MONITORING_ALERTS.py
├── monitoring/
│   ├── config/
│   │   └── monitoring_config.json
│   ├── logs/
│   │   └── postgresql_monitoring.log
│   └── reports/
│       └── health_reports/
└── scripts/
    ├── start_monitoring.sh
    └── stop_monitoring.sh
```

### **3. Configuration File**
Create `monitoring/config/monitoring_config.json`:
```json
{
  "database": {
    "url": "postgresql://mingus_user:mingus_password@localhost:5432/mingus_production",
    "connection_timeout": 10,
    "pool_size": 5
  },
  "monitoring": {
    "interval_seconds": 30,
    "metrics_history_size": 1000,
    "alert_history_size": 100
  },
  "alerts": {
    "email_enabled": true,
    "webhook_enabled": false,
    "slack_enabled": false,
    "email": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "username": "your-email@gmail.com",
      "password": "your-app-password",
      "from_email": "alerts@mingus.com",
      "to_email": "admin@mingus.com"
    },
    "webhook": {
      "url": "https://your-webhook-endpoint.com/alerts"
    },
    "slack": {
      "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK"
    }
  },
  "thresholds": {
    "connection_count": {
      "warning": 80,
      "critical": 95
    },
    "query_time_avg": {
      "warning": 100,
      "critical": 500
    },
    "cache_hit_ratio": {
      "warning": 0.85,
      "critical": 0.70
    },
    "disk_usage_percent": {
      "warning": 80,
      "critical": 90
    },
    "memory_usage_percent": {
      "warning": 85,
      "critical": 95
    },
    "error_rate": {
      "warning": 0.05,
      "critical": 0.10
    },
    "slow_queries": {
      "warning": 10,
      "critical": 50
    }
  }
}
```

---

## **🚀 Deployment Options**

### **Option 1: Direct Python Execution**

#### **Start Monitoring**
```bash
# Navigate to project directory
cd /path/to/mingus-app

# Set environment variables
export DATABASE_URL="postgresql://mingus_user:mingus_password@localhost:5432/mingus_production"
export EMAIL_ALERTS_ENABLED="true"
export SMTP_USERNAME="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"

# Start monitoring
python POSTGRESQL_MONITORING_ALERTS.py
```

#### **Run as Background Process**
```bash
# Start in background
nohup python POSTGRESQL_MONITORING_ALERTS.py > monitoring.log 2>&1 &

# Check if running
ps aux | grep POSTGRESQL_MONITORING_ALERTS

# Stop monitoring
pkill -f POSTGRESQL_MONITORING_ALERTS
```

### **Option 2: Systemd Service (Linux)**

#### **Create Service File**
Create `/etc/systemd/system/mingus-monitoring.service`:
```ini
[Unit]
Description=MINGUS PostgreSQL Monitoring
After=network.target

[Service]
Type=simple
User=mingus
WorkingDirectory=/path/to/mingus-app
Environment=DATABASE_URL=postgresql://mingus_user:mingus_password@localhost:5432/mingus_production
Environment=EMAIL_ALERTS_ENABLED=true
Environment=SMTP_USERNAME=your-email@gmail.com
Environment=SMTP_PASSWORD=your-app-password
ExecStart=/usr/bin/python3 POSTGRESQL_MONITORING_ALERTS.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### **Enable and Start Service**
```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable mingus-monitoring

# Start service
sudo systemctl start mingus-monitoring

# Check status
sudo systemctl status mingus-monitoring

# View logs
sudo journalctl -u mingus-monitoring -f
```

### **Option 3: Docker Container**

#### **Create Dockerfile**
Create `Dockerfile.monitoring`:
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy monitoring script
COPY POSTGRESQL_MONITORING_ALERTS.py .

# Create directories
RUN mkdir -p /app/logs /app/reports

# Run monitoring
CMD ["python", "POSTGRESQL_MONITORING_ALERTS.py"]
```

#### **Create docker-compose.yml**
```yaml
version: '3.8'
services:
  postgresql-monitoring:
    build:
      context: .
      dockerfile: Dockerfile.monitoring
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - EMAIL_ALERTS_ENABLED=${EMAIL_ALERTS_ENABLED}
      - SMTP_USERNAME=${SMTP_USERNAME}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    volumes:
      - ./logs:/app/logs
      - ./reports:/app/reports
    restart: unless-stopped
    depends_on:
      - postgres
```

#### **Run with Docker**
```bash
# Build and start
docker-compose up -d postgresql-monitoring

# View logs
docker-compose logs -f postgresql-monitoring

# Stop
docker-compose down
```

---

## **📊 Monitoring Metrics**

### **Key Metrics Tracked**

#### **Connection Metrics**
- **Total Connections**: Number of active database connections
- **Active Connections**: Connections currently processing queries
- **Idle Connections**: Connections waiting for queries
- **Connection Pool Utilization**: Percentage of pool capacity used

#### **Performance Metrics**
- **Average Query Time**: Mean response time for queries
- **Maximum Query Time**: Slowest query response time
- **Slow Queries**: Number of queries taking >1 second
- **Total Queries**: Total number of queries executed

#### **Cache Metrics**
- **Cache Hit Ratio**: Percentage of queries served from cache
- **Memory Usage**: Database memory utilization
- **Shared Buffer Usage**: Shared buffer pool utilization

#### **System Metrics**
- **Disk Usage**: Database storage utilization
- **Uptime**: Database server uptime
- **Error Rate**: Percentage of failed queries
- **Conflict Count**: Database conflicts and deadlocks

### **Alert Thresholds**

#### **Warning Level**
- Connection count > 80
- Average query time > 100ms
- Cache hit ratio < 85%
- Disk usage > 80%
- Memory usage > 85%
- Error rate > 5%
- Slow queries > 10

#### **Critical Level**
- Connection count > 95
- Average query time > 500ms
- Cache hit ratio < 70%
- Disk usage > 90%
- Memory usage > 95%
- Error rate > 10%
- Slow queries > 50

---

## **🔔 Alert Configuration**

### **Email Alerts**

#### **Gmail Setup**
1. Enable 2-factor authentication
2. Generate app password
3. Configure SMTP settings:
   ```bash
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USERNAME=your-email@gmail.com
   SMTP_PASSWORD=your-16-char-app-password
   ```

#### **Custom SMTP Setup**
```bash
# For other providers
SMTP_SERVER=your-smtp-server.com
SMTP_PORT=587
SMTP_USERNAME=your-username
SMTP_PASSWORD=your-password
```

### **Webhook Alerts**

#### **Configure Webhook Endpoint**
```bash
WEBHOOK_URL=https://your-webhook-endpoint.com/alerts
```

#### **Webhook Payload Format**
```json
{
  "level": "CRITICAL",
  "subject": "Database Connection Failure",
  "message": "Unable to connect to PostgreSQL database",
  "timestamp": "2025-01-15T10:30:00Z",
  "source": "mingus_postgresql_monitor"
}
```

### **Slack Alerts**

#### **Create Slack Webhook**
1. Go to Slack App settings
2. Create new app
3. Enable Incoming Webhooks
4. Create webhook URL
5. Configure environment variable:
   ```bash
   SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
   ```

#### **Slack Message Format**
```json
{
  "attachments": [{
    "color": "#ff0000",
    "title": "PostgreSQL Alert: Database Connection Failure",
    "text": "Unable to connect to PostgreSQL database",
    "fields": [
      {
        "title": "Level",
        "value": "CRITICAL",
        "short": true
      },
      {
        "title": "Time",
        "value": "2025-01-15 10:30:00",
        "short": true
      }
    ],
    "footer": "MINGUS PostgreSQL Monitor"
  }]
}
```

---

## **📈 Health Reports**

### **Report Generation**
The monitoring system automatically generates health reports every monitoring cycle.

#### **Health Score Calculation**
- **Base Score**: 100 points
- **Connection Penalty**: -20 points if >80 connections
- **Query Time Penalty**: -20 points if >200ms average
- **Cache Penalty**: -15 points if <80% cache hit
- **Error Penalty**: -25 points if >5% error rate

#### **Health Status Levels**
- **HEALTHY**: 80-100 points
- **DEGRADED**: 60-79 points
- **CRITICAL**: 0-59 points

### **Report Access**
```python
# Generate health report
monitor = PostgreSQLMonitor(database_url, alert_config)
health_report = monitor.generate_health_report()
print(json.dumps(health_report, indent=2))
```

#### **Sample Health Report**
```json
{
  "status": "HEALTHY",
  "health_score": 85,
  "timestamp": "2025-01-15T10:30:00Z",
  "metrics": {
    "connection_count": 25,
    "active_connections": 8,
    "query_time_avg": 75.5,
    "cache_hit_ratio": 0.92,
    "disk_usage_percent": 45.2,
    "memory_usage_percent": 68.7,
    "error_rate": 0.01,
    "uptime_seconds": 86400
  },
  "trends": {
    "connection_trend": 2,
    "query_time_trend": -5.2,
    "cache_hit_trend": 0.01
  },
  "recent_alerts": []
}
```

---

## **🔧 Troubleshooting**

### **Common Issues**

#### **Connection Failures**
```bash
# Check database connectivity
psql $DATABASE_URL -c "SELECT 1;"

# Verify environment variables
echo $DATABASE_URL
echo $SMTP_USERNAME
```

#### **Permission Issues**
```bash
# Check file permissions
ls -la POSTGRESQL_MONITORING_ALERTS.py

# Fix permissions if needed
chmod +x POSTGRESQL_MONITORING_ALERTS.py
```

#### **Email Alert Failures**
```bash
# Test SMTP connection
python -c "
import smtplib
server = smtplib.SMTP('smtp.gmail.com', 587)
server.starttls()
server.login('your-email@gmail.com', 'your-app-password')
server.quit()
print('SMTP connection successful')
"
```

#### **High Resource Usage**
```bash
# Check monitoring process
ps aux | grep POSTGRESQL_MONITORING_ALERTS

# Monitor memory usage
top -p $(pgrep -f POSTGRESQL_MONITORING_ALERTS)
```

### **Log Analysis**
```bash
# View monitoring logs
tail -f postgresql_monitoring.log

# Search for errors
grep ERROR postgresql_monitoring.log

# Search for alerts
grep ALERT postgresql_monitoring.log
```

---

## **📋 Maintenance**

### **Daily Tasks**
- Review monitoring logs for errors
- Check alert history for patterns
- Verify email/webhook/Slack notifications
- Monitor health score trends

### **Weekly Tasks**
- Review performance metrics trends
- Analyze slow query patterns
- Update alert thresholds if needed
- Clean up old log files

### **Monthly Tasks**
- Review and optimize monitoring queries
- Update monitoring configuration
- Test alert delivery systems
- Generate monthly performance report

### **Log Rotation**
```bash
# Create logrotate configuration
sudo tee /etc/logrotate.d/mingus-monitoring << EOF
/path/to/mingus-app/postgresql_monitoring.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 644 mingus mingus
}
EOF
```

---

## **🔒 Security Considerations**

### **Database Security**
- Use SSL connections for database access
- Implement connection pooling with limits
- Use read-only database user for monitoring
- Regularly rotate database passwords

### **Alert Security**
- Use app passwords for email (not regular passwords)
- Secure webhook endpoints with authentication
- Use HTTPS for all webhook URLs
- Regularly rotate API keys and tokens

### **Access Control**
- Limit monitoring script access to necessary users
- Use environment variables for sensitive data
- Implement proper file permissions
- Monitor access to monitoring logs

---

## **📞 Support**

### **Getting Help**
- Check the troubleshooting section above
- Review monitoring logs for error details
- Test individual components separately
- Contact the development team for assistance

### **Useful Commands**
```bash
# Check monitoring status
systemctl status mingus-monitoring

# View recent logs
journalctl -u mingus-monitoring --since "1 hour ago"

# Test database connection
psql $DATABASE_URL -c "SELECT version();"

# Generate health report
python -c "
from POSTGRESQL_MONITORING_ALERTS import PostgreSQLMonitor
import os
monitor = PostgreSQLMonitor(os.getenv('DATABASE_URL'), {})
print(monitor.generate_health_report())
"
```

---

## **✅ Setup Checklist**

### **Installation** ✅
- [ ] Python dependencies installed
- [ ] Environment variables configured
- [ ] Configuration file created
- [ ] Monitoring script tested

### **Deployment** ✅
- [ ] Monitoring service started
- [ ] Log files created and writable
- [ ] Database connection verified
- [ ] Initial metrics collected

### **Alerting** ✅
- [ ] Email alerts configured and tested
- [ ] Webhook alerts configured (if using)
- [ ] Slack alerts configured (if using)
- [ ] Alert thresholds reviewed

### **Monitoring** ✅
- [ ] Health reports generated
- [ ] Performance metrics tracked
- [ ] Alert history populated
- [ ] Log rotation configured

---

**🎯 Next Steps**

1. **Complete the setup checklist above**
2. **Test all alert channels**
3. **Review and adjust alert thresholds**
4. **Set up log rotation and maintenance**
5. **Document any custom configurations**

---

**📞 For questions or issues**: Contact the development team or refer to the troubleshooting section above. 