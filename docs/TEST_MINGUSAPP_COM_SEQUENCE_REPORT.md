# test.mingusapp.com – Login → Vibe-Check → Dashboard Report

This document is **only for test.mingusapp.com** (no production). It reports the current test sequence results and the exact steps to get a successful flow.

---

## Test sequence completed (current behavior)

| Step | URL | Result | Notes |
|------|-----|--------|--------|
| 1. Load app / login | `https://test.mingusapp.com/` | **OK** | Returns 200; login page (“Sign in to your account”) loads. |
| 2. Load login route | `https://test.mingusapp.com/login` | **404 Not Found** | Direct request to `/login` returns 404. |
| 3. Vibe-check route | `https://test.mingusapp.com/vibe-check-meme` | **404 Not Found** | Direct request returns 404. |
| 4. Dashboard route | `https://test.mingusapp.com/dashboard` | **404 Not Found** | Direct request returns 404. |

### What this means

- **Root (`/`) works:** The app is deployed and nginx serves the SPA at the root. If a user opens **https://test.mingusapp.com** (no path), they see the login page.
- **Client routes return 404:** Requests to `/login`, `/vibe-check-meme`, and `/dashboard` hit nginx as file paths. There are no physical files for those paths, and the **current nginx config in use** on the server is **not** sending these to `index.html`, so nginx returns 404.

Consequences:

- **Bookmarks / refresh:** If the user bookmarks `/login` or refreshes on `/vibe-check-meme` or `/dashboard`, they get 404.
- **Redirect after login:** The app does `window.location.replace('/vibe-check-meme')`. That triggers a **new request** to `https://test.mingusapp.com/vibe-check-meme`, which currently returns 404, so the user never sees the vibe-check page.
- **Continue to Dashboard:** Same for `/dashboard` – 404 on direct load.

So today you **cannot** complete the full sequence (login → vibe-check-meme → dashboard) on test.mingusapp.com until nginx is fixed.

---

## Goal: successful login → vibe-check-meme → dashboard

You need:

1. **Login page** – Either opening `https://test.mingusapp.com` or `https://test.mingusapp.com/login` shows the login form (both should work).
2. **After login** – Browser is sent to `/vibe-check-meme` and gets the **same SPA** (index.html), so React Router shows the vibe-check page.
3. **Vibe-check** – Meme loads from `/api/user-meme`; user can click “Continue to Dashboard.”
4. **Dashboard** – Navigate to `/dashboard` and get the SPA again, so the Career Protection dashboard loads.

The only way to get (2) and (4) is for nginx to serve **index.html** for `/login`, `/vibe-check-meme`, `/dashboard`, and any other client-side route. That is the **SPA fallback**.

---

## Steps to take (in order)

### Step 1: Fix nginx so client routes serve the SPA

The config that **actually** handles `test.mingusapp.com` on the server must have a `location /` that falls back to `index.html`. The repo’s recommended config already has it.

**Option A – Use the repo’s test config (recommended)**

The config file must be on the server before you can copy it into place. Choose one:

- **From your local machine** (where the repo lives): run `scp scripts/nginx/mingusapp.com.test.conf test.mingusapp.com:/tmp/mingusapp.com.test.conf` first, then SSH in and run the server commands below.
- **From the server only** (no access to run scp): create the file with `sudo nano /etc/nginx/sites-available/mingus-test`, paste the full config from `scripts/nginx/mingusapp.com.test.conf` (see “Full config to paste” at the end of this doc), save and exit, then run only the `ln -sf`, `nginx -t`, and `reload` commands below (skip the `cp /tmp/...` line).

On the **server** (after the file exists in `/tmp` **or** you created `mingus-test` with nano):

```bash
# Backup current config (if you have a separate test file)
sudo cp /etc/nginx/sites-available/mingus-test /etc/nginx/sites-available/mingus-test.bak.$(date +%Y%m%d) 2>/dev/null || true

# Install the repo config (skip this line if you created mingus-test with nano above)
sudo cp /tmp/mingusapp.com.test.conf /etc/nginx/sites-available/mingus-test

# Enable and reload
sudo ln -sf /etc/nginx/sites-available/mingus-test /etc/nginx/sites-enabled/mingus-test
sudo nginx -t && sudo systemctl reload nginx
```

If your server uses a **single combined file** for both mingusapp.com and test.mingusapp.com (e.g. only `sites-available/mingusapp.com`), then:

- Open that file and find the **server block** with `server_name test.mingusapp.com;`.
- Ensure that block has exactly:
  - `root /var/www/mingusapp.com;`
  - In `location /` (the one that matches the frontend):
    ```nginx
    location / {
        try_files $uri $uri/ /index.html;
    }
    ```
- If `try_files` is missing or different, fix it, then run `sudo nginx -t && sudo systemctl reload nginx`.

**Option B – Single combined config**

If you prefer one file for both hosts, use the combined config and ensure the test block has the SPA fallback:

```bash
scp scripts/nginx/mingusapp.com.combined.conf test.mingusapp.com:/tmp/mingusapp.com.combined.conf
ssh test.mingusapp.com
sudo cp /tmp/mingusapp.com.combined.conf /etc/nginx/sites-available/mingusapp.com
# Disable mingus-test if it exists, so only one config defines test.mingusapp.com
sudo rm -f /etc/nginx/sites-enabled/mingus-test
sudo nginx -t && sudo systemctl reload nginx
```

See [NGINX_OPTION_B_APPLY.md](./NGINX_OPTION_B_APPLY.md) for full steps and conflict resolution.

---

### Step 2: Verify routes return 200 and the app

On the server or from your machine:

```bash
# All should return HTTP 200 and the same HTML (with index-....js)
curl -sI https://test.mingusapp.com/
curl -sI https://test.mingusapp.com/login
curl -sI https://test.mingusapp.com/vibe-check-meme
curl -sI https://test.mingusapp.com/dashboard
```

You should see `HTTP/1.1 200 OK` and `content-type: text/html` for each. Then:

```bash
curl -s https://test.mingusapp.com/login | grep -o 'index-[a-z0-9]*\.js'
```

You should see the current bundle name (e.g. `index-f6e209cc.js`). If so, the SPA is being served for all routes.

**If you see “conflicting server name test.mingusapp.com (ignored)” when running `nginx -t`:** Two configs define the same host (e.g. `mingusapp.com` and `mingus-test`). Nginx uses the **first** one loaded and ignores the other. If `/login`, `/vibe-check-meme`, and `/dashboard` already return 200, the config that is **in use** has the SPA fallback and you’re done. Cleanup is optional: have only one config define `test.mingusapp.com`—either remove the test blocks from the main config (so `mingus-test` is used) or disable `mingus-test` and keep the test block in the main config. See [VIBE_CHECK_MEME_NGINX_FIX.md](./VIBE_CHECK_MEME_NGINX_FIX.md) “Conflicting server name” for exact steps.

#### Option A: Use only mingus-test for test.mingusapp.com

So that only `mingus-test` defines test.mingusapp.com (no duplicate), replace the main config with the production-only version.

**From your local machine** (repo root):

```bash
scp scripts/nginx/mingusapp.com.production-only.conf test.mingusapp.com:/tmp/mingusapp.com.production-only.conf
```

**On the server:**

```bash
sudo cp /etc/nginx/sites-available/mingusapp.com /etc/nginx/sites-available/mingusapp.com.bak.$(date +%Y%m%d)
sudo cp /tmp/mingusapp.com.production-only.conf /etc/nginx/sites-available/mingusapp.com
# If sites-enabled/mingusapp.com is a real file (not a symlink), replace it with a symlink so nginx uses sites-available
sudo rm -f /etc/nginx/sites-enabled/mingusapp.com
sudo ln -s /etc/nginx/sites-available/mingusapp.com /etc/nginx/sites-enabled/mingusapp.com
sudo nginx -t && sudo systemctl reload nginx
```

**Check:** `sudo nginx -t` should show no "conflicting server name" warnings. test.mingusapp.com is then defined only in `sites-enabled/mingus-test`. If production uses a different `root` (e.g. not `/var/www/mingus-app/frontend/dist`), edit `/etc/nginx/sites-available/mingusapp.com` and set the correct `root`, then reload nginx again.

**If you still see "conflicting server name" after replacing mingusapp.com:** A second file still defines test.mingusapp.com. On the server run:

```bash
# See which enabled configs exist
ls -la /etc/nginx/sites-enabled/

# Find which file(s) mention test.mingusapp.com
sudo grep -r "test.mingusapp.com" /etc/nginx/sites-enabled/
```

One of the listed files (besides mingus-test) still has a `server_name test.mingusapp.com` block. Either remove that file from sites-enabled (if it's a duplicate) or edit that file to remove/comment out the test.mingusapp.com server blocks. Then run `sudo nginx -t && sudo systemctl reload nginx`.

---

### Step 3: Run the full test sequence again

From your **local machine** (repo root), with a real test account for test.mingusapp.com:

```bash
CYPRESS_BASE_URL=https://test.mingusapp.com \
CYPRESS_LOGIN_EMAIL=your-test-account@example.com \
CYPRESS_LOGIN_PASSWORD=yourpassword \
npx cypress run --spec cypress/e2e/login-vibe-dashboard-do.cy.ts
```

Or run the same flow manually in a browser:

1. Open **https://test.mingusapp.com** (or https://test.mingusapp.com/login).
2. Sign in with your test credentials.
3. You should land on **vibe-check-meme** (meme or “Continue to Dashboard”).
4. Click **Continue to Dashboard** (or vote then continue).
5. You should see the **Dashboard** (Career Protection).

---

### Step 4: If login or vibe-check still fail

- **Login fails (stay on login, “Invalid email or password”):**  
  Confirm the backend for test.mingusapp.com is running (e.g. app on `127.0.0.1:5000`) and that `POST /api/auth/login` is proxied there (nginx `location /api/` → `proxy_pass http://127.0.0.1:5000`). Use an account that exists on the **test** environment.

- **“Could not load vibe check” on vibe-check-meme:**  
  Check that `GET /api/user-meme` is proxied to the same backend and returns 200 when the session cookie is present. Check backend logs for that request.

- **Dashboard blank or errors:**  
  Check browser Network tab for failing `/api/risk/*` (or other) requests and fix backend or nginx proxy for those paths.

---

## Summary

| Item | Status / action |
|------|------------------|
| **Root (/) on test.mingusapp.com** | OK – login page loads. |
| **/login, /vibe-check-meme, /dashboard** | 404 – nginx not serving SPA for these paths. |
| **Fix** | Ensure the nginx config for test.mingusapp.com has `location / { try_files $uri $uri/ /index.html; }` and reload nginx. |
| **After fix** | Re-run Cypress or manual test: login → vibe-check-meme → dashboard should succeed. |

Use the steps above in order; after Step 1 and 2, the test.mingusapp.com sequence (login → view vibe-check-meme → dashboard) can complete successfully.

---

## Full config to paste (when creating the file on the server with nano)

If you are on the server and cannot run `scp` from your laptop, run `sudo nano /etc/nginx/sites-available/mingus-test`, then paste this entire block, save (Ctrl+O, Enter, Ctrl+X), and run the enable/reload commands from Step 1 (skip the `cp /tmp/...` line).

```nginx
# test.mingusapp.com - no upstream block (mingusapp.com already defines "backend")
# API is proxied directly to 127.0.0.1:5000 to avoid duplicate upstream with main config.

# HTTPS Server Block
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name test.mingusapp.com;

    root /var/www/mingusapp.com;
    index index.html index.htm;

    # SSL Configuration (managed by Certbot) - use test.mingusapp.com cert
    ssl_certificate /etc/letsencrypt/live/test.mingusapp.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/test.mingusapp.com/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubdomains; preload" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self' https://api.mingusapp.com;" always;

    access_log /var/log/nginx/mingusapp.com.access.log;
    error_log /var/log/nginx/mingusapp.com.error.log;

    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    location = /favicon.ico {
        try_files $uri /mingus-logo.png =204;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }

    location ~* \.(jpg|jpeg|png|gif|ico|css|js|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
        try_files $uri =404;
    }

    location ~ /.well-known/acme-challenge {
        allow all;
        root /var/www/html;
    }
}

server {
    listen 80;
    listen [::]:80;
    server_name test.mingusapp.com;

    location ~ /.well-known/acme-challenge {
        allow all;
        root /var/www/html;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}
```
