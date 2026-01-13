# Automated Security Reporting Setup

## Daily Security Reports Configured ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **Automated Reporting Active**

---

## Configuration Applied

### 1. Daily Cron Job
**Schedule:** Daily at 8:00 AM UTC  
**Command:** `/home/mingus-app/security-check.sh`  
**Output:** `/home/mingus-app/daily-security-report.txt`

**Cron Entry:**
```
0 8 * * * /home/mingus-app/security-check.sh > /home/mingus-app/daily-security-report.txt 2>&1
```

### 2. Log Rotation
**Configuration:** `/etc/logrotate.d/mingus-security`  
**Settings:**
- **Frequency:** Daily rotation
- **Retention:** 7 days
- **Compression:** Enabled
- **Permissions:** 644 (mingus-app:mingus-app)

---

## How It Works

### Daily Execution
1. **8:00 AM UTC** - Cron job runs automatically
2. **Script Execution** - Security check script runs
3. **Report Generation** - Output saved to `daily-security-report.txt`
4. **Log Rotation** - Old reports rotated daily

### Log Rotation Behavior
- **Daily:** New report overwrites current file
- **Retention:** Keeps 7 days of reports
- **Compression:** Old reports are compressed (.gz)
- **Cleanup:** Reports older than 7 days are deleted

---

## Report Location

### Current Report
- **File:** `/home/mingus-app/daily-security-report.txt`
- **Owner:** mingus-app:mingus-app
- **Permissions:** 644 (readable by user)

### Rotated Reports
- **Location:** `/home/mingus-app/`
- **Format:** `daily-security-report.txt.1.gz`, `daily-security-report.txt.2.gz`, etc.
- **Retention:** 7 compressed files

---

## Viewing Reports

### View Current Report
```bash
# Connect to droplet
ssh mingus-test

# View today's report
cat ~/daily-security-report.txt

# Or with pager
less ~/daily-security-report.txt
```

### View from Local Machine
```bash
# View remotely
ssh mingus-test "cat ~/daily-security-report.txt"

# Download report
scp mingus-test:~/daily-security-report.txt ./
```

### View Rotated Reports
```bash
# List rotated reports
ls -lh ~/daily-security-report.txt*

# View compressed report
zcat ~/daily-security-report.txt.1.gz

# Or decompress and view
gunzip -c ~/daily-security-report.txt.1.gz | less
```

---

## Cron Job Management

### View Cron Jobs
```bash
# List all cron jobs
crontab -l

# Edit cron jobs
crontab -e
```

### Modify Schedule
```bash
# Edit crontab
crontab -e

# Change time (example: 9 AM instead of 8 AM)
# From: 0 8 * * *
# To:   0 9 * * *
```

### Common Cron Schedules
```
0 8 * * *     # Daily at 8:00 AM
0 */6 * * *   # Every 6 hours
0 0 * * 0     # Weekly on Sunday at midnight
0 8 * * 1-5   # Weekdays at 8:00 AM
```

### Remove Cron Job
```bash
# Edit crontab
crontab -e

# Remove the line with security-check.sh
```

---

## Log Rotation Management

### Test Log Rotation
```bash
# Dry run (test without rotating)
sudo logrotate -d /etc/logrotate.d/mingus-security

# Force rotation (for testing)
sudo logrotate -f /etc/logrotate.d/mingus-security
```

### View Log Rotation Status
```bash
# Check logrotate state
sudo cat /var/lib/logrotate/status | grep mingus-security
```

### Modify Retention
```bash
# Edit log rotation config
sudo nano /etc/logrotate.d/mingus-security

# Change rotate value:
rotate 30  # Keep 30 days instead of 7
```

---

## Report Contents

Each daily report contains:

1. **Date/Time** - When the check was run
2. **UFW Status** - Firewall rules and status
3. **Fail2ban Status** - Intrusion prevention status
4. **Failed SSH Attempts** - Recent authentication failures
5. **Current Connections** - Active network connections
6. **System Load** - Server load and uptime
7. **Disk Usage** - Filesystem usage
8. **Memory Usage** - RAM and swap usage

---

## Automation Benefits

### ✅ Regular Monitoring
- Daily security checks without manual intervention
- Consistent monitoring schedule
- Historical data for trend analysis

### ✅ Log Management
- Automatic log rotation
- Compression saves disk space
- Old logs automatically cleaned up

### ✅ Easy Access
- Reports stored in predictable location
- Easy to view or download
- Historical reports available

---

## Email Notifications (Optional)

### Add Email to Reports
```bash
# Edit security-check.sh
nano ~/security-check.sh

# Add at the end:
echo "" >> /tmp/security-report.txt
echo "--- Sending Report ---" >> /tmp/security-report.txt
cat ~/daily-security-report.txt | mail -s "Daily Security Report - $(hostname)" your-email@example.com
```

### Install Mail Client
```bash
# Install mailutils
sudo apt install mailutils

# Configure postfix (if needed)
sudo dpkg-reconfigure postfix
```

---

## Monitoring and Alerts

### Check if Reports Are Running
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
sudo grep CRON /var/log/syslog | tail -10

# Check last report timestamp
ls -lh ~/daily-security-report.txt
```

### Set Up Alerts
```bash
# Create alert script
cat > ~/check-security-alerts.sh << 'EOF'
#!/bin/bash
# Check for failed SSH attempts
FAILED=$(grep "Failed password" ~/daily-security-report.txt | wc -l)
if [ $FAILED -gt 10 ]; then
    echo "ALERT: High number of failed SSH attempts: $FAILED"
fi

# Check disk usage
DISK=$(df -h / | awk 'NR==2 {print $5}' | sed 's/%//')
if [ $DISK -gt 80 ]; then
    echo "ALERT: Disk usage is ${DISK}%"
fi
EOF

chmod +x ~/check-security-alerts.sh
```

---

## Troubleshooting

### Reports Not Generating
```bash
# Check cron service
sudo systemctl status cron

# Check cron logs
sudo grep security-check /var/log/syslog

# Test script manually
~/security-check.sh > ~/daily-security-report.txt 2>&1
```

### Log Rotation Not Working
```bash
# Test log rotation
sudo logrotate -d /etc/logrotate.d/mingus-security

# Check logrotate service
sudo systemctl status logrotate

# Force rotation
sudo logrotate -f /etc/logrotate.d/mingus-security
```

### Permission Issues
```bash
# Fix report file permissions
chmod 644 ~/daily-security-report.txt
chown mingus-app:mingus-app ~/daily-security-report.txt
```

---

## Summary

✅ **Cron Job:** Configured (daily at 8 AM)  
✅ **Log Rotation:** Configured (7 day retention)  
✅ **Report Location:** `/home/mingus-app/daily-security-report.txt`  
✅ **Automation:** Active and working  

**Your droplet will now generate daily security reports automatically!**

---

## Next Steps

1. ✅ **Automated Reporting** - Complete!
2. → **Monitor Reports** - Check reports regularly
3. → **Set Up Alerts** - Configure email notifications (optional)
4. → **Review Trends** - Analyze historical data
5. → **Adjust Schedule** - Modify timing if needed

---

**Status:** ✅ **Automated Security Reporting Complete - Daily Reports Active**

