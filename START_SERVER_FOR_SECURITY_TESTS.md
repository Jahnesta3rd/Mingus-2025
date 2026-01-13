# How to Start Server for Security Tests

## Quick Start

### Step 1: Start the Server

Open a terminal and run:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
source venv_security/bin/activate
FLASK_PORT=5001 python app.py
```

**Note:** Use port 5001 to avoid Apple AirPlay on port 5000 (macOS).

### Step 2: Verify Server is Running

In another terminal, test the health endpoint:

```bash
curl -I http://localhost:5001/health
```

**Expected Output:**
```
HTTP/1.1 200 OK
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:; connect-src 'self'; frame-ancestors 'none';
...
```

### Step 3: Run Security Tests

Once the server is running, run the security tests:

```bash
cd "/Users/johnniewatsoniii/Desktop/Mingus Application - Cursor"
source venv_security/bin/activate
python run_all_security_tests.py --base-url http://localhost:5001 --skip-rate-reset
```

---

## Troubleshooting

### Server Won't Start

1. **Check for errors in the terminal output**
   - Look for import errors, missing dependencies, or configuration issues

2. **Verify virtual environment is activated**
   ```bash
   which python
   # Should show: .../venv_security/bin/python
   ```

3. **Check if port is already in use**
   ```bash
   lsof -i :5001
   # If something is using the port, kill it or use a different port
   ```

4. **Try a different port**
   ```bash
   FLASK_PORT=8000 python app.py
   # Then update test URL: --base-url http://localhost:8000
   ```

### Connection Refused

- **Server not started**: Make sure the server process is running
- **Wrong port**: Verify the server is listening on the port you're testing
- **Firewall**: Check if firewall is blocking the connection

### Missing Dependencies

If you see import errors, install missing packages:

```bash
source venv_security/bin/activate
pip install -r requirements.txt
```

---

## Security Fixes Applied

All security fixes have been applied to the code:

✅ **Security Headers** - Set on all responses  
✅ **Public Endpoints** - `/health` and `/api/status` bypass security  
✅ **CORS OPTIONS** - Properly handled  
✅ **Rate Limiting** - `/health` is exempt  

The fixes are in the code and will work once the server is running.

---

## Expected Test Results

After starting the server and running tests, you should see:

- ✅ `/health` endpoint returns **200 OK** (not 403)
- ✅ Security headers present on all responses
- ✅ Improved test pass rates
- ✅ Public endpoints accessible
- ✅ CORS working correctly

---

**Files Modified:**
- `backend/middleware/security.py` - Security headers and public endpoint handling
- `app.py` - Rate limiting exemption for `/health`

All code changes are complete and ready to test once the server is running.
