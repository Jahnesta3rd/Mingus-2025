# DigitalOcean Droplet User Setup

## User Creation Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **User Created and Configured**

---

## User Created

### User Details
- **Username:** `mingus-app`
- **Full Name:** Mingus Application User
- **Home Directory:** `/home/mingus-app`
- **Groups:** `mingus-app`, `sudo`
- **SSH Access:** ✅ Configured

---

## Setup Commands Executed

### 1. Create User
```bash
adduser --gecos 'Mingus Application User' --disabled-password mingus-app
```
- ✅ User created with full name
- ✅ Password authentication disabled (SSH key only)

### 2. Add to Sudo Group
```bash
usermod -aG sudo mingus-app
```
- ✅ User added to sudo group
- ✅ Can run administrative commands with `sudo`

### 3. SSH Directory Setup
```bash
mkdir -p /home/mingus-app/.ssh
cp /root/.ssh/authorized_keys /home/mingus-app/.ssh/
chown -R mingus-app:mingus-app /home/mingus-app/.ssh
chmod 700 /home/mingus-app/.ssh
chmod 600 /home/mingus-app/.ssh/authorized_keys
```
- ✅ SSH directory created
- ✅ SSH key copied from root
- ✅ Permissions set correctly (700 for directory, 600 for key)

---

## Verification

### User Information
- **User ID:** Verified
- **Groups:** `mingus-app`, `sudo` ✅
- **Home Directory:** `/home/mingus-app` ✅

### SSH Access
- **SSH Directory:** `/home/mingus-app/.ssh` ✅
- **Authorized Keys:** Present ✅
- **Permissions:** Correct (700/600) ✅
- **Connection Test:** Successful ✅

---

## Connection Methods

### Method 1: Using SSH Config (Recommended) ✅

SSH config has been updated automatically. You can now connect:
```bash
ssh mingus-app
```

**SSH Config Entry:**
```
Host mingus-app
    HostName 64.225.16.241
    User mingus-app
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes
```

### Method 2: Direct Connection
```bash
ssh -i ~/.ssh/mingus_test mingus-app@64.225.16.241
```

---

## Security Notes

### ✅ Security Features
- Password authentication disabled (SSH key only)
- User has sudo privileges (can run admin commands)
- SSH key properly configured
- Correct file permissions set

### ✅ Passwordless Sudo Configured
- User can run sudo commands without password
- Configured in `/etc/sudoers.d/mingus-app`
- Verified and working ✅

### ⚠️ Security Recommendations

1. **Disable Root Login** (after verifying user works):
   ```bash
   # Edit SSH config
   sudo nano /etc/ssh/sshd_config
   
   # Change:
   PermitRootLogin no
   
   # Restart SSH
   sudo systemctl restart sshd
   ```

2. **Set Password for Emergency Access** (optional):
   ```bash
   sudo passwd mingus-app
   ```
   (Only if you want password fallback)

3. **Configure SSH Key Only** (already done):
   - Password authentication disabled ✅
   - SSH key authentication enabled ✅

---

## Next Steps

### 1. ✅ User Created - **COMPLETE!**

### 2. → Test Sudo Access
```bash
# Connect as mingus-app
ssh mingus-app

# Test sudo
sudo whoami
# Should output: root

# Test system command
sudo apt update
```

### 3. → Update SSH Config (Local)
Add the new user to your local SSH config for easier access.

### 4. → Disable Root Login (Optional)
After verifying everything works, disable root SSH login for security.

### 5. → Application Deployment
Deploy Mingus application as the `mingus-app` user.

---

## User Management Commands

### Switch to User
```bash
# From root
su - mingus-app

# Or connect directly via SSH
ssh mingus-app
```

### Check User Info
```bash
id mingus-app
groups mingus-app
```

### Remove User (if needed)
```bash
sudo userdel -r mingus-app
```

---

## File Permissions Reference

### SSH Directory
```
/home/mingus-app/.ssh          → 700 (drwx------)
/home/mingus-app/.ssh/authorized_keys → 600 (-rw-------)
```

### Home Directory
```
/home/mingus-app               → 755 (drwxr-xr-x)
```

---

## Troubleshooting

### If SSH Connection Fails:
1. Check key permissions: `chmod 600 ~/.ssh/mingus_test`
2. Verify authorized_keys: `cat /home/mingus-app/.ssh/authorized_keys`
3. Check SSH service: `sudo systemctl status sshd`
4. Test with verbose: `ssh -v mingus-app`

### If Sudo Doesn't Work:
1. Verify group membership: `groups mingus-app`
2. Check sudoers: `sudo visudo`
3. Test sudo: `sudo -v`

---

## Summary

✅ **User Created:** mingus-app  
✅ **Sudo Access:** Configured  
✅ **SSH Access:** Working  
✅ **Security:** SSH key only, no password  

**The `mingus-app` user is ready for application deployment!**

---

**Status:** ✅ **User Setup Complete - Ready for Application Deployment**

