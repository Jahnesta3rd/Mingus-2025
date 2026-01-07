# DigitalOcean Droplet Firewall (UFW) Configuration

## Firewall Configuration Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **UFW Firewall Configured and Enabled**

---

## Configuration Steps Executed

### 1. Reset UFW to Defaults
```bash
sudo ufw --force reset
```
- ✅ Cleared all existing rules
- ✅ Reset to clean state

### 2. Set Default Policies
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
```
- ✅ **Incoming:** Deny by default (secure)
- ✅ **Outgoing:** Allow by default (normal operation)

### 3. Allow SSH (Critical First Step!)
```bash
sudo ufw allow ssh
sudo ufw allow 22/tcp
```
- ✅ SSH access allowed (prevents lockout)
- ✅ Port 22 explicitly allowed

### 4. Allow Web Traffic
```bash
sudo ufw allow http
sudo ufw allow https
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```
- ✅ HTTP (port 80) allowed
- ✅ HTTPS (port 443) allowed

### 5. Allow Development Ports
```bash
sudo ufw allow 3000/tcp comment "React development server"
sudo ufw allow 5000/tcp comment "Flask API server"
```
- ✅ Port 3000 (React dev server) allowed
- ✅ Port 5000 (Flask API) allowed

### 6. Allow PostgreSQL
```bash
sudo ufw allow from 127.0.0.1 to any port 5432 comment "PostgreSQL local"
sudo ufw allow from 10.108.0.0/24 to any port 5432 comment "PostgreSQL private network"
```
- ✅ PostgreSQL (port 5432) from localhost allowed
- ✅ PostgreSQL from private network (10.108.0.0/24) allowed

### 7. Enable Firewall
```bash
sudo ufw --force enable
```
- ✅ Firewall enabled and active

---

## Firewall Rules Summary

### Default Policies
- **Incoming:** Deny (blocked by default)
- **Outgoing:** Allow (permitted by default)

### Allowed Incoming Ports

| Port | Service | Access | Comment |
|------|---------|--------|---------|
| 22 | SSH | All | SSH access |
| 80 | HTTP | All | Web traffic |
| 443 | HTTPS | All | Secure web traffic |
| 3000 | React Dev | All | Development server |
| 5000 | Flask API | All | API server |
| 5432 | PostgreSQL | localhost + private network | Database |

### Network Restrictions
- **PostgreSQL (5432):** Only from:
  - `127.0.0.1` (localhost)
  - `10.108.0.0/24` (private network)

---

## Security Benefits

### ✅ Protection Provided
- **Default Deny:** All incoming traffic blocked unless explicitly allowed
- **SSH Protected:** Only port 22 open for remote access
- **Web Access:** HTTP/HTTPS ports open for web services
- **Database Secured:** PostgreSQL only accessible from trusted networks
- **Development Ports:** Open for testing environment

### ⚠️ Important Notes

1. **SSH Access:** Port 22 is open - ensure SSH is hardened (already done)
2. **Development Ports:** Ports 3000 and 5000 are open to all - consider restricting in production
3. **PostgreSQL:** Only accessible from localhost and private network - good security practice
4. **Default Deny:** Any new services need explicit firewall rules

---

## Firewall Management Commands

### View Status
```bash
# Verbose status (shows all rules)
sudo ufw status verbose

# Numbered status (for deletion)
sudo ufw status numbered

# Show rules with comments
sudo ufw status | grep comment
```

### Add Rules
```bash
# Allow port
sudo ufw allow 8080/tcp

# Allow port with comment
sudo ufw allow 8080/tcp comment "Custom service"

# Allow from specific IP
sudo ufw allow from 192.168.1.100

# Allow from subnet
sudo ufw allow from 192.168.1.0/24
```

### Remove Rules
```bash
# Delete by number (use status numbered first)
sudo ufw delete 5

# Delete by rule
sudo ufw delete allow 3000/tcp
```

### Disable/Enable
```bash
# Disable firewall (temporarily)
sudo ufw disable

# Enable firewall
sudo ufw enable

# Reload firewall
sudo ufw reload
```

---

## Testing Firewall

### Test SSH Access
```bash
# Should work (port 22 allowed)
ssh mingus-app
```

### Test Web Ports
```bash
# Test HTTP
curl http://64.225.16.241

# Test HTTPS
curl https://64.225.16.241
```

### Test Blocked Ports
```bash
# Should be blocked (not in allowed list)
nc -zv 64.225.16.241 3306  # MySQL (should fail)
nc -zv 64.225.16.241 8080  # Custom port (should fail)
```

---

## Adding Additional Rules

### Example: Allow Custom Port
```bash
# Allow port 8080 for custom service
sudo ufw allow 8080/tcp comment "Custom service"

# Verify
sudo ufw status verbose
```

### Example: Restrict Development Ports
```bash
# Remove public access to dev ports
sudo ufw delete allow 3000/tcp
sudo ufw delete allow 5000/tcp

# Allow only from your IP
sudo ufw allow from YOUR_IP_ADDRESS to any port 3000 comment "React dev (restricted)"
sudo ufw allow from YOUR_IP_ADDRESS to any port 5000 comment "Flask API (restricted)"
```

### Example: Allow Database from Specific IP
```bash
# Allow PostgreSQL from specific IP
sudo ufw allow from 192.168.1.50 to any port 5432 comment "PostgreSQL from office"
```

---

## Troubleshooting

### If SSH Connection Fails
```bash
# Use DigitalOcean console to access droplet
# Then check firewall status
sudo ufw status

# Ensure SSH is allowed
sudo ufw allow ssh
sudo ufw reload
```

### If Service Not Accessible
```bash
# Check if port is allowed
sudo ufw status | grep PORT_NUMBER

# Add rule if missing
sudo ufw allow PORT_NUMBER/tcp

# Reload firewall
sudo ufw reload
```

### View Firewall Logs
```bash
# UFW logs are in syslog
sudo tail -f /var/log/syslog | grep UFW

# Or check auth log
sudo tail -f /var/log/auth.log
```

---

## Production Recommendations

### For Production Environment:

1. **Restrict Development Ports:**
   ```bash
   # Remove public access
   sudo ufw delete allow 3000/tcp
   sudo ufw delete allow 5000/tcp
   ```

2. **Limit SSH Access:**
   ```bash
   # Allow SSH only from your IP
   sudo ufw delete allow ssh
   sudo ufw allow from YOUR_IP_ADDRESS to any port 22 comment "SSH from office"
   ```

3. **Add Rate Limiting:**
   ```bash
   # UFW doesn't have built-in rate limiting
   # Consider using fail2ban (already installed)
   ```

4. **Monitor Firewall:**
   ```bash
   # Set up monitoring for firewall events
   # Check logs regularly
   ```

---

## Integration with Fail2ban

UFW works well with fail2ban (already installed):

- **UFW:** Controls which ports are open
- **Fail2ban:** Monitors logs and temporarily bans IPs with suspicious activity

Both work together for layered security.

---

## Summary

✅ **Firewall:** Configured and enabled  
✅ **Default Policies:** Deny incoming, allow outgoing  
✅ **SSH Access:** Protected and allowed  
✅ **Web Traffic:** HTTP/HTTPS allowed  
✅ **Development Ports:** Open for testing  
✅ **Database:** Restricted to trusted networks  
✅ **Security:** Significantly improved  

**Your droplet firewall is now configured and protecting your server!**

---

**Status:** ✅ **Firewall Configuration Complete - Server is Protected**

