# How to Find Your DigitalOcean Droplet IP Address

## Where to Find the IP Address

### Method 1: DigitalOcean Dashboard (Easiest)

1. **Log in to DigitalOcean**
   - Go to: https://cloud.digitalocean.com
   - Sign in to your account

2. **Navigate to Your Droplet**
   - Click on **"Droplets"** in the left sidebar
   - Find your droplet named **"mingus-test"**
   - Click on the droplet name to open its details

3. **Find the IP Address**
   - Look for the **"IP addresses"** section
   - You'll see:
     - **IPv4:** `157.230.123.45` (or similar) ← **USE THIS ONE**
     - **IPv6:** `2604:a880:xxx:xxx::xxx` (optional, not needed for SSH)

4. **Copy the IPv4 Address**
   - Click the **copy icon** next to the IPv4 address
   - Or manually copy the IP (format: `xxx.xxx.xxx.xxx`)

### Method 2: Droplets List View

1. Go to **Droplets** in the sidebar
2. In the list view, you'll see a column showing the IP address
3. The IPv4 address is displayed directly in the table

### Method 3: Using DigitalOcean API (Advanced)

If you have the DigitalOcean CLI (`doctl`) installed:

```bash
doctl compute droplet list
```

This will show all droplets with their IP addresses.

---

## Which IP Address to Use?

### ✅ Use IPv4 Address (Recommended)

**Format:** `157.230.123.45` (four numbers separated by dots)

**Why IPv4?**
- Most compatible with SSH
- Works with all SSH clients
- Standard for server connections
- Your SSH config is set up for IPv4

### ❌ Don't Use IPv6 (Unless Specifically Needed)

**Format:** `2604:a880:xxx:xxx::xxx` (hexadecimal with colons)

**Why Not IPv6?**
- Requires additional configuration
- May not be enabled on your network
- IPv4 is simpler and works everywhere

---

## Example IP Address Formats

### ✅ Correct IPv4 Formats:
```
157.230.123.45
192.168.1.100
10.0.0.1
```

### ❌ IPv6 (Don't use for initial setup):
```
2604:a880:800:a1::1a:3001
2001:db8::1
```

---

## What Your Droplet IP Should Look Like

Based on your droplet configuration:
- **Name:** mingus-test
- **Region:** New York 3
- **IPv4:** Will be something like `157.230.xxx.xxx` or `159.89.xxx.xxx`

**Example:**
```
IPv4: 157.230.123.45
```

---

## How to Verify You Have the Right IP

1. **Check in DigitalOcean Dashboard:**
   - The IP should be listed under your droplet
   - It should be in the "mingus-test" droplet details

2. **Test the IP:**
   ```bash
   # Ping the IP (should respond)
   ping -c 3 YOUR_IP_ADDRESS
   
   # Check if SSH port is open
   nc -zv YOUR_IP_ADDRESS 22
   ```

---

## Once You Have the IP

### Option 1: Use the Helper Script
```bash
./update_droplet_ip.sh YOUR_IP_ADDRESS
```

**Example:**
```bash
./update_droplet_ip.sh 157.230.123.45
```

### Option 2: Manual Update
```bash
# Update SSH config
sed -i '' 's/\[DROPLET-IP\]/157.230.123.45/g' ~/.ssh/config

# Test connection
ssh mingus-test
```

### Option 3: Direct Connection
```bash
ssh -i ~/.ssh/mingus_test root@157.230.123.45
```

---

## Visual Guide: Finding IP in DigitalOcean

```
DigitalOcean Dashboard
├── Droplets (left sidebar)
    └── mingus-test (click on name)
        └── Overview Tab
            └── IP addresses section
                ├── IPv4: 157.230.123.45  ← COPY THIS
                └── IPv6: 2604:a880:...   (ignore for now)
```

---

## Troubleshooting

### "I don't see my droplet"
- Make sure you're logged into the correct DigitalOcean account
- Check if the droplet is still being created (may take 1-2 minutes)
- Verify you're in the correct project: "Mingus Test Environment"

### "The IP address is not showing"
- Wait a few minutes if the droplet was just created
- Refresh the page
- Check if the droplet is in "Active" status

### "I have multiple IPs"
- Use the **IPv4** address (the one with dots, not colons)
- If you have multiple IPv4 addresses, use the primary one (usually the first one listed)

---

## Quick Reference

**What you need:**
- ✅ IPv4 address from DigitalOcean dashboard
- ✅ Format: `xxx.xxx.xxx.xxx` (four numbers)
- ✅ From your "mingus-test" droplet

**What to do with it:**
1. Copy the IPv4 address
2. Run: `./update_droplet_ip.sh YOUR_IP`
3. Or manually update `~/.ssh/config`

---

**Next Step:** Get your IPv4 address from DigitalOcean and provide it to test the connection!

