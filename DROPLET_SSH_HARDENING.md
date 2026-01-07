# DigitalOcean Droplet SSH Hardening

## SSH Hardening Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **SSH Configuration Hardened**

---

## Changes Applied

### Security Settings Modified

1. **PermitRootLogin no**
   - Disables root login via SSH
   - Forces use of non-root user (mingus-app)

2. **PasswordAuthentication no**
   - Disables password authentication
   - Only SSH key authentication allowed

3. **PubkeyAuthentication yes**
   - Explicitly enables SSH key authentication

4. **AuthorizedKeysFile .ssh/authorized_keys**
   - Sets standard location for authorized keys

5. **PermitEmptyPasswords no**
   - Prevents empty password logins

6. **ChallengeResponseAuthentication no**
   - Disables challenge-response authentication

7. **UsePAM yes**
   - Enables Pluggable Authentication Modules

8. **X11Forwarding no**
   - Disables X11 forwarding (not needed for server)

9. **MaxAuthTries 3**
   - Limits authentication attempts to 3
   - Helps prevent brute force attacks

10. **ClientAliveInterval 300**
    - Sends keepalive messages every 300 seconds (5 minutes)

11. **ClientAliveCountMax 2**
    - Maximum keepalive messages before disconnecting

### Access Control

12. **AllowUsers mingus-app**
    - Only allows `mingus-app` user to connect via SSH
    - All other users are blocked

13. **Protocol 2**
    - Forces SSH protocol version 2 (more secure)

---

## Backup Created

- **Backup Location:** `/etc/ssh/sshd_config.backup`
- **Original Config:** Preserved for rollback if needed

---

## Verification

### SSH Config Syntax
- ✅ Configuration syntax validated
- ✅ No syntax errors detected

### SSH Service Status
- ✅ SSH service restarted successfully
- ✅ Service running and active

### Connection Test
- ✅ SSH connection verified after changes
- ✅ `mingus-app` user can still connect

---

## Security Improvements

### Before Hardening:
- ❌ Root login enabled
- ❌ Password authentication enabled
- ❌ All users could connect
- ❌ Unlimited authentication attempts

### After Hardening:
- ✅ Root login disabled
- ✅ Password authentication disabled
- ✅ Only `mingus-app` user allowed
- ✅ Limited authentication attempts (3)
- ✅ SSH key authentication only
- ✅ Protocol 2 enforced

---

## Important Notes

### ⚠️ Root Access
- **Root login is now DISABLED**
- You can only connect as `mingus-app` user
- Use `sudo` for administrative tasks

### ⚠️ User Access
- **Only `mingus-app` can connect via SSH**
- Other users (if created) cannot SSH in
- To allow additional users, add them to `AllowUsers` line

### ⚠️ Password Authentication
- **Password authentication is DISABLED**
- Only SSH key authentication works
- Make sure your SSH key is properly configured

---

## Rollback Instructions

If you need to revert the changes:

```bash
# Connect as mingus-app
ssh mingus-app

# Restore backup
sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart sshd
```

---

## Adding Additional Users

To allow additional users to connect via SSH:

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Change:
AllowUsers mingus-app

# To (example):
AllowUsers mingus-app another-user

# Or allow multiple users:
AllowUsers mingus-app user1 user2

# Restart SSH
sudo systemctl restart sshd
```

---

## Connection Methods

### Current Working Connection
```bash
ssh mingus-app
```

### Root Access (No Longer Works)
```bash
# This will FAIL:
ssh root@64.225.16.241
# Error: Permission denied (publickey)
```

### Other Users (Blocked)
```bash
# This will FAIL:
ssh other-user@64.225.16.241
# Error: Access denied
```

---

## Security Checklist

- [x] ✅ Root login disabled
- [x] ✅ Password authentication disabled
- [x] ✅ SSH key authentication only
- [x] ✅ User access restricted (mingus-app only)
- [x] ✅ Authentication attempts limited
- [x] ✅ Protocol 2 enforced
- [x] ✅ X11 forwarding disabled
- [x] ✅ Config backup created
- [x] ✅ SSH service restarted
- [x] ✅ Connection verified

---

## Next Steps

### 1. ✅ SSH Hardening - **COMPLETE!**

### 2. → Configure Firewall (UFW)
Set up firewall rules to restrict network access

### 3. → Configure Fail2ban
Ensure fail2ban is running and configured

### 4. → Application Deployment
Deploy Mingus application as `mingus-app` user

### 5. → Monitor Security
Set up logging and monitoring for security events

---

## Troubleshooting

### If You Get Locked Out

If you lose SSH access:

1. **Use DigitalOcean Console:**
   - Go to DigitalOcean dashboard
   - Access droplet console
   - Restore SSH config from backup

2. **Restore from Backup:**
   ```bash
   # Via console
   sudo cp /etc/ssh/sshd_config.backup /etc/ssh/sshd_config
   sudo systemctl restart sshd
   ```

### If Connection Fails

1. **Check SSH Key:**
   ```bash
   # Verify key is in authorized_keys
   cat ~/.ssh/authorized_keys
   ```

2. **Check User:**
   ```bash
   # Verify user exists
   id mingus-app
   ```

3. **Check SSH Service:**
   ```bash
   sudo systemctl status sshd
   ```

---

## Summary

✅ **SSH Hardening:** Complete  
✅ **Root Login:** Disabled  
✅ **Password Auth:** Disabled  
✅ **User Access:** Restricted to mingus-app  
✅ **Security:** Significantly improved  

**Your droplet SSH configuration is now hardened and secure!**

---

**Status:** ✅ **SSH Hardening Complete - Server is More Secure**

