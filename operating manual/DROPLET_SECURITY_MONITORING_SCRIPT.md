# Security Monitoring Script

## Security Check Script Created ✅

**Date:** January 7, 2026  
**Location:** `/home/mingus-app/security-check.sh`  
**Status:** ✅ **Script Created and Tested**

---

## Script Details

### Location
- **Path:** `/home/mingus-app/security-check.sh`
- **Owner:** mingus-app:mingus-app
- **Permissions:** 755 (executable)
- **Size:** ~500 bytes

### Script Contents

The script provides a comprehensive security status check including:

1. **Date/Time Stamp** - When the check was run
2. **UFW Status** - Firewall rules and status
3. **Fail2ban Status** - Intrusion prevention status
4. **Failed SSH Attempts** - Recent authentication failures
5. **Current Connections** - Active network connections
6. **System Load** - Server load and uptime
7. **Disk Usage** - Filesystem usage
8. **Memory Usage** - RAM and swap usage

---

## Usage

### Run the Script
```bash
# Connect to droplet
ssh mingus-test

# Run security check
./security-check.sh
```

### Run from Local Machine
```bash
# Execute remotely
ssh mingus-test "./security-check.sh"
```

### Schedule Regular Checks
```bash
# Add to crontab for daily checks
crontab -e

# Add line (runs daily at 9 AM):
0 9 * * * /home/mingus-app/security-check.sh >> /home/mingus-app/security-logs/security-check-$(date +\%Y-\%m-\%d).log 2>&1
```

---

## Script Output

The script displays:

### UFW Status
- Firewall rules
- Active/inactive status
- Allowed ports and sources

### Fail2ban Status
- Active jails
- Banned IPs
- Failed attempt counts

### Failed SSH Attempts
- Recent authentication failures
- IP addresses attempting access
- Timestamps

### Current Connections
- Active network connections
- Listening ports
- Process information

### System Metrics
- System load average
- Uptime
- Disk usage
- Memory usage

---

## Customization

### Add More Checks
```bash
# Edit the script
nano ~/security-check.sh

# Add additional checks:
echo "--- Running Processes ---"
ps aux | head -10

echo "--- Recent Logins ---"
last -10
```

### Email Notifications
```bash
# Add email sending
echo "--- Sending Report ---"
./security-check.sh | mail -s "Daily Security Check" your-email@example.com
```

### Log Rotation
```bash
# Create log directory
mkdir -p ~/security-logs

# Run with logging
./security-check.sh >> ~/security-logs/security-$(date +%Y-%m-%d).log
```

---

## Automation

### Daily Automated Checks

Create a cron job:
```bash
# Edit crontab
crontab -e

# Add daily check at 9 AM
0 9 * * * /home/mingus-app/security-check.sh >> /home/mingus-app/security-logs/daily-$(date +\%Y-\%m-\%d).log 2>&1
```

### Weekly Summary
```bash
# Weekly summary script
cat > ~/weekly-security-summary.sh << 'EOF'
#!/bin/bash
echo "=== WEEKLY SECURITY SUMMARY ===" > /tmp/weekly-summary.txt
echo "Week of: $(date)" >> /tmp/weekly-summary.txt
echo "" >> /tmp/weekly-summary.txt
cat ~/security-logs/daily-*.log >> /tmp/weekly-summary.txt
# Email or display summary
cat /tmp/weekly-summary.txt
EOF

chmod +x ~/weekly-security-summary.sh
```

---

## Troubleshooting

### Script Not Executable
```bash
# Fix permissions
chmod +x ~/security-check.sh
```

### Sudo Permission Issues
```bash
# Verify sudo access
sudo -l

# Check sudoers file
sudo cat /etc/sudoers.d/mingus-app
```

### Missing Commands
```bash
# Install missing tools
sudo apt install net-tools  # for netstat
```

---

## Security Best Practices

### Regular Monitoring
- Run script daily
- Review failed SSH attempts
- Check banned IPs
- Monitor system resources

### Alert Thresholds
- Set up alerts for:
  - High number of failed attempts
  - Unusual network connections
  - High system load
  - Low disk space

### Log Retention
- Keep logs for 30-90 days
- Rotate logs regularly
- Archive old logs

---

## Summary

✅ **Script Created:** `/home/mingus-app/security-check.sh`  
✅ **Permissions:** Set correctly  
✅ **Tested:** Working  
✅ **Ready:** For regular security monitoring  

**You can now run `./security-check.sh` anytime to check your droplet's security status!**

---

**Status:** ✅ **Security Monitoring Script Complete - Ready to Use**

