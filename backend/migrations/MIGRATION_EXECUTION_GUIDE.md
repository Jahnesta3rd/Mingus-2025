# Email Verification System Migration Execution Guide

## 🚨 **CRITICAL SAFETY INFORMATION**

**⚠️  NEVER run migrations directly on production without thorough testing!**
**⚠️  Always create complete database backups before any migration!**
**⚠️  Test on development/staging environments first!**

## 📋 **Pre-Migration Checklist**

### 1. **Environment Preparation**
- [ ] **Development Environment**: Test migration on local/dev database
- [ ] **Staging Environment**: Test migration on staging database
- [ ] **Production Environment**: Schedule maintenance window
- [ ] **Team Notification**: Inform all team members of migration

### 2. **Database Backup Strategy**
- [ ] **Full Database Backup**: `pg_dump` of entire database
- [ **Point-in-Time Recovery**: Enable WAL archiving if possible
- [ ] **Backup Verification**: Test backup restoration process
- [ ] **Backup Storage**: Store backups in multiple locations

### 3. **System Requirements**
- [ ] **PostgreSQL Version**: 15+ (recommended: 16+)
- [ ] **Disk Space**: Ensure 2x current database size available
- [ ] **Memory**: Sufficient RAM for migration operations
- [ ] **Network**: Stable connection to database

### 4. **Application Preparation**
- [ ] **Code Deployment**: Deploy new code before migration
- [ ] **Feature Flags**: Enable email verification features
- [ ] **Monitoring**: Set up monitoring for migration process
- [ ] **Rollback Plan**: Prepare rollback procedures

## 🔧 **Migration Execution Steps**

### **Phase 1: Development Environment**

#### Step 1: Test Migration Script
```bash
# Install required dependencies
pip install psycopg2-binary

# Test migration script (dry run)
python backend/migrations/execute_email_verification_migration.py --env development --dry-run

# Verify output and check for any errors
```

#### Step 2: Execute Development Migration
```bash
# Run actual migration on development
python backend/migrations/execute_email_verification_migration.py --env development --execute

# Verify migration success
python backend/migrations/execute_email_verification_migration.py --env development --dry-run
```

#### Step 3: Test Application Functionality
```bash
# Start your Flask application
flask run

# Test email verification endpoints
curl -X POST http://localhost:5000/api/email-verification/send \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "verification_type": "signup"}'

# Verify database changes
psql -d your_dev_database -c "SELECT COUNT(*) FROM users WHERE email_verified = FALSE;"
```

### **Phase 2: Staging Environment**

#### Step 1: Deploy to Staging
```bash
# Deploy code to staging environment
git checkout staging
git merge feature/email-verification-system

# Deploy to staging server
# (Follow your deployment process)
```

#### Step 2: Execute Staging Migration
```bash
# Connect to staging database
export DATABASE_URL="postgresql://user:pass@staging-db:5432/staging_db"

# Run migration (dry run first)
python backend/migrations/execute_email_verification_migration.py --env staging --dry-run

# Execute migration
python backend/migrations/execute_email_verification_migration.py --env staging --execute
```

#### Step 3: Staging Validation
```bash
# Run comprehensive tests
pytest backend/tests/test_email_verification_system.py -v

# Test email verification flow end-to-end
# Create test user, send verification, verify email, etc.
```

### **Phase 3: Production Environment**

#### Step 1: Production Preparation
```bash
# Schedule maintenance window (recommended: 2-4 hours)
# Notify users of scheduled maintenance
# Prepare rollback procedures
```

#### Step 2: Production Backup
```bash
# Create full database backup
pg_dump -h production-db -U username -d production_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Verify backup size and integrity
ls -lh backup_*.sql
pg_restore --list backup_*.sql | head -20
```

#### Step 3: Production Migration
```bash
# Deploy code to production
git checkout production
git merge feature/email-verification-system

# Deploy to production server
# (Follow your deployment process)

# Execute migration (dry run first)
python backend/migrations/execute_email_verification_migration.py --env production --dry-run

# Execute migration
python backend/migrations/execute_email_verification_migration.py --env production --execute
```

#### Step 4: Production Validation
```bash
# Verify migration success
python backend/migrations/execute_email_verification_migration.py --env production --dry-run

# Check application health
curl https://your-production-domain.com/api/email-verification/health

# Monitor application logs for errors
tail -f /var/log/your-app/application.log
```

## 📊 **Migration Validation Queries**

### **1. Verify Column Addition**
```sql
-- Check if email_verified column exists
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'email_verified';

-- Verify all users have the column
SELECT COUNT(*) as total_users,
       COUNT(email_verified) as users_with_column,
       COUNT(CASE WHEN email_verified = FALSE THEN 1 END) as unverified_users
FROM users;
```

### **2. Verify Backup Table**
```sql
-- Check backup table integrity
SELECT COUNT(*) as backup_count FROM users_backup_010;
SELECT COUNT(*) as current_count FROM users;

-- Compare backup vs current data
SELECT 
    (SELECT COUNT(*) FROM users_backup_010) as backup_count,
    (SELECT COUNT(*) FROM users) as current_count,
    (SELECT COUNT(*) FROM users_backup_010) - (SELECT COUNT(*) FROM users) as difference;
```

### **3. Verify New Tables**
```sql
-- Check if all tables were created
SELECT table_name 
FROM information_schema.tables 
WHERE table_name LIKE 'email_verification%'
ORDER BY table_name;

-- Verify table structures
\d email_verifications
\d email_verification_audit_log
\d email_verification_settings
```

### **4. Verify Indexes**
```sql
-- Check index creation
SELECT indexname, tablename, indexdef
FROM pg_indexes 
WHERE tablename LIKE 'email_verification%'
ORDER BY tablename, indexname;

-- Check user table indexes
SELECT indexname, tablename, indexdef
FROM pg_indexes 
WHERE tablename = 'users' AND indexname LIKE '%email_verified%';
```

### **5. Verify Functions and Triggers**
```sql
-- Check function creation
SELECT proname, prosrc 
FROM pg_proc 
WHERE proname LIKE '%email_verification%';

-- Check trigger creation
SELECT tgname, tgrelid::regclass, tgfoid::regproc
FROM pg_trigger 
WHERE tgname LIKE '%verification%';
```

## 🔄 **Rollback Procedures**

### **Immediate Rollback (If Migration Fails)**
```bash
# Stop the migration script if it's running
# Check migration status
python backend/migrations/execute_email_verification_migration.py --env production --dry-run

# If rollback is needed
python backend/migrations/execute_email_verification_migration.py --env production --rollback
```

### **Manual Rollback (If Script Fails)**
```sql
-- Connect to production database
-- Check current state
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'email_verified';

-- If column exists, remove it
ALTER TABLE users DROP COLUMN IF EXISTS email_verified;

-- Drop new tables
DROP TABLE IF EXISTS email_verification_analytics CASCADE;
DROP TABLE IF EXISTS email_verification_reminders CASCADE;
DROP TABLE IF EXISTS email_verification_settings CASCADE;
DROP TABLE IF EXISTS email_verification_audit_log CASCADE;
DROP TABLE IF EXISTS email_verifications CASCADE;

-- Restore from backup if needed
-- (This should be done carefully and may require downtime)
```

### **Data Recovery (If Rollback Fails)**
```sql
-- If users table is corrupted, restore from backup
-- WARNING: This will cause data loss of any changes made after migration

-- Rename current users table
ALTER TABLE users RENAME TO users_corrupted;

-- Restore from backup
CREATE TABLE users AS SELECT * FROM users_backup_010;

-- Verify restoration
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM users_backup_010;
```

## 📈 **Performance Optimization**

### **1. Index Optimization**
```sql
-- Analyze table statistics after migration
ANALYZE users;
ANALYZE email_verifications;
ANALYZE email_verification_audit_log;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes 
WHERE tablename LIKE 'email_verification%'
ORDER BY idx_scan DESC;
```

### **2. Query Performance**
```sql
-- Monitor slow queries
SELECT query, calls, total_time, mean_time
FROM pg_stat_statements 
WHERE query LIKE '%email_verification%'
ORDER BY mean_time DESC
LIMIT 10;
```

### **3. Maintenance Tasks**
```sql
-- Schedule regular maintenance
-- Add to your crontab or use pg_cron extension

-- Daily: Update statistics
ANALYZE email_verifications;
ANALYZE email_verification_audit_log;

-- Weekly: Clean up old audit logs (if needed)
DELETE FROM email_verification_audit_log 
WHERE created_at < NOW() - INTERVAL '90 days';

-- Monthly: Reindex if needed
REINDEX TABLE email_verifications;
```

## 🚨 **Troubleshooting Common Issues**

### **1. Migration Script Fails**
```bash
# Check error logs
tail -f /var/log/your-app/migration.log

# Verify database connectivity
psql -h your-db-host -U username -d your-db -c "SELECT 1;"

# Check disk space
df -h

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-*.log
```

### **2. Column Already Exists**
```sql
-- Check if column exists
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'users' AND column_name = 'email_verified';

-- If it exists, check its properties
\d users
```

### **3. Foreign Key Constraint Errors**
```sql
-- Check for orphaned records
SELECT ev.user_id, ev.email
FROM email_verifications ev
LEFT JOIN users u ON ev.user_id = u.id
WHERE u.id IS NULL;

-- Fix orphaned records (if any)
DELETE FROM email_verifications 
WHERE user_id NOT IN (SELECT id FROM users);
```

### **4. Performance Issues**
```sql
-- Check for missing indexes
EXPLAIN ANALYZE SELECT * FROM email_verifications WHERE user_id = 1;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public' AND tablename LIKE 'email_verification%';
```

## 📞 **Emergency Contacts**

### **Database Administrator**
- **Name**: [Your DBA Name]
- **Phone**: [Phone Number]
- **Email**: [Email Address]

### **System Administrator**
- **Name**: [Your SysAdmin Name]
- **Phone**: [Phone Number]
- **Email**: [Email Address]

### **Application Developer**
- **Name**: [Your Name]
- **Phone**: [Phone Number]
- **Email**: [Email Address]

## 📝 **Post-Migration Checklist**

### **1. Application Testing**
- [ ] **Email Verification Flow**: Test complete signup flow
- [ ] **Email Change Flow**: Test email change verification
- [ ] **Resend Functionality**: Test verification email resend
- [ ] **Rate Limiting**: Verify rate limiting is working
- [ ] **Audit Logging**: Check audit log entries

### **2. Performance Monitoring**
- [ ] **Response Times**: Monitor API response times
- [ ] **Database Performance**: Check query execution times
- [ ] **Email Delivery**: Monitor email delivery success rates
- [ ] **Error Rates**: Monitor error rates and types

### **3. Data Validation**
- [ ] **User Counts**: Verify user counts match expectations
- [ ] **Verification Status**: Check verification status distribution
- [ ] **Audit Logs**: Verify audit log completeness
- [ ] **Backup Integrity**: Verify backup table integrity

### **4. Documentation Update**
- [ ] **API Documentation**: Update API documentation
- [ ] **User Guide**: Update user documentation
- [ ] **Admin Guide**: Update administrative procedures
- [ ] **Runbook**: Update operational runbooks

## 🎯 **Success Criteria**

The migration is considered successful when:

1. ✅ **All existing users have `email_verified = FALSE`**
2. ✅ **New email verification tables are created and accessible**
3. ✅ **All indexes are created and functional**
4. ✅ **Application can send and verify emails**
5. ✅ **Audit logging is working correctly**
6. ✅ **Performance is within acceptable limits**
7. ✅ **Rollback procedures are tested and documented**

## 🔚 **Conclusion**

This migration guide provides a comprehensive approach to safely implementing the email verification system. Remember:

- **Always test on development/staging first**
- **Create complete backups before production migration**
- **Monitor the migration process closely**
- **Have rollback procedures ready**
- **Validate everything thoroughly after migration**

If you encounter any issues not covered in this guide, refer to the troubleshooting section or contact the emergency contacts listed above.

---

**Last Updated**: [Current Date]
**Version**: 1.0.0
**Author**: MINGUS Development Team
