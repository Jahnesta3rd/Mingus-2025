#!/bin/bash

# Script to update SSH config with droplet IP and test connection

if [ -z "$1" ]; then
    echo "Usage: $0 <DROPLET-IP>"
    echo ""
    echo "Example: $0 157.230.123.45"
    exit 1
fi

DROPLET_IP="$1"
SSH_CONFIG="$HOME/.ssh/config"
KEY_PATH="$HOME/.ssh/mingus_test"

echo "Updating SSH config with droplet IP: $DROPLET_IP"
echo ""

# Backup SSH config
if [ -f "$SSH_CONFIG" ]; then
    cp "$SSH_CONFIG" "$SSH_CONFIG.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ Backup created: $SSH_CONFIG.backup.*"
fi

# Update SSH config
if sed -i '' "s/\[DROPLET-IP\]/$DROPLET_IP/g" "$SSH_CONFIG" 2>/dev/null || \
   sed -i "s/\[DROPLET-IP\]/$DROPLET_IP/g" "$SSH_CONFIG" 2>/dev/null; then
    echo "✅ SSH config updated successfully"
else
    echo "❌ Failed to update SSH config"
    exit 1
fi

# Verify update
echo ""
echo "Updated SSH config entry:"
grep -A 4 "Host mingus-test" "$SSH_CONFIG"
echo ""

# Test connection
echo "Testing connection to droplet..."
echo ""

# Test 1: Ping
echo "1. Testing ping to $DROPLET_IP..."
if ping -c 3 "$DROPLET_IP" > /dev/null 2>&1; then
    echo "   ✅ Droplet is reachable"
else
    echo "   ⚠️  Ping failed (may be normal if ICMP is blocked)"
fi

# Test 2: Port 22
echo "2. Testing SSH port (22)..."
if command -v nc > /dev/null 2>&1; then
    if nc -zv -w 5 "$DROPLET_IP" 22 > /dev/null 2>&1; then
        echo "   ✅ SSH port is open"
    else
        echo "   ⚠️  SSH port check failed (nc may not be available)"
    fi
else
    echo "   ⚠️  netcat (nc) not available, skipping port check"
fi

# Test 3: SSH Connection
echo "3. Testing SSH connection..."
echo ""
echo "Attempting to connect..."
echo ""

if ssh -i "$KEY_PATH" -o ConnectTimeout=10 -o StrictHostKeyChecking=accept-new root@"$DROPLET_IP" "echo '✅ Connection successful!'; hostname; uname -a" 2>&1; then
    echo ""
    echo "=========================================="
    echo "✅ Connection test successful!"
    echo "=========================================="
    echo ""
    echo "You can now connect using:"
    echo "  ssh mingus-test"
    echo ""
    echo "Or directly:"
    echo "  ssh -i $KEY_PATH root@$DROPLET_IP"
else
    echo ""
    echo "=========================================="
    echo "❌ Connection test failed"
    echo "=========================================="
    echo ""
    echo "Troubleshooting steps:"
    echo "1. Verify droplet is running in DigitalOcean dashboard"
    echo "2. Check that SSH key is added to the droplet"
    echo "3. Verify firewall allows SSH (port 22)"
    echo "4. Check key permissions: chmod 600 $KEY_PATH"
    echo ""
    echo "Try manual connection:"
    echo "  ssh -v -i $KEY_PATH root@$DROPLET_IP"
    exit 1
fi

