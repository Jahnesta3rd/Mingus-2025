# DigitalOcean Droplet Initial Setup

## Setup Completed ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **Initial Setup Complete**

---

## Commands Executed

### 1. System Update
```bash
apt update && apt upgrade -y
```
- ✅ Updated package lists
- ✅ Upgraded all system packages to latest versions

### 2. Essential Tools Installation
```bash
apt install -y ufw fail2ban unattended-upgrades htop curl wget git nano
```

**Installed Packages:**
- ✅ **ufw** - Uncomplicated Firewall (firewall management)
- ✅ **fail2ban** - Intrusion prevention system
- ✅ **unattended-upgrades** - Automatic security updates
- ✅ **htop** - Interactive process viewer
- ✅ **curl** - Command-line HTTP client
- ✅ **wget** - File downloader
- ✅ **git** - Version control system
- ✅ **nano** - Text editor

---

## Installed Tools Overview

### Security Tools

#### UFW (Uncomplicated Firewall)
- Firewall management tool
- Easy to configure and manage
- Next step: Configure firewall rules

#### Fail2ban
- Monitors log files for suspicious activity
- Automatically bans IPs with too many failed login attempts
- Protects against brute force attacks

#### Unattended-Upgrades
- Automatically installs security updates
- Keeps system up-to-date without manual intervention
- Reduces security vulnerabilities

### Utility Tools

#### htop
- Interactive process viewer
- Better than `top` with improved UI
- Usage: `htop`

#### curl & wget
- Download files and test HTTP endpoints
- Essential for web development and testing

#### git
- Version control system
- Needed for deploying code from repositories

#### nano
- User-friendly text editor
- Easier than vi/vim for beginners

---

## Next Steps

### 1. ✅ Initial Setup - **COMPLETE!**

### 2. → Configure Firewall (UFW)
```bash
# Connect to droplet
ssh mingus-test

# Allow SSH (important - do this first!)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Enable firewall
ufw enable

# Check status
ufw status
```

### 3. → Configure Fail2ban
```bash
# Fail2ban is installed but may need configuration
# Check status
systemctl status fail2ban

# Enable and start
systemctl enable fail2ban
systemctl start fail2ban

# Check jail status
fail2ban-client status
```

### 4. → Configure Unattended-Upgrades
```bash
# Check configuration
cat /etc/apt/apt.conf.d/50unattended-upgrades

# Enable automatic updates (usually enabled by default)
# Verify it's running
systemctl status unattended-upgrades
```

### 5. → Create Non-Root User (Security Best Practice)
```bash
# Create new user
adduser mingus

# Add to sudo group
usermod -aG sudo mingus

# Copy SSH key to new user
mkdir -p /home/mingus/.ssh
cp ~/.ssh/authorized_keys /home/mingus/.ssh/
chown -R mingus:mingus /home/mingus/.ssh
chmod 700 /home/mingus/.ssh
chmod 600 /home/mingus/.ssh/authorized_keys

# Test login as new user
# (from your local machine)
ssh -i ~/.ssh/mingus_test mingus@64.225.16.241
```

### 6. → Harden SSH Configuration
```bash
# Edit SSH config
nano /etc/ssh/sshd_config

# Recommended changes:
# - Disable root login: PermitRootLogin no
# - Change SSH port (optional): Port 2222
# - Disable password authentication: PasswordAuthentication no
# - Limit login attempts: MaxAuthTries 3

# Restart SSH service
systemctl restart sshd
```

---

## Verification Commands

### Check Installed Packages
```bash
dpkg -l | grep -E 'ufw|fail2ban|unattended-upgrades|htop|curl|wget|git|nano'
```

### Check System Status
```bash
# System info
uname -a

# Memory usage
free -h

# Disk usage
df -h

# Running processes
htop
```

### Check Services
```bash
# Firewall status
ufw status

# Fail2ban status
systemctl status fail2ban

# Unattended-upgrades status
systemctl status unattended-upgrades
```

---

## Security Checklist

- [x] ✅ System packages updated
- [x] ✅ Security tools installed (ufw, fail2ban, unattended-upgrades)
- [ ] ⏳ Firewall configured
- [ ] ⏳ Fail2ban configured and running
- [ ] ⏳ Unattended-upgrades enabled
- [ ] ⏳ Non-root user created
- [ ] ⏳ SSH hardened
- [ ] ⏳ Root login disabled (after user setup)

---

## Quick Reference

### Connect to Droplet
```bash
ssh mingus-test
```

### Useful Commands
```bash
# View system resources
htop

# Check firewall
ufw status

# Check fail2ban
fail2ban-client status

# Update packages manually
apt update && apt upgrade

# Edit files
nano filename
```

---

## Troubleshooting

### If package installation fails:
```bash
# Update package lists
apt update

# Fix broken packages
apt --fix-broken install

# Try installation again
apt install -y [package-name]
```

### If services don't start:
```bash
# Check service status
systemctl status [service-name]

# View logs
journalctl -u [service-name]

# Start service
systemctl start [service-name]
```

---

## Summary

✅ **Initial Setup:** Complete  
✅ **Security Tools:** Installed  
✅ **Utility Tools:** Installed  
✅ **System:** Updated and ready

**Your droplet is now set up with essential tools and ready for further configuration!**

---

**Status:** ✅ **Initial Setup Complete - Ready for Security Configuration**

