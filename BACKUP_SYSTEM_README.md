# MINGUS Financial Application - Backup and Recovery System

## Overview

The MINGUS Backup and Recovery System is an enterprise-grade solution designed specifically for financial applications serving African American professionals. This comprehensive system provides automated backup, recovery, monitoring, and compliance reporting capabilities to ensure data protection and business continuity.

## Features

### 🔒 **Security & Compliance**
- **Encryption**: AES-256 encryption for all backups (at rest and in transit)
- **SOX Compliance**: Full audit trails and financial data integrity verification
- **PCI DSS Compliance**: Secure handling of sensitive financial information
- **Access Controls**: Role-based access control and audit logging

### 🗄️ **Database Backup**
- **PostgreSQL 15+**: Full, incremental, and WAL-based backups
- **Point-in-Time Recovery (PITR)**: Granular recovery to specific timestamps
- **Automated Verification**: Backup integrity testing and validation
- **Cross-Region Replication**: S3-based backup distribution

### 🚀 **Redis Backup**
- **RDB Snapshots**: Point-in-time database snapshots
- **AOF Persistence**: Append-only file for durability
- **Session Data**: Complete session state preservation
- **Configuration Backup**: Redis server configuration preservation

### 📁 **File System Backup**
- **User Documents**: Encrypted backup of financial documents
- **Configuration Files**: Application and system configuration backup
- **Application Code**: Source code and deployment artifacts
- **Incremental Backups**: Changed file detection and backup

### 📊 **Monitoring & Alerting**
- **Prometheus Metrics**: Real-time performance and health monitoring
- **Grafana Dashboards**: Visual monitoring and reporting
- **Email Alerts**: Configurable notification system
- **Slack Integration**: Team communication and alerting

### 🔄 **Recovery & Testing**
- **Automated Recovery Testing**: Weekly recovery procedure validation
- **Disaster Recovery**: Comprehensive recovery runbooks
- **Performance Validation**: Recovery time and data integrity verification
- **Compliance Reporting**: Automated compliance status reporting

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Application   │    │   PostgreSQL    │    │      Redis      │
│     Layer       │    │   Database      │    │     Cache       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backup Management Layer                      │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │   Database  │  │    Redis    │  │    Files    │            │
│  │   Backup    │  │   Backup    │  │   Backup    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage & Encryption Layer                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │  Local      │  │     S3      │  │ Encryption  │            │
│  │  Storage    │  │  Cross-Reg  │  │   (AES-256) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Monitoring & Alerting Layer                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Prometheus  │  │   Grafana   │  │   Alerts    │            │
│  │   Metrics   │  │ Dashboards  │  │ (Email/SMS) │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Quick Start

### 1. **Installation**

```bash
# Clone the repository
git clone <repository-url>
cd mingus-backup-system

# Install dependencies
pip install -r requirements-backup.txt

# Create necessary directories
mkdir -p /var/backups/{postgresql,redis,files}
mkdir -p /var/recovery/postgresql
mkdir -p logs
```

### 2. **Configuration**

```bash
# Set environment variables
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_DB=mingus
export POSTGRES_USER=mingus
export POSTGRES_PASSWORD=your_secure_password

export REDIS_HOST=localhost
export REDIS_PORT=6379
export REDIS_PASSWORD=your_redis_password

export BACKUP_ENCRYPTION_KEY=your_encryption_key
export AWS_ACCESS_KEY_ID=your_aws_key
export AWS_SECRET_ACCESS_KEY=your_aws_secret
export BACKUP_S3_BUCKET=your-backup-bucket
```

### 3. **Run Backup Scheduler**

```bash
# Start the backup scheduler
python scripts/backup_scheduler.py

# Or run as daemon
python scripts/backup_scheduler.py --daemon

# Check status
python scripts/backup_scheduler.py --status
```

### 4. **Manual Operations**

```bash
# Run manual backup
python scripts/backup_scheduler.py --manual-backup=full:database

# Test recovery
python scripts/backup_scheduler.py --recovery-test

# Create cron jobs
python scripts/backup_scheduler.py --create-cron
```

## Docker Deployment

### 1. **Build and Run**

```bash
# Navigate to backup directory
cd docker/backup

# Build and start services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f backup-system
```

### 2. **Access Services**

- **Backup System**: http://localhost:5000
- **Prometheus**: http://localhost:9091
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)

### 3. **Environment Configuration**

```bash
# Copy and edit environment file
cp .env.example .env

# Edit environment variables
nano .env

# Restart services
docker-compose down
docker-compose up -d
```

## Backup Schedule

### **Daily Backups**
- **02:00 AM**: Full database backup
- **01:00 AM**: User documents backup
- **01:30 AM**: Configuration files backup
- **02:00 AM**: Application code backup

### **Hourly Backups**
- **Business Hours (9 AM - 6 PM)**: Incremental database backups
- **Every Hour**: AOF Redis backups
- **Every Hour**: File system incremental backups

### **Maintenance**
- **03:00 AM**: Cleanup old backups
- **04:00 AM**: System health checks
- **Sunday 02:00 AM**: Recovery testing
- **Sunday 07:00 AM**: Weekly compliance reports

## Recovery Procedures

### **Database Recovery**

```bash
# Full recovery
python -c "
from backend.recovery.database_recovery import DatabaseRecoveryManager
from backend.recovery.database_recovery import create_recovery_config_from_env

config = create_recovery_config_from_env()
manager = DatabaseRecoveryManager(config)

metadata = manager.perform_full_recovery(
    backup_id='BACKUP_ID',
    target_database='mingus_recovery'
)
print(f'Recovery status: {metadata.status}')
"

# Point-in-time recovery
import datetime
recovery_time = datetime.datetime(2024, 1, 15, 14, 30, 0)
metadata = manager.perform_point_in_time_recovery(
    backup_id='BACKUP_ID',
    target_database='mingus_pitr',
    recovery_time=recovery_time
)
```

### **Redis Recovery**

```bash
# Stop Redis
sudo systemctl stop redis

# Restore RDB file
cp /var/backups/redis/rdb/rdb_backup_*.rdb /var/lib/redis/dump.rdb
chown redis:redis /var/lib/redis/dump.rdb

# Start Redis
sudo systemctl start redis

# Verify recovery
redis-cli ping
redis-cli info keyspace
```

### **File Recovery**

```bash
# Extract backup
cd /var/backups/files/documents
tar -xzf document_backup_*.tar.gz

# Restore files
sudo cp -r documents/* /app/documents/
sudo chown -R app:app /app/documents/
```

## Monitoring and Alerting

### **Prometheus Metrics**

The system exposes the following metrics:

- `backup_success_total`: Total successful backups by type
- `backup_failure_total`: Total failed backups by type
- `backup_duration_seconds`: Backup duration histogram
- `backup_size_bytes`: Backup size in bytes
- `recovery_success_total`: Total successful recoveries
- `storage_usage_bytes`: Storage usage metrics

### **Alerting Configuration**

```bash
# Set alert thresholds
export ALERT_CPU_THRESHOLD=80
export ALERT_MEMORY_THRESHOLD=85
export ALERT_DISK_THRESHOLD=90
export ALERT_STORAGE_THRESHOLD=10

# Configure email alerts
export EMAIL_ALERTS_ENABLED=true
export EMAIL_SMTP_SERVER=smtp.gmail.com
export EMAIL_USERNAME=your_email@gmail.com
export EMAIL_PASSWORD=your_app_password
export EMAIL_TO=admin@company.com,ops@company.com

# Configure Slack alerts
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### **Grafana Dashboards**

Pre-configured dashboards include:

- **Backup Overview**: Success rates, durations, and sizes
- **Recovery Metrics**: Recovery times and success rates
- **System Health**: CPU, memory, disk, and network usage
- **Compliance Status**: SOX and PCI DSS compliance metrics

## Compliance Features

### **SOX Compliance**
- Complete audit trails for all backup and recovery operations
- Financial data integrity verification
- Access control validation
- Automated compliance reporting

### **PCI DSS Compliance**
- Encryption of sensitive data at rest and in transit
- Secure backup storage and transmission
- Access control and monitoring
- Regular security assessments

### **Audit Requirements**
- Detailed logging of all operations
- Metadata preservation for compliance
- Automated compliance score calculation
- Regular compliance validation testing

## Performance and Scalability

### **Performance Targets**
- **Backup Time**: < 2 hours for full database backup
- **Recovery Time**: < 4 hours for complete system recovery
- **Data Loss**: < 1 hour (RPO)
- **System Availability**: > 99.9%

### **Scalability Features**
- Parallel backup operations
- Incremental backup strategies
- Compression and deduplication
- Distributed backup storage

### **Resource Requirements**
- **CPU**: 4+ cores recommended
- **Memory**: 8GB+ RAM recommended
- **Storage**: 2x data size for local backups
- **Network**: 100Mbps+ for S3 replication

## Troubleshooting

### **Common Issues**

#### **Backup Failures**
```bash
# Check backup logs
tail -f logs/backup_scheduler.log

# Verify database connectivity
python -c "
import psycopg2
conn = psycopg2.connect(
    host='localhost',
    database='mingus',
    user='mingus',
    password='password'
)
print('Database connection successful')
"
```

#### **Recovery Issues**
```bash
# Check recovery logs
tail -f logs/recovery.log

# Verify backup integrity
python -c "
from backend.backup.database_backup import PostgreSQLBackupManager
manager = PostgreSQLBackupManager(config)
backups = manager.get_backup_status()
for backup in backups:
    print(f'{backup.backup_id}: {backup.verification_status}')
"
```

#### **Monitoring Issues**
```bash
# Check Prometheus status
curl http://localhost:9090/-/healthy

# Verify metrics endpoint
curl http://localhost:9090/metrics

# Check Grafana connectivity
curl http://localhost:3000/api/health
```

### **Log Files**
- **Backup Scheduler**: `logs/backup_scheduler.log`
- **Database Backup**: `logs/database_backup.log`
- **Redis Backup**: `logs/redis_backup.log`
- **File Backup**: `logs/file_backup.log`
- **Recovery**: `logs/recovery.log`
- **Monitoring**: `logs/monitoring.log`

## Development and Testing

### **Running Tests**

```bash
# Install test dependencies
pip install -r requirements-backup.txt

# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_database_backup.py
pytest tests/test_recovery.py
pytest tests/test_monitoring.py

# Run with coverage
pytest --cov=backend tests/
```

### **Code Quality**

```bash
# Format code
black backend/ scripts/

# Lint code
flake8 backend/ scripts/

# Type checking
mypy backend/ scripts/
```

### **Adding New Features**

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-backup-type
   ```

2. **Implement Feature**
   - Add new backup manager class
   - Implement backup methods
   - Add configuration options
   - Update monitoring metrics

3. **Add Tests**
   - Unit tests for new functionality
   - Integration tests for backup/restore
   - Performance tests for large datasets

4. **Update Documentation**
   - Update README
   - Add configuration examples
   - Update recovery procedures

## Support and Maintenance

### **Regular Maintenance Tasks**

- **Daily**: Monitor backup success rates and alert on failures
- **Weekly**: Review backup logs and performance metrics
- **Monthly**: Update backup retention policies and cleanup old backups
- **Quarterly**: Review and update recovery procedures
- **Annually**: Full disaster recovery testing and compliance validation

### **Backup Verification**

```bash
# Verify backup integrity
python -c "
from backend.backup.database_backup import PostgreSQLBackupManager
manager = PostgreSQLBackupManager(config)

# Test backup restore
test_result = manager.test_backup_restore('BACKUP_ID')
print(f'Backup verification: {test_result.status}')
"
```

### **Performance Monitoring**

```bash
# Check backup performance
python -c "
from backend.backup.monitoring import BackupMonitoringManager
monitor = BackupMonitoringManager(config)

# Get latest metrics
health = monitor.get_latest_health_metrics(1)[0]
print(f'CPU: {health.cpu_usage}%, Memory: {health.memory_usage}%')
"
```

## Contributing

We welcome contributions to improve the backup and recovery system. Please:

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### **Development Guidelines**

- Follow PEP 8 coding standards
- Add type hints to all functions
- Include comprehensive docstrings
- Write unit tests for new functionality
- Update relevant documentation

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

For questions, support, or contributions:

- **Project Maintainer**: [Your Name] - [email@company.com]
- **Technical Support**: [support@company.com]
- **Security Issues**: [security@company.com]

## Acknowledgments

- PostgreSQL community for excellent database tools
- Redis team for robust caching solutions
- AWS for reliable cloud storage services
- Open source community for monitoring and alerting tools

---

**Version**: 1.0.0  
**Last Updated**: [Date]  
**Next Review**: [Date]
