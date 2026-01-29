#!/bin/bash
# Alternative method: Add SSH key via root access (if available)

echo "🔑 Adding SSH Key via Root Access"
echo "=================================================="
echo ""

# Try connecting as root first
echo "Attempting to connect as root..."
echo "If you have root password access, you can add the key this way:"
echo ""

echo "1. SSH as root:"
echo "   ssh root@test.mingusapp.com"
echo ""
echo "2. Once connected as root, run:"
echo "   mkdir -p /home/mingus-app/.ssh"
echo "   echo 'ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIMvnTbQQFWcKbBwC42ArL/wUQBosYeYsAp2iE2OXQ5wO johnnie_watson_3rd@mac.com' > /home/mingus-app/.ssh/authorized_keys"
echo "   chown -R mingus-app:mingus-app /home/mingus-app/.ssh"
echo "   chmod 700 /home/mingus-app/.ssh"
echo "   chmod 600 /home/mingus-app/.ssh/authorized_keys"
echo ""
