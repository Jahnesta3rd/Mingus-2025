# Option B: Single config for test.mingusapp.com (no mingus-test)

Use one file (`mingusapp.com`) for both production and test. Disable `mingus-test` so there is no conflicting server name.

## Step 1: Copy combined config to the server

From your **Mac** (repo root):

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
scp scripts/nginx/mingusapp.com.combined.conf test.mingusapp.com:/tmp/mingusapp.com.combined.conf
```

## Step 2: Backup, replace, disable mingus-test, test, reload

SSH in and run:

```bash
ssh test.mingusapp.com
```

Then on the server:

```bash
# Backup current config
sudo cp /etc/nginx/sites-available/mingusapp.com /etc/nginx/sites-available/mingusapp.com.bak.$(date +%Y%m%d)

# Replace with combined config (production + test in one file)
sudo cp /tmp/mingusapp.com.combined.conf /etc/nginx/sites-available/mingusapp.com

# Disable mingus-test so only mingusapp.com defines test.mingusapp.com
sudo rm -f /etc/nginx/sites-enabled/mingus-test

# Test and reload
sudo nginx -t && sudo systemctl reload nginx
```

You should see only:

```text
nginx: the configuration file /etc/nginx/nginx.conf syntax is ok
nginx: configuration file /etc/nginx/nginx.conf test is successful
```

No “conflicting server name” warnings.

## Step 3: Verify

- **Test site:** https://test.mingusapp.com and https://test.mingusapp.com/login should load the app (no 404).
- **Production:** https://mingusapp.com should still work.

## If you get "Your connection is not private" / ERR_CERT_COMMON_NAME_INVALID

The server can be sending the **production** cert (mingusapp.com) for test.mingusapp.com. The combined config was updated so the **test HTTPS block is the first 443 block** in the file (nginx uses the first as default and for SNI in some setups). Re-apply the config and reload:

```bash
# From your Mac
scp scripts/nginx/mingusapp.com.combined.conf test.mingusapp.com:/tmp/mingusapp.com.combined.conf

# On server
ssh test.mingusapp.com
sudo cp /tmp/mingusapp.com.combined.conf /etc/nginx/sites-available/mingusapp.com
sudo nginx -t && sudo systemctl reload nginx
```

**Check which cert nginx is serving** (on the server):

```bash
echo | openssl s_client -connect test.mingusapp.com:443 -servername test.mingusapp.com 2>/dev/null | openssl x509 -noout -subject -dates
```

You should see `subject=CN = test.mingusapp.com`. If you see `CN = mingusapp.com`, another config or block is still taking precedence.

## If production uses a different backend port or root

The combined config uses:

- **Production:** `root /var/www/mingus-app/frontend/dist` and `proxy_pass http://backend` (upstream `backend` = 127.0.0.1:5000).
- **Test:** `root /var/www/mingusapp.com` and `proxy_pass http://127.0.0.1:5000`.

If production on this server uses port 5001 or a different root, edit `/etc/nginx/sites-available/mingusapp.com` on the server and change the production `server` block (the one with `server_name mingusapp.com www.mingusapp.com`) to match your real paths and upstream, then run `sudo nginx -t && sudo systemctl reload nginx` again.
