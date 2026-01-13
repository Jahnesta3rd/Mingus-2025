# How to Start the Server for Security Testing

## Issue Identified

The `venv_security` virtual environment was created only for running security tests (it has `requests` installed). It does **not** have Flask or other application dependencies needed to run the server.

## Solution: Use Your Main Environment

You need to start the server using your main Python environment that has all the application dependencies installed.

### Option 1: If You Have a Main Virtual Environment

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# Activate your main virtual environment (replace 'venv' with your actual venv name)
source venv/bin/activate  # or whatever your main venv is called

# Start the server on port 5001
FLASK_PORT=5001 python app.py
```

### Option 2: If Dependencies Are Installed System-Wide

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"

# Start the server directly (no venv activation needed)
FLASK_PORT=5001 python3 app.py
```

### Option 3: Install Dependencies in venv_security

If you want to use `venv_security` for everything:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
source venv_security/bin/activate

# Install all application dependencies
pip install -r requirements.txt

# Then start the server
FLASK_PORT=5001 python app.py
```

---

## Once Server is Running

### Test the Health Endpoint

In a **new terminal window**, run:

```bash
curl -I http://localhost:5001/health
```

**Expected Output:**
```
HTTP/1.1 200 OK
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';
...
```

### Run Security Tests

In another terminal (or after stopping the server):

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
source venv_security/bin/activate  # This one has requests for tests
python run_all_security_tests.py --base-url http://localhost:5001 --skip-rate-reset
```

---

## Security Fixes Status

✅ **All code fixes are complete and ready!**

The security fixes have been applied to:
- `backend/middleware/security.py` - Security headers and public endpoint handling
- `app.py` - Rate limiting exemption

Once you start the server, the fixes will be active and you can verify them with the curl command above.

---

## Quick Checklist

- [ ] Start server: `FLASK_PORT=5001 python app.py` (in main environment)
- [ ] Test health: `curl -I http://localhost:5001/health`
- [ ] Verify headers are present in the response
- [ ] Run security tests: `python run_all_security_tests.py --base-url http://localhost:5001`

---

**Note:** Port 5001 is used to avoid Apple AirPlay on port 5000 (macOS). If you prefer a different port, update the `--base-url` in the test command accordingly.
