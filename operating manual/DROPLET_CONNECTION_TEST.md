# DigitalOcean Droplet Connection Test

## Prerequisites

Before testing the connection, ensure:
- ✅ Droplet is created in DigitalOcean
- ✅ SSH key "Mingus Test Environment Key" is added to the droplet
- ✅ Droplet IP address is known
- ✅ SSH config is updated with the droplet IP

---

## Step 1: Update SSH Config with Droplet IP

If you haven't already, update `~/.ssh/config` with your actual droplet IP:

```bash
# Option 1: Edit manually
nano ~/.ssh/config
# Replace [DROPLET-IP] with your actual IP

# Option 2: Use sed (replace YOUR_IP with actual IP)
sed -i '' 's/\[DROPLET-IP\]/YOUR_ACTUAL_IP/g' ~/.ssh/config
```

**Example SSH config entry:**
```
Host mingus-test
    HostName 157.230.123.45  # ← Your actual droplet IP
    User root
    IdentityFile ~/.ssh/mingus_test
    IdentitiesOnly yes
```

---

## Step 2: Test SSH Connection

### Method 1: Using SSH Config (Recommended)
```bash
ssh mingus-test
```

### Method 2: Direct Connection with Key
```bash
ssh -i ~/.ssh/mingus_test root@[YOUR-DROPLET-IP]
```

Replace `[YOUR-DROPLET-IP]` with your actual droplet IP address.

---

## Expected Output on Successful Connection

```
The authenticity of host '[IP] ([IP])' can't be established.
ED25519 key fingerprint is SHA256:xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx.
This key is not known by any other names
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '[IP]' (ED25519) to the list of known hosts.

Welcome to Ubuntu 22.04 LTS (GNU/Linux 5.15.0-xxx-generic x86_64)

 * Documentation:  https://help.ubuntu.com
 * Management:     https://landscape.canonical.com
 * Support:        https://ubuntu.com/advantage

  System information as of [DATE]

  System load:  0.0                Processes:             123
  Usage of /:   2.0% of 160.00GB   Users logged in:       1
  Memory usage: 5%                 IPv4 address for eth0: [IP]
  Swap usage:   0%

0 updates can be applied immediately.

root@mingus-test:~#
```

---

## Verification Checklist

After successful connection, verify:

### ✅ Droplet Information
- [ ] Hostname matches: `mingus-test` or `ubuntu-xxx`
- [ ] Ubuntu version: 22.04 LTS
- [ ] System resources match expected (4 vCPUs, 8GB RAM)
- [ ] Disk space: 160GB available

### ✅ SSH Authentication
- [ ] Connected without password prompt
- [ ] Using SSH key authentication
- [ ] Logged in as `root` user

### ✅ Network Configuration
- [ ] IPv4 address visible
- [ ] Can ping external hosts: `ping -c 3 8.8.8.8`
- [ ] DNS resolution works: `nslookup google.com`

### ✅ System Status
- [ ] System load is low
- [ ] Memory usage is reasonable
- [ ] No critical errors in system logs

---

## Troubleshooting

### Issue: "Host key verification failed"
**Solution:**
```bash
# Remove old host key
ssh-keygen -R [DROPLET-IP]

# Try connection again
ssh mingus-test
```

### Issue: "Permission denied (publickey)"
**Possible Causes:**
1. SSH key not added to droplet
2. Wrong key being used
3. Key permissions incorrect

**Solutions:**
```bash
# Verify key permissions
chmod 600 ~/.ssh/mingus_test

# Test key directly
ssh -v -i ~/.ssh/mingus_test root@[DROPLET-IP]

# Check if key is in DigitalOcean
# Go to: Settings → Security → SSH Keys
```

### Issue: "Connection timed out"
**Possible Causes:**
1. Droplet not running
2. Firewall blocking SSH (port 22)
3. Wrong IP address

**Solutions:**
```bash
# Check droplet status in DigitalOcean dashboard
# Verify firewall rules allow SSH (port 22)
# Ping the droplet IP
ping [DROPLET-IP]

# Check if port 22 is open
nc -zv [DROPLET-IP] 22
```

### Issue: "Could not resolve hostname"
**Solution:**
```bash
# Use IP address instead of hostname
ssh -i ~/.ssh/mingus_test root@[DROPLET-IP]

# Or update /etc/hosts (not recommended for droplets)
```

---

## Post-Connection Setup

Once connected successfully:

### 1. Update System
```bash
apt update && apt upgrade -y
```

### 2. Create Non-Root User (Recommended)
```bash
adduser mingus
usermod -aG sudo mingus
```

### 3. Configure Firewall
```bash
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### 4. Install Essential Tools
```bash
apt install -y curl wget git build-essential
```

### 5. Set Up SSH for New User
```bash
# Copy your public key to new user
mkdir -p /home/mingus/.ssh
cp ~/.ssh/authorized_keys /home/mingus/.ssh/
chown -R mingus:mingus /home/mingus/.ssh
chmod 700 /home/mingus/.ssh
chmod 600 /home/mingus/.ssh/authorized_keys
```

---

## Connection Test Script

Save this as `test_droplet_connection.sh`:

```bash
#!/bin/bash

DROPLET_IP="${1:-[YOUR-DROPLET-IP]}"
KEY_PATH="$HOME/.ssh/mingus_test"

echo "Testing connection to droplet at $DROPLET_IP..."
echo ""

# Test 1: Ping
echo "1. Testing ping..."
if ping -c 3 "$DROPLET_IP" > /dev/null 2>&1; then
    echo "   ✅ Droplet is reachable"
else
    echo "   ❌ Droplet is not reachable"
    exit 1
fi

# Test 2: Port 22
echo "2. Testing SSH port (22)..."
if nc -zv -w 5 "$DROPLET_IP" 22 > /dev/null 2>&1; then
    echo "   ✅ SSH port is open"
else
    echo "   ❌ SSH port is closed or filtered"
    exit 1
fi

# Test 3: SSH Connection
echo "3. Testing SSH connection..."
if ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=no root@"$DROPLET_IP" "echo 'Connection successful'" > /dev/null 2>&1; then
    echo "   ✅ SSH connection successful"
    echo ""
    echo "You can now connect using:"
    echo "  ssh -i $KEY_PATH root@$DROPLET_IP"
    echo "  or"
    echo "  ssh mingus-test  (if SSH config is updated)"
else
    echo "   ❌ SSH connection failed"
    exit 1
fi
```

**Usage:**
```bash
chmod +x test_droplet_connection.sh
./test_droplet_connection.sh [YOUR-DROPLET-IP]
```

---

## Next Steps After Successful Connection

1. ✅ **Connection Verified** - SSH key authentication working
2. → **Security Hardening** - Set up firewall, disable root login
3. → **User Setup** - Create non-root user with sudo
4. → **Application Deployment** - Install Mingus application stack
5. → **Monitoring Setup** - Configure monitoring and alerts
6. → **Backup Verification** - Test backup and restore process

---

**Status:** Ready to test connection once droplet IP is configured

