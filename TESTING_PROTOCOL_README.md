# Comprehensive Testing Protocol

This document describes the comprehensive testing protocol for the Mingus Application.

## Overview

The testing protocol validates the following components:

1. **Server Status** - Health check and API status endpoints
2. **Database Connection** - PostgreSQL connectivity and operations
3. **Redis Service** - Redis connectivity and operations
4. **Backend API** - API endpoint functionality
5. **Frontend Build** - Frontend build process validation
6. **Nginx Service** - Nginx service status and configuration
7. **STRIPE Test Keys** - STRIPE API key validation

## Prerequisites

### Required Python Packages

Install the following packages before running the tests:

```bash
pip install requests psycopg2-binary redis stripe
```

Or install from the test requirements:

```bash
pip install -r test_requirements.txt
```

### Environment Variables

Set the following environment variables (or create a `.env` file):

```bash
# Server Configuration
BASE_URL=http://localhost:5000

# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mingus_db
DB_USER=mingus_user
DB_PASSWORD=MingusApp2026!

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password  # Optional if no password set
REDIS_DB=0

# STRIPE Configuration
STRIPE_TEST_SECRET_KEY=sk_test_...
STRIPE_TEST_PUBLISHABLE_KEY=pk_test_...
```

### System Requirements

- Python 3.8+
- Node.js 16+ (for frontend build test)
- npm (for frontend build test)
- PostgreSQL client libraries
- Redis server running
- Nginx installed (for nginx test)

## Running the Tests

### Basic Usage

```bash
python comprehensive_testing_protocol.py
```

### With Environment Variables

```bash
BASE_URL=http://localhost:5000 \
DB_HOST=localhost \
DB_NAME=mingus_db \
python comprehensive_testing_protocol.py
```

### Using .env File

Create a `.env` file in the project root with your configuration:

```bash
BASE_URL=http://localhost:5000
DB_HOST=localhost
DB_PORT=5432
DB_NAME=mingus_db
DB_USER=mingus_user
DB_PASSWORD=your_password
REDIS_HOST=localhost
REDIS_PORT=6379
STRIPE_TEST_SECRET_KEY=sk_test_...
```

Then run:

```bash
python comprehensive_testing_protocol.py
```

## Test Details

### 1. Server Status Test

**What it tests:**
- `/health` endpoint returns 200 with status "healthy"
- `/api/status` endpoint returns 200 with operational status
- Server is accessible and responding

**Expected Result:**
- Both endpoints return 200 OK
- Health check shows "healthy" status
- API status shows "operational" status

### 2. Database Connection Test

**What it tests:**
- PostgreSQL connection using provided credentials
- Basic SELECT query execution
- Database and user information retrieval
- Table access verification

**Expected Result:**
- Connection established successfully
- Queries execute without errors
- Database information retrieved correctly

### 3. Redis Service Test

**What it tests:**
- Redis connection using provided configuration
- PING command to verify connectivity
- SET/GET operations to verify read/write functionality
- Redis server information retrieval

**Expected Result:**
- Connection established successfully
- PING returns PONG
- Read/write operations work correctly
- Redis info retrieved successfully

### 4. Backend API Test

**What it tests:**
- Multiple API endpoints respond correctly
- HTTP status codes are appropriate
- API endpoints are accessible

**Expected Result:**
- All tested endpoints return 200 or 201 status codes
- No connection errors
- API responses are valid JSON

### 5. Frontend Build Test

**What it tests:**
- Frontend directory exists
- `package.json` is present
- Dependencies are installed (`node_modules` exists)
- Build process completes successfully
- `dist` directory is created with build artifacts

**Expected Result:**
- Build command completes with exit code 0
- `dist` directory contains built files
- No build errors or warnings

### 6. Nginx Service Test

**What it tests:**
- Nginx service is active/running
- Nginx configuration is valid (`nginx -t`)
- Nginx is listening on port 80

**Expected Result:**
- Service status is "active"
- Configuration test passes
- Port 80 is listening

**Note:** On macOS, `systemctl` is not available. The test will attempt alternative methods but may show warnings.

### 7. STRIPE Test Keys Test

**What it tests:**
- STRIPE secret key is present in environment
- STRIPE publishable key is present (optional)
- Secret key is valid and authenticates with STRIPE API
- Key type (test vs live) is identified

**Expected Result:**
- Secret key is present and valid
- STRIPE API authentication succeeds
- Key type is correctly identified

## Test Results

### Output Format

The test script provides color-coded output:

- **GREEN** - Test passed
- **RED** - Test failed
- **YELLOW** - Test warning

### Result Files

Test results are automatically saved to a JSON file:

```
test_results_YYYYMMDD_HHMMSS.json
```

The JSON file contains:
- Test timestamp
- Summary statistics (total, passed, failed, warnings)
- Detailed results for each test including:
  - Test name
  - Status (PASS/FAIL/WARN)
  - Message
  - Detailed information/error messages

### Example Output

```
================================================================
MINGUS COMPREHENSIVE TESTING PROTOCOL
================================================================
Started at: 2026-01-08 14:30:00

Testing Server Status...
PASS - Server Status: Both /health and /api/status endpoints responding correctly

Testing Database Connection...
PASS - Database Connection: Successfully connected to PostgreSQL database

Testing Redis Service...
PASS - Redis Service: Redis service is operational

Testing Backend API...
PASS - Backend API: All 2 endpoints tested successfully

Testing Frontend Build...
PASS - Frontend Build: Frontend build completed successfully

Testing Nginx Service...
PASS - Nginx Service: Nginx is running and configuration is valid

Testing STRIPE Test Keys...
PASS - STRIPE Test Keys: STRIPE keys are valid (TEST mode)

================================================================
TEST SUMMARY
================================================================

Total Tests: 7
Passed: 7
Failed: 0
Warnings: 0

Detailed results saved to: test_results_20260108_143000.json
Completed at: 2026-01-08 14:30:15
```

## Troubleshooting

### Server Status Test Fails

- **Issue:** Cannot connect to server
- **Solution:** 
  - Verify the server is running: `python app.py`
  - Check BASE_URL is correct
  - Verify firewall/network settings

### Database Connection Test Fails

- **Issue:** Connection refused or authentication failed
- **Solution:**
  - Verify PostgreSQL is running: `sudo systemctl status postgresql`
  - Check database credentials in environment variables
  - Verify database exists: `psql -U postgres -l`
  - Check PostgreSQL is listening: `ss -tlnp | grep 5432`

### Redis Service Test Fails

- **Issue:** Cannot connect to Redis
- **Solution:**
  - Verify Redis is running: `redis-cli ping`
  - Check Redis configuration: `redis-cli CONFIG GET requirepass`
  - Verify Redis is listening: `ss -tlnp | grep 6379`
  - Check password if authentication is enabled

### Frontend Build Test Fails

- **Issue:** Build command fails
- **Solution:**
  - Install dependencies: `cd frontend && npm install`
  - Check Node.js version: `node --version` (should be 16+)
  - Check for TypeScript errors: `cd frontend && npm run lint`
  - Verify all dependencies are installed

### Nginx Service Test Fails

- **Issue:** Nginx not active or config invalid
- **Solution:**
  - Start Nginx: `sudo systemctl start nginx`
  - Check configuration: `sudo nginx -t`
  - Reload configuration: `sudo systemctl reload nginx`
  - Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`

### STRIPE Test Keys Test Fails

- **Issue:** Authentication failed
- **Solution:**
  - Verify STRIPE_TEST_SECRET_KEY is set correctly
  - Check key starts with `sk_test_` for test keys
  - Verify key is not expired or revoked
  - Check network connectivity to STRIPE API

## Continuous Integration

This testing protocol can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
name: Comprehensive Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install requests psycopg2-binary redis stripe
      - name: Run comprehensive tests
        env:
          BASE_URL: http://localhost:5000
          DB_HOST: localhost
          DB_NAME: test_db
        run: python comprehensive_testing_protocol.py
```

## Next Steps

After running the comprehensive tests:

1. **Review Results:** Check the generated JSON file for detailed information
2. **Fix Failures:** Address any failed tests
3. **Investigate Warnings:** Review warnings and fix if necessary
4. **Document Issues:** Document any persistent issues or limitations
5. **Schedule Regular Tests:** Set up automated testing schedule

## Support

For issues or questions about the testing protocol:

1. Check the troubleshooting section above
2. Review the test result JSON file for detailed error messages
3. Check application logs for additional context
4. Verify all prerequisites are met
