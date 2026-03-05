# Backend Error Rate Debugging (63–74% errors)

## View last 20 errors in logs

**Gunicorn / systemd (e.g. mingus-backend.service):**
```bash
# Backend error log
sudo tail -n 500 /var/log/mingus-app/backend-error.log | grep -i -E "error|exception|failed|405|400|500" | tail -20

# Or last 20 lines of error log
sudo tail -n 20 /var/log/mingus-app/backend-error.log
```

**App log file (when LOG_FILE is set, e.g. `logs/app.log`):**
```bash
tail -n 500 logs/app.log | grep -i -E "error|exception|failed|405|400|500" | tail -20
```

**CORS-specific failures:**
```bash
grep -i "CORS BLOCKED\|CORS ERROR\|CORS FAILURE" logs/cors.log 2>/dev/null | tail -20
```

## Common causes of high error rate

1. **CORS** – Requests from `https://test.mingusapp.com` blocked when origin was not in `CORS_ORIGINS`.  
   **Fix applied:** `https://test.mingusapp.com` is always appended to allowed origins in `app.py`; also added to `env.example` and `scripts/systemd/mingus-test.service`.

2. **405 on `/api/create-payment-intent`** – Browser sends OPTIONS first; if the route only had `methods=['POST']`, OPTIONS could get 405 and the real POST never sent.  
   **Fix applied:** Route now has `methods=['POST', 'OPTIONS']` and returns `204` for OPTIONS.

3. **Validation / 400** – e.g. assessment type or payload validation failing (e.g. `vehicle-financial-health` not in backend allowlist).  
   **Check:** `grep "400\|Validation\|Invalid" backend-error.log` and confirm validation allowlists match frontend.

4. **500 / exceptions** – Unhandled errors in a hot path (health, status, assessments, payment).  
   **Check:** Last lines of `backend-error.log` and tracebacks; fix or add handling for the failing endpoint.

## After deploying fixes

1. Restart the backend (e.g. `sudo systemctl restart mingus-test` or `mingus-backend`).
2. Confirm `CORS_ORIGINS` in env or service includes `https://test.mingusapp.com` (or rely on app.py appending it).
3. Retest checkout flow: OPTIONS then POST to `/api/create-payment-intent` from the test frontend.
4. Re-check error rate and last 20 errors; repeat until systematic causes are gone.
