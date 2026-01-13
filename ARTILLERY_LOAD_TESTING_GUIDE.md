# Artillery Load Testing Guide

## Overview

Artillery is a modern, powerful load testing toolkit designed for API testing. This guide covers setting up and running Artillery load tests for the Mingus application.

## Installation

### Option 1: Global Installation (Recommended)

```bash
npm install -g artillery
```

### Option 2: Local Installation

```bash
cd artillery
npm install
```

### Option 3: Using npx (No Installation)

```bash
npx artillery@latest run artillery/artillery-config.yml
```

### Verify Installation

```bash
artillery --version
```

## Quick Start

### 1. Start Flask Application

```bash
export FLASK_PORT=5001
python app.py
```

### 2. Run Standard Load Test

```bash
cd artillery
artillery run artillery-config.yml
```

### 3. Run All Tests

```bash
./artillery/run-artillery-tests.sh
```

## Test Scenarios

### Standard Load Test (`artillery-config.yml`)

**Phases:**
- Warm-up: 30s at 2 req/s
- Ramp-up: 60s from 5 to 20 req/s
- Sustained: 120s at 20 req/s
- Spike: 30s at 50 req/s
- Cool-down: 30s at 5 req/s

**Endpoints Tested:**
- Health check (10% weight)
- API status (10% weight)
- Metrics (5% weight)
- Dashboard (5% weight)
- Error statistics (5% weight)
- Assessment submission (15% weight)
- Profile retrieval (10% weight)
- Vehicle endpoint (10% weight)
- Job matching (10% weight)
- Error generation (5% weight)

**Run:**
```bash
artillery run artillery/artillery-config.yml
```

### Stress Test (`artillery-stress.yml`)

**Phases:**
- Ramp to stress: 60s from 10 to 100 req/s
- Sustained stress: 300s at 100 req/s
- Spike: 30s at 200 req/s
- Recovery: 60s at 20 req/s

**Purpose:** Test system under high sustained load

**Run:**
```bash
artillery run artillery/artillery-stress.yml
```

### Spike Test (`artillery-spike.yml`)

**Phases:**
- Normal load: 60s at 10 req/s
- Spike: 30s at 200 req/s
- Return to normal: 60s at 10 req/s

**Purpose:** Test system response to sudden traffic spikes

**Run:**
```bash
artillery run artillery/artillery-spike.yml
```

## Configuration

### Custom Target URL

```bash
artillery run --target http://localhost:5001 artillery/artillery-config.yml
```

### Custom Output

```bash
artillery run \
  --output results/test-$(date +%Y%m%d_%H%M%S).json \
  artillery/artillery-config.yml
```

### Generate HTML Report

```bash
# Run test and save JSON
artillery run --output results/test.json artillery/artillery-config.yml

# Generate HTML report
artillery report results/test.json > results/test-report.html
```

## Test Results

### Understanding Artillery Output

Artillery provides real-time metrics during test execution:

```
Scenarios launched:  150
Scenarios completed: 150
Requests completed:  450
Mean response/sec: 15.2
Response time (msec):
  min: 45.2
  max: 1250.3
  median: 89.5
  p95: 234.1
  p99: 456.7
```

### Key Metrics

- **Scenarios launched**: Total scenarios executed
- **Requests completed**: Total HTTP requests
- **Mean response/sec**: Average throughput
- **Response time**: min, max, median, p95, p99
- **Codes**: HTTP status code distribution
- **Errors**: Error count and types

### HTML Reports

Artillery generates detailed HTML reports with:
- Response time distributions
- Request rate over time
- Status code breakdown
- Error analysis
- Endpoint-specific metrics

## Custom Test Scenarios

### Create Custom Scenario

Create `artillery/custom-test.yml`:

```yaml
config:
  target: "http://localhost:5001"
  phases:
    - duration: 60
      arrivalRate: 10
      name: "Custom test"
  
  defaults:
    headers:
      Content-Type: "application/json"

scenarios:
  - name: "Custom Scenario"
    flow:
      - get:
          url: "/health"
          expect:
            - statusCode: 200
            - maxResponseTime: 500
```

Run:
```bash
artillery run artillery/custom-test.yml
```

## Integration with Monitoring

### Real-Time Monitoring

While Artillery runs, monitor the application:

```bash
# Terminal 1: Run Artillery
artillery run artillery/artillery-config.yml

# Terminal 2: Monitor dashboard
open http://localhost:5001/dashboard

# Terminal 3: Watch metrics
watch -n 2 'curl -s http://localhost:5001/api/metrics | jq'
```

### Compare Metrics

1. **Before test:**
   ```bash
   curl http://localhost:5001/api/metrics > metrics-before.json
   ```

2. **Run Artillery test**

3. **After test:**
   ```bash
   curl http://localhost:5001/api/metrics > metrics-after.json
   ```

4. **Compare:**
   ```bash
   diff metrics-before.json metrics-after.json
   ```

## Advanced Configuration

### Custom Headers

```yaml
config:
  defaults:
    headers:
      Authorization: "Bearer {{ token }}"
      X-CSRF-Token: "{{ csrf_token }}"
```

### Variable Substitution

```yaml
config:
  variables:
    userId: "user123"
    apiKey: "key456"

scenarios:
  - name: "Authenticated Request"
    flow:
      - get:
          url: "/api/users/{{ userId }}"
          headers:
            Authorization: "Bearer {{ apiKey }}"
```

### Conditional Logic

```yaml
scenarios:
  - name: "Conditional Flow"
    flow:
      - get:
          url: "/api/status"
          capture:
            - json: "$.status"
              as: "status"
      - think: 1
      - get:
          url: "/api/{{ status }}/data"
```

## Performance Targets

### Response Time Targets

Set expectations in test config:

```yaml
scenarios:
  - name: "Fast Endpoint"
    flow:
      - get:
          url: "/health"
          expect:
            - maxResponseTime: 100  # 100ms max
            - statusCode: 200
```

### Error Rate Targets

```yaml
config:
  ensure:
    maxErrorRate: 1  # Max 1% error rate
    p95: 500  # 95th percentile under 500ms
    p99: 1000  # 99th percentile under 1000ms
```

## Troubleshooting

### Artillery Not Found

```bash
# Install globally
npm install -g artillery

# Or use npx
npx artillery@latest run artillery/artillery-config.yml
```

### Connection Refused

1. **Check server is running:**
   ```bash
   curl http://localhost:5001/health
   ```

2. **Verify port:**
   ```bash
   # Check if port 5001 is correct
   export FLASK_PORT=5001
   python app.py
   ```

### High Error Rate

1. **Check server logs**
2. **Review error statistics:**
   ```bash
   curl http://localhost:5001/api/errors/stats?hours=1 | jq
   ```
3. **Reduce load:**
   ```yaml
   phases:
     - duration: 60
       arrivalRate: 5  # Reduce from higher rate
   ```

### Slow Response Times

1. **Check system resources:**
   ```bash
   curl http://localhost:5001/api/metrics | jq '.system'
   ```

2. **Review recommendations:**
   ```bash
   curl http://localhost:5001/api/metrics/recommendations | jq
   ```

3. **Check database performance**
4. **Review cache hit rates**

## Best Practices

### 1. Start Small

Begin with low load and gradually increase:
```yaml
phases:
  - duration: 30
    arrivalRate: 1
  - duration: 30
    arrivalRate: 5
  - duration: 30
    arrivalRate: 10
```

### 2. Monitor During Tests

- Watch dashboard: `http://localhost:5001/dashboard`
- Monitor logs: `tail -f logs/app.log`
- Check errors: `tail -f logs/errors.log`

### 3. Save Results

Always save test results:
```bash
artillery run --output results/test-$(date +%Y%m%d_%H%M%S).json \
  artillery/artillery-config.yml
```

### 4. Compare Baselines

Establish baseline metrics and compare:
```bash
# Baseline
artillery run --output results/baseline.json artillery/artillery-config.yml

# After changes
artillery run --output results/after-changes.json artillery/artillery-config.yml

# Compare
artillery report --compare results/baseline.json results/after-changes.json
```

### 5. Test Realistic Scenarios

Match production traffic patterns:
- User behavior patterns
- Peak hours simulation
- Realistic data payloads

## Example Test Execution

### Full Test Suite

```bash
# 1. Start Flask app
export FLASK_PORT=5001
python app.py

# 2. Run all Artillery tests
cd artillery
./run-artillery-tests.sh

# 3. View results
open results/*-report.html
```

### Single Test with Custom Parameters

```bash
artillery run \
  --target http://localhost:5001 \
  --output results/custom-test.json \
  --count 1000 \
  --concurrency 50 \
  artillery/artillery-config.yml
```

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Load Tests
on: [push, pull_request]
jobs:
  load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-node@v2
        with:
          node-version: '18'
      - run: npm install -g artillery
      - run: |
          # Start Flask app
          python app.py &
          sleep 10
          # Run tests
          artillery run artillery/artillery-config.yml
```

## Results Analysis

### Key Metrics to Review

1. **Response Times:**
   - p95 and p99 percentiles
   - Mean and median
   - Max response time

2. **Throughput:**
   - Requests per second
   - Successful requests
   - Failed requests

3. **Error Rate:**
   - HTTP error codes
   - Timeout errors
   - Connection errors

4. **System Resources:**
   - CPU usage during test
   - Memory usage
   - Database connections

### Performance Benchmarks

**Target Metrics:**
- p95 response time: < 500ms
- p99 response time: < 1000ms
- Error rate: < 1%
- Throughput: > 50 req/s (sustained)

## Next Steps

1. **Install Artillery:**
   ```bash
   npm install -g artillery
   ```

2. **Run Standard Test:**
   ```bash
   artillery run artillery/artillery-config.yml
   ```

3. **Review Results:**
   - Check Artillery output
   - View HTML reports
   - Compare with monitoring dashboard

4. **Iterate:**
   - Adjust load patterns
   - Test different scenarios
   - Optimize based on results

---

**Status**: ✅ Artillery load testing configured and ready

**Quick Start**: `artillery run artillery/artillery-config.yml`
