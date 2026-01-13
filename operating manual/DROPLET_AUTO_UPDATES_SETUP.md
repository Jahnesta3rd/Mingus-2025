# DigitalOcean Droplet Automatic Security Updates

## Automatic Updates Configuration Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **Automatic Security Updates Configured**

---

## Configuration Applied

### Auto-Upgrades Configuration
**File:** `/etc/apt/apt.conf.d/20auto-upgrades`

**Settings:**
- **Update-Package-Lists:** Daily (1)
- **Unattended-Upgrade:** Daily (1)
- **Download-Upgradeable-Packages:** Daily (1)
- **AutocleanInterval:** Weekly (7 days)

### Unattended-Upgrades Configuration
**File:** `/etc/apt/apt.conf.d/50unattended-upgrades`

**Security Updates Only:**
- **Allowed Origins:**
  - `${distro_id}:${distro_codename}-security` (Ubuntu security updates)
  - `${distro_id}ESMApps:${distro_codename}-apps-security` (ESM Apps security)
  - `${distro_id}ESM:${distro_codename}-infra-security` (ESM Infra security)

**Cleanup Settings:**
- **Remove-Unused-Dependencies:** true
- **Remove-New-Unused-Dependencies:** true

**Reboot Settings:**
- **Automatic-Reboot:** false (no automatic reboots)

**Notifications:**
- **Mail:** root (emails sent to root user)

---

## How It Works

### Update Schedule
1. **Daily:** Package lists are updated
2. **Daily:** Security updates are checked and downloaded
3. **Daily:** Security updates are automatically installed
4. **Weekly:** System cleans up unused packages

### Security Updates Only
- ✅ **Only security updates** are installed automatically
- ❌ **Regular updates** are NOT installed automatically
- ✅ **System stability** is maintained

### Automatic Actions
- Downloads security updates
- Installs security updates
- Removes unused dependencies
- Cleans up package cache

---

## Service Status

### Unattended-Upgrades Service
- ✅ **Service:** Enabled and running
- ✅ **Startup:** Enabled on boot
- ✅ **Configuration:** Validated

---

## Configuration Details

### Update Frequency
- **Package Lists:** Updated daily
- **Security Updates:** Checked and installed daily
- **Autoclean:** Runs weekly

### What Gets Updated
- ✅ **Security patches** only
- ✅ **Critical security fixes**
- ✅ **ESM security updates** (if enabled)

### What Does NOT Get Updated
- ❌ Regular package updates
- ❌ Feature updates
- ❌ Non-security updates

### Automatic Reboot
- **Automatic-Reboot:** false
- **Manual reboot required** after kernel updates
- **Prevents unexpected downtime**

---

## Monitoring and Logs

### Check Update Status
```bash
# View unattended-upgrades logs
sudo tail -f /var/log/unattended-upgrades/unattended-upgrades.log

# Check last update
sudo grep "Packages that will be upgraded" /var/log/unattended-upgrades/unattended-upgrades.log | tail -5

# View update history
sudo cat /var/log/unattended-upgrades/history.log
```

### Check Service Status
```bash
# Service status
sudo systemctl status unattended-upgrades

# Check if updates are pending
sudo unattended-upgrade --dry-run
```

### View Configuration
```bash
# Auto-upgrades config
cat /etc/apt/apt.conf.d/20auto-upgrades

# Unattended-upgrades config
cat /etc/apt/apt.conf.d/50unattended-upgrades
```

---

## Manual Update Commands

### Check for Updates
```bash
# Update package lists
sudo apt update

# Check for security updates
sudo apt list --upgradable | grep -i security

# Check for all updates
apt list --upgradable
```

### Manual Security Updates
```bash
# Install security updates manually
sudo apt upgrade -y

# Or use unattended-upgrades manually
sudo unattended-upgrade
```

---

## Email Notifications

### Current Configuration
- **Recipient:** root
- **Location:** `/var/mail/root`

### View Email Notifications
```bash
# Check root's mail
sudo mail

# Or view mail file
sudo cat /var/mail/root | tail -50
```

### Configure Email Forwarding
```bash
# Forward root mail to your email
sudo nano /etc/aliases

# Add:
root: your-email@example.com

# Update aliases
sudo newaliases
```

---

## Important Notes

### ⚠️ Automatic Reboot Disabled
- **Automatic-Reboot:** false
- **Kernel updates require manual reboot**
- **Check for pending reboots:**
  ```bash
  # Check if reboot is needed
  if [ -f /var/run/reboot-required ]; then
    echo "Reboot required!"
    cat /var/run/reboot-required.pkgs
  fi
  ```

### ⚠️ Security Updates Only
- Only security updates are installed automatically
- Regular updates must be installed manually
- This maintains system stability

### ⚠️ Email Notifications
- Emails are sent to root user
- Check `/var/mail/root` for notifications
- Configure email forwarding if needed

---

## Testing Configuration

### Dry Run Test
```bash
# Test without making changes
sudo unattended-upgrade --dry-run --debug

# This shows what would be updated
```

### Manual Run
```bash
# Run unattended-upgrades manually
sudo unattended-upgrade -v

# Verbose output shows what's happening
```

---

## Customization

### Change Update Frequency
```bash
# Edit auto-upgrades config
sudo nano /etc/apt/apt.conf.d/20auto-upgrades

# Change values:
# "1" = daily
# "7" = weekly
# "0" = disable
```

### Enable Automatic Reboot
```bash
# Edit unattended-upgrades config
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Change:
Unattended-Upgrade::Automatic-Reboot "true";

# Add reboot time (optional):
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
```

### Add More Update Sources
```bash
# Edit unattended-upgrades config
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades

# Add to Allowed-Origins:
"${distro_id}:${distro_codename}-updates";
```

---

## Troubleshooting

### Updates Not Installing
```bash
# Check service status
sudo systemctl status unattended-upgrades

# Check logs
sudo tail -50 /var/log/unattended-upgrades/unattended-upgrades.log

# Test manually
sudo unattended-upgrade --dry-run
```

### Service Not Running
```bash
# Start service
sudo systemctl start unattended-upgrades

# Enable on boot
sudo systemctl enable unattended-upgrades

# Check logs
sudo journalctl -u unattended-upgrades -n 50
```

### Check for Pending Updates
```bash
# Check what updates are available
sudo apt list --upgradable

# Check security updates specifically
sudo apt list --upgradable | grep -i security
```

---

## Security Benefits

### ✅ Automatic Protection
- Security patches installed automatically
- System stays up-to-date with security fixes
- Reduces window of vulnerability

### ✅ Minimal Maintenance
- No manual intervention required
- Updates happen in background
- System remains secure automatically

### ✅ Stability Maintained
- Only security updates (not feature updates)
- No automatic reboots
- System remains stable

---

## Integration with Other Security Tools

### Works With:
- ✅ **UFW Firewall** - Protects network access
- ✅ **Fail2ban** - Prevents brute force attacks
- ✅ **SSH Hardening** - Secure remote access
- ✅ **Automatic Updates** - Keeps system patched

**All security layers working together!**

---

## Summary

✅ **Automatic Updates:** Configured and active  
✅ **Security Updates:** Installed automatically  
✅ **Service:** Enabled and running  
✅ **Reboot Policy:** Manual (no automatic reboots)  
✅ **Notifications:** Sent to root user  

**Your droplet will now automatically install security updates!**

---

## Next Steps

1. ✅ **Automatic Updates Configured** - Complete!
2. → **Configure Email Forwarding** - Forward root mail to your email
3. → **Monitor Updates** - Check logs regularly
4. → **Plan Reboots** - Reboot after kernel updates
5. → **Review Updates** - Check what's being updated

---

**Status:** ✅ **Automatic Security Updates Complete - System Will Stay Updated**

