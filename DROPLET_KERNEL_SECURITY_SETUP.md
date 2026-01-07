# DigitalOcean Droplet Kernel Security Parameters

## Kernel Security Configuration Complete ✅

**Date:** January 7, 2026  
**Droplet:** mingus-test (64.225.16.241)  
**Status:** ✅ **Kernel Security Parameters Configured**

---

## Configuration Applied

### Security Configuration File
**Location:** `/etc/sysctl.d/99-security.conf`

### Security Settings Applied

#### 1. IP Spoofing Protection
- `net.ipv4.conf.default.rp_filter = 1`
- `net.ipv4.conf.all.rp_filter = 1`
- **Protection:** Prevents IP address spoofing attacks

#### 2. ICMP Redirect Protection
- `net.ipv4.conf.all.accept_redirects = 0`
- `net.ipv6.conf.all.accept_redirects = 0`
- `net.ipv4.conf.default.accept_redirects = 0`
- `net.ipv6.conf.default.accept_redirects = 0`
- **Protection:** Prevents ICMP redirect attacks

#### 3. Send Redirects Disabled
- `net.ipv4.conf.all.send_redirects = 0`
- `net.ipv4.conf.default.send_redirects = 0`
- **Protection:** Prevents sending ICMP redirects

#### 4. Source Routing Disabled
- `net.ipv4.conf.all.accept_source_route = 0`
- `net.ipv6.conf.all.accept_source_route = 0`
- `net.ipv4.conf.default.accept_source_route = 0`
- `net.ipv6.conf.default.accept_source_route = 0`
- **Protection:** Prevents source routing attacks

#### 5. Log Martians
- `net.ipv4.conf.all.log_martians = 1`
- **Protection:** Logs suspicious packets (invalid source addresses)

#### 6. ICMP Ping Settings
- `net.ipv4.icmp_echo_ignore_all = 0` (responds to pings)
- `net.ipv4.icmp_echo_ignore_broadcasts = 1` (ignores broadcast pings)
- **Protection:** Prevents ping flood attacks while allowing normal pings

#### 7. TCP SYN Flood Protection
- `net.ipv4.tcp_syncookies = 1` (enables SYN cookies)
- `net.ipv4.tcp_max_syn_backlog = 2048` (increases backlog)
- `net.ipv4.tcp_synack_retries = 2` (reduces retries)
- `net.ipv4.tcp_syn_retries = 5` (limits SYN retries)
- **Protection:** Protects against SYN flood attacks

---

## Security Benefits

### ✅ Network Attack Protection
- **IP Spoofing:** Blocked
- **ICMP Redirects:** Ignored
- **Source Routing:** Disabled
- **SYN Floods:** Protected

### ✅ Logging and Monitoring
- **Martian Packets:** Logged for analysis
- **Suspicious Activity:** Tracked in logs

### ✅ Performance Optimization
- **TCP Backlog:** Optimized for better performance
- **SYN Retries:** Limited to prevent resource exhaustion

---

## Verification

### Check Current Settings
```bash
# View all security settings
sudo sysctl -a | grep -E '(rp_filter|accept_redirects|accept_source_route|tcp_syncookies)'

# Check specific settings
sudo sysctl net.ipv4.conf.all.rp_filter
sudo sysctl net.ipv4.tcp_syncookies
```

### Verify Configuration File
```bash
# View configuration
cat /etc/sysctl.d/99-security.conf

# Test configuration
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

---

## How Settings Work

### IP Spoofing Protection (rp_filter)
- **What it does:** Validates that incoming packets match the routing table
- **Protection:** Prevents attackers from spoofing IP addresses
- **Value:** 1 = strict mode (enabled)

### ICMP Redirect Protection
- **What it does:** Ignores ICMP redirect messages
- **Protection:** Prevents man-in-the-middle attacks via redirects
- **Value:** 0 = disabled (ignored)

### Source Routing Disabled
- **What it does:** Rejects packets with source routing options
- **Protection:** Prevents routing manipulation attacks
- **Value:** 0 = disabled

### TCP SYN Cookies
- **What it does:** Uses cryptographic cookies for SYN-ACK responses
- **Protection:** Prevents SYN flood attacks
- **Value:** 1 = enabled

### Log Martians
- **What it does:** Logs packets with invalid source addresses
- **Protection:** Helps detect and analyze attacks
- **Value:** 1 = enabled

---

## Persistence

### Settings Persist Across Reboots
- Configuration file: `/etc/sysctl.d/99-security.conf`
- Loaded automatically on boot
- Applied via `sysctl --system` during startup

### Manual Application
```bash
# Apply settings manually
sudo sysctl -p /etc/sysctl.d/99-security.conf

# Or reload all sysctl settings
sudo sysctl --system
```

---

## Monitoring

### Check Logs for Martian Packets
```bash
# View kernel logs
sudo dmesg | grep -i martian

# Or check syslog
sudo grep -i martian /var/log/syslog | tail -20
```

### Monitor Network Activity
```bash
# View network statistics
sudo netstat -s | grep -i syn

# Check TCP connections
sudo ss -s
```

---

## Customization

### Adjust TCP Backlog
```bash
# Edit config
sudo nano /etc/sysctl.d/99-security.conf

# Change:
net.ipv4.tcp_max_syn_backlog = 4096  # Increase for high-traffic servers

# Apply
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

### Disable Ping Responses
```bash
# Edit config
sudo nano /etc/sysctl.d/99-security.conf

# Change:
net.ipv4.icmp_echo_ignore_all = 1  # Ignore all pings

# Apply
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

### Enable IPv6 Disable (if needed)
```bash
# Edit config
sudo nano /etc/sysctl.d/99-security.conf

# Uncomment:
net.ipv6.conf.all.disable_ipv6 = 1

# Apply
sudo sysctl -p /etc/sysctl.d/99-security.conf
```

---

## Integration with Other Security

### Works With:
- ✅ **UFW Firewall** - Network-level protection
- ✅ **Fail2ban** - Application-level protection
- ✅ **SSH Hardening** - Service-level protection
- ✅ **Kernel Security** - System-level protection

**All security layers working together!**

---

## Troubleshooting

### Settings Not Applied
```bash
# Check if file exists
ls -la /etc/sysctl.d/99-security.conf

# Apply manually
sudo sysctl -p /etc/sysctl.d/99-security.conf

# Check for errors
sudo sysctl --system 2>&1 | grep -i error
```

### Verify Settings
```bash
# Check specific setting
sudo sysctl net.ipv4.tcp_syncookies

# Should show: net.ipv4.tcp_syncookies = 1
```

### Reset Settings
```bash
# Remove config file
sudo rm /etc/sysctl.d/99-security.conf

# Reload defaults
sudo sysctl --system
```

---

## Security Checklist

- [x] ✅ IP Spoofing Protection - Enabled
- [x] ✅ ICMP Redirect Protection - Enabled
- [x] ✅ Source Routing Disabled - Enabled
- [x] ✅ TCP SYN Flood Protection - Enabled
- [x] ✅ Martian Packet Logging - Enabled
- [x] ✅ Settings Applied - Verified
- [x] ✅ Persistence Configured - Verified

---

## Summary

✅ **Kernel Security:** Configured and active  
✅ **IP Spoofing:** Protected  
✅ **ICMP Attacks:** Protected  
✅ **SYN Floods:** Protected  
✅ **Source Routing:** Disabled  
✅ **Logging:** Enabled for monitoring  

**Your droplet kernel is now hardened with security best practices!**

---

## Next Steps

1. ✅ **Kernel Security Configured** - Complete!
2. → **Monitor Logs** - Check for martian packets
3. → **Review Settings** - Verify all protections active
4. → **Test Network** - Ensure services still work
5. → **Document Changes** - Keep track of customizations

---

**Status:** ✅ **Kernel Security Parameters Complete - System-Level Protection Active**

