# DigitalOcean Droplet Connection Details

## 🔐 Complete Connection Information

**Last Updated:** January 2026  
**Status:** ✅ All connection methods verified and working

---

## 📍 Server Information

### Basic Details
- **Droplet Name:** `mingus-test`
- **IP Address:** `64.225.16.241`
- **Domain:** `mingusapp.com` (production), `test.mingusapp.com` (test)
- **Hostname:** `Mingus-Test`
- **Operating System:** Ubuntu (Linux kernel 6.8.0-71-generic)
- **Architecture:** x86_64

### System Resources
- **Memory:** 1.9GB total, 1.6GB available
- **Disk:** 48GB total, 46GB free (5% used)
- **Status:** ✅ Active and running

### Application Directory
- **Path:** `/var/www/mingus-app`
- **Frontend:** `/var/www/mingus-app/frontend`
- **Backend:** `/var/www/mingus-app/backend`

---

## 🔑 SSH Connection Methods

### ✅ Method 1: Using SSH Config (Recommended)

**Command:**
```bash
ssh mingus-test
```

**SSH Config Entry (add to `~/.ssh/config`):**
```
Host mingus-test
    HostName 64.225.16.241
    User mingus-app
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes
```

**Why this is best:**
- ✅ Shortest command
- ✅ Automatically uses correct key
- ✅ No need to remember IP or user
- ✅ Works with all SSH tools (scp, rsync, etc.)

---

### ✅ Method 2: Using Domain Name

**Command:**
```bash
ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com
```

**Or for test environment:**
```bash
ssh -i ~/.ssh/mingus_test mingus-app@test.mingusapp.com
```

**Why this works:**
- ✅ Uses domain name (easier to remember)
- ✅ DNS resolves to `64.225.16.241`
- ✅ Works if IP changes (unlikely)

---

### ✅ Method 3: Using IP Address Directly

**Command:**
```bash
ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241
```

**Why this works:**
- ✅ Direct connection (no DNS lookup)
- ✅ Fastest connection method
- ✅ Works even if DNS is down

---

## 🔐 Authentication Details

### SSH Key Information
- **Private Key Location:** `~/.ssh/mingus_test`
- **Public Key Location:** `~/.ssh/mingus_test.pub`
- **Key Type:** ED25519 (most secure)
- **Key Status:** ✅ Added to server's authorized_keys

### User Account
- **Username:** `mingus-app`
- **Full Name:** Mingus Application User
- **Home Directory:** `/home/mingus-app`
- **Groups:** `mingus-app`, `sudo`
- **Sudo Access:** ✅ Passwordless sudo configured

### Security Features
- ✅ **Key-only authentication** (no passwords)
- ✅ **Root login disabled** (security hardening)
- ✅ **User restrictions** (only mingus-app allowed)
- ✅ **Fail2ban** (brute-force protection)
- ✅ **Max auth tries: 3**
- ✅ **Protocol 2 enforced**

---

## ❌ Methods That Will NOT Work

### Root Login (Disabled for Security)

**These commands will FAIL:**
```bash
ssh root@64.225.16.241          # ❌ Permission denied
ssh root@mingusapp.com          # ❌ Permission denied
ssh root@test.mingusapp.com      # ❌ Permission denied
```

**Why they fail:**
- Root login is disabled (`PermitRootLogin no`)
- Only `mingus-app` user is allowed (`AllowUsers mingus-app`)
- This is a security feature

**Solution:** Use `mingus-app` user with sudo for administrative tasks

---

## 🚀 Quick Connection Commands

### Connect to Server
```bash
# Easiest method
ssh mingus-test

# With domain
ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com

# With IP
ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241
```

### Run Commands Remotely
```bash
# Check server uptime
ssh mingus-test "uptime"

# Check disk space
ssh mingus-test "df -h"

# Check running services
ssh mingus-test "sudo systemctl status mingus-backend"
```

### Copy Files to Server
```bash
# Copy file to server
scp -i ~/.ssh/mingus_test file.txt mingus-app@mingusapp.com:~/

# Copy directory to server
scp -i ~/.ssh/mingus_test -r directory/ mingus-app@mingusapp.com:~/

# Copy file from server
scp -i ~/.ssh/mingus_test mingus-app@mingusapp.com:~/file.txt ./
```

### Using SSH Config (if configured)
```bash
# Copy file (using SSH config)
scp file.txt mingus-test:~/

# Copy from server
scp mingus-test:~/file.txt ./
```

---

## 🌐 Web Access

### Production URLs
- **Main Site:** https://mingusapp.com
- **WWW:** https://www.mingusapp.com
- **API:** https://mingusapp.com/api

### Test Environment URLs
- **Test Site:** https://test.mingusapp.com
- **Test API:** https://test.mingusapp.com/api

---

## 📋 Common Tasks

### Navigate to Application Directory
```bash
ssh mingus-test
cd /var/www/mingus-app
```

### Pull Latest Code
```bash
ssh mingus-test
cd /var/www/mingus-app
git pull origin main
```

### Restart Services
```bash
ssh mingus-test
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

### Check Service Status
```bash
ssh mingus-test
sudo systemctl status mingus-backend
sudo systemctl status nginx
```

### View Logs
```bash
ssh mingus-test
# Backend logs
sudo journalctl -u mingus-backend -f

# Nginx logs
sudo tail -f /var/log/nginx/mingusapp.com.access.log
sudo tail -f /var/log/nginx/mingusapp.com.error.log
```

### Use Sudo (Passwordless)
```bash
ssh mingus-test
sudo whoami          # Should return: root
sudo apt update      # Update packages
sudo systemctl restart nginx  # Restart services
```

---

## 🔧 Setup SSH Config (One-Time)

If you haven't set up SSH config yet, add this to `~/.ssh/config`:

```bash
# Edit SSH config
nano ~/.ssh/config

# Add this entry:
Host mingus-test
    HostName 64.225.16.241
    User mingus-app
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes

# Save and exit (Ctrl+X, then Y, then Enter)
```

**Set correct permissions:**
```bash
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/mingus_test
```

---

## 🛠️ Troubleshooting

### Connection Fails

1. **Check SSH key exists:**
   ```bash
   ls -la ~/.ssh/mingus_test
   ```

2. **Check key permissions:**
   ```bash
   chmod 600 ~/.ssh/mingus_test
   ```

3. **Test DNS resolution:**
   ```bash
   dig A mingusapp.com
   # Should return: 64.225.16.241
   ```

4. **Test connectivity:**
   ```bash
   ping 64.225.16.241
   ```

5. **Check SSH config:**
   ```bash
   cat ~/.ssh/config | grep -A 5 mingus-test
   ```

6. **Verbose SSH connection (for debugging):**
   ```bash
   ssh -v mingus-test
   # Shows detailed connection information
   ```

### Permission Denied

- ✅ Make sure you're using `mingus-app` user (not root)
- ✅ Verify SSH key permissions: `chmod 600 ~/.ssh/mingus_test`
- ✅ Check that key is in server's authorized_keys

### Host Key Verification Failed

If you see "Host key verification failed":
```bash
# Remove old host key
ssh-keygen -R 64.225.16.241

# Or remove from known_hosts manually
nano ~/.ssh/known_hosts
# Remove the line with 64.225.16.241
```

---

## 📊 Connection Summary Table

| Method | Command | Status | Notes |
|--------|---------|--------|-------|
| **SSH Config** | `ssh mingus-test` | ✅ Recommended | Easiest, uses config |
| **Domain + User** | `ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com` | ✅ Works | Uses domain name |
| **IP + User** | `ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241` | ✅ Works | Direct IP connection |
| **Root via IP** | `ssh root@64.225.16.241` | ❌ Disabled | Security feature |
| **Root via Domain** | `ssh root@mingusapp.com` | ❌ Disabled | Security feature |

---

## 🔒 Security Notes

### Active Security Features
- ✅ SSH key authentication only (no passwords)
- ✅ Root login disabled
- ✅ User restrictions (only mingus-app)
- ✅ Fail2ban protection
- ✅ Firewall configured (UFW)
- ✅ SSH protocol 2 enforced

### Best Practices
- ✅ Always use SSH key authentication
- ✅ Keep SSH key secure (never share private key)
- ✅ Use `mingus-app` user with sudo (not root)
- ✅ Regularly update server packages
- ✅ Monitor SSH logs for suspicious activity

---

## 📝 Quick Reference Card

**Copy this for easy access:**

```
=== DIGITALOCEAN DROPLET CONNECTION ===

IP Address: 64.225.16.241
Domain: mingusapp.com / test.mingusapp.com
User: mingus-app
SSH Key: ~/.ssh/mingus_test
App Directory: /var/www/mingus-app

Quick Connect:
  ssh mingus-test

Full Command:
  ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241

Web URLs:
  Production: https://mingusapp.com
  Test: https://test.mingusapp.com
```

---

## ✅ Verification Checklist

- [x] ✅ Droplet IP: `64.225.16.241`
- [x] ✅ Domain: `mingusapp.com` / `test.mingusapp.com`
- [x] ✅ SSH User: `mingus-app`
- [x] ✅ SSH Key: `~/.ssh/mingus_test`
- [x] ✅ SSH Config: `mingus-test` host configured
- [x] ✅ Application Directory: `/var/www/mingus-app`
- [x] ✅ Sudo Access: Passwordless configured
- [x] ✅ Security: Root login disabled
- [x] ✅ Connection: Verified and working

---

**Status:** ✅ **All connection details documented and verified**

**Last Updated:** January 2026
