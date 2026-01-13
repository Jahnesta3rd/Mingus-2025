# DigitalOcean Droplet Fail2ban Configuration

## Fail2ban Configuration Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **Fail2ban Configured and Active**

---

## Configuration Applied

### Jail Configuration File
**Location:** `/etc/fail2ban/jail.local`

### Default Settings
- **bantime:** 3600 seconds (1 hour)
- **findtime:** 600 seconds (10 minutes)
- **maxretry:** 3 attempts
- **backend:** systemd
- **destemail:** your-email@domain.com (update with real email)
- **sendername:** Mingus Test Server
- **mta:** sendmail

### SSH Jail Settings
- **enabled:** true
- **port:** ssh (port 22)
- **filter:** sshd
- **logpath:** /var/log/auth.log
- **maxretry:** 3 attempts
- **bantime:** 3600 seconds (1 hour)
- **findtime:** 600 seconds (10 minutes)

### Disabled Jails
- **apache:** disabled
- **nginx:** disabled
- **postfix:** disabled

---

## How Fail2ban Works

### Protection Mechanism
1. **Monitors Logs:** Watches `/var/log/auth.log` for failed login attempts
2. **Tracks Attempts:** Counts failed attempts within the findtime window
3. **Bans IPs:** When maxretry is reached, bans the IP address
4. **Auto-Unban:** IP is unbanned after bantime expires

### Example Scenario
- **3 failed SSH attempts** within 10 minutes
- **IP gets banned** for 1 hour
- **After 1 hour**, IP is automatically unbanned

---

## Current Status

### Service Status
- ✅ **Service:** Enabled and running
- ✅ **Startup:** Enabled on boot
- ✅ **SSH Jail:** Active and monitoring

### Active Jails
- **sshd:** Monitoring SSH login attempts

---

## Configuration Details

### Ban Duration
- **bantime = 3600** (1 hour)
  - IPs are banned for 1 hour after exceeding maxretry

### Detection Window
- **findtime = 600** (10 minutes)
  - Failed attempts are counted within a 10-minute window

### Retry Limit
- **maxretry = 3**
  - 3 failed attempts trigger a ban

### Log Monitoring
- **logpath = /var/log/auth.log**
  - Monitors authentication log for SSH attempts

---

## Fail2ban Management Commands

### Check Status
```bash
# Overall status
sudo fail2ban-client status

# Specific jail status
sudo fail2ban-client status sshd

# List all jails
sudo fail2ban-client status | grep "Jail list"
```

### View Banned IPs
```bash
# View banned IPs for SSH jail
sudo fail2ban-client get sshd banned

# View all banned IPs
sudo fail2ban-client status sshd | grep "Banned IP"
```

### Manual IP Management
```bash
# Ban an IP manually
sudo fail2ban-client set sshd banip 192.168.1.100

# Unban an IP manually
sudo fail2ban-client set sshd unbanip 192.168.1.100

# Unban all IPs
sudo fail2ban-client unban --all
```

### Service Management
```bash
# Restart fail2ban
sudo systemctl restart fail2ban

# Stop fail2ban
sudo systemctl stop fail2ban

# Start fail2ban
sudo systemctl start fail2ban

# Check logs
sudo journalctl -u fail2ban -f
```

---

## Testing Fail2ban

### Test Ban (Careful!)
```bash
# From another machine, try to SSH with wrong password 3 times
# The IP should get banned after 3 attempts

# Check if IP is banned
sudo fail2ban-client status sshd
```

### View Fail2ban Logs
```bash
# Real-time log monitoring
sudo tail -f /var/log/fail2ban.log

# Check recent bans
sudo grep "Ban" /var/log/fail2ban.log | tail -10
```

---

## Email Notifications

### Current Configuration
- **Email:** your-email@domain.com (placeholder - update this!)
- **Sender:** Mingus Test Server
- **MTA:** sendmail

### ⚠️ Update Email Address
To receive email notifications, update the email in the config:

```bash
# Edit config
sudo nano /etc/fail2ban/jail.local

# Change:
destemail = your-email@domain.com

# To your real email:
destemail = your-real-email@example.com

# Restart fail2ban
sudo systemctl restart fail2ban
```

### Email Requirements
- **sendmail** must be installed and configured
- Or configure a different MTA (postfix, etc.)
- For production, consider using a proper email service

---

## Integration with UFW

Fail2ban works with UFW:

1. **UFW:** Controls which ports are open
2. **Fail2ban:** Monitors logs and temporarily bans malicious IPs

Both provide layered security:
- **UFW:** First line of defense (firewall)
- **Fail2ban:** Second line of defense (intrusion prevention)

---

## Customization Options

### Adjust Ban Time
```bash
# Edit config
sudo nano /etc/fail2ban/jail.local

# Change bantime (in seconds)
# 3600 = 1 hour
# 7200 = 2 hours
# 86400 = 24 hours

# Restart
sudo systemctl restart fail2ban
```

### Adjust Retry Limit
```bash
# Change maxretry
# Lower = more strict (bans faster)
# Higher = more lenient (allows more attempts)

# In jail.local:
maxretry = 5  # Allow 5 attempts instead of 3
```

### Add More Jails
```bash
# Example: Enable nginx jail
sudo nano /etc/fail2ban/jail.local

# Change:
[nginx]
enabled = true

# Restart
sudo systemctl restart fail2ban
```

---

## Troubleshooting

### Fail2ban Not Starting
```bash
# Check service status
sudo systemctl status fail2ban

# Check logs
sudo journalctl -u fail2ban -n 50

# Test configuration
sudo fail2ban-client -t
```

### IP Not Getting Banned
```bash
# Check if jail is active
sudo fail2ban-client status sshd

# Check log path
sudo ls -la /var/log/auth.log

# Verify log format
sudo tail -20 /var/log/auth.log
```

### False Positives
```bash
# If your IP gets banned incorrectly
# Unban it manually:
sudo fail2ban-client set sshd unbanip YOUR_IP

# Add to whitelist (edit jail.local):
[DEFAULT]
ignoreip = 127.0.0.1/8 ::1 YOUR_TRUSTED_IP
```

---

## Security Best Practices

### ✅ Current Configuration
- SSH jail enabled and monitoring
- Reasonable ban time (1 hour)
- Appropriate retry limit (3 attempts)
- Monitoring authentication logs

### 🔒 Additional Recommendations

1. **Whitelist Your IP:**
   ```bash
   # Add to jail.local [DEFAULT] section
   ignoreip = 127.0.0.1/8 ::1 YOUR_IP_ADDRESS
   ```

2. **Enable Email Notifications:**
   - Update email address
   - Configure MTA properly
   - Monitor ban notifications

3. **Monitor Regularly:**
   ```bash
   # Check banned IPs weekly
   sudo fail2ban-client status sshd
   ```

4. **Review Logs:**
   ```bash
   # Check for patterns
   sudo grep "Ban" /var/log/fail2ban.log
   ```

---

## Summary

✅ **Fail2ban:** Configured and active  
✅ **SSH Jail:** Monitoring authentication attempts  
✅ **Protection:** Automatic IP banning after 3 failed attempts  
✅ **Ban Duration:** 1 hour  
✅ **Integration:** Works with UFW firewall  

**Your droplet is now protected against brute force attacks!**

---

## Next Steps

1. ✅ **Fail2ban Configured** - Complete!
2. → **Update Email Address** - Set real email for notifications
3. → **Whitelist Your IP** - Prevent accidental bans
4. → **Monitor Activity** - Check logs regularly
5. → **Test Protection** - Verify fail2ban is working

---

**Status:** ✅ **Fail2ban Configuration Complete - Intrusion Prevention Active**

