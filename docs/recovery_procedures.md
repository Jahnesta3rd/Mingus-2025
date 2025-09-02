# MINGUS Financial Application - Recovery Procedures

## Table of Contents

1. [Overview](#overview)
2. [Recovery Objectives](#recovery-objectives)
3. [Pre-Recovery Checklist](#pre-recovery-checklist)
4. [Database Recovery Procedures](#database-recovery-procedures)
5. [Redis Recovery Procedures](#redis-recovery-procedures)
6. [File System Recovery Procedures](#file-system-recovery-procedures)
7. [Disaster Recovery Scenarios](#disaster-recovery-scenarios)
8. [Compliance and Audit Requirements](#compliance-and-audit-requirements)
9. [Testing and Validation](#testing-and-validation)
10. [Emergency Contacts](#emergency-contacts)

## Overview

This document provides comprehensive recovery procedures for the MINGUS financial application backup and recovery system. The system is designed to meet enterprise-grade requirements for financial applications serving African American professionals with sensitive financial data.

### System Architecture

- **Primary Database**: PostgreSQL 15+ with WAL archiving
- **Cache Layer**: Redis 7+ with RDB and AOF persistence
- **File Storage**: Encrypted file backups with compression
- **Backup Storage**: Local + S3 cross-region replication
- **Monitoring**: Prometheus + Grafana with alerting

## Recovery Objectives

### Recovery Time Objective (RTO): 4 Hours
- **Critical Systems**: 2 hours (database, authentication)
- **Supporting Systems**: 4 hours (file storage, monitoring)
- **Non-Critical Systems**: 8 hours (analytics, reporting)

### Recovery Point Objective (RPO): 1 Hour
- **Database**: 15 minutes (WAL archiving)
- **Redis**: 1 hour (AOF persistence)
- **Files**: 1 hour (incremental backups)

### Data Integrity Requirements
- **Financial Data**: 100% integrity verification required
- **User Data**: 99.99% integrity verification required
- **Audit Trails**: Complete preservation required

## Pre-Recovery Checklist

### 1. System Assessment
- [ ] Verify backup system status
- [ ] Check available storage space
- [ ] Validate network connectivity
- [ ] Confirm access to backup storage
- [ ] Review recent backup logs

### 2. Resource Verification
- [ ] Ensure sufficient CPU/memory resources
- [ ] Verify disk space for recovery operations
- [ ] Check network bandwidth availability
- [ ] Confirm access to encryption keys

### 3. Documentation Preparation
- [ ] Gather backup metadata
- [ ] Prepare recovery scripts
- [ ] Document current system state
- [ ] Prepare communication plan

### 4. Team Coordination
- [ ] Notify stakeholders
- [ ] Assign recovery team roles
- [ ] Establish communication channels
- [ ] Set up incident tracking

## Database Recovery Procedures

### Full Database Recovery

#### Step 1: Environment Preparation
```bash
# Create recovery directory
mkdir -p /var/recovery/postgresql
cd /var/recovery/postgresql

# Verify backup availability
ls -la /var/backups/postgresql/full/
```

#### Step 2: Backup Selection
```bash
# List available backups
python -c "
from backend.backup.database_backup import PostgreSQLBackupManager
from backend.backup.database_backup import create_backup_config_from_env

config = create_backup_config_from_env()
manager = PostgreSQLBackupManager(config)
backups = manager.get_backup_status()
for backup in backups[:5]:
    print(f'{backup.backup_id}: {backup.timestamp} - {backup.status}')
"
```

#### Step 3: Recovery Execution
```bash
# Execute recovery
python -c "
from backend.recovery.database_recovery import DatabaseRecoveryManager
from backend.recovery.database_recovery import create_recovery_config_from_env

config = create_recovery_config_from_env()
manager = DatabaseRecoveryManager(config)

# Perform recovery
metadata = manager.perform_full_recovery(
    backup_id='SELECTED_BACKUP_ID',
    target_database='mingus_recovery'
)

print(f'Recovery completed: {metadata.status}')
print(f'Recovery time: {metadata.recovery_time_seconds} seconds')
"
```

#### Step 4: Verification
```bash
# Connect to recovered database
psql -h localhost -U mingus -d mingus_recovery

# Verify tables and data
\dt
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM financial_transactions;
SELECT COUNT(*) FROM audit_logs;

# Check data integrity
SELECT 
    schemaname,
    tablename,
    n_tup_ins as inserts,
    n_tup_upd as updates,
    n_tup_del as deletes
FROM pg_stat_user_tables;
```

### Point-in-Time Recovery (PITR)

#### Step 1: Identify Recovery Point
```bash
# List WAL files
ls -la /var/lib/postgresql/wal_archive/

# Find WAL file for target time
python -c "
import datetime
from pathlib import Path

target_time = datetime.datetime(2024, 1, 15, 14, 30, 0)
wal_dir = Path('/var/lib/postgresql/wal_archive')

for wal_file in wal_dir.glob('*.wal'):
    file_time = datetime.datetime.fromtimestamp(wal_file.stat().st_mtime)
    if file_time >= target_time:
        print(f'{wal_file.name}: {file_time}')
        break
"
```

#### Step 2: Execute PITR
```bash
python -c "
from backend.recovery.database_recovery import DatabaseRecoveryManager
from backend.recovery.database_recovery import create_recovery_config_from_env
import datetime

config = create_recovery_config_from_env()
manager = DatabaseRecoveryManager(config)

# Perform PITR
recovery_time = datetime.datetime(2024, 1, 15, 14, 30, 0)
metadata = manager.perform_point_in_time_recovery(
    backup_id='BASE_BACKUP_ID',
    target_database='mingus_pitr',
    recovery_time=recovery_time
)

print(f'PITR completed: {metadata.status}')
"
```

### Incremental Recovery

#### Step 1: Apply Base Backup
```bash
# Apply full backup first
python scripts/backup_scheduler.py --job=database_full
```

#### Step 2: Apply Incremental Backups
```bash
# List incremental backups
ls -la /var/backups/postgresql/incremental/

# Apply WAL files
python -c "
from backend.recovery.database_recovery import DatabaseRecoveryManager
from backend.recovery.database_recovery import create_recovery_config_from_env

config = create_recovery_config_from_env()
manager = DatabaseRecoveryManager(config)

# Apply incremental recovery
metadata = manager.perform_incremental_recovery(
    backup_id='INCREMENTAL_BACKUP_ID',
    target_database='mingus_incremental'
)
"
```

## Redis Recovery Procedures

### RDB Recovery

#### Step 1: Stop Redis Service
```bash
sudo systemctl stop redis
# or
docker stop mingus-backup-redis
```

#### Step 2: Restore RDB File
```bash
# Copy backup RDB file
cp /var/backups/redis/rdb/rdb_backup_*.rdb /var/lib/redis/dump.rdb

# Set proper permissions
chown redis:redis /var/lib/redis/dump.rdb
chmod 644 /var/lib/redis/dump.rdb
```

#### Step 3: Start Redis Service
```bash
sudo systemctl start redis
# or
docker start mingus-backup-redis

# Verify recovery
redis-cli ping
redis-cli info keyspace
```

### AOF Recovery

#### Step 1: Prepare AOF File
```bash
# Copy backup AOF file
cp /var/backups/redis/aof/aof_backup_*.aof /var/lib/redis/appendonly.aof

# Set proper permissions
chown redis:redis /var/lib/redis/appendonly.aof
chmod 644 /var/lib/redis/appendonly.aof
```

#### Step 2: Configure Redis
```bash
# Edit redis.conf
echo "appendonly yes" >> /etc/redis/redis.conf
echo "appendfsync everysec" >> /etc/redis/redis.conf
```

#### Step 3: Restart Redis
```bash
sudo systemctl restart redis
# Verify recovery
redis-cli ping
redis-cli info persistence
```

### Session Data Recovery

#### Step 1: Export Session Data
```bash
python -c "
from backend.backup.redis_backup import RedisBackupManager
from backend.backup.redis_backup import create_redis_backup_config_from_env

config = create_redis_backup_config_from_env()
manager = RedisBackupManager(config)

# Create session backup
metadata = manager.create_session_backup()
print(f'Session backup created: {metadata.backup_id}')
"
```

#### Step 2: Restore Session Data
```bash
# Parse session backup and restore
python -c "
import json
import redis

# Load session backup
with open('/var/backups/redis/session/session_backup_*.json', 'r') as f:
    session_data = json.load(f)

# Connect to Redis
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

# Restore sessions
for key, data in session_data.items():
    if data['type'] == 'string':
        r.set(key, data['value'], ex=data['ttl'] if data['ttl'] > 0 else None)
    elif data['type'] == 'hash':
        r.hset(key, mapping=data['value'])
        if data['ttl'] > 0:
            r.expire(key, data['ttl'])

print('Session data restored successfully')
"
```

## File System Recovery Procedures

### Documents Recovery

#### Step 1: Identify Backup
```bash
# List available document backups
ls -la /var/backups/files/documents/

# Check backup metadata
python -c "
from backend.backup.file_backup import FileBackupManager
from backend.backup.file_backup import create_file_backup_config_from_env

config = create_file_backup_config_from_env()
manager = FileBackupManager(config)

backups = manager.get_backup_status()
for backup in backups:
    if backup.backup_type == 'documents':
        print(f'{backup.backup_id}: {backup.timestamp} - {backup.total_files} files')
"
```

#### Step 2: Restore Documents
```bash
# Extract backup
cd /var/backups/files/documents
tar -xzf document_backup_*.tar.gz

# Restore to target location
sudo cp -r documents/* /app/documents/
sudo chown -R app:app /app/documents/
```

### Configuration Recovery

#### Step 1: Restore Configs
```bash
# Extract configuration backup
cd /var/backups/files/configs
tar -xzf config_backup_*.tar.gz

# Restore configurations
sudo cp -r configs/* /app/config/
sudo chown -R app:app /app/config/
```

#### Step 2: Verify Configurations
```bash
# Check critical config files
ls -la /app/config/
cat /app/config/app.conf
cat /app/config/database.conf
```

### Code Recovery

#### Step 1: Restore Application Code
```bash
# Extract code backup
cd /var/backups/files/code
tar -xzf code_backup_*.tar.gz

# Restore code
sudo cp -r code/* /app/backend/
sudo chown -R app:app /app/backend/
```

#### Step 2: Verify Code Integrity
```bash
# Check file permissions
ls -la /app/backend/
find /app/backend -name "*.py" -exec python -m py_compile {} \;
```

## Disaster Recovery Scenarios

### Scenario 1: Complete System Failure

#### Impact Assessment
- **Severity**: Critical
- **Affected Systems**: All
- **Estimated Recovery Time**: 4-6 hours

#### Recovery Steps
1. **Immediate Response** (0-30 minutes)
   - Activate incident response team
   - Assess damage scope
   - Notify stakeholders

2. **Infrastructure Recovery** (30 minutes - 2 hours)
   - Restore server infrastructure
   - Configure network connectivity
   - Verify storage systems

3. **Data Recovery** (2-4 hours)
   - Restore database from latest backup
   - Recover Redis data
   - Restore application files

4. **System Validation** (4-6 hours)
   - Verify data integrity
   - Test application functionality
   - Validate compliance requirements

### Scenario 2: Database Corruption

#### Impact Assessment
- **Severity**: High
- **Affected Systems**: Database, application
- **Estimated Recovery Time**: 2-3 hours

#### Recovery Steps
1. **Assessment** (0-15 minutes)
   - Identify corruption scope
   - Determine backup requirements

2. **Recovery** (15 minutes - 2 hours)
   - Restore from last known good backup
   - Apply WAL files if available
   - Verify data integrity

3. **Validation** (2-3 hours)
   - Run integrity checks
   - Validate financial data
   - Test application functionality

### Scenario 3: Storage System Failure

#### Impact Assessment
- **Severity**: Medium
- **Affected Systems**: File storage, backups
- **Estimated Recovery Time**: 3-4 hours

#### Recovery Steps
1. **Storage Recovery** (0-1 hour)
   - Restore storage infrastructure
   - Verify storage connectivity

2. **Data Restoration** (1-3 hours)
   - Restore from S3 backups
   - Verify file integrity
   - Restore application files

3. **System Validation** (3-4 hours)
   - Test file operations
   - Verify backup functionality
   - Validate compliance

## Compliance and Audit Requirements

### SOX Compliance

#### Financial Data Integrity
- [ ] Verify all financial transactions are preserved
- [ ] Validate audit trail completeness
- [ ] Confirm data accuracy and consistency
- [ ] Document recovery procedures

#### Access Controls
- [ ] Verify user authentication systems
- [ ] Validate role-based access controls
- [ ] Confirm audit logging functionality
- [ ] Test security measures

### PCI DSS Compliance

#### Data Protection
- [ ] Verify encryption of sensitive data
- [ ] Validate secure transmission protocols
- [ ] Confirm secure storage practices
- [ ] Test access controls

#### Audit Requirements
- [ ] Document all recovery actions
- [ ] Maintain audit trails
- [ ] Verify compliance monitoring
- [ ] Generate compliance reports

### Audit Trail Requirements

#### Recovery Documentation
- [ ] Document all recovery steps
- [ ] Record timestamps and actions
- [ ] Maintain operator logs
- [ ] Preserve system logs

#### Compliance Reporting
- [ ] Generate recovery reports
- [ ] Document compliance status
- [ ] Maintain audit records
- [ ] Provide evidence for audits

## Testing and Validation

### Automated Testing

#### Recovery Testing Schedule
- **Weekly**: Automated recovery tests
- **Monthly**: Full disaster recovery drills
- **Quarterly**: Compliance validation tests

#### Test Procedures
```bash
# Run automated recovery test
python scripts/backup_scheduler.py --recovery-test

# Check test results
python -c "
from backend.recovery.database_recovery import DatabaseRecoveryManager
from backend.recovery.database_recovery import create_recovery_config_from_env

config = create_recovery_config_from_env()
manager = DatabaseRecoveryManager(config)

results = manager.get_test_results()
for result in results[:5]:
    print(f'{result.test_id}: {result.test_status} - {result.test_duration_seconds}s')
"
```

### Manual Testing

#### Recovery Validation Checklist
- [ ] Database connectivity
- [ ] Data integrity verification
- [ ] Application functionality
- [ ] Performance benchmarks
- [ ] Security validation
- [ ] Compliance verification

#### Performance Testing
```bash
# Database performance test
pgbench -h localhost -U mingus -d mingus_recovery -c 10 -t 1000

# Redis performance test
redis-benchmark -h localhost -p 6379 -n 100000 -c 50

# Application performance test
ab -n 1000 -c 10 http://localhost:5000/api/health
```

## Emergency Contacts

### Primary Contacts
- **System Administrator**: [Admin Name] - [Phone] - [Email]
- **Database Administrator**: [DBA Name] - [Phone] - [Email]
- **Security Officer**: [Security Name] - [Phone] - [Email]

### Escalation Contacts
- **IT Manager**: [Manager Name] - [Phone] - [Email]
- **Chief Technology Officer**: [CTO Name] - [Phone] - [Email]
- **Compliance Officer**: [Compliance Name] - [Phone] - [Email]

### External Contacts
- **Cloud Provider Support**: [Provider] - [Phone] - [Support Portal]
- **Backup Storage Provider**: [Provider] - [Phone] - [Support Portal]
- **Security Vendor**: [Vendor] - [Phone] - [Support Portal]

## Recovery Metrics and KPIs

### Performance Metrics
- **Recovery Time**: Target < 4 hours
- **Data Loss**: Target < 1 hour
- **System Availability**: Target > 99.9%
- **Backup Success Rate**: Target > 99.5%

### Compliance Metrics
- **Audit Trail Completeness**: 100%
- **Data Integrity**: 100%
- **Access Control Validation**: 100%
- **Compliance Reporting**: 100%

### Monitoring and Alerting
- **Real-time Monitoring**: Prometheus + Grafana
- **Alert Thresholds**: Configurable via environment variables
- **Notification Channels**: Email, Slack, SMS
- **Escalation Procedures**: Automated escalation after 30 minutes

## Conclusion

This recovery procedures document provides comprehensive guidance for recovering the MINGUS financial application from various failure scenarios. Regular testing and validation of these procedures is essential to ensure they remain effective and compliant with regulatory requirements.

### Maintenance Schedule
- **Monthly**: Review and update procedures
- **Quarterly**: Validate compliance requirements
- **Annually**: Full procedure review and testing
- **After Incidents**: Update procedures based on lessons learned

### Continuous Improvement
- Monitor recovery performance metrics
- Identify areas for improvement
- Update procedures based on new technologies
- Incorporate feedback from recovery exercises

---

**Document Version**: 1.0  
**Last Updated**: [Date]  
**Next Review**: [Date]  
**Approved By**: [Name/Title]
