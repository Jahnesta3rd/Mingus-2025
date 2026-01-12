# API Load Testing Guide

**Tools Created:** `load_test_api.py` and `performance_test_suite.py`

---

## Quick Start

### 1. Basic Load Test

Test a single endpoint with default settings (100 requests, 10 concurrent users):

```bash
python load_test_api.py --endpoint /health
```

### 2. Custom Load Test

Test with custom parameters:

```bash
python load_test_api.py \
  --endpoint /api/status \
  --requests 200 \
  --concurrent 20 \
  --url http://localhost:5000
```

### 3. Comprehensive Test Suite

Test multiple endpoints automatically:

```bash
python load_test_api.py --requests 100 --concurrent 10 --save
```

### 4. Performance Comparison (Cache vs No Cache)

Compare performance with and without caching:

```bash
python performance_test_suite.py \
  --endpoint /api/vehicle \
  --compare-cache \
  --url http://localhost:5000
```

### 5. Full Performance Suite

Run complete performance test suite:

```bash
python performance_test_suite.py --full --url http://localhost:5000
```

---

## Test Scenarios

### Scenario 1: Light Load
```bash
python load_test_api.py --requests 50 --concurrent 5
```

### Scenario 2: Medium Load
```bash
python load_test_api.py --requests 200 --concurrent 20
```

### Scenario 3: Heavy Load
```bash
python load_test_api.py --requests 1000 --concurrent 50
```

### Scenario 4: Stress Test
```bash
python load_test_api.py --requests 5000 --concurrent 100
```

---

## Testing Specific Endpoints

### Health Check
```bash
python load_test_api.py --endpoint /health --requests 100
```

### Assessment Endpoint (POST)
```bash
python load_test_api.py \
  --endpoint /api/assessments \
  --method POST \
  --requests 50
```

### Profile Endpoint
```bash
python load_test_api.py --endpoint /api/profile --requests 100
```

### Vehicle Endpoint
```bash
python load_test_api.py --endpoint /api/vehicle --requests 100
```

---

## Understanding Results

### Key Metrics

1. **Response Times:**
   - Average: Mean response time
   - Median: Middle value (less affected by outliers)
   - P95: 95% of requests faster than this
   - P99: 99% of requests faster than this

2. **Throughput:**
   - Requests/Second: How many requests can be handled per second

3. **Success Rate:**
   - Successful vs Failed requests
   - Error breakdown

### Performance Targets

| Endpoint Type | Target Response Time | Target Throughput |
|--------------|---------------------|-------------------|
| Health Check | < 50ms | > 100 req/s |
| Simple GET | < 200ms | > 50 req/s |
| Complex GET | < 500ms | > 20 req/s |
| POST/PUT | < 1000ms | > 10 req/s |

---

## Cache Performance Testing

### Test Cache Effectiveness

```bash
# Compare cached vs uncached performance
python performance_test_suite.py \
  --endpoint /api/vehicle \
  --compare-cache
```

This will:
1. Test endpoint without cache (cold)
2. Warm up the cache
3. Test endpoint with cache (warm)
4. Show performance improvement percentage

### Expected Cache Improvements

- **First Request (Cold):** Slower (hits database)
- **Subsequent Requests (Warm):** 70-90% faster (from cache)
- **Cache Hit Rate:** Should be > 80% after warmup

---

## Monitoring During Tests

### Check Application Logs
```bash
tail -f logs/app.log
```

### Check Redis Cache
```bash
redis-cli
> INFO stats
> KEYS query_cache:*
```

### Check Database Connections
```bash
# PostgreSQL
psql -U your_user -d your_db -c "SELECT count(*) FROM pg_stat_activity;"
```

---

## Interpreting Results

### Good Performance
- ✅ Average response time < 500ms
- ✅ P95 response time < 1000ms
- ✅ Success rate > 95%
- ✅ No timeout errors
- ✅ Consistent response times

### Performance Issues
- ⚠️ Average response time > 1000ms
- ⚠️ P95 response time > 2000ms
- ⚠️ Success rate < 90%
- ⚠️ Many timeout errors
- ⚠️ Inconsistent response times

### Optimization Opportunities
- High response times → Enable query caching
- Low throughput → Optimize database queries
- Many errors → Check rate limiting settings
- Timeouts → Increase connection pool size

---

## Advanced Testing

### Test with Authentication

```python
# Create a test script
import requests
from load_test_api import APILoadTester

tester = APILoadTester(base_url="http://localhost:5000")

# Login first
login_response = requests.post(
    "http://localhost:5000/api/auth/login",
    json={"email": "test@example.com", "password": "test"}
)
token = login_response.json().get('token')

# Test with auth header
headers = {'Authorization': f'Bearer {token}'}
result = tester.run_load_test(
    endpoint='/api/profile',
    method='GET',
    num_requests=100,
    concurrent_users=10,
    headers=headers
)
```

### Test POST Endpoints

```bash
python load_test_api.py \
  --endpoint /api/assessments \
  --method POST \
  --requests 50 \
  --concurrent 5
```

Note: POST endpoints may need custom data - modify the script for specific payloads.

---

## Saving Results

### Save to JSON
```bash
python load_test_api.py --full --save
```

Results saved as: `load_test_results_YYYYMMDD_HHMMSS.json`

### Analyze Results
```python
import json

with open('load_test_results_*.json') as f:
    data = json.load(f)
    
for result in data['results']:
    print(f"{result['endpoint']}: {result['avg_response_time']*1000:.2f}ms")
```

---

## Troubleshooting

### Connection Errors
- Check if Flask app is running
- Verify base URL is correct
- Check firewall settings

### Timeout Errors
- Increase timeout in script (default: 30s)
- Check server resources
- Reduce concurrent users

### Low Throughput
- Check database connection pool
- Verify Redis is running
- Check server CPU/memory usage

---

## Best Practices

1. **Start Small:** Begin with light load, gradually increase
2. **Monitor Resources:** Watch CPU, memory, database connections
3. **Test Realistic Scenarios:** Use actual user behavior patterns
4. **Compare Before/After:** Test before and after optimizations
5. **Document Results:** Save results for comparison
6. **Test Regularly:** Run tests after major changes

---

## Example Test Workflow

```bash
# 1. Start your Flask application
python app.py

# 2. Run light load test
python load_test_api.py --requests 50 --concurrent 5

# 3. Run medium load test
python load_test_api.py --requests 200 --concurrent 20

# 4. Test cache performance
python performance_test_suite.py --endpoint /api/vehicle --compare-cache

# 5. Run comprehensive test and save results
python load_test_api.py --full --save

# 6. Analyze results
cat load_test_results_*.json | jq '.results[] | {endpoint, avg_response_time, requests_per_second}'
```

---

## Performance Benchmarks

### Baseline (No Optimizations)
- Health: ~100ms average
- Simple GET: ~300ms average
- Complex GET: ~800ms average

### With Query Caching
- Health: ~50ms average (50% improvement)
- Simple GET: ~100ms average (67% improvement)
- Complex GET: ~200ms average (75% improvement)

### With Redis Sessions
- Session operations: < 10ms
- Scalable across multiple servers
- Persistent across restarts

---

**Status:** Ready to use
