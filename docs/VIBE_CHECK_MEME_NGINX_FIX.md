# Fix: test.mingusapp.com Serving Old Bundle / Site Down After Removing mingus-test

## What happened

1. **Correct files** are at `/var/www/mingusapp.com/` (index.html with `index-f6e209cc.js`).
2. **mingus-test** was serving from `/opt/mingus-test/frontend/build` (old bundle `index-352dcbf5.js`) and was taking precedence for `test.mingusapp.com`.
3. **mingus-test was removed** from `sites-enabled`, so nginx no longer had a server block for `test.mingusapp.com`.
4. **Result**: Requests to `https://test.mingusapp.com` hit the default server (or nothing), so the site appears down or shows the default nginx page.

## Fix: Enable the test config that serves from `/var/www/mingusapp.com`

You need a server block for `test.mingusapp.com` that uses **root /var/www/mingusapp.com** (where the correct build is). Use the repo’s test config.

### Option A: Use the config from this repo (recommended)

From your **local machine** (in the repo root):

```bash
# Copy the test-only nginx config to the server
scp scripts/nginx/mingusapp.com.test.conf test.mingusapp.com:/tmp/nginx-test-mingusapp.conf

# SSH in and enable it
ssh test.mingusapp.com "sudo cp /tmp/nginx-test-mingusapp.conf /etc/nginx/sites-available/mingus-test && sudo ln -sf /etc/nginx/sites-available/mingus-test /etc/nginx/sites-enabled/mingus-test && sudo nginx -t && sudo systemctl reload nginx"
```

Then verify:

```bash
ssh test.mingusapp.com "curl -s https://test.mingusapp.com/vibe-check-meme 2>/dev/null | grep -o 'index-[a-z0-9]*\.js'"
```

You should see **index-f6e209cc.js** (or whatever the current build hash is).

### Option B: Do it manually on the server

1. **SSH in**
   ```bash
   ssh test.mingusapp.com
   ```

2. **Create the test config** (or copy from repo)
   ```bash
   sudo nano /etc/nginx/sites-available/mingus-test
   ```
   Paste the contents of `scripts/nginx/mingusapp.com.test.conf` from this repo. Ensure:
   - `server_name test.mingusapp.com;`
   - `root /var/www/mingusapp.com;`
   - `ssl_certificate` and `ssl_certificate_key` point to **test.mingusapp.com** cert (e.g. `/etc/letsencrypt/live/test.mingusapp.com/`).
   - `location / { try_files $uri $uri/ /index.html; }` for SPA.
   - `location /api/` proxies to `http://127.0.0.1:5000` (or your backend).

3. **Enable and reload**
   ```bash
   sudo ln -sf /etc/nginx/sites-available/mingus-test /etc/nginx/sites-enabled/mingus-test
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Verify**
   ```bash
   curl -sI https://test.mingusapp.com/
   curl -s https://test.mingusapp.com/ | grep -o 'index-[a-z0-9]*\.js'
   ```

### If SSL cert path is wrong

If nginx -t or reload fails with certificate errors, list certs:

```bash
sudo ls -la /etc/letsencrypt/live/
```

Use the directory that matches **test.mingusapp.com** (e.g. `test.mingusapp.com` or sometimes `mingusapp.com`). In the server block, set:

- `ssl_certificate /etc/letsencrypt/live/<that-name>/fullchain.pem;`
- `ssl_certificate_key /etc/letsencrypt/live/<that-name>/privkey.pem;`

### Summary

| Item | Value |
|------|--------|
| **Domain** | test.mingusapp.com |
| **Web root** | /var/www/mingusapp.com |
| **Config to enable** | sites-available/mingus-test → sites-enabled/mingus-test |
| **Backend** | proxy_pass http://127.0.0.1:5000 for /api/ |
| **SPA** | try_files $uri $uri/ /index.html for / |

After this, `https://test.mingusapp.com` and `https://test.mingusapp.com/vibe-check-meme` should serve the current frontend from `/var/www/mingusapp.com`.

**If /login or /vibe-check-meme still return 404:** The server is not using this config (or nginx wasn’t reloaded). Ensure the config above is the one in use for `test.mingusapp.com` and run `sudo nginx -t && sudo systemctl reload nginx`. The block must have `location / { try_files $uri $uri/ /index.html; }` so all client routes serve `index.html`.

---

## Conflicting server name "test.mingusapp.com" (ignored)

If nginx -t shows:

```text
[warn] conflicting server name "test.mingusapp.com" on 0.0.0.0:443, ignored
```

then **two** configs define `test.mingusapp.com` (e.g. `mingusapp.com` and `mingus-test`). Nginx uses the first and **ignores** the second, so the mingus-test config is not used.

**Fix: use only one config for test.mingusapp.com.**

**Option A – Use only mingus-test (recommended)**  
Remove the test.mingusapp.com server blocks from the main config so mingus-test is the only one:

```bash
ssh test.mingusapp.com
sudo nano /etc/nginx/sites-available/mingusapp.com
```

Find every `server { ... server_name test.mingusapp.com; ... }` block (HTTP and HTTPS) and **comment it out** (add `#` at the start of each line) or delete it. Save, then:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

Now only `sites-enabled/mingus-test` defines test.mingusapp.com (root /var/www/mingusapp.com, SPA fallback).

**Option B – Use only the main config**  
Disable mingus-test and fix the test block in mingusapp.com:

```bash
ssh test.mingusapp.com
sudo rm /etc/nginx/sites-enabled/mingus-test
sudo nano /etc/nginx/sites-available/mingusapp.com
```

In the **test.mingusapp.com** server block, set:

- `root /var/www/mingusapp.com;`
- `location / { try_files $uri $uri/ /index.html; }`
- `location /api/ { proxy_pass http://127.0.0.1:5000; ... }` (as in mingus-test)

Then:

```bash
sudo nginx -t && sudo systemctl reload nginx
```

---

## If you get 502 on /api/* (e.g. api/auth/login)

502 means nginx is proxying to the backend but gunicorn is not responding. Fix by starting the backend from the **repo directory** so it uses the latest code:

```bash
ssh test.mingusapp.com
sudo pkill -f 'gunicorn.*app:app' 2>/dev/null || true
sleep 2
# Run from repo; use venv from /opt/mingus-test
sudo -u mingus-app bash -c 'cd /home/mingus-app/mingus-app && /opt/mingus-test/venv/bin/gunicorn --bind 127.0.0.1:5000 --workers 2 --timeout 120 app:app --daemon'
curl -s http://127.0.0.1:5000/health
```

If that fails, check: `ls /home/mingus-app/mingus-app/app.py` and `ls /opt/mingus-test/venv/bin/gunicorn`. The deploy script (Step 5) now runs the backend from the repo directory automatically.
