# SSH Connection Guide - mingusapp.com

## SSH Connection Methods

**Date:** January 8, 2026  
**Server:** 64.225.16.241 (mingusapp.com)  
**Status:** ✅ SSH Configured and Secured

---

## ⚠️ Important Security Note

**Root login is DISABLED** for security reasons. You cannot SSH as root.

**Correct user:** `mingus-app` (with sudo privileges)

---

## ✅ Recommended Connection Methods

### Method 1: Using SSH Config (Easiest)

**Command:**
```bash
ssh mingus-test
```

**Why this works:**
- Uses your configured SSH host (`mingus-test`)
- Automatically uses the correct key (`~/.ssh/mingus_test`)
- Connects as `mingus-app` user
- No need to specify IP or user

**SSH Config Entry:**
```
Host mingus-test
    HostName 64.225.16.241
    User mingus-app
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes
```

---

### Method 2: Using Domain Name

**Command:**
```bash
ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com
```

**Why this works:**
- Uses domain name (mingusapp.com) instead of IP
- DNS resolves to 64.225.16.241
- Specifies user (`mingus-app`) and key file

---

### Method 3: Using IP Address

**Command:**
```bash
ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241
```

**Why this works:**
- Direct IP connection
- Specifies user (`mingus-app`) and key file
- Works even if DNS is down

---

## ❌ Methods That Will NOT Work

### ❌ Root Login (Disabled)

**These commands will FAIL:**
```bash
ssh root@64.225.16.241          # ❌ Permission denied
ssh root@mingusapp.com          # ❌ Permission denied
```

**Why they fail:**
- Root login is disabled (`PermitRootLogin no`)
- Only `mingus-app` user is allowed (`AllowUsers mingus-app`)
- This is a security feature we configured

---

## Quick Reference

| Method | Command | Status |
|--------|---------|--------|
| **SSH Config** | `ssh mingus-test` | ✅ Recommended |
| **Domain + User** | `ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com` | ✅ Works |
| **IP + User** | `ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241` | ✅ Works |
| **Root via IP** | `ssh root@64.225.16.241` | ❌ Disabled |
| **Root via Domain** | `ssh root@mingusapp.com` | ❌ Disabled |

---

## Using Sudo

Once connected, you can use sudo for administrative tasks:

```bash
# Connect
ssh mingus-test

# Use sudo (passwordless)
sudo whoami          # Should return: root
sudo apt update      # Update packages
sudo systemctl status ssh  # Check services
```

**Note:** `mingus-app` has passwordless sudo configured.

---

## SSH Key Information

**Key Location:**
- Private key: `~/.ssh/mingus_test`
- Public key: `~/.ssh/mingus_test.pub`

**Key Type:** ED25519 (most secure)

**Key Status:** ✅ Added to server's authorized_keys

---

## Troubleshooting

### If Connection Fails:

1. **Check SSH key:**
   ```bash
   ls -la ~/.ssh/mingus_test
   ```

2. **Test DNS resolution:**
   ```bash
   dig A mingusapp.com
   # Should return: 64.225.16.241
   ```

3. **Test connectivity:**
   ```bash
   ping 64.225.16.241
   ```

4. **Check SSH config:**
   ```bash
   cat ~/.ssh/config | grep -A 5 mingus-test
   ```

5. **Verbose SSH connection:**
   ```bash
   ssh -v mingus-test
   # Shows detailed connection information
   ```

---

## Security Features Active

Your SSH connection is protected by:

- ✅ **Key-only authentication** (no passwords)
- ✅ **Root login disabled**
- ✅ **User restrictions** (only mingus-app allowed)
- ✅ **Fail2ban** (brute-force protection)
- ✅ **Max auth tries: 3**
- ✅ **Protocol 2 enforced**

---

## Quick Commands

```bash
# Connect (easiest)
ssh mingus-test

# Connect with domain
ssh -i ~/.ssh/mingus_test mingus-app@mingusapp.com

# Connect with IP
ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241

# Run command remotely
ssh mingus-test "uptime"

# Copy file to server
scp -i ~/.ssh/mingus_test file.txt mingus-app@mingusapp.com:~/

# Copy file from server
scp -i ~/.ssh/mingus_test mingus-app@mingusapp.com:~/file.txt ./
```

---

## Summary

**✅ Use this command:**
```bash
ssh mingus-test
```

**❌ Don't use:**
```bash
ssh root@64.225.16.241      # Root login disabled
ssh root@mingusapp.com      # Root login disabled
```

**User:** `mingus-app` (with sudo)  
**Key:** `~/.ssh/mingus_test`  
**Status:** ✅ Ready to connect

---

**Last Updated:** January 8, 2026  
**Status:** ✅ SSH Connection Guide Complete

