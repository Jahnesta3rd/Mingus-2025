# Quick Start - Comprehensive Testing Protocol

## Installation

### 1. Install Test Dependencies

```bash
pip install -r test_requirements.txt
```

Or install individually:

```bash
pip install requests psycopg2-binary redis stripe
```

### 2. Set Environment Variables

Create a `.env` file or export variables:

```bash
# Server
export BASE_URL=http://localhost:5000

# Database
export DB_HOST=localhost
export DB_PORT=5432
export DB_NAME=mingus_db
export DB_USER=mingus_user
export DB_PASSWORD=MingusApp2026!

# Redis
export REDIS_HOST=localhost
export REDIS_PORT=6379
# export REDIS_PASSWORD=your_password  # Optional

# STRIPE
export STRIPE_TEST_SECRET_KEY=sk_test_...
export STRIPE_TEST_PUBLISHABLE_KEY=pk_test_...
```

## Run Tests

```bash
python3 comprehensive_testing_protocol.py
```

## What Gets Tested

1. ✅ **Server Status** - `/health` and `/api/status` endpoints
2. ✅ **Database Connection** - PostgreSQL connectivity
3. ✅ **Redis Service** - Redis connectivity and operations
4. ✅ **Backend API** - API endpoint functionality
5. ✅ **Frontend Build** - Frontend build process
6. ✅ **Nginx Service** - Nginx status and configuration
7. ✅ **STRIPE Test Keys** - STRIPE API key validation

## Results

Results are saved to: `test_results_YYYYMMDD_HHMMSS.json`

For detailed documentation, see: `TESTING_PROTOCOL_README.md`
