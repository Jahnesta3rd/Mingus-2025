# Automatic Service Restart Configuration

This document describes the automatic service restart configuration for the Mingus Application.

## Overview

The application is configured with multiple layers of automatic restart on failure:

1. **Systemd Service Restart** - Built-in systemd restart policies
2. **Service Monitor** - Custom monitoring script with intelligent restart logic
3. **Health Check with Auto-Restart** - Health endpoint monitoring

## Systemd Restart Configuration

### Service Files

Both `mingus-backend.service` and `mingus-frontend.service` are configured with:

```ini
Restart=always
RestartSec=10
StartLimitInterval=300
StartLimitBurst=5
```

**Configuration Details:**
- `Restart=always` - Always restart the service on failure
- `RestartSec=10` - Wait 10 seconds before restarting
- `StartLimitInterval=300` - Time window for counting restarts (5 minutes)
- `StartLimitBurst=5` - Maximum 5 restarts within the time window

### Service Overrides

Additional configuration in `/etc/systemd/system/mingus-*.service.d/override.conf`:
- Enhanced restart policies
- Failure notification hooks
- Watchdog support (if available)

## Service Monitor

The `monitor_services.sh` script provides intelligent monitoring and restart:

### Features

- **Smart Restart Logic**: Tracks restart attempts and prevents infinite restart loops
- **Health Checks**: Verifies service health beyond just process status
- **Alerting**: Sends alerts when services exceed restart limits
- **Time-based Reset**: Resets restart counts after a time window

### Configuration

```bash
MAX_RESTARTS=5              # Maximum restart attempts
RESTART_WINDOW=300          # Time window in seconds (5 minutes)
MONITOR_INTERVAL=30         # Check interval in seconds
```

### Usage

```bash
# Run once
./scripts/monitor_services.sh

# Run in daemon mode
./scripts/monitor_services.sh --daemon

# Check status
./scripts/monitor_services.sh --status

# Reset restart counts
./scripts/monitor_services.sh --reset
```

### Monitor Service (Systemd)

The monitor can run as a systemd service:

```bash
# Enable and start
sudo systemctl enable mingus-monitor.service
sudo systemctl start mingus-monitor.service

# Check status
sudo systemctl status mingus-monitor.service
```

## Health Check with Auto-Restart

The `check_service_health.sh` script performs health checks and restarts unhealthy services:

### Features

- Checks service process status
- Verifies health endpoints
- Automatically restarts unhealthy services
- Can run as cron job

### Usage

```bash
# With auto-restart (default)
./scripts/check_service_health.sh

# Without auto-restart
./scripts/check_service_health.sh --no-restart
```

### Cron Configuration

Add to crontab for regular health checks:

```bash
# Check every 5 minutes
*/5 * * * * /var/www/mingus-app/scripts/check_service_health.sh >> /var/log/mingus-app/health.log 2>&1
```

## Setup Instructions

### 1. Configure Automatic Restart

```bash
# Run configuration script (as root)
sudo ./scripts/configure_auto_restart.sh
```

This will:
- Install enhanced systemd service files
- Configure service overrides
- Set up failure notification services
- Enable monitoring service

### 2. Verify Configuration

```bash
# Check service restart policies
systemctl show mingus-backend.service | grep Restart
systemctl show mingus-frontend.service | grep Restart

# Check service status
systemctl status mingus-backend
systemctl status mingus-frontend
```

### 3. Test Restart Functionality

```bash
# Manually stop service to test auto-restart
sudo systemctl stop mingus-backend
sleep 15
sudo systemctl status mingus-backend  # Should show as active
```

## Monitoring and Alerts

### View Restart History

```bash
# Systemd journal
journalctl -u mingus-backend -f
journalctl -u mingus-frontend -f

# Service monitor logs
tail -f /var/www/mingus-app/logs/service_monitor_*.log

# Failure log
tail -f /var/log/mingus-app/failures.log
```

### Check Restart Counts

```bash
./scripts/monitor_services.sh --status
```

### Alert Configuration

Edit `monitor_services.sh` to configure alerts:

```bash
send_alert() {
    local service=$1
    local message=$2
    
    # Email alert
    echo "$message" | mail -s "Alert: $service" admin@example.com
    
    # Slack webhook
    curl -X POST https://hooks.slack.com/your-webhook \
        -d "{\"text\":\"$message\"}"
    
    # Custom webhook
    curl -X POST https://your-alerting-service.com/webhook \
        -d "{\"service\":\"$service\",\"message\":\"$message\"}"
}
```

## Restart Policies Explained

### Systemd Restart Policies

| Policy | Description |
|--------|-------------|
| `no` | Never restart |
| `on-success` | Restart only on successful exit |
| `on-failure` | Restart only on failure |
| `on-abnormal` | Restart on abnormal exit |
| `on-abort` | Restart on abort signal |
| `on-watchdog` | Restart on watchdog timeout |
| `always` | Always restart (used in our config) |

### Start Limit

The `StartLimitInterval` and `StartLimitBurst` prevent infinite restart loops:

- If a service restarts more than `StartLimitBurst` times within `StartLimitInterval`, systemd will stop trying
- This prevents resource exhaustion from restart loops
- Our configuration: 5 restarts per 5 minutes

## Troubleshooting

### Service Won't Restart

1. **Check restart limits:**
   ```bash
   systemctl show mingus-backend | grep StartLimit
   ```

2. **Reset restart limits:**
   ```bash
   systemctl reset-failed mingus-backend
   ```

3. **Check service logs:**
   ```bash
   journalctl -u mingus-backend -n 50
   ```

### Too Many Restarts

If a service is restarting too frequently:

1. **Check the root cause:**
   ```bash
   journalctl -u mingus-backend -f
   ```

2. **Temporarily disable auto-restart:**
   ```bash
   sudo systemctl edit mingus-backend
   # Add: Restart=no
   ```

3. **Fix the underlying issue** before re-enabling restart

### Monitor Service Not Working

1. **Check if monitor is running:**
   ```bash
   systemctl status mingus-monitor
   ```

2. **Check monitor logs:**
   ```bash
   journalctl -u mingus-monitor -f
   ```

3. **Restart monitor:**
   ```bash
   sudo systemctl restart mingus-monitor
   ```

## Best Practices

1. **Monitor Restart Frequency**: Regularly check restart counts to identify problematic services
2. **Set Appropriate Limits**: Adjust `MAX_RESTARTS` and `RESTART_WINDOW` based on your needs
3. **Alert on Excessive Restarts**: Configure alerts when services exceed restart limits
4. **Investigate Root Causes**: Don't just rely on auto-restart; fix underlying issues
5. **Test Restart Functionality**: Regularly test that auto-restart works as expected
6. **Document Restart Behavior**: Keep track of restart patterns for troubleshooting

## Configuration Files

- **Systemd Services**: `/etc/systemd/system/mingus-*.service`
- **Service Overrides**: `/etc/systemd/system/mingus-*.service.d/override.conf`
- **Monitor Service**: `/etc/systemd/system/mingus-monitor.service`
- **Restart Counts**: `/var/www/mingus-app/.service_restart_counts`
- **Monitor Logs**: `/var/www/mingus-app/logs/service_monitor_*.log`
- **Failure Log**: `/var/log/mingus-app/failures.log`

## Summary

The automatic restart configuration provides three layers of protection:

1. **Systemd** - Immediate restart on process failure
2. **Service Monitor** - Intelligent monitoring with restart limits
3. **Health Checks** - Application-level health verification

This multi-layered approach ensures high availability while preventing infinite restart loops.
