# Login → Vibe-Check → Dashboard Test & Troubleshooting

This doc describes how to run the **user login test sequence** against the latest deploy on Digital Ocean (mingusapp.com or test.mingusapp.com), and how to fix common errors.

**For test.mingusapp.com only:** See **[TEST_MINGUSAPP_COM_SEQUENCE_REPORT.md](./TEST_MINGUSAPP_COM_SEQUENCE_REPORT.md)** for the completed sequence results, current errors, and step-by-step fix for that host.

## Test sequence

1. **Login** – Load `/login`, submit credentials, expect redirect to `/vibe-check-meme`.
2. **Vibe-check page** – View vibe-check (meme loads from `/api/user-meme`); optional vote then continue.
3. **Dashboard** – Navigate to `/dashboard` and confirm the Career Protection dashboard loads.

## How to run the test

### Prerequisites

- **Credentials**: Use a real account on the target environment. The test uses the live API (no stubbing).
- **Base URL**: Production = `https://mingusapp.com`. Test server = `https://test.mingusapp.com` (must be serving the app; see errors below).

### Commands

From the repo root:

**Production (mingusapp.com):**

```bash
CYPRESS_BASE_URL=https://mingusapp.com \
CYPRESS_LOGIN_EMAIL=your@email.com \
CYPRESS_LOGIN_PASSWORD=yourpassword \
npx cypress run --spec cypress/e2e/login-vibe-dashboard-do.cy.ts
```

**Test server (test.mingusapp.com):**

```bash
CYPRESS_BASE_URL=https://test.mingusapp.com \
CYPRESS_LOGIN_EMAIL=your@email.com \
CYPRESS_LOGIN_PASSWORD=yourpassword \
npx cypress run --spec cypress/e2e/login-vibe-dashboard-do.cy.ts
```

**Interactive (headed) run:**

```bash
CYPRESS_BASE_URL=https://mingusapp.com \
CYPRESS_LOGIN_EMAIL=your@email.com \
CYPRESS_LOGIN_PASSWORD=yourpassword \
npx cypress open
```

Then choose the spec `login-vibe-dashboard-do.cy.ts`.

If `LOGIN_EMAIL` / `LOGIN_PASSWORD` are not set, the spec skips the tests that require login and only runs “loads login page without 404”.

---

## Errors encountered and troubleshooting

### 1. Login page returns 404 (e.g. test.mingusapp.com)

**Symptom:** Visiting `https://test.mingusapp.com/login` (or `/vibe-check-meme`, `/dashboard`) returns **404 Not Found** or nginx default page.

**Cause:** Nginx has no server block for that host, or the block does not serve the SPA: requests to `/login` go to the filesystem, and there is no `login` file, so nginx returns 404.

**Steps to fix:**

1. Ensure a server block exists for the host (e.g. `test.mingusapp.com`) with:
   - `root` pointing to the deployed frontend (e.g. `/var/www/mingusapp.com`).
   - SPA fallback so all routes serve `index.html`:
     ```nginx
     location / {
       try_files $uri $uri/ /index.html;
     }
     ```
2. Use the repo’s config:
   - **Option A:** `scripts/nginx/mingusapp.com.test.conf` – copy to the server as the config for test.mingusapp.com (see [VIBE_CHECK_MEME_NGINX_FIX.md](./VIBE_CHECK_MEME_NGINX_FIX.md)).
   - **Option B:** Single combined config – see [NGINX_OPTION_B_APPLY.md](./NGINX_OPTION_B_APPLY.md) and use `scripts/nginx/mingusapp.com.combined.conf`.
3. Reload nginx after changing config:
   ```bash
   sudo nginx -t && sudo systemctl reload nginx
   ```
4. Verify:
   ```bash
   curl -sI https://test.mingusapp.com/login
   # Should be 200 and return HTML (same as /)
   curl -s https://test.mingusapp.com/login | grep -o 'index-[a-z0-9]*\.js'
   # Should show current bundle hash
   ```

**Reference:** [VIBE_CHECK_MEME_NGINX_FIX.md](./VIBE_CHECK_MEME_NGINX_FIX.md), [NGINX_OPTION_B_APPLY.md](./NGINX_OPTION_B_APPLY.md).

---

### 2. Login fails (stay on /login or “Invalid email or password”)

**Symptom:** After submitting the form, URL stays on `/login` or an error message appears.

**Checks:**

1. **Credentials** – Confirm email/password are correct for the environment (production vs test).
2. **API** – Login uses `POST /api/auth/login`. Check:
   - Browser DevTools → Network: status of the login request (4xx/5xx).
   - Backend logs on the server for auth errors.
3. **CORS / cookie** – If the test runs from a different origin, ensure the backend allows that origin and sends credentials (cookies) correctly. For same-origin (e.g. Cypress visiting mingusapp.com), this is usually fine.
4. **Backend up** – Ensure the app behind nginx (e.g. `proxy_pass http://127.0.0.1:5000`) is running and that `/api/auth/login` is routed to it.

---

### 3. Vibe-check page shows “Could not load vibe check”

**Symptom:** After login you land on `/vibe-check-meme` but see “Could not load vibe check” and a “Continue to Dashboard” button.

**Cause:** The vibe-check component loads a meme from `GET /api/user-meme`. If that request fails (4xx/5xx or network error), the UI shows this message.

**Steps to fix:**

1. **Auth** – `/api/user-meme` may require an authenticated session (cookie or token). Confirm the login response sets the session cookie and that the next request to `/api/user-meme` includes it (same site, no blocking).
2. **Backend** – Check backend logs when loading vibe-check. Ensure the meme/analytics endpoints are registered and not returning 500.
3. **Network** – In DevTools → Network, confirm `/api/user-meme` is sent and what status/body it returns.

---

### 4. Dashboard does not load or shows errors

**Symptom:** After “Continue to Dashboard” or navigating to `/dashboard`, the page is blank, shows an error, or never finishes loading.

**Checks:**

1. **Route** – Confirm nginx serves `/dashboard` as the SPA (same `try_files ... /index.html` as for `/login`).
2. **APIs** – Dashboard calls e.g. `/api/risk/dashboard-state` and other endpoints. Check Network tab for failed (4xx/5xx) requests.
3. **Auth / VibeGuard** – App may require auth and/or completed vibe-check. If the guard redirects away, you may see a flash then redirect to login or vibe-check; ensure you’re logged in and have passed vibe-check (or bypass in dev if applicable).
4. **Console** – Check browser console for JavaScript errors that might prevent the dashboard from rendering.

---

### 5. test.mingusapp.com uses wrong SSL cert

**Symptom:** Browser or client reports certificate mismatch (e.g. cert is for mingusapp.com when visiting test.mingusapp.com).

**Steps:** See [NGINX_CERT_DEBUG.md](./NGINX_CERT_DEBUG.md). Ensure the **first** `listen 443 ssl` block for the server (or the block that matches `test.mingusapp.com`) uses the certificate for `test.mingusapp.com`:

- `ssl_certificate /etc/letsencrypt/live/test.mingusapp.com/fullchain.pem;`
- `ssl_certificate_key /etc/letsencrypt/live/test.mingusapp.com/privkey.pem;`

Reload nginx and verify:

```bash
echo | openssl s_client -connect test.mingusapp.com:443 -servername test.mingusapp.com 2>/dev/null | openssl x509 -noout -subject
# Should show: subject=CN = test.mingusapp.com
```

---

## Quick reference

| Step        | URL                  | Possible failure              | Fix focus                    |
|------------|----------------------|-------------------------------|------------------------------|
| Load login | `/login`             | 404                           | Nginx SPA fallback, server block |
| Submit login | `POST /api/auth/login` | 4xx/5xx, stay on /login     | Backend auth, credentials    |
| Vibe-check | `/vibe-check-meme`, `GET /api/user-meme` | “Could not load vibe check” | Auth cookie, backend meme API |
| Dashboard  | `/dashboard`, `/api/risk/*` etc. | Blank, errors, redirects   | SPA route, API, auth/guards |

Running the spec with the correct `CYPRESS_BASE_URL` and credentials will reproduce these flows and help identify which step fails; use the sections above to correct the corresponding configuration or backend.
