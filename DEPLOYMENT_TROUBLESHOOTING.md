# Deployment Troubleshooting Guide

## Permission Denied Error

If you're getting "permission denied" when running the deployment command, here's how to fix it:

### Option 1: SSH in First, Then Run Commands (Recommended)

**Step 1:** SSH into your server interactively:
```bash
ssh mingus-app@test.mingusapp.com
```

**Step 2:** Once you're logged in, run these commands one by one:
```bash
cd /var/www/mingus-app
git pull origin main
cd frontend
npm install
npm run build
cd ..
sudo systemctl restart mingus-backend
sudo systemctl restart nginx
```

This way, you'll be prompted for your sudo password interactively.

---

### Option 2: Use SSH Key Authentication

If you want to run commands non-interactively, set up SSH key authentication:

**On your local machine:**
```bash
# Generate SSH key if you don't have one
ssh-keygen -t rsa -b 4096 -C "your_email@example.com"

# Copy your public key to the server
ssh-copy-id mingus-app@test.mingusapp.com
```

Then you can run commands without password prompts.

---

### Option 3: Use a Deployment Script on the Server

**Step 1:** Copy the deployment script to your server:
```bash
# From your local machine
scp deploy_interactive.sh mingus-app@test.mingusapp.com:/home/mingus-app/
```

**Step 2:** SSH into your server:
```bash
ssh mingus-app@test.mingusapp.com
```

**Step 3:** Make the script executable and run it:
```bash
chmod +x ~/deploy_interactive.sh
~/deploy_interactive.sh
```

---

### Option 4: Configure Passwordless Sudo (Advanced)

If you want to run sudo commands without a password prompt:

**On the server:**
```bash
# Edit sudoers file (be careful!)
sudo visudo

# Add this line (replace 'mingus-app' with your username):
mingus-app ALL=(ALL) NOPASSWD: /usr/bin/systemctl restart mingus-backend, /usr/bin/systemctl restart nginx
```

**⚠️ Warning:** Only do this if you understand the security implications!

---

## Common Issues

### Issue: "Permission denied (publickey)"
**Solution:** Set up SSH key authentication (see Option 2 above)

### Issue: "sudo: a password is required"
**Solution:** Use Option 1 (SSH in first, then run commands interactively)

### Issue: "cd: /var/www/mingus-app: Permission denied"
**Solution:** Check directory permissions:
```bash
ls -la /var/www/
# If needed, fix permissions:
sudo chown -R mingus-app:mingus-app /var/www/mingus-app
```

### Issue: "npm: command not found"
**Solution:** Install Node.js/npm or use nvm:
```bash
# Check if node is installed
which node
which npm

# If not installed, install Node.js
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install node
```

---

## Quick Reference: Step-by-Step Deployment

**Recommended approach (most reliable):**

1. **SSH into server:**
   ```bash
   ssh mingus-app@test.mingusapp.com
   ```

2. **Navigate and pull:**
   ```bash
   cd /var/www/mingus-app
   git pull origin main
   ```

3. **Build frontend:**
   ```bash
   cd frontend
   npm install
   npm run build
   cd ..
   ```

4. **Restart services (enter password when prompted):**
   ```bash
   sudo systemctl restart mingus-backend
   sudo systemctl restart nginx
   ```

5. **Verify services are running:**
   ```bash
   sudo systemctl status mingus-backend
   sudo systemctl status nginx
   ```

---

**Status:** Ready to deploy ✅
