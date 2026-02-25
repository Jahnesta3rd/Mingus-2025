# Certificate Mismatch at test.mingusapp.com – Troubleshooting

When a browser or client reports a **certificate mismatch** (e.g. "Your connection is not private", `ERR_CERT_COMMON_NAME_INVALID`, or cert name doesn’t match), the server is usually presenting the **mingusapp.com** certificate instead of the **test.mingusapp.com** certificate. This happens due to nginx’s default 443 server block, not SNI.

---

## Quick fix (recommended)

Use the **combined** nginx config so the **test** HTTPS block is the first (and default) 443 block and uses the test cert. From your Mac:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
scp scripts/nginx/mingusapp.com.combined.conf test.mingusapp.com:/tmp/mingusapp.com.combined.conf
ssh test.mingusapp.com
```

On the server:

```bash
sudo cp /etc/nginx/sites-available/mingusapp.com /etc/nginx/sites-available/mingusapp.com.bak.$(date +%Y%m%d)
sudo cp /tmp/mingusapp.com.combined.conf /etc/nginx/sites-available/mingusapp.com
sudo rm -f /etc/nginx/sites-enabled/mingus-test
sudo nginx -t && sudo systemctl reload nginx
```

Then verify (see [Verify the fix](#verify-the-fix) below).

---

## Diagnose on the server

Run these **on the server** (e.g. `ssh test.mingusapp.com`) to see why the wrong cert is used.

### 1. Which certificate is actually served?

```bash
echo | openssl s_client -connect test.mingusapp.com:443 -servername test.mingusapp.com 2>/dev/null | openssl x509 -noout -subject -issuer -dates
```

- **Expected:** `subject=CN = test.mingusapp.com` (or similar with test.mingusapp.com in the subject).
- **Problem:** `subject=CN = mingusapp.com` (or no test.mingusapp.com) → wrong cert is being sent.

### 2. What’s in sites-enabled?

```bash
ls -la /etc/nginx/sites-enabled/
```

If **default** (or any file other than your mingus config) is present, it may define the first `listen 443 ssl` and become the default 443 server, so that cert is used when nothing else matches.

### 3. Which 443 block is first in the loaded config?

```bash
sudo nginx -T 2>/dev/null | grep -E "listen 443|server_name|ssl_certificate " | head -50
```

Check the **first** `listen 443` block and its `ssl_certificate` and `server_name`. If that block uses the **mingusapp.com** cert, it’s the default and can cause the mismatch.

### 4. Does the test.mingusapp.com cert exist?

```bash
sudo ls -la /etc/letsencrypt/live/test.mingusapp.com/
```

You should see `fullchain.pem` and `privkey.pem`. If the directory is missing or empty, the cert was never issued or was removed — see [Obtain or renew the test cert](#obtain-or-renew-the-test-cert).

### 5. What does the active mingusapp.com config use?

```bash
grep -n "server_name\|listen 443\|ssl_certificate " /etc/nginx/sites-available/mingusapp.com | head -30
```

Confirm whether the **first** 443 block has `server_name test.mingusapp.com` and `ssl_certificate .../test.mingusapp.com/...`.

---

## Fix options

### Option A: Use combined config (recommended)

The repo’s **combined** config puts the **test** HTTPS block first and marks it `default_server`, so the correct cert is used. Follow the [Quick fix](#quick-fix-recommended) above. Full steps: [NGINX_OPTION_B_APPLY.md](./NGINX_OPTION_B_APPLY.md).

### Option B: Add default_server to the test block only

If you keep a **separate** test config (e.g. `mingus-test`), make the **test** HTTPS block the default for 443 so nginx doesn’t use another block’s cert:

1. Edit the config that contains the test block (e.g. `sites-available/mingusapp.com` or `mingus-test`):
   ```bash
   sudo nano /etc/nginx/sites-available/mingusapp.com
   ```
2. Find the **test** HTTPS server block (`server_name test.mingusapp.com` and `ssl_certificate .../test.mingusapp.com/...`).
3. Change:
   ```nginx
   listen 443 ssl http2;
   listen [::]:443 ssl http2;
   server_name test.mingusapp.com;
   ```
   to:
   ```nginx
   listen 443 ssl http2 default_server;
   listen [::]:443 ssl http2 default_server;
   server_name test.mingusapp.com;
   ```
4. Save, then:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```

If you use the repo’s standalone test config, use `scripts/nginx/mingusapp.com.test.conf` (it already has `default_server`). Copy it to the server and enable it; see [VIBE_CHECK_MEME_NGINX_FIX.md](./VIBE_CHECK_MEME_NGINX_FIX.md).

### Option C: Remove conflicting default 443

If another file (e.g. `default`) defines `listen 443 ssl` or `default_server`, either:

- Disable it: `sudo rm /etc/nginx/sites-enabled/default`, or  
- Ensure your mingus config is loaded so that the **first** 443 block is the test block with the test cert,

then `sudo nginx -t && sudo systemctl reload nginx`.

---

## Verify the fix

From the server or your Mac:

```bash
echo | openssl s_client -connect test.mingusapp.com:443 -servername test.mingusapp.com 2>/dev/null | openssl x509 -noout -subject -dates
```

You should see **subject=CN = test.mingusapp.com**. Then open https://test.mingusapp.com in a browser; the certificate warning should be gone (for a valid Let’s Encrypt cert).

---

## Obtain or renew the test cert

If `/etc/letsencrypt/live/test.mingusapp.com/` is missing or the cert is expired:

1. Ensure DNS for **test.mingusapp.com** points to the server (e.g. A record to `64.225.16.241`).
2. On the server, allow HTTP for ACME challenge and run certbot:
   ```bash
   sudo certbot certonly --webroot -w /var/www/html -d test.mingusapp.com
   ```
3. Ensure the nginx block for test.mingusapp.com uses:
   - `ssl_certificate /etc/letsencrypt/live/test.mingusapp.com/fullchain.pem;`
   - `ssl_certificate_key /etc/letsencrypt/live/test.mingusapp.com/privkey.pem;`
4. Reload nginx: `sudo nginx -t && sudo systemctl reload nginx`.

---

## Summary

| Symptom | Cause | Fix |
|--------|--------|-----|
| Cert mismatch at test.mingusapp.com | First 443 block (or default_server) uses mingusapp.com cert | Use combined config or make test block `default_server` |
| test.mingusapp.com cert missing/expired | No or old Let’s Encrypt cert | Run certbot for test.mingusapp.com, point nginx to that cert, reload |
| “Conflicting server name test.mingusapp.com” | Two configs define test.mingusapp.com | Use only one (e.g. combined config and disable mingus-test) |

See also: [NGINX_CERT_DEBUG.md](./NGINX_CERT_DEBUG.md), [NGINX_OPTION_B_APPLY.md](./NGINX_OPTION_B_APPLY.md), [LOGIN_VIBE_DASHBOARD_TROUBLESHOOTING.md](./LOGIN_VIBE_DASHBOARD_TROUBLESHOOTING.md) (§ Certificate mismatch).
